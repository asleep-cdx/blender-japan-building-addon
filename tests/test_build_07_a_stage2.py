"""Pure-Python Build 07-A Stage 2 layout and basic geometry tests."""

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

from japanese_house_modeler.stair_geometry import (
    assemble_stair_mesh, build_riser_fragments, build_tread_fragments,
    identity_transform_contract, MeshFragment, prepare_stair_geometry,
    resolve_stair_layout, validate_mesh_fragments,
)


REFERENCE = dict(
    points=((0.0, 0.0), (3.6, 0.0)), ascent_direction="FORWARD",
    base_z_mm=0.0, floor_to_floor_mm=2800.0, riser_count=16,
    stair_width_mm=900.0, tread_thickness_mm=30.0,
    riser_thickness_mm=12.0,
)


def resolved(**changes):
    values = dict(REFERENCE)
    values.update(changes)
    return resolve_stair_layout(**values)


def local_coordinates(layout, vertex):
    delta = (vertex[0] - layout.lower_xy[0], vertex[1] - layout.lower_xy[1])
    return (delta[0] * layout.forward_axis[0] + delta[1] * layout.forward_axis[1],
            delta[0] * layout.left_axis[0] + delta[1] * layout.left_axis[1],
            vertex[2])


class StairLayoutTests(unittest.TestCase):
    def test_reference_numeric_contract(self):
        layout = resolved()
        self.assertEqual(layout.canonical_path, REFERENCE["points"])
        self.assertAlmostEqual(layout.run_length_mm, 3600.0)
        self.assertAlmostEqual(layout.actual_riser_mm, 175.0)
        self.assertEqual(layout.independent_tread_count, 15)
        self.assertAlmostEqual(layout.going_mm, 240.0)
        self.assertAlmostEqual(layout.upper_arrival_z_mm, 2800.0)

    def test_forward_and_reverse_preserve_canonical_order(self):
        forward = resolved()
        reverse = resolved(ascent_direction="REVERSE")
        self.assertEqual(forward.lower_xy, (0.0, 0.0))
        self.assertEqual(forward.upper_arrival_xy, (3.6, 0.0))
        self.assertEqual(reverse.lower_xy, (3.6, 0.0))
        self.assertEqual(reverse.upper_arrival_xy, (0.0, 0.0))
        self.assertEqual(reverse.canonical_path, REFERENCE["points"])
        self.assertEqual(reverse.forward_axis, (-1.0, 0.0, 0.0))
        self.assertEqual(reverse.left_axis, (0.0, -1.0, 0.0))

    def test_horizontal_vertical_and_oblique_axes(self):
        cases = (
            (((0, 0), (3.6, 0)), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
            (((0, 0), (0, 3.6)), (0.0, 1.0, 0.0), (-1.0, 0.0, 0.0)),
            (((0, 0), (2.16, 2.88)), (0.6, 0.8, 0.0), (-0.8, 0.6, 0.0)),
        )
        for points, forward, left in cases:
            with self.subTest(points=points):
                layout = resolved(points=points)
                self.assertAlmostEqual(layout.run_length, 3.6)
                for actual, expected in zip(layout.forward_axis, forward):
                    self.assertAlmostEqual(actual, expected)
                for actual, expected in zip(layout.left_axis, left):
                    self.assertAlmostEqual(actual, expected)

    def test_upper_arrival_includes_base_height(self):
        layout = resolved(base_z_mm=1200.0)
        self.assertAlmostEqual(layout.upper_arrival_z_mm, 4000.0)

    def test_invalid_dimensions_are_rejected(self):
        invalid = (
            {"floor_to_floor_mm": 0}, {"floor_to_floor_mm": math.inf},
            {"riser_count": 1}, {"stair_width_mm": 0},
            {"tread_thickness_mm": 175}, {"riser_thickness_mm": 240},
            {"base_z_mm": math.nan},
        )
        for changes in invalid:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                resolved(**changes)

    def test_riser_count_rejects_non_finite_non_integer_and_bool(self):
        for value in (True, False, math.nan, math.inf, -math.inf, 16.5, 1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                resolved(riser_count=value)
        for value in (2, 16, 16.0):
            with self.subTest(value=value):
                self.assertEqual(resolved(riser_count=value).riser_count, int(value))

    def test_invalid_paths_are_rejected(self):
        for points in (((0, 0), (0, 0)), ((0, 0), (math.nan, 1)), ((0, 0),)):
            with self.subTest(points=points), self.assertRaises(ValueError):
                resolved(points=points)


class StairGeometryTests(unittest.TestCase):
    def test_riser_independent_tread_core(self):
        layout = resolved()
        treads = build_tread_fragments(layout)
        self.assertEqual(len(treads), 15)
        self.assertTrue(validate_mesh_fragments(treads))
        self.assertEqual([part.ordinal for part in treads], list(range(1, 16)))
        self.assertTrue(all(part.part_type == "TREAD" for part in treads))

    def test_tread_positions_elevations_and_width(self):
        layout = resolved()
        treads = build_tread_fragments(layout)
        for ordinal, tread in enumerate(treads, 1):
            local = tuple(local_coordinates(layout, vertex) for vertex in tread.vertices)
            self.assertAlmostEqual(min(point[0] for point in local),
                                   (ordinal - 1) * layout.going)
            self.assertAlmostEqual(max(point[0] for point in local), ordinal * layout.going)
            self.assertAlmostEqual(min(point[1] for point in local), -layout.width / 2)
            self.assertAlmostEqual(max(point[1] for point in local), layout.width / 2)
            self.assertAlmostEqual(max(point[2] for point in local),
                                   layout.base_z + ordinal * layout.actual_riser)
        self.assertAlmostEqual(max(v[2] for v in treads[-1].vertices), 2.625)
        self.assertAlmostEqual(min(v[2] for v in treads[0].vertices), 0.145)
        self.assertAlmostEqual(max(v[2] for v in treads[0].vertices), 0.175)

    def test_riser_count_and_final_riser_contract(self):
        layout = resolved()
        risers = build_riser_fragments(layout)
        self.assertEqual(len(risers), 16)
        final_local = tuple(local_coordinates(layout, vertex)
                            for vertex in risers[-1].vertices)
        self.assertAlmostEqual(min(point[0] for point in final_local), layout.run_length)
        self.assertAlmostEqual(max(point[0] for point in final_local),
                               layout.run_length + layout.riser_thickness)
        self.assertAlmostEqual(max(point[2] for point in final_local),
                               layout.upper_arrival_z)
        self.assertAlmostEqual(min(v[2] for v in risers[0].vertices), 0.0)
        self.assertAlmostEqual(max(v[2] for v in risers[0].vertices), 0.145)
        self.assertAlmostEqual(min(v[2] for v in risers[1].vertices), 0.175)
        self.assertAlmostEqual(max(v[2] for v in risers[1].vertices), 0.320)
        self.assertAlmostEqual(min(v[2] for v in risers[-1].vertices), 2.625)
        self.assertAlmostEqual(max(v[2] for v in risers[-1].vertices), 2.800)

    def test_closed_solid_validation_rejects_broken_topology(self):
        valid = build_tread_fragments(resolved())[0]
        missing_face = MeshFragment(
            valid.part_type, valid.ordinal, valid.vertices, valid.faces[:-1])
        duplicate_face = MeshFragment(
            valid.part_type, valid.ordinal, valid.vertices,
            valid.faces[:-1] + (valid.faces[0],))
        repeated_index = MeshFragment(
            valid.part_type, valid.ordinal, valid.vertices,
            ((0, 0, 2, 3),) + valid.faces[1:])
        for malformed in (missing_face, duplicate_face, repeated_index):
            with self.subTest(faces=malformed.faces), self.assertRaises(ValueError):
                validate_mesh_fragments((malformed,))

    def test_all_orientation_geometry_is_finite_symmetric_and_valid(self):
        paths = (((0, 0), (3.6, 0)), ((0, 0), (0, 3.6)),
                 ((0, 0), (2.16, 2.88)))
        for points in paths:
            for direction in ("FORWARD", "REVERSE"):
                with self.subTest(points=points, direction=direction):
                    layout = resolved(points=points, ascent_direction=direction)
                    fragments = (build_tread_fragments(layout)
                                 + build_riser_fragments(layout))
                    self.assertTrue(validate_mesh_fragments(fragments))
                    ys = [local_coordinates(layout, vertex)[1]
                          for fragment in fragments for vertex in fragment.vertices]
                    self.assertAlmostEqual(min(ys), -layout.width / 2)
                    self.assertAlmostEqual(max(ys), layout.width / 2)
                    self.assertTrue(all(math.isfinite(value)
                                        for fragment in fragments
                                        for vertex in fragment.vertices for value in vertex))

    def test_assembly_offsets_faces_into_one_complete_mesh(self):
        layout = resolved()
        fragments = build_tread_fragments(layout) + build_riser_fragments(layout)
        mesh = assemble_stair_mesh(fragments)
        self.assertEqual(len(mesh.vertices), 31 * 8)
        self.assertEqual(len(mesh.faces), 31 * 6)
        self.assertEqual(max(index for face in mesh.faces for index in face),
                         len(mesh.vertices) - 1)

    def test_prepare_returns_complete_layout_parts_and_arrays(self):
        layout, fragments, mesh = prepare_stair_geometry(**REFERENCE)
        self.assertEqual(layout.independent_tread_count, 15)
        self.assertEqual([part.part_type for part in fragments].count("TREAD"), 15)
        self.assertEqual([part.part_type for part in fragments].count("RISER"), 16)
        self.assertTrue(mesh.vertices)
        self.assertTrue(mesh.faces)


class StairStage2StructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.operator_source = (ROOT / "japanese_house_modeler" /
                               "stair_operators.py").read_text()
        cls.ui_source = (ROOT / "japanese_house_modeler" / "ui.py").read_text()
        cls.init_source = (ROOT / "japanese_house_modeler" / "__init__.py").read_text()
        cls.tree = ast.parse(cls.operator_source)

    def test_prepare_precedes_the_only_mesh_object_commit(self):
        commit = next(node for node in ast.walk(self.tree)
                      if isinstance(node, ast.FunctionDef) and node.name == "_commit")
        calls = [ast.unparse(node.func) for node in ast.walk(commit)
                 if isinstance(node, ast.Call)]
        modal = next(node for node in ast.walk(self.tree)
                     if isinstance(node, ast.FunctionDef) and node.name == "modal")
        modal_source = ast.unparse(modal)
        self.assertEqual(modal_source.count("prepare_stair_geometry("), 1)
        self.assertLess(modal_source.index("prepare_stair_geometry("),
                        modal_source.index("self._commit("))
        self.assertEqual(calls.count("bpy.data.meshes.new"), 1)
        self.assertEqual(calls.count("bpy.data.objects.new"), 1)
        self.assertIn("mesh.from_pydata", self.operator_source)

    def test_failure_cleanup_and_identity_transform_remain(self):
        for declaration in ("bpy.data.objects.remove", "bpy.data.meshes.remove",
                            "stair_object.location = (0.0, 0.0, 0.0)",
                            "stair_object.rotation_euler = (0.0, 0.0, 0.0)",
                            "stair_object.scale = (1.0, 1.0, 1.0)"):
            self.assertIn(declaration, self.operator_source)
        for declaration in ("previous_selected", "previous_active",
                            "_restore_selection"):
            self.assertIn(declaration, self.operator_source)
        self.assertEqual(identity_transform_contract(),
                         ((0, 0, 0), (0, 0, 0), (1, 1, 1)))

    def test_derived_ui_remains_read_only_and_stage3_is_registered(self):
        for label in ("上端到達高さ", "実蹴上", "独立踏板枚数", "水平長", "踏面ピッチ"):
            self.assertIn(label, self.ui_source)
        for operator in ("edit_stair_dimensions", "edit_stair_path",
                         "reverse_stair_ascent", "regenerate_stair", "repair_stair"):
            self.assertIn(operator, self.init_source)
        # Stage 4 uses the specified convert_stair_mesh id rather than the
        # ambiguous finalize_stair spelling guarded by the earlier stage.
        self.assertNotIn("finalize_stair", self.init_source)
        self.assertNotIn("show_risers", self.ui_source)


if __name__ == "__main__":
    unittest.main()
