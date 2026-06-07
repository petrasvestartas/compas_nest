from compas.data import json_dumps
from compas.data import json_loads
from compas.geometry import Polyline

import pytest

from compas_nest import nest_geo
from compas_nest import nest_sheets
from compas_nest import offset_geo
from compas_nest import offset_polyline
from compas_nest import offset_sheets
from compas_nest import opennest
from compas_nest import opennest_collision
from compas_nest import pack
from compas_nest import text_to_polylines


def rect(x0, y0, w, h):
    return Polyline([[x0, y0, 0], [x0 + w, y0, 0], [x0 + w, y0 + h, 0], [x0, y0 + h, 0], [x0, y0, 0]])


def _area(polyline):
    pts = list(polyline.points)
    if pts[0] == pts[-1]:
        pts = pts[:-1]
    a = 0.0
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i][0], pts[i][1]
        x2, y2 = pts[(i + 1) % n][0], pts[(i + 1) % n][1]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2


@pytest.fixture
def geo():
    g = nest_geo()
    g.add_part(rect(0, 0, 20, 10), copies=3)
    g.add_part(rect(0, 0, 15, 15), holes=[rect(5, 5, 5, 5)], copies=2)
    return g


@pytest.fixture
def sheets():
    s = nest_sheets()
    s.add_sheet(rect(0, 0, 100, 100), holes=[rect(40, 40, 10, 10)])
    return s


def _assert_within_sheet(result, w=100, h=100):
    for group in result.placed_polylines():
        for part in group["parts"]:
            for p in part["outline"].points:
                assert -1e-6 <= p[0] <= w + 1e-6
                assert -1e-6 <= p[1] <= h + 1e-6


def test_collision_places_all(geo, sheets):
    result = opennest_collision(iterations=300, num_rotations=16, seed=1, verbose=False).solve(geo, sheets)
    assert len(result.placed) == 5
    assert len(result.unplaced) == 0
    assert result.n_sheets >= 1
    _assert_within_sheet(result)


def test_nfp_places_all(geo, sheets):
    result = opennest(generations=5, rotations=4, seed=1, num_seeds=2, verbose=False).solve(geo, sheets)
    assert len(result.placed) == 5
    assert result.fitness is not None
    _assert_within_sheet(result)


def test_serialization_roundtrip(geo, sheets):
    geo2 = json_loads(json_dumps(geo))
    assert len(geo2.parts) == 2
    assert geo2.parts[1]["copies"] == 2
    assert len(geo2.parts[1]["holes"]) == 1
    assert isinstance(geo2.parts[0]["outline"], Polyline)

    sheets2 = json_loads(json_dumps(sheets))
    assert len(sheets2.sheets) == 1
    assert len(sheets2.sheets[0]["holes"]) == 1


def test_result_to_json(geo, sheets, tmp_path):
    result = opennest_collision(iterations=200, num_rotations=8, seed=1, verbose=False).solve(geo, sheets)
    path = result.to_json(str(tmp_path / "out.json"))
    data = json_loads(open(path).read())
    assert data["n_sheets"] >= 1
    assert len(data["sheets"]) >= 1


def test_offset_polyline_directions():
    square = rect(0, 0, 10, 10)
    assert _area(offset_polyline(square, 2)) > 100  # grow
    assert _area(offset_polyline(square, -2)) < 100  # shrink


def test_offset_geo_and_sheets(geo, sheets):
    g2 = offset_geo(geo, 1.0)
    assert _area(g2.parts[1]["outline"]) > _area(geo.parts[1]["outline"])  # element outer grown
    assert _area(g2.parts[1]["holes"][0]) < _area(geo.parts[1]["holes"][0])  # element hole shrunk

    s2 = offset_sheets(sheets, 2.0)
    assert _area(s2.sheets[0]["outline"]) < _area(sheets.sheets[0]["outline"])  # sheet outer shrunk
    assert _area(s2.sheets[0]["holes"][0]) > _area(sheets.sheets[0]["holes"][0])  # sheet hole grown


def test_offset_clearance_end_to_end(geo, sheets):
    d = 2.0
    result = opennest_collision(iterations=400, num_rotations=16, seed=1, verbose=False).solve(
        offset_geo(geo, d), offset_sheets(sheets, d)
    )
    # render the ORIGINAL parts at the solved poses; they must stay inside the original sheet
    for group in result.placed_polylines(geo=geo):
        for part in group["parts"]:
            for p in part["outline"].points:
                assert -1e-6 <= p[0] <= 100 + 1e-6
                assert -1e-6 <= p[1] <= 100 + 1e-6


def test_pack_grid(geo):
    result = pack(geo, columns=2, gap_x=5.0, gap_y=5.0)
    assert len(result.placed) == 5  # 3 + 2 copies, all placed
    assert result.n_sheets == 1
    # the four corners of each placed outline are finite and the layout spans > one cell
    xs = [p[0] for g in result.placed_polylines() for part in g["parts"] for p in part["outline"].points]
    assert max(xs) > 20  # wrapped/advanced beyond a single part


def test_text_to_polylines():
    strokes = text_to_polylines("AB", height=10.0)
    assert len(strokes) >= 3  # A = 2 strokes, B = 1
    ys = [p[1] for pl in strokes for p in pl.points]
    assert max(ys) <= 10.0 + 1e-6  # scaled to height
    # a curved glyph is arc-sampled (not a single chord)
    assert max(len(pl.points) for pl in text_to_polylines("C", height=10.0)) > 3


def test_result_serialization_roundtrip(geo, sheets):
    result = opennest_collision(iterations=200, num_rotations=8, seed=1, verbose=False).solve(geo, sheets)
    reloaded = json_loads(json_dumps(result))
    assert type(reloaded).__name__ == "nest_result"
    assert reloaded.n_sheets == result.n_sheets
    assert len(reloaded.placed) == len(result.placed)
    assert len(reloaded.placed_polylines()) == len(result.placed_polylines())  # geo survived too


def test_text_frame_places_and_orients():
    from compas.geometry import Frame

    plain = text_to_polylines("A", height=10.0)
    framed = text_to_polylines("A", height=10.0, frame=Frame([100, 0, 0], [1, 0, 0], [0, 1, 0]))
    assert framed[0].points[0][0] > plain[0].points[0][0] + 90  # shifted to the frame origin


def test_from_size_factory():
    sheets = nest_sheets.from_size(100, 50, count=2)
    assert len(sheets.sheets) == 2
    origins = sheets.origins()
    assert origins[0][0] == 0.0
    assert origins[1][0] > origins[0][0]
