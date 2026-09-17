"""Pure coverage for Build 06-C Stage 2 Crown Profile support."""

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
    make_snapshot, oriented_edge_indices, signed_area,
)
from japanese_house_modeler.finish_mesh import custom_polygon_should_be_smooth
from japanese_house_modeler.finish_orientation import (
    oriented_profile_contour, placed_vertical_bounds,
)
from japanese_house_modeler.finish_profiles import (
    PROFILE_INSTANCE_FIELDS, STANDARD_PROFILE_IDS, derived_profile_cache_identity,
    oriented_contour, placement_adjusted_contour, resolve_custom_profile,
    resolve_profile, transactional_profile_edit,
)


STANDARD = ("SIMPLE", "BEVEL", "ROUNDED")


def _profile(name):
    return resolve_profile(name, 1, 1, 60, 10, 5, 5)


def _definition(profile_id="CUSTOM-asymmetric", smooth=(1,)):
    # Clockwise, convex, non-zero-offset contour.  Deliberate asymmetry makes
    # an incorrect vertical reflection observable in coordinates and shading.
    contour = ((.002, .003), (.004, .021), (.013, .074), (.019, .008))
    points = [types.SimpleNamespace(
        x=x, y=y, smooth_to_next=index in smooth)
        for index, (x, y) in enumerate(contour)]
    return types.SimpleNamespace(profile_id=profile_id, profile_revision=1,
                                 schema_version=1, display_name="Asymmetric",
                                 points=points)


class StandardCrownOrientationTests(unittest.TestCase):
    def test_vertical_reflection_of_every_standard_profile(self):
        for name in STANDARD:
            canonical = _profile(name).contour
            crown = oriented_contour(_profile(name), 1, -1)
            self.assertEqual(crown,
                             tuple(reversed(tuple((x, -y) for x, y in canonical))))
            self.assertLess(signed_area(crown), 0)

    def test_all_horizontal_vertical_parities_preserve_winding(self):
        contour = _profile("BEVEL").contour
        for horizontal in (-1, 1):
            for vertical in (-1, 1):
                oriented = oriented_profile_contour(contour, horizontal, vertical)
                self.assertLess(signed_area(oriented), 0)
                expected_reversal = horizontal * vertical < 0
                transformed = tuple((horizontal * x, vertical * y)
                                    for x, y in contour)
                self.assertEqual(oriented,
                                 tuple(reversed(transformed))
                                 if expected_reversal else transformed)

    def test_standard_identity_is_not_crown_specific(self):
        self.assertEqual(STANDARD_PROFILE_IDS, STANDARD)
        for name in STANDARD:
            self.assertEqual(_profile(name).profile_id, name)

    def test_baseboard_standard_orientation_remains_unchanged(self):
        for name in STANDARD:
            profile = _profile(name)
            self.assertEqual(oriented_contour(profile, 1, 1), profile.contour)


class CustomCrownOrientationTests(unittest.TestCase):
    def setUp(self):
        self.definition = _definition()
        self.profile = resolve_custom_profile(
            self.definition.profile_id, 1, 1, 2.0, [self.definition])

    def test_smooth_edge_remap_for_vertical_and_double_reflection(self):
        self.assertEqual((1,), oriented_edge_indices(4, (1,), 1, 1))
        self.assertEqual((1,), oriented_edge_indices(4, (1,), -1, -1))
        self.assertEqual((1,), oriented_edge_indices(4, (1,), 1, -1))
        # An edge whose index moves demonstrates the single-reflection rule.
        self.assertEqual((2,), oriented_edge_indices(4, (0,), 1, -1))
        self.assertEqual((0,), oriented_edge_indices(4, (0,), -1, -1))

    def test_asymmetric_bezier_snapshot_uses_fully_oriented_smooth_edge(self):
        knots = (((0, 0), (.4, 0), (0, .4)),
                 ((2, 0), (2.7, .3), (1.4, 0)),
                 ((2.4, 3), (1.7, 3), (2.6, 2.2)),
                 ((0, 2), (0, 1.4), (.3, 2.5)))
        snapshot = make_snapshot("BEZIER", knots=knots,
                                 profile_id="CUSTOM-bezier")
        crown = oriented_profile_contour(snapshot.contour, 1, -1)
        indices = oriented_edge_indices(len(snapshot.contour),
                                        snapshot.smooth_edges, 1, -1)
        expected_edges = {
            frozenset(((x1, -y1), (x2, -y2)))
            for index in snapshot.smooth_edges
            for (x1, y1), (x2, y2) in ((snapshot.contour[index],
                snapshot.contour[(index + 1) % len(snapshot.contour)]),)
        }
        actual_edges = {frozenset((crown[index],
                                   crown[(index + 1) % len(crown)]))
                        for index in indices}
        self.assertEqual(expected_edges, actual_edges)

    def test_custom_scale_and_crown_orientation_preserve_offsets(self):
        crown = placement_adjusted_contour(self.profile, 1, 2.5, -1)
        self.assertAlmostEqual(min(y for _x, y in crown), 2.5 - .148)
        self.assertAlmostEqual(max(y for _x, y in crown), 2.5 - .006)
        self.assertAlmostEqual(min(x for x, _y in crown), .004)
        self.assertAlmostEqual(max(x for x, _y in crown), .038)

    def test_actual_scaled_bounds_control_crown_placement(self):
        self.assertEqual(placed_vertical_bounds(self.profile.bounds, 2.5, -1),
                         (2.352, 2.494))

    def test_cache_identity_distinguishes_both_orientation_axes_and_scale(self):
        identities = {
            derived_profile_cache_identity(self.profile, horizontal, 2.5, vertical)
            for horizontal in (-1, 1) for vertical in (-1, 1)
        }
        self.assertEqual(len(identities), 4)
        unscaled = resolve_custom_profile(
            self.definition.profile_id, 1, 1, 1.0, [self.definition])
        self.assertNotIn(derived_profile_cache_identity(unscaled, 1, 2.5, -1),
                         identities)

    def test_custom_snapshot_identity_revision_schema_are_unchanged(self):
        self.assertEqual((self.profile.profile_id, self.profile.profile_revision,
                          self.profile.schema_version),
                         ("CUSTOM-asymmetric", 1, 1))
        self.assertEqual(tuple((point.x, point.y)
                              for point in self.definition.points),
                         ((.002, .003), (.004, .021), (.013, .074), (.019, .008)))

    def test_crown_shading_matches_vertical_orientation(self):
        index = oriented_edge_indices(4, (1,), 1, -1)[0]
        oriented = oriented_profile_contour(self.profile.contour, 1, -1)
        first, second = oriented[index], oriented[(index + 1) % 4]
        base = 2.5
        quad = ((0, first[0], base + first[1]),
                (0, second[0], base + second[1]),
                (1, second[0], base + second[1]),
                (1, first[0], base + first[1]))
        path = (((0, 0, base), (1, 0, base)),)
        self.assertTrue(custom_polygon_should_be_smooth(
            self.profile, quad, 1, base + min(y for _x, y in oriented), path,
            vertical_sign=-1))

    def test_baseboard_custom_orientation_and_edge_mapping_unchanged(self):
        self.assertEqual(oriented_contour(self.profile, 1, 1),
                         self.profile.contour)
        self.assertEqual(oriented_edge_indices(4, (1,), 1, 1), (1,))


class ProfileSwitchTransactionTests(unittest.TestCase):
    def test_failed_crown_profile_switch_restores_all_profile_fields(self):
        owner = types.SimpleNamespace(**dict(zip(
            PROFILE_INSTANCE_FIELDS,
            ("SIMPLE", 1, 1, 60, 10, 5, 5, 1))))
        before = tuple(getattr(owner, field) for field in PROFILE_INSTANCE_FIELDS)
        prepare = mock.Mock(side_effect=ValueError("miter validation failed"))
        with self.assertRaisesRegex(ValueError, "miter"):
            transactional_profile_edit(
                owner, ("ROUNDED", 1, 1, 60, 10, 5, 5, 1), prepare, [])
        self.assertEqual(before, tuple(getattr(owner, field)
                                      for field in PROFILE_INSTANCE_FIELDS))
        prepare.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
