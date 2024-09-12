from heuristic import evaluate
import heapq
from board import ACTIONSPACE_INV, HiveBoard

states_count = 0

def minimax(board: HiveBoard, depth, is_maximizing, player, eval_params,
            alpha=-float('inf'), beta=float('inf')):
    """
    Minimax algorithm with alpha-beta pruning.

    Parameters:
    state: current game state.
    depth: how deep we want to search in the game tree.
    is_maximizing: boolean indicating if it's the maximizing player's turn.
    alpha: best score the maximizing player can guarantee so far (for pruning).
    beta: best score the minimizing player can guarantee so far (for pruning).
    
    Returns:
    score: The best score the current player can achieve.
    best_move: The best move to play from this state (optional).
    """
    global states_count
    states_count += 1 

    # Base case: check if the game is over or depth limit reached
    if board.game_over() or depth == 0:
        return evaluate(board.get_game_state(player), player, eval_params), None

    actions = board.get_legal_actions(board.get_player_turn())
    valid_moves = create_action_list(actions)
    best_move = None

    if is_maximizing:
        max_eval = -float('inf')  # Maximizer wants to maximize this
        for move in valid_moves:
            og_pos = make_move(board, move) # Apply move
            eval_, _ = minimax(board, depth - 1, False, player, eval_params, alpha, beta)
            undo_move(board, move, og_pos)
            
            # Update max evaluation and best move
            if eval_ > max_eval:
                max_eval = eval_
                best_move = move
            
            alpha = max(alpha, eval_)
            if beta <= alpha:
                break  # Beta cutoff
            
        return max_eval, best_move

    else:
        min_eval = float('inf')
        for move in valid_moves:
            og_pos = make_move(board, move) # Apply move
            eval_, _ = minimax(board, depth - 1, True, player, eval_params, alpha, beta)
            undo_move(board, move, og_pos)
            
            # Update min evaluation and best move
            if eval_ < min_eval:
                min_eval = eval_
                best_move = move
            
            beta = min(beta, eval_)
            if beta <= alpha:
                break  # Alpha cutoff
        
        return min_eval, best_move


def beam_minimax(board: HiveBoard, depth, is_maximizing, player, eval_params,
                 alpha=-float('inf'), beta=float('inf'), beam_width=3):
    """
    Minimax algorithm with alpha-beta pruning and beam search.

    Parameters:
    board: current game state (HiveBoard).
    depth: how deep we want to search in the game tree.
    is_maximizing: boolean indicating if it's the maximizing player's turn.
    player: the current player.
    eval_params: parameters for the evaluation function.
    alpha: best score the maximizing player can guarantee so far (for pruning).
    beta: best score the minimizing player can guarantee so far (for pruning).
    beam_width: number of best moves to explore at each level of the tree (beam search).

    Returns:
    score: The best score the current player can achieve.
    best_move: The best move to play from this state (optional).
    """
    global states_count
    states_count += 1

    # Base case: check if the game is over or depth limit reached
    if board.game_over() or depth == 0:
        return evaluate(board.get_game_state(player), player, eval_params), None

    actions = board.get_legal_actions(board.get_player_turn())
    valid_moves = create_action_list(actions)
    best_move = None

    # Evaluate all moves at this level
    move_evaluations = []

    for move in valid_moves:
        og_pos = make_move(board, move)  # Apply move
        eval_ = evaluate(board.get_game_state(player), player, eval_params)
        undo_move(board, move, og_pos)  # Undo move
        
        # Store the evaluated move (negative eval for heapq for maximizer)
        move_evaluations.append((eval_, move))

    # Sort moves based on evaluation (maximizer sorts in descending order, minimizer ascending)
    if is_maximizing:
        best_moves = heapq.nlargest(beam_width, move_evaluations, key=lambda x: x[0])
    else:
        best_moves = heapq.nsmallest(beam_width, move_evaluations, key=lambda x: x[0])

    # Now run minimax on the selected top-k moves (beam search)
    if is_maximizing:
        max_eval = -float('inf')
        for eval_, move in best_moves:
            og_pos = make_move(board, move)  # Apply move
            eval_, _ = beam_minimax(board, depth - 1, False, player, eval_params, alpha, beta, beam_width)
            undo_move(board, move, og_pos)  # Undo move

            if eval_ > max_eval:
                max_eval = eval_
                best_move = move

            alpha = max(alpha, eval_)
            if beta <= alpha:
                break  # Beta cutoff

        return max_eval, best_move

    else:
        min_eval = float('inf')
        for eval_, move in best_moves:
            og_pos = make_move(board, move)  # Apply move
            eval_, _ = beam_minimax(board, depth - 1, True, player, eval_params, alpha, beta, beam_width)
            undo_move(board, move, og_pos)  # Undo move

            if eval_ < min_eval:
                min_eval = eval_
                best_move = move

            beta = min(beta, eval_)
            if beta <= alpha:
                break  # Alpha cutoff

        print(states_count)
        return min_eval, best_move


def create_action_list(actions):
    """
    Create list of action tuples as board returns legal actions as boolean mask
    """
    action_list = []
    for pos in actions:
        for tile_idx in range(len(actions[pos])):
            if actions[pos][tile_idx] == True:
                action_list.append((pos, tile_idx))
    return action_list


def make_move(board: HiveBoard, action: tuple):
    """
    Apply move to board. Returns original position of piece.
    """
    pos, tile_idx = action
    piece_id = ACTIONSPACE_INV[tile_idx]
    tile_name = piece_id + '_p' + str(board.get_player_turn())
    tile_obj = board.name_obj_mapping[tile_name]
    original_pos = tile_obj.position
    
    # work out if piece to be moved has been placed or not
    if tile_obj not in board.player1_hand and tile_obj not in board.player2_hand:
        board.move_tile(tile_obj, pos, update_turns=True)
    else:
        board.place_tile(tile_obj, pos, update_turns=True) 
    
    return original_pos


def undo_move(board: HiveBoard, action: tuple, original_pos):
    """
    Undo move on board.
    """
    pos, tile_idx = action
    piece_id = ACTIONSPACE_INV[tile_idx]
    tile_name = piece_id + '_p' + str(3 - board.get_player_turn())
    tile_obj = board.name_obj_mapping[tile_name]
    
    board.undo_move(tile_obj, original_pos)