"""Build 07-D Stage 3 N-flight/U pure production contracts."""
import pathlib, sys, types, unittest
ROOT = pathlib.Path(__file__).parents[1]
package = types.ModuleType("japanese_house_modeler")
package.__path__ = [str(ROOT / "japanese_house_modeler")]
sys.modules.setdefault("japanese_house_modeler", package)
from japanese_house_modeler.stair_multiflight import (
    RISER_DISTRIBUTION_AUTO, RISER_DISTRIBUTION_MANUAL,
    auto_distribute_risers, canonical_multi_path, prepare_distribution_edit_candidate,
    prepare_multiflight_geometry, prepare_multiflight_residential_geometry,
    resolve_multiflight_layout, switch_distribution_mode, validate_manual_allocation)
from japanese_house_modeler.stair_residential import ResidentialFields

U=((0,0),(3,0),(3,1.8),(0,1.8)); IDS=("p0","p1","p2","p3")
ARGS=(U,"FORWARD",0,2800,16,900,30,12)

class CanonicalTests(unittest.TestCase):
    def test_u_identity_and_turns(self):
        path=canonical_multi_path(U,IDS); self.assertEqual(len(path),4)
        self.assertEqual(tuple(p.point_id for p in path),IDS)
        vectors=[(b.xy[0]-a.xy[0],b.xy[1]-a.xy[1]) for a,b in zip(path,path[1:])]
        self.assertEqual(vectors[0],(-vectors[2][0],-vectors[2][1]))
        self.assertTrue(all(a[0]*b[0]+a[1]*b[1]==0 for a,b in zip(vectors,vectors[1:])))
    def test_crossing_and_overlap_rejected(self):
        for points in (((0,0),(2,0),(2,2),(1,2),(1,-1)),
                       ((0,0),(2,0),(2,1),(0,1),(0,0))):
            with self.assertRaises(ValueError): canonical_multi_path(points)
    def test_oblique_and_duplicate_rejected(self):
        with self.assertRaises(ValueError): canonical_multi_path(((0,0),(2,0),(3,1)))
        with self.assertRaises(ValueError): canonical_multi_path(((0,0),(2,0),(2,0),(0,0)))

class LayoutTests(unittest.TestCase):
    def test_effective_runs_and_two_landings(self):
        layout=resolve_multiflight_layout(*ARGS,point_ids=IDS)
        self.assertEqual([round(f.effective_run,2) for f in sorted(layout.flights,key=lambda f:f.canonical_index)],[2.55,.9,2.55])
        self.assertEqual(len(layout.flights),3); self.assertEqual(len(layout.landings),2)
        self.assertEqual([x.center_xy for x in layout.landings],[(3.,0.),(3.,1.8)])
        self.assertEqual([x.material_role for x in layout.landings],["TREAD","TREAD"])
        self.assertEqual([t.point_id for t in layout.turns],["p1","p2"])
    def test_too_short_middle_rejected(self):
        with self.assertRaises(ValueError): resolve_multiflight_layout(
            ((0,0),(3,0),(3,.8),(0,.8)),"FORWARD",0,2800,16,900,30,12)
    def test_auto_is_deterministic_exact_and_minimum(self):
        self.assertEqual(auto_distribute_risers((2.55,.9,2.55),16),
                         auto_distribute_risers((2.55,.9,2.55),16))
        result=auto_distribute_risers((1,1,1),6); self.assertEqual(result,(2,2,2))
        self.assertEqual(sum(auto_distribute_risers((2,3,2),16)),16)
        with self.assertRaises(ValueError): auto_distribute_risers((1,1,1),5)
    def test_forward_reverse_elevations_and_identity(self):
        f=resolve_multiflight_layout(*ARGS,point_ids=IDS,allocation=(5,6,5))
        r=resolve_multiflight_layout(U,"REVERSE",0,2800,16,900,30,12,point_ids=IDS,allocation=(5,6,5))
        self.assertEqual(f.canonical_path,r.canonical_path); self.assertEqual(f.allocation,r.allocation)
        self.assertEqual([round(x.top_z,3) for x in f.landings],[.875,1.925])
        self.assertEqual([round(x.top_z,3) for x in r.landings],[1.925,.875])
        self.assertEqual([x.canonical_index for x in r.flights],[2,1,0])
    def test_middle_has_both_cutbacks_one_owner(self):
        l=resolve_multiflight_layout(*ARGS,point_ids=IDS)
        middle=next(f for f in l.flights if f.canonical_index==1)
        self.assertEqual(middle.start_xy,(3.,.45)); self.assertEqual(middle.end_xy,(3.,1.35))
        self.assertEqual(sum(f.canonical_index==1 for f in l.flights),1)

class DistributionTests(unittest.TestCase):
    def test_manual_three_and_mode_switch(self):
        self.assertEqual(validate_manual_allocation((5,6,5),16,3),(5,6,5))
        for bad in ((5,5,5),(1,7,8)):
            with self.assertRaises(ValueError): validate_manual_allocation(bad,16,3)
        self.assertEqual(switch_distribution_mode(RISER_DISTRIBUTION_AUTO,(5,6,5),(2,1,2),16)[0],RISER_DISTRIBUTION_MANUAL)
        self.assertEqual(switch_distribution_mode(RISER_DISTRIBUTION_MANUAL,(5,6,5),(2,1,2),16)[0],RISER_DISTRIBUTION_AUTO)
    def test_invalid_candidate_does_not_mutate_snapshot(self):
        snapshot={"riser_distribution_mode":"AUTO","riser_count":16,"path_points":U,
                  "manual_riser_allocation":(5,6,5)}; original=dict(snapshot)
        with self.assertRaises(ValueError): prepare_distribution_edit_candidate(snapshot,"MANUAL",(5,5,5))
        self.assertEqual(snapshot,original)

class GeometryTests(unittest.TestCase):
    def test_basic_has_two_landings_finite(self):
        layout,fragments,mesh=prepare_multiflight_geometry(*ARGS,point_ids=IDS)
        self.assertEqual(sum(f.part_type=="TREAD" and len(f.vertices)==8 for f in fragments)>=2,True)
        self.assertTrue(mesh.vertices); self.assertTrue(all(all(abs(v)<1e9 for v in p) for p in mesh.vertices))
    def test_residential_u_modes_and_boards(self):
        for underside in ("STEPPED_CLOSED","SLOPED_CLOSED"):
            fields=ResidentialFields(underside_mode=underside,left_side_board_enabled=True,right_side_board_enabled=True)
            layout,fragments,mesh=prepare_multiflight_residential_geometry(*ARGS,point_ids=IDS,fields=fields)
            self.assertEqual(len(layout.landings),2); self.assertTrue(mesh.faces)
            self.assertIn("UNDERBODY",{f.part_type for f in fragments}); self.assertIn("SIDE_BOARD",{f.part_type for f in fragments})
    def test_l_regression_still_uses_compatibility_landing(self):
        l=resolve_multiflight_layout(((0,0),(3,0),(3,3)),"FORWARD",0,2800,16,900,30,12,point_ids=("a","b","c"))
        self.assertEqual(l.landing,l.landings[0])

if __name__ == "__main__": unittest.main()
