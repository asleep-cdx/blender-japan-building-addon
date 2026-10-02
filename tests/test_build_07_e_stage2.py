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
    canonical_turn_specs, classify_adjacent_turns, equal_pattern_fractions,
    manual_allocation_from_auto, physical_winder_tread_polygon, polygon_area,
    prepare_winder_geometry, promote_schema4_landing_allocation,
    resolve_nominal_cells, resolve_turn_frame, resolve_winder_layout,
    snap_angle_15,
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

if __name__ == "__main__": unittest.main()
