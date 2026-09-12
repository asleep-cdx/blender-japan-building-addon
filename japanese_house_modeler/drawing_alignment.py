"""Pure canonical-centerline helpers for interactive Wall drawing."""

import math
from collections import namedtuple


_MIN_WALL_LENGTH_M = 1.0e-6
_EXTENSION_BOUNDARY_EPSILON_M = 1.0e-9
_MIN_SPLIT_SEGMENT_M = 0.001

ExtensionProjection = namedtuple(
    "ExtensionProjection", ("point", "reference_endpoint", "axis", "side")
)
SegmentProjection = namedtuple(
    "SegmentProjection", ("point", "parameter", "length", "axis")
)


def project_to_wall_segment(raw_point, start, end):
    """Project a point onto the strict interior of a canonical Wall segment."""
    try:
        px, py = float(raw_point[0]), float(raw_point[1])
        sx, sy = float(start[0]), float(start[1])
        ex, ey = float(end[0]), float(end[1])
    except (IndexError, TypeError, ValueError):
        return None
    if not all(math.isfinite(value) for value in (px, py, sx, sy, ex, ey)):
        return None
    dx, dy = ex - sx, ey - sy
    length = math.hypot(dx, dy)
    if length <= _MIN_WALL_LENGTH_M:
        return None
    axis = dx / length, dy / length
    parameter = (px - sx) * axis[0] + (py - sy) * axis[1]
    if (parameter <= _EXTENSION_BOUNDARY_EPSILON_M
            or parameter >= length - _EXTENSION_BOUNDARY_EPSILON_M):
        return None
    point = (sx + axis[0] * parameter, sy + axis[1] * parameter, 0.0)
    return SegmentProjection(point, parameter, length, (*axis, 0.0))


def is_safe_split_projection(projection, threshold=_MIN_SPLIT_SEGMENT_M):
    """Require both child segments to be strictly longer than ``threshold``."""
    try:
        parameter = float(projection.parameter)
        length = float(projection.length)
        threshold = float(threshold)
    except (AttributeError, TypeError, ValueError):
        return False
    return (all(math.isfinite(value) for value in (parameter, length, threshold))
            and threshold >= 0.0
            and parameter > threshold
            and length - parameter > threshold)


def constrained_direction(start, raw_point, step_degrees=15.0):
    """Return the nearest angular-step forward unit direction in canonical XY."""
    try:
        dx = float(raw_point[0]) - float(start[0])
        dy = float(raw_point[1]) - float(start[1])
        step = math.radians(float(step_degrees))
    except (IndexError, TypeError, ValueError):
        return None
    if not all(math.isfinite(value) for value in (dx, dy, step)) or step <= 0.0:
        return None
    if math.hypot(dx, dy) <= _MIN_WALL_LENGTH_M:
        return None
    angle = round(math.atan2(dy, dx) / step) * step
    return math.cos(angle), math.sin(angle), 0.0


def intersect_forward_ray_segment(origin, direction, start, end):
    """Intersect a forward XY ray with a safely interior Wall segment."""
    try:
        ox, oy = float(origin[0]), float(origin[1])
        rx, ry = float(direction[0]), float(direction[1])
        sx, sy = float(start[0]), float(start[1])
        ex, ey = float(end[0]), float(end[1])
    except (IndexError, TypeError, ValueError):
        return None
    if not all(math.isfinite(v) for v in (ox, oy, rx, ry, sx, sy, ex, ey)):
        return None
    ray_length = math.hypot(rx, ry)
    segment_length = math.hypot(ex - sx, ey - sy)
    if ray_length <= _MIN_WALL_LENGTH_M or segment_length <= _MIN_WALL_LENGTH_M:
        return None
    rx, ry = rx / ray_length, ry / ray_length
    dx, dy = ex - sx, ey - sy
    cross = rx * dy - ry * dx
    if abs(cross) <= _EXTENSION_BOUNDARY_EPSILON_M:
        return None
    qx, qy = sx - ox, sy - oy
    ray_parameter = (qx * dy - qy * dx) / cross
    segment_fraction = (qx * ry - qy * rx) / cross
    if ray_parameter < 0.0:
        return None
    projection = SegmentProjection(
        (ox + ray_parameter * rx, oy + ray_parameter * ry, 0.0),
        segment_fraction * segment_length,
        segment_length,
        (dx / segment_length, dy / segment_length, 0.0),
    )
    return projection if is_safe_split_projection(projection) else None


def canonical_split_segments(start, end, point):
    """Return deterministic START- and END-side canonical segment endpoints."""
    projection = project_to_wall_segment(point, start, end)
    if projection is None or not is_safe_split_projection(projection):
        return None
    return ((tuple(start), projection.point), (projection.point, tuple(end)))


def same_host_connection_forbidden(start_mid_host, end_mid_host,
                                   start_endpoint_host=None,
                                   end_endpoint_host=None):
    """Reject same-host pairs only when at least one target is mid-segment."""
    if start_mid_host is None and end_mid_host is None:
        return False
    start_host = (
        start_mid_host if start_mid_host is not None else start_endpoint_host
    )
    end_host = end_mid_host if end_mid_host is not None else end_endpoint_host
    return start_host is not None and start_host is end_host


def select_unambiguous_candidate(candidates, tie_epsilon=1.0e-6):
    """Select the uniquely closest ``(distance, value)`` candidate."""
    valid = [item for item in candidates if math.isfinite(item[0])]
    if not valid:
        return None
    valid.sort(key=lambda item: item[0])
    if len(valid) > 1 and abs(valid[0][0] - valid[1][0]) <= tie_epsilon:
        return None
    return valid[0][1]


def wall_axis_angle_degrees(start, end):
    """Return the direction-independent canonical XY axis angle."""
    try:
        sx, sy = float(start[0]), float(start[1])
        ex, ey = float(end[0]), float(end[1])
    except (IndexError, TypeError, ValueError):
        return None
    if not all(math.isfinite(value) for value in (sx, sy, ex, ey)):
        return None
    dx, dy = ex - sx, ey - sy
    if math.hypot(dx, dy) <= _MIN_WALL_LENGTH_M:
        return None
    angle = math.degrees(math.atan2(dy, dx)) % 180.0
    return 0.0 if math.isclose(angle, 180.0) else angle


def wall_length_m(start, end):
    """Derive Wall length only from canonical start/end XY coordinates."""
    try:
        dx = float(end[0]) - float(start[0])
        dy = float(end[1]) - float(start[1])
    except (IndexError, TypeError, ValueError):
        return None
    length = math.hypot(dx, dy)
    return length if math.isfinite(length) and length > _MIN_WALL_LENGTH_M else None


def endpoint_move_midpoint_valid(source, host, projection):
    """Pure guard shared by endpoint-move preview and commit."""
    return source is not host and is_safe_split_projection(projection)


def project_to_wall_extension(raw_point, start, end):
    """Project onto a canonical line only when outside its saved segment."""
    try:
        px, py = float(raw_point[0]), float(raw_point[1])
        sx, sy = float(start[0]), float(start[1])
        ex, ey = float(end[0]), float(end[1])
    except (IndexError, TypeError, ValueError):
        return None
    values = (px, py, sx, sy, ex, ey)
    if not all(math.isfinite(value) for value in values):
        return None
    dx, dy = ex - sx, ey - sy
    length = math.hypot(dx, dy)
    if length <= _MIN_WALL_LENGTH_M:
        return None
    axis = dx / length, dy / length
    parameter = (px - sx) * axis[0] + (py - sy) * axis[1]
    if parameter < -_EXTENSION_BOUNDARY_EPSILON_M:
        reference, side = (sx, sy, 0.0), "START"
    elif parameter > length + _EXTENSION_BOUNDARY_EPSILON_M:
        reference, side = (ex, ey, 0.0), "END"
    else:
        return None
    point = (sx + axis[0] * parameter, sy + axis[1] * parameter, 0.0)
    return ExtensionProjection(point, reference, (*axis, 0.0), side)


def extension_geometry_key(projection):
    """Return an object-order-independent key for equal-distance candidates."""
    return (
        tuple(projection.point),
        tuple(projection.reference_endpoint),
        tuple(projection.axis),
        0 if projection.side == "START" else 1,
    )


def combined_axis_alignment(raw_point, x_reference=None, y_reference=None):
    """Apply the established X and Y alignments to one final candidate point."""
    try:
        x = float(x_reference[0]) if x_reference is not None else float(raw_point[0])
        y = float(y_reference[1]) if y_reference is not None else float(raw_point[1])
        z = float(raw_point[2]) if len(raw_point) > 2 else 0.0
    except (IndexError, TypeError, ValueError):
        return None
    if not all(math.isfinite(value) for value in (x, y, z)):
        return None
    return x, y, z
