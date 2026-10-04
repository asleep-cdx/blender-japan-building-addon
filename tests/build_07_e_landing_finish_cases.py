"""Build 07-E generalized non-right Landing finish authority regressions."""
import math
import pathlib
import sys
import types
import unittest
from dataclasses import replace

ROOT=pathlib.Path(__file__).parents[1]
package=sys.modules.get("japanese_house_modeler")
if package is None:
    package=types.ModuleType("japanese_house_modeler")
    package.__path__=[str(ROOT/"japanese_house_modeler")]
    sys.modules["japanese_house_modeler"]=package

from japanese_house_modeler.stair_geometry import _signed_volume, validate_mesh_fragments
from japanese_house_modeler.stair_landing_finish import (
    build_generalized_landing_body, build_generalized_landing_side_board,
    prepare_generalized_landing_finish, resolve_generalized_landing_finish,
)
from japanese_house_modeler.stair_body_interfaces import (
    ResidentialBodyComponent, _canonical_values, _snap, body_port,
    join_body_component_surfaces, port_surface_ownership,
    resolve_body_interface,
)
from japanese_house_modeler.stair_geometry import MeshFragment
from japanese_house_modeler.stair_geometry import resolve_stair_layout, validate_simple_polygon
from japanese_house_modeler.stair_residential import ResidentialFields
from japanese_house_modeler.stair_residential_geometry import (
    sloped_underbody_profile, stepped_underbody_profile,
)
from japanese_house_modeler.stair_turn import EPS_LENGTH
from japanese_house_modeler.stair_turn import (
    TurnSpec, polygon_area, resolve_winder_layout, TURN_LANDING, WINDER_NONE,
)


def fixture(degrees=63,width=750,mirror=False,direction="FORWARD"):
    angle=math.radians(degrees); sign=1 if mirror else -1
    points=((0,0),(0,2.2),
            (sign*2.2*math.sin(angle),2.2+2.2*math.cos(angle)))
    ids=("p0","turn","p2")
    spec=(TurnSpec("turn",TURN_LANDING,WINDER_NONE),)
    layout=resolve_winder_layout(points,direction,0,2800,16,width,30,20,
                                  point_ids=ids,turn_specs=spec)
    return layout.turns[0]


def authority(frame,width=.75,mode="SLOPED_CLOSED",board=.018,
              direction="FORWARD"):
    return resolve_generalized_landing_finish(
        frame,width,1.4,0,.03,.02,.15,.0095,board,.04,mode,direction)

def distance_line(point,a,b):
    return abs((b[0]-a[0])*(a[1]-point[1])
               -(a[0]-point[0])*(b[1]-a[1]))/math.dist(a,b)

def on_segment(point,a,b,eps=1e-9):
    return (distance_line(point,a,b)<=eps
            and min(a[0],b[0])-eps<=point[0]<=max(a[0],b[0])+eps
            and min(a[1],b[1])-eps<=point[1]<=max(a[1],b[1])+eps)

def points(polygon):
    return {(round(p[0],9),round(p[1],9)) for p in polygon}

def inside(point,polygon,eps=1e-9):
    values=[]
    for a,b in zip(polygon,polygon[1:]+polygon[:1]):
        values.append((b[0]-a[0])*(point[1]-a[1])
                      -(b[1]-a[1])*(point[0]-a[0]))
    return all(v>=-eps for v in values) or all(v<=eps for v in values)


class GeneralizedLandingFinishTests(unittest.TestCase):
    def test_plan_offsets_angles_mirrors_and_widths(self):
        for degrees in (47,63,82):
            for mirror in (False,True):
                for width in (.9,.75,.65):
                    a=authority(fixture(degrees,width*1000,mirror),width)
                    self.assertEqual(len(a.footprint),4)
                    self.assertGreater(math.dist(a.a_entry,a.o_inner),0)
                    self.assertGreater(math.dist(a.a_exit,a.o_inner),0)
                    self.assertEqual(a,authority(
                        fixture(degrees,width*1000,mirror),width))
                    i,e,o,x=a.entry_interface[0],a.entry_interface[1],a.outer_chain[1],a.exit_interface[1]
                    self.assertTrue(on_segment(a.a_entry,i,e))
                    self.assertTrue(on_segment(a.a_exit,i,x))
                    self.assertAlmostEqual(distance_line(a.a_entry,e,o),.02)
                    self.assertAlmostEqual(distance_line(a.o_inner,e,o),.02)
                    self.assertAlmostEqual(distance_line(a.a_exit,o,x),.02)
                    self.assertAlmostEqual(distance_line(a.o_inner,o,x),.02)
                    self.assertAlmostEqual(polygon_area(a.cavity)
                                           +polygon_area(a.skirt),
                                           polygon_area(a.footprint))
                    self.assertIsNotNone(a.b_entry)
                    # Outward offsets meet the supporting interface lines just
                    # beyond E_in/E_out; collinearity, not segment containment,
                    # is the constant-thickness miter authority.
                    self.assertAlmostEqual(distance_line(a.b_entry,i,e),0)
                    self.assertAlmostEqual(distance_line(a.b_exit,i,x),0)
                    self.assertAlmostEqual(distance_line(a.b_entry,e,o),.018)
                    self.assertAlmostEqual(distance_line(a.o_outer,e,o),.018)
                    self.assertAlmostEqual(distance_line(a.b_exit,o,x),.018)
                    self.assertAlmostEqual(distance_line(a.o_outer,o,x),.018)
                    self.assertTrue(validate_mesh_fragments(
                        build_generalized_landing_side_board(a,True,.04)))

    def test_63_stepped_and_sloped_closed_bodies(self):
        for mode in ("STEPPED_CLOSED","SLOPED_CLOSED"):
            a=authority(fixture(),mode=mode)
            parts=build_generalized_landing_body(a,mode)
            self.assertTrue(validate_mesh_fragments(parts))
            self.assertTrue(all(p.part_type=="UNDERBODY" for p in parts))
            self.assertEqual(min(v[2] for p in parts for v in p.vertices),
                             a.z_soffit)
            self.assertGreater(a.z_soffit,0)
            self.assertLess(max(v[2] for p in parts for v in p.vertices),
                            a.z_top)
            volume=sum(_signed_volume(p.vertices,p.faces) for p in parts)
            expected=(polygon_area(a.footprint)*(
                (a.z_contact-a.z_soffit) if mode=="STEPPED_CLOSED"
                else (a.z_slab_top-a.z_soffit))
                +(0 if mode=="STEPPED_CLOSED" else polygon_area(a.skirt)*(
                    a.z_contact-a.z_slab_top)))
            self.assertAlmostEqual(volume,expected,places=9)
            self.assertTrue(all(inside(v[:2],a.footprint)
                                for p in parts for v in p.vertices))
            self.assertEqual(parts,build_generalized_landing_body(a,mode))

    def test_ports_retain_semantic_breakpoints(self):
        a=authority(fixture())
        self.assertEqual(a.entry_port.stations,(a.entry_interface[0],
                                                a.a_entry,
                                                a.entry_interface[1]))
        self.assertEqual(a.exit_port.stations,(a.exit_interface[0],
                                               a.a_exit,
                                               a.exit_interface[1]))
        self.assertEqual(a.entry_port.soffit_edge[0][2],a.z_soffit)
        self.assertEqual(a.exit_port.contact_edge[-1][2],a.z_contact)
        for port in (a.entry_port,a.exit_port):
            self.assertGreater(polygon_area(port.profile_qz),0)
            self.assertEqual(len(port.profile_qz),len(port.profile_xyz))
            self.assertEqual(tuple(p[2] for p in port.profile_xyz),
                             tuple(p[1] for p in port.profile_qz))
        self.assertEqual(len(a.entry_port.profile_qz),6)
        stepped=authority(fixture(),mode="STEPPED_CLOSED")
        self.assertEqual(len(stepped.entry_port.profile_qz),4)

    def test_board_miter_constant_distance_and_role(self):
        a=authority(fixture())
        boards=build_generalized_landing_side_board(a,True,.04)
        self.assertTrue(validate_mesh_fragments(boards))
        self.assertEqual(boards[0].part_type,"SIDE_BOARD")
        self.assertEqual(min(v[2] for v in boards[0].vertices),a.z_soffit)
        self.assertEqual(max(v[2] for v in boards[0].vertices),a.z_top+.04)
        self.assertEqual(len(a.board_footprint),6)

    def test_reverse_recomputes_ports_without_changing_frame_identity(self):
        frame=fixture(direction="FORWARD"); snapshot=frame
        forward=authority(frame,direction="FORWARD")
        reverse=authority(frame,direction="REVERSE")
        self.assertEqual(forward.entry_interface,reverse.exit_interface)
        self.assertEqual(forward.exit_interface,reverse.entry_interface)
        self.assertEqual(set(forward.footprint),set(reverse.footprint))
        self.assertNotEqual(forward.outside_side,reverse.outside_side)
        self.assertIn(reverse.a_entry,reverse.entry_port.stations)
        self.assertIn(reverse.a_exit,reverse.exit_port.stations)
        self.assertEqual(frame,snapshot)

    def test_exact90_dispatches_only_to_oracle(self):
        marker=object(); calls=[]
        result=prepare_generalized_landing_finish(
            fixture(90),exact90_oracle=lambda:(calls.append(True),marker)[1])
        self.assertIs(result,marker)
        self.assertEqual(calls,[True])

    def test_exact90_semantic_footprints_reduce_to_square_oracle(self):
        a=authority(fixture(90)); width=.75; r=.02; s=.018
        self.assertAlmostEqual(polygon_area(a.footprint),width*width)
        self.assertAlmostEqual(polygon_area(a.cavity),(width-r)**2)
        self.assertAlmostEqual(polygon_area(a.skirt),
                               width*width-(width-r)**2)
        self.assertAlmostEqual(polygon_area(a.board_footprint),
                               (width+s)**2-width*width)
        i=a.entry_interface[0]
        u=tuple((a.entry_interface[1][j]-i[j])/width for j in range(2))
        v=tuple((a.exit_interface[1][j]-i[j])/width for j in range(2))
        def p(x,y): return (i[0]+u[0]*x+v[0]*y,
                            i[1]+u[1]*x+v[1]*y)
        self.assertEqual(points(a.footprint),points((p(0,0),p(width,0),
                                                     p(width,width),p(0,width))))
        self.assertEqual(points(a.cavity),points((p(0,0),p(width-r,0),
                                                  p(width-r,width-r),p(0,width-r))))
        self.assertEqual(points(a.skirt),points((p(width,0),p(width,width),
                                                 p(0,width),p(0,width-r),
                                                 p(width-r,width-r),p(width-r,0))))
        self.assertEqual(points(a.board_footprint),points((p(width+s,0),
            p(width+s,width+s),p(0,width+s),p(0,width),p(width,width),p(width,0))))

    def test_mirror_is_geometric_reflection(self):
        for degrees in (47,63,82):
            a=authority(fixture(degrees,750,False))
            b=authority(fixture(degrees,750,True))
            reflect=lambda polygon:{(round(-p[0],9),round(p[1],9)) for p in polygon}
            for left,right in ((a.footprint,b.footprint),(a.cavity,b.cavity),
                               (a.skirt,b.skirt),(a.board_footprint,b.board_footprint)):
                self.assertEqual(reflect(left),points(right))
            self.assertEqual((a.z_top,a.z_contact,a.z_soffit,a.z_slab_top),
                             (b.z_top,b.z_contact,b.z_soffit,b.z_slab_top))

    def test_invalid_authority_inputs(self):
        frame=fixture()
        base=dict(width=.75,z_top=1.4,base_z=0,tread_thickness=.03,
                  riser_thickness=.02,body_depth=.15,
                  underside_thickness=.0095,board_thickness=.018,
                  board_reveal=.04,underside_mode="SLOPED_CLOSED")
        for key,value in (("width",0),("tread_thickness",-1),
                          ("riser_thickness",float("nan")),("body_depth",0),
                          ("underside_thickness",0),("board_thickness",-.1),
                          ("underside_mode","UNKNOWN")):
            values=dict(base);values[key]=value
            with self.subTest(key=key):
                with self.assertRaisesRegex(ValueError,"GEOMETRY_INVALID"):
                    resolve_generalized_landing_finish(frame,**values)

    def test_candidate_resolution_has_no_mutation(self):
        frame=fixture(); snapshot=frame
        a=authority(frame)
        _parts=build_generalized_landing_body(a,"SLOPED_CLOSED")
        _boards=build_generalized_landing_side_board(a,True,.04)
        self.assertEqual(frame,snapshot)

    def test_component_interface_region_algebra(self):
        segment=((0,0),(1,0))
        source_port=body_port("EXIT",segment,
            ((0,0),(1,0),(1,1),(0,1)))
        destination_port=body_port("ENTRY",segment,
            ((0,0),(1,0),(1,2),(.5,2),(.5,1),(0,1)))
        source=ResidentialBodyComponent(("WINDER",0),"WINDER",0,None,(),
                                        None,source_port)
        destination=ResidentialBodyComponent(("STRAIGHT",1),
            "STRAIGHT_FLIGHT",1,None,(),destination_port,None)
        interface=resolve_body_interface(source,destination)
        self.assertEqual(interface.closure_owner,destination.identity)
        self.assertEqual(interface.overlap_cells,((0.0,.5,0.0,1.0),
                                                   (.5,1.0,0.0,1.0)))
        self.assertEqual(interface.transition_cells,((.5,1.0,1.0,2.0),))
        self.assertEqual(interface,
                         resolve_body_interface(source,destination))

    def test_matching_component_profiles_have_no_transition(self):
        port=body_port("PORT",((0,0),(1,0)),
                       ((0,0),(1,0),(1,1),(0,1)))
        source=ResidentialBodyComponent(("LANDING",0),"LANDING",0,None,(),
                                        None,port)
        destination=ResidentialBodyComponent(("WINDER",1),"WINDER",1,None,(),
                                             port,None)
        interface=resolve_body_interface(source,destination)
        self.assertFalse(interface.transition_cells)
        self.assertTrue(interface.overlap_cells)
        self.assertIsNone(interface.closure_owner)

    def test_body_interface_authority_matrix(self):
        segment=((2.0,3.0),(3.0,3.0))
        def component(identity, profile, *, entry=False, reverse=False,
                      breaks=()):
            edge=tuple(reversed(segment)) if reverse else segment
            width=1.0
            local=tuple((width-q,z) for q,z in profile) if reverse else profile
            local_breaks=tuple((width-q,z) for q,z in breaks) if reverse else breaks
            port=body_port(identity[0],edge,local,local_breaks)
            return ResidentialBodyComponent(identity,"WINDER",identity[1],None,(),
                port if entry else None,None if entry else port)
        rectangle=((0,0),(1,0),(1,1),(0,1))
        cases=(
            (rectangle,rectangle),
            (((0,0),(1,0),(1,.5),(0,.5)),rectangle),
            (rectangle,((0,0),(1,0),(1,.5),(0,.5))),
            (((0,0),(1,0),(1,2),(.5,2),(.5,1),(0,1)),rectangle),
            (((0,0),(1,0),(1,1),(0,1)),((0,2),(1,2),(1,3),(0,3))),
        )
        def area(cells): return sum((b-a)*(d-c) for a,b,c,d in cells)
        def polygon_area(poly):
            return abs(sum(a[0]*b[1]-a[1]*b[0]
                           for a,b in zip(poly,poly[1:]+poly[:1])))/2
        for index,(left,right) in enumerate(cases):
            source=component(("S",index),left)
            destination=component(("D",index),right,entry=True)
            result=resolve_body_interface(source,destination)
            with self.subTest(index=index):
                self.assertAlmostEqual(polygon_area(left),
                    area(result.overlap_cells)+area(result.source_only_cells))
                self.assertAlmostEqual(polygon_area(right),
                    area(result.overlap_cells)+area(result.destination_only_cells))
                self.assertAlmostEqual(area(result.transition_cells),
                    area(result.source_only_cells)+area(result.destination_only_cells))
                self.assertTrue(all((b-a)*(d-c)>1e-12
                                    for a,b,c,d in result.transition_cells))
                self.assertEqual(result,resolve_body_interface(source,destination))
        self.assertFalse(resolve_body_interface(
            component(("S",9),cases[-1][0]),
            component(("D",9),cases[-1][1],entry=True)).overlap_cells)

    def test_reversed_port_and_eps_values_normalize(self):
        profile=((0,0),(1,0),(1,1),(0,1))
        source=ResidentialBodyComponent(("S",0),"WINDER",0,None,(),None,
            body_port("EXIT",((0,0),(1,0)),profile,((.25,.5),)))
        direct=ResidentialBodyComponent(("D",0),"LANDING",1,None,(),
            body_port("ENTRY",((0,0),(1,0)),profile,((.25,.5),)),None)
        reverse=ResidentialBodyComponent(("D",0),"LANDING",1,None,(),
            body_port("ENTRY",((1,0),(0,0)),
                      tuple((1-q,z) for q,z in profile),((.75,.5),),
                      canonical_segment=((0,0),(1,0))),None)
        a=resolve_body_interface(source,direct)
        b=resolve_body_interface(source,reverse)
        for name in ("frame","q_stations","z_stations","grid_stations",
                     "authority_stations","semantic_stations","overlap_cells",
                     "source_only_cells","destination_only_cells",
                     "transition_cells","closure_owner"):
            self.assertEqual(getattr(a,name),getattr(b,name))
        self.assertIn(.25,a.q_stations)
        self.assertIn(.5,a.z_stations)
        station=next(s for s in a.stations if s.q==.25 and s.z==.5)
        self.assertEqual(station.xyz,(.25,0.0,.5))
        perturbed=ResidentialBodyComponent(("D",0),"LANDING",1,None,(),
            body_port("ENTRY",((0,0),(1+1e-10,0)),
                ((0,1e-10),(1+1e-10,1e-10),(1+1e-10,1),(0,1))),None)
        c=resolve_body_interface(source,perturbed,((0,0),(1,0)))
        self.assertEqual(c.q_stations,(0.0,.25,1.0))
        self.assertEqual(c.z_stations,(0.0,.5,1.0))
        self.assertFalse(c.transition_cells)

    def test_diagonal_body_port_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"non-rectilinear"):
            body_port("INVALID",((0,0),(1,0)),
                      ((0,0),(1,0),(1,1),(.5,2),(0,1)))

    def test_canonical_q_is_independent_of_both_local_orders(self):
        canonical=((4.0,2.0),(4.0,3.0))
        profile=((0,0),(1,0),(1,1),(.4,1),(.4,.6),(0,.6))
        def port(key, reverse):
            segment=tuple(reversed(canonical)) if reverse else canonical
            local=tuple((1-q,z) for q,z in profile) if reverse else profile
            breaks=((.7,.8,"NAMED"),) if not reverse else ((.3,.8,"NAMED"),)
            return body_port(key,segment,local,breaks,canonical_segment=canonical)
        results=[]
        for source_reverse in (False,True):
            for destination_reverse in (False,True):
                source=ResidentialBodyComponent(("S",0),"WINDER",0,None,(),None,
                                                port("P",source_reverse))
                destination=ResidentialBodyComponent(("D",1),"LANDING",1,None,(),
                    port("P",destination_reverse),None)
                results.append(resolve_body_interface(source,destination,
                                                       canonical))
        baseline=results[0]
        for result in results[1:]:
            for name in ("frame","q_stations","z_stations","grid_stations",
                         "authority_stations","semantic_stations","overlap_cells",
                         "source_only_cells","destination_only_cells",
                         "transition_cells","closure_owner"):
                self.assertEqual(getattr(baseline,name),getattr(result,name))
            self.assertEqual(result.source_port.profile_qz,profile)
            self.assertEqual(result.destination_port.profile_qz,profile)

    def test_pair_provenance_does_not_tag_cartesian_cross_points(self):
        profile=((0,0),(1,0),(1,1),(0,1))
        breaks=((.25,.50,"A"),(.75,.80,"B"))
        port=body_port("P",((0,0),(1,0)),profile,breaks)
        source=ResidentialBodyComponent(("S",0),"WINDER",0,None,(),None,port)
        destination=ResidentialBodyComponent(("D",1),"LANDING",1,None,(),port,None)
        result=resolve_body_interface(source,destination)
        semantic={(station.q,station.z) for station in result.semantic_stations}
        self.assertEqual(semantic,{(.25,.5),(.75,.8)})
        grid={(station.q,station.z) for station in result.grid_stations}
        self.assertTrue({(.25,.8),(.75,.5)} <= grid)
        self.assertFalse({(.25,.8),(.75,.5)} & semantic)

    def test_semantic_eps_precedence_and_reverse_traversal(self):
        profile=((0,0),(1,0),(1,1),(.25,1),(.25,.5),(0,.5))
        shifted=(.25+1e-10,.5+1e-10,"JOINT")
        a=body_port("A",((0,0),(1,0)),profile,(shifted,))
        b=body_port("B",((0,0),(1,0)),profile,((.25,.5,"JOINT"),))
        left=ResidentialBodyComponent(("A",0),"WINDER",0,None,(),None,a)
        right=ResidentialBodyComponent(("B",1),"LANDING",1,None,(),b,None)
        forward=resolve_body_interface(left,right)
        reverse=resolve_body_interface(
            ResidentialBodyComponent(("B",1),"LANDING",0,None,(),None,b),
            ResidentialBodyComponent(("A",0),"WINDER",1,None,(),a,None))
        self.assertEqual(forward.q_stations,reverse.q_stations)
        self.assertEqual(forward.z_stations,reverse.z_stations)
        self.assertEqual(tuple(s.xyz for s in forward.semantic_stations),
                         tuple(s.xyz for s in reverse.semantic_stations))
        self.assertIn((.25,.5),{(s.q,s.z) for s in forward.semantic_stations})
        for dq,dz in ((1e-10,0),(0,1e-10),(1e-10,1e-10)):
            named=(.25+dq,.5+dz,"ONLY_NAMED")
            named_port=body_port("N",((0,0),(1,0)),profile,(named,))
            plain_port=body_port("P",((0,0),(1,0)),profile)
            result=resolve_body_interface(
                ResidentialBodyComponent(("N",0),"WINDER",0,None,(),None,
                                         named_port),
                ResidentialBodyComponent(("P",1),"LANDING",1,None,(),
                                         plain_port,None))
            station=next(s for s in result.semantic_stations
                         if any("ONLY_NAMED" in tag for tag in s.tags))
            self.assertEqual((station.q,station.z),(.25+dq,.5+dz))
            self.assertEqual(station.xyz,(.25+dq,0.0,.5+dz))

    def test_body_port_rejects_non_finite_authority(self):
        profile=((0,0),(1,0),(1,1),(0,1))
        cases=(
            (((float("nan"),0),(1,0)),profile,()),
            (((0,0),(1,float("inf"))),profile,()),
            (((0,0),(1,0)),profile,((float("nan"),.5),)),
            (((0,0),(1,0)),profile,((.5,float("nan")),)),
            (((0,0),(1,0)),profile,((.5,float("inf")),)),
        )
        for segment,shape,breaks in cases:
            with self.subTest(segment=segment,breaks=breaks):
                with self.assertRaisesRegex(ValueError,"GEOMETRY_INVALID"):
                    body_port("INVALID",segment,shape,breaks)

    def test_eps_clusters_are_bounded_not_transitively_chained(self):
        eps=EPS_LENGTH
        cases=(
            ((0,1),(.9*eps,1),(1.8*eps,1)),
            ((0,0),(.9*eps,1),(1.8*eps,1)),
            ((0,1),(.9*eps,0),(1.8*eps,1)),
        )
        for values in cases:
            with self.subTest(values=values):
                stations=_canonical_values(values)
                self.assertGreaterEqual(len(stations),2)
                self.assertEqual(stations,_canonical_values(tuple(reversed(values))))
                for value,_priority in values:
                    self.assertLessEqual(abs(value-_snap(value,stations)),eps)
        semantic_first=_canonical_values(cases[1])
        self.assertEqual(semantic_first[0],0.0)
        self.assertNotEqual(semantic_first[-1],0.0)
        semantic_middle=_canonical_values(cases[2])
        self.assertEqual(semantic_middle[0],.9*eps)

    def test_eps_chain_is_bounded_for_q_z_and_role_reversal(self):
        eps=EPS_LENGTH
        # The scalar authority is shared by q and z; exercise both axes through
        # complete ports and exchange source/destination ownership.
        profile=((0,0),(1,0),(1,1),(0,1))
        a=body_port("A",((0,0),(1,0)),profile,
                    ((.9*eps,.9*eps,"MIDDLE"),))
        b=body_port("B",((0,0),(1,0)),profile,
                    ((1.8*eps,1.8*eps,"HIGH"),))
        forward=resolve_body_interface(
            ResidentialBodyComponent(("A",0),"WINDER",0,None,(),None,a),
            ResidentialBodyComponent(("B",1),"LANDING",1,None,(),b,None))
        reverse=resolve_body_interface(
            ResidentialBodyComponent(("B",1),"LANDING",0,None,(),None,b),
            ResidentialBodyComponent(("A",0),"WINDER",1,None,(),a,None))
        self.assertEqual(forward.q_stations,reverse.q_stations)
        self.assertEqual(forward.z_stations,reverse.z_stations)
        self.assertGreaterEqual(len([q for q in forward.q_stations
                                    if q <= 2*eps]),2)
        self.assertGreaterEqual(len([z for z in forward.z_stations
                                    if z <= 2*eps]),2)
        for value in (0,.9*eps,1.8*eps):
            self.assertLessEqual(abs(value-_snap(value,forward.q_stations)),eps)
            self.assertLessEqual(abs(value-_snap(value,forward.z_stations)),eps)

    def test_snap_failure_is_geometry_invalid(self):
        with self.assertRaisesRegex(ValueError,"GEOMETRY_INVALID"):
            _snap(2.0,(0.0,1.0))

    def test_production_surface_join_consumes_body_interface(self):
        faces=((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),
               (2,3,7,6),(3,0,4,7))
        def box(x0,x1,z1,ordinal):
            vertices=((x0,0,0),(x1,0,0),(x1,1,0),(x0,1,0),
                      (x0,0,z1),(x1,0,z1),(x1,1,z1),(x0,1,z1))
            return MeshFragment("UNDERBODY",ordinal,vertices,faces)
        seam=((0,0),(0,1))
        low=body_port("EXIT",seam,((0,0),(1,0),(1,1),(0,1)))
        high=body_port("ENTRY",seam,((0,0),(1,0),(1,2),(0,2)))
        source=ResidentialBodyComponent(("STRAIGHT",0),"STRAIGHT_FLIGHT",0,
                                        None,(box(-1,0,1,1),),None,low)
        destination=ResidentialBodyComponent(("WINDER",0),"WINDER",1,None,
                                             (box(0,1,2,2),),high,None)
        self.assertTrue(port_surface_ownership(source,"EXIT").face_indices)
        self.assertTrue(port_surface_ownership(destination,"ENTRY").face_indices)
        source=replace(source,exit_surface_ownership=
                       port_surface_ownership(source,"EXIT"))
        destination=replace(destination,entry_surface_ownership=
                            port_surface_ownership(destination,"ENTRY"))
        joined=join_body_component_surfaces((source,destination),(seam,))
        self.assertTrue(validate_mesh_fragments((joined.fragment,)))
        interface=joined.interfaces[0]
        self.assertEqual(interface.closure_owner,destination.identity)
        self.assertAlmostEqual(sum((q1-q0)*(z1-z0)
            for q0,q1,z0,z1 in interface.transition_cells),1.0)
        self.assertEqual(joined.transition_owners,(destination.identity,))
        # No positive-area cap remains over the common overlap z=[0,1].
        coplanar=[face for face in joined.fragment.faces
                  if all(abs(joined.fragment.vertices[i][0])<1e-12 for i in face)]
        self.assertEqual(len(coplanar),1)

    def test_authorized_entry_prepend_contract_is_non_simple_at_native_tip(self):
        """Document the production blocker without weakening validation."""
        layout=resolve_stair_layout(((0,0),(3,0)),"FORWARD",0,2800,16,
                                    750,30,20)
        for resolver in (stepped_underbody_profile,sloped_underbody_profile):
            native=resolver(layout,ResidentialFields())
            self.assertEqual(native.inner[0],native.outer[0])
            self.assertEqual(native.inner[0],
                             (layout.riser_thickness,layout.base_z))
            inner=((0.0,layout.base_z),)+native.inner
            outer=((0.0,layout.base_z-.05),)+native.outer
            with self.subTest(resolver=resolver.__name__):
                with self.assertRaises(ValueError):
                    validate_simple_polygon(inner+tuple(reversed(outer)))



if __name__=="__main__": unittest.main()
