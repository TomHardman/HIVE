import sys
import argparse

from PyQt5 import QtWidgets
from GUI import HiveGUI
from game import HiveBoard
from AI.agents import Agent, RandomAgent, DQLAgent, HeuristicAgent
from AI.minimax import Params
from AI.DQL import DQN, DQN_gat

import torch


def create_agent(agent_type: str, player: int, board: HiveBoard, reduced: bool = False) -> Agent | None:
    """
    Factory function to create an agent based on agent type.

    Args:
        agent_type: Type of agent ('dqn', 'random', 'mm', or None for human player)
        player: Player number (1 or 2)
        board: The game board
        reduced: Whether to use reduced feature set for DQL agents

    Returns:
        Agent instance or None if agent_type is None (human player)
    """
    match agent_type:
        case 'dqn':
            dqn = DQN(13 if reduced else 25)
            dqn.load_state_dict(torch.load('/Users/tomhardman/Documents/Projects/HIVE/HIVE/py/models/simplified3_at40000.pt'))
            return DQLAgent(player, dqn, 0, board, reduced=reduced)

        case 'random':
            return RandomAgent(player, board)

        case 'mm':
            params = Params(queen_surrounding_reward=1, win_reward=100, ownership_reward=5, mp_reward=0.5)
            return HeuristicAgent(player, 3, params, board)

        case None:
            return None

        case _:
            raise ValueError(f"Unknown agent type: {agent_type}. Must be 'dqn', 'random', 'mm', or None")


def play(args):
    board = HiveBoard()
    app = QtWidgets.QApplication(sys.argv)
    gui = HiveGUI(board, rl_debug=False)

    # Create and set agents for each player
    player1_agent = create_agent(args.player1, 1, board, reduced=args.reduced)
    player2_agent = create_agent(args.player2, 2, board, reduced=args.reduced)

    if player1_agent:
        gui.set_player(1, player1_agent)
    if player2_agent:
        gui.set_player(2, player2_agent)

    gui.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Play Hive with configurable AI agents')
    parser.add_argument('--player1', type=str, default=None,
                        help="Agent type for player 1: 'dqn', 'random', 'mm', or None for human")
    parser.add_argument('--player2', type=str, default=None,
                        help="Agent type for player 2: 'dqn', 'random', 'mm', or None for human")
    parser.add_argument('--reduced', action='store_true',
                        help='Use reduced feature set for DQL agents')
    parser.add_argument('--simplified', type=bool, default=False,
                        help='Whether to play simplfied game - 3 pieces surrounding Queen is win condition')
    args = parser.parse_args()
    play(args)