# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## Unreleased

### Added

* `nest_geo` and `nest_sheets` COMPAS `Data` containers (replicating the OpenNest C# `nest_geo` / `nest_sheets`).
* `opennest_collision` wrapper around the physics / overlap-relaxation engine (`np_nest`), with a non-blocking `start()` + `collision_solve` handle for live animation.
* `opennest` wrapper around the NFP + genetic-algorithm engine (`nfp_nest`).
* `nest_result` with world-placed geometry grouped per sheet and `to_json()` (placed polylines + transformations) serialization.
* nanobind C++ bindings `_nest_physics` and `_nfp_nest`.
* compas_viewer examples (top view, grouped scene, live animation, real 48-element dataset) and pytest smoke tests.

### Changed

### Removed
