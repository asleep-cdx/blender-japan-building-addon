"""Pure Stage-2 guide and path-point relocation mathematics.

The module has no Blender dependency.  Screen-space projection stays in the
operator; these helpers resolve canonical world-XY candidates only.
"""

from dataclasses import dataclass
import math

from .drawing_alignment import constrained_direction, select_unambiguous_candidate
from .stair_multiflight import canonical_multi_path


@dataclass(frozen=True)
class MoveCandidate:
    points: tuple
    point_ids: tuple
    moved_index: int
    guide: str


def move_anchor_index(point_count, moved_index):
    """Return the canonical anchor; ascent direction intentionally is irrelevant."""
    if not 0 <= moved_index < point_count or point_count < 2:
        raise ValueError("移動Path点indexが不正です。")
    return 1 if moved_index == 0 else moved_index - 1


def endpoint_right_angle_candidate(points, moved_index, raw_point):
    """Project START/END onto its mathematically exact 90-degree locus."""
    points = tuple(tuple(map(float, p[:2])) for p in points)
    if len(points) != 3 or moved_index not in (0, 2):
        raise ValueError("endpoint 90度guideは3点LのSTART/END専用です。")
    turn = points[1]
    fixed = points[2] if moved_index == 0 else points[0]
    axis = (fixed[0] - turn[0], fixed[1] - turn[1])
    length = math.hypot(*axis)
    if length <= 1.0e-6:
        raise ValueError("90度guideの固定Flightが短すぎます。")
    normal = (-axis[1] / length, axis[0] / length)
    delta = (float(raw_point[0]) - turn[0], float(raw_point[1]) - turn[1])
    t = delta[0] * normal[0] + delta[1] * normal[1]
    if abs(t) <= 1.0e-6:
        raise ValueError("90度guide candidateが短すぎます。")
    return turn[0] + t * normal[0], turn[1] + t * normal[1]


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


def resolve_move_candidate(points, point_ids, moved_index, raw_point, *,
                           shift=False, guide_candidates=(), distances=()):
    """Resolve preview/commit identically and filter every snap through strict L validity."""
    original = tuple(tuple(map(float, p[:2])) for p in points)
    anchor = original[move_anchor_index(len(original), moved_index)]
    raw = tuple(map(float, raw_point[:2]))
    if shift and moved_index != 1:
        direction = constrained_direction(anchor, raw, step_degrees=15.0)
        if direction is None:
            raise ValueError("Shift方向を解決できません。")
        length = math.hypot(raw[0] - anchor[0], raw[1] - anchor[1])
        raw = (anchor[0] + direction[0] * length, anchor[1] + direction[1] * length)
    structural = (turn_right_angle_candidate(original, raw, shift=shift)
                  if moved_index == 1 else
                  endpoint_right_angle_candidate(original, moved_index, raw))
    candidates = [(0.0, structural, "RIGHT_ANGLE")]
    for distance, point in zip(distances, guide_candidates):
        candidate_points = list(original)
        candidate_points[moved_index] = tuple(point[:2])
        try:
            canonical_multi_path(candidate_points, point_ids)
        except ValueError:
            continue
        candidates.append((float(distance), tuple(point[:2]), "ALIGNMENT"))
    selected = select_unambiguous_candidate((d, (p, name)) for d, p, name in candidates)
    if selected is None:
        raise ValueError("guide candidateが曖昧です。")
    point, guide = selected
    result = list(original)
    result[moved_index] = point
    path = canonical_multi_path(result, point_ids)
    return MoveCandidate(tuple(p.xy for p in path), tuple(p.point_id for p in path),
                         moved_index, guide)
