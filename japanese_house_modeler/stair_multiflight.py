"""Pure Build 07-D Stage 1 multi-point Stair resolution and geometry.

This module deliberately lives beside :mod:`stair_geometry`: the accepted
two-point resolver remains the compatibility authority for schema 1--3.
"""

from dataclasses import dataclass
import math
import uuid

from .stair_geometry import (
    MeshFragment, StairMeshData, assemble_stair_mesh, validate_mesh_fragments,
)


MULTIPOINT_SCHEMA_VERSION = 4
TURN_LANDING = "LANDING"
RISER_DISTRIBUTION_AUTO = "AUTO"
_EPSILON = 1.0e-6
_MM_PER_METRE = 1000.0
_BOX_FACES = (
    (0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
    (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),
)


@dataclass(frozen=True)
class PathPoint:
    point_id: str
    xy: tuple


@dataclass(frozen=True)
class FlightLayout:
    canonical_index: int
    start_xy: tuple
    end_xy: tuple
    forward: tuple
    left: tuple
    effective_run: float
    riser_count: int
    tread_count: int
    going: float
    start_z: float
    end_z: float
    actual_riser: float


@dataclass(frozen=True)
class LandingLayout:
    turn_point_id: str
    center_xy: tuple
    top_z: float
    thickness: float
    material_role: str = "TREAD"


@dataclass(frozen=True)
class MultiFlightLayout:
    canonical_path: tuple
    traversal_point_ids: tuple
    ascent_direction: str
    flights: tuple
    landing: LandingLayout
    allocation: tuple
    actual_riser: float
    base_z: float
    upper_arrival_z: float
    width: float
    tread_thickness: float
    riser_thickness: float

    @property
    def actual_riser_mm(self):
        return self.actual_riser * _MM_PER_METRE

    @property
    def upper_arrival_z_mm(self):
        return self.upper_arrival_z * _MM_PER_METRE


def generate_path_point_id():
    """Return identity generated only for an explicit schema-4 operation."""
    return str(uuid.uuid4())


def project_l_creation_candidate(p0, p1, raw_p2):
    """Project only a creation-time third click onto an exact right angle.

    Canonical validation intentionally does not call this helper: persisted or
    numerically edited paths must never be silently repaired.
    """
    converted = []
    for point in (p0, p1, raw_p2):
        if point is None or len(point) < 2:
            raise ValueError("L作成candidateのPath点を取得できません。")
        xy = (float(point[0]), float(point[1]))
        if not all(math.isfinite(value) for value in xy):
            raise ValueError("L作成candidate座標は有限値である必要があります。")
        converted.append(xy)
    start, turn, raw_end = converted
    dx, dy = turn[0] - start[0], turn[1] - start[1]
    incoming_length = math.hypot(dx, dy)
    if incoming_length <= _EPSILON:
        raise ValueError("L作成candidateの第1 Flightが短すぎます。")
    left = (-dy / incoming_length, dx / incoming_length)
    raw_delta = (raw_end[0] - turn[0], raw_end[1] - turn[1])
    signed_projection = raw_delta[0] * left[0] + raw_delta[1] * left[1]
    if abs(signed_projection) <= _EPSILON:
        raise ValueError("L作成candidateの曲がり方向または第2 Flight長を決定できません。")
    return (turn[0] + left[0] * signed_projection,
            turn[1] + left[1] * signed_projection)


def canonical_multi_path(points, point_ids=None):
    """Validate the Stage 1 three-point, right-angle L canonical path."""
    if points is None or len(points) < 2:
        raise ValueError("Multi-point Pathには2点以上が必要です。")
    if len(points) != 3:
        raise ValueError("Stage 1 L Pathは正確に3点である必要があります。")
    converted = []
    for point in points:
        if point is None or len(point) < 2:
            raise ValueError("Path点を取得できません。")
        xy = (float(point[0]), float(point[1]))
        if not all(math.isfinite(value) for value in xy):
            raise ValueError("Path点座標は有限値である必要があります。")
        converted.append(xy)
    vectors, lengths = [], []
    for first, second in zip(converted, converted[1:]):
        vector = (second[0] - first[0], second[1] - first[1])
        length = math.hypot(*vector)
        if length <= _EPSILON:
            raise ValueError("Pathに重複または短すぎる隣接点があります。")
        vectors.append(vector)
        lengths.append(length)
    dot = vectors[0][0] * vectors[1][0] + vectors[0][1] * vectors[1][1]
    cross = vectors[0][0] * vectors[1][1] - vectors[0][1] * vectors[1][0]
    tolerance = max(lengths[0] * lengths[1] * 1.0e-6, 1.0e-12)
    if abs(dot) > tolerance or abs(cross) <= tolerance:
        raise ValueError("Stage 1 Landingは90度のL Turnのみ対応します。")
    if point_ids is None:
        ids = tuple(generate_path_point_id() for _ in converted)
    else:
        ids = tuple(str(value) for value in point_ids)
        if len(ids) != len(converted) or any(not value for value in ids):
            raise ValueError("schema 4 Path point identityが不正です。")
        if len(set(ids)) != len(ids):
            raise ValueError("Path point identityは一意である必要があります。")
    return tuple(PathPoint(identity, xy) for identity, xy in zip(ids, converted))


def auto_distribute_risers(effective_runs, overall_riser_count):
    """Deterministically apportion risers by effective run (ties by order)."""
    runs = tuple(float(value) for value in effective_runs)
    if not runs or any(not math.isfinite(value) or value <= 0 for value in runs):
        raise ValueError("AUTO配分には正の有限なFlight長が必要です。")
    if isinstance(overall_riser_count, bool):
        raise ValueError("全体蹴上数は整数である必要があります。")
    numeric = float(overall_riser_count)
    if not math.isfinite(numeric) or not numeric.is_integer():
        raise ValueError("全体蹴上数は整数である必要があります。")
    total = int(numeric)
    if total < 2 * len(runs):
        raise ValueError("各Flightへ2蹴上を配分できません。")
    # k_i = r_i - 1.  Begin at the required one interval per flight and
    # repeatedly give the next interval to the currently largest going.
    # This is a deterministic discrete equalisation; index resolves ties.
    interval_total = total - len(runs)
    intervals = [1] * len(runs)
    for _unused in range(interval_total - len(runs)):
        index = min(range(len(runs)), key=lambda i: (-runs[i] / intervals[i], i))
        intervals[index] += 1
    result = tuple(value + 1 for value in intervals)
    if sum(result) != total:
        raise ValueError("AUTO蹴上配分を解決できません。")
    return result


def _positive_mm(value, label):
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{label}は正の有限値である必要があります。")
    return value / _MM_PER_METRE


def resolve_multiflight_layout(points, ascent_direction, base_z_mm,
                               floor_to_floor_mm, riser_count, stair_width_mm,
                               tread_thickness_mm, riser_thickness_mm, *,
                               point_ids=None, allocation=None):
    """Resolve one schema-4 L candidate completely without Scene mutation."""
    path = canonical_multi_path(points, point_ids)
    base_z = float(base_z_mm) / _MM_PER_METRE
    if not math.isfinite(base_z):
        raise ValueError("下端基準高さは有限値である必要があります。")
    floor_height = _positive_mm(floor_to_floor_mm, "階高")
    width = _positive_mm(stair_width_mm, "階段幅")
    tread_thickness = _positive_mm(tread_thickness_mm, "踏板厚")
    riser_thickness = _positive_mm(riser_thickness_mm, "蹴込み板厚")
    raw_lengths = tuple(math.hypot(b.xy[0] - a.xy[0], b.xy[1] - a.xy[1])
                        for a, b in zip(path, path[1:]))
    effective_runs = tuple(length - width / 2.0 for length in raw_lengths)
    if any(value <= _EPSILON for value in effective_runs):
        raise ValueError("Landing cutback後のFlight長が不足しています。")
    resolved = (auto_distribute_risers(effective_runs, riser_count)
                if allocation is None else tuple(int(value) for value in allocation))
    if (len(resolved) != 2 or any(value < 2 for value in resolved)
            or sum(resolved) != int(riser_count)):
        raise ValueError("保存されたAUTO蹴上配分が不正です。")
    actual_riser = floor_height / int(riser_count)
    if tread_thickness >= actual_riser:
        raise ValueError("踏板厚は実蹴上より小さくする必要があります。")
    if ascent_direction == "FORWARD":
        traversal = path
        traversal_indices = (0, 1)
    elif ascent_direction == "REVERSE":
        traversal = tuple(reversed(path))
        traversal_indices = (1, 0)
    else:
        raise ValueError("不明な上り方向です。")
    flights, cumulative = [], 0
    for position, (start, end) in enumerate(zip(traversal, traversal[1:])):
        canonical_index = traversal_indices[position]
        count = resolved[canonical_index]
        run = effective_runs[canonical_index]
        going = run / (count - 1)
        if riser_thickness >= going:
            raise ValueError("蹴込み板厚は踏面ピッチより小さくする必要があります。")
        raw_dx, raw_dy = end.xy[0] - start.xy[0], end.xy[1] - start.xy[1]
        raw_length = math.hypot(raw_dx, raw_dy)
        forward = (raw_dx / raw_length, raw_dy / raw_length)
        flight_start = start.xy
        flight_end = (end.xy[0] - forward[0] * width / 2.0,
                      end.xy[1] - forward[1] * width / 2.0)
        if position == 1:
            flight_start = (start.xy[0] + forward[0] * width / 2.0,
                            start.xy[1] + forward[1] * width / 2.0)
            flight_end = end.xy
        start_z = base_z + cumulative * actual_riser
        cumulative += count
        flights.append(FlightLayout(
            canonical_index, flight_start, flight_end, forward,
            (-forward[1], forward[0]), run, count, count - 1, going,
            start_z, base_z + cumulative * actual_riser, actual_riser))
    landing_top = flights[0].end_z
    landing = LandingLayout(path[1].point_id, path[1].xy, landing_top,
                            tread_thickness)
    return MultiFlightLayout(
        path, tuple(item.point_id for item in traversal), ascent_direction,
        tuple(flights), landing, resolved, actual_riser, base_z,
        base_z + floor_height, width, tread_thickness, riser_thickness)


def _oriented_box(centerline_start, forward, left, width, x0, x1, z0, z1,
                  part_type, ordinal):
    half = width / 2.0
    raw = []
    for z in (z0, z1):
        for y in (-half, half):
            for x in (x0, x1):
                raw.append((centerline_start[0] + forward[0] * x + left[0] * y,
                            centerline_start[1] + forward[1] * x + left[1] * y, z))
    order = (0, 1, 3, 2, 4, 5, 7, 6)
    return MeshFragment(part_type, ordinal, tuple(raw[i] for i in order), _BOX_FACES)


def build_multiflight_fragments(layout):
    """Build both flights and the landing as parts of one mesh candidate."""
    fragments, ordinal = [], 0
    for flight_index, flight in enumerate(layout.flights):
        for step in range(1, flight.tread_count + 1):
            ordinal += 1
            top = flight.start_z + step * layout.actual_riser
            fragments.append(_oriented_box(
                flight.start_xy, flight.forward, flight.left, layout.width,
                (step - 1) * flight.going, step * flight.going,
                top - layout.tread_thickness, top, "TREAD", ordinal))
        for step in range(1, flight.riser_count + 1):
            ordinal += 1
            final = step == flight.riser_count
            x = flight.effective_run if final else (step - 1) * flight.going
            bottom = flight.start_z + (step - 1) * layout.actual_riser
            top = (flight.end_z if final else
                   flight.start_z + step * layout.actual_riser - layout.tread_thickness)
            fragments.append(_oriented_box(
                flight.start_xy, flight.forward, flight.left, layout.width,
                x, x + layout.riser_thickness, bottom, top, "RISER", ordinal))
        if flight_index == 0:
            ordinal += 1
            # The right-angle incoming/outgoing axes form the nominal w x w slab.
            incoming = layout.flights[0].forward
            landing_left = (-incoming[1], incoming[0])
            center = layout.landing.center_xy
            fragments.append(_oriented_box(
                center, incoming, landing_left, layout.width,
                -layout.width / 2.0, layout.width / 2.0,
                layout.landing.top_z - layout.landing.thickness,
                layout.landing.top_z, "TREAD", ordinal))
    fragments = tuple(fragments)
    validate_mesh_fragments(fragments)
    return fragments


def prepare_multiflight_geometry(points, ascent_direction, base_z_mm,
                                 floor_to_floor_mm, riser_count, stair_width_mm,
                                 tread_thickness_mm, riser_thickness_mm, *,
                                 point_ids=None, allocation=None):
    """Prepare canonical layout, all parts, and one combined Mesh data result."""
    layout = resolve_multiflight_layout(
        points, ascent_direction, base_z_mm, floor_to_floor_mm, riser_count,
        stair_width_mm, tread_thickness_mm, riser_thickness_mm,
        point_ids=point_ids, allocation=allocation)
    fragments = build_multiflight_fragments(layout)
    mesh = assemble_stair_mesh(fragments)
    return layout, fragments, StairMeshData(mesh.vertices, mesh.faces, mesh.face_roles)
