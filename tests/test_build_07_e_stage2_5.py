"""Build 07-E Stage-2.5 Candidate-r1 Winder-top regressions.

The exact-90 fixture was captured by executing ``stair_turn.py`` at Candidate
r1 commit b0d92fc15f7ec103e3cf18b6110dce2b5841fd3e.  It is a golden production
result, not a second implementation of the Candidate-r1 geometry formulas.
"""

import json
import math
import pathlib
import sys
import types
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).parents[1]
package = sys.modules.get("japanese_house_modeler")
if package is None:
    package = types.ModuleType("japanese_house_modeler")
    package.__path__ = [str(ROOT / "japanese_house_modeler")]
    sys.modules["japanese_house_modeler"] = package

from japanese_house_modeler import stair_turn
from japanese_house_modeler.stair_turn import (
    TurnSpec,
    prepare_winder_geometry,
)


R1_COMMIT = "b0d92fc15f7ec103e3cf18b6110dce2b5841fd3e"
R1_TREE = "e90e4bfa0e0583552bc761a200b8e51a52590470"
L_POINTS = ((0.0, 0.0), (0.0, 2.2), (-2.2, 2.2))
L_IDS = ("p0", "turn", "p2")
U_POINTS = ((0.0, 0.0), (0.0, 2.2), (0.9, 2.2), (0.9, 0.0))
U_IDS = ("p0", "t1", "t2", "p3")
ORACLE_PATH = (ROOT / "tests" / "fixtures" /
               "build_07_e_stage_2_5_candidate_r1_exact90_equal3.json")


def _winder_fragments(layout, fragments):
    ordinals = {
        2 * event_index + offset
        for event_index, event in enumerate(layout.rise_events)
        if event.owner == "WINDER_TREAD"
        for offset in (1, 2)
    }
    return tuple(part for part in fragments if part.ordinal in ordinals)


def _fragment_data(part):
    return {
        "ordinal": part.ordinal,
        "part_type": part.part_type,
        "vertices": [list(vertex) for vertex in part.vertices],
        "faces": [list(face) for face in part.faces],
    }


def _prepare(points, direction, ids, *, turn_specs=None, pattern="EQUAL_3",
             riser_count=16):
    return prepare_winder_geometry(
        points, direction, 0, 2800, riser_count, 900, 30, 12,
        point_ids=ids, turn_specs=turn_specs, winder_pattern=pattern,
        tread_front_overhang_mm=5)


class CandidateR1IdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.oracle = json.loads(ORACLE_PATH.read_text(encoding="utf-8"))

    def test_oracle_records_exact_candidate_r1_authority(self):
        self.assertEqual(self.oracle["authority"], {
            "commit": R1_COMMIT,
            "tree": R1_TREE,
        })

    def test_exact90_equal3_preserves_r1_except_approved_rear_support(self):
        for direction in ("FORWARD", "REVERSE"):
            with self.subTest(direction=direction):
                layout, fragments, _mesh = _prepare(
                    L_POINTS, direction, L_IDS)
                actual = {
                    "ascent_direction": direction,
                    "rise_event_owners": [
                        event.owner for event in layout.rise_events
                    ],
                    "winder_fragments": [
                        _fragment_data(part)
                        for part in _winder_fragments(layout, fragments)
                    ],
                }
                expected = self.oracle["cases"][direction]
                self.assertEqual(actual["ascent_direction"],
                                 expected["ascent_direction"])
                self.assertEqual(actual["rise_event_owners"],
                                 expected["rise_event_owners"])
                self.assertEqual(len(actual["winder_fragments"]),
                                 len(expected["winder_fragments"]))
                for current, historical in zip(
                        actual["winder_fragments"],
                        expected["winder_fragments"]):
                    self.assertEqual(current["ordinal"], historical["ordinal"])
                    self.assertEqual(current["part_type"],
                                     historical["part_type"])
                    self.assertEqual(current["faces"], historical["faces"])
                    if current["part_type"] == "RISER":
                        self.assertEqual(current["vertices"],
                                         historical["vertices"])
                        continue
                    differences = []
                    for index, (new, old) in enumerate(zip(
                            current["vertices"], historical["vertices"])):
                        self.assertEqual(new[2], old[2])
                        if new[:2] != old[:2]:
                            differences.append((index, new, old))
                    # Fresh Stage 3 explicitly corrects only the front/rear
                    # finite outer endpoints, duplicated at bottom and top.
                    half = len(current["vertices"]) // 2
                    changed = tuple(index for index, _new, _old in differences)
                    self.assertIn(len(changed), (2, 4))
                    base_count = len(changed) // 2
                    self.assertEqual(
                        tuple(index + half for index in changed[:base_count]),
                        changed[base_count:])

    def test_production_uses_candidate_r1_per_cell_calls(self):
        with mock.patch.object(
                stair_turn, "resolve_physical_winder_plans",
                side_effect=AssertionError("Turn-wide plan entered production")):
            with mock.patch.object(
                    stair_turn, "physical_winder_tread_polygon",
                    wraps=stair_turn.physical_winder_tread_polygon) as tread:
                with mock.patch.object(
                        stair_turn, "resolve_winder_riser_plan",
                        wraps=stair_turn.resolve_winder_riser_plan) as riser:
                    layout, fragments, _mesh = _prepare(
                        L_POINTS, "FORWARD", L_IDS)
        self.assertEqual(tread.call_count, 3)
        # Three production Risers plus two exact hidden-rear outer contacts
        # reused by the preceding Treads at internal Winder interfaces.
        self.assertEqual(riser.call_count, 5)
        self.assertEqual(
            tuple(part.part_type
                  for part in _winder_fragments(layout, fragments)),
            ("TREAD", "RISER") * 3)


class RestoredProductionSmokeTests(unittest.TestCase):
    def assert_winder_smoke(self, layout, fragments, expected_treads):
        winder = _winder_fragments(layout, fragments)
        self.assertEqual(len(winder), expected_treads * 2)
        self.assertEqual(tuple(part.part_type for part in winder),
                         ("TREAD", "RISER") * expected_treads)
        self.assertEqual(tuple(part.ordinal for part in winder),
                         tuple(sorted(part.ordinal for part in winder)))
        self.assertTrue(all(math.isfinite(value)
                            for part in winder
                            for vertex in part.vertices
                            for value in vertex))

    def test_63_degree_equal3_forward_and_reverse(self):
        angle = math.radians(63.0)
        points = ((0.0, 0.0), (0.0, 2.2),
                  (-2.2 * math.sin(angle),
                   2.2 + 2.2 * math.cos(angle)))
        for direction in ("FORWARD", "REVERSE"):
            with self.subTest(direction=direction):
                layout, fragments, _mesh = _prepare(
                    points, direction, L_IDS)
                self.assertAlmostEqual(abs(layout.turn.theta), angle)
                self.assert_winder_smoke(layout, fragments, 3)

    def test_bf1_and_bf2_forward_and_reverse(self):
        for pattern in ("BF_1", "BF_2"):
            for direction in ("FORWARD", "REVERSE"):
                with self.subTest(pattern=pattern, direction=direction):
                    layout, fragments, _mesh = _prepare(
                        L_POINTS, direction, L_IDS, pattern=pattern)
                    self.assertEqual(layout.winder_counts, (2,))
                    self.assert_winder_smoke(layout, fragments, 2)

    def test_compact_u_equal_and_bf_combinations(self):
        combinations = (("EQUAL_2", "EQUAL_3"), ("BF_1", "BF_2"))
        for patterns in combinations:
            specs = tuple(
                TurnSpec(U_IDS[index + 1], "WINDER", pattern)
                for index, pattern in enumerate(patterns))
            for direction in ("FORWARD", "REVERSE"):
                with self.subTest(patterns=patterns, direction=direction):
                    layout, fragments, _mesh = _prepare(
                        U_POINTS, direction, U_IDS, turn_specs=specs)
                    self.assertEqual(layout.u_classification, "COMPACT_U")
                    self.assertEqual(layout.straight_allocation[1], 0)
                    self.assertEqual(layout.winder_counts, (2, 3) if
                                     patterns[1] == "EQUAL_3" else (2, 2))
                    self.assert_winder_smoke(
                        layout, fragments, sum(layout.winder_counts))


if __name__ == "__main__":
    unittest.main()
