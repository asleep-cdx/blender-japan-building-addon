"""Build 07-D Stage 4 lifecycle and final-regression contracts.

This suite is deliberately Blender-independent. Save/reopen, RNA Undo/Redo and
practical placement evidence belongs to ``BUILD_07_D_STAGE4_RUNTIME_TEST.md``.
"""
import ast
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
    identity_transform_contract, prepare_stair_geometry, validate_mesh_fragments)
from japanese_house_modeler.stair_multiflight import (
    prepare_multiflight_residential_geometry, resolve_multiflight_layout)
from japanese_house_modeler.stair_residential import (
    BASIC_TREAD_RISER, SLOPED, SLOPED_CLOSED, STANDARD_RESIDENTIAL,
    STEPPED, STEPPED_CLOSED, ResidentialFields, assemble_material_slot_plan)
from japanese_house_modeler.stair_residential_geometry import prepare_residential_geometry
from japanese_house_modeler.stair_state import (
    GEOMETRY_MISSING, ID_CONFLICT, ID_MISSING, TRANSFORM_CHANGED, StairState,
    diagnose_stair, duplicate_stair_ids, operation_allowed)

STRAIGHT = ((0.0, 0.0), (3.6, 0.0))
L_PATH = ((0.0, 0.0), (3.0, 0.0), (3.0, 3.0))
U_PATH = ((0.0, 0.0), (3.0, 0.0), (3.0, 1.8), (0.0, 1.8))
COMMON = dict(ascent_direction="FORWARD", base_z_mm=100,
              floor_to_floor_mm=2800, riser_count=16, stair_width_mm=900,
              tread_thickness_mm=30, riser_thickness_mm=12)


def node(tree, kind, name):
    return next(item for item in tree.body
                if isinstance(item, kind) and item.name == name)


def polygon_area(vertices, face):
    """Return the 3-D polygon area using Newell's method."""
    normal = [0.0, 0.0, 0.0]
    points = [vertices[index] for index in face]
    for current, following in zip(points, points[1:] + points[:1]):
        normal[0] += (current[1] - following[1]) * (current[2] + following[2])
        normal[1] += (current[2] - following[2]) * (current[0] + following[0])
        normal[2] += (current[0] - following[0]) * (current[1] + following[1])
    return 0.5 * math.sqrt(sum(value * value for value in normal))


class SchemaAndPersistenceTests(unittest.TestCase):
    def test_schema_1_2_3_straight_resolve_without_upgrade(self):
        for schema, mode in ((1, BASIC_TREAD_RISER), (2, STANDARD_RESIDENTIAL),
                             (3, STANDARD_RESIDENTIAL)):
            state = StairState("stable", STRAIGHT, **COMMON,
                               assembly_mode=mode, stair_schema_version=schema)
            with self.subTest(schema=schema):
                self.assertEqual(diagnose_stair(state), ())
                self.assertEqual(state.stair_schema_version, schema)
                self.assertEqual(state.path_points, STRAIGHT)

    def test_schema_4_l_u_preserve_ids_direction_and_saved_allocations(self):
        for path, ids, allocation in (
                (L_PATH, ("l0", "l1", "l2"), (8, 8)),
                (U_PATH, ("u0", "u1", "u2", "u3"), (5, 6, 5))):
            for direction in ("FORWARD", "REVERSE"):
                layout = resolve_multiflight_layout(
                    path, direction, 100, 2800, 16, 900, 30, 12,
                    point_ids=ids, allocation=allocation)
                self.assertEqual(tuple(p.xy for p in layout.canonical_path), path)
                self.assertEqual(tuple(p.point_id for p in layout.canonical_path), ids)
                self.assertEqual(layout.ascent_direction, direction)
                self.assertEqual(layout.allocation, allocation)

    def test_auto_is_deterministic_and_manual_is_retained(self):
        first = resolve_multiflight_layout(L_PATH, "FORWARD", 0, 2800, 16,
                                           900, 30, 12)
        second = resolve_multiflight_layout(L_PATH, "FORWARD", 0, 2800, 16,
                                            900, 30, 12)
        self.assertEqual(first.allocation, second.allocation)
        manual = resolve_multiflight_layout(L_PATH, "FORWARD", 0, 2800, 16,
                                            900, 30, 12, allocation=(7, 9))
        self.assertEqual(manual.allocation, (7, 9))

    def test_material_roles_and_identity_transform_remain_canonical(self):
        materials = [object() for _ in range(5)]
        fields = ResidentialFields(
            base_material=materials[0], tread_material=materials[1],
            riser_material=materials[2], underside_material=materials[3],
            side_board_material=materials[4])
        plan = assemble_material_slot_plan(fields)
        # A fully overridden role set does not create an unused base slot.
        self.assertEqual(plan.slots, tuple(materials[1:]))
        self.assertEqual(identity_transform_contract(),
                         ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (1.0, 1.0, 1.0)))


class RepairAndLifecycleTests(unittest.TestCase):
    def test_all_four_recoverable_issues_are_diagnosed_and_repairable(self):
        base = dict(stair_id="stable", path_points=STRAIGHT, **COMMON)
        cases = ((ID_MISSING, {"stair_id": ""}),
                 (ID_CONFLICT, {}, {"stable"}),
                 (TRANSFORM_CHANGED, {"location": (1, 0, 0)}),
                 (GEOMETRY_MISSING, {"vertex_count": 0, "face_count": 0}))
        for entry in cases:
            issue, changes, *duplicates = entry
            state = StairState(**dict(base, **changes))
            issues = diagnose_stair(state, duplicates[0] if duplicates else ())
            self.assertIn(issue, issues)
            self.assertTrue(operation_allowed("REPAIR", issues))

    def test_duplicate_repair_scope_leaves_unrelated_ids_unchanged(self):
        survivor = types.SimpleNamespace(is_managed=True, stair_id="duplicate")
        target = types.SimpleNamespace(is_managed=True, stair_id="duplicate")
        unrelated = types.SimpleNamespace(is_managed=True, stair_id="other")
        self.assertEqual(duplicate_stair_ids((survivor, target, unrelated)),
                         {"duplicate"})
        target.stair_id = "replacement"
        self.assertEqual(duplicate_stair_ids((survivor, target, unrelated)), frozenset())
        self.assertEqual((survivor.stair_id, unrelated.stair_id), ("duplicate", "other"))

    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "japanese_house_modeler/stair_operators.py").read_text()
        cls.tree = ast.parse(cls.source)

    def function_source(self, name):
        return ast.unparse(node(self.tree, ast.FunctionDef, name))

    def class_source(self, name):
        return ast.unparse(node(self.tree, ast.ClassDef, name))

    def test_regenerate_repair_preserve_canonical_material_snapshot(self):
        snapshot = self.function_source("_canonical_snapshot")
        transaction = self.function_source("_transactional_update")
        for value in ("path_points", "point_ids", "riser_distribution_mode",
                      "auto_riser_allocation", "manual_riser_allocation",
                      "residential=residential_fields(stair)"):
            self.assertIn(value, snapshot)
        self.assertIn("getattr(old_data, 'materials', ())", transaction)
        self.assertIn("_set_canonical(stair, old_canonical)", transaction)

    def test_repair_generates_id_only_for_missing_or_conflict(self):
        repair = self.class_source("JHM_OT_repair_stair")
        self.assertIn("ID_CONFLICT in issues or ID_MISSING in issues", repair)
        self.assertNotIn("TRANSFORM_CHANGED in issues or", repair)
        self.assertNotIn("GEOMETRY_MISSING in issues or", repair)

    def test_finalize_removes_management_without_regeneration(self):
        helper = self.function_source("finalize_stair_management")
        finalize = self.class_source("JHM_OT_convert_stair_mesh")
        self.assertIn("stair.is_stair = False", helper)
        for forbidden in ("_transactional_update", "_prepare_candidate", ".data ="):
            self.assertNotIn(forbidden, finalize)
        finalized = types.SimpleNamespace(is_managed=False, stair_id="old")
        self.assertEqual(duplicate_stair_ids((finalized,)), frozenset())

    def test_delete_is_active_object_only_and_accepts_abnormal_state(self):
        delete = self.class_source("JHM_OT_delete_stair")
        self.assertIn("bpy.data.objects.remove(obj, do_unlink=True)", delete)
        for forbidden in ("bpy.ops.object.delete", "bpy.data.meshes.remove",
                          "bpy.data.materials.remove"):
            self.assertNotIn(forbidden, delete)
        for issue in (ID_MISSING, ID_CONFLICT, TRANSFORM_CHANGED, GEOMETRY_MISSING):
            self.assertTrue(operation_allowed("DELETE", (issue,)))

    def test_stair_lifecycle_has_no_finish_or_wall_mutation(self):
        lifecycle = "\n".join(self.class_source(name) for name in (
            "JHM_OT_reverse_stair_ascent", "JHM_OT_regenerate_stair",
            "JHM_OT_repair_stair", "JHM_OT_convert_stair_mesh",
            "JHM_OT_delete_stair"))
        for forbidden in ("jhm_wall", "jhm_finish", "finish_id", "wall_id"):
            self.assertNotIn(forbidden, lifecycle)


class GeometryRegressionTests(unittest.TestCase):
    def assert_mesh_valid(self, fragments, mesh):
        self.assertTrue(validate_mesh_fragments(fragments))
        self.assertTrue(all(math.isfinite(value)
                            for vertex in mesh.vertices for value in vertex))
        self.assertTrue(mesh.faces)
        self.assertTrue(all(polygon_area(mesh.vertices, face) > 1.0e-12
                            for face in mesh.faces))
        signatures = [(fragment.part_type,
                       tuple(round(value, 10) for vertex in fragment.vertices
                             for value in vertex), fragment.faces)
                      for fragment in fragments]
        self.assertEqual(len(signatures), len(set(signatures)))

    def test_representative_straight_l_u_are_deterministic(self):
        straight = lambda: prepare_stair_geometry(STRAIGHT, **COMMON)
        l_shape = lambda: prepare_multiflight_residential_geometry(
            L_PATH, **COMMON, point_ids=("l0", "l1", "l2"))
        u_shape = lambda: prepare_multiflight_residential_geometry(
            U_PATH, **COMMON, point_ids=("u0", "u1", "u2", "u3"))
        for factory in (straight, l_shape, u_shape):
            first, second = factory(), factory()
            self.assertEqual(first[-1], second[-1])

    def test_representative_topology_matrix(self):
        cases = (
            (STRAIGHT, "FORWARD", STEPPED_CLOSED, False, STEPPED),
            (STRAIGHT, "REVERSE", SLOPED_CLOSED, True, SLOPED),
            (L_PATH, "FORWARD", STEPPED_CLOSED, True, STEPPED),
            (L_PATH, "REVERSE", SLOPED_CLOSED, False, SLOPED),
            (U_PATH, "FORWARD", SLOPED_CLOSED, True, STEPPED),
            (U_PATH, "REVERSE", STEPPED_CLOSED, True, SLOPED))
        for path, direction, underside, boards, board_mode in cases:
            fields = replace(ResidentialFields(), underside_mode=underside,
                             left_side_board_enabled=boards,
                             right_side_board_enabled=boards,
                             side_board_mode=board_mode)
            args = dict(COMMON, ascent_direction=direction)
            if len(path) == 2:
                _layout, fragments, mesh = prepare_residential_geometry(
                    path, **args, fields=fields)
            else:
                _layout, fragments, mesh = prepare_multiflight_residential_geometry(
                    path, **args, fields=fields)
            with self.subTest(path=len(path), direction=direction,
                              underside=underside, boards=boards,
                              board_mode=board_mode):
                self.assert_mesh_valid(fragments, mesh)

    def test_runtime_plan_covers_grouped_acceptance(self):
        text = (ROOT / "BUILD_07_D_STAGE4_RUNTIME_TEST.md").read_text()
        self.assertGreaterEqual(sum(line.startswith("## Test ") for line in text.splitlines()), 10)
        self.assertLessEqual(sum(line.startswith("## Test ") for line in text.splitlines()), 18)
        for required in ("Ctrl+Z", "Ctrl+Shift+Z", "fully exit Blender",
                         "schema-1", "schema-2", "schema-3", "AUTO", "MANUAL",
                         "ID_CONFLICT", "GEOMETRY_MISSING", "TRANSFORM_CHANGED",
                         "Finalize", "active-only", "Wall", "Finish", "nonmanifold"):
            self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
