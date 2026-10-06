"""Fresh Build 07-E Stage-3A visual stepped-body regressions."""

import math
import pathlib
import sys
import types
import unittest


ROOT = pathlib.Path(__file__).parents[1]
package = sys.modules.get("japanese_house_modeler")
if package is None:
    package = types.ModuleType("japanese_house_modeler")
    package.__path__ = [str(ROOT / "japanese_house_modeler")]
    sys.modules["japanese_house_modeler"] = package

from japanese_house_modeler.stair_residential import ResidentialFields
from japanese_house_modeler.stair_turn import (
    TurnSpec,
    prepare_turn_geometry,
    prepare_turn_residential_geometry,
)


L_POINTS = ((0.0, 0.0), (0.0, 2.2), (-2.2, 2.2))
L_IDS = ("p0", "turn", "p2")
U_POINTS = ((0.0, 0.0), (0.0, 2.2), (0.9, 2.2), (0.9, 0.0))
U_IDS = ("p0", "t1", "t2", "p3")
FIELDS = ResidentialFields(
    left_side_board_enabled=False, right_side_board_enabled=False,
    tread_front_overhang_mm=5.0)


def _kwargs(points=L_POINTS, direction="FORWARD", ids=L_IDS, **extra):
    values = dict(
        points=points, ascent_direction=direction, base_z_mm=0,
        floor_to_floor_mm=2800, riser_count=16, stair_width_mm=900,
        tread_thickness_mm=30, riser_thickness_mm=12, point_ids=ids,
        winder_pattern="EQUAL_3")
    values.update(extra)
    return values


def _top_signature(fragments):
    return tuple((part.part_type, part.ordinal, part.vertices, part.faces)
                 for part in fragments if part.part_type in ("TREAD", "RISER"))


class FreshStage3ASteppedBodyTests(unittest.TestCase):
    def prepare(self, **kwargs):
        return prepare_turn_residential_geometry(
            fields=FIELDS, **_kwargs(**kwargs))

    def assert_valid_body(self, fragments):
        bodies = tuple(part for part in fragments
                       if part.part_type == "UNDERBODY")
        self.assertTrue(bodies)
        self.assertTrue(all(math.isfinite(value)
                            for part in bodies for vertex in part.vertices
                            for value in vertex))
        self.assertTrue(all(len(part.vertices) >= 6 and len(part.faces) >= 5
                            for part in bodies))
        return bodies

    def assert_top_unchanged(self, **kwargs):
        basic = prepare_turn_geometry(
            **_kwargs(**kwargs),
            tread_front_overhang_mm=FIELDS.tread_front_overhang_mm,
            tread_front_edge_mode=FIELDS.tread_front_edge_mode,
            tread_front_edge_size_mm=FIELDS.tread_front_edge_size_mm)[1]
        residential = self.prepare(**kwargs)[1]
        self.assertEqual(_top_signature(residential), _top_signature(basic))

    def test_exact90_equal3_forward_and_reverse_body_and_frozen_top(self):
        for direction in ("FORWARD", "REVERSE"):
            with self.subTest(direction=direction):
                _layout, fragments, mesh = self.prepare(direction=direction)
                bodies = self.assert_valid_body(fragments)
                self.assertTrue(all(role == "UNDERSIDE" for role in
                                    mesh.face_roles[-sum(len(p.faces) for p in bodies):]))
                self.assert_top_unchanged(direction=direction)

    def test_repeated_generation_is_deterministic(self):
        first = self.prepare()
        second = self.prepare()
        self.assertEqual(first[1], second[1])
        self.assertEqual(first[2], second[2])

    def test_visible_soffit_uses_rise_top_closure_depth_authority(self):
        for direction in ("FORWARD", "REVERSE"):
            with self.subTest(direction=direction):
                first = self.prepare(direction=direction)
                second = self.prepare(direction=direction)
                bodies = self.assert_valid_body(first[1])
                lower_levels = tuple(
                    min(vertex[2] for vertex in body.vertices)
                    for body in bodies)
                self.assertAlmostEqual(lower_levels[0], 0.0)
                # Accepted stepped_closure_visible_profile authority:
                # second rise TOP 0.350m - closure depth 0.150m = 0.200m.
                straight_levels = {
                    round(vertex[2], 9) for vertex in bodies[0].vertices}
                self.assertIn(0.200, straight_levels)
                self.assertNotIn(0.170, straight_levels)
                self.assertEqual(first[1], second[1])
                self.assertEqual(first[2], second[2])
                self.assert_top_unchanged(direction=direction)

    def test_straight_body_is_set_back_from_tread_nosing_and_riser(self):
        for direction in ("FORWARD", "REVERSE"):
            with self.subTest(direction=direction):
                layout, fragments, _mesh = self.prepare(direction=direction)
                tread = next(part for part in fragments
                             if part.part_type == "TREAD")
                body = next(part for part in fragments
                            if part.part_type == "UNDERBODY")
                path = layout.canonical_path
                start, following = ((path[0].xy, path[1].xy)
                                    if direction == "FORWARD" else
                                    (path[-1].xy, path[-2].xy))
                vector = (following[0] - start[0], following[1] - start[1])
                length = math.hypot(*vector)
                forward = (vector[0] / length, vector[1] / length)
                station = lambda vertex: ((vertex[0] - start[0]) * forward[0]
                                          + (vertex[1] - start[1]) * forward[1])
                tread_front = min(station(vertex) for vertex in tread.vertices)
                body_front = min(station(vertex) for vertex in body.vertices)
                self.assertAlmostEqual(tread_front, -0.005)
                self.assertAlmostEqual(body_front, 0.012)
                self.assertGreater(body_front, tread_front)
                # The former copied footprint began at -5mm and left only
                # h-depth = 25mm as an exposed tab.  The accepted contact-side
                # body instead starts behind the 12mm Riser rear plane.
                self.assertGreater(body_front, 0.0)

    def test_winder_bodies_do_not_copy_physical_tread_footprints(self):
        layout, fragments, _mesh = self.prepare()
        treads = tuple(part for part in fragments if part.part_type == "TREAD")
        winder_treads = tuple(
            tread for tread, event in zip(treads, layout.rise_events)
            if event.owner == "WINDER_TREAD")
        winder_bodies = tuple(
            part for part in fragments if part.part_type == "UNDERBODY")[1:4]
        self.assertEqual(len(winder_treads), len(winder_bodies), 3)
        for tread, body in zip(winder_treads, winder_bodies):
            tread_plan = {vertex[:2] for vertex in tread.vertices}
            body_plan = {vertex[:2] for vertex in body.vertices}
            self.assertNotEqual(body_plan, tread_plan)
            self.assertFalse(body_plan.issuperset(tread_plan))

    def test_63_degree_equal3_smoke_and_frozen_top(self):
        angle = math.radians(63.0)
        points = ((0.0, 0.0), (0.0, 2.2),
                  (-2.2 * math.sin(angle), 2.2 + 2.2 * math.cos(angle)))
        self.assert_valid_body(self.prepare(points=points)[1])
        self.assert_top_unchanged(points=points)

    def test_bf_patterns_smoke(self):
        for pattern in ("BF_1", "BF_2"):
            with self.subTest(pattern=pattern):
                self.assert_valid_body(self.prepare(winder_pattern=pattern)[1])

    def test_compact_u_keeps_both_turns(self):
        specs = (TurnSpec("t1", "WINDER", "EQUAL_2"),
                 TurnSpec("t2", "WINDER", "EQUAL_3"))
        layout, fragments, _mesh = self.prepare(
            points=U_POINTS, ids=U_IDS, turn_specs=specs)
        self.assertEqual(layout.winder_counts, (2, 3))
        self.assertEqual(layout.u_classification, "COMPACT_U")
        self.assert_valid_body(fragments)
        self.assert_top_unchanged(points=U_POINTS, ids=U_IDS, turn_specs=specs)

    def test_deferred_variants_are_rejected_before_assembly(self):
        with self.assertRaisesRegex(ValueError, "Stage 3C"):
            prepare_turn_residential_geometry(
                fields=ResidentialFields(), **_kwargs())

    def test_closure_depth_not_exceeding_tread_thickness_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "closure depth"):
            prepare_turn_residential_geometry(
                fields=ResidentialFields(
                    side_board_band_width_mm=30.0,
                    left_side_board_enabled=False,
                    right_side_board_enabled=False), **_kwargs())


if __name__ == "__main__":
    unittest.main()
