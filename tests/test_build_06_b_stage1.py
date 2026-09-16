"""Pure Build 06-B Stage 1 production Profile and safety contracts."""

import pathlib
import sys
import types
import unittest

ROOT = pathlib.Path(__file__).parents[1]
package = types.ModuleType("japanese_house_modeler")
package.__path__ = [str(ROOT / "japanese_house_modeler")]
sys.modules.setdefault("japanese_house_modeler", package)

from japanese_house_modeler.finish_profiles import (
    LEGACY_SIMPLE_PROFILE_ID, PROFILE_SCHEMA_VERSION, SIMPLE_PROFILE_ID,
    oriented_contour, production_profile_values, resolve_profile,
    transactional_profile_edit,
)
from japanese_house_modeler.finish_path import profile_horizontal_sign
from japanese_house_modeler.finish_surface import (
    endpoint_blocked_by_footprints, validate_profile_miter_space,
)


def signed_area(points):
    return sum(a[0] * b[1] - b[0] * a[1]
               for a, b in zip(points, points[1:] + points[:1])) * .5


class Build06BStage1ProfileTests(unittest.TestCase):
    def test_simple_default_60_by_10(self):
        profile = resolve_profile("SIMPLE", 1, 1, 60, 10)
        self.assertEqual((profile.height_mm, profile.projection_mm), (60, 10))
        self.assertEqual(profile.bounds, (0, .01, 0, .06))

    def test_simple_run_local_height_and_projection(self):
        run_a = resolve_profile("SIMPLE", 1, 1, 80, 18)
        run_b = resolve_profile("SIMPLE", 1, 1, 60, 10)
        self.assertEqual((run_a.height_mm, run_a.projection_mm), (80, 18))
        self.assertEqual((run_b.height_mm, run_b.projection_mm), (60, 10))

    def test_invalid_dimensions_identity_revision_and_schema_rejected(self):
        for dimensions in ((0, 10), (-1, 10), (60, float("inf")),
                           (float("nan"), 10)):
            with self.assertRaises(ValueError):
                resolve_profile("SIMPLE", 1, 1, *dimensions)
        for identity in (("MISSING", 1, 1), ("SIMPLE", 2, 1),
                         ("SIMPLE", 1, 2)):
            with self.assertRaises(ValueError):
                resolve_profile(*identity, 60, 10)

    def test_legacy_is_non_destructively_resolved_and_editable(self):
        profile = resolve_profile(LEGACY_SIMPLE_PROFILE_ID, 0, 0, 0, 0)
        self.assertEqual((profile.profile_id, profile.profile_revision,
                          profile.schema_version, profile.height_mm,
                          profile.projection_mm),
                         (SIMPLE_PROFILE_ID, 1, PROFILE_SCHEMA_VERSION, 60, 10))
        self.assertEqual(production_profile_values(profile),
                         ("SIMPLE", 1, 1, 60, 10))

    def test_all_side_traversal_orientation_combinations(self):
        expected = {("LEFT", "FORWARD"): -1, ("LEFT", "REVERSE"): 1,
                    ("RIGHT", "FORWARD"): 1, ("RIGHT", "REVERSE"): -1}
        self.assertEqual({key: profile_horizontal_sign(*key) for key in expected},
                         expected)

    def test_mirrored_contour_preserves_winding(self):
        profile = resolve_profile("SIMPLE", 1, 1, 75, 14)
        positive = oriented_contour(profile, 1)
        negative = oriented_contour(profile, -1)
        self.assertGreater(signed_area(positive) * signed_area(negative), 0)
        self.assertEqual({abs(x) for x, _y in negative}, {0, .014})


class Build06BStage1SafetyTests(unittest.TestCase):
    def test_ninety_and_oblique_miters_scale_with_projection(self):
        ninety = (((0, 0), (1, 0)), ((1, 0), (1, 1)))
        oblique = (((0, 0), (1, 0)), ((1, 0), (1.5, .8660254)))
        self.assertAlmostEqual(validate_profile_miter_space(ninety, .01)[1], .01)
        self.assertAlmostEqual(validate_profile_miter_space(ninety, .04)[1], .04)
        self.assertGreater(validate_profile_miter_space(oblique, .02)[1], 0)

    def test_short_segment_between_corners_is_rejected(self):
        segments = (((0, 0), (1, 0)), ((1, 0), (1, .03)),
                    ((1, .03), (2, .03)))
        with self.assertRaisesRegex(ValueError, "短すぎ"):
            validate_profile_miter_space(segments, .02)

    def test_endpoint_blocker_uses_actual_projection_not_ten_mm(self):
        blocker = (((.03, -.1), (.03, .1), .01),)
        self.assertFalse(endpoint_blocked_by_footprints(
            (0, 0), (1, 0), blocker, .01))
        self.assertTrue(endpoint_blocked_by_footprints(
            (0, 0), (1, 0), blocker, .05))

    def test_failed_edit_snapshot_contract(self):
        class Run:
            profile_id = "SIMPLE"
            profile_revision = 1
            profile_schema_version = 1
            profile_height_mm = 60.0
            profile_projection_mm = 10.0

        run = Run()
        with self.assertRaises(ValueError):
            transactional_profile_edit(
                run, ("SIMPLE", 1, 1, 0.0, 20.0),
                lambda: self.fail("invalid values must not prepare geometry"))
        self.assertEqual((run.profile_id, run.profile_revision,
                          run.profile_schema_version, run.profile_height_mm,
                          run.profile_projection_mm),
                         ("SIMPLE", 1, 1, 60.0, 10.0))


if __name__ == "__main__":
    unittest.main()
