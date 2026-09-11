"""Pure canonical-centerline helpers for interactive Wall drawing."""

import math
from collections import namedtuple


_MIN_WALL_LENGTH_M = 1.0e-6
_EXTENSION_BOUNDARY_EPSILON_M = 1.0e-9

ExtensionProjection = namedtuple(
    "ExtensionProjection", ("point", "reference_endpoint", "axis", "side")
)


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
