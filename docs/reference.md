# API Reference

## Engines

::: compas_nest.opennest_collision

::: compas_nest.opennest

::: compas_nest.collision_solve

## Data structures

::: compas_nest.nest_geo

::: compas_nest.nest_sheets

## Result

::: compas_nest.nest_result

## Offsetting

Add clearance before nesting (Clipper2): elements grow, sheets shrink. Solve on the offset
geometry, then render the original parts with `nest_result.placed_polylines(geo=original)`.

::: compas_nest.offset_geo

::: compas_nest.offset_sheets

::: compas_nest.offset_polyline

## Viewer helper (optional)

Requires `compas_viewer`.

::: compas_nest.viewer.animate
