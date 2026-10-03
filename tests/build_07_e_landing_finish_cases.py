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

from japanese_house_modeler.stair_geometry import validate_mesh_fragments
from japanese_house_modeler.stair_landing_finish import (
    build_generalized_landing_body, build_generalized_landing_side_board,
    prepare_generalized_landing_finish, resolve_generalized_landing_finish,
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

    def test_board_miter_constant_distance_and_role(self):
        a=authority(fixture())
        boards=build_generalized_landing_side_board(a,True,.04)
        self.assertTrue(validate_mesh_fragments(boards))
        self.assertEqual(boards[0].part_type,"SIDE_BOARD")
        self.assertEqual(min(v[2] for v in boards[0].vertices),a.z_soffit)
        self.assertEqual(max(v[2] for v in boards[0].vertices),a.z_top+.04)
        self.assertEqual(len(a.board_footprint),6)

    def test_reverse_recomputes_ports_without_changing_frame_identity(self):
        frame=fixture(direction="FORWARD")
        forward=authority(frame,direction="FORWARD")
        reverse=authority(frame,direction="REVERSE")
        self.assertNotEqual(forward.entry_interface,reverse.entry_interface)
        self.assertEqual(set(forward.footprint),set(reverse.footprint))

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

    def test_candidate_resolution_has_no_mutation(self):
        frame=fixture(); snapshot=frame
        a=authority(frame)
        _parts=build_generalized_landing_body(a,"SLOPED_CLOSED")
        _boards=build_generalized_landing_side_board(a,True,.04)
        self.assertEqual(frame,snapshot)


if __name__=="__main__": unittest.main()
