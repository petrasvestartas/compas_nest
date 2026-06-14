"""COMPAS data structures for nesting input, replicating the OpenNest C# ``nest_geo`` and ``nest_sheets`` containers."""

from compas.data import Data
from compas.geometry import Polyline


def _ring_xy(polyline, ox=0.0, oy=0.0):
    """Flatten a polyline ring to (vertex_count, [x0, y0, x1, y1, ...]) dropping a trailing closing duplicate.

    Parameters
    ----------
    polyline : :class:`compas.geometry.Polyline`
        The ring.
    ox, oy : float
        Origin offset subtracted from every coordinate (used to express sheets in their local frame).

    Returns
    -------
    tuple[int, list[float]]
    """
    pts = list(polyline.points)
    if len(pts) >= 2 and pts[0] == pts[-1]:
        pts = pts[:-1]
    flat = []
    for p in pts:
        flat.append(float(p[0]) - ox)
        flat.append(float(p[1]) - oy)
    return len(pts), flat


class nest_geo(Data):
    """Container for the parts (polylines with optional holes) to nest.

    Replicates the role of the OpenNest C# ``nest_geo`` class.

    Parameters
    ----------
    parts : list[dict], optional
        Each part is a dict ``{"outline": Polyline, "holes": [Polyline, ...], "copies": int, "attributes": [Geometry, ...]}``.
    name : str, optional

    Attributes
    ----------
    parts : list[dict]
        The parts. Index into this list is the *part index* returned by the engines.
    """

    def __init__(self, parts=None, name=None):
        super().__init__(name=name)
        self.parts = parts or []

    @property
    def __data__(self):
        return {
            "parts": [
                {
                    "outline": part["outline"],
                    "holes": list(part.get("holes", [])),
                    "copies": int(part.get("copies", 1)),
                    "rotations": int(part.get("rotations", 0)),
                    "attributes": list(part.get("attributes", [])),
                }
                for part in self.parts
            ]
        }

    @classmethod
    def __from_data__(cls, data):
        return cls(parts=data["parts"])

    def add_part(self, outline, holes=None, copies=1, attributes=None, rotations=0):
        """Add a part.

        Parameters
        ----------
        outline : :class:`compas.geometry.Polyline`
            Closed outer ring of the part.
        holes : list[:class:`compas.geometry.Polyline`], optional
            Interior holes.
        copies : int, optional
            Number of identical copies to nest.
        attributes : list[:class:`compas.geometry.Geometry`], optional
            Extra geometry carried along with the part through placement (opennest engine feature).
        rotations : int, optional
            Per-part rotation override. ``0`` (default) = use the solver's global rotation setting;
            ``N`` = this part may only use ``N`` orientations (360/N degree steps); ``1`` = fixed
            (no rotation, e.g. grain direction). Lets rectangular and freeform parts share one nest
            with different rotation rules.

        Returns
        -------
        int
            The index of the added part.
        """
        self.parts.append(
            {
                "outline": outline,
                "holes": list(holes or []),
                "copies": int(copies),
                "rotations": max(0, int(rotations)),
                "attributes": list(attributes or []),
            }
        )
        return len(self.parts) - 1

    def _flatten_parts(self, expand_copies):
        """Flatten parts to the flat arrays the engines consume (parts stay in their raw frame).

        Parameters
        ----------
        expand_copies : bool
            If True, repeat each part ``copies`` times (physics engine, which has no quantity input)
            and return an ``origin_index`` map. If False, return per-part ``quantities`` (NFP engine).

        Returns
        -------
        dict
            Keys: ``vertex_counts``, ``xy``, ``hole_counts``, ``hole_vertex_counts``, ``hole_xy``,
            and either ``origin_index`` (expand) or ``quantities``.
        """
        vertex_counts = []
        xy = []
        hole_counts = []
        hole_vertex_counts = []
        hole_xy = []
        origin_index = []
        quantities = []
        # Per-part rotation override, one entry per emitted part (per instance when copies are
        # expanded, per part otherwise) — index-aligned with vertex_counts, i.e. part_count. 0 = global.
        rotations = []

        for part_index, part in enumerate(self.parts):
            copies = max(1, int(part.get("copies", 1)))
            reps = copies if expand_copies else 1
            if not expand_copies:
                quantities.append(copies)
            rot = max(0, int(part.get("rotations", 0)))
            for _ in range(reps):
                n, flat = _ring_xy(part["outline"])
                vertex_counts.append(n)
                xy.extend(flat)
                holes = part.get("holes", [])
                hole_counts.append(len(holes))
                for h in holes:
                    hn, hflat = _ring_xy(h)
                    hole_vertex_counts.append(hn)
                    hole_xy.extend(hflat)
                origin_index.append(part_index)
                rotations.append(rot)

        result = {
            "vertex_counts": vertex_counts,
            "xy": xy,
            "hole_counts": hole_counts,
            "hole_vertex_counts": hole_vertex_counts,
            "hole_xy": hole_xy,
            "rotations": rotations,
        }
        if expand_copies:
            result["origin_index"] = origin_index
        else:
            result["quantities"] = quantities
        return result


class nest_sheets(Data):
    """Container for the sheets (polylines with optional holes) to nest into.

    Replicates the role of the OpenNest C# ``nest_sheets`` class.

    Parameters
    ----------
    sheets : list[dict], optional
        Each sheet is a dict ``{"outline": Polyline, "holes": [Polyline, ...]}``.
    name : str, optional

    Attributes
    ----------
    sheets : list[dict]
        The sheets. Index into this list is the ``sheet_id`` returned by the engines.
    """

    def __init__(self, sheets=None, name=None):
        super().__init__(name=name)
        self.sheets = sheets or []

    @property
    def __data__(self):
        return {
            "sheets": [
                {"outline": sheet["outline"], "holes": list(sheet.get("holes", []))}
                for sheet in self.sheets
            ]
        }

    @classmethod
    def __from_data__(cls, data):
        return cls(sheets=data["sheets"])

    def add_sheet(self, outline, holes=None):
        """Add a sheet.

        Parameters
        ----------
        outline : :class:`compas.geometry.Polyline`
            Closed outer boundary of the sheet.
        holes : list[:class:`compas.geometry.Polyline`], optional
            Forbidden interior regions parts must avoid.

        Returns
        -------
        int
            The index of the added sheet.
        """
        self.sheets.append({"outline": outline, "holes": list(holes or [])})
        return len(self.sheets) - 1

    @classmethod
    def from_size(cls, width, height, count=1, gap=None):
        """Build ``count`` rectangular sheets laid out left to right.

        Parameters
        ----------
        width, height : float
            Sheet dimensions.
        count : int, optional
            Number of identical sheets.
        gap : float, optional
            Horizontal spacing between sheet origins in addition to ``width`` (defaults to ``0.1 * width``).

        Returns
        -------
        :class:`nest_sheets`
        """
        gap = 0.1 * width if gap is None else gap
        sheets = cls()
        for i in range(count):
            ox = i * (width + gap)
            outline = Polyline(
                [
                    [ox, 0.0, 0.0],
                    [ox + width, 0.0, 0.0],
                    [ox + width, height, 0.0],
                    [ox, height, 0.0],
                    [ox, 0.0, 0.0],
                ]
            )
            sheets.add_sheet(outline)
        return sheets

    def origins(self):
        """Return the world origin (bbox min x, y) of each sheet.

        The engines work in a sheet-local frame; placements are returned relative to this origin.

        Returns
        -------
        list[tuple[float, float]]
        """
        out = []
        for sheet in self.sheets:
            pts = sheet["outline"].points
            ox = min(float(p[0]) for p in pts)
            oy = min(float(p[1]) for p in pts)
            out.append((ox, oy))
        return out

    def to_arrays(self):
        """Flatten sheets to flat arrays in their local frame (each sheet normalised to its bbox min).

        Returns
        -------
        dict
            Keys: ``vertex_counts``, ``xy``, ``hole_counts``, ``hole_vertex_counts``, ``hole_xy``, ``origins``.
        """
        vertex_counts = []
        xy = []
        hole_counts = []
        hole_vertex_counts = []
        hole_xy = []
        origins = self.origins()

        for sheet, (ox, oy) in zip(self.sheets, origins):
            n, flat = _ring_xy(sheet["outline"], ox, oy)
            vertex_counts.append(n)
            xy.extend(flat)
            holes = sheet.get("holes", [])
            hole_counts.append(len(holes))
            for h in holes:
                hn, hflat = _ring_xy(h, ox, oy)
                hole_vertex_counts.append(hn)
                hole_xy.extend(hflat)

        return {
            "vertex_counts": vertex_counts,
            "xy": xy,
            "hole_counts": hole_counts,
            "hole_vertex_counts": hole_vertex_counts,
            "hole_xy": hole_xy,
            "origins": origins,
        }
