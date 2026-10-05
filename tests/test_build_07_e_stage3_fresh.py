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
        with self.assertRaisesRegex(ValueError, "Stage 3B"):
            prepare_turn_residential_geometry(
                fields=ResidentialFields(
                    underside_mode="SLOPED_CLOSED",
                    left_side_board_enabled=False,
                    right_side_board_enabled=False), **_kwargs())
        with self.assertRaisesRegex(ValueError, "Stage 3C"):
            prepare_turn_residential_geometry(
                fields=ResidentialFields(), **_kwargs())


if __name__ == "__main__":
    unittest.main()
