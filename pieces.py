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


class Ant(HiveTile):
    def __init__(self, player, n):
        super().__init__('ant', player, n)
    
    def get_valid_moves(self):
        pass


class Beetle(HiveTile):
    def __init__(self, player, n):
        super().__init__('beetle', player, n, beetle=True)


class Grasshopper(HiveTile):
    def __init__(self, player, n):
        super().__init__('grasshopper', player, n)
    

    def get_valid_moves(self):
        valid_moves_temp = set() # temporary set to store valid moves before checking connectedness
        valid_moves = set()

        original_pos = self.position
        first_iter = True

        bfs_queue = deque(self)
        seen = set([original_pos])
        
        while bfs_queue:
            tile = bfs_queue.popleft()
            pos = tile.position

            if first_iter:
                npos_arr = [(pos[0], pos[1]+1), (pos[0]+1, pos[1]), (pos[0]+1, pos[1]-1), 
                    (pos[0], pos[1]-1), (pos[0]-1, pos[1]), (pos[0]-1, pos[1]+1)]
                first_iter = False
            
            else:
                # logic to make sure position lies on a straight line from the grasshopper
                delta_1 = min(pos[0] - original_pos[0], abs(pos[0] - original_pos[0])) / abs(pos[0] - original_pos[0])
                delta_2 = min(pos[1] - original_pos[1], abs(pos[1] - original_pos[1])) / abs(pos[1] - original_pos[1])
                npos_arr = [(pos[0] + delta_1, pos[1] + delta_2)]
            
            for pos in npos_arr:
                if pos not in seen:
                    seen.add(pos)
                    
                    if self.get_tile(pos) == None:
                        valid_moves_temp.add(pos)
                    
                    else:
                        bfs_queue.append(self.get_tile(pos))

        # check if the move is valid by checking if the hive is still connected
        for move in valid_moves_temp:
            self.board.move_tile(self, move)
            if self.board.connected():
                valid_moves.add(move)
            self.board.move_tile(self, original_pos)
        
        return valid_moves
                

        
class Spider(HiveTile):
    def __init__(self, player, n):
        super().__init__('spider', player, n)


class Queen(HiveTile):
    def __init__(self, player, n):
        super().__init__('queen', player, n)

        