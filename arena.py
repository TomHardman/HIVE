from board import HiveBoard
from agents import RandomAgent, DQLAgent, HeuristicAgent
from networks import DQN, DQN_gat
import torch
from heuristic import Params

"""
Provides arena environment for agents to self play/for agents to play each other
"""

class HiveArena():
    def __init__(self, player1, player2, simplified):
        self.p1 = player1
        self.p2 = player2
        self.simplified = simplified

    def play_game(self):
        """
        Play a game between two agents.
        """
        board = HiveBoard(max_turns=20, simplified_game=self.simplified)
        self.p1.set_board(board)
        self.p2.set_board(board)
        moves = 0
        
        while (result := board.game_over()) == False:
            player = board.get_player_turn()
            if player == 1:
                action = self.p1.sample_action()
                moves += 1
            else:
                action = self.p2.sample_action()
                moves += 1

        print('Game Over', result, 'in', moves, 'moves')
        return result
    
    def simulate_games(self, num_games, print_outcomes=False, log=False):
        """
        Simulate a number of games between two agents.
        """
        results = []
        for i in range(num_games):
            if log:
                print('Playing Game', i+1)    
            results.append(self.play_game())
        
        if print_outcomes:
            print(results)
            print('Player 1 wins:', results.count(1))
            print('Player 2 wins:', results.count(2))
            print('Draws:', results.count(0))
        
        return results


if __name__ == '__main__':
    with open('models/simplified3_at10000.pt', 'rb') as f:
        state_dict = torch.load(f)
    reduced = False
    
    dqn = DQN_gat(13 if reduced else 25)
    dqn.load_state_dict(state_dict)
    rl_agent1 = DQLAgent(1, dqn, 0, reduced=reduced)
    rl_agent2 = DQLAgent(2, dqn, 0, reduced=reduced)

    randomagent1 = RandomAgent(1)
    randomagent2 = RandomAgent(2)

    # Heuristic Agent
    params = Params(queen_surrounding_reward=1, win_reward=100, ownership_reward=3, 
                    mp_reward=0.5)
    heuristic_agent2 = HeuristicAgent(2, 1, params)
    
    arena = HiveArena(randomagent1, heuristic_agent2, simplified=False)
    arena.simulate_games(10, print_outcomes=True, log=True)