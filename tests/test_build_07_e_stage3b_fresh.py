"""Fresh Build 07-E Stage-3B visual sloped-body regressions."""

import hashlib
import math
import pathlib
import sys
import types
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).parents[1]
package = sys.modules.get("japanese_house_modeler")
if package is None:
    package = types.ModuleType("japanese_house_modeler")
    package.__path__ = [str(ROOT / "japanese_house_modeler")]
    sys.modules["japanese_house_modeler"] = package

from japanese_house_modeler.stair_residential import ResidentialFields
from japanese_house_modeler.stair_turn import (
    TurnSpec,
    canonical_turn_endpoint_z,
    physical_cell_boundaries,
    physical_winder_tread_polygon,
    polygon_area,
    prepare_turn_geometry,
    prepare_turn_residential_geometry,
    resolve_sloped_turn_stations,
    sloped_turn_lower_z_at_fraction,
    winder_riser_hidden_rear_outer,
)


L_POINTS = ((0.0, 0.0), (0.0, 2.2), (-2.2, 2.2))
L_IDS = ("p0", "turn", "p2")
U_POINTS = ((0.0, 0.0), (0.0, 2.2), (0.9, 2.2), (0.9, 0.0))
U_IDS = ("p0", "t1", "t2", "p3")
SLOPED = ResidentialFields(
    underside_mode="SLOPED_CLOSED", left_side_board_enabled=False,
    right_side_board_enabled=False, tread_front_overhang_mm=5.0)
STEPPED = ResidentialFields(
    underside_mode="STEPPED_CLOSED", left_side_board_enabled=False,
    right_side_board_enabled=False, tread_front_overhang_mm=5.0)


def _kwargs(points=L_POINTS, direction="FORWARD", ids=L_IDS, **extra):
    values = dict(
        points=points, ascent_direction=direction, base_z_mm=0,
        floor_to_floor_mm=2800, riser_count=16, stair_width_mm=900,
        tread_thickness_mm=30, riser_thickness_mm=12, point_ids=ids,
        winder_pattern="EQUAL_3")
    values.update(extra)
    return values


def _signature(fragments, roles=("TREAD", "RISER")):
    return tuple((part.part_type, part.ordinal, part.vertices, part.faces)
                 for part in fragments if part.part_type in roles)


class FreshStage3BSlopedBodyTests(unittest.TestCase):
    def prepare(self, **kwargs):
        return prepare_turn_residential_geometry(
            fields=SLOPED, **_kwargs(**kwargs))

    def assert_valid_body(self, fragments):
        bodies = tuple(part for part in fragments
                       if part.part_type == "UNDERBODY")
        self.assertTrue(bodies)
        for body in bodies:
            self.assertGreaterEqual(len(body.vertices), 6)
            self.assertGreaterEqual(len(body.faces), 5)
            self.assertTrue(all(math.isfinite(value)
                                for vertex in body.vertices for value in vertex))
            for face in body.faces:
                points = [body.vertices[index] for index in face]
                area_vector = [0.0, 0.0, 0.0]
                for a, b in zip(points, points[1:] + points[:1]):
                    area_vector[0] += (a[1] - b[1]) * (a[2] + b[2])
                    area_vector[1] += (a[2] - b[2]) * (a[0] + b[0])
                    area_vector[2] += (a[0] - b[0]) * (a[1] + b[1])
                self.assertGreater(math.sqrt(sum(v * v for v in area_vector)),
                                   1.0e-12)
        return bodies

    def assert_top_frozen(self, **kwargs):
        basic = prepare_turn_geometry(
            **_kwargs(**kwargs),
            tread_front_overhang_mm=SLOPED.tread_front_overhang_mm,
            tread_front_edge_mode=SLOPED.tread_front_edge_mode,
            tread_front_edge_size_mm=SLOPED.tread_front_edge_size_mm)[1]
        residential = self.prepare(**kwargs)[1]
        self.assertEqual(_signature(residential), _signature(basic))

    def assert_tread_extensions(self, layout, turn_index, nosing=0.005):
        canonical_cells = layout.turn_cells[turn_index]
        cells = (canonical_cells if layout.ascent_direction == "FORWARD"
                 else tuple(reversed(canonical_cells)))
        frame = layout.turns[turn_index]
        chain = (frame.entry_outer, frame.outer_corner, frame.exit_outer)
        for cell_index, cell in enumerate(cells):
            boundaries = physical_cell_boundaries(
                cell, layout.ascent_direction,
                frame.inner_pivot)
            rear_authority = (
                winder_riser_hidden_rear_outer(
                    cells[cell_index + 1], layout.ascent_direction,
                    frame.inner_pivot, layout.riser_thickness)
                if cell_index + 1 < len(cells) else None)
            physical = physical_winder_tread_polygon(
                cell, layout.ascent_direction,
                frame.inner_pivot, nosing, layout.riser_thickness,
                frame=frame, rear_outer_authority=rear_authority)
            centroid = tuple(sum(point[index] for point in cell.polygon)
                             / len(cell.polygon) for index in (0, 1))
            for boundary, distance in ((boundaries.front, nosing),
                                       (boundaries.rear,
                                        layout.riser_thickness)):
                pivot, outer = boundary
                ray = (outer[0] - pivot[0], outer[1] - pivot[1])
                length = math.hypot(*ray)
                ray = (ray[0] / length, ray[1] / length)
                signed = lambda point: (ray[0] * (point[1] - pivot[1])
                                        - ray[1] * (point[0] - pivot[0]))
                interior = 1.0 if signed(centroid) >= 0.0 else -1.0
                target = (1 if tuple(outer) == tuple(cell.polygon[1])
                          else len(cell.polygon) - 1)
                self.assertAlmostEqual(
                    interior * signed(physical[target]), -distance)
                self.assertTrue(any(
                    abs((end[0] - start[0])
                        * (physical[target][1] - start[1])
                        - (end[1] - start[1])
                        * (physical[target][0] - start[0])) <= 1e-12
                    for start, end in zip(chain, chain[1:])))
                if boundary == boundaries.rear and rear_authority is not None:
                    self.assertEqual(physical[target], rear_authority)
            self.assertEqual(physical[0], frame.inner_pivot)
            if frame.outer_corner in cell.polygon:
                self.assertIn(frame.outer_corner, physical)
            self.assertGreater(polygon_area(physical), 0.0)
            self.assertEqual(len(physical), len(set(physical)))
            self.assertTrue(all(math.hypot(b[0] - a[0], b[1] - a[1]) > 1e-9
                                for a, b in zip(
                                    physical, physical[1:] + physical[:1])))

    def test_equal3_forward_reverse_valid_underside_and_frozen_top(self):
        for direction in ("FORWARD", "REVERSE"):
            with self.subTest(direction=direction):
                _layout, fragments, mesh = self.prepare(direction=direction)
                bodies = self.assert_valid_body(fragments)
                self.assertTrue(all(role == "UNDERSIDE" for role in
                                    mesh.face_roles[-sum(len(p.faces)
                                                         for p in bodies):]))
                self.assert_top_frozen(direction=direction)

    def test_winder_tread_rear_support_extends_to_successor_side(self):
        for direction in ("FORWARD", "REVERSE"):
            with self.subTest(direction=direction):
                layout, fragments, _mesh = self.prepare(direction=direction)
                self.assert_tread_extensions(layout, 0)

                # The last ascent-local Winder rear outer point lies on the
                # hidden rear plane of the succeeding exact-90 Straight Riser.
                cells = (layout.turn_cells[0]
                         if direction == "FORWARD" else
                         tuple(reversed(layout.turn_cells[0])))
                final = cells[-1]
                boundary = physical_cell_boundaries(
                    final, direction, layout.turns[0].inner_pivot).rear
                physical = physical_winder_tread_polygon(
                    final, direction, layout.turns[0].inner_pivot, 0.005,
                    layout.riser_thickness, frame=layout.turns[0])
                target = (1 if tuple(boundary[1]) == tuple(final.polygon[1])
                          else len(final.polygon) - 1)
                if direction == "FORWARD":
                    start = layout.canonical_path[1].xy
                    toward = layout.turns[0].outgoing
                else:
                    start = layout.canonical_path[1].xy
                    toward = (-layout.turns[0].incoming[0],
                              -layout.turns[0].incoming[1])
                start = (start[0] + toward[0] * layout.turns[0].cutback,
                         start[1] + toward[1] * layout.turns[0].cutback)
                rear_plane = (start[0] + toward[0] * layout.riser_thickness,
                              start[1] + toward[1] * layout.riser_thickness)
                delta = (physical[target][0] - rear_plane[0],
                         physical[target][1] - rear_plane[1])
                self.assertAlmostEqual(delta[0] * toward[0]
                                       + delta[1] * toward[1], 0.0)

                self.assertTrue(all(math.isfinite(value)
                                    for part in fragments
                                    for vertex in part.vertices
                                    for value in vertex))

    def test_rear_support_rule_covers_patterns_angles_and_both_compact_turns(self):
        for pattern in ("BF_1", "BF_2"):
            for direction in ("FORWARD", "REVERSE"):
                with self.subTest(pattern=pattern, direction=direction):
                    layout = self.prepare(
                        winder_pattern=pattern, direction=direction)[0]
                    self.assert_tread_extensions(layout, 0)

        angle = math.radians(63.0)
        points = ((0.0, 0.0), (0.0, 2.2),
                  (-2.2 * math.sin(angle), 2.2 + 2.2 * math.cos(angle)))
        layout = self.prepare(points=points)[0]
        self.assert_tread_extensions(layout, 0)

        specs = (TurnSpec("t1", "WINDER", "EQUAL_3"),
                 TurnSpec("t2", "WINDER", "EQUAL_3"))
        for direction in ("FORWARD", "REVERSE"):
            layout = self.prepare(
                points=U_POINTS, ids=U_IDS, turn_specs=specs,
                direction=direction)[0]
            self.assertEqual(layout.u_classification, "COMPACT_U")
            self.assert_tread_extensions(layout, 0)
            self.assert_tread_extensions(layout, 1)

    def test_straight_uses_sloped_profile_and_preserves_finish_setback(self):
        layout, fragments, _mesh = self.prepare()
        bodies = tuple(p for p in fragments if p.part_type == "UNDERBODY")
        first = bodies[0]
        path = layout.canonical_path
        direction = (path[1].xy[0] - path[0].xy[0],
                     path[1].xy[1] - path[0].xy[1])
        length = math.hypot(*direction)
        direction = (direction[0] / length, direction[1] / length)
        station = lambda v: ((v[0] - path[0].xy[0]) * direction[0]
                             + (v[1] - path[0].xy[1]) * direction[1])
        self.assertAlmostEqual(min(station(v) for v in first.vertices), 0.012)
        tread = next(p for p in fragments if p.part_type == "TREAD")
        self.assertAlmostEqual(min(station(v) for v in tread.vertices), -0.005)
        lower = sorted({round(v[2], 9) for v in first.vertices})
        self.assertGreater(len(lower), 2)

    def test_winder_contact_is_tread_owned_and_uses_stage3a_setback(self):
        for direction in ("FORWARD", "REVERSE"):
            with self.subTest(direction=direction):
                layout, fragments, _mesh = self.prepare(direction=direction)
                treads = tuple(part for part in fragments
                               if part.part_type == "TREAD")
                winder_treads = tuple(
                    tread for tread, event in zip(treads, layout.rise_events)
                    if event.owner == "WINDER_TREAD")
                bodies = tuple(part for part in fragments
                               if part.part_type == "UNDERBODY")
                winder_bodies = bodies[-len(winder_treads):]
                cells = layout.turn_cells[0]
                ascent_cells = (cells if direction == "FORWARD"
                                else tuple(reversed(cells)))
                self.assertEqual(len(winder_bodies), len(winder_treads))

                for tread, body, cell in zip(
                        winder_treads, winder_bodies, ascent_cells):
                    tread_top = max(vertex[2] for vertex in tread.vertices)
                    tread_bottom = min(vertex[2] for vertex in tread.vertices)
                    self.assertAlmostEqual(
                        tread_top - tread_bottom, layout.tread_thickness)
                    body_top = max(vertex[2] for vertex in body.vertices)
                    self.assertEqual(body_top, tread_bottom)
                    self.assertTrue(all(vertex[2] <= tread_bottom
                                        for vertex in body.vertices))
                    self.assertTrue(any(vertex[2] < tread_bottom
                                        for vertex in body.vertices))

                    boundaries = physical_cell_boundaries(
                        cell, direction, layout.turns[0].inner_pivot)
                    origin, outer = boundaries.front
                    ray = (outer[0] - origin[0], outer[1] - origin[1])
                    length = math.hypot(*ray)
                    ray = (ray[0] / length, ray[1] / length)
                    centroid = tuple(sum(point[index]
                                         for point in cell.polygon)
                                     / len(cell.polygon) for index in (0, 1))
                    cross = lambda point: (ray[0] * (point[1] - origin[1])
                                           - ray[1] * (point[0] - origin[0]))
                    side = 1.0 if cross(centroid) >= 0.0 else -1.0
                    self.assertTrue(all(
                        side * cross(vertex) >= layout.riser_thickness - 1e-6
                        for vertex in body.vertices))

                    # PR #39 used a constant closure-depth ribbon.  The new
                    # lower ring varies while every upper vertex is owned by
                    # the one horizontal accepted tread underside.
                    lower_z = tuple(vertex[2] for vertex in body.vertices
                                    if vertex[2] < body_top)
                    self.assertTrue(any(
                        not math.isclose(value + 0.150, body_top,
                                         abs_tol=1e-9)
                        for value in lower_z))

    def test_adjacent_cells_reuse_one_lower_field_at_dividers(self):
        for direction in ("FORWARD", "REVERSE"):
            layout, _fragments, _mesh = self.prepare(direction=direction)
            canonical = canonical_turn_endpoint_z(direction, 0.6, 1.2)
            cells = layout.turn_cells[0]
            for lower_cell, upper_cell in zip(cells, cells[1:]):
                fraction = lower_cell.rear_fraction
                self.assertEqual(fraction, upper_cell.front_fraction)
                from_lower = sloped_turn_lower_z_at_fraction(
                    cells, canonical[0], canonical[1],
                    lower_cell.rear_fraction)
                from_upper = sloped_turn_lower_z_at_fraction(
                    cells, canonical[0], canonical[1],
                    upper_cell.front_fraction)
                self.assertEqual(from_lower, from_upper)

    def test_turn_station_authority_is_sloped_shared_and_pivot_relieved(self):
        layout, _fragments, _mesh = self.prepare()
        stations = resolve_sloped_turn_stations(layout, 0, 0.6, 1.2)
        self.assertGreaterEqual(len(stations), 4)
        self.assertEqual(stations[0].lower_z, 0.6)
        self.assertEqual(stations[-1].lower_z, 1.2)
        self.assertGreater(len({round(s.lower_z, 9) for s in stations}), 2)
        pivot = layout.turns[0].inner_pivot
        self.assertTrue(all(math.hypot(s.inner[0] - pivot[0],
                                      s.inner[1] - pivot[1]) > 1.0e-6
                            for s in stations))
        # Re-resolution is exact, so adjacent strips consume identical XYZ.
        self.assertEqual(stations,
                         resolve_sloped_turn_stations(layout, 0, 0.6, 1.2))

    def test_reverse_reuses_opposite_straight_endpoint_authorities(self):
        self.assertEqual(
            canonical_turn_endpoint_z("FORWARD", 0.6, 1.2), (0.6, 1.2))
        self.assertEqual(
            canonical_turn_endpoint_z("REVERSE", 0.6, 1.2), (1.2, 0.6))

        captured = {}
        original = resolve_sloped_turn_stations

        def capture(layout, turn_index, canonical_entry_z, canonical_exit_z):
            captured[layout.ascent_direction] = (
                canonical_entry_z, canonical_exit_z)
            return original(layout, turn_index, canonical_entry_z,
                            canonical_exit_z)

        module = "japanese_house_modeler.stair_turn.resolve_sloped_turn_stations"
        with mock.patch(module, side_effect=capture):
            _forward_layout, forward_fragments, _mesh = self.prepare()
            reverse_layout, reverse_fragments, _mesh = self.prepare(
                direction="REVERSE")

        forward_entry, forward_exit = captured["FORWARD"]
        reverse_entry, reverse_exit = captured["REVERSE"]
        self.assertLess(forward_entry, forward_exit)
        self.assertGreater(reverse_entry, reverse_exit)

        reverse_bodies = tuple(part for part in reverse_fragments
                               if part.part_type == "UNDERBODY")
        low_ascent_straight, high_ascent_straight = reverse_bodies[:2]
        # canonical frame.exit physically meets the first/low Straight during
        # REVERSE ascent; frame.entry meets the second/high Straight.  Exact
        # float membership proves the resolver reused those profile endpoints.
        self.assertIn(reverse_exit,
                      tuple(vertex[2] for vertex in low_ascent_straight.vertices))
        self.assertIn(reverse_entry,
                      tuple(vertex[2] for vertex in high_ascent_straight.vertices))
        stations = original(reverse_layout, 0, reverse_entry, reverse_exit)
        self.assertEqual(stations[0].lower_z, reverse_entry)
        self.assertEqual(stations[-1].lower_z, reverse_exit)
        self.assertGreater(stations[0].lower_z, stations[-1].lower_z)

        # The correction is endpoint mapping only; FORWARD output remains the
        # same deterministic production result obtained without the wrapper.
        self.assertEqual(forward_fragments, self.prepare()[1])

    def test_outer_corner_is_retained_as_geometry_only_station(self):
        angle = math.radians(63.0)
        points = ((0.0, 0.0), (0.0, 2.2),
                  (-2.2 * math.sin(angle), 2.2 + 2.2 * math.cos(angle)))
        layout, fragments, _mesh = self.prepare(points=points)
        stations = resolve_sloped_turn_stations(layout, 0, 0.5, 1.1)
        corner = layout.turns[0].outer_corner
        self.assertIn(corner, tuple(station.outer for station in stations))
        self.assert_valid_body(fragments)
        self.assert_top_frozen(points=points)

    def test_bf_patterns_are_supported(self):
        for pattern in ("BF_1", "BF_2"):
            with self.subTest(pattern=pattern):
                self.assert_valid_body(
                    self.prepare(winder_pattern=pattern)[1])

    def test_compact_u_has_two_turn_bodies_and_shared_transition(self):
        specs = (TurnSpec("t1", "WINDER", "EQUAL_2"),
                 TurnSpec("t2", "WINDER", "EQUAL_3"))
        layout, fragments, _mesh = self.prepare(
            points=U_POINTS, ids=U_IDS, turn_specs=specs)
        self.assertEqual(layout.u_classification, "COMPACT_U")
        bodies = self.assert_valid_body(fragments)
        self.assertGreaterEqual(len(bodies), 2 + sum(layout.winder_counts))
        # Both station sets reuse the one proportionally resolved transition.
        first = resolve_sloped_turn_stations(layout, 0, 0.4, 0.8)
        second = resolve_sloped_turn_stations(layout, 1, 0.8, 1.4)
        self.assertEqual(first[-1].lower_z, second[0].lower_z)
        self.assert_top_frozen(points=U_POINTS, ids=U_IDS, turn_specs=specs)

    def test_generation_is_deterministic(self):
        first = self.prepare()
        second = self.prepare()
        self.assertEqual(first[1], second[1])
        self.assertEqual(first[2], second[2])

    def test_stage3a_stepped_body_signature_is_unchanged(self):
        result = prepare_turn_residential_geometry(
            fields=STEPPED, **_kwargs())[1]
        body_signature = _signature(result, roles=("UNDERBODY",))
        digest = hashlib.sha256(repr(body_signature).encode()).hexdigest()
        self.assertEqual(
            digest,
            "a5f2ba90caf51cc9926bb574e7b5c2f0f1a46a179a83a087a46b815b244569ff")

    def test_stage3b_r2_sloped_underbody_signature_is_unchanged(self):
        result = self.prepare()[1]
        body_signature = _signature(result, roles=("UNDERBODY",))
        digest = hashlib.sha256(repr(body_signature).encode()).hexdigest()
        self.assertEqual(
            digest,
            "b5cdc5dbab80199907c656661a708b69be6402d16c07fba50999ddb5c8dc5314")

    def test_side_boards_remain_stage3c_deferred(self):
        with self.assertRaisesRegex(ValueError, "Stage 3C"):
            prepare_turn_residential_geometry(
                fields=ResidentialFields(underside_mode="SLOPED_CLOSED"),
                **_kwargs())


if __name__ == "__main__":
    unittest.main()
