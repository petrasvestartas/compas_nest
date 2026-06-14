"""opennest_collision — the physics / overlap-relaxation nesting engine."""

import sys
import threading
import time

from compas_nest import _nest_physics  # type: ignore

from .result import nest_result


class collision_solve:
    """Handle to a collision solve running on a background thread.

    Returned by :meth:`opennest_collision.start`. Poll :meth:`snapshot` for the current best layout
    (e.g. from a viewer animation callback), check :meth:`is_running`, and call :meth:`wait` for the
    final result.
    """

    def __init__(self, geo, sheet_origins, origin_index, n_instances, thread, box):
        self.geo = geo
        self.sheet_origins = sheet_origins
        self.origin_index = origin_index
        self.n_instances = n_instances
        self._thread = thread
        self._box = box

    def progress(self):
        """int : Relaxation rounds completed so far."""
        return _nest_physics.progress()

    def is_running(self):
        """bool : Whether the solve thread is still running."""
        return self._thread.is_alive()

    def cancel(self):
        """Ask the solve to stop at the next round and return its best layout so far."""
        _nest_physics.cancel()

    def _build(self, tx, ty, angle, sheet_id, n_sheets):
        raw = [
            (self.origin_index[i], sheet_id[i], angle[i], tx[i], ty[i])
            for i in range(self.n_instances)
        ]
        return nest_result._from_engine(raw, self.geo, self.sheet_origins, n_sheets, degrees=False)

    def snapshot(self):
        """Build a :class:`compas_nest.nest_result` from the current mid-solve layout."""
        _placed, tx, ty, angle, sheet_id, n_sheets = _nest_physics.poll_layout(self.n_instances)
        return self._build(tx, ty, angle, sheet_id, n_sheets)

    def wait(self):
        """Block until the solve finishes and return the final :class:`compas_nest.nest_result`."""
        self._thread.join()
        _rc, tx, ty, angle, sheet_id, n_sheets = self._box["ret"]
        return self._build(tx, ty, angle, sheet_id, n_sheets)


class opennest_collision:
    """Nest polylines (with holes) into sheets (with holes) using the collision/relaxation engine.

    Replicates the OpenNest ``OpenNestCollision`` Grasshopper component. The solve runs on a background
    thread while the calling thread prints live progress (relaxation rounds); ``Ctrl-C`` cancels and
    returns the best layout found so far.

    Parameters
    ----------
    iterations : int, optional
        Relaxation-round budget (deterministic). ~4000 packs tight on one sheet; ~1 is a rough preview.
    num_rotations : int, optional
        Discrete orientations sampled per part (more = tighter, slower).
    spacing : float, optional
        Minimum gap kept between parts and from holes.
    seed : int, optional
        Base RNG seed.
    n_starts : int, optional
        Multi-start: run this many seeds and keep the densest.
    part_holes_mode : int, optional
        0 = ignore part holes, 1 = nest smaller parts into larger parts' holes.
    pole_max : int, optional
        Inscribed circles per part for collision tests (more = accurate, fewer = faster).
    final_compact : int, optional
        0 = off, 1 = bottom-left post-pack slide, 2 = multi-direction.
    fit_mode : int, optional
        0 = place all parts on fewest sheets, 1 = single sheet, max fill.
    max_sheets : int, optional
        Cap on sheets used (0 = engine default of 6).
    time_budget_secs : float, optional
        If > 0, use a wall-clock budget instead of ``iterations``.
    simplify_tolerance : float, optional
        Geometry simplification tolerance (<= 0 keeps the lean default).
    verbose : bool, optional
        Print progress to the terminal.
    """

    def __init__(
        self,
        iterations=4000,
        num_rotations=3600,
        spacing=0.0,
        seed=100,
        n_starts=1,
        part_holes_mode=1,  # 1 = fill (nest into holes)
        pole_max=16,
        final_compact=2,  # 2 = multi-direction compaction
        fit_mode=1,  # 1 = one sheet, max fill
        max_sheets=0,
        time_budget_secs=0.0,
        simplify_tolerance=0.0,
        verbose=True,
    ):
        self.iterations = iterations
        self.num_rotations = num_rotations
        self.spacing = spacing
        self.seed = seed
        self.n_starts = n_starts
        self.part_holes_mode = part_holes_mode
        self.pole_max = pole_max
        self.final_compact = final_compact
        self.fit_mode = fit_mode
        self.max_sheets = max_sheets
        self.time_budget_secs = time_budget_secs
        self.simplify_tolerance = simplify_tolerance
        self.verbose = verbose

    def _params(self):
        p = _nest_physics.NpParams()
        p.num_rotations = max(1, int(self.num_rotations))
        p.spacing = float(self.spacing)
        p.simplify_tolerance = float(self.simplify_tolerance)
        p.seed = int(self.seed)
        p.n_starts = int(self.n_starts)
        p.part_holes_mode = int(self.part_holes_mode)
        p.pole_max = int(self.pole_max)
        p.final_compact = int(self.final_compact)
        p.fit_mode = int(self.fit_mode)
        p.max_sheets = int(self.max_sheets)
        if self.time_budget_secs > 0:
            p.iter_mode = 0
            p.time_budget_secs = float(self.time_budget_secs)
            p.iter_budget = 0
        else:
            p.iter_mode = 1
            p.iter_budget = int(self.iterations)
            p.time_budget_secs = 0.0
        return p

    def start(self, geo, sheets):
        """Launch the solve on a background thread and return immediately.

        Use this for live/animated UIs: poll :meth:`collision_solve.snapshot` while
        :meth:`collision_solve.is_running` is true, then call :meth:`collision_solve.wait`.

        Parameters
        ----------
        geo : :class:`compas_nest.nest_geo`
            Parts to nest. ``copies`` are expanded into separate instances (the instance order matches
            the snapshot/result arrays).
        sheets : :class:`compas_nest.nest_sheets`
            Sheets to nest into.

        Returns
        -------
        :class:`collision_solve`
        """
        parts = geo._flatten_parts(expand_copies=True)
        sh = sheets.to_arrays()
        params = self._params()
        # The engine tiles sheet 0 up to max_sheets; cap to the sheets we actually provide so it
        # never returns a sheet_id without a matching origin.
        n_sheets = len(sheets.sheets)
        params.max_sheets = min(self.max_sheets, n_sheets) if self.max_sheets > 0 else n_sheets

        box = {}

        def work():
            box["ret"] = _nest_physics.nest(
                parts["vertex_counts"], parts["xy"],
                sh["vertex_counts"], sh["xy"],
                sh["hole_counts"], sh["hole_vertex_counts"], sh["hole_xy"],
                parts["hole_counts"], parts["hole_vertex_counts"], parts["hole_xy"],
                params,
                parts["rotations"],   # per-part rotation overrides (0 = global)
            )

        _nest_physics.cancel_reset()
        thread = threading.Thread(target=work, daemon=True)
        thread.start()
        return collision_solve(geo, sh["origins"], parts["origin_index"], len(parts["vertex_counts"]), thread, box)

    def solve(self, geo, sheets):
        """Run the nest, blocking until done (prints progress when ``verbose``).

        Parameters
        ----------
        geo : :class:`compas_nest.nest_geo`
            Parts to nest. ``copies`` are expanded into separate instances.
        sheets : :class:`compas_nest.nest_sheets`
            Sheets to nest into.

        Returns
        -------
        :class:`compas_nest.nest_result`
        """
        handle = self.start(geo, sheets)
        try:
            while handle.is_running():
                if self.verbose:
                    sys.stdout.write("\r[opennest_collision] {} / ~{} rounds  (Ctrl-C = stop)".format(handle.progress(), self.iterations))
                    sys.stdout.flush()
                time.sleep(0.1)
        except KeyboardInterrupt:
            handle.cancel()
        result = handle.wait()
        if self.verbose:
            sys.stdout.write("\n")
            print("[opennest_collision] placed {}/{} instances on {} sheet(s).".format(len(result.placed), len(result.placements), result.n_sheets))
        return result
