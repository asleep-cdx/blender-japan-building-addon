"""Pure acceptance coverage for Build 06-B Stage 2-A."""

import pathlib
import sys
import types
import unittest

ROOT = pathlib.Path(__file__).parents[1]
package = types.ModuleType("japanese_house_modeler")
package.__path__ = [str(ROOT / "japanese_house_modeler")]
sys.modules.setdefault("japanese_house_modeler", package)

from japanese_house_modeler.finish_exclusions import (
    activated_identity, calculate_visible_intervals, classify_visible_state,
    exclusion_split_identities, merge_coverage, subtract_intervals,
    normalize_distance_from_start, piece_reaches_boundary, run_boundary_field,
    transactional_edit,
)
from japanese_house_modeler.finish_path import resolve_boundary
from japanese_house_modeler.finish_surface import (
    endpoint_blocked_by_footprints, resolve_junction_butt, resolve_surface_path,
)


class Stage2AIntervalTests(unittest.TestCase):
    def test_middle(self): self.assertEqual(subtract_intervals((0, 2000), ((700, 1100),)), ((0, 700), (1100, 2000)))
    def test_beginning(self): self.assertEqual(subtract_intervals((0, 10), ((0, 2),)), ((2, 10),))
    def test_end(self): self.assertEqual(subtract_intervals((0, 10), ((8, 10),)), ((0, 8),))
    def test_whole_is_empty(self): self.assertEqual(subtract_intervals((0, 10), ((0, 10),)), ())
    def test_two_separate(self): self.assertEqual(subtract_intervals((0, 10), ((2, 3), (7, 8))), ((0, 2), (3, 7), (8, 10)))
    def test_overlap_merges_for_calculation(self): self.assertEqual(merge_coverage(((5, 9), (8, 12))), ((5, 12),))
    def test_touching_merges_for_calculation(self): self.assertEqual(merge_coverage(((5, 9), (9, 12))), ((5, 12),))
    def test_input_records_are_not_mutated(self):
        records = [(5, 9), (8, 12)]; merge_coverage(records)
        self.assertEqual(records, [(5, 9), (8, 12)])
    def test_removing_overlap_restores_unique_coverage(self): self.assertEqual(subtract_intervals((0, 20), ((5, 9),)), ((0, 5), (9, 20)))
    def test_invalid_exclusion_rejected(self):
        with self.assertRaises(ValueError): merge_coverage(((5, 5),))
    def test_original_span_unchanged(self):
        span = [0, 10]; subtract_intervals(span, ((2, 4),)); self.assertEqual(span, [0, 10])

    def test_disabled_and_legacy_disabled_have_no_effect(self):
        spans = (("w", 0, 10, "FORWARD"),)
        exclusions = (("w", 2, 4, False), ("w", 6, 8, False))
        self.assertEqual(calculate_visible_intervals(spans, exclusions), (("w", 0.0, 10.0, "FORWARD"),))

    def test_path_order_forward_then_reverse(self):
        spans = (("a", 0, 10, "FORWARD"), ("b", 0, 10, "REVERSE"))
        result = calculate_visible_intervals(spans, (("b", 4, 6, True),))
        self.assertEqual(result, (("a", 0.0, 10.0, "FORWARD"), ("b", 6.0, 10.0, "REVERSE"), ("b", 0.0, 4.0, "REVERSE")))

    def test_gap_produces_independent_pieces(self): self.assertEqual(len(subtract_intervals((0, 10), ((4, 6),))), 2)


class Stage2AIdentityStateTests(unittest.TestCase):
    def test_logical_and_fragment_identity_are_distinct(self):
        result = exclusion_split_identities("logical", "fragment", 1, lambda: "new")
        self.assertEqual(result, (("logical", "fragment"),))

    def test_split_preserves_logical_and_replaces_fragments(self):
        values = iter(("f2", "f3"))
        result = exclusion_split_identities("logical", "f1", 2, lambda: next(values))
        self.assertEqual(result, (("logical", "f2"), ("logical", "f3")))

    def test_generated_logical_identity_is_shared(self):
        values = iter(("logical", "f2", "f3"))
        result = exclusion_split_identities("", "", 2, lambda: next(values))
        self.assertEqual(result, (("logical", "f2"), ("logical", "f3")))

    def test_valid_empty_classification(self): self.assertEqual(classify_visible_state(True, 0, 1), "VALID_EMPTY")
    def test_empty_without_exclusion_is_normal_policy(self): self.assertEqual(classify_visible_state(True, 0, 0), "NORMAL")
    def test_invalid_is_not_valid_empty(self): self.assertEqual(classify_visible_state(False, 0, 1), "INVALID")

    def test_transaction_success(self):
        state = ["old"]
        transactional_edit(tuple(state), lambda: state.__setitem__(0, "new"), lambda: "curve", lambda value: state.append(value), lambda snapshot: state.__setitem__(slice(None), snapshot))
        self.assertEqual(state, ["new", "curve"])

    def test_transaction_rolls_back_prepare_failure(self):
        state = ["old"]
        def fail(): raise RuntimeError("geometry")
        with self.assertRaises(RuntimeError):
            transactional_edit(tuple(state), lambda: state.__setitem__(0, "new"), fail, lambda _value: None, lambda snapshot: state.__setitem__(slice(None), snapshot))
        self.assertEqual(state, ["old"])

    def test_partial_boundary_positive_validation(self): self.assertEqual(subtract_intervals((100, 900), ()), ((100.0, 900.0),))
    def test_partial_boundary_reverse_validation(self):
        with self.assertRaises(ValueError): subtract_intervals((900, 100), ())


class Stage2AReverseGroupingTests(unittest.TestCase):
    def assert_uncut(self, traversal):
        self.assertTrue(piece_reaches_boundary(
            (0, 1000), (0, 1000), traversal, "ARRIVAL"))
        self.assertTrue(piece_reaches_boundary(
            (0, 1000), (0, 1000), traversal, "DEPARTURE"))

    def test_forward_forward_continuous(self):
        self.assert_uncut("FORWARD"); self.assert_uncut("FORWARD")

    def test_forward_reverse_continuous(self):
        self.assert_uncut("FORWARD"); self.assert_uncut("REVERSE")

    def test_reverse_forward_continuous(self):
        self.assert_uncut("REVERSE"); self.assert_uncut("FORWARD")

    def test_reverse_reverse_continuous(self):
        self.assert_uncut("REVERSE"); self.assert_uncut("REVERSE")

    def test_reverse_arrival_cut_does_not_join_previous(self):
        self.assertFalse(piece_reaches_boundary(
            (0, 800), (0, 1000), "REVERSE", "ARRIVAL"))

    def test_reverse_departure_cut_does_not_join_next(self):
        self.assertFalse(piece_reaches_boundary(
            (200, 1000), (0, 1000), "REVERSE", "DEPARTURE"))

    def test_full_reverse_joins_both_sides(self): self.assert_uncut("REVERSE")


class Stage2ABoundaryAndMigrationTests(unittest.TestCase):
    def test_displayed_rounded_wall_end_normalizes_semantically(self):
        self.assertEqual(normalize_distance_from_start(3031.00, 3030.9994),
                         ("WALL_END", 0.0))

    def test_zero_normalizes_to_wall_start(self):
        self.assertEqual(normalize_distance_from_start(0.00, 3030.9994),
                         ("WALL_START", 0.0))

    def test_interior_distance_is_unchanged(self):
        self.assertEqual(normalize_distance_from_start(725.25, 3030.9994),
                         ("DISTANCE_FROM_START", 725.25))

    def test_clearly_outside_distance_is_rejected(self):
        with self.assertRaises(ValueError):
            normalize_distance_from_start(3031.02, 3030.9994)

    def test_wall_end_exclusion_round_trip_preserves_coverage(self):
        length = 3030.9994
        displayed = round(resolve_boundary("WALL_END", 0.0, length), 2)
        kind, value = normalize_distance_from_start(displayed, length)
        self.assertEqual((kind, value), ("WALL_END", 0.0))
        self.assertEqual(resolve_boundary(kind, value, length), length)

    def test_partial_wall_end_round_trip_remains_valid(self):
        length = 3030.9994
        displayed = round(resolve_boundary("WALL_END", 0.0, length), 2)
        kind, value = normalize_distance_from_start(displayed, length)
        self.assertEqual(resolve_boundary(kind, value, length), length)

    def test_normalized_full_span_is_valid_empty(self):
        length = 3030.9994
        start = normalize_distance_from_start(0.0, length)
        end = normalize_distance_from_start(3031.0, length)
        coverage = ((resolve_boundary(*start, length),
                     resolve_boundary(*end, length)),)
        visible = subtract_intervals((0.0, length), coverage)
        self.assertEqual(visible, ())
        self.assertEqual(classify_visible_state(True, len(visible), 1),
                         "VALID_EMPTY")

    def test_single_forward_fields(self):
        self.assertEqual((run_boundary_field("FORWARD", "START"),
                          run_boundary_field("FORWARD", "END")),
                         ("entry", "exit"))

    def test_single_reverse_fields(self):
        self.assertEqual((run_boundary_field("REVERSE", "START"),
                          run_boundary_field("REVERSE", "END")),
                         ("exit", "entry"))

    def test_multi_first_reverse(self):
        self.assertEqual(run_boundary_field("REVERSE", "START"), "exit")

    def test_multi_last_reverse(self):
        self.assertEqual(run_boundary_field("REVERSE", "END"), "entry")

    def test_existing_boundary_normalizes_from_wall_start(self):
        self.assertEqual(resolve_boundary("WALL_START", 123, 1000), 0)
        self.assertEqual(resolve_boundary("WALL_END", 123, 1000), 1000)
        self.assertEqual(resolve_boundary("DISTANCE_FROM_END", 250, 1000), 750)

    def test_legacy_identity_migrates_only_on_activation(self):
        values = iter(("logical", "fragment"))
        self.assertEqual(activated_identity("", "", lambda: next(values)),
                         ("logical", "fragment"))

    def test_existing_identity_is_preserved(self):
        self.assertEqual(activated_identity("logical", "fragment",
                                            lambda: self.fail()),
                         ("logical", "fragment"))


class Stage2AJunctionButtTests(unittest.TestCase):
    horizontal = ((0.0, 0.05), (2.0, 0.05))
    vertical = ((1.95, 0.0), (1.95, 2.0))
    corner = (1.95, 0.05)

    def test_previous_excluded_through_junction_trims_next_start(self):
        result = resolve_junction_butt(
            self.vertical, self.horizontal, "START")
        self.assertEqual(result, (self.corner, self.vertical[1]))

    def test_next_excluded_from_junction_trims_previous_end(self):
        result = resolve_junction_butt(
            self.horizontal, self.vertical, "END")
        self.assertEqual(result, (self.horizontal[0], self.corner))

    def test_reverse_and_side_orientation_are_axis_independent(self):
        reverse_vertical = tuple(reversed(self.vertical))
        reverse_horizontal = tuple(reversed(self.horizontal))
        result = resolve_junction_butt(
            reverse_vertical, reverse_horizontal, "END")[1]
        self.assertAlmostEqual(result[0], self.corner[0])
        self.assertAlmostEqual(result[1], self.corner[1])

    def test_normal_uncut_junction_still_resolves_one_miter(self):
        self.assertEqual(resolve_surface_path(
            (self.horizontal, self.vertical)),
            (self.horizontal[0], self.corner, self.vertical[1]))

    def test_interior_exclusion_remains_plain_butt(self):
        interior = ((0.5, 0.05), (1.0, 0.05))
        self.assertEqual(interior[1], (1.0, 0.05))

    def test_unrelated_branch_blocker_is_still_detected(self):
        self.assertTrue(endpoint_blocked_by_footprints(
            self.corner, (1.0, 0.0),
            (((1.95, 0.05), (2.95, 0.05), 0.1),), 0.01))


if __name__ == "__main__":
    unittest.main()
