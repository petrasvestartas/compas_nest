from pathlib import Path

from compas.colors import Color
from compas.data import json_dump
from compas.geometry import Frame
from compas_viewer import Viewer

from compas_nest import text_to_polylines

BLUE: Color = Color.from_hex("#0072B2")
OUTPUT: Path = Path(__file__).parent.parent / "data" / "output" / "08_text.json"

# 1. a frame to place/orient the text (origin = text origin, x-axis = reading direction)
frame: Frame = Frame([0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0])

# 2. render text to single-stroke polylines (OpenNest XML font) on that frame, 10-unit cap height
strokes: list = text_to_polylines("compas_nest\n0 1 2 3 4 5 6 7 8 9", height=10.0, font="regular", frame=frame)

# 3. view the frame and the stroke polylines (blue)
viewer: Viewer = Viewer()
viewer.scene.add(frame)
for stroke in strokes:
    viewer.scene.add(stroke, linecolor=BLUE, linewidth=2)
viewer.show()

# 4. save the polylines to JSON
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
json_dump(strokes, OUTPUT)
