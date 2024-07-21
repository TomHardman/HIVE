from board import HiveBoard

def turn_cl(board, player):
    turn = input(f'Player {player} Turn:') # input turn in format tile_name, move_type, new_position
        if len(turn.split(' ')) == 2:
            tile_name, move_type = turn.split(' ')

        elif len(turn.split(' ')) == 3:
            tile_name, move_type, new_position = turn.split(' ')
    
    while board.execute_move_cli(tile_name, move_type, player, new_position) == False:
        turn = input(f'Player {player} Turn:') # input turn in format tile_name, move_type, new_position
        tile_name, move_type, new_position = turn.split(' ')


def game_loop(board):
    print('Player 1 Turn')
    # player 1 turn
    print('Player 2 Turn')


def main():
    print('starting game')
    board = HiveBoard()
    game_loop(board)


if __name__ == '__main__':
    main() 

