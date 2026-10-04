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
from japanese_house_modeler.stair_terminal_stack import (
    accepted_straight_underbody_candidate,
    audit_constant_top_part_overlap, constant_prism_intersection_volume,
    riser_mediated_interface_parts,
    RISER_MEDIATED_INTERFACE, classify_straight_winder_terminal,
    straight_component_events, straight_terminal_stack,
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
    build_stepped_underbody_fragments,
    canonical_physical_winder_cell_bindings,
    resolve_physical_stepped_body_cells,
    compact_contributor_authority, propagate_semantic_edge_splits,
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

    def test_08a_riser_mediated_terminal_audit(self):
        fields=ResidentialFields(underside_mode="STEPPED_CLOSED",
                                 left_side_board_enabled=False,
                                 right_side_board_enabled=False)
        resolved,parts,_mesh=prepare_winder_geometry(
            L,*BASE,point_ids=IDS,assembly_mode="STANDARD_RESIDENTIAL",
            residential_fields=fields)
        mappings=straight_component_events(resolved)
        incoming,outgoing=mappings
        self.assertNotEqual(incoming.canonical_segment_index,
                            outgoing.canonical_segment_index)
        tread=next(part for part in parts
                   if part.part_type=="TREAD"
                   and part.ordinal==incoming.final_tread_ordinal)
        riser=next(part for part in parts
                   if part.part_type=="RISER"
                   and part.ordinal==incoming.final_riser_ordinal)
        outgoing_tread=next(part for part in parts if part.part_type=="TREAD"
                            and part.ordinal==outgoing.first_tread_ordinal)
        outgoing_riser=next(part for part in parts if part.part_type=="RISER"
                            and part.ordinal==outgoing.first_riser_ordinal)
        _incoming_local,incoming_body=accepted_straight_underbody_candidate(
            resolved,incoming,fields)
        _outgoing_local,outgoing_body=accepted_straight_underbody_candidate(
            resolved,outgoing,fields)
        self.assertIsNot(outgoing_tread,tread)
        self.assertIsNot(outgoing_riser,riser)
        self.assertNotEqual(outgoing_body.vertices,incoming_body.vertices)
        underbody=next(part for part in parts
                       if part.part_type=="UNDERBODY" and part.ordinal==10000)
        snapshot=(tread,riser,underbody)
        semantic=resolved.turn.inner_pivot
        incoming=resolved.turn.incoming
        left=(-incoming[1],incoming[0])
        stack=straight_terminal_stack(
            "EXIT",semantic,incoming,left,resolved.riser_thickness,
            riser,tread,incoming_body)
        authority=classify_straight_winder_terminal(
            stack,(resolved.turn.inner_pivot,resolved.turn.entry_outer),
            ("STRAIGHT",0),("WINDER",0))
        self.assertEqual(authority.interface_class,RISER_MEDIATED_INTERFACE)
        self.assertAlmostEqual(authority.plane_offset,resolved.riser_thickness)
        entry_stack=straight_terminal_stack(
            "ENTRY",resolved.turn.inner_pivot,resolved.turn.outgoing,
            (-resolved.turn.outgoing[1],resolved.turn.outgoing[0]),
            resolved.riser_thickness,outgoing_riser,outgoing_tread,outgoing_body)
        entry_authority=classify_straight_winder_terminal(
            entry_stack,(resolved.turn.inner_pivot,resolved.turn.exit_outer),
            ("WINDER",0),("STRAIGHT",1))
        self.assertEqual(entry_authority.interface_class,
                         RISER_MEDIATED_INTERFACE)
        self.assertAlmostEqual(entry_authority.plane_offset,
                               resolved.riser_thickness)

        # Convex clipping gives exact plan area for the square-profile Tread
        # against nominal Winder cell 1; both have constant Z intervals here.
        tread_plan=[]
        z_tread=(min(v[2] for v in tread.vertices),max(v[2] for v in tread.vertices))
        for vertex in tread.vertices:
            point=vertex[:2]
            if point not in tread_plan: tread_plan.append(point)
        # Order the rectangular footprint around its centroid.
        center=(sum(p[0] for p in tread_plan)/len(tread_plan),
                sum(p[1] for p in tread_plan)/len(tread_plan))
        tread_plan.sort(key=lambda p:math.atan2(p[1]-center[1],p[0]-center[0]))
        subject=list(tread_plan)
        signed=lambda poly:sum(a[0]*b[1]-a[1]*b[0]
                               for a,b in zip(poly,poly[1:]+poly[:1]))/2
        clip=list(resolved.cells[0].polygon)
        if signed(clip)<0: clip.reverse()
        for a,b in zip(clip,clip[1:]+clip[:1]):
            output=[]
            for p,q in zip(subject,subject[1:]+subject[:1]):
                cross=lambda x:(b[0]-a[0])*(x[1]-a[1])-(b[1]-a[1])*(x[0]-a[0])
                ip,iq=cross(p)>=-1e-12,cross(q)>=-1e-12
                if ip: output.append(p)
                if ip!=iq:
                    dp=(q[0]-p[0],q[1]-p[1]); edge=(b[0]-a[0],b[1]-a[1])
                    den=dp[0]*edge[1]-dp[1]*edge[0]
                    t=((a[0]-p[0])*edge[1]-(a[1]-p[1])*edge[0])/den
                    output.append((p[0]+t*dp[0],p[1]+t*dp[1]))
            subject=output
        area=abs(signed(subject))
        plan=resolve_stepped_underbody(
            resolved.cells,winder_tread_tops(resolved)[0],.15,0,
            tread_thickness=resolved.tread_thickness)[0]
        z_overlap=max(0,min(z_tread[1],plan.top_z)-max(z_tread[0],plan.visible_z))
        self.assertGreater(area,0.0)  # plan overlap is intentional proximity
        self.assertEqual(z_overlap,0.0)  # but physical volume is disjoint
        z_riser=(min(v[2] for v in riser.vertices),max(v[2] for v in riser.vertices))
        riser_overlap=max(0,min(z_riser[1],plan.top_z)
                          -max(z_riser[0],plan.visible_z))
        self.assertEqual(riser_overlap,0.0)
        self.assertEqual((tread,riser,underbody),snapshot)
        interfaces=riser_mediated_interface_parts(resolved,parts,fields)
        straight_to_winder,winder_to_straight=interfaces
        self.assertEqual(straight_to_winder.destination_boundary_riser.ordinal,
                         mappings[0].final_riser_ordinal+2)
        self.assertEqual(straight_to_winder.destination_entry_tread.ordinal,
                         mappings[0].final_riser_ordinal+1)
        self.assertEqual(winder_to_straight.destination_boundary_riser.ordinal,
                         mappings[1].first_riser_ordinal)
        self.assertEqual(winder_to_straight.destination_entry_tread.ordinal,
                         mappings[1].first_tread_ordinal)
        self.assertIsNot(straight_to_winder.destination_boundary_riser,riser)
        # Exact source-authority convex-prism intersection exposes the first
        # production contradiction and triggers the mandated audit STOP.
        boundary=straight_to_winder.destination_boundary_riser
        boundary_plan=[]
        for vertex in boundary.vertices:
            if vertex[:2] not in boundary_plan:boundary_plan.append(vertex[:2])
        center=(sum(p[0] for p in boundary_plan)/len(boundary_plan),
                sum(p[1] for p in boundary_plan)/len(boundary_plan))
        boundary_plan.sort(key=lambda p:math.atan2(p[1]-center[1],p[0]-center[0]))
        volume=constant_prism_intersection_volume(
            plan.polygon,(plan.visible_z,plan.top_z),boundary_plan,
            (min(v[2] for v in boundary.vertices),
             max(v[2] for v in boundary.vertices)))
        self.assertGreater(volume,1e-12)
        self.assertAlmostEqual(volume,0.001758430780618328,places=12)
        overlap=audit_constant_top_part_overlap(
            plan.polygon,(plan.visible_z,plan.top_z),boundary_plan,
            (min(v[2] for v in boundary.vertices),
             max(v[2] for v in boundary.vertices)),"RISER")
        self.assertEqual(overlap.intersection_volume,volume)
        self.assertLess(overlap.part_bottom,overlap.body_bottom)
        self.assertFalse(overlap.complete_soffit_survives_subtraction)

    def test_08b_physical_riser_exclusion_known_fixture(self):
        physical=resolve_physical_winder_plans(
            self.x.turn,self.x.cells,self.x.ascent_direction,
            self.x.nosing,self.x.riser_thickness)
        cells,plans=resolve_physical_stepped_body_cells(
            self.x.cells,physical,self.tops,.15,self.x.base_z,
            tread_thickness=self.x.tread_thickness)
        height=self.x.actual_riser-self.x.tread_thickness
        def area(polygon):
            return abs(sum(a[0]*b[1]-a[1]*b[0]
                           for a,b in zip(polygon,polygon[1:]+polygon[:1]))/2)
        raw=constant_prism_intersection_volume(
            self.x.cells[0].polygon,(cells[0].visible_z,cells[0].top_z),
            physical[0].riser_polygon,
            (self.tops[0]-self.x.actual_riser,
             self.tops[0]-self.x.tread_thickness))
        self.assertAlmostEqual(raw,0.001758430780618328,places=12)
        final=sum(constant_prism_intersection_volume(
            plan.polygon,(plan.visible_z,plan.top_z),physical[0].riser_polygon,
            (self.tops[0]-self.x.actual_riser,
             self.tops[0]-self.x.tread_thickness)) for plan in plans)
        self.assertAlmostEqual(final,0.0,places=12)
        raw_volume=area(self.x.cells[0].polygon)*(
            cells[0].top_z-cells[0].visible_z)
        final_volume=sum(area(p.polygon)*(p.top_z-p.visible_z)
                         for p in plans if p.cell_index==1)
        self.assertAlmostEqual(raw_volume,final_volume+raw,places=12)
        self.assertTrue(all(p.visible_z==1.075 for p in plans
                            if p.cell_index==1))
        validate_mesh_fragments(build_stepped_underbody_fragments(plans))

    def test_08c_stepped_physical_exclusion_matrix(self):
        fields=ResidentialFields(underside_mode="STEPPED_CLOSED",
                                 left_side_board_enabled=False,
                                 right_side_board_enabled=False)
        for degrees in (90,63):
            angle=math.radians(degrees)
            points=((0,0),(0,2.2),
                    (-2.2*math.sin(angle),2.2+2.2*math.cos(angle)))
            for width in (750,650):
                for direction in ("FORWARD","REVERSE"):
                    resolved=resolve_winder_layout(
                        points,direction,0,2800,16,width,30,20,point_ids=IDS)
                    tops=winder_tread_tops(resolved)[0]
                    turn_tops=(tops if direction=="FORWARD"
                               else tuple(reversed(tops)))
                    physical=resolve_physical_winder_plans(
                        resolved.turn,resolved.cells,direction,resolved.nosing,
                        resolved.riser_thickness)
                    bindings=canonical_physical_winder_cell_bindings(
                        resolved.cells,physical,turn_tops)
                    self.assertEqual(tuple((b.cell_index,b.physical_plan.cell_index)
                                           for b in bindings),((1,1),(2,2),(3,3)))
                    body,plans=resolve_physical_stepped_body_cells(
                        resolved.cells,physical,turn_tops,.15,resolved.base_z,
                        tread_thickness=resolved.tread_thickness)
                    def area(polygon):
                        return abs(sum(a[0]*b[1]-a[1]*b[0]
                                       for a,b in zip(
                                           polygon,polygon[1:]+polygon[:1]))/2)
                    for binding,authority in zip(bindings,body):
                        height=authority.top_z-authority.visible_z
                        raw=area(binding.cell.polygon)*height
                        excluded=constant_prism_intersection_volume(
                            binding.cell.polygon,
                            (authority.visible_z,authority.top_z),
                            binding.physical_plan.riser_polygon,
                            (binding.tread_top_z-resolved.actual_riser,
                             binding.tread_top_z-resolved.tread_thickness))
                        final=sum(area(plan.polygon)*height for plan in plans
                                  if plan.cell_index==binding.cell_index)
                        self.assertAlmostEqual(raw,final+excluded,places=11)
                        if resolved.turn.outer_corner in binding.cell.polygon:
                            self.assertTrue(any(
                                resolved.turn.outer_corner in plan.polygon
                                for plan in plans
                                if plan.cell_index==binding.cell_index))
                    self.assertEqual((body,plans),resolve_physical_stepped_body_cells(
                        resolved.cells,physical,turn_tops,.15,resolved.base_z,
                        tread_thickness=resolved.tread_thickness))
                    for plan in plans:
                        for binding in bindings:
                            top=binding.tread_top_z
                            part=binding.physical_plan
                            self.assertAlmostEqual(constant_prism_intersection_volume(
                                plan.polygon,(plan.visible_z,plan.top_z),
                                part.riser_polygon,
                                (top-resolved.actual_riser,
                                 top-resolved.tread_thickness)),0.0,places=11)
                            self.assertAlmostEqual(constant_prism_intersection_volume(
                                plan.polygon,(plan.visible_z,plan.top_z),
                                part.polygon,
                                (top-resolved.tread_thickness,top)),0.0,places=11)
                    validate_mesh_fragments(build_stepped_underbody_fragments(plans))
                    produced,parts,_mesh=prepare_winder_geometry(
                        points,direction,0,2800,16,width,30,20,point_ids=IDS,
                        assembly_mode="STANDARD_RESIDENTIAL",
                        residential_fields=fields)
                    self.assertEqual(produced, resolved)
                    validate_mesh_fragments(tuple(
                        part for part in parts if part.part_type=="UNDERBODY"))

    def test_08d_reverse_binding_is_canonical(self):
        resolved=resolve_winder_layout(
            L,"REVERSE",*BASE[1:],point_ids=IDS)
        physical=resolve_physical_winder_plans(
            resolved.turn,resolved.cells,resolved.ascent_direction,
            resolved.nosing,resolved.riser_thickness)
        self.assertEqual(tuple(plan.cell_index for plan in physical),(3,2,1))
        ascent_tops=winder_tread_tops(resolved)[0]
        canonical_tops=tuple(reversed(ascent_tops))
        bindings=canonical_physical_winder_cell_bindings(
            resolved.cells,physical,canonical_tops)
        self.assertEqual(tuple(cell.index for cell in resolved.cells),(1,2,3))
        self.assertEqual(tuple((binding.cell.index,
                                binding.physical_plan.cell_index)
                               for binding in bindings),((1,1),(2,2),(3,3)))
        self.assertEqual(tuple(binding.tread_top_z for binding in bindings),
                         canonical_tops)

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

    def test_17a_complete_terminal_part_selection_matrix(self):
        for degrees in (90,63):
            angle=math.radians(degrees)
            points=((0,0),(0,2.2),(-2.2*math.sin(angle),2.2+2.2*math.cos(angle)))
            for width in (750,650):
                for direction in ("FORWARD","REVERSE"):
                    for mode in ("STEPPED_CLOSED","SLOPED_CLOSED"):
                        fields=ResidentialFields(underside_mode=mode,
                            left_side_board_enabled=False,right_side_board_enabled=False)
                        resolved,parts,_=prepare_winder_geometry(
                            points,direction,0,2800,16,width,30,20,
                            point_ids=IDS,assembly_mode="STANDARD_RESIDENTIAL",
                            residential_fields=fields)
                        mappings=straight_component_events(resolved)
                        self.assertEqual(len(mappings),2)
                        selected=[]
                        for position,component in enumerate(mappings):
                            entry=position==1
                            tread_ordinal=(component.first_tread_ordinal if entry
                                           else component.final_tread_ordinal)
                            riser_ordinal=(component.first_riser_ordinal if entry
                                           else component.final_riser_ordinal)
                            tread=next(p for p in parts if p.part_type=="TREAD"
                                       and p.ordinal==tread_ordinal)
                            riser=next(p for p in parts if p.part_type=="RISER"
                                       and p.ordinal==riser_ordinal)
                            _local,body=accepted_straight_underbody_candidate(
                                resolved,component,fields)
                            selected.append(straight_terminal_stack(
                                "ENTRY" if entry else "EXIT",
                                resolved.turn.inner_pivot,component.forward,
                                (-component.forward[1],component.forward[0]),
                                resolved.riser_thickness,riser,tread,body))
                        self.assertIsNot(selected[0].boundary_tread,
                                         selected[1].boundary_tread)
                        self.assertIsNot(selected[0].boundary_riser,
                                         selected[1].boundary_riser)
                        self.assertNotEqual(selected[0].native_underbody.vertices,
                                            selected[1].native_underbody.vertices)
                        self.assertEqual(mappings,straight_component_events(resolved))
    def test_17b_terminal_stack_rejects_invalid_authority(self):
        fragment=lambda role: type("Part",(),{"part_type":role})()
        valid=("ENTRY",(0,0),(1,0),(0,1),.02,
               fragment("RISER"),fragment("TREAD"),fragment("UNDERBODY"))
        bad=(
            valid[:2]+((2,0),)+valid[3:],
            valid[:3]+((1,1),)+valid[4:],
            valid[:5]+(None,)+valid[6:],
            valid[:6]+(fragment("RISER"),)+valid[7:],
            valid[:7]+(fragment("TREAD"),),
        )
        for values in bad:
            with self.assertRaisesRegex(ValueError,"GEOMETRY_INVALID"):
                straight_terminal_stack(values[0],values[1],values[2],values[3],
                                        values[4],values[5],values[6],values[7])

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
        board=next(p for p in trimmed if 14000<=p.ordinal<14100)
        a,b=resolved.shared_interface; dx,dy=b[0]-a[0],b[1]-a[1]
        length=math.hypot(dx,dy); tangent=(dx/length,dy/length)
        normal=(-tangent[1],tangent[0]); half=.018/2
        z0=min(v[2] for v in board.vertices); z1=max(v[2] for v in board.vertices)
        output={(p.ordinal,v) for p in trimmed if p.part_type=="UNDERBODY"
                for v in p.vertices}
        expected=[]
        for part in original:
            if part.part_type!="UNDERBODY" or part.ordinal%100==99: continue
            for vertex in part.vertices:
                delta=(vertex[0]-a[0],vertex[1]-a[1])
                s=delta[0]*tangent[0]+delta[1]*tangent[1]
                v=delta[0]*normal[0]+delta[1]*normal[1]
                safely_outside=(s<-1e-9 or s>length+1e-9
                                or abs(v)>half+1e-9
                                or vertex[2]<z0-1e-9
                                or vertex[2]>z1+1e-9)
                if safely_outside: expected.append((part.ordinal,vertex))
        self.assertTrue(expected)
        self.assertTrue(all(item in output for item in expected))
        self.assertTrue(all(validate_mesh_fragments((p,)) for p in trimmed
                            if p.part_type=="UNDERBODY"))
        again=prepare_winder_geometry(U,"FORWARD",0,2800,17,750,30,20,
            point_ids=UIDS,turn_specs=specs,
            assembly_mode="STANDARD_RESIDENTIAL",residential_fields=fields,
            tread_front_overhang_mm=5)[1]
        self.assertEqual(trimmed,again)

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
        profiled_candidates=set()
        for width in (900,750,650):
            compact=((0,0),(0,2.2),(width/1000,2.2),(width/1000,0))
            for direction in ("FORWARD","REVERSE"):
                for mode in ("SQUARE","BEVEL","ROUND"):
                    fields=ResidentialFields(underside_mode="SLOPED_CLOSED",side_board_mode="SLOPED",tread_front_overhang_mm=5,tread_front_edge_mode=mode,tread_front_edge_size_mm=2)
                    resolved,parts,mesh=prepare_winder_geometry(compact,direction,0,2800,17,width,30,20,point_ids=UIDS,turn_specs=specs,assembly_mode="STANDARD_RESIDENTIAL",residential_fields=fields,tread_front_overhang_mm=5,tread_front_edge_mode=mode,tread_front_edge_size_mm=2)
                    self.assertIn("SIDE_BOARD",mesh.face_roles)
                    self.assertTrue(all(len(p.faces)>=4 for p in parts))
                    board=next(p for p in parts if 14000<=p.ordinal<14100)
                    a,b=resolved.shared_interface; length=math.dist(a,b)
                    tangent=((b[0]-a[0])/length,(b[1]-a[1])/length)
                    normal=(-tangent[1],tangent[0]); half=.018/2
                    z0=min(v[2] for v in board.vertices)
                    z1=max(v[2] for v in board.vertices)
                    for part in (p for p in parts if p.part_type in
                                 ("TREAD","RISER","UNDERBODY")):
                        ss=[(v[0]-a[0])*tangent[0]+(v[1]-a[1])*tangent[1]
                            for v in part.vertices]
                        vv=[(v[0]-a[0])*normal[0]+(v[1]-a[1])*normal[1]
                            for v in part.vertices]
                        overlaps=(max(ss)>1e-9 and min(ss)<length-1e-9
                                  and max(v[2] for v in part.vertices)>z0+1e-9
                                  and min(v[2] for v in part.vertices)<z1-1e-9)
                        if overlaps:
                            crosses=min(vv)<-half+1e-9 and max(vv)>half-1e-9
                            if mode in ("BEVEL","ROUND") and part.part_type=="TREAD":
                                if crosses: profiled_candidates.add(mode)
                            else:
                                self.assertFalse(crosses,(width,direction,mode,
                                                         part.part_type,
                                                         part.ordinal))
        self.assertEqual(profiled_candidates,{"BEVEL","ROUND"})

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

    def test_56_stepped_union_owns_dividers_once(self):
        fixtures=[]
        for direction in ("FORWARD","REVERSE"):
            fixtures.append((L,direction,750))
        fixtures.append((L,"FORWARD",650))
        angle=math.radians(63)
        fixtures.append((((0,0),(0,2.2),
                          (-2.2*math.sin(angle),2.2+2.2*math.cos(angle))),
                         "FORWARD",750))
        for points,direction,width in fixtures:
            resolved=resolve_winder_layout(
                points,direction,0,2800,16,width,30,20,point_ids=IDS)
            tops=winder_tread_tops(resolved)[0]
            turn_tops=(tops if direction=="FORWARD" else tuple(reversed(tops)))
            plans=resolve_stepped_underbody(
                resolved.cells,turn_tops,.15,0,tread_thickness=.03)
            fragment=build_stepped_underbody_fragments(plans)[0]
            self.assertTrue(validate_mesh_fragments((fragment,)))
            geometric_faces=[]
            for face in fragment.faces:
                geometric_faces.append(frozenset(fragment.vertices[i]
                                                  for i in face))
            self.assertEqual(len(geometric_faces),len(set(geometric_faces)))
            for plan in plans:
                expected={(p[0],p[1],plan.visible_z) for p in plan.polygon}
                self.assertIn(frozenset(expected),geometric_faces)
            self.assertIn(resolved.turn.outer_corner,
                          {v[:2] for v in fragment.vertices})

    def test_57_equal_stepped_levels_have_no_divider_wall(self):
        resolved=layout()
        plans=resolve_stepped_underbody(
            resolved.cells,(.20,.20,.20),.15,0,tread_thickness=.03)
        fragment=build_stepped_underbody_fragments(plans)[0]
        for first,second in zip(resolved.cells,resolved.cells[1:]):
            endpoints={resolved.turn.inner_pivot,first.polygon[-1]}
            divider_faces=[face for face in fragment.faces
                           if {fragment.vertices[i][:2] for i in face}
                           <= endpoints
                           and len({fragment.vertices[i][2]
                                    for i in face})>1]
            self.assertEqual(divider_faces,[])

    def test_58_compact_contributors_use_source_terminal_authority(self):
        specs=(TurnSpec("a","WINDER","EQUAL_3"),
               TurnSpec("b","WINDER","EQUAL_3"))
        for width in (900,750,650):
            compact=((0,0),(0,2.2),(width/1000.0,2.2),
                     (width/1000.0,0))
            for direction in ("FORWARD","REVERSE"):
                resolved=resolve_winder_layout(
                    compact,direction,0,2800,17,width,30,20,
                    point_ids=UIDS,turn_specs=specs)
                seam=math.dist(*resolved.shared_interface)
                for tops in winder_tread_tops(resolved):
                    terminal=tops[-1] if direction=="FORWARD" else tops[0]
                    authority=compact_contributor_authority(
                        seam,max(0,terminal-.15),terminal,.04)
                    self.assertEqual(authority.s_start,0.0)
                    self.assertEqual(authority.s_end,seam)
                    self.assertEqual(authority.lower_start,
                                     authority.lower_end)
                    self.assertEqual(authority.upper_start,
                                     authority.upper_end)
        # Full-width rectangles can join or remain vertically separated, but
        # their complement cannot be enclosed in (s,z), hence no profile hole.

    def test_59_semantic_registry_runs_in_production_path(self):
        fields=ResidentialFields(underside_mode="SLOPED_CLOSED",
                                 side_board_mode="SLOPED")
        _x,parts,_mesh=prepare_winder_geometry(
            L,*BASE,point_ids=IDS,assembly_mode="STANDARD_RESIDENTIAL",
            residential_fields=fields)
        self.assertEqual(parts,propagate_semantic_edge_splits(parts))

    def test_60_compact_boards_share_butt_planes(self):
        specs=(TurnSpec("a","WINDER","EQUAL_3"),
               TurnSpec("b","WINDER","EQUAL_3"))
        for direction in ("FORWARD","REVERSE"):
            for underside,board_mode in (("STEPPED_CLOSED","STEPPED"),
                                         ("SLOPED_CLOSED","SLOPED")):
                fields=ResidentialFields(underside_mode=underside,
                                         side_board_mode=board_mode)
                resolved,parts,_mesh=prepare_winder_geometry(
                    U,direction,0,2800,17,750,30,20,point_ids=UIDS,
                    turn_specs=specs,assembly_mode="STANDARD_RESIDENTIAL",
                    residential_fields=fields)
                a,b=resolved.shared_interface
                length=math.dist(a,b); tangent=((b[0]-a[0])/length,
                                                (b[1]-a[1])/length)
                ordinary=[p for p in parts if p.part_type=="SIDE_BOARD"
                          and p.ordinal<14000]
                shared=[p for p in parts if 14000<=p.ordinal<14100]
                self.assertTrue(ordinary and shared)
                for part in ordinary+shared:
                    stations=[(v[0]-a[0])*tangent[0]
                              +(v[1]-a[1])*tangent[1]
                              for v in part.vertices]
                    self.assertGreaterEqual(min(stations),-1e-9)
                    self.assertLessEqual(max(stations),length+1e-9)
                    self.assertTrue(validate_mesh_fragments((part,)))
                shared_stations={round((v[0]-a[0])*tangent[0]
                                       +(v[1]-a[1])*tangent[1],9)
                                 for p in shared for v in p.vertices}
                self.assertIn(0.0,shared_stations)
                self.assertIn(round(length,9),shared_stations)

if __name__ == "__main__": unittest.main()

# Landing authority foundation cases are kept in a focused source module but
# imported here so the mandated Stage-1+2+3 command executes them.
from tests.build_07_e_landing_finish_cases import GeneralizedLandingFinishTests
