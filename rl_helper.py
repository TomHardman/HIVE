import torch
from torch_geometric.data import Data

from collections import deque
from dataclasses import dataclass
import random

from board import ACTIONSPACE, ACTIONSPACE_INV

REWARDS_DICT = {'queen_ownership': 2,
                'queen_surrounding': 1,
                'change_in_moves': 0.01,
                'change_moveable_pieces': 0.2,
                'win_lose': 10}

class RewardCalculator:
    def __init__(self, rewards_dict: dict):
        self.rewards_dict = rewards_dict

    def pieces_around_queen(self, player, state):
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
        If player manages to increase number of pieces around opposition's
        queen between s and s_prime, positive reward is given - vice versa
        for decrease. If player's own queen has more pieces around it in s_prime,
        negative reward is given and vice versa.
        """
        opp = 3 - player

        n_s_self = self.pieces_around_queen(player, s)
        n_s_prime_self = self.pieces_around_queen(player, s_prime)
        n_s_opp = self.pieces_around_queen(opp, s)
        n_s_prime_opp = self.pieces_around_queen(opp, s_prime)

        return (n_s_prime_opp - n_s_opp) - (n_s_prime_self - n_s_self)

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
            print(key, getattr(self, 'reward_' + key)(player, s, s_prime), self.rewards_dict[key] * getattr(self, 'reward_' + key)(player, s, s_prime))
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
    s: GraphState
    s_prime: GraphState
    action: tuple[tuple[int, int], int]
    reward : float # reward from taking action a in state s


class ExperienceReplay:
    def __init__(self, capacity):
        self.capacity = capacity
        self.memory = [] # ring buffer for O(1) sampling and appending
        self.position = 0

    def push(self, transition: Transition):
        if len(self.memory) < self.capacity:
            self.memory.append(None)
        self.memory[self.position] = transition
        self.position = (self.position + 1) % self.capacity

    def sample(self, batch_size):
        return random.sample(self.memory, batch_size)

    def __len__(self):
        return len(self.memory)


def get_graph_from_state(state, player) -> tuple[Data, torch.Tensor, torch.Tensor]:
    """
    Returns a GraphState object containingf the state of the board that can be processed by agent.
    Consists of  PyTorch Geometric Data object representing the board state in graph
    form, a global feature vector containing info about the no. pieces in each hand, a
    mask representing the valid actions for each node in the graph and a mapping of board
    positions to graph nodes. 
    Each node is a 24d feature vector representing either a tile on the board or
    a possible space that could be moved into. The feature vector is one hot encoded
    with the pieces currently residing in the tile. The first 11 slots represent the
    pieces for the current player and last 11 slots represent the pieces for the opposition.
    The 23rd slot is used to indicate if the node is actually an empty space that can be
    moved into. The 24th slot is used to indicate if the slot can be used for tile placement:
    +1 indicates it can be used by the current player and -1 indicates it can be used by
    the opposition player. The edges represent possible moves or simply adjacency between tiles.
    Each edge is a 1d feature vector with +1 indicating adjacency and -1 indicating a
    possible move. A 22d global feature vector representing the number of pieces in the current
    player's hand and the opposing player's hand is then used.
    """
    node_features = [[0 for i in range(24)]]
    edges = [[],[]]
    edge_features = []
    action_mask = [[0 for i in range(11)]] # initialise action mask at 0,0
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
            piece_id = tile.name.split('_')[0]
            idx = ACTIONSPACE.get(piece_id) 
            if tile.player == player:
                node_features[pos_node_mapping[pos]][idx] = 1
            else:
                node_features[pos_node_mapping[pos]][idx + 11] = 1
        
        npos_arr = [(pos[0], pos[1] + 1), (pos[0] + 1, pos[1]), (pos[0] + 1, pos[1] - 1),
                    (pos[0], pos[1] - 1), (pos[0] - 1, pos[1]), (pos[0] - 1, pos[1] + 1)]
        
        for npos in npos_arr:
            if npos not in pos_node_mapping:
                node_features.append([0 for i in range(24)])
                action_mask.append([0 for i in range(11)]) # no valid actions for tile nodes
                pos_node_mapping[npos] = node_idx
                node_idx += 1
                
                if state['tile_positions'].get(npos):
                    pos_queue.append(npos)
                
            # create bidirectional edge between nodes
            edges[0].append(pos_node_mapping[pos])
            edges[1].append(pos_node_mapping[npos])
            edge_features.append([1])

            edges[0].append(pos_node_mapping[npos])
            edges[1].append(pos_node_mapping[pos])
            edge_features.append([1])

    # add nodes for possible tile placements for self and opp
    for p in [player, 3 - player]:
        valid_moves = state[f'valid_moves_p{p}']
        for pos in valid_moves:
            if pos not in pos_node_mapping:
                action_mask.append([0 for i in range(11)])
                pos_node_mapping[pos] = node_idx
                node_features.append([0 for i in range(24)])
                node_idx += 1
            
            node_features[pos_node_mapping[pos]][22] = 1 # tile can be used for placement
            
            for idx, valid in enumerate(valid_moves[pos]):
                if valid:
                    action_mask[pos_node_mapping[pos]][idx] = 1 # valid action in action space
                    piece_id = ACTIONSPACE_INV[idx]
                    tile_name = piece_id + '_p' + str(p)
                    tile_obj = state['name_obj_mapping'][tile_name]
                    player_hand = state[f'player{p}_hand']
                    
                    tile_placed = True
                    if tile_obj in player_hand:
                        tile_placed=False
                    
                    if not tile_placed:
                        if pos != (0, 0):
                        # add bidirectional edge to represent tile adjacency
                            if p == player:
                                node_features[pos_node_mapping[pos]][23] = 1
                            else:
                                node_features[pos_node_mapping[pos]][23] = -1

                    else:
                        # add unidirectional edge to represent move
                        edges[0].append(pos_node_mapping[tile_obj.position])
                        edges[1].append(pos_node_mapping[pos])
                        edge_features.append([-1])

        # create global feature vector representing player hands
        player_hand = state[f'player{p}_hand']
        for tile in player_hand:
            idx = ACTIONSPACE.get(tile.name.split('_')[0])
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
    return GraphState(Data(x=x, edge_index=edge_index, edge_attr=edge_attr, u=u), u, action_mask, pos_node_mapping)
