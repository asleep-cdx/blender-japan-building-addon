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
    canonical_multi_path, distribution_edit_initial_allocation,
    prepare_multiflight_residential_geometry,
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
        l,fr,m=self.prepare(); self.assertEqual(fr[-3].part_type,"TREAD");self.assertEqual(fr[-2].part_type,"UNDERBODY");self.assertEqual(fr[-1].part_type,"UNDERBODY");self.assertIn("UNDERSIDE",m.face_roles)
    def test_board_sides(self):
        for left,right,count in ((True,True,6),(True,False,2),(False,True,4),(False,False,0)):
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
        self.assertEqual(len(bodies),4)
        def bounds(fragment):
            return tuple((min(vertex[axis] for vertex in fragment.vertices),max(vertex[axis] for vertex in fragment.vertices)) for axis in range(3))
        ordered=[bodies[0],bodies[-2],bodies[-1],bodies[1]]
        for first,second in zip(ordered,ordered[1:]):
            self.assertTrue(all(max(a[0],b[0])<=min(a[1],b[1])+1e-9 for a,b in zip(bounds(first),bounds(second))))
        self.assertGreaterEqual(min(vertex[2] for fragment in bodies for vertex in fragment.vertices),layout.base_z)
    def test_landing_tread_underbody_do_not_overlap(self):
        layout,fragments,mesh=self.prepare(left=False,right=False)
        tread,body=fragments[-3],fragments[-2]
        tread_bottom=min(vertex[2] for vertex in tread.vertices)
        body_top=max(vertex[2] for vertex in body.vertices)
        self.assertAlmostEqual(tread_bottom,body_top)
        self.assertAlmostEqual(max(vertex[2] for vertex in tread.vertices),layout.landing.top_z)
        self.assertLess(body_top,layout.landing.top_z)
        self.assertTrue(all(role=="TREAD" for role in mesh.face_roles[-18:-12]))
    def test_landing_board_turn_mapping_and_openings(self):
        for points,outer in ((POINTS,"RIGHT"),(((0,0),(3,0),(3,-3)),"LEFT")):
            for mode in ("STEPPED","SLOPED"):
                for left,right in ((True,False),(False,True),(True,True),(False,False)):
                    with self.subTest(points=points,mode=mode,left=left,right=right):
                        layout,fragments,_mesh=self.prepare(board=mode,left=left,right=right,points=points)
                        fields=ResidentialFields(side_board_mode=mode,left_side_board_enabled=left,right_side_board_enabled=right)
                        joins=build_landing_side_board_fragments(layout,fields)
                        expected=2 if ((outer=="LEFT" and left) or (outer=="RIGHT" and right)) else 0
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

if __name__ == '__main__': unittest.main()
