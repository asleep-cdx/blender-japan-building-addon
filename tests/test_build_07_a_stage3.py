"""Pure and structural coverage for Build 07-A Stage 3."""

import ast
import math
import pathlib
import sys
import types
import unittest

ROOT = pathlib.Path(__file__).parents[1]
package = types.ModuleType("japanese_house_modeler")
package.__path__ = [str(ROOT / "japanese_house_modeler")]
sys.modules.setdefault("japanese_house_modeler", package)

from japanese_house_modeler.stair_geometry import prepare_stair_geometry
from japanese_house_modeler.stair_state import (
    GEOMETRY_MISSING, ID_CONFLICT, ID_MISSING, INVALID_CANONICAL, NORMAL,
    OBJECT_TYPE_CHANGED, TRANSFORM_CHANGED, StairState, diagnose_stair,
    duplicate_stair_ids, operation_allowed, state_label,
)


REFERENCE = dict(
    points=((0.0, 0.0), (3.6, 0.0)), ascent_direction="FORWARD",
    base_z_mm=0.0, floor_to_floor_mm=2800.0, riser_count=16,
    stair_width_mm=900.0, tread_thickness_mm=30.0,
    riser_thickness_mm=12.0,
)


def prepared(**changes):
    values = dict(REFERENCE)
    values.update(changes)
    return prepare_stair_geometry(**values)


def state(**changes):
    values = dict(
        stair_id="id-a", path_points=REFERENCE["points"],
        ascent_direction="FORWARD", base_z_mm=0.0,
        floor_to_floor_mm=2800.0, riser_count=16, stair_width_mm=900.0,
        tread_thickness_mm=30.0, riser_thickness_mm=12.0)
    values.update(changes)
    return StairState(**values)


class CandidateTests(unittest.TestCase):
    def test_each_dimension_candidate_is_resolved(self):
        cases = (
            ("base_z_mm", 500.0, "base_z", .5),
            ("floor_to_floor_mm", 3000.0, "floor_to_floor", 3.0),
            ("riser_count", 18, "riser_count", 18),
            ("stair_width_mm", 1000.0, "width", 1.0),
            ("tread_thickness_mm", 25.0, "tread_thickness", .025),
            ("riser_thickness_mm", 10.0, "riser_thickness", .01),
        )
        for key, value, attribute, expected in cases:
            with self.subTest(key=key):
                layout, _parts, mesh = prepared(**{key: value})
                self.assertAlmostEqual(getattr(layout, attribute), expected)
                self.assertTrue(mesh.vertices and mesh.faces)

    def test_horizontal_3600_contract(self):
        layout, _, _ = prepared(points=((0, 0), (3.6, 0)))
        self.assertAlmostEqual(layout.run_length_mm, 3600)
        self.assertAlmostEqual(layout.going_mm, 240)
        self.assertEqual(layout.riser_count, 16)

    def test_translation_changes_plan_only(self):
        original, _, _ = prepared()
        moved, _, _ = prepared(points=((1, 2), (4.6, 2)))
        self.assertEqual(moved.canonical_path, ((1.0, 2.0), (4.6, 2.0)))
        self.assertAlmostEqual(moved.run_length, original.run_length)
        self.assertAlmostEqual(moved.going, original.going)
        self.assertEqual(moved.floor_to_floor, original.floor_to_floor)

    def test_rotation_preserves_run_length_and_rotates_geometry(self):
        horizontal, _, horizontal_mesh = prepared()
        vertical, _, vertical_mesh = prepared(points=((0, 0), (0, 3.6)))
        self.assertAlmostEqual(vertical.run_length, horizontal.run_length)
        self.assertNotEqual(vertical.forward_axis, horizontal.forward_axis)
        self.assertNotEqual(vertical_mesh.vertices, horizontal_mesh.vertices)

    def test_run_length_edit_changes_going(self):
        short, _, _ = prepared(points=((0, 0), (3.0, 0)))
        self.assertAlmostEqual(short.going_mm, 200.0)

    def test_reverse_round_trip_preserves_path_and_length(self):
        forward, _, forward_mesh = prepared()
        reverse, _, reverse_mesh = prepared(ascent_direction="REVERSE")
        again, _, _ = prepared(ascent_direction="FORWARD")
        self.assertEqual(reverse.canonical_path, forward.canonical_path)
        self.assertAlmostEqual(reverse.run_length, forward.run_length)
        self.assertNotEqual(reverse_mesh.vertices, forward_mesh.vertices)
        self.assertEqual(again.canonical_path, forward.canonical_path)
        self.assertEqual(again.upper_xy, forward.upper_xy)

    def test_invalid_candidates_fail_before_any_commit_layer(self):
        cases = (
            {"floor_to_floor_mm": 0}, {"riser_count": 1},
            {"points": ((0, 0), (0, 0))}, {"tread_thickness_mm": 175},
            {"riser_thickness_mm": 240}, {"base_z_mm": math.nan},
        )
        for changes in cases:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                prepared(**changes)


class DiagnosisTests(unittest.TestCase):
    def test_normal(self):
        issues = diagnose_stair(state())
        self.assertEqual(issues, ())
        self.assertEqual(state_label(issues), "正常")
        self.assertEqual(NORMAL, "NORMAL")

    def test_missing_and_duplicate_id(self):
        self.assertIn(ID_MISSING, diagnose_stair(state(stair_id="")))
        self.assertIn(ID_CONFLICT, diagnose_stair(state(), {"id-a"}))

    def test_duplicate_helper_excludes_unmanaged_and_empty(self):
        records = [types.SimpleNamespace(is_managed=True, stair_id="same"),
                   types.SimpleNamespace(is_managed=True, stair_id="same"),
                   types.SimpleNamespace(is_managed=False, stair_id="same"),
                   types.SimpleNamespace(is_managed=True, stair_id="")]
        self.assertEqual(duplicate_stair_ids(records), {"same"})

    def test_each_transform_component_is_diagnosed(self):
        cases = ({"location": (1, 0, 0)}, {"rotation": (0, .1, 0)},
                 {"scale": (1, 1, 2)})
        for changes in cases:
            with self.subTest(changes=changes):
                self.assertIn(TRANSFORM_CHANGED, diagnose_stair(state(**changes)))

    def test_invalid_canonical_and_geometry_missing_can_coexist(self):
        issues = diagnose_stair(state(floor_to_floor_mm=0, vertex_count=0,
                                      face_count=0))
        self.assertIn(INVALID_CANONICAL, issues)
        self.assertIn(GEOMETRY_MISSING, issues)

    def test_mesh_data_vertices_and_faces_are_geometry_missing(self):
        cases = ({"has_mesh": False}, {"vertex_count": 0}, {"face_count": 0})
        for changes in cases:
            with self.subTest(changes=changes):
                self.assertIn(GEOMETRY_MISSING, diagnose_stair(state(**changes)))

    def test_non_mesh_is_type_changed_not_geometry_missing_or_repairable(self):
        issues = diagnose_stair(state(object_type="CURVE"))
        self.assertEqual(issues, (OBJECT_TYPE_CHANGED,))
        self.assertNotIn(GEOMETRY_MISSING, issues)
        self.assertFalse(operation_allowed("REPAIR", issues))
        for operation in ("EDIT_DIMENSIONS", "EDIT_PATH", "REVERSE",
                          "REGENERATE", "FINALIZE"):
            self.assertFalse(operation_allowed(operation, issues))
        self.assertTrue(operation_allowed("DELETE", issues))

    def test_valid_canonical_empty_mesh_remains_repairable(self):
        issues = diagnose_stair(state(vertex_count=0, face_count=0))
        self.assertEqual(issues, (GEOMETRY_MISSING,))
        self.assertTrue(operation_allowed("REPAIR", issues))


class PolicyTests(unittest.TestCase):
    def test_normal_only_operations(self):
        for operation in ("EDIT_DIMENSIONS", "EDIT_PATH", "REVERSE",
                          "REGENERATE", "FINALIZE"):
            self.assertTrue(operation_allowed(operation, ()))
            self.assertFalse(operation_allowed(operation, (TRANSFORM_CHANGED,)))

    def test_repair_recoverable_but_never_invalid_canonical(self):
        for issue in (ID_MISSING, ID_CONFLICT, TRANSFORM_CHANGED, GEOMETRY_MISSING):
            self.assertTrue(operation_allowed("REPAIR", (issue,)))
        self.assertFalse(operation_allowed("REPAIR", ()))
        self.assertFalse(operation_allowed("REPAIR", (INVALID_CANONICAL,)))
        self.assertFalse(operation_allowed(
            "REPAIR", (INVALID_CANONICAL, GEOMETRY_MISSING)))
        self.assertFalse(operation_allowed(
            "REPAIR", (OBJECT_TYPE_CHANGED, ID_CONFLICT)))

    def test_future_delete_is_abnormal_allowed(self):
        self.assertTrue(operation_allowed("DELETE", (INVALID_CANONICAL,)))


class TransactionStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "japanese_house_modeler" /
                      "stair_operators.py").read_text()
        cls.tree = ast.parse(cls.source)

    def function(self, name):
        return next(node for node in ast.walk(self.tree)
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name == name)

    def test_prepare_precedes_replacement_and_swap(self):
        source = ast.unparse(self.function("_transactional_update"))
        self.assertLess(source.index("_prepare_candidate(candidate)"),
                        source.index("bpy.data.meshes.new"))
        self.assertLess(source.index("replacement.from_pydata"),
                        source.index("stair_object.data = replacement"))
        self.assertLess(source.index("stair_object.data = replacement"),
                        source.index("_set_canonical(stair, candidate)"))

    def test_rollback_restores_all_snapshots_and_removes_replacement(self):
        source = ast.unparse(self.function("_transactional_update"))
        for fragment in ("setattr(stair_object, 'data', old_data)",
                         "_set_canonical(stair, old_canonical)",
                         "setattr(stair, 'stair_id', old_id)", "old_transform",
                         "_cleanup_unused_data(replacement)"):
            self.assertIn(fragment, source)

    def test_material_slots_are_transferred_before_swap(self):
        source = ast.unparse(self.function("_transactional_update"))
        self.assertIn("getattr(old_data, 'materials', ())", source)
        self.assertIn("for material in materials", source)
        self.assertLess(source.index("replacement.materials.append(material)"),
                        source.index("stair_object.data = replacement"))

    def test_cross_type_conversion_paths_are_absent(self):
        transaction = ast.unparse(self.function("_transactional_update"))
        self.assertNotIn("def _assign_object_data", self.source)
        self.assertNotIn("bpy.ops.object.convert", self.source)
        self.assertNotIn("stair_object.data = None", transaction)
        self.assertNotIn("bpy.data.objects.new", transaction)
        self.assertNotIn("bpy.data.objects.remove", transaction)

    def test_non_mesh_old_data_is_not_treated_as_a_mesh(self):
        transaction = ast.unparse(self.function("_transactional_update"))
        cleanup = ast.unparse(self.function("_cleanup_unused_data"))
        self.assertIn("old_data = stair_object.data", transaction)
        self.assertNotIn("old_mesh", transaction)
        self.assertIn("isinstance(data, bpy.types.Mesh)", cleanup)
        self.assertNotIn("bpy.data.meshes.remove(old_data)", self.source)

    def test_post_commit_cleanup_is_best_effort(self):
        transaction = ast.unparse(self.function("_transactional_update"))
        helper = ast.unparse(self.function("_cleanup_unused_data"))
        best_effort = ast.unparse(self.function("_best_effort"))
        self.assertTrue(transaction.rstrip().endswith("_cleanup_unused_data(old_data)"))
        self.assertIn("_best_effort(remove_if_unused)", helper)
        self.assertIn("except Exception", best_effort)

    def test_rollback_cleanup_preserves_original_exception(self):
        transaction = ast.unparse(self.function("_transactional_update"))
        cleanup_index = transaction.index("_cleanup_unused_data(replacement)")
        self.assertEqual(transaction[cleanup_index:].count("raise"), 1)
        self.assertIn("_best_effort(lambda", transaction)

    def test_operator_converts_rna_failures_to_cancelled_warning(self):
        runner = ast.unparse(self.function("_run_candidate"))
        self.assertIn("except Exception as exc", runner)
        self.assertIn("self.report({'WARNING'}, str(exc))", runner)
        self.assertIn("{'CANCELLED'}", runner)

    def test_all_stage3_operators_share_transaction_core_and_undo(self):
        for class_name in ("JHM_OT_edit_stair_dimensions", "JHM_OT_edit_stair_path",
                           "JHM_OT_reverse_stair_ascent", "JHM_OT_regenerate_stair",
                           "JHM_OT_repair_stair"):
            node = next(node for node in self.tree.body
                        if isinstance(node, ast.ClassDef) and node.name == class_name)
            source = ast.unparse(node)
            self.assertIn("UNDO", source)
            self.assertTrue("_run_candidate" in source)

    def test_dialog_values_are_temporary_and_allow_invalid_candidates(self):
        dimensions = ast.unparse(self.function("invoke"))
        properties = (ROOT / "japanese_house_modeler" / "properties.py").read_text()
        self.assertIn("invoke_props_dialog", self.source)
        self.assertNotIn("jhm_stair_dimensions_candidate", properties)
        operator_segment = self.source[self.source.index("class JHM_OT_edit_stair_dimensions"):]
        self.assertNotIn("min=", operator_segment.split("class JHM_OT_edit_stair_path")[0])

    def test_repair_uuid_is_prepared_before_transaction(self):
        repair = next(node for node in self.tree.body
                      if isinstance(node, ast.ClassDef)
                      and node.name == "JHM_OT_repair_stair")
        source = ast.unparse(repair)
        self.assertLess(source.index("generate_stair_id()"),
                        source.index("self._run_candidate"))
        self.assertIn("reset_transform=True", source)

    def test_no_mesh_reverse_inference_or_destructive_clear(self):
        self.assertNotIn("clear_geometry", self.source)
        self.assertNotIn("foreach_get", self.source)

    def test_stage4_finalization_name_remains_distinct_from_stage3(self):
        init = (ROOT / "japanese_house_modeler" / "__init__.py").read_text()
        ui = (ROOT / "japanese_house_modeler" / "ui.py").read_text()
        # The specified Stage 4 id is convert_stair_mesh, not the formerly
        # deferred/ambiguous finalize_stair spelling.
        self.assertNotIn("finalize_stair", init)
        self.assertNotIn("finalize_stair", ui)


if __name__ == "__main__":
    unittest.main()
