from collections import deque
from abc import ABC, abstractmethod
import functools

# Global cache for moves across all instances and search
_TILE_MOVE_CACHE = {}


class HiveTile(ABC): # parent class for all pieces
    def __init__(self, name, player, n, board, beetle=False):
        self.player = player
        self.name = name + str(n) + '_p' + str(player)
        self.insect = name
        self.position = None
        self.is_beetle = beetle
        self.board = board
    
    def __hash__(self): # hash based on name
        return hash(self.name)
    
    def __eq__(self, other): # equality based on name
        return isinstance(other, self.__class__) and self.name == other.name
    
    def covered(self):
        '''Returns True if tile is covered by beetle and is therefore immobile.'''
        return self.board.get_tile_stack(self.position)[-1] != self # checks if top tile at current position is self
    
    def queen_placed(self):
        '''Returns True if queen has already been placed'''
        return self.board.pieces_remaining[self.player - 1]['queen'] == 0
    
    def check_slide_space(self, npos_arr, i):
        """
        Returns true if there is sufficient space to slide into empty tile at npos_arr[i], where
        npos_arr is array of neighbouring positions to tile, represented clockwise from 12 o'clock
        """
        if self.board.get_tile_stack(npos_arr[(i-1)%6]) == None or self.board.get_tile_stack(npos_arr[(i+1)%6]) == None:
            return True
        # need to make sure slide logic isn't being affected by current position of tile itself
        elif len(self.board.get_tile_stack(npos_arr[(i-1)%6])) == 1 and self.board.get_tile_stack(npos_arr[(i-1)%6])[0] == self:
            return True
        elif len(self.board.get_tile_stack(npos_arr[(i+1)%6])) == 1 and self.board.get_tile_stack(npos_arr[(i+1)%6])[0] == self:
            return True
        return False
    
    def test_breakage(self, original_pos):
        if len (self.board.tile_positions) >= 2:
            self.board.move_tile(self, (100, 100)) # test if removing from original pos breaks hive
            if self.board.check_unconnected(dummy_pos=(100, 100)):
                self.board.move_tile(self, original_pos)
                return True
            self.board.move_tile(self, original_pos)
        return False

    def _get_board_hash(self):
        """Generate a comprehensive hash of the current board state for caching"""
        board_state = []
        for pos, tiles in self.board.tile_positions.items():
            # Include position and all pieces at that position (preserving stack order)
            board_state.append((pos, tuple(tile.name for tile in tiles)))
        
        # Convert to frozenset for hashability
        return frozenset(board_state)
    
    def _cached_valid_moves(self, calculation_function):
        """
        Cache wrapper for valid moves calculations.
        Uses both local and global caches for optimal performance.
        """
        # Skip caching if piece is covered or queen not placed
        if self.covered() or not self.queen_placed():
            return set()
            
        # Create a comprehensive key that uniquely identifies this piece and board state
        board_hash = self._get_board_hash()
        cache_key = (self.name, board_hash)
        
        # Check global cache first (persists across search tree)
        print(len(_TILE_MOVE_CACHE))
        if cache_key in _TILE_MOVE_CACHE:
            return _TILE_MOVE_CACHE[cache_key]
        
        # Calculate moves if not in cache
        valid_moves = calculation_function()
        
        # Store in both caches
        _TILE_MOVE_CACHE[cache_key] = valid_moves
        
        return valid_moves
    
    @abstractmethod
    def get_valid_moves(self):
        '''Returns set of valid moves for tile'''
        pass


class Ant(HiveTile):
    def __init__(self, player, n, board):
        super().__init__('ant', player, n, board)
    
    def _calculate_valid_moves(self):
        """Actual computation function for Ant's valid moves"""
        original_pos = self.position

        if self.test_breakage(original_pos):
            return set()

        seen = set()
        valid_moves = set()
        bfs_queue = deque([original_pos])

        while bfs_queue:
            pos = bfs_queue.popleft()
            npos_arr = [(pos[0], pos[1]+1), (pos[0]+1, pos[1]), (pos[0]+1, pos[1]-1),
                        (pos[0], pos[1]-1), (pos[0]-1, pos[1]), (pos[0]-1, pos[1]+1)]
            
            for i in range(len(npos_arr)):
                if npos_arr[i] not in seen:
                    if self.board.get_tile_stack(npos_arr[i]) == None: # if there is a space to move into
                        #   check adjacent neighbours to see if sliding is possible
                        if self.check_slide_space(npos_arr, i):
                            # check whether tile can be moved without breaking one-hive rule - this applies during move
                            if self.board.get_tile_stack(npos_arr[(i-1)%6]) != self.board.get_tile_stack(npos_arr[(i+1)%6]):
                                self.board.move_tile(self, npos_arr[i])
                                if not self.board.check_unconnected():
                                    valid_moves.add(npos_arr[i])
                                    seen.add(npos_arr[i]) # only stores spaces ant has explored from
                                    bfs_queue.append(npos_arr[i]) 
                                self.board.move_tile(self, original_pos) 
        return valid_moves
    
    def get_valid_moves(self):
        """Returns set of valid moves for Ant, using caching"""
        return self._cached_valid_moves(self._calculate_valid_moves)
        

class Beetle(HiveTile):
    def __init__(self, player, n, board):
        super().__init__('beetle', player, n, board, beetle=True)
    
    def _calculate_valid_moves(self):
        """Actual computation function for Beetle's valid moves"""
        original_pos = self.position
        
        if self.test_breakage(original_pos):
            return set()

        valid_moves_temp = set()
        valid_moves = set()

        npos_arr = [(original_pos[0], original_pos[1]+1), (original_pos[0]+1, original_pos[1]), 
                    (original_pos[0]+1, original_pos[1]-1), (original_pos[0], original_pos[1]-1), 
                    (original_pos[0]-1, original_pos[1]), (original_pos[0]-1, original_pos[1]+1)]

        for i in range(len(npos_arr)):
            if self.board.get_tile_stack(npos_arr[i]) == None:
                # check adjacent neighbours to see if sliding is possible
                if self.check_slide_space(npos_arr, i):
                    # check whether tile can be moved without breaking one-hive rule - this applies during move
                    if len(self.board.get_tile_stack(original_pos)) == 1:
                        if self.board.get_tile_stack(npos_arr[(i-1)%6]) != self.board.get_tile_stack(npos_arr[(i+1)%6]):
                            valid_moves_temp.add(npos_arr[i])
                    else:
                        valid_moves_temp.add(npos_arr[i])
                
                # slide logic doesn't apply if climbing down
                elif len(self.board.get_tile_stack(original_pos)) > 1:
                    valid_moves_temp.add(npos_arr[i])

            # check sliding logic at higher level
            elif len(self.board.get_tile_stack(original_pos)) == 2 and len(self.board.get_tile_stack(npos_arr[i])) == 1:
                if self.board.get_tile_stack(npos_arr[(i-1)%6]) == None or self.board.get_tile_stack(npos_arr[(i+1)%6]) == None:
                    valid_moves_temp.add(npos_arr[i])
                elif not (len(self.board.get_tile_stack(npos_arr[(i-1)%6])) == 2 and len(self.board.get_tile_stack(npos_arr[(i-1)%6])) == 2):
                    valid_moves_temp.add(npos_arr[i])
            else:
                valid_moves_temp.add(npos_arr[i])

        
        # check if the move is valid by checking if the hive is still connected after moving
        for move in valid_moves_temp:
            self.board.move_tile(self, move)
            if not self.board.check_unconnected():
                valid_moves.add(move)
            self.board.move_tile(self, original_pos)
        
        return valid_moves
    
    def get_valid_moves(self):
        """Returns set of valid moves for Beetle, using caching"""
        return self._cached_valid_moves(self._calculate_valid_moves)


class Grasshopper(HiveTile):
    def __init__(self, player, n, board):
        super().__init__('grasshopper', player, n, board)
    
    def _calculate_valid_moves(self):
        """Actual computation function for Grasshopper's valid moves"""
        original_pos = self.position
        
        if self.test_breakage(original_pos):
            return set()

        valid_moves_temp = set() # temporary set to store valid moves before checking connectedness
        valid_moves = set()

        npos_arr = [(original_pos[0], original_pos[1]+1), (original_pos[0]+1, original_pos[1]), 
                    (original_pos[0]+1, original_pos[1]-1), (original_pos[0], original_pos[1]-1), 
                    (original_pos[0]-1, original_pos[1]), (original_pos[0]-1, original_pos[1]+1)]

        bfs_queue = deque()
        
        for pos in npos_arr:
            if self.board.get_tile_stack(pos) != None:
                bfs_queue.append(pos) # add all neighbouring tiles to the queue
        
        while bfs_queue:
            pos = bfs_queue.popleft()
            diff_1 = pos[0] - original_pos[0]
            diff_2 = pos[1] - original_pos[1]

            if diff_1 != 0:
                delta_1 = diff_1 // abs(diff_1)
            else:
                delta_1 = 0
            
            if diff_2 != 0:
                delta_2 = diff_2 // abs(diff_2)
            else:
                delta_2 = 0
            
            npos_arr = [(pos[0] + delta_1, pos[1] + delta_2)] # can only travel out in a straight line
            
            for pos in npos_arr:
                if self.board.get_tile_stack(pos) == None:
                    valid_moves_temp.add(pos) 
                else:
                    bfs_queue.append(pos)

        # check if the move is valid by checking if the hive is still connected
        for move in valid_moves_temp:
            self.board.move_tile(self, move) 
            if not self.board.check_unconnected():
                valid_moves.add(move)
            self.board.move_tile(self, original_pos)
        
        return valid_moves
    
    def get_valid_moves(self):
        """Returns set of valid moves for Grasshopper, using caching"""
        return self._cached_valid_moves(self._calculate_valid_moves)
                

class Spider(HiveTile):
    def __init__(self, player, n, board):
        super().__init__('spider', player, n, board)
    
    def _calculate_valid_moves(self):
        """Actual computation function for Spider's valid moves"""
        original_pos = self.position
        
        if self.test_breakage(original_pos):
            return set()
            
        seen = set([self.position])
        valid_moves = set()
        bfs_queue = deque([(original_pos, 0)])

        while bfs_queue:
            pos, turns = bfs_queue.popleft()
            npos_arr = [((pos[0], pos[1]+1), turns+1), ((pos[0]+1, pos[1]), turns+1), ((pos[0]+1, pos[1]-1), turns+1),
                        ((pos[0], pos[1]-1), turns+1), ((pos[0]-1, pos[1]), turns+1), ((pos[0]-1, pos[1]+1), turns+1)]
            
            for i in range(len(npos_arr)):
                if npos_arr[i][0] not in seen:
                    if self.board.get_tile_stack(npos_arr[i][0]) == None: # if there is a space to move into
                        #   check adjacent neighbours to see if there is space to slide
                        if self.check_slide_space(npos_arr, i):
                            # check whether tile can be moved without breaking one-hive rule - this applies during move
                            if self.board.get_tile_stack(npos_arr[(i-1)%6][0]) != self.board.get_tile_stack(npos_arr[(i+1)%6][0]):
                                self.board.move_tile(self, npos_arr[i][0]) 
                                if not self.board.check_unconnected():
                                    if npos_arr[i][1] == 3: # spider must move exactly 3 spaces
                                        valid_moves.add(npos_arr[i][0])
                                    elif npos_arr[i][1] < 3: # if spider hasn't moved 3 spaces yet, add to queue
                                        seen.add(npos_arr[i][0])
                                        bfs_queue.append(npos_arr[i])
                                self.board.move_tile(self, original_pos)
            
        return valid_moves
    
    def get_valid_moves(self):
        """Returns set of valid moves for Spider, using caching"""
        return self._cached_valid_moves(self._calculate_valid_moves)


class Queen(HiveTile):
    def __init__(self, player, n, board):
        super().__init__('queen', player, n, board)
    
    def _calculate_valid_moves(self):
        """Actual computation function for Queen's valid moves"""
        original_pos = self.position
        
        if self.test_breakage(original_pos):
            return set()

        valid_moves_temp = set()
        valid_moves = set()

        npos_arr = [(original_pos[0], original_pos[1]+1), (original_pos[0]+1, original_pos[1]), 
                    (original_pos[0]+1, original_pos[1]-1), (original_pos[0], original_pos[1]-1), 
                    (original_pos[0]-1, original_pos[1]), (original_pos[0]-1, original_pos[1]+1)]

        for i in range(len(npos_arr)):
            if self.board.get_tile_stack(npos_arr[i]) == None:
                # check adjacent neighbours to see if sliding is possible
                if self.board.get_tile_stack(npos_arr[(i-1)%6]) == None or self.board.get_tile_stack(npos_arr[(i+1)%6]) == None:
                    if self.board.get_tile_stack(npos_arr[(i-1)%6]) != self.board.get_tile_stack(npos_arr[(i+1)%6]):
                        valid_moves_temp.add(npos_arr[i])
        
        # check if the move is valid by checking if the hive is still connected after moving
        for move in valid_moves_temp:
            self.board.move_tile(self, move)
            if not self.board.check_unconnected():
                valid_moves.add(move)
            self.board.move_tile(self, original_pos)
        
        return valid_moves
    
    def get_valid_moves(self):
        """Returns set of valid moves for Queen, using caching"""
        return self._cached_valid_moves(self._calculate_valid_moves)

        