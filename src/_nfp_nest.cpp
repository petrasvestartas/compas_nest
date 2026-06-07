// nanobind binding for the OpenNest NFP + genetic-algorithm engine.
// Wraps the cdecl C ABI in external/nest/opennest_cpp/src/capi/nfp_nest_capi.h.
//
// Output arrays are length = instance_count = sum(part_quantities), emitted in
// expansion order (part0 x q0, part1 x q1, ...). The solve releases the GIL so a
// Python thread can poll progress() / fitness() / cancel().
#include <nanobind/nanobind.h>
#include <nanobind/stl/vector.h>
#include <nanobind/stl/tuple.h>

#include <numeric>
#include <vector>

#include "capi/nfp_nest_capi.h"

namespace nb = nanobind;
using namespace nb::literals;

static const int *ip(const std::vector<int> &v) { return v.empty() ? nullptr : v.data(); }
static const double *dp(const std::vector<double> &v) { return v.empty() ? nullptr : v.data(); }

NB_MODULE(_nfp_nest, m)
{
    m.doc() = "OpenNest NFP + genetic-algorithm nesting engine (nfp_nest).";

    nb::class_<NfpParams>(m, "NfpParams")
        .def(nb::init<>())
        .def_rw("placementType", &NfpParams::placementType)
        .def_rw("rotations", &NfpParams::rotations)
        .def_rw("mutationRate", &NfpParams::mutationRate)
        .def_rw("populationSize", &NfpParams::populationSize)
        .def_rw("seed", &NfpParams::seed)
        .def_rw("curveTolerance", &NfpParams::curveTolerance)
        .def_rw("clipperScale", &NfpParams::clipperScale)
        .def_rw("spacing", &NfpParams::spacing)
        .def_rw("sheetSpacing", &NfpParams::sheetSpacing)
        .def_rw("rotationLimit", &NfpParams::rotationLimit)
        .def_rw("useHoles", &NfpParams::useHoles)
        .def_rw("exploreConcave", &NfpParams::exploreConcave)
        .def_rw("clipByHull", &NfpParams::clipByHull)
        .def_rw("clipByRects", &NfpParams::clipByRects)
        .def_rw("simplify", &NfpParams::simplify)
        .def_rw("mode", &NfpParams::mode)
        .def_rw("generations", &NfpParams::generations)
        .def_rw("numSeeds", &NfpParams::numSeeds)
        .def_rw("useParallel", &NfpParams::useParallel)
        .def_rw("timeBudgetSecs", &NfpParams::timeBudgetSecs)
        .def_rw("maxSheets", &NfpParams::maxSheets)
        .def_rw("edgeSamples", &NfpParams::edgeSamples)
        .def_rw("compactionPasses", &NfpParams::compactionPasses)
        .def_rw("tryAllRotations", &NfpParams::tryAllRotations)
        .def_rw("exactNfp", &NfpParams::exactNfp);

    // nest(...) -> (placed, tx, ty, angle, sheet_id, part_index, n_sheets, fitness)
    // angle is in DEGREES. Output arrays have length sum(part_quantities).
    m.def(
        "nest",
        [](const std::vector<int> &part_vertex_counts,
           const std::vector<double> &part_xy,
           const std::vector<int> &part_quantities,
           const std::vector<int> &part_hole_counts,
           const std::vector<int> &part_hole_vertex_counts,
           const std::vector<double> &part_hole_xy,
           const std::vector<int> &sheet_vertex_counts,
           const std::vector<double> &sheet_xy,
           const std::vector<int> &sheet_hole_counts,
           const std::vector<int> &sheet_hole_vertex_counts,
           const std::vector<double> &sheet_hole_xy,
           const NfpParams &params)
        {
            int part_count = static_cast<int>(part_vertex_counts.size());
            int sheet_count = static_cast<int>(sheet_vertex_counts.size());
            int instance_count = std::accumulate(part_quantities.begin(), part_quantities.end(), 0);

            std::vector<double> tx(instance_count, 0.0), ty(instance_count, 0.0), angle(instance_count, 0.0);
            std::vector<int> sheet_id(instance_count, -1), part_index(instance_count, -1);
            int n_sheets = 0;
            double fitness = 0.0;
            NfpParams p = params;

            int placed = nfp_nest(
                part_count, ip(part_vertex_counts), dp(part_xy), ip(part_quantities),
                ip(part_hole_counts), ip(part_hole_vertex_counts), dp(part_hole_xy),
                sheet_count, ip(sheet_vertex_counts), dp(sheet_xy),
                ip(sheet_hole_counts), ip(sheet_hole_vertex_counts), dp(sheet_hole_xy),
                &p,
                tx.data(), ty.data(), angle.data(), sheet_id.data(), part_index.data(),
                &n_sheets, &fitness);

            return std::make_tuple(placed, std::move(tx), std::move(ty), std::move(angle),
                                   std::move(sheet_id), std::move(part_index), n_sheets, fitness);
        },
        "part_vertex_counts"_a, "part_xy"_a, "part_quantities"_a,
        "part_hole_counts"_a, "part_hole_vertex_counts"_a, "part_hole_xy"_a,
        "sheet_vertex_counts"_a, "sheet_xy"_a,
        "sheet_hole_counts"_a, "sheet_hole_vertex_counts"_a, "sheet_hole_xy"_a,
        "params"_a,
        "Nest part instances onto sheets. Returns "
        "(placed, tx, ty, angle, sheet_id, part_index, n_sheets, fitness).",
        nb::call_guard<nb::gil_scoped_release>());

    m.def("progress", &nfp_progress, "GA generation reached so far.");
    m.def("fitness", &nfp_fitness, "Best fitness so far.");
    m.def("cancel", &nfp_cancel, "Ask the running solve to stop.");
    m.def("cancel_reset", &nfp_cancel_reset, "Clear the cancel flag.");

    // poll_layout(instance_count) -> (placed, tx, ty, angle, sheet_id, part_index, n_sheets)
    m.def(
        "poll_layout",
        [](int instance_count)
        {
            std::vector<double> tx(instance_count, 0.0), ty(instance_count, 0.0), angle(instance_count, 0.0);
            std::vector<int> sheet_id(instance_count, -1), part_index(instance_count, -1);
            int n_sheets = 0;
            int placed = nfp_poll_layout(instance_count, tx.data(), ty.data(), angle.data(),
                                         sheet_id.data(), part_index.data(), &n_sheets);
            return std::make_tuple(placed, std::move(tx), std::move(ty), std::move(angle),
                                   std::move(sheet_id), std::move(part_index), n_sheets);
        },
        "instance_count"_a,
        "Snapshot the current best layout mid-solve.");
}
