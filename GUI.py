import sys
import math

from PyQt5 import QtGui       # extends QtCore with GUI functionality
from PyQt5 import QtWidgets
from PyQt5 import QtOpenGL 
from PyQt5.QtCore import Qt

import OpenGL.GL as gl
from OpenGL import GLU

from gui_pieces import BoardPiece, ButtonPiece
from board import HiveBoard
from drawing import draw_hexagon


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
        
        # game state
        self.board = HiveBoard()
        self.placing_tile = None   # tile being placed by player - stored as ButtonPiece object
        self.moving_tile = None    # tile being moved by player - stored as BoardPiece object
    
    def update_GUI(self):
        self.board_canvas.update()
        self.selection_canvas.update()
    
    @property
    def player_turn(self):
        return self.board.get_player_turn()
    
    @property
    def pieces_remaining(self):
        return self.board.pieces_remaining


class BoardCanvas(QtOpenGL.QGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        # mouse position
        self.setMouseTracking(True)  # Enable mouse tracking
        self.contains_mouse = False
        self.mouse_x = 0
        self.mouse_y = 0

        self.tiles = {} # dictionary mapping BoardPiece object to board position and canvas position
    
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
        
        if self.parent.placing_tile:
            self.display_valid_moves()
            if self.contains_mouse:
                self.parent.placing_tile.render(self.mouse_x, self.height()-self.mouse_y) # render tile being placed in mouse position
        
        for tile, (board_pos, canvas_pos) in self.tiles.items():
            tile.render(canvas_pos[0], canvas_pos[1])
        
        # Display player turn
        gl.glColor3f(0.0, 0.0, 0.0)
        self.renderText(10, 20, 
                        f"Player Turn: {self.parent.player_turn}", QtGui.QFont("Arial", 12))
    
    def display_valid_moves(self):
        if self.parent.placing_tile:
            valid_placements = self.parent.board.get_valid_placements(self.parent.player_turn)
            for pos in valid_placements:
                board_pos = self.get_canvas_coords(pos)
                gl.glColor3f(0.0, 1.0, 0.0)  # Green
                draw_hexagon(board_pos[0], board_pos[1], 99, fill=False)
                
        if self.parent.moving_tile:
            pass
    
    def get_canvas_coords(self, board_pos):
        x0 = self.width() // 2
        y0 = self.height() // 2
        
        hex_width = 100
        delta = hex_width * math.sqrt(3)/2

        delta1 = [delta * math.sqrt(3)/2, delta/2]
        delta2 = [0, delta]

        canvas_pos = (x0 + board_pos[0]*delta1[0] + board_pos[1]*delta2[0], 
                      y0 + board_pos[0]*delta1[1] + board_pos[1]*delta2[1])
        
        return canvas_pos

    def mouseMoveEvent(self, event):
        # Update mouse position
        self.mouse_x = event.x()
        self.mouse_y = event.y()
        self.contains_mouse = True
        
        # if mouse is within board canvas, update board canvas to not show tile being placed 
        if self.mouse_y > self.parent.selection_canvas.height():
            self.parent.selection_canvas.contains_mouse = False
        
        self.parent.update_GUI() # Trigger paint event
    
    def mousePressEvent(self, event):
        
        if self.parent.moving_tile:
            pass
        
        elif self.parent.placing_tile:
            if chosen_pos := self.valid_placement_clicked(event.x(), event.y()):
                # Place tile in chosen position
                insect = self.parent.placing_tile.insect
                player = self.parent.player_turn
                tile_number = str(self.parent.pieces_remaining[player-1][insect])
                tilename = insect + tile_number + '_p' + str(player)
                tile_object = self.parent.board.name_obj_mapping[tilename]
                self.parent.board.place_tile(tile_object, chosen_pos)

                # Render tile in chosen position
                canvas_pos = self.get_canvas_coords(chosen_pos)
                tile = BoardPiece(canvas_pos[0], canvas_pos[1], 100, player, tilename)
                self.tiles[tile] = (chosen_pos, canvas_pos)

            self.parent.placing_tile = None
        
        self.parent.update_GUI()

    def get_tile_clicked(self, x, y):
        return False
    
    def valid_placement_clicked(self, x, y):
        for pos in self.parent.valid_placements:
            canvas_pos = self.get_canvas_coords(pos)
            mouse_pos = (canvas_pos[0], self.height() - canvas_pos[1])
            radius = 50
            distance = math.sqrt((x - mouse_pos[0])**2 + (y - mouse_pos[1])**2)
            if distance <= radius * 0.9:
                return pos
        return None


class SelectionCanvas(QtOpenGL.QGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFixedSize(1000, 150)

        # mouse position
        self.setMouseTracking(True)  # Enable mouse tracking
        self.contains_mouse = False
        self.mouse_x = 0
        self.mouse_y = 0

        self.initializeButtons()
        self.placing_tile = None
    
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
        
        if self.parent.placing_tile and self.contains_mouse:
            self.renderText(10, 20,
                            f"Tile Clicked: {self.parent.placing_tile.insect}", QtGui.QFont("Arial", 12))
            self.parent.placing_tile.render(self.mouse_x, self.height()-self.mouse_y)
        
        self.renderButtons()
    
    def initializeButtons(self):
        insects = ['ant', 'beetle', 'spider', 'grasshopper', 'queen']
        x_pos = [self.width()//2 + i*self.width()//5 for i in range(-2, 3)]
        y_pos = [self.height()//2 for _ in range(5)]

        self.buttons_p1 = [ButtonPiece(x, y, 100, 1, insect) for x, y, insect in zip(x_pos, y_pos, insects)]
        self.buttons_p2 = [ButtonPiece(x, y, 100, 2, insect) for x, y, insect in zip(x_pos, y_pos, insects)]
        self.buttons = [self.buttons_p1, self.buttons_p2]
        
    def renderButtons(self):
        player = self.parent.player_turn
        for i in range(len(self.buttons[0])):
                button = self.buttons[player-1][i]
                if self.parent.pieces_remaining[player-1][button.insect] > 0:
                    button.render()
                    button.render_n_remaining(self.parent.pieces_remaining[player-1][button.insect])
        
    def mouseMoveEvent(self, event):
        # Update mouse position
        self.mouse_x = event.x()
        self.mouse_y = event.y()
        self.contains_mouse = True

        # if mouse is within selection canvas, update board canvas to not show tile being placed  
        if self.mouse_y < self.parent.selection_canvas.height():
            self.parent.board_canvas.contains_mouse = False
        
        self.parent.update_GUI() # Trigger paint event
    
    def mousePressEvent(self, event):
        # Check if a button is clicked
        if clicked_tile := self.get_button_clicked(event.x(), event.y()):
            self.parent.placing_tile = clicked_tile
            self.parent.valid_placements = self.parent.board.get_valid_placements(self.parent.player_turn)
            
            if not self.parent.valid_placements: # if no valid placements, don't allow tile to be placed
                self.parent.placing_tile = None
        else:
            self.parent.placing_tile = None
            self.parent.valid_placements = []
        self.parent.update_GUI() # Trigger paint event

    def get_button_clicked(self, x, y):
        if self.parent.player_turn == 1:
            for button in self.buttons_p1:
                if button.contains(x, y):
                    return button
        else:
            for button in self.buttons_p2:
                if button.contains(x, y):
                    return button
        return None


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    window = HiveGUI()
    window.show()

    sys.exit(app.exec_())
    