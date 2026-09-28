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
    _clip_profile_x,
    _build_landing_tread_fragment, _build_landing_underbody_fragment,
    _build_landing_underbody_transition,
    _build_sloped_upper_underbody_fragment, _flight_stair_layout,
    _resolve_lower_outer_board_terminal, _resolve_upper_start_reveal,
    _resolve_upper_turn_soffit,
    canonical_multi_path, distribution_edit_initial_allocation,
    prepare_multiflight_residential_geometry,
    resolve_multiflight_layout, segment_allocations, switch_distribution_mode,
    validate_manual_allocation)
from japanese_house_modeler.stair_residential import ResidentialFields
from japanese_house_modeler.stair_residential_geometry import (
    build_underbody_fragment, build_residential_riser_fragments,
    build_residential_tread_fragments, build_top_arrival_nosing_fragment,
    side_board_lower_profile, side_board_profile,
    sloped_side_board_profile, sloped_underbody_profile,
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
        l,fr,m=self.prepare(underside="SLOPED_CLOSED",left=False,right=False)
        landing=fr[-1]
        self.assertEqual(landing.part_type,"TREAD")
        self.assertAlmostEqual(max(v[2] for v in landing.vertices)-min(v[2] for v in landing.vertices),l.tread_thickness)
        self.assertEqual(sum(f.part_type=="UNDERBODY" for f in fr),3)
        self.assertIn("UNDERSIDE",m.face_roles)
    def test_board_sides(self):
        for left,right,count in ((True,True,5),(True,False,2),(False,True,3),(False,False,0)):
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
        layout,fragments,_mesh=self.prepare(underside="SLOPED_CLOSED",left=False,right=False)
        bodies=[fragment for fragment in fragments if fragment.part_type=="UNDERBODY"]
        self.assertEqual(len(bodies),3)
        # Each straight Flight owns exactly its accepted local closed body;
        # there is no Landing-spanning transition or filler body.
        locals_=tuple(_flight_stair_layout(flight,layout) for flight in layout.flights)
        fields=ResidentialFields(underside_mode="SLOPED_CLOSED",left_side_board_enabled=False,right_side_board_enabled=False)
        turn_z,_lower=_resolve_upper_turn_soffit(locals_[1],fields)
        self.assertEqual(bodies[0],build_underbody_fragment(locals_[0],fields))
        self.assertEqual(bodies[1],_build_sloped_upper_underbody_fragment(
            locals_[1],fields,turn_z))
        self.assertEqual(bodies[2],_build_landing_underbody_fragment(
            layout,fields,bodies[2].ordinal,turn_z))
        self.assertGreaterEqual(min(vertex[2] for fragment in bodies for vertex in fragment.vertices),layout.base_z)
    def test_landing_tread_underbody_do_not_overlap(self):
        layout,fragments,_mesh=self.prepare(underside="SLOPED_CLOSED",left=False,right=False)
        tread=fragments[-1]
        self.assertEqual(tread.part_type,"TREAD")
        self.assertAlmostEqual(max(v[2] for v in tread.vertices),layout.landing.top_z)
        self.assertAlmostEqual(min(v[2] for v in tread.vertices),layout.landing.top_z-layout.tread_thickness)
        bodies=[f for f in fragments if f.part_type=="UNDERBODY"]
        self.assertEqual(len(bodies),3)
        turn=bodies[-1]
        upper=_flight_stair_layout(layout.flights[1],layout)
        turn_z,_lower=_resolve_upper_turn_soffit(
            upper,ResidentialFields(underside_mode="SLOPED_CLOSED"))
        self.assertAlmostEqual(min(v[2] for v in turn.vertices),turn_z)
        expected_thickness=ResidentialFields().underside_thickness_mm/1000
        self.assertAlmostEqual(max(v[2] for v in turn.vertices)-min(v[2] for v in turn.vertices),expected_thickness)
        self.assertLess(max(v[2] for v in turn.vertices),min(v[2] for v in tread.vertices))
    def test_landing_board_turn_mapping_and_openings(self):
        for points,outer in ((POINTS,"RIGHT"),(((0,0),(3,0),(3,-3)),"LEFT")):
            for mode in ("STEPPED","SLOPED"):
                for left,right in ((True,False),(False,True),(True,True),(False,False)):
                    with self.subTest(points=points,mode=mode,left=left,right=right):
                        layout,fragments,_mesh=self.prepare(board=mode,left=left,right=right,points=points)
                        fields=ResidentialFields(side_board_mode=mode,left_side_board_enabled=left,right_side_board_enabled=right)
                        joins=build_landing_side_board_fragments(layout,fields)
                        expected=1 if ((outer=="LEFT" and left) or (outer=="RIGHT" and right)) else 0
                        self.assertEqual(len(joins),expected)
                        if joins:
                            center=layout.landing.center_xy;half=layout.width/2
                            incoming=layout.flights[0]
                            local=[((v[0]-center[0])*incoming.forward[0]+(v[1]-center[1])*incoming.forward[1],
                                    (v[0]-center[0])*incoming.left[0]+(v[1]-center[1])*incoming.left[1])
                                   for v in joins[0].vertices]
                            # Every perimeter vertex stays on or outside the
                            # square boundary; neither opening is fenced.
                            self.assertTrue(all(abs(x)>=half-1e-9 or abs(y)>=half-1e-9
                                                for x,y in local))
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
        tread=fragments[-1]
        self.assertEqual(tread.part_type,"TREAD")
        self.assertNotIn("LANDING",mesh.face_roles)
        incoming=layout.flights[0]
        final_risers=[part for part in fragments if part.part_type=="RISER"
                      and math.isclose(max(v[2] for v in part.vertices),
                                       layout.landing.top_z-layout.tread_thickness,
                                       abs_tol=1e-9)]
        self.assertEqual(len(final_risers),1)
        self.assertEqual(sum(f.part_type=="UNDERBODY" for f in fragments),3)
    def test_enabled_landing_fascia_reaches_resolved_soffit(self):
        fields=ResidentialFields(underside_mode="SLOPED_CLOSED",
                                 left_side_board_enabled=True,
                                 right_side_board_enabled=True)
        layout,fragments,_mesh=prepare_multiflight_residential_geometry(
            POINTS,"FORWARD",0,2800,16,900,30,12,point_ids=IDS,fields=fields)
        locals_=tuple(_flight_stair_layout(flight,layout) for flight in layout.flights)
        turn_z,_lower=_resolve_upper_turn_soffit(locals_[1],fields)
        incoming_old=side_board_lower_profile(locals_[0],fields)[-1][1]
        perimeter=[part for part in fragments if part.part_type=="SIDE_BOARD"][-1]
        self.assertAlmostEqual(min(v[2] for v in perimeter.vertices),turn_z)
        self.assertNotAlmostEqual(turn_z,incoming_old)
        self.assertEqual((perimeter,),build_landing_side_board_fragments(
            layout,fields,perimeter.ordinal,turn_z))
    def test_upper_boards_share_deterministic_turn_start(self):
        for points in (POINTS,((0,0),(3,0),(3,-3))):
            fields=ResidentialFields(underside_mode="SLOPED_CLOSED",
                                     side_board_mode="STEPPED")
            layout=resolve_multiflight_layout(
                points,"FORWARD",0,2800,16,900,30,12,point_ids=IDS)
            local=_flight_stair_layout(layout.flights[1],layout)
            turn_z,lower=_resolve_upper_turn_soffit(local,fields)
            for side in ("LEFT","RIGHT"):
                board=_build_l_flight_board_fragment(
                    local,side,fields,1,False,lower)
                local_xz=[((v[0]-local.lower_xy[0])*local.axes.forward[0]
                           +(v[1]-local.lower_xy[1])*local.axes.forward[1],v[2])
                          for v in board.vertices]
                at_start=[z for x,z in local_xz if math.isclose(x,0,abs_tol=1e-9)]
                self.assertIn(turn_z,at_start)
    def test_upper_only_reveal_restoration_tracks_profile_and_value(self):
        from japanese_house_modeler.stair_geometry import validate_simple_polygon
        for points in (POINTS,((0,0),(3,0),(3,-3))):
            for mode in ("STEPPED","SLOPED"):
                for reveal_mm in (20,40,60):
                    with self.subTest(points=points,mode=mode,reveal=reveal_mm):
                        fields=ResidentialFields(
                            underside_mode="SLOPED_CLOSED",side_board_mode=mode,
                            side_board_reveal_mm=reveal_mm)
                        layout=resolve_multiflight_layout(
                            points,"FORWARD",0,2800,16,900,30,12,point_ids=IDS)
                        local=_flight_stair_layout(layout.flights[1],layout)
                        _turn_z,lower=_resolve_upper_turn_soffit(local,fields)
                        profile=(sloped_side_board_profile(local,fields)
                                 if mode=="SLOPED" else side_board_profile(local,fields))
                        source=validate_simple_polygon(
                            profile.outer+tuple(reversed(lower)))
                        floor=local.base_z+reveal_mm/1000
                        restored=_resolve_upper_start_reveal(
                            source,reveal_mm/1000,floor)
                        self.assertAlmostEqual(min(x for x,_z in restored),
                                               -reveal_mm/1000)
                        self.assertTrue(all(z>=floor-1e-9 for x,z in restored if x<0))
                        current=validate_simple_polygon(
                            _clip_profile_x(source,0,keep_greater=True))
                        self.assertEqual({p for p in restored if p[0]>1e-9},
                                         {p for p in current if p[0]>1e-9})
                        _built_layout,built_fragments,_mesh=(
                            prepare_multiflight_residential_geometry(
                                points,"FORWARD",0,2800,16,900,30,12,
                                point_ids=IDS,fields=fields))
                        production_boards=[part for part in built_fragments
                                           if part.part_type=="SIDE_BOARD"]
                        cross=(layout.flights[0].forward[0]*layout.flights[1].forward[1]
                               -layout.flights[0].forward[1]*layout.flights[1].forward[0])
                        outer="RIGHT" if cross>0 else "LEFT"
                        for side in ("LEFT","RIGHT"):
                            fragment=_build_l_flight_board_fragment(
                                local,side,fields,1,False,lower,False,None,
                                floor if side==outer else None)
                            local_xz=[((v[0]-local.lower_xy[0])*local.axes.forward[0]
                                       +(v[1]-local.lower_xy[1])*local.axes.forward[1],v[2])
                                      for v in fragment.vertices]
                            expected_min=-reveal_mm/1000 if side==outer else 0.0
                            self.assertAlmostEqual(min(x for x,_z in local_xz),expected_min)
                            if side==outer:
                                self.assertTrue(all(z>=floor-1e-9
                                                    for x,z in local_xz if x<0))
                            self.assertIn(fragment,production_boards)
    def test_zero_reveal_helper_is_exact_r14_clip(self):
        from japanese_house_modeler.stair_geometry import validate_simple_polygon
        fields=ResidentialFields(underside_mode="SLOPED_CLOSED")
        layout=resolve_multiflight_layout(
            POINTS,"FORWARD",0,2800,16,900,30,12,point_ids=IDS)
        local=_flight_stair_layout(layout.flights[1],layout)
        _turn_z,lower=_resolve_upper_turn_soffit(local,fields)
        profile=side_board_profile(local,fields)
        source=validate_simple_polygon(profile.outer+tuple(reversed(lower)))
        self.assertEqual(_resolve_upper_start_reveal(source,0,local.base_z),
                         validate_simple_polygon(
                             _clip_profile_x(source,0,keep_greater=True)))
    def test_lower_is_accepted_and_upper_only_replaces_initial_foot(self):
        fields=ResidentialFields(underside_mode="SLOPED_CLOSED")
        for points in (POINTS,((0,0),(3,0),(3,-3))):
            with self.subTest(points=points):
                layout,fragments,_mesh=self.prepare(
                    underside="SLOPED_CLOSED",left=False,right=False,points=points)
                bodies=[part for part in fragments if part.part_type=="UNDERBODY"]
                locals_=tuple(_flight_stair_layout(flight,layout) for flight in layout.flights)
                self.assertEqual(len(bodies),3)
                self.assertEqual(bodies[0],build_underbody_fragment(locals_[0],fields))
                turn_z,lower=_resolve_upper_turn_soffit(locals_[1],fields)
                self.assertEqual(bodies[1],_build_sloped_upper_underbody_fragment(
                    locals_[1],fields,turn_z))
                accepted=sloped_underbody_profile(locals_[1],fields).outer
                self.assertEqual(lower[1:],accepted[-2:])
                slope=(accepted[-1][1]-accepted[-2][1])/(accepted[-1][0]-accepted[-2][0])
                self.assertAlmostEqual(turn_z,accepted[-2][1]-slope*accepted[-2][0])
                local_xz=[((v[0]-locals_[1].lower_xy[0])*locals_[1].axes.forward[0]
                           +(v[1]-locals_[1].lower_xy[1])*locals_[1].axes.forward[1],v[2])
                          for v in bodies[1].vertices]
                at_start=[z for x,z in local_xz if math.isclose(x,0,abs_tol=1e-9)]
                self.assertIn(turn_z,at_start)
                self.assertTrue(math.isclose((lower[1][1]-lower[0][1])
                    /(lower[1][0]-lower[0][0]),slope,abs_tol=1e-9))
    def test_landing_slab_footprint_and_thickness(self):
        for points in (POINTS,((0,0),(3,0),(3,-3))):
            layout,fragments,_mesh=self.prepare(
                underside="SLOPED_CLOSED",left=False,right=False,points=points)
            landing=fragments[-1]
            incoming=layout.flights[0];center=layout.landing.center_xy
            local=[((v[0]-center[0])*incoming.forward[0]+(v[1]-center[1])*incoming.forward[1],
                    (v[0]-center[0])*incoming.left[0]+(v[1]-center[1])*incoming.left[1],v[2])
                   for v in landing.vertices]
            self.assertAlmostEqual(max(v[0] for v in local),layout.width/2)
            # Nosing affects only the incoming approach edge; canonical rear
            # depth and lateral footprint remain exactly w.
            self.assertAlmostEqual(max(v[0] for v in local)-(-layout.width/2),layout.width)
            self.assertAlmostEqual(max(v[1] for v in local)-min(v[1] for v in local),layout.width)
            self.assertAlmostEqual(max(v[2] for v in local)-min(v[2] for v in local),layout.tread_thickness)
            turn=[part for part in fragments if part.part_type=="UNDERBODY"][-1]
            turn_local=[((v[0]-center[0])*incoming.forward[0]+(v[1]-center[1])*incoming.forward[1],
                         (v[0]-center[0])*incoming.left[0]+(v[1]-center[1])*incoming.left[1],v[2])
                        for v in turn.vertices]
            self.assertAlmostEqual(max(v[0] for v in turn_local)-min(v[0] for v in turn_local),layout.width)
            self.assertAlmostEqual(max(v[1] for v in turn_local)-min(v[1] for v in turn_local),layout.width)
            self.assertEqual(len({round(v[2],10) for v in turn_local}),2)
            turn_z,_lower=_resolve_upper_turn_soffit(
                _flight_stair_layout(layout.flights[1],layout),
                ResidentialFields(underside_mode="SLOPED_CLOSED"))
            self.assertAlmostEqual(min(v[2] for v in turn_local),turn_z)
            self.assertLess(max(v[2] for v in turn_local),min(v[2] for v in local))
    def test_landing_board_is_one_continuous_perimeter_without_filler(self):
        for points,side in ((POINTS,"RIGHT"),(((0,0),(3,0),(3,-3)),"LEFT")):
            fields=ResidentialFields(underside_mode="SLOPED_CLOSED",
                left_side_board_enabled=side=="LEFT",right_side_board_enabled=side=="RIGHT")
            layout=resolve_multiflight_layout(points,"FORWARD",0,2800,16,900,30,12,point_ids=IDS)
            joins=build_landing_side_board_fragments(layout,fields)
            self.assertEqual(len(joins),1)
            join=joins[0]
            self.assertEqual(join.part_type,"SIDE_BOARD")
            self.assertEqual(len(join.vertices),12)
            self.assertEqual(len(join.faces),8)
            edges={}
            for face in join.faces:
                for a,b in zip(face,face[1:]+face[:1]):
                    edge=tuple(sorted((a,b)));edges[edge]=edges.get(edge,0)+1
            self.assertTrue(all(count==2 for count in edges.values()))
    def test_landing_perimeter_has_no_positive_volume_board_overlap(self):
        for points in (POINTS,((0,0),(3,0),(3,-3))):
            layout,fragments,_mesh=self.prepare(
                underside="SLOPED_CLOSED",left=True,right=True,points=points)
            boards=[part for part in fragments if part.part_type=="SIDE_BOARD"]
            perimeter=boards[-1]
            incoming=layout.flights[0]
            cross=(incoming.forward[0]*layout.flights[1].forward[1]
                   -incoming.forward[1]*layout.flights[1].forward[0])
            outer_board=boards[1 if cross>0 else 0]
            local=_flight_stair_layout(incoming,layout)
            tail=[v for v in outer_board.vertices
                  if ((v[0]-local.lower_xy[0])*local.axes.forward[0]
                      +(v[1]-local.lower_xy[1])*local.axes.forward[1])
                     > local.run_length+1e-9]
            self.assertTrue(tail)
            self.assertLessEqual(max(v[2] for v in tail),
                                 min(v[2] for v in perimeter.vertices)+1e-9)
    def test_only_lower_outer_terminal_extends_to_body_end(self):
        for points in (POINTS,((0,0),(3,0),(3,-3))):
            for mode in ("STEPPED","SLOPED"):
                for riser_mm in (8,12,18):
                    with self.subTest(points=points,mode=mode,riser_mm=riser_mm):
                        fields=ResidentialFields(
                            underside_mode="SLOPED_CLOSED",side_board_mode=mode)
                        layout,fragments,_mesh=prepare_multiflight_residential_geometry(
                            points,"FORWARD",0,2800,16,900,30,riser_mm,
                            point_ids=IDS,fields=fields)
                        lower=_flight_stair_layout(layout.flights[0],layout)
                        upper=_flight_stair_layout(layout.flights[1],layout)
                        turn_z,_profile=_resolve_upper_turn_soffit(upper,fields)
                        cross=(layout.flights[0].forward[0]*layout.flights[1].forward[1]
                               -layout.flights[0].forward[1]*layout.flights[1].forward[0])
                        outer="RIGHT" if cross>0 else "LEFT"
                        inner="LEFT" if outer=="RIGHT" else "RIGHT"
                        extended=_build_l_flight_board_fragment(
                            lower,outer,fields,0,False,None,True,turn_z)
                        unchanged=_build_l_flight_board_fragment(
                            lower,inner,fields,0)
                        def local_xz(fragment):
                            return [((v[0]-lower.lower_xy[0])*lower.axes.forward[0]
                                     +(v[1]-lower.lower_xy[1])*lower.axes.forward[1],v[2])
                                    for v in fragment.vertices]
                        outer_xz=local_xz(extended);inner_xz=local_xz(unchanged)
                        terminal=lower.run_length+lower.riser_thickness
                        self.assertAlmostEqual(max(x for x,_z in outer_xz),terminal)
                        self.assertAlmostEqual(max(x for x,_z in inner_xz),lower.run_length)
                        self.assertAlmostEqual(terminal-lower.run_length,riser_mm/1000)
                        tail=[(x,z) for x,z in outer_xz if x>lower.run_length+1e-9]
                        self.assertTrue(tail)
                        self.assertLessEqual(max(z for _x,z in tail),turn_z+1e-9)
                        accepted=(sloped_side_board_profile(lower,fields)
                                  if mode=="SLOPED" else side_board_profile(lower,fields))
                        terminal_bottom=min(z for x,z in outer_xz
                                            if math.isclose(x,terminal,abs_tol=1e-9))
                        self.assertAlmostEqual(terminal_bottom,accepted.lower[-1][1])
                        production_boards=[part for part in fragments
                                           if part.part_type=="SIDE_BOARD"]
                        self.assertIn(extended,production_boards)
                        self.assertIn(unchanged,production_boards)
    def test_terminal_change_leaves_all_non_board_fragments_canonical(self):
        fields=ResidentialFields(underside_mode="SLOPED_CLOSED",
                                 left_side_board_enabled=True,
                                 right_side_board_enabled=True)
        layout,fragments,_mesh=prepare_multiflight_residential_geometry(
            POINTS,"FORWARD",0,2800,16,900,30,12,point_ids=IDS,fields=fields)
        locals_=tuple(_flight_stair_layout(flight,layout) for flight in layout.flights)
        turn_z,_lower=_resolve_upper_turn_soffit(locals_[1],fields)
        expected=[]
        for index,local in enumerate(locals_):
            expected.extend(build_residential_tread_fragments(local,fields))
            if index==1:
                cap=build_top_arrival_nosing_fragment(local,fields)
                if cap is not None: expected.append(cap)
            expected.extend(build_residential_riser_fragments(local,fields))
            expected.append(build_underbody_fragment(local,fields) if index==0
                            else _build_sloped_upper_underbody_fragment(local,fields,turn_z))
        nonboards=[part for part in fragments if part.part_type!="SIDE_BOARD"]
        turn=next(part for part in nonboards[len(expected):]
                  if part.part_type=="UNDERBODY")
        landing=nonboards[-1]
        expected.append(_build_landing_underbody_fragment(
            layout,fields,turn.ordinal,turn_z))
        expected.append(_build_landing_tread_fragment(
            layout,fields,landing.ordinal))
        self.assertEqual(tuple(nonboards),tuple(expected))
    def test_disabled_outer_board_does_not_create_terminal_extension(self):
        for points,outer in ((POINTS,"RIGHT"),(((0,0),(3,0),(3,-3)),"LEFT")):
            fields=ResidentialFields(
                underside_mode="SLOPED_CLOSED",
                left_side_board_enabled=outer!="LEFT",
                right_side_board_enabled=outer!="RIGHT")
            layout,fragments,_mesh=prepare_multiflight_residential_geometry(
                points,"FORWARD",0,2800,16,900,30,12,
                point_ids=IDS,fields=fields)
            lower=_flight_stair_layout(layout.flights[0],layout)
            boards=[part for part in fragments if part.part_type=="SIDE_BOARD"]
            self.assertEqual(len(boards),2)
            local_x=[(v[0]-lower.lower_xy[0])*lower.axes.forward[0]
                     +(v[1]-lower.lower_xy[1])*lower.axes.forward[1]
                     for v in boards[0].vertices]
            self.assertAlmostEqual(max(local_x),lower.run_length)
    def test_sloped_production_has_three_owned_underbody_regions(self):
        _layout,fragments,_mesh=self.prepare(
            underside="SLOPED_CLOSED",left=False,right=False)
        underbodies=[fragment for fragment in fragments if fragment.part_type=="UNDERBODY"]
        self.assertEqual(len(underbodies),3)
        self.assertEqual(fragments[-1].part_type,"TREAD")
        for fragment in underbodies:
            edges={}
            for face in fragment.faces:
                for a,b in zip(face,face[1:]+face[:1]):
                    key=tuple(sorted((a,b)));edges[key]=edges.get(key,0)+1
            self.assertTrue(all(count==2 for count in edges.values()))
    def test_sloped_parts_do_not_duplicate_visible_tread_faces(self):
        for points in (POINTS,((0,0),(3,0),(3,-3))):
            layout,fragments,_mesh=self.prepare(
                underside="SLOPED_CLOSED",left=True,right=True,points=points)
            owners={}
            for fragment in fragments:
                for face in fragment.faces:
                    key=tuple(sorted(tuple(round(value,10) for value in fragment.vertices[index])
                                     for index in face))
                    prior=owners.get(key)
                    if prior is not None:
                        roles=(prior,fragment.part_type)
                        if "TREAD" in roles:
                            # The sole TREAD contact is the hidden interface
                            # between Landing slab and thin turn body, never
                            # the finished walking top.
                            self.assertIn("UNDERBODY",roles)
                            self.assertTrue(all(math.isclose(vertex[2],
                                layout.landing.top_z-layout.tread_thickness)
                                for vertex in key))
                    owners[key]=fragment.part_type
    def test_stepped_upper_underbody_regression_unchanged(self):
        fields=ResidentialFields(underside_mode="STEPPED_CLOSED")
        layout=resolve_multiflight_layout(POINTS,"FORWARD",0,2800,16,900,30,12,point_ids=IDS)
        local=_flight_stair_layout(layout.flights[1],layout)
        self.assertEqual(_build_l_flight_underbody_fragment(local,fields,1),
                         build_underbody_fragment(local,fields))


if __name__ == '__main__': unittest.main()
