"""Pure registration and validation rules for project-local Custom Profiles.

Revision 1 deliberately accepts convex, simple contours only.  This keeps the
Curve cap and editable-Mesh contract provable; no convex hull or other lossy
replacement is ever made.
"""

from dataclasses import dataclass
import math
import uuid


CUSTOM_BEZIER_SEGMENTS_PER_SPAN_R1 = 16
CUSTOM_MAX_CONTOUR_POINTS = 1024
CUSTOM_COORDINATE_TOLERANCE_M = 1.0e-7
CUSTOM_AREA_EPSILON_M2 = 1.0e-12
CUSTOM_PROFILE_SCHEMA_VERSION = 1
CUSTOM_PROFILE_REVISION = 1
RESERVED_PROFILE_IDS = frozenset(("SIMPLE", "BEVEL", "ROUNDED", "SIMPLE_10X60"))


@dataclass(frozen=True)
class CustomProfileSnapshot:
    """Blender-independent immutable canonical registration result."""

    profile_id: str
    profile_revision: int
    schema_version: int
    source_type: str
    contour: tuple
    bounds: tuple
    smooth_edges: tuple


def new_custom_profile_id():
    """Return a collision-resistant identity that cannot be a standard ID."""
    return "CUSTOM-" + str(uuid.uuid4())


def validate_custom_profile_id(value):
    if not isinstance(value, str) or not value or value in RESERVED_PROFILE_IDS:
        raise ValueError("Custom Profile IDが不正です。")
    if not value.startswith("CUSTOM-"):
        raise ValueError("Custom Profile IDが予約済みIDと区別できません。")
    return value


def validate_uniform_scale(value):
    value = float(value)
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError("Custom Profile scaleは有限の正数である必要があります。")
    return value


def _point(value):
    if len(value) < 2:
        raise ValueError("Profile座標が不正です。")
    result = (float(value[0]), float(value[1]))
    if not all(math.isfinite(item) for item in result):
        raise ValueError("Profile座標は有限である必要があります。")
    return result


def points_close(first, second, tolerance=CUSTOM_COORDINATE_TOLERANCE_M):
    return (abs(first[0] - second[0]) <= tolerance
            and abs(first[1] - second[1]) <= tolerance)


def remove_adjacent_duplicates(points, tolerance=CUSTOM_COORDINATE_TOLERANCE_M):
    result = []
    for value in points:
        point = _point(value)
        if not result or not points_close(result[-1], point, tolerance):
            result.append(point)
    if len(result) > 1 and points_close(result[0], result[-1], tolerance):
        result.pop()
    return tuple(result)


def signed_area(points):
    return 0.5 * sum(first[0] * second[1] - second[0] * first[1]
                     for first, second in zip(points, points[1:] + points[:1]))


def contour_bounds(points):
    xs, ys = zip(*points)
    return min(xs), max(xs), min(ys), max(ys)


def _orientation(a, b, c, epsilon=CUSTOM_COORDINATE_TOLERANCE_M):
    cross = ((b[0] - a[0]) * (c[1] - a[1])
             - (b[1] - a[1]) * (c[0] - a[0]))
    return 0 if abs(cross) <= epsilon else (1 if cross > 0 else -1)


def _on_segment(a, b, p, epsilon=CUSTOM_COORDINATE_TOLERANCE_M):
    return (_orientation(a, b, p, epsilon) == 0
            and min(a[0], b[0]) - epsilon <= p[0] <= max(a[0], b[0]) + epsilon
            and min(a[1], b[1]) - epsilon <= p[1] <= max(a[1], b[1]) + epsilon)


def segments_intersect(a, b, c, d):
    values = (_orientation(a, b, c), _orientation(a, b, d),
              _orientation(c, d, a), _orientation(c, d, b))
    if values[0] * values[1] < 0 and values[2] * values[3] < 0:
        return True
    return ((values[0] == 0 and _on_segment(a, b, c))
            or (values[1] == 0 and _on_segment(a, b, d))
            or (values[2] == 0 and _on_segment(c, d, a))
            or (values[3] == 0 and _on_segment(c, d, b)))


def has_self_intersection(points):
    count = len(points)
    for first in range(count):
        a, b = points[first], points[(first + 1) % count]
        for second in range(first + 1, count):
            if second in (first, (first + 1) % count) or first == (second + 1) % count:
                continue
            if segments_intersect(a, b, points[second], points[(second + 1) % count]):
                return True
    return False


def is_convex(points):
    turns = {_orientation(points[i], points[(i + 1) % len(points)],
                          points[(i + 2) % len(points)])
             for i in range(len(points))}
    turns.discard(0)
    return len(turns) <= 1


def normalize_poly_contour(points):
    """Return a validated clockwise production contour without a closing point."""
    contour = remove_adjacent_duplicates(points)
    if len(contour) < 3:
        raise ValueError("Profileには3個以上の有効な点が必要です。")
    if len(contour) > CUSTOM_MAX_CONTOUR_POINTS:
        raise ValueError("Profile点数が上限を超えています。")
    bounds = contour_bounds(contour)
    if bounds[0] < -CUSTOM_COORDINATE_TOLERANCE_M or bounds[2] < -CUSTOM_COORDINATE_TOLERANCE_M:
        raise ValueError("Profile座標は+X/+Y領域に配置してください。")
    area = signed_area(contour)
    if abs(area) <= CUSTOM_AREA_EPSILON_M2:
        raise ValueError("Profile面積が小さすぎます。")
    if has_self_intersection(contour):
        raise ValueError("Profile輪郭が自己交差または接触しています。")
    if not is_convex(contour):
        raise ValueError("revision 1では凹形Custom Profileを使用できません。")
    # Standard SIMPLE/BEVEL/ROUNDED Profiles are clockwise (negative signed
    # area).  Custom revision 1 uses that same production winding contract.
    if area > 0.0:
        contour = tuple(reversed(contour))
    return contour


def cubic_bezier(p0, p1, p2, p3, t):
    p0, p1, p2, p3 = map(_point, (p0, p1, p2, p3))
    t = float(t); u = 1.0 - t
    return (u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
            u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1])


def bezier_span_is_straight(p0, p1, p2, p3):
    """Whether all controls lie on the endpoint line (a planar segment)."""
    p0, p1, p2, p3 = map(_point, (p0, p1, p2, p3))
    return (_orientation(p0, p3, p1) == 0
            and _orientation(p0, p3, p2) == 0)


def sample_cyclic_bezier(knots, segments=CUSTOM_BEZIER_SEGMENTS_PER_SPAN_R1):
    """Sample each cyclic span at t=0..(segments-1)/segments exactly once."""
    segments = int(segments)
    if segments != CUSTOM_BEZIER_SEGMENTS_PER_SPAN_R1:
        raise ValueError("未対応のBezier sampling revisionです。")
    if len(knots) * segments > CUSTOM_MAX_CONTOUR_POINTS:
        raise ValueError("Bezier sampling後のProfile点数が上限を超えます。")
    sampled = []
    for index, knot in enumerate(knots):
        nxt = knots[(index + 1) % len(knots)]
        p0, outgoing = _point(knot[0]), _point(knot[1])
        incoming, p3 = _point(nxt[2]), _point(nxt[0])
        sampled.extend(cubic_bezier(p0, outgoing, incoming, p3, step / segments)
                       for step in range(segments))
    return normalize_poly_contour(sampled)


def scaled_contour(contour, scale):
    scale = validate_uniform_scale(scale)
    return tuple((x * scale, y * scale) for x, y in contour)


def mirrored_contour(contour):
    """Mirror derived geometry across X=0 and preserve canonical winding."""
    return tuple((-x, y) for x, y in reversed(contour))


def mirrored_edge_indices(point_count, edge_indices):
    """Remap canonical edges after ``reversed(mirror(contour))``.

    Canonical edge ``i`` joins ``p[i]`` to ``p[i+1]``.  In the reversed
    contour that same physical edge starts at ``n - 2 - i``.
    """
    count = int(point_count)
    if count < 1:
        return ()
    return tuple(sorted((count - 2 - int(index)) % count
                        for index in edge_indices))


def oriented_edge_indices(point_count, edge_indices, horizontal_sign):
    if not math.isfinite(float(horizontal_sign)):
        raise ValueError("Profile orientationが不正です。")
    canonical = tuple(sorted(int(index) for index in edge_indices))
    return (canonical if float(horizontal_sign) >= 0.0
            else mirrored_edge_indices(point_count, canonical))


def make_snapshot(source_type, points=None, knots=None, profile_id=None):
    source_type = str(source_type).upper()
    if source_type == "POLY":
        contour = normalize_poly_contour(points or ())
        smooth = ()
    elif source_type == "BEZIER":
        knots = tuple(knots or ())
        contour = sample_cyclic_bezier(knots)
        # Each sampled edge belongs to its source span.  Curved spans are
        # smooth; collinear-control spans stay planar/hard.  If winding was
        # reversed, remap edge indices rather than globally smoothing.
        flags = []
        for index, knot in enumerate(knots):
            nxt = knots[(index + 1) % len(knots)]
            curved = not bezier_span_is_straight(
                knot[0], knot[1], nxt[2], nxt[0])
            flags.extend((curved,) * CUSTOM_BEZIER_SEGMENTS_PER_SPAN_R1)
        raw = tuple(cubic_bezier(knot[0], knot[1],
                                knots[(index + 1) % len(knots)][2],
                                knots[(index + 1) % len(knots)][0], step /
                                CUSTOM_BEZIER_SEGMENTS_PER_SPAN_R1)
                    for index, knot in enumerate(knots)
                    for step in range(CUSTOM_BEZIER_SEGMENTS_PER_SPAN_R1))
        if len(contour) != len(raw):
            # Coincident adjacent samples are normalized; conservative hard
            # intent avoids falsely smoothing a sharp transition.
            smooth = ()
        elif signed_area(raw) > 0.0:
            count = len(flags)
            smooth = tuple(index for index in range(count)
                           if flags[(count - 2 - index) % count])
        else:
            smooth = tuple(index for index, value in enumerate(flags) if value)
    else:
        raise ValueError("POLYまたはBEZIERのみ登録できます。")
    return CustomProfileSnapshot(
        validate_custom_profile_id(profile_id or new_custom_profile_id()),
        CUSTOM_PROFILE_REVISION, CUSTOM_PROFILE_SCHEMA_VERSION, source_type,
        contour, contour_bounds(contour), smooth)


def find_definition(library, profile_id, revision, schema):
    matches = [item for item in (library or ())
               if item.profile_id == profile_id
               and int(item.profile_revision) == int(revision)
               and int(item.schema_version) == int(schema)]
    if len(matches) != 1:
        raise ValueError("登録済みCustom Profile定義が見つかりません。")
    return matches[0]


def profile_is_referenced(objects, profile_id, revision=1, schema=1):
    return any(getattr(getattr(obj, "jhm_finish", None), "is_finish", False)
               and obj.jhm_finish.profile_id == profile_id
               and obj.jhm_finish.profile_revision == revision
               and obj.jhm_finish.profile_schema_version == schema
               for obj in objects)
