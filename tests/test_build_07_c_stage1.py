"""Build 07-C Stage 1 foundation and compatibility contracts."""

import ast
from dataclasses import fields, replace
import pathlib
import sys
import types
import unittest

ROOT = pathlib.Path(__file__).parents[1]
package = types.ModuleType("japanese_house_modeler")
package.__path__ = [str(ROOT / "japanese_house_modeler")]
sys.modules.setdefault("japanese_house_modeler", package)

from japanese_house_modeler.stair_geometry import prepare_stair_geometry
from japanese_house_modeler.stair_residential import (
    BEVEL, ROUND, SLOPED, SLOPED_CLOSED, SQUARE, STEPPED, STEPPED_CLOSED,
    ResidentialFields, StairTransitionSnapshot, assemble_material_slot_plan,
    residential_candidate, residential_fields, validate_mode_data,
    schema_version_after_residential_edit,
)
from japanese_house_modeler.stair_residential_geometry import prepare_residential_geometry


class FoundationTests(unittest.TestCase):
    def test_identifiers_exist(self):
        self.assertEqual((STEPPED_CLOSED, SLOPED_CLOSED),
                         ("STEPPED_CLOSED", "SLOPED_CLOSED"))
        self.assertEqual((STEPPED, SLOPED), ("STEPPED", "SLOPED"))
        self.assertEqual((SQUARE, BEVEL, ROUND), ("SQUARE", "BEVEL", "ROUND"))

    def test_compatibility_defaults(self):
        value = ResidentialFields()
        self.assertEqual(value.side_board_mode, STEPPED)
        self.assertEqual(value.tread_front_overhang_mm, 0.0)
        self.assertEqual(value.tread_front_edge_mode, SQUARE)
        self.assertEqual(value.tread_front_edge_size_mm, 5.0)
        self.assertEqual(value.side_board_band_width_mm, 150.0)

    def test_legacy_read_is_non_mutating(self):
        record = types.SimpleNamespace(underside_mode=STEPPED_CLOSED)
        before = vars(record).copy()
        value = residential_fields(record)
        self.assertEqual(vars(record), before)
        self.assertEqual(value.side_board_mode, STEPPED)
        self.assertEqual(value.tread_front_overhang_mm, 0.0)

    def test_storage_authority_has_no_duplicate(self):
        names = {field.name for field in fields(ResidentialFields)}
        self.assertIn("side_board_band_width_mm", names)
        self.assertNotIn("closed_body_depth_mm", names)
        self.assertNotIn("stair_body_thickness_mm", names)

    def test_rna_fields_and_identifiers_are_persistent(self):
        source = (ROOT / "japanese_house_modeler/properties.py").read_text()
        for name in ("side_board_mode", "tread_front_overhang_mm",
                     "tread_front_edge_mode", "tread_front_edge_size_mm"):
            self.assertIn(f"{name}:", source)
        for identifier in ("SLOPED_CLOSED", "STEPPED", "SLOPED", "SQUARE",
                           "BEVEL", "ROUND"):
            self.assertIn(f'"{identifier}"', source)

    def test_stage1_rejects_unimplemented_geometry(self):
        for value in (ResidentialFields(underside_mode=SLOPED_CLOSED),
                      ResidentialFields(side_board_mode=SLOPED),
                      ResidentialFields(tread_front_overhang_mm=5.0),
                      ResidentialFields(tread_front_edge_mode=BEVEL),
                      ResidentialFields(tread_front_edge_mode=ROUND)):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_mode_data("STANDARD_RESIDENTIAL", 3, value)


class GeometryCompatibilityTests(unittest.TestCase):
    args = (((0, 0), (3.6, 0)), "FORWARD", 0, 2800, 16, 900, 30, 12)

    def test_default_residential_counts_and_roles(self):
        mesh = prepare_residential_geometry(*self.args)[2]
        self.assertEqual((len(mesh.vertices), len(mesh.faces)), (620, 732))
        self.assertEqual(set(mesh.face_roles), {"TREAD", "RISER", "UNDERSIDE",
                                                "SIDE_BOARD"})

    def test_valid_body_depth_prepares_and_changes_geometry(self):
        default = prepare_residential_geometry(*self.args)[2]
        edited = prepare_residential_geometry(
            *self.args, fields=ResidentialFields(side_board_band_width_mm=120))[2]
        self.assertEqual((len(edited.vertices), len(edited.faces)), (620, 732))
        self.assertNotEqual(default.vertices, edited.vertices)

    def test_invalid_body_depth_is_rejected(self):
        for depth in (0, 175, float("nan"), float("inf"), True):
            with self.subTest(depth=depth), self.assertRaises(ValueError):
                prepare_residential_geometry(
                    *self.args, fields=ResidentialFields(
                        side_board_band_width_mm=depth))

    def test_basic_geometry_ignores_residential_fields(self):
        mesh = prepare_stair_geometry(*self.args)[2]
        self.assertEqual((len(mesh.vertices), len(mesh.faces)), (248, 186))


class SchemaSnapshotAndMaterialTests(unittest.TestCase):
    def record(self, schema=2):
        values = dict(path_points=((0, 0), (3.6, 0)), ascent_direction="FORWARD",
                      base_z_mm=0, floor_to_floor_mm=2800, riser_count=16,
                      stair_width_mm=900, tread_thickness_mm=30,
                      riser_thickness_mm=12, assembly_mode="BASIC_TREAD_RISER",
                      stair_schema_version=schema, stair_id="stable",
                      location=(0, 0, 0), rotation=(0, 0, 0), scale=(1, 1, 1))
        values.update(vars(ResidentialFields(side_board_band_width_mm=120)))
        return types.SimpleNamespace(**values)

    def test_explicit_apply_uses_schema_three(self):
        candidate = residential_candidate(self.record())
        self.assertEqual(candidate.stair_schema_version, 3)
        self.assertEqual(candidate.assembly_mode, "STANDARD_RESIDENTIAL")

    def test_schema_two_side_board_thickness_edit_stays_schema_two(self):
        before = ResidentialFields()
        after = replace(before, side_board_thickness_mm=24.0)
        self.assertEqual(
            schema_version_after_residential_edit(2, before, after), 2)

    def test_schema_two_side_board_reveal_edit_stays_schema_two(self):
        before = ResidentialFields()
        after = replace(before, side_board_reveal_mm=55.0)
        self.assertEqual(
            schema_version_after_residential_edit(2, before, after), 2)

    def test_schema_two_body_depth_edit_bumps_to_schema_three(self):
        before = ResidentialFields(side_board_band_width_mm=150.0)
        after = replace(before, side_board_band_width_mm=120.0)
        self.assertEqual(
            schema_version_after_residential_edit(2, before, after), 3)

    def test_schema_two_no_op_stays_schema_two(self):
        value = ResidentialFields()
        self.assertEqual(
            schema_version_after_residential_edit(2, value, replace(value)), 2)

    def test_schema_three_legacy_edit_stays_schema_three(self):
        before = ResidentialFields()
        after = replace(before, side_board_thickness_mm=24.0)
        self.assertEqual(
            schema_version_after_residential_edit(3, before, after), 3)

    def test_snapshot_round_trip_keeps_new_fields(self):
        snapshot = StairTransitionSnapshot.capture(self.record())
        restored = snapshot.restore_values()
        for name in ("side_board_mode", "tread_front_overhang_mm",
                     "tread_front_edge_mode", "tread_front_edge_size_mm",
                     "side_board_band_width_mm"):
            self.assertEqual(restored[name], getattr(snapshot.residential, name))

    def test_material_semantics_unchanged(self):
        wood, white = object(), object()
        plan = assemble_material_slot_plan(
            ResidentialFields(base_material=wood, riser_material=white))
        self.assertEqual(plan.slots, (wood, white))
        self.assertEqual(dict(plan.role_indices), {
            "TREAD": 0, "RISER": 1, "UNDERSIDE": 0, "SIDE_BOARD": 0})

    def test_source_schema_policy_and_thickness_ui(self):
        source = (ROOT / "japanese_house_modeler/stair_operators.py").read_text()
        self.assertIn('stair.stair_schema_version = 3', source)
        self.assertEqual(source.count('max(3, candidate["stair_schema_version"])'), 1)
        self.assertIn("schema_version_after_residential_edit(", source)
        self.assertIn('name="階段本体厚み (mm)"', source)
        self.assertNotIn("closed_body_depth_mm", source)
        self.assertNotIn("stair_body_thickness_mm", source)

    def test_identification(self):
        source = (ROOT / "japanese_house_modeler/__init__.py").read_text()
        self.assertIn('"version": (0, 7, 2)', source)
        self.assertIn("Build 07-C: Sloped Closed Underside + Straight Stair Finish Variants",
                      source)


if __name__ == "__main__":
    unittest.main()
