import sys
import math
import time
from collections import defaultdict

from PyQt5 import QtGui       # extends QtCore with GUI functionality
from PyQt5 import QtWidgets
from PyQt5 import QtOpenGL 
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QEventLoop

import OpenGL.GL as gl
from OpenGL import GLU

from .gui_pieces import BoardPiece, ButtonPiece
from .drawing import draw_hexagon
from game import HiveBoard, ACTIONSPACE
from .PX_SCALE import PX_SCALE
from AI.DQL import ExperienceReplay, RewardCalculator, get_graph_from_state, REWARDS_DICT, Transition


class HiveGUI(QtWidgets.QMainWindow):   
    def __init__(self, board: HiveBoard, rl_debug=False):
        super().__init__()
        self.resize(1000, 800)
        self.setWindowTitle('HIVE GUI')

        # game state
        self.board = board
        self.placing_tile = None   # tile being placed by player - stored as ButtonPiece object
        self.moving_tile = None    # tile being moved by player - stored as BoardPiece object

        # general layout
        self.splitter = QtWidgets.QSplitter(Qt.Vertical)
        self.board_canvas = BoardCanvas(self)
        self.selection_canvas = SelectionCanvas(self)
        self.splitter.addWidget(self.board_canvas)
        self.splitter.addWidget(self.selection_canvas)
        self.setCentralWidget(self.splitter)

        # player attributes to store if a certain player is an artificial agent
        self.player1 = None
        self.player2 = None
        self.p1_memory = [[self.board.get_game_state(1), None]] # store state action pairs for p1
        self.p2_memory = [] # store state action pairs for p2

        # RL debugging
        self.rl_debug = rl_debug
        if rl_debug:
            self.replay = ExperienceReplay(capacity=1000) 
            self.reward_calc = RewardCalculator(rewards_dict=REWARDS_DICT)
    
    def set_player(self, player, agent):
        if player == 1:
            self.player1 = agent
        elif player == 2:
            self.player2 = agent
        else:
            raise ValueError(f'{player} not a valid player number')
        
    def update_GUI(self):
        self.board_canvas.update()
        self.selection_canvas.update()
        self.check_game_over()

        if self.player1 and self.player_turn==1:
            QApplication.processEvents(QEventLoop.ExcludeUserInputEvents)
            time.sleep(1)
            action = self.player1.sample_action()
            self.update_from_board()
            self.update_memory(action)
        
        if self.player2 and self.player_turn==2:
            QApplication.processEvents(QEventLoop.ExcludeUserInputEvents)
            time.sleep(1)
            action = self.player2.sample_action()
            self.update_from_board()
            self.update_memory(action)
        
        self.board_canvas.update()
        self.selection_canvas.update()
        self.check_game_over()

    @property
    def player_turn(self):
        return self.board.get_player_turn()
    
    @property
    def pieces_remaining(self):
        return self.board.pieces_remaining
    
    def check_game_over(self):
        if victor := self.board.game_over():
            self.close()
            print(f'Player {victor} Wins!')
    
    def test_valid(self):
        for pos, info_list in self.board_canvas.tiles:
            for tile_bp, _ in info_list:
                tile_ht = tile_bp.tile # tile name of BoardPiece object
            assert (pos == tile_ht.position)
    
    def update_memory(self, action):
        """
        Updates memory of state action pairs
        """
        if self.player_turn == 2: # player 1 has just been
            self.p1_memory[-1][1] = action
            self.p2_memory.append([self.board.get_game_state(2), None])
        else: # player 2 has just been
            self.p2_memory[-1][1] = action
            self.p1_memory.append([self.board.get_game_state(1), None])
            self.rl_update()

    def update_from_board(self):
        """
        Updates the board_canvas.tiles dictionary with the current state of the board
        This allows an artificial player to interact directly with the HIVEBoard object
        and the changes to be shown in the GUI
        """
        # Create BoardPiece object for tile if it doesn't already exist
        for pos, tiles in self.board.tile_positions.items():
            canvas_pos = self.board_canvas.get_canvas_coords(pos)
            for tile in tiles:
                if tile not in self.board_canvas.bp_tile_dict:
                    tile_bp = BoardPiece(canvas_pos[0], canvas_pos[1], 100, tile, self.board)
                    self.board_canvas.tiles[pos].append((tile_bp, canvas_pos))
                    self.board_canvas.bp_tile_dict[tile] = tile_bp
        
        # Update position of other BoardPiece tiles
        for pos, info_list in self.board_canvas.tiles.items():
            for tile_bp, canvas_pos in info_list:
                correct_pos = tile_bp.hive_tile.position
                canvas_pos = self.board_canvas.get_canvas_coords(correct_pos)
                if correct_pos != pos:
                    self.board_canvas.tiles[pos].pop()
                    self.board_canvas.tiles[correct_pos].append((tile_bp, canvas_pos))
                    return # we should only ever have to update the position of one tile


    def rl_update(self):
        """
        Update the replay memory with the current state of the board
        """
        if self.rl_debug:
            s = get_graph_from_state(self.p1_memory[-2][0], 1)
            s_prime = get_graph_from_state(self.p1_memory[-1][0], 1)
            action = self.p1_memory[-2][1]
            reward = self.reward_calc(1, self.p1_memory[-2][0], self.p1_memory[-1][0])
            transition = Transition(s, action, reward, s_prime)
            self.replay.push(transition)


class BoardCanvas(QtOpenGL.QGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        # mouse position
        self.setMouseTracking(True)  # Enable mouse tracking
        self.contains_mouse = False
        self.dragging = False
        self.mouse_x = 0
        self.mouse_y = 0
        self.pan_x = 0
        self.pan_y = 0

        self.tiles = defaultdict(list) # dictionary mapping board co-ordinate to BoardPiece object and canvas position
        self.bp_tile_dict = defaultdict(list) # dictionary mapping HiveTile object to BoardPiece object
    
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
        
        if self.tiles.items():
            for board_pos, tiles_list in self.tiles.items():
                for tile, canvas_pos in tiles_list:
                    if self.parent.moving_tile and tile == self.parent.moving_tile:
                        pass
                    else:
                        tile.render(canvas_pos[0] - self.pan_x, canvas_pos[1] + self.pan_y)
        
        if self.parent.placing_tile:
            self.display_valid_moves()
            if self.contains_mouse:
                self.parent.placing_tile.render(self.mouse_x, self.height()-self.mouse_y) # render tile being placed in mouse position
        
        if self.parent.moving_tile:
            self.display_valid_moves()
            self.parent.moving_tile.render(self.mouse_x, (self.height() - self.mouse_y))
        
        # Display player turn
        gl.glColor3f(0.0, 0.0, 0.0)
        self.renderText(10, 20, 
                        f"Player Turn: {self.parent.player_turn}", QtGui.QFont("Arial", 12))
    
    def display_valid_moves(self):
        if self.parent.placing_tile:
            valid_placements = self.parent.board.get_valid_placements(self.parent.player_turn,
                                                                      self.parent.placing_tile.insect)
            for pos in valid_placements:
                board_pos = self.get_canvas_coords(pos)
                gl.glColor3f(0.0, 1.0, 0.0)  # Green
                draw_hexagon((board_pos[0] - self.pan_x) * PX_SCALE, 
                             (board_pos[1] + self.pan_y) * PX_SCALE, 
                             99 * PX_SCALE, fill=False)
                
        if self.parent.moving_tile:
            tilename = self.parent.moving_tile.name
            tile_object = self.parent.board.name_obj_mapping[tilename]
            valid_moves = tile_object.get_valid_moves()

            for pos in valid_moves:
                board_pos = self.get_canvas_coords(pos)
                gl.glColor3f(0.0, 1.0, 0.0)  # Green
                draw_hexagon((board_pos[0] - self.pan_x) * PX_SCALE, 
                             (board_pos[1] + self.pan_y) * PX_SCALE, 
                             99 * PX_SCALE, fill=False)
    
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
        if self.dragging:
            delta_x = self.mouse_x - event.x()
            delta_y = self.mouse_y - event.y()
            self.pan_x += delta_x
            self.pan_y += delta_y

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
            if chosen_pos := self.valid_move_clicked(event.x()+self.pan_x, 
                                                     event.y()+self.pan_y):         
                tilename = self.parent.moving_tile.name
                tile_object = self.parent.board.name_obj_mapping[tilename]
                original_pos = tile_object.position
                
                # Place tile in chosen position
                self.parent.board.move_tile(tile_object, chosen_pos, update_turns=True)

                # Update self.tiles
                canvas_pos = self.get_canvas_coords(chosen_pos)
                self.tiles[chosen_pos].append((self.parent.moving_tile, canvas_pos))
                self.tiles[original_pos].pop()

                # update memory with action
                tile_idx = ACTIONSPACE[tilename.split('_')[0]]
                self.parent.update_memory((chosen_pos, tile_idx))
        
            self.parent.moving_tile = None
        
        elif self.parent.placing_tile:
            if chosen_pos := self.valid_placement_clicked(event.x()+self.pan_x, 
                                                          event.y()+self.pan_y):
                insect = self.parent.placing_tile.insect
                player = self.parent.player_turn
                tile_number = str(self.parent.pieces_remaining[player-1][insect])
                tilename = insect + tile_number + '_p' + str(player)
                tile_object = self.parent.board.name_obj_mapping[tilename]

                # Place tile in chosen position
                self.parent.board.place_tile(tile_object, chosen_pos)

                # Render tile in chosen position
                canvas_pos = self.get_canvas_coords(chosen_pos)
                tile_bp = BoardPiece(canvas_pos[0], canvas_pos[1], 100, tile_object, self.parent.board)
                self.tiles[chosen_pos].append((tile_bp, canvas_pos))
                self.bp_tile_dict[tile_object] = tile_bp

                # update memory with action
                tile_idx = ACTIONSPACE[tilename.split('_')[0]]
                self.parent.update_memory((chosen_pos, tile_idx))
                
            self.parent.placing_tile = None
        
        else: # if not currently in moving or placing mode
            if tile_clicked := self.get_tile_clicked(event.x() + self.pan_x,
                                                     event.y() + self.pan_y):
                self.parent.moving_tile = tile_clicked

            self.dragging = True
                
        self.parent.update_GUI()

    def mouseReleaseEvent(self, event):
        self.dragging = False


    def get_tile_clicked(self, x, y):
        """If a valid tile is clicked and can be moved returns the BoardPiece object for tile"""
        tile_bp = None
        for pos, tiles in self.parent.board.tile_positions.items():
            canvas_pos = self.get_canvas_coords(pos)
            mouse_pos = (canvas_pos[0], self.height() - canvas_pos[1])
            radius = 50
            distance = math.sqrt((x - mouse_pos[0])**2 + (y - mouse_pos[1])**2)
            if distance <= radius * 0.9:
                tile_bp = self.tiles[pos][-1][0]
                break
        
        if tile_bp:
            assert(tile_bp.name == tiles[-1].name)
            # outside of for loop as get_valid_moves would change dict keys while iterating
            if tiles[-1].get_valid_moves() and tile_bp.player == self.parent.player_turn:
                return tile_bp
                  
    def valid_placement_clicked(self, x, y):
        """If in placing tile mode checks if position clicked is a valid placement and
        returns board position (in hex co-ordinates) if so"""
        for pos in self.parent.board.get_valid_placements(self.parent.player_turn,
                                                          self.parent.placing_tile.insect):
            canvas_pos = self.get_canvas_coords(pos)
            mouse_pos = (canvas_pos[0], self.height() - canvas_pos[1])
            radius = 50
            distance = math.sqrt((x - mouse_pos[0])**2 + (y - mouse_pos[1])**2)
            if distance <= radius * 0.9:
                return pos
        return None
    
    def valid_move_clicked(self, x, y):
        """If in moving tile mode checks if position clicked is a valid move and
        returns board position (in hex co-ordinates) if so"""
        tilename = self.parent.moving_tile.name
        tile_obj = self.parent.board.name_obj_mapping[tilename] # get tile object
        
        for pos in tile_obj.get_valid_moves():
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

        self.buttons_p1 = [ButtonPiece(x, y, 2/3 * self.height(), 1, insect, self.parent.board) 
                           for x, y, insect in zip(x_pos, y_pos, insects)]
        self.buttons_p2 = [ButtonPiece(x, y, 2/3 * self.height(), 2, insect, self.parent.board) 
                           for x, y, insect in zip(x_pos, y_pos, insects)]
        self.buttons = [self.buttons_p1, self.buttons_p2]
        
    def renderButtons(self):
        player = self.parent.player_turn
        for i in range(len(self.buttons[0])):
                button = self.buttons[player-1][i]
                if self.parent.board.get_valid_placements(self.parent.player_turn,
                                                          button.insect):
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
        if self.parent.moving_tile:
            self.parent.moving_tile = None

        if clicked_tile := self.get_button_clicked(event.x(), event.y()):
            self.parent.placing_tile = clicked_tile
            valid_placements = self.parent.board.get_valid_placements(self.parent.player_turn,
                                                                      self.parent.placing_tile.insect)
            
            if not valid_placements: # if no valid placements, don't allow tile to be placed
                self.parent.placing_tile = None
        else:
            self.parent.placing_tile = None
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

