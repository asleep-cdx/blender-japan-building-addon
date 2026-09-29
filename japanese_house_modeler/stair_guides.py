"""Pure Stage-2 guide and path-point relocation mathematics.

The module has no Blender dependency.  Screen-space projection stays in the
operator; these helpers resolve canonical world-XY candidates only.
"""

from dataclasses import dataclass
import math

from .drawing_alignment import constrained_direction, select_unambiguous_candidate
from .stair_multiflight import canonical_multi_path


GUIDE_THRESHOLD_PX = 10.0


@dataclass(frozen=True)
class MoveCandidate:
    points: tuple
    point_ids: tuple
    moved_index: int
    guide: str


@dataclass(frozen=True)
class MoveGuideLine:
    """Raw-independent infinite structural guide in canonical world XY."""
    name: str
    origin: tuple
    direction: tuple


@dataclass(frozen=True)
class RightAngleGuideRays:
    """Persistent visual state for the two valid L-creation directions."""
    origin: tuple
    left_direction: tuple
    right_direction: tuple


def creation_right_angle_guide_rays(p0, p1):
    """Return the two opposite unit rays perpendicular to confirmed P0->P1."""
    start = tuple(map(float, p0[:2]))
    turn = tuple(map(float, p1[:2]))
    incoming = turn[0] - start[0], turn[1] - start[1]
    length = math.hypot(*incoming)
    if length <= 1.0e-6 or not all(math.isfinite(value)
                                   for value in start + turn):
        raise ValueError("90度creation guideのconfirmed Pathが不正です。")
    unit = incoming[0] / length, incoming[1] / length
    left = -unit[1], unit[0]
    return RightAngleGuideRays(turn, left, (-left[0], -left[1]))


def move_anchor_index(point_count, moved_index):
    """Return the canonical anchor; ascent direction intentionally is irrelevant."""
    if not 0 <= moved_index < point_count or point_count < 2:
        raise ValueError("移動Path点indexが不正です。")
    return 1 if moved_index == 0 else moved_index - 1


def endpoint_right_angle_guide_line(points, moved_index):
    """Return the exact START/END relocation locus for any N-point path."""
    points = tuple(tuple(map(float, p[:2])) for p in points)
    if len(points) < 3 or moved_index not in (0, len(points) - 1):
        raise ValueError("endpoint 90度guideには3点以上のSTART/ENDが必要です。")
    if moved_index == 0:
        turn, fixed = points[1], points[2]
    else:
        turn, fixed = points[-2], points[-3]
    axis = fixed[0] - turn[0], fixed[1] - turn[1]
    length = math.hypot(*axis)
    if length <= 1.0e-6:
        raise ValueError("90度guideの固定Flightが短すぎます。")
    return MoveGuideLine(
        "RIGHT_ANGLE", turn, (-axis[1] / length, axis[0] / length))


def endpoint_right_angle_candidate(points, moved_index, raw_point):
    """Project raw input onto the shared endpoint guide-line authority."""
    line = endpoint_right_angle_guide_line(points, moved_index)
    turn, normal = line.origin, line.direction
    delta = (float(raw_point[0]) - turn[0], float(raw_point[1]) - turn[1])
    t = delta[0] * normal[0] + delta[1] * normal[1]
    if abs(t) <= 1.0e-6:
        raise ValueError("90度guide candidateが短すぎます。")
    return turn[0] + t * normal[0], turn[1] + t * normal[1]


def _line_from_points(name, start, end):
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = math.hypot(dx, dy)
    if length <= 1.0e-6:
        return None
    return MoveGuideLine(name, tuple(start), (dx / length, dy / length))


def _same_infinite_line(first, second):
    cross = first.direction[0] * second.direction[1] - first.direction[1] * second.direction[0]
    delta = second.origin[0] - first.origin[0], second.origin[1] - first.origin[1]
    offset = delta[0] * first.direction[1] - delta[1] * first.direction[0]
    return abs(cross) <= 1.0e-9 and abs(offset) <= 1.0e-9


def move_persistent_guides(points, moved_index):
    """Return structural lines available before raw cursor input exists."""
    points = tuple(tuple(map(float, point[:2])) for point in points)
    if len(points) < 3 or not 0 <= moved_index < len(points):
        raise ValueError("persistent guideのPath point indexが不正です。")
    guides = []
    if moved_index in (0, len(points) - 1):
        guides.append(endpoint_right_angle_guide_line(points, moved_index))
    for neighbor in (moved_index - 1, moved_index + 1):
        if 0 <= neighbor < len(points):
            line = _line_from_points(
                "SEGMENT_EXTENSION", points[moved_index], points[neighbor])
            if line is not None:
                guides.append(line)
    anchor_index = move_anchor_index(len(points), moved_index)
    anchor = points[anchor_index]
    for start, end in zip(points, points[1:]):
        line = _line_from_points("PARALLEL", anchor,
                                 (anchor[0] + end[0] - start[0],
                                  anchor[1] + end[1] - start[1]))
        if line is not None:
            guides.append(line)
    unique = []
    for guide in guides:
        if any(_same_infinite_line(guide, saved) for saved in unique):
            continue
        unique.append(guide)
    return tuple(unique)


def turn_right_angle_candidate(points, raw_point, *, shift=False):
    """Return the closest Thales-circle point, or its Shift-constrained ray root."""
    p0, _old, p2 = (tuple(map(float, p[:2])) for p in points)
    raw = tuple(map(float, raw_point[:2]))
    if shift:
        direction = constrained_direction(p0, raw, step_degrees=15.0)
        if direction is None:
            raise ValueError("Shift方向を解決できません。")
        chord = (p2[0] - p0[0], p2[1] - p0[1])
        t = chord[0] * direction[0] + chord[1] * direction[1]
        if t <= 1.0e-6:
            raise ValueError("Shiftと90度を同時に満たす非退化解がありません。")
        return p0[0] + t * direction[0], p0[1] + t * direction[1]
    center = ((p0[0] + p2[0]) / 2.0, (p0[1] + p2[1]) / 2.0)
    radius = math.hypot(p2[0] - p0[0], p2[1] - p0[1]) / 2.0
    delta = (raw[0] - center[0], raw[1] - center[1])
    distance = math.hypot(*delta)
    if radius <= 1.0e-6 or distance <= 1.0e-6:
        raise ValueError("TURN 90度guideを一意に解決できません。")
    return center[0] + radius * delta[0] / distance, center[1] + radius * delta[1] / distance


def aligned_candidates(raw_point, reference_points):
    """Return world X/Y alignment candidates; references create no dependency."""
    x, y = map(float, raw_point[:2])
    result = []
    for reference in reference_points:
        rx, ry = map(float, reference[:2])
        result.extend(((rx, y), (x, ry)))
    return tuple(result)


def project_to_line(raw_point, line_start, line_end):
    """Project a world-XY point onto an infinite extension/parallel guide."""
    raw = tuple(map(float, raw_point[:2]))
    start = tuple(map(float, line_start[:2]))
    end = tuple(map(float, line_end[:2]))
    axis = end[0] - start[0], end[1] - start[1]
    length_squared = axis[0] * axis[0] + axis[1] * axis[1]
    if length_squared <= 1.0e-12:
        return None
    t = ((raw[0] - start[0]) * axis[0]
         + (raw[1] - start[1]) * axis[1]) / length_squared
    return start[0] + t * axis[0], start[1] + t * axis[1]


def endpoint_shift_candidate(points, moved_index, raw_point):
    """Solve endpoint Shift and exact-90 simultaneously, never sequentially."""
    points = tuple(tuple(map(float, p[:2])) for p in points)
    if len(points) < 3 or moved_index not in (0, len(points) - 1):
        raise ValueError("Endpoint Shiftには3点以上のSTART/ENDが必要です。")
    line = endpoint_right_angle_guide_line(points, moved_index)
    anchor = line.origin
    direction = constrained_direction(anchor, raw_point, step_degrees=15.0)
    if direction is None:
        raise ValueError("Shift方向を解決できません。")
    # The rounded ray itself must be the 90-degree locus.  Reprojection after
    # rounding would violate the explicit Shift contract.
    if abs(direction[0] * line.direction[1]
           - direction[1] * line.direction[0]) > 1.0e-6:
        raise ValueError("Shift 15度とLanding 90度を同時に満たせません。")
    length = math.hypot(float(raw_point[0]) - anchor[0],
                        float(raw_point[1]) - anchor[1])
    if length <= 1.0e-6:
        raise ValueError("Shift candidateが短すぎます。")
    return anchor[0] + direction[0] * length, anchor[1] + direction[1] * length


def resolve_move_candidate(points, point_ids, moved_index, raw_point, *,
                           shift=False, guide_candidates=(), distances=(),
                           guide_names=(), threshold_px=GUIDE_THRESHOLD_PX):
    """Resolve preview/commit identically and filter every snap through strict L validity."""
    original = tuple(tuple(map(float, p[:2])) for p in points)
    anchor = original[move_anchor_index(len(original), moved_index)]
    raw = tuple(map(float, raw_point[:2]))
    if len(original) > 3:
        candidates = []
        if shift:
            direction = constrained_direction(anchor, raw, step_degrees=15.0)
            if direction is not None:
                distance = math.hypot(raw[0] - anchor[0], raw[1] - anchor[1])
                candidates.append((0.0, (anchor[0] + direction[0] * distance,
                                         anchor[1] + direction[1] * distance), "SHIFT"))
        else:
            candidates.append((0.0, raw, "FREE"))
            candidates.extend((float(distance), tuple(point[:2]),
                               tuple(guide_names)[index]
                               if index < len(tuple(guide_names)) else "ALIGNMENT")
                              for index, (distance, point) in enumerate(
                                  zip(distances, guide_candidates))
                              if float(distance) <= float(threshold_px))
        valid = []
        for distance, point, name in candidates:
            candidate = list(original)
            candidate[moved_index] = point
            try:
                path = canonical_multi_path(candidate, point_ids)
            except ValueError:
                continue
            resolved = tuple(p.xy for p in path)
            if any(math.hypot(resolved[moved_index][0] - saved[1][0][moved_index][0],
                              resolved[moved_index][1] - saved[1][0][moved_index][1])
                   <= 1.0e-9 for saved in valid):
                continue
            valid.append((distance, (resolved, name)))
        selected = select_unambiguous_candidate(valid)
        if selected is None:
            if moved_index not in (0, len(original) - 1):
                raise ValueError("この折れ点は他のPath点を固定したままでは90度条件を維持して移動できません。")
            raise ValueError("guide candidateが曖昧またはPath全体条件を満たしません。")
        resolved, guide = selected
        return MoveCandidate(resolved, tuple(point_ids), moved_index, guide)
    if shift:
        point = (turn_right_angle_candidate(original, raw, shift=True)
                 if moved_index == 1 else
                 endpoint_shift_candidate(original, moved_index, raw))
        result = list(original)
        result[moved_index] = point
        path = canonical_multi_path(result, point_ids)
        return MoveCandidate(tuple(p.xy for p in path),
                             tuple(p.point_id for p in path), moved_index, "SHIFT")
    # A free raw point is valid only when it already satisfies strict L.
    candidates = []
    raw_points = list(original)
    raw_points[moved_index] = raw
    try:
        canonical_multi_path(raw_points, point_ids)
    except ValueError:
        pass
    else:
        candidates.append((0.0, raw, "FREE"))
    names = tuple(guide_names)
    for index, (distance, point) in enumerate(zip(distances, guide_candidates)):
        distance = float(distance)
        if not math.isfinite(distance) or distance > float(threshold_px):
            continue
        candidate_points = list(original)
        candidate_points[moved_index] = tuple(point[:2])
        try:
            canonical_multi_path(candidate_points, point_ids)
        except ValueError:
            continue
        name = names[index] if index < len(names) else "ALIGNMENT"
        candidates.append((distance, tuple(point[:2]), name))
    unique = []
    for distance, point, name in candidates:
        if any(math.hypot(point[0] - saved[1][0], point[1] - saved[1][1])
               <= 1.0e-9 for saved in unique):
            continue
        unique.append((distance, point, name))
    selected = select_unambiguous_candidate(
        (d, (p, name)) for d, p, name in unique)
    if selected is None:
        raise ValueError("guide candidateが曖昧です。")
    point, guide = selected
    result = list(original)
    result[moved_index] = point
    path = canonical_multi_path(result, point_ids)
    return MoveCandidate(tuple(p.xy for p in path), tuple(p.point_id for p in path),
                         moved_index, guide)


def resolve_creation_candidate(points, point_ids, raw_point, *, shift=False,
                               guide_candidates=(), distances=(), guide_names=(),
                               threshold_px=GUIDE_THRESHOLD_PX):
    """Resolve an L third-click through the same strict guide selection policy."""
    if len(points) != 2:
        raise ValueError("L作成の第3点解決には確定済み2点が必要です。")
    provisional = (tuple(points[0]), tuple(points[1]), tuple(raw_point[:2]))
    ids = tuple(point_ids)
    if len(ids) != 3:
        raise ValueError("L作成point identityが不正です。")
    # Reuse END rules: P1 is the canonical anchor and the incoming Flight is
    # fixed.  Shift therefore also has to satisfy exact 90 degrees.
    return resolve_move_candidate(provisional, ids, 2, raw_point, shift=shift,
                                  guide_candidates=guide_candidates,
                                  distances=distances, guide_names=guide_names,
                                  threshold_px=threshold_px)
