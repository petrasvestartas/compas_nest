# Examples

Each example builds the input, runs an engine, shows the result in compas_viewer, and writes the
placed geometry to `data/output/` as JSON (full result) and OBJ (outlines + holes).

1. [Collision](01_collision_viewer.md) — physics/relaxation engine, default viewer.
2. [NFP + GA](02_nfp_viewer.md) — NFP + genetic-algorithm engine.
3. [Live animation (NFP)](03_nfp_animated.md) — watch the GA layout evolve.
4. [Clearance offset](04_collision_dataset.md) — add gaps with `offset_geo` / `offset_sheets`.
5. [Attributes](05_attributes.md) — carry geometry (a centroid point) through placement.
