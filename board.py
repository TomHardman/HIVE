from collections import defaultdict
from pieces import Ant, Beetle, Grasshopper, Spider, Queen
import copy


ACTIONSPACE  = {'queen1': 0,
                'spider1': 1,
                'spider2': 2,
                'beetle1': 3,
                'beetle2': 4,
                'ant1': 5,
                'ant2': 6,
                'ant3': 7,
                'grasshopper1': 8,
                'grasshopper2': 9,
                'grasshopper3': 10}

ACTIONSPACE_INV = {v: k for k, v in ACTIONSPACE.items()}


class HiveBoard():
    def __init__(self) -> None:
        self.tile_positions  = defaultdict(list) # mapping from board position to tile objects
        self.name_obj_mapping = {} # mapping from tile name to object
        
        # create and fill hands for both players and fill name obj mapping
        self.player1_hand = set()
        self.player2_hand = set()
        self.fill_hand(self.player1_hand, 1)
        self.fill_hand(self.player2_hand, 2)
        self.pieces_remaining = [{'ant': 3, 
                                  'beetle': 2, 
                                  'grasshopper': 3, 
                                  'spider': 2, 
                                  'queen': 1} 
                                for _ in range(2)] # store number of pieces remaining for each player

        # initialise turn counters
        self.player_turns = [0, 0]

        # initialise booleans to store queen positions
        self.queen_positions = [None, None]
    
    def get_player_turn(self):
        if self.player_turns[0] == self.player_turns[1]:
            return 1
        else:
            return 2

    def get_tile_stack(self, position):
        '''Returns the tiles at the given position, or None if there is no tile there.'''
        if position not in self.tile_positions:
            return None
        else:
            return self.tile_positions[position]

    def place_tile(self, tile, position):
        self.tile_positions[position].append(tile)
        tile.position = position
        self.update_edges(tile)
        
        # remove tile from hand and update turns
        if tile.player == 1:
            self.player1_hand.discard(tile)
            self.pieces_remaining[0][tile.insect] -= 1
            self.player_turns[0] += 1
        else:
            self.player2_hand.discard(tile)
            self.pieces_remaining[1][tile.insect] -= 1
            self.player_turns[1] += 1
        
        if 'queen' in tile.name:
            self.queen_positions[tile.player-1] = position

    def move_tile(self, tile, new_position, update_turns=False):
        """Moves a tile to a new position on the board. Player turns
        are only updated if update turns is set to true"""
        # remove tile from old position
        self.tile_positions[tile.position].remove(tile)
        if len(self.tile_positions[tile.position]) == 0:
            del self.tile_positions[tile.position]
        
        # add tile to new position
        self.tile_positions[new_position].append(tile)
        tile.position = new_position
        self.update_edges(tile)

        # when called from GUI we want this method to update player turns
        if update_turns:
            player = tile.player
            self.player_turns[player - 1] += 1
        
        if tile.name.split('_')[0][:-1] == 'queen':
            self.queen_positions[tile.player-1] = new_position
    
    def fill_hand(self, hand, player):
        '''Fills the hand of the given player with three ants,
        three grasshoppers, two beetles, two spiders, and one queen.'''
        
        for i in range(3):
            ant = Ant(player, i+1, self)
            hand.add(ant)
            self.name_obj_mapping[ant.name] = ant
            grasshopper = Grasshopper(player, i+1, self)
            hand.add(grasshopper)
            self.name_obj_mapping[grasshopper.name] = grasshopper
        for i in range(2):
            beetle = Beetle(player, i+1, self)
            hand.add(beetle)
            self.name_obj_mapping[beetle.name] = beetle
            spider = Spider(player, i+1, self)
            hand.add(spider)
            self.name_obj_mapping[spider.name] = spider
        queen = Queen(player, 1, self)
        hand.add(queen)
        self.name_obj_mapping[queen.name] = queen

    def valid_placement(self, pos, player):
        '''Returns True if the tile can be placed at the given position, False otherwise.'''
        valid = True
        connected = False
        npos_arr = [(pos[0], pos[1]+1), (pos[0]+1, pos[1]), (pos[0]+1, pos[1]-1), # neighbouring positions
                    (pos[0], pos[1]-1), (pos[0]-1, pos[1]), (pos[0]-1, pos[1]+1)]
        
        if self.player_turns[player - 1] == 0: # first turn for second player must be adjacent to first player's tile
            for npos in npos_arr:
                if self.get_tile_stack(npos) and self.get_tile_stack(npos)[-1].player != player:
                    return True
            return False
        
        for npos in npos_arr:
            if self.get_tile_stack(npos):
                connected = True

                if self.get_tile_stack(npos)[-1].player != player: # check for neighbouring opposing player tiles
                    valid = False
                    break
                    
        return connected and valid
         
    def get_valid_placements(self, player, insect):
        '''Returns list of all valid placement positions for a given player'''
        valid_placements = set()
        seen = set()

        if not self.pieces_remaining[player - 1][insect]:
            return []

        if not any(self.player_turns): # first turn can be anywhere
            return [(0, 0)] # first tile placed at (0, 0)

        elif self.player_turns[player-1] == 0: # first turn for second player must be adjacent to first player's tile
            return [(0, 1), (1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1)]
        
        # Queen must be placed within first three turns
        elif self.pieces_remaining[player - 1]['queen'] == 1 and self.player_turns[player-1] == 2:
            if insect != 'queen':
                return []

        for pos in self.tile_positions:
            npos_arr = [(pos[0], pos[1]+1), (pos[0]+1, pos[1]), (pos[0]+1, pos[1]-1), 
                        (pos[0], pos[1]-1), (pos[0]-1, pos[1]), (pos[0]-1, pos[1]+1)]
            for npos in npos_arr:
                if self.get_tile_stack(npos) == None and npos not in seen:
                    valid = True
                    seen.add(npos)
                    nnpos_arr = [(npos[0], npos[1]+1), (npos[0]+1, npos[1]), (npos[0]+1, npos[1]-1), 
                                 (npos[0], npos[1]-1), (npos[0]-1, npos[1]), (npos[0]-1, npos[1]+1)]
                    
                    for nnpos in nnpos_arr:
                        if self.get_tile_stack(nnpos) and self.get_tile_stack(nnpos)[-1].player != player:
                            valid = False
                            break
                    
                    if valid:
                        valid_placements.add(npos)
        
        return valid_placements
    
    def check_unconnected(self):
        """
        Returns True if the board is in an unconnected state, False otherwise.
        Performs a depth-first search to check if all tiles are connected.
        """
        seen = set()
        stack = [list(self.tile_positions.keys())[0]] # start search from a single position
        connected = False
        
        while stack:
            pos = stack.pop()
            seen.add(pos)
            npos_arr = [(pos[0], pos[1]+1), (pos[0]+1, pos[1]), (pos[0]+1, pos[1]-1), 
                        (pos[0], pos[1]-1), (pos[0]-1, pos[1]), (pos[0]-1, pos[1]+1)]
            
            for npos in npos_arr:
                if self.get_tile_stack(npos) and npos not in seen: # if tiles exists at npos and hasn't been visited
                    stack.append(npos)
        
        if len(seen) == len(self.tile_positions):
            connected = True
        
        return not connected
                   
    def valid_move(self, tile, new_position, player):
        '''Returns True if the tile can be moved to the given position, False otherwise.'''
        if new_position in tile.get_valid_moves():
            return True
        return False
    
    def execute_move_cli(self, tile_name, move_type, player, new_position=None):
        '''Executes a move for the given player (when using command line interface)'''
        
        if tile_name not in self.name_obj_mapping:
            print('Invalid tile name')
            return False

        tile = self.name_obj_mapping[tile_name]
        turns = self.player_turns[player-1]
        queen_placed = self.pieces_remaining[player - 1]['queen'] == 0

        if queen_placed == False:
            if move_type != 'place':
                print('Cannot move before placing queen')
                return False
            if 'queen' not in tile.name and turns == 2:
                print('Must place queen within first 3 turns') 
                return False
        
        if move_type == 'place':
            if not new_position:
                print('No position given')
                return False
            if tile not in self.player1_hand and player == 1:
                print('Tile not in hand')
                return False
            elif tile not in self.player2_hand and player == 2:
                print('Tile not in hand')
                return False
            elif self.valid_placement(new_position, player):
                self.place_tile(tile, new_position)
            else:
                print('Invalid placement')
                return False
        
        elif move_type == 'move':
            if self.valid_move(tile, new_position, player):
                self.move_tile(tile, new_position)
            else:
                print('Invalid move')
                return False
        else:
            print('Invalid move type')
            return False
        
        print('Move successful')
        self.player_turns[player-1] += 1
        return True
    
    def update_edges(self, tile, recursed=False):
        '''Updates the edges of the tile based on its position.'''
        pos = tile.position
        neighbouring_positions = [(pos[0], pos[1]+1), (pos[0]+1, pos[1]), (pos[0]+1, pos[1]-1), 
                                  (pos[0], pos[1]-1), (pos[0]-1, pos[1]), (pos[0]-1, pos[1]+1)]            
        
        for i, npos in enumerate(neighbouring_positions):
            ntile = self.get_tile_stack(npos)
            tile.neighbours[i] = ntile
            
            if ntile and recursed==False: # update neighbour's edges
                for tile_n in ntile:
                    self.update_edges(tile_n, True)
                
    
    def game_over(self):
        """
        Checks if the game is over due to one player surrounding the other's Queen or
        a stalemate where neither play can move
        """
        
        for i, pos in enumerate(self.queen_positions):
            if pos: # if queen has been placed
                npos_arr = [(pos[0], pos[1]+1), (pos[0]+1, pos[1]), (pos[0]+1, pos[1]-1), 
                            (pos[0], pos[1]-1), (pos[0]-1, pos[1]), (pos[0]-1, pos[1]+1)]
                
                surrounded = True
                for npos in npos_arr:
                    if self.get_tile_stack(npos) == None:
                        surrounded = False
                        break
                
                if surrounded: # return player number of opposing player if queen is surrounded
                    return 2 if i == 0 else 1
        
        p1_actions = self.get_legal_actions(1)
        p2_actions = self.get_legal_actions(2)

        if not any(p1_actions.values()) and not any(p2_actions.values()): # stalemate
            return 0
        
        return False
    

    def get_legal_actions(self, player):
        '''Returns a list of all legal actions for the given player
        Action space is represented as a dictionary mapping each board
        position to an array of possible moves. Each array index represents
        placing/moving a different tile at/to that position.'''
        legal_actions = defaultdict(list)
        player_tiles = []

        for tile in self.name_obj_mapping.values():
            if tile.player == player:
                player_tiles.append(tile)
        
        for tile in player_tiles:
            if tile in self.player1_hand or tile in self.player2_hand:
                for pos in self.get_valid_placements(player, tile.insect):
                    legal_actions[pos].append(tile)
            else:
                for pos in tile.get_valid_moves():
                    legal_actions[pos].append(tile)
        
        # map tiles at each position to array of indices
        for pos, tiles in legal_actions.items():
            moves = [False for i in range(11)]
            for tile in tiles:
                idx = ACTIONSPACE[tile.name.split('_')[0]]
                moves[idx] = True
            legal_actions[pos] = moves
        
        return legal_actions
    

    def get_game_state(self, player):
        """
        Returns the current game state as a dictionary - to be used 
        by the RL agent 
        """
        game_state = {'player1_hand': self.player1_hand.copy(),
                      'player2_hand': self.player2_hand.copy(),
                      'player_turns': self.player_turns.copy(),
                      'queen_positions': copy.deepcopy(self.queen_positions),
                      'tile_positions': copy.deepcopy(self.tile_positions),
                      'valid_moves_p1': self.get_legal_actions(1),
                      'valid_moves_p2': self.get_legal_actions(2),
                      'winner': self.game_over(),
                      'name_obj_mapping': self.name_obj_mapping}
        return game_state

            
