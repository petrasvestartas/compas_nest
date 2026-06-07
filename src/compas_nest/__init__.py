"""compas_nest — 2D irregular nesting (OpenNest) for the COMPAS framework."""

import os
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version

__author__ = ["Petras Vestartas"]
__copyright__ = "Petras Vestartas"
__license__ = "MIT License"
__email__ = "petrasvestartas@gmail.com"

try:
    __version__ = version("compas_nest")
except PackageNotFoundError:
    __version__ = "0.0.0"

HERE = os.path.dirname(__file__)
HOME = os.path.abspath(os.path.join(HERE, "../../"))
DATA = os.path.abspath(os.path.join(HOME, "data"))
DOCS = os.path.abspath(os.path.join(HOME, "docs"))
TEMP = os.path.abspath(os.path.join(HOME, "temp"))

from .datastructures import nest_geo  # noqa: E402
from .datastructures import nest_sheets  # noqa: E402
from .result import nest_result  # noqa: E402
from .collision import collision_solve  # noqa: E402
from .collision import opennest_collision  # noqa: E402
from .nfp import nfp_solve  # noqa: E402
from .nfp import opennest  # noqa: E402
from .offset import offset_geo  # noqa: E402
from .offset import offset_polyline  # noqa: E402
from .offset import offset_sheets  # noqa: E402

__all__ = [
    "HOME",
    "DATA",
    "DOCS",
    "TEMP",
    "nest_geo",
    "nest_sheets",
    "nest_result",
    "opennest_collision",
    "collision_solve",
    "opennest",
    "nfp_solve",
    "offset_polyline",
    "offset_geo",
    "offset_sheets",
]
