"""Pure Build 06-B Stage 2-B standard Profile contracts."""

import math
import pathlib
import sys
import types
import unittest

ROOT = pathlib.Path(__file__).parents[1]
package = types.ModuleType("japanese_house_modeler")
package.__path__ = [str(ROOT / "japanese_house_modeler")]
sys.modules.setdefault("japanese_house_modeler", package)

from japanese_house_modeler.finish_mesh import polygon_should_be_smooth
from japanese_house_modeler.finish_exclusions import calculate_visible_intervals
from japanese_house_modeler.finish_profiles import (
    BEVEL_PROFILE_ID, DEFAULT_BEVEL_MM, DEFAULT_RADIUS_MM,
    LEGACY_SIMPLE_PROFILE_ID, PROFILE_SCHEMA_VERSION,
    ROUNDED_ARC_SEGMENTS_R1, ROUNDED_PROFILE_ID, SIMPLE_PROFILE_ID,
    derived_profile_cache_identity, oriented_contour, resolve_finish_profile,
    resolve_profile, transactional_profile_edit,
)
from japanese_house_modeler.finish_surface import (
    endpoint_blocked_by_footprints, validate_profile_miter_space,
)


def signed_area(points):
    return sum(a[0] * b[1] - b[0] * a[1]
               for a, b in zip(points, points[1:] + points[:1])) * .5


class Run:
    def __init__(self, profile_id="SIMPLE", height=60.0, projection=10.0,
                 bevel=5.0, radius=5.0):
        self.profile_id = profile_id
        self.profile_revision = 1
        self.profile_schema_version = 1
        self.profile_height_mm = height
        self.profile_projection_mm = projection
        self.profile_bevel_mm = bevel
        self.profile_radius_mm = radius

    def state(self):
        return (self.profile_id, self.profile_revision,
                self.profile_schema_version, self.profile_height_mm,
                self.profile_projection_mm, self.profile_bevel_mm,
                self.profile_radius_mm)


class NoopChange:
    replacement = None

    def commit(self, _replacement): pass
    def rollback(self): pass
    def discard(self, _replacement): pass
    def dispose_old(self): pass


class Stage2BResolutionTests(unittest.TestCase):
    def test_simple_contour_is_unchanged(self):
        profile = resolve_profile("SIMPLE", 1, 1, 60, 10)
        self.assertEqual(profile.contour,
                         ((0, 0), (0, .06), (.01, .06), (.01, 0)))
        self.assertEqual(profile.bounds, (0, .01, 0, .06))

    def test_bevel_revision_one_exact_contour_and_bounds(self):
        profile = resolve_profile("BEVEL", 1, 1, 60, 10, 2, 5)
        self.assertEqual(profile.contour,
                         ((0, 0), (0, .06), (.008, .06),
                          (.01, .058), (.01, 0)))
        self.assertEqual(profile.bounds, (0, .01, 0, .06))

    def test_rounded_revision_one_endpoints_count_and_bounds(self):
        profile = resolve_profile("ROUNDED", 1, 1, 60, 10, 5, 4)
        self.assertEqual(len(profile.contour), ROUNDED_ARC_SEGMENTS_R1 + 4)
        self.assertEqual(profile.contour[2], (.006, .06))
        self.assertAlmostEqual(profile.contour[-2][0], .01)
        self.assertAlmostEqual(profile.contour[-2][1], .056)
        self.assertEqual(profile.bounds, (0, .01, 0, .06))
        self.assertTrue(all(a != b for a, b in
                            zip(profile.contour, profile.contour[1:])))

    def test_rounded_resolution_is_deterministic(self):
        first = resolve_profile("ROUNDED", 1, 1, 83, 17, 5, 6)
        second = resolve_profile("ROUNDED", 1, 1, 83, 17, 5, 6)
        self.assertEqual(first, second)

    def test_unknown_revision_and_schema_are_strict(self):
        for kind in (BEVEL_PROFILE_ID, ROUNDED_PROFILE_ID):
            with self.assertRaises(ValueError):
                resolve_profile(kind, 2, 1, 60, 10, 5, 5)
            with self.assertRaises(ValueError):
                resolve_profile(kind, 1, 2, 60, 10, 5, 5)

    def test_relevant_round_and_bevel_constraints(self):
        for kind, bevel, radius in (("BEVEL", 10, 5),
                                    ("ROUNDED", 5, 10)):
            with self.assertRaises(ValueError):
                resolve_profile(kind, 1, 1, 60, 10, bevel, radius)

    def test_nonfinite_zero_and_negative_values_are_rejected(self):
        invalid = (float("nan"), float("inf"), 0, -1)
        for value in invalid:
            with self.assertRaises(ValueError):
                resolve_profile("BEVEL", 1, 1, 60, 10, value, 5)
            with self.assertRaises(ValueError):
                resolve_profile("ROUNDED", 1, 1, 60, 10, 5, value)
            with self.assertRaises(ValueError):
                resolve_profile("SIMPLE", 1, 1, value, 10)

    def test_inactive_parameters_do_not_change_simple_geometry(self):
        a = resolve_profile("SIMPLE", 1, 1, 60, 10, 1, 2)
        b = resolve_profile("SIMPLE", 1, 1, 60, 10, 7, 8)
        self.assertEqual(a.contour, b.contour)

    def test_legacy_simple_is_unchanged(self):
        profile = resolve_profile(LEGACY_SIMPLE_PROFILE_ID)
        self.assertEqual((profile.profile_id, profile.profile_revision,
                          profile.schema_version, profile.height_mm,
                          profile.projection_mm),
                         (SIMPLE_PROFILE_ID, 1, PROFILE_SCHEMA_VERSION, 60, 10))


class Stage2BOrientationAndIdentityTests(unittest.TestCase):
    def test_both_new_profiles_preserve_winding_when_mirrored(self):
        for kind in (BEVEL_PROFILE_ID, ROUNDED_PROFILE_ID):
            profile = resolve_profile(kind, 1, 1, 60, 10, 3, 3)
            positive = oriented_contour(profile, 1)
            negative = oriented_contour(profile, -1)
            self.assertGreater(signed_area(positive) * signed_area(negative), 0)
            self.assertGreaterEqual(min(x for x, _y in positive), 0)
            self.assertLessEqual(max(x for x, _y in negative), 0)

    def test_bevel_cache_identity_includes_bevel(self):
        a = resolve_profile("BEVEL", 1, 1, 60, 10, 2, 5)
        b = resolve_profile("BEVEL", 1, 1, 60, 10, 5, 5)
        self.assertNotEqual(derived_profile_cache_identity(a, 1, 0),
                            derived_profile_cache_identity(b, 1, 0))

    def test_rounded_cache_identity_includes_radius(self):
        a = resolve_profile("ROUNDED", 1, 1, 60, 10, 5, 2)
        b = resolve_profile("ROUNDED", 1, 1, 60, 10, 5, 5)
        self.assertNotEqual(derived_profile_cache_identity(a, 1, 0),
                            derived_profile_cache_identity(b, 1, 0))


class Stage2BTransactionAndSafetyTests(unittest.TestCase):
    def test_run_local_profile_switch_does_not_touch_other_run(self):
        first, second = Run(), Run()
        transactional_profile_edit(
            first, ("BEVEL", 1, 1, 80, 20, 6, 5), NoopChange)
        self.assertEqual(resolve_finish_profile(first).profile_id, "BEVEL")
        self.assertEqual(second.state(), ("SIMPLE", 1, 1, 60, 10, 5, 5))

    def test_failed_kind_switch_restores_every_profile_field(self):
        run = Run("BEVEL", 70, 14, 4, 3)
        before = run.state()
        with self.assertRaises(ValueError):
            transactional_profile_edit(
                run, ("ROUNDED", 1, 1, 90, 20, 8, 20), lambda: None)
        self.assertEqual(run.state(), before)

    def test_prepare_failure_restores_kind_parameters_and_material_owner(self):
        run = Run()
        material = object()
        run.material = material
        with self.assertRaisesRegex(RuntimeError, "geometry"):
            transactional_profile_edit(
                run, ("BEVEL", 1, 1, 70, 14, 4, 9),
                lambda: (_ for _ in ()).throw(RuntimeError("geometry")))
        self.assertEqual(run.state(), ("SIMPLE", 1, 1, 60, 10, 5, 5))
        self.assertIs(run.material, material)

    def test_safety_extent_comes_from_resolved_bounds(self):
        profile = resolve_profile("ROUNDED", 1, 1, 60, 37, 5, 5)
        self.assertEqual(profile.projection_m, profile.bounds[1])
        blocker = (((.03, -.1), (.03, .1), .01),)
        self.assertTrue(endpoint_blocked_by_footprints(
            (0, 0), (1, 0), blocker, profile.projection_m))

    def test_nondefault_profile_extent_drives_short_segment_validation(self):
        segments = (((0, 0), (1, 0)), ((1, 0), (1, .03)),
                    ((1, .03), (2, .03)))
        profile = resolve_profile("BEVEL", 1, 1, 60, 20, 5, 5)
        with self.assertRaisesRegex(ValueError, "短すぎ"):
            validate_profile_miter_space(segments, profile.projection_m)

    def test_bevel_and_rounded_keep_exclusion_pieces_independent(self):
        expected = (("wall", 0.0, 700.0, "FORWARD"),
                    ("wall", 1100.0, 2000.0, "FORWARD"))
        for kind in (BEVEL_PROFILE_ID, ROUNDED_PROFILE_ID):
            profile = resolve_profile(kind, 1, 1, 60, 10, 5, 5)
            visible = calculate_visible_intervals(
                (("wall", 0, 2000, "FORWARD"),),
                (("wall", 700, 1100, True),))
            self.assertEqual(visible, expected)
            self.assertEqual(len(visible), 2)  # no join across the gap
            self.assertEqual(profile.maximum_horizontal_extent_m, .01)


class Stage2BShadingPolicyTests(unittest.TestCase):
    def test_simple_and_bevel_are_entirely_planar(self):
        for kind in ("SIMPLE", "BEVEL"):
            profile = resolve_profile(kind, 1, 1, 60, 10, 5, 5)
            self.assertFalse(profile.shading.smooth_round)
            self.assertFalse(polygon_should_be_smooth(profile, .5))

    def test_rounded_arc_is_smooth_but_planar_regions_are_flat(self):
        profile = resolve_profile("ROUNDED", 1, 1, 60, 10, 5, 5)
        self.assertEqual(profile.shading.smooth_contour_edges,
                         tuple(range(2, 18)))
        self.assertTrue(polygon_should_be_smooth(profile, .5))
        self.assertFalse(polygon_should_be_smooth(profile, 0))
        self.assertFalse(polygon_should_be_smooth(profile, 1))


if __name__ == "__main__":
    unittest.main()
