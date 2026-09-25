"""Build 07-C Stage 4 lifecycle, rollback, and final-regression contracts.

The suite is intentionally Blender-independent.  RNA Undo, full process reload,
and practical placement are covered by ``BUILD_07_C_STAGE4_RUNTIME_TEST.md``.
"""

import ast
from dataclasses import fields, replace
import math
import pathlib
import sys
import types
import unittest

ROOT = pathlib.Path(__file__).parents[1]
package = types.ModuleType("japanese_house_modeler")
package.__path__ = [str(ROOT / "japanese_house_modeler")]
sys.modules.setdefault("japanese_house_modeler", package)

from japanese_house_modeler.stair_geometry import validate_mesh_fragments
from japanese_house_modeler.stair_residential import (
    BASIC_TREAD_RISER, BEVEL, MATERIAL_ROLES, ROUND, SLOPED,
    SLOPED_CLOSED, SQUARE, STANDARD_RESIDENTIAL, STEPPED,
    STEPPED_CLOSED, ResidentialFields, StairTransitionSnapshot,
    assemble_material_slot_plan, new_residential_fields,
)
from japanese_house_modeler.stair_residential_geometry import (
    prepare_residential_geometry,
)
from japanese_house_modeler.stair_state import (
    GEOMETRY_MISSING, ID_CONFLICT, ID_MISSING, INVALID_CANONICAL,
    OBJECT_TYPE_CHANGED, TRANSFORM_CHANGED, duplicate_stair_ids,
    operation_allowed,
)

ARGS = (((0.0, 0.0), (3.6, 0.0)), "FORWARD", 125, 2800, 16, 900, 30, 12)


def function_node(tree, name):
    return next(node for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name == name)


def class_node(tree, name):
    return next(node for node in tree.body
                if isinstance(node, ast.ClassDef) and node.name == name)


class CompleteSnapshotTests(unittest.TestCase):
    def record(self):
        material_values = {name: object() for name in (
            "base_material", "tread_material", "riser_material",
            "underside_material", "side_board_material")}
        residential = ResidentialFields(
            underside_mode=SLOPED_CLOSED, underside_thickness_mm=11.0,
            side_board_band_width_mm=145.0, left_side_board_enabled=True,
            right_side_board_enabled=False, side_board_mode=SLOPED,
            side_board_thickness_mm=20.0, side_board_reveal_mm=42.0,
            tread_front_overhang_mm=8.0, tread_front_edge_mode=ROUND,
            tread_front_edge_size_mm=4.0, **material_values)
        return types.SimpleNamespace(
            path_points=((1.0, 2.0), (4.0, 6.0)),
            ascent_direction="REVERSE", base_z_mm=375.0,
            floor_to_floor_mm=2800.0, riser_count=16,
            stair_width_mm=950.0, tread_thickness_mm=32.0,
            riser_thickness_mm=13.0, assembly_mode=STANDARD_RESIDENTIAL,
            stair_schema_version=3, stair_id="07-c-stable-id",
            location=(0.0, 0.0, 0.0), rotation=(0.0, 0.0, 0.0),
            scale=(1.0, 1.0, 1.0), **vars(residential))

    def test_snapshot_and_restore_cover_every_stage3_field(self):
        record = self.record()
        snapshot = StairTransitionSnapshot.capture(record)
        restored = snapshot.restore_values()
        required = {field.name for field in fields(ResidentialFields)} | {
            "path_points", "ascent_direction", "base_z_mm",
            "floor_to_floor_mm", "riser_count", "stair_width_mm",
            "tread_thickness_mm", "riser_thickness_mm", "assembly_mode",
            "stair_schema_version", "stair_id", "transform"}
        self.assertEqual(set(restored), required)
        material_names = {field.name for field in fields(ResidentialFields)
                          if field.name.endswith("_material")}
        for name in required - {"transform"}:
            assertion = self.assertIs if name in material_names else self.assertEqual
            assertion(restored[name], getattr(record, name))
        self.assertEqual(restored["transform"],
                         (record.location, record.rotation, record.scale))

    def test_rna_declares_every_residential_snapshot_field(self):
        tree = ast.parse((ROOT / "japanese_house_modeler/properties.py").read_text())
        stair = class_node(tree, "JHM_StairProperties")
        annotations = {node.target.id for node in stair.body
                       if isinstance(node, ast.AnnAssign)
                       and isinstance(node.target, ast.Name)}
        self.assertTrue({field.name for field in fields(ResidentialFields)}
                        .issubset(annotations))


class TransactionAndOperatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "japanese_house_modeler/stair_operators.py").read_text()
        cls.tree = ast.parse(cls.source)

    def function_source(self, name):
        return ast.unparse(function_node(self.tree, name))

    def class_source(self, name):
        return ast.unparse(class_node(self.tree, name))

    def test_prepare_precedes_snapshot_and_every_scene_mutation(self):
        node = function_node(self.tree, "_transactional_update")
        statements = [ast.unparse(item) for item in node.body]
        self.assertEqual(statements[1], "mesh_data = _prepare_candidate(candidate)")
        source = self.function_source("_transactional_update")
        prepare = source.index("mesh_data = _prepare_candidate(candidate)")
        for mutation in ("old_data = stair_object.data", "bpy.data.meshes.new"):
            self.assertLess(prepare, source.index(mutation))

    def test_commit_failure_restores_mesh_state_id_and_transform(self):
        source = self.function_source("_transactional_update")
        expected = (
            "old_data = stair_object.data",
            "old_canonical = _canonical_snapshot(stair)",
            "old_id = stair.stair_id", "old_transform =",
            "setattr(stair_object, 'data', old_data)",
            "_set_canonical(stair, old_canonical)",
            "setattr(stair, 'stair_id', old_id)",
            "setattr(stair_object, 'location', old_transform[0])",
            "setattr(stair_object, 'rotation_euler', old_transform[1])",
            "setattr(stair_object, 'scale', old_transform[2])")
        for contract in expected:
            with self.subTest(contract=contract):
                self.assertIn(contract, source)

    def test_canonical_snapshot_and_restore_use_complete_value_object(self):
        snapshot = self.function_source("_canonical_snapshot")
        restore = self.function_source("_set_canonical")
        self.assertIn("residential=residential_fields(stair)", snapshot)
        self.assertIn("assembly_mode=semantic_assembly_mode(stair)", snapshot)
        self.assertIn("stair_schema_version=semantic_schema_version(stair)", snapshot)
        self.assertIn("for name, value in vars(values['residential']).items()", restore)

    def test_every_ui_lifecycle_operator_is_one_undoable_operation(self):
        operators = (
            "JHM_OT_edit_stair_dimensions", "JHM_OT_edit_stair_path",
            "JHM_OT_reverse_stair_ascent", "JHM_OT_regenerate_stair",
            "JHM_OT_apply_residential_stair", "JHM_OT_edit_residential_stair",
            "JHM_OT_edit_stair_materials", "JHM_OT_repair_stair",
            "JHM_OT_convert_stair_mesh", "JHM_OT_delete_stair")
        for operator in operators:
            with self.subTest(operator=operator):
                self.assertIn("bl_options = {'REGISTER', 'UNDO'}",
                              self.class_source(operator))

    def test_repair_changes_id_only_for_an_id_issue(self):
        source = self.class_source("JHM_OT_repair_stair")
        self.assertIn("ID_CONFLICT in issues or ID_MISSING in issues", source)
        self.assertNotIn("TRANSFORM_CHANGED in issues", source)
        self.assertNotIn("GEOMETRY_MISSING in issues", source)

    def test_finalize_does_not_regenerate_or_replace_mesh(self):
        source = self.class_source("JHM_OT_convert_stair_mesh")
        helper = self.function_source("finalize_stair_management")
        self.assertIn("stair.is_stair = False", helper)
        for forbidden in ("_transactional_update", "_prepare_candidate",
                          ".data =", "bpy.data.meshes.new"):
            self.assertNotIn(forbidden, source)

    def test_delete_is_active_object_only_and_preserves_datablocks(self):
        source = self.class_source("JHM_OT_delete_stair")
        self.assertIn("bpy.data.objects.remove(obj, do_unlink=True)", source)
        for forbidden in ("bpy.ops.object.delete", "bpy.data.meshes.remove",
                          "bpy.data.materials.remove"):
            self.assertNotIn(forbidden, source)


class InvalidCandidateAtomicityTests(unittest.TestCase):
    def assert_invalid(self, values):
        with self.assertRaises(ValueError):
            prepare_residential_geometry(*ARGS, fields=values)

    def test_all_stage4_invalid_candidates_fail_during_pure_prepare(self):
        base = replace(new_residential_fields(), side_board_reveal_mm=40.0)
        cases = (
            replace(base, side_board_band_width_mm=0.0),
            replace(base, tread_front_overhang_mm=225.0),
            replace(base, tread_front_overhang_mm=41.0),
            replace(base, tread_front_edge_mode=BEVEL,
                    tread_front_edge_size_mm=0.0),
            replace(base, tread_front_edge_mode=BEVEL,
                    tread_front_edge_size_mm=15.0),
            replace(base, tread_front_edge_mode=ROUND,
                    tread_front_edge_size_mm=15.0),
            replace(base, tread_front_edge_mode=BEVEL,
                    tread_front_edge_size_mm=6.0),
            replace(base, tread_front_edge_mode=ROUND,
                    tread_front_edge_size_mm=6.0))
        for values in cases:
            with self.subTest(values=values):
                self.assert_invalid(values)


class IdentityAndPolicyTests(unittest.TestCase):
    def test_duplicate_policy_ignores_finalized_object_and_keeps_survivor(self):
        survivor = types.SimpleNamespace(is_managed=True, stair_id="same")
        conflict = types.SimpleNamespace(is_managed=True, stair_id="same")
        finalized = types.SimpleNamespace(is_managed=False, stair_id="same")
        self.assertEqual(duplicate_stair_ids((survivor, conflict, finalized)),
                         {"same"})
        conflict.stair_id = "repaired"
        self.assertEqual(duplicate_stair_ids((survivor, conflict, finalized)),
                         frozenset())
        self.assertEqual(survivor.stair_id, "same")

    def test_repair_and_abnormal_delete_central_policy(self):
        for issue in (ID_MISSING, ID_CONFLICT, TRANSFORM_CHANGED,
                      GEOMETRY_MISSING):
            self.assertTrue(operation_allowed("REPAIR", (issue,)))
        for issue in (INVALID_CANONICAL, OBJECT_TYPE_CHANGED):
            self.assertFalse(operation_allowed("REPAIR", (issue,)))
        for issue in (ID_MISSING, ID_CONFLICT, TRANSFORM_CHANGED,
                      GEOMETRY_MISSING, INVALID_CANONICAL,
                      OBJECT_TYPE_CHANGED):
            self.assertTrue(operation_allowed("DELETE", (issue,)))


class MaterialRegressionTests(unittest.TestCase):
    def test_exact_roles_and_no_nosing_role(self):
        self.assertEqual(MATERIAL_ROLES,
                         ("TREAD", "RISER", "UNDERSIDE", "SIDE_BOARD"))
        self.assertNotIn("NOSING", MATERIAL_ROLES)

    def test_fallback_partial_unassigned_all_unassigned_and_dedup(self):
        base, tread = object(), object()
        fallback = assemble_material_slot_plan(
            ResidentialFields(base_material=base, tread_material=tread))
        self.assertEqual(fallback.slots, (tread, base))
        partial = assemble_material_slot_plan(
            ResidentialFields(tread_material=tread))
        self.assertEqual(partial.slots, (tread, None))
        self.assertEqual(assemble_material_slot_plan(ResidentialFields()).slots, ())
        dedup = assemble_material_slot_plan(ResidentialFields(
            base_material=base, tread_material=base, riser_material=base,
            underside_material=base, side_board_material=base))
        self.assertEqual(dedup.slots, (base,))
        self.assertEqual(set(dict(dedup.role_indices).values()), {0})

    def test_profiled_nosing_and_sloped_parts_keep_established_roles(self):
        values = replace(new_residential_fields(), underside_mode=SLOPED_CLOSED,
                         side_board_mode=SLOPED,
                         tread_front_edge_mode=ROUND,
                         tread_front_edge_size_mm=4.0)
        _layout, fragments, mesh = prepare_residential_geometry(*ARGS, fields=values)
        self.assertEqual(set(mesh.face_roles), set(MATERIAL_ROLES))
        self.assertEqual({fragment.part_type for fragment in fragments},
                         {"TREAD", "RISER", "UNDERBODY", "SIDE_BOARD"})
        tread_parts = [fragment for fragment in fragments
                       if fragment.part_type == "TREAD"]
        self.assertEqual(len(tread_parts), ARGS[4])  # N-1 treads + arrival cap


class GeometryAndLegacyRegressionTests(unittest.TestCase):
    def test_four_representative_07c_combinations_are_closed_and_bounded(self):
        variants = (
            (STEPPED_CLOSED, STEPPED, SQUARE),
            (STEPPED_CLOSED, SLOPED, BEVEL),
            (SLOPED_CLOSED, STEPPED, ROUND),
            (SLOPED_CLOSED, SLOPED, ROUND))
        for underside, board, edge in variants:
            values = replace(new_residential_fields(), underside_mode=underside,
                             side_board_mode=board, tread_front_edge_mode=edge,
                             tread_front_edge_size_mm=4.0)
            layout, fragments, mesh = prepare_residential_geometry(*ARGS, fields=values)
            with self.subTest(underside=underside, board=board, edge=edge):
                self.assertTrue(validate_mesh_fragments(fragments))
                self.assertTrue(all(math.isfinite(value)
                                    for vertex in mesh.vertices for value in vertex))
                self.assertGreater(len(mesh.faces), 0)
                self.assertGreaterEqual(min(v[2] for v in mesh.vertices), layout.base_z)
                body_and_boards = [f for f in fragments
                                   if f.part_type in {"UNDERSIDE", "SIDE_BOARD"}]
                self.assertLessEqual(max(v[0] for f in body_and_boards
                                         for v in f.vertices),
                                     layout.run_length + layout.riser_thickness)

    def test_schema2_zero_nosing_exact_07b_fixture(self):
        _layout, fragments, mesh = prepare_residential_geometry(
            *ARGS, assembly_mode=STANDARD_RESIDENTIAL,
            stair_schema_version=2, fields=ResidentialFields())
        self.assertTrue(validate_mesh_fragments(fragments))
        self.assertEqual((len(mesh.vertices), len(mesh.faces)), (620, 732))

    def test_basic_source_has_no_residential_production_dependency(self):
        source = (ROOT / "japanese_house_modeler/stair_geometry.py").read_text()
        for name in ("underside_mode", "side_board_mode",
                     "tread_front_overhang_mm", "tread_front_edge_mode"):
            self.assertNotIn(name, source)
        self.assertEqual(BASIC_TREAD_RISER, "BASIC_TREAD_RISER")

    def test_runtime_plan_has_eight_grouped_tests_and_isolation_placement(self):
        runtime = (ROOT / "BUILD_07_C_STAGE4_RUNTIME_TEST.md").read_text()
        self.assertEqual(sum(line.startswith("## Test ")
                             for line in runtime.splitlines()), 8)
        for required in ("Ctrl+Z", "Ctrl+Shift+Z", "fully exit Blender",
                         "ID_CONFLICT", "GEOMETRY_MISSING", "Finalize",
                         "620", "732", "248", "186", "Wall", "Finish",
                         "2800", "upper-floor-like", "NOT ACCEPTED"):
            with self.subTest(required=required):
                self.assertIn(required, runtime)


if __name__ == "__main__":
    unittest.main()
