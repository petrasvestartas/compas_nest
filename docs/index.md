# compas_nest

**2D irregular nesting for the [COMPAS](https://compas.dev) framework.**

![compas_nest](images/04_collision_dataset.gif)

`compas_nest` packs irregular parts onto sheets with minimal waste — **parts and sheets may have
holes**, parts can nest **inside** holes, and sheets can be **non-rectangular**. It exposes the C++
nesting engines of [OpenNest](https://github.com/petrasvestartas/OpenNest) to Python through
[nanobind](https://github.com/wjakob/nanobind), with live
[compas_viewer](https://github.com/compas-dev/compas_viewer) visualization and JSON / OBJ output.

## Where to find things

- **[Installation](installation.md)** — install from PyPI, with `uv`, conda, or from source.
- **[Examples](examples/index.md)** — the viewer workflows: collision and NFP nesting, live
  animation, the real dataset, attributes, and clearance offsetting.
- **[API Reference](api/index.md)** — the two engines, the `nest_geo` / `nest_sheets` data
  structures, the `nest_result` (placements, transformations, JSON / OBJ export), and offsetting.
- **[Credits](credits.md)** — the OpenNest engines and the published methods they build on.
