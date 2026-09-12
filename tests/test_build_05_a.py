"""Pure geometry coverage for Build 05-A."""

import importlib.util
import math
import pathlib
import unittest


ROOT = pathlib.Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build05_alignment", ROOT / "japanese_house_modeler" / "drawing_alignment.py"
)
alignment = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(alignment)


class SegmentProjectionTests(unittest.TestCase):
    def assertPoint(self, actual, expected):
        self.assertIsNotNone(actual)
        self.assertAlmostEqual(actual.point[0], expected[0], places=10)
        self.assertAlmostEqual(actual.point[1], expected[1], places=10)

    def test_horizontal_and_vertical(self):
        self.assertPoint(alignment.project_to_wall_segment((4, 2), (0, 0), (10, 0)), (4, 0))
        self.assertPoint(alignment.project_to_wall_segment((2, 4), (0, 0), (0, 10)), (0, 4))

    def test_15_and_45_degrees(self):
        for degrees in (15, 45):
            radians = math.radians(degrees)
            end = (10 * math.cos(radians), 10 * math.sin(radians))
            expected = (4 * math.cos(radians), 4 * math.sin(radians))
            normal = (-math.sin(radians), math.cos(radians))
            raw = (expected[0] + normal[0], expected[1] + normal[1])
            with self.subTest(degrees=degrees):
                self.assertPoint(alignment.project_to_wall_segment(raw, (0, 0), end), expected)

    def test_reversed_segment_projects_to_same_world_point(self):
        forward = alignment.project_to_wall_segment((4, 2), (0, 0), (10, 0))
        reverse = alignment.project_to_wall_segment((4, 2), (10, 0), (0, 0))
        self.assertEqual(forward.point, reverse.point)

    def test_boundaries_and_exterior_are_excluded(self):
        for point in ((0, 0), (10, 0), (-1, 0), (11, 0)):
            with self.subTest(point=point):
                self.assertIsNone(alignment.project_to_wall_segment(point, (0, 0), (10, 0)))

    def test_invalid_inputs(self):
        cases = (((0, 0), (0, 0), (0, 0)),
                 ((math.nan, 0), (0, 0), (1, 0)),
                 ((0, math.inf), (0, 0), (1, 0)),
                 (None, (0, 0), (1, 0)))
        for raw, start, end in cases:
            with self.subTest(raw=raw):
                self.assertIsNone(alignment.project_to_wall_segment(raw, start, end))


class CandidateTests(unittest.TestCase):
    def test_unique_closest_candidate(self):
        self.assertEqual(alignment.select_unambiguous_candidate([(2, "a"), (1, "b")]), "b")

    def test_equal_candidates_are_ambiguous_in_any_order(self):
        candidates = [(1, "a"), (1, "b")]
        self.assertIsNone(alignment.select_unambiguous_candidate(candidates))
        self.assertIsNone(alignment.select_unambiguous_candidate(reversed(candidates)))

    def test_equal_distance_different_projections_are_ambiguous(self):
        self.assertIsNone(alignment.select_unambiguous_candidate([(3, (1, 0)), (3, (0, 1))]))


class CanonicalSplitTests(unittest.TestCase):
    def test_horizontal_split_preserves_direction(self):
        segments = alignment.canonical_split_segments((0, 0, 0), (10, 0, 0), (4, 2, 0))
        self.assertEqual(segments, (((0, 0, 0), (4.0, 0.0, 0.0)),
                                    ((4.0, 0.0, 0.0), (10, 0, 0))))

    def test_angled_split_coordinates(self):
        for degrees in (15, 45):
            radians = math.radians(degrees)
            end = (10 * math.cos(radians), 10 * math.sin(radians), 0)
            point = (4 * math.cos(radians), 4 * math.sin(radians), 0)
            segments = alignment.canonical_split_segments((0, 0, 0), end, point)
            with self.subTest(degrees=degrees):
                self.assertPointAlmostEqual(segments[0][1], point)
                self.assertPointAlmostEqual(segments[1][0], point)

    def assertPointAlmostEqual(self, actual, expected):
        for first, second in zip(actual, expected):
            self.assertAlmostEqual(first, second, places=10)

    def test_same_host_midpoint_and_endpoint_combinations_are_rejected(self):
        host = object()
        other = object()
        self.assertTrue(alignment.same_host_connection_forbidden(host, host))
        self.assertTrue(alignment.same_host_connection_forbidden(None, host, host, None))
        self.assertTrue(alignment.same_host_connection_forbidden(host, None, None, host))
        self.assertFalse(alignment.same_host_connection_forbidden(host, other))

    def test_same_host_endpoint_to_endpoint_is_not_rejected(self):
        host = object()
        self.assertFalse(
            alignment.same_host_connection_forbidden(None, None, host, host)
        )


class WallAngleTests(unittest.TestCase):
    def test_expected_angles_and_reverse_direction(self):
        for degrees in (0, 15, 45, 90, 135):
            radians = math.radians(degrees)
            end = (math.cos(radians), math.sin(radians))
            with self.subTest(degrees=degrees):
                self.assertAlmostEqual(alignment.wall_axis_angle_degrees((0, 0), end), degrees)
                self.assertAlmostEqual(alignment.wall_axis_angle_degrees(end, (0, 0)), degrees)

    def test_negative_direction_normalizes(self):
        self.assertAlmostEqual(alignment.wall_axis_angle_degrees((0, 0), (-1, -1)), 45)

    def test_invalid_angle(self):
        for end in ((0, 0), (math.nan, 1), (math.inf, 0)):
            self.assertIsNone(alignment.wall_axis_angle_degrees((0, 0), end))


if __name__ == "__main__":
    unittest.main()
