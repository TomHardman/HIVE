from OpenGL.GL import *
import math

from drawing import *


class BoardPiece:
    def __init__() -> None:
        pass

class ButtonPiece:
    def __init__(self, x, y, width, player, insect):
        self.x = x
        self.y = y
        self.width = width
        self.player = player
        self.insect = insect
        pass

    def render(self):
        # Enable depth testing
        glEnable(GL_DEPTH_TEST)
        
        # Clear the depth buffer
        glClear(GL_DEPTH_BUFFER_BIT)
        
        # Draw hexagon at a certain depth
        if self.player == 1:
            glColor3f(0.988, 0.901, 0.589) #cream
            draw_hexagon(self.x, self.y, self.width)
        else:
            glColor3f(0.0, 0.0, 0.0)
            draw_hexagon(self.x, self.y, self.width)
        
        # Draw ant at a closer depth
        glPushMatrix()
        glTranslatef(0, 0, 1)  # Keep ant at the default depth
        draw_insect(self.insect, self.x, self.y, self.width)
        glPopMatrix()
        
        # Disable depth testing if not needed elsewhere
        glDisable(GL_DEPTH_TEST)
