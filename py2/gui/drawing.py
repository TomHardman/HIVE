from OpenGL.GL import *
from OpenGL.GLUT import glutBitmapCharacter, GLUT_BITMAP_8_BY_13
import math

from .px_scale import PX_SCALE

# Per-insect fill colours matching the physical Hive pieces
_INSECT_COL = {
    'queen':       (0.95, 0.62, 0.08),   # amber
    'ant':         (0.18, 0.45, 0.88),   # blue
    'spider':      (0.58, 0.18, 0.06),   # dark red-brown
    'grasshopper': (0.12, 0.72, 0.18),   # green
    'beetle':      (0.55, 0.18, 0.72),   # purple
}

def _dark(col):
    """Darkened shade of a colour for detail lines / contrast stripes."""
    return (col[0] * 0.30, col[1] * 0.30, col[2] * 0.30)

def _light(col):
    """Lightened shade of a colour (e.g. for wings)."""
    return (min(1.0, col[0] + 0.52 * (1 - col[0])),
            min(1.0, col[1] + 0.52 * (1 - col[1])),
            min(1.0, col[2] + 0.52 * (1 - col[2])))


def draw_hexagon(x0, y0, width, fill=True):
    radius = width / 2
    if fill:
        glBegin(GL_POLYGON)
    else:
        glLineWidth(4.0 * PX_SCALE)
        glBegin(GL_LINE_LOOP)
    for i in range(6):
        angle = 2 * math.pi * i / 6
        glVertex2f(radius * math.cos(angle) + x0, radius * math.sin(angle) + y0)
    glEnd()
    glLineWidth(1.0)


def draw_ellipse(x0, y0, h_rad, v_rad, num_segments=48):
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(x0, y0)
    for i in range(num_segments + 1):
        angle = 2 * math.pi * i / num_segments
        glVertex2f(x0 + h_rad * math.cos(angle), y0 + v_rad * math.sin(angle))
    glEnd()


def draw_text(x, y, text):
    glRasterPos2f(x, y)
    for char in text:
        glutBitmapCharacter(GLUT_BITMAP_8_BY_13, ord(char))


# ── Insect drawings ───────────────────────────────────────────────────────────
#
# All coordinates are relative to (x0, y0) — the centre of the hex tile.
# width = distance between opposite vertices of the hexagon (= 100 in board units).
# Insect colours match the physical Hive pieces regardless of player.


def draw_ant(x0, y0, width, player=1):
    """
    Blue ant: three oval segments in a straight vertical line (abdomen bottom,
    thorax centre, head top), six legs from the thorax, two antennae with bulb tips.
    """
    col = _INSECT_COL['ant']
    w   = width

    glColor3f(*col)

    draw_ellipse(x0, y0 - w*0.135, w*0.115, w*0.115)   # abdomen (large, bottom)
    draw_ellipse(x0, y0,           w*0.055, w*0.055)   # thorax  (tiny, centre)
    draw_ellipse(x0, y0 + w*0.130, w*0.080, w*0.080)   # head    (medium, top)

    glLineWidth(2.0 * PX_SCALE)
    glBegin(GL_LINES)
    # Three legs per side from the thorax
    for sx in (-1, 1):
        glVertex2f(x0, y0);  glVertex2f(x0 + sx*w*0.215, y0 + w*0.085)
        glVertex2f(x0, y0);  glVertex2f(x0 + sx*w*0.225, y0)
        glVertex2f(x0, y0);  glVertex2f(x0 + sx*w*0.215, y0 - w*0.085)
    # Antennae from head, diverging upward
    glVertex2f(x0, y0 + w*0.165);  glVertex2f(x0 - w*0.110, y0 + w*0.295)
    glVertex2f(x0, y0 + w*0.165);  glVertex2f(x0 + w*0.110, y0 + w*0.295)
    glEnd()
    glLineWidth(1.0)

    # Antenna bulb tips
    draw_ellipse(x0 - w*0.110, y0 + w*0.310, w*0.022, w*0.022)
    draw_ellipse(x0 + w*0.110, y0 + w*0.310, w*0.022, w*0.022)


def draw_spider(x0, y0, width, player=1):
    """
    Dark-red spider: large round abdomen (top), smaller cephalothorax (bottom),
    eight jointed legs spreading symmetrically, two downward fangs.
    """
    col = _INSECT_COL['spider']
    dk  = _dark(col)
    w   = width

    glColor3f(*col)
    draw_ellipse(x0, y0 - w*0.060, w*0.108, w*0.128)   # abdomen (bottom)
    draw_ellipse(x0, y0 + w*0.078, w*0.070, w*0.075)   # cephalothorax (top)

    cx, cy = x0, y0 + w*0.078

    glColor3f(*col)
    glLineWidth(2.0 * PX_SCALE)

    # Four leg-pairs, mirrored left/right; angles negated vs original (180° flip)
    leg_angles = [(210, 250), (193, 220), (167, 140), (150, 110)]
    for a1d, a2d in leg_angles:
        for side in (1, -1):
            a1 = math.radians(a1d) if side == 1 else math.pi - math.radians(a1d)
            a2 = math.radians(a2d) if side == 1 else math.pi - math.radians(a2d)
            ex = cx + w*0.118 * math.cos(a1)
            ey = cy + w*0.118 * math.sin(a1)
            tx = ex + w*0.124 * math.cos(a2)
            ty = ey + w*0.124 * math.sin(a2)
            glBegin(GL_LINES)
            glVertex2f(cx, cy); glVertex2f(ex, ey)
            glVertex2f(ex, ey); glVertex2f(tx, ty)
            glEnd()

    # Fangs pointing upward from cephalothorax
    glBegin(GL_LINES)
    glVertex2f(x0 - w*0.028, y0 + w*0.125); glVertex2f(x0 - w*0.042, y0 + w*0.200)
    glVertex2f(x0 + w*0.028, y0 + w*0.125); glVertex2f(x0 + w*0.042, y0 + w*0.200)
    glEnd()
    glLineWidth(1.0)


def draw_grasshopper(x0, y0, width, player=1):
    """
    Green grasshopper: tapered body polygon, small head, long antennae,
    two small front leg pairs, huge characteristic bent hind legs.
    """
    col = _INSECT_COL['grasshopper']
    dk  = _dark(col)
    w   = width

    glColor3f(*col)

    # Tapered body (wide at thorax, pointed at tail)
    glBegin(GL_POLYGON)
    glVertex2f(x0,           y0 + w*0.28)
    glVertex2f(x0 + w*0.096, y0 + w*0.17)
    glVertex2f(x0 + w*0.082, y0 - w*0.24)
    glVertex2f(x0,           y0 - w*0.30)
    glVertex2f(x0 - w*0.082, y0 - w*0.24)
    glVertex2f(x0 - w*0.096, y0 + w*0.17)
    glEnd()

    # Head
    draw_ellipse(x0, y0 + w*0.315, w*0.080, w*0.070)

    # Eye spots
    glColor3f(*dk)
    draw_ellipse(x0 - w*0.030, y0 + w*0.330, w*0.018, w*0.016)
    draw_ellipse(x0 + w*0.030, y0 + w*0.330, w*0.018, w*0.016)

    glColor3f(*col)
    glLineWidth(2.2 * PX_SCALE)

    # Long antennae
    glBegin(GL_LINES)
    glVertex2f(x0 - w*0.030, y0 + w*0.365); glVertex2f(x0 - w*0.225, y0 + w*0.465)
    glVertex2f(x0 + w*0.030, y0 + w*0.365); glVertex2f(x0 + w*0.225, y0 + w*0.465)
    glEnd()

    # Two small front leg pairs
    glBegin(GL_LINES)
    glVertex2f(x0 - w*0.090, y0 + w*0.130); glVertex2f(x0 - w*0.232, y0 + w*0.185)
    glVertex2f(x0 + w*0.090, y0 + w*0.130); glVertex2f(x0 + w*0.232, y0 + w*0.185)
    glVertex2f(x0 - w*0.090, y0 + w*0.040); glVertex2f(x0 - w*0.232, y0 + w*0.040)
    glVertex2f(x0 + w*0.090, y0 + w*0.040); glVertex2f(x0 + w*0.232, y0 + w*0.040)
    glEnd()

    # Large hind legs: body → raised knee → foot
    glLineWidth(2.8 * PX_SCALE)
    glBegin(GL_LINES)
    glVertex2f(x0 - w*0.090, y0 - w*0.050); glVertex2f(x0 - w*0.305, y0 + w*0.125)
    glVertex2f(x0 - w*0.305, y0 + w*0.125); glVertex2f(x0 - w*0.225, y0 - w*0.305)
    glVertex2f(x0 + w*0.090, y0 - w*0.050); glVertex2f(x0 + w*0.305, y0 + w*0.125)
    glVertex2f(x0 + w*0.305, y0 + w*0.125); glVertex2f(x0 + w*0.225, y0 - w*0.305)
    glEnd()
    glLineWidth(1.0)


def draw_beetle(x0, y0, width, player=1):
    """
    Purple beetle: two rounded elytra, pronotum, head with mandibles,
    centre split, three leg pairs.
    """
    col = _INSECT_COL['beetle']
    dk  = _dark(col)
    w   = width

    glColor3f(*col)

    # Elytra — two offset ovals
    draw_ellipse(x0 - w*0.065, y0 - w*0.068, w*0.118, w*0.228)
    draw_ellipse(x0 + w*0.065, y0 - w*0.068, w*0.118, w*0.228)

    # Pronotum
    draw_ellipse(x0, y0 + w*0.185, w*0.100, w*0.078)

    # Head
    draw_ellipse(x0, y0 + w*0.282, w*0.070, w*0.062)

    # Centre split (elytra dividing line) — use darkened col for contrast
    glColor3f(*dk)
    glLineWidth(2.2 * PX_SCALE)
    glBegin(GL_LINES)
    glVertex2f(x0, y0 + w*0.148); glVertex2f(x0, y0 - w*0.295)
    glEnd()

    # Mandibles and legs in insect colour
    glColor3f(*col)
    glBegin(GL_LINES)
    glVertex2f(x0 - w*0.038, y0 + w*0.328); glVertex2f(x0 - w*0.105, y0 + w*0.405)
    glVertex2f(x0 + w*0.038, y0 + w*0.328); glVertex2f(x0 + w*0.105, y0 + w*0.405)
    glEnd()

    # Three leg pairs
    glLineWidth(2.0 * PX_SCALE)
    glBegin(GL_LINES)
    glVertex2f(x0 - w*0.128, y0 + w*0.128); glVertex2f(x0 - w*0.310, y0 + w*0.225)
    glVertex2f(x0 + w*0.128, y0 + w*0.128); glVertex2f(x0 + w*0.310, y0 + w*0.225)
    glVertex2f(x0 - w*0.142, y0 - w*0.038); glVertex2f(x0 - w*0.335, y0 - w*0.038)
    glVertex2f(x0 + w*0.142, y0 - w*0.038); glVertex2f(x0 + w*0.335, y0 - w*0.038)
    glVertex2f(x0 - w*0.128, y0 - w*0.178); glVertex2f(x0 - w*0.310, y0 - w*0.272)
    glVertex2f(x0 + w*0.128, y0 - w*0.178); glVertex2f(x0 + w*0.310, y0 - w*0.272)
    glEnd()
    glLineWidth(1.0)


def draw_queen(x0, y0, width, player=1):
    """
    Amber bee: two wide wings spread to the sides, striped abdomen,
    thorax, round head, three leg pairs, antennae with bulb tips.
    """
    col = _INSECT_COL['queen']
    dk  = (0.08, 0.05, 0.01)          # near-black for dark stripes / legs
    wing_col = _light(col)            # pale amber wings
    w   = width

    # Wings — flat ovals spreading to the sides behind the body
    glColor3f(*wing_col)
    for sx in (-1, 1):
        wx = x0 + sx * w * 0.195
        wy = y0 + w * 0.095
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(wx, wy)
        for j in range(49):
            a = 2 * math.pi * j / 48
            glVertex2f(wx + w * 0.198 * math.cos(a),
                       wy + w * 0.108 * math.sin(a))
        glEnd()

    # Striped abdomen — alternating amber / dark bands
    stripe_cols = [col, dk, col, dk, col]
    for i, sc in enumerate(stripe_cols):
        glColor3f(*sc)
        sy = y0 - w*0.265 + i * w*0.082
        draw_ellipse(x0, sy, w*0.088 - i*0.003*w, w*0.048)

    # Thorax
    glColor3f(*col)
    draw_ellipse(x0, y0 + w*0.090, w*0.082, w*0.082)

    # Head
    draw_ellipse(x0, y0 + w*0.205, w*0.062, w*0.060)

    glColor3f(*col)
    glLineWidth(1.8 * PX_SCALE)
    glBegin(GL_LINES)
    # Three leg pairs from thorax
    for sx in (-1, 1):
        glVertex2f(x0, y0 + w*0.115); glVertex2f(x0 + sx*w*0.240, y0 + w*0.185)
        glVertex2f(x0, y0 + w*0.085); glVertex2f(x0 + sx*w*0.258, y0 + w*0.088)
        glVertex2f(x0, y0 + w*0.055); glVertex2f(x0 + sx*w*0.240, y0 - w*0.035)
    # Antennae
    glVertex2f(x0 - w*0.022, y0 + w*0.248); glVertex2f(x0 - w*0.118, y0 + w*0.355)
    glVertex2f(x0 + w*0.022, y0 + w*0.248); glVertex2f(x0 + w*0.118, y0 + w*0.355)
    glEnd()
    glLineWidth(1.0)

    draw_ellipse(x0 - w*0.118, y0 + w*0.370, w*0.018, w*0.018)
    draw_ellipse(x0 + w*0.118, y0 + w*0.370, w*0.018, w*0.018)


def draw_insect(insect, x0, y0, width, player=1):
    _MAP = {
        'ant':         draw_ant,
        'spider':      draw_spider,
        'grasshopper': draw_grasshopper,
        'beetle':      draw_beetle,
        'queen':       draw_queen,
    }
    _MAP[insect](x0, y0, width, player)
