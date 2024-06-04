from collections import defaultdict
from pieces import Ant, Beetle, Grasshopper, Spider, Queen


class HiveBoard():
    def __init__(self) -> None:
        self.tile_positions  = defaultdict(set) # mapping from board position to tile objects
        self.name_obj_mapping = {} # mapping from tile name to object
        
        # create and fill hands for both players and fill name obj mapping
        self.player1_hand = set()
        self.player2_hand = set()
        self.fill_hand(self.player1_hand, 1)
        self.fill_hand(self.player2_hand, 2)

        # initialise turn counters
        self.player_turns = [0, 0]

        # initialise booleans to store whether queens have been placed
        self.queens_placed = [False, False]

    def get_tile(self, position):
        '''Returns the tiles at the given position, or None if there is no tile there.'''
        if position not in self.tile_positions:
            return None
        else:
            return self.tile_positions[position]

    def place_tile(self, tile, position):
        self.tile_positions[position].add(tile)
        tile.position = position
        self.update_edges(tile)
        
        # remove tile from hand
        if tile.player == 1:
            self.player1_hand.discard(tile)
        else:
            self.player2_hand.discard(tile)
        
        if 'queen' in tile.name:
            self.queens_placed[tile.player-1] = True

    def move_tile(self, tile, new_position):
        # remove tile from old position
        self.tile_positions[tile.position].discard(tile)
        if len(self.tile_positions[tile.position]) == 0:
            del self.tile_positions[tile.position]
        
        # add tile to new position
        self.tile_positions[new_position].add(tile)
        tile.position = new_position
        self.update_edges(tile)
    
    def fill_hand(self, hand, player):
        for i in range(3):
            hand.add(Ant(player, i+1))
            self.name_obj_mapping[hand[-1].name] = hand[-1]
            hand.add(Grasshopper(player, i+1))
            self.name_obj_mapping[hand[-1].name] = hand[-1]
        for i in range(2):
            hand.add(Beetle(player, i+1))
            self.name_obj_mapping[hand[-1].name] = hand[-1]
            hand.add(Spider(player, i+1))
            self.name_obj_mapping[hand[-1].name] = hand[-1]
        hand.add(Queen(player, 1))
        self.name_obj_mapping[hand[-1].name] = hand[-1]

    
    def valid_placement(self, tile, position, player):
        '''Returns True if the tile can be placed at the given position, False otherwise.'''
        if position in self.tile_positions:
            return False
        return True
    
    def valid_move(self, tile, new_position, player):
        '''Returns True if the tile can be moved to the given position, False otherwise.'''
        if new_position in self.tile_positions:
            return False
        return True
    
    def execute_move_cli(self, tile_name, move_type, player, new_position=None):
        '''Executes a move for the given player.'''
        tile = self.name_obj_mapping[tile_name]
        turns = self.player_turns[player-1]
        queen_placed = self.queens_placed[player-1]

        if queen_placed == False:
            if move_type != 'place':
                print('Cannot move before placing queen')
                return False
            if tile.name != 'queen' and turns == 2:
                print('Must place queen within first 3 turns') 
                return False
        
        if move_type == 'place':
            if tile not in self.player1_hand and player == 1:
                print('Tile not in hand')
                return False
            elif tile not in self.player2_hand and player == 2:
                print('Tile not in hand')
                return False
            elif self.valid_placement(tile, new_position, player):
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
    
    def update_edges(self, tile):
        '''Updates the edges of the tile based on its position.'''
        pos = tile.position
        neighbouring_positions = [(pos[0], pos[1]+1), (pos[0]+1, pos[1]), (pos[0]+1, pos[1]-1), 
                                  (pos[0], pos[1]-1), (pos[0]-1, pos[1]), (pos[0]-1, pos[1]+1)]                 
        
        for i, npos in enumerate(neighbouring_positions):
            ntile = self.get_tile(npos)
            tile.neighbours[i] = ntile

            
