from pathlib import Path

from compas.colors import Color
from compas.data import json_dump
from compas_viewer import Viewer

from compas_nest import text_to_polylines

BLUE: Color = Color.from_hex("#0072B2")
OUTPUT: Path = Path(__file__).parent.parent / "data" / "output" / "08_text.json"

# 1. render text to single-stroke polylines (OpenNest XML font), 10-unit cap height
strokes: list = text_to_polylines("compas_nest\n0 1 2", height=10.0, font="regular")

# 2. view the stroke polylines (blue)
viewer: Viewer = Viewer()
for stroke in strokes:
    viewer.scene.add(stroke, linecolor=BLUE, linewidth=2)
viewer.show()

# 3. save the polylines to JSON
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
json_dump(strokes, OUTPUT)
