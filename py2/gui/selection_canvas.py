import math

from PyQt5 import QtGui
from PyQt5 import QtOpenGL
from PyQt5.QtCore import pyqtSignal

import OpenGL.GL as gl
from OpenGL import GLU

from .gui_pieces import ButtonPiece
from .px_scale import PX_SCALE

_INSECTS = ['queen', 'ant', 'beetle', 'grasshopper', 'spider']


class SelectionCanvas(QtOpenGL.QGLWidget):
    """
    Renders the piece-selection tray. Never touches the game engine directly.

    Emits signals for user actions; the controller handles them.
    """

    piece_selected = pyqtSignal(str)   # insect name ('ant', 'queen', ...)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(150)
        self.setMouseTracking(True)

        self.mouse_x = 0
        self.mouse_y = 0

        # State set by controller
        self._player_turn: int = 1
        self._pieces_remaining: dict = {}   # insect → count for current player

        # ButtonPiece layout (rebuilt in resizeGL / first paint)
        self._buttons: list[ButtonPiece] = []
        self._buttons_dirty = True

    # ============= Controller-facing API =============

    def set_player_turn(self, player: int):
        self._player_turn = player
        self._buttons_dirty = True
        self.update()

    def set_pieces_remaining(self, remaining: dict):
        """remaining: insect → count for the current player."""
        self._pieces_remaining = remaining
        self._buttons_dirty = True
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
        self._buttons_dirty = True

    def paintGL(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        if self._buttons_dirty:
            self._rebuild_buttons()

        for button in self._buttons:
            count = self._pieces_remaining.get(button.insect, 0)
            if count > 0:
                button.render()
                button.render_n_remaining(count)

    # ============= Internal helpers =============

    def _rebuild_buttons(self):
        n = len(_INSECTS)
        spacing = self.width() // (n + 1)
        y = self.height() // 2
        btn_width = int(self.height() * 2 / 3)

        self._buttons = [
            ButtonPiece(
                spacing * (i + 1),
                y,
                btn_width,
                self._player_turn,
                insect,
            )
            for i, insect in enumerate(_INSECTS)
        ]
        self._buttons_dirty = False

    def _button_at(self, x, y) -> ButtonPiece | None:
        """Return the ButtonPiece under (x, y), or None."""
        for button in self._buttons:
            count = self._pieces_remaining.get(button.insect, 0)
            if count > 0 and button.contains(x, y):
                return button
        return None

    # ============= Mouse events =============

    def mouseMoveEvent(self, event):
        self.mouse_x = event.x()
        self.mouse_y = event.y()
        self.update()

    def mousePressEvent(self, event):
        if button := self._button_at(event.x(), event.y()):
            self.piece_selected.emit(button.insect)
