from collections import defaultdict
from pieces import Ant, Beetle, Grasshopper, Spider, Queen


class HiveBoard():
    def __init__(self) -> None:
        self.tile_positions  = defaultdict(list) # mapping from board position to tile objects
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
        self.queen_positions = [None, None]

    def get_tile(self, position):
        '''Returns the tiles at the given position, or None if there is no tile there.'''
        if position not in self.tile_positions:
            return None
        else:
            return self.tile_positions[position]

    def place_tile(self, tile, position):
        self.tile_positions[position].append(tile)
        tile.position = position
        self.update_edges(tile)
        
        # remove tile from hand
        if tile.player == 1:
            self.player1_hand.discard(tile)
        else:
            self.player2_hand.discard(tile)
        
        if 'queen' in tile.name:
            self.queens_placed[tile.player-1] = True
            self.queen_positions[tile.player-1] = position

    def move_tile(self, tile, new_position):
        old_pos = tile.position

        # remove tile from old position
        self.tile_positions[tile.position].remove(tile)
        if len(self.tile_positions[tile.position]) == 0:
            del self.tile_positions[tile.position]
        
        # add tile to new position
        self.tile_positions[new_position].append(tile)
        tile.position = new_position
        self.update_edges(tile, old_Pos)
    
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
        
        if not any(self.player_turns): # first turn can be anywhere
            return True
        
        elif self.player_turns[player - 1] == 0: # first turn for second player must be adjacent to first player's tile
            for npos in npos_arr:
                if self.get_tile(npos) and self.get_tile(npos)[-1].player != player:
                    return True
            return False
        
        for npos in npos_arr:
            if self.get_tile(npos):
                connected = True

                if self.get_tile(npos)[-1].player != player: # check for neighbouring opposing player tiles
                    valid = False
                    break
                    
        return connected and valid
         
    def get_valid_placements(self, player):
        '''Returns list of all valid placement positions for a given player'''
        valid_placements = set()
        seen = set()

        for pos in self.tile_positions:
            npos_arr = [(pos[0], pos[1]+1), (pos[0]+1, pos[1]), (pos[0]+1, pos[1]-1), 
                        (pos[0], pos[1]-1), (pos[0]-1, pos[1]), (pos[0]-1, pos[1]+1)]
            for npos in npos_arr:
                if self.get_tile(npos) == None and npos not in seen:
                    valid = True
                    seen.add(npos)
                    nnpos_arr = [(npos[0], npos[1]+1), (npos[0]+1, npos[1]), (npos[0]+1, npos[1]-1), 
                                 (npos[0], npos[1]-1), (npos[0]-1, npos[1]), (npos[0]-1, npos[1]+1)]
                    
                    for nnpos in nnpos_arr:
                        if self.get_tile(nnpos) and self.get_tile(nnpos)[-1].player != player:
                            valid = False
                            break
                    
                    if valid:
                        valid_placements.add(npos)
        
        return valid_placements
    
    def check_unconnected(self):
        '''Returns True if the board is in an unconnected state, False otherwise.
        Performs a depth-first search to check if all tiles are connected.'''
        seen = set()
        stack = [list(self.tile_positions.keys())[0]] # start search from a single position
        connected = False
        
        while stack:
            pos = stack.pop()
            seen.add(pos)
            npos_arr = [(pos[0], pos[1]+1), (pos[0]+1, pos[1]), (pos[0]+1, pos[1]-1), 
                        (pos[0], pos[1]-1), (pos[0]-1, pos[1]), (pos[0]-1, pos[1]+1)]
            
            for npos in npos_arr:
                if self.get_tile(npos) and npos not in seen: # if tiles exists at npos and hasn't been visited
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
        queen_placed = self.queens_placed[player-1]

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
            ntile = self.get_tile(npos)
            tile.neighbours[i] = ntile
            
            if ntile and recursed==False: # update neighbour's edges
                for tile_n in ntile:
                    self.update_edges(tile_n, True)
                
    
    def game_over(self):
        '''Checks if the game is over (queen surrounded) and returns the player
        number of the victor if so'''
        
        for i, pos in enumerate(self.queen_positions):
            if pos: # if queen has been placed
                npos_arr = [(pos[0], pos[1]+1), (pos[0]+1, pos[1]), (pos[0]+1, pos[1]-1), 
                            (pos[0], pos[1]-1), (pos[0]-1, pos[1]), (pos[0]-1, pos[1]+1)]
                
                surrounded = True
                for npos in npos_arr:
                    if self.get_tile(npos) == None:
                        surrounded = False
                        break
                
                if surrounded: # return player number of opposing player if queen is surrounded
                    return 2 if i == 0 else 1
        
        return False