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
    winder_tread_tops, build_winder_finish_fragments,
)
from japanese_house_modeler.stair_residential import ResidentialFields
from japanese_house_modeler.stair_geometry import _signed_volume, validate_mesh_fragments
from japanese_house_modeler.stair_winder_finish import (
    butt_joint_plane, compact_grouped_height, divider_closure_indices,
    high_side_pivot_closure, pivot_relief, ray_relief_intersection,
    resolve_side_board_profile, resolve_sloped_stations,
    resolve_stepped_underbody, shared_edge_splits, stepped_patch_z,
    subtract_box_intersection, symmetric_board_component,
    union_profile_rectangles, world_side_for_uphill,
    exact_rectangle_union_components, rectangle_component_boundaries,
    _variable_prism, trim_prism_fragment_against_shared_board,
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
    def test_34_piecewise_terminal_alignment_is_production_authority(self):
        x=layout(); before=resolve_physical_winder_plans(x.turn,x.cells,"FORWARD",x.nosing,x.riser_thickness)
        f=ResidentialFields(left_side_board_enabled=False,right_side_board_enabled=False)
        y,_p,_m=prepare_winder_geometry(L,*BASE,point_ids=IDS,assembly_mode="STANDARD_RESIDENTIAL",residential_fields=f)
        after=resolve_physical_winder_plans(y.turn,y.cells,"FORWARD",y.nosing,y.riser_thickness)
        self.assertEqual(before,after)
        trim=after[0].inner_trim
        def cross(line,p):
            a,b=line; return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
        self.assertAlmostEqual(cross(trim.entry_terminal,after[0].inner_front),0)
        self.assertAlmostEqual(cross(trim.exit_terminal,after[-1].inner_rear),0)
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

    def test_45_center_enablement_matrix_and_reverse(self):
        specs=(TurnSpec("a","WINDER","EQUAL_3"),TurnSpec("b","WINDER","EQUAL_3"))
        def count(direction,left,right):
            fields=ResidentialFields(left_side_board_enabled=left,right_side_board_enabled=right)
            _x,parts,_m=prepare_winder_geometry(U,direction,0,2800,17,750,30,20,point_ids=UIDS,turn_specs=specs,assembly_mode="STANDARD_RESIDENTIAL",residential_fields=fields)
            return int(any(14000 <= p.ordinal < 14100 for p in parts))
        self.assertEqual((count("FORWARD",True,True),count("FORWARD",False,True),count("FORWARD",True,False),count("FORWARD",False,False)),(1,1,0,0))
        self.assertEqual((count("REVERSE",True,False),count("REVERSE",False,True)),(1,0))

    def test_46_high_side_closure_is_production_mesh(self):
        fields=ResidentialFields(underside_mode="SLOPED_CLOSED",left_side_board_enabled=False,right_side_board_enabled=False)
        _x,parts,_m=prepare_winder_geometry(L,*BASE,point_ids=IDS,assembly_mode="STANDARD_RESIDENTIAL",residential_fields=fields)
        closure=[p for p in parts if p.part_type=="UNDERBODY" and p.ordinal==11099]
        self.assertEqual(len(closure),1)
        self.assertGreater(len(closure[0].vertices),4)
        self.assertTrue(any(len(face)==3 for face in closure[0].faces))

    def test_47_compact_shared_board_trims_production_roles(self):
        x,parts,_mesh=self._compact("FORWARD","SLOPED_CLOSED")
        board=next(p for p in parts if 14000<=p.ordinal<14100)
        z0=min(v[2] for v in board.vertices); z1=max(v[2] for v in board.vertices)
        a,b=x.shared_interface; dx,dy=b[0]-a[0],b[1]-a[1]
        length=math.hypot(dx,dy); normal=(-dy/length,dx/length); half=.018/2
        for part in (p for p in parts if p.part_type in ("TREAD","RISER","UNDERBODY")):
            if max(v[2] for v in part.vertices)<=z0+1e-6 or min(v[2] for v in part.vertices)>=z1-1e-6: continue
            offsets=[(v[0]-a[0])*normal[0]+(v[1]-a[1])*normal[1] for v in part.vertices]
            self.assertFalse(min(offsets)<-half+1e-6 and max(offsets)>half-1e-6)
        self.assertTrue({"TREAD","RISER","UNDERBODY"}.issubset({p.part_type for p in parts}))

    def test_48_partial_height_trim_creates_capped_role_pieces(self):
        _x,parts,_mesh=self._compact("FORWARD","SLOPED_CLOSED")
        for role in ("RISER","UNDERBODY"):
            ordinals=[p.ordinal for p in parts if p.part_type==role]
            self.assertLess(len(set(ordinals)),len(ordinals))
            self.assertTrue(all(len(p.faces)>=4 for p in parts if p.part_type==role))

    def test_49_exact_l_profile_has_one_shell_and_missing_corner(self):
        components=exact_rectangle_union_components(((0,2,0,1),(0,1,1,2)))
        self.assertEqual(len(components),1)
        loops=rectangle_component_boundaries(components[0])
        self.assertEqual(len(loops),1)
        self.assertIn((1.0,1.0),loops[0])
        area=abs(sum(loops[0][i][0]*loops[0][(i+1)%len(loops[0])][1]-loops[0][(i+1)%len(loops[0])][0]*loops[0][i][1] for i in range(len(loops[0])))/2)
        self.assertEqual(area,3.0)

    def test_50_sloped_trim_preserves_original_vertex_z(self):
        specs=(TurnSpec("a","WINDER","EQUAL_3"),TurnSpec("b","WINDER","EQUAL_3"))
        fields=ResidentialFields(underside_mode="SLOPED_CLOSED",side_board_mode="SLOPED",tread_front_overhang_mm=5)
        resolved=resolve_winder_layout(U,"FORWARD",0,2800,17,750,30,20,point_ids=UIDS,turn_specs=specs,tread_front_overhang_mm=5)
        original=build_winder_finish_fragments(resolved,fields)
        _x,trimmed,_m=prepare_winder_geometry(U,"FORWARD",0,2800,17,750,30,20,point_ids=UIDS,turn_specs=specs,assembly_mode="STANDARD_RESIDENTIAL",residential_fields=fields,tread_front_overhang_mm=5)
        source={(p.ordinal,round(v[0],9),round(v[1],9)):set() for p in original if p.part_type=="UNDERBODY" for v in p.vertices}
        for p in original:
            if p.part_type=="UNDERBODY":
                for v in p.vertices: source[(p.ordinal,round(v[0],9),round(v[1],9))].add(round(v[2],9))
        output={}
        for p in trimmed:
            if p.part_type=="UNDERBODY":
                for v in p.vertices:
                    output.setdefault((p.ordinal,round(v[0],9),round(v[1],9)),set()).add(round(v[2],9))
        retained=0
        for key,zs in source.items():
            if key in output:
                matches=zs & output[key]
                retained+=len(matches)
        self.assertGreater(retained,0)

    def test_51_mixed_z_contour_keeps_partial_capped_remnant(self):
        source=_variable_prism(((0,-1),(1,-1),(1,1),(0,1)),
                               (.1,.3,.3,.1),(.8,.8,.8,.8),
                               "UNDERBODY",77)
        pieces=trim_prism_fragment_against_shared_board(
            source,((0,0),(1,0)),1.0,.2,.6,.2,.8)
        self.assertGreater(len(pieces),0)
        vertices=[v for p in pieces for v in p.vertices]
        self.assertTrue(any(abs(v[2]-.2)<1e-9 and .2<v[0]<.8 for v in vertices))
        self.assertTrue(any(abs(v[2]-.1)<1e-9 for v in vertices))
        self.assertTrue(all(p.part_type=="UNDERBODY" and len(p.faces)>=4 for p in pieces))
        self.assertTrue(all(validate_mesh_fragments((p,)) for p in pieces))
        retained=sum(_signed_volume(p.vertices,p.faces) for p in pieces)
        self.assertAlmostEqual(retained,1.2-.231,places=9)
        again=trim_prism_fragment_against_shared_board(
            source,((0,0),(1,0)),1.0,.2,.6,.2,.8)
        self.assertEqual(pieces,again)

    def test_52_compact_front_profiles_complete_with_center_board(self):
        specs=(TurnSpec("a","WINDER","EQUAL_3"),TurnSpec("b","WINDER","EQUAL_3"))
        for mode in ("SQUARE","BEVEL","ROUND"):
            fields=ResidentialFields(underside_mode="SLOPED_CLOSED",side_board_mode="SLOPED",tread_front_overhang_mm=5,tread_front_edge_mode=mode,tread_front_edge_size_mm=2)
            _x,parts,mesh=prepare_winder_geometry(U,"FORWARD",0,2800,17,750,30,20,point_ids=UIDS,turn_specs=specs,assembly_mode="STANDARD_RESIDENTIAL",residential_fields=fields,tread_front_overhang_mm=5,tread_front_edge_mode=mode,tread_front_edge_size_mm=2)
            self.assertIn("SIDE_BOARD",mesh.face_roles)
            self.assertTrue(all(len(p.faces)>=4 for p in parts))

    def test_53_compact_terminal_profiles_are_constant_cross_sections(self):
        specs=(TurnSpec("a","WINDER","EQUAL_3"),TurnSpec("b","WINDER","EQUAL_3"))
        fields=ResidentialFields(underside_mode="SLOPED_CLOSED",side_board_mode="SLOPED")
        resolved=resolve_winder_layout(U,"FORWARD",0,2800,17,750,30,20,point_ids=UIDS,turn_specs=specs)
        parts=build_winder_finish_fragments(resolved,fields)
        shared=[p for p in parts if 14000<=p.ordinal<14100]
        self.assertTrue(shared)
        # Supported contributors span the whole reconciled cross-section and
        # have one lower/upper Z at each terminal, so holes are unreachable.
        for part in shared:
            zs=sorted(set(round(v[2],9) for v in part.vertices))
            self.assertEqual(len(zs),2)

    def test_54_pivot_core_reuses_all_relief_station_xyz(self):
        for degrees in (90,63):
            angle=math.radians(degrees); points=((0,0),(0,2.2),(-2.2*math.sin(angle),2.2+2.2*math.cos(angle)))
            fields=ResidentialFields(underside_mode="SLOPED_CLOSED",left_side_board_enabled=False,right_side_board_enabled=False)
            resolved=resolve_winder_layout(points,*BASE,point_ids=IDS)
            tops=winder_tread_tops(resolved)[0]
            _relief,stations=resolve_sloped_stations(resolved.turn,resolved.cells,max(0,tops[0]-.15),max(0,tops[-1]-.15),resolved.riser_thickness)
            _x,parts,_m=prepare_winder_geometry(points,*BASE,point_ids=IDS,assembly_mode="STANDARD_RESIDENTIAL",residential_fields=fields)
            core=next(p for p in parts if p.ordinal==11099)
            vertices=set(core.vertices)
            expected={(s.inner[0],s.inner[1],s.z) for s in stations}
            self.assertTrue(expected.issubset(vertices))
            self.assertGreaterEqual(sum(len(face)==3 for face in core.faces),len(stations))

    def test_55_pivot_core_and_strips_share_contact_xyz(self):
        for degrees in (90,63):
            angle=math.radians(degrees)
            points=((0,0),(0,2.2),
                    (-2.2*math.sin(angle),2.2+2.2*math.cos(angle)))
            fields=ResidentialFields(
                underside_mode="SLOPED_CLOSED",
                left_side_board_enabled=False,
                right_side_board_enabled=False)
            resolved=resolve_winder_layout(points,*BASE,point_ids=IDS)
            tops=winder_tread_tops(resolved)[0]
            _relief,stations=resolve_sloped_stations(
                resolved.turn,resolved.cells,max(0,tops[0]-.15),
                max(0,tops[-1]-.15),resolved.riser_thickness)
            _x,parts,_m=prepare_winder_geometry(
                points,*BASE,point_ids=IDS,
                assembly_mode="STANDARD_RESIDENTIAL",
                residential_fields=fields)
            core=next(p for p in parts if p.ordinal==11099)
            strips=[p for p in parts if 11000<=p.ordinal<11099]
            for station in stations:
                xy=(station.inner[0],station.inner[1])
                core_z={v[2] for v in core.vertices if v[:2]==xy}
                strip_z={v[2] for p in strips for v in p.vertices
                         if v[:2]==xy}
                self.assertEqual(core_z,strip_z)
                self.assertEqual(len(core_z),2)
                self.assertIn(station.z,core_z)

if __name__ == "__main__": unittest.main()
