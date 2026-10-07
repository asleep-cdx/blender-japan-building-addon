"""Fresh Stage-3C ordinary Winder Side Board continuation."""

from collections import Counter
from dataclasses import replace
import hashlib
import math
import pathlib
import sys
import types
import unittest


ROOT = pathlib.Path(__file__).parents[1]
package = sys.modules.get("japanese_house_modeler")
if package is None:
    package = types.ModuleType("japanese_house_modeler")
    package.__path__ = [str(ROOT / "japanese_house_modeler")]
    sys.modules["japanese_house_modeler"] = package

from japanese_house_modeler.stair_geometry import validate_mesh_fragments
from japanese_house_modeler.stair_multiflight import prepare_multiflight_residential_geometry
from japanese_house_modeler.stair_residential import ResidentialFields
from japanese_house_modeler.stair_turn import (
    ScopeUnsupportedError, TurnSpec, _board_outer_distance,
    _board_outer_points,
    _canonical_outer_station,
    physical_cell_boundaries, prepare_turn_residential_geometry,
    winder_tread_rear_outer_authority, winder_underbody_support_footprint,
)


L = ((0.0, 0.0), (0.0, 2.2), (-2.2, 2.2))
COMPACT_U = ((0.0, 0.0), (0.0, 2.2), (0.9, 2.2), (0.9, 0.0))
ORDINARY_U = ((0.0, 0.0), (0.0, 2.2), (2.0, 2.2), (2.0, 0.0))
OFF = ResidentialFields(left_side_board_enabled=False,
                        right_side_board_enabled=False,
                        tread_front_overhang_mm=5.0)


def prepare(fields=None, points=L, direction="FORWARD", pattern="EQUAL_3",
            specs=None, width_mm=900, base_z_mm=0,
            floor_to_floor_mm=2800, riser_count=16):
    ids = ("p0", "t1", "p2") if len(points) == 3 else ("p0", "t1", "t2", "p3")
    return prepare_turn_residential_geometry(
        points, direction, base_z_mm, floor_to_floor_mm, riser_count,
        width_mm, 30, 12,
        fields=OFF if fields is None else fields, point_ids=ids,
        winder_pattern=pattern, turn_specs=specs)


def signature(parts):
    return tuple((part.part_type, part.ordinal, part.vertices, part.faces)
                 for part in parts if part.part_type != "SIDE_BOARD")


def boards(parts):
    return tuple(part for part in parts if part.part_type == "SIDE_BOARD")


def has_xy(parts, point):
    return any(math.dist(vertex[:2], point) < 1.0e-9
               for part in parts for vertex in part.vertices)


def rotate_xy(point, angle):
    cosine, sine = math.cos(angle), math.sin(angle)
    return (cosine * point[0] - sine * point[1],
            sine * point[0] + cosine * point[1])


def fragment_digest(parts):
    return hashlib.sha256(repr(tuple(
        (part.part_type, part.ordinal, part.vertices, part.faces)
        for part in parts)).encode()).hexdigest()


class FreshStage3CSideBoardTests(unittest.TestCase):
    def fields(self, underside="STEPPED_CLOSED", upper="STEPPED",
               left=True, right=True):
        return replace(OFF, underside_mode=underside, side_board_mode=upper,
                       left_side_board_enabled=left,
                       right_side_board_enabled=right)

    def test_four_independent_lower_upper_combinations(self):
        off_signature = {}
        for underside in ("STEPPED_CLOSED", "SLOPED_CLOSED"):
            off_signature[underside] = signature(prepare(
                self.fields(underside, left=False, right=False))[1])
            for upper in ("STEPPED", "SLOPED"):
                with self.subTest(underside=underside, upper=upper):
                    layout, parts, mesh = prepare(self.fields(underside, upper))
                    self.assertEqual(layout.winder_counts, (3,))
                    self.assertTrue(boards(parts))
                    self.assertEqual(signature(parts), off_signature[underside])
                    self.assertEqual(len(mesh.faces), len(mesh.face_roles))
                    self.assertTrue(validate_mesh_fragments(parts))

    def test_left_only_and_right_only_have_distinct_plan_ownership(self):
        left = prepare(self.fields(left=True, right=False))[1]
        right = prepare(self.fields(left=False, right=True))[1]
        self.assertTrue(boards(left))
        self.assertTrue(boards(right))
        self.assertNotEqual(boards(left), boards(right))
        self.assertEqual(signature(left), signature(right))

    def test_boards_off_exact_stage3b_signature_and_on_frozen(self):
        for underside in ("STEPPED_CLOSED", "SLOPED_CLOSED"):
            with self.subTest(underside=underside):
                off = prepare(self.fields(underside, left=False, right=False))
                on = prepare(self.fields(underside))
                self.assertFalse(boards(off[1]))
                self.assertEqual(off[1], on[1][:len(off[1])])
                self.assertEqual(signature(off[1]), signature(on[1]))

    def test_outer_corner_survives_equal2_and_equal4(self):
        for pattern in ("EQUAL_2", "EQUAL_4"):
            for direction in ("FORWARD", "REVERSE"):
                with self.subTest(pattern=pattern, direction=direction):
                    outer_is_right = direction == "FORWARD"
                    layout, parts, _mesh = prepare(
                        self.fields(left=not outer_is_right,
                                    right=outer_is_right),
                        direction=direction, pattern=pattern)
                    self.assertTrue(has_xy(boards(parts),
                                           layout.turn.outer_corner))

    def test_bf_patterns_and_arbitrary_angle(self):
        for pattern in ("BF_1", "BF_2"):
            with self.subTest(pattern=pattern):
                _layout, parts, _mesh = prepare(self.fields(), pattern=pattern)
                self.assertTrue(validate_mesh_fragments(boards(parts)))
        angle = math.radians(63.0)
        angled = ((0.0, 0.0), (0.0, 2.2),
                  (-2.2 * math.sin(angle), 2.2 + 2.2 * math.cos(angle)))
        layout, parts, _mesh = prepare(self.fields(), points=angled)
        self.assertTrue(has_xy(boards(parts), layout.turn.outer_corner))

    def test_sloped_corner_uses_walking_station_fraction(self):
        layout, parts, _mesh = prepare(
            self.fields(upper="SLOPED", left=False, right=True))
        frame = layout.turn
        cell_index = next(index for index, cell in enumerate(layout.cells)
                          if frame.outer_corner in cell.polygon)
        cell = layout.cells[cell_index]
        bounds = physical_cell_boundaries(
            cell, layout.ascent_direction, frame.inner_pivot)
        distance = lambda point: _board_outer_distance(
            frame, point, layout.ascent_direction)
        fraction = ((distance(frame.outer_corner) - distance(bounds.front[1]))
                    / (distance(bounds.rear[1]) - distance(bounds.front[1])))
        event_index = layout.straight_allocation[0] + cell_index + 1
        expected = (layout.base_z + (event_index - 1 + fraction)
                    * layout.actual_riser + 0.04)
        corner_tops = [vertex[2] for board in boards(parts)
                       for vertex in board.vertices
                       if math.dist(vertex[:2], frame.outer_corner) < 1.0e-9]
        self.assertTrue(any(abs(z - expected) < 1.0e-9 for z in corner_tops))

    def test_outer_lower_vertices_use_accepted_body_ring(self):
        for mode in ("STEPPED_CLOSED", "SLOPED_CLOSED"):
            with self.subTest(mode=mode):
                layout, parts, _mesh = prepare(
                    self.fields(underside=mode, left=False, right=True))
                bodies = [part for part in parts if part.part_type == "UNDERBODY"]
                board_vertices = {vertex for board in boards(parts)
                                  for vertex in board.vertices}
                for index, cell in enumerate(layout.cells):
                    rear = winder_tread_rear_outer_authority(
                        layout, 0, layout.cells, index)
                    footprint = winder_underbody_support_footprint(
                        layout, 0, cell, rear)
                    event_index = layout.straight_allocation[0] + index + 1
                    lower = layout.base_z + (event_index - 1) * layout.actual_riser
                    exterior = [point for point in footprint if
                                _canonical_outer_station(layout.turn, point) is not None
                                and any(math.dist(point, vertex[:2]) < 1.0e-9
                                        for body in bodies
                                        for vertex in body.vertices
                                        if abs(vertex[2] - lower) < 1.0e-9)]
                    self.assertGreaterEqual(len(exterior), 2)
                    self.assertTrue(all((point[0], point[1], lower)
                                        in board_vertices for point in exterior))

    def test_mirrored_turn_outer_side_is_left(self):
        mirrored = ((0.0, 0.0), (0.0, 2.2), (2.2, 2.2))
        layout, parts, _mesh = prepare(
            self.fields(left=True, right=False), points=mirrored)
        self.assertLess(layout.turn.theta, 0.0)
        self.assertTrue(has_xy(boards(parts), layout.turn.outer_corner))

    def assert_inner_join(self, points=L, direction="FORWARD", pattern="EQUAL_3",
                          underside="STEPPED_CLOSED", upper="STEPPED",
                          reveal_mm=40, thickness_mm=18, width_mm=900,
                          base_z_mm=0, floor_to_floor_mm=2800, riser_count=16):
        incoming_plan = (points[1][0] - points[0][0],
                         points[1][1] - points[0][1])
        outgoing_plan = (points[2][0] - points[1][0],
                         points[2][1] - points[1][1])
        turns_left = (incoming_plan[0] * outgoing_plan[1]
                      - incoming_plan[1] * outgoing_plan[0]) > 0.0
        inner_left = turns_left == (direction == "FORWARD")
        fields = replace(self.fields(underside, upper, left=inner_left,
                                     right=not inner_left),
                         side_board_reveal_mm=reveal_mm,
                         side_board_thickness_mm=thickness_mm)
        layout, parts, _mesh = prepare(
            fields, points=points, direction=direction, pattern=pattern,
            width_mm=width_mm, base_z_mm=base_z_mm,
            floor_to_floor_mm=floor_to_floor_mm, riser_count=riser_count)
        inner_boards = boards(parts)
        self.assertEqual(len(inner_boards), 2)  # Exactly the two Straight flights.
        self.assertTrue(validate_mesh_fragments(inner_boards))
        frame = layout.turn
        pivot = frame.inner_pivot
        incoming_direction = (frame.incoming if direction == "FORWARD" else
                              tuple(-value for value in frame.outgoing))
        outgoing_direction = (frame.outgoing if direction == "FORWARD" else
                              tuple(-value for value in frame.incoming))
        first_count = layout.straight_allocation[
            0 if direction == "FORWARD" else -1]
        exit_z = (layout.base_z + (first_count + len(layout.cells))
                  * layout.actual_riser)
        thickness = thickness_mm / 1000.0
        sign = 1 if inner_left else -1
        for board, axis in zip(inner_boards,
                               (incoming_direction, outgoing_direction)):
            normal = (-axis[1], axis[0])
            for vertex in board.vertices:
                delta = (vertex[0] - pivot[0], vertex[1] - pivot[1])
                lateral = delta[0] * normal[0] + delta[1] * normal[1]
                self.assertTrue(min(abs(lateral),
                                    abs(lateral - sign * thickness)) < 2.0e-8)
        incoming, outgoing = inner_boards
        self.assertAlmostEqual(max(v[2] for v in incoming.vertices), exit_z,
                               delta=1.0e-9)
        self.assertAlmostEqual(min(v[2] for v in outgoing.vertices), exit_z,
                               delta=1.0e-9)
        def station(vertex, axis):
            return ((vertex[0] - pivot[0]) * axis[0]
                    + (vertex[1] - pivot[1]) * axis[1])
        outgoing_stations = [station(v, outgoing_direction)
                             for v in outgoing.vertices]
        self.assertAlmostEqual(min(outgoing_stations), 0.0, delta=2.0e-8)
        self.assertTrue(any(abs(s) < 2.0e-8 for s in outgoing_stations))
        # The incoming top spans the pivot station; the outgoing lower face
        # starts there at precisely the same elevation, on both board sides.
        for lateral_target in (0.0, sign * thickness):
            cap_stations = [station(v, incoming_direction)
                            for v in incoming.vertices
                            if abs(v[2] - exit_z) < 1.0e-9
                            and abs((v[0] - pivot[0]) * -incoming_direction[1]
                                    + (v[1] - pivot[1]) * incoming_direction[0]
                                    - lateral_target) < 2.0e-8]
            self.assertLess(min(cap_stations), -1.0e-6)
            self.assertGreater(max(cap_stations), 1.0e-6)
            self.assertTrue(any(abs(station(v, outgoing_direction)) < 2.0e-8
                                and abs(v[2] - exit_z) < 1.0e-9
                                for v in outgoing.vertices))
        return layout, incoming, outgoing, incoming_direction, outgoing_direction

    def assert_inner_join_rotates(self, points, direction, underside, upper):
        reference = self.assert_inner_join(points, direction,
                                           underside=underside, upper=upper)
        angle = math.radians(17.0)
        rotated_points = tuple(rotate_xy(point, angle) for point in points)
        rotated = self.assert_inner_join(rotated_points, direction,
                                         underside=underside, upper=upper)
        for original, turned in zip(reference[1:3], rotated[1:3]):
            self.assertEqual((original.ordinal, original.faces,
                              len(original.vertices)),
                             (turned.ordinal, turned.faces,
                              len(turned.vertices)))
            for original_vertex, turned_vertex in zip(
                    original.vertices, turned.vertices):
                restored = rotate_xy(turned_vertex[:2], -angle)
                self.assertAlmostEqual(restored[0], original_vertex[0],
                                       delta=2.0e-8)
                self.assertAlmostEqual(restored[1], original_vertex[1],
                                       delta=2.0e-8)
                self.assertAlmostEqual(turned_vertex[2], original_vertex[2],
                                       delta=1.0e-10)

    def test_exact90_inner_join_rotates_in_both_directions_and_chiralities(self):
        mirrored = ((0.0, 0.0), (0.0, 2.2), (2.2, 2.2))
        for points in (L, mirrored):
            for direction in ("FORWARD", "REVERSE"):
                for underside in ("STEPPED_CLOSED", "SLOPED_CLOSED"):
                    for upper in ("STEPPED", "SLOPED"):
                        with self.subTest(points=points, direction=direction,
                                          underside=underside, upper=upper):
                            self.assert_inner_join_rotates(
                                points, direction, underside, upper)

    def test_arbitrary_angle_inner_join_rotates_forward_and_reverse(self):
        angle = math.radians(63.0)
        points = ((0.0, 0.0), (0.0, 2.2),
                  (-2.2 * math.sin(angle), 2.2 + 2.2 * math.cos(angle)))
        for direction in ("FORWARD", "REVERSE"):
            for upper in ("STEPPED", "SLOPED"):
                with self.subTest(direction=direction, upper=upper):
                    self.assert_inner_join_rotates(
                        points, direction, "STEPPED_CLOSED", upper)

    def test_inner_join_is_mirror_equivalent(self):
        mirrored = ((0.0, 0.0), (0.0, 2.2), (2.2, 2.2))
        for direction in ("FORWARD", "REVERSE"):
            with self.subTest(direction=direction):
                left = direction == "FORWARD"
                reference = boards(prepare(
                    self.fields(left=left, right=not left),
                    direction=direction)[1])
                reflected = boards(prepare(
                    self.fields(left=not left, right=left),
                    points=mirrored, direction=direction)[1])
                self.assertEqual(len(reference), len(reflected))
                for a, b in zip(reference, reflected):
                    self.assertEqual(len(a.vertices), len(b.vertices))
                    for vertex in a.vertices:
                        target = (-vertex[0], vertex[1], vertex[2])
                        self.assertTrue(any(math.dist(target, other) < 2.0e-8
                                            for other in b.vertices))

    def test_inner_join_all_patterns_have_only_straight_owners(self):
        for pattern in ("EQUAL_2", "EQUAL_3", "EQUAL_4", "BF_1", "BF_2"):
            for direction in ("FORWARD", "REVERSE"):
                with self.subTest(pattern=pattern, direction=direction):
                    self.assert_inner_join(pattern=pattern, direction=direction)

    def test_inner_join_reveal_is_parametric_but_start_plane_is_fixed(self):
        for upper in ("STEPPED", "SLOPED"):
            for reveal_mm in (20, 40, 60):
                with self.subTest(upper=upper, reveal_mm=reveal_mm):
                    layout, incoming, outgoing, in_axis, out_axis = (
                        self.assert_inner_join(
                            upper=upper, reveal_mm=reveal_mm))
                    pivot = layout.turn.inner_pivot
                    exit_z = layout.base_z + (layout.straight_allocation[0]
                                              + len(layout.cells)) * layout.actual_riser
                    incoming_cap = [((v[0] - pivot[0]) * in_axis[0]
                                     + (v[1] - pivot[1]) * in_axis[1])
                                    for v in incoming.vertices
                                    if abs(v[2] - exit_z) < 1.0e-9]
                    self.assertTrue(any(abs(value + reveal_mm / 1000.0) < 2.0e-8
                                        for value in incoming_cap))
                    outgoing_stations = [((v[0] - pivot[0]) * out_axis[0]
                                          + (v[1] - pivot[1]) * out_axis[1])
                                         for v in outgoing.vertices]
                    self.assertAlmostEqual(min(outgoing_stations), 0.0,
                                           delta=2.0e-8)
                    run = layout.straight_runs[1]
                    count = layout.straight_allocation[1]
                    breakpoint = ((run / count if upper == "STEPPED" else run)
                                  - reveal_mm / 1000.0)
                    self.assertTrue(any(abs(value - breakpoint) < 2.0e-8
                                        for value in outgoing_stations))

    def test_inner_join_thickness_is_parametric(self):
        pivots = []
        widths = []
        for thickness_mm in (12, 18, 24):
            with self.subTest(thickness_mm=thickness_mm):
                layout, _incoming, _outgoing, _in_axis, _out_axis = (
                    self.assert_inner_join(thickness_mm=thickness_mm))
                pivots.append(layout.turn.inner_pivot)
                widths.append(layout.width)
        self.assertEqual(pivots, [pivots[0]] * len(pivots))
        self.assertEqual(widths, [widths[0]] * len(widths))

    def test_inner_terminal_follows_resolved_height_and_riser_count(self):
        self.assert_inner_join(width_mm=750, base_z_mm=100,
                               floor_to_floor_mm=3000, riser_count=17)

    def test_inner_outer_enable_matrix_preserves_each_owned_shape(self):
        inner = boards(prepare(self.fields(left=True, right=False))[1])
        outer = boards(prepare(self.fields(left=False, right=True))[1])
        layout, parts, _mesh = prepare(self.fields())
        both = boards(parts)
        self.assertEqual((len(inner), len(outer), len(both)), (2, 8, 10))
        shape = lambda fragment: (fragment.vertices, fragment.faces)
        self.assertEqual(Counter(map(shape, both)),
                         Counter(map(shape, inner + outer)))
        off_layout, off_parts, _mesh = prepare(
            self.fields(left=False, right=False))
        self.assertEqual(layout.rise_events, off_layout.rise_events)
        self.assertEqual(layout.straight_allocation,
                         off_layout.straight_allocation)
        self.assertEqual(signature(parts), signature(off_parts))

    def test_ordinary_u_middle_inner_board_uses_both_turn_contexts(self):
        specs = (TurnSpec("t1", "WINDER", "EQUAL_2"),
                 TurnSpec("t2", "WINDER", "EQUAL_4"))
        for direction in ("FORWARD", "REVERSE"):
            for upper in ("STEPPED", "SLOPED"):
                with self.subTest(direction=direction, upper=upper):
                    fields = self.fields(
                        upper=upper, left=direction == "REVERSE",
                        right=direction == "FORWARD")
                    layout, parts, _mesh = prepare(
                        fields, points=ORDINARY_U, direction=direction,
                        specs=specs)
                    inner = boards(parts)
                    self.assertEqual(len(inner), 3)
                    self.assertTrue(validate_mesh_fragments(inner))
                    first_turn, last_turn = (layout.turns if direction == "FORWARD"
                                             else tuple(reversed(layout.turns)))
                    start = first_turn.inner_pivot
                    end = last_turn.inner_pivot
                    axis = tuple((b - a) / math.dist(start, end)
                                 for a, b in zip(start, end))
                    station = lambda v: sum((v[i] - start[i]) * axis[i]
                                            for i in range(2))
                    self.assertAlmostEqual(
                        min(station(v) for v in inner[1].vertices), 0.0,
                        delta=2.0e-8)
                    first_count = layout.straight_allocation[
                        0 if direction == "FORWARD" else -1]
                    first_winders, second_winders = (
                        layout.winder_counts if direction == "FORWARD" else
                        tuple(reversed(layout.winder_counts)))
                    middle_count = layout.straight_allocation[1]
                    first_exit = layout.base_z + (
                        first_count + first_winders) * layout.actual_riser
                    second_exit = layout.base_z + (
                        first_count + first_winders + middle_count
                        + second_winders) * layout.actual_riser
                    self.assertAlmostEqual(
                        min(v[2] for v in inner[1].vertices), first_exit,
                        delta=1.0e-9)
                    self.assertAlmostEqual(
                        max(v[2] for v in inner[1].vertices), second_exit,
                        delta=1.0e-9)
                    self.assertAlmostEqual(
                        min(v[2] for v in inner[2].vertices), second_exit,
                        delta=1.0e-9)
    def outer_return_case(self, points=L, pattern="EQUAL_3", direction="FORWARD",
                          reveal_mm=40, thickness_mm=18, width_mm=900):
        incoming = (points[1][0] - points[0][0],
                    points[1][1] - points[0][1])
        outgoing = (points[2][0] - points[1][0],
                    points[2][1] - points[1][1])
        turns_left = incoming[0] * outgoing[1] - incoming[1] * outgoing[0] > 0
        outer_right = turns_left == (direction == "FORWARD")
        fields = replace(self.fields(left=not outer_right, right=outer_right),
                         side_board_reveal_mm=reveal_mm,
                         side_board_thickness_mm=thickness_mm)
        layout, parts, _mesh = prepare(fields, points=points, pattern=pattern,
                                       direction=direction, width_mm=width_mm)
        cells = (layout.cells if direction == "FORWARD" else
                 tuple(reversed(layout.cells)))
        base_count = 2  # One unchanged Straight board on each side of this L.
        for index, cell in enumerate(cells):
            support = winder_underbody_support_footprint(
                layout, 0, cell,
                winder_tread_rear_outer_authority(layout, 0, cells, index))
            base_count += len(_board_outer_points(
                layout.turn, support, direction)) - 1
        base = boards(parts)[:base_count]
        returns = boards(parts)[base_count:]
        self.assertTrue(validate_mesh_fragments(returns))
        # r2 base strips have vertical faces: their upper and lower plan
        # vertices coincide. The rejected r3 loft failed this assertion.
        for board in base[1:-1]:
            self.assertEqual(len(board.vertices), 8)
            self.assertEqual(tuple(v[:2] for v in board.vertices[:4]),
                             tuple(v[:2] for v in board.vertices[4:]))
        return layout, cells, base, returns

    def assert_outer_return_contract(self, points=L, pattern="EQUAL_3",
                                     direction="FORWARD", reveal_mm=40,
                                     thickness_mm=18, width_mm=900):
        layout, cells, base, returns = self.outer_return_case(
            points, pattern, direction, reveal_mm, thickness_mm, width_mm)
        frame = layout.turn
        reveal = reveal_mm / 1000.0
        event_start = layout.straight_allocation[
            0 if direction == "FORWARD" else -1]
        self.assertEqual(len({(min(v[2] for v in board.vertices),
                               max(v[2] for v in board.vertices))
                              for board in returns}), len(cells) - 1)
        for index, cell in enumerate(cells[1:], 1):
            bounds = physical_cell_boundaries(
                cell, direction, frame.inner_pivot)
            event = bounds.front[1]
            support = winder_underbody_support_footprint(
                layout, 0, cell,
                winder_tread_rear_outer_authority(layout, 0, cells, index))
            support_start = _board_outer_points(frame, support, direction)[0]
            event_station = _board_outer_distance(frame, event, direction)
            support_station = _board_outer_distance(
                frame, support_start, direction)
            top = layout.base_z + (event_start + index + 1) * layout.actual_riser
            low = top - layout.actual_riser + reveal
            high = top + reveal
            matching = [board for board in returns
                        if abs(min(v[2] for v in board.vertices) - low) < 1.0e-9
                        and abs(max(v[2] for v in board.vertices) - high) < 1.0e-9]
            self.assertTrue(matching, (pattern, direction, index))
            stations = [_board_outer_distance(frame, v[:2], direction)
                        for board in matching for v in board.vertices
                        if _canonical_outer_station(frame, v[:2]) is not None]
            self.assertAlmostEqual(min(stations), event_station - reveal,
                                   delta=2.0e-8)
            self.assertAlmostEqual(max(stations), support_station,
                                   delta=2.0e-8)
            self.assertGreater(support_station, event_station)
            self.assertLessEqual(max(stations) - min(stations),
                                 reveal + support_station - event_station + 2.0e-8)
            # The return rests on the lower r2 board and meets the upper one
            # at its unchanged body-support station.
            for z in (low, high):
                self.assertTrue(any(
                    math.dist(v[:2], support_start) < 2.0e-8
                    and abs(v[2] - z) < 1.0e-9
                    for board in base for v in board.vertices))
            outside_support = min(
                (v[:2] for board in matching for v in board.vertices[:4]
                 if _canonical_outer_station(frame, v[:2]) is None),
                key=lambda point: math.dist(point, support_start))
            for z in (low, high):
                self.assertTrue(any(
                    math.dist(v[:2], outside_support) < 2.0e-8
                    and abs(v[2] - z) < 1.0e-9
                    for board in base for v in board.vertices))
            corner = _board_outer_distance(
                frame, frame.outer_corner, direction)
            if min(stations) + 1.0e-9 < corner < max(stations) - 1.0e-9:
                self.assertGreaterEqual(len(matching), 2)
                self.assertTrue(any(v[:2] == frame.outer_corner
                                    for board in matching for v in board.vertices))
        return layout, base, returns

    def test_r2_outer_base_is_exact_and_return_is_separate(self):
        layout, base, returns = self.assert_outer_return_contract()
        self.assertEqual(len(layout.cells), 3)
        self.assertEqual(len(returns), 2)
        self.assertEqual(fragment_digest(base),
                         "ab63c55aef767d6fdc8c109a3798327edd7fe22b20334dab8662bc92de6fd101")
        self.assertEqual(fragment_digest(base + returns),
                         "8ac14f31d4e09e2b0e75cc9a132c6a83e84230a554c0e0c5d2627e94f8727edc")

    def test_runtime_width_750mm_retains_event_owned_returns(self):
        layout, base, returns = self.assert_outer_return_contract(width_mm=750)
        self.assertEqual(layout.width, 0.75)
        self.assertEqual(len(returns), 2)
        self.assertTrue(validate_mesh_fragments(base + returns))

    def test_return_heights_follow_resolved_base_and_riser(self):
        fields = self.fields(left=False, right=True)
        layout, parts, _mesh = prepare_turn_residential_geometry(
            L, "FORWARD", 100, 3000, 17, 750, 30, 12,
            fields=fields, point_ids=("p0", "t1", "p2"),
            winder_pattern="EQUAL_3")
        base_count = 2
        for index, cell in enumerate(layout.cells):
            support = winder_underbody_support_footprint(
                layout, 0, cell,
                winder_tread_rear_outer_authority(
                    layout, 0, layout.cells, index))
            base_count += len(_board_outer_points(
                layout.turn, support, "FORWARD")) - 1
        returns = boards(parts)[base_count:]
        self.assertEqual(len(returns), 2)
        for index, board in enumerate(returns, 1):
            top = layout.base_z + (layout.straight_allocation[0] + index + 1) * layout.actual_riser
            self.assertAlmostEqual(min(v[2] for v in board.vertices),
                                   top - layout.actual_riser + 0.04,
                                   delta=1.0e-9)
            self.assertAlmostEqual(max(v[2] for v in board.vertices),
                                   top + 0.04, delta=1.0e-9)

    def test_reveal_controls_return_projection_and_elevation(self):
        starts = []
        for reveal_mm in (20, 40, 60):
            with self.subTest(reveal_mm=reveal_mm):
                layout, _base, returns = self.assert_outer_return_contract(
                    reveal_mm=reveal_mm)
                frame = layout.turn
                first = min(_board_outer_distance(frame, v[:2], "FORWARD")
                            for v in returns[0].vertices
                            if _canonical_outer_station(frame, v[:2]) is not None)
                starts.append(first)
        self.assertAlmostEqual(starts[0] - starts[1], 0.020, delta=1.0e-9)
        self.assertAlmostEqual(starts[1] - starts[2], 0.020, delta=1.0e-9)

    def test_thickness_extends_return_outside_walking_width(self):
        starts = []
        for thickness_mm in (12, 18, 24):
            with self.subTest(thickness_mm=thickness_mm):
                layout, _base, returns = self.assert_outer_return_contract(
                    thickness_mm=thickness_mm)
                frame = layout.turn
                board = returns[0]
                inner = [v[:2] for v in board.vertices[:4]
                         if _canonical_outer_station(frame, v[:2]) is not None]
                outer = [v[:2] for v in board.vertices[:4]
                         if _canonical_outer_station(frame, v[:2]) is None]
                self.assertEqual((len(inner), len(outer)), (2, 2))
                starts.append(min(_board_outer_distance(
                    frame, point, "FORWARD") for point in inner))
                for point in inner:
                    self.assertAlmostEqual(min(math.dist(point, q)
                                               for q in outer),
                                           thickness_mm / 1000.0,
                                           delta=1.0e-9)
        self.assertAlmostEqual(max(starts) - min(starts), 0.0, delta=1.0e-9)

    def test_equal2_equal4_reverse_mirror_and_arbitrary_angle_returns(self):
        mirrored = ((0.0, 0.0), (0.0, 2.2), (2.2, 2.2))
        angle = math.radians(63.0)
        angled = ((0.0, 0.0), (0.0, 2.2),
                  (-2.2 * math.sin(angle), 2.2 + 2.2 * math.cos(angle)))
        for points, patterns in ((L, ("EQUAL_2", "EQUAL_4", "BF_1", "BF_2")),
                                 (mirrored, ("EQUAL_3",)),
                                 (angled, ("EQUAL_3",))):
            for pattern in patterns:
                for direction in ("FORWARD", "REVERSE"):
                    with self.subTest(points=points, pattern=pattern,
                                      direction=direction):
                        layout, base, _returns = self.assert_outer_return_contract(
                            points, pattern, direction)
                        self.assertTrue(has_xy(base, layout.turn.outer_corner))

    def test_outer_base_and_returns_rotate_together(self):
        angle = math.radians(17.0)
        for direction in ("FORWARD", "REVERSE"):
            with self.subTest(direction=direction):
                outer_right = direction == "FORWARD"
                fields = self.fields(left=not outer_right,
                                     right=outer_right)
                reference = boards(prepare(fields, direction=direction)[1])
                rotated = boards(prepare(
                    fields, points=tuple(rotate_xy(point, angle)
                                         for point in L),
                    direction=direction)[1])
                self.assertEqual(len(reference), len(rotated))
                for original, turned in zip(reference, rotated):
                    self.assertEqual(original.faces, turned.faces)
                    for a, b in zip(original.vertices, turned.vertices):
                        restored = rotate_xy(b[:2], -angle)
                        self.assertAlmostEqual(restored[0], a[0], delta=2.0e-8)
                        self.assertAlmostEqual(restored[1], a[1], delta=2.0e-8)
                        self.assertAlmostEqual(b[2], a[2], delta=1.0e-10)

    def test_tread_and_riser_keep_exact_r4_signatures_with_inner_join(self):
        for underside in ("STEPPED_CLOSED", "SLOPED_CLOSED"):
            for upper in ("STEPPED", "SLOPED"):
                with self.subTest(underside=underside, upper=upper):
                    _layout, parts, _mesh = prepare(
                        self.fields(underside, upper, left=True, right=False))
                    self.assertEqual(len(boards(parts)), 2)
                    self.assertEqual(fragment_digest(
                        part for part in parts if part.part_type == "TREAD"),
                        "cc7695fb5431c3b28e7955be4330523ee8b2c48d3e62dde2b7334f1186058cc9")
                    self.assertEqual(fragment_digest(
                        part for part in parts if part.part_type == "RISER"),
                        "59066dc7b8a461429af26d0515ec2d609694a059406b324d65869f1d6b1618b4")

    def test_sloped_outer_board_retains_exact_r2_signature(self):
        expected = {
            "STEPPED_CLOSED": "e7d6633ab21ef6962382a31ece3289226d9b9d5fcae791412e8668a4a2d588ea",
            "SLOPED_CLOSED": "769e8939b7af640141d979c3b6566d39bc0156589343519b682934c5e2d5b284",
        }
        for underside, outer_digest in expected.items():
            with self.subTest(underside=underside):
                _layout, parts, _mesh = prepare(
                    self.fields(underside, "SLOPED", left=False, right=True))
                self.assertEqual(fragment_digest(boards(parts)), outer_digest)
                _layout, both, _mesh = prepare(self.fields(underside, "SLOPED"))
                both_shapes = Counter((part.vertices, part.faces)
                                      for part in boards(both))
                self.assertEqual(len(boards(both)), len(boards(parts)) + 2)
                for part in boards(parts):
                    self.assertGreaterEqual(
                        both_shapes[(part.vertices, part.faces)], 1)

    def test_ordinary_two_turn_u(self):
        specs = (TurnSpec("t1", "WINDER", "EQUAL_2"),
                 TurnSpec("t2", "WINDER", "EQUAL_4"))
        layout, parts, _mesh = prepare(self.fields(), points=ORDINARY_U,
                                       specs=specs)
        self.assertNotEqual(layout.u_classification, "COMPACT_U")
        self.assertEqual(layout.winder_counts, (2, 4))
        self.assertTrue(boards(parts))
        self.assertTrue(validate_mesh_fragments(parts))

    def test_reverse_reassigns_outer_side(self):
        forward, _parts, _mesh = prepare(self.fields(), direction="FORWARD")
        reverse, _parts, _mesh = prepare(self.fields(), direction="REVERSE")
        self.assertTrue(has_xy(
            boards(prepare(self.fields(left=False, right=True),
                           direction="FORWARD")[1]),
            forward.turn.outer_corner))
        self.assertTrue(has_xy(
            boards(prepare(self.fields(left=True, right=False),
                           direction="REVERSE")[1]),
            reverse.turn.outer_corner))
        self.assertFalse(has_xy(
            boards(prepare(self.fields(left=True, right=False),
                           direction="FORWARD")[1]),
            forward.turn.outer_corner))

    def test_repeated_preparation_is_deterministic(self):
        first = prepare(self.fields())
        second = prepare(self.fields())
        self.assertEqual(first, second)

    def test_compact_u_is_deferred_atomically_when_boards_enabled(self):
        specs = (TurnSpec("t1", "WINDER", "EQUAL_3"),
                 TurnSpec("t2", "WINDER", "EQUAL_3"))
        with self.assertRaisesRegex(ScopeUnsupportedError,
                                    "Stage 3D deferred"):
            prepare(self.fields(), points=COMPACT_U, specs=specs)
        layout, parts, _mesh = prepare(points=COMPACT_U, specs=specs)
        self.assertEqual(layout.u_classification, "COMPACT_U")
        self.assertFalse(boards(parts))

    def test_board_fragments_are_finite_closed_and_positive(self):
        for direction in ("FORWARD", "REVERSE"):
            with self.subTest(direction=direction):
                _layout, parts, _mesh = prepare(
                    self.fields("SLOPED_CLOSED", "SLOPED"), direction=direction)
                self.assertTrue(validate_mesh_fragments(boards(parts)))
                self.assertTrue(all(math.isfinite(v)
                                    for board in boards(parts)
                                    for vertex in board.vertices for v in vertex))

    def test_schema4_landing_regression_identity(self):
        _layout, parts, mesh = prepare_multiflight_residential_geometry(
            ((0.0, 0.0), (3.0, 0.0), (3.0, 3.0)), "FORWARD",
            100, 2800, 16, 900, 30, 12,
            point_ids=("l0", "l1", "l2"), fields=ResidentialFields())
        digest = hashlib.sha256(repr(tuple(
            (part.part_type, part.ordinal, part.vertices, part.faces)
            for part in parts)).encode()).hexdigest()
        self.assertEqual((len(parts), len(mesh.vertices), len(mesh.faces)),
                         (39, 632, 726))
        self.assertEqual(digest,
                         "05f012f304fea49fc1ed218789077cde0027a2fe47645e8fbc5f5f94bc72665f")

    def test_positive_nosing_final_upper_arrival(self):
        layout, parts, _mesh = prepare(self.fields())
        ordinary_limit = 2 * (len(layout.rise_events) - 1)
        ordinary = tuple(part for part in parts
                         if part.part_type in ("TREAD", "RISER")
                         and part.ordinal <= ordinary_limit)
        self.assertEqual(len(ordinary), ordinary_limit)
        self.assertEqual(fragment_digest(ordinary),
                         "dbdc3dabcd23082db7fbd3f3d64c0518a9ae4a552fbcadd9e58f72225f155899")
        self.assertAlmostEqual(max(vertex[2] for vertex in
                                   ordinary[-2].vertices), 2.625)
        arrival = tuple(part for part in parts
                        if part.part_type in ("TREAD", "RISER")
                        and part.ordinal > ordinary_limit)
        self.assertEqual(tuple(part.part_type for part in arrival),
                         ("RISER", "TREAD"))
        riser, cap = arrival
        self.assertEqual((riser.ordinal, cap.ordinal),
                         (ordinary_limit + 1, ordinary_limit + 2))
        self.assertAlmostEqual(min(vertex[2] for vertex in riser.vertices),
                               layout.upper_arrival_z - layout.actual_riser)
        self.assertAlmostEqual(max(vertex[2] for vertex in riser.vertices),
                               layout.upper_arrival_z - layout.tread_thickness)
        self.assertAlmostEqual(min(vertex[2] for vertex in cap.vertices),
                               layout.upper_arrival_z - layout.tread_thickness)
        self.assertAlmostEqual(max(vertex[2] for vertex in cap.vertices),
                               layout.upper_arrival_z)
        self.assertEqual(len(layout.rise_events), 16)
        self.assertEqual(layout.rise_events[-1].owner, "UPPER_ARRIVAL")
        self.assertTrue(all(vertex[2] <= layout.upper_arrival_z + 1.0e-10
                            for part in parts if part.part_type != "SIDE_BOARD"
                            for vertex in part.vertices))

        # The final reference plane is the physical ascent destination.
        self.assert_arrival_plan(layout, riser, cap)

    def assert_arrival_plan(self, layout, riser, cap=None):
        points = layout.canonical_path
        start, end = ((points[-2].xy, points[-1].xy)
                      if layout.ascent_direction == "FORWARD" else
                      (points[1].xy, points[0].xy))
        direction = (end[0] - start[0], end[1] - start[1])
        length = math.hypot(*direction)
        direction = (direction[0] / length, direction[1] / length)
        station = lambda vertex: ((vertex[0] - end[0]) * direction[0]
                                  + (vertex[1] - end[1]) * direction[1])
        self.assertAlmostEqual(min(station(v) for v in riser.vertices), 0.0)
        self.assertAlmostEqual(max(station(v) for v in riser.vertices),
                               layout.riser_thickness)
        if cap is not None:
            self.assertAlmostEqual(min(station(v) for v in cap.vertices),
                                   -layout.nosing)
            self.assertAlmostEqual(max(station(v) for v in cap.vertices),
                                   layout.riser_thickness)

    def test_zero_nosing_arrival_has_only_full_height_riser(self):
        fields = replace(self.fields(), tread_front_overhang_mm=0.0)
        layout, parts, _mesh = prepare(fields)
        ordinary_limit = 2 * (len(layout.rise_events) - 1)
        arrival = tuple(part for part in parts
                        if part.part_type in ("TREAD", "RISER")
                        and part.ordinal > ordinary_limit)
        self.assertEqual(len(arrival), 1)
        self.assertEqual(arrival[0].part_type, "RISER")
        self.assertAlmostEqual(min(v[2] for v in arrival[0].vertices),
                               layout.upper_arrival_z - layout.actual_riser)
        self.assertAlmostEqual(max(v[2] for v in arrival[0].vertices),
                               layout.upper_arrival_z)
        self.assert_arrival_plan(layout, arrival[0])

    def test_reverse_arrival_uses_ascent_destination(self):
        layout, parts, _mesh = prepare(self.fields(), direction="REVERSE")
        ordinary_limit = 2 * (len(layout.rise_events) - 1)
        riser, cap = (part for part in parts
                      if part.part_type in ("TREAD", "RISER")
                      and part.ordinal > ordinary_limit)
        self.assert_arrival_plan(layout, riser, cap)
        self.assertAlmostEqual(max(v[2] for v in cap.vertices),
                               layout.upper_arrival_z)

    def test_upper_arrival_rotates_with_final_ascent_flight(self):
        angle = math.radians(17.0)
        for direction in ("FORWARD", "REVERSE"):
            for nosing in (0.0, 5.0):
                with self.subTest(direction=direction, nosing=nosing):
                    fields = replace(self.fields(), tread_front_overhang_mm=nosing)
                    original = prepare(fields, direction=direction)
                    rotated = prepare(fields,
                                      points=tuple(rotate_xy(point, angle)
                                                   for point in L),
                                      direction=direction)
                    cutoff = 2 * (len(original[0].rise_events) - 1)
                    arrivals = [tuple(part for part in case[1]
                                      if part.part_type in ("TREAD", "RISER")
                                      and part.ordinal > cutoff)
                                for case in (original, rotated)]
                    self.assertEqual(len(arrivals[0]), len(arrivals[1]))
                    for expected, actual in zip(*arrivals):
                        self.assertEqual((expected.part_type, expected.ordinal,
                                          expected.faces),
                                         (actual.part_type, actual.ordinal,
                                          actual.faces))
                        for a, b in zip(expected.vertices, actual.vertices):
                            xy = rotate_xy(b[:2], -angle)
                            self.assertAlmostEqual(xy[0], a[0], delta=2.0e-8)
                            self.assertAlmostEqual(xy[1], a[1], delta=2.0e-8)
                            self.assertAlmostEqual(b[2], a[2], delta=1.0e-10)

    def test_arrival_cap_uses_schema5_front_edge_modes(self):
        for mode in ("BEVEL", "ROUND"):
            with self.subTest(mode=mode):
                fields = replace(self.fields(), tread_front_edge_mode=mode,
                                 tread_front_edge_size_mm=3.0)
                layout, parts, _mesh = prepare(fields)
                cap = max((part for part in parts if part.part_type == "TREAD"),
                          key=lambda part: part.ordinal)
                self.assertGreater(len(cap.vertices), 8)
                self.assertTrue(validate_mesh_fragments((cap,)))
                self.assert_arrival_plan(layout, next(
                    part for part in parts if part.part_type == "RISER"
                    and part.ordinal == cap.ordinal - 1), cap)

    def test_r4_bodies_outer_base_and_returns_remain_exact(self):
        expected = {
            "STEPPED_CLOSED": (
                "8bee259a060052f36c0c1fd31c9930da726e18c949b88d0c0282fe983530293f",
                "ab63c55aef767d6fdc8c109a3798327edd7fe22b20334dab8662bc92de6fd101",
                "96f4a6f401dc932c567b6f8334e94c2009fe566aedd0ec0db4329ad4e17186d1",
                "8ac14f31d4e09e2b0e75cc9a132c6a83e84230a554c0e0c5d2627e94f8727edc"),
            "SLOPED_CLOSED": (
                "9ac142645660279282478b6a24dfa9152478feeb6a86d92643c3305b38459a21",
                "85a1151cce0f159af2e9b9f86de84f5ceef4d540aeafa4156407d1a32cac5bca",
                "96f4a6f401dc932c567b6f8334e94c2009fe566aedd0ec0db4329ad4e17186d1",
                "715e80f1e0b2c4612c3044ab0478e98baa7492f8da48ba8c5de98fca0cb4fbdc"),
        }
        for mode, (body_digest, base_digest, return_digest,
                   board_digest) in expected.items():
            with self.subTest(mode=mode):
                _layout, parts, _mesh = prepare(
                    self.fields(underside=mode, left=False, right=True))
                self.assertEqual(fragment_digest(
                    part for part in parts if part.part_type == "UNDERBODY"),
                    body_digest)
                self.assertEqual(fragment_digest(boards(parts)[:6]), base_digest)
                self.assertEqual(fragment_digest(boards(parts)[6:]), return_digest)
                self.assertEqual(fragment_digest(boards(parts)), board_digest)


if __name__ == "__main__":
    unittest.main()
