"""Optional compas_viewer helper for the live animation (requires ``pip install compas_viewer``).

``animate`` drives a running solve in a top (plan) view fitted to the geometry, groups
sheets and elements (with their holes), and optionally writes the final layout to COMPAS JSON.
"""

from typing import Optional
from typing import Union

from compas.colors import Color
from compas.geometry import Translation

from .collision import collision_solve
from .datastructures import nest_geo
from .datastructures import nest_sheets
from .nfp import nfp_solve

SHEET_COLOR = Color.from_hex("#000000")  # black
ELEMENT_COLOR = Color.from_hex("#0072B2")  # darker COMPAS blue


def _add_region(viewer, parent, name, outline, holes, color):
    group = viewer.scene.add_group(name=name, parent=parent)
    group.add(outline, linecolor=color, linewidth=2)
    for hole in holes:
        group.add(hole, linecolor=color)


def _fit_top(viewer):
    # Look straight down (2D problem) and fit to all geometry. The view setter binds shaders and
    # the fit uploads to the GPU, so the GL context must be current here.
    from compas_viewer.commands import zoom_selected_cmd

    viewer.renderer.makeCurrent()
    viewer.renderer.view = "top"
    viewer.renderer.camera.target.set(0, 0, 0)
    viewer.renderer.camera.position.set(0, 0, 1000)
    zoom_selected_cmd.callback(viewer)
    viewer.renderer.doneCurrent()


def _add_sheets(viewer, sheets):
    group = viewer.scene.add_group(name="sheets")
    for i, sheet in enumerate(sheets.sheets):
        _add_region(viewer, group, "sheet_%d" % i, sheet["outline"], sheet["holes"], SHEET_COLOR)


def animate(
    handle: Union[collision_solve, nfp_solve],
    geo: nest_geo,
    sheets: nest_sheets,
    save: Optional[str] = None,
    park: float = -80.0,
) -> None:
    """Animate a running solve live (top view); save the final layout to ``save`` on close.

    Parameters
    ----------
    handle : :class:`compas_nest.collision_solve` or :class:`compas_nest.nfp_solve`
        What :meth:`compas_nest.opennest_collision.start` or :meth:`compas_nest.opennest.start` returns.
    geo : :class:`compas_nest.nest_geo`
        The parts to draw/save (one viewer object per instance). May differ from the geometry the
        ``handle`` solved — e.g. pass the *original* parts while the solve ran on offset geometry,
        to show the true parts with the resulting gaps (same part order/copies required).
    sheets : :class:`compas_nest.nest_sheets`
        The sheets being nested into.
    save : str, optional
        If given, the final layout is written to this JSON path when the window closes.
    park : float, optional
        Y offset where not-yet-placed elements are staged (below the sheets).
    """
    from compas_viewer import Viewer

    viewer = Viewer()
    _add_sheets(viewer, sheets)

    # one object per part instance, created from the original geometry; only its transform changes
    instances = [(i, part) for i, part in enumerate(geo.parts) for _ in range(max(1, int(part["copies"])))]
    group = viewer.scene.add_group(name="elements")
    objects = []
    for k, (part_index, part) in enumerate(instances):
        sub = viewer.scene.add_group(name="element_%d" % k, parent=group)
        objects.append([sub.add(part["outline"], linecolor=ELEMENT_COLOR, linewidth=2)] + [sub.add(h, linecolor=ELEMENT_COLOR) for h in part["holes"]])

    parked = Translation.from_vector([0.0, park, 0.0])

    @viewer.on(interval=120)
    def _(frame):
        running = handle.is_running()
        layout = handle.snapshot() if running else handle.wait()  # final layout once the solve ends
        viewer.renderer.makeCurrent()
        for k, parts in enumerate(objects):
            placement = layout.placements[k]
            matrix = layout.transformation(placement) if placement["sheet_id"] >= 0 else parked
            for obj in parts:
                obj.transformation = matrix
                obj.update(update_transform=True)
        viewer.renderer.doneCurrent()
        if frame == 0:
            _fit_top(viewer)
        if not running:
            viewer.timer.stop()

    viewer.show()
    handle.cancel()
    if save:
        import os

        result = handle.wait()
        result.geo = geo  # render/serialize the geometry passed here (e.g. the original parts when solving on offset geometry)
        result.to_json(save)
        result.to_obj(os.path.splitext(os.fspath(save))[0] + ".obj")
