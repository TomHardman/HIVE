from OpenGL.GL import *
import math

from .drawing import draw_hexagon, draw_insect
from .px_scale import PX_SCALE


class PieceMixin:
    def render(self, x=None, y=None):
        rx = (x * PX_SCALE) if x is not None else self.x
        ry = (y * PX_SCALE) if y is not None else self.y

        glEnable(GL_DEPTH_TEST)
        glClear(GL_DEPTH_BUFFER_BIT)

        if self.player == 1:
            glColor3f(0.988, 0.901, 0.589)
            draw_hexagon(rx, ry, self.width)
            glColor3f(0.955, 0.863, 0.515)
            draw_hexagon(rx, ry, self.width, fill=False)
        else:
            glColor3f(0.0, 0.0, 0.0)
            draw_hexagon(rx, ry, self.width)
            glColor3f(0.15, 0.15, 0.15)
            draw_hexagon(rx, ry, self.width, fill=False)

        glPushMatrix()
        glTranslatef(0, 0, 1)
        draw_insect(self.insect, rx, ry, self.width, self.player)
        glPopMatrix()

        glDisable(GL_DEPTH_TEST)

    def contains(self, mouse_x, mouse_y):
        radius = self.width / (PX_SCALE * 2)
        distance = math.sqrt((mouse_x - self.x / PX_SCALE) ** 2 + (mouse_y - self.y / PX_SCALE) ** 2)
        return distance <= radius


class BoardPiece(PieceMixin):
    """Rendering helper for a tile that is on the board."""

    def __init__(self, x, y, width, tile_state):
        """
        tile_state : TileState from the controller
        """
        self.x = x * PX_SCALE
        self.y = y * PX_SCALE
        self.width = width * PX_SCALE
        self.player = tile_state.player
        self.insect = tile_state.insect
        self.tile_idx = tile_state.tile_idx
        self.position = tile_state.position


class ButtonPiece(PieceMixin):
    """Rendering helper for a piece-type button in the selection tray."""

    def __init__(self, x, y, width, player, insect):
        self.x = x * PX_SCALE
        self.y = y * PX_SCALE
        self.width = width * PX_SCALE
        self.player = player
        self.insect = insect

    def render_n_remaining(self, n):
        from .drawing import draw_text
        glColor3f(0.0, 0.0, 0.0)
        draw_text(self.x - 3 * PX_SCALE, self.y - 60 * PX_SCALE, str(n))
