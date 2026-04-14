import math
from collections import defaultdict

from PyQt5 import QtGui
from PyQt5 import QtOpenGL
from PyQt5.QtCore import pyqtSignal

import OpenGL.GL as gl
from OpenGL import GLU

from .drawing import draw_hexagon
from .gui_pieces import BoardPiece
from .px_scale import PX_SCALE


class BoardCanvas(QtOpenGL.QGLWidget):
    """
    Renders the hex board. Never touches the game engine directly.

    Emits signals for user actions; the controller handles them.
    """

    board_tile_clicked = pyqtSignal(tuple)     # user clicked a placed tile: (q, r)
    move_requested     = pyqtSignal(int, tuple)   # tile_idx, to_pos
    whitespace_clicked = pyqtSignal()          # user clicked an empty area

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setMouseTracking(True)

        self.mouse_x = 0
        self.mouse_y = 0
        self.contains_mouse = False
        self.pan_x = 0
        self.pan_y = 0
        self.dragging = False

        # Rendering state (set by controller via set_board_state / highlight_*)
        self._board_state: dict = {}          # (q,r) → list[TileState]
        self._board_pieces: dict = {}         # (q,r) → list[BoardPiece]
        self._valid_moves: list = []          # list of (q,r) to highlight
        self._valid_placements: list = []     # list of (q,r) to highlight
        self._selected_tile_idx: int | None = None  # tile being moved
        self._placing_insect: str | None = None     # insect type being placed

    # ============= Controller-facing API =============

    def set_board_state(self, board_state: dict):
        """board_state: (q,r) → list[TileState]"""
        self._board_state = board_state
        self._board_pieces = {}
        for pos, tile_states in board_state.items():
            canvas_pos = self.get_canvas_coords(pos)
            self._board_pieces[pos] = [
                BoardPiece(canvas_pos[0], canvas_pos[1], 100, ts)
                for ts in tile_states
            ]
        self.update()

    def highlight_moves(self, positions: list, tile_idx: int):
        self._valid_moves = positions
        self._selected_tile_idx = tile_idx
        self._valid_placements = []
        self.update()

    def highlight_placements(self, positions: list, tile_idx: int, insect: str):
        self._valid_placements = positions
        self._placing_insect = insect
        self._selected_tile_idx = tile_idx
        self._valid_moves = []
        self.update()

    def clear_highlights(self):
        self._valid_moves = []
        self._valid_placements = []
        self._selected_tile_idx = None
        self._placing_insect = None
        self.update()

    # ============= OpenGL =============

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

        gl.glColor3f(0.0, 0.0, 0.0)
        self.renderText(10, self.height() - 20,
                        f"Mouse: ({self.mouse_x}, {self.mouse_y})",
                        QtGui.QFont("Arial", 12))

        # Draw tiles
        for pos, pieces in self._board_pieces.items():
            canvas_pos = self.get_canvas_coords(pos)
            for piece in pieces:
                piece.render(canvas_pos[0] - self.pan_x, canvas_pos[1] + self.pan_y)

        # Draw valid move highlights
        for pos in self._valid_moves:
            cp = self.get_canvas_coords(pos)
            gl.glColor3f(0.0, 1.0, 0.0)
            draw_hexagon((cp[0] - self.pan_x) * PX_SCALE,
                         (cp[1] + self.pan_y) * PX_SCALE,
                         99 * PX_SCALE, fill=False)

        # Draw valid placement highlights
        for pos in self._valid_placements:
            cp = self.get_canvas_coords(pos)
            gl.glColor3f(0.0, 1.0, 0.0)
            draw_hexagon((cp[0] - self.pan_x) * PX_SCALE,
                         (cp[1] + self.pan_y) * PX_SCALE,
                         99 * PX_SCALE, fill=False)

        # Player turn indicator
        if hasattr(self, '_player_turn'):
            gl.glColor3f(0.0, 0.0, 0.0)
            self.renderText(10, 20,
                            f"Player Turn: {self._player_turn}",
                            QtGui.QFont("Arial", 12))

    # ============= Coordinate mapping =============

    def get_canvas_coords(self, board_pos: tuple) -> tuple:
        x0 = self.width() // 2
        y0 = self.height() // 2
        hex_width = 100
        delta = hex_width * math.sqrt(3) / 2
        delta1 = [delta * math.sqrt(3) / 2, delta / 2]
        delta2 = [0, delta]
        q, r = board_pos
        return (x0 + q * delta1[0] + r * delta2[0],
                y0 + q * delta1[1] + r * delta2[1])

    def _canvas_to_board(self, cx, cy) -> tuple | None:
        """Find the board hex closest to canvas point (cx, cy). Returns (q,r) or None."""
        best_pos = None
        best_dist = float('inf')
        radius = 50
        for pos in list(self._board_state.keys()) + list(self._valid_moves) + list(self._valid_placements):
            cp = self.get_canvas_coords(pos)
            mouse = (cp[0], self.height() - cp[1])
            dist = math.sqrt((cx - mouse[0]) ** 2 + (cy - mouse[1]) ** 2)
            if dist < radius * 0.9 and dist < best_dist:
                best_dist = dist
                best_pos = pos
        return best_pos

    # ============= Mouse events =============

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.pan_x += self.mouse_x - event.x()
            self.pan_y += self.mouse_y - event.y()
        self.mouse_x = event.x()
        self.mouse_y = event.y()
        self.contains_mouse = True
        self.update()

    def mousePressEvent(self, event):
        cx = event.x() + self.pan_x
        cy = event.y() + self.pan_y

        if self._valid_moves:
            # In move mode: check if a highlighted destination was clicked
            for pos in self._valid_moves:
                cp = self.get_canvas_coords(pos)
                mouse = (cp[0], self.height() - cp[1])
                if math.sqrt((cx - mouse[0]) ** 2 + (cy - mouse[1]) ** 2) <= 50 * 0.9:
                    self.move_requested.emit(self._selected_tile_idx, pos)
                    return

        elif self._valid_placements:
            # In placement mode: check if a highlighted placement was clicked
            for pos in self._valid_placements:
                cp = self.get_canvas_coords(pos)
                mouse = (cp[0], self.height() - cp[1])
                if math.sqrt((cx - mouse[0]) ** 2 + (cy - mouse[1]) ** 2) <= 50 * 0.9:
                    self.parent.placement_requested.emit(self._selected_tile_idx, pos)
                    return

        else:
            # No active selection: check if a board tile was clicked
            for pos, pieces in self._board_pieces.items():
                if not pieces:
                    continue
                cp = self.get_canvas_coords(pos)
                mouse = (cp[0], self.height() - cp[1])
                if math.sqrt((cx - mouse[0]) ** 2 + (cy - mouse[1]) ** 2) <= 50 * 0.9:
                    self.board_tile_clicked.emit(pos)
                    return
            
            self.dragging = True

        self.whitespace_clicked.emit()

    def mouseReleaseEvent(self, event):
        self.dragging = False
