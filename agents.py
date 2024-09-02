import random
from abc import ABC, abstractmethod

from rl_helper import get_graph_from_state
from board import ACTIONSPACE_INV
from networks import DQN
from board import HiveBoard

import torch


class Agent(ABC):
    """Interface for agents to implement."""
    @abstractmethod
    def sample_action(self):
        pass

    @abstractmethod
    def set_board(self, board):
        pass


class RandomAgent(Agent):
    def __init__(self, player, board=None):
        self.player = player
        self.board = board
    
    def set_board(self, board):
        self.board = board

    def sample_action(self):
        """
        Get possible actions from board and randomly sample an action.
        Action space is represented as a dictionary mapping each board
        position to an array of possible moves. Each array index represents
        placing/moving a different tile at/to that position. If the tile
        has not yet been placed this is performed as a placement and if
        the tile has been placed this is performed as a movement.
        """
        # gets possible actions from board
        actions = self.board.get_legal_actions(self.player)

        action_set = set()
        
        for pos in actions:
            for tile_idx in range(len(actions[pos])):
                if actions[pos][tile_idx] == True:
                    action_set.add((pos, tile_idx))
        
        if action_set:
            # randomly sample an action
            action = random.choice(list(action_set))

            # get tile object and position
            pos = action[0]
            tile_idx = action[1]
            piece_id = ACTIONSPACE_INV[tile_idx]
            tile_name = piece_id + '_p' + str(self.player)
            tile_obj = self.board.name_obj_mapping[tile_name]
            
            # work out if piece to be moved has been placed or not
            if tile_obj not in self.board.player1_hand and tile_obj not in self.board.player2_hand:
                self.board.move_tile(tile_obj, pos, update_turns=True)
            
            else:
                self.board.place_tile(tile_obj, pos)
            
            return action
        
        else: # if no possible actions increment turn count and return False
            self.board.player_turns[self.player-1] += 1
            print('No possible actions for agent')
            return False
        

class RLAgent(Agent):
    def __init__(self, player: int, q_network: DQN, epsilon: float, 
                 board=None, reduced=False):
        self.player = player
        self.board = board
        self.epsilon = epsilon # for epsilon greedy policy
        self.q_network = q_network
        self.reduced = reduced
    
    def set_board(self, board: HiveBoard):
        self.board = board

    def sample_action(self):
        """
        Sample using epsilon greedy policy
        """

        random_num = random.random()
        if random_num < self.epsilon:
            action = self.get_random_action()
            if action:
                pos, tile_idx = action[0], action[1]

        else:
            # get graph state from board
            state = self.board.get_game_state(self.player)
            gs = get_graph_from_state(state, self.player, reduced=self.reduced)
            pos_node_mapping = gs.pos_node_mapping
            pos_node_mapping_rev = {v: k for k, v in pos_node_mapping.items()}

            if torch.max(gs.action_mask) == 0:
                self.board.player_turns[self.player-1] += 1
                print('No possible actions for agent')
                return False
            
            # get masked Q values from model
            masked_q_values = self.q_network.forward(gs)
            
            # get best action
            action_idx = torch.argmax(masked_q_values).item()
            
            # get action
            pos = pos_node_mapping_rev[action_idx//11]
            tile_idx = action_idx % 11
            action = (pos, tile_idx)

        if action:
            # get tile object
            piece_id = ACTIONSPACE_INV[tile_idx]
            tile_name = piece_id + '_p' + str(self.player)
            tile_obj = self.board.name_obj_mapping[tile_name]
            
            # work out if piece to be moved has been placed or not
            if tile_obj not in self.board.player1_hand and tile_obj not in self.board.player2_hand:
                self.board.move_tile(tile_obj, pos, update_turns=True)
            
            else:
                self.board.place_tile(tile_obj, pos)

        else: 
            self.board.player_turns[self.player-1] += 1
            print('No possible actions for agent')
            return False
        
        return action
    
    def get_random_action(self):
        actions = self.board.get_legal_actions(self.player)
        action_set = set()
        
        for pos in actions:
            for tile_idx in range(len(actions[pos])):
                if actions[pos][tile_idx] == True:
                    action_set.add((pos, tile_idx))
        
        if action_set:
            # randomly sample an action
            action = random.choice(list(action_set))
        
        else:
            action = None

        return action




    
