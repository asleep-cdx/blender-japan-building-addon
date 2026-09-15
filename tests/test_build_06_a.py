"""Pure Build 06-A identity, surface, path, and dependency contracts."""

import math
import pathlib
import sys
import types
import unittest

ROOT = pathlib.Path(__file__).parents[1]
package = types.ModuleType("japanese_house_modeler")
package.__path__ = [str(ROOT / "japanese_house_modeler")]
sys.modules.setdefault("japanese_house_modeler", package)

from japanese_house_modeler.finish_dependencies import (
    SpanRecord, WallSplitResult, partition_records_for_delete,
    partition_run_on_delete, remap_run_for_split, remap_span_for_split,
    remap_semantic_interval, transactional_mutation,
)
from japanese_house_modeler.finish_identity import (
    duplicate_ids, duplicate_repair_is_safe, ensure_persistent_id,
    reference_is_trusted, repair_candidate,
)
from japanese_house_modeler.finish_path import (
    backspace_pending, boundary_reaches_endpoint, profile_horizontal_sign,
    propagate_canonical_side, resolve_boundary, resolve_interval,
    transition_boundaries_reach, traversal_endpoints, traversal_for_connection,
    verification_profile_points,
)
from japanese_house_modeler.finish_surface import (
    endpoint_blocked_by_footprints, face_segment, line_intersection, resolve_join,
    resolve_surface_path, side_normal, transition_blocked_by_footprints,
    wall_axis,
)
from japanese_house_modeler.finish_state import (
    finish_problem_keys, status_label, unique_rebind_candidate,
)


class Owner:
    def __init__(self, wall_id=""):
        self.wall_id = wall_id


class Build06AIdentityTests(unittest.TestCase):
    def test_new_and_preserved_id(self):
        owner = Owner()
        value = ensure_persistent_id(owner)
        self.assertEqual(value, owner.wall_id)
        self.assertEqual(value, ensure_persistent_id(owner))
        self.assertEqual(len(value), 36)

    def test_duplicate_detection_ignores_empty(self):
        first, second = Owner("x"), Owner("x")
        self.assertEqual(duplicate_ids([first, second, Owner()]), {"x": (first, second)})

    def test_pointer_and_id(self):
        first, second = Owner("x"), Owner("y")
        self.assertTrue(reference_is_trusted(first, "x", [first, second]))
        self.assertFalse(reference_is_trusted(first, "y", [first, second]))
        self.assertFalse(reference_is_trusted(first, "x", [first, Owner("x")]))

    def test_explicit_repair_candidate(self):
        owner = Owner("x")
        self.assertIs(repair_candidate("x", [owner]), owner)
        self.assertIsNone(repair_candidate("x", [owner, Owner("x")]))
        self.assertIsNone(repair_candidate("", [Owner("")]))

    def test_duplicate_repair_ownership(self):
        original, duplicate = object(), object()
        self.assertTrue(duplicate_repair_is_safe(
            duplicate, [(original, "x", True)]))
        self.assertFalse(duplicate_repair_is_safe(
            duplicate, [(duplicate, "x", True)]))
        self.assertFalse(duplicate_repair_is_safe(
            duplicate, [(None, "x", False)]))

    def test_exclusion_reference_uses_same_duplicate_repair_contract(self):
        original, duplicate = object(), object()
        exclusion_to_original = [(original, "x", True)]
        exclusion_to_duplicate = [(duplicate, "x", True)]
        self.assertTrue(duplicate_repair_is_safe(duplicate, exclusion_to_original))
        self.assertFalse(duplicate_repair_is_safe(duplicate, exclusion_to_duplicate))


class Build06APathTests(unittest.TestCase):
    def test_canonical_endpoint_reach_including_numeric_boundary(self):
        self.assertTrue(boundary_reaches_endpoint(0, 2000, "START"))
        self.assertTrue(boundary_reaches_endpoint(2000, 2000, "END"))
        self.assertFalse(boundary_reaches_endpoint(1500, 2000, "END"))
        self.assertTrue(boundary_reaches_endpoint(
            resolve_boundary("DISTANCE_FROM_START", 2000, 2000), 2000, "END"))
        self.assertTrue(boundary_reaches_endpoint(
            resolve_boundary("DISTANCE_FROM_END", 2000, 2000), 2000, "START"))

    def test_traversal_endpoint_and_profile_orientation_matrix(self):
        self.assertEqual(traversal_endpoints("FORWARD"), ("START", "END"))
        self.assertEqual(traversal_endpoints("REVERSE"), ("END", "START"))
        self.assertEqual(profile_horizontal_sign("LEFT", "FORWARD"), -1.0)
        self.assertEqual(profile_horizontal_sign("RIGHT", "REVERSE"), -1.0)
        self.assertEqual(profile_horizontal_sign("RIGHT", "FORWARD"), 1.0)
        self.assertEqual(profile_horizontal_sign("LEFT", "REVERSE"), 1.0)

    def test_mirrored_profiles_preserve_polygon_winding(self):
        def signed_area(points):
            return sum(first[0] * second[1] - second[0] * first[1]
                       for first, second in zip(points, points[1:] + points[:1])) / 2.0

        positive = verification_profile_points(1.0)
        negative = verification_profile_points(-1.0)
        original_working_negative = (
            (0.0, 0.0), (-.01, 0.0), (-.01, .06), (0.0, .06))
        self.assertEqual(negative, original_working_negative)
        self.assertEqual(math.copysign(1.0, signed_area(positive)),
                         math.copysign(1.0, signed_area(original_working_negative)))
        self.assertEqual({point[0] for point in positive}, {0.0, .01})
        self.assertEqual({point[0] for point in negative}, {0.0, -.01})
        self.assertEqual({point[1] for point in positive}, {0.0, .06})
        self.assertEqual({point[1] for point in negative}, {0.0, .06})

    def test_transition_rejects_partial_departure_before_miter(self):
        self.assertFalse(transition_boundaries_reach(
            (0, 1500), 2000, "FORWARD", (0, 1000), 1000, "FORWARD"))
        self.assertTrue(transition_boundaries_reach(
            (0, 2000), 2000, "FORWARD", (0, 1000), 1000, "FORWARD"))

    def test_reverse_transition_uses_high_to_low_boundaries(self):
        self.assertTrue(transition_boundaries_reach(
            (2000, 0), 2000, "REVERSE", (1000, 0), 1000, "REVERSE"))
        self.assertFalse(transition_boundaries_reach(
            (2000, 500), 2000, "REVERSE", (1000, 0), 1000, "REVERSE"))

    def test_boundaries_and_partial_interval(self):
        self.assertEqual(resolve_boundary("DISTANCE_FROM_END", 400, 2000), 1600)
        self.assertEqual(resolve_interval("DISTANCE_FROM_START", 500,
                                          "DISTANCE_FROM_END", 400, 2000),
                         (500, 1600))

    def test_reverse_interval(self):
        self.assertEqual(resolve_interval("WALL_START", 0, "WALL_END", 0,
                                          2000, "REVERSE"), (2000, 0))

    def test_invalid_interval(self):
        with self.assertRaises(ValueError):
            resolve_interval("WALL_START", 0, "WALL_START", 0, 2000)

    def test_physically_reversed_canonical_interval_is_rejected(self):
        with self.assertRaises(ValueError):
            resolve_interval("DISTANCE_FROM_START", 1500,
                             "DISTANCE_FROM_START", 500, 2000, "REVERSE")

    def test_non_finite_boundary_is_rejected(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.assertRaises(ValueError):
                resolve_boundary("WALL_START", value, 2000)

    def test_endpoint_orientation_mapping(self):
        self.assertEqual(traversal_for_connection("END", "START"),
                         ("FORWARD", "FORWARD"))
        self.assertEqual(traversal_for_connection("END", "END"),
                         ("FORWARD", "REVERSE"))
        self.assertEqual(traversal_for_connection("START", "START"),
                         ("REVERSE", "FORWARD"))
        self.assertEqual(traversal_for_connection("START", "END"),
                         ("REVERSE", "REVERSE"))

    def test_backspace_prunes_candidate_wall_identity(self):
        spans, ids = backspace_pending(
            [("A", "LEFT", "FORWARD"), ("B", "LEFT", "FORWARD")],
            {"A": "a", "B": "b"})
        self.assertEqual(spans, [("A", "LEFT", "FORWARD")])
        self.assertEqual(ids, {"A": "a"})


class Build06ASurfaceTests(unittest.TestCase):
    def test_wall_axis_canonical_length_ignores_z_difference(self):
        axis, length = wall_axis((0, 0, -4), (3, 4, 12))
        self.assertEqual(axis, (.6, .8))
        self.assertEqual(length, 5.0)

    def test_single_span_endpoint_blocker_uses_outward_projection(self):
        upward = [((1, 0), (1, 2), .2)]
        downward = [((1, 0), (1, -2), .2)]
        self.assertTrue(endpoint_blocked_by_footprints(
            (1, .1), (0, 1), upward))
        self.assertFalse(endpoint_blocked_by_footprints(
            (1, -.1), (0, -1), upward))
        self.assertTrue(endpoint_blocked_by_footprints(
            (1, -.1), (0, -1), downward))
        self.assertFalse(endpoint_blocked_by_footprints((1, .1), (0, 1), ()))

    def test_endpoint_blocker_rejects_invalid_thickness(self):
        for thickness in (math.nan, math.inf, -math.inf, 0.0, -0.1):
            with self.subTest(thickness=thickness), self.assertRaises(ValueError):
                endpoint_blocked_by_footprints(
                    (1, .1), (0, 1), [((1, 0), (1, 2), thickness)])

    def test_left_right_normals(self):
        self.assertEqual(side_normal((0, 0), (2, 0), "LEFT"), (0.0, 1.0))
        self.assertEqual(side_normal((0, 0), (2, 0), "RIGHT"), (0.0, -1.0))
        self.assertEqual(side_normal((0, 0), (0, 2), "LEFT"), (-1.0, 0.0))

    def test_reversed_wall_labels_follow_canonical_direction(self):
        self.assertEqual(side_normal((2, 0), (0, 0), "LEFT"), (0.0, -1.0))

    def test_face_offset_and_partial(self):
        segment = face_segment((0, 0), (2, 0), .2, "LEFT",
                               ("DISTANCE_FROM_START", 500,
                                "DISTANCE_FROM_END", 500))
        self.assertEqual(segment, ((.5, .1), (1.5, .1)))

    def test_diagonal_normal_is_unit(self):
        normal = side_normal((0, 0), (1, 1), "RIGHT")
        self.assertAlmostEqual(math.hypot(*normal), 1.0)

    def test_right_angle_and_oblique_intersection(self):
        self.assertEqual(line_intersection(((0, 1), (1, 1)), ((1, 0), (1, 2))), (1, 1))
        point = line_intersection(((0, 0), (2, 0)), ((1, -1), (2, 1)))
        self.assertAlmostEqual(point[0], 1.5)

    def test_unequal_thickness_corner(self):
        first = face_segment((0, 0), (1, 0), .2, "LEFT")
        second = face_segment((1, 0), (1, 1), .4, "LEFT")
        self.assertEqual(resolve_join(first, second), (.8, .1))

    def test_collinear_continuation(self):
        self.assertEqual(resolve_surface_path((((0, 1), (1, 1)),
                                               ((1, 1), (2, 1)))),
                         ((0, 1), (1, 1), (2, 1)))

    def test_parallel_gap_and_distant_miter_rejected(self):
        self.assertIsNone(resolve_join(((0, 0), (1, 0)), ((1, 1), (2, 1))))
        self.assertIsNone(resolve_join(((0, 0), (1, 0)), ((100, 1), (100, 2))))

    def test_invalid_default_interval_traversal(self):
        with self.assertRaises(ValueError):
            face_segment((0, 0), (1, 0), .2, "LEFT", traversal="SIDEWAYS")

    def test_physical_side_propagates_across_reversed_canonical_wall(self):
        self.assertEqual(propagate_canonical_side("LEFT", "FORWARD", "FORWARD"),
                         "LEFT")
        self.assertEqual(propagate_canonical_side("LEFT", "FORWARD", "REVERSE"),
                         "RIGHT")
        self.assertEqual(propagate_canonical_side("RIGHT", "REVERSE", "FORWARD"),
                         "LEFT")

    def test_t_branch_blocks_only_occupied_finish_side(self):
        left = (((0, .1), (1, .1)), ((1, .1), (2, .1)))
        right = (((0, -.1), (1, -.1)), ((1, -.1), (2, -.1)))
        upward = [((1, 0), (1, 2), .2)]
        self.assertTrue(transition_blocked_by_footprints(*left, upward))
        self.assertFalse(transition_blocked_by_footprints(*right, upward))

    def test_cross_blocks_corresponding_sides(self):
        left = ((0, .1), (1, .1)), ((1, .1), (2, .1))
        right = ((0, -.1), (1, -.1)), ((1, -.1), (2, -.1))
        cross = [((1, 0), (1, 2), .2), ((1, 0), (1, -2), .2)]
        self.assertTrue(transition_blocked_by_footprints(*left, cross))
        self.assertTrue(transition_blocked_by_footprints(*right, cross))

    def test_unconnected_geometric_crossing_is_not_a_topology_blocker(self):
        transition = ((0, .1), (1, .1)), ((1, .1), (2, .1))
        self.assertFalse(transition_blocked_by_footprints(*transition, ()))

    def test_oblique_unequal_thickness_blocker(self):
        transition = ((0, .1), (1, .1)), ((1, .1), (2, .1))
        self.assertTrue(transition_blocked_by_footprints(
            *transition, [((1, 0), (2, 1), .3)]))

    def test_blocker_uses_full_canonical_length(self):
        transition = ((-1, .75), (0, .75)), ((0, .75), (1, .75))
        self.assertTrue(transition_blocked_by_footprints(
            *transition, [((0, 0), (0, 2), .2)]))

    def test_obstruction_respects_supplied_miter_limit(self):
        transition = ((0, 0), (1, 0)), ((2, 1), (2, 2))
        unrelated = [((10, 10), (10, 11), .2)]
        self.assertFalse(transition_blocked_by_footprints(
            *transition, unrelated, miter_limit=2.0))
        self.assertTrue(transition_blocked_by_footprints(
            *transition, unrelated, miter_limit=0.5))


class Build06ADependencyTests(unittest.TestCase):
    def test_whole_crossing_split(self):
        span = SpanRecord("a", 0, 2000)
        self.assertEqual(remap_span_for_split(span, "a", "b", 1000),
                         (SpanRecord("a", 0, 1000), SpanRecord("b", 0, 1000)))

    def test_before_and_after(self):
        before = SpanRecord("a", 100, 500)
        after = SpanRecord("a", 1200, 1800)
        self.assertEqual(remap_span_for_split(before, "a", "b", 1000), (before,))
        self.assertEqual(remap_span_for_split(after, "a", "b", 1000),
                         (SpanRecord("b", 200, 800),))

    def test_exact_boundary_has_no_zero_length_piece(self):
        left = SpanRecord("a", 0, 1000)
        right = SpanRecord("a", 1000, 2000)
        self.assertEqual(len(remap_span_for_split(left, "a", "b", 1000)), 1)
        self.assertEqual(remap_span_for_split(right, "a", "b", 1000),
                         (SpanRecord("b", 0, 1000),))

    def test_reverse_crossing_reverses_piece_order(self):
        span = SpanRecord("a", 200, 1800, "REVERSE")
        result = remap_span_for_split(span, "a", "b", 1000)
        self.assertEqual([item.wall_id for item in result], ["b", "a"])

    def test_multiple_runs_are_independent(self):
        runs = ((SpanRecord("a", 0, 1500),), (SpanRecord("a", 200, 300),))
        mapped = tuple(remap_run_for_split(run, "a", "b", 1000) for run in runs)
        self.assertEqual(tuple(map(len, mapped)), (2, 1))

    def test_delete_partitions_and_does_not_bridge(self):
        spans = tuple(SpanRecord(value, 0, 1) for value in "ABC")
        result = partition_run_on_delete(spans, "B")
        self.assertEqual([[span.wall_id for span in run] for run in result], [["A"], ["C"]])

    def test_invalid_remap_inputs_rejected(self):
        for span in (SpanRecord("a", 2, 1), SpanRecord("a", -1, 2),
                     SpanRecord("a", 0, math.inf),
                     SpanRecord("a", 0, 1, "SIDEWAYS")):
            with self.assertRaises(ValueError):
                remap_span_for_split(span, "a", "b", 0.5)

    def test_semantic_whole_wall_split_and_future_resize(self):
        pieces = remap_semantic_interval(
            "WALL_START", 0, "WALL_END", 0, 5000, 2000)
        self.assertEqual((pieces[0].entry_kind, pieces[0].exit_kind),
                         ("WALL_START", "WALL_END"))
        self.assertEqual((pieces[1].entry_kind, pieces[1].exit_kind),
                         ("WALL_START", "WALL_END"))
        self.assertEqual(resolve_boundary(pieces[1].exit_kind,
                                          pieces[1].exit_value_mm, 4000), 4000)

    def test_semantic_distance_from_end_survives_successor(self):
        pieces = remap_semantic_interval(
            "DISTANCE_FROM_START", 2500, "DISTANCE_FROM_END", 400,
            5000, 2000)
        self.assertEqual(len(pieces), 1)
        self.assertEqual(pieces[0].exit_kind, "DISTANCE_FROM_END")
        self.assertEqual(pieces[0].exit_value_mm, 400)
        self.assertEqual(resolve_boundary(pieces[0].exit_kind,
                                          pieces[0].exit_value_mm, 4000), 3600)

    def test_semantic_exclusion_cases_use_same_contract(self):
        before = remap_semantic_interval(
            "WALL_START", 0, "DISTANCE_FROM_START", 500, 3000, 1000)
        crossing = remap_semantic_interval(
            "DISTANCE_FROM_START", 500, "WALL_END", 0, 3000, 1000)
        exact = remap_semantic_interval(
            "DISTANCE_FROM_START", 1000, "WALL_END", 0, 3000, 1000)
        self.assertEqual([piece.wall_part for piece in before], ["ORIGINAL"])
        self.assertEqual([piece.wall_part for piece in crossing],
                         ["ORIGINAL", "SUCCESSOR"])
        self.assertEqual([piece.wall_part for piece in exact], ["SUCCESSOR"])

    def test_split_event_integration_contract(self):
        event = WallSplitResult("host", "a", "next", "b", 2000, 800)
        self.assertEqual(event.original_id, "a")
        self.assertEqual(event.split_distance_mm, 800)

    def test_delete_partition_contract_has_no_empty_runs(self):
        spans = (SpanRecord("B", 0, 1), SpanRecord("A", 0, 1),
                 SpanRecord("B", 0, 1))
        self.assertEqual(partition_records_for_delete(spans, "B"), ((spans[1],),))

    def test_transaction_restores_and_reraises(self):
        restored = []
        with self.assertRaisesRegex(RuntimeError, "failure"):
            transactional_mutation("before", lambda: (_ for _ in ()).throw(
                RuntimeError("failure")), restored.append)
        self.assertEqual(restored, ["before"])


class Build06AStateTests(unittest.TestCase):
    def test_finish_status_classification(self):
        problems = finish_problem_keys(True, [(False, False, False)], False, False)
        self.assertEqual(problems, ("WALL_MISSING", "INTERVAL", "DISCONTINUOUS"))
        self.assertIn("Wall欠落", status_label(problems))

    def test_unique_pointer_repair_and_duplicate_refusal(self):
        first, second = object(), object()
        self.assertIs(unique_rebind_candidate("x", [(first, "x"), (second, "y")]), first)
        self.assertIsNone(unique_rebind_candidate("x", [(first, "x"), (second, "x")]))
        self.assertIsNone(unique_rebind_candidate("", [(first, "")]))

    def test_empty_expected_id_and_zero_span_are_not_normal(self):
        empty_id = finish_problem_keys(True, [(True, True, False, True)], True, True, 1)
        zero = finish_problem_keys(True, [], True, True, 0)
        self.assertIn("WALL_ID", empty_id)
        self.assertEqual(zero, ("INTERVAL", "DISCONTINUOUS"))


if __name__ == "__main__":
    unittest.main()
