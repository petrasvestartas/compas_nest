"""Pack elements into a simple grid (array) layout — a deterministic alternative to nesting.

Mirrors the OpenNest grasshopper "pack / array" behaviour: each part instance is dropped into a grid
cell sized by its bounding box, wrapping into rows, with gaps. The result is a
:class:`compas_nest.nest_result`, so it plugs into the same viewer / ``placed_polylines`` /
``to_json`` / ``to_obj`` as a real nest.
"""

from .result import nest_result


def _bbox(polyline):
    xs = [float(p[0]) for p in polyline.points]
    ys = [float(p[1]) for p in polyline.points]
    return min(xs), min(ys), max(xs), max(ys)


def pack(geo, columns=10, gap_x=10.0, gap_y=10.0, max_width=None):
    """Lay parts out in a simple row-major grid (no nesting).

    Each part instance (``copies`` expanded) is placed left to right; the x-advance uses each part's
    own width and the row height is the tallest part in that row. Two wrapping modes:

    * **array** (default) — start a new row every ``columns`` items.
    * **distance** — pass ``max_width`` and a row wraps once the next part would exceed that width
      (``columns`` is ignored). A part wider than ``max_width`` still gets its own row.

    Parameters
    ----------
    geo : :class:`compas_nest.nest_geo`
        The parts to arrange (holes and attributes are carried along).
    columns : int, optional
        Number of cells per row before wrapping (array mode).
    gap_x, gap_y : float, optional
        Gaps between cells horizontally and vertically.
    max_width : float, optional
        If set, wrap by row width instead of by ``columns`` (distance mode).

    Returns
    -------
    :class:`compas_nest.nest_result`
        All instances placed on a single sheet with rotation 0; use ``placed_polylines()`` /
        ``to_json()`` / ``to_obj()`` as usual.
    """
    columns = max(1, int(columns))
    placements = []
    x = 0.0
    y = 0.0
    row_h = 0.0
    col = 0
    for part_index, part in enumerate(geo.parts):
        copies = max(1, int(part.get("copies", 1)))
        minx, miny, maxx, maxy = _bbox(part["outline"])
        w = maxx - minx
        h = maxy - miny
        for _ in range(copies):
            # distance mode: wrap before placing if this part would overflow the row
            if max_width is not None and col > 0 and (x + w) > max_width:
                col = 0
                x = 0.0
                y += row_h + gap_y
                row_h = 0.0
            placements.append(
                {
                    "part_index": part_index,
                    "sheet_id": 0,
                    "angle": 0.0,
                    "tx": x - minx,  # land the part's min corner at (x, y)
                    "ty": y - miny,
                }
            )
            x += w + gap_x
            row_h = max(row_h, h)
            col += 1
            # array mode: wrap after a fixed number of columns
            if max_width is None and col >= columns:
                col = 0
                x = 0.0
                y += row_h + gap_y
                row_h = 0.0

    return nest_result(placements, geo, [(0.0, 0.0)], 1 if placements else 0)
