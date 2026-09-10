"""Pure/mock coverage for Build 04-C and 04-D joint mathematics."""

import importlib.util
import math
import pathlib
import sys
import types
import unittest


ROOT = pathlib.Path(__file__).parents[1]
PACKAGE = "japanese_house_modeler"


class _Meshes:
    pass


bpy = types.ModuleType("bpy")
bpy.data = types.SimpleNamespace(meshes=_Meshes())
sys.modules["bpy"] = bpy
package = types.ModuleType(PACKAGE)
package.__path__ = [str(ROOT / PACKAGE)]
sys.modules[PACKAGE] = package

connections = types.ModuleType(f"{PACKAGE}.connections")
connections.is_valid_wall_object = lambda wall: True
connections.junction_members = lambda wall, endpoint: wall.members[endpoint]
sys.modules[connections.__name__] = connections

junctions_spec = importlib.util.spec_from_file_location(
    f"{PACKAGE}.junctions", ROOT / PACKAGE / "junctions.py"
)
junctions = importlib.util.module_from_spec(junctions_spec)
sys.modules[junctions_spec.name] = junctions
junctions_spec.loader.exec_module(junctions)

spec = importlib.util.spec_from_file_location(
    f"{PACKAGE}.joints", ROOT / PACKAGE / "joints.py"
)
joints = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = joints
spec.loader.exec_module(joints)


IDENTITY = tuple(
    tuple(1.0 if row == column else 0.0 for column in range(4))
    for row in range(4)
)


class Wall:
    _next_pointer = 1

    def __init__(self, start, end, thickness=130.0, height=2500.0):
        self.jhm_wall = types.SimpleNamespace(
            start=(*start, 0.0), end=(*end, 0.0),
            wall_thickness=thickness, wall_height=height,
        )
        self.matrix_basis = IDENTITY
        self.members = {"START": [(self, "START")], "END": [(self, "END")]}
        self.classification = {"START": "ISOLATED", "END": "ISOLATED"}
        self._pointer = Wall._next_pointer
        Wall._next_pointer += 1

    def as_pointer(self):
        return self._pointer


def connect(first, first_endpoint, second, second_endpoint, key="CORNER"):
    members = [(first, first_endpoint), (second, second_endpoint)]
    first.members[first_endpoint] = members
    second.members[second_endpoint] = list(reversed(members))
    first.classification[first_endpoint] = key
    second.classification[second_endpoint] = key


def connect_t(*members):
    topology = list(members)
    for index, (wall, endpoint) in enumerate(members):
        wall.members[endpoint] = topology[index:] + topology[:index]
        wall.classification[endpoint] = "T_JUNCTION"


def connect_cross(*members):
    topology = list(members)
    for index, (wall, endpoint) in enumerate(members):
        wall.members[endpoint] = topology[index:] + topology[:index]


def wall_from_junction(angle, endpoint="START", thickness=130.0, length=2.0,
                       origin=(0.0, 0.0)):
    radians = math.radians(angle)
    far = (origin[0] + length * math.cos(radians),
           origin[1] + length * math.sin(radians))
    return (Wall(origin, far, thickness) if endpoint == "START"
            else Wall(far, origin, thickness))


def assert_points_equal(test, first, second):
    test.assertAlmostEqual(first[0], second[0], places=10)
    test.assertAlmostEqual(first[1], second[1], places=10)


class MiterMathTests(unittest.TestCase):
    def corner(self, degrees, first_thickness=130.0, second_thickness=130.0):
        radians = math.radians(degrees)
        first = Wall((0, 0), (2, 0), first_thickness)
        second = Wall((0, 0), (2 * math.cos(radians), 2 * math.sin(radians)), second_thickness)
        connect(first, "START", second, "START")
        return first, second

    def test_90_degree_equal_and_cross_side_symmetry(self):
        first, second = self.corner(90)
        first_pair = joints.calculate_miter_pair(first, "START", second, "START")
        second_pair = joints.calculate_miter_pair(second, "START", first, "START")
        self.assertIsNotNone(first_pair)
        assert_points_equal(self, first_pair[0], second_pair[1])
        assert_points_equal(self, first_pair[1], second_pair[0])

    def test_45_and_15_degree_are_safe(self):
        for degrees in (45, 15):
            with self.subTest(degrees=degrees):
                first, second = self.corner(degrees)
                self.assertIsNotNone(
                    joints.calculate_miter_pair(first, "START", second, "START")
                )

    def test_acute_corner_falls_back(self):
        first, second = self.corner(2.5)
        self.assertIsNone(joints.calculate_miter_pair(first, "START", second, "START"))

    def test_unequal_thickness_still_shares_edge(self):
        first, second = self.corner(90, 130, 200)
        first_pair = joints.calculate_miter_pair(first, "START", second, "START")
        second_pair = joints.calculate_miter_pair(second, "START", first, "START")
        assert_points_equal(self, first_pair[0], second_pair[1])
        assert_points_equal(self, first_pair[1], second_pair[0])

    def test_parallel_and_near_parallel_fall_back(self):
        for degrees in (180, 0.000000001):
            with self.subTest(degrees=degrees):
                first, second = self.corner(degrees)
                self.assertIsNone(
                    joints.calculate_miter_pair(first, "START", second, "START")
                )

    def test_position_mismatch_falls_back(self):
        first = Wall((0, 0), (2, 0))
        second = Wall((0.000002, 0), (0.000002, 2))
        self.assertIsNone(joints.calculate_miter_pair(first, "START", second, "START"))

    def test_finite_polygon_validation(self):
        self.assertTrue(joints.validate_lower_polygon(((0, 1), (0, -1), (2, -1), (2, 1))))
        self.assertFalse(joints.validate_lower_polygon(((0, 1), (0, -1), (math.inf, -1), (2, 1))))
        self.assertFalse(joints.validate_lower_polygon(((0, 0), (1, 1), (0, 1), (1, 0))))

    def test_single_and_both_endpoint_miter_geometry(self):
        center = Wall((0, 0), (2, 0))
        start_partner = Wall((0, 0), (0, 2))
        connect(center, "START", start_partner, "START")
        geometry = joints.build_wall_geometry(center)
        self.assertIsNotNone(geometry)
        self.assertTrue(joints.validate_lower_polygon([vertex[:2] for vertex in geometry[0][:4]]))

        end_partner = Wall((2, 0), (2, 2))
        connect(center, "END", end_partner, "START")
        geometry = joints.build_wall_geometry(center)
        self.assertIsNotNone(geometry)
        lower = [vertex[:2] for vertex in geometry[0][:4]]
        self.assertTrue(joints.validate_lower_polygon(lower))
        self.assertGreater(abs(sum(lower[index][0] * lower[(index + 1) % 4][1] - lower[(index + 1) % 4][0] * lower[index][1] for index in range(4))), 0)


class TJunctionMathTests(unittest.TestCase):
    def make_t(self, angle=90.0, main_thickness=(130.0, 130.0), branch_thickness=130.0,
               branch_length=2.0, endpoints=("START", "START", "START"),
               main_angle=180.0):
        radians = math.radians(angle)
        # Each endpoint direction points inward from the shared canonical origin.
        def wall_for(direction, endpoint, thickness, length=2.0):
            far = (direction[0] * length, direction[1] * length)
            return Wall((0, 0), far, thickness) if endpoint == "START" else Wall(far, (0, 0), thickness)
        first = wall_for((1, 0), endpoints[0], main_thickness[0])
        main_radians = math.radians(main_angle)
        second = wall_for(
            (math.cos(main_radians), math.sin(main_radians)),
            endpoints[1], main_thickness[1],
        )
        branch = wall_for((math.cos(radians), math.sin(radians)), endpoints[2], branch_thickness, branch_length)
        connect_t((first, endpoints[0]), (second, endpoints[1]), (branch, endpoints[2]))
        return first, second, branch

    def test_90_degree_roles_and_trim_on_host_boundary(self):
        first, second, branch = self.make_t()
        roles = junctions.t_junction_roles(branch, "START")
        self.assertEqual({member[0] for member in roles[0]}, {first, second})
        self.assertIs(roles[1][0], branch)
        pair, status = joints.endpoint_joint_pair(branch, "START")
        self.assertEqual(status, "T_BRANCH")
        self.assertTrue(all(abs(point[1] - 0.065) < 1.0e-10 for point in pair))
        self.assertEqual(joints.endpoint_joint_pair(first, "START")[1], "T_MAIN")
        self.assertEqual(joints.endpoint_joint_pair(second, "START")[1], "T_MAIN")

    def test_exact_180_degree_main_pair_is_valid(self):
        first, second, branch = self.make_t(main_angle=180.0)
        self.assertEqual(junctions.classify_junction(first, "START").key, "T_JUNCTION")
        self.assertEqual(joints.endpoint_joint_pair(first, "START")[1], "T_MAIN")
        self.assertEqual(joints.endpoint_joint_pair(second, "START")[1], "T_MAIN")
        self.assertEqual(joints.endpoint_joint_pair(branch, "START")[1], "T_BRANCH")

    def test_classified_179_5_degree_main_pair_safely_falls_back(self):
        members = self.make_t(main_angle=179.5)
        self.assertTrue(
            all(junctions.classify_junction(wall, "START").key == "T_JUNCTION" for wall in members)
        )
        self.assertTrue(
            all(joints.endpoint_joint_pair(wall, "START")[1] == "FALLBACK" for wall in members)
        )

    def test_roles_are_member_order_independent(self):
        first, second, branch = self.make_t()
        expected = {first, second}
        for order in (
            [(first, "START"), (second, "START"), (branch, "START")],
            [(branch, "START"), (first, "START"), (second, "START")],
            [(second, "START"), (branch, "START"), (first, "START")],
        ):
            for wall, endpoint in order:
                wall.members[endpoint] = list(order)
            roles = junctions.t_junction_roles(branch, "START")
            self.assertEqual({member[0] for member in roles[0]}, expected)
            self.assertIs(roles[1][0], branch)

    def test_start_end_combinations_and_main_reference_invariance(self):
        for endpoints in (("START", "END", "START"), ("END", "START", "END")):
            first, second, branch = self.make_t(endpoints=endpoints)
            first_solution = joints.calculate_t_solution(first, endpoints[0])
            second_solution = joints.calculate_t_solution(second, endpoints[1])
            self.assertIsNotNone(first_solution)
            for first_point, second_point in zip(first_solution[2], second_solution[2]):
                assert_points_equal(self, first_point, second_point)
            assert_points_equal(self, first_solution[3], second_solution[3])
            self.assertAlmostEqual(
                abs(first_solution[4][0] * second_solution[4][0] + first_solution[4][1] * second_solution[4][1]),
                1.0,
                places=10,
            )
            self.assertEqual(joints.endpoint_joint_pair(branch, endpoints[2])[1], "T_BRANCH")

    def test_exact_main_reversal_preserves_trim_and_host_boundary(self):
        first, second, branch = self.make_t()
        original = joints.calculate_t_solution(branch, "START")
        reversed_members = [(second, "START"), (first, "START"), (branch, "START")]
        for wall, member_endpoint in reversed_members:
            wall.members[member_endpoint] = list(reversed_members)
        reversed_solution = joints.calculate_t_solution(branch, "START")
        self.assertIsNotNone(original)
        self.assertIsNotNone(reversed_solution)
        for original_point, reversed_point in zip(original[2], reversed_solution[2]):
            assert_points_equal(self, original_point, reversed_point)
        assert_points_equal(self, original[3], reversed_solution[3])
        self.assertAlmostEqual(
            abs(original[4][0] * reversed_solution[4][0] + original[4][1] * reversed_solution[4][1]),
            1.0,
            places=10,
        )

    def test_45_and_15_degree_branches_are_valid(self):
        for angle in (45.0, 15.0):
            _first, _second, branch = self.make_t(angle=angle)
            self.assertEqual(joints.endpoint_joint_pair(branch, "START")[1], "T_BRANCH")

    def test_shallow_branch_falls_back_for_every_member(self):
        members = self.make_t(angle=2.5)
        self.assertTrue(all(joints.endpoint_joint_pair(wall, "START")[1] == "FALLBACK" for wall in members))

    def test_branch_may_be_thicker_than_equal_mains(self):
        first, second, branch = self.make_t(branch_thickness=200.0)
        self.assertEqual(joints.endpoint_joint_pair(branch, "START")[1], "T_BRANCH")
        self.assertEqual(joints.endpoint_joint_pair(first, "START")[1], "T_MAIN")
        self.assertEqual(joints.endpoint_joint_pair(second, "START")[1], "T_MAIN")

    def test_orthogonal_unequal_main_uses_step_profile(self):
        first, second, branch = self.make_t(main_thickness=(130.0, 200.0))
        self.assertEqual(joints.endpoint_joint_pair(first, "START")[1], "T_MAIN")
        self.assertEqual(joints.endpoint_joint_pair(second, "START")[1], "T_MAIN")
        profile, status = joints.endpoint_joint_profile(branch, "START")
        self.assertEqual(status, "T_BRANCH")
        self.assertEqual(len(profile), 4)
        self.assertEqual(sorted({round(point[1], 3) for point in profile}), [0.065, 0.1])
        self.assertEqual(tuple(map(len, joints.build_wall_geometry(branch))), (12, 8))

    def test_unequal_main_oblique_branch_falls_back_for_all(self):
        members = self.make_t(angle=45.0, main_thickness=(130.0, 200.0))
        self.assertTrue(all(joints.endpoint_joint_pair(wall, "START")[1] == "FALLBACK"
                            for wall in members))

    def test_step_t_reversal_endpoints_and_length_safety(self):
        first, second, branch = self.make_t(
            main_thickness=(200.0, 130.0), branch_thickness=200.0,
            endpoints=("END", "START", "END"),
        )
        profile, status = joints.endpoint_joint_profile(branch, "END")
        self.assertEqual((status, len(profile)), ("T_BRANCH", 4))
        self.assertEqual(sorted({round(abs(point[1]), 3) for point in profile}), [0.065, 0.1])
        for lengths in ((0.09, 2.0, 2.0), (2.0, 0.09, 2.0), (2.0, 2.0, 0.09)):
            walls = self.make_t(main_thickness=(130.0, 200.0), branch_thickness=200.0,
                                branch_length=lengths[2])
            for wall, length in zip(walls[:2], lengths[:2]):
                direction = joints.endpoint_data(wall, "START")[1]
                wall.jhm_wall.end = (direction[0] * length, direction[1] * length, 0.0)
            self.assertTrue(all(joints.endpoint_joint_pair(wall, "START")[1] == "FALLBACK"
                                for wall in walls))

    def test_position_mismatch_falls_back_for_all(self):
        members = self.make_t()
        members[2].jhm_wall.start = (2.0e-6, 0.0, 0.0)
        self.assertTrue(all(joints.endpoint_joint_pair(wall, "START")[1] == "FALLBACK" for wall in members))

    def test_non_identity_transform_falls_back(self):
        members = self.make_t()
        members[1].matrix_basis = tuple(
            tuple(2.0 if row == column == 0 else (1.0 if row == column else 0.0) for column in range(4))
            for row in range(4)
        )
        self.assertTrue(all(joints.endpoint_joint_pair(wall, "START")[1] == "FALLBACK" for wall in members))

    def test_very_short_branch_falls_back(self):
        members = self.make_t(branch_length=0.04)
        self.assertTrue(all(joints.endpoint_joint_pair(wall, "START")[1] == "FALLBACK" for wall in members))

    def test_t_branch_with_opposite_corner_builds_or_safely_falls_back(self):
        _first, _second, branch = self.make_t(branch_length=1.0)
        corner = Wall((0.0, 1.0), (1.0, 1.0))
        connect(branch, "END", corner, "START")
        geometry = joints.build_wall_geometry(branch)
        self.assertIsNotNone(geometry)
        statuses = joints._resolved_endpoint_pairs(branch)[2]
        self.assertIn(statuses["START"], {"T_BRANCH", "FALLBACK"})
        self.assertIn(statuses["END"], {"MITER", "FALLBACK"})


class CrossMathTests(unittest.TestCase):
    def make_cross(self, angles=(0.0, 180.0, 90.0, 270.0),
                   endpoints=("START",) * 4, thicknesses=(130.0,) * 4,
                   lengths=(2.0,) * 4):
        walls = tuple(
            wall_from_junction(angle, endpoint, thickness, length)
            for angle, endpoint, thickness, length
            in zip(angles, endpoints, thicknesses, lengths)
        )
        connect_cross(*(zip(walls, endpoints)))
        return walls

    def statuses(self, walls, endpoints=None):
        endpoints = endpoints or ("START",) * 4
        return tuple(
            joints.endpoint_joint_pair(wall, endpoint)[1]
            for wall, endpoint in zip(walls, endpoints)
        )

    def test_standard_cross_unique_partition_and_roles(self):
        walls = self.make_cross()
        pairs = junctions.cross_junction_pairs(walls[0], "START")
        self.assertEqual(len(pairs), 2)
        self.assertEqual({member[0] for member in pairs[0]} |
                         {member[0] for member in pairs[1]}, set(walls))
        self.assertEqual(self.statuses(walls),
                         ("CROSS_THROUGH", "CROSS_THROUGH", "CROSS_BUTT", "CROSS_BUTT"))

    def test_member_order_caller_and_start_end_do_not_change_roles(self):
        endpoints = ("START", "END", "END", "START")
        walls = self.make_cross(endpoints=endpoints)
        expected = {walls[0], walls[1]}
        orders = (
            list(zip(walls, endpoints)),
            [(walls[2], endpoints[2]), (walls[0], endpoints[0]),
             (walls[3], endpoints[3]), (walls[1], endpoints[1])],
        )
        for order in orders:
            for wall, member_endpoint in order:
                wall.members[member_endpoint] = list(order)
            for caller, caller_endpoint in order:
                solution = joints.calculate_cross_solution(caller, caller_endpoint)
                self.assertEqual(set(solution[0]), {
                    (wall, endpoint) for wall, endpoint in zip(walls[:2], endpoints[:2])
                })
                self.assertEqual(
                    {member[0] for member in solution[0]}, expected
                )

    def test_geometric_tie_break_is_deterministic(self):
        walls = self.make_cross(angles=(45.0, 225.0, -45.0, 135.0))
        # Equal X closeness is settled by canonical y: +45 is through.
        self.assertEqual(self.statuses(walls),
                         ("CROSS_THROUGH", "CROSS_THROUGH", "CROSS_BUTT", "CROSS_BUTT"))
        order = [(walls[3], "START"), (walls[1], "START"),
                 (walls[0], "START"), (walls[2], "START")]
        for wall in walls:
            wall.members["START"] = list(order)
        self.assertEqual(self.statuses(walls),
                         ("CROSS_THROUGH", "CROSS_THROUGH", "CROSS_BUTT", "CROSS_BUTT"))

    def test_ambiguous_collinear_cross_falls_back(self):
        walls = self.make_cross(angles=(0.0, 180.0, 0.0, 180.0))
        self.assertEqual(junctions.classify_junction(walls[0], "START").key, "CROSS")
        self.assertIsNone(junctions.cross_junction_pairs(walls[0], "START"))
        self.assertEqual(self.statuses(walls), ("FALLBACK",) * 4)

    def test_exact_pairs_valid_but_classified_near_opposite_falls_back(self):
        exact = self.make_cross()
        self.assertIsNotNone(joints.calculate_cross_solution(exact[3], "START"))
        near = self.make_cross(angles=(0.0, 179.5, 90.0, 270.0))
        self.assertEqual(junctions.classify_junction(near[0], "START").key, "CROSS")
        self.assertEqual(self.statuses(near), ("FALLBACK",) * 4)

    def test_position_and_transform_fail_whole_solution(self):
        mismatched = self.make_cross()
        mismatched[3].jhm_wall.start = (2.0e-6, 0.0, 0.0)
        self.assertEqual(self.statuses(mismatched), ("FALLBACK",) * 4)
        transformed = self.make_cross()
        transformed[1].matrix_basis = tuple(
            tuple(2.0 if row == column == 0 else (1.0 if row == column else 0.0)
                  for column in range(4)) for row in range(4)
        )
        self.assertEqual(self.statuses(transformed), ("FALLBACK",) * 4)

    def test_90_degree_butts_stop_on_host_outer_boundaries(self):
        walls = self.make_cross()
        for wall in walls[2:]:
            pair, status = joints.endpoint_joint_pair(wall, "START")
            self.assertEqual(status, "CROSS_BUTT")
            expected_y = 0.065 if wall is walls[2] else -0.065
            self.assertTrue(all(abs(point[1] - expected_y) < 1.0e-10 for point in pair))

    def test_crossing_angles_and_shallow_safety(self):
        for angle in (45.0, 15.0):
            walls = self.make_cross(angles=(0.0, 180.0, angle, angle + 180.0))
            self.assertEqual(self.statuses(walls).count("CROSS_BUTT"), 2)
        shallow = self.make_cross(angles=(0.0, 180.0, 2.5, 182.5))
        self.assertEqual(self.statuses(shallow), ("FALLBACK",) * 4)

    def test_orthogonal_unequal_through_steps_and_butts_may_differ(self):
        unequal_through = self.make_cross(thicknesses=(130.0, 200.0, 130.0, 130.0))
        self.assertEqual(self.statuses(unequal_through),
                         ("CROSS_THROUGH", "CROSS_THROUGH", "CROSS_BUTT", "CROSS_BUTT"))
        for wall in unequal_through[2:]:
            profile, status = joints.endpoint_joint_profile(wall, "START")
            self.assertEqual((status, len(profile)), ("CROSS_BUTT", 4))
            self.assertEqual(tuple(map(len, joints.build_wall_geometry(wall))), (12, 8))
        unequal_butts = self.make_cross(thicknesses=(130.0, 130.0, 130.0, 200.0))
        self.assertEqual(self.statuses(unequal_butts),
                         ("CROSS_THROUGH", "CROSS_THROUGH", "CROSS_BUTT", "CROSS_BUTT"))

    def test_unequal_through_oblique_cross_falls_back(self):
        walls = self.make_cross(angles=(0.0, 180.0, 45.0, 225.0),
                                thicknesses=(130.0, 200.0, 130.0, 130.0))
        self.assertEqual(self.statuses(walls), ("FALLBACK",) * 4)

    def test_step_cross_start_end_order_caller_and_length_safety(self):
        endpoints = ("END", "START", "END", "START")
        walls = self.make_cross(endpoints=endpoints,
                                thicknesses=(200.0, 130.0, 130.0, 200.0))
        expected = ("CROSS_THROUGH", "CROSS_THROUGH", "CROSS_BUTT", "CROSS_BUTT")
        for order in (list(zip(walls, endpoints)), list(reversed(list(zip(walls, endpoints))))):
            for wall, member_endpoint in order:
                wall.members[member_endpoint] = list(order)
            self.assertEqual(self.statuses(walls, endpoints), expected)
            for wall, member_endpoint in order:
                self.assertIsNotNone(joints.calculate_cross_step_solution(wall, member_endpoint))
        for lengths in ((0.05, 2.0, 2.0, 2.0), (2.0, 0.05, 2.0, 2.0),
                        (2.0, 2.0, 0.09, 2.0)):
            unsafe = self.make_cross(thicknesses=(130.0, 200.0, 130.0, 130.0),
                                     lengths=lengths)
            self.assertEqual(self.statuses(unsafe), ("FALLBACK",) * 4)


class PolygonAndExtrusionTests(unittest.TestCase):
    make_cross = CrossMathTests.make_cross
    statuses = CrossMathTests.statuses

    def test_variable_simple_polygons_and_invalid_contacts(self):
        self.assertTrue(joints.validate_lower_polygon(
            ((0, 1), (0, -1), (2, -1), (2, 1))))
        self.assertTrue(joints.validate_lower_polygon(
            ((.1, .1), (.1, 0), (.065, 0), (.065, -.1),
             (1.9, -.1), (1.9, 0), (1.935, 0), (1.935, .1))))
        self.assertFalse(joints.validate_lower_polygon(
            ((0, 0), (2, 0), (1, 1), (1, 0), (0, 1))))
        self.assertFalse(joints.validate_lower_polygon(
            ((0, 0), (3, 0), (3, 1), (1, 1), (2, 1), (0, 1))))
        self.assertFalse(joints.validate_lower_polygon(
            ((0, 0), (1, 0), (1, 0), (1, 1), (0, 1))))

    def test_generic_extrusion_counts_indices_and_finiteness(self):
        wall = Wall((0, 0), (2, 0))
        geometry = joints.build_wall_geometry(wall)
        self.assertEqual(tuple(map(len, geometry)), (8, 6))
        original = joints.endpoint_joint_profile
        profiles = {
            "START": (((.1, .1), (.1, 0), (.065, 0), (.065, -.1)), "T_BRANCH"),
            "END": (((1.9, -.1), (1.9, 0), (1.935, 0), (1.935, .1)), "T_BRANCH"),
        }
        try:
            joints.endpoint_joint_profile = lambda _wall, endpoint: profiles[endpoint]
            geometry = joints.build_wall_geometry(wall)
        finally:
            joints.endpoint_joint_profile = original
        self.assertEqual(tuple(map(len, geometry)), (16, 10))
        vertices, faces = geometry
        self.assertTrue(all(math.isfinite(value) for vertex in vertices for value in vertex))
        self.assertTrue(all(0 <= index < len(vertices) for face in faces for index in face))

    def test_very_short_butt_falls_back_for_all(self):
        walls = self.make_cross(lengths=(2.0, 2.0, 0.04, 2.0))
        self.assertEqual(self.statuses(walls), ("FALLBACK",) * 4)

    def test_through_reference_reversal_preserves_trim_set(self):
        walls = self.make_cross(angles=(0.0, 180.0, 45.0, 225.0))
        original = joints.calculate_cross_solution(walls[0], "START")
        order = [(walls[1], "START"), (walls[0], "START"),
                 (walls[2], "START"), (walls[3], "START")]
        for wall in walls:
            wall.members["START"] = list(order)
        reversed_solution = joints.calculate_cross_solution(walls[1], "START")
        original_points = sorted(point for _member, pair in original[1] for point in pair)
        reversed_points = sorted(point for _member, pair in reversed_solution[1] for point in pair)
        for first, second in zip(original_points, reversed_points):
            assert_points_equal(self, first, second)

    def test_cross_butt_with_opposite_corner_builds_or_locally_falls_back(self):
        walls = self.make_cross(lengths=(2.0, 2.0, 1.0, 2.0))
        corner = Wall((0.0, 1.0), (1.0, 1.0))
        connect(walls[2], "END", corner, "START")
        self.assertIsNotNone(joints.build_wall_geometry(walls[2]))
        statuses = joints._resolved_endpoint_pairs(walls[2])[2]
        self.assertIn(statuses["START"], {"CROSS_BUTT", "FALLBACK"})
        self.assertIn(statuses["END"], {"MITER", "FALLBACK"})


if __name__ == "__main__":
    unittest.main()
