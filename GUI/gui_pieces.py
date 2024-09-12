from OpenGL.GL import *
import math

from .drawing import *
from .PX_SCALE import PX_SCALE # for making sure co-ordinates are the same as mouse co-ords


class PieceMixin:
    def render(self, x=None, y=None):
        if not x:
            x = self.x
        else:
            x = x * PX_SCALE
        if not y:
            y = self.y
        else:
            y = y * PX_SCALE

        # Enable depth testing
        glEnable(GL_DEPTH_TEST)
        
        # Clear the depth buffer
        glClear(GL_DEPTH_BUFFER_BIT)
        
        # Draw hexagon at a certain depth
        if self.player == 1:
            glColor3f(0.988, 0.901, 0.589) #cream
            draw_hexagon(x, y, self.width)
            glColor3f(0.955, 0.863, 0.515) #darker cream border
            draw_hexagon(x, y, self.width, fill=False)
        else:
            glColor3f(0.0, 0.0, 0.0)
            draw_hexagon(x, y, self.width)
            glColor3f(0.15, 0.15, 0.15) #lighter border
            draw_hexagon(x, y, self.width, fill=False)
        
        # Draw ant at a closer depth
        glPushMatrix()
        glTranslatef(0, 0, 1)
        draw_insect(self.insect, x, y, self.width)
        glPopMatrix()
        
        # Disable depth testing if not needed elsewhere
        glDisable(GL_DEPTH_TEST)
    
    def contains(self, mouse_x, mouse_y):
        # Basic point-in-polygon test for hexagon
        # Approximate by checking if within the circumscribed circle
        radius = self.width / (PX_SCALE * 2)
        distance = math.sqrt((mouse_x - self.x/PX_SCALE)**2 + (mouse_y - self.y/PX_SCALE)**2)
        return distance <= radius


class BoardPiece(PieceMixin):
    def __init__(self, x, y, width, tile, board):
        self.x = x * PX_SCALE # converts to same co-ord scale as mouse
        self.y = y * PX_SCALE
        self.width = width * PX_SCALE

        self.hive_tile = tile # points to HiveTile object
        self.player = tile.player
        self.insect = tile.name.split('_')[0][:-1]
        self.name = tile.name
        self.board = board

class ButtonPiece(PieceMixin):
    def __init__(self, x, y, width, player, insect, board):
        self.x = x * PX_SCALE
        self.y = y * PX_SCALE
        self.width = width * PX_SCALE
        self.player = player
        self.insect = insect
        self.board = board
    
    def render_n_remaining(self, n):
        glColor3f(0.0, 0.0, 0.0)
        draw_text(self.x - 3 * PX_SCALE, self.y - 60 * PX_SCALE, str(n))