"""Pure and structural coverage for Build 07-B Stage 2 underbody."""

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
    polygon_signed_area, resolve_stair_layout, validate_mesh_fragments,
)
from japanese_house_modeler.stair_residential import (
    BASIC_TREAD_RISER, STANDARD_RESIDENTIAL, ResidentialFields,
    validate_stepped_underbody_thickness,
)
from japanese_house_modeler.stair_residential_geometry import (
    build_underbody_fragment, prepare_stage2_residential_geometry,
    stepped_underbody_inner_profile, stepped_underbody_outer_profile,
    stepped_underbody_profile,
)
from japanese_house_modeler.stair_state import (
    INVALID_CANONICAL, StairState, diagnose_stair,
)


OFF = ResidentialFields(left_side_board_enabled=False,
                        right_side_board_enabled=False)


def layout(path=((0, 0), (3.6, 0)), direction="FORWARD", base=0):
    return resolve_stair_layout(path, direction, base, 2800, 16, 900, 30, 12)


def prepare(**changes):
    values = dict(points=((0, 0), (3.6, 0)), ascent_direction="FORWARD",
                  base_z_mm=0, floor_to_floor_mm=2800, riser_count=16,
                  stair_width_mm=900, tread_thickness_mm=30,
                  riser_thickness_mm=12, fields=OFF)
    values.update(changes)
    return prepare_stage2_residential_geometry(**values)


class AnalyticalProfileTests(unittest.TestCase):
    def assertPointsAlmostEqual(self, actual, expected):
        self.assertEqual(len(actual), len(expected))
        for actual_point, expected_point in zip(actual, expected):
            for actual_value, expected_value in zip(actual_point, expected_point):
                self.assertAlmostEqual(actual_value, expected_value)

    def test_inner_standard_exact_sequence_and_endpoints(self):
        inner = stepped_underbody_inner_profile(layout())
        self.assertPointsAlmostEqual(
            inner[:5], ((.012, 0), (.012, .145), (.252, .145),
                        (.252, .32), (.492, .32)))
        self.assertPointsAlmostEqual(inner[-1:], ((3.612, 2.595),))
        self.assertTrue(all(a != b for a, b in zip(inner, inner[1:])))

    def test_outer_uses_translated_line_intersections_and_exact_terminations(self):
        stair = layout()
        inner = stepped_underbody_inner_profile(stair)
        outer = stepped_underbody_outer_profile(inner, .0095, stair.base_z)
        self.assertPointsAlmostEqual(
            outer[:5], ((.0215, 0), (.0215, .1355),
                        (.2615, .1355), (.2615, .3105),
                        (.5015, .3105)))
        self.assertPointsAlmostEqual(outer[-1:], ((3.612, 2.5855),))

    def test_closed_profile_bounds_area_and_simplicity(self):
        result = stepped_underbody_profile(layout(base=425), OFF)
        self.assertAlmostEqual(min(z for _, z in result.polygon), .425)
        self.assertAlmostEqual(max(x for x, _ in result.polygon), 3.612)
        self.assertNotAlmostEqual(max(x for x, _ in result.polygon), 3.6215)
        self.assertGreater(polygon_signed_area(result.polygon), 0)
        self.assertEqual(result.inner[0], (.012, .425))
        self.assertEqual(result.outer[0], (.012, .425))
        self.assertEqual(result.outer[1], (.39, .425))


class ThicknessTests(unittest.TestCase):
    def test_default_is_supported(self):
        stair = layout()
        self.assertEqual(validate_stepped_underbody_thickness(
            OFF, stair.actual_riser, stair.tread_thickness,
            stair.riser_thickness), .0095)

    def test_boundaries_nonfinite_and_above_are_rejected(self):
        stair = layout()
        for value in (0, -1, math.nan, math.inf):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_stepped_underbody_thickness(
                    replace(OFF, underside_thickness_mm=value),
                    stair.actual_riser, stair.tread_thickness,
                    stair.riser_thickness)

    def test_positive_thickness_is_not_tied_to_old_offset_limits(self):
        stair = layout()
        for value in (12, 145, 1000):
            self.assertEqual(validate_stepped_underbody_thickness(
                replace(OFF, underside_thickness_mm=value),
                stair.actual_riser, stair.tread_thickness,
                stair.riser_thickness), value / 1000.0)

    def test_mode_aware_diagnosis_leaves_basic_unused_value_legal(self):
        common = dict(stair_id="id", path_points=((0, 0), (3.6, 0)),
                      ascent_direction="FORWARD", base_z_mm=0,
                      floor_to_floor_mm=2800, riser_count=16,
                      stair_width_mm=900, tread_thickness_mm=30,
                      riser_thickness_mm=12,
                      residential=replace(OFF, underside_thickness_mm=-123))
        self.assertNotIn(INVALID_CANONICAL, diagnose_stair(StairState(**common)))
        residential = StairState(**common, assembly_mode=STANDARD_RESIDENTIAL,
                                 stair_schema_version=2)
        self.assertIn(INVALID_CANONICAL, diagnose_stair(residential))


class SolidAndAssemblyTests(unittest.TestCase):
    def test_underbody_is_one_closed_outward_full_width_fragment(self):
        fragment = build_underbody_fragment(layout(), OFF)
        self.assertEqual(fragment.part_type, "UNDERBODY")
        self.assertTrue(validate_mesh_fragments((fragment,)))
        self.assertAlmostEqual(min(v[1] for v in fragment.vertices), -.45)
        self.assertAlmostEqual(max(v[1] for v in fragment.vertices), .45)
        self.assertTrue(all(math.isfinite(n) for v in fragment.vertices for n in v))

    def test_assembly_has_treads_risers_and_only_one_underbody(self):
        stair, fragments, mesh = prepare()
        counts = {kind: sum(f.part_type == kind for f in fragments)
                  for kind in ("TREAD", "RISER", "UNDERBODY", "SIDE_BOARD")}
        self.assertEqual(counts, {"TREAD": 15, "RISER": 16,
                                  "UNDERBODY": 1, "SIDE_BOARD": 0})
        self.assertTrue(mesh.vertices and mesh.faces)
        self.assertEqual(stair.run_length, 3.6)

    def test_side_boards_on_are_rejected_not_silently_ignored(self):
        with self.assertRaises(ValueError):
            prepare(fields=ResidentialFields())

    def test_forward_reverse_oblique_and_nonzero_base_follow_resolved_axes(self):
        path = ((1, 2), (4, 6))
        forward = build_underbody_fragment(layout(path, "FORWARD", 300), OFF)
        reverse = build_underbody_fragment(layout(path, "REVERSE", 300), OFF)
        self.assertAlmostEqual(min(v[2] for v in forward.vertices), .3)
        self.assertAlmostEqual(min(v[2] for v in reverse.vertices), .3)
        # Lower profile starts near the respective resolved lower endpoint.
        self.assertLess(min(math.dist(v[:2], path[0]) for v in forward.vertices), .5)
        self.assertLess(min(math.dist(v[:2], path[1]) for v in reverse.vertices), .5)
        self.assertNotEqual(forward.vertices, reverse.vertices)


class ScopeAndRuntimePathTests(unittest.TestCase):
    def test_basic_preparer_remains_tread_riser_only(self):
        from japanese_house_modeler.stair_geometry import prepare_stair_geometry
        _, fragments, _ = prepare_stair_geometry(
            ((0, 0), (3.6, 0)), "FORWARD", 0, 2800, 16, 900, 30, 12)
        self.assertEqual({f.part_type for f in fragments}, {"TREAD", "RISER"})

    def test_runtime_hook_is_non_registered_and_public_scope_remains_closed(self):
        operators = (ROOT / "japanese_house_modeler" / "stair_operators.py").read_text()
        addon = "\n".join(p.read_text() for p in
                           (ROOT / "japanese_house_modeler").glob("*.py"))
        self.assertIn("regenerate_stage2_residential_for_runtime", operators)
        for forbidden in ("jhm.apply_residential_stair",
                          "jhm.edit_residential_stair",
                          "jhm.edit_stair_materials"):
            self.assertNotIn(forbidden, addon)
        ui = (ROOT / "japanese_house_modeler" / "ui.py").read_text()
        self.assertNotIn("underside_thickness_mm", ui)


if __name__ == "__main__":
    unittest.main()
