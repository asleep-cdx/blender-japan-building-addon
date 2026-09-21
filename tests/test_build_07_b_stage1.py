"""Pure and structural coverage for Build 07-B Stage 1 foundation."""

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
    MeshFragment, build_tread_fragments, extrude_xz_profile,
    polygon_signed_area, resolve_stair_layout, triangulate_simple_polygon,
    validate_mesh_fragments, validate_simple_polygon,
)
from japanese_house_modeler.stair_residential import (
    BASIC_TREAD_RISER, STANDARD_RESIDENTIAL, ResidentialFields,
    StairTransitionSnapshot, residential_candidate, resolve_material_roles,
    semantic_assembly_mode, semantic_schema_version, validate_mode_data,
)
from japanese_house_modeler.stair_state import (
    INVALID_CANONICAL, StairState, diagnose_stair,
)


def record(**changes):
    values = dict(base_z_mm=0.0, floor_to_floor_mm=2800.0, riser_count=16,
                  stair_width_mm=900.0, tread_thickness_mm=30.0,
                  riser_thickness_mm=12.0, path_points=((0, 0), (3.6, 0)),
                  ascent_direction="FORWARD", stair_id="stable")
    values.update(changes)
    return types.SimpleNamespace(**values)


def state(**changes):
    values = dict(stair_id="stable", path_points=((0, 0), (3.6, 0)),
                  ascent_direction="FORWARD", base_z_mm=0,
                  floor_to_floor_mm=2800, riser_count=16,
                  stair_width_mm=900, tread_thickness_mm=30,
                  riser_thickness_mm=12)
    values.update(changes)
    return StairState(**values)


class CompatibilityAndDataTests(unittest.TestCase):
    def test_legacy_semantics_do_not_mutate_record(self):
        legacy = record()
        before = vars(legacy).copy()
        self.assertEqual(semantic_assembly_mode(legacy), BASIC_TREAD_RISER)
        self.assertEqual(semantic_schema_version(legacy), 1)
        self.assertEqual(vars(legacy), before)

    def test_schema_and_mode_are_independent(self):
        basic_v3 = record(assembly_mode=BASIC_TREAD_RISER,
                          stair_schema_version=3)
        self.assertEqual(semantic_assembly_mode(basic_v3), BASIC_TREAD_RISER)
        self.assertEqual(semantic_schema_version(basic_v3), 3)
        self.assertTrue(validate_mode_data(BASIC_TREAD_RISER, 3))

    def test_basic_ignores_unused_bad_residential_values(self):
        bad = ResidentialFields(underside_thickness_mm=math.nan,
                                side_board_thickness_mm=-1)
        self.assertTrue(validate_mode_data(BASIC_TREAD_RISER, 1, bad))
        self.assertNotIn(INVALID_CANONICAL,
                         diagnose_stair(state(residential=bad)))

    def test_fixed_residential_defaults_and_validation(self):
        fields = ResidentialFields()
        self.assertEqual((fields.underside_thickness_mm,
                          fields.side_board_thickness_mm,
                          fields.side_board_band_width_mm), (9.5, 18.0, 150.0))
        self.assertTrue(fields.left_side_board_enabled)
        self.assertTrue(fields.right_side_board_enabled)
        self.assertTrue(validate_mode_data(STANDARD_RESIDENTIAL, 2, fields))
        for change in (dict(underside_thickness_mm=0),
                       dict(side_board_band_width_mm=math.inf),
                       dict(left_side_board_enabled=1),
                       dict(underside_mode="SLOPED_CLOSED")):
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_mode_data(STANDARD_RESIDENTIAL, 2,
                                   ResidentialFields(**change))

    def assert_candidate_schema(self, source_schema, expected_schema):
        source = record(assembly_mode=BASIC_TREAD_RISER,
                        stair_schema_version=source_schema,
                        location=(1, 2, 3), rotation=(.1, .2, .3))
        before = vars(source).copy()
        snapshot = StairTransitionSnapshot.capture(source)
        candidate = residential_candidate(source)
        self.assertEqual(candidate.assembly_mode, STANDARD_RESIDENTIAL)
        self.assertEqual(candidate.stair_schema_version, expected_schema)
        self.assertEqual(snapshot.stair_schema_version, source_schema)
        self.assertEqual(vars(source), before)
        for name in ("path_points", "ascent_direction", "stair_id",
                     "transform", "base_material", "side_board_material"):
            self.assertIn(name, snapshot.restore_values())

    def test_schema_1_basic_candidate_uses_residential_schema_2(self):
        self.assert_candidate_schema(1, 2)

    def test_schema_2_basic_candidate_remains_schema_2(self):
        self.assert_candidate_schema(2, 2)

    def test_schema_3_basic_candidate_is_not_downgraded(self):
        self.assert_candidate_schema(3, 3)


class MaterialTests(unittest.TestCase):
    def test_base_fallback_and_override_identity(self):
        base, wood = object(), object()
        resolved = resolve_material_roles(
            ResidentialFields(base_material=base, tread_material=wood))
        self.assertIs(resolved["TREAD"], wood)
        for role in ("RISER", "UNDERSIDE", "SIDE_BOARD"):
            self.assertIs(resolved[role], base)

    def test_tread_only_preserves_other_unassigned_roles(self):
        wood = object()
        resolved = resolve_material_roles(ResidentialFields(tread_material=wood))
        self.assertIs(resolved["TREAD"], wood)
        self.assertIsNone(resolved["RISER"])
        self.assertIsNone(resolved["UNDERSIDE"])
        self.assertIsNone(resolved["SIDE_BOARD"])


class PolygonTests(unittest.TestCase):
    CONCAVE = ((0, 0), (3, 0), (3, 1), (1, 1), (1, 3), (0, 3))

    def test_convex_concave_and_both_windings_normalize(self):
        square = ((0, 0), (1, 0), (1, 1), (0, 1))
        for points in (square, tuple(reversed(square)), self.CONCAVE,
                       tuple(reversed(self.CONCAVE))):
            with self.subTest(points=points):
                self.assertGreater(polygon_signed_area(validate_simple_polygon(points)), 0)

    def test_closing_and_consecutive_duplicate_cleanup(self):
        result = validate_simple_polygon(((0, 0), (1, 0), (1, 0),
                                          (1, 1), (0, 1), (0, 0)))
        self.assertEqual(len(result), 4)

    def test_invalid_profiles_are_rejected(self):
        cases = (((0, 0), (1, 0), (math.nan, 1)),
                 ((0, 0), (1, 1), (0, 1), (1, 0)),
                 ((0, 0), (1, 0), (2, 0)),
                 ((0, 0), (1e-14, 0), (0, 1)))
        for points in cases:
            with self.subTest(points=points), self.assertRaises(ValueError):
                validate_simple_polygon(points)

    def test_concave_triangulation_is_deterministic_and_area_complete(self):
        polygon, triangles = triangulate_simple_polygon(self.CONCAVE)
        self.assertEqual((polygon, triangles), triangulate_simple_polygon(self.CONCAVE))
        area = sum(abs(polygon_signed_area(tuple(polygon[i] for i in triangle)))
                   for triangle in triangles)
        self.assertAlmostEqual(area, polygon_signed_area(polygon))
        self.assertEqual(len(triangles), len(polygon) - 2)

        def inside_or_boundary(point):
            # Even/odd ray casting with an explicit boundary check.
            inside = False
            for index, start in enumerate(polygon):
                end = polygon[(index + 1) % len(polygon)]
                cross = ((end[0] - start[0]) * (point[1] - start[1])
                         - (end[1] - start[1]) * (point[0] - start[0]))
                if (abs(cross) <= 1.0e-12
                        and min(start[0], end[0]) <= point[0] <= max(start[0], end[0])
                        and min(start[1], end[1]) <= point[1] <= max(start[1], end[1])):
                    return True
                if ((start[1] > point[1]) != (end[1] > point[1])):
                    crossing_x = (start[0] + (point[1] - start[1])
                                  * (end[0] - start[0]) / (end[1] - start[1]))
                    if point[0] < crossing_x:
                        inside = not inside
            return inside

        for triangle in triangles:
            vertices = tuple(polygon[index] for index in triangle)
            samples = ((
                (sum(point[0] for point in vertices) / 3.0,
                 sum(point[1] for point in vertices) / 3.0),
            ) + tuple(
                ((vertices[index][0] + vertices[(index + 1) % 3][0]) / 2.0,
                 (vertices[index][1] + vertices[(index + 1) % 3][1]) / 2.0)
                for index in range(3)))
            self.assertTrue(all(inside_or_boundary(point) for point in samples))


class ExtrusionTests(unittest.TestCase):
    def test_concave_extrusion_is_closed_finite_and_outward(self):
        fragment = extrude_xz_profile(PolygonTests.CONCAVE, -.5, .5,
                                      part_type="FOUNDATION")
        self.assertTrue(validate_mesh_fragments((fragment,)))
        self.assertEqual(len(fragment.vertices), 12)
        self.assertTrue(all(math.isfinite(value) for v in fragment.vertices for value in v))

    def test_existing_box_fragment_still_passes_general_validator(self):
        layout = resolve_stair_layout(((0, 0), (3.6, 0)), "FORWARD", 0,
                                      2800, 16, 900, 30, 12)
        self.assertTrue(validate_mesh_fragments(build_tread_fragments(layout)))

    def test_bad_winding_is_rejected_not_just_vertex_count_checked(self):
        valid = extrude_xz_profile(((0, 0), (1, 0), (1, 1), (0, 1)), 0, 1)
        faces = list(valid.faces)
        faces[0] = tuple(reversed(faces[0]))
        with self.assertRaises(ValueError):
            validate_mesh_fragments((MeshFragment("BAD", 1, valid.vertices,
                                                  tuple(faces)),))


class ScopeTests(unittest.TestCase):
    def test_stage3_supersedes_temporary_public_scope_guard(self):
        production = "\n".join(path.read_text()
                               for path in (ROOT / "japanese_house_modeler").glob("*.py"))
        for required in ("JHM_OT_apply_residential_stair",
                          "JHM_OT_edit_residential_stair",
                          "JHM_OT_edit_stair_materials"):
            self.assertIn(required, production)

    def test_stage3_residential_actions_are_exposed_in_ui(self):
        ui = (ROOT / "japanese_house_modeler" / "ui.py").read_text()
        for name in ("jhm.apply_residential_stair",
                     "jhm.edit_residential_stair", "jhm.edit_stair_materials"):
            self.assertIn(name, ui)


if __name__ == "__main__":
    unittest.main()
