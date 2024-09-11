import sys

from PyQt5 import QtWidgets
from GUI import HiveGUI
from board import HiveBoard
from agents import RandomAgent, RLAgent

from rl_helper import ExperienceReplay, RewardCalculator, get_graph_from_state
from networks import DQN, DQN_gat

import torch


if __name__ == '__main__':
    reduced = False
    board = HiveBoard()
    dqn = DQN_gat(13 if reduced else 25)
    dqn.load_state_dict(torch.load('models/simplified3_at10000.pt'))
    random_agent2 = RandomAgent(2, board)
    rl_agent = RLAgent(1, dqn, 0, board, reduced=reduced)
    
    app = QtWidgets.QApplication(sys.argv)

    gui = HiveGUI(board, rl_debug=True)
    gui.set_player(1, agent=rl_agent)
    #gui.set_player(2, agent=random_agent2)
    gui.show()
    
    sys.exit(app.exec_()) 