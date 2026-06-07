// nanobind binding for Clipper2 polygon offsetting (Inflate / Shrink).
// Reuses the Clipper2 vendored with the NFP engine (external/nest/opennest_cpp/src/clipper2).
//
// delta > 0 inflates a CCW polygon outward; delta < 0 shrinks it inward. A single input polygon
// may yield zero (vanished on shrink) or several output rings, so a list of polygons is returned.
#include <nanobind/nanobind.h>
#include <nanobind/stl/vector.h>
#include <nanobind/stl/array.h>

#include <array>
#include <utility>
#include <vector>

#include "clipper2/clipper.h"

namespace nb = nanobind;
using namespace nb::literals;

using Poly = std::vector<std::array<double, 2>>;
using Polys = std::vector<Poly>;

// join_type: 0 = Square, 1 = Bevel, 2 = Round, 3 = Miter (default).
static Polys inflate(const Polys &polys, double delta, int join_type, double miter_limit)
{
    Clipper2Lib::PathsD paths;
    paths.reserve(polys.size());
    for (const auto &p : polys)
    {
        Clipper2Lib::PathD path;
        path.reserve(p.size());
        for (const auto &q : p)
            path.push_back(Clipper2Lib::PointD(q[0], q[1]));
        paths.push_back(std::move(path));
    }

    Clipper2Lib::PathsD sol = Clipper2Lib::InflatePaths(
        paths, delta, static_cast<Clipper2Lib::JoinType>(join_type),
        Clipper2Lib::EndType::Polygon, miter_limit);

    Polys out;
    out.reserve(sol.size());
    for (const auto &path : sol)
    {
        Poly p;
        p.reserve(path.size());
        for (const auto &q : path)
            p.push_back({q.x, q.y});
        out.push_back(std::move(p));
    }
    return out;
}

NB_MODULE(_clipper, m)
{
    m.doc() = "Clipper2 polygon offsetting.";
    m.def("inflate", &inflate,
          "polygons"_a, "delta"_a, "join_type"_a = 3, "miter_limit"_a = 2.0,
          "Offset closed polygons by delta (>0 outward, <0 inward). Returns offset polygons.");
}
