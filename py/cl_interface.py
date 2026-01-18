from game import HiveBoard

def turn_cl(board, player):
    turn = input(f'Player {player} Turn: ') # input turn in format tile_name, move_type, new_position
    tile_name, move_type, new_position = turn.split(' ')
    new_position = tuple(map(int, new_position.split(',')))
    
    while board.execute_move_cli(tile_name, move_type, player, new_position) == False:
        turn = input(f'Player {player} Turn: ') # input turn in format tile_name, move_type, n1,n2
        tile_name, move_type, new_position = turn.split(' ')
        new_position = tuple(map(int, new_position.split(',')))


def game_loop(board):
    while board.game_over() == False:
        turn_cl(board, 1)
        turn_cl(board, 2)
    
    print(f'Game Over, Player: {board.game_over()} wins!')


def main():
    print('Starting Game')
    board = HiveBoard()
    game_loop(board)


if __name__ == '__main__':
    main() 

