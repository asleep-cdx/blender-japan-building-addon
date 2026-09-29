"""Build 07-D Stage 3 N-flight/U pure production contracts."""
import pathlib, sys, types, unittest
ROOT = pathlib.Path(__file__).parents[1]
package = types.ModuleType("japanese_house_modeler")
package.__path__ = [str(ROOT / "japanese_house_modeler")]
sys.modules.setdefault("japanese_house_modeler", package)
from japanese_house_modeler.stair_multiflight import (
    RISER_DISTRIBUTION_AUTO, RISER_DISTRIBUTION_MANUAL,
    _build_multiturn_residential_parts, _flight_stair_layout,
    _residential_turn_contexts, _resolve_multiturn_flight_board_polygon,
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
    @staticmethod
    def owned(points=U, direction="FORWARD", underside="SLOPED_CLOSED",
              left=True, right=True, board_mode="STEPPED", reveal=35.0,
              riser_thickness=12.0):
        layout=resolve_multiflight_layout(
            points,direction,0,2800,16,900,30,riser_thickness,
            point_ids=IDS if points==U else None,allocation=(5,6,5))
        fields=ResidentialFields(
            underside_mode=underside,left_side_board_enabled=left,
            right_side_board_enabled=right,side_board_mode=board_mode,
            side_board_reveal_mm=reveal)
        locals_=tuple(_flight_stair_layout(f,layout) for f in layout.flights)
        turns=_residential_turn_contexts(layout,locals_,fields)
        return layout,fields,locals_,turns,_build_multiturn_residential_parts(
            layout,locals_,turns,fields)

    @staticmethod
    def assert_closed(test, fragment):
        incidence={}
        for face in fragment.faces:
            test.assertGreaterEqual(len(face),3)
            for a,b in zip(face,face[1:]+face[:1]):
                edge=tuple(sorted((a,b))); incidence[edge]=incidence.get(edge,0)+1
        test.assertTrue(incidence)
        test.assertTrue(all(count==2 for count in incidence.values()))

    @staticmethod
    def local_x(local, vertex):
        dx,dy=vertex[0]-local.lower_xy[0],vertex[1]-local.lower_xy[1]
        return dx*local.axes.forward[0]+dy*local.axes.forward[1]

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
    def test_sloped_ownership_is_exactly_once(self):
        layout,fields,locals_,turns,parts=self.owned()
        self.assertEqual([x.owner_index for x in parts.flight_underbodies],[0,1,2])
        self.assertEqual(len(parts.flight_underbodies),3)
        self.assertEqual([(x.owner_index,x.side) for x in parts.flight_boards],
                         [(0,"LEFT"),(0,"RIGHT"),(1,"LEFT"),(1,"RIGHT"),(2,"LEFT"),(2,"RIGHT")])
        self.assertEqual(len(parts.landing_treads),2)
        self.assertEqual(len(parts.landing_underbodies),2)
        self.assertLess(turns[0].turn_soffit_z,turns[0].landing.top_z-turns[0].landing.thickness)
        self.assertLess(turns[1].turn_soffit_z,turns[1].landing.top_z-turns[1].landing.thickness)
        self.assertNotEqual(turns[0].turn_soffit_z,turns[1].turn_soffit_z)
    def test_r19_landings_are_low_hollow_closed_per_turn(self):
        _layout,_fields,_locals,turns,parts=self.owned(left=False,right=False)
        self.assertEqual(parts.landing_boards,())
        for turn,owned in zip(turns,parts.landing_underbodies):
            fragment=owned.fragment; zs=[v[2] for v in fragment.vertices]
            self.assertAlmostEqual(min(zs),turn.turn_soffit_z)
            self.assertGreater(len(fragment.vertices),8) # not a full-footprint box
            self.assertGreater(len(set(round(z,9) for z in zs)),2)
            self.assert_closed(self,fragment)
    def test_mirrored_chirality_owns_opposite_perimeter(self):
        mirrored=((0,0),(3,0),(3,-1.8),(0,-1.8))
        _,_,_,left_turns,left_parts=self.owned()
        _,_,_,right_turns,right_parts=self.owned(mirrored)
        self.assertEqual([t.outer_side for t in left_turns],["RIGHT","RIGHT"])
        self.assertEqual([t.outer_side for t in right_turns],["LEFT","LEFT"])
        self.assertEqual([b.side for b in left_parts.landing_boards],["RIGHT","RIGHT"])
        self.assertEqual([b.side for b in right_parts.landing_boards],["LEFT","LEFT"])
    def test_reverse_keeps_plan_owners_and_recomputes_turn_z(self):
        forward=self.owned(); reverse=self.owned(direction="REVERSE")
        self.assertEqual({x.owner_index for x in forward[4].flight_underbodies},
                         {x.owner_index for x in reverse[4].flight_underbodies})
        self.assertEqual([t.landing.center_xy for t in forward[3]],
                         list(reversed([t.landing.center_xy for t in reverse[3]])))
        self.assertEqual([round(t.landing.top_z,3) for t in forward[3]],[.875,1.925])
        self.assertEqual([round(t.landing.top_z,3) for t in reverse[3]],[.875,1.925])
    def test_middle_board_has_start_and_end_in_one_fragment(self):
        _layout,fields,locals_,_turns,parts=self.owned()
        middle=locals_[1]
        for owned in [x for x in parts.flight_boards if x.owner_index==1]:
            xs=[self.local_x(middle,v) for v in owned.fragment.vertices]
            self.assertLessEqual(min(xs),0.0)
            self.assertGreaterEqual(max(xs),middle.run_length)
        self.assertEqual(sum(x.owner_index==1 for x in parts.flight_boards),2)
    def test_four_outgoing_board_starts_use_entire_turn_lower_profile(self):
        _layout,fields,_locals,turns,parts=self.owned()
        end_by_flight={t.incoming_flight.canonical_index:t for t in turns}
        checked=[]
        for turn in turns:
            for side in ("LEFT","RIGHT"):
                polygon=_resolve_multiturn_flight_board_polygon(
                    turn.outgoing_local,side,fields,start_turn=turn,
                    end_turn=end_by_flight.get(turn.outgoing_flight.canonical_index))
                for point in turn.lower_profile:
                    self.assertTrue(any(abs(point[0]-p[0])<1e-9 and
                                        abs(point[1]-p[1])<1e-9 for p in polygon))
                self.assertTrue(any(abs(p[0])<1e-9 and
                                    abs(p[1]-turn.turn_soffit_z)<1e-9
                                    for p in polygon))
                # The complete first lower segment, not only its x=0 endpoint,
                # remains an edge of the final closed board polygon.
                a,b=turn.lower_profile[:2]
                edges=tuple(zip(polygon,polygon[1:]+polygon[:1]))
                self.assertTrue(any((u==a and v==b) or (u==b and v==a)
                                    for u,v in edges))
                checked.append((turn.turn_index,side))
        self.assertEqual(checked,[(0,"LEFT"),(0,"RIGHT"),(1,"LEFT"),(1,"RIGHT")])
        self.assertEqual(len(parts.flight_boards),6)
    def test_lower_authority_survives_mirror_reverse_board_modes_and_dimensions(self):
        routes=(U,((0,0),(3,0),(3,-1.8),(0,-1.8)))
        for route in routes:
            for direction in ("FORWARD","REVERSE"):
                for board_mode in ("STEPPED","SLOPED"):
                    for reveal in (20.0,40.0,60.0):
                        for riser_thickness in (8.0,12.0,18.0):
                            _layout,fields,_locals,turns,parts=self.owned(
                                route,direction,board_mode=board_mode,
                                reveal=reveal,riser_thickness=riser_thickness)
                            end_by_flight={t.incoming_flight.canonical_index:t
                                           for t in turns}
                            self.assertEqual(len(parts.flight_boards),6)
                            for turn in turns:
                                for side in ("LEFT","RIGHT"):
                                    polygon=_resolve_multiturn_flight_board_polygon(
                                        turn.outgoing_local,side,fields,
                                        start_turn=turn,end_turn=end_by_flight.get(
                                            turn.outgoing_flight.canonical_index))
                                    self.assertTrue(all(point in polygon
                                                        for point in turn.lower_profile))
                                    self.assertGreaterEqual(len(polygon),4)
    def test_each_landing_board_has_one_owner_and_no_duplicate_geometry(self):
        _layout,_fields,_locals,_turns,parts=self.owned()
        self.assertEqual([x.owner_index for x in parts.landing_boards],[0,1])
        fragments=(parts.flight_underbodies+parts.flight_boards+
                   parts.landing_treads+parts.landing_underbodies+
                   parts.landing_boards)
        signatures=[]
        for owned in fragments:
            signature=tuple(sorted(tuple(round(c,8) for c in v)
                                   for v in owned.fragment.vertices))
            self.assertNotIn(signature,signatures); signatures.append(signature)
    def test_stepped_both_turns_are_single_closed_transitions(self):
        _layout,_fields,_locals,_turns,parts=self.owned(underside="STEPPED_CLOSED")
        self.assertEqual(len(parts.flight_underbodies),3)
        self.assertEqual(len(parts.landing_underbodies),2)
        for owned in parts.flight_underbodies+parts.landing_underbodies:
            self.assert_closed(self,owned.fragment)
    def test_topology_is_finite_nonzero_and_closed(self):
        import math
        for underside in ("STEPPED_CLOSED","SLOPED_CLOSED"):
            *_,parts=self.owned(underside=underside)
            collections=(parts.flight_underbodies,parts.flight_boards,
                         parts.landing_treads,parts.landing_underbodies,
                         parts.landing_boards)
            for owned in sum(collections,()):
                fragment=owned.fragment
                self.assertTrue(all(math.isfinite(c) for v in fragment.vertices for c in v))
                for face in fragment.faces:
                    a,b,c=(fragment.vertices[i] for i in face[:3])
                    ab=tuple(b[i]-a[i] for i in range(3)); ac=tuple(c[i]-a[i] for i in range(3))
                    cross=(ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0])
                    self.assertGreater(sum(v*v for v in cross),1e-18)
                self.assert_closed(self,fragment)
    def test_l_regression_still_uses_compatibility_landing(self):
        l=resolve_multiflight_layout(((0,0),(3,0),(3,3)),"FORWARD",0,2800,16,900,30,12,point_ids=("a","b","c"))
        self.assertEqual(l.landing,l.landings[0])

if __name__ == "__main__": unittest.main()
