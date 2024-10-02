import sys
import argparse

from PyQt5 import QtWidgets
from GUI import HiveGUI
from game import HiveBoard
from AI.agents import RandomAgent, DQLAgent, HeuristicAgent
from AI.minimax import Params
from AI.DQL import DQN, DQN_gat

import torch

def play(args):
    reduced = False
    board = HiveBoard()
    app = QtWidgets.QApplication(sys.argv)
    gui = HiveGUI(board, rl_debug=False)

    if args.mode == 'dqn':
        # DQL Agent
        dqn = DQN(13 if reduced else 25)
        dqn.load_state_dict(torch.load('AI/DQL/models/simplified3_no_win_r_40000.pt'))
        rl_agent = DQLAgent(2, dqn, 0, board, reduced=reduced)
        gui.set_player(2, agent=rl_agent)

    if args.mode == 'random':
        # Random Agent
        random_agent = RandomAgent(1, board)
        gui.set_player(2, agent=random_agent)

    if args.mode == 'mm':
        # Heuristic Agent
        params = Params(queen_surrounding_reward=1, win_reward=100, ownership_reward=5,
                        mp_reward=0.5)
        heuristic_agent = HeuristicAgent(2, 2, params, board)
        gui.set_player(2, agent=heuristic_agent)
    
    gui.show()
    sys.exit(app.exec_()) 

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, default=None, help='Mode of play: dqn, random, mm or None for player vs player')
    args = parser.parse_args()
    play(args)