import sys

from PyQt5 import QtWidgets
from GUI import HiveGUI
from game import HiveBoard
from AI.agents import RandomAgent, DQLAgent, HeuristicAgent
from AI.minimax import Params
from AI.DQL import DQN, DQN_gat

import torch

if __name__ == '__main__':
    reduced = False
    board = HiveBoard()
    
    # DQL Agent
    dqn = DQN(13 if reduced else 25)
    dqn.load_state_dict(torch.load('AI/DQL/models/simplified3_no_win_r_40000.pt'))
    rl_agent = DQLAgent(2, dqn, 0, board, reduced=reduced)

    # Random Agent
    random_agent = RandomAgent(1, board)

    # Heuristic Agent
    params = Params(queen_surrounding_reward=1, win_reward=100, ownership_reward=5,
                    mp_reward=0.5)
    heuristic_agent = HeuristicAgent(2, 2, params, board)
    
    app = QtWidgets.QApplication(sys.argv)

    gui = HiveGUI(board, rl_debug=True)
    #gui.set_player(1, agent=random_agent)
    gui.set_player(2, agent=heuristic_agent)
    gui.show()
    
    sys.exit(app.exec_()) 