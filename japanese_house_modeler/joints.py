"""Derived Wall joint geometry and atomic Mesh regeneration."""

import math

import bpy

from .connections import is_valid_wall_object, junction_members
from .junctions import (
    CONTINUATION, CORNER, CROSS, INVALID, ISOLATED, T_JUNCTION, classify_junction,
    cross_junction_pairs, t_junction_roles,
)


_MIN_WALL_LENGTH_M = 1.0e-6
_JOINT_POSITION_TOLERANCE_M = 1.0e-6
_LINE_PARALLEL_EPSILON = 1.0e-10
_POLYGON_AREA_EPSILON = 1.0e-12
_MAX_MITER_FACTOR = 10.0
_MAX_T_TRIM_FACTOR = 10.0
_T_MAIN_THICKNESS_TOLERANCE_MM = 1.0e-6
_T_PARAMETER_TOLERANCE_M = 1.0e-9
_T_MAIN_COLLINEAR_TOLERANCE = 1.0e-6
_CROSS_PAIR_COLLINEAR_TOLERANCE = 1.0e-6
_CONTINUATION_COLLINEAR_TOLERANCE = 1.0e-6
_CROSS_THROUGH_THICKNESS_TOLERANCE_MM = 1.0e-6
_CROSS_PARAMETER_TOLERANCE_M = 1.0e-9
_MAX_CROSS_TRIM_FACTOR = 10.0
_STEP_ORTHOGONAL_TOLERANCE = 1.0e-6
_TRANSFORM_EPSILON = 1.0e-6
_ANGLED_CLIP_TOLERANCE_M = 1.0e-9
_MAX_ANGLED_TRIM_FACTOR = 10.0


def _xy(value):
    return float(value[0]), float(value[1])


def _add(point, direction, scale):
    return point[0] + direction[0] * scale, point[1] + direction[1] * scale


def _distance(first, second):
    return math.hypot(first[0] - second[0], first[1] - second[1])


def endpoint_data(wall_object, endpoint):
    """Return canonical position, inward unit direction, normal, and half-width."""
    if endpoint not in {"START", "END"}:
        return None
    try:
        wall = wall_object.jhm_wall
        start = _xy(wall.start)
        end = _xy(wall.end)
        point = start if endpoint == "START" else end
        direction = (end[0] - start[0], end[1] - start[1])
        if endpoint == "END":
            direction = (-direction[0], -direction[1])
        length = math.hypot(*direction)
        half_width = float(wall.wall_thickness) / 2000.0
    except (AttributeError, IndexError, ReferenceError, TypeError, ValueError):
        return None
    if (
        not all(math.isfinite(value) for value in (*point, *direction, half_width))
        or length <= _MIN_WALL_LENGTH_M
        or half_width <= 0.0
    ):
        return None
    unit = direction[0] / length, direction[1] / length
    return point, unit, (-unit[1], unit[0]), half_width


def square_endpoint_pair(wall_object, endpoint):
    """Return (local plus, local minus) at a canonical endpoint."""
    data = endpoint_data(wall_object, endpoint)
    if data is None:
        return None
    point, _direction, normal, half_width = data
    return _add(point, normal, half_width), _add(point, normal, -half_width)


def calculate_continuation_solution(wall_object, endpoint):
    """Validate that a classified continuation is safe for real Mesh output."""
    classification = classify_junction(wall_object, endpoint)
    if classification.key != CONTINUATION or classification.member_count != 2:
        return None
    try:
        members = tuple(junction_members(wall_object, endpoint))
    except (AttributeError, ReferenceError, TypeError, ValueError):
        return None
    if len(members) != 2:
        return None
    data = [endpoint_data(*member) for member in members]
    if any(item is None for item in data):
        return None
    if any(not has_identity_transform(member[0]) for member in members):
        return None
    if _distance(data[0][0], data[1][0]) > _JOINT_POSITION_TOLERANCE_M:
        return None
    first_direction, second_direction = data[0][1], data[1][1]
    cross = (first_direction[0] * second_direction[1]
             - first_direction[1] * second_direction[0])
    dot = (first_direction[0] * second_direction[0]
           + first_direction[1] * second_direction[1])
    if (not math.isfinite(cross) or not math.isfinite(dot)
            or abs(cross) > _CONTINUATION_COLLINEAR_TOLERANCE or dot >= 0.0):
        return None
    return members


def line_intersection(point, direction, other_point, other_direction):
    """Intersect two infinite 2D lines, or return None when near parallel."""
    denominator = (
        direction[0] * other_direction[1]
        - direction[1] * other_direction[0]
    )
    if not math.isfinite(denominator) or abs(denominator) <= _LINE_PARALLEL_EPSILON:
        return None
    offset = other_point[0] - point[0], other_point[1] - point[1]
    parameter = (
        offset[0] * other_direction[1] - offset[1] * other_direction[0]
    ) / denominator
    result = _add(point, direction, parameter)
    return result if all(math.isfinite(value) for value in result) else None


def calculate_miter_pair(first_object, first_endpoint, second_object, second_endpoint):
    """Calculate first Wall's cross-side miter pair, with all safety checks."""
    first = endpoint_data(first_object, first_endpoint)
    second = endpoint_data(second_object, second_endpoint)
    if first is None or second is None:
        return None
    first_point, first_direction, first_normal, first_half = first
    second_point, second_direction, second_normal, second_half = second
    if _distance(first_point, second_point) > _JOINT_POSITION_TOLERANCE_M:
        return None
    if not has_identity_transform(first_object) or not has_identity_transform(second_object):
        return None

    first_plus = _add(first_point, first_normal, first_half)
    first_minus = _add(first_point, first_normal, -first_half)
    second_plus = _add(second_point, second_normal, second_half)
    second_minus = _add(second_point, second_normal, -second_half)
    plus = line_intersection(first_plus, first_direction, second_minus, second_direction)
    minus = line_intersection(first_minus, first_direction, second_plus, second_direction)
    if plus is None or minus is None:
        return None
    limit = max(first_half, second_half) * _MAX_MITER_FACTOR
    if _distance(plus, first_point) > limit or _distance(minus, first_point) > limit:
        return None
    return plus, minus


def calculate_t_solution(wall_object, endpoint):
    """Resolve one shared T solution; return roles and branch pair, or None."""
    classification = classify_junction(wall_object, endpoint)
    if classification.key != T_JUNCTION or classification.member_count != 3:
        return None
    roles = t_junction_roles(wall_object, endpoint)
    if roles is None:
        return None
    main_members, branch_member = roles
    main_members = tuple(main_members)
    all_members = (*main_members, branch_member)
    data = [endpoint_data(*member) for member in all_members]
    if any(item is None for item in data):
        return None
    if any(not has_identity_transform(member[0]) for member in all_members):
        return None
    main_a, main_b, branch = data
    junction = main_a[0]
    if any(_distance(item[0], junction) > _JOINT_POSITION_TOLERANCE_M for item in data[1:]):
        return None
    try:
        thickness_a = float(main_members[0][0].jhm_wall.wall_thickness)
        thickness_b = float(main_members[1][0].jhm_wall.wall_thickness)
    except (AttributeError, ReferenceError, TypeError, ValueError):
        return None
    if abs(thickness_a - thickness_b) > _T_MAIN_THICKNESS_TOLERANCE_MM:
        return None

    # Classification deliberately accepts a one-degree opposite tolerance, but
    # mesh construction needs one geometric host line.  Only an effectively
    # collinear, oppositely directed main pair has a reference-independent outer
    # boundary; near-opposite classified T junctions therefore safely fall back.
    main_cross = (
        main_a[1][0] * main_b[1][1] - main_a[1][1] * main_b[1][0]
    )
    main_dot = main_a[1][0] * main_b[1][0] + main_a[1][1] * main_b[1][1]
    if abs(main_cross) > _T_MAIN_COLLINEAR_TOLERANCE or main_dot >= 0.0:
        return None

    _main_point, main_direction, main_normal, main_half = main_a
    branch_point, branch_direction, branch_normal, branch_half = branch
    side_dot = branch_direction[0] * main_normal[0] + branch_direction[1] * main_normal[1]
    if not math.isfinite(side_dot) or abs(side_dot) <= _LINE_PARALLEL_EPSILON:
        return None
    host_origin = _add(junction, main_normal, main_half if side_dot > 0.0 else -main_half)
    trim_points = []
    parameters = []
    for side in (branch_half, -branch_half):
        side_origin = _add(branch_point, branch_normal, side)
        trim = line_intersection(side_origin, branch_direction, host_origin, main_direction)
        if trim is None:
            return None
        parameter = (
            (trim[0] - side_origin[0]) * branch_direction[0]
            + (trim[1] - side_origin[1]) * branch_direction[1]
        )
        trim_points.append(trim)
        parameters.append(parameter)

    limit = max(main_half, branch_half) * _MAX_T_TRIM_FACTOR
    branch_length = _distance(
        _xy(branch_member[0].jhm_wall.start), _xy(branch_member[0].jhm_wall.end)
    )
    if (
        any(parameter < -_T_PARAMETER_TOLERANCE_M for parameter in parameters)
        or any(_distance(trim, junction) > limit for trim in trim_points)
        or any(parameter >= branch_length - _MIN_WALL_LENGTH_M for parameter in parameters)
    ):
        return None
    return main_members, branch_member, tuple(trim_points), host_origin, main_direction


def _canonical_axis(first_direction, second_direction):
    """Derive one order/sign-independent unit axis from opposite directions."""
    axes = []
    for direction in (first_direction, second_direction):
        x, y = direction
        if x < 0.0 or (abs(x) <= _LINE_PARALLEL_EPSILON and y < 0.0):
            x, y = -x, -y
        axes.append((x, y))
    combined = axes[0][0] + axes[1][0], axes[0][1] + axes[1][1]
    length = math.hypot(*combined)
    if not math.isfinite(length) or length <= _LINE_PARALLEL_EPSILON:
        return None
    return combined[0] / length, combined[1] / length


def _cross_role_data(wall_object, endpoint):
    """Validate a Cross and apply the single Build 04-E role policy."""
    classification = classify_junction(wall_object, endpoint)
    if classification.key != CROSS or classification.member_count != 4:
        return None
    pairs = cross_junction_pairs(wall_object, endpoint)
    if pairs is None:
        return None
    members = tuple(member for pair in pairs for member in pair)
    data = [(member, endpoint_data(*member)) for member in members]
    if any(item is None for _member, item in data):
        return None
    if any(not has_identity_transform(member[0]) for member in members):
        return None
    junction = data[0][1][0]
    if any(_distance(item[0], junction) > _JOINT_POSITION_TOLERANCE_M
           for _member, item in data[1:]):
        return None
    pair_data = []
    for pair in pairs:
        first = endpoint_data(*pair[0])
        second = endpoint_data(*pair[1])
        cross = first[1][0] * second[1][1] - first[1][1] * second[1][0]
        dot = first[1][0] * second[1][0] + first[1][1] * second[1][1]
        axis = _canonical_axis(first[1], second[1])
        if (abs(cross) > _CROSS_PAIR_COLLINEAR_TOLERANCE
                or dot >= 0.0 or axis is None):
            return None
        pair_data.append((tuple(pair), first, axis))
    axis_cross = (pair_data[0][2][0] * pair_data[1][2][1]
                  - pair_data[0][2][1] * pair_data[1][2][0])
    if abs(axis_cross) <= _CROSS_PAIR_COLLINEAR_TOLERANCE:
        return None
    through_index = max(range(2), key=lambda index: (
        abs(pair_data[index][2][0]), pair_data[index][2][1],
        pair_data[index][2][0],
    ))
    through = pair_data[through_index]
    butt = pair_data[1 - through_index]
    return through, butt, junction


def calculate_cross_solution(wall_object, endpoint):
    """Resolve roles and both butt trims as one all-or-nothing Cross solution."""
    role_data = _cross_role_data(wall_object, endpoint)
    if role_data is None:
        return None
    (through_members, host, host_axis), (butt_members, _ref, _axis), junction = role_data
    try:
        through_thicknesses = [
            float(member[0].jhm_wall.wall_thickness) for member in through_members
        ]
    except (AttributeError, ReferenceError, TypeError, ValueError):
        return None
    if abs(through_thicknesses[0] - through_thicknesses[1]) > (
        _CROSS_THROUGH_THICKNESS_TOLERANCE_MM
    ):
        return None

    _host_point, host_direction, host_normal, host_half = host
    trims = []
    for member in butt_members:
        butt = endpoint_data(*member)
        butt_point, butt_direction, butt_normal, butt_half = butt
        side_dot = butt_direction[0] * host_normal[0] + butt_direction[1] * host_normal[1]
        if not math.isfinite(side_dot) or abs(side_dot) <= _LINE_PARALLEL_EPSILON:
            return None
        host_origin = _add(
            junction, host_normal, host_half if side_dot > 0.0 else -host_half
        )
        trim_points = []
        parameters = []
        for side in (butt_half, -butt_half):
            side_origin = _add(butt_point, butt_normal, side)
            trim = line_intersection(side_origin, butt_direction, host_origin, host_direction)
            if trim is None:
                return None
            parameter = (
                (trim[0] - side_origin[0]) * butt_direction[0]
                + (trim[1] - side_origin[1]) * butt_direction[1]
            )
            trim_points.append(trim)
            parameters.append(parameter)
        limit = max(host_half, butt_half) * _MAX_CROSS_TRIM_FACTOR
        wall_length = _distance(_xy(member[0].jhm_wall.start), _xy(member[0].jhm_wall.end))
        if (
            any(parameter < -_CROSS_PARAMETER_TOLERANCE_M for parameter in parameters)
            or any(_distance(trim, junction) > limit for trim in trim_points)
            or any(parameter >= wall_length - _MIN_WALL_LENGTH_M for parameter in parameters)
        ):
            return None
        trims.append((member, tuple(trim_points)))
    return through_members, tuple(trims), junction, host_axis


def _positive_negative_hosts(members, host_axis):
    """Return hosts extending along canonical positive and negative axes."""
    result = {}
    for member in members:
        data = endpoint_data(*member)
        if data is None:
            return None
        coordinate = data[1][0] * host_axis[0] + data[1][1] * host_axis[1]
        if coordinate > _STEP_ORTHOGONAL_TOLERANCE:
            key = "positive"
        elif coordinate < -_STEP_ORTHOGONAL_TOLERANCE:
            key = "negative"
        else:
            return None
        if key in result:
            return None
        result[key] = (member, data)
    return (result.get("positive"), result.get("negative")) if len(result) == 2 else None


def _step_profile(member, junction, host_axis, positive_half, negative_half):
    data = endpoint_data(*member)
    if data is None:
        return None
    _point, direction, normal, half = data
    profile = []
    for side in (half, -half):
        side_point = _add(junction, normal, side)
        coordinate = ((side_point[0] - junction[0]) * host_axis[0]
                      + (side_point[1] - junction[1]) * host_axis[1])
        if coordinate > _STEP_ORTHOGONAL_TOLERANCE:
            depth = positive_half
        elif coordinate < -_STEP_ORTHOGONAL_TOLERANCE:
            depth = negative_half
        else:
            return None
        profile.extend((_add(side_point, direction, depth),
                        _add(junction, direction, depth)))
    # The loop produces P+, C+, P-, C-; endpoint winding requires C- before P-.
    profile = (profile[0], profile[1], profile[3], profile[2])
    return profile if all(math.isfinite(v) for point in profile for v in point) else None


def calculate_t_step_solution(wall_object, endpoint):
    """Resolve an orthogonal unequal-main T as one shared step solution."""
    classification = classify_junction(wall_object, endpoint)
    roles = t_junction_roles(wall_object, endpoint)
    if classification.key != T_JUNCTION or classification.member_count != 3 or roles is None:
        return None
    main_members, branch_member = tuple(roles[0]), roles[1]
    members = (*main_members, branch_member)
    data = [endpoint_data(*member) for member in members]
    if any(item is None for item in data) or any(not has_identity_transform(m[0]) for m in members):
        return None
    junction = data[0][0]
    if any(_distance(item[0], junction) > _JOINT_POSITION_TOLERANCE_M for item in data[1:]):
        return None
    cross = data[0][1][0] * data[1][1][1] - data[0][1][1] * data[1][1][0]
    dot = data[0][1][0] * data[1][1][0] + data[0][1][1] * data[1][1][1]
    host_axis = _canonical_axis(data[0][1], data[1][1])
    if abs(cross) > _T_MAIN_COLLINEAR_TOLERANCE or dot >= 0.0 or host_axis is None:
        return None
    hosts = _positive_negative_hosts(main_members, host_axis)
    if hosts is None:
        return None
    positive, negative = hosts
    positive_half, negative_half = positive[1][3], negative[1][3]
    if abs(positive_half - negative_half) * 2000.0 <= _T_MAIN_THICKNESS_TOLERANCE_MM:
        return None
    branch = data[2]
    if abs(branch[1][0] * host_axis[0] + branch[1][1] * host_axis[1]) > _STEP_ORTHOGONAL_TOLERANCE:
        return None
    positive_length = _distance(
        _xy(positive[0][0].jhm_wall.start), _xy(positive[0][0].jhm_wall.end)
    )
    negative_length = _distance(
        _xy(negative[0][0].jhm_wall.start), _xy(negative[0][0].jhm_wall.end)
    )
    if positive_length <= branch[3] + _MIN_WALL_LENGTH_M:
        return None
    if negative_length <= branch[3] + _MIN_WALL_LENGTH_M:
        return None
    branch_length = _distance(_xy(branch_member[0].jhm_wall.start), _xy(branch_member[0].jhm_wall.end))
    if branch_length <= max(positive_half, negative_half) + _MIN_WALL_LENGTH_M:
        return None
    profile = _step_profile(branch_member, junction, host_axis, positive_half, negative_half)
    if profile is None:
        return None
    return main_members, branch_member, profile, junction, host_axis


def calculate_cross_step_solution(wall_object, endpoint):
    """Resolve an orthogonal unequal-through Cross as one shared step solution."""
    role_data = _cross_role_data(wall_object, endpoint)
    if role_data is None:
        return None
    (through, _host, host_axis), (butts, _butt, butt_axis), junction = role_data
    hosts = _positive_negative_hosts(through, host_axis)
    if hosts is None:
        return None
    positive, negative = hosts
    positive_half, negative_half = positive[1][3], negative[1][3]
    if abs(positive_half - negative_half) * 2000.0 <= _CROSS_THROUGH_THICKNESS_TOLERANCE_MM:
        return None
    if abs(host_axis[0] * butt_axis[0] + host_axis[1] * butt_axis[1]) > _STEP_ORTHOGONAL_TOLERANCE:
        return None
    profiles = []
    for member in butts:
        butt = endpoint_data(*member)
        host_margin = butt[3] + _MIN_WALL_LENGTH_M
        if any(_distance(_xy(host[0][0].jhm_wall.start), _xy(host[0][0].jhm_wall.end)) <= host_margin
               for host in (positive, negative)):
            return None
        length = _distance(_xy(member[0].jhm_wall.start), _xy(member[0].jhm_wall.end))
        if length <= max(positive_half, negative_half) + _MIN_WALL_LENGTH_M:
            return None
        profile = _step_profile(member, junction, host_axis, positive_half, negative_half)
        if profile is None:
            return None
        profiles.append((member, profile))
    return through, tuple(profiles), junction, host_axis


def world_to_endpoint_local(point, origin, direction, normal):
    """Project a world XY point into an endpoint's (s, q) basis."""
    offset = point[0] - origin[0], point[1] - origin[1]
    return (offset[0] * direction[0] + offset[1] * direction[1],
            offset[0] * normal[0] + offset[1] * normal[1])


def endpoint_local_to_world(point, origin, direction, normal):
    """Transform an endpoint-local (s, q) point to world XY."""
    return (origin[0] + point[0] * direction[0] + point[1] * normal[0],
            origin[1] + point[0] * direction[1] + point[1] * normal[1])


def canonical_rectangle(wall_object, endpoint):
    """Return the canonical, CCW rectangle beginning at an endpoint."""
    data = endpoint_data(wall_object, endpoint)
    if data is None:
        return None
    origin, direction, normal, half = data
    length = _distance(_xy(wall_object.jhm_wall.start), _xy(wall_object.jhm_wall.end))
    return tuple(endpoint_local_to_world(point, origin, direction, normal) for point in (
        (0.0, half), (0.0, -half), (length, -half), (length, half)
    ))


def segment_intersection_parameters(first, second, third, fourth,
                                    tolerance=_ANGLED_CLIP_TOLERANCE_M):
    """Return all split parameters on two segments, including overlap ends."""
    r = second[0] - first[0], second[1] - first[1]
    s = fourth[0] - third[0], fourth[1] - third[1]
    denominator = r[0] * s[1] - r[1] * s[0]
    offset = third[0] - first[0], third[1] - first[1]
    numerator = offset[0] * r[1] - offset[1] * r[0]
    rr, ss = r[0] * r[0] + r[1] * r[1], s[0] * s[0] + s[1] * s[1]
    if rr <= tolerance * tolerance or ss <= tolerance * tolerance:
        return (), ()
    if abs(denominator) <= tolerance:
        if abs(numerator) > tolerance:
            return (), ()
        first_values = sorted(((point[0] - first[0]) * r[0] +
                               (point[1] - first[1]) * r[1]) / rr
                              for point in (third, fourth))
        low, high = max(0.0, first_values[0]), min(1.0, first_values[1])
        if low > high + tolerance:
            return (), ()
        first_hits = (low,) if abs(low - high) <= tolerance else (low, high)
        points = [_add(first, r, value) for value in first_hits]
        second_hits = tuple(((point[0] - third[0]) * s[0] +
                             (point[1] - third[1]) * s[1]) / ss for point in points)
        return tuple(first_hits), second_hits
    t = (offset[0] * s[1] - offset[1] * s[0]) / denominator
    u = (offset[0] * r[1] - offset[1] * r[0]) / denominator
    if -tolerance <= t <= 1.0 + tolerance and -tolerance <= u <= 1.0 + tolerance:
        return (min(1.0, max(0.0, t)),), (min(1.0, max(0.0, u)),)
    return (), ()


def _dedupe_parameters(values, tolerance=_ANGLED_CLIP_TOLERANCE_M):
    result = []
    for value in sorted(values):
        value = min(1.0, max(0.0, value))
        if not result or abs(value - result[-1]) > tolerance:
            result.append(value)
    return tuple(result)


def split_segment(first, second, parameters):
    """Split one segment in deterministic parameter order."""
    direction = second[0] - first[0], second[1] - first[1]
    values = _dedupe_parameters((0.0, 1.0, *parameters))
    return tuple((_add(first, direction, values[index]),
                  _add(first, direction, values[index + 1]))
                 for index in range(len(values) - 1)
                 if values[index + 1] - values[index] > _ANGLED_CLIP_TOLERANCE_M)


def _point_polygon_classification(point, polygon):
    """Return -1 outside, 0 boundary, or 1 inside for a simple polygon."""
    inside = False
    for index, first in enumerate(polygon):
        second = polygon[(index + 1) % len(polygon)]
        if (abs(_cross(first, second, point)) <= _ANGLED_CLIP_TOLERANCE_M and
                min(first[0], second[0]) - _ANGLED_CLIP_TOLERANCE_M <= point[0] <=
                max(first[0], second[0]) + _ANGLED_CLIP_TOLERANCE_M and
                min(first[1], second[1]) - _ANGLED_CLIP_TOLERANCE_M <= point[1] <=
                max(first[1], second[1]) + _ANGLED_CLIP_TOLERANCE_M):
            return 0
        if ((first[1] > point[1]) != (second[1] > point[1]) and
                point[0] < (second[0] - first[0]) * (point[1] - first[1]) /
                (second[1] - first[1]) + first[0]):
            inside = not inside
    return 1 if inside else -1


def _trace_cycles(edges):
    """Trace a directed 1-in/1-out boundary graph, rejecting ambiguity."""
    def key(point):
        scale = _ANGLED_CLIP_TOLERANCE_M
        return round(point[0] / scale), round(point[1] / scale)
    points, outgoing, incoming = {}, {}, {}
    for first, second in edges:
        a, b = key(first), key(second)
        if a == b:
            continue
        points.setdefault(a, first); points.setdefault(b, second)
        if a in outgoing and outgoing[a] != b:
            return None
        outgoing[a] = b
        incoming[b] = incoming.get(b, 0) + 1
    if not outgoing or any(incoming.get(vertex, 0) != 1 for vertex in outgoing):
        return None
    cycles, unused = [], set(outgoing)
    while unused:
        start = min(unused)
        cycle, current = [], start
        while current in unused:
            unused.remove(current); cycle.append(points[current])
            current = outgoing.get(current)
            if current is None:
                return None
        if current != start or not validate_lower_polygon(cycle):
            return None
        cycles.append(tuple(cycle))
    return tuple(cycles)


def rectangle_difference_cycles(guest, hosts):
    """Planar arrangement for one rectangle minus exactly two rectangles."""
    polygons = (tuple(guest), tuple(hosts[0]), tuple(hosts[1]))
    raw = [(polygon[index], polygon[(index + 1) % 4])
           for polygon in polygons for index in range(4)]
    splits = [[0.0, 1.0] for _edge in raw]
    for first in range(len(raw)):
        for second in range(first + 1, len(raw)):
            first_hits, second_hits = segment_intersection_parameters(
                *raw[first], *raw[second])
            splits[first].extend(first_hits); splits[second].extend(second_hits)
    candidates = []
    for edge, values in zip(raw, splits):
        candidates.extend(split_segment(*edge, values))
    probe = 1.0e-7
    directed = {}
    def visible(point):
        return (_point_polygon_classification(point, polygons[0]) >= 0 and
                all(_point_polygon_classification(point, host) < 0 for host in polygons[1:]))
    for first, second in candidates:
        dx, dy = second[0] - first[0], second[1] - first[1]
        length = math.hypot(dx, dy)
        midpoint = (first[0] + second[0]) * 0.5, (first[1] + second[1]) * 0.5
        normal = -dy / length, dx / length
        left = visible(_add(midpoint, normal, probe))
        right = visible(_add(midpoint, normal, -probe))
        if left == right:
            continue
        edge = (first, second) if left else (second, first)
        key = tuple(round(value / _ANGLED_CLIP_TOLERANCE_M)
                    for point in edge for value in point)
        directed[key] = edge
    return _trace_cycles(tuple(directed.values()))


def _simplify_profile(points):
    result = []
    for point in points:
        if result and _distance(result[-1], point) <= _ANGLED_CLIP_TOLERANCE_M:
            continue
        while len(result) >= 2 and abs(_cross(result[-2], result[-1], point)) <= _ANGLED_CLIP_TOLERANCE_M:
            result.pop()
        result.append(point)
    return tuple(result)


def _polygon_touches_segment(polygon, first, second):
    """Return whether a polygon boundary uses or touches a tagged segment."""
    return any(segment_intersection_parameters(
        polygon[index], polygon[(index + 1) % len(polygon)], first, second
    )[0] for index in range(len(polygon)))


def segment_touches_polygon(first, second, polygon):
    """Return whether any part of a segment reaches a polygon or its boundary."""
    if (_point_polygon_classification(first, polygon) >= 0 or
            _point_polygon_classification(second, polygon) >= 0):
        return True
    return _polygon_touches_segment(polygon, first, second)


def clip_guest_profile(guest_member, host_members):
    """Return the far-connected component's local-plus to local-minus cut path."""
    data = endpoint_data(*guest_member)
    if data is None or len(host_members) != 2:
        return None
    origin, direction, normal, half = data
    length = _distance(_xy(guest_member[0].jhm_wall.start), _xy(guest_member[0].jhm_wall.end))
    guest = canonical_rectangle(*guest_member)
    hosts = tuple(canonical_rectangle(*member) for member in host_members)
    if guest is None or any(host is None for host in hosts):
        return None
    scale = max(half, *(endpoint_data(*member)[3] for member in host_members))
    limit = scale * _MAX_ANGLED_TRIM_FACTOR
    cycles = rectangle_difference_cycles(guest, hosts)
    if not cycles:
        return None
    far_probe = endpoint_local_to_world((length - 1.0e-7, 0.0), origin, direction, normal)
    selected = [cycle for cycle in cycles if _point_polygon_classification(far_probe, cycle) >= 0]
    if len(selected) != 1:
        return None
    polygon = selected[0]
    # Any other boundary cycle inside the far component would be an unsupported hole.
    if any(_point_polygon_classification(cycle[0], polygon) == 1
           for cycle in cycles if cycle is not polygon):
        return None
    # canonical_rectangle indexes 2 -> 3 are the Host far-end face.  Reject
    # only when that tagged face actually participates in, or touches, the
    # selected far-connected difference boundary.
    if any(_polygon_touches_segment(polygon, host[2], host[3]) for host in hosts):
        return None
    local = [world_to_endpoint_local(point, origin, direction, normal) for point in polygon]
    plus = [index for index, point in enumerate(local) if abs(point[1] - half) <= 1.0e-7]
    minus = [index for index, point in enumerate(local) if abs(point[1] + half) <= 1.0e-7]
    if not plus or not minus:
        return None
    plus_index = min(plus, key=lambda index: local[index][0])
    minus_index = min(minus, key=lambda index: local[index][0])
    path, index = [], plus_index
    while True:
        path.append(polygon[index])
        if index == minus_index:
            break
        index = (index + 1) % len(polygon)
        if len(path) > len(polygon):
            return None
    profile = _simplify_profile(path)
    local_profile = [world_to_endpoint_local(point, origin, direction, normal) for point in profile]
    if (len(profile) < 2 or any(point[0] >= length - _MIN_WALL_LENGTH_M or
                                point[0] < -_T_PARAMETER_TOLERANCE_M or point[0] > limit
                                for point in local_profile)):
        return None
    # The complete canonical far edge must remain visible.  Endpoint
    # classification plus exact edge intersections catches crossings, touches,
    # tangencies, and collinear overlaps without relying on sampling.
    far_edge = (endpoint_local_to_world((length, -half), origin, direction, normal),
                endpoint_local_to_world((length, half), origin, direction, normal))
    if any(segment_touches_polygon(*far_edge, host) for host in hosts):
        return None
    return profile


def calculate_t_oblique_solution(wall_object, endpoint):
    """Resolve an unequal-main oblique T by canonical rectangle clipping."""
    classification = classify_junction(wall_object, endpoint)
    roles = t_junction_roles(wall_object, endpoint)
    if classification.key != T_JUNCTION or classification.member_count != 3 or roles is None:
        return None
    mains, branch = tuple(roles[0]), roles[1]
    members = (*mains, branch)
    data = [endpoint_data(*member) for member in members]
    if any(item is None for item in data) or any(not has_identity_transform(member[0]) for member in members):
        return None
    junction = data[0][0]
    if any(_distance(item[0], junction) > _JOINT_POSITION_TOLERANCE_M for item in data[1:]):
        return None
    cross = data[0][1][0] * data[1][1][1] - data[0][1][1] * data[1][1][0]
    dot = data[0][1][0] * data[1][1][0] + data[0][1][1] * data[1][1][1]
    axis = _canonical_axis(data[0][1], data[1][1])
    if abs(cross) > _T_MAIN_COLLINEAR_TOLERANCE or dot >= 0.0 or axis is None:
        return None
    if abs(data[0][3] - data[1][3]) * 2000.0 <= _T_MAIN_THICKNESS_TOLERANCE_MM:
        return None
    axis_dot = abs(data[2][1][0] * axis[0] + data[2][1][1] * axis[1])
    if axis_dot <= _STEP_ORTHOGONAL_TOLERANCE or 1.0 - axis_dot <= _LINE_PARALLEL_EPSILON:
        return None
    profile = clip_guest_profile(branch, mains)
    return (mains, branch, profile, junction, axis) if profile is not None else None


def calculate_cross_oblique_solution(wall_object, endpoint):
    """Resolve an unequal-through oblique Cross as one atomic clip solution."""
    role_data = _cross_role_data(wall_object, endpoint)
    if role_data is None:
        return None
    (through, _host, host_axis), (butts, _butt, butt_axis), junction = role_data
    halves = [endpoint_data(*member)[3] for member in through]
    if abs(halves[0] - halves[1]) * 2000.0 <= _CROSS_THROUGH_THICKNESS_TOLERANCE_MM:
        return None
    axis_dot = abs(host_axis[0] * butt_axis[0] + host_axis[1] * butt_axis[1])
    if axis_dot <= _STEP_ORTHOGONAL_TOLERANCE or 1.0 - axis_dot <= _LINE_PARALLEL_EPSILON:
        return None
    profiles = []
    for member in butts:
        profile = clip_guest_profile(member, through)
        if profile is None:
            return None
        profiles.append((member, profile))
    return through, tuple(profiles), junction, host_axis


def endpoint_joint_profile(wall_object, endpoint):
    """Return an ordered local-plus to local-minus endpoint profile and status."""
    square = square_endpoint_pair(wall_object, endpoint)
    if square is None:
        return None, "FALLBACK"
    classification = classify_junction(wall_object, endpoint)
    if classification.key == ISOLATED:
        return square, "ISOLATED"
    if classification.key == CONTINUATION and classification.member_count == 2:
        status = ("CONTINUATION" if calculate_continuation_solution(
            wall_object, endpoint
        ) is not None else "FALLBACK")
        return square, status
    if classification.key == T_JUNCTION and classification.member_count == 3:
        solution = calculate_t_solution(wall_object, endpoint)
        if solution is None:
            solution = calculate_t_step_solution(wall_object, endpoint)
        if solution is None:
            solution = calculate_t_oblique_solution(wall_object, endpoint)
        if solution is None:
            return square, "FALLBACK"
        main_members, branch_member, branch_pair, _host_origin, _host_direction = solution
        current = (wall_object, endpoint)
        if any(member[0] is current[0] and member[1] == current[1] for member in main_members):
            return square, "T_MAIN"
        if branch_member[0] is current[0] and branch_member[1] == current[1]:
            return branch_pair, "T_BRANCH"
        return square, "FALLBACK"
    if classification.key == CROSS and classification.member_count == 4:
        solution = calculate_cross_solution(wall_object, endpoint)
        if solution is None:
            solution = calculate_cross_step_solution(wall_object, endpoint)
        if solution is None:
            solution = calculate_cross_oblique_solution(wall_object, endpoint)
        if solution is None:
            return square, "FALLBACK"
        through_members, butt_trims, _junction, _host_axis = solution
        current = (wall_object, endpoint)
        if any(member[0] is current[0] and member[1] == current[1] for member in through_members):
            return square, "CROSS_THROUGH"
        for member, trim_pair in butt_trims:
            if member[0] is current[0] and member[1] == current[1]:
                return trim_pair, "CROSS_BUTT"
        return square, "FALLBACK"
    if classification.key == INVALID:
        return square, "FALLBACK"
    if classification.key != CORNER or classification.member_count != 2:
        return square, "UNSUPPORTED"
    members = junction_members(wall_object, endpoint)
    partner = next(
        (member for member in members if member[0] is not wall_object), None
    )
    if partner is None:
        return square, "FALLBACK"
    miter = calculate_miter_pair(wall_object, endpoint, partner[0], partner[1])
    return (miter, "MITER") if miter is not None else (square, "FALLBACK")


def endpoint_joint_pair(wall_object, endpoint):
    """Compatibility view of a profile as its outer local-plus/minus pair."""
    profile, status = endpoint_joint_profile(wall_object, endpoint)
    if profile is None:
        return None, status
    return (profile[0], profile[-1]), status


def joint_status_label(wall_object, endpoint):
    """Return a read-only Japanese label for the effective joint treatment."""
    _start, _end, statuses = _resolved_endpoint_profiles(wall_object)
    status = statuses[endpoint]
    return {
        "ISOLATED": "未接続",
        "CONTINUATION": "直線",
        "MITER": "マイター",
        "T_MAIN": "T字主壁",
        "T_BRANCH": "T字枝壁",
        "CROSS_THROUGH": "十字通し壁",
        "CROSS_BUTT": "十字突合せ壁",
        "FALLBACK": "安全フォールバック",
        "UNSUPPORTED": "未対応",
    }[status]


def _resolved_endpoint_profiles(wall_object):
    """Resolve variable profiles and Wall-local polygon fallback."""
    squares = {
        endpoint: square_endpoint_pair(wall_object, endpoint)
        for endpoint in ("START", "END")
    }
    requested = {
        endpoint: endpoint_joint_profile(wall_object, endpoint)
        for endpoint in ("START", "END")
    }
    if any(pair is None for pair in squares.values()):
        return None, None, {"START": "FALLBACK", "END": "FALLBACK"}
    profiles = {endpoint: requested[endpoint][0] for endpoint in requested}
    statuses = {endpoint: requested[endpoint][1] for endpoint in requested}

    def valid():
        return validate_lower_polygon(
            list(profiles["START"]) + list(profiles["END"])
        )

    if not valid():
        # A shared unsafe T/Cross is rejected earlier for all members.  This
        # branch is intentionally Wall-local: a safe branch trim can still be
        # incompatible with this Wall's independently resolved opposite-end
        # joint, in which case only this visual endpoint is squared off.
        for endpoint in ("START", "END"):
            if statuses[endpoint] not in {"MITER", "T_BRANCH", "CROSS_BUTT"}:
                continue
            profiles[endpoint] = squares[endpoint]
            statuses[endpoint] = "FALLBACK"
            if valid():
                break
    if not valid():
        profiles = squares
        for endpoint in statuses:
            if statuses[endpoint] in {"MITER", "T_BRANCH", "CROSS_BUTT"}:
                statuses[endpoint] = "FALLBACK"
    return profiles["START"], profiles["END"], statuses


def _resolved_endpoint_pairs(wall_object):
    """Compatibility wrapper exposing only each resolved profile's outer pair."""
    start, end, statuses = _resolved_endpoint_profiles(wall_object)
    if start is None or end is None:
        return None, None, statuses
    return (start[0], start[-1]), (end[0], end[-1]), statuses


def _cross(first, second, third):
    return ((second[0] - first[0]) * (third[1] - first[1])) - (
        (second[1] - first[1]) * (third[0] - first[0])
    )


def _point_on_segment(point, first, second):
    return (abs(_cross(first, second, point)) <= _JOINT_POSITION_TOLERANCE_M
            and min(first[0], second[0]) - _JOINT_POSITION_TOLERANCE_M <= point[0]
            <= max(first[0], second[0]) + _JOINT_POSITION_TOLERANCE_M
            and min(first[1], second[1]) - _JOINT_POSITION_TOLERANCE_M <= point[1]
            <= max(first[1], second[1]) + _JOINT_POSITION_TOLERANCE_M)


def _segments_intersect(first, second, third, fourth):
    a, b = _cross(first, second, third), _cross(first, second, fourth)
    c, d = _cross(third, fourth, first), _cross(third, fourth, second)
    tolerance = _JOINT_POSITION_TOLERANCE_M
    if ((a > tolerance and b < -tolerance) or (a < -tolerance and b > tolerance)) and (
            (c > tolerance and d < -tolerance) or (c < -tolerance and d > tolerance)):
        return True
    return ((abs(a) <= tolerance and _point_on_segment(third, first, second))
            or (abs(b) <= tolerance and _point_on_segment(fourth, first, second))
            or (abs(c) <= tolerance and _point_on_segment(first, third, fourth))
            or (abs(d) <= tolerance and _point_on_segment(second, third, fourth)))


def validate_lower_polygon(points):
    """Validate finiteness, area, and non-adjacent edge intersections."""
    if len(points) < 3 or not all(
        math.isfinite(value) for point in points for value in point
    ):
        return False
    count = len(points)
    if any(_distance(points[index], points[(index + 1) % count])
           <= _JOINT_POSITION_TOLERANCE_M for index in range(count)):
        return False
    area = abs(
        sum(
            point[0] * points[(index + 1) % count][1]
            - points[(index + 1) % count][0] * point[1]
            for index, point in enumerate(points)
        )
    ) * 0.5
    if area <= _POLYGON_AREA_EPSILON:
        return False
    for first in range(count):
        for second in range(first + 1, count):
            if second == first + 1 or (first == 0 and second == count - 1):
                continue
            if _segments_intersect(points[first], points[(first + 1) % count],
                                   points[second], points[(second + 1) % count]):
                return False
    return True


def build_wall_geometry(wall_object):
    """Build joint-aware cuboid geometry exclusively from canonical Wall data."""
    try:
        height = float(wall_object.jhm_wall.wall_height) / 1000.0
        thickness = float(wall_object.jhm_wall.wall_thickness)
    except (AttributeError, ReferenceError, TypeError, ValueError):
        return None
    if not math.isfinite(height) or height <= 0.0 or thickness <= 0.0:
        return None
    start_profile, end_profile, _statuses = _resolved_endpoint_profiles(wall_object)
    if start_profile is None or end_profile is None:
        return None
    lower = list(start_profile) + list(end_profile)
    if not validate_lower_polygon(lower):
        return None
    vertices = [(point[0], point[1], 0.0) for point in lower]
    vertices.extend((point[0], point[1], height) for point in lower)
    count = len(lower)
    faces = [tuple(reversed(range(count))), tuple(range(count, count * 2))]
    faces.extend((index, (index + 1) % count, count + (index + 1) % count,
                  count + index) for index in range(count))
    faces = tuple(faces)
    return vertices, faces


def has_identity_transform(wall_object):
    try:
        matrix = wall_object.matrix_basis
        return all(
            abs(matrix[row][column] - (1.0 if row == column else 0.0))
            <= _TRANSFORM_EPSILON
            for row in range(4)
            for column in range(4)
        )
    except (AttributeError, IndexError, ReferenceError, TypeError):
        return False


def affected_walls(wall_object, endpoints=("START", "END")):
    """Deduplicate one Wall and all live members at the requested endpoints."""
    objects = {}
    if is_valid_wall_object(wall_object):
        objects[wall_object.as_pointer()] = wall_object
    for endpoint in endpoints:
        for member_object, _member_endpoint in junction_members(wall_object, endpoint):
            if is_valid_wall_object(member_object):
                objects[member_object.as_pointer()] = member_object
    return list(objects.values())


def merge_affected(*groups):
    objects = {}
    for group in groups:
        for wall_object in group:
            if is_valid_wall_object(wall_object):
                objects[wall_object.as_pointer()] = wall_object
    return list(objects.values())


def regenerate_wall_meshes(wall_objects):
    """Build then atomically swap all affected meshes, rolling back any failure."""
    objects = merge_affected(wall_objects)
    if any(not has_identity_transform(wall_object) for wall_object in objects):
        raise ValueError("Object TransformがあるWallは接合を再生成できません。")
    prepared = []
    try:
        for wall_object in objects:
            geometry = build_wall_geometry(wall_object)
            if geometry is None:
                raise ValueError(f"{wall_object.name} の接合形状が不正です。")
            old_mesh = wall_object.data
            new_mesh = bpy.data.meshes.new(old_mesh.name)
            prepared.append((wall_object, old_mesh, new_mesh))
            new_mesh.from_pydata(geometry[0], [], geometry[1])
            for material in old_mesh.materials:
                new_mesh.materials.append(material)
            new_mesh.update()
    except Exception:
        for _wall_object, _old_mesh, new_mesh in prepared:
            if new_mesh.users == 0:
                bpy.data.meshes.remove(new_mesh)
        raise

    swapped = []
    try:
        for wall_object, old_mesh, new_mesh in prepared:
            wall_object.data = new_mesh
            swapped.append((wall_object, old_mesh, new_mesh))
    except Exception:
        for wall_object, old_mesh, _new_mesh in reversed(swapped):
            wall_object.data = old_mesh
        for _wall_object, _old_mesh, new_mesh in prepared:
            if new_mesh.users == 0:
                bpy.data.meshes.remove(new_mesh)
        raise
    for _wall_object, old_mesh, _new_mesh in prepared:
        if old_mesh.users == 0:
            bpy.data.meshes.remove(old_mesh)
