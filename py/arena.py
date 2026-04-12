import argparse

from game import HiveBoard
from AI.agents import Agent, RandomAgent, DQLAgent, HeuristicAgent
from AI.DQL.networks import DQN, DQN_gat, DQN_simple
from AI.minimax.heuristic import Params
import torch

"""
Provides arena environment for agents to self play/for agents to play each other
"""


def create_agent(agent_type: str, player: int, reduced: bool = False) -> Agent | None:
    """
    Factory function to create an agent based on agent type.

    Args:
        agent_type: Type of agent ('dqn', 'random', 'mm', or None for human player)
        player: Player number (1 or 2)
        reduced: Whether to use reduced feature set for DQL agents

    Returns:
        Agent instance or None if agent_type is None (human player)
    """
    match agent_type:
        case 'dqn':
            dqn = DQN_simple(13 if reduced else 25)
            dqn.load_state_dict(torch.load('/Users/tomhardman/Documents/Projects/HIVE/HIVE/py/models/simplified3_at124000.pt'))
            return DQLAgent(player, dqn, 0, reduced=reduced)

        case 'random':
            return RandomAgent(player)

        case 'mm':
            params = Params(queen_surrounding_reward=1, win_reward=100, ownership_reward=3, mp_reward=0.5)
            return HeuristicAgent(player, 3, params)

        case None:
            raise ValueError("Arena requires two AI agents. None is not allowed for player agents.")

        case _:
            raise ValueError(f"Unknown agent type: {agent_type}. Must be 'dqn', 'random', or 'mm'")


class HiveArena:
    def __init__(self, player1: Agent, player2: Agent, simplified: bool = False):
        self.p1 = player1
        self.p2 = player2
        self.simplified = simplified

    def play_game(self) -> int:
        """
        Play a game between two agents.

        Returns:
            Winner (1, 2, or 0 for draw)
        """
        board = HiveBoard(max_turns=50, simplified_game=self.simplified)
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

        print(f'Game Over: Player {result} wins in {moves} moves')
        return result

    def simulate_games(self, num_games: int, print_outcomes: bool = False, log: bool = False) -> list[int]:
        """
        Simulate a number of games between two agents.

        Args:
            num_games: Number of games to play
            print_outcomes: Whether to print detailed results
            log: Whether to log each game

        Returns:
            List of game results (1 = player1 wins, 2 = player2 wins, 0 = draw)
        """
        results = []
        for i in range(num_games):
            if log:
                print(f'Playing Game {i+1}/{num_games}')
            results.append(self.play_game())

        if print_outcomes:
            print('\n=== Tournament Results ===')
            print(f'Total games: {num_games}')
            print(f'Player 1 wins: {results.count(1)} ({100*results.count(1)/num_games:.1f}%)')
            print(f'Player 2 wins: {results.count(2)} ({100*results.count(2)/num_games:.1f}%)')
            print(f'Draws: {results.count(0)} ({100*results.count(0)/num_games:.1f}%)')

        return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run tournament between two AI agents')
    parser.add_argument('--player1', type=str, default='dqn',
                        help="Agent type for player 1: 'dqn', 'random', or 'mm'")
    parser.add_argument('--player2', type=str, default='random',
                        help="Agent type for player 2: 'dqn', 'random', or 'mm'")
    parser.add_argument('--games', type=int, default=10,
                        help='Number of games to simulate')
    parser.add_argument('--reduced', action='store_true',
                        help='Use reduced feature set for DQL agents')
    parser.add_argument('--simplified', action='store_true',
                        help='Use simplified game rules')
    parser.add_argument('--log', action='store_true',
                        help='Log each game')
    args = parser.parse_args()

    # Create agents
    player1_agent = create_agent(args.player1, 1, reduced=args.reduced)
    player2_agent = create_agent(args.player2, 2, reduced=args.reduced)

    # Run tournament
    arena = HiveArena(player1_agent, player2_agent, simplified=args.simplified)
    arena.simulate_games(args.games, print_outcomes=True, log=args.log)