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
    derived_profile_cache_identity,
    LEGACY_SIMPLE_PROFILE_ID, PROFILE_SCHEMA_VERSION,
    PRODUCTION_CURVE_DIMENSIONS, SIMPLE_PROFILE_ID,
    oriented_contour, placement_adjusted_contour, production_profile_values,
    resolve_profile,
    resolve_default_simple_profile, transactional_profile_edit,
    uniform_vertical_base,
)
from japanese_house_modeler.finish_path import profile_horizontal_sign
from japanese_house_modeler.finish_mesh import (
    MESH_WELD_DISTANCE_M, closed_volume_topology_is_valid,
)
from japanese_house_modeler.finish_surface import (
    endpoint_blocked_by_footprints, transition_blocked_by_footprints,
    validate_profile_miter_space,
)


def signed_area(points):
    return sum(a[0] * b[1] - b[0] * a[1]
               for a, b in zip(points, points[1:] + points[:1])) * .5


class Build06BStage1ProfileTests(unittest.TestCase):
    def test_production_finish_path_is_two_dimensional(self):
        self.assertEqual(PRODUCTION_CURVE_DIMENSIONS, "2D")

    def test_placement_adjusted_contour_preserves_canonical_profile(self):
        profile = resolve_profile("SIMPLE", 1, 1, 60, 10)
        canonical = profile.contour
        for base, expected_y in ((0.0, (0.0, .06)),
                                 (.5, (.5, .56)),
                                 (-.2, (-.2, -.14))):
            derived = placement_adjusted_contour(profile, 1, base)
            self.assertEqual({x for x, _y in derived}, {0.0, .01})
            self.assertEqual((min(y for _x, y in derived),
                              max(y for _x, y in derived)), expected_y)
            self.assertEqual(profile.contour, canonical)
            self.assertEqual((profile.height_mm, profile.projection_mm),
                             (60, 10))

    def test_placement_mirroring_preserves_winding_and_cache_separation(self):
        profile = resolve_profile("SIMPLE", 1, 1, 60, 10)
        positive = placement_adjusted_contour(profile, 1, .5)
        mirrored = placement_adjusted_contour(profile, -1, .5)
        self.assertGreater(signed_area(positive) * signed_area(mirrored), 0)
        first = derived_profile_cache_identity(profile, 1, .5)
        second = derived_profile_cache_identity(profile, 1, -.2)
        self.assertNotEqual(first, second)
        self.assertEqual(first[-1], 500.0)
        self.assertEqual(second[-1], -200.0)

    def test_stage1_path_requires_one_vertical_base(self):
        self.assertEqual(uniform_vertical_base(((0, 0, .5), (1, 0, .5))), .5)
        with self.assertRaisesRegex(ValueError, "異なるvertical"):
            uniform_vertical_base(((0, 0, .5), (1, 0, .6)))

    def test_mesh_cleanup_uses_micrometre_weld_and_closed_volume_policy(self):
        self.assertEqual(MESH_WELD_DISTANCE_M, 1.0e-6)
        self.assertTrue(closed_volume_topology_is_valid(0, 0, .001))
        self.assertTrue(closed_volume_topology_is_valid(0, 0, -.001))
        self.assertFalse(closed_volume_topology_is_valid(1, 1, .001))
        self.assertFalse(closed_volume_topology_is_valid(0, 0, 0.0))
        self.assertFalse(closed_volume_topology_is_valid(
            0, 0, float("nan")))

    def test_preview_default_uses_resolved_production_simple_profile(self):
        profile = resolve_default_simple_profile()
        self.assertEqual((profile.profile_id, profile.profile_revision,
                          profile.schema_version), ("SIMPLE", 1, 1))
        self.assertEqual(profile.projection_m, .01)

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

    def test_valid_provisional_edit_rolls_back_when_prepare_fails(self):
        class Run:
            profile_id = "SIMPLE"
            profile_revision = 1
            profile_schema_version = 1
            profile_height_mm = 60.0
            profile_projection_mm = 10.0

        run = Run()

        def fail_prepare():
            self.assertEqual((run.profile_id, run.profile_revision,
                              run.profile_schema_version, run.profile_height_mm,
                              run.profile_projection_mm),
                             ("SIMPLE", 1, 1, 85.0, 17.0))
            raise ValueError("injected preparation failure")

        with self.assertRaisesRegex(ValueError, "injected"):
            transactional_profile_edit(
                run, ("SIMPLE", 1, 1, 85.0, 17.0), fail_prepare)
        self.assertEqual((run.profile_id, run.profile_revision,
                          run.profile_schema_version, run.profile_height_mm,
                          run.profile_projection_mm),
                         ("SIMPLE", 1, 1, 60.0, 10.0))

    def test_transition_blocker_checks_only_actual_profile_side(self):
        transition = (((0, 0), (1, 0)), ((1, 0), (2, 0)))
        upper = (((1, .03), (1, .2), .01),)
        lower = (((1, -.2), (1, -.03), .01),)
        outward = ((0.0, 1.0), (0.0, 1.0))
        self.assertTrue(transition_blocked_by_footprints(
            *transition, upper, projection_m=.05, outward_normals=outward))
        self.assertFalse(transition_blocked_by_footprints(
            *transition, lower, projection_m=.05, outward_normals=outward))

    def test_transition_blocker_rejects_outer_miter_envelope_only(self):
        transition = (((0, 0), (1, 0)), ((1, 0), (1, 1)))
        # Neither straight outer edge reaches this thin vertical footprint;
        # only the horizontal edge from the first outer endpoint to the outer
        # miter vertex crosses it.
        blocker = (((1.05, .095), (1.05, .2), .005),)
        self.assertTrue(transition_blocked_by_footprints(
            *transition, blocker, projection_m=.1,
            outward_normals=((0.0, 1.0), (1.0, 0.0))))

    def test_resolved_join_length_rejects_overlapping_miters(self):
        # Raw middle length is 300 mm, but its two resolved joins are only
        # 100 mm apart.  Two 60 mm miter extensions therefore overlap.
        segments = (((0, 0), (1, 0)),
                    ((1.02, -.1), (1.02, .2)),
                    ((1, .1), (2, .1)))
        with self.assertRaisesRegex(ValueError, "短すぎ"):
            validate_profile_miter_space(segments, .06)


if __name__ == "__main__":
    unittest.main()
