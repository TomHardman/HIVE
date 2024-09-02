import sys

from PyQt5 import QtWidgets
from GUI import HiveGUI
from board import HiveBoard
from agents import RandomAgent, RLAgent

from rl_helper import ExperienceReplay, RewardCalculator, get_graph_from_state
from networks import DQN

import torch


if __name__ == '__main__':
    board = HiveBoard()
    dqn = DQN(25)
    dqn.load_state_dict(torch.load('models/overnight_60000.pt'))
    random_agent2 = RandomAgent(2, board)
    rl_agent = RLAgent(2, dqn, 0, board)
    
    app = QtWidgets.QApplication(sys.argv)

    gui = HiveGUI(board, rl_debug=True)
    gui.set_player(2, agent=rl_agent)
    gui.show()
    
    sys.exit(app.exec_()) 