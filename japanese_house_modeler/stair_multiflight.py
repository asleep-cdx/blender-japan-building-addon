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
RISER_DISTRIBUTION_MANUAL = "MANUAL"
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


@dataclass(frozen=True)
class FlightAllocation:
    """Riser count bound to one physical canonical segment."""
    start_point_id: str
    end_point_id: str
    riser_count: int


def segment_allocations(path, counts):
    path = tuple(path)
    counts = tuple(int(value) for value in counts)
    if len(counts) != len(path) - 1:
        raise ValueError("Flight allocation数がPath segment数と一致しません。")
    return tuple(FlightAllocation(a.point_id, b.point_id, count)
                 for a, b, count in zip(path, path[1:], counts))


def allocation_counts(path, allocations):
    """Resolve point-ID keyed allocation in canonical order."""
    mapping = {(item.start_point_id, item.end_point_id): int(item.riser_count)
               for item in allocations}
    try:
        return tuple(mapping[(a.point_id, b.point_id)] for a, b in zip(path, path[1:]))
    except KeyError as exc:
        raise ValueError("保存されたphysical Flight allocationがPathと一致しません。") from exc


def validate_manual_allocation(counts, overall_riser_count, flight_count=2):
    values = tuple(int(value) for value in counts)
    if len(values) != flight_count or any(value < 2 for value in values):
        raise ValueError("各FlightのMANUAL蹴上数は2以上である必要があります。")
    if sum(values) != int(overall_riser_count):
        raise ValueError("MANUAL蹴上数合計が全体蹴上数と一致しません。")
    return values


def switch_distribution_mode(current_mode, allocation, effective_runs,
                             overall_riser_count):
    """Pure AUTO/MANUAL transition; AUTO->MANUAL copies, reverse recalculates."""
    if current_mode == RISER_DISTRIBUTION_AUTO:
        return RISER_DISTRIBUTION_MANUAL, validate_manual_allocation(
            allocation, overall_riser_count, len(effective_runs))
    if current_mode == RISER_DISTRIBUTION_MANUAL:
        return RISER_DISTRIBUTION_AUTO, auto_distribute_risers(
            effective_runs, overall_riser_count)
    raise ValueError("Riser Distribution modeが不正です。")


def distribution_edit_initial_allocation(current_mode, auto_allocation,
                                         manual_allocation):
    """Resolve dialog authority exclusively from the currently active mode."""
    if current_mode == RISER_DISTRIBUTION_AUTO:
        selected = auto_allocation
    elif current_mode == RISER_DISTRIBUTION_MANUAL:
        selected = manual_allocation
    else:
        raise ValueError("Riser Distribution modeが不正です。")
    try:
        values = tuple(int(value) for value in selected)
    except (TypeError, ValueError) as exc:
        raise ValueError("Riser Distribution初期値が不正です。") from exc
    if not values:
        raise ValueError("Riser Distribution初期値がありません。")
    return values


def prepare_distribution_edit_candidate(snapshot, mode, manual_allocation):
    """Validate a distribution edit before returning a mutated copy."""
    candidate = dict(snapshot)
    old_mode = candidate["riser_distribution_mode"]
    if mode == RISER_DISTRIBUTION_MANUAL:
        values = validate_manual_allocation(
            manual_allocation, candidate["riser_count"])
        candidate["manual_riser_allocation"] = values
    elif mode == RISER_DISTRIBUTION_AUTO:
        if old_mode == RISER_DISTRIBUTION_MANUAL:
            candidate["auto_riser_allocation"] = None
    else:
        raise ValueError("Riser Distribution modeが不正です。")
    candidate["riser_distribution_mode"] = mode
    return candidate


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


def _flight_stair_layout(flight, layout):
    """Adapt a resolved Flight to accepted 07-C local-part helper input."""
    from .stair_geometry import StairAxes, StairLayout
    return StairLayout(
        tuple((flight.start_xy, flight.end_xy)), flight.start_xy, flight.end_xy,
        StairAxes((*flight.forward, 0.0), (*flight.left, 0.0)),
        flight.start_z, flight.end_z - flight.start_z, flight.end_z,
        flight.effective_run, flight.riser_count, flight.tread_count,
        flight.actual_riser, flight.going, layout.width,
        layout.tread_thickness, layout.riser_thickness)


def build_landing_side_board_fragments(layout, fields, start_ordinal=1,
                                       landing_soffit=None):
    """Build one non-overlapping L-shaped outer-perimeter board.

    The Landing top remains the canonical w x w square.  This polygon is only
    its exposed outer fascia: the incoming and outgoing legs and their corner
    have one owner, so no square filler or overlapping oriented boxes exist.
    """
    thickness = float(fields.side_board_thickness_mm) / _MM_PER_METRE
    reveal = float(fields.side_board_reveal_mm) / _MM_PER_METRE
    band = float(fields.side_board_band_width_mm) / _MM_PER_METRE
    if not all(math.isfinite(v) and v > 0.0 for v in (thickness, band)):
        raise ValueError("Landing Side Board寸法が不正です。")
    top = layout.landing.top_z + max(0.0, reveal)
    bottom = (max(layout.base_z, top - band) if landing_soffit is None
              else float(landing_soffit))
    if top - bottom <= _EPSILON:
        raise ValueError("Landing Side Board高さが不足しています。")
    incoming, outgoing = layout.flights
    turn_cross = (incoming.forward[0] * outgoing.forward[1]
                  - incoming.forward[1] * outgoing.forward[0])
    if abs(turn_cross) <= _EPSILON:
        raise ValueError("Landing Side Boardには非退化90度Turnが必要です。")
    # Left turn: local RIGHT is outside. Right turn: local LEFT is outside.
    outer_side = "RIGHT" if turn_cross > 0.0 else "LEFT"
    enabled = (fields.right_side_board_enabled if outer_side == "RIGHT"
               else fields.left_side_board_enabled)
    if not enabled:
        return ()
    half = layout.width / 2.0
    if turn_cross > 0.0:
        footprint = ((-half, -half - thickness),
                     (half + thickness, -half - thickness),
                     (half + thickness, half), (half, half),
                     (half, -half), (-half, -half))
    else:
        footprint = ((-half, half), (-half, half + thickness),
                     (half + thickness, half + thickness),
                     (half + thickness, -half), (half, -half),
                     (half, half))
    from .stair_geometry import validate_simple_polygon
    footprint = validate_simple_polygon(footprint)
    count = len(footprint)
    vertices = tuple(
        (layout.landing.center_xy[0] + incoming.forward[0] * x
         + incoming.left[0] * y,
         layout.landing.center_xy[1] + incoming.forward[1] * x
         + incoming.left[1] * y, z)
        for z in (bottom, top) for x, y in footprint)
    faces = (tuple(reversed(range(count))), tuple(range(count, count * 2)))
    faces += tuple((index, (index + 1) % count,
                    (index + 1) % count + count, index + count)
                   for index in range(count))
    fragment = MeshFragment(
        "SIDE_BOARD", int(start_ordinal), vertices, faces)
    validate_mesh_fragments((fragment,))
    return (fragment,)


def _clip_profile_x(profile, boundary, keep_greater):
    """Clip a closed XZ polygon at a vertical Landing boundary."""
    output = []
    points = tuple(profile)
    inside = ((lambda point: point[0] >= boundary - _EPSILON)
              if keep_greater else
              (lambda point: point[0] <= boundary + _EPSILON))
    for start, end in zip(points, points[1:] + points[:1]):
        start_in, end_in = inside(start), inside(end)
        if start_in:
            output.append(start)
        if start_in != end_in:
            dx = end[0] - start[0]
            if abs(dx) <= _EPSILON:
                continue
            t = (boundary - start[0]) / dx
            output.append((boundary, start[1] + t * (end[1] - start[1])))
    return tuple(output)


def _resolve_lower_outer_board_terminal(
        source_polygon, run_length, riser_thickness, turn_soffit_z):
    """Retain only the accepted terminal tail below Landing ownership."""
    from .stair_geometry import validate_simple_polygon
    left = float(run_length)
    right = left + float(riser_thickness)
    soffit = float(turn_soffit_z)
    clipped = list(_clip_profile_x(source_polygon, left, keep_greater=False))
    terminal_z = [point[1] for point in source_polygon
                  if math.isclose(point[0], right, abs_tol=_EPSILON)]
    if not terminal_z:
        raise ValueError("Lower Flight Side Board terminalを解決できません。")
    lower_right = min(terminal_z)
    pair = None
    for index, point in enumerate(clipped):
        following = clipped[(index + 1) % len(clipped)]
        if (math.isclose(point[0], left, abs_tol=_EPSILON)
                and math.isclose(following[0], left, abs_tol=_EPSILON)
                and point[1] < following[1]):
            pair = index
            break
    if pair is None:
        raise ValueError("Lower Flight Side Board clip境界が不正です。")
    lower_left, upper_left = clipped[pair], clipped[pair + 1]
    if not lower_right < soffit < upper_left[1]:
        raise ValueError("Lower Flight Side Board ownership高さが不正です。")
    clipped[pair:pair + 2] = (
        lower_left, (right, lower_right), (right, soffit),
        (left, soffit), upper_left)
    return validate_simple_polygon(clipped)


def _clip_profile_z(profile, boundary, keep_greater):
    """Clip a closed XZ polygon against one horizontal line."""
    output = []
    points = tuple(profile)
    inside = ((lambda point: point[1] >= boundary - _EPSILON)
              if keep_greater else
              (lambda point: point[1] <= boundary + _EPSILON))
    for start, end in zip(points, points[1:] + points[:1]):
        start_in, end_in = inside(start), inside(end)
        if start_in:
            output.append(start)
        if start_in != end_in:
            dz = end[1] - start[1]
            if abs(dz) <= _EPSILON:
                continue
            parameter = (boundary - start[1]) / dz
            output.append((start[0] + parameter * (end[0] - start[0]),
                           boundary))
    return tuple(output)


def _resolve_upper_start_reveal(
        source_polygon, reveal, reveal_floor_z):
    """Restore only accepted x<0 profile area above Landing ownership."""
    from .stair_geometry import validate_simple_polygon
    reveal = float(reveal)
    current = validate_simple_polygon(
        _clip_profile_x(source_polygon, 0.0, keep_greater=True))
    if reveal <= _EPSILON:
        return current
    cap = validate_simple_polygon(_clip_profile_z(
        _clip_profile_x(source_polygon, 0.0, keep_greater=False),
        float(reveal_floor_z), keep_greater=True))
    current_start = min((point for point in current
                         if math.isclose(point[0], 0.0, abs_tol=_EPSILON)),
                        key=lambda point: point[1])
    current_upper = max((point for point in current
                         if math.isclose(point[0], 0.0, abs_tol=_EPSILON)),
                        key=lambda point: point[1])
    start_index = current.index(current_start)
    current = current[start_index:] + current[:start_index]
    if current[-1] != current_upper:
        raise ValueError("Upper Flight Side Board境界orderingが不正です。")
    cap_floor = min((point for point in cap
                     if math.isclose(point[0], 0.0, abs_tol=_EPSILON)),
                    key=lambda point: point[1])
    cap_upper = max((point for point in cap
                     if math.isclose(point[0], 0.0, abs_tol=_EPSILON)),
                    key=lambda point: point[1])
    if not (math.isclose(cap_upper[1], current_upper[1], abs_tol=_EPSILON)
            and math.isclose(cap_floor[1], reveal_floor_z,
                             abs_tol=_EPSILON)):
        raise ValueError("Upper Flight Side Board reveal境界が不正です。")
    cap_index = cap.index(cap_floor)
    cap = cap[cap_index:] + cap[:cap_index]
    if len(cap) < 4 or cap[1] != cap_upper:
        raise ValueError("Upper Flight Side Board reveal orderingが不正です。")
    return validate_simple_polygon(
        current + cap[2:] + (cap_floor,))


def _build_l_flight_board_fragment(local, side, fields, position,
                                   preserve_outgoing_reveal=False,
                                   lower_profile=None, extend_lower_terminal=False,
                                   turn_soffit_z=None,
                                   upper_reveal_floor_z=None):
    """Clip only the Landing endpoint while preserving the Flight local frame."""
    from .stair_geometry import extrude_xz_profile, validate_simple_polygon
    from .stair_residential_geometry import side_board_profile, sloped_side_board_profile
    profile = (sloped_side_board_profile(local, fields)
               if fields.side_board_mode == "SLOPED"
               else side_board_profile(local, fields))
    source_polygon = profile.polygon
    lower = profile.lower if lower_profile is None else tuple(lower_profile)
    if lower_profile is not None:
        source_polygon = validate_simple_polygon(
            profile.outer + tuple(reversed(lower)))
    if position == 1 and not math.isclose(
            profile.outer[-2][0], profile.outer[-1][0], abs_tol=_EPSILON):
        # L upper arrival uses a horizontal cap followed by a world-Z return;
        # do not inherit the legacy zero-nosing diagonal closure.
        rear = profile.outer[-1][0]
        outer = profile.outer[:-1] + ((rear, profile.outer[-2][1]),
                                      profile.outer[-1])
        source_polygon = validate_simple_polygon(
            outer + tuple(reversed(lower)))
    reveal = (max(0.0, float(fields.side_board_reveal_mm) / _MM_PER_METRE)
              if preserve_outgoing_reveal else 0.0)
    if upper_reveal_floor_z is not None:
        if position != 1:
            raise ValueError("Upper Flight reveal指定が不正です。")
        from .stair_residential import validate_side_board_reveal
        reveal = validate_side_board_reveal(
            fields, local.actual_riser, local.going)
        polygon = _resolve_upper_start_reveal(
            source_polygon, reveal, upper_reveal_floor_z)
    elif extend_lower_terminal:
        if position != 0 or turn_soffit_z is None:
            raise ValueError("Lower Flight outer terminal指定が不正です。")
        polygon = _resolve_lower_outer_board_terminal(
            source_polygon, local.run_length, local.riser_thickness,
            turn_soffit_z)
    else:
        polygon = _clip_profile_x(
            source_polygon, -reveal if position == 1 else local.run_length,
            keep_greater=position == 1)
    thickness = float(fields.side_board_thickness_mm) / _MM_PER_METRE
    half = local.width / 2.0
    if side == "LEFT":
        y_min, y_max, ordinal = half, half + thickness, 1
    else:
        y_min, y_max, ordinal = -half - thickness, -half, 2
    fragment = extrude_xz_profile(
        polygon, y_min, y_max, part_type="SIDE_BOARD", ordinal=ordinal)
    forward, left = local.axes.forward, local.axes.left
    vertices = tuple((local.lower_xy[0] + forward[0] * x + left[0] * y,
                      local.lower_xy[1] + forward[1] * x + left[1] * y, z)
                     for x, y, z in fragment.vertices)
    result = MeshFragment("SIDE_BOARD", ordinal, vertices, fragment.faces)
    validate_mesh_fragments((result,))
    return result


def _build_landing_tread_fragment(layout, fields, ordinal):
    """Profile only the incoming approach edge with accepted 07-C treatment."""
    from .stair_geometry import extrude_xz_profile
    from .stair_residential import validate_nosing_board_compatibility
    from .stair_residential_geometry import tread_front_xz_profile
    incoming = layout.flights[0]
    n, q = validate_nosing_board_compatibility(
        fields, incoming.going, layout.tread_thickness, layout.actual_riser)
    half = layout.width / 2.0
    profile = tread_front_xz_profile(
        -half - n, half,
        layout.landing.top_z - layout.landing.thickness,
        layout.landing.top_z, fields.tread_front_edge_mode, q)
    local = extrude_xz_profile(
        profile, -half, half, part_type="TREAD", ordinal=ordinal)
    left = (-incoming.forward[1], incoming.forward[0])
    vertices = tuple((layout.landing.center_xy[0] + incoming.forward[0] * x
                      + left[0] * y,
                      layout.landing.center_xy[1] + incoming.forward[1] * x
                      + left[1] * y, z) for x, y, z in local.vertices)
    result = MeshFragment("TREAD", ordinal, vertices, local.faces)
    validate_mesh_fragments((result,))
    return result


def _build_l_flight_underbody_fragment(local, fields, position):
    """Return the accepted closed local body for either straight Flight."""
    from .stair_residential_geometry import build_underbody_fragment
    return build_underbody_fragment(local, fields)


def _resolve_upper_turn_soffit(local, fields):
    """Return x=0 Z and the accepted constant-pitch upper soffit tail."""
    from .stair_residential_geometry import sloped_underbody_profile
    accepted = sloped_underbody_profile(local, fields).outer
    slope_start, slope_end = accepted[-2:]
    dx = slope_end[0] - slope_start[0]
    if dx <= _EPSILON:
        raise ValueError("Upper Flight soffit勾配runが不足しています。")
    slope = (slope_end[1] - slope_start[1]) / dx
    turn_soffit_z = slope_start[1] - slope * slope_start[0]
    return float(turn_soffit_z), ((0.0, float(turn_soffit_z)),
                                  slope_start, slope_end)


def _build_sloped_upper_underbody_fragment(local, fields, turn_soffit_z):
    """Replace only the accepted Landing-side horizontal lower foot."""
    from .stair_geometry import extrude_xz_profile, validate_simple_polygon
    from .stair_residential_geometry import sloped_underbody_profile
    accepted = sloped_underbody_profile(local, fields)
    resolved_z, lower = _resolve_upper_turn_soffit(local, fields)
    if not math.isclose(resolved_z, turn_soffit_z, abs_tol=_EPSILON):
        raise ValueError("Upper Flight turn soffit authorityが一致しません。")
    inner = ((0.0, local.base_z),) + accepted.inner
    polygon = validate_simple_polygon(inner + tuple(reversed(lower)))
    fragment = extrude_xz_profile(
        polygon, -local.width / 2.0, local.width / 2.0,
        part_type="UNDERBODY", ordinal=1)
    forward, left = local.axes.forward, local.axes.left
    vertices = tuple((local.lower_xy[0] + forward[0] * x + left[0] * y,
                      local.lower_xy[1] + forward[1] * x + left[1] * y, z)
                     for x, y, z in fragment.vertices)
    result = MeshFragment("UNDERBODY", 1, vertices, fragment.faces)
    validate_mesh_fragments((result,))
    return result


def _build_landing_underbody_fragment(
        layout, fields, ordinal, turn_soffit_z):
    """Build the thin horizontal SLOPED_CLOSED turn region.

    This region owns only the canonical w x w Landing footprint.  Its visible
    bottom comes from the extrapolated Upper Flight pitch and its shell depth
    from the Residential underside thickness; every boundary is horizontal
    or vertical.
    """
    from .stair_residential import validate_stepped_underbody_thickness
    thickness = validate_stepped_underbody_thickness(
        fields, layout.actual_riser, layout.tread_thickness,
        layout.riser_thickness)
    bottom = float(turn_soffit_z)
    top = bottom + thickness
    if bottom < layout.base_z - _EPSILON:
        raise ValueError("Landing UNDERBODYがbase_z未満です。")
    incoming = layout.flights[0]
    left = (-incoming.forward[1], incoming.forward[0])
    return _oriented_box(
        layout.landing.center_xy, incoming.forward, left, layout.width,
        -layout.width / 2.0, layout.width / 2.0,
        bottom, top, "UNDERBODY", ordinal)


def _build_landing_underbody_transition(layout, outgoing_local, fields,
                                        landing_soffit, ordinal):
    """Extrude one continuous Landing-horizontal-to-upper-slope section."""
    from .stair_geometry import extrude_xz_profile
    from .stair_residential_geometry import side_board_lower_profile
    lower = side_board_lower_profile(outgoing_local, fields)
    # SLOPED connects directly to the actual visible slope start, skipping the
    # profile's initial horizontal foot. STEPPED retains its accepted first
    # step contact unchanged.
    contact_index = 1 if fields.underside_mode == "SLOPED_CLOSED" else 0
    contact_x, contact_z = lower[contact_index]
    tread_bottom = layout.landing.top_z - layout.landing.thickness
    first_tread_underside = (outgoing_local.base_z + outgoing_local.actual_riser
                             - outgoing_local.tread_thickness)
    contact_top = min(first_tread_underside,
                      contact_z + (tread_bottom - landing_soffit))
    landing_start = -layout.width
    polygon = ((landing_start, landing_soffit),
               (0.0, landing_soffit),
               (contact_x, contact_z),
               (contact_x, contact_top),
               (0.0, tread_bottom),
               (landing_start, tread_bottom))
    turn_cross = (layout.flights[0].forward[0] * layout.flights[1].forward[1]
                  - layout.flights[0].forward[1] * layout.flights[1].forward[0])
    y_min, y_max = -layout.width / 2.0, layout.width / 2.0
    # Keep the existing Final Riser as the approach face: trim the prism to
    # its rear plane rather than emitting a coplanar UNDERSIDE face over it.
    if turn_cross > 0.0:
        y_max -= layout.riser_thickness
    else:
        y_min += layout.riser_thickness
    local = extrude_xz_profile(
        polygon, y_min, y_max,
        part_type="UNDERBODY", ordinal=ordinal)
    forward, left = outgoing_local.axes.forward, outgoing_local.axes.left
    vertices = tuple((outgoing_local.lower_xy[0] + forward[0] * x + left[0] * y,
                      outgoing_local.lower_xy[1] + forward[1] * x + left[1] * y,
                      z) for x, y, z in local.vertices)
    result = MeshFragment("UNDERBODY", ordinal, vertices, local.faces)
    validate_mesh_fragments((result,))
    return result


def prepare_multiflight_residential_geometry(
        points, ascent_direction, base_z_mm, floor_to_floor_mm, riser_count,
        stair_width_mm, tread_thickness_mm, riser_thickness_mm, *,
        point_ids=None, allocation=None, fields=None):
    """Prepare a complete Residential L as local Flights plus Landing parts.

    Straight geometry dispatch is deliberately not used: accepted 07-C part
    helpers receive each already-resolved local Flight, preserving one whole-
    Stair resolver and a single assembled Mesh.
    """
    from .stair_residential import (
        ResidentialFields, residential_fields, validate_nosing_board_compatibility,
        validate_side_board_reveal, validate_stepped_closure_depth,
        validate_stepped_underbody_thickness,
    )
    from .stair_residential_geometry import (
        build_residential_tread_fragments, build_residential_riser_fragments,
        build_top_arrival_nosing_fragment, side_board_lower_profile,
    )
    values = (ResidentialFields() if fields is None else
              fields if isinstance(fields, ResidentialFields) else residential_fields(fields))
    layout = resolve_multiflight_layout(
        points, ascent_direction, base_z_mm, floor_to_floor_mm, riser_count,
        stair_width_mm, tread_thickness_mm, riser_thickness_mm,
        point_ids=point_ids, allocation=allocation)
    locals_ = tuple(_flight_stair_layout(flight, layout) for flight in layout.flights)
    for local in locals_:
        validate_nosing_board_compatibility(
            values, local.going, local.tread_thickness, local.actual_riser)
        validate_stepped_underbody_thickness(
            values, local.actual_riser, local.tread_thickness, local.riser_thickness)
        validate_stepped_closure_depth(values, local.actual_riser, local.going)
        if values.left_side_board_enabled or values.right_side_board_enabled:
            validate_side_board_reveal(values, local.actual_riser, local.going)
    # STEPPED retains its accepted incoming-profile authority.  SLOPED replaces
    # this below with the Upper Flight pitch extrapolated only to local x=0.
    board_bottom = side_board_lower_profile(locals_[0], values)[-1][1]
    if not math.isclose(layout.landing.thickness, layout.tread_thickness,
                        abs_tol=_EPSILON):
        raise ValueError("Landing slab厚はTread厚と一致する必要があります。")
    fragments = []
    turn_cross = (layout.flights[0].forward[0] * layout.flights[1].forward[1]
                  - layout.flights[0].forward[1] * layout.flights[1].forward[0])
    outer_side = "RIGHT" if turn_cross > 0.0 else "LEFT"
    sloped = values.underside_mode == "SLOPED_CLOSED"
    turn_soffit_z = None
    upper_lower = None
    upper_reveal_floor_z = None
    if sloped:
        turn_soffit_z, upper_lower = _resolve_upper_turn_soffit(
            locals_[1], values)
        board_bottom = turn_soffit_z
        reveal = validate_side_board_reveal(
            values, locals_[1].actual_riser, locals_[1].going)
        upper_reveal_floor_z = locals_[1].base_z + reveal
        if not math.isclose(
                upper_reveal_floor_z, layout.landing.top_z + reveal,
                abs_tol=_EPSILON):
            raise ValueError("LandingとUpper Flight reveal高さが一致しません。")
    for index, local in enumerate(locals_):
        fragments.extend(build_residential_tread_fragments(local, values))
        # The final upper arrival alone owns the 07-C positive-nosing cap.
        if index == len(locals_) - 1:
            cap = build_top_arrival_nosing_fragment(local, values)
            if cap is not None:
                fragments.append(cap)
        fragments.extend(build_residential_riser_fragments(local, values))
        fragments.append(
            _build_sloped_upper_underbody_fragment(
                local, values, turn_soffit_z)
            if sloped and index == 1 else
            _build_l_flight_underbody_fragment(local, values, index))
        if values.left_side_board_enabled:
            fragments.append(_build_l_flight_board_fragment(
                local, "LEFT", values, index,
                False if sloped and index == 1 else index == 1 and outer_side == "LEFT",
                upper_lower if sloped and index == 1 else None,
                sloped and index == 0,
                turn_soffit_z,
                upper_reveal_floor_z
                if sloped and index == 1 and outer_side == "LEFT" else None))
        if values.right_side_board_enabled:
            fragments.append(_build_l_flight_board_fragment(
                local, "RIGHT", values, index,
                False if sloped and index == 1 else index == 1 and outer_side == "RIGHT",
                upper_lower if sloped and index == 1 else None,
                sloped and index == 0,
                turn_soffit_z,
                upper_reveal_floor_z
                if sloped and index == 1 and outer_side == "RIGHT" else None))
    fragments.extend(build_landing_side_board_fragments(
        layout, values, len(fragments) + 1, board_bottom))
    ordinal = len(fragments) + 1
    if sloped:
        fragments.append(_build_landing_underbody_fragment(
            layout, values, ordinal, turn_soffit_z))
        fragments.append(_build_landing_tread_fragment(
            layout, values, ordinal + 1))
    else:
        fragments.append(_build_landing_tread_fragment(layout, values, ordinal))
        fragments.append(_build_landing_underbody_transition(
            layout, locals_[1], values, board_bottom, ordinal + 1))
    fragments = tuple(fragments)
    validate_mesh_fragments(fragments)
    return layout, fragments, assemble_stair_mesh(fragments)
