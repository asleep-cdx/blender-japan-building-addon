"""Build 07-B Stage 3 side-board, material, and activation contracts."""
from dataclasses import replace
import pathlib, sys, types, unittest
ROOT=pathlib.Path(__file__).parents[1]
pkg=types.ModuleType('japanese_house_modeler'); pkg.__path__=[str(ROOT/'japanese_house_modeler')]
sys.modules.setdefault('japanese_house_modeler',pkg)
from japanese_house_modeler.stair_geometry import (prepare_stair_geometry,
    resolve_stair_layout, validate_mesh_fragments)
from japanese_house_modeler.stair_residential import (MATERIAL_ROLES, ResidentialFields,
    assemble_material_slot_plan, resolve_material_roles)
from japanese_house_modeler.stair_residential_geometry import (build_side_board_fragment,
    prepare_residential_geometry, prepare_stage2_residential_geometry,
    side_board_profile, side_board_reference_profile,
    stepped_underbody_profile)
from japanese_house_modeler.stair_state import operation_allowed

def layout(direction='FORWARD', path=((0,0),(3.6,0)), base=425):
 return resolve_stair_layout(path,direction,base,2800,16,900,30,12)
def local_y(l,v): return (v[0]-l.lower_xy[0])*l.axes.left[0]+(v[1]-l.lower_xy[1])*l.axes.left[1]

class SideBoardTests(unittest.TestCase):
 def test_exact_reference(self):
  l=layout(); p=side_board_reference_profile(l)
  self.assertEqual(p[:4],((0,l.base_z),(0,l.base_z+l.actual_riser),(l.going,l.base_z+l.actual_riser),(l.going,l.base_z+2*l.actual_riser)))
  self.assertEqual(p[-1],(l.run_length,l.upper_arrival_z))
 def test_translated_band_uses_correct_exterior_direction(self):
  l=layout(); p=side_board_profile(l)
  self.assertEqual(p.outer[0],(-.04,l.base_z))
  self.assertEqual(p.outer[1],(-.04,l.base_z+l.actual_riser+.04))
  self.assertEqual(p.outer[-1],(l.run_length-.04,l.upper_arrival_z))
  self.assertNotIn((.04,l.base_z),p.outer)
  for reference,outer in zip(p.reference[1:-1],p.outer[1:-1]):
   self.assertAlmostEqual(outer[0],reference[0]-.04)
   self.assertAlmostEqual(outer[1],reference[1]+.04)
 def test_clean_lower_and_upper_terminations(self):
  l=layout(); p=side_board_profile(l)
  self.assertEqual([q for q in p.polygon if q[1]==l.base_z],[(0,l.base_z),(-.04,l.base_z)])
  self.assertEqual(min(z for x,z in p.polygon),l.base_z)
  self.assertEqual([q for q in p.polygon if q[1]==l.upper_arrival_z],[(l.run_length,l.upper_arrival_z),(l.run_length-.04,l.upper_arrival_z)])
  self.assertEqual(max(x for x,z in p.polygon),l.run_length)
 def test_four_combinations_and_body_unchanged(self):
  bodies=[]
  for left,right in ((1,1),(1,0),(0,1),(0,0)):
   l,fragments,_=prepare_residential_geometry(((0,0),(3.6,0)),'FORWARD',425,2800,16,900,30,12,fields=ResidentialFields(left_side_board_enabled=bool(left),right_side_board_enabled=bool(right)))
   self.assertEqual(sum(f.part_type=='SIDE_BOARD' for f in fragments),left+right)
   bodies.append(next(f for f in fragments if f.part_type=='UNDERBODY'))
  self.assertTrue(all(body==bodies[0] for body in bodies))
 def test_boards_off_exactly_matches_accepted_stage2_body(self):
  fields=ResidentialFields(left_side_board_enabled=False,right_side_board_enabled=False)
  args=(((0,0),(3.6,0)),'FORWARD',425,2800,16,900,30,12)
  self.assertEqual(prepare_residential_geometry(*args,fields=fields),
                   prepare_stage2_residential_geometry(*args,fields=fields))
 def test_width_and_one_side_envelopes(self):
  l=layout(); left=build_side_board_fragment(l,'LEFT'); right=build_side_board_fragment(l,'RIGHT')
  self.assertAlmostEqual(min(local_y(l,v) for v in left.vertices),.432)
  self.assertAlmostEqual(max(local_y(l,v) for v in left.vertices),.450)
  self.assertAlmostEqual(min(local_y(l,v) for v in right.vertices),-.450)
  self.assertAlmostEqual(max(local_y(l,v) for v in right.vertices),-.432)
 def test_all_combinations_stay_inside_body_envelope(self):
  for left,right in ((1,1),(1,0),(0,1),(0,0)):
   l,_fragments,mesh=prepare_residential_geometry(((0,0),(3.6,0)),'FORWARD',425,2800,16,900,30,12,fields=ResidentialFields(left_side_board_enabled=bool(left),right_side_board_enabled=bool(right)))
   ys=[local_y(l,v) for v in mesh.vertices]
   self.assertAlmostEqual(min(ys),-.45); self.assertAlmostEqual(max(ys),.45)
 def test_profile_width_changes_only_side_boards(self):
  args=(((0,0),(3.6,0)),'FORWARD',425,2800,16,900,30,12)
  results=[]
  for width in (40,60):
   _l,fragments,_mesh=prepare_residential_geometry(*args,fields=ResidentialFields(side_board_profile_width_mm=width))
   results.append((tuple(f for f in fragments if f.part_type!='SIDE_BOARD'),
                   tuple(f for f in fragments if f.part_type=='SIDE_BOARD')))
  self.assertEqual(results[0][0],results[1][0]); self.assertNotEqual(results[0][1],results[1][1])
  p40=side_board_profile(layout(),ResidentialFields(side_board_profile_width_mm=40))
  p60=side_board_profile(layout(),ResidentialFields(side_board_profile_width_mm=60))
  self.assertEqual(p40.reference,p60.reference); self.assertNotEqual(p40.outer,p60.outer)
 def test_closure_depth_remains_independent_compatibility_field(self):
  l=layout(); a=stepped_underbody_profile(l,ResidentialFields(side_board_band_width_mm=150)); b=stepped_underbody_profile(l,ResidentialFields(side_board_band_width_mm=100))
  self.assertNotEqual(a.outer,b.outer); self.assertEqual(a.inner,b.inner)
 def test_reverse_oblique_and_nonzero_base(self):
  for direction in ('FORWARD','REVERSE'):
   l=layout(direction,((1,2),(4,6)),425); f=build_side_board_fragment(l,'LEFT')
   self.assertAlmostEqual(min(v[2] for v in f.vertices),l.base_z)
   self.assertAlmostEqual(min(local_y(l,v) for v in f.vertices),l.width/2-.018)
   self.assertAlmostEqual(max(local_y(l,v) for v in f.vertices),l.width/2)
   self.assertTrue(validate_mesh_fragments((f,)))
 def test_invalid_band_rejected_atomically_during_prepare(self):
  with self.assertRaises(ValueError): prepare_residential_geometry(((0,0),(3.6,0)),'FORWARD',0,2800,16,900,30,12,fields=ResidentialFields(side_board_band_width_mm=175))
  for invalid in (0,175,float('nan'),float('inf'),True):
   with self.subTest(invalid=invalid),self.assertRaises(ValueError):
    prepare_residential_geometry(((0,0),(3.6,0)),'FORWARD',0,2800,16,900,30,12,fields=ResidentialFields(side_board_profile_width_mm=invalid))
 def test_invalid_profile_width_is_ignored_when_boards_off(self):
  fields=ResidentialFields(left_side_board_enabled=False,right_side_board_enabled=False,side_board_profile_width_mm=float('nan'))
  prepare_residential_geometry(((0,0),(3.6,0)),'FORWARD',0,2800,16,900,30,12,fields=fields)
 def test_corrected_body_regressions(self):
  l=layout(); p=stepped_underbody_profile(l)
  self.assertEqual([q for q in p.outer if q[1]==l.base_z],[(l.riser_thickness,l.base_z),(l.going+.15,l.base_z)])
  _basic_l,_basic_f,basic=prepare_stair_geometry(((0,0),(3.6,0)),'FORWARD',425,2800,16,900,30,12)
  self.assertEqual((len(basic.vertices),len(basic.faces)),(248,186))

class MaterialTests(unittest.TestCase):
 def test_base_partial_override_and_identity_dedupe(self):
  wood,white=object(),object(); f=ResidentialFields(base_material=wood,riser_material=white)
  self.assertEqual(tuple(resolve_material_roles(f)),MATERIAL_ROLES)
  plan=assemble_material_slot_plan(f); self.assertEqual(plan.slots,(wood,white)); self.assertEqual(dict(plan.role_indices),{'TREAD':0,'RISER':1,'UNDERSIDE':0,'SIDE_BOARD':0})
 def test_mixed_empty_slot_without_substitute(self):
  wood=object(); plan=assemble_material_slot_plan(ResidentialFields(tread_material=wood))
  self.assertEqual(plan.slots,(wood,None)); self.assertEqual(dict(plan.role_indices),{'TREAD':0,'RISER':1,'UNDERSIDE':1,'SIDE_BOARD':1})
 def test_all_none_creates_no_slots(self):
  plan=assemble_material_slot_plan(ResidentialFields()); self.assertEqual(plan.slots,()); self.assertEqual(set(dict(plan.role_indices).values()),{0})
 def test_every_face_has_role(self):
  _l,fragments,mesh=prepare_residential_geometry(((0,0),(3.6,0)),'FORWARD',0,2800,16,900,30,12)
  self.assertEqual(len(mesh.faces),len(mesh.face_roles)); self.assertEqual(set(mesh.face_roles),set(MATERIAL_ROLES))

class ActivationTests(unittest.TestCase):
 def test_central_policy_mode_gates(self):
  self.assertTrue(operation_allowed('APPLY_RESIDENTIAL',(),'BASIC_TREAD_RISER'))
  self.assertFalse(operation_allowed('APPLY_RESIDENTIAL',(),'STANDARD_RESIDENTIAL'))
  self.assertTrue(operation_allowed('EDIT_MATERIALS',(),'STANDARD_RESIDENTIAL'))
  self.assertFalse(operation_allowed('EDIT_RESIDENTIAL',(),'BASIC_TREAD_RISER'))
 def test_public_source_and_no_stage4_features(self):
  source=(ROOT/'japanese_house_modeler'/'stair_operators.py').read_text()
  for op in ('jhm.apply_residential_stair','jhm.edit_residential_stair','jhm.edit_stair_materials'): self.assertIn(op,source)
  for feature in ('SLOPED_CLOSED","','WINDER","','LANDING","'): self.assertNotIn(feature,source)
if __name__=='__main__': unittest.main()
