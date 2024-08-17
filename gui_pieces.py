from OpenGL.GL import *
import math

from drawing import *

class PieceMixin:
    def render(self, x=None, y=None):
        if not x:
            x = self.x
        if not y:
            y = self.y

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
        radius = self.width / 2
        distance = math.sqrt((mouse_x - self.x)**2 + (mouse_y - self.y)**2)
        return distance <= radius


class BoardPiece(PieceMixin):
    def __init__(self, x, y, width, player, tilename) -> None:
        self.x = x
        self.y = y
        self.width = width
        self.player = player
        self.insect = tilename.split('_')[0][:-1]
        self.name = tilename


class ButtonPiece(PieceMixin):
    def __init__(self, x, y, width, player, insect):
        self.x = x
        self.y = y
        self.width = width
        self.player = player
        self.insect = insect
    
    def render_n_remaining(self, n):
        glColor3f(0.0, 0.0, 0.0)
        draw_text(self.x - 3, self.y - 60, str(n))