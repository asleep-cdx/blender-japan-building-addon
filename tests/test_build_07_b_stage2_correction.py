"""Regression gates for the corrected Build 07-B stepped closed body."""

from dataclasses import replace
import math
import pathlib
import sys
import types
import unittest

ROOT = pathlib.Path(__file__).parents[1]
package = types.ModuleType("japanese_house_modeler")
package.__path__ = [str(ROOT / "japanese_house_modeler")]
sys.modules.setdefault("japanese_house_modeler", package)

from japanese_house_modeler.stair_geometry import resolve_stair_layout
from japanese_house_modeler.stair_residential import (
    BASIC_TREAD_RISER, ResidentialFields, validate_mode_data,
)
from japanese_house_modeler.stair_residential_geometry import (
    build_underbody_fragment, prepare_stage2_residential_geometry,
    stepped_closure_visible_profile, stepped_underbody_profile,
)


OFF = ResidentialFields(left_side_board_enabled=False,
                        right_side_board_enabled=False)


def make_layout(path=((0, 0), (3.6, 0)), direction="FORWARD", base=0):
    return resolve_stair_layout(path, direction, base, 2800, 16, 900, 30, 12)


class CorrectedProfileTests(unittest.TestCase):
    def test_standard_profile_is_a_continuous_orthogonal_soffit(self):
        stair = make_layout()
        visible = stepped_underbody_profile(stair, OFF).outer
        self.assertEqual(visible, stepped_closure_visible_profile(stair, .15))
        self.assertGreater(len(visible), 4)
        for first, second in zip(visible, visible[1:]):
            self.assertTrue(first[0] == second[0] or first[1] == second[1])

    def test_first_step_bottom_is_one_flat_segment_without_notch(self):
        stair = make_layout()
        visible = stepped_underbody_profile(stair, OFF).outer
        base_points = [point for point in visible if point[1] == stair.base_z]
        self.assertEqual(base_points, [(stair.riser_thickness, stair.base_z),
                                      (stair.going + .15, stair.base_z)])
        self.assertEqual(visible[2][0], visible[1][0])
        self.assertGreater(visible[2][1], stair.base_z)

    def test_no_profile_point_is_below_nonzero_base(self):
        stair = make_layout(base=425)
        profile = stepped_underbody_profile(stair, OFF)
        self.assertAlmostEqual(min(z for _, z in profile.polygon), .425)

    def test_thickness_does_not_move_visible_silhouette(self):
        stair = make_layout()
        expected = stepped_underbody_profile(stair, OFF).outer
        for thickness in (1.0, 9.5, 50.0, 1000.0):
            fields = replace(OFF, underside_thickness_mm=thickness)
            self.assertEqual(stepped_underbody_profile(stair, fields).outer,
                             expected)

    def test_closure_depth_drives_visible_silhouette(self):
        stair = make_layout()
        shallow = stepped_underbody_profile(
            stair, replace(OFF, side_board_band_width_mm=100)).outer
        self.assertEqual(shallow[1], (stair.going + .1, stair.base_z))
        self.assertEqual(shallow[2][1], stair.base_z + 2 * stair.actual_riser - .1)

    def test_upper_termination_stops_at_final_riser_outer_face(self):
        stair = make_layout()
        visible = stepped_underbody_profile(stair, OFF).outer
        self.assertAlmostEqual(visible[-1][0],
                               stair.run_length + stair.riser_thickness)
        self.assertLessEqual(max(x for x, _ in visible),
                             stair.run_length + stair.riser_thickness)


class CorrectedSolidTests(unittest.TestCase):
    def test_body_is_closed_and_spans_full_width(self):
        stair = make_layout()
        fragment = build_underbody_fragment(stair, OFF)
        forward, left = stair.axes.forward, stair.axes.left
        local_y = [((vertex[0] - stair.lower_xy[0]) * left[0]
                    + (vertex[1] - stair.lower_xy[1]) * left[1])
                   for vertex in fragment.vertices]
        self.assertAlmostEqual(min(local_y), -stair.width / 2)
        self.assertAlmostEqual(max(local_y), stair.width / 2)
        self.assertTrue(fragment.faces)

    def test_side_board_flags_do_not_control_body_profile(self):
        stair = make_layout()
        profiles = []
        for left in (False, True):
            for right in (False, True):
                fields = replace(OFF, left_side_board_enabled=left,
                                 right_side_board_enabled=right)
                profiles.append(stepped_underbody_profile(stair, fields).polygon)
        self.assertTrue(all(profile == profiles[0] for profile in profiles))

    def test_forward_reverse_oblique_and_nonzero_base(self):
        path = ((1, 2), (4, 6))
        forward = build_underbody_fragment(make_layout(path, "FORWARD", 300), OFF)
        reverse = build_underbody_fragment(make_layout(path, "REVERSE", 300), OFF)
        self.assertAlmostEqual(min(v[2] for v in forward.vertices), .3)
        self.assertAlmostEqual(min(v[2] for v in reverse.vertices), .3)
        self.assertNotEqual(forward.vertices, reverse.vertices)
        self.assertTrue(all(math.isfinite(value) for fragment in (forward, reverse)
                            for vertex in fragment.vertices for value in vertex))

    def test_invalid_thickness_and_depth_reject_before_candidate_return(self):
        common = dict(points=((0, 0), (3.6, 0)), ascent_direction="FORWARD",
                      base_z_mm=0, floor_to_floor_mm=2800, riser_count=16,
                      stair_width_mm=900, tread_thickness_mm=30,
                      riser_thickness_mm=12)
        for fields in (replace(OFF, underside_thickness_mm=0),
                       replace(OFF, underside_thickness_mm=math.nan),
                       replace(OFF, side_board_band_width_mm=175),
                       replace(OFF, side_board_band_width_mm=math.inf)):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                prepare_stage2_residential_geometry(**common, fields=fields)


class CompatibilityAndScopeTests(unittest.TestCase):
    def test_basic_still_ignores_unused_residential_values(self):
        invalid = replace(OFF, underside_thickness_mm=-1,
                          side_board_band_width_mm=math.inf)
        self.assertTrue(validate_mode_data(BASIC_TREAD_RISER, 1, invalid))

    def test_existing_stage2_fragment_contract_is_preserved(self):
        _, fragments, mesh = prepare_stage2_residential_geometry(
            ((0, 0), (3.6, 0)), "FORWARD", 0, 2800, 16, 900, 30, 12,
            fields=OFF)
        self.assertEqual(sum(f.part_type == "UNDERBODY" for f in fragments), 1)
        self.assertEqual(sum(f.part_type == "TREAD" for f in fragments), 15)
        self.assertEqual(sum(f.part_type == "RISER" for f in fragments), 16)
        self.assertTrue(mesh.vertices and mesh.faces)

    def test_stage3_public_functionality_remains_absent(self):
        source = "\n".join(path.read_text() for path in
                           (ROOT / "japanese_house_modeler").glob("*.py"))
        for operator in ("jhm.apply_residential_stair",
                         "jhm.edit_residential_stair",
                         "jhm.edit_stair_materials"):
            self.assertNotIn(operator, source)


if __name__ == "__main__":
    unittest.main()
