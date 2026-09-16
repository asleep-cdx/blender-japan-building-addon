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
    calculate_visible_intervals, classify_visible_state,
    exclusion_split_identities, merge_coverage, subtract_intervals,
    transactional_edit,
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


if __name__ == "__main__":
    unittest.main()
