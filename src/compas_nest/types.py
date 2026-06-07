"""Type aliases used across compas_nest."""

from typing import TypedDict

from compas.geometry import Geometry
from compas.geometry import Polyline


class Part(TypedDict, total=False):
    """A part to nest: an outer ring with optional holes, copies, and carried attribute geometry."""

    outline: Polyline
    holes: list[Polyline]
    copies: int
    attributes: list[Geometry]


class Sheet(TypedDict, total=False):
    """A sheet to nest into: an outer boundary with optional forbidden holes."""

    outline: Polyline
    holes: list[Polyline]


class Placement(TypedDict):
    """A single placed instance pose (angle in radians, sheet-local translation + sheet origin applied)."""

    part_index: int
    sheet_id: int
    angle: float
    tx: float
    ty: float
