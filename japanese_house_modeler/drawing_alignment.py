"""Pure canonical-centerline helpers for interactive Wall drawing."""

import math
from collections import namedtuple


_MIN_WALL_LENGTH_M = 1.0e-6
_EXTENSION_BOUNDARY_EPSILON_M = 1.0e-9

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


def canonical_split_segments(start, end, point):
    """Return deterministic START- and END-side canonical segment endpoints."""
    projection = project_to_wall_segment(point, start, end)
    if projection is None:
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
