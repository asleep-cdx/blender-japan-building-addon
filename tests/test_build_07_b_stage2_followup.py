"""Build 07-B Stage 2 follow-up: clean Tread rear/Riser junction."""

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

from japanese_house_modeler.stair_geometry import (
    build_riser_fragments, build_tread_fragments, prepare_stair_geometry,
    resolve_stair_layout, validate_mesh_fragments,
)
from japanese_house_modeler.stair_residential import (
    BASIC_TREAD_RISER, ResidentialFields, validate_mode_data,
)
from japanese_house_modeler.stair_residential_geometry import (
    build_residential_tread_fragments, prepare_stage2_residential_geometry,
    stepped_closure_visible_profile, stepped_underbody_inner_profile,
    stepped_underbody_profile,
)

OFF = ResidentialFields(left_side_board_enabled=False,
                        right_side_board_enabled=False)


def layout(path=((0, 0), (3.6, 0)), direction="FORWARD", base=425):
    return resolve_stair_layout(path, direction, base, 2800, 16, 900, 30, 12)


def local_x(stair, vertex):
    return ((vertex[0] - stair.lower_xy[0]) * stair.axes.forward[0]
            + (vertex[1] - stair.lower_xy[1]) * stair.axes.forward[1])


class TreadRiserJunctionTests(unittest.TestCase):
    def test_residential_treads_extend_exactly_one_riser_thickness(self):
        stair = layout()
        for ordinal, tread in enumerate(
                build_residential_tread_fragments(stair), 1):
            xs = [local_x(stair, vertex) for vertex in tread.vertices]
            self.assertAlmostEqual(min(xs), (ordinal - 1) * stair.going)
            self.assertAlmostEqual(max(xs),
                                   ordinal * stair.going
                                   + stair.riser_thickness)

    def test_basic_treads_and_accepted_mesh_counts_are_unchanged(self):
        stair, fragments, mesh = prepare_stair_geometry(
            ((0, 0), (3.6, 0)), "FORWARD", 425, 2800, 16, 900, 30, 12)
        for ordinal, tread in enumerate(build_tread_fragments(stair), 1):
            self.assertAlmostEqual(max(local_x(stair, v)
                                       for v in tread.vertices),
                                   ordinal * stair.going)
        self.assertEqual((len(mesh.vertices), len(mesh.faces)), (248, 186))
        self.assertEqual({f.part_type for f in fragments}, {"TREAD", "RISER"})

    def test_tread_and_next_riser_share_rear_plane_but_riser_bottom_is_unchanged(self):
        stair = layout()
        treads = build_residential_tread_fragments(stair)
        risers = build_riser_fragments(stair)
        for ordinal, tread in enumerate(treads, 1):
            rear = ordinal * stair.going + stair.riser_thickness
            self.assertAlmostEqual(max(local_x(stair, v) for v in tread.vertices), rear)
            next_riser = risers[ordinal]
            self.assertAlmostEqual(max(local_x(stair, v) for v in next_riser.vertices), rear)
            self.assertAlmostEqual(min(v[2] for v in next_riser.vertices),
                                   stair.base_z + ordinal * stair.actual_riser)
            self.assertNotAlmostEqual(min(v[2] for v in next_riser.vertices),
                                      stair.base_z + ordinal * stair.actual_riser
                                      - stair.tread_thickness)

    def test_inner_profile_has_horizontal_then_vertical_at_extended_rear(self):
        stair = layout()
        inner = stepped_underbody_inner_profile(stair)
        for ordinal in range(1, stair.riser_count - 1):
            rear = ordinal * stair.going + stair.riser_thickness
            underside = stair.base_z + ordinal * stair.actual_riser - stair.tread_thickness
            index = inner.index((rear, underside))
            self.assertEqual(inner[index - 1][1], underside)
            self.assertEqual(inner[index + 1][0], rear)
            self.assertNotIn((ordinal * stair.going, underside), inner)


class PreservedCorrectionContractTests(unittest.TestCase):
    def test_visible_soffit_first_bottom_and_terminations_are_unchanged(self):
        stair = layout()
        profile = stepped_underbody_profile(stair, OFF)
        self.assertEqual(profile.outer,
                         stepped_closure_visible_profile(stair, .15))
        self.assertEqual([p for p in profile.outer if p[1] == stair.base_z],
                         [(stair.riser_thickness, stair.base_z),
                          (stair.going + .15, stair.base_z)])
        self.assertAlmostEqual(max(x for x, _ in profile.polygon),
                               stair.run_length + stair.riser_thickness)
        self.assertGreaterEqual(min(z for _, z in profile.polygon), stair.base_z)

    def test_full_width_valid_mesh_for_forward_reverse_oblique_nonzero_base(self):
        for direction in ("FORWARD", "REVERSE"):
            stair, fragments, mesh = prepare_stage2_residential_geometry(
                ((1, 2), (4, 6)), direction, 425, 2800, 16, 900, 30, 12,
                fields=OFF)
            self.assertTrue(validate_mesh_fragments(fragments))
            self.assertTrue(all(math.isfinite(n) for v in mesh.vertices for n in v))
            underbody = next(f for f in fragments if f.part_type == "UNDERBODY")
            ys = [((v[0] - stair.lower_xy[0]) * stair.axes.left[0]
                   + (v[1] - stair.lower_xy[1]) * stair.axes.left[1])
                  for v in underbody.vertices]
            self.assertAlmostEqual(min(ys), -stair.width / 2)
            self.assertAlmostEqual(max(ys), stair.width / 2)
            self.assertGreaterEqual(min(v[2] for v in mesh.vertices), stair.base_z)

    def test_unused_residential_values_do_not_affect_basic(self):
        expected = prepare_stair_geometry(
            ((0, 0), (3.6, 0)), "FORWARD", 0, 2800, 16, 900, 30, 12)[2]
        unused = replace(OFF, underside_thickness_mm=-1,
                         side_board_band_width_mm=math.inf)
        actual = prepare_stair_geometry(
            ((0, 0), (3.6, 0)), "FORWARD", 0, 2800, 16, 900, 30, 12)[2]
        self.assertEqual(actual, expected)
        self.assertTrue(validate_mode_data(BASIC_TREAD_RISER, 1, unused))

    def test_stage3_public_operators_are_now_registered(self):
        source = "\n".join(path.read_text() for path in
                           (ROOT / "japanese_house_modeler").glob("*.py"))
        for operator in ("jhm.apply_residential_stair",
                         "jhm.edit_residential_stair",
                         "jhm.edit_stair_materials"):
            self.assertIn(operator, source)


if __name__ == "__main__":
    unittest.main()
