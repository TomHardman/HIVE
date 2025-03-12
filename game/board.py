from collections import defaultdict
from .pieces import Ant, Beetle, Grasshopper, Spider, Queen
from .ACTIONSPACE import ACTIONSPACE, ACTIONSPACE_INV
import copy

# Precompute neighbor position deltas for optimization
NEIGHBOR_DELTAS = [(0, 1), (1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1)]

# Global transposition tables for AI search optimization
# These persist across all board instances and search tree
_GLOBAL_MOVE_CACHE = {}
_GLOBAL_CONNECTIVITY_CACHE = {}


class HiveBoard():
    def __init__(self, max_turns=None, simplified_game=False) -> None:
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

        # to stop game after certain number of turns
        self.max_turns = max_turns

        # ends game once player gets two pieces around opposing queen
        self.simplified_game = simplified_game
        
        # Local caches for valid moves and connectivity checks
        self._move_cache = {}
        self._connectivity_cache = {}
        
        # Control flag for cache invalidation during AI search
        # Set to False during minimax to preserve cached results
        self._invalidate_global_cache = True

    def set_cache_invalidation(self, invalidate: bool):
        """
        Set whether global caches should be invalidated when board state changes.
        Used by AI search algorithms to preserve cached results across the search tree.
        
        Args:
            invalidate: If True, global caches will be invalidated. If False, they will be preserved.
        """
        self._invalidate_global_cache = invalidate
    
    def get_player_turn(self):
        if self.player_turns[0] == self.player_turns[1]:
            return 1
        else:
            return 2
            
    def get_neighbors(self, position):
        """Returns the neighboring positions for a given position."""
        return [(position[0] + dx, position[1] + dy) for dx, dy in NEIGHBOR_DELTAS]

    def get_tile_stack(self, position):
        '''Returns the tiles at the given position, or None if there is no tile there.'''
        if position not in self.tile_positions:
            return None
        else:
            return self.tile_positions[position]

    def place_tile(self, tile, position: tuple, update_turns: bool = True):
        """Places a tile at the given position on the board. Player
        turns only updated if update_turns is set to true"""
        # Invalidate local caches
        self._move_cache = {}
        self._connectivity_cache = {}
        
        # Invalidate global caches if enabled
        if self._invalidate_global_cache:
            global _GLOBAL_MOVE_CACHE, _GLOBAL_CONNECTIVITY_CACHE
            _GLOBAL_MOVE_CACHE = {}
            _GLOBAL_CONNECTIVITY_CACHE = {}
        self.tile_positions[position].append(tile)
        tile.position = position
        
        # remove tile from hand and update turns
        if tile.player == 1:
            self.player1_hand.discard(tile)
            self.pieces_remaining[0][tile.insect] -= 1
            if update_turns:
                self.player_turns[0] += 1
        else:
            self.player2_hand.discard(tile)
            self.pieces_remaining[1][tile.insect] -= 1
            if update_turns:
                self.player_turns[1] += 1
        
        if 'queen' in tile.name:
            self.queen_positions[tile.player-1] = position

    def move_tile(self, tile, new_position: tuple, update_turns: bool = False):
        """Moves a tile to a new position on the board. Player turns
        are only updated if update turns is set to true"""
        # Invalidate local caches
        self._move_cache = {}
        self._connectivity_cache = {}
        
        # Invalidate global caches if enabled
        if self._invalidate_global_cache:
            global _GLOBAL_MOVE_CACHE, _GLOBAL_CONNECTIVITY_CACHE
            _GLOBAL_MOVE_CACHE = {}
            _GLOBAL_CONNECTIVITY_CACHE = {}
        
        # remove tile from old position
        self.tile_positions[tile.position].remove(tile)
        if len(self.tile_positions[tile.position]) == 0:
            del self.tile_positions[tile.position]
        
        # add tile to new position
        self.tile_positions[new_position].append(tile)
        tile.position = new_position

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
        npos_arr = self.get_neighbors(pos)
        
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
            npos_arr = self.get_neighbors(pos)
            for npos in npos_arr:
                if self.get_tile_stack(npos) == None and npos not in seen:
                    valid = True
                    seen.add(npos)
                    nnpos_arr = self.get_neighbors(npos)
                    
                    for nnpos in nnpos_arr:
                        if self.get_tile_stack(nnpos) and self.get_tile_stack(nnpos)[-1].player != player:
                            valid = False
                            break
                    
                    if valid:
                        valid_placements.add(npos)
        
        return valid_placements
    
    def check_unconnected(self, dummy_pos=None):
        """
        Returns True if the board is in an unconnected state, False otherwise.
        Performs a depth-first search to check if all tiles are connected.
        When dummy_pos is provided, this is when a piece is being moved to a
        very far away dummy position to check if its removal breaks the hive.
        In this scenario we don't want to begin our dfs from the dummy position
        and must account for it when checking connectedness.
        """
        # Generate a comprehensive hash of the current board state
        # This captures not just which positions are occupied, but by what pieces
        board_state = []
        for pos, tiles in self.tile_positions.items():
            # Include position and all pieces at that position (preserving stack order)
            board_state.append((pos, tuple(tile.name for tile in tiles)))
        
        # Convert to frozenset for hashability
        board_hash = frozenset(board_state)
        
        # Check local cache first
        if dummy_pos is None and board_hash in self._connectivity_cache:
            return self._connectivity_cache[board_hash]
        
        # Then check global cache
        if dummy_pos is None and board_hash in _GLOBAL_CONNECTIVITY_CACHE:
            # Store in local cache for faster future access
            self._connectivity_cache[board_hash] = _GLOBAL_CONNECTIVITY_CACHE[board_hash]
            return _GLOBAL_CONNECTIVITY_CACHE[board_hash]
        seen = set()
        stack = [list(self.tile_positions.keys())[0]] # start search from a single position
        if stack[0] == dummy_pos:
            stack = [list(self.tile_positions.keys())[1]]
        connected = False
        
        while stack:
            pos = stack.pop()
            seen.add(pos)
            npos_arr = self.get_neighbors(pos)
            
            for npos in npos_arr:
                if self.get_tile_stack(npos) and npos not in seen: # if tiles exists at npos and hasn't been visited
                    stack.append(npos)
        
        if len(seen) == len(self.tile_positions):
            connected = True
        
        elif dummy_pos and len(seen) == len(self.tile_positions) - 1:
            connected = True
        
        # Cache the result both locally and globally if not using a dummy position
        if dummy_pos is None:
            result = not connected
            self._connectivity_cache[board_hash] = result
            _GLOBAL_CONNECTIVITY_CACHE[board_hash] = result
            return result
        else:
            return not connected
                   
    def valid_move(self, tile, new_position, player):
        '''Returns True if the tile can be moved to the given position, False otherwise.'''
        # Generate a comprehensive cache key based on tile and complete board state
        # This captures not just occupied positions but what pieces are where
        board_state = []
        for pos, tiles in self.tile_positions.items():
            # Include position and all pieces at that position (preserving stack order)
            board_state.append((pos, tuple(tile.name for tile in tiles)))
        
        # The cache key combines the specific tile and the complete board state
        cache_key = (tile.name, frozenset(board_state))
        print("Cache Length;")
        print(len(_GLOBAL_MOVE_CACHE))
        
        # Check local cache first
        if cache_key in self._move_cache:
            valid_moves = self._move_cache[cache_key]
        # Then check global cache
        elif cache_key in _GLOBAL_MOVE_CACHE:
            valid_moves = _GLOBAL_MOVE_CACHE[cache_key]
            # Store in local cache for faster future access
            self._move_cache[cache_key] = valid_moves
        else:
            # Calculate and cache the valid moves
            valid_moves = tile.get_valid_moves()
            self._move_cache[cache_key] = valid_moves
            _GLOBAL_MOVE_CACHE[cache_key] = valid_moves
            
        if new_position in valid_moves:
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
                
    def game_over(self):
        """
        Checks if the game is over due to one player surrounding the other's Queen or
        a stalemate where neither play can move 
        """
        surrounding = [0, 0] # pieces surround p1 queen and p2 queen
        surrounded = False
        
        for i, pos in enumerate(self.queen_positions):
            if pos: # if queen has been placed
                pieces_surrounding = 6
                npos_arr = self.get_neighbors(pos)
                
                surrounded = True
                for npos in npos_arr:
                    if self.get_tile_stack(npos) == None:
                        surrounded = False
                        pieces_surrounding -= 1
                
                surrounding[i] = pieces_surrounding
                
            if surrounded: # return player number of opposing player if queen is surrounded
                return 2 if i == 0 else 1
        
        if self.simplified_game:
            if surrounding[0] >= 3 and 3 > surrounding[1]:
                return 1
            elif surrounding[1] >= 3 and 3 > surrounding[0]:
                return 2
                
        if self.max_turns and self.player_turns[0] >= self.max_turns and self.player_turns[1] >= self.max_turns:
            if surrounding[0] > surrounding[1]:
                return 1
            elif surrounding[0] < surrounding[1]:
                return 2
            else:
                return f'Draw {surrounding[0]}, {surrounding[1]}'

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
        by agent
        """
        # Use simple list copies for primitive data instead of deep copies
        game_state = {'player_turns': list(self.player_turns),  # Simple list copy
                      'queen_positions': list(self.queen_positions),  # Simple list copy
                      'tile_positions': copy.deepcopy(self.tile_positions),  # Still need deepcopy for complex structure
                      'valid_moves_p1': self.get_legal_actions(1),
                      'valid_moves_p2': self.get_legal_actions(2),
                      'winner': self.game_over()}

        # Record in terms of indexes relating to tile position - this avoids having to reference tile objects
        idx_pos_mapping= {}
        for pos, tiles in self.tile_positions.items():
            for tile in tiles:
                idx = ACTIONSPACE[tile.name.split('_')[0]]
                if tile.player != player:
                    idx = idx + 11
                idx_pos_mapping[idx] = pos

        p1_hand = [ACTIONSPACE[tile.name.split('_')[0]] for tile in self.player1_hand]
        p2_hand = [ACTIONSPACE[tile.name.split('_')[0]] for tile in self.player2_hand]

        game_state['player1_hand'] = p1_hand
        game_state['player2_hand'] = p2_hand
        game_state['idx_pos_mapping'] = idx_pos_mapping

        return game_state

    def load_state(self, state: dict):
        """Loads a game state from state dictionary"""
        # Invalidate local caches
        self._move_cache = {}
        self._connectivity_cache = {}
        
        # Invalidate global caches if enabled
        if self._invalidate_global_cache:
            global _GLOBAL_MOVE_CACHE, _GLOBAL_CONNECTIVITY_CACHE
            _GLOBAL_MOVE_CACHE = {}
            _GLOBAL_CONNECTIVITY_CACHE = {}
        
        # clear current tile positions and player hands
        self.tile_positions.clear()
        self.player1_hand.clear()
        self.player2_hand.clear()
        self.fill_hand(self.player1_hand, 1)
        self.fill_hand(self.player2_hand, 2)
        self.pieces_remaining = [{'ant': 3, 
                                  'beetle': 2, 
                                  'grasshopper': 3, 
                                  'spider': 2, 
                                  'queen': 1} 
                                for _ in range(2)]
        
        self.queen_positions = state['queen_positions'].copy()
        self.player_turns = state['player_turns'].copy()
        tile_positions = state['tile_positions']
        for pos, tiles in tile_positions.items(): # iterate through tile positions and place tiles
            for tile in tiles:
                tile_name = tile.name
                tile_obj = self.name_obj_mapping[tile_name]
                self.place_tile(tile_obj, pos, update_turns=False)
    
    def undo_move(self, tile, old_position=None):
        """Undoes a move"""
        # Invalidate local caches
        self._move_cache = {}
        self._connectivity_cache = {}
        
        # Invalidate global caches if enabled
        if self._invalidate_global_cache:
            global _GLOBAL_MOVE_CACHE, _GLOBAL_CONNECTIVITY_CACHE
            _GLOBAL_MOVE_CACHE = {}
            _GLOBAL_CONNECTIVITY_CACHE = {}
        if old_position == None: # tile was placed
            self.tile_positions[tile.position].pop()
            if len(self.tile_positions[tile.position]) == 0:
                del self.tile_positions[tile.position]
            tile.position = None
            if tile.player == 1:
                self.player1_hand.add(tile)
                self.pieces_remaining[0][tile.insect] += 1
            else:
                self.player2_hand.add(tile)
                self.pieces_remaining[1][tile.insect] += 1
        
        else: # tile was moved
            self.move_tile(tile, old_position, update_turns=False)
        
        self.player_turns[tile.player-1] -= 1