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
        """
        Optimized version that checks if removing a piece would break the hive
        without modifying the board state
        """
        # Special case: if only 1-2 pieces on board, moving can't break connectivity
        if len(self.board.tile_positions) <= 2:
            return False
        
        # The key insight: the hive stays connected if the piece's original position
        # has at least two neighbors that are also neighbors of each other
        
        # Get occupied positions except this piece's position
        occupied = set(self.board.tile_positions.keys())
        occupied.remove(original_pos)
        
        # Get all neighbors of the original position
        neighbors = [
            (original_pos[0], original_pos[1]+1), (original_pos[0]+1, original_pos[1]),
            (original_pos[0]+1, original_pos[1]-1), (original_pos[0], original_pos[1]-1),
            (original_pos[0]-1, original_pos[1]), (original_pos[0]-1, original_pos[1]+1)
        ]
        
        # Count occupied neighbors
        occupied_neighbors = [n for n in neighbors if n in occupied]
        
        # If fewer than 2 neighbors, removing can't disconnect (already disconnected or linear)
        if len(occupied_neighbors) < 2:
            return False
            
        # Check if neighbors form a connected subgraph
        # We only need to check pairs of neighbors to see if any are adjacent
        for i in range(len(occupied_neighbors)):
            for j in range(i+1, len(occupied_neighbors)):
                if self._are_adjacent(occupied_neighbors[i], occupied_neighbors[j]):
                    return False  # Found adjacent neighbors, hive won't break
                    
        # No adjacent neighbors found, removing would break the hive
        return True

    def _are_adjacent(self, pos1, pos2):
        """Check if two positions are adjacent on the hex grid"""
        dx = pos1[0] - pos2[0]
        dy = pos1[1] - pos2[1]
        return (dx == 0 and abs(dy) == 1) or (dy == 0 and abs(dx) == 1) or (dx == dy and abs(dx) == 1)
    
    def _can_slide_to(self, from_pos, direction_index, neighbors, occupied_positions):
        """
        Check if piece can slide from from_pos to the neighbor at direction_index
        without physically moving pieces on the board.
        """
        # Get the positions to the left and right of the target position
        left_idx = (direction_index - 1) % 6
        right_idx = (direction_index + 1) % 6
        left_pos = neighbors[left_idx]
        right_pos = neighbors[right_idx]
        
        # If either side is empty, sliding is possible
        if left_pos not in occupied_positions or right_pos not in occupied_positions:
            return True
            
        # Check if the piece itself is currently at one of these positions
        if (len(self.board.get_tile_stack(left_pos) or []) == 1 and 
            self.board.get_tile_stack(left_pos)[0] == self):
            return True
            
        if (len(self.board.get_tile_stack(right_pos) or []) == 1 and 
            self.board.get_tile_stack(right_pos)[0] == self):
            return True
            
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
        """Optimized Ant move generation without temporary board state changes"""
        original_pos = self.position

        if self.test_breakage(original_pos):
            return set()

        # Get occupied positions for faster lookup
        occupied_positions = set(self.board.tile_positions.keys())
        
        # Track positions we've already processed
        seen = set([original_pos])
        valid_moves = set()
        
        # Start BFS from original position
        frontier = set([original_pos])
        next_frontier = set()
        
        # Continue BFS until no new positions can be reached
        while frontier:
            for pos in frontier:
                # Get all six neighboring positions
                neighbors = [
                    (pos[0], pos[1]+1), (pos[0]+1, pos[1]), (pos[0]+1, pos[1]-1),
                    (pos[0], pos[1]-1), (pos[0]-1, pos[1]), (pos[0]-1, pos[1]+1)
                ]
                
                # Process each neighbor
                for i, neighbor_pos in enumerate(neighbors):
                    # Skip if already processed
                    if neighbor_pos in seen:
                        continue
                    
                    # Skip if position is occupied
                    if neighbor_pos in occupied_positions:
                        continue
                    
                    # Check if sliding is possible (without modifying board state)
                    if not self._can_slide_to(pos, i, neighbors, occupied_positions):
                        continue
                    
                    # Check if move would break hive connectivity (without temporary moves)
                    if self.test_breakage(original_pos):
                        continue
                    
                    # This is a valid move
                    valid_moves.add(neighbor_pos)
                    seen.add(neighbor_pos)
                    next_frontier.add(neighbor_pos)
            
            # Prepare for next iteration
            frontier = next_frontier
            next_frontier = set()
        
        return valid_moves
    
    def get_valid_moves(self):
        """Returns set of valid moves for Ant, using caching"""
        return self._cached_valid_moves(self._calculate_valid_moves)
        

class Beetle(HiveTile):
    def __init__(self, player, n, board):
        super().__init__('beetle', player, n, board, beetle=True)
    
    def _calculate_valid_moves(self):
        """Optimized Beetle move generation without temporary board state changes"""
        original_pos = self.position
        is_on_stack = len(self.board.get_tile_stack(original_pos)) > 1
        
        # Skip connectivity test if beetle is on a stack (can't disconnect hive)
        if not is_on_stack and self.test_breakage(original_pos):
            return set()

        # Get occupied positions for faster lookup
        occupied_positions = set(self.board.tile_positions.keys())
        
        # Get all six neighboring positions
        neighbors = [
            (original_pos[0], original_pos[1]+1), (original_pos[0]+1, original_pos[1]),
            (original_pos[0]+1, original_pos[1]-1), (original_pos[0], original_pos[1]-1),
            (original_pos[0]-1, original_pos[1]), (original_pos[0]-1, original_pos[1]+1)
        ]
        
        valid_moves = set()
        
        # Process each neighbor
        for i, neighbor_pos in enumerate(neighbors):
            # Case 1: Moving to an empty space
            if neighbor_pos not in occupied_positions:
                # If on a stack, can always move down to empty space
                if is_on_stack:
                    valid_moves.add(neighbor_pos)
                    continue
                
                # Otherwise, check sliding rules
                # Get the positions to the left and right
                left_idx = (i - 1) % 6
                right_idx = (i + 1) % 6
                left_pos = neighbors[left_idx]
                right_pos = neighbors[right_idx]
                
                # Need at least one empty side to slide
                if left_pos not in occupied_positions or right_pos not in occupied_positions:
                    # Additional check for non-equal sides when on ground level
                    if self.board.get_tile_stack(left_pos) != self.board.get_tile_stack(right_pos):
                        valid_moves.add(neighbor_pos)
            
            # Case 2: Can always climb onto other pieces
            else:
                # Get the stack at that position
                dest_stack = self.board.get_tile_stack(neighbor_pos)
                
                # If we're on the ground level, need to check slide rules for climbing
                if not is_on_stack:
                    # Get the positions to the left and right
                    left_idx = (i - 1) % 6
                    right_idx = (i + 1) % 6
                    left_pos = neighbors[left_idx]
                    right_pos = neighbors[right_idx]
                    
                    # Climbing from level 1 has special rules
                    if (len(dest_stack) == 1 and len(self.board.get_tile_stack(original_pos)) == 1):
                        # Need either empty space on one side
                        if (left_pos not in occupied_positions or right_pos not in occupied_positions):
                            valid_moves.add(neighbor_pos)
                        # Or non-double-stack on both sides
                        elif not (len(self.board.get_tile_stack(left_pos)) == 2 and 
                                 len(self.board.get_tile_stack(right_pos)) == 2):
                            valid_moves.add(neighbor_pos)
                    else:
                        # All other climbing is always valid
                        valid_moves.add(neighbor_pos)
                else:
                    # When already on a stack, can always climb further
                    valid_moves.add(neighbor_pos)
        
        return valid_moves
    
    def get_valid_moves(self):
        """Returns set of valid moves for Beetle, using caching"""
        return self._cached_valid_moves(self._calculate_valid_moves)


class Grasshopper(HiveTile):
    def __init__(self, player, n, board):
        super().__init__('grasshopper', player, n, board)
    
    def _calculate_valid_moves(self):
        """Optimized function for Grasshopper's valid moves without temporary board changes"""
        original_pos = self.position
        
        if self.test_breakage(original_pos):
            return set()

        valid_moves = set()
        
        # Get occupied positions for faster lookup
        occupied_positions = set(self.board.tile_positions.keys())
        
        # Get all six neighboring positions - grasshopper can only start jumping from occupied spaces
        neighbors = [
            (original_pos[0], original_pos[1]+1), (original_pos[0]+1, original_pos[1]),
            (original_pos[0]+1, original_pos[1]-1), (original_pos[0], original_pos[1]-1),
            (original_pos[0]-1, original_pos[1]), (original_pos[0]-1, original_pos[1]+1)
        ]
        
        # Check each of the six directions
        for pos in neighbors:
            # Only proceed if there's a piece to jump over
            if pos in occupied_positions:
                # Calculate direction vector
                diff_x = pos[0] - original_pos[0]
                diff_y = pos[1] - original_pos[1]
                
                # Normalize direction
                delta_x = diff_x // max(1, abs(diff_x)) if diff_x != 0 else 0
                delta_y = diff_y // max(1, abs(diff_y)) if diff_y != 0 else 0
                
                # Start from the neighboring piece
                current_pos = pos
                
                # Keep moving in the same direction until finding an empty space
                while True:
                    # Calculate the next position in the same direction
                    next_pos = (current_pos[0] + delta_x, current_pos[1] + delta_y)
                    
                    # If we find an empty spot, it's a valid landing position
                    if next_pos not in occupied_positions:
                        valid_moves.add(next_pos)
                        break
                    
                    # Continue in the same direction
                    current_pos = next_pos
        
        return valid_moves
    
    def get_valid_moves(self):
        """Returns set of valid moves for Grasshopper, using caching"""
        return self._cached_valid_moves(self._calculate_valid_moves)
                

class Spider(HiveTile):
    def __init__(self, player, n, board):
        super().__init__('spider', player, n, board)
    
    def _calculate_valid_moves(self):
        """Optimized computation function for Spider's valid moves without temporary board changes"""
        original_pos = self.position
        
        if self.test_breakage(original_pos):
            return set()
            
        # Get occupied positions for faster lookup
        occupied_positions = set(self.board.tile_positions.keys())
        
        # Track positions we've already processed
        seen = set([original_pos])
        valid_moves = set()
        
        # We use a list for BFS queue to track turns
        bfs_queue = deque([(original_pos, 0)])  # (position, turns)

        while bfs_queue:
            pos, turns = bfs_queue.popleft()
            
            # Get all six neighboring positions
            neighbors = [
                (pos[0], pos[1]+1), (pos[0]+1, pos[1]), (pos[0]+1, pos[1]-1),
                (pos[0], pos[1]-1), (pos[0]-1, pos[1]), (pos[0]-1, pos[1]+1)
            ]
            
            # Process each neighbor
            for i, neighbor_pos in enumerate(neighbors):
                # Skip if already processed
                if neighbor_pos in seen:
                    continue
                
                # Skip if position is occupied
                if neighbor_pos in occupied_positions:
                    continue
                
                # Check if sliding is possible (without modifying board state)
                if not self._can_slide_to(pos, i, neighbors, occupied_positions):
                    continue
                
                # Spider must follow its unique movement rules
                next_turns = turns + 1
                
                # Check if this is a valid final destination (exactly 3 steps)
                if next_turns == 3:
                    # Check if move would break hive connectivity
                    if not self.test_breakage(original_pos):
                        valid_moves.add(neighbor_pos)
                # Otherwise, add to queue for further exploration (less than 3 steps)
                elif next_turns < 3:
                    seen.add(neighbor_pos)
                    bfs_queue.append((neighbor_pos, next_turns))
            
        return valid_moves
    
    def get_valid_moves(self):
        """Returns set of valid moves for Spider, using caching"""
        return self._cached_valid_moves(self._calculate_valid_moves)


class Queen(HiveTile):
    def __init__(self, player, n, board):
        super().__init__('queen', player, n, board)
    
    def _calculate_valid_moves(self):
        """Optimized queen move generation without temporary board state changes"""
        original_pos = self.position
        
        if self.test_breakage(original_pos):
            return set()

        # Get occupied positions for faster lookup
        occupied_positions = set(self.board.tile_positions.keys())
        
        # Get all six neighboring positions
        neighbors = [
            (original_pos[0], original_pos[1]+1), (original_pos[0]+1, original_pos[1]),
            (original_pos[0]+1, original_pos[1]-1), (original_pos[0], original_pos[1]-1),
            (original_pos[0]-1, original_pos[1]), (original_pos[0]-1, original_pos[1]+1)
        ]
        
        valid_moves = set()
        
        # Process each neighbor
        for i, neighbor_pos in enumerate(neighbors):
            # Skip if position is occupied
            if neighbor_pos in occupied_positions:
                continue
            
            # Queen needs at least one empty space on either side to slide
            left_idx = (i - 1) % 6
            right_idx = (i + 1) % 6
            left_pos = neighbors[left_idx]
            right_pos = neighbors[right_idx]
            
            # Check if slide is possible
            if left_pos not in occupied_positions or right_pos not in occupied_positions:
                # Additional requirement: positions on either side must not be the same piece
                if self.board.get_tile_stack(left_pos) != self.board.get_tile_stack(right_pos):
                    valid_moves.add(neighbor_pos)
        
        return valid_moves
    
    def get_valid_moves(self):
        """Returns set of valid moves for Queen, using caching"""
        return self._cached_valid_moves(self._calculate_valid_moves)

        