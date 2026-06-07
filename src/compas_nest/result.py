"""Result of a nesting solve: placement poses and the world-placed geometry they imply."""

import math
import os

from compas.data import json_dump
from compas.geometry import Rotation
from compas.geometry import Translation


class nest_result:
    """Placements produced by a nesting engine.

    The placement contract (shared by both engines) is::

        world_point = Rotate(part_point, angle, about origin) + (tx, ty) + sheet_origin

    where ``part_point`` is a vertex of the *original* part geometry and ``angle`` is in radians.

    Parameters
    ----------
    placements : list[dict]
        Each placement: ``{"part_index": int, "sheet_id": int, "angle": float (rad), "tx": float, "ty": float}``.
        Unplaced instances have ``sheet_id == -1``.
    geo : :class:`compas_nest.nest_geo`
        The parts that were nested (placements reference parts by ``part_index``).
    sheet_origins : list[tuple[float, float]]
        World origin of each sheet, added to sheet-local ``(tx, ty)``.
    n_sheets : int
        Number of sheets actually used.
    fitness : float, optional
        Solver fitness (NFP engine only).
    """

    def __init__(self, placements, geo, sheet_origins, n_sheets, fitness=None):
        self.placements = placements
        self.geo = geo
        self.sheet_origins = sheet_origins
        self.n_sheets = n_sheets
        self.fitness = fitness

    @property
    def placed(self):
        """list[dict] : Placements that landed on a sheet (``sheet_id >= 0``)."""
        return [p for p in self.placements if p["sheet_id"] >= 0]

    @property
    def unplaced(self):
        """list[dict] : Placements that could not be placed."""
        return [p for p in self.placements if p["sheet_id"] < 0]

    def transformation(self, placement):
        """Return the world :class:`compas.geometry.Transformation` for a placement."""
        ox, oy = self.sheet_origins[placement["sheet_id"]]
        R = Rotation.from_axis_and_angle([0.0, 0.0, 1.0], placement["angle"])
        T = Translation.from_vector([ox + placement["tx"], oy + placement["ty"], 0.0])
        return T * R

    def placed_polylines(self, geo=None):
        """Return the placed geometry grouped per sheet.

        Parameters
        ----------
        geo : :class:`compas_nest.nest_geo`, optional
            Apply the solved poses to this geometry instead of the one that was nested. Use it to
            render the *original* parts when the solve ran on offset (clearance) geometry.

        Returns
        -------
        list[dict]
            One entry per used sheet::

                {"sheet_id": int,
                 "parts": [{"part_index": int, "transformation": Transformation,
                            "outline": Polyline, "holes": [Polyline, ...],
                            "attributes": [Geometry, ...]}, ...]}
        """
        parts_source = (geo or self.geo).parts
        groups = {}
        for placement in self.placed:
            sid = placement["sheet_id"]
            X = self.transformation(placement)
            part = parts_source[placement["part_index"]]
            entry = {
                "part_index": placement["part_index"],
                "transformation": X,
                "outline": part["outline"].transformed(X),
                "holes": [h.transformed(X) for h in part.get("holes", [])],
                "attributes": [a.transformed(X) for a in part.get("attributes", [])],
            }
            groups.setdefault(sid, []).append(entry)
        return [{"sheet_id": sid, "parts": groups[sid]} for sid in sorted(groups)]

    def to_json(self, filepath, geo=None):
        """Serialize the placed polylines (with holes) and transformations to COMPAS JSON.

        Parameters
        ----------
        filepath : str
            Output path. Parent directories are created if missing.
        geo : :class:`compas_nest.nest_geo`, optional
            Apply the solved poses to this geometry instead of the nested one (see
            :meth:`placed_polylines`).
        """
        filepath = os.fspath(filepath)
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        json_dump({"n_sheets": self.n_sheets, "sheets": self.placed_polylines(geo=geo)}, filepath)
        return filepath

    def to_obj(self, filepath, geo=None):
        """Write the placed outlines and holes to a Wavefront OBJ as closed polyline loops.

        Parameters
        ----------
        filepath : str
            Output path. Parent directories are created if missing.
        geo : :class:`compas_nest.nest_geo`, optional
            Apply the solved poses to this geometry instead of the nested one (see
            :meth:`placed_polylines`).
        """
        filepath = os.fspath(filepath)
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        lines = ["# compas_nest placed geometry"]
        offset = 0
        for group in self.placed_polylines(geo=geo):
            for part in group["parts"]:
                for ring in [part["outline"], *part["holes"]]:
                    pts = list(ring.points)
                    if len(pts) >= 2 and pts[0] == pts[-1]:
                        pts = pts[:-1]
                    for p in pts:
                        lines.append("v {} {} {}".format(float(p[0]), float(p[1]), float(p[2])))
                    idx = [offset + i + 1 for i in range(len(pts))]
                    lines.append("l " + " ".join(str(i) for i in idx + [idx[0]]))  # closed loop
                    offset += len(pts)
        with open(filepath, "w") as f:
            f.write("\n".join(lines) + "\n")
        return filepath

    @staticmethod
    def _from_engine(placements_raw, geo, sheet_origins, n_sheets, fitness=None, degrees=False):
        placements = []
        for part_index, sheet_id, angle, tx, ty in placements_raw:
            placements.append(
                {
                    "part_index": int(part_index),
                    "sheet_id": int(sheet_id),
                    "angle": math.radians(angle) if degrees else float(angle),
                    "tx": float(tx),
                    "ty": float(ty),
                }
            )
        return nest_result(placements, geo, sheet_origins, n_sheets, fitness)

    def __repr__(self):
        return "nest_result(placed={}/{}, n_sheets={}, fitness={})".format(
            len(self.placed), len(self.placements), self.n_sheets, self.fitness
        )
