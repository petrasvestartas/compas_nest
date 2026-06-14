// nanobind binding for the nest_physics (collision / overlap-relaxation) engine.
// Wraps the cdecl C ABI in external/nest/nest_physics_cpp/nest_physics_capi.h.
//
// Geometry crosses as flat 1-D arrays exactly as the C ABI expects; the Python
// layer (compas_nest.datastructures) builds these from nest_geo / nest_sheets.
// The solve releases the GIL so a Python thread can poll progress() / cancel().
#include <nanobind/nanobind.h>
#include <nanobind/stl/vector.h>
#include <nanobind/stl/tuple.h>

#include <vector>

#include "nest_physics_capi.h"

namespace nb = nanobind;
using namespace nb::literals;

// NULL the engine's optional pointers when a buffer is empty (the C ABI treats
// NULL hole arrays as "no holes").
static const int *ip(const std::vector<int> &v) { return v.empty() ? nullptr : v.data(); }
static const double *dp(const std::vector<double> &v) { return v.empty() ? nullptr : v.data(); }

NB_MODULE(_nest_physics, m)
{
    m.doc() = "nest_physics collision/overlap-relaxation nesting engine (np_nest).";

    nb::class_<NpParams>(m, "NpParams")
        .def(nb::init<>())
        .def_rw("num_rotations", &NpParams::num_rotations)
        .def_rw("spacing", &NpParams::spacing)
        .def_rw("simplify_tolerance", &NpParams::simplify_tolerance)
        .def_rw("seed", &NpParams::seed)
        .def_rw("time_budget_secs", &NpParams::time_budget_secs)
        .def_rw("iter_budget", &NpParams::iter_budget)
        .def_rw("iter_mode", &NpParams::iter_mode)
        .def_rw("max_sheets", &NpParams::max_sheets)
        .def_rw("n_starts", &NpParams::n_starts)
        .def_rw("part_holes_mode", &NpParams::part_holes_mode)
        .def_rw("pole_max", &NpParams::pole_max)
        .def_rw("final_compact", &NpParams::final_compact)
        .def_rw("fit_mode", &NpParams::fit_mode);

    // nest(...) -> (rc, tx, ty, angle, sheet_id, n_sheets)
    // tx/ty/angle/sheet_id have length part_count (number of part outer rings).
    m.def(
        "nest",
        [](const std::vector<int> &part_vertex_counts,
           const std::vector<double> &part_xy,
           const std::vector<int> &sheet_outer_vertex_counts,
           const std::vector<double> &sheet_outer_xy,
           const std::vector<int> &sheet_hole_counts,
           const std::vector<int> &hole_vertex_counts,
           const std::vector<double> &hole_xy,
           const std::vector<int> &part_hole_counts,
           const std::vector<int> &part_hole_vertex_counts,
           const std::vector<double> &part_hole_xy,
           const NpParams &params,
           const std::vector<int> &part_rotations)
        {
            int part_count = static_cast<int>(part_vertex_counts.size());
            int sheet_count = static_cast<int>(sheet_outer_vertex_counts.size());

            std::vector<double> tx(part_count, 0.0), ty(part_count, 0.0), angle(part_count, 0.0);
            std::vector<int> sheet_id(part_count, -1);
            int n_sheets = 0;
            NpParams p = params;

            int rc = np_nest(
                part_count, ip(part_vertex_counts), dp(part_xy),
                ip(part_rotations),
                sheet_count, ip(sheet_outer_vertex_counts), dp(sheet_outer_xy),
                ip(sheet_hole_counts), ip(hole_vertex_counts), dp(hole_xy),
                ip(part_hole_counts), ip(part_hole_vertex_counts), dp(part_hole_xy),
                &p,
                tx.data(), ty.data(), angle.data(), sheet_id.data(), &n_sheets);

            return std::make_tuple(rc, std::move(tx), std::move(ty),
                                   std::move(angle), std::move(sheet_id), n_sheets);
        },
        "part_vertex_counts"_a, "part_xy"_a,
        "sheet_outer_vertex_counts"_a, "sheet_outer_xy"_a,
        "sheet_hole_counts"_a, "hole_vertex_counts"_a, "hole_xy"_a,
        "part_hole_counts"_a, "part_hole_vertex_counts"_a, "part_hole_xy"_a,
        "params"_a,
        "part_rotations"_a = std::vector<int>(),
        "Nest part outer rings onto sheets. Returns (rc, tx, ty, angle, sheet_id, n_sheets). "
        "part_rotations is an optional per-part rotation override (one int per part: "
        "0 = use params.num_rotations; N = only N orientations; 1 = fixed); empty = global.",
        nb::call_guard<nb::gil_scoped_release>());

    // Live progress / cancellation (safe to call from another thread during nest()).
    m.def("progress", &np_progress, "Relaxation rounds completed so far.");
    m.def("cancel", &np_cancel, "Ask the running solve to stop at the next round.");
    m.def("cancel_reset", &np_cancel_reset, "Clear the cancel flag.");

    // poll_layout(part_count) -> (placed, tx, ty, angle, sheet_id, n_sheets)
    m.def(
        "poll_layout",
        [](int part_count)
        {
            std::vector<double> tx(part_count, 0.0), ty(part_count, 0.0), angle(part_count, 0.0);
            std::vector<int> sheet_id(part_count, -1);
            int n_sheets = 0;
            int placed = np_poll_layout(part_count, tx.data(), ty.data(),
                                        angle.data(), sheet_id.data(), &n_sheets);
            return std::make_tuple(placed, std::move(tx), std::move(ty),
                                   std::move(angle), std::move(sheet_id), n_sheets);
        },
        "part_count"_a,
        "Snapshot the current best layout mid-solve.");
}
