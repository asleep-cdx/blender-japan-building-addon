"""Pure and structural coverage for Build 07-A Stage 4."""

import ast
import pathlib
import sys
import types
import unittest

ROOT = pathlib.Path(__file__).parents[1]
package = types.ModuleType("japanese_house_modeler")
package.__path__ = [str(ROOT / "japanese_house_modeler")]
sys.modules.setdefault("japanese_house_modeler", package)

from japanese_house_modeler.stair_state import (
    GEOMETRY_MISSING, ID_CONFLICT, ID_MISSING, INVALID_CANONICAL,
    OBJECT_TYPE_CHANGED, TRANSFORM_CHANGED, duplicate_stair_ids,
    operation_allowed,
)


class PropertySerializationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "japanese_house_modeler" / "properties.py").read_text()
        cls.tree = ast.parse(cls.source)

    def class_source(self, name):
        node = next(node for node in self.tree.body
                    if isinstance(node, ast.ClassDef) and node.name == name)
        return ast.unparse(node)

    def test_serialization_facing_defaults(self):
        expected = {
            "base_z_mm": "0.0", "floor_to_floor_mm": "2800.0",
            "riser_count": "16", "stair_width_mm": "900.0",
            "tread_thickness_mm": "30.0", "riser_thickness_mm": "12.0",
            "ascent_direction": "'FORWARD'",
        }
        for class_name in ("JHM_NewStairDefaults", "JHM_StairProperties"):
            source = self.class_source(class_name)
            for name, value in expected.items():
                with self.subTest(class_name=class_name, property=name):
                    self.assertIn(name, source)
                    self.assertIn(f"default={value}", source)

    def test_managed_marker_and_uuid_storage_defaults(self):
        source = self.class_source("JHM_StairProperties")
        self.assertIn("is_stair: bpy.props.BoolProperty(default=False", source)
        self.assertIn("stair_id: bpy.props.StringProperty(default=''", source)
        self.assertIn("path_points", source)


class LifecyclePolicyTests(unittest.TestCase):
    ABNORMAL = (ID_MISSING, ID_CONFLICT, TRANSFORM_CHANGED,
                INVALID_CANONICAL, GEOMETRY_MISSING, OBJECT_TYPE_CHANGED)

    def test_finalize_is_normal_only(self):
        self.assertTrue(operation_allowed("FINALIZE", ()))
        for issue in self.ABNORMAL:
            with self.subTest(issue=issue):
                self.assertFalse(operation_allowed("FINALIZE", (issue,)))

    def test_delete_allows_normal_and_every_abnormal_state(self):
        self.assertTrue(operation_allowed("DELETE", ()))
        for issue in self.ABNORMAL:
            with self.subTest(issue=issue):
                self.assertTrue(operation_allowed("DELETE", (issue,)))

    def test_duplicate_conflict_disappears_only_when_record_is_removed(self):
        record = lambda managed=True: types.SimpleNamespace(
            is_managed=managed, stair_id="stable-id")
        first, duplicate = record(), record()
        self.assertEqual(duplicate_stair_ids((first, duplicate)), {"stable-id"})
        self.assertEqual(duplicate_stair_ids((first,)), frozenset())
        self.assertEqual(first.stair_id, "stable-id")

    def test_finalized_records_are_excluded_without_uuid_rewrite(self):
        managed = types.SimpleNamespace(is_managed=True, stair_id="stable-id")
        finalized = types.SimpleNamespace(is_managed=False, stair_id="stable-id")
        self.assertEqual(duplicate_stair_ids((managed, finalized)), frozenset())
        self.assertEqual(finalized.stair_id, "stable-id")


class OperatorStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "japanese_house_modeler" /
                      "stair_operators.py").read_text()
        cls.tree = ast.parse(cls.source)
        cls.init_source = (ROOT / "japanese_house_modeler" / "__init__.py").read_text()

    def class_source(self, name):
        node = next(node for node in self.tree.body
                    if isinstance(node, ast.ClassDef) and node.name == name)
        return ast.unparse(node)

    def test_finalize_operator_is_registered_and_undoable(self):
        source = self.class_source("JHM_OT_convert_stair_mesh")
        self.assertIn("jhm.convert_stair_mesh", source)
        self.assertIn("{'REGISTER', 'UNDO'}", source)
        self.assertIn("operation = 'FINALIZE'", source)
        self.assertIn("_require_allowed(context)", source)
        self.assertIn("finalize_stair_management(obj.jhm_stair)", source)
        self.assertIn("JHM_OT_convert_stair_mesh", self.init_source)

    def test_finalize_transition_changes_only_management_marker(self):
        function = next(node for node in self.tree.body
                        if isinstance(node, ast.FunctionDef)
                        and node.name == "finalize_stair_management")
        source = ast.unparse(function)
        self.assertIn("stair.is_stair = False", source)
        self.assertNotIn("stair_id", source)
        self.assertNotIn("path_points", source)

    def test_finalize_does_not_replace_or_regenerate_any_data(self):
        source = self.class_source("JHM_OT_convert_stair_mesh")
        for forbidden in ("bpy.data.objects.new", "bpy.data.meshes.new",
                          "prepare_stair_geometry", ".data =", "materials",
                          "location =", "rotation_euler =", "scale ="):
            self.assertNotIn(forbidden, source)

    def test_delete_operator_is_registered_active_only_and_undoable(self):
        source = self.class_source("JHM_OT_delete_stair")
        self.assertIn("jhm.delete_stair", source)
        self.assertIn("{'REGISTER', 'UNDO'}", source)
        self.assertIn("operation = 'DELETE'", source)
        self.assertIn("_require_allowed(context)", source)
        self.assertIn("bpy.data.objects.remove(obj, do_unlink=True)", source)
        self.assertNotIn("bpy.ops.object.delete", source)
        self.assertIn("JHM_OT_delete_stair", self.init_source)

    def test_delete_does_not_assume_mesh_or_remove_shared_data(self):
        source = self.class_source("JHM_OT_delete_stair")
        self.assertNotIn("obj.type", source)
        self.assertNotIn("obj.data", source)
        self.assertNotIn("bpy.data.meshes.remove", source)
        self.assertNotIn("bpy.data.materials.remove", source)

    def test_selected_target_requires_active_selected_managed_object(self):
        function = next(node for node in self.tree.body
                        if isinstance(node, ast.FunctionDef)
                        and node.name == "_selected_stair")
        source = ast.unparse(function)
        self.assertIn("context.active_object", source)
        self.assertIn("obj.select_get()", source)
        self.assertIn("is_stair", source)


class UIAndScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ui = (ROOT / "japanese_house_modeler" / "ui.py").read_text()
        cls.production = "\n".join(
            path.read_text() for path in (ROOT / "japanese_house_modeler").glob("*.py"))

    def test_stage4_labels_and_policy_are_present(self):
        self.assertIn("編集可能Meshとして確定", self.ui)
        self.assertIn("階段を削除", self.ui)
        self.assertIn('operation_allowed("FINALIZE", issues)', self.ui)
        self.assertIn('operation_allowed("DELETE", issues)', self.ui)

    def test_stage4_scope_does_not_add_deferred_stair_features(self):
        stage4_files = "\n".join((
            (ROOT / "japanese_house_modeler" / "stair_operators.py").read_text(),
            self.ui,
        )).lower()
        for forbidden in ("nosing", "landing",
                          "winder", "multi-point", "floor connection"):
            with self.subTest(feature=forbidden):
                self.assertNotIn(forbidden, stage4_files)


if __name__ == "__main__":
    unittest.main()
