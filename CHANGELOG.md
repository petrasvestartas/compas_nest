# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## Unreleased

### Added

* `nest_geo` and `nest_sheets` COMPAS `Data` containers (replicating the OpenNest C# `nest_geo` / `nest_sheets`).
* `opennest_collision` wrapper around the physics / overlap-relaxation engine (`np_nest`), with a non-blocking `start()` + `collision_solve` handle for live animation.
* `opennest` wrapper around the NFP + genetic-algorithm engine (`nfp_nest`).
* `nest_result` with world-placed geometry grouped per sheet and `to_json()` (placed polylines + transformations) serialization.
* nanobind C++ bindings `_nest_physics`, `_nfp_nest`, and `_clipper` (Clipper2 offsetting).
* `opennest.start()` + `nfp_solve` handle for live NFP animation.
* `offset_geo` / `offset_sheets` / `offset_polyline` — Clipper2 clearance offsetting (elements grow, sheets shrink); `nest_result.placed_polylines(geo=...)` to render original parts after solving on offset geometry.
* `pack` — simple grid/array layout (no solving) returning a `nest_result`.
* `text_to_polylines` — single-stroke text from the OpenNest XML fonts (`regular` / `bold`).
* `nest_result.to_obj()` — placed outlines + holes as OBJ; examples save JSON + OBJ.
* compas_viewer examples (top view, grouped scene, live animation, real 48-element dataset) and pytest smoke tests.

### Changed

* Version is now derived from git via setuptools-scm (every push publishes a `0.1.1.devN`; tag `vX.Y.Z` for a release).

### Removed
