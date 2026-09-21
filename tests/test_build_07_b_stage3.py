"""Build 07-B Stage 3 side-board, material, and activation coverage."""
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

from japanese_house_modeler.stair_geometry import polygon_signed_area, resolve_stair_layout, validate_mesh_fragments
from japanese_house_modeler.stair_residential import (ResidentialFields, derive_material_slot_plan,
    validate_side_board_dimensions)
from japanese_house_modeler.stair_residential_geometry import (build_side_board_fragment,
    prepare_residential_geometry, side_board_profile, side_board_reference_profile)
from japanese_house_modeler.stair_state import INVALID_CANONICAL, StairState, diagnose_stair


def layout(path=((0, 0), (3.6, 0)), direction="FORWARD", base=0):
    return resolve_stair_layout(path, direction, base, 2800, 16, 900, 30, 12)


def prepare(fields=ResidentialFields(), path=((0, 0), (3.6, 0)), direction="FORWARD"):
    return prepare_residential_geometry(path, direction, 0, 2800, 16, 900, 30, 12,
                                        fields=fields)


class SideBoardProfileTests(unittest.TestCase):
    def test_reference_is_exact_analytical_walking_profile(self):
        points = side_board_reference_profile(layout(base=425))
        expected = ((0, .425), (0, .6), (.24, .6), (.24, .775), (.48, .775))
        for actual, wanted in zip(points, expected):
            self.assertAlmostEqual(actual[0], wanted[0]); self.assertAlmostEqual(actual[1], wanted[1])
        self.assertEqual(len(points), 32)
        self.assertAlmostEqual(points[-1][0], 3.6)
        self.assertAlmostEqual(points[-1][1], 3.225)

    def test_complete_band_uses_segment_offsets_and_intersections(self):
        result = side_board_profile(layout())
        self.assertTrue(any(math.isclose(x, .15) and math.isclose(z, .025)
                            for x, z in result.complete_polygon))
        self.assertTrue(any(math.isclose(x, .39) and math.isclose(z, .025)
                            for x, z in result.complete_polygon))
        self.assertGreater(polygon_signed_area(result.complete_polygon), 0)

    def test_whole_polygon_is_clipped_at_base_and_l_plus_r(self):
        result = side_board_profile(layout())
        self.assertAlmostEqual(min(z for _x, z in result.polygon), 0)
        self.assertAlmostEqual(max(x for x, _z in result.polygon), 3.612)
        self.assertTrue(all(x <= 3.612 + 1e-12 for x, _z in result.polygon))
        self.assertGreater(polygon_signed_area(result.polygon), 0)
        boundary = [z for x, z in result.polygon if math.isclose(x, 3.612)]
        self.assertGreater(max(boundary) - min(boundary), .3)


class DimensionAndAssemblyTests(unittest.TestCase):
    def test_feature_aware_range(self):
        stair = layout()
        for changes in (dict(side_board_thickness_mm=0), dict(side_board_band_width_mm=0),
                        dict(side_board_thickness_mm=math.inf), dict(side_board_band_width_mm=175)):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate_side_board_dimensions(ResidentialFields(**changes), stair.actual_riser, stair.going)
        off = ResidentialFields(left_side_board_enabled=False, right_side_board_enabled=False,
                                side_board_band_width_mm=999)
        self.assertEqual(validate_side_board_dimensions(off, stair.actual_riser, stair.going)[1], .999)

    def test_four_enable_combinations_and_outer_width(self):
        for left, right, count in ((True, True, 2), (True, False, 1),
                                   (False, True, 1), (False, False, 0)):
            fields = ResidentialFields(left_side_board_enabled=left,
                                       right_side_board_enabled=right)
            stair, fragments, _mesh = prepare(fields)
            boards = [f for f in fragments if f.part_type == "SIDE_BOARD"]
            self.assertEqual(len(boards), count)
            if left and right:
                ys = [v[1] for f in fragments for v in f.vertices]
                self.assertAlmostEqual(max(ys) - min(ys), .936)
            self.assertEqual(stair.canonical_path, ((0.0, 0.0), (3.6, 0.0)))

    def test_each_side_is_an_independent_closed_solid(self):
        for side in ("LEFT", "RIGHT"):
            fragment = build_side_board_fragment(layout(), side)
            self.assertTrue(validate_mesh_fragments((fragment,)))
            self.assertEqual(fragment.ordinal, 1 if side == "LEFT" else 2)
            self.assertLess(min(v[2] for v in fragment.vertices), .03)

    def test_oblique_reverse_swaps_uphill_relative_world_side(self):
        path = ((1, 2), (4, 6))
        forward = build_side_board_fragment(layout(path, "FORWARD"), "LEFT")
        reverse = build_side_board_fragment(layout(path, "REVERSE"), "LEFT")
        self.assertNotEqual(forward.vertices, reverse.vertices)
        fcenter = tuple(sum(v[i] for v in forward.vertices) / len(forward.vertices) for i in range(2))
        rcenter = tuple(sum(v[i] for v in reverse.vertices) / len(reverse.vertices) for i in range(2))
        self.assertNotEqual(fcenter, rcenter)

    def test_mesh_face_roles_cover_every_polygon(self):
        _layout, _fragments, mesh = prepare()
        self.assertEqual(len(mesh.faces), len(mesh.face_roles))
        self.assertEqual(set(mesh.face_roles), {"TREAD", "RISER", "UNDERBODY", "SIDE_BOARD"})


class MaterialPlanTests(unittest.TestCase):
    def test_base_partial_override_and_identity_dedupe(self):
        wood, white = object(), object()
        plan = derive_material_slot_plan(ResidentialFields(base_material=wood,
                                                            riser_material=white))
        self.assertEqual(plan.slots, (wood, white))
        self.assertEqual([plan.index_for(r) for r in ("TREAD", "RISER", "UNDERSIDE", "SIDE_BOARD")],
                         [0, 1, 0, 0])

    def test_mixed_unassigned_has_one_real_empty_slot_without_leakage(self):
        wood = object()
        plan = derive_material_slot_plan(ResidentialFields(tread_material=wood))
        self.assertEqual(plan.slots, (wood, None))
        self.assertEqual(plan.index_for("TREAD"), 0)
        for role in ("RISER", "UNDERSIDE", "SIDE_BOARD"):
            self.assertEqual(plan.index_for(role), 1)

    def test_all_unassigned_uses_zero_slots(self):
        plan = derive_material_slot_plan(ResidentialFields())
        self.assertEqual(plan.slots, ())
        self.assertTrue(all(index == 0 for _role, index in plan.role_indices))


class ValidationAndActivationTests(unittest.TestCase):
    def test_invalid_residential_band_is_invalid_canonical_but_basic_ignores_it(self):
        common = dict(stair_id="id", path_points=((0, 0), (3.6, 0)), ascent_direction="FORWARD",
                      base_z_mm=0, floor_to_floor_mm=2800, riser_count=16, stair_width_mm=900,
                      tread_thickness_mm=30, riser_thickness_mm=12,
                      residential=ResidentialFields(side_board_band_width_mm=175))
        self.assertNotIn(INVALID_CANONICAL, diagnose_stair(StairState(**common)))
        self.assertIn(INVALID_CANONICAL, diagnose_stair(StairState(
            **common, assembly_mode="STANDARD_RESIDENTIAL", stair_schema_version=2)))

    def test_public_operators_are_registered_and_creation_prepares_residential(self):
        operators = (ROOT / "japanese_house_modeler" / "stair_operators.py").read_text()
        registration = (ROOT / "japanese_house_modeler" / "__init__.py").read_text()
        for name in ("JHM_OT_apply_residential_stair", "JHM_OT_edit_residential_stair",
                     "JHM_OT_edit_stair_materials"):
            self.assertIn(name, operators); self.assertIn(name, registration)
        self.assertIn("prepare_residential_geometry", operators)

    def test_stage4_features_are_not_present(self):
        production = "\n".join(path.read_text() for path in
                               (ROOT / "japanese_house_modeler").glob("stair*.py"))
        for forbidden in ("SLOPED_CLOSED", "anti_slip_groove", "winder"):
            self.assertNotIn(forbidden, production)


if __name__ == "__main__":
    unittest.main()
