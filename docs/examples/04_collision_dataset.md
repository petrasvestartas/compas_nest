# 04 · Clearance offset

The 48-element dataset nested into two 510x635 sheets with a clearance offset (`offset_geo` /
`offset_sheets`): the solve runs on offset geometry, and the *original* parts are drawn at the solved
poses so the real clearance gaps are visible.

![clearance](../images/04_collision_dataset.gif)

```python
--8<-- "examples/04_collision_dataset.py"
```
