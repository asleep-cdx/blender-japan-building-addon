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
    resolve_multiflight_layout,
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


if __name__ == "__main__":
    unittest.main()
