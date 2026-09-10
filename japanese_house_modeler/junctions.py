"""Read-only classification of Wall endpoint junctions."""

import math
from collections import namedtuple

from .connections import junction_members


_ANGLE_TOLERANCE_DEG = 1.0
_MIN_DIRECTION_LENGTH = 1.0e-6

ISOLATED = "ISOLATED"
CONTINUATION = "CONTINUATION"
CORNER = "CORNER"
OVERLAP = "OVERLAP"
T_JUNCTION = "T_JUNCTION"
THREE_WAY = "THREE_WAY"
CROSS = "CROSS"
FOUR_WAY = "FOUR_WAY"
MULTI = "MULTI"
INVALID = "INVALID"

JunctionClassification = namedtuple(
    "JunctionClassification", ("key", "member_count", "angle")
)


def endpoint_direction(wall_object, endpoint):
    """Return the normalized XY direction from a junction into a Wall."""
    if endpoint not in {"START", "END"}:
        return None
    try:
        wall = wall_object.jhm_wall
        start_x, start_y = float(wall.start[0]), float(wall.start[1])
        end_x, end_y = float(wall.end[0]), float(wall.end[1])
    except (AttributeError, IndexError, ReferenceError, TypeError, ValueError):
        return None

    direction_x = end_x - start_x
    direction_y = end_y - start_y
    if endpoint == "END":
        direction_x = -direction_x
        direction_y = -direction_y
    length = math.hypot(direction_x, direction_y)
    if not math.isfinite(length) or length <= _MIN_DIRECTION_LENGTH:
        return None
    return (direction_x / length, direction_y / length, 0.0)


def pair_angle(first, second):
    """Return the smaller angle in degrees between normalized directions."""
    try:
        dot = float(first[0]) * float(second[0]) + float(first[1]) * float(
            second[1]
        )
    except (IndexError, TypeError, ValueError):
        return None
    if not math.isfinite(dot):
        return None
    return math.degrees(math.acos(max(-1.0, min(1.0, dot))))


def _is_opposite(angle):
    return abs(angle - 180.0) <= _ANGLE_TOLERANCE_DEG


def _is_same_direction(angle):
    return angle <= _ANGLE_TOLERANCE_DEG


def _angle(directions, first, second):
    return pair_angle(directions[first], directions[second])


def classify_directions(directions):
    """Classify a sequence of normalized XY directions without side effects."""
    member_count = len(directions)
    if member_count == 0 or any(direction is None for direction in directions):
        return JunctionClassification(INVALID, member_count, None)
    if member_count == 1:
        return JunctionClassification(ISOLATED, member_count, None)
    if member_count >= 5:
        return JunctionClassification(MULTI, member_count, None)

    angles = {}
    for first in range(member_count):
        for second in range(first + 1, member_count):
            angle = _angle(directions, first, second)
            if angle is None:
                return JunctionClassification(INVALID, member_count, None)
            angles[(first, second)] = angle

    if member_count == 2:
        angle = angles[(0, 1)]
        if _is_opposite(angle):
            key = CONTINUATION
        elif _is_same_direction(angle):
            key = OVERLAP
        else:
            key = CORNER
        return JunctionClassification(key, member_count, angle)

    if member_count == 3:
        opposite_pairs = [pair for pair, angle in angles.items() if _is_opposite(angle)]
        if len(opposite_pairs) == 1:
            straight_pair = opposite_pairs[0]
            branch = next(index for index in range(3) if index not in straight_pair)
            branch_angles = [
                angles[tuple(sorted((branch, straight_member)))]
                for straight_member in straight_pair
            ]
            if not any(_is_same_direction(angle) for angle in branch_angles):
                return JunctionClassification(T_JUNCTION, member_count, None)
        return JunctionClassification(THREE_WAY, member_count, None)

    pairings = (
        (((0, 1), (2, 3))),
        (((0, 2), (1, 3))),
        (((0, 3), (1, 2))),
    )
    if any(
        _is_opposite(angles[first_pair]) and _is_opposite(angles[second_pair])
        for first_pair, second_pair in pairings
    ):
        return JunctionClassification(CROSS, member_count, None)
    return JunctionClassification(FOUR_WAY, member_count, None)


def classify_junction(wall_object, endpoint):
    """Derive one endpoint's classification from saved data and topology."""
    try:
        members = junction_members(wall_object, endpoint)
    except (AttributeError, ReferenceError, TypeError, ValueError):
        return JunctionClassification(INVALID, 0, None)
    directions = [
        endpoint_direction(member_object, member_endpoint)
        for member_object, member_endpoint in members
    ]
    return classify_directions(directions)


def t_junction_roles(wall_object, endpoint):
    """Return the unique straight pair and branch for a three-member T.

    The result is derived on every call and deliberately retains no role state.
    Pair selection examines all combinations, so it is independent of the order
    in which the connection topology happens to enumerate its members.
    """
    try:
        members = list(junction_members(wall_object, endpoint))
    except (AttributeError, ReferenceError, TypeError, ValueError):
        return None
    if len(members) != 3:
        return None
    directions = [endpoint_direction(obj, member_endpoint) for obj, member_endpoint in members]
    if any(direction is None for direction in directions):
        return None
    opposite_pairs = []
    for first in range(3):
        for second in range(first + 1, 3):
            angle = pair_angle(directions[first], directions[second])
            if angle is not None and _is_opposite(angle):
                opposite_pairs.append((first, second))
    if len(opposite_pairs) != 1:
        return None
    first, second = opposite_pairs[0]
    branch = next(index for index in range(3) if index not in (first, second))
    if any(
        _is_same_direction(pair_angle(directions[branch], directions[index]))
        for index in (first, second)
    ):
        return None
    return (members[first], members[second]), members[branch]


def cross_junction_pairs(wall_object, endpoint):
    """Return the unique two-opposite-pair partition of a four-member Cross.

    All three disjoint partitions are examined. Returning no result for both
    zero and multiple candidates keeps ambiguous topology out of Mesh solving,
    and makes the result independent of junction member enumeration order.
    """
    try:
        members = list(junction_members(wall_object, endpoint))
    except (AttributeError, ReferenceError, TypeError, ValueError):
        return None
    if len(members) != 4:
        return None
    directions = [endpoint_direction(obj, member_endpoint) for obj, member_endpoint in members]
    if any(direction is None for direction in directions):
        return None
    candidates = []
    for pairing in (
        ((0, 1), (2, 3)),
        ((0, 2), (1, 3)),
        ((0, 3), (1, 2)),
    ):
        if all(
            _is_opposite(pair_angle(directions[first], directions[second]))
            for first, second in pairing
        ):
            candidates.append(pairing)
    if len(candidates) != 1:
        return None
    return tuple(
        (members[first], members[second]) for first, second in candidates[0]
    )


_DISPLAY_NAMES = {
    ISOLATED: "未接続",
    CONTINUATION: "直線継続",
    CORNER: "コーナー",
    OVERLAP: "同方向重複",
    T_JUNCTION: "T字候補",
    THREE_WAY: "3方向接続",
    CROSS: "十字候補",
    FOUR_WAY: "4方向接続",
    MULTI: "多方向接続",
    INVALID: "判定不能",
}


def classification_label(classification):
    """Format a classification for the Japanese UI."""
    label = _DISPLAY_NAMES.get(classification.key, _DISPLAY_NAMES[INVALID])
    if classification.member_count == 2 and classification.angle is not None:
        return f"{label} ({classification.angle:.1f}°)"
    if classification.key == MULTI:
        return f"{label} ({classification.member_count})"
    return label
