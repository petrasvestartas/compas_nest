# Examples

Each example builds the input, runs an engine, shows the result in compas_viewer, and writes the
placed geometry to `data/output/` as JSON (full result) and OBJ (outlines + holes).

1. [Collision](01_collision_viewer.md) — physics/relaxation engine, default viewer.
2. [NFP + GA](02_nfp_viewer.md) — NFP + genetic-algorithm engine.
3. [Live animation (NFP)](03_nfp_animated.md) — watch the GA layout evolve.
4. [Clearance offset](04_collision_dataset.md) — add gaps with `offset_geo` / `offset_sheets`.
5. [Attributes](05_attributes.md) — carry geometry (a centroid point) through placement.
6. [Pack (array)](06_pack_array.md) — fixed number of elements per row with `pack`.
7. [Pack (distance)](07_pack_distance.md) — wrap by row width with `pack(max_width=...)`.
8. [Text (font)](08_text.md) — single-stroke text with `text_to_polylines`.
