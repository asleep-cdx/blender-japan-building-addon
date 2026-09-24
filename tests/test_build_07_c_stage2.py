"""Build 07-C Stage 2 sloped closed-body and side-board contracts."""
from dataclasses import replace
import math, pathlib, sys, types, unittest

ROOT = pathlib.Path(__file__).parents[1]
package = types.ModuleType("japanese_house_modeler")
package.__path__ = [str(ROOT / "japanese_house_modeler")]
sys.modules.setdefault("japanese_house_modeler", package)

from japanese_house_modeler.stair_geometry import prepare_stair_geometry, resolve_stair_layout, validate_mesh_fragments
from japanese_house_modeler.stair_residential import (BEVEL, ROUND, SLOPED,
    SLOPED_CLOSED, STEPPED, STEPPED_CLOSED, ResidentialFields,
    schema_version_after_residential_edit, validate_mode_data)
from japanese_house_modeler.stair_residential_geometry import (C_sloped,
    build_side_board_fragment, build_underbody_fragment,
    prepare_residential_geometry, side_board_lower_profile,
    side_board_profile, sloped_side_board_profile, sloped_underbody_profile,
    stepped_closure_visible_profile)

ARGS = (((0, 0), (3.6, 0)), "FORWARD", 425, 2800, 16, 900, 30, 12)
def layout(direction="FORWARD", path=((0, 0), (3.6, 0)), base=425):
    return resolve_stair_layout(path, direction, base, 2800, 16, 900, 30, 12)
def local_x(l, v):
    return ((v[0]-l.lower_xy[0])*l.axes.forward[0]
            +(v[1]-l.lower_xy[1])*l.axes.forward[1])
def local_y(l, v):
    return ((v[0]-l.lower_xy[0])*l.axes.left[0]
            +(v[1]-l.lower_xy[1])*l.axes.left[1])

class SlopedBodyTests(unittest.TestCase):
    def test_c_sloped_exact_endpoints(self):
        l=layout(); d=.15
        upper_x=l.run_length+l.riser_thickness
        points=C_sloped(l,d)
        self.assertEqual(points[:2],((l.riser_thickness,l.base_z),
                                     (l.going+d,l.base_z)))
        self.assertEqual(points[2][0],upper_x)
        self.assertAlmostEqual(points[2][1],l.base_z
                               +(upper_x-l.going-d)*l.actual_riser/l.going)
    def test_corrected_slope_is_pitch_parallel_and_shallower_than_r1(self):
        l=layout(); d=.15; p=C_sloped(l,d)
        slope=(p[2][1]-p[1][1])/(p[2][0]-p[1][0])
        self.assertAlmostEqual(slope,l.actual_riser/l.going)
        r1_upper=l.base_z+(l.riser_count-1)*l.actual_riser-d
        self.assertLess(p[2][1],r1_upper)
    def test_lower_flat_and_single_slope(self):
        p=C_sloped(layout(),.15); self.assertEqual(p[0][1],p[1][1]); self.assertEqual(len(p),3)
    def test_upper_closure_plane(self):
        l=layout(); p=sloped_underbody_profile(l,ResidentialFields(underside_mode=SLOPED_CLOSED)); self.assertEqual(p.inner[-1][0],p.outer[-1][0])
    def test_profile_bounds_finite_and_positive(self):
        l=layout(); p=sloped_underbody_profile(l,ResidentialFields(underside_mode=SLOPED_CLOSED))
        self.assertTrue(all(math.isfinite(q) for v in p.polygon for q in v)); self.assertGreater(len(p.polygon),3)
        self.assertGreaterEqual(min(z for x,z in p.polygon),l.base_z); self.assertLessEqual(max(x for x,z in p.polygon),l.run_length+l.riser_thickness)
    def test_invalid_positive_run_rejected(self):
        l=layout(path=((0,0),(.2,0)))
        with self.assertRaises(ValueError): C_sloped(l,.2)
    def test_full_width_closed_fragment(self):
        l=layout(); f=build_underbody_fragment(l,ResidentialFields(underside_mode=SLOPED_CLOSED))
        self.assertTrue(validate_mesh_fragments((f,))); self.assertAlmostEqual(max(local_y(l,v) for v in f.vertices)-min(local_y(l,v) for v in f.vertices),l.width)
    def test_board_states_keep_same_body(self):
        bodies=[]
        for left,right in ((1,1),(1,0),(0,1),(0,0)):
            fields=ResidentialFields(underside_mode=SLOPED_CLOSED,left_side_board_enabled=bool(left),right_side_board_enabled=bool(right))
            _l,fs,_m=prepare_residential_geometry(*ARGS,fields=fields)
            self.assertEqual(sum(f.part_type=='SIDE_BOARD' for f in fs),left+right)
            bodies.append(next(f for f in fs if f.part_type=='UNDERBODY'))
        self.assertTrue(all(x==bodies[0] for x in bodies))
    def test_all_body_board_combinations(self):
        for u in (STEPPED_CLOSED,SLOPED_CLOSED):
            for b in (STEPPED,SLOPED):
                prepare_residential_geometry(*ARGS,fields=ResidentialFields(underside_mode=u,side_board_mode=b))
    def test_reverse_oblique_nonzero_base(self):
        for direction in ('FORWARD','REVERSE'):
            fields=ResidentialFields(underside_mode=SLOPED_CLOSED,side_board_mode=SLOPED)
            l,fs,_=prepare_residential_geometry(((1,2),(4,6)),direction,425,2800,16,900,30,12,fields=fields)
            body=next(f for f in fs if f.part_type=='UNDERBODY')
            self.assertAlmostEqual(min(v[2] for v in body.vertices),l.base_z)
            self.assertLessEqual(max(local_x(l,v) for v in body.vertices),l.run_length+l.riser_thickness+1e-12)
    def test_depth_moves_soffit_shell_does_not(self):
        l=layout(); base=ResidentialFields(underside_mode=SLOPED_CLOSED)
        a=sloped_underbody_profile(l,base); b=sloped_underbody_profile(l,replace(base,side_board_band_width_mm=120)); c=sloped_underbody_profile(l,replace(base,underside_thickness_mm=20))
        self.assertNotEqual(a.outer,b.outer); self.assertEqual(a.outer,c.outer); self.assertEqual(a.inner,b.inner)

class SlopedBoardTests(unittest.TestCase):
    def fields(self, **kw): return replace(ResidentialFields(side_board_mode=SLOPED),**kw)
    def test_main_edge_straight_and_not_sawtooth(self):
        l=layout(); p=sloped_side_board_profile(l,self.fields())
        self.assertEqual(len(p.outer),4)
        self.assertEqual(p.outer[0][0],p.outer[1][0])
        self.assertEqual(p.outer[1][1],l.base_z+l.actual_riser+.04)
        self.assertNotEqual(p.outer[1][1],p.outer[2][1])
    def test_lower_end_and_upper_caps(self):
        l=layout(); p=sloped_side_board_profile(l,self.fields())
        self.assertEqual(p.outer[0][1],l.base_z); self.assertEqual(p.lower[0][1],l.base_z)
        self.assertEqual(p.outer[-2][1],p.outer[-1][1]); self.assertEqual(p.outer[-1][0],l.run_length+l.riser_thickness)
        self.assertEqual(p.lower[-1][0],p.outer[-1][0])
    def test_no_diagonal_rear_or_overshoot(self):
        l=layout(); p=sloped_side_board_profile(l,self.fields()); rear=l.run_length+l.riser_thickness
        self.assertEqual(max(x for x,z in p.polygon),rear)
        rear_points=[q for q in p.polygon if q[0]==rear]; self.assertEqual(len(rear_points),2)
    def test_external_left_right_extrusion(self):
        l=layout(); left=build_side_board_fragment(l,'LEFT',self.fields()); right=build_side_board_fragment(l,'RIGHT',self.fields())
        self.assertAlmostEqual(min(local_y(l,v) for v in left.vertices),l.width/2); self.assertAlmostEqual(max(local_y(l,v) for v in left.vertices),l.width/2+.018)
        self.assertAlmostEqual(min(local_y(l,v) for v in right.vertices),-l.width/2-.018); self.assertAlmostEqual(max(local_y(l,v) for v in right.vertices),-l.width/2)
    def test_reveal_controls_visible_projection(self):
        l=layout(); a=sloped_side_board_profile(l,self.fields(side_board_reveal_mm=40)); b=sloped_side_board_profile(l,self.fields(side_board_reveal_mm=60)); self.assertNotEqual(a.outer,b.outer); self.assertEqual(a.lower,b.lower)
    def test_underside_mode_alone_selects_lower_edge_for_both_tops(self):
        l=layout()
        stepped_lower=stepped_closure_visible_profile(l,.15)
        sloped_lower=C_sloped(l,.15)
        for board_mode,builder in ((STEPPED,side_board_profile),
                                   (SLOPED,sloped_side_board_profile)):
            with self.subTest(board_mode=board_mode):
                stepped=builder(l,ResidentialFields(
                    underside_mode=STEPPED_CLOSED,side_board_mode=board_mode))
                sloped=builder(l,ResidentialFields(
                    underside_mode=SLOPED_CLOSED,side_board_mode=board_mode))
                self.assertEqual(stepped.lower,stepped_lower)
                self.assertEqual(sloped.lower,sloped_lower)
                self.assertEqual(stepped.lower,side_board_lower_profile(
                    l,ResidentialFields(underside_mode=STEPPED_CLOSED)))
                self.assertEqual(sloped.lower,side_board_lower_profile(
                    l,ResidentialFields(underside_mode=SLOPED_CLOSED)))
                self.assertNotEqual(stepped.lower,sloped.lower)
    def test_stepped_top_is_unchanged_when_lower_family_changes(self):
        l=layout()
        a=side_board_profile(l,ResidentialFields())
        b=side_board_profile(l,ResidentialFields(underside_mode=SLOPED_CLOSED))
        self.assertEqual(a.outer,b.outer)
        self.assertNotEqual(a.lower,b.lower)
    def test_sloped_top_is_unchanged_when_lower_family_changes(self):
        l=layout()
        a=sloped_side_board_profile(l,self.fields())
        b=sloped_side_board_profile(l,self.fields(underside_mode=SLOPED_CLOSED))
        self.assertEqual(a.outer,b.outer)
        self.assertNotEqual(a.lower,b.lower)

class MigrationAndRegressionTests(unittest.TestCase):
    def test_stage2_migration_triggers(self):
        before=ResidentialFields()
        for after in (replace(before,underside_mode=SLOPED_CLOSED),replace(before,side_board_mode=SLOPED),replace(before,side_board_band_width_mm=120)):
            self.assertEqual(schema_version_after_residential_edit(2,before,after),3)
    def test_legacy_and_noop_stay_schema_two(self):
        before=ResidentialFields(); self.assertEqual(schema_version_after_residential_edit(2,before,replace(before)),2); self.assertEqual(schema_version_after_residential_edit(2,before,replace(before,side_board_thickness_mm=22)),2)
    def test_stage3_geometry_rejected(self):
        for value in (ResidentialFields(tread_front_overhang_mm=5),ResidentialFields(tread_front_edge_mode=BEVEL),ResidentialFields(tread_front_edge_mode=ROUND)):
            with self.assertRaises(ValueError): validate_mode_data('STANDARD_RESIDENTIAL',3,value)
    def test_default_and_basic_counts(self):
        residential=prepare_residential_geometry(*ARGS)[2]; basic=prepare_stair_geometry(*ARGS)[2]
        self.assertEqual((len(residential.vertices),len(residential.faces)),(620,732)); self.assertEqual((len(basic.vertices),len(basic.faces)),(248,186))
    def test_material_roles(self):
        mesh=prepare_residential_geometry(*ARGS,fields=ResidentialFields(underside_mode=SLOPED_CLOSED,side_board_mode=SLOPED))[2]
        self.assertIn('UNDERSIDE',mesh.face_roles); self.assertIn('SIDE_BOARD',mesh.face_roles)

if __name__ == '__main__': unittest.main()
