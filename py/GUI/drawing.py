from OpenGL.GL import *
from OpenGL.GLUT import glutBitmapCharacter, GLUT_BITMAP_8_BY_13
import math

from .PX_SCALE import PX_SCALE


def draw_hexagon(x0, y0, width, fill=True):
    """
    Draw a filled hexagon of a specified width.

    :param x0: The x-coordinate of the center of the hexagon.
    :param y0: The y-coordinate of the center of the hexagon.
    :param width: The distance between two opposite vertices of the hexagon.
    """
    radius = width / 2  # The radius of the circumscribed circle

    if fill:
        glBegin(GL_POLYGON)
    else:
        glLineWidth(4.0 * PX_SCALE) 
        glBegin(GL_LINE_LOOP)
    
    for i in range(6):  # Hexagon has 6 vertices
        angle = 2 * math.pi * i / 6
        x = radius * math.cos(angle) + x0
        y = radius * math.sin(angle) + y0
        glVertex2f(x, y)
    
    glEnd()
    glLineWidth(1.0)


def draw_ellipse(x0, y0, h_rad, v_rad, num_segments=100):
    """
    Draw a filled ellipse with the specified width and height.
    
    :param x0: The x-coordinate of the center of the ellipse.
    :param y0: The y-coordinate of the center of the ellipse.
    :param h_rad: Half the width of the ellipse (horizontal radius).
    :param v_rad: Half the height of the ellipse (vertical radius).
    :param num_segments: Number of segments used to approximate the ellipse.
    """
    glBegin(GL_TRIANGLE_FAN)
    # Center of the ellipse
    glVertex2f(x0, y0)
    
    for i in range(num_segments + 1):
        angle = 2 * math.pi * i / num_segments
        x = x0 + h_rad * math.cos(angle)
        y = y0 + v_rad * math.sin(angle)
        glVertex2f(x, y)
    
    glEnd()


def draw_text(x, y, text):
    """Draws some text"""
    glRasterPos2f(x, y)  # Set the position for the text
    for char in text:
        glutBitmapCharacter(GLUT_BITMAP_8_BY_13, ord(char))


def draw_ant(x0, y0, width):
    """
    Draw a simple ant inside a hexagon of specified width.
    
    :param x0: The x-coordinate of the center of the hexagon.
    :param y0: The y-coordinate of the center of the hexagon.
    :param width: The width of the hexagon (distance between opposite vertices).
    """
    segment_radius = width / 10

    glColor3f(0.01, 0.29, 0.88)

    for i , delta_y in enumerate([-1.8*segment_radius, 0, 1.8*segment_radius]):
        draw_ellipse(x0, y0 + delta_y, 0.75*segment_radius, segment_radius)
        
        glLineWidth(2.0 * PX_SCALE)
        glBegin(GL_LINES)
        if i == 0:
            # Lower legs
            glVertex2f(x0 - 0.75*segment_radius, y0 + delta_y)
            glVertex2f(x0 - 1.5*segment_radius, y0 + delta_y - 1.5*segment_radius)
            glVertex2f(x0 + 0.75*segment_radius, y0 + delta_y)
            glVertex2f(x0 + 1.5*segment_radius, y0 + delta_y - 1.5*segment_radius)

        if i == 1:
            # Middle legs
            glVertex2f(x0 - 0.7*segment_radius, y0 + delta_y)
            glVertex2f(x0 - 2.0*segment_radius, y0 + delta_y)
            glVertex2f(x0 + 0.7*segment_radius, y0 + delta_y)
            glVertex2f(x0 + 2.0*segment_radius, y0 + delta_y)
        
        if i == 2:
            # Upper legs
            glVertex2f(x0 - 0.75*segment_radius, y0 + delta_y)
            glVertex2f(x0 - 1.5*segment_radius, y0 + delta_y + 1.5*segment_radius)
            glVertex2f(x0 + 0.75*segment_radius, y0 + delta_y)
            glVertex2f(x0 + 1.5*segment_radius, y0 + delta_y + 1.5*segment_radius)

            #Antennae
            glVertex2f(x0, y0 + delta_y)
            glVertex2f(x0 - 0.75*segment_radius, y0 + delta_y + 1.5*segment_radius)
            glVertex2f(x0, y0 + delta_y)
            glVertex2f(x0 + 0.75*segment_radius, y0 + delta_y + 1.5*segment_radius)

        glEnd()
        glLineWidth(1.0)


def draw_spider(x0, y0, width):
    """Draws Spider inside a hexagon of specified width.
    
    :param x0: The x-coordinate of the center of the hexagon.
    :param y0: The y-coordinate of the center of the hexagon.
    :param width: The width of the hexagon (distance between opposite vertices).
    """
    glColor3f(0.48, 0.25, 0.07)  # Brown color for the text
    segment_radius = width / 7
    draw_ellipse(x0, y0, 0.75*segment_radius, segment_radius)

    # pincers
    glLineWidth(2.0 * PX_SCALE)
    glBegin(GL_LINES)
    glVertex2f(x0, y0)
    glVertex2f(x0 + width/22, y0 + width/5)
    glVertex2f(x0, y0)
    glVertex2f(x0 - width/22, y0 + width/5)
    glEnd()

    # top legs
    glLineWidth(2.0 * PX_SCALE)
    glBegin(GL_LINES)
    glVertex2f(x0, y0)
    glVertex2f(x0 + width/7, y0 + width/3)
    glVertex2f(x0, y0)
    glVertex2f(x0 - width/7, y0 + width/3)
    glEnd()

    # top mid legs
    glLineWidth(2.0 * PX_SCALE)
    glBegin(GL_LINES)
    glVertex2f(x0, y0)
    glVertex2f(x0 + width/3, y0 + width/7.5)
    glVertex2f(x0, y0)
    glVertex2f(x0 - width/3, y0 + width/7.5)
    glEnd()

    # bottom mid legs
    glLineWidth(2.0 * PX_SCALE)
    glBegin(GL_LINES)
    glVertex2f(x0, y0)
    glVertex2f(x0 + width/4.2, y0 - width/8.5)
    glVertex2f(x0, y0)
    glVertex2f(x0 - width/4.2, y0 - width/8.5)
    glEnd()

    # bottom legs
    glLineWidth(2.0 * PX_SCALE)
    glBegin(GL_LINES)
    glVertex2f(x0, y0)
    glVertex2f(x0 + width/6, y0 - width/3.2)
    glVertex2f(x0, y0)
    glVertex2f(x0 - width/6, y0 - width/3.2)
    glEnd()

    glLineWidth(1.0)


def draw_grasshopper(x0, y0, width):
    """
    Draws Grasshopper inside a hexagon of specified width.
    
    :param x0: The x-coordinate of the center of the hexagon.
    :param y0: The y-coordinate of the center of the hexagon.
    :param width: The width of the hexagon (distance between opposite vertices).
    """
    glColor3f(0.13, 0.7, 0.1)  # Green color

    glBegin(GL_POLYGON)
    glVertex2f(x0 + width/6, y0)
    glVertex2f(x0 + width/12, y0 + width/4)
    glVertex2f(x0 - width/12, y0 + width/4)
    glVertex2f(x0 - width/6, y0)
    glVertex2f(x0 - width/11, y0-width/3)
    glVertex2f(x0 + width/11, y0-width/3)
    glVertex2f(x0 + width/6, y0)
    glEnd()

    draw_ellipse(x0, y0+width/4, h_rad=width/12, v_rad=width/18)
    draw_ellipse(x0, y0-width/3, h_rad=width/11, v_rad=width/18)

    # antennae
    glLineWidth(2.0 * PX_SCALE)
    glBegin(GL_LINES)
    glVertex2f(x0, y0+width/4)
    glVertex2f(x0 + width/12, y0 + width/2.4)
    glVertex2f(x0, y0+width/4)
    glVertex2f(x0 - width/12, y0 + width/2.4)
    glEnd()

    # top legs
    glBegin(GL_LINES)
    glVertex2f(x0, y0+width/7)
    glVertex2f(x0-width/5, y0+width/6.5)
    glVertex2f(x0-width/5, y0+width/6.5)
    glVertex2f(x0-width/4, y0+width/4)

    glVertex2f(x0, y0+width/7)
    glVertex2f(x0+width/5, y0+width/6.5)
    glVertex2f(x0+width/5, y0+width/6.5)
    glVertex2f(x0+width/4, y0+width/4)

    glVertex2f(x0, y0+width/10)
    glVertex2f(x0-width/5, y0+width/10.5)
    glVertex2f(x0-width/5, y0+width/10.5)
    glVertex2f(x0-width/4, y0)
    
    glVertex2f(x0, y0+width/10)
    glVertex2f(x0+width/5, y0+width/10.5)
    glVertex2f(x0+width/5, y0+width/10.5)
    glVertex2f(x0+width/4, y0)
    glEnd()

    # bottom legs
    glBegin(GL_LINES)
    glVertex2f(x0, y0-width/7)
    glVertex2f(x0-width/5, y0)
    glVertex2f(x0-width/5, y0)
    glVertex2f(x0-width/4, y0-width/2.7)

    glVertex2f(x0, y0-width/7)
    glVertex2f(x0+width/5, y0)
    glVertex2f(x0+width/5, y0)
    glVertex2f(x0+width/4, y0-width/2.7)
    glEnd()


def draw_beetle(x0, y0, width):
    """
    Draws Beetle inside a hexagon of specified width.
    
    :param x0: The x-coordinate of the center of the hexagon.
    :param y0: The y-coordinate of the center of the hexagon.
    :param width: The width of the hexagon (distance between opposite vertices).
    """
    glColor3f(0.8, 0, 1.0)  # Green color for the text
    segment_radius = width / 4.2

    # body and head
    draw_ellipse(x0, y0-width/15, 0.75*segment_radius, segment_radius)
    draw_ellipse(x0, y0 + 0.18*width, h_rad=width/9, v_rad=width/11)

    # pincers
    glBegin(GL_POLYGON)
    glVertex2f(x0, y0+3*width/15)
    glVertex2f(x0+width/14, y0+5*width/15)
    glVertex2f(x0+width/10, y0+2*width/15)
    glVertex2f(x0, y0+3*width/15)
    glVertex2f(x0-width/14, y0+5*width/15)
    glVertex2f(x0-width/10, y0+2*width/15)
    glVertex2f(x0, y0+4*width/15)
    glEnd()


    # middle legs
    glLineWidth(2.0 * PX_SCALE)
    glBegin(GL_LINES)
    glVertex2f(x0, y0-width/15)
    glVertex2f(x0 - width/2.7, y0-width/15)
    glVertex2f(x0, y0-width/15)
    glVertex2f(x0 + width/2.7, y0-width/15)

    # top legs
    glVertex2f(x0, y0-width/15)
    glVertex2f(x0 - width/3.3, y0+3*width/15)
    glVertex2f(x0, y0-width/15)
    glVertex2f(x0 + width/3.3, y0+3*width/15)

    # bottom legs
    glVertex2f(x0, y0-width/15)
    glVertex2f(x0 - width/3.3, y0-5*width/15)
    glVertex2f(x0, y0-width/15)
    glVertex2f(x0 + width/3.3, y0-5*width/15)
    glEnd()
    glLineWidth(1.0)



def draw_queen(x0, y0, width):
    """
    Draw a Queen Bee inside a hexagon of specified width.
    
    :param x0: The x-coordinate of the center of the hexagon.
    :param y0: The y-coordinate of the center of the hexagon.
    :param width: The width of the hexagon (distance between opposite vertices).
    """
    glColor3f(0.969, 0.725, 0.047) 
    draw_ellipse(x0, y0 - 0.05*width, h_rad=width/7, v_rad=width/5)
    draw_ellipse(x0, y0 + 0.16*width, h_rad=width/12, v_rad=width/18)

    glLineWidth(2.0*PX_SCALE)
    glBegin(GL_LINES)

    # Lower legs
    glVertex2f(x0, y0 - 0.05*width)
    glVertex2f(x0 - width * 0.18, y0 - 0.3*width)
    glVertex2f(x0, y0 - 0.05*width)
    glVertex2f(x0 + width * 0.18, y0 - 0.3*width)
    
    # Middle legs
    glVertex2f(x0, y0 - 0.05*width)
    glVertex2f(x0 - width * 0.25, y0 - 0.1*width)
    glVertex2f(x0, y0 - 0.05*width)
    glVertex2f(x0 + width * 0.25, y0 - 0.1*width)

    # Upper legs
    glVertex2f(x0, y0 - 0.05*width)
    glVertex2f(x0 - width * 0.18, y0 + 0.21*width)
    glVertex2f(x0, y0 - 0.05*width)
    glVertex2f(x0 + width * 0.18, y0 + 0.21*width)

    #Antennae
    glVertex2f(x0, y0 + 0.16*width)
    glVertex2f(x0 - width * 0.1, y0 + 0.23*width)
    glVertex2f(x0, y0 + 0.16*width)
    glVertex2f(x0 + width * 0.1, y0 + 0.23*width)

    glEnd()
    glLineWidth(1.0)

    #Wings - elliptical sectors
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(x0, y0 -0.05*width)
    for j in range(50):
        angle = 2 * math.pi * j / 300
        x = x0 - 0.35*width * math.cos(angle - math.pi/12)
        y = y0 + 0.2*width * math.sin(angle - math.pi/12)
        glVertex2f(x, y)
    glEnd()
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(x0, y0 -0.05*width)  
    for j in range(50):
        angle = 2 * math.pi * j / 300
        x = x0 + 0.35*width * math.cos(angle - math.pi/12)
        y = y0 + 0.2*width * math.sin(angle - math.pi/12)
        glVertex2f(x, y)
    glEnd()

def draw_insect(insect, x0, y0, width):
    mapping_dict = {
        'ant': draw_ant,
        'spider': draw_spider,
        'grasshopper': draw_grasshopper,
        'beetle': draw_beetle,
        'queen': draw_queen
    }

    return mapping_dict[insect](x0, y0, width)