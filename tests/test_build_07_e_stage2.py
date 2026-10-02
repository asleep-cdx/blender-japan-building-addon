"""Build 07-E Stage-2 generalized Turn production contracts."""
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

from japanese_house_modeler.stair_turn import (
    BF_RIGHT_ANGLE_TOLERANCE, ScopeUnsupportedError, TurnSpec,
    WINDER_BF_1, WINDER_BF_2, WINDER_EQUAL_2, WINDER_EQUAL_3,
    active_schema5_allocation, canonical_turn_specs, classify_adjacent_turns,
    compatibility_scalar_pattern, dimension_edit_auto_allocation,
    equal_pattern_fractions,
    manual_allocation_from_auto, physical_winder_tread_polygon, polygon_area,
    prepare_schema4_promotion, prepare_winder_geometry,
    promote_schema4_landing_allocation, reconcile_shared_interface,
    resolve_nominal_cells, resolve_turn_frame, resolve_winder_layout,
    path_move_validation_allocation, snap_angle_15,
    turn_settings_available,
)
from japanese_house_modeler.stair_guides import (
    move_failure_message, resolve_generalized_move_candidate,
    resolve_move_candidate,
)
from japanese_house_modeler.stair_residential import (
    ResidentialFields, assemble_material_slot_plan,
)

L = ((0, 0), (0, 2.2), (-2.2, 2.2))
L_IDS = ("p0", "turn", "p2")
U = ((0, 0), (0, 2.2), (.9, 2.2), (.9, 0))
U_IDS = ("p0", "t1", "t2", "p3")
BASE = ("FORWARD", 0, 2800, 16, 900, 30, 12)


def layout(points=L, ids=L_IDS, specs=None, **kw):
    return resolve_winder_layout(points, *BASE, point_ids=ids,
                                 turn_specs=specs, **kw)


class BFTests(unittest.TestCase):
    def test_01_bf1_fraction(self): self.assertEqual(equal_pattern_fractions(WINDER_BF_1), (2/3,))
    def test_02_bf2_fraction(self): self.assertEqual(equal_pattern_fractions(WINDER_BF_2), (1/3,))
    def test_03_bf_geometry(self):
        for p in (WINDER_BF_1, WINDER_BF_2):
            self.assertEqual(len(resolve_nominal_cells(resolve_turn_frame(*L, .9), p)), 2)
    def test_04_bf_mirror(self):
        a = resolve_nominal_cells(resolve_turn_frame(*L, .9), WINDER_BF_1)
        mirrored = tuple((x, -y) for x, y in L)
        b = resolve_nominal_cells(resolve_turn_frame(*mirrored, .9), WINDER_BF_1)
        self.assertEqual(tuple(tuple((x, -y) for x, y in c.polygon) for c in a), tuple(c.polygon for c in b))
    def test_05_reverse_identity(self):
        self.assertEqual(layout(winder_pattern=WINDER_BF_1).winder_pattern,
                         resolve_winder_layout(L, "REVERSE", *BASE[1:], point_ids=L_IDS,
                                               winder_pattern=WINDER_BF_1).winder_pattern)
    def test_06_bf_scope_error(self):
        angle = math.radians(63); p = ((0,0),(0,2.2),(-2.2*math.sin(angle),2.2+2.2*math.cos(angle)))
        with self.assertRaises(ScopeUnsupportedError) as caught: layout(p, L_IDS, winder_pattern=WINDER_BF_1)
        self.assertEqual(caught.exception.category, "SCOPE_UNSUPPORTED")
    def test_07_named_bf_tolerance(self): self.assertGreater(BF_RIGHT_ANGLE_TOLERANCE, 0)


class TurnAndUTests(unittest.TestCase):
    SPECS = (TurnSpec("t1", "WINDER", "EQUAL_2"), TurnSpec("t2", "WINDER", "EQUAL_3"))
    def test_08_per_turn_key(self): self.assertEqual(tuple(s.path_point_id for s in canonical_turn_specs(U_IDS, self.SPECS)), ("t1","t2"))
    def test_09_stage1_adapter(self): self.assertEqual(canonical_turn_specs(L_IDS, None)[0].winder_pattern, "EQUAL_3")
    def test_10_independent_patterns(self): self.assertEqual(layout(U,U_IDS,self.SPECS).winder_counts, (2,3))
    def test_11_bf_combinations(self):
        for patterns in (("BF_1","EQUAL_3"),("BF_1","BF_2")):
            specs=tuple(TurnSpec(U_IDS[i+1],"WINDER",p) for i,p in enumerate(patterns))
            self.assertEqual(layout(U,U_IDS,specs).winder_counts, (2, 3 if patterns[1]=="EQUAL_3" else 2))
    def test_12_mixed_landing_winder(self):
        x=layout(U,U_IDS,(TurnSpec("t1","LANDING","NONE"),TurnSpec("t2","WINDER","EQUAL_3")))
        self.assertEqual((x.landing_count,x.winder_counts),(1,(0,3)))
    def test_13_separated(self): self.assertEqual(classify_adjacent_turns(1.1,.45,.45)[0],"SEPARATED_U")
    def test_14_compact(self): self.assertEqual(classify_adjacent_turns(.9,.45,.45)[0],"COMPACT_U")
    def test_15_overlap(self): self.assertEqual(classify_adjacent_turns(.8,.45,.45)[0],"INVALID_OVERLAP")
    def test_16_compact_zero_middle(self): self.assertEqual(layout(U,U_IDS,self.SPECS).straight_runs[1:2],(0.0,))
    def test_17_compact_allocation_zero(self): self.assertEqual(layout(U,U_IDS,self.SPECS).straight_allocation[1],0)
    def test_18_shared_cross_section(self): self.assertEqual(len(layout(U,U_IDS,self.SPECS).shared_interface),2)
    def test_19_rise_invariant(self): self.assertEqual(len(layout(U,U_IDS,self.SPECS).rise_events),16)
    def test_20_auto_deterministic(self): self.assertEqual(layout(U,U_IDS,self.SPECS).straight_allocation,layout(U,U_IDS,self.SPECS).straight_allocation)
    def test_21_reverse_canonical_allocation(self):
        f=layout(U,U_IDS,self.SPECS); r=resolve_winder_layout(U,"REVERSE",*BASE[1:],point_ids=U_IDS,turn_specs=self.SPECS)
        self.assertEqual(f.straight_allocation,r.straight_allocation)
    def test_22_no_duplicate_shared_riser(self):
        x,parts,_=prepare_winder_geometry(U,*BASE,point_ids=U_IDS,turn_specs=self.SPECS)
        self.assertEqual(sum(p.part_type=="RISER" for p in parts),sum(x.straight_allocation)+sum(x.winder_counts))


class AngleMigrationFinishTests(unittest.TestCase):
    def angled(self, degrees, mode="WINDER"):
        a=math.radians(degrees); points=((0,0),(0,2.2),(-2.2*math.sin(a),2.2+2.2*math.cos(a)))
        spec=(TurnSpec("turn",mode,"NONE" if mode=="LANDING" else "EQUAL_3"),)
        return layout(points,L_IDS,spec)
    def test_23_arbitrary_63_landing(self): self.assertAlmostEqual(abs(self.angled(63,"LANDING").turn.theta),math.radians(63))
    def test_24_exact90_landing_square(self): self.assertAlmostEqual(polygon_area(layout(turn_mode="LANDING",winder_pattern="NONE").turn.envelope),.81)
    def test_25_arbitrary_equal3(self):
        x=self.angled(63); self.assertEqual(tuple(round(math.degrees((c.rear_fraction-c.front_fraction)*abs(x.turn.theta))) for c in x.cells),(21,21,21))
    def test_26_arbitrary_mirror(self): self.assertAlmostEqual(self.angled(63).turn.theta,-self.angled(-63).turn.theta)
    def test_27_free_angle_47(self): self.assertAlmostEqual(abs(self.angled(47).turn.theta),math.radians(47))
    def test_28_shift15(self): self.assertAlmostEqual(math.degrees(snap_angle_15(math.radians(47))),45)
    def test_29_promotion(self): self.assertEqual(promote_schema4_landing_allocation((6,5,5)),(5,4,4))
    def test_30_auto_manual_copy(self): self.assertEqual(manual_allocation_from_auto((5,0,4)),(5,0,4))
    def test_31_invalid_manual(self):
        with self.assertRaises(ValueError): layout(allocation=(1,1))
    def test_32_positive_nosing(self):
        x=resolve_winder_layout(L,*BASE,point_ids=L_IDS,tread_front_overhang_mm=5)
        physical=physical_winder_tread_polygon(x.cells[0],"FORWARD",x.turn.inner_pivot,.005,x.riser_thickness)
        self.assertNotEqual(physical,x.cells[0].polygon)
    def test_33_edge_constraints(self):
        with self.assertRaises(ValueError): resolve_winder_layout(L,*BASE,point_ids=L_IDS,tread_front_overhang_mm=5,tread_front_edge_mode="ROUND",tread_front_edge_size_mm=6)
    def test_34_width650_deterministic(self):
        args=(L,"FORWARD",0,2800,16,650,30,12)
        a=prepare_winder_geometry(*args,point_ids=L_IDS,tread_front_overhang_mm=5)[2]
        b=prepare_winder_geometry(*args,point_ids=L_IDS,tread_front_overhang_mm=5)[2]
        self.assertEqual(a,b)


class StaticReviewRegressionTests(unittest.TestCase):
    def test_35_schema4_u_selected_turn_only_promotion(self):
        specs, mode, allocation = prepare_schema4_promotion(
            U_IDS, 0, "WINDER", "EQUAL_2", "AUTO", (6, 5, 5))
        self.assertEqual(specs, (TurnSpec("t1", "WINDER", "EQUAL_2"),
                                 TurnSpec("t2", "LANDING", "NONE")))
        self.assertEqual((mode, allocation), ("AUTO", ()))

    def test_36_second_turn_can_be_edited_after_materialization(self):
        specs = list(prepare_schema4_promotion(
            U_IDS, 0, "WINDER", "EQUAL_2", "AUTO", ())[0])
        specs[1] = TurnSpec("t2", "WINDER", "EQUAL_3")
        self.assertEqual(layout(U, U_IDS, tuple(specs)).winder_counts, (2, 3))

    def test_37_manual_landing_promotion_preserves_manual(self):
        specs, mode, allocation = prepare_schema4_promotion(
            U_IDS, 1, "LANDING", "NONE", "MANUAL", (6, 5, 5))
        self.assertEqual((mode, allocation), ("MANUAL", (5, 4, 4)))
        self.assertTrue(all(spec.turn_mode == "LANDING" for spec in specs))

    def test_38_manual_winder_promotion_is_blocked_without_mutation(self):
        old = ("schema4", (6, 5, 5), None)
        with self.assertRaises(ValueError):
            prepare_schema4_promotion(
                U_IDS, 0, "WINDER", "EQUAL_2", "MANUAL", old[1])
        self.assertEqual(old, ("schema4", (6, 5, 5), None))

    def test_39_schema5_free_angle_63(self):
        raw = (-2.2 * math.sin(math.radians(63)),
               2.2 + 2.2 * math.cos(math.radians(63)))
        candidate = resolve_generalized_move_candidate(
            L, L_IDS, 2, raw, shift=False)
        self.assertAlmostEqual(abs(resolve_turn_frame(*candidate.points, .9).theta),
                               math.radians(63))

    def test_40_schema5_shift_nearest_15(self):
        raw = (-2.2 * math.sin(math.radians(63)),
               2.2 + 2.2 * math.cos(math.radians(63)))
        candidate = resolve_generalized_move_candidate(
            L, L_IDS, 2, raw, shift=True)
        degrees = abs(math.degrees(resolve_turn_frame(*candidate.points, .9).theta))
        self.assertAlmostEqual(degrees / 15.0, round(degrees / 15.0))

    def test_41_schema4_move_remains_exact_90(self):
        with self.assertRaises(ValueError):
            resolve_move_candidate(L, L_IDS, 2, (-1.7, 3.1), shift=False)

    def test_42_compact_actual_shared_section(self):
        specs = (TurnSpec("t1", "WINDER", "EQUAL_2"),
                 TurnSpec("t2", "WINDER", "EQUAL_3"))
        resolved = layout(U, U_IDS, specs)
        self.assertEqual((resolved.turns[0].inner_pivot,
                          resolved.turns[0].exit_outer), resolved.shared_interface)
        self.assertEqual((resolved.turns[1].inner_pivot,
                          resolved.turns[1].entry_outer), resolved.shared_interface)
        self.assertEqual((resolved.turn_cells[0][-1].polygon[0],
                          resolved.turn_cells[0][-1].polygon[-1]),
                         (resolved.turn_cells[1][0].polygon[0],
                          resolved.turn_cells[1][0].polygon[1]))

    def test_43_compact_interface_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError, "shared interface mismatch"):
            reconcile_shared_interface(((0, 0), (0, 1)),
                                       ((0, 0), (.01, 1)))

    def test_44_landing_arrival_riser_and_roles(self):
        specs = (TurnSpec("turn", "LANDING", "NONE"),)
        resolved, fragments, mesh = prepare_winder_geometry(
            L, *BASE, point_ids=L_IDS, turn_specs=specs)
        self.assertEqual([event.owner for event in resolved.rise_events].count(
            "LANDING_ARRIVAL"), 1)
        self.assertGreater(sum(part.part_type == "RISER" for part in fragments),
                           sum(resolved.straight_allocation))
        self.assertNotIn("LANDING", mesh.face_roles)

    def test_45_landing_roles_exist_in_residential_material_plan(self):
        _resolved, _fragments, mesh = prepare_winder_geometry(
            L, *BASE, point_ids=L_IDS,
            turn_specs=(TurnSpec("turn", "LANDING", "NONE"),))
        roles = dict(assemble_material_slot_plan(ResidentialFields()).role_indices)
        self.assertTrue(set(mesh.face_roles).issubset(roles))

    def _profile_mesh(self, mode):
        return prepare_winder_geometry(
            L, *BASE, point_ids=L_IDS, tread_front_overhang_mm=8,
            tread_front_edge_mode=mode, tread_front_edge_size_mm=3)[2]

    def test_46_bevel_actual_geometry_differs(self):
        square, bevel = self._profile_mesh("SQUARE"), self._profile_mesh("BEVEL")
        self.assertNotEqual(square.vertices, bevel.vertices)
        self.assertGreater(len(bevel.vertices), len(square.vertices))

    def test_47_round_actual_geometry_differs(self):
        square, rounded = self._profile_mesh("SQUARE"), self._profile_mesh("ROUND")
        self.assertNotEqual(square.vertices, rounded.vertices)
        self.assertGreater(len(rounded.vertices), len(square.vertices))

    def test_48_schema5_straight_treads_keep_profile(self):
        _layout, fragments, _mesh = prepare_winder_geometry(
            L, *BASE, point_ids=L_IDS, tread_front_overhang_mm=8,
            tread_front_edge_mode="BEVEL", tread_front_edge_size_mm=3)
        straight_profiles = [part for part in fragments
                             if part.part_type == "TREAD"
                             and len(part.vertices) > 8]
        self.assertGreater(len(straight_profiles), 0)

    def test_49_reverse_equal4_local_indices(self):
        resolved = resolve_winder_layout(
            L, "REVERSE", *BASE[1:], point_ids=L_IDS,
            winder_pattern="EQUAL_4")
        self.assertEqual([event.owner_index for event in resolved.rise_events
                          if event.owner == "WINDER_TREAD"], [1, 2, 3, 4])

    def test_50_reverse_u_indices_restart_per_uphill_component(self):
        specs = (TurnSpec("t1", "WINDER", "EQUAL_2"),
                 TurnSpec("t2", "WINDER", "EQUAL_3"))
        resolved = resolve_winder_layout(
            U, "REVERSE", *BASE[1:], point_ids=U_IDS, turn_specs=specs)
        indices = [event.owner_index for event in resolved.rise_events
                   if event.owner == "WINDER_TREAD"]
        self.assertEqual(indices, [1, 2, 3, 1, 2])

    def test_51_invalid_candidate_does_not_mutate_turn_specs(self):
        specs = (TurnSpec("turn", "WINDER", "EQUAL_3"),)
        snapshot = tuple(specs)
        with self.assertRaises(ValueError):
            layout(((0, 0), (.1, 0), (.1, 1)), L_IDS, specs)
        self.assertEqual(specs, snapshot)

    def test_52_manual_active_allocation(self):
        self.assertEqual(active_schema5_allocation(
            "MANUAL", (8, 4), (5, 7)), (5, 7))

    def test_53_schema4_manual_turn_settings_available(self):
        self.assertTrue(turn_settings_available(4, "MANUAL"))

    def test_54_schema4_manual_landing_available_by_ui_policy(self):
        self.assertTrue(turn_settings_available(4, "MANUAL"))
        specs, mode, allocation = prepare_schema4_promotion(
            U_IDS, 0, "LANDING", "NONE", "MANUAL", (6, 5, 5))
        self.assertEqual((mode, allocation), ("MANUAL", (5, 4, 4)))
        self.assertEqual(specs[0].turn_mode, "LANDING")

    def test_55_schema4_manual_winder_still_blocked(self):
        with self.assertRaisesRegex(ValueError, "先にAUTO"):
            prepare_schema4_promotion(
                U_IDS, 0, "WINDER", "EQUAL_2", "MANUAL", (6, 5, 5))

    def test_56_auto_path_move_recomputes_allocation(self):
        self.assertIsNone(path_move_validation_allocation("AUTO", (5, 0, 4)))

    def test_57_manual_path_move_keeps_manual_allocation(self):
        self.assertEqual(path_move_validation_allocation(
            "MANUAL", (5, 0, 4)), (5, 0, 4))

    def test_58_separated_to_compact_auto_reallocates(self):
        separated = ((0, 0), (0, 2.2), (1.1, 2.2), (1.1, 0))
        specs = (TurnSpec("t1", "WINDER", "EQUAL_2"),
                 TurnSpec("t2", "WINDER", "EQUAL_3"))
        old = layout(separated, U_IDS, specs).straight_allocation
        with self.assertRaises(ValueError):
            layout(U, U_IDS, specs, allocation=old)
        moved = layout(U, U_IDS, specs,
                       allocation=path_move_validation_allocation("AUTO", old))
        self.assertEqual(moved.straight_allocation[1], 0)

    def test_59_compact_to_separated_auto_reallocates(self):
        separated = ((0, 0), (0, 2.2), (1.1, 2.2), (1.1, 0))
        specs = (TurnSpec("t1", "WINDER", "EQUAL_2"),
                 TurnSpec("t2", "WINDER", "EQUAL_3"))
        old = layout(U, U_IDS, specs).straight_allocation
        with self.assertRaises(ValueError):
            layout(separated, U_IDS, specs, allocation=old)
        moved = layout(separated, U_IDS, specs,
                       allocation=path_move_validation_allocation("AUTO", old))
        self.assertGreater(moved.straight_allocation[1], 0)

    def test_60_single_landing_scalar_synchronizes_to_none(self):
        specs = (TurnSpec("turn", "LANDING", "NONE"),)
        self.assertEqual(compatibility_scalar_pattern(specs, "EQUAL_3"), "NONE")

    def test_61_multi_turn_scalar_is_only_none_sentinel(self):
        specs = (TurnSpec("t1", "WINDER", "EQUAL_2"),
                 TurnSpec("t2", "WINDER", "EQUAL_3"))
        self.assertEqual(compatibility_scalar_pattern(specs, "EQUAL_3"), "NONE")

    def test_62_stage1_empty_specs_keep_legacy_scalar(self):
        self.assertEqual(compatibility_scalar_pattern((), "EQUAL_3"), "EQUAL_3")

    def test_63_schema5_auto_dimension_edit_invalidates_allocation(self):
        self.assertIsNone(dimension_edit_auto_allocation(
            5, "AUTO", (4, 2, 4)))

    def test_64_schema5_manual_dimension_edit_retains_authority(self):
        stored = (4, 2, 4)
        self.assertIs(dimension_edit_auto_allocation(
            5, "MANUAL", stored), stored)

    def test_65_width_change_does_not_reuse_stale_auto(self):
        points = ((0, 0), (0, 3), (1.8, 3), (1.8, 0))
        specs = (TurnSpec("t1", "WINDER", "EQUAL_2"),
                 TurnSpec("t2", "WINDER", "EQUAL_3"))
        before = resolve_winder_layout(
            points, *BASE[:4], 900, *BASE[5:], point_ids=U_IDS,
            turn_specs=specs)
        active = dimension_edit_auto_allocation(
            5, "AUTO", before.straight_allocation)
        after = resolve_winder_layout(
            points, *BASE[:4], 1500, *BASE[5:], point_ids=U_IDS,
            turn_specs=specs, allocation=active)
        self.assertNotEqual(before.straight_allocation,
                            after.straight_allocation)

    def test_66_schema4_auto_dimension_regression(self):
        self.assertIsNone(dimension_edit_auto_allocation(
            4, "AUTO", (6, 5, 5)))

    def test_67_schema5_failure_message_is_generalized_reason(self):
        reason = "SCOPE_UNSUPPORTED: BF patternはright-angle Turnのみ対応します。"
        message = move_failure_message(5, 1, 3, ValueError(reason))
        self.assertEqual(message, reason)
        self.assertNotIn("90度条件を維持", message)

    def test_68_schema4_failure_message_keeps_exact90_policy(self):
        message = move_failure_message(4, 1, 3, ValueError("geometry"))
        self.assertIn("90度条件を維持", message)

if __name__ == "__main__": unittest.main()
