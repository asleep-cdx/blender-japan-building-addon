"""Pure Build 05-B geometry, safety, state and UI regression tests."""

import importlib.util
import ast
import math
import pathlib
import unittest


ROOT = pathlib.Path(__file__).parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "japanese_house_modeler" / filename
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


alignment = load("build05b_alignment", "drawing_alignment.py")
state = load("build05b_state", "wall_state.py")


class ConstrainedIntersectionTests(unittest.TestCase):
    def assert_point(self, projection, expected):
        self.assertIsNotNone(projection)
        for actual, wanted in zip(projection.point, expected):
            self.assertAlmostEqual(actual, wanted, places=9)

    def test_horizontal_and_vertical_hosts(self):
        self.assert_point(alignment.intersect_forward_ray_segment(
            (0, 0), (1, 0), (4, -2), (4, 2)), (4, 0, 0))
        self.assert_point(alignment.intersect_forward_ray_segment(
            (0, 0), (0, 1), (-2, 4), (2, 4)), (0, 4, 0))

    def test_15_and_45_degree_constraint(self):
        for degrees in (15, 45):
            direction = alignment.constrained_direction(
                (0, 0), (math.cos(math.radians(degrees)),
                         math.sin(math.radians(degrees))))
            result = alignment.intersect_forward_ray_segment(
                (0, 0), direction, (2, -10), (2, 10))
            with self.subTest(degrees=degrees):
                self.assert_point(result, (2, 2 * math.tan(math.radians(degrees)), 0))

    def test_parallel_behind_and_outside_are_invalid(self):
        cases = (
            ((1, 0), (0, 1), (10, 1)),
            ((1, 0), (-3, -1), (-3, 1)),
            ((1, 0), (3, 1), (3, 2)),
        )
        for direction, start, end in cases:
            self.assertIsNone(alignment.intersect_forward_ray_segment(
                (0, 0), direction, start, end))

    def test_reversed_host_is_invariant(self):
        first = alignment.intersect_forward_ray_segment(
            (0, 0), (1, 0), (3, -2), (3, 2))
        second = alignment.intersect_forward_ray_segment(
            (0, 0), (1, 0), (3, 2), (3, -2))
        self.assertEqual(first.point, second.point)

    def test_ambiguous_candidates_are_rejected(self):
        self.assertIsNone(alignment.select_unambiguous_candidate(
            [(2.0, "first-host"), (2.0, "second-host")]))


class SplitAndLengthTests(unittest.TestCase):
    def test_strict_one_millimetre_boundary(self):
        for x, valid in ((0.001, False), (0.0010001, True),
                         (9.999, False), (9.9989999, True)):
            projection = alignment.project_to_wall_segment((x, 0), (0, 0), (10, 0))
            self.assertEqual(alignment.is_safe_split_projection(projection), valid)

    def test_split_helper_cannot_bypass_safety(self):
        self.assertIsNone(alignment.canonical_split_segments(
            (0, 0), (1, 0), (0.001, 0)))

    def test_canonical_length(self):
        self.assertEqual(alignment.wall_length_m((0, 0), (3, 4)), 5)
        self.assertEqual(alignment.wall_length_m((2, 2), (2, -1)), 3)
        for end in ((0, 0), (math.nan, 0), (math.inf, 0)):
            self.assertIsNone(alignment.wall_length_m((0, 0), end))

    def test_endpoint_move_target_guard(self):
        source, host = object(), object()
        projection = alignment.project_to_wall_segment((5, 0), (0, 0), (10, 0))
        self.assertTrue(alignment.endpoint_move_midpoint_valid(source, host, projection))
        self.assertFalse(alignment.endpoint_move_midpoint_valid(host, host, projection))

    def test_same_host_build_05_a_regression(self):
        host = object()
        self.assertTrue(alignment.same_host_connection_forbidden(host, host))
        self.assertFalse(alignment.same_host_connection_forbidden(None, None, host, host))


class ManagedStateTests(unittest.TestCase):
    def test_transformed_candidate_excluded(self):
        self.assertTrue(state.drawing_candidate_eligible(True, True, True))
        self.assertFalse(state.drawing_candidate_eligible(True, True, False))

    def test_identity_matrix_validation(self):
        identity = [[float(row == column) for column in range(4)] for row in range(4)]
        self.assertTrue(state.has_identity_matrix(identity))
        identity[0][3] = 1.0
        self.assertFalse(state.has_identity_matrix(identity))

    def test_status_includes_duplicate_topology_problem(self):
        self.assertEqual(
            state.managed_state_problems(True, False), ("TOPOLOGY",))
        self.assertEqual(state.managed_state_problems(True, True), ())

    def test_ui_uses_single_add_icon_and_new_label(self):
        source = (ROOT / "japanese_house_modeler" / "ui.py").read_text(encoding="utf-8")
        self.assertIn('"jhm.create_wall", text="壁を生成", icon="ADD"', source)
        self.assertNotIn('text="＋ 壁"', source)


class OperatorSafetyRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (
            ROOT / "japanese_house_modeler" / "operators.py"
        ).read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)

    def method(self, class_name, method_name):
        operator = next(
            node for node in self.tree.body
            if isinstance(node, ast.ClassDef) and node.name == class_name
        )
        return next(
            node for node in operator.body
            if isinstance(node, ast.FunctionDef) and node.name == method_name
        )

    def test_normal_midpoint_preview_applies_split_safety(self):
        method = self.method("JHM_OT_create_wall", "snap_segment_candidate")
        calls = {
            node.func.id
            for node in ast.walk(method)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertIn("project_to_wall_segment", calls)
        self.assertIn("is_safe_split_projection", calls)

    def test_rebuild_restores_topology_when_regeneration_fails(self):
        method = self.method("JHM_OT_rebuild_wall_joints", "execute")
        calls = [
            node.func.id
            for node in ast.walk(method)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        ]
        self.assertIn("snapshot_topology", calls)
        self.assertIn("cleanup_untrusted_connections", calls)
        self.assertIn("regenerate_wall_meshes", calls)
        handler_calls = {
            node.func.id
            for handler in ast.walk(method)
            if isinstance(handler, ast.ExceptHandler)
            for node in ast.walk(handler)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertIn("restore_topology", handler_calls)


if __name__ == "__main__":
    unittest.main()
