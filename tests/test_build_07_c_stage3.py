"""Build 07-C Stage 3 nosing and tread-front contracts."""

from dataclasses import replace
import math
import pathlib
import sys
import types
import unittest

ROOT = pathlib.Path(__file__).parents[1]
package = types.ModuleType("japanese_house_modeler")
package.__path__ = [str(ROOT / "japanese_house_modeler")]
sys.modules.setdefault("japanese_house_modeler", package)

from japanese_house_modeler.stair_geometry import build_riser_fragments, resolve_stair_layout, validate_mesh_fragments
from japanese_house_modeler.stair_residential import (
    BEVEL, MATERIAL_ROLES, ROUND, SLOPED, SLOPED_CLOSED, SQUARE,
    STEPPED, STEPPED_CLOSED, ResidentialFields, new_residential_fields,
    residential_fields, schema_version_after_residential_edit,
    validate_nosing_board_compatibility, validate_tread_front,
)
from japanese_house_modeler.stair_residential_geometry import (
    build_residential_riser_fragments, build_residential_tread_fragments,
    build_top_arrival_nosing_fragment, prepare_residential_geometry,
    side_board_profile, sloped_side_board_profile, sloped_underbody_profile,
    tread_front_xz_profile,
)

ARGS = (((0, 0), (3.6, 0)), "FORWARD", 125, 2800, 16, 900, 30, 12)


def layout(points=ARGS[0], direction=ARGS[1], base=ARGS[2]):
    return resolve_stair_layout(points, direction, base, *ARGS[3:])


class DefaultsAndValidationTests(unittest.TestCase):
    def test_creation_default_is_explicit_and_legacy_default_stays_zero(self):
        self.assertEqual(new_residential_fields().tread_front_overhang_mm, 5.0)
        self.assertEqual(ResidentialFields().tread_front_overhang_mm, 0.0)
        self.assertEqual((new_residential_fields().tread_front_edge_mode,
                          new_residential_fields().tread_front_edge_size_mm),
                         (SQUARE, 5.0))

    def test_missing_and_stored_legacy_values_stay_zero(self):
        self.assertEqual(residential_fields(types.SimpleNamespace()).tread_front_overhang_mm, 0.0)
        self.assertEqual(residential_fields(types.SimpleNamespace(
            tread_front_overhang_mm=0.0)).tread_front_overhang_mm, 0.0)

    def test_overhang_range(self):
        l = layout()
        for mm in (0, l.going * 1000 - 1e-6):
            self.assertEqual(validate_tread_front(
                ResidentialFields(tread_front_overhang_mm=mm),
                l.going, l.tread_thickness)[0], mm / 1000)
        for mm in (-1, l.going * 1000, float("nan")):
            with self.assertRaises(ValueError):
                validate_tread_front(ResidentialFields(tread_front_overhang_mm=mm), l.going, l.tread_thickness)

    def test_bevel_and_round_size_range(self):
        l = layout()
        for mode in (BEVEL, ROUND):
            self.assertEqual(validate_tread_front(ResidentialFields(
                tread_front_overhang_mm=5, tread_front_edge_mode=mode,
                tread_front_edge_size_mm=5), l.going, l.tread_thickness),
                (0.005, 0.005))
            for n, q in ((0, 1), (5, 0), (5, 15), (5, 6)):
                with self.subTest(mode=mode, n=n, q=q), self.assertRaises(ValueError):
                    validate_tread_front(ResidentialFields(
                        tread_front_overhang_mm=n, tread_front_edge_mode=mode,
                        tread_front_edge_size_mm=q), l.going, l.tread_thickness)

    def test_square_ignores_stored_edge_size(self):
        l = layout()
        self.assertEqual(validate_tread_front(ResidentialFields(
            tread_front_edge_size_mm=-123), l.going, l.tread_thickness)[0], 0)

    def test_board_reveal_compatibility(self):
        l = layout()
        validate_nosing_board_compatibility(ResidentialFields(
            tread_front_overhang_mm=5, side_board_reveal_mm=40),
            l.going, l.tread_thickness, l.actual_riser)
        with self.assertRaises(ValueError):
            validate_nosing_board_compatibility(ResidentialFields(
                tread_front_overhang_mm=70, side_board_reveal_mm=40),
                l.going, l.tread_thickness, l.actual_riser)
        validate_nosing_board_compatibility(ResidentialFields(
            tread_front_overhang_mm=70, left_side_board_enabled=False,
            right_side_board_enabled=False), l.going, l.tread_thickness,
            l.actual_riser)

    def test_front_edit_promotes_schema_two_only_when_changed(self):
        old = ResidentialFields()
        self.assertEqual(schema_version_after_residential_edit(2, old, old), 2)
        self.assertEqual(schema_version_after_residential_edit(
            2, old, replace(old, tread_front_overhang_mm=5)), 3)


class ProfileTests(unittest.TestCase):
    def test_square_exact_profile(self):
        self.assertEqual(tread_front_xz_profile(1, 2, 3, 4, SQUARE, 99),
                         ((1, 3), (2, 3), (2, 4), (1, 4)))

    def test_bevel_exact_profile(self):
        self.assertEqual(tread_front_xz_profile(1, 2, 3, 4, BEVEL, .1),
                         ((1.1, 3), (2, 3), (2, 4), (1.1, 4),
                          (1, 3.9), (1, 3.1)))

    def test_round_is_deterministic_with_four_chords_per_corner(self):
        a = tread_front_xz_profile(1, 2, 3, 4, ROUND, .1)
        self.assertEqual(a, tread_front_xz_profile(1, 2, 3, 4, ROUND, .1))
        self.assertEqual(len(a), 12)
        self.assertAlmostEqual(min(x for x, _z in a), 1.0)
        self.assertEqual(a[:4], ((1.1, 3), (2, 3), (2, 4), (1.1, 4)))


class GeometryTests(unittest.TestCase):
    def fields(self, **changes):
        return replace(ResidentialFields(), **changes)

    def test_zero_overhang_is_exact_accepted_regression(self):
        mesh = prepare_residential_geometry(*ARGS)[2]
        self.assertEqual((len(mesh.vertices), len(mesh.faces)), (620, 732))
        first = build_residential_tread_fragments(layout())[0]
        self.assertAlmostEqual(min(v[0] for v in first.vertices), 0.0)

    def test_nosing_changes_front_only(self):
        l = layout()
        old = build_residential_tread_fragments(l, self.fields())
        new = build_residential_tread_fragments(l, self.fields(tread_front_overhang_mm=5))
        for ordinal, (a, b) in enumerate(zip(old, new), 1):
            self.assertAlmostEqual(min(v[0] for v in b.vertices), (ordinal - 1) * l.going - .005)
            self.assertAlmostEqual(max(v[0] for v in b.vertices), ordinal * l.going + l.riser_thickness)
            self.assertEqual((min(v[2] for v in a.vertices), max(v[2] for v in a.vertices)),
                             (min(v[2] for v in b.vertices), max(v[2] for v in b.vertices)))

    def test_risers_final_riser_and_tread_count_unchanged(self):
        l = layout()
        self.assertEqual(build_riser_fragments(l), build_riser_fragments(l))
        self.assertEqual(len(build_residential_tread_fragments(l,
            self.fields(tread_front_overhang_mm=5))), l.riser_count - 1)
        final = build_riser_fragments(l)[-1]
        self.assertAlmostEqual(min(v[0] for v in final.vertices), l.run_length)

    def test_profiled_fragments_are_closed_positive_and_all_tread(self):
        for mode, counts in ((SQUARE, (8, 6)), (BEVEL, (12, 14)),
                             (ROUND, (24, 32))):
            fields = self.fields(tread_front_overhang_mm=5,
                                 tread_front_edge_mode=mode,
                                 left_side_board_enabled=False,
                                 right_side_board_enabled=False)
            l, fragments, mesh = prepare_residential_geometry(*ARGS, fields=fields)
            tread = fragments[0]
            self.assertEqual((len(tread.vertices), len(tread.faces)), counts)
            self.assertTrue(validate_mesh_fragments((tread,)))
            self.assertTrue(all(math.isfinite(x) for v in tread.vertices for x in v))
            self.assertEqual(set(mesh.face_roles), {"TREAD", "RISER", "UNDERSIDE"})
            self.assertEqual(MATERIAL_ROLES, ("TREAD", "RISER", "UNDERSIDE", "SIDE_BOARD"))

    def test_body_and_board_profiles_do_not_depend_on_nosing(self):
        l = layout()
        zero = self.fields(underside_mode=SLOPED_CLOSED, side_board_mode=SLOPED)
        nose = replace(zero, tread_front_overhang_mm=5)
        self.assertEqual(sloped_underbody_profile(l, zero), sloped_underbody_profile(l, nose))
        self.assertEqual(sloped_side_board_profile(l, zero), sloped_side_board_profile(l, nose))
        old_stepped = side_board_profile(l, replace(zero, side_board_mode=STEPPED))
        new_stepped = side_board_profile(l, replace(nose, side_board_mode=STEPPED))
        self.assertEqual(old_stepped.lower, new_stepped.lower)
        self.assertNotEqual(old_stepped.outer, new_stepped.outer)

    def test_square_top_arrival_cap_has_exact_bounds_and_full_width(self):
        l = layout(base=0)
        cap = build_top_arrival_nosing_fragment(
            l, self.fields(tread_front_overhang_mm=5))
        self.assertIsNotNone(cap)
        self.assertEqual(cap.part_type, "TREAD")
        self.assertEqual(cap.ordinal, l.riser_count)
        self.assertEqual((min(v[0] for v in cap.vertices),
                          max(v[0] for v in cap.vertices)),
                         (l.run_length - .005,
                          l.run_length + l.riser_thickness))
        self.assertEqual((min(v[1] for v in cap.vertices),
                          max(v[1] for v in cap.vertices)),
                         (-l.width / 2, l.width / 2))
        self.assertEqual((min(v[2] for v in cap.vertices),
                          max(v[2] for v in cap.vertices)), (2.77, 2.8))
        self.assertTrue(validate_mesh_fragments((cap,)))

    def test_top_arrival_thickness_linkage_and_finished_height(self):
        for thickness, expected_bottom in ((30, 2.77), (40, 2.76)):
            l = resolve_stair_layout(ARGS[0], ARGS[1], 0, 2800, 16, 900,
                                     thickness, 12)
            cap = build_top_arrival_nosing_fragment(
                l, self.fields(tread_front_overhang_mm=5))
            self.assertAlmostEqual(min(v[2] for v in cap.vertices),
                                   expected_bottom)
            self.assertAlmostEqual(max(v[2] for v in cap.vertices), 2.8)

    def test_final_riser_top_depends_only_on_positive_nosing(self):
        l = layout(base=0)
        legacy = build_residential_riser_fragments(l, self.fields())
        corrected = build_residential_riser_fragments(
            l, self.fields(tread_front_overhang_mm=5))
        self.assertEqual(len(legacy), l.riser_count)
        self.assertEqual(len(corrected), l.riser_count)
        self.assertEqual(max(v[2] for v in legacy[-1].vertices), 2.8)
        self.assertEqual(max(v[2] for v in corrected[-1].vertices), 2.77)
        self.assertEqual(min(v[2] for v in legacy[-1].vertices),
                         min(v[2] for v in corrected[-1].vertices))

    def test_zero_nosing_has_no_cap_and_keeps_exact_legacy_risers(self):
        l = layout()
        self.assertIsNone(build_top_arrival_nosing_fragment(l, self.fields()))
        self.assertEqual(build_residential_riser_fragments(l, self.fields()),
                         build_riser_fragments(l))
        self.assertEqual(l.independent_tread_count, l.riser_count - 1)

    def test_top_cap_uses_every_front_profile_and_tread_role(self):
        l = layout()
        for mode, counts in ((SQUARE, (8, 6)), (BEVEL, (12, 14)),
                             (ROUND, (24, 32))):
            fields = self.fields(tread_front_overhang_mm=5,
                                 tread_front_edge_mode=mode)
            cap = build_top_arrival_nosing_fragment(l, fields)
            self.assertEqual((len(cap.vertices), len(cap.faces)), counts)
            self.assertTrue(validate_mesh_fragments((cap,)))
            _layout, _fragments, mesh = prepare_residential_geometry(
                *ARGS, fields=fields)
            self.assertEqual(mesh.face_roles.count("TREAD"),
                             sum(len(f.faces) for f in _fragments
                                 if f.part_type == "TREAD"))

    def test_top_cap_is_not_an_ordinary_full_depth_tread(self):
        l = layout()
        ordinary = build_residential_tread_fragments(
            l, self.fields(tread_front_overhang_mm=5))
        cap = build_top_arrival_nosing_fragment(
            l, self.fields(tread_front_overhang_mm=5))
        self.assertEqual(len(ordinary), l.independent_tread_count)
        self.assertAlmostEqual(max(v[0] for v in cap.vertices)
                               - min(v[0] for v in cap.vertices),
                               .005 + l.riser_thickness)

    def test_stepped_board_corrected_top_and_sloped_profile_unchanged(self):
        l = layout()
        fields = self.fields(tread_front_overhang_mm=5)
        reveal = fields.side_board_reveal_mm / 1000
        stepped = side_board_profile(l, fields)
        expected = ((l.run_length - reveal, l.upper_arrival_z + reveal),
                    (l.run_length + l.riser_thickness,
                     l.upper_arrival_z + reveal),
                    (l.run_length + l.riser_thickness, l.upper_arrival_z))
        self.assertEqual(stepped.outer[-3:], expected)
        self.assertEqual(stepped.outer[-3][1], stepped.outer[-2][1])
        self.assertEqual(stepped.outer[-2][0], stepped.outer[-1][0])
        sloped = sloped_side_board_profile(l, fields)
        self.assertEqual(sloped.outer, (
            (-reveal, l.base_z),
            (-reveal, l.base_z + l.actual_riser + reveal),
            (l.run_length - reveal, l.upper_arrival_z + reveal),
            (l.run_length + l.riser_thickness, l.upper_arrival_z + reveal),
            (l.run_length + l.riser_thickness, l.upper_arrival_z)))

    def test_all_body_board_combinations_with_square_nosing(self):
        for underside in (STEPPED_CLOSED, SLOPED_CLOSED):
            for board in (STEPPED, SLOPED):
                _l, fragments, _mesh = prepare_residential_geometry(
                    *ARGS, fields=self.fields(underside_mode=underside,
                    side_board_mode=board, tread_front_overhang_mm=5))
                self.assertTrue(validate_mesh_fragments(fragments))

    def test_bevel_round_with_boards_off_and_on(self):
        for mode in (BEVEL, ROUND):
            for enabled in (False, True):
                _l, fragments, mesh = prepare_residential_geometry(
                    *ARGS, fields=self.fields(tread_front_overhang_mm=5,
                    tread_front_edge_mode=mode, left_side_board_enabled=enabled,
                    right_side_board_enabled=enabled))
                self.assertTrue(validate_mesh_fragments(fragments))
                self.assertTrue(all(role in MATERIAL_ROLES for role in mesh.face_roles))

    def test_forward_reverse_oblique_and_nonzero_base(self):
        for direction in ("FORWARD", "REVERSE"):
            l, fragments, _mesh = prepare_residential_geometry(
                ((1, 2), (4, 6)), direction, 375, *ARGS[3:],
                fields=self.fields(tread_front_overhang_mm=5))
            self.assertEqual(l.base_z, .375)
            self.assertTrue(validate_mesh_fragments(fragments))

    def test_invalid_candidate_preparation_has_no_mutation_target(self):
        fields = self.fields(tread_front_overhang_mm=70, side_board_reveal_mm=40)
        with self.assertRaises(ValueError):
            prepare_residential_geometry(*ARGS, fields=fields)

    def test_basic_source_remains_independent(self):
        source = (ROOT / "japanese_house_modeler/stair_geometry.py").read_text()
        self.assertNotIn("tread_front_overhang", source)


if __name__ == "__main__":
    unittest.main()
