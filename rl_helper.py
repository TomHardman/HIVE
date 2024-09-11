import torch
from torch_geometric.data import Data
from torch.utils.data import Dataset
from torch_geometric.loader import DataLoader

from collections import deque
from dataclasses import dataclass
import random

import matplotlib.pyplot as plt

from board import ACTIONSPACE, ACTIONSPACE_INV

REWARDS_DICT = {'queen_ownership': 0,
                'queen_surrounding': 1,
                'change_in_moves': 0,
                'change_moveable_pieces': 0,
                'win_lose': 0}

REDUCED_MAPPING = {'queen': 0, 'beetle': 1, 'ant': 2, 'grasshopper': 3, 'spider': 4}


class LossBuffer:
    def __init__(self) -> None:
        self.memory = []
        self.avg = 0

    def push(self, loss):
        if loss == None:
            return
        
        self.memory.append(loss)
        self.avg = self.avg * (len(self) - 1)/len(self) + loss/len(self)

        if len(self.memory) % 1000 == 0:
            self.plot_loss(len(self.memory))
    
    def plot_loss(self, iters):
        plt.plot(self.memory)
        plt.savefig(f'loss_plots/loss_{iters}.png')
    
    def __len__(self):
        return len(self.memory)


class RewardCalculator:
    def __init__(self, rewards_dict: dict):
        self.rewards_dict = rewards_dict

    def pieces_around_queen(self, player, state, opp=False):
        """
        Returns the number of pieces around the queen of the given player
        in state s
        """
        queen_position = state['queen_positions'][player - 1]
        if queen_position:
            npos_arr = [(queen_position[0], queen_position[1] + 1),
                        (queen_position[0] + 1, queen_position[1]),
                        (queen_position[0] + 1, queen_position[1] - 1),
                        (queen_position[0], queen_position[1] - 1),
                        (queen_position[0] - 1, queen_position[1]),
                        (queen_position[0] - 1, queen_position[1] + 1)]
        else:
            npos_arr = []
        
        pieces_around_queen = 0
        for pos in npos_arr:
            if state['tile_positions'].get(pos):
                if opp:
                    if state['tile_positions'][pos][-1].player != player:
                        pieces_around_queen += 1
                if not opp:
                    pieces_around_queen += 1
        return pieces_around_queen
    
    def queen_ownership(self, player, state):
        """
        Returns 1 if player owns the queen, -1 if opponent owns the queen
        """
        queen_position = state['queen_positions'][player - 1]
        tile_stack = state['tile_positions'].get(queen_position)
        if tile_stack:
            if tile_stack[-1].player == player:
                return 1
            else:
                return 0
        return 1
    
    def moveable_pieces(self, player, state):
        """
        Returns the number of moveable pieces for the given player in state s
        """
        moveable_pieces_set = set()
        for pos in state['valid_moves_p' + str(player)]:
            for idx, valid in enumerate(state['valid_moves_p' + str(player)][pos]):
                if valid:
                    moveable_pieces_set.add(idx)
        return len(moveable_pieces_set)

    def reward_queen_surrounding(self, player, s, s_prime):
        """
        If player manages to increase number of (own) pieces around opposition's
        queen between s and s_prime, positive reward is given - vice versa
        for decrease. If player's own queen has more pieces around it in s_prime,
        negative reward is given and vice versa.
        """
        opp = 3 - player

        n_s_self = self.pieces_around_queen(player, s)
        n_s_prime_self = self.pieces_around_queen(player, s_prime)
        n_s_opp = self.pieces_around_queen(opp, s, opp=True)
        n_s_prime_opp = self.pieces_around_queen(opp, s_prime, opp=True)

        #return (n_s_prime_opp - n_s_opp) - (n_s_prime_self - n_s_self)
        return (n_s_prime_opp - n_s_opp)

    def reward_change_in_moves(self, player, s, s_prime):
        """
        If player manages to reduce opposition's available moves between
        s and s_prime, positive reward is given - vice versa for
        decrease. If player's own available moves increase between s
        and s prime, negative reward is given and vice versa.
        """
        key_self = f'valid_moves_p{player}'
        key_opp = f'valid_moves_p{3 - player}'

        n_s_self = len(s[key_self]) # number of available moves for player in state s
        n_s_prime_self = len(s_prime[key_self]) # number of available moves for player in state s_prime
        n_s_opp = len(s[key_opp])
        n_s_prime_opp = len(s_prime[key_opp])

        return (n_s_opp - n_s_prime_opp) - (n_s_self - n_s_prime_self)
    
    def reward_queen_ownership(self, player, s, s_prime):
        """
        If player reclaims ownership of the queen (if opposition has beetle on top)
        between s and s_prime, positive reward is given. If player loses queen
        ownership, negative reward is given
        """
        ownership_change_self = self.queen_ownership(player, s_prime) - self.queen_ownership(player, s)
        ownership_change_opp = self.queen_ownership(3 - player, s_prime) - self.queen_ownership(3 - player, s)

        return ownership_change_self - ownership_change_opp
    
    def reward_change_moveable_pieces(self, player, s, s_prime):
        """
        If player manages to increase the number of moveable pieces between
        s and s_prime, positive reward is given. If player decreases the
        number of moveable pieces, negative reward is given.
        """
        moveable_pieces_change_self = self.moveable_pieces(player, s_prime) - self.moveable_pieces(player, s)
        moveable_pieces_change_opp = self.moveable_pieces(3 - player, s_prime) - self.moveable_pieces(3 - player, s)

        if moveable_pieces_change_opp == -8: # this occurs if forced to play queen on turn 3
            moveable_pieces_change_opp = 0
        if moveable_pieces_change_self == -8:
            moveable_pieces_change_self = 0

        return moveable_pieces_change_self - moveable_pieces_change_opp

    def reward_win_lose(self, player, s, s_prime):
        """
        If player wins the game, positive reward is given - if player loses,
        negative reward is given.
        """
        if s_prime['winner'] == player:
            return 1
        elif s_prime['winner'] == 3 - player:
            return -1
        return 0
    
    def calculate_reward(self, player, s, s_prime):
        """
        Calculate reward for player based on the change in the state of the board
        from s to s_prime
        """
        reward = 0

        for key in self.rewards_dict.keys():
            reward += self.rewards_dict[key] * getattr(self, 'reward_' + key)(player, s, s_prime)
            #print(key, getattr(self, 'reward_' + key)(player, s, s_prime), self.rewards_dict[key] * getattr(self, 'reward_' + key)(player, s, s_prime))
        #print(f'Reward {reward}')
        return reward
    
    def __call__(self, player, s, s_prime):
        return self.calculate_reward(player, s, s_prime)


@dataclass
class GraphState:
    data: Data
    global_feature_vector: torch.Tensor
    action_mask: torch.Tensor
    pos_node_mapping: dict # maps board position to graph node


@dataclass
class Transition:
    s: Data
    s_prime: Data
    action: tuple[tuple[int, int], int]
    reward : float # reward from taking action a in state s
    done : bool = False # whether the game is over


class TransitionDataLoader():
    def __init__(self, transitions):
        for transition in transitions:
            gs = transition.s
        
    
    def __len__(self):
        return
    
    def __getitem__(self, idx):
        return


class ExperienceReplay:
    def __init__(self, capacity):
        self.capacity = capacity
        self.memory = [] # ring buffer for O(1) sampling and appending
        self.reward_memory = [] # only remembers experiences with rewards
        self.position = 0

    def push(self, transition: Transition):
        if len(self.memory) < self.capacity:
            self.memory.append(None)
        self.memory[self.position] = transition
        if transition.reward != 0:
            self.reward_memory.append(transition)
        self.position = (self.position + 1) % self.capacity

    def sample(self, batch_size):
        sample = random.sample(self.memory, batch_size//2) + random.sample(self.reward_memory, min(batch_size//2, len(self.reward_memory)))
        return sample

    def __len__(self):
        return len(self.memory)


def get_graph_from_state(state, player, reduced=False) -> GraphState:
    """
    Returns a GraphState object containing the state of the board that can be processed by agent.
    Consists of  PyTorch Geometric Data object representing the board state in graph
    form, a global feature vector containing info about the no. pieces in each hand, a
    mask representing the valid actions for each node in the graph and a mapping of board
    positions to graph nodes so that actions can be correctly understood.

    Each node is a length d feature vector representing either a tile on the board or
    a possible space that could be moved into. There are two options for the feature vector:
    - one hot encode first 5 positions with type of tile (reduced = True)
    - one hot encode first 11 positions with the specific tile in each piece

    The next 5 / 11 slots represent the same encoding for the opposing player.

    Following the last 3 slots are used as follows: 
    -3 slot: 1 if the node is actually an empty space that can be moved into
    -2 slot: 1 if the node is a valid tile placement for the current player and -1 for opposition
    -1 slot: 1 if the node is 'owned by the current player' -1 if not (e.g if enemy player has 
             beetle on top of current player's piece this node is not owned by the current player)

    The edges represent possible moves or simply adjacency between tiles.
    Each edge is a 1d feature vector with 0 indicating adjacency and 1 indicating a
    possible move. A 22d global feature vector representing the number of pieces in the current
    player's hand and the opposing player's hand is then also supplied. This can be combined into
    the network at an intermediate point.

    Action space is represented by length 11 vector at each node representing the possible actions
    of moving a piece to that node.
    """
    if reduced == True:
        n = 13
    else:
        n = 25

    node_features = [[0 for i in range(n)]]
    edges = [[],[]]
    edge_features = []
    action_mask = [[0 for i in range(11)]] # initialise action mask for first position
    global_feature_vector = [0 for i in range(22)]

    if state['tile_positions']:
        initial_pos = list(state['tile_positions'].keys())[0]
    else:
        initial_pos = (0, 0)
   
    # use bfs to visit all tile nodes
    pos_queue = deque([initial_pos])
    pos_node_mapping = {initial_pos: 0} # maps position to node index
    node_idx = 1

    while pos_queue:
        pos = pos_queue.popleft()
        tiles = state['tile_positions'].get(pos)
        if not tiles:
            break
        for tile in tiles: # iterate through HiveTile objects at location
            if not reduced:
                piece_id = tile.name.split('_')[0]
                idx = ACTIONSPACE.get(piece_id) 
                if tile.player == player:
                    node_features[pos_node_mapping[pos]][idx] = 1
                else:
                    node_features[pos_node_mapping[pos]][idx + 11] = 1
            else:
                piece_id_red = tile.name.split('_')[0][:-1]
                idx = REDUCED_MAPPING.get(piece_id_red)
                if tile.player == player:
                    node_features[pos_node_mapping[pos]][idx] += 1
                else:
                    node_features[pos_node_mapping[pos]][idx + 5] += 1
            
            if tile == tiles[-1]:
                if tile.player == player:
                    node_features[pos_node_mapping[pos]][-1] = 1
                else:
                    node_features[pos_node_mapping[pos]][-1] = -1
        
        npos_arr = [(pos[0], pos[1] + 1), (pos[0] + 1, pos[1]), (pos[0] + 1, pos[1] - 1),
                    (pos[0], pos[1] - 1), (pos[0] - 1, pos[1]), (pos[0] - 1, pos[1] + 1)]
        
        for npos in npos_arr:
            if npos not in pos_node_mapping:
                node_features.append([0 for i in range(n)])
                action_mask.append([0 for i in range(11)]) # no valid actions for tile nodes
                pos_node_mapping[npos] = node_idx
                node_idx += 1
                
                if state['tile_positions'].get(npos):
                    pos_queue.append(npos)
                
            # create bidirectional edge between nodes
            edges[0].append(pos_node_mapping[pos])
            edges[1].append(pos_node_mapping[npos])
            edge_features.append([0])

            edges[0].append(pos_node_mapping[npos])
            edges[1].append(pos_node_mapping[pos])
            edge_features.append([0])
    
    for tile_pos in state['tile_positions']:
        try:
            assert(tile_pos in pos_node_mapping)
            assert(state['tile_positions'][tile_pos][-1].position == tile_pos)
        except AssertionError:
            raise AssertionError(f'Position {tile_pos} not in pos_node_mapping or tile not at top of')

    # add nodes for possible tile placements for self and opp
    for p in [player, 3 - player]:
        valid_moves = state[f'valid_moves_p{p}']
        for pos in valid_moves:
            if pos not in pos_node_mapping:
                action_mask.append([0 for i in range(11)])
                pos_node_mapping[pos] = node_idx
                node_features.append([0 for i in range(n)])
                node_idx += 1
            
            node_features[pos_node_mapping[pos]][-3] = 1 # encode empty space
            
            for idx, valid in enumerate(valid_moves[pos]):
                if valid:
                    if p == player:
                        action_mask[pos_node_mapping[pos]][idx] = 1 # valid action in action space
                    
                    player_hand = state[f'player{p}_hand']
                    
                    tile_placed = True
                    if idx in player_hand:
                        tile_placed=False
                    
                    if not tile_placed:
                        if pos != (0, 0):
                            # encoding valid placement
                            if p == player:
                                node_features[pos_node_mapping[pos]][-2] = 1
                            else:
                                node_features[pos_node_mapping[pos]][-2] = -1

                    else:
                        # add unidirectional edge to represent move
                        if p != player:
                            idx = idx + 11 
                        tile_pos = state['idx_pos_mapping'][idx]
                        try:
                            edges[0].append(pos_node_mapping[tile_pos])
                        except KeyError:
                            raise KeyError(f'Position {tile_pos} not in pos_node_mapping')
                        edges[1].append(pos_node_mapping[pos])
                        edge_features.append([2])

        # create global feature vector representing player hands
        player_hand = state[f'player{p}_hand']
        for idx in player_hand:
            if p == player:
                global_feature_vector[idx] += 1
            else:
                global_feature_vector[idx + 11] += 1
        
    # create PyTorch Geometric Data object
    x = torch.tensor(node_features, dtype=torch.float)
    edge_index = torch.tensor(edges, dtype=torch.long)
    edge_attr = torch.tensor(edge_features, dtype=torch.float)
    u = torch.tensor(global_feature_vector, dtype=torch.float)
    action_mask = torch.tensor(action_mask, dtype=torch.int)
    return Data(x=x, edge_index=edge_index, edge_attr=edge_attr,
                u=u, action_mask=action_mask, pos_node_mapping=pos_node_mapping,
                queen_positions=state['queen_positions'])
