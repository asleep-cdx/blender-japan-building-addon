"""Pure canonical helpers for Build 07-A Stage 1 stairs."""

from dataclasses import dataclass
import math
import uuid


MIN_STAIR_PATH_LENGTH_M = 1.0e-6
STAGE1_PATH_POINT_COUNT = 2
IDENTITY_LOCATION = (0.0, 0.0, 0.0)
IDENTITY_ROTATION = (0.0, 0.0, 0.0)
IDENTITY_SCALE = (1.0, 1.0, 1.0)


@dataclass(frozen=True)
class StairAxes:
    """Resolved world-plan axes, independent from Blender mesh state."""

    forward: tuple
    left: tuple
    up: tuple = (0.0, 0.0, 1.0)


def generate_stair_id():
    """Return a persistent identity suitable for canonical storage."""
    return str(uuid.uuid4())


def canonical_path(points):
    """Validate and return exactly two ordered world-XY plan points."""
    if points is None or len(points) != STAGE1_PATH_POINT_COUNT:
        raise ValueError("Stage 1 Stair Pathは正確に2点である必要があります。")
    result = []
    for point in points:
        if point is None or len(point) < 2:
            raise ValueError("Stair Path点を取得できません。")
        x, y = float(point[0]), float(point[1])
        if not math.isfinite(x) or not math.isfinite(y):
            raise ValueError("Stair Path座標は有限値である必要があります。")
        result.append((x, y))
    dx = result[1][0] - result[0][0]
    dy = result[1][1] - result[0][1]
    if math.hypot(dx, dy) <= MIN_STAIR_PATH_LENGTH_M:
        raise ValueError("Stair Pathが短すぎます。")
    return tuple(result)


def resolve_lower_upper(points, ascent_direction):
    """Resolve elevation roles without changing canonical draw order."""
    path = canonical_path(points)
    if ascent_direction == "FORWARD":
        return path[0], path[1]
    if ascent_direction == "REVERSE":
        return path[1], path[0]
    raise ValueError("不明な上り方向です。")


def resolve_stair_axes(points, ascent_direction):
    """Return +X uphill, +Y left while facing uphill, and world +Z."""
    lower, upper = resolve_lower_upper(points, ascent_direction)
    dx, dy = upper[0] - lower[0], upper[1] - lower[1]
    length = math.hypot(dx, dy)
    forward = (dx / length, dy / length, 0.0)
    return StairAxes(forward, (-forward[1], forward[0], 0.0))


def identity_transform_contract():
    """Expose the required transform values for runtime and pure tests."""
    return IDENTITY_LOCATION, IDENTITY_ROTATION, IDENTITY_SCALE

