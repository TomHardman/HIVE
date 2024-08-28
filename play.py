import sys

from PyQt5 import QtWidgets
from GUI import HiveGUI
from board import HiveBoard
from random_agent import RandomAgent

from rl_helper import ExperienceReplay, RewardCalculator, get_graph_from_state


if __name__ == '__main__':
    board = HiveBoard()
    random_agent2 = RandomAgent(2, board)
    
    app = QtWidgets.QApplication(sys.argv)

    gui = HiveGUI(board, rl_debug=True)
    gui.set_player(2, agent=random_agent2)
    gui.show()
    
    sys.exit(app.exec_()) 