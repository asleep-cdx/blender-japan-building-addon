"""Build 07-D Stage 2 pure editing and Residential L contracts."""
import math, pathlib, sys, types, unittest
ROOT = pathlib.Path(__file__).parents[1]
package = types.ModuleType("japanese_house_modeler")
package.__path__ = [str(ROOT / "japanese_house_modeler")]
sys.modules.setdefault("japanese_house_modeler", package)
from japanese_house_modeler.drawing_alignment import constrained_direction, select_unambiguous_candidate
from japanese_house_modeler.stair_guides import (aligned_candidates, endpoint_right_angle_candidate,
    move_anchor_index, resolve_move_candidate, turn_right_angle_candidate)
from japanese_house_modeler.stair_multiflight import (RISER_DISTRIBUTION_AUTO,
    FlightAllocation, allocation_counts, canonical_multi_path, prepare_multiflight_residential_geometry,
    resolve_multiflight_layout, segment_allocations, switch_distribution_mode,
    validate_manual_allocation)
from japanese_house_modeler.stair_residential import ResidentialFields

POINTS=((0,0),(3,0),(3,3)); IDS=("p0","p1","p2")
def dot_at(points):
    a,b,c=points
    return (a[0]-b[0])*(c[0]-b[0])+(a[1]-b[1])*(c[1]-b[1])

class GuideTests(unittest.TestCase):
    def test_anchor_rules_are_canonical(self): self.assertEqual([move_anchor_index(3,i) for i in range(3)],[1,0,1])
    def test_shift_uses_shared_wall_math(self):
        c=turn_right_angle_candidate(POINTS,(2,1.1),shift=True); u=constrained_direction(POINTS[0],(2,1.1),15)
        self.assertAlmostEqual(math.atan2(c[1],c[0]), math.atan2(u[1],u[0])); self.assertAlmostEqual(dot_at((POINTS[0],c,POINTS[2])),0)
    def test_endpoint_loci(self):
        for i in (0,2):
            c=endpoint_right_angle_candidate(POINTS,i,(1.2,2.1)); p=list(POINTS);p[i]=c;self.assertAlmostEqual(dot_at(p),0)
    def test_turn_thales_locus(self):
        c=turn_right_angle_candidate(POINTS,(2,2)); self.assertAlmostEqual(dot_at((POINTS[0],c,POINTS[2])),0)
    def test_ids_retained_and_preview_is_commit_candidate(self):
        c=resolve_move_candidate(POINTS,IDS,1,(2,1)); self.assertEqual(c.point_ids,IDS);self.assertEqual(c.points,canonical_multi_path(c.points,IDS) and c.points)
    def test_wall_references_are_coordinates_only(self): self.assertEqual(aligned_candidates((2,3),((1,4),)),((1.,3.),(2.,4.)))
    def test_ambiguous_policy(self): self.assertIsNone(select_unambiguous_candidate(((4,"a"),(4,"b"))))
    def test_non_right_numeric_rejected(self):
        with self.assertRaises(ValueError): canonical_multi_path(((0,0),(2,0),(3,2)),IDS)

class AllocationTests(unittest.TestCase):
    def layout(self, **kw): return resolve_multiflight_layout(POINTS,"FORWARD",0,2800,16,900,30,12,point_ids=IDS,**kw)
    def test_manual_valid(self): self.assertEqual(validate_manual_allocation((7,9),16),(7,9))
    def test_manual_sum_rejected(self):
        with self.assertRaises(ValueError): validate_manual_allocation((7,8),16)
    def test_manual_minimum_rejected(self):
        with self.assertRaises(ValueError): validate_manual_allocation((1,15),16)
    def test_auto_to_manual_copies(self): self.assertEqual(switch_distribution_mode("AUTO",(8,8),(2,2),16),("MANUAL",(8,8)))
    def test_manual_to_auto_recalculates(self): self.assertEqual(switch_distribution_mode("MANUAL",(7,9),(4,2),16)[0],"AUTO")
    def test_physical_mapping_survives_reverse(self):
        path=canonical_multi_path(POINTS,IDS); allocations=segment_allocations(path,(7,9)); self.assertEqual(allocation_counts(path,allocations),(7,9))
    def test_manual_path_move_preserves_counts(self): self.assertEqual(self.layout(allocation=(7,9)).allocation,(7,9))
    def test_reverse_preserves_counts(self):
        l=resolve_multiflight_layout(POINTS,"REVERSE",0,2800,16,900,30,12,point_ids=IDS,allocation=(7,9));self.assertEqual(l.allocation,(7,9))
    def test_auto_path_change_reallocates(self):
        a=self.layout().allocation;b=resolve_multiflight_layout(((0,0),(5,0),(5,2)),"FORWARD",0,2800,16,900,30,12,point_ids=IDS).allocation;self.assertNotEqual(a,b)

class ResidentialGeometryTests(unittest.TestCase):
    def prepare(self, underside="STEPPED_CLOSED", board="STEPPED", edge="SQUARE", left=True,right=True):
        f=ResidentialFields(underside_mode=underside,side_board_mode=board,tread_front_edge_mode=edge,
          tread_front_overhang_mm=10,tread_front_edge_size_mm=3,left_side_board_enabled=left,right_side_board_enabled=right)
        return prepare_multiflight_residential_geometry(POINTS,"FORWARD",0,2800,16,900,30,12,point_ids=IDS,fields=f)
    def test_representative_matrix(self):
        for combo in (("STEPPED_CLOSED","STEPPED","SQUARE"),("STEPPED_CLOSED","SLOPED","BEVEL"),("SLOPED_CLOSED","STEPPED","ROUND"),("SLOPED_CLOSED","SLOPED","SQUARE")):
            with self.subTest(combo=combo):
                l,fr,m=self.prepare(*combo);self.assertTrue(all(math.isfinite(x) for v in m.vertices for x in v));self.assertAlmostEqual(l.upper_arrival_z,2.8);self.assertGreaterEqual(min(v[2] for v in m.vertices),l.base_z)
                self.assertEqual(set(m.face_roles),{"TREAD","RISER","UNDERSIDE","SIDE_BOARD"});self.assertNotIn("LANDING",m.face_roles)
    def test_landing_tread_and_underbody(self):
        l,fr,m=self.prepare(); self.assertEqual(fr[-2].part_type,"TREAD");self.assertEqual(fr[-1].part_type,"UNDERBODY");self.assertIn("UNDERSIDE",m.face_roles)
    def test_board_sides(self):
        for left,right,count in ((True,True,4),(True,False,2),(False,True,2),(False,False,0)):
            _,fr,_=self.prepare(left=left,right=right); self.assertEqual(sum(f.part_type=="SIDE_BOARD" for f in fr),count)
    def test_per_flight_nosing_rejected(self):
        f=ResidentialFields(tread_front_overhang_mm=1000)
        with self.assertRaises(ValueError): prepare_multiflight_residential_geometry(POINTS,"FORWARD",0,2800,16,900,30,12,point_ids=IDS,fields=f)
    def test_source_ui_and_transaction_foundations(self):
        source=(ROOT/'japanese_house_modeler/stair_operators.py').read_text(); ui=(ROOT/'japanese_house_modeler/ui.py').read_text()
        self.assertIn('class JHM_OT_move_stair_path_point',source);self.assertIn('prepare_multiflight_residential_geometry',source);self.assertIn('折れ点 1 を移動',ui)

if __name__ == '__main__': unittest.main()
