"""Build 07-E Stage-1 pure geometry and compatibility contracts."""

import math
import pathlib
import sys
import types
import unittest

ROOT = pathlib.Path(__file__).parents[1]
package = types.ModuleType("japanese_house_modeler")
package.__path__ = [str(ROOT / "japanese_house_modeler")]
sys.modules.setdefault("japanese_house_modeler", package)

from japanese_house_modeler.stair_geometry import prepare_stair_geometry
from japanese_house_modeler.stair_multiflight import prepare_multiflight_geometry
from japanese_house_modeler.stair_winder import (
    EPS_LENGTH, WINDER_EQUAL_2, WINDER_EQUAL_3, WINDER_EQUAL_4,
    allocate_straight_events, equal_pattern_fractions, polygon_area,
    prepare_winder_geometry, resolve_nominal_cells, resolve_turn_frame,
    resolve_winder_layout, signed_turn_angle,
)


POINTS = ((0.0, 0.0), (3.0, 0.0), (3.0, 3.0))
IDS = ("start", "turn-authority", "end")
ARGS = (POINTS, "FORWARD", 0, 2800, 16, 900, 30, 12)


class TurnFrameTests(unittest.TestCase):
    def test_signed_turn_angle_left_and_right(self):
        self.assertAlmostEqual(signed_turn_angle(*POINTS), math.pi / 2)
        right = ((0, 0), (3, 0), (3, -3))
        self.assertAlmostEqual(signed_turn_angle(*right), -math.pi / 2)

    def test_generalized_frame_and_exact_90_reduction(self):
        frame = resolve_turn_frame(*POINTS, .9, "turn-authority")
        self.assertEqual(frame.point_id, IDS[1])
        self.assertAlmostEqual(polygon_area(frame.envelope), .9 ** 2)
        self.assertAlmostEqual(frame.cutback, .45)
        self.assertEqual(len(frame.envelope), 4)

    def test_arbitrary_angle_frame_foundation_not_15_degree_gated(self):
        angle = math.radians(63)
        frame = resolve_turn_frame((0, 0), (3, 0),
                                   (3 + 3 * math.cos(angle), 3 * math.sin(angle)), .9)
        self.assertAlmostEqual(frame.theta, angle)

    def test_numerical_singularities_and_short_cutback(self):
        invalid = (((0, 0), (0, 0), (1, 0)),
                   ((0, 0), (1, 0), (2, 0)),
                   ((0, 0), (1, 0), (0, 1e-9)),
                   ((0, 0), (.1, 0), (.1, 1)))
        for points in invalid:
            with self.subTest(points=points), self.assertRaises(ValueError):
                resolve_turn_frame(*points, .9)


class NominalCellTests(unittest.TestCase):
    def test_equal_fractions(self):
        self.assertEqual(equal_pattern_fractions(WINDER_EQUAL_2), (.5,))
        self.assertEqual(equal_pattern_fractions(WINDER_EQUAL_3), (1/3, 2/3))
        self.assertEqual(equal_pattern_fractions(WINDER_EQUAL_4), (.25, .5, .75))

    def test_equal3_preserves_outer_corner_and_complete_area(self):
        frame = resolve_turn_frame(*POINTS, .9)
        cells = resolve_nominal_cells(frame, WINDER_EQUAL_3)
        self.assertIn(frame.outer_corner, cells[1].polygon)
        self.assertAlmostEqual(sum(polygon_area(cell.polygon) for cell in cells),
                               polygon_area(frame.envelope))
        self.assertTrue(all(polygon_area(cell.polygon) > 0 for cell in cells))

    def test_left_right_mirror_and_determinism(self):
        left = resolve_nominal_cells(resolve_turn_frame(*POINTS, .9), WINDER_EQUAL_4)
        right_points = tuple((x, -y) for x, y in POINTS)
        right = resolve_nominal_cells(resolve_turn_frame(*right_points, .9),
                                      WINDER_EQUAL_4)
        reflected = tuple(tuple((x, -y) for x, y in cell.polygon) for cell in left)
        self.assertEqual(reflected, tuple(cell.polygon for cell in right))
        self.assertEqual(left, resolve_nominal_cells(
            resolve_turn_frame(*POINTS, .9), WINDER_EQUAL_4))


class RiseAndAllocationTests(unittest.TestCase):
    def test_rise_event_invariant_and_ownership(self):
        layout = resolve_winder_layout(*ARGS, point_ids=IDS,
                                       winder_pattern=WINDER_EQUAL_3)
        self.assertEqual(sum(layout.straight_allocation) + len(layout.cells) + 1, 16)
        self.assertEqual(len(layout.rise_events), 16)
        self.assertEqual([event.owner for event in layout.rise_events].count(
            "WINDER_TREAD"), 3)
        self.assertEqual(layout.rise_events[-1].owner, "UPPER_ARRIVAL")

    def test_auto_is_deterministic_and_ties_use_canonical_order(self):
        self.assertEqual(allocate_straight_events((2, 1), 10, 0, 3), (4, 2))
        self.assertEqual(allocate_straight_events((1, 1), 8, 0, 3), (2, 2))
        self.assertEqual(allocate_straight_events((1, 1), 9, 0, 3), (3, 2))

    def test_positive_region_never_silently_gets_zero(self):
        with self.assertRaises(ValueError):
            allocate_straight_events((1, 1), 4, 0, 2)


class ProductionAndCompatibilityTests(unittest.TestCase):
    def test_build_identity(self):
        source = (ROOT / "japanese_house_modeler/__init__.py").read_text()
        self.assertIn('"version": (0, 7, 4)', source)
        self.assertIn("Build 07-E: Winder + Arbitrary-angle Turn/Landing", source)

    def test_width_900_750_650_and_all_equal_patterns(self):
        for width in (900, 750, 650):
            for pattern in (WINDER_EQUAL_2, WINDER_EQUAL_3, WINDER_EQUAL_4):
                with self.subTest(width=width, pattern=pattern):
                    layout, fragments, mesh = prepare_winder_geometry(
                        POINTS, "FORWARD", 0, 2800, 16, width, 30, 20,
                        point_ids=IDS, winder_pattern=pattern)
                    self.assertEqual(len(layout.cells), int(pattern[-1]))
                    self.assertGreater(len(fragments), 0)
                    self.assertEqual(len(mesh.faces), len(mesh.face_roles))

    def test_no_legal_width_threshold_exists(self):
        source = (ROOT / "japanese_house_modeler/stair_winder.py").read_text()
        self.assertNotIn("MIN_LEGAL_STAIR_WIDTH", source)
        layout = resolve_winder_layout(
            POINTS, "FORWARD", 0, 2800, 16, 100, 30, 12,
            point_ids=IDS, winder_pattern=WINDER_EQUAL_3)
        self.assertAlmostEqual(layout.width, .1)

    def test_invalid_candidate_is_pure_and_repeatable(self):
        snapshot = tuple(POINTS)
        for _unused in range(2):
            with self.assertRaises(ValueError):
                prepare_winder_geometry(
                    ((0, 0), (.1, 0), (.1, 1)), "FORWARD", 0, 2800,
                    16, 900, 30, 12, point_ids=IDS)
        self.assertEqual(POINTS, snapshot)

    def test_schema_1_2_3_and_schema_4_geometry_regression(self):
        straight = prepare_stair_geometry(
            ((0, 0), (3.6, 0)), "FORWARD", 0, 2800, 16, 900, 30, 12)[2]
        landing = prepare_multiflight_geometry(*ARGS, point_ids=IDS)[2]
        self.assertEqual((len(straight.vertices), len(straight.faces)), (248, 186))
        self.assertGreater(len(landing.vertices), 0)

    def test_repeated_regeneration_is_deterministic(self):
        first = prepare_winder_geometry(*ARGS, point_ids=IDS,
                                         winder_pattern=WINDER_EQUAL_3)[2]
        second = prepare_winder_geometry(*ARGS, point_ids=IDS,
                                          winder_pattern=WINDER_EQUAL_3)[2]
        self.assertEqual(first, second)

    def test_reverse_keeps_canonical_subdivision_and_reverses_traversal(self):
        forward = resolve_winder_layout(*ARGS, point_ids=IDS,
                                        winder_pattern=WINDER_EQUAL_3)
        reverse = resolve_winder_layout(
            POINTS, "REVERSE", *ARGS[2:], point_ids=IDS,
            winder_pattern=WINDER_EQUAL_3)
        self.assertEqual(forward.cells, reverse.cells)
        self.assertEqual(reverse.traversal_point_ids, tuple(reversed(IDS)))
        reverse_mesh = prepare_winder_geometry(
            POINTS, "REVERSE", *ARGS[2:], point_ids=IDS,
            winder_pattern=WINDER_EQUAL_3)[2]
        self.assertGreater(len(reverse_mesh.vertices), 0)

    def test_named_epsilon_is_numerical_not_width_minimum(self):
        self.assertLess(EPS_LENGTH, .001)


if __name__ == "__main__":
    unittest.main()
