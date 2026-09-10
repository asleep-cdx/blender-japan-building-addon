"""Derived Wall joint geometry and atomic Mesh regeneration."""

import math

import bpy

from .connections import is_valid_wall_object, junction_members
from .junctions import (
    CONTINUATION, CORNER, CROSS, ISOLATED, T_JUNCTION, classify_junction,
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
_CROSS_THROUGH_THICKNESS_TOLERANCE_MM = 1.0e-6
_CROSS_PARAMETER_TOLERANCE_M = 1.0e-9
_MAX_CROSS_TRIM_FACTOR = 10.0
_TRANSFORM_EPSILON = 1.0e-6


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


def calculate_cross_solution(wall_object, endpoint):
    """Resolve roles and both butt trims as one all-or-nothing Cross solution."""
    classification = classify_junction(wall_object, endpoint)
    if classification.key != CROSS or classification.member_count != 4:
        return None
    pairs = cross_junction_pairs(wall_object, endpoint)
    if pairs is None:
        return None
    members = tuple(member for pair in pairs for member in pair)
    data_by_member = [(member, endpoint_data(*member)) for member in members]
    if any(data is None for _member, data in data_by_member):
        return None
    if any(not has_identity_transform(member[0]) for member in members):
        return None
    junction = data_by_member[0][1][0]
    if any(
        _distance(data[0], junction) > _JOINT_POSITION_TOLERANCE_M
        for _member, data in data_by_member[1:]
    ):
        return None

    pair_data = []
    for pair in pairs:
        first = endpoint_data(*pair[0])
        second = endpoint_data(*pair[1])
        cross = first[1][0] * second[1][1] - first[1][1] * second[1][0]
        dot = first[1][0] * second[1][0] + first[1][1] * second[1][1]
        if abs(cross) > _CROSS_PAIR_COLLINEAR_TOLERANCE or dot >= 0.0:
            return None
        axis = _canonical_axis(first[1], second[1])
        if axis is None:
            return None
        pair_data.append((pair, first, axis))

    axis_cross = (
        pair_data[0][2][0] * pair_data[1][2][1]
        - pair_data[0][2][1] * pair_data[1][2][0]
    )
    if abs(axis_cross) <= _CROSS_PAIR_COLLINEAR_TOLERANCE:
        return None

    # Maximise world-X alignment, then canonical y (and x) to settle geometric
    # ties such as +45/-45 degrees without consulting object or member identity.
    through_index = max(
        range(2), key=lambda index: (
            abs(pair_data[index][2][0]),
            pair_data[index][2][1],
            pair_data[index][2][0],
        )
    )
    through_members, host, host_axis = pair_data[through_index]
    butt_members, _butt_reference, _butt_axis = pair_data[1 - through_index]
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


def endpoint_joint_pair(wall_object, endpoint):
    """Return the effective endpoint pair and its derived UI status key."""
    square = square_endpoint_pair(wall_object, endpoint)
    if square is None:
        return None, "FALLBACK"
    classification = classify_junction(wall_object, endpoint)
    if classification.key == ISOLATED:
        return square, "ISOLATED"
    if classification.key == CONTINUATION and classification.member_count == 2:
        return square, "CONTINUATION"
    if classification.key == T_JUNCTION and classification.member_count == 3:
        solution = calculate_t_solution(wall_object, endpoint)
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
            return square, "FALLBACK"
        through_members, butt_trims, _junction, _host_axis = solution
        current = (wall_object, endpoint)
        if any(member[0] is current[0] and member[1] == current[1] for member in through_members):
            return square, "CROSS_THROUGH"
        for member, trim_pair in butt_trims:
            if member[0] is current[0] and member[1] == current[1]:
                return trim_pair, "CROSS_BUTT"
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


def joint_status_label(wall_object, endpoint):
    """Return a read-only Japanese label for the effective joint treatment."""
    _start, _end, statuses = _resolved_endpoint_pairs(wall_object)
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


def _resolved_endpoint_pairs(wall_object):
    """Resolve polygon-level fallback and report each endpoint's effective state."""
    squares = {
        endpoint: square_endpoint_pair(wall_object, endpoint)
        for endpoint in ("START", "END")
    }
    requested = {
        endpoint: endpoint_joint_pair(wall_object, endpoint)
        for endpoint in ("START", "END")
    }
    if any(pair is None for pair in squares.values()):
        return None, None, {"START": "FALLBACK", "END": "FALLBACK"}
    pairs = {endpoint: requested[endpoint][0] for endpoint in requested}
    statuses = {endpoint: requested[endpoint][1] for endpoint in requested}

    def valid():
        return validate_lower_polygon(
            [pairs["START"][0], pairs["START"][1], pairs["END"][0], pairs["END"][1]]
        )

    if not valid():
        # A shared unsafe T/Cross is rejected earlier for all members.  This
        # branch is intentionally Wall-local: a safe branch trim can still be
        # incompatible with this Wall's independently resolved opposite-end
        # joint, in which case only this visual endpoint is squared off.
        for endpoint in ("START", "END"):
            if statuses[endpoint] not in {"MITER", "T_BRANCH", "CROSS_BUTT"}:
                continue
            pairs[endpoint] = squares[endpoint]
            statuses[endpoint] = "FALLBACK"
            if valid():
                break
    if not valid():
        pairs = squares
        for endpoint in statuses:
            if statuses[endpoint] in {"MITER", "T_BRANCH", "CROSS_BUTT"}:
                statuses[endpoint] = "FALLBACK"
    return pairs["START"], pairs["END"], statuses


def _cross(first, second, third):
    return ((second[0] - first[0]) * (third[1] - first[1])) - (
        (second[1] - first[1]) * (third[0] - first[0])
    )


def _segments_cross(first, second, third, fourth):
    a = _cross(first, second, third)
    b = _cross(first, second, fourth)
    c = _cross(third, fourth, first)
    d = _cross(third, fourth, second)
    return a * b < 0.0 and c * d < 0.0


def validate_lower_polygon(points):
    """Validate finiteness, area, and non-adjacent edge intersections."""
    if len(points) != 4 or not all(
        math.isfinite(value) for point in points for value in point
    ):
        return False
    area = abs(
        sum(
            point[0] * points[(index + 1) % 4][1]
            - points[(index + 1) % 4][0] * point[1]
            for index, point in enumerate(points)
        )
    ) * 0.5
    return area > _POLYGON_AREA_EPSILON and not (
        _segments_cross(points[0], points[1], points[2], points[3])
        or _segments_cross(points[1], points[2], points[3], points[0])
    )


def build_wall_geometry(wall_object):
    """Build joint-aware cuboid geometry exclusively from canonical Wall data."""
    try:
        height = float(wall_object.jhm_wall.wall_height) / 1000.0
        thickness = float(wall_object.jhm_wall.wall_thickness)
    except (AttributeError, ReferenceError, TypeError, ValueError):
        return None
    if not math.isfinite(height) or height <= 0.0 or thickness <= 0.0:
        return None
    start_pair, end_pair, _statuses = _resolved_endpoint_pairs(wall_object)
    if start_pair is None or end_pair is None:
        return None
    lower = [start_pair[0], start_pair[1], end_pair[0], end_pair[1]]
    if not validate_lower_polygon(lower):
        return None
    vertices = [(point[0], point[1], 0.0) for point in lower]
    vertices.extend((point[0], point[1], height) for point in lower)
    faces = (
        (0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
        (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),
    )
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
