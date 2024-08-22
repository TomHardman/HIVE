import sys

from PyQt5 import QtWidgets
from GUI import HiveGUI
from board import HiveBoard
from random_agent import RandomAgent



if __name__ == '__main__':
    board = HiveBoard()
    random_agent2 = RandomAgent(board, 2)
    
    app = QtWidgets.QApplication(sys.argv)

    gui = HiveGUI(board)
    gui.set_player(2, agent=random_agent2)
    gui.show()
    
    sys.exit(app.exec_())