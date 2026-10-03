"""Build 07-E Stage-3 closed-body and Side Board pure regressions."""
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
    TurnSpec, prepare_winder_geometry, resolve_turn_frame,
    resolve_winder_layout, resolve_nominal_cells, resolve_physical_winder_plans,
    winder_tread_tops,
)
from japanese_house_modeler.stair_residential import ResidentialFields
from japanese_house_modeler.stair_winder_finish import (
    butt_joint_plane, compact_grouped_height, divider_closure_indices,
    high_side_pivot_closure, pivot_relief, ray_relief_intersection,
    resolve_side_board_profile, resolve_sloped_stations,
    resolve_stepped_underbody, shared_edge_splits, stepped_patch_z,
    subtract_box_intersection, symmetric_board_component,
    union_profile_rectangles, world_side_for_uphill,
)

L=((0,0),(0,2.2),(-2.2,2.2)); IDS=("p0","t","p2")
U=((0,0),(0,2.2),(.75,2.2),(.75,0)); UIDS=("p0","a","b","p3")
BASE=("FORWARD",0,2800,16,750,30,20)

def layout(points=L, ids=IDS, **kw):
    return resolve_winder_layout(points,*BASE,point_ids=ids,**kw)

class SteppedTests(unittest.TestCase):
    def setUp(self):
        self.x=layout(); self.tops=winder_tread_tops(self.x)[0]
        self.plans=resolve_stepped_underbody(self.x.cells,self.tops,.15,0,
                                             tread_thickness=.03,entry_z=0)
    def test_01_patch_equation(self): self.assertEqual(stepped_patch_z(.1,.15,0),0)
    def test_02_patch_levels(self): self.assertEqual(tuple(p.visible_z for p in self.plans),tuple(max(0,z-.15) for z in self.tops))
    def test_03_floor_clamp(self):
        plans=resolve_stepped_underbody(self.x.cells,(.05,.1,.2),.15,0,tread_thickness=.01)
        self.assertNotIn(2,divider_closure_indices(plans))
    def test_04_destination_divider(self): self.assertTrue(all(p.divider_owner=="DESTINATION" for p in self.plans))
    def test_05_entry_owner(self): self.assertTrue(self.plans[0].entry_closure)
    def test_06_exit_neighbor_owner(self): self.assertFalse(self.plans[-1].exit_closure)
    def test_07_outer_corner_preserved(self): self.assertIn(self.x.turn.outer_corner,self.plans[1].polygon)
    def test_08_shell_does_not_move_patch(self): self.assertEqual(stepped_patch_z(.3,.15,0),.15)

class SlopedTests(unittest.TestCase):
    def setUp(self):
        self.x=layout(); self.relief,self.stations=resolve_sloped_stations(self.x.turn,self.x.cells,.1,.4,self.x.riser_thickness)
    def test_09_rho(self): self.assertEqual(self.relief.rho,.02)
    def test_10_ray_hits_chord(self):
        p=ray_relief_intersection(self.x.turn,self.relief,.5); self.assertTrue(all(math.isfinite(v) for v in p))
    def test_11_complete_order(self): self.assertEqual([s.fraction for s in self.stations],sorted(s.fraction for s in self.stations))
    def test_12_outer_o_inserted(self): self.assertEqual(sum(s.kind=="OUTER_CORNER" for s in self.stations),1)
    def test_13_outer_o_z(self): self.assertAlmostEqual(next(s.z for s in self.stations if s.kind=="OUTER_CORNER"),.25)
    def test_14_event_z(self): self.assertAlmostEqual(self.stations[1].z,.2)
    def test_15_high_closure(self): self.assertEqual(high_side_pivot_closure(self.x.turn,self.relief,.1,.4)[0],"HIGH_SIDE_PIVOT_CLOSURE")
    def test_16_no_pivot_spine(self): self.assertTrue(all(s.inner!=self.x.turn.inner_pivot for s in self.stations))
    def test_17_arbitrary_angle(self):
        a=math.radians(63); pts=((0,0),(0,2.2),(-2.2*math.sin(a),2.2+2.2*math.cos(a)))
        x=layout(pts,IDS); r,s=resolve_sloped_stations(x.turn,x.cells,.1,.4,x.riser_thickness); self.assertGreater(len(s),4)

class SharedAndCompactTests(unittest.TestCase):
    def test_18_split_full_3d(self): self.assertEqual(len(shared_edge_splits((0,0,0),(1,0,1),((.5,0,.5),(.5,0,.6)))),3)
    def test_19_grouped_equal3(self): self.assertEqual(compact_grouped_height(0,1,3,3),.5)
    def test_20_grouped_asymmetric(self): self.assertEqual(compact_grouped_height(0,1,2,3),.4)
    def test_21_reverse_authority(self): self.assertEqual(compact_grouped_height(0,1,3,2),.6)
    def test_22_positive_union(self): self.assertEqual(len(union_profile_rectangles(((0,1,0,1),(.5,1.5,.5,1.5)))),1)
    def test_23_edge_union(self): self.assertEqual(len(union_profile_rectangles(((0,1,0,1),(1,2,0,1)))),1)
    def test_24_point_separate(self): self.assertEqual(len(union_profile_rectangles(((0,1,0,1),(1,2,1,2)))),2)
    def test_25_z_gap_separate(self): self.assertEqual(len(union_profile_rectangles(((0,1,0,1),(0,1,2,3)))),2)
    def test_26_symmetric_thickness(self): self.assertEqual((symmetric_board_component(((0,0),(1,0),(1,1)),.018).v_min,symmetric_board_component(((0,0),(1,0),(1,1)),.018).v_max),(-.009,.009))
    def test_27_trim_partial_height(self):
        pieces=subtract_box_intersection((0,2,0,2,0,2),(.5,1.5,.5,1.5,.5,1.5)); self.assertGreater(len(pieces),1); self.assertTrue(any(p[4]==0 and p[5]==.5 for p in pieces))
    def test_28_butt_plane(self): self.assertEqual(butt_joint_plane((1,2,3),(0,2))[1],(0,1))

class BoardAndIntegrationTests(unittest.TestCase):
    def test_29_four_modes(self):
        for lower in ("STEPPED","SLOPED"):
            for upper in ("STEPPED","SLOPED"):
                p=resolve_side_board_profile("LEFT",((0,0),(1,.1)),((0,.2),(1,.4)),.04,upper); self.assertEqual(p.side,"LEFT")
    def test_30_reverse_sides(self): self.assertEqual(world_side_for_uphill("LEFT","REVERSE"),"RIGHT")
    def test_31_width_matrix(self):
        for width in (900,800,750,700,650):
            x=resolve_winder_layout(L,"FORWARD",0,2800,16,width,30,20,point_ids=IDS); self.assertEqual(len(x.cells),3)
    def test_32_production_stepped_role(self):
        f=ResidentialFields(left_side_board_enabled=False,right_side_board_enabled=False)
        _x,parts,_m=prepare_winder_geometry(L,*BASE,point_ids=IDS,assembly_mode="STANDARD_RESIDENTIAL",residential_fields=f)
        self.assertGreater(sum(p.part_type=="UNDERBODY" for p in parts),0)
    def test_33_material_roles(self):
        f=ResidentialFields(left_side_board_enabled=False,right_side_board_enabled=False)
        _x,_p,m=prepare_winder_geometry(L,*BASE,point_ids=IDS,assembly_mode="STANDARD_RESIDENTIAL",residential_fields=f)
        self.assertTrue(set(m.face_roles)<=set(("TREAD","RISER","UNDERSIDE","SIDE_BOARD")))
    def test_34_k_finish_unchanged(self):
        x=layout(); before=resolve_physical_winder_plans(x.turn,x.cells,"FORWARD",x.nosing,x.riser_thickness)[0].inner_trim.chord
        f=ResidentialFields(left_side_board_enabled=False,right_side_board_enabled=False)
        y,_p,_m=prepare_winder_geometry(L,*BASE,point_ids=IDS,assembly_mode="STANDARD_RESIDENTIAL",residential_fields=f)
        after=resolve_physical_winder_plans(y.turn,y.cells,"FORWARD",y.nosing,y.riser_thickness)[0].inner_trim.chord
        self.assertEqual(before,after)
    def test_35_deterministic(self):
        f=ResidentialFields(left_side_board_enabled=False,right_side_board_enabled=False)
        a=prepare_winder_geometry(L,*BASE,point_ids=IDS,assembly_mode="STANDARD_RESIDENTIAL",residential_fields=f)[2]
        b=prepare_winder_geometry(L,*BASE,point_ids=IDS,assembly_mode="STANDARD_RESIDENTIAL",residential_fields=f)[2]
        self.assertEqual(a,b)

    def test_36_production_sloped(self):
        f=ResidentialFields(underside_mode="SLOPED_CLOSED",side_board_mode="SLOPED",left_side_board_enabled=False,right_side_board_enabled=False)
        _x,parts,_m=prepare_winder_geometry(L,*BASE,point_ids=IDS,assembly_mode="STANDARD_RESIDENTIAL",residential_fields=f)
        self.assertGreater(sum(p.part_type=="UNDERBODY" for p in parts),0)

    def test_37_production_boards_both_sides(self):
        f=ResidentialFields()
        _x,parts,_m=prepare_winder_geometry(L,*BASE,point_ids=IDS,assembly_mode="STANDARD_RESIDENTIAL",residential_fields=f)
        self.assertGreaterEqual(sum(p.part_type=="SIDE_BOARD" for p in parts),2)

    def test_38_all_four_modes_use_production_path(self):
        for underside in ("STEPPED_CLOSED","SLOPED_CLOSED"):
            for board in ("STEPPED","SLOPED"):
                f=ResidentialFields(underside_mode=underside,side_board_mode=board)
                _x,parts,mesh=prepare_winder_geometry(L,*BASE,point_ids=IDS,assembly_mode="STANDARD_RESIDENTIAL",residential_fields=f)
                self.assertIn("SIDE_BOARD",mesh.face_roles)
                self.assertIn("UNDERBODY",tuple(p.part_type for p in parts))

    def test_39_full_finish_width_matrix(self):
        for width in (900,800,750,700,650):
            for underside,board in (("STEPPED_CLOSED","STEPPED"),("SLOPED_CLOSED","SLOPED")):
                f=ResidentialFields(underside_mode=underside,side_board_mode=board)
                _x,parts,_m=prepare_winder_geometry(L,"FORWARD",0,2800,16,width,30,20,point_ids=IDS,assembly_mode="STANDARD_RESIDENTIAL",residential_fields=f)
                self.assertTrue(any(p.part_type=="SIDE_BOARD" for p in parts))

    def _compact(self, direction, underside):
        specs=(TurnSpec("a","WINDER","EQUAL_3"),TurnSpec("b","WINDER","EQUAL_3"))
        fields=ResidentialFields(underside_mode=underside,side_board_mode=("SLOPED" if underside=="SLOPED_CLOSED" else "STEPPED"),tread_front_overhang_mm=5)
        return prepare_winder_geometry(U,direction,0,2800,17,750,30,20,point_ids=UIDS,turn_specs=specs,assembly_mode="STANDARD_RESIDENTIAL",residential_fields=fields,tread_front_overhang_mm=5)

    def test_40_compact_u_full_fixture_both_modes(self):
        for underside in ("STEPPED_CLOSED","SLOPED_CLOSED"):
            x,parts,mesh=self._compact("FORWARD",underside)
            self.assertEqual((x.u_classification,x.straight_allocation[1]),("COMPACT_U",0))
            self.assertIn("SIDE_BOARD",mesh.face_roles)
            self.assertEqual(sum(p.ordinal==14000 for p in parts),1)

    def test_41_compact_u_reverse_production(self):
        x,parts,_mesh=self._compact("REVERSE","SLOPED_CLOSED")
        self.assertEqual(x.u_classification,"COMPACT_U")
        self.assertEqual(sum(p.ordinal==14000 for p in parts),1)

    def test_42_reverse_rebuilds_board_world_geometry(self):
        f=ResidentialFields(left_side_board_enabled=True,right_side_board_enabled=False)
        forward=prepare_winder_geometry(L,*BASE,point_ids=IDS,assembly_mode="STANDARD_RESIDENTIAL",residential_fields=f)[1]
        reverse=prepare_winder_geometry(L,"REVERSE",*BASE[1:],point_ids=IDS,assembly_mode="STANDARD_RESIDENTIAL",residential_fields=f)[1]
        fv=tuple(p.vertices for p in forward if p.part_type=="SIDE_BOARD")
        rv=tuple(p.vertices for p in reverse if p.part_type=="SIDE_BOARD")
        self.assertNotEqual(fv,rv)

    def test_43_arbitrary_angle_full_finish(self):
        angle=math.radians(63); points=((0,0),(0,2.2),(-2.2*math.sin(angle),2.2+2.2*math.cos(angle)))
        f=ResidentialFields(underside_mode="SLOPED_CLOSED",side_board_mode="SLOPED")
        _x,parts,_m=prepare_winder_geometry(points,*BASE,point_ids=IDS,assembly_mode="STANDARD_RESIDENTIAL",residential_fields=f)
        self.assertTrue(any(p.part_type=="SIDE_BOARD" for p in parts))

    def test_44_schema5_ui_gate(self):
        source=(ROOT/"japanese_house_modeler"/"ui.py").read_text()
        self.assertIn("stair.stair_schema_version <= 5",source)

if __name__ == "__main__": unittest.main()
