# Examples

Each example builds the input, runs an engine, shows the result in compas_viewer, and writes the
placed geometry to `data/output/` as JSON (full result) and OBJ (outlines + holes).

- [Collision](01_collision.md) — physics/relaxation engine, default viewer.
- [NFP + GA](02_nfp.md) — NFP + genetic-algorithm engine.
- [Live animation (NFP)](03_nfp_animated.md) — watch the GA layout evolve.
- [Clearance offset](04_clearance.md) — add gaps with `offset_geo` / `offset_sheets`.
- [Attributes](05_attributes.md) — carry geometry (a centroid point) through placement.
