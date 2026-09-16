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
    oriented_edge_indices, profile_is_referenced, sample_cyclic_bezier,
    scaled_contour, signed_area,
    validate_custom_profile_id, validate_uniform_scale,
)
from japanese_house_modeler.finish_profiles import (
    BEVEL_PROFILE_ID, PROFILE_INSTANCE_FIELDS, ROUNDED_PROFILE_ID,
    SIMPLE_PROFILE_ID, derived_profile_cache_identity, oriented_contour,
    resolve_custom_profile, resolve_profile, transactional_profile_edit,
)
from japanese_house_modeler.finish_mesh import (
    custom_polygon_should_be_smooth, polygon_should_be_smooth,
)


SQUARE = ((0, 0), (0.01, 0), (0.01, 0.06), (0, 0.06))
CLOCKWISE_SQUARE = ((0, 0), (0, 0.06), (0.01, 0.06), (0.01, 0))


def circle_knots():
    # Four deterministic cubic spans approximating a circle translated into +X/+Y.
    k = 0.5522847498307936
    raw = (((1, 0), (1 + k, 0), (1 - k, 0)),
           ((2, 1), (2, 1 + k), (2, 1 - k)),
           ((1, 2), (1 - k, 2), (1 + k, 2)),
           ((0, 1), (0, 1 - k), (0, 1 + k)))
    return tuple(tuple((x + 1, y + 1) for x, y in knot) for knot in raw)


def mixed_knots():
    """Convex contour whose first span is straight and second is curved."""
    return (((0, 0), (.5, 0), (0, .5)),
            ((2, 0), (2.8, .5), (1.5, 0)),
            ((2, 2), (1.5, 2), (2.8, 1.5)),
            ((0, 2), (0, 1.5), (.5, 2)))


class CustomContourTests(unittest.TestCase):
    def test_poly_ccw_input_normalizes_clockwise_without_closing_point(self):
        value = normalize_poly_contour(SQUARE + (SQUARE[0],))
        self.assertEqual(4, len(value)); self.assertLess(signed_area(value), 0)

    def test_poly_clockwise_input_remains_clockwise(self):
        value = normalize_poly_contour(CLOCKWISE_SQUARE)
        self.assertEqual(CLOCKWISE_SQUARE, value)
        self.assertLess(signed_area(value), 0)

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
        self.assertLess(signed_area(first), 0)

    def test_other_sampling_revision_rejected(self):
        with self.assertRaises(ValueError): sample_cyclic_bezier(circle_knots(), 8)

    def test_point_limit(self):
        with self.assertRaises(ValueError):
            sample_cyclic_bezier(circle_knots() * (CUSTOM_MAX_CONTOUR_POINTS // 16 + 1))

    def test_non_finite_handle(self):
        knots = list(circle_knots()); knots[0] = (knots[0][0], (math.nan, 0), knots[0][2])
        with self.assertRaises(ValueError): sample_cyclic_bezier(knots)

    def test_mixed_straight_and_curved_span_intent(self):
        snapshot = make_snapshot("BEZIER", knots=mixed_knots())
        self.assertLess(signed_area(snapshot.contour), 0)
        # Raw input is CCW, so old span edges 16..31 become canonical
        # clockwise edges n-2-i => 31..46 without losing their physical span.
        self.assertEqual(tuple(range(31, 47)), snapshot.smooth_edges)


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

    def test_custom_and_mirror_preserve_standard_clockwise_winding(self):
        contour = normalize_poly_contour(SQUARE)
        simple = resolve_profile("SIMPLE", 1, 1, 60, 10)
        self.assertLess(signed_area(contour), 0)
        self.assertLess(signed_area(simple.contour), 0)
        self.assertEqual(math.copysign(1, signed_area(simple.contour)),
                         math.copysign(1, signed_area(contour)))
        self.assertLess(signed_area(mirrored_contour(contour)), 0)
        profile = types.SimpleNamespace(contour=contour)
        self.assertLess(signed_area(oriented_contour(profile, 1)), 0)
        self.assertLess(signed_area(oriented_contour(profile, -1)), 0)

    def test_all_standard_profiles_are_clockwise(self):
        for name in ("SIMPLE", "BEVEL", "ROUNDED"):
            self.assertLess(signed_area(
                resolve_profile(name, 1, 1, 60, 10, 5, 5).contour), 0)

    def test_cache_identity_includes_scale_and_contour(self):
        base = resolve_profile("SIMPLE", 1, 1, 60, 10)
        changed = types.SimpleNamespace(**{**base.__dict__, "uniform_scale": 2})
        self.assertNotEqual(derived_profile_cache_identity(base, 1, 0),
                            derived_profile_cache_identity(changed, 1, 0))

    def test_cache_identity_includes_shading_intent(self):
        base = resolve_profile("SIMPLE", 1, 1, 60, 10)
        shading = types.SimpleNamespace(smooth_round=True,
                                        smooth_contour_edges=(1,))
        changed = types.SimpleNamespace(**{**base.__dict__, "shading": shading})
        self.assertNotEqual(derived_profile_cache_identity(base, 1, 0),
                            derived_profile_cache_identity(changed, 1, 0))

    def test_poly_shading_is_hard(self):
        self.assertEqual((), make_snapshot("POLY", points=SQUARE).smooth_edges)

    def test_bezier_shading_is_deterministic(self):
        first = make_snapshot("BEZIER", knots=circle_knots())
        second = make_snapshot("BEZIER", knots=circle_knots())
        self.assertEqual(first.smooth_edges, second.smooth_edges)
        self.assertEqual(tuple(range(len(first.contour))), first.smooth_edges)

    def test_mirrored_edge_remap_preserves_physical_edge(self):
        contour = ((0, 0), (3, 0), (2, 2), (0, 1))
        canonical = (0, 1)
        mirrored = oriented_edge_indices(len(contour), canonical, -1)
        self.assertEqual((0, 1), oriented_edge_indices(len(contour), canonical, 1))
        self.assertEqual((1, 2), mirrored)
        derived = mirrored_contour(contour)
        canonical_edges = {
            frozenset(((-contour[index][0], contour[index][1]),
                       (-contour[(index + 1) % len(contour)][0],
                        contour[(index + 1) % len(contour)][1])))
            for index in canonical}
        derived_edges = {frozenset((derived[index],
                                    derived[(index + 1) % len(derived)]))
                         for index in mirrored}
        self.assertEqual(canonical_edges, derived_edges)

    def test_custom_quad_consumes_explicit_edge_intent(self):
        profile = types.SimpleNamespace(
            contour=CLOCKWISE_SQUARE,
            shading=types.SimpleNamespace(smooth_contour_edges=(2,)))
        smooth_quad = ((0, .01, 0), (0, .01, .06),
                       (1, .01, .06), (1, .01, 0))
        hard_quad = ((0, 0, 0), (0, .01, 0),
                     (1, .01, 0), (1, 0, 0))
        path = (((0, 0, 0), (1, 0, 0)),)
        self.assertTrue(custom_polygon_should_be_smooth(
            profile, smooth_quad, 1, 0, path))
        self.assertFalse(custom_polygon_should_be_smooth(
            profile, hard_quad, 1, 0, path))
        self.assertFalse(custom_polygon_should_be_smooth(
            profile, ((0, 0, 0), (0, .01, 0), (0, .01, .06),
                      (0, .005, .07), (0, 0, .06)), 1, 0, path))  # cap stays flat

    def test_equal_height_opposite_edges_are_not_ambiguous(self):
        profile = types.SimpleNamespace(
            contour=CLOCKWISE_SQUARE,
            shading=types.SimpleNamespace(smooth_contour_edges=(2,)))
        path = (((0, 0, 0), (1, 0, 0)),)
        right = ((0, .01, 0), (0, .01, .06),
                 (1, .01, .06), (1, .01, 0))
        left = ((0, 0, .06), (0, 0, 0), (1, 0, 0), (1, 0, .06))
        self.assertTrue(custom_polygon_should_be_smooth(
            profile, right, 1, 0, path))
        self.assertFalse(custom_polygon_should_be_smooth(
            profile, left, 1, 0, path))

    def test_equal_height_opposite_edges_mirrored_orientation(self):
        profile = types.SimpleNamespace(
            contour=CLOCKWISE_SQUARE,
            shading=types.SimpleNamespace(smooth_contour_edges=(2,)))
        path = (((0, 0, 0), (1, 0, 0)),)
        mirrored_right = ((0, -.01, .06), (0, -.01, 0),
                          (1, -.01, 0), (1, -.01, .06))
        mirrored_left = ((0, 0, 0), (0, 0, .06),
                         (1, 0, .06), (1, 0, 0))
        self.assertTrue(custom_polygon_should_be_smooth(
            profile, mirrored_right, -1, 0, path))
        self.assertFalse(custom_polygon_should_be_smooth(
            profile, mirrored_left, -1, 0, path))

    def test_standard_stage2b_shading_unchanged(self):
        for name in ("SIMPLE", "BEVEL"):
            self.assertFalse(polygon_should_be_smooth(
                resolve_profile(name, 1, 1, 60, 10, 5, 5), .5))
        rounded = resolve_profile("ROUNDED", 1, 1, 60, 10, 5, 5)
        self.assertTrue(polygon_should_be_smooth(rounded, .5))
        self.assertFalse(polygon_should_be_smooth(rounded, 0))
        self.assertFalse(polygon_should_be_smooth(rounded, 1))


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
