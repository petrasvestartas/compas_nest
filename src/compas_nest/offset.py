"""Clipper2-based polygon offsetting, used to add clearance before nesting.

Convention (orientation-normalised, so it does not depend on input winding):
``distance > 0`` grows a ring outward, ``distance < 0`` shrinks it inward.

The directional helpers add a uniform clearance ``d`` so the *real* parts end up with gaps:

* :func:`offset_geo` — element outer ``+d`` (grow), element holes ``-d`` (shrink)
* :func:`offset_sheets` — sheet outer ``-d`` (shrink), sheet holes ``+d`` (grow)
"""

from typing import List
from typing import Optional

from compas.geometry import Polyline

from compas_nest import _clipper  # type: ignore

from .datastructures import nest_geo
from .datastructures import nest_sheets


def _ring(polyline: Polyline) -> List[List[float]]:
    """Return the polyline as a list of ``[x, y]`` points, dropping a trailing closing duplicate."""
    pts = list(polyline.points)
    if len(pts) >= 2 and pts[0] == pts[-1]:
        pts = pts[:-1]
    return [[float(p[0]), float(p[1])] for p in pts]


def _signed_area(ring: List[List[float]]) -> float:
    a = 0.0
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        a += x1 * y2 - x2 * y1
    return 0.5 * a


def offset_polyline(polyline: Polyline, distance: float) -> Optional[Polyline]:
    """Offset a single closed polyline.

    Parameters
    ----------
    polyline : :class:`compas.geometry.Polyline`
        Closed ring (a trailing duplicate point is tolerated).
    distance : float
        Positive grows the ring outward, negative shrinks it inward.

    Returns
    -------
    :class:`compas.geometry.Polyline` or None
        The offset ring (the largest one if the offset splits it), or ``None`` if it vanishes.
    """
    ring = _ring(polyline)
    if len(ring) < 3:
        return None
    # normalise to CCW so positive distance is always outward
    if _signed_area(ring) < 0:
        ring = ring[::-1]
    result = _clipper.inflate([[(x, y) for x, y in ring]], float(distance))
    if not result:
        return None
    best = max(result, key=lambda r: abs(_signed_area([list(p) for p in r])))
    points = [[float(p[0]), float(p[1]), 0.0] for p in best]
    points.append(points[0])  # close
    return Polyline(points)


def offset_geo(geo: nest_geo, distance: float) -> nest_geo:
    """Return a copy of ``geo`` with each part outer grown and holes shrunk by ``distance``.

    Parameters
    ----------
    geo : :class:`compas_nest.nest_geo`
    distance : float
        Clearance to add around the parts.

    Returns
    -------
    :class:`compas_nest.nest_geo`
    """
    out = nest_geo(name=geo.name)
    for part in geo.parts:
        outline = offset_polyline(part["outline"], +distance)
        if outline is None:
            continue
        holes = []
        for hole in part.get("holes", []):
            shrunk = offset_polyline(hole, -distance)
            if shrunk is not None:
                holes.append(shrunk)
        out.add_part(outline, holes=holes, copies=int(part.get("copies", 1)), attributes=list(part.get("attributes", [])))
    return out


def offset_sheets(sheets: nest_sheets, distance: float) -> nest_sheets:
    """Return a copy of ``sheets`` with each sheet outer shrunk and holes grown by ``distance``.

    Parameters
    ----------
    sheets : :class:`compas_nest.nest_sheets`
    distance : float
        Clearance to keep from sheet edges and holes.

    Returns
    -------
    :class:`compas_nest.nest_sheets`
    """
    out = nest_sheets(name=sheets.name)
    for sheet in sheets.sheets:
        outline = offset_polyline(sheet["outline"], -distance)
        if outline is None:
            continue
        holes = []
        for hole in sheet.get("holes", []):
            grown = offset_polyline(hole, +distance)
            if grown is not None:
                holes.append(grown)
        out.add_sheet(outline, holes=holes)
    return out
