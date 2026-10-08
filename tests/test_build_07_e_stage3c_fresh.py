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

from japanese_house_modeler.stair_geometry import (
    StairAxes, StairLayout, validate_mesh_fragments)
from japanese_house_modeler.stair_multiflight import prepare_multiflight_residential_geometry
from japanese_house_modeler.stair_residential import ResidentialFields
from japanese_house_modeler.stair_residential_geometry import (
    build_side_board_fragment, sloped_side_board_profile)
from japanese_house_modeler.stair_turn import (
    ScopeUnsupportedError, TurnSpec, _board_outer_distance,
    _board_outer_points,
    _canonical_outer_station,
    _winder_board_straight_local,
    physical_cell_boundaries, prepare_turn_residential_geometry,
    winder_tread_rear_outer_authority, winder_underbody_support_footprint,
)


L = ((0.0, 0.0), (0.0, 2.2), (-2.2, 2.2))
LONG_L = ((0.0, 0.0), (0.0, 3.6), (-3.6, 3.6))
RUNTIME_L = ((0.0, 0.0), (3.0154, 0.0), (3.0154, 2.9448))
COMPACT_U = ((0.0, 0.0), (0.0, 2.2), (0.9, 2.2), (0.9, 0.0))
ORDINARY_U = ((0.0, 0.0), (0.0, 2.2), (2.0, 2.2), (2.0, 0.0))
OFF = ResidentialFields(left_side_board_enabled=False,
                        right_side_board_enabled=False,
                        tread_front_overhang_mm=5.0)


def prepare(fields=None, points=L, direction="FORWARD", pattern="EQUAL_3",
            specs=None, width_mm=900, base_z_mm=0,
            floor_to_floor_mm=2800, riser_count=16, riser_thickness_mm=12):
    ids = ("p0", "t1", "p2") if len(points) == 3 else ("p0", "t1", "t2", "p3")
    return prepare_turn_residential_geometry(
        points, direction, base_z_mm, floor_to_floor_mm, riser_count,
        width_mm, 30, riser_thickness_mm,
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


def analytical_sloped_lines(layout, fields):
    """Read both ascent-local principal lines from residential profiles."""
    runs = layout.straight_runs
    counts = layout.straight_allocation
    if layout.ascent_direction == "REVERSE":
        runs, counts = tuple(reversed(runs)), tuple(reversed(counts))
    starts = (0, counts[0] + layout.winder_counts[0])
    lines = []
    for run, count, first_event in zip(runs, counts, starts):
        base = layout.base_z + first_event * layout.actual_riser
        local = StairLayout(
            (), (0.0, 0.0), (run, 0.0),
            StairAxes((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
            base, (count + 1) * layout.actual_riser,
            base + (count + 1) * layout.actual_riser,
            run, count + 1, count, layout.actual_riser, run / count,
            layout.width, layout.tread_thickness, layout.riser_thickness)
        upper = sloped_side_board_profile(local, fields).outer
        start, end = upper[1:3]
        lines.append((run, start,
                      (end[1] - start[1]) / (end[0] - start[0])))
    return tuple(lines)


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

    def test_sloped_corner_follows_outgoing_straight_principal_slope(self):
        fields = self.fields(upper="SLOPED", left=False, right=True)
        layout, parts, _mesh = prepare(
            fields)
        frame = layout.turn
        outgoing = analytical_sloped_lines(layout, fields)[1]
        remaining = math.dist(frame.outer_corner, frame.exit_outer)
        expected = (outgoing[1][1] + outgoing[2]
                    * (-remaining - outgoing[1][0]))
        corner_tops = [vertex[2] for board in boards(parts)
                       for vertex in board.vertices[len(board.vertices) // 2:]
                       if math.dist(vertex[:2], frame.outer_corner) < 1.0e-9]
        self.assertTrue(corner_tops)
        self.assertTrue(all(abs(z - expected) < 1.0e-9 for z in corner_tops))

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

    def test_sloped_outer_board_has_new_deterministic_signature(self):
        expected = {
            "STEPPED_CLOSED": "4f0b2466e150a04356630a8dd6ea253732cd258215c3147fbf2676964efd2b97",
            "SLOPED_CLOSED": "38e0e60242f4cbd72063988bb8b0c27f56557e5161af8c9deee4ed170f60426b",
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

    def test_r5_stepped_and_inner_board_signatures_are_frozen(self):
        expected = {
            ("STEPPED_CLOSED", "STEPPED"): (
                "ab2803107c6b77cccf7e7949850dfdcc54ca8722fe91bd12b8abb6cdeb8e3c2e",
                "8ac14f31d4e09e2b0e75cc9a132c6a83e84230a554c0e0c5d2627e94f8727edc",
                "83f5f148eed5c9c03f7722f554a6a155442ce1323ca5b01ec9a87b279c967a22"),
            ("STEPPED_CLOSED", "SLOPED"): (
                "1f9d5f34b867a88057c3a837f0ada12dd827dad865ba74a8d152dcc3488ef6b8",),
            ("SLOPED_CLOSED", "STEPPED"): (
                "0bc1fa2fba8ffcef8f84abd70411b26e5c80c3d1a74daa3ad00606d52cb0dfdd",
                "715e80f1e0b2c4612c3044ab0478e98baa7492f8da48ba8c5de98fca0cb4fbdc",
                "91c3a8547aba4e74bf7084d077bdd17439cd70d550fa6dccc746597e1033fff4"),
            ("SLOPED_CLOSED", "SLOPED"): (
                "7ac9c0663a77d94bcea96063b91fbaa0b077da98a39383e8ceb52ecdde731f24",),
        }
        for (underside, upper), digests in expected.items():
            with self.subTest(underside=underside, upper=upper):
                inner = boards(prepare(self.fields(
                    underside, upper, left=True, right=False))[1])
                self.assertEqual(fragment_digest(inner), digests[0])
                if upper == "STEPPED":
                    outer = boards(prepare(self.fields(
                        underside, upper, left=False, right=True))[1])
                    both = boards(prepare(self.fields(underside, upper))[1])
                    self.assertEqual(fragment_digest(outer), digests[1])
                    self.assertEqual(fragment_digest(both), digests[2])

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


class FreshStage3CSlopedOuterContinuityTests(unittest.TestCase):
    def case(self, points=LONG_L, direction="FORWARD", pattern="EQUAL_3",
             underside="SLOPED_CLOSED", reveal_mm=40, thickness_mm=18,
             riser_thickness_mm=12, floor_to_floor_mm=2800, riser_count=16,
             both=False, expected_mode="BRIDGE"):
        incoming = (points[1][0] - points[0][0],
                    points[1][1] - points[0][1])
        outgoing = (points[2][0] - points[1][0],
                    points[2][1] - points[1][1])
        turn_left = incoming[0] * outgoing[1] - incoming[1] * outgoing[0] > 0
        outer_right = turn_left == (direction == "FORWARD")
        fields = replace(OFF, underside_mode=underside,
                         side_board_mode="SLOPED",
                         left_side_board_enabled=both or not outer_right,
                         right_side_board_enabled=both or outer_right,
                         side_board_reveal_mm=reveal_mm,
                         side_board_thickness_mm=thickness_mm)
        layout, parts, _mesh = prepare(
            fields, points=points, direction=direction, pattern=pattern,
            riser_thickness_mm=riser_thickness_mm,
            floor_to_floor_mm=floor_to_floor_mm, riser_count=riser_count)
        all_boards = boards(parts)
        self.assertTrue(validate_mesh_fragments(all_boards))
        self.assertEqual(signature(parts), signature(prepare(
            replace(fields, left_side_board_enabled=False,
                    right_side_board_enabled=False),
            points=points, direction=direction, pattern=pattern,
            riser_thickness_mm=riser_thickness_mm,
            floor_to_floor_mm=floor_to_floor_mm,
            riser_count=riser_count)[1]))
        # For outer-only tests, the two Straight owners enclose Turn strips.
        if both:
            return layout, parts, fields, None
        turn_boards = all_boards[1:-1]
        self.assertTrue(turn_boards)
        chain = ((layout.turn.entry_outer, layout.turn.outer_corner,
                  layout.turn.exit_outer) if direction == "FORWARD" else
                 (layout.turn.exit_outer, layout.turn.outer_corner,
                  layout.turn.entry_outer))
        corner_s = math.dist(chain[0], chain[1])
        total_s = corner_s + math.dist(chain[1], chain[2])
        in_line, out_line = analytical_sloped_lines(layout, fields)
        in_z = lambda s: (in_line[1][1] + in_line[2]
                          * (in_line[0] + s - in_line[1][0]))
        out_z = lambda s: (out_line[1][1] + out_line[2]
                           * (s - total_s - out_line[1][0]))
        bridge_corner_z = out_z(corner_s)
        join_s = (bridge_corner_z - in_z(0.0)) / in_line[2]
        fallback = (join_s > corner_s + 1.0e-8
                    or join_s < in_line[1][0] - in_line[0] - 1.0e-8)
        self.assertEqual("GLOBAL" if fallback else "BRIDGE", expected_mode)
        global_pitch = (out_z(total_s) - in_z(0.0)) / total_s
        corner_z = (in_z(0.0) + global_pitch * corner_s if fallback
                    else bridge_corner_z)
        expected = (lambda s: in_z(0.0) + global_pitch * s) if fallback else (
            lambda s: (in_z(s) if s <= join_s else
                       corner_z if s <= corner_s else out_z(s)))
        if (layout.turn_specs[0].winder_pattern in ("EQUAL_2", "BF_2")
                and len(layout.turn_cells[0]) == 2):
            cells = (layout.turn_cells[0] if direction == "FORWARD" else
                     tuple(reversed(layout.turn_cells[0])))
            first = layout.straight_allocation[
                0 if direction == "FORWARD" else 1]
            physical = tuple((
                _board_outer_distance(
                    layout.turn, physical_cell_boundaries(
                        cell, direction, layout.turn.inner_pivot).front[1],
                    direction),
                layout.rise_events[first + index].top_z)
                for index, cell in enumerate(cells))
            if any(expected(station) < top - 1.0e-6
                   for station, top in physical):
                # The accepted r6 analytical bridge was too low at a real
                # RiseEvent. Keep the same principal pitches and move only
                # the two intersections of its single horizontal section.
                self.assertFalse(fallback)
                corner_z = max(bridge_corner_z,
                               *(top + reveal_mm / 1000.0
                                 for _station, top in physical))
                join_s = (corner_z - in_z(0.0)) / in_line[2]
                outgoing_join = (total_s
                                 + (corner_z - out_z(total_s)) / out_line[2])
                self.assertLessEqual(join_s, corner_s)
                self.assertGreaterEqual(outgoing_join, corner_s)
                expected = lambda s: (in_z(s) if s <= join_s else
                                      corner_z if s <= outgoing_join else
                                      out_z(s))
        samples = []
        for board in turn_boards:
            self.assertEqual(len(board.vertices), 8)
            for vertex in board.vertices[4:]:
                if _canonical_outer_station(layout.turn, vertex[:2]) is None:
                    continue
                s = _board_outer_distance(layout.turn, vertex[:2], direction)
                self.assertAlmostEqual(vertex[2], expected(s), delta=2.0e-9)
                samples.append((s, vertex[2]))
        self.assertTrue(samples)
        for s, z in samples:
            self.assertTrue(all(abs(z - other_z) < 2.0e-9
                                for other_s, other_z in samples
                                if abs(s - other_s) < 2.0e-9))
        self.assertTrue(has_xy(turn_boards, chain[1]))
        self.assertTrue(any(abs(s - corner_s) < 2.0e-9
                            and abs(z - corner_z) < 2.0e-9
                            for s, z in samples))
        if fallback:
            self.assertTrue(any(math.dist(v[:2], chain[0]) < 2.0e-8
                                and abs(v[2] - in_z(0.0)) < 2.0e-9
                                for v in all_boards[0].vertices))
            self.assertTrue(any(math.dist(v[:2], chain[2]) < 2.0e-8
                                and abs(v[2] - out_z(total_s)) < 2.0e-9
                                for v in all_boards[-1].vertices))
            self.assertTrue(any(abs(s - total_s) < 2.0e-8
                                and abs(z - out_z(total_s)) < 2.0e-9
                                for s, z in samples))
            stations = sorted({s for s, _z in samples
                               if -1.0e-8 <= s <= total_s + 1.0e-8})
            self.assertGreaterEqual(len(stations), 3)
            for a, b in zip(stations, stations[1:]):
                if b - a > 1.0e-8:
                    self.assertAlmostEqual(
                        (expected(b) - expected(a)) / (b - a),
                        global_pitch, delta=2.0e-8)
        elif join_s > layout.riser_thickness + 1.0e-8:
            self.assertTrue(any(abs(s - join_s) < 2.0e-8
                                and abs(z - corner_z) < 2.0e-9
                                for s, z in samples))
        else:
            axis = tuple((b - a) / math.dist(chain[0], chain[1])
                         for a, b in zip(chain[0], chain[1]))
            join_xy = (chain[0][0] + axis[0] * join_s,
                       chain[0][1] + axis[1] * join_s)
            self.assertTrue(has_xy((all_boards[0],), join_xy))
            self.assertTrue(any(abs(v[2] - corner_z) < 2.0e-9
                                for v in all_boards[0].vertices
                                if math.dist(v[:2], join_xy) < 2.0e-8))
        entry_support_s = layout.riser_thickness
        entry_xy = (chain[0][0] + (chain[1][0] - chain[0][0])
                    * entry_support_s / corner_s,
                    chain[0][1] + (chain[1][1] - chain[0][1])
                    * entry_support_s / corner_s)
        self.assertTrue(any(math.dist(v[:2], entry_xy) < 2.0e-8
                            and abs(v[2] - expected(entry_support_s)) < 2.0e-9
                            for v in all_boards[0].vertices))
        self.assertTrue(any(abs(s - entry_support_s) < 2.0e-8
                            and abs(z - expected(s)) < 2.0e-9
                            for s, z in samples))
        if fallback:
            exit_support_s = total_s + layout.riser_thickness
            exit_axis = tuple((b - a) / math.dist(chain[1], chain[2])
                              for a, b in zip(chain[1], chain[2]))
            exit_xy = tuple(chain[2][i] + exit_axis[i] * layout.riser_thickness
                            for i in range(2))
            self.assertTrue(any(math.dist(v[:2], exit_xy) < 2.0e-8
                                and abs(v[2] - expected(exit_support_s)) < 2.0e-9
                                for v in all_boards[-1].vertices))
            self.assertTrue(any(abs(s - exit_support_s) < 2.0e-8
                                and abs(z - expected(s)) < 2.0e-9
                                for s, z in samples))
        return layout, parts, fields, (join_s, corner_s, corner_z, samples,
                                       "GLOBAL" if fallback else "BRIDGE",
                                       in_z(0.0), out_z(total_s), global_pitch)

    def test_incoming_slope_bridge_outgoing_slope_both_undersides(self):
        for points, sign in ((L, -1), (LONG_L, 1)):
            for direction in ("FORWARD", "REVERSE"):
                for underside in ("STEPPED_CLOSED", "SLOPED_CLOSED"):
                    with self.subTest(points=points, direction=direction,
                                      underside=underside):
                        result = self.case(points=points, direction=direction,
                                           underside=underside)
                        join_s = result[3][0]
                        self.assertEqual(join_s > 0.0, sign > 0)
                        self.assertTrue(validate_mesh_fragments(boards(result[1])))

        # The Straight rear cap extends into the Turn. A join inside this
        # overlap must flatten the Straight cap as well as the Winder strip.
        near_entry = ((0.0, 0.0), (0.0, 2.27), (-2.27, 2.27))
        layout, _parts, _fields, geometry = self.case(points=near_entry)
        self.assertGreater(geometry[0], 0.0)
        self.assertLess(geometry[0], layout.riser_thickness)

    def test_reveal_riser_thickness_patterns_and_height_are_parametric(self):
        for reveal_mm in (20, 40, 60):
            with self.subTest(reveal_mm=reveal_mm):
                self.case(reveal_mm=reveal_mm)
        for thickness_mm in (12, 20):
            with self.subTest(riser_thickness_mm=thickness_mm):
                self.case(riser_thickness_mm=thickness_mm)
        for thickness_mm in (12, 18, 24):
            with self.subTest(side_board_thickness_mm=thickness_mm):
                _layout, parts, _fields, _geometry = self.case(
                    thickness_mm=thickness_mm)
                for board in boards(parts)[1:-1]:
                    ring = board.vertices[:4]
                    widths = (math.dist(ring[0][:2], ring[3][:2]),
                              math.dist(ring[1][:2], ring[2][:2]))
                    self.assertTrue(any(abs(width - thickness_mm / 1000.0)
                                        < 2.0e-8 for width in widths))
        for pattern in ("EQUAL_2", "EQUAL_3", "EQUAL_4", "BF_1", "BF_2"):
            with self.subTest(pattern=pattern):
                self.case(points=L if pattern == "EQUAL_4" else LONG_L,
                          pattern=pattern)
        self.case(floor_to_floor_mm=3000, riser_count=17)

    def test_outgoing_outer_straight_is_accepted_residential_board(self):
        for direction in ("FORWARD", "REVERSE"):
            with self.subTest(direction=direction):
                layout, parts, fields, _geometry = self.case(
                    direction=direction)
                path = layout.canonical_path
                origin = path[1].xy
                target = (path[2].xy if direction == "FORWARD"
                          else path[0].xy)
                length = math.dist(origin, target)
                axis = tuple((b - a) / length for a, b in zip(origin, target))
                start = tuple(origin[i] + axis[i] * layout.turn.cutback
                              for i in range(2))
                run = (layout.straight_runs[1] if direction == "FORWARD"
                       else layout.straight_runs[0])
                count = (layout.straight_allocation[1]
                         if direction == "FORWARD" else
                         layout.straight_allocation[0])
                first_event = (layout.straight_allocation[0]
                               if direction == "FORWARD" else
                               layout.straight_allocation[1])
                first_event += layout.winder_counts[0]
                base = layout.base_z + first_event * layout.actual_riser
                local = StairLayout(
                    (), start,
                    tuple(start[i] + axis[i] * run for i in range(2)),
                    StairAxes((*axis, 0.0), (-axis[1], axis[0], 0.0)),
                    base, (count + 1) * layout.actual_riser,
                    base + (count + 1) * layout.actual_riser,
                    run, count + 1, count, layout.actual_riser, run / count,
                    layout.width, layout.tread_thickness,
                    layout.riser_thickness)
                side = "RIGHT" if direction == "FORWARD" else "LEFT"
                accepted = build_side_board_fragment(local, side, fields)
                actual = boards(parts)[-1]
                self.assertEqual(actual.vertices, accepted.vertices)
                self.assertEqual(actual.faces, accepted.faces)

    def test_sloped_outer_repeated_preparation_is_deterministic(self):
        first = self.case()[1]
        second = self.case()[1]
        self.assertEqual(first, second)

    def test_equal4_long_l_uses_one_global_turn_slope(self):
        mirrored = tuple((-x, y) for x, y in LONG_L)
        for points in (LONG_L, mirrored):
            for direction in ("FORWARD", "REVERSE"):
                for underside in ("STEPPED_CLOSED", "SLOPED_CLOSED"):
                    with self.subTest(points=points, direction=direction,
                                      underside=underside):
                        layout, parts, _fields, geometry = self.case(
                            points=points, direction=direction,
                            pattern="EQUAL_4", underside=underside,
                            expected_mode="GLOBAL")
                        join_s, corner_s, _corner_z, samples = geometry[:4]
                        self.assertGreater(join_s, corner_s)
                        self.assertTrue(has_xy(boards(parts),
                                               layout.turn.outer_corner))
                        self.assertTrue(validate_mesh_fragments(boards(parts)))
                        self.assertTrue(all(math.isfinite(z) for _s, z in samples))
        # Both boards retain the same outer shapes and accepted non-board top.
        outer_layout, outer_parts, outer_fields, _geometry = self.case(
            pattern="EQUAL_4", expected_mode="GLOBAL")
        both_layout, both_parts, _both_fields, _ = self.case(
            pattern="EQUAL_4", expected_mode="GLOBAL", both=True)
        self.assertEqual(outer_layout.rise_events, both_layout.rise_events)
        self.assertEqual(signature(outer_parts), signature(both_parts))
        both_shapes = Counter((p.vertices, p.faces) for p in boards(both_parts))
        for part in boards(outer_parts):
            self.assertGreaterEqual(both_shapes[(part.vertices, part.faces)], 1)

    def test_equal4_global_fallback_rotates_with_plan(self):
        turn = math.radians(17.0)
        for direction in ("FORWARD", "REVERSE"):
            with self.subTest(direction=direction):
                reference = self.case(pattern="EQUAL_4", direction=direction,
                                      expected_mode="GLOBAL")[1]
                rotated = self.case(
                    points=tuple(rotate_xy(point, turn) for point in LONG_L),
                    pattern="EQUAL_4", direction=direction,
                    expected_mode="GLOBAL")[1]
                expected_boards, actual_boards = boards(reference), boards(rotated)
                self.assertEqual(len(expected_boards), len(actual_boards))
                for original, transformed in zip(expected_boards, actual_boards):
                    self.assertEqual(original.faces, transformed.faces)
                    for before, after in zip(original.vertices,
                                             transformed.vertices):
                        restored = rotate_xy(after[:2], -turn)
                        self.assertAlmostEqual(restored[0], before[0], delta=2.0e-8)
                        self.assertAlmostEqual(restored[1], before[1], delta=2.0e-8)
                        self.assertAlmostEqual(after[2], before[2], delta=2.0e-9)

    def test_mirror_arbitrary_angle_and_rotation(self):
        mirrored = tuple((-x, y) for x, y in LONG_L)
        angle = math.radians(63.0)
        angled = ((0.0, 0.0), (0.0, 2.2),
                  (-2.2 * math.sin(angle), 2.2 + 2.2 * math.cos(angle)))
        for points in (mirrored, angled):
            for direction in ("FORWARD", "REVERSE"):
                with self.subTest(points=points, direction=direction):
                    self.case(points=points, direction=direction)
        turn = math.radians(17.0)
        for direction in ("FORWARD", "REVERSE"):
            with self.subTest(direction=direction):
                reference = self.case(direction=direction)[1]
                rotated = self.case(
                    points=tuple(rotate_xy(point, turn) for point in LONG_L),
                    direction=direction)[1]
                a, b = boards(reference), boards(rotated)
                self.assertEqual(len(a), len(b))
                for original, transformed in zip(a, b):
                    self.assertEqual(original.faces, transformed.faces)
                    for before, after in zip(original.vertices,
                                             transformed.vertices):
                        restored = rotate_xy(after[:2], -turn)
                        self.assertAlmostEqual(restored[0], before[0], delta=2.0e-8)
                        self.assertAlmostEqual(restored[1], before[1], delta=2.0e-8)
                        self.assertAlmostEqual(after[2], before[2], delta=2.0e-9)

    def test_ordinary_u_two_turns_and_both_sides(self):
        points = ((0.0, 0.0), (0.0, 2.2), (2.2, 2.2), (2.2, 0.0))
        specs = (TurnSpec("t1", "WINDER", "EQUAL_2"),
                 TurnSpec("t2", "WINDER", "EQUAL_4"))
        for direction in ("FORWARD", "REVERSE"):
            with self.subTest(direction=direction):
                fields = replace(OFF, underside_mode="SLOPED_CLOSED",
                                 side_board_mode="SLOPED",
                                 left_side_board_enabled=True,
                                 right_side_board_enabled=True)
                layout, parts, _mesh = prepare(
                    fields, points=points, specs=specs,
                    direction=direction, riser_count=18)
                self.assertNotEqual(layout.u_classification, "COMPACT_U")
                self.assertEqual(layout.winder_counts, (2, 4))
                self.assertTrue(validate_mesh_fragments(boards(parts)))
                self.assertEqual(signature(parts), signature(prepare(
                    replace(fields, left_side_board_enabled=False,
                            right_side_board_enabled=False),
                    points=points, specs=specs, direction=direction,
                    riser_count=18)[1]))


class FreshStage3CTwoCellOuterClearanceTests(unittest.TestCase):
    """Physical two-cell tread clearance without changing r6 accepted shapes."""

    def case(self, pattern="EQUAL_2", direction="FORWARD", points=RUNTIME_L,
             *, underside="SLOPED_CLOSED", reveal_mm=40,
             thickness_mm=18, riser_thickness_mm=12,
             floor_to_floor_mm=2800, riser_count=16,
             board_mode="SLOPED", enabled="outer", width_mm=750):
        a = tuple(points[1][i] - points[0][i] for i in range(2))
        b = tuple(points[2][i] - points[1][i] for i in range(2))
        left_turn = a[0] * b[1] - a[1] * b[0] > 0.0
        outer_right = left_turn == (direction == "FORWARD")
        left_on = enabled == "both" or (enabled == "outer" and not outer_right)
        left_on |= enabled == "inner" and outer_right
        right_on = enabled == "both" or (enabled == "outer" and outer_right)
        right_on |= enabled == "inner" and not outer_right
        fields = replace(
            OFF, underside_mode=underside, side_board_mode=board_mode,
            left_side_board_enabled=left_on,
            right_side_board_enabled=right_on,
            side_board_reveal_mm=reveal_mm,
            side_board_thickness_mm=thickness_mm)
        layout, parts, _mesh = prepare(
            fields, points, direction, pattern, width_mm=width_mm,
            floor_to_floor_mm=floor_to_floor_mm, riser_count=riser_count,
            riser_thickness_mm=riser_thickness_mm)
        return layout, parts, fields

    def physical_constraints(self, layout):
        cells = (layout.turn_cells[0] if layout.ascent_direction == "FORWARD"
                 else tuple(reversed(layout.turn_cells[0])))
        first = layout.straight_allocation[
            0 if layout.ascent_direction == "FORWARD" else 1]
        result = []
        for index, cell in enumerate(cells):
            event = layout.rise_events[first + index]
            self.assertEqual(event.owner, "WINDER_TREAD")
            boundary = physical_cell_boundaries(
                cell, layout.ascent_direction, layout.turn.inner_pivot).front[1]
            result.append((_board_outer_distance(
                layout.turn, boundary, layout.ascent_direction), event.top_z))
        self.assertEqual(len(result), 2)
        self.assertEqual(len(layout.rise_events),
                         sum(layout.straight_allocation) + 3)
        return tuple(result)

    def turn_upper_segments(self, layout, parts):
        segments = []
        for board in boards(parts)[1:-1]:
            edge = tuple((_board_outer_distance(
                layout.turn, vertex[:2], layout.ascent_direction), vertex[2])
                for vertex in board.vertices[4:]
                if _canonical_outer_station(layout.turn, vertex[:2]) is not None)
            self.assertEqual(len(edge), 2)
            segments.append(tuple(sorted(edge)))
        self.assertTrue(segments)
        return tuple(segments)

    def upper_at(self, segments, station):
        values = []
        for (a, za), (b, zb) in segments:
            if a - 2.0e-8 <= station <= b + 2.0e-8:
                values.append(za + (zb - za) * (station - a) / (b - a))
        self.assertTrue(values, f"outer board has no upper at s={station}")
        for value in values[1:]:
            self.assertAlmostEqual(value, values[0], delta=2.0e-8)
        return values[0]

    def test_runtime_equal2_bf2_physical_clearance_and_profile(self):
        for pattern, event_station in (("EQUAL_2", .75),
                                       ("BF_2", math.sqrt(3) / 4)):
            with self.subTest(pattern=pattern):
                layout, parts, fields = self.case(pattern)
                self.assertTrue(validate_mesh_fragments(boards(parts)))
                constraints = self.physical_constraints(layout)
                station, top = constraints[1]
                self.assertAlmostEqual(station, event_station, delta=2.0e-9)
                self.assertAlmostEqual(top, 1.575, delta=2.0e-9)
                samples = self.turn_upper_segments(layout, parts)
                corrected = self.upper_at(samples, station)
                self.assertAlmostEqual(corrected, top + .04, delta=2.0e-9)
                self.assertGreaterEqual(corrected, top)
                self.assertTrue(has_xy(boards(parts), layout.turn.outer_corner))

                incoming, outgoing = analytical_sloped_lines(layout, fields)
                corner_s = math.dist(layout.turn.entry_outer,
                                     layout.turn.outer_corner)
                total_s = corner_s + math.dist(
                    layout.turn.outer_corner, layout.turn.exit_outer)
                entry_z = (incoming[1][1] + incoming[2]
                           * (incoming[0] - incoming[1][0]))
                exit_z = outgoing[1][1] - outgoing[2] * outgoing[1][0]
                old_b = exit_z + outgoing[2] * (corner_s - total_s)
                self.assertAlmostEqual(old_b, 1.4998996031, delta=2.0e-8)
                self.assertAlmostEqual(top - old_b, .0751003969,
                                       delta=2.0e-8)
                cells = layout.turn_cells[0]
                support = winder_underbody_support_footprint(
                    layout, 0, cells[1], winder_tread_rear_outer_authority(
                        layout, 0, cells, 1))
                support_s = _board_outer_distance(
                    layout.turn, _board_outer_points(
                        layout.turn, support, "FORWARD")[0], "FORWARD")
                old_support_z = (old_b if support_s <= corner_s else
                                 exit_z + outgoing[2] * (support_s - total_s))
                if pattern == "EQUAL_2":
                    # Blender's 68.16 mm sample is after Stage 3B's riser
                    # setback, while the physical divider itself is at B.
                    self.assertAlmostEqual(old_support_z, 1.5068338,
                                           delta=2.0e-7)
                else:
                    self.assertAlmostEqual(old_support_z, old_b,
                                           delta=2.0e-8)
                self.assertAlmostEqual(self.upper_at(samples, support_s),
                                       corrected, delta=2.0e-8)
                join_in = (corrected - entry_z) / incoming[2]
                join_out = total_s + (corrected - exit_z) / outgoing[2]
                self.assertLess(join_in, station + 2.0e-8)
                self.assertLess(join_in, corner_s)
                self.assertGreater(join_out, corner_s)
                self.assertLess(join_out, total_s - .04)
                self.assertAlmostEqual(self.upper_at(samples, join_in),
                                       corrected, delta=2.0e-8)
                self.assertAlmostEqual(self.upper_at(samples, join_out),
                                       corrected, delta=2.0e-8)
                self.assertAlmostEqual(self.upper_at(samples, corner_s),
                                       corrected, delta=2.0e-8)
                for (a, za), (b, zb) in samples:
                    self.assertGreaterEqual(zb + 2.0e-9, za)
                    slope = (zb - za) / (b - a)
                    self.assertTrue(any(abs(slope - target) < 2.0e-8
                                        for target in (incoming[2], 0.0,
                                                       outgoing[2])))

                # The incoming r6 terminal and outgoing residential Straight
                # remain exact; only Winder strips change for this fixture.
                path = layout.canonical_path
                count_in, count_out = layout.straight_allocation
                out_direction = (0.0, 1.0)
                outgoing_start = (path[1].xy[0],
                                  path[1].xy[1] + layout.turn.cutback)
                outgoing_local = _winder_board_straight_local(
                    layout, (outgoing_start, out_direction,
                             layout.straight_runs[1], count_out),
                    count_in + 2)
                actual = boards(parts)
                self.assertEqual(fragment_digest((actual[0],)),
                    "83c3590e93061f4564da75f099202c6d7bf9a2a357671ee630f0705ebb3deff0")
                straight_shapes = tuple((board.vertices, board.faces)
                                        for board in (actual[0], actual[-1]))
                self.assertEqual(hashlib.sha256(repr(straight_shapes).encode()).hexdigest(),
                    "4bdf6d37fcd208fe310c38f47e7d716ae29eb2472c28d9aab930a3c71d195841")
                accepted = build_side_board_fragment(
                    outgoing_local, "RIGHT", fields)
                self.assertEqual((actual[-1].vertices, actual[-1].faces),
                                 (accepted.vertices, accepted.faces))

    def test_r6_frozen_patterns_and_deferred_equal4(self):
        frozen = {
            "EQUAL_3": (
                "0d3fe6e4f521911561eba4fbfdbc1d36574c8031e49bfa7e1a74aeb98b4640bc",
                "79839da8fa3096bae1940d0c9d07a63cda1cf5caaa607ec09a57425096328750",
                "47f7bfbd00d836301ce58e887d7430822063f38ae849d4d65249c063f4683410"),
            "BF_1": (
                "e76a7724875efe4b9650653c922174635776c1c8becf6118de5c415e4de7f790",
                "6b877cd6f6e70b34a8078d8fc8d7243d17a5658f71a9349049c704952e2aa878",
                "75f83a25ea95d652d22346214ed8c0399827a2363bba5ff5ef23c23f208657bb"),
            "EQUAL_4": (
                "95d7282db58a037bb799040a709566b6a4fd3c722d5b1ca61a8df0a4ac09305a",
                "27c3efaa948005fc44811d44af6171cd26babdf9b4a42eba7ee3964851b5178f",
                "49669d44850083e5888802e1db041b53ea9e46f7e81b6959669a63943ad4a962"),
        }
        for pattern, digests in frozen.items():
            for enabled, expected in zip(("outer", "inner", "both"), digests):
                with self.subTest(pattern=pattern, enabled=enabled):
                    _layout, parts, _fields = self.case(
                        pattern, enabled=enabled)
                    self.assertEqual(fragment_digest(boards(parts)), expected)
        frozen_nonboard = {
            "EQUAL_3": "54f38db8ee141d6e70c463f245ec8451eff5f0ae0b42a45b9ba48bd328f0484b",
            "BF_1": "cad19557b91cc872407290da06113cfc81bad0fd2bd22788c32dc4d35a24c5a4",
            "EQUAL_4": "0ea1ac18fecf3849fdefdbe5f4dc33aab93e06744854060cbdd49f04028a218f",
        }
        for pattern, expected in frozen_nonboard.items():
            _layout, parts, _fields = self.case(pattern, enabled="both")
            self.assertEqual(fragment_digest(
                p for p in parts if p.part_type != "SIDE_BOARD"), expected)

        # BF_1 is also a two-cell pattern. Even this valid variant with an
        # r6 physical deficit remains frozen outside the approved r7 targets.
        bf1_points = ((0.0, 0.0), (2.2, 0.0), (2.2, 3.0))
        layout, parts, _fields = self.case(
            "BF_1", "REVERSE", bf1_points)
        station, top = self.physical_constraints(layout)[1]
        self.assertAlmostEqual(station, math.sqrt(3) / 4, delta=2.0e-9)
        self.assertAlmostEqual(top, 1.75, delta=2.0e-9)
        self.assertEqual(fragment_digest(boards(parts)),
            "e8c07a4c6ad64cd498144e804b16fbde29136db1c418c49ee2d60b1d554f4a45")

    def test_nonboard_stepped_and_inner_signatures_are_frozen(self):
        frozen = {
            "EQUAL_2": (
                "7c8a4c530b2218409bb941fe33cb3a3f93b70588b3e06ea2771b941190c64219",
                "6f81662b68360a4098b9fe5f625e5d9f7cff50d90dbf74ea5ef5926a89290f03",
                "da462c936b9b23301b6a091b01cf0a3d85a77691d982c115f68d604c5dcab565"),
            "BF_2": (
                "649d9702ea6d1805ec6615c81d44c74ea65430c48b9168b52b3bb6bbd951a5ff",
                "2648781cf095b06fd93381b0aff20cad65641264f834a6acc364d346dfe6f7d4",
                "c280ba1e4e0346319d0897d822e5adca96ee38cd62ca8eae4231754a6cf2f7fa"),
        }
        for pattern, (sloped_body, stepped_body, stepped_board) in frozen.items():
            for underside, expected_body in (
                    ("SLOPED_CLOSED", sloped_body),
                    ("STEPPED_CLOSED", stepped_body)):
                with self.subTest(pattern=pattern, underside=underside):
                    layout, parts, _fields = self.case(
                        pattern, underside=underside, enabled="both")
                    self.assertEqual(fragment_digest(
                        p for p in parts if p.part_type != "SIDE_BOARD"),
                        expected_body)
                    self.assertEqual(layout.straight_allocation, (7, 6))
                    self.assertEqual(len(layout.rise_events), 16)
                    self.assertEqual(layout.turn.outer_corner,
                                     (3.3904, -0.375))
                    arrival_riser = tuple(p for p in parts
                                          if p.part_type == "RISER"
                                          and p.ordinal == 31)
                    arrival_cap = tuple(p for p in parts
                                        if p.part_type == "TREAD"
                                        and p.ordinal == 32)
                    self.assertEqual(fragment_digest(arrival_riser),
                        "d46f0f22e2455b6380ef70d6041003c0cb6f5776a5edb2ca58c1be315162e732")
                    self.assertEqual(fragment_digest(arrival_cap),
                        "0c302887d4b432a26f967f0387c6fd414677e67cdf67c57b7070ea69ea7d62fb")
            _layout, inner, _fields = self.case(pattern, enabled="inner")
            self.assertEqual(fragment_digest(boards(inner)),
                             "6b877cd6f6e70b34a8078d8fc8d7243d17a5658f71a9349049c704952e2aa878")
            _layout, stepped, _fields = self.case(
                pattern, underside="STEPPED_CLOSED", board_mode="STEPPED")
            self.assertEqual(fragment_digest(boards(stepped)), stepped_board)

    def test_parameters_modes_and_board_enable_matrix(self):
        for pattern in ("EQUAL_2", "BF_2"):
            for direction in ("FORWARD", "REVERSE"):
                for reveal in (20, 40, 60):
                    for thickness in (12, 18, 24):
                        for riser_thickness in (12, 20):
                            for height, count in ((2800, 16), (3000, 17)):
                                for underside in ("STEPPED_CLOSED",
                                                  "SLOPED_CLOSED"):
                                    with self.subTest(pattern=pattern,
                                            direction=direction, reveal=reveal,
                                            thickness=thickness,
                                            riser_thickness=riser_thickness,
                                            height=height, count=count,
                                            underside=underside):
                                        layout, parts, _fields = self.case(
                                            pattern, direction,
                                            underside=underside,
                                            reveal_mm=reveal,
                                            thickness_mm=thickness,
                                            riser_thickness_mm=riser_thickness,
                                            floor_to_floor_mm=height,
                                            riser_count=count)
                                        self.assertTrue(validate_mesh_fragments(
                                            boards(parts)))
                                        station, top = self.physical_constraints(
                                            layout)[1]
                                        actual = self.upper_at(
                                            self.turn_upper_segments(layout, parts),
                                            station)
                                        self.assertGreaterEqual(actual + 2.0e-8,
                                                                top)
        for pattern in ("EQUAL_2", "BF_2"):
            variants = {}
            for enabled in ("both", "outer", "inner", "off"):
                layout, parts, _fields = self.case(pattern, enabled=enabled)
                variants[enabled] = parts
                self.assertTrue(validate_mesh_fragments(boards(parts)))
                self.assertEqual(len(layout.rise_events), 16)
            base = signature(variants["off"])
            self.assertTrue(all(signature(parts) == base
                                for parts in variants.values()))
            self.assertFalse(boards(variants["off"]))
            both_shapes = Counter((p.vertices, p.faces)
                                  for p in boards(variants["both"]))
            for enabled in ("outer", "inner"):
                for part in boards(variants[enabled]):
                    self.assertGreaterEqual(
                        both_shapes[(part.vertices, part.faces)], 1)

    def test_rotation_mirror_and_arbitrary_angle(self):
        angle = math.radians(63.0)
        arbitrary = ((0.0, 0.0), (0.0, 2.2),
                     (-2.2 * math.sin(angle),
                      2.2 + 2.2 * math.cos(angle)))
        mirrored = tuple((-x, y) for x, y in RUNTIME_L)
        turn = math.radians(17.0)
        for points, patterns, width in (
                (RUNTIME_L, ("EQUAL_2", "BF_2"), 750),
                (mirrored, ("EQUAL_2", "BF_2"), 750),
                (arbitrary, ("EQUAL_2",), 900)):
            for pattern in patterns:
                for direction in ("FORWARD", "REVERSE"):
                    with self.subTest(points=points, pattern=pattern,
                                      direction=direction):
                        original_layout, original, _ = self.case(
                            pattern, direction, points, width_mm=width)
                        turned_layout, transformed, _ = self.case(
                            pattern, direction,
                            tuple(rotate_xy(point, turn) for point in points),
                            width_mm=width)
                        self.assertEqual(original_layout.rise_events,
                                         turned_layout.rise_events)
                        before, after = boards(original), boards(transformed)
                        self.assertEqual(len(before), len(after))
                        for first, second in zip(before, after):
                            self.assertEqual(first.faces, second.faces)
                            for vertex, rotated in zip(first.vertices,
                                                       second.vertices):
                                restored = rotate_xy(rotated[:2], -turn)
                                self.assertAlmostEqual(restored[0], vertex[0],
                                                       delta=2.0e-8)
                                self.assertAlmostEqual(restored[1], vertex[1],
                                                       delta=2.0e-8)
                                self.assertAlmostEqual(rotated[2], vertex[2],
                                                       delta=2.0e-9)
                        station, top = self.physical_constraints(
                            original_layout)[1]
                        self.assertGreaterEqual(self.upper_at(
                            self.turn_upper_segments(original_layout, original),
                            station) + 2.0e-8, top)

    def test_unequal_legs_local_incoming_transition(self):
        points = ((0.0, 0.0), (3.0154, 0.0), (3.0154, 5.0))
        layout, parts, fields = self.case(
            "BF_2", points=points, reveal_mm=20)
        self.assertTrue(validate_mesh_fragments(boards(parts)))
        constraints = self.physical_constraints(layout)
        self.assertAlmostEqual(constraints[0][0], 0.0, delta=2.0e-8)
        station, top = constraints[1]
        self.assertGreaterEqual(self.upper_at(
            self.turn_upper_segments(layout, parts), station) + 2.0e-8, top)
        incoming_line = analytical_sloped_lines(layout, fields)[0]
        run = layout.straight_runs[0]
        original_entry = (incoming_line[1][1] + incoming_line[2]
                          * (run - incoming_line[1][0]))
        self.assertLess(original_entry + incoming_line[2] * station, top)
        straight = boards(parts)[0]
        ring = straight.vertices[:len(straight.vertices) // 2]
        upper_by_x = {}
        for x, _y, z in ring:
            upper_by_x[x] = max(z, upper_by_x.get(x, -math.inf))
        anchor_x = run - layout.straight_runs[0] / layout.straight_allocation[0]
        rear_x = run + layout.riser_thickness
        anchor_z = upper_by_x[anchor_x]
        rear_z = upper_by_x[rear_x]
        local_pitch = (rear_z - anchor_z) / (rear_x - anchor_x)
        self.assertGreater(local_pitch, incoming_line[2])
        new_entry = anchor_z + local_pitch * (run - anchor_x)
        self.assertGreaterEqual(new_entry + local_pitch * station + 2.0e-8,
                                top + .02)

    def test_hard_clearance_without_forcing_extra_incoming_bend(self):
        points = ((0.0, 0.0), (2.2, 0.0), (2.2, 5.0))
        layout, parts, fields = self.case(
            "BF_2", points=points, reveal_mm=20)
        station, top = self.physical_constraints(layout)[1]
        actual = self.upper_at(self.turn_upper_segments(layout, parts), station)
        self.assertAlmostEqual(actual, top, delta=2.0e-8)
        self.assertTrue(validate_mesh_fragments(boards(parts)))
        incoming = analytical_sloped_lines(layout, fields)[0]
        run = layout.straight_runs[0]
        original_entry = (incoming[1][1] + incoming[2]
                          * (run - incoming[1][0]))
        self.assertGreaterEqual(original_entry + incoming[2] * station, top)


if __name__ == "__main__":
    unittest.main()
