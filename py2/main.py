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

import json
import sys
import argparse
from pathlib import Path

from PyQt5.QtWidgets import QApplication

import hive_engine

from controller.game_controller import GameController
from gui.main_window import HiveGUI
from agents import Agent, RandomAgent, MinimaxAgent, MinimaxParams

_CONFIG_PATH = Path(__file__).parent / 'config.json'


def _load_minimax_agent() -> MinimaxAgent:
    if _CONFIG_PATH.exists():
        with _CONFIG_PATH.open() as f:
            cfg = json.load(f)
        return MinimaxAgent(params=MinimaxParams(**cfg.get('minimax', {})))
    return MinimaxAgent(params=MinimaxParams())


def _make_agent(name: str | None) -> Agent | None:
    if name is None or name == 'human':
        return None
    if name == 'random':
        return RandomAgent()
    if name == 'minimax':
        return _load_minimax_agent()
    raise ValueError(f"Unknown agent type: {name!r}. Valid: human, random, minimax")


def main() -> None:
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
