from pathlib import Path

from compas.data import json_load

from compas_nest import collision_solve
from compas_nest import nest_geo
from compas_nest import nest_sheets
from compas_nest import offset_geo
from compas_nest import offset_sheets
from compas_nest import opennest_collision
from compas_nest.viewer import animate

DATA: Path = Path(__file__).parent.parent / "data"
CLEARANCE: float = 0.1  # small gap (units) around every element and from the sheet edges/holes

# 1. the 48 element outlines (data/elements_strips.json) on a single 510 x 635 sheet
geo: nest_geo = nest_geo()
for outline in json_load(str(DATA / "elements_strips.json")):
    geo.add_part(outline)

sheets: nest_sheets = nest_sheets.from_size(510, 635, count=1)

# 2. offset for clearance (elements grow, sheets shrink), then solve on the offset geometry.
#    These settings replicate the OpenNest Grasshopper run that fits all 48 onto one sheet. The solve
#    is heavy (~10 min): 3600 orientations x 10000 rounds, multi-start. The original outlines are
#    nested with their full edges (the result is the original parts at the solved poses).
offset_g: nest_geo = offset_geo(geo, CLEARANCE)
offset_s: nest_sheets = offset_sheets(sheets, CLEARANCE)
handle: collision_solve = opennest_collision(
    iterations=10000,     # round budget for a tight single-sheet pack
    num_rotations=3600,   # fine orientation sampling (the elongated strips need it)
    seed=100,             # base RNG seed
    n_starts=6,           # multi-start: try several seeds, keep the densest (this is what fits all 48)
    part_holes_mode=1,    # "elements holes fill": nest smaller parts into larger parts' holes
    pole_max=48,          # collision-gradient fidelity (tighter packing)
    final_compact=2,      # multi-directional post-pack compaction (reclaims interior voids)
    fit_mode=1,           # "fit one sheet": pack everything onto a single sheet
    verbose=False,
).start(offset_g, offset_s)

# 3. animate the ORIGINAL parts at the solved poses (so the real parts show the clearance gaps)
animate(handle, geo, offset_s, save=DATA / "output" / "04_collision_dataset.json", park=-635.0)
