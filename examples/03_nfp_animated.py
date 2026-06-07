from pathlib import Path

from compas.data import json_load

from compas_nest import nest_geo
from compas_nest import nest_sheets
from compas_nest import nfp_solve
from compas_nest import offset_geo
from compas_nest import offset_sheets
from compas_nest import opennest
from compas_nest.viewer import animate

DATA: Path = Path(__file__).parent.parent / "data"
CLEARANCE: float = 0.1  # small gap (units) around every element and from the sheet edges/holes

# 1. the 48 element outlines (data/elements_strips.json) and two 510 x 635 sheets
geo: nest_geo = nest_geo()
for outline in json_load(str(DATA / "elements_strips.json")):
    geo.add_part(outline)

sheets: nest_sheets = nest_sheets.from_size(510, 635, count=2)

# 2. offset for clearance (elements grow, sheets shrink), then solve on the offset geometry
offset_g: nest_geo = offset_geo(geo, CLEARANCE)
offset_s: nest_sheets = offset_sheets(sheets, CLEARANCE)
handle: nfp_solve = opennest(generations=1000, rotations=8, seed=7, verbose=False).start(offset_g, offset_s)

# 3. animate the ORIGINAL parts at the solved poses (so the real parts show the clearance gaps)
animate(handle, geo, offset_s, save=DATA / "output" / "03_nfp_animated.json", park=-635.0)
