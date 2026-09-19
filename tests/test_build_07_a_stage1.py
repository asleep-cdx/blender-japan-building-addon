"""Pure-Python Build 07-A Stage 1 canonical and structural contracts."""

import ast
import math
import pathlib
import sys
import types
import unittest
import uuid

ROOT = pathlib.Path(__file__).parents[1]
package = types.ModuleType("japanese_house_modeler")
package.__path__ = [str(ROOT / "japanese_house_modeler")]
sys.modules.setdefault("japanese_house_modeler", package)

from japanese_house_modeler.stair_geometry import (
    MIN_STAIR_PATH_LENGTH_M, canonical_path, generate_stair_id,
    identity_transform_contract, resolve_lower_upper, resolve_stair_axes,
)


class StairCanonicalTests(unittest.TestCase):
    def test_uuid_generation_is_valid_and_unique(self):
        first, second = generate_stair_id(), generate_stair_id()
        self.assertEqual(str(uuid.UUID(first)), first)
        self.assertNotEqual(first, second)

    def test_path_requires_exactly_two_points(self):
        for points in ((), ((0, 0),), ((0, 0), (1, 0), (2, 0))):
            with self.assertRaises(ValueError):
                canonical_path(points)

    def test_zero_and_near_zero_length_are_rejected(self):
        for end in ((0, 0), (MIN_STAIR_PATH_LENGTH_M, 0)):
            with self.assertRaises(ValueError):
                canonical_path(((0, 0), end))

    def test_non_finite_coordinate_is_rejected(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.assertRaises(ValueError):
                canonical_path(((0, 0), (value, 1)))

    def test_draw_order_and_world_xy_are_preserved(self):
        self.assertEqual(canonical_path(((4, 3, 99), (-2, 5, -10))),
                         ((4.0, 3.0), (-2.0, 5.0)))

    def test_forward_resolves_p0_lower(self):
        self.assertEqual(resolve_lower_upper(((1, 2), (3, 4)), "FORWARD"),
                         ((1, 2), (3, 4)))

    def test_reverse_resolves_p1_lower_without_reordering_storage(self):
        points = ((1, 2), (3, 4))
        self.assertEqual(resolve_lower_upper(points, "REVERSE"),
                         ((3, 4), (1, 2)))
        self.assertEqual(points, ((1, 2), (3, 4)))

    def test_horizontal_axes(self):
        axes = resolve_stair_axes(((0, 0), (2, 0)), "FORWARD")
        self.assertEqual(axes.forward, (1, 0, 0))
        self.assertEqual(axes.left, (0, 1, 0))

    def test_vertical_plan_axes(self):
        axes = resolve_stair_axes(((0, 0), (0, 2)), "FORWARD")
        self.assertEqual(axes.forward, (0, 1, 0))
        self.assertEqual(axes.left, (-1, 0, 0))

    def test_oblique_axes_are_normalized(self):
        axes = resolve_stair_axes(((0, 0), (3, 4)), "FORWARD")
        self.assertEqual(axes.forward, (.6, .8, 0))
        self.assertEqual(axes.left, (-.8, .6, 0))

    def test_left_axis_orientation_and_world_up(self):
        axes = resolve_stair_axes(((0, 0), (3, -4)), "FORWARD")
        cross_z = axes.forward[0] * axes.left[1] - axes.forward[1] * axes.left[0]
        self.assertAlmostEqual(cross_z, 1.0)
        self.assertEqual(axes.up, (0, 0, 1))

    def test_identity_transform_contract(self):
        self.assertEqual(identity_transform_contract(),
                         ((0, 0, 0), (0, 0, 0), (1, 1, 1)))


class StairSourceStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.init_source = (ROOT / "japanese_house_modeler" / "__init__.py").read_text()
        cls.properties_source = (ROOT / "japanese_house_modeler" / "properties.py").read_text()
        cls.operator_source = (ROOT / "japanese_house_modeler" / "stair_operators.py").read_text()
        cls.operator_tree = ast.parse(cls.operator_source)

    def test_addon_identity_and_registration_declarations(self):
        self.assertIn('"version": (0, 7, 0)', self.init_source)
        self.assertIn("JHM_OT_create_stair", self.init_source)
        self.assertIn("jhm_new_stair_defaults", self.init_source)
        self.assertIn("jhm_stair", self.init_source)

    def test_default_values_are_declared(self):
        for declaration in ("default=0.0", "default=2800.0", "default=16",
                            "default=900.0", "default=30.0", "default=12.0",
                            'default="FORWARD"'):
            self.assertIn(declaration, self.properties_source)

    def test_canonical_stair_property_groups_are_declared(self):
        for name in ("JHM_StairPathPoint", "JHM_NewStairDefaults",
                     "JHM_StairProperties"):
            self.assertIn(f"class {name}", self.properties_source)
        self.assertIn("path_points: bpy.props.CollectionProperty", self.properties_source)

    def test_cancel_precedes_the_only_commit_call(self):
        modal = next(node for node in ast.walk(self.operator_tree)
                     if isinstance(node, ast.FunctionDef) and node.name == "modal")
        commits = [node for node in ast.walk(modal) if isinstance(node, ast.Call)
                   and isinstance(node.func, ast.Attribute)
                   and node.func.attr == "_commit"]
        self.assertEqual(len(commits), 1)
        self.assertIn('event.type in {"ESC", "RIGHTMOUSE"}', self.operator_source)

    def test_commit_creates_exactly_one_mesh_and_one_object(self):
        commit = next(node for node in ast.walk(self.operator_tree)
                      if isinstance(node, ast.FunctionDef) and node.name == "_commit")
        calls = [ast.unparse(node.func) for node in ast.walk(commit)
                 if isinstance(node, ast.Call)]
        self.assertEqual(calls.count("bpy.data.meshes.new"), 1)
        self.assertEqual(calls.count("bpy.data.objects.new"), 1)

    def test_commit_sets_identity_transform(self):
        self.assertIn("stair_object.location = (0.0, 0.0, 0.0)", self.operator_source)
        self.assertIn("stair_object.rotation_euler = (0.0, 0.0, 0.0)", self.operator_source)
        self.assertIn("stair_object.scale = (1.0, 1.0, 1.0)", self.operator_source)


if __name__ == "__main__":
    unittest.main()
