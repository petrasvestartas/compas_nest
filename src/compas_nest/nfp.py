"""opennest — the NFP + genetic-algorithm nesting engine (the OpenNest component)."""

import sys
import threading
import time

from compas_nest import _nfp_nest  # type: ignore

from .result import nest_result


class nfp_solve:
    """Handle to an NFP solve running on a background thread.

    Returned by :meth:`opennest.start`. Poll :meth:`snapshot` for the current best layout
    (e.g. from a viewer animation callback), check :meth:`is_running`, and call :meth:`wait` for the
    final result.
    """

    def __init__(self, geo, sheet_origins, n_instances, thread, box):
        self.geo = geo
        self.sheet_origins = sheet_origins
        self.n_instances = n_instances
        self._thread = thread
        self._box = box

    def progress(self):
        """int : GA generation reached so far."""
        return _nfp_nest.progress()

    def fitness(self):
        """float : Best fitness so far."""
        return _nfp_nest.fitness()

    def is_running(self):
        """bool : Whether the solve thread is still running."""
        return self._thread.is_alive()

    def cancel(self):
        """Ask the solve to stop and return its best layout so far."""
        _nfp_nest.cancel()

    def _build(self, tx, ty, angle, sheet_id, part_index, n_sheets, fitness=None):
        raw = [
            (part_index[i], sheet_id[i], angle[i], tx[i], ty[i])
            for i in range(self.n_instances)
        ]
        return nest_result._from_engine(raw, self.geo, self.sheet_origins, n_sheets, fitness=fitness, degrees=True)

    def snapshot(self):
        """Build a :class:`compas_nest.nest_result` from the current mid-solve layout."""
        _placed, tx, ty, angle, sheet_id, part_index, n_sheets = _nfp_nest.poll_layout(self.n_instances)
        return self._build(tx, ty, angle, sheet_id, part_index, n_sheets)

    def wait(self):
        """Block until the solve finishes and return the final :class:`compas_nest.nest_result`."""
        self._thread.join()
        _placed, tx, ty, angle, sheet_id, part_index, n_sheets, fitness = self._box["ret"]
        return self._build(tx, ty, angle, sheet_id, part_index, n_sheets, fitness)


class opennest:
    """Nest polylines (with holes) into sheets (with holes) using the NFP + genetic-algorithm engine.

    Replicates the OpenNest grasshopper component, including carrying ``attributes``
    geometry through placement. The solve runs on a background thread while the calling thread prints
    live progress (GA generation + fitness); ``Ctrl-C`` cancels and returns the best layout so far.

    Parameters
    ----------
    generations : int, optional
        GA generations to evolve (the component "Iterations").
    rotations : int, optional
        Discrete rotation count (360 / n orientations).
    placement_type : int, optional
        0 = box, 1 = gravity, 2 = squeeze.
    spacing : float, optional
        Gap between parts.
    seed : int, optional
        RNG seed (-1 = time-based, non-deterministic).
    mutation_rate : int, optional
        GA mutation rate (applied as 0.01 * rate).
    population_size : int, optional
        GA population size.
    use_holes : bool, optional
        Allow nesting into holes.
    try_all_rotations : bool, optional
        Evaluate every rotation per placement (slower, tighter). Defaults to ``False``.

        .. warning::
            The upstream NFP engine's ``tryAllRotations`` path can **crash (segfault)** on some
            mixes of part shapes (e.g. a triangle together with a holed rectangle). Leave this
            ``False`` unless you know your geometry is safe.
    exact_nfp : bool, optional
        Full-resolution exact NFP (no gap, slower).
    mode : int, optional
        0 = faithful (single-thread parity), 1 = default, 2 = turbo (multi-seed).
    num_seeds : int, optional
        Turbo: parallel independent seeds.
    use_parallel : bool, optional
        Parallel NFP / population evaluation.
    curve_tolerance : float, optional
        Simplification tolerance.
    clipper_scale : float, optional
        Clipper integer scale.
    time_budget_secs : float, optional
        If > 0, run until elapsed (overrides ``generations``).
    max_sheets : int, optional
        0 = use all provided sheets.
    verbose : bool, optional
        Print progress to the terminal.
    """

    def __init__(
        self,
        generations=10,
        rotations=8,
        placement_type=1,
        spacing=0.0,
        seed=30,
        mutation_rate=10,
        population_size=10,
        use_holes=True,
        try_all_rotations=False,
        exact_nfp=False,
        mode=1,
        num_seeds=4,
        use_parallel=True,
        curve_tolerance=0.3,
        clipper_scale=1e7,
        sheet_spacing=0.0,
        rotation_limit=360.0,
        time_budget_secs=0.0,
        max_sheets=0,
        verbose=True,
    ):
        self.generations = generations
        self.rotations = rotations
        self.placement_type = placement_type
        self.spacing = spacing
        self.seed = seed
        self.mutation_rate = mutation_rate
        self.population_size = population_size
        self.use_holes = use_holes
        self.try_all_rotations = try_all_rotations
        self.exact_nfp = exact_nfp
        self.mode = mode
        self.num_seeds = num_seeds
        self.use_parallel = use_parallel
        self.curve_tolerance = curve_tolerance
        self.clipper_scale = clipper_scale
        self.sheet_spacing = sheet_spacing
        self.rotation_limit = rotation_limit
        self.time_budget_secs = time_budget_secs
        self.max_sheets = max_sheets
        self.verbose = verbose

    def _params(self):
        p = _nfp_nest.NfpParams()
        p.placementType = int(self.placement_type)
        p.rotations = max(1, int(self.rotations))
        p.mutationRate = int(self.mutation_rate)
        p.populationSize = max(1, int(self.population_size))
        p.seed = int(self.seed)
        p.curveTolerance = float(self.curve_tolerance)
        p.clipperScale = float(self.clipper_scale)
        p.spacing = float(self.spacing)
        p.sheetSpacing = float(self.sheet_spacing)
        p.rotationLimit = float(self.rotation_limit)
        p.useHoles = 1 if self.use_holes else 0
        p.exploreConcave = 0
        p.clipByHull = 0
        p.clipByRects = 0
        p.simplify = 0
        p.mode = int(self.mode)
        p.generations = int(self.generations)
        p.numSeeds = int(self.num_seeds)
        p.useParallel = 1 if self.use_parallel else 0
        p.timeBudgetSecs = float(self.time_budget_secs)
        p.maxSheets = int(self.max_sheets)
        p.edgeSamples = 0
        p.compactionPasses = 0
        p.tryAllRotations = 1 if self.try_all_rotations else 0
        p.exactNfp = 1 if self.exact_nfp else 0
        return p

    def start(self, geo, sheets):
        """Launch the solve on a background thread and return immediately.

        Use this for live/animated UIs: poll :meth:`nfp_solve.snapshot` while
        :meth:`nfp_solve.is_running` is true, then call :meth:`nfp_solve.wait`.

        Parameters
        ----------
        geo : :class:`compas_nest.nest_geo`
            Parts to nest (``copies`` handled natively as quantities; instance order is
            part0 x q0, part1 x q1, ...).
        sheets : :class:`compas_nest.nest_sheets`
            Sheets to nest into.

        Returns
        -------
        :class:`nfp_solve`
        """
        parts = geo._flatten_parts(expand_copies=False)
        sh = sheets.to_arrays()
        params = self._params()
        n_instances = sum(parts["quantities"])

        box = {}

        def work():
            box["ret"] = _nfp_nest.nest(
                parts["vertex_counts"], parts["xy"], parts["quantities"],
                parts["hole_counts"], parts["hole_vertex_counts"], parts["hole_xy"],
                sh["vertex_counts"], sh["xy"],
                sh["hole_counts"], sh["hole_vertex_counts"], sh["hole_xy"],
                params,
                parts["rotations"],   # per-part rotation overrides (0 = global)
            )

        _nfp_nest.cancel_reset()
        thread = threading.Thread(target=work, daemon=True)
        thread.start()
        return nfp_solve(geo, sh["origins"], n_instances, thread, box)

    def solve(self, geo, sheets):
        """Run the nest, blocking until done (prints progress when ``verbose``).

        Parameters
        ----------
        geo : :class:`compas_nest.nest_geo`
            Parts to nest (``copies`` handled natively as quantities).
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
                    sys.stdout.write("\r[opennest] gen {} / {}   fit {:.3f}   (Ctrl-C = stop)".format(handle.progress(), self.generations, handle.fitness()))
                    sys.stdout.flush()
                time.sleep(0.1)
        except KeyboardInterrupt:
            handle.cancel()
        result = handle.wait()
        if self.verbose:
            sys.stdout.write("\n")
            print("[opennest] placed {}/{} instances on {} sheet(s), fitness {:.3f}.".format(len(result.placed), len(result.placements), result.n_sheets, result.fitness or 0.0))
        return result
