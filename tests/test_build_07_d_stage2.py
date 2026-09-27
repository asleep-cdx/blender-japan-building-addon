"""Build 07-D Stage 2 pure editing and Residential L contracts."""
import math, pathlib, sys, types, unittest
ROOT = pathlib.Path(__file__).parents[1]
package = types.ModuleType("japanese_house_modeler")
package.__path__ = [str(ROOT / "japanese_house_modeler")]
sys.modules.setdefault("japanese_house_modeler", package)
from japanese_house_modeler.drawing_alignment import constrained_direction, select_unambiguous_candidate
from japanese_house_modeler.stair_guides import (aligned_candidates, endpoint_right_angle_candidate,
    creation_right_angle_guide_rays, endpoint_shift_candidate, move_anchor_index,
    resolve_creation_candidate,
    resolve_move_candidate, turn_right_angle_candidate)
from japanese_house_modeler.stair_multiflight import (RISER_DISTRIBUTION_AUTO,
    FlightAllocation, allocation_counts, build_landing_side_board_fragments,
    _build_l_flight_board_fragment, _build_l_flight_underbody_fragment,
    _build_landing_underbody_transition, _flight_stair_layout,
    _baseline_z, _build_sloped_upper_section_fragment, _upper_section_baseline,
    canonical_multi_path, distribution_edit_initial_allocation,
    prepare_multiflight_residential_geometry,
    resolve_multiflight_layout, segment_allocations, switch_distribution_mode,
    validate_manual_allocation)
from japanese_house_modeler.stair_residential import ResidentialFields
from japanese_house_modeler.stair_residential_geometry import (
    build_underbody_fragment, side_board_lower_profile, side_board_profile,
)

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
        c=resolve_move_candidate(POINTS,IDS,1,(2,1),guide_candidates=(turn_right_angle_candidate(POINTS,(2,1)),),distances=(2,),guide_names=("RIGHT_ANGLE",)); self.assertEqual(c.point_ids,IDS);self.assertEqual(c.points,canonical_multi_path(c.points,IDS) and c.points)
    def test_wall_references_are_coordinates_only(self): self.assertEqual(aligned_candidates((2,3),((1,4),)),((1.,3.),(2.,4.)))
    def test_ambiguous_policy(self): self.assertIsNone(select_unambiguous_candidate(((4,"a"),(4,"b"))))
    def test_non_right_numeric_rejected(self):
        with self.assertRaises(ValueError): canonical_multi_path(((0,0),(2,0),(3,2)),IDS)
    def test_alignment_can_beat_right_angle_guide(self):
        result=resolve_move_candidate(POINTS,IDS,2,(3.2,2.1),guide_candidates=((3,2),(3,4)),distances=(8,2),guide_names=("RIGHT_ANGLE","Y_ALIGNMENT"))
        self.assertEqual(result.points[2],(3.,4.));self.assertEqual(result.guide,"Y_ALIGNMENT")
    def test_threshold_outside_non_right_rejected(self):
        with self.assertRaises(ValueError): resolve_creation_candidate(POINTS[:2],IDS,(2.8,2),guide_candidates=((3,2),),distances=(11,))
    def test_endpoint_shift_compatible(self):
        point=endpoint_shift_candidate(POINTS,2,(3,2));self.assertAlmostEqual(dot_at((POINTS[0],POINTS[1],point)),0)
    def test_endpoint_shift_incompatible(self):
        with self.assertRaises(ValueError): endpoint_shift_candidate(POINTS,2,(4,2))
    def test_creation_has_two_persistent_perpendicular_rays(self):
        rays=creation_right_angle_guide_rays(POINTS[0],POINTS[1])
        incoming=(POINTS[1][0]-POINTS[0][0],POINTS[1][1]-POINTS[0][1])
        self.assertEqual(rays.origin,POINTS[1])
        for direction in (rays.left_direction,rays.right_direction):
            self.assertAlmostEqual(incoming[0]*direction[0]+incoming[1]*direction[1],0)
        self.assertAlmostEqual(rays.left_direction[0]+rays.right_direction[0],0)
        self.assertAlmostEqual(rays.left_direction[1]+rays.right_direction[1],0)
    def test_invalid_candidate_does_not_remove_visual_guide_foundation(self):
        rays=creation_right_angle_guide_rays(POINTS[0],POINTS[1])
        with self.assertRaises(ValueError):
            resolve_creation_candidate(POINTS[:2],IDS,(2.5,2),guide_candidates=((3,2),),distances=(20,))
        self.assertEqual(rays.origin,POINTS[1])
        with self.assertRaises(ValueError): endpoint_shift_candidate(POINTS,2,(4,2))
        self.assertEqual(creation_right_angle_guide_rays(POINTS[0],POINTS[1]),rays)
    def test_creation_threshold_snap_is_exact_90(self):
        result=resolve_creation_candidate(POINTS[:2],IDS,(2.95,2),guide_candidates=((3,2),),distances=(6,),guide_names=("RIGHT_ANGLE",))
        self.assertAlmostEqual(dot_at(result.points),0)

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
    def test_auto_dialog_ignores_stale_manual_history(self):
        initial_auto=self.layout().allocation
        stale_manual=(7,9)
        self.assertNotEqual(initial_auto,stale_manual)
        # MANUAL -> AUTO, followed by an AUTO Path edit/reallocation.
        changed=resolve_multiflight_layout(((0,0),(5,0),(5,2)),"FORWARD",0,2800,16,900,30,12,point_ids=IDS).allocation
        self.assertNotEqual(changed,stale_manual)
        dialog=distribution_edit_initial_allocation("AUTO",changed,stale_manual)
        self.assertEqual(dialog,changed)
        mode,manual=switch_distribution_mode("AUTO",dialog,(4.55,1.55),16)
        self.assertEqual((mode,manual),("MANUAL",changed))
        source=(ROOT/'japanese_house_modeler/stair_operators.py').read_text()
        self.assertIn('distribution_edit_initial_allocation(',source)
    def test_manual_dialog_uses_current_manual(self):
        self.assertEqual(distribution_edit_initial_allocation("MANUAL",(8,8),(7,9)),(7,9))

class ResidentialGeometryTests(unittest.TestCase):
    def prepare(self, underside="STEPPED_CLOSED", board="STEPPED", edge="SQUARE", left=True,right=True,points=POINTS):
        f=ResidentialFields(underside_mode=underside,side_board_mode=board,tread_front_edge_mode=edge,
          tread_front_overhang_mm=10,tread_front_edge_size_mm=3,left_side_board_enabled=left,right_side_board_enabled=right)
        return prepare_multiflight_residential_geometry(points,"FORWARD",0,2800,16,900,30,12,point_ids=IDS,fields=f)
    def test_representative_matrix(self):
        for combo in (("STEPPED_CLOSED","STEPPED","SQUARE"),("STEPPED_CLOSED","SLOPED","BEVEL"),("SLOPED_CLOSED","STEPPED","ROUND"),("SLOPED_CLOSED","SLOPED","SQUARE")):
            with self.subTest(combo=combo):
                l,fr,m=self.prepare(*combo);self.assertTrue(all(math.isfinite(x) for v in m.vertices for x in v));self.assertAlmostEqual(l.upper_arrival_z,2.8);self.assertGreaterEqual(min(v[2] for v in m.vertices),l.base_z)
                self.assertEqual(set(m.face_roles),{"TREAD","RISER","UNDERSIDE","SIDE_BOARD"});self.assertNotIn("LANDING",m.face_roles)
    def test_landing_tread_and_underbody(self):
        l,fr,m=self.prepare(); self.assertEqual(fr[-2].part_type,"TREAD");self.assertEqual(fr[-1].part_type,"UNDERBODY");self.assertIn("UNDERSIDE",m.face_roles)
    def test_board_sides(self):
        for left,right,count in ((True,True,7),(True,False,2),(False,True,5),(False,False,0)):
            _,fr,_=self.prepare(left=left,right=right); self.assertEqual(sum(f.part_type=="SIDE_BOARD" for f in fr),count)
    def test_per_flight_nosing_rejected(self):
        f=ResidentialFields(tread_front_overhang_mm=1000)
        with self.assertRaises(ValueError): prepare_multiflight_residential_geometry(POINTS,"FORWARD",0,2800,16,900,30,12,point_ids=IDS,fields=f)
    def test_source_ui_and_transaction_foundations(self):
        source=(ROOT/'japanese_house_modeler/stair_operators.py').read_text(); ui=(ROOT/'japanese_house_modeler/ui.py').read_text()
        self.assertIn('class JHM_OT_move_stair_path_point',source);self.assertIn('prepare_multiflight_residential_geometry',source);self.assertIn('折れ点 1 を移動',ui)
    def test_operator_production_wiring(self):
        source=(ROOT/'japanese_house_modeler/stair_operators.py').read_text()
        self.assertIn('resolve_creation_candidate(',source);self.assertIn('shift=event.shift',source)
        self.assertIn('_visible_wall_endpoint_coordinates(context)',source)
        self.assertIn('guide_candidates=guides',source);self.assertIn('draw_handler_add(',source);self.assertIn('draw_handler_remove(',source)
        self.assertNotIn('wall.connections.add',source);self.assertNotIn('split_wall',source)
        self.assertIn('creation_right_angle_guide_rays(',source)
        self.assertNotIn('if self._start_point is None or self._candidate is None:',source)
    def test_fragments_closed_nonzero_and_turn_join_finite(self):
        _layout,fragments,mesh=self.prepare("SLOPED_CLOSED","SLOPED","ROUND")
        for fragment in fragments:
            self.assertTrue(all(math.isfinite(value) for vertex in fragment.vertices for value in vertex))
            edges={}
            for face in fragment.faces:
                self.assertGreaterEqual(len(set(face)),3)
                for a,b in zip(face,face[1:]+face[:1]): edges[tuple(sorted((a,b)))]=edges.get(tuple(sorted((a,b))),0)+1
            self.assertTrue(all(count==2 for count in edges.values()))
        self.assertEqual(set(mesh.face_roles),{"TREAD","RISER","UNDERSIDE","SIDE_BOARD"})
    def test_flight_underbodies_contact_landing_foundation(self):
        layout,fragments,_mesh=self.prepare(left=False,right=False)
        bodies=[fragment for fragment in fragments if fragment.part_type=="UNDERBODY"]
        self.assertEqual(len(bodies),3)
        def bounds(fragment):
            return tuple((min(vertex[axis] for vertex in fragment.vertices),max(vertex[axis] for vertex in fragment.vertices)) for axis in range(3))
        ordered=[bodies[0],bodies[-1],bodies[1]]
        for first,second in zip(ordered,ordered[1:]):
            self.assertTrue(all(max(a[0],b[0])<=min(a[1],b[1])+1e-9 for a,b in zip(bounds(first),bounds(second))))
        self.assertGreaterEqual(min(vertex[2] for fragment in bodies for vertex in fragment.vertices),layout.base_z)
    def test_landing_tread_underbody_do_not_overlap(self):
        layout,fragments,mesh=self.prepare(left=False,right=False)
        tread,body=fragments[-2],fragments[-1]
        tread_bottom=min(vertex[2] for vertex in tread.vertices)
        outgoing=layout.flights[1];origin=outgoing.start_xy
        landing_vertices=[vertex for vertex in body.vertices
                          if ((vertex[0]-origin[0])*outgoing.forward[0]
                              +(vertex[1]-origin[1])*outgoing.forward[1])<=1e-9]
        body_top=max(vertex[2] for vertex in landing_vertices)
        self.assertAlmostEqual(tread_bottom,body_top)
        self.assertAlmostEqual(max(vertex[2] for vertex in tread.vertices),layout.landing.top_z)
        self.assertLess(body_top,layout.landing.top_z)
        self.assertEqual(tread.part_type,"TREAD")
        self.assertEqual(body.part_type,"UNDERBODY")
    def test_landing_board_turn_mapping_and_openings(self):
        for points,outer in ((POINTS,"RIGHT"),(((0,0),(3,0),(3,-3)),"LEFT")):
            for mode in ("STEPPED","SLOPED"):
                for left,right in ((True,False),(False,True),(True,True),(False,False)):
                    with self.subTest(points=points,mode=mode,left=left,right=right):
                        layout,fragments,_mesh=self.prepare(board=mode,left=left,right=right,points=points)
                        fields=ResidentialFields(side_board_mode=mode,left_side_board_enabled=left,right_side_board_enabled=right)
                        joins=build_landing_side_board_fragments(layout,fields)
                        expected=3 if ((outer=="LEFT" and left) or (outer=="RIGHT" and right)) else 0
                        self.assertEqual(len(joins),expected)
                        center=layout.landing.center_xy; half=layout.width/2
                        portals=((layout.flights[0],-half),(layout.flights[1],half))
                        for fragment in (item for item in fragments if item.part_type=="SIDE_BOARD"):
                            for flight,plane in portals:
                                local=[((v[0]-center[0])*flight.forward[0]+(v[1]-center[1])*flight.forward[1],
                                        (v[0]-center[0])*flight.left[0]+(v[1]-center[1])*flight.left[1]) for v in fragment.vertices]
                                along=(min(p[0] for p in local),max(p[0] for p in local)); lateral=(min(p[1] for p in local),max(p[1] for p in local))
                                if along[0]-1e-9<=plane<=along[1]+1e-9:
                                    self.assertFalse(lateral[0]<half-1e-9 and lateral[1]>-half+1e-9)
    def test_upper_board_keeps_shared_flight_origin_and_reveal_semantics(self):
        fields=ResidentialFields(underside_mode="SLOPED_CLOSED",side_board_mode="STEPPED")
        layout=resolve_multiflight_layout(POINTS,"FORWARD",0,2800,16,900,30,12,point_ids=IDS)
        locals_=tuple(_flight_stair_layout(flight,layout) for flight in layout.flights)
        # Equal local dimensions yield identical accepted ordinary profiles;
        # L trimming never translates lower_xy.
        self.assertEqual(locals_[1].lower_xy,layout.flights[1].start_xy)
        upper=side_board_profile(locals_[1],fields)
        self.assertEqual(upper.lower,side_board_lower_profile(locals_[1],fields))
        reveal=fields.side_board_reveal_mm/1000
        ordinary_returns=[x for x,z in upper.outer[1:-2]]
        self.assertTrue(any(math.isclose((level-1)*locals_[1].going-reveal,x,abs_tol=1e-9)
                            for level in range(1,locals_[1].riser_count) for x in ordinary_returns))
    def test_landing_board_caps_and_top_arrival_are_vertical(self):
        fields=ResidentialFields(underside_mode="SLOPED_CLOSED",side_board_mode="STEPPED")
        layout=resolve_multiflight_layout(POINTS,"FORWARD",0,2800,16,900,30,12,point_ids=IDS)
        locals_=tuple(_flight_stair_layout(flight,layout) for flight in layout.flights)
        for index,local in enumerate(locals_):
            preserve=index==1
            fragment=_build_l_flight_board_fragment(local,"RIGHT",fields,index,preserve)
            boundary=(local.run_length if index==0 else
                      -fields.side_board_reveal_mm/1000)
            local_x=[(v[0]-local.lower_xy[0])*local.axes.forward[0]+(v[1]-local.lower_xy[1])*local.axes.forward[1] for v in fragment.vertices]
            self.assertGreaterEqual(sum(math.isclose(x,boundary,abs_tol=1e-8) for x in local_x),4)
            if index==1:
                rear=max(local_x)
                rear_z={round(v[2],9) for v,x in zip(fragment.vertices,local_x)
                        if math.isclose(x,rear,abs_tol=1e-8)}
                self.assertGreaterEqual(len(rear_z),2)
    def test_landing_front_treatment_only_changes_approach(self):
        meshes={}
        for edge in ("SQUARE","BEVEL","ROUND"):
            layout,fragments,_=self.prepare(edge=edge,left=False,right=False)
            tread=fragments[-2]
            incoming=layout.flights[0];center=layout.landing.center_xy
            local=[((v[0]-center[0])*incoming.forward[0]+(v[1]-center[1])*incoming.forward[1],
                    (v[0]-center[0])*incoming.left[0]+(v[1]-center[1])*incoming.left[1],v[2]) for v in tread.vertices]
            meshes[edge]=local
            self.assertAlmostEqual(max(v[0] for v in local),layout.width/2)
            self.assertAlmostEqual(min(v[1] for v in local),-layout.width/2)
            self.assertAlmostEqual(max(v[1] for v in local),layout.width/2)
            self.assertLess(min(v[0] for v in local),-layout.width/2)
        self.assertNotEqual(len(meshes["SQUARE"]),len(meshes["BEVEL"]))
        self.assertNotEqual(len(meshes["BEVEL"]),len(meshes["ROUND"]))
    def test_landing_body_depth_is_profile_derived_not_width(self):
        depths=[]
        for width in (900,1100):
            layout,fragments,_=prepare_multiflight_residential_geometry(
                POINTS,"FORWARD",0,2800,16,width,30,12,point_ids=IDS,
                fields=ResidentialFields(underside_mode="SLOPED_CLOSED",
                                         left_side_board_enabled=False,
                                         right_side_board_enabled=False))
            body=fragments[-1]
            depths.append(max(v[2] for v in body.vertices)-min(v[2] for v in body.vertices))
            self.assertNotAlmostEqual(min(v[2] for v in body.vertices),layout.landing.top_z-layout.width)
        self.assertNotAlmostEqual(abs(depths[1]-depths[0]),0.2)
    def test_lower_flight_ordinary_profile_is_preserved_before_landing_clip(self):
        fields=ResidentialFields(underside_mode="SLOPED_CLOSED",side_board_mode="STEPPED")
        layout=resolve_multiflight_layout(POINTS,"FORWARD",0,2800,16,900,30,12,point_ids=IDS)
        local=_flight_stair_layout(layout.flights[0],layout)
        accepted=side_board_profile(local,fields)
        fragment=_build_l_flight_board_fragment(local,"RIGHT",fields,0)
        self.assertTrue(fragment.vertices)
        self.assertEqual(accepted.lower,side_board_lower_profile(local,fields))
    def test_landing_material_role_boundaries(self):
        layout,fragments,mesh=self.prepare(underside="SLOPED_CLOSED")
        tread,landing_body=fragments[-2:]
        self.assertEqual((tread.part_type,landing_body.part_type),
                         ("TREAD","UNDERBODY"))
        self.assertNotIn("LANDING",mesh.face_roles)
        incoming=layout.flights[0]
        final_risers=[part for part in fragments if part.part_type=="RISER"
                      and math.isclose(max(v[2] for v in part.vertices),
                                       layout.landing.top_z-layout.tread_thickness,
                                       abs_tol=1e-9)]
        self.assertEqual(len(final_risers),1)
        riser=final_risers[0]
        axis=incoming.forward;origin=layout.landing.center_xy
        riser_front=min((v[0]-origin[0])*axis[0]+(v[1]-origin[1])*axis[1]
                        for v in riser.vertices)
        body_front=min((v[0]-origin[0])*axis[0]+(v[1]-origin[1])*axis[1]
                       for v in landing_body.vertices)
        self.assertGreater(body_front,riser_front)
    def test_enabled_landing_fascia_reaches_resolved_soffit(self):
        fields=ResidentialFields(underside_mode="SLOPED_CLOSED",
                                 left_side_board_enabled=True,
                                 right_side_board_enabled=True)
        layout=resolve_multiflight_layout(POINTS,"FORWARD",0,2800,16,900,30,12,point_ids=IDS)
        locals_=tuple(_flight_stair_layout(flight,layout) for flight in layout.flights)
        soffit=side_board_lower_profile(locals_[0],fields)[-1][1]
        boards=build_landing_side_board_fragments(layout,fields,1,soffit)
        self.assertEqual(len(boards),3)
        self.assertTrue(all(math.isclose(min(v[2] for v in board.vertices),soffit)
                            for board in boards))
        self.assertTrue(all(board.part_type=="SIDE_BOARD" for board in boards))
    def test_first_upper_outer_reveal_survives_without_inner_opening_intrusion(self):
        fields=ResidentialFields(underside_mode="SLOPED_CLOSED",side_board_mode="STEPPED")
        layout=resolve_multiflight_layout(POINTS,"FORWARD",0,2800,16,900,30,12,point_ids=IDS)
        local=_flight_stair_layout(layout.flights[1],layout)
        outer=_build_l_flight_board_fragment(local,"RIGHT",fields,1,True)
        inner=_build_l_flight_board_fragment(local,"LEFT",fields,1,False)
        def minimum_x(fragment):
            return min((v[0]-local.lower_xy[0])*local.axes.forward[0]
                       +(v[1]-local.lower_xy[1])*local.axes.forward[1]
                       for v in fragment.vertices)
        self.assertAlmostEqual(minimum_x(outer),-fields.side_board_reveal_mm/1000)
        self.assertAlmostEqual(minimum_x(inner),0.0)
    def test_outgoing_transition_has_diagonal_soffit_and_contacts(self):
        layout,fragments,_mesh=self.prepare(underside="SLOPED_CLOSED",left=False,right=False)
        transition=fragments[-1]
        outgoing=layout.flights[1];origin=outgoing.start_xy
        outgoing_local=_flight_stair_layout(outgoing,layout)
        fields=ResidentialFields(underside_mode="SLOPED_CLOSED")
        soffit=side_board_lower_profile(
            _flight_stair_layout(layout.flights[0],layout),fields)[-1][1]
        baseline=_upper_section_baseline(layout,outgoing_local,fields,soffit)
        self.assertEqual(len(baseline),2)
        self.assertLess(baseline[0][0],0);self.assertGreater(baseline[1][0],0)
        self.assertGreater(baseline[1][1],baseline[0][1])
        self.assertEqual(transition.part_type,"UNDERBODY")
    def test_sloped_upper_body_starts_on_visible_slope_contact(self):
        fields=ResidentialFields(underside_mode="SLOPED_CLOSED")
        layout=resolve_multiflight_layout(POINTS,"FORWARD",0,2800,16,900,30,12,point_ids=IDS)
        local=_flight_stair_layout(layout.flights[1],layout)
        contact=side_board_lower_profile(local,fields)[1]
        body=_build_l_flight_underbody_fragment(local,fields,1)
        local_x=[(v[0]-local.lower_xy[0])*local.axes.forward[0]
                 +(v[1]-local.lower_xy[1])*local.axes.forward[1]
                 for v in body.vertices]
        self.assertAlmostEqual(min(local_x),contact[0])
        lower=side_board_lower_profile(local,fields)
        slope=(lower[2][1]-lower[1][1])/(lower[2][0]-lower[1][0])
        self.assertAlmostEqual(contact[1],lower[2][1]-slope*(lower[2][0]-contact[0]))
    def test_stepped_upper_underbody_regression_unchanged(self):
        fields=ResidentialFields(underside_mode="STEPPED_CLOSED")
        layout=resolve_multiflight_layout(POINTS,"FORWARD",0,2800,16,900,30,12,point_ids=IDS)
        local=_flight_stair_layout(layout.flights[1],layout)
        self.assertEqual(_build_l_flight_underbody_fragment(local,fields,1),
                         build_underbody_fragment(local,fields))
    def test_side_board_and_transition_share_outer_contact_plane(self):
        fields=ResidentialFields(underside_mode="SLOPED_CLOSED",
                                 left_side_board_enabled=True,
                                 right_side_board_enabled=True)
        layout=resolve_multiflight_layout(POINTS,"FORWARD",0,2800,16,900,30,12,point_ids=IDS)
        local=_flight_stair_layout(layout.flights[1],layout)
        soffit=side_board_lower_profile(_flight_stair_layout(layout.flights[0],layout),fields)[-1][1]
        transition=_build_sloped_upper_section_fragment(layout,local,fields,soffit,1)
        board=_build_l_flight_board_fragment(local,"RIGHT",fields,1,True)
        def local_y(fragment):
            return [(v[0]-local.lower_xy[0])*local.axes.left[0]
                    +(v[1]-local.lower_xy[1])*local.axes.left[1]
                    for v in fragment.vertices]
        self.assertAlmostEqual(min(local_y(transition)),-layout.width/2)
        self.assertAlmostEqual(max(local_y(board)),-layout.width/2)
        self.assertGreater(max(local_y(transition)),min(local_y(transition)))
    def test_side_board_and_body_use_identical_straight_baseline(self):
        fields=ResidentialFields(underside_mode="SLOPED_CLOSED",
                                 side_board_mode="SLOPED")
        layout=resolve_multiflight_layout(POINTS,"FORWARD",0,2800,16,900,30,12,point_ids=IDS)
        lower=_flight_stair_layout(layout.flights[0],layout)
        upper=_flight_stair_layout(layout.flights[1],layout)
        soffit=side_board_lower_profile(lower,fields)[-1][1]
        baseline=_upper_section_baseline(layout,upper,fields,soffit)
        board=_build_l_flight_board_fragment(
            upper,"RIGHT",fields,1,True,baseline)
        local=[((v[0]-upper.lower_xy[0])*upper.axes.forward[0]
                +(v[1]-upper.lower_xy[1])*upper.axes.forward[1],v[2])
               for v in board.vertices]
        for x in (-fields.side_board_reveal_mm/1000,baseline[1][0]):
            zs=[z for px,z in local if math.isclose(px,x,abs_tol=1e-8)]
            self.assertTrue(zs);self.assertAlmostEqual(min(zs),_baseline_z(baseline,x))
        self.assertEqual(len(baseline),2)

if __name__ == '__main__': unittest.main()
