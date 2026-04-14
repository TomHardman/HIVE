"""
Entry point for the HIVE GUI.

Usage examples:
    # Human vs Human
    python main.py

    # Human vs Random agent
    python main.py --player2 random

    # Random vs Random
    python main.py --player1 random --player2 random

    # Simplified game (queen surrounded by 3 = loss)
    python main.py --player2 random --simplified
"""

import sys
import argparse

from PyQt5.QtWidgets import QApplication

import hive_engine

from controller.game_controller import GameController
from gui.main_window import HiveGUI
from agents.random_agent import RandomAgent


def _make_agent(name: str):
    if name is None or name == 'human':
        return None
    if name == 'random':
        return RandomAgent()
    raise ValueError(f"Unknown agent type: {name!r}. Valid: human, random")


def main():
    parser = argparse.ArgumentParser(description="HIVE board game")
    parser.add_argument('--player1', default='human', help='Player 1 agent (human|random)')
    parser.add_argument('--player2', default='human', help='Player 2 agent (human|random)')
    parser.add_argument('--max-turns', type=int, default=-1,
                        help='Maximum turns before draw (-1 = unlimited)')
    parser.add_argument('--simplified', action='store_true',
                        help='Simplified game: queen surrounded by 3 = loss')
    args = parser.parse_args()

    app = QApplication(sys.argv)

    game = hive_engine.Game(args.max_turns, args.simplified)
    view = HiveGUI()
    controller = GameController(
        game=game,
        view=view,
        player1=_make_agent(args.player1),
        player2=_make_agent(args.player2),
    )

    view.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
