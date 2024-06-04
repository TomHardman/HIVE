class HiveTile(): # interface for all pieces
    def __init__(self, name, player, n, beetle=False):
        self.player = player
        self.name = name + str(n) + '_p' + str(player)
        self.position = None
        self.neighbours = [None, None, None, None, None, None] # clockwise from 12 o'clock
        self.is_beetle = beetle
    
    def __hash__(self): # hash based on name
        return hash(self.name)
    
    def __eq__(self, other): # equality based on name
        return isinstance(other, self.__class__) and self.name == other.name

class Ant(HiveTile):
    def __init__(self, player, n):
        super().__init__('ant', player, n)

class Beetle(HiveTile):
    def __init__(self, player, n):
        super().__init__('beetle', player, n, beetle=True)

class Grasshopper(HiveTile):
    def __init__(self, player, n):
        super().__init__('grasshopper', player, n)

class Spider(HiveTile):
    def __init__(self, player, n):
        super().__init__('spider', player, n)

class Queen(HiveTile):
    def __init__(self, player, n):
        super().__init__('queen', player, n)

        