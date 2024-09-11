from board import HiveBoard
from agents import RandomAgent, RLAgent
from networks import DQN, DQN_gat
import torch

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
        board = HiveBoard(max_turns=100, simplified_game=self.simplified)
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
    dqn = DQN(13 if reduced else 25)
    dqn.load_state_dict(state_dict)
    randomagent1 = RandomAgent(1)
    randomagent2 = RandomAgent(2)
    agent1 = RLAgent(1, dqn, 0, reduced=reduced)
    agent2 = RLAgent(2, dqn, 0)
    arena = HiveArena(agent1, randomagent2, simplified=False)
    arena.simulate_games(50, print_outcomes=True, log=True)