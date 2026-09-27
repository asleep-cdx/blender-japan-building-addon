"""Build 07-D Stage 1 multi-point L foundation contracts."""

import pathlib
import sys
import types
import unittest

ROOT = pathlib.Path(__file__).parents[1]
package = types.ModuleType("japanese_house_modeler")
package.__path__ = [str(ROOT / "japanese_house_modeler")]
sys.modules.setdefault("japanese_house_modeler", package)

from japanese_house_modeler.stair_geometry import canonical_path, prepare_stair_geometry
from japanese_house_modeler.stair_multiflight import (
    MULTIPOINT_SCHEMA_VERSION, PathPoint, auto_distribute_risers,
    canonical_multi_path, prepare_multiflight_geometry,
    project_l_creation_candidate, resolve_multiflight_layout,
)
from japanese_house_modeler.stair_state import (
    INVALID_CANONICAL, StairState, diagnose_stair,
)


ARGS = (((0, 0), (3.0, 0), (3.0, 3.0)), "FORWARD", 100, 2800, 16,
        900, 30, 12)


class IdentityAndCompatibilityTests(unittest.TestCase):
    def test_build_identity(self):
        source = (ROOT / "japanese_house_modeler/__init__.py").read_text()
        self.assertIn('"version": (0, 7, 3)', source)
        self.assertIn("Build 07-D: Multi-point Path + L/U + Landing", source)

    def test_legacy_canonical_path_is_still_exactly_two_points(self):
        self.assertEqual(canonical_path(((0, 0), (1, 0))), ((0.0, 0.0), (1.0, 0.0)))
        with self.assertRaises(ValueError):
            canonical_path(((0, 0), (1, 0), (1, 1)))

    def test_schema_1_2_3_are_not_rewritten_on_read(self):
        source = (ROOT / "japanese_house_modeler/stair_operators.py").read_text()
        self.assertIn('if values["stair_schema_version"] >= MULTIPOINT_SCHEMA_VERSION', source)
        self.assertEqual(MULTIPOINT_SCHEMA_VERSION, 4)

    def test_straight_geometry_regression(self):
        mesh = prepare_stair_geometry(
            ((0, 0), (3.6, 0)), "FORWARD", 0, 2800, 16, 900, 30, 12)[2]
        self.assertEqual((len(mesh.vertices), len(mesh.faces)), (248, 186))


class CanonicalAndValidationTests(unittest.TestCase):
    def test_creation_projection_makes_slightly_skewed_click_exactly_90_degrees(self):
        p0, p1, raw = (1, 1), (4, 2), (3.15, 5.1)
        p2 = project_l_creation_candidate(p0, p1, raw)
        incoming = (p1[0] - p0[0], p1[1] - p0[1])
        outgoing = (p2[0] - p1[0], p2[1] - p1[1])
        self.assertAlmostEqual(sum(a * b for a, b in zip(incoming, outgoing)), 0.0)
        self.assertEqual(tuple(p.xy for p in canonical_multi_path((p0, p1, p2)))[-1],
                         p2)

    def test_valid_rotated_left_and_right_l(self):
        for points in (((0, 0), (2, 2), (0, 4)),
                       ((0, 0), (2, 2), (4, 0))):
            path = canonical_multi_path(points, ("p0", "p1", "p2"))
            self.assertEqual(tuple(p.point_id for p in path), ("p0", "p1", "p2"))
            self.assertTrue(all(isinstance(p, PathPoint) for p in path))

    def test_duplicate_and_short_points_rejected(self):
        for points in (((0, 0), (0, 0), (0, 1)),
                       ((0, 0), (1e-8, 0), (1e-8, 1))):
            with self.subTest(points=points), self.assertRaises(ValueError):
                canonical_multi_path(points)

    def test_nonfinite_point_rejected(self):
        with self.assertRaises(ValueError):
            canonical_multi_path(((0, 0), (float("nan"), 0), (1, 1)))

    def test_non_right_angle_rejected(self):
        with self.assertRaises(ValueError):
            canonical_multi_path(((0, 0), (2, 0), (3, 1)))

    def test_too_short_after_landing_cutback_rejected(self):
        with self.assertRaises(ValueError):
            resolve_multiflight_layout(
                ((0, 0), (.4, 0), (.4, 2)), "FORWARD", 0, 2800, 16,
                900, 30, 12)


class ResolutionTests(unittest.TestCase):
    def test_effective_cutback_and_auto_distribution(self):
        layout = resolve_multiflight_layout(*ARGS)
        self.assertEqual(tuple(f.effective_run for f in layout.flights), (2.55, 2.55))
        self.assertEqual(layout.allocation, (8, 8))
        self.assertEqual(sum(layout.allocation), 16)
        self.assertTrue(all(value >= 2 for value in layout.allocation))

    def test_auto_is_deterministic_and_ties_use_canonical_order(self):
        self.assertEqual(auto_distribute_risers((2, 1), 9), (6, 3))
        self.assertEqual(auto_distribute_risers((1, 1), 5), (3, 2))

    def test_insufficient_or_impossible_auto_rejected(self):
        for runs, count in (((1, 1), 3), ((1, 0), 8)):
            with self.subTest(runs=runs), self.assertRaises(ValueError):
                auto_distribute_risers(runs, count)

    def test_common_riser_landing_and_upper_invariants(self):
        layout = resolve_multiflight_layout(*ARGS)
        self.assertTrue(all(f.actual_riser == layout.actual_riser
                            for f in layout.flights))
        self.assertAlmostEqual(layout.landing.top_z,
                               .1 + layout.allocation[0] * layout.actual_riser)
        self.assertAlmostEqual(layout.upper_arrival_z, .1 + 2.8)
        self.assertAlmostEqual(layout.flights[-1].end_z, layout.upper_arrival_z)

    def test_reverse_changes_traversal_not_canonical_path(self):
        ids = ("start", "turn", "end")
        forward = resolve_multiflight_layout(*ARGS, point_ids=ids)
        reverse_args = (ARGS[0], "REVERSE", *ARGS[2:])
        reverse = resolve_multiflight_layout(*reverse_args, point_ids=ids)
        expected = tuple(point.xy for point in forward.canonical_path)
        self.assertEqual(tuple(point.xy for point in reverse.canonical_path), expected)
        self.assertEqual(reverse.traversal_point_ids, tuple(reversed(ids)))
        self.assertEqual(reverse.allocation, forward.allocation)

    def test_auto_riser_edit_recalculates_and_produces_storable_snapshot(self):
        old = resolve_multiflight_layout(*ARGS)
        edited = resolve_multiflight_layout(
            ARGS[0], ARGS[1], ARGS[2], ARGS[3], 17, *ARGS[5:], allocation=None)
        self.assertEqual(old.allocation, (8, 8))
        self.assertEqual(sum(edited.allocation), 17)
        restored = resolve_multiflight_layout(
            ARGS[0], ARGS[1], ARGS[2], ARGS[3], 17, *ARGS[5:],
            allocation=edited.allocation)
        self.assertEqual(restored.allocation, edited.allocation)

    def test_width_edit_recalculates_using_new_effective_runs(self):
        points = ((0, 0), (5, 0), (5, 2))
        narrow = resolve_multiflight_layout(
            points, "FORWARD", 0, 2800, 10, 900, 30, 12)
        wide = resolve_multiflight_layout(
            points, "FORWARD", 0, 2800, 10, 3000, 30, 12)
        self.assertNotEqual(narrow.allocation, wide.allocation)
        self.assertEqual(sum(wide.allocation), 10)

    def test_ordinary_regenerate_preserves_valid_saved_allocation(self):
        saved = (7, 9)
        regenerated = resolve_multiflight_layout(*ARGS, allocation=saved)
        self.assertEqual(regenerated.allocation, saved)


class SchemaFourDiagnosisTests(unittest.TestCase):
    def state(self, **changes):
        values = dict(
            stair_id="managed", path_points=ARGS[0], ascent_direction=ARGS[1],
            base_z_mm=ARGS[2], floor_to_floor_mm=ARGS[3], riser_count=ARGS[4],
            stair_width_mm=ARGS[5], tread_thickness_mm=ARGS[6],
            riser_thickness_mm=ARGS[7], stair_schema_version=4,
            point_ids=("p0", "p1", "p2"), turn_mode="LANDING",
            riser_distribution_mode="AUTO", auto_riser_allocation=(8, 8))
        values.update(changes)
        return StairState(**values)

    def test_invalid_saved_allocation_is_invalid_canonical(self):
        for allocation in ((8,), (1, 15), (8, 7), ("bad", "8")):
            with self.subTest(allocation=allocation):
                self.assertIn(INVALID_CANONICAL, diagnose_stair(
                    self.state(auto_riser_allocation=allocation)))

    def test_empty_duplicate_or_wrong_count_point_ids_are_invalid(self):
        for ids in (("p0", "", "p2"), ("same", "same", "p2"), ("p0", "p1")):
            with self.subTest(ids=ids):
                self.assertIn(INVALID_CANONICAL,
                              diagnose_stair(self.state(point_ids=ids)))

    def test_turn_and_distribution_modes_are_validated(self):
        self.assertIn(INVALID_CANONICAL,
                      diagnose_stair(self.state(turn_mode="WINDER")))
        self.assertIn(INVALID_CANONICAL,
                      diagnose_stair(self.state(riser_distribution_mode="MANUAL")))

    def test_schema_1_2_3_diagnosis_remains_non_schema4(self):
        for schema in (1, 2, 3):
            state = StairState(
                "legacy", ((0, 0), (3.6, 0)), "FORWARD", 0, 2800, 16,
                900, 30, 12, stair_schema_version=schema)
            with self.subTest(schema=schema):
                self.assertNotIn(INVALID_CANONICAL, diagnose_stair(state))


class GeometryAndTransactionBoundaryTests(unittest.TestCase):
    def test_one_combined_mesh_and_landing_tread_role(self):
        layout, fragments, mesh = prepare_multiflight_geometry(*ARGS)
        self.assertGreater(len(mesh.vertices), 0)
        self.assertEqual(len(mesh.face_roles), len(mesh.faces))
        landing = [part for part in fragments
                   if part.part_type == layout.landing.material_role]
        self.assertTrue(landing)
        self.assertEqual(layout.landing.material_role, "TREAD")
        self.assertNotIn("LANDING", mesh.face_roles)

    def test_invalid_candidate_fails_in_pure_prepare(self):
        with self.assertRaises(ValueError):
            prepare_multiflight_geometry(
                ((0, 0), (2, 0), (3, 1)), "FORWARD", 0, 2800, 16,
                900, 30, 12)

    def test_operator_prepares_before_scene_mutation(self):
        source = (ROOT / "japanese_house_modeler/stair_operators.py").read_text()
        prepare = source.index("prepare_multiflight_geometry(")
        mutation = source.index('bpy.data.meshes.new("JHM Stair")')
        self.assertLess(prepare, mutation)

    def test_operator_separates_auto_edit_from_regenerate_preservation(self):
        source = (ROOT / "japanese_house_modeler/stair_operators.py").read_text()
        self.assertIn('candidate["auto_riser_allocation"] = None', source)
        self.assertIn('values["auto_riser_allocation"] = layout.allocation', source)
        self.assertIn(
            'return self._run_candidate(context, _canonical_snapshot(obj.jhm_stair))',
            source)

    def test_modal_preview_and_commit_share_creation_projection(self):
        source = (ROOT / "japanese_house_modeler/stair_operators.py").read_text()
        self.assertIn("self._candidate = self._resolve_creation_candidate", source)
        self.assertIn("point = self._resolve_creation_candidate(point)", source)


if __name__ == "__main__":
    unittest.main()
