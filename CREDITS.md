# Credits

`compas_nest` is the **COMPAS / Python binding** of the [OpenNest](https://github.com/petrasvestartas/OpenNest)
C++ nesting engines. The engines build substantially on the **published methods** of the projects below —
with many additions of their own. We gratefully credit the original authors for the underlying techniques.

## OpenNest

Original **OpenNest** Grasshopper plugin, the C++ nesting engines, and the enhancements wrapped here by
**Petras Vestartas**. <https://github.com/petrasvestartas/OpenNest>

## Nesting algorithms (methods translated & extended)

- **SVGnest** — Jack Qiao. No-fit-polygon + genetic-algorithm method behind the NFP engine (`opennest` /
  `nfp_nest`). <https://github.com/Jack000/SVGnest>
- **Deepnest** — Jack Qiao. Desktop evolution of SVGnest. <https://github.com/Jack000/Deepnest>
- **DeepNestPort / DeepNestSharp** — C# ports that informed the translation.
  <https://github.com/Dragnalith/DeepnestPort> · <https://github.com/Wedg/DeepNestSharp>

## Physics / strip-packing (method behind `opennest_collision` / `nest_physics`)

- **jagua-rs** — Jeroen Gardeyn. Collision-detection engine for 2D irregular cutting & packing.
  <https://github.com/JeroenGar/jagua-rs>
- **sparrow** — *"A fast and reliable heuristic for 2D irregular strip packing"*, Jeroen Gardeyn,
  Greet Vanden Berghe & Tony Wauters (KU Leuven), 2025. <https://github.com/JeroenGar/sparrow>

## Geometry libraries (used directly)

- **Clipper2** — Angus Johnson. Polygon clipping & offsetting (used for the `offset_geo` / `offset_sheets`
  clearance and inside the NFP engine). <https://github.com/AngusJohnson/Clipper2>
- **Boost.Polygon** — no-fit-polygon (Minkowski) convolution in the NFP engine; a minimal subset is vendored.
  <https://www.boost.org/>

## Python binding

- **nanobind** — Wenzel Jakob. C++ ↔ Python bindings. <https://github.com/wjakob/nanobind>
- **COMPAS** & **compas_viewer** — the framework and viewer this package integrates with.
  <https://compas.dev>
- **compas_cgal** — the binding/build/deploy pattern this package follows.
  <https://github.com/compas-dev/compas_cgal>

---

`compas_nest` is released under the **MIT License** (see [LICENSE](LICENSE)). Each dependency keeps its own
license; if you redistribute, include the upstream licenses for the bundled components (Clipper2, Boost.Polygon).
