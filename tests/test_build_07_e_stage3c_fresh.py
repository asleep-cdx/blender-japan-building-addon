"""Fresh Stage-3C ordinary Winder Side Board continuation."""

from dataclasses import replace
import hashlib
import math
import pathlib
import sys
import types
import unittest


ROOT = pathlib.Path(__file__).parents[1]
package = sys.modules.get("japanese_house_modeler")
if package is None:
    package = types.ModuleType("japanese_house_modeler")
    package.__path__ = [str(ROOT / "japanese_house_modeler")]
    sys.modules["japanese_house_modeler"] = package

from japanese_house_modeler.stair_geometry import validate_mesh_fragments
from japanese_house_modeler.stair_multiflight import prepare_multiflight_residential_geometry
from japanese_house_modeler.stair_residential import ResidentialFields
from japanese_house_modeler.stair_turn import (
    ScopeUnsupportedError, TurnSpec, _board_outer_distance,
    _canonical_outer_station,
    physical_cell_boundaries, prepare_turn_residential_geometry,
    winder_tread_rear_outer_authority, winder_underbody_support_footprint,
)


L = ((0.0, 0.0), (0.0, 2.2), (-2.2, 2.2))
COMPACT_U = ((0.0, 0.0), (0.0, 2.2), (0.9, 2.2), (0.9, 0.0))
ORDINARY_U = ((0.0, 0.0), (0.0, 2.2), (2.0, 2.2), (2.0, 0.0))
OFF = ResidentialFields(left_side_board_enabled=False,
                        right_side_board_enabled=False,
                        tread_front_overhang_mm=5.0)


def prepare(fields=None, points=L, direction="FORWARD", pattern="EQUAL_3",
            specs=None):
    ids = ("p0", "t1", "p2") if len(points) == 3 else ("p0", "t1", "t2", "p3")
    return prepare_turn_residential_geometry(
        points, direction, 0, 2800, 16, 900, 30, 12,
        fields=OFF if fields is None else fields, point_ids=ids,
        winder_pattern=pattern, turn_specs=specs)


def signature(parts):
    return tuple((part.part_type, part.ordinal, part.vertices, part.faces)
                 for part in parts if part.part_type != "SIDE_BOARD")


def boards(parts):
    return tuple(part for part in parts if part.part_type == "SIDE_BOARD")


def has_xy(parts, point):
    return any(math.dist(vertex[:2], point) < 1.0e-9
               for part in parts for vertex in part.vertices)


class FreshStage3CSideBoardTests(unittest.TestCase):
    def fields(self, underside="STEPPED_CLOSED", upper="STEPPED",
               left=True, right=True):
        return replace(OFF, underside_mode=underside, side_board_mode=upper,
                       left_side_board_enabled=left,
                       right_side_board_enabled=right)

    def test_four_independent_lower_upper_combinations(self):
        off_signature = {}
        for underside in ("STEPPED_CLOSED", "SLOPED_CLOSED"):
            off_signature[underside] = signature(prepare(
                self.fields(underside, left=False, right=False))[1])
            for upper in ("STEPPED", "SLOPED"):
                with self.subTest(underside=underside, upper=upper):
                    layout, parts, mesh = prepare(self.fields(underside, upper))
                    self.assertEqual(layout.winder_counts, (3,))
                    self.assertTrue(boards(parts))
                    self.assertEqual(signature(parts), off_signature[underside])
                    self.assertEqual(len(mesh.faces), len(mesh.face_roles))
                    self.assertTrue(validate_mesh_fragments(parts))

    def test_left_only_and_right_only_have_distinct_plan_ownership(self):
        left = prepare(self.fields(left=True, right=False))[1]
        right = prepare(self.fields(left=False, right=True))[1]
        self.assertTrue(boards(left))
        self.assertTrue(boards(right))
        self.assertNotEqual(boards(left), boards(right))
        self.assertEqual(signature(left), signature(right))

    def test_boards_off_exact_stage3b_signature_and_on_frozen(self):
        for underside in ("STEPPED_CLOSED", "SLOPED_CLOSED"):
            with self.subTest(underside=underside):
                off = prepare(self.fields(underside, left=False, right=False))
                on = prepare(self.fields(underside))
                self.assertFalse(boards(off[1]))
                self.assertEqual(off[1], on[1][:len(off[1])])
                self.assertEqual(signature(off[1]), signature(on[1]))

    def test_outer_corner_survives_equal2_and_equal4(self):
        for pattern in ("EQUAL_2", "EQUAL_4"):
            for direction in ("FORWARD", "REVERSE"):
                with self.subTest(pattern=pattern, direction=direction):
                    outer_is_right = direction == "FORWARD"
                    layout, parts, _mesh = prepare(
                        self.fields(left=not outer_is_right,
                                    right=outer_is_right),
                        direction=direction, pattern=pattern)
                    self.assertTrue(has_xy(boards(parts),
                                           layout.turn.outer_corner))

    def test_bf_patterns_and_arbitrary_angle(self):
        for pattern in ("BF_1", "BF_2"):
            with self.subTest(pattern=pattern):
                _layout, parts, _mesh = prepare(self.fields(), pattern=pattern)
                self.assertTrue(validate_mesh_fragments(boards(parts)))
        angle = math.radians(63.0)
        angled = ((0.0, 0.0), (0.0, 2.2),
                  (-2.2 * math.sin(angle), 2.2 + 2.2 * math.cos(angle)))
        layout, parts, _mesh = prepare(self.fields(), points=angled)
        self.assertTrue(has_xy(boards(parts), layout.turn.outer_corner))

    def test_sloped_corner_uses_walking_station_fraction(self):
        layout, parts, _mesh = prepare(
            self.fields(upper="SLOPED", left=False, right=True))
        frame = layout.turn
        cell_index = next(index for index, cell in enumerate(layout.cells)
                          if frame.outer_corner in cell.polygon)
        cell = layout.cells[cell_index]
        bounds = physical_cell_boundaries(
            cell, layout.ascent_direction, frame.inner_pivot)
        distance = lambda point: _board_outer_distance(
            frame, point, layout.ascent_direction)
        fraction = ((distance(frame.outer_corner) - distance(bounds.front[1]))
                    / (distance(bounds.rear[1]) - distance(bounds.front[1])))
        event_index = layout.straight_allocation[0] + cell_index + 1
        expected = (layout.base_z + (event_index - 1 + fraction)
                    * layout.actual_riser + 0.04)
        corner_tops = [vertex[2] for board in boards(parts)
                       for vertex in board.vertices
                       if math.dist(vertex[:2], frame.outer_corner) < 1.0e-9]
        self.assertTrue(any(abs(z - expected) < 1.0e-9 for z in corner_tops))

    def test_outer_lower_vertices_use_accepted_body_ring(self):
        for mode in ("STEPPED_CLOSED", "SLOPED_CLOSED"):
            with self.subTest(mode=mode):
                layout, parts, _mesh = prepare(
                    self.fields(underside=mode, left=False, right=True))
                bodies = [part for part in parts if part.part_type == "UNDERBODY"]
                board_vertices = {vertex for board in boards(parts)
                                  for vertex in board.vertices}
                for index, cell in enumerate(layout.cells):
                    rear = winder_tread_rear_outer_authority(
                        layout, 0, layout.cells, index)
                    footprint = winder_underbody_support_footprint(
                        layout, 0, cell, rear)
                    event_index = layout.straight_allocation[0] + index + 1
                    lower = layout.base_z + (event_index - 1) * layout.actual_riser
                    exterior = [point for point in footprint if
                                _canonical_outer_station(layout.turn, point) is not None
                                and any(math.dist(point, vertex[:2]) < 1.0e-9
                                        for body in bodies
                                        for vertex in body.vertices
                                        if abs(vertex[2] - lower) < 1.0e-9)]
                    self.assertGreaterEqual(len(exterior), 2)
                    self.assertTrue(all((point[0], point[1], lower)
                                        in board_vertices for point in exterior))

    def test_mirrored_turn_outer_side_is_left(self):
        mirrored = ((0.0, 0.0), (0.0, 2.2), (2.2, 2.2))
        layout, parts, _mesh = prepare(
            self.fields(left=True, right=False), points=mirrored)
        self.assertLess(layout.turn.theta, 0.0)
        self.assertTrue(has_xy(boards(parts), layout.turn.outer_corner))

    def test_ordinary_two_turn_u(self):
        specs = (TurnSpec("t1", "WINDER", "EQUAL_2"),
                 TurnSpec("t2", "WINDER", "EQUAL_4"))
        layout, parts, _mesh = prepare(self.fields(), points=ORDINARY_U,
                                       specs=specs)
        self.assertNotEqual(layout.u_classification, "COMPACT_U")
        self.assertEqual(layout.winder_counts, (2, 4))
        self.assertTrue(boards(parts))
        self.assertTrue(validate_mesh_fragments(parts))

    def test_reverse_reassigns_outer_side(self):
        forward, _parts, _mesh = prepare(self.fields(), direction="FORWARD")
        reverse, _parts, _mesh = prepare(self.fields(), direction="REVERSE")
        self.assertTrue(has_xy(
            boards(prepare(self.fields(left=False, right=True),
                           direction="FORWARD")[1]),
            forward.turn.outer_corner))
        self.assertTrue(has_xy(
            boards(prepare(self.fields(left=True, right=False),
                           direction="REVERSE")[1]),
            reverse.turn.outer_corner))
        self.assertFalse(has_xy(
            boards(prepare(self.fields(left=True, right=False),
                           direction="FORWARD")[1]),
            forward.turn.outer_corner))

    def test_repeated_preparation_is_deterministic(self):
        first = prepare(self.fields())
        second = prepare(self.fields())
        self.assertEqual(first, second)

    def test_compact_u_is_deferred_atomically_when_boards_enabled(self):
        specs = (TurnSpec("t1", "WINDER", "EQUAL_3"),
                 TurnSpec("t2", "WINDER", "EQUAL_3"))
        with self.assertRaisesRegex(ScopeUnsupportedError,
                                    "Stage 3D deferred"):
            prepare(self.fields(), points=COMPACT_U, specs=specs)
        layout, parts, _mesh = prepare(points=COMPACT_U, specs=specs)
        self.assertEqual(layout.u_classification, "COMPACT_U")
        self.assertFalse(boards(parts))

    def test_board_fragments_are_finite_closed_and_positive(self):
        for direction in ("FORWARD", "REVERSE"):
            with self.subTest(direction=direction):
                _layout, parts, _mesh = prepare(
                    self.fields("SLOPED_CLOSED", "SLOPED"), direction=direction)
                self.assertTrue(validate_mesh_fragments(boards(parts)))
                self.assertTrue(all(math.isfinite(v)
                                    for board in boards(parts)
                                    for vertex in board.vertices for v in vertex))

    def test_schema4_landing_regression_identity(self):
        _layout, parts, mesh = prepare_multiflight_residential_geometry(
            ((0.0, 0.0), (3.0, 0.0), (3.0, 3.0)), "FORWARD",
            100, 2800, 16, 900, 30, 12,
            point_ids=("l0", "l1", "l2"), fields=ResidentialFields())
        digest = hashlib.sha256(repr(tuple(
            (part.part_type, part.ordinal, part.vertices, part.faces)
            for part in parts)).encode()).hexdigest()
        self.assertEqual((len(parts), len(mesh.vertices), len(mesh.faces)),
                         (39, 632, 726))
        self.assertEqual(digest,
                         "05f012f304fea49fc1ed218789077cde0027a2fe47645e8fbc5f5f94bc72665f")


if __name__ == "__main__":
    unittest.main()
