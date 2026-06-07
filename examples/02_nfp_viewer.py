from pathlib import Path

from compas.colors import Color
from compas.geometry import Polyline
from compas_viewer import Viewer

from compas_nest import nest_geo
from compas_nest import nest_result
from compas_nest import nest_sheets
from compas_nest import opennest

BLACK: Color = Color.from_hex("#000000")
BLUE: Color = Color.from_hex("#0072B2")
OUTPUT: Path = Path(__file__).parent.parent / "data" / "output" / "02_nfp_viewer.json"

# 1. parts (one with a hole, plus triangles) and a sheet (with a hole)
geo: nest_geo = nest_geo()
geo.add_part(Polyline([[0, 0, 0], [30, 0, 0], [30, 12, 0], [0, 12, 0], [0, 0, 0]]), copies=4)
geo.add_part(
    Polyline([[0, 0, 0], [20, 0, 0], [20, 20, 0], [0, 20, 0], [0, 0, 0]]),
    holes=[Polyline([[6, 6, 0], [14, 6, 0], [14, 14, 0], [6, 14, 0], [6, 6, 0]])],
    copies=2,
)
geo.add_part(Polyline([[0, 0, 0], [22, 0, 0], [0, 22, 0], [0, 0, 0]]), copies=4)

sheets: nest_sheets = nest_sheets()
sheets.add_sheet(
    Polyline([[0, 0, 0], [120, 0, 0], [120, 120, 0], [0, 120, 0], [0, 0, 0]]),
    holes=[Polyline([[50, 50, 0], [65, 50, 0], [65, 65, 0], [50, 65, 0], [50, 50, 0]])],
)

# 2. nest with the NFP + genetic-algorithm engine
result: nest_result = opennest(generations=20, rotations=8, seed=7).solve(geo, sheets)

# 3. view with compas_viewer (sheets black, placed elements blue)
viewer: Viewer = Viewer()
for sheet in sheets.sheets:
    viewer.scene.add(sheet["outline"], linecolor=BLACK, linewidth=2)
    for hole in sheet["holes"]:
        viewer.scene.add(hole, linecolor=BLACK)
for group in result.placed_polylines():
    for part in group["parts"]:
        viewer.scene.add(part["outline"], linecolor=BLUE, linewidth=2)
        for hole in part["holes"]:
            viewer.scene.add(hole, linecolor=BLUE)
viewer.show()

# 4. save the placed geometry to JSON (full result) and OBJ (outlines + holes)
result.to_json(OUTPUT)
result.to_obj(OUTPUT.with_suffix(".obj"))
