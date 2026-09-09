"""Pure/mock coverage for Build 04-C joint mathematics."""

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

junctions = types.ModuleType(f"{PACKAGE}.junctions")
junctions.CONTINUATION = "CONTINUATION"
junctions.CORNER = "CORNER"
junctions.ISOLATED = "ISOLATED"
junctions.classify_junction = lambda wall, endpoint: types.SimpleNamespace(
    key=wall.classification[endpoint], member_count=len(wall.members[endpoint])
)
sys.modules[junctions.__name__] = junctions

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


if __name__ == "__main__":
    unittest.main()
