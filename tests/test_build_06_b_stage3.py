"""Pure regression coverage for Build 06-B Stage 3 Custom Profiles."""

import math
import pathlib
import sys
import types
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).parents[1]
package = types.ModuleType("japanese_house_modeler")
package.__path__ = [str(ROOT / "japanese_house_modeler")]
sys.modules.setdefault("japanese_house_modeler", package)

from japanese_house_modeler.finish_custom_profiles import (
    CUSTOM_BEZIER_SEGMENTS_PER_SPAN_R1, CUSTOM_MAX_CONTOUR_POINTS,
    CUSTOM_COORDINATE_TOLERANCE_M, RESERVED_PROFILE_IDS, contour_bounds,
    cubic_bezier, find_definition, has_self_intersection, make_snapshot,
    mirrored_contour, new_custom_profile_id, normalize_poly_contour,
    profile_is_referenced, sample_cyclic_bezier, scaled_contour, signed_area,
    validate_custom_profile_id, validate_uniform_scale,
)
from japanese_house_modeler.finish_profiles import (
    BEVEL_PROFILE_ID, PROFILE_INSTANCE_FIELDS, ROUNDED_PROFILE_ID,
    SIMPLE_PROFILE_ID, derived_profile_cache_identity, oriented_contour,
    resolve_custom_profile, resolve_profile, transactional_profile_edit,
)


SQUARE = ((0, 0), (0.01, 0), (0.01, 0.06), (0, 0.06))


def circle_knots():
    # Four deterministic cubic spans approximating a circle translated into +X/+Y.
    k = 0.5522847498307936
    raw = (((1, 0), (1 + k, 0), (1 - k, 0)),
           ((2, 1), (2, 1 + k), (2, 1 - k)),
           ((1, 2), (1 - k, 2), (1 + k, 2)),
           ((0, 1), (0, 1 - k), (0, 1 + k)))
    return tuple(tuple((x + 1, y + 1) for x, y in knot) for knot in raw)


class CustomContourTests(unittest.TestCase):
    def test_poly_removes_closing_point_and_normalizes_ccw(self):
        value = normalize_poly_contour(tuple(reversed(SQUARE)) + (SQUARE[-1],))
        self.assertEqual(4, len(value)); self.assertGreater(signed_area(value), 0)

    def test_poly_bounds(self):
        self.assertEqual((0.0, .01, 0.0, .06), contour_bounds(normalize_poly_contour(SQUARE)))

    def test_duplicate_collapse(self):
        with self.assertRaises(ValueError): normalize_poly_contour(((0, 0),) * 4)

    def test_fewer_than_three(self):
        with self.assertRaises(ValueError): normalize_poly_contour(((0, 0), (1, 0)))

    def test_zero_area(self):
        with self.assertRaises(ValueError): normalize_poly_contour(((0, 0), (1, 0), (2, 0)))

    def test_negative_region(self):
        with self.assertRaises(ValueError): normalize_poly_contour(((-1, 0), (1, 0), (0, 1)))

    def test_tolerance_allows_tiny_negative(self):
        value = normalize_poly_contour(((-CUSTOM_COORDINATE_TOLERANCE_M, 0), (1, 0), (0, 1)))
        self.assertEqual(3, len(value))

    def test_bow_tie_rejected(self):
        with self.assertRaises(ValueError): normalize_poly_contour(((0, 0), (1, 1), (0, 1), (1, 0)))

    def test_non_adjacent_touch_rejected(self):
        self.assertTrue(has_self_intersection(((0, 0), (2, 0), (1, 0), (1, 1))))

    def test_concavity_explicitly_rejected(self):
        with self.assertRaisesRegex(ValueError, "凹形"):
            normalize_poly_contour(((0, 0), (2, 0), (1, 1), (2, 2), (0, 2)))

    def test_non_finite(self):
        with self.assertRaises(ValueError): normalize_poly_contour(((0, 0), (math.inf, 0), (0, 1)))


class BezierTests(unittest.TestCase):
    def test_cubic_endpoints(self):
        self.assertEqual((0.0, 0.0), cubic_bezier((0, 0), (1, 0), (1, 1), (2, 1), 0))
        self.assertEqual((2.0, 1.0), cubic_bezier((0, 0), (1, 0), (1, 1), (2, 1), 1))

    def test_fixed_sampling_repeatability(self):
        first = sample_cyclic_bezier(circle_knots())
        self.assertEqual(first, sample_cyclic_bezier(circle_knots()))
        self.assertEqual(4 * CUSTOM_BEZIER_SEGMENTS_PER_SPAN_R1, len(first))
        self.assertNotEqual(first[0], first[-1])

    def test_other_sampling_revision_rejected(self):
        with self.assertRaises(ValueError): sample_cyclic_bezier(circle_knots(), 8)

    def test_point_limit(self):
        with self.assertRaises(ValueError):
            sample_cyclic_bezier(circle_knots() * (CUSTOM_MAX_CONTOUR_POINTS // 16 + 1))

    def test_non_finite_handle(self):
        knots = list(circle_knots()); knots[0] = (knots[0][0], (math.nan, 0), knots[0][2])
        with self.assertRaises(ValueError): sample_cyclic_bezier(knots)


class IdentityAndResolutionTests(unittest.TestCase):
    def test_ids_are_unique_and_reserved(self):
        first, second = new_custom_profile_id(), new_custom_profile_id()
        self.assertNotEqual(first, second); self.assertNotIn(first, RESERVED_PROFILE_IDS)

    def test_reserved_id_rejected(self):
        with self.assertRaises(ValueError): validate_custom_profile_id("SIMPLE")

    def test_immutable_lookup(self):
        item = types.SimpleNamespace(profile_id="CUSTOM-x", profile_revision=1, schema_version=1)
        self.assertIs(item, find_definition([item], "CUSTOM-x", 1, 1))
        with self.assertRaises(ValueError): find_definition([item], "CUSTOM-x", 2, 1)

    def test_source_independent_snapshot(self):
        snapshot = make_snapshot("POLY", points=SQUARE)
        self.assertFalse(hasattr(snapshot, "source_object")); self.assertIsInstance(snapshot.contour, tuple)

    def test_standard_regression(self):
        for name in (SIMPLE_PROFILE_ID, BEVEL_PROFILE_ID, ROUNDED_PROFILE_ID):
            profile = resolve_profile(name, 1, 1, 60, 10, 5, 5)
            self.assertEqual(name, profile.profile_id)
        self.assertEqual("SIMPLE", resolve_profile("SIMPLE_10X60").profile_id)

    def test_custom_resolution_scale_and_bounds(self):
        points = [types.SimpleNamespace(x=x, y=y, smooth_to_next=False) for x, y in SQUARE]
        definition = types.SimpleNamespace(profile_id="CUSTOM-x", profile_revision=1,
            schema_version=1, display_name="X", points=points)
        profile = resolve_custom_profile("CUSTOM-x", 1, 1, 2, [definition])
        self.assertEqual(.02, profile.projection_m); self.assertEqual(.12, profile.height_m)
        self.assertEqual(2, profile.uniform_scale)


class ScaleOrientationShadingTests(unittest.TestCase):
    def test_scale_validation(self):
        for value in (0, -1, math.inf, math.nan):
            with self.assertRaises(ValueError): validate_uniform_scale(value)

    def test_scaled_contour(self):
        self.assertEqual(((0.0, 0.0), (2.0, 4.0)), scaled_contour(((0, 0), (1, 2)), 2))

    def test_mirror_preserves_positive_winding(self):
        contour = normalize_poly_contour(SQUARE)
        self.assertGreater(signed_area(mirrored_contour(contour)), 0)
        profile = types.SimpleNamespace(contour=contour)
        self.assertGreater(signed_area(oriented_contour(profile, -1)), 0)

    def test_cache_identity_includes_scale_and_contour(self):
        base = resolve_profile("SIMPLE", 1, 1, 60, 10)
        changed = types.SimpleNamespace(**{**base.__dict__, "uniform_scale": 2})
        self.assertNotEqual(derived_profile_cache_identity(base, 1, 0),
                            derived_profile_cache_identity(changed, 1, 0))

    def test_poly_shading_is_hard(self):
        self.assertEqual((), make_snapshot("POLY", points=SQUARE).smooth_edges)

    def test_bezier_shading_is_deterministic(self):
        first = make_snapshot("BEZIER", knots=circle_knots())
        second = make_snapshot("BEZIER", knots=circle_knots())
        self.assertEqual(first.smooth_edges, second.smooth_edges)
        self.assertEqual(tuple(range(len(first.contour))), first.smooth_edges)


class SafetyTransactionTests(unittest.TestCase):
    def test_reference_helper(self):
        finish = types.SimpleNamespace(is_finish=True, profile_id="CUSTOM-x",
                                       profile_revision=1, profile_schema_version=1)
        obj = types.SimpleNamespace(jhm_finish=finish)
        self.assertTrue(profile_is_referenced([obj], "CUSTOM-x"))
        self.assertFalse(profile_is_referenced([obj], "CUSTOM-y"))

    def test_missing_custom_rolls_back_all_fields(self):
        values = ("CUSTOM-missing", 1, 1, 9, 8, 2, 3, 4)
        owner = types.SimpleNamespace(**dict(zip(PROFILE_INSTANCE_FIELDS,
            ("SIMPLE", 1, 1, 60, 10, 5, 5, 1))))
        before = tuple(getattr(owner, field) for field in PROFILE_INSTANCE_FIELDS)
        with self.assertRaises(ValueError): transactional_profile_edit(owner, values, mock.Mock(), [])
        self.assertEqual(before, tuple(getattr(owner, field) for field in PROFILE_INSTANCE_FIELDS))

    def test_unsafe_scale_rolls_back(self):
        point_defs = [types.SimpleNamespace(x=x, y=y, smooth_to_next=False) for x, y in SQUARE]
        definition = types.SimpleNamespace(profile_id="CUSTOM-x", profile_revision=1,
            schema_version=1, display_name="X", points=point_defs)
        owner = types.SimpleNamespace(**dict(zip(PROFILE_INSTANCE_FIELDS,
            ("SIMPLE", 1, 1, 60, 10, 5, 5, 1))))
        before = tuple(getattr(owner, field) for field in PROFILE_INSTANCE_FIELDS)
        with self.assertRaises(ValueError):
            transactional_profile_edit(owner, ("CUSTOM-x", 1, 1, 60, 10, 5, 5, 0), mock.Mock(), [definition])
        self.assertEqual(before, tuple(getattr(owner, field) for field in PROFILE_INSTANCE_FIELDS))


if __name__ == "__main__":
    unittest.main()
