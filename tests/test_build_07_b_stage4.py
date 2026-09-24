"""Build 07-B Stage 4 lifecycle and full-regression contracts.

These tests deliberately remain Blender-independent.  Runtime behavior that needs
RNA, Undo, file reload, or visual inspection is specified in the companion manual.
"""

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

from japanese_house_modeler.stair_residential import (
    BASIC_TREAD_RISER, STANDARD_RESIDENTIAL, ResidentialFields,
    StairTransitionSnapshot, assemble_material_slot_plan, residential_candidate,
)
from japanese_house_modeler.stair_state import (
    GEOMETRY_MISSING, ID_CONFLICT, ID_MISSING, INVALID_CANONICAL,
    OBJECT_TYPE_CHANGED, TRANSFORM_CHANGED, duplicate_stair_ids,
    operation_allowed,
)


def function_node(tree, name):
    return next(node for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == name)


def class_node(tree, name):
    return next(node for node in tree.body
                if isinstance(node, ast.ClassDef) and node.name == name)


class SerializationContractTests(unittest.TestCase):
    def test_property_group_has_exact_stage4_residential_fields(self):
        tree = ast.parse((ROOT / "japanese_house_modeler/properties.py").read_text())
        stair = class_node(tree, "JHM_StairProperties")
        annotations = {node.target.id for node in stair.body
                       if isinstance(node, ast.AnnAssign)
                       and isinstance(node.target, ast.Name)}
        required = {
            "assembly_mode", "stair_schema_version", "underside_mode",
            "underside_thickness_mm", "left_side_board_enabled",
            "right_side_board_enabled", "side_board_thickness_mm",
            "side_board_band_width_mm", "side_board_reveal_mm",
            "base_material", "tread_material", "riser_material",
            "underside_material", "side_board_material",
        }
        self.assertTrue(required.issubset(annotations))
        self.assertNotIn("side_board_profile_width_mm", annotations)

    def test_rna_and_pure_residential_field_names_match(self):
        source = (ROOT / "japanese_house_modeler/properties.py").read_text()
        for field in fields(ResidentialFields):
            with self.subTest(field=field.name):
                self.assertIn(f"{field.name}:", source)


class CentralPolicyTests(unittest.TestCase):
    def test_normal_operations(self):
        for operation in ("EDIT_DIMENSIONS", "EDIT_PATH", "REVERSE",
                          "REGENERATE", "FINALIZE", "DELETE"):
            with self.subTest(operation=operation):
                self.assertTrue(operation_allowed(operation, ()))

    def test_mode_dependent_operations(self):
        expected = {
            "APPLY_RESIDENTIAL": (True, False),
            "EDIT_RESIDENTIAL": (False, True),
            "EDIT_MATERIALS": (False, True),
        }
        for operation, (basic, residential) in expected.items():
            self.assertEqual(operation_allowed(operation, (), BASIC_TREAD_RISER), basic)
            self.assertEqual(operation_allowed(operation, (), STANDARD_RESIDENTIAL),
                             residential)

    def test_repairable_and_nonrepairable_issues(self):
        for issue in (ID_MISSING, ID_CONFLICT, TRANSFORM_CHANGED,
                      GEOMETRY_MISSING):
            self.assertTrue(operation_allowed("REPAIR", (issue,)), issue)
        for issue in (INVALID_CANONICAL, OBJECT_TYPE_CHANGED):
            self.assertFalse(operation_allowed("REPAIR", (issue,)), issue)
        self.assertFalse(operation_allowed(
            "REPAIR", (ID_CONFLICT, INVALID_CANONICAL, GEOMETRY_MISSING)))

    def test_delete_remains_available_in_abnormal_managed_states(self):
        issues = (ID_MISSING, ID_CONFLICT, TRANSFORM_CHANGED,
                  GEOMETRY_MISSING, INVALID_CANONICAL, OBJECT_TYPE_CHANGED)
        for issue in issues:
            self.assertTrue(operation_allowed("DELETE", (issue,)), issue)


class CompatibilityAndSnapshotTests(unittest.TestCase):
    def record(self, mode=BASIC_TREAD_RISER, schema=3):
        values = dict(
            path_points=((1.0, 2.0), (4.0, 6.0)), ascent_direction="REVERSE",
            base_z_mm=425.0, floor_to_floor_mm=2800.0, riser_count=16,
            stair_width_mm=950.0, tread_thickness_mm=30.0,
            riser_thickness_mm=12.0, assembly_mode=mode,
            stair_schema_version=schema, stair_id="stable-id",
            location=(0.0, 0.0, 0.0), rotation=(0.0, 0.0, 0.0),
            scale=(1.0, 1.0, 1.0),
        )
        values.update(vars(ResidentialFields(
            underside_thickness_mm=7.0, right_side_board_enabled=False,
            side_board_reveal_mm=55.0, tread_material=object())))
        return types.SimpleNamespace(**values)

    def test_snapshot_keeps_mode_schema_id_path_transform_and_all_materials(self):
        record = self.record(STANDARD_RESIDENTIAL)
        snapshot = StairTransitionSnapshot.capture(record)
        self.assertEqual(snapshot.assembly_mode, STANDARD_RESIDENTIAL)
        self.assertEqual(snapshot.stair_schema_version, 3)
        self.assertEqual(snapshot.stair_id, "stable-id")
        self.assertEqual(snapshot.path_points, ((1.0, 2.0), (4.0, 6.0)))
        self.assertEqual(snapshot.transform,
                         ((0.0, 0.0, 0.0),) * 2 + ((1.0, 1.0, 1.0),))
        for name in vars(ResidentialFields()):
            self.assertIs(getattr(snapshot.residential, name), getattr(record, name))

    def test_explicit_conversion_only_changes_mode_and_minimum_schema(self):
        source = self.record(BASIC_TREAD_RISER, schema=3)
        candidate = residential_candidate(source)
        self.assertEqual(source.assembly_mode, BASIC_TREAD_RISER)
        self.assertEqual(candidate.assembly_mode, STANDARD_RESIDENTIAL)
        self.assertEqual(candidate.stair_schema_version, 3)
        self.assertEqual(candidate.path_points, ((1.0, 2.0), (4.0, 6.0)))
        self.assertEqual(candidate.stair_id, "stable-id")

    def test_schema_and_assembly_mode_are_independent(self):
        snapshot = StairTransitionSnapshot.capture(self.record(BASIC_TREAD_RISER, 9))
        self.assertEqual(snapshot.assembly_mode, BASIC_TREAD_RISER)
        self.assertEqual(snapshot.stair_schema_version, 9)


class MaterialLifecycleTests(unittest.TestCase):
    def test_base_fallback_and_role_override(self):
        wood, white = object(), object()
        plan = assemble_material_slot_plan(
            ResidentialFields(base_material=wood, riser_material=white))
        self.assertEqual(plan.slots, (wood, white))
        self.assertEqual(dict(plan.role_indices), {
            "TREAD": 0, "RISER": 1, "UNDERSIDE": 0, "SIDE_BOARD": 0})

    def test_tread_only_never_lends_wood_to_unassigned_roles(self):
        wood = object()
        plan = assemble_material_slot_plan(ResidentialFields(tread_material=wood))
        self.assertEqual(plan.slots, (wood, None))
        self.assertEqual(dict(plan.role_indices), {
            "TREAD": 0, "RISER": 1, "UNDERSIDE": 1, "SIDE_BOARD": 1})

    def test_all_unassigned_creates_no_substitute_slot(self):
        plan = assemble_material_slot_plan(ResidentialFields())
        self.assertEqual(plan.slots, ())
        self.assertEqual(set(dict(plan.role_indices).values()), {0})


class DuplicateIdLifecycleTests(unittest.TestCase):
    def test_only_managed_duplicates_conflict_and_survivor_id_is_stable(self):
        first = types.SimpleNamespace(is_managed=True, stair_id="X")
        second = types.SimpleNamespace(is_managed=True, stair_id="X")
        finalized = types.SimpleNamespace(is_managed=False, stair_id="X")
        self.assertEqual(duplicate_stair_ids((first, second, finalized)), {"X"})
        second.is_managed = False
        self.assertEqual(duplicate_stair_ids((first, second, finalized)), frozenset())
        self.assertEqual(first.stair_id, "X")


class TransactionStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = ROOT / "japanese_house_modeler/stair_operators.py"
        cls.source = cls.path.read_text()
        cls.tree = ast.parse(cls.source)

    def source_of(self, name):
        return ast.unparse(function_node(self.tree, name))

    def class_source(self, name):
        return ast.unparse(class_node(self.tree, name))

    def test_prepare_precedes_every_scene_mutation_and_snapshot(self):
        node = function_node(self.tree, "_transactional_update")
        statements = [ast.unparse(item) for item in node.body]
        self.assertIn("mesh_data = _prepare_candidate(candidate)", statements[1])
        prepare_index = self.source.index("mesh_data = _prepare_candidate(candidate)")
        self.assertLess(prepare_index, self.source.index("old_data = stair_object.data",
                                                        prepare_index))
        self.assertLess(prepare_index, self.source.index("bpy.data.meshes.new",
                                                        prepare_index))

    def test_commit_snapshot_covers_mesh_canonical_id_and_transform(self):
        source = self.source_of("_transactional_update")
        for text in ("old_data = stair_object.data",
                     "old_canonical = _canonical_snapshot(stair)",
                     "old_id = stair.stair_id", "tuple(stair_object.location)",
                     "tuple(stair_object.rotation_euler)",
                     "tuple(stair_object.scale)"):
            self.assertIn(text, source)

    def test_canonical_snapshot_contains_complete_residential_value_object(self):
        source = self.source_of("_canonical_snapshot")
        self.assertIn("residential=residential_fields(stair)", source)
        self.assertIn("assembly_mode=semantic_assembly_mode(stair)", source)
        self.assertIn("stair_schema_version=semantic_schema_version(stair)", source)

    def test_commit_failure_restores_every_snapshot_component(self):
        source = self.source_of("_transactional_update")
        for text in ("setattr(stair_object, 'data', old_data)",
                     "_set_canonical(stair, old_canonical)",
                     "setattr(stair, 'stair_id', old_id)",
                     "setattr(stair_object, 'location', old_transform[0])",
                     "setattr(stair_object, 'rotation_euler', old_transform[1])",
                     "setattr(stair_object, 'scale', old_transform[2])"):
            self.assertIn(text, source)

    def test_cleanup_is_best_effort_on_failure_and_after_success(self):
        source = self.source_of("_transactional_update")
        self.assertIn("_cleanup_unused_data(replacement)", source)
        self.assertIn("_cleanup_unused_data(old_data)", source)
        cleanup = self.source_of("_cleanup_unused_data")
        self.assertIn("_best_effort(remove_if_unused)", cleanup)
        best_effort = self.source_of("_best_effort")
        self.assertIn("except Exception", best_effort)
        self.assertIn("pass", best_effort)

    def test_ordinary_residential_operations_start_from_current_snapshot(self):
        classes = (
            "JHM_OT_edit_stair_dimensions", "JHM_OT_edit_stair_path",
            "JHM_OT_reverse_stair_ascent", "JHM_OT_regenerate_stair",
            "JHM_OT_edit_residential_stair", "JHM_OT_edit_stair_materials",
            "JHM_OT_repair_stair",
        )
        for name in classes:
            with self.subTest(operator=name):
                self.assertIn("_canonical_snapshot(obj.jhm_stair)",
                              self.class_source(name))

    def test_repair_changes_id_only_for_missing_or_conflict(self):
        source = self.class_source("JHM_OT_repair_stair")
        self.assertIn("ID_CONFLICT in issues or ID_MISSING in issues", source)
        self.assertNotIn("TRANSFORM_CHANGED in issues", source)
        self.assertNotIn("GEOMETRY_MISSING in issues", source)


class FinalizeDeleteAndScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / "japanese_house_modeler/stair_operators.py"
        cls.tree = ast.parse(path.read_text())

    def test_finalize_only_clears_management_marker_without_regeneration(self):
        finalize = ast.unparse(class_node(self.tree, "JHM_OT_convert_stair_mesh"))
        helper = ast.unparse(function_node(self.tree, "finalize_stair_management"))
        self.assertIn("stair.is_stair = False", helper)
        for forbidden in ("_transactional_update", "prepare_", ".data =",
                          "bpy.data.meshes.new", "bpy.data.objects.new"):
            self.assertNotIn(forbidden, finalize)

    def test_delete_is_active_object_level_only_and_leaves_data_blocks_alone(self):
        source = ast.unparse(class_node(self.tree, "JHM_OT_delete_stair"))
        self.assertIn("bpy.data.objects.remove(obj, do_unlink=True)", source)
        for forbidden in ("bpy.ops.object.delete", "bpy.data.meshes.remove",
                          "bpy.data.materials.remove"):
            self.assertNotIn(forbidden, source)

    def test_residential_default_underside_remains_stepped_closed(self):
        self.assertEqual(ResidentialFields().underside_mode, "STEPPED_CLOSED")


if __name__ == "__main__":
    unittest.main()
