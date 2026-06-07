# compas_nest

**Documentation: https://petrasvestartas.github.io/compas_nest/**

2D irregular nesting for the [COMPAS](https://compas.dev) framework — Python bindings for the
[OpenNest](https://github.com/petrasvestartas/OpenNest) C++ engines, built with
[nanobind](https://github.com/wjakob/nanobind).

Nest polylines **with holes** into sheets **with holes**, with live terminal progress and
[compas_viewer](https://github.com/compas-dev/compas_viewer) visualization.

![compas_nest](docs/images/04_collision_dataset.gif)

## Two engines

| Class | Engine | Notes |
|---|---|---|
| `opennest_collision` | physics / overlap-relaxation (`np_nest`) | dependency-free; iteration-budget driven; nests parts into holes |
| `opennest` | NFP + genetic algorithm (`nfp_nest`) | bundled Clipper2; generation/fitness driven; carries part *attributes* through placement |

## Install

```bash
pip install compas_nest
```

### From source (editable)

**One-step (uv, macOS + Windows Git Bash + Linux):** creates a local `.venv`, installs every
dependency, and builds the package:

```bash
git clone --recurse-submodules https://github.com/petrasvestartas/compas_nest.git
cd compas_nest
bash bash/install.sh
```

After editing C++ sources, rebuild without recreating the env: `bash bash/build.sh --test`.

**conda:**

```bash
conda env create -f environment.yml
conda activate compas_nest
pip install --no-build-isolation -ve .
```

**plain pip:**

```bash
pip install nanobind "scikit-build-core[pyproject]"
pip install --no-build-isolation -ve .
```

The C++ engine sources live under `external/nest/` (`nest_physics_cpp/` + `opennest_cpp/`, the latter
bundling Clipper2 and a minimal Boost subset). They are self-contained — no CGAL/Boost/Eigen download
is needed.

## Quick start

```python
from compas.geometry import Polyline
from compas_nest import nest_geo, nest_sheets, opennest_collision

def rect(x0, y0, w, h):
    return Polyline([[x0, y0, 0], [x0+w, y0, 0], [x0+w, y0+h, 0], [x0, y0+h, 0], [x0, y0, 0]])

geo = nest_geo()
geo.add_part(rect(0, 0, 20, 10), copies=3)
geo.add_part(rect(0, 0, 15, 15), holes=[rect(5, 5, 5, 5)], copies=2)

sheets = nest_sheets()
sheets.add_sheet(rect(0, 0, 100, 100), holes=[rect(40, 40, 10, 10)])

result = opennest_collision(iterations=2000, num_rotations=64).solve(geo, sheets)

for group in result.placed_polylines():
    print("sheet", group["sheet_id"], "->", len(group["parts"]), "parts")

# serialize placed polylines (with holes) + transformations to COMPAS JSON
result.to_json("data/output/quickstart.json")
```

See the `examples/` folder for the viewer workflows, and the
[documentation](https://petrasvestartas.github.io/compas_nest/) for examples, API reference and credits.

## License & credits

MIT — see [LICENSE](LICENSE). Attributions for the underlying work are in [CREDITS.md](CREDITS.md).
