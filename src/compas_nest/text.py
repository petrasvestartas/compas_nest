"""Text to single-stroke polylines, using the OpenNest XML engraving fonts.

Ports the OpenNest single-line font (``fonts/regular.xml`` / ``fonts/bold.xml``): each glyph is a set
of stroke paths of straight segments and bulge-arcs, normalised to a 0..1 em. :func:`text_to_polylines`
renders a string to a list of :class:`compas.geometry.Polyline` (arcs sampled to segments), scaled by
``height`` and laid out left to right. Handy for sheet-number labels on a nested layout.
"""

import math
import xml.etree.ElementTree as ET
from importlib.resources import files

from compas.geometry import Polyline

H_SPACING = 0.1  # gap between glyphs, in em (matches OpenNest)
V_SPACING = 1.4  # line height, in em
# Arcs are emitted as straight segments (good for fabrication). Sampling is adaptive: roughly one
# segment per ARC_STEP of sweep, so gentle curves stay light and tight curves get enough points.
ARC_STEP = math.radians(15.0)  # max angle per segment
_ARC_MIN = 2  # at least this many segments per arc

_FONTS = {}  # name -> {char: glyph}


def _arc_points(p1, tangent, p2):
    """Sample an arc that starts at p1 with the given start tangent and ends at p2 (excludes p1).

    The number of straight segments is chosen from the swept angle (~one per :data:`ARC_STEP`),
    keeping the point count minimal while staying close to the true arc.
    """
    x1, y1 = p1
    x2, y2 = p2
    tx, ty = tangent
    tl = math.hypot(tx, ty)
    if tl < 1e-12:
        return [(x2, y2)]
    tx, ty = tx / tl, ty / tl
    nx, ny = -ty, tx  # left normal
    dx, dy = x1 - x2, y1 - y2
    denom = 2.0 * (dx * nx + dy * ny)
    if abs(denom) < 1e-12:
        return [(x2, y2)]  # degenerate -> straight
    s = -(dx * dx + dy * dy) / denom
    cx, cy = x1 + s * nx, y1 + s * ny
    r = math.hypot(x1 - cx, y1 - cy)
    a1 = math.atan2(y1 - cy, x1 - cx)
    a2 = math.atan2(y2 - cy, x2 - cx)
    # pick the sweep whose initial direction matches the tangent
    if (-math.sin(a1)) * tx + (math.cos(a1)) * ty >= 0:
        sweep = (a2 - a1) % (2 * math.pi)
    else:
        sweep = -((a1 - a2) % (2 * math.pi))
    segments = max(_ARC_MIN, int(math.ceil(abs(sweep) / ARC_STEP)))
    return [(cx + r * math.cos(a1 + sweep * i / segments), cy + r * math.sin(a1 + sweep * i / segments)) for i in range(1, segments + 1)]


def _parse_glyph(letter):
    """Parse one <letter> into {start, end, strokes:[[(x,y), ...], ...]} with arcs sampled."""
    start = float(letter.get("start", 0.0))
    end = float(letter.get("end", 0.7))
    strokes = []
    for path in letter.findall("path"):
        lx, ly = float(path.get("x")), float(path.get("y"))
        pts = [(lx, ly)]
        for to in path.findall("to"):
            tox, toy = float(to.get("x")), float(to.get("y"))
            b = to.get("b")
            if b is None:
                pts.append((tox, toy))
            else:
                d2 = 2.0 * math.atan(float(b))
                cs, sn = math.cos(d2), math.sin(d2)
                chx, chy = tox - lx, toy - ly
                tangent = (chx * cs - chy * sn, chx * sn + chy * cs)
                pts.extend(_arc_points((lx, ly), tangent, (tox, toy)))
            lx, ly = tox, toy
        strokes.append(pts)
    return {"start": start, "end": end, "strokes": strokes}


def _font(name="regular"):
    """Load (and cache) a glyph table from the packaged XML font."""
    if name not in _FONTS:
        xml = files("compas_nest").joinpath("fonts", name + ".xml").read_text(encoding="utf-8")
        root = ET.fromstring(xml)
        glyphs = {}
        for letter in root.findall("letter"):
            glyphs[chr(int(letter.get("code")))] = _parse_glyph(letter)
        _FONTS[name] = glyphs
    return _FONTS[name]


def text_to_polylines(text, height=1.0, font="regular", origin=(0.0, 0.0), spacing=H_SPACING):
    """Render ``text`` to a list of single-stroke :class:`compas.geometry.Polyline`.

    Parameters
    ----------
    text : str
        The string (supports multiple lines separated by newlines).
    height : float, optional
        Cap height (em) the glyphs are scaled to.
    font : str, optional
        Packaged font name: ``"regular"`` or ``"bold"``.
    origin : tuple[float, float], optional
        Lower-left start position of the first line.
    spacing : float, optional
        Extra gap between glyphs, in em.

    Returns
    -------
    list[:class:`compas.geometry.Polyline`]
        One polyline per stroke, in the XY plane, scaled by ``height``.
    """
    glyphs = _font(font)
    fallback = glyphs.get("\0")
    ox, oy = origin
    out = []
    for line_i, line in enumerate(text.split("\n")):
        x = ox
        y = oy - line_i * V_SPACING * height
        for ch in line:
            glyph = glyphs.get(ch, fallback)
            if glyph is None:
                x += (0.5 + spacing) * height
                continue
            x -= glyph["start"] * height  # account for the glyph's left bearing
            for stroke in glyph["strokes"]:
                out.append(Polyline([[x + px * height, y + py * height, 0.0] for (px, py) in stroke]))
            x += glyph["end"] * height + spacing * height
    return out
