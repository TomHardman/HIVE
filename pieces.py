from collections import deque


class HiveTile(): # parent class for all pieces
    def __init__(self, name, player, n, board, beetle=False):
        self.player = player
        self.name = name + str(n) + '_p' + str(player)
        self.position = None
        self.neighbours = [None, None, None, None, None, None] # clockwise from 12 o'clock
        self.is_beetle = beetle
        self.board = board
    
    def __hash__(self): # hash based on name
        return hash(self.name)
    
    def __eq__(self, other): # equality based on name
        return isinstance(other, self.__class__) and self.name == other.name
    
    def covered(self):
        '''Returns True if tile is covered by beetle and is therefore immobile.'''
        return self.board.get_tile_stack(self.position)[-1] != self # checks if top tile at current position is self


class Ant(HiveTile):
    def __init__(self, player, n, board):
        super().__init__('ant', player, n, board)
    
    def get_valid_moves(self):
        pass


class Beetle(HiveTile):
    def __init__(self, player, n, board):
        super().__init__('beetle', player, n, board, beetle=True)
    
    def get_valid_moves(self):
        if self.covered():
            return set()
        
        valid_moves_temp = set()
        valid_moves = set()

        original_pos = self.position
        npos_arr = [(original_pos[0], original_pos[1]+1), (original_pos[0]+1, original_pos[1]), 
                    (original_pos[0]+1, original_pos[1]-1), (original_pos[0], original_pos[1]-1), 
                    (original_pos[0]-1, original_pos[1]), (original_pos[0]-1, original_pos[1]+1)]

        for i in range(len(npos_arr)):
            if self.board.get_tile_stack(npos_arr[i]) == None:
                # check adjacent neighbours to see if sliding is possible
                if self.board.get_tile_stack(npos_arr[(i-1)%6]) == None or self.board.get_tile_stack(npos_arr[(i+1)%6]) == None:
                    valid_moves_temp.add(npos_arr[i])

            elif len(self.board.get_tile_stack(npos_arr[i])) <= len(self.board.get_tile_stack(original_pos)): # can only climb one level at once
                valid_moves_temp.add(npos_arr[i])
        
        # check if the move is valid by checking if the hive is still connected after moving
        for move in valid_moves_temp:
            self.board.move_tile(self, move)
            if not self.board.check_unconnected():
                valid_moves.add(move)
            self.board.move_tile(self, original_pos)
        
        return valid_moves


class Grasshopper(HiveTile):
    def __init__(self, player, n, board):
        super().__init__('grasshopper', player, n, board)
    
    def get_valid_moves(self):
        if self.covered():
            return set()

        valid_moves_temp = set() # temporary set to store valid moves before checking connectedness
        valid_moves = set()

        original_pos = self.position
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
                

class Spider(HiveTile):
    def __init__(self, player, n, board):
        super().__init__('spider', player, n, board)


class Queen(HiveTile):
    def __init__(self, player, n, board):
        super().__init__('queen', player, n, board)
    
    def get_valid_moves(self):
        if self.covered():
            return set()
        
        valid_moves_temp = set()
        valid_moves = set()

        original_pos = self.position
        npos_arr = [(original_pos[0], original_pos[1]+1), (original_pos[0]+1, original_pos[1]), 
                    (original_pos[0]+1, original_pos[1]-1), (original_pos[0], original_pos[1]-1), 
                    (original_pos[0]-1, original_pos[1]), (original_pos[0]-1, original_pos[1]+1)]

        for i in range(len(npos_arr)):
            if self.board.get_tile_stack(npos_arr[i]) == None:
                # check adjacent neighbours to see if sliding is possible
                if self.board.get_tile_stack(npos_arr[(i-1)%6]) == None or self.board.get_tile_stack(npos_arr[(i+1)%6]) == None:
                    valid_moves_temp.add(npos_arr[i])
        
        # check if the move is valid by checking if the hive is still connected after moving
        for move in valid_moves_temp:
            self.board.move_tile(self, move)
            if not self.board.check_unconnected():
                valid_moves.add(move)
            self.board.move_tile(self, original_pos)
        
        return valid_moves

        