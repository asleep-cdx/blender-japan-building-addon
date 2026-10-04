"""Build 07-E generalized non-right Landing finish authority regressions."""
import math
import pathlib
import sys
import types
import unittest

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
    ResidentialBodyComponent, body_port, resolve_body_interface,
)
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


if __name__=="__main__": unittest.main()
