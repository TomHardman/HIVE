import random
from board import ACTIONSPACE_INV

"""Random Agent to play HIVE"""

class RandomAgent:
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
        
    



    
