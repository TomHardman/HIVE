import sys
from PyQt5 import QtCore      # core Qt functionality
from PyQt5 import QtGui       # extends QtCore with GUI functionality
from PyQt5 import QtWidgets
from PyQt5 import QtOpenGL 
from PyQt5.QtCore import Qt

import OpenGL.GL as gl
from OpenGL import GLU

from gui_pieces import BoardPiece, ButtonPiece

from board import HiveBoard


class HiveGUI(QtWidgets.QMainWindow):   
    def __init__(self):
        super().__init__()
        self.resize(1000, 800)
        self.setWindowTitle('HIVE GUI')

        # general layout
        self.splitter = QtWidgets.QSplitter(Qt.Vertical)
        self.board_canvas = BoardCanvas(self)
        self.selection_canvas = SelectionCanvas(self)
        self.splitter.addWidget(self.board_canvas)
        self.splitter.addWidget(self.selection_canvas)
        self.setCentralWidget(self.splitter)
        
        self.board = HiveBoard()
        self.player_turn = self.board.get_player_turn()


class BoardCanvas(QtOpenGL.QGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        # mouse position
        self.setMouseTracking(True)  # Enable mouse tracking
        self.mouse_x = 0
        self.mouse_y = 0
    
    def initializeGL(self):
        self.qglClearColor(QtGui.QColor(255, 255, 255))
        gl.glEnable(gl.GL_DEPTH_TEST)
    
    def resizeGL(self, width, height):
        gl.glViewport(0, 0, width, height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        aspect = width / float(height)

        GLU.gluOrtho2D(0, width, 0, height)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()
    
    def paintGL(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        # Display mouse position
        gl.glColor3f(0.0, 0.0, 0.0)
        self.renderText(10, self.height() - 20, 
                        f"Mouse Position: ({self.mouse_x}, {self.mouse_y})", QtGui.QFont("Arial", 12))
        
        # Display player turn
        self.renderText(10, 20, 
                        f"Player Turn: {self.parent.player_turn}", QtGui.QFont("Arial", 12))

    def mouseMoveEvent(self, event):
        # Update mouse position
        self.mouse_x = event.x()
        self.mouse_y = event.y()
        self.update() # Trigger paint event


class SelectionCanvas(QtOpenGL.QGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFixedSize(1000, 150)

        # mouse position
        self.setMouseTracking(True)  # Enable mouse tracking
        self.mouse_x = 0
        self.mouse_y = 0

        self.initializeButtons()
    
    def initializeGL(self):
        self.qglClearColor(QtGui.QColor(255, 255, 255))
        gl.glEnable(gl.GL_DEPTH_TEST)
    
    def resizeGL(self, width, height):
        gl.glViewport(0, 0, width, height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()

        GLU.gluOrtho2D(0, width, 0, height)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()
    
    def paintGL(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        # Display mouse position
        gl.glColor3f(0.0, 0.0, 0.0)
        self.renderText(10, self.height() - 20, 
                        f"Mouse Position: ({self.mouse_x}, {self.mouse_y})", QtGui.QFont("Arial", 12))
        
        self.renderButtons()
    

    def initializeButtons(self):
        insects = ['ant', 'beetle', 'spider', 'grasshopper', 'queen']
        x_pos = [self.width()//2 + i*self.width()//5 for i in range(-2, 3)]
        y_pos = [self.height()//2 for _ in range(5)]

        self.buttons_p1 = [ButtonPiece(x, y, 100, 1, insect) for x, y, insect in zip(x_pos, y_pos, insects)]
        self.buttons_p2 = [ButtonPiece(x, y, 100, 2, insect) for x, y, insect in zip(x_pos, y_pos, insects)]
        
    
    def renderButtons(self):
        if self.parent.player_turn == 1:
            for button in self.buttons_p1:
                button.render()
        else:
            for button in self.buttons_p2:
                button.render()
        
    
    def mouseMoveEvent(self, event):
        # Update mouse position
        self.mouse_x = event.x()
        self.mouse_y = event.y()
        self.update() # Trigger paint event


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    window = HiveGUI()
    window.show()

    sys.exit(app.exec_())
    