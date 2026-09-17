"""Pure Build 06-C Stage 1 Crown orientation and transaction coverage."""

import pathlib
import sys
import types
import unittest

ROOT = pathlib.Path(__file__).parents[1]
package = types.ModuleType("japanese_house_modeler")
package.__path__ = [str(ROOT / "japanese_house_modeler")]
sys.modules.setdefault("japanese_house_modeler", package)

from japanese_house_modeler.finish_exclusions import classify_visible_state
from japanese_house_modeler.finish_orientation import (
    finish_vertical_sign, orientation_parity, oriented_profile_contour,
    placed_vertical_bounds, regeneration_state_after_bulk,
)
from japanese_house_modeler.finish_path import resolve_vertical
from japanese_house_modeler.finish_profiles import (
    PROFILE_SCHEMA_VERSION, SIMPLE_PROFILE_ID, SIMPLE_PROFILE_REVISION,
    derived_profile_cache_identity, placement_adjusted_contour, resolve_profile,
)


def signed_area(contour):
    return sum(x1 * y2 - x2 * y1
               for (x1, y1), (x2, y2) in
               zip(contour, contour[1:] + contour[:1])) / 2.0


class FinishOrientationTests(unittest.TestCase):
    def setUp(self):
        self.simple = resolve_profile(
            SIMPLE_PROFILE_ID, SIMPLE_PROFILE_REVISION,
            PROFILE_SCHEMA_VERSION, 60.0, 10.0)

    def test_baseboard_vertical_sign_is_positive(self):
        self.assertEqual(finish_vertical_sign("BASEBOARD"), 1.0)

    def test_crown_vertical_sign_is_negative(self):
        self.assertEqual(finish_vertical_sign("CROWN"), -1.0)

    def test_unknown_finish_type_is_rejected(self):
        with self.assertRaises(ValueError):
            finish_vertical_sign("CHAIR_RAIL")

    def test_orientation_parity_covers_single_and_double_reflections(self):
        self.assertEqual(orientation_parity(1, -1), -1)
        self.assertEqual(orientation_parity(-1, -1), 1)

    def test_crown_simple_extends_downward_from_reference(self):
        contour = placement_adjusted_contour(self.simple, 1, 2.5, -1)
        self.assertAlmostEqual(min(y for _x, y in contour), 2.44)
        self.assertAlmostEqual(max(y for _x, y in contour), 2.5)

    def test_vertical_placement_uses_actual_nonzero_profile_bounds(self):
        self.assertEqual(placed_vertical_bounds((-.1, .2, .02, .08), 2.5, -1),
                         (2.42, 2.48))

    def test_vertical_reflection_preserves_winding(self):
        original = self.simple.contour
        reflected = oriented_profile_contour(original, 1, -1)
        self.assertGreater(signed_area(original) * signed_area(reflected), 0)

    def test_double_reflection_preserves_winding(self):
        original = self.simple.contour
        reflected = oriented_profile_contour(original, -1, -1)
        self.assertGreater(signed_area(original) * signed_area(reflected), 0)

    def test_baseboard_orientation_is_unchanged(self):
        self.assertEqual(placement_adjusted_contour(self.simple, 1, 0, 1),
                         self.simple.contour)

    def test_cache_identity_distinguishes_vertical_orientation(self):
        upward = derived_profile_cache_identity(self.simple, 1, 2.5, 1)
        downward = derived_profile_cache_identity(self.simple, 1, 2.5, -1)
        self.assertNotEqual(upward, downward)

    def test_vertical_offset_keeps_world_z_sign(self):
        self.assertAlmostEqual(resolve_vertical("CEILING", -20, 0, 0, 2500),
                               2.48)

    def test_reference_arithmetic_is_unchanged(self):
        self.assertAlmostEqual(resolve_vertical("FLOOR", 35, 0, 100, 2500),
                               .135)
        self.assertAlmostEqual(resolve_vertical("ABSOLUTE", -999, 725, 0, 0),
                               .725)


class FinishStateTests(unittest.TestCase):
    def test_full_exclusion_is_valid_empty(self):
        self.assertEqual(classify_visible_state(True, 0, 1), "VALID_EMPTY")

    def test_empty_without_exclusion_is_not_valid_empty(self):
        self.assertEqual(classify_visible_state(True, 0, 0), "NORMAL")

    def test_failed_bulk_retains_all_old_geometry_and_marks_stale(self):
        old = ("baseboard-old", "crown-old")
        installed, stale = regeneration_state_after_bulk(
            old, ("baseboard-new",), RuntimeError("injected"))
        self.assertEqual(installed, old)
        self.assertTrue(stale)

    def test_successful_bulk_installs_all_and_clears_stale(self):
        installed, stale = regeneration_state_after_bulk(
            ("old-a", "old-b"), ("new-a", "new-b"))
        self.assertEqual(installed, ("new-a", "new-b"))
        self.assertFalse(stale)

    def test_partial_success_is_not_a_valid_bulk_commit(self):
        with self.assertRaises(ValueError):
            regeneration_state_after_bulk(("old-a", "old-b"), ("new-a",))


if __name__ == "__main__":
    unittest.main()
