from pathlib import Path

from compas.colors import Color
from compas.geometry import Point
from compas.geometry import Polyline
from compas.geometry import centroid_points
from compas_viewer import Viewer

from compas_nest import nest_geo
from compas_nest import nest_result
from compas_nest import nest_sheets
from compas_nest import opennest_collision

BLACK: Color = Color.from_hex("#000000")
BLUE: Color = Color.from_hex("#0072B2")
RED: Color = Color.from_hex("#C0392B")
OUTPUT: Path = Path(__file__).parent.parent / "data" / "output" / "05_attributes.json"


def centroid(polyline: Polyline) -> Point:
    return Point(*centroid_points(list(polyline.points)[:-1]))


# 1. parts, each carrying a point at its centroid as an attribute (moves with the part)
outlines = [
    Polyline([
        [0, 0, 0],
        [30, 0, 0],
        [30, 12, 0],
        [0, 12, 0],
        [0, 0, 0],
    ]),
    Polyline([
        [0, 0, 0],
        [20, 0, 0],
        [20, 20, 0],
        [0, 20, 0],
        [0, 0, 0],
    ]),
]

geo: nest_geo = nest_geo()
for outline in outlines:
    geo.add_part(outline, attributes=[centroid(outline)], copies=4)

sheets: nest_sheets = nest_sheets()
sheets.add_sheet(
    Polyline([
        [0, 0, 0],
        [120, 0, 0],
        [120, 120, 0],
        [0, 120, 0],
        [0, 0, 0],
    ]),
)

# 2. nest
result: nest_result = opennest_collision().solve(geo, sheets)

# 3. view: each placed element (outline + its centroid point) in its own scene group
viewer: Viewer = Viewer()
sheets_group = viewer.scene.add_group(name="sheets")
for i, sheet in enumerate(sheets.sheets):
    sheets_group.add(sheet["outline"], name="sheet_%d" % i, linecolor=BLACK, linewidth=2)

elements = viewer.scene.add_group(name="elements")
for k, group in enumerate(result.placed_polylines()):
    for j, part in enumerate(group["parts"]):
        element = viewer.scene.add_group(name="element_%d_%d" % (k, j), parent=elements)
        element.add(part["outline"], linecolor=BLUE, linewidth=2)
        for attribute in part["attributes"]:
            element.add(attribute, pointcolor=RED, pointsize=12)
viewer.show()

# 4. save to JSON (full result, incl. transformed attributes) and OBJ (outlines + holes)
result.to_json(OUTPUT)
result.to_obj(OUTPUT.with_suffix(".obj"))
