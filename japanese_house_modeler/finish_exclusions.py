"""Pure Stage 2-A exclusion interval and managed-state helpers."""

import math
import uuid


EPSILON_MM = 1.0e-7
# Blender dialogs display these distances to 0.01 mm.  Half one displayed unit
# plus 0.0001 mm floating noise absorbs endpoint round trips without turning
# arbitrary outside values valid.
UI_ENDPOINT_TOLERANCE_MM = 0.0051


def new_exclusion_id():
    """Return an object-name-independent collision-resistant identity."""
    return uuid.uuid4().hex


def normalize_distance_from_start(
        value_mm, wall_length_mm, tolerance_mm=UI_ENDPOINT_TOLERANCE_MM):
    """Convert a dialog distance to a semantic canonical Wall boundary."""
    value, length, tolerance = map(
        float, (value_mm, wall_length_mm, tolerance_mm))
    if (not all(map(math.isfinite, (value, length, tolerance)))
            or length <= 0.0 or tolerance < 0.0):
        raise ValueError("invalid Wall boundary normalization")
    if abs(value) <= tolerance:
        return "WALL_START", 0.0
    if abs(value - length) <= tolerance:
        return "WALL_END", 0.0
    if 0.0 < value < length:
        return "DISTANCE_FROM_START", value
    raise ValueError("入力した境界位置がWallの範囲外です。")


def merge_coverage(intervals, epsilon=EPSILON_MM):
    """Merge overlap/touching coverage for calculation without mutating input."""
    ordered = sorted((float(a), float(b)) for a, b in intervals)
    for a, b in ordered:
        if not all(map(math.isfinite, (a, b))) or b - a <= epsilon:
            raise ValueError("invalid exclusion interval")
    merged = []
    for a, b in ordered:
        if merged and a <= merged[-1][1] + epsilon:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else:
            merged.append((a, b))
    return tuple(merged)


def subtract_intervals(interval, exclusions, epsilon=EPSILON_MM):
    """Subtract validated coverage from one ascending canonical span interval."""
    start, end = map(float, interval)
    if not all(map(math.isfinite, (start, end))) or end - start <= epsilon:
        raise ValueError("invalid span interval")
    result, cursor = [], start
    relevant = [(max(start, a), min(end, b)) for a, b in exclusions
                if b > start + epsilon and a < end - epsilon]
    for a, b in merge_coverage(relevant, epsilon) if relevant else ():
        if a > cursor + epsilon:
            result.append((cursor, a))
        cursor = max(cursor, b)
    if cursor < end - epsilon:
        result.append((cursor, end))
    return tuple(result)


def calculate_visible_intervals(spans, exclusions):
    """Return path-ordered visible pieces; records are never rewritten.

    Spans are ``(key, start, end, traversal)`` and exclusions are
    ``(key, start, end, enabled)``.  Canonical coordinates always ascend;
    pieces are emitted in FinishRun traversal order.
    """
    by_key = {}
    for key, start, end, enabled in exclusions:
        if enabled:
            by_key.setdefault(key, []).append((start, end))
    visible = []
    for key, start, end, traversal in spans:
        pieces = subtract_intervals((start, end), by_key.get(key, ()))
        if traversal == "REVERSE":
            pieces = tuple(reversed(pieces))
        elif traversal != "FORWARD":
            raise ValueError("invalid traversal direction")
        visible.extend((key, a, b, traversal) for a, b in pieces)
    return tuple(visible)


def classify_visible_state(canonical_valid, visible_count, exclusion_count):
    if not canonical_valid:
        return "INVALID"
    if visible_count == 0 and exclusion_count:
        return "VALID_EMPTY"
    return "NORMAL"


def traversal_bounds(interval, traversal):
    """Return canonical arrival/departure coordinates in traversal order."""
    start, end = map(float, interval)
    if end - start <= EPSILON_MM:
        raise ValueError("invalid span interval")
    if traversal == "FORWARD":
        return start, end
    if traversal == "REVERSE":
        return end, start
    raise ValueError("invalid traversal direction")


def piece_reaches_boundary(piece, interval, traversal, boundary,
                           epsilon=0.001):
    """Whether an ascending visible piece reaches arrival or departure."""
    if boundary not in {"ARRIVAL", "DEPARTURE"}:
        raise ValueError("invalid traversal boundary")
    arrival, departure = traversal_bounds(interval, traversal)
    piece_arrival, piece_departure = traversal_bounds(piece, traversal)
    expected = arrival if boundary == "ARRIVAL" else departure
    actual = piece_arrival if boundary == "ARRIVAL" else piece_departure
    return abs(actual - expected) <= float(epsilon)


def run_boundary_field(traversal, endpoint):
    """Map an actual Run endpoint to its canonical FinishSpan field prefix."""
    if endpoint == "START":
        return "entry" if traversal == "FORWARD" else "exit"
    if endpoint == "END":
        return "exit" if traversal == "FORWARD" else "entry"
    raise ValueError("invalid Run endpoint")


def activated_identity(exclusion_id, fragment_id, factory=new_exclusion_id):
    """Lazily migrate a legacy record when the user explicitly enables it."""
    return exclusion_id or factory(), fragment_id or factory()


def exclusion_split_identities(exclusion_id, fragment_id, piece_count,
                               factory=new_exclusion_id):
    """Preserve a logical ID and replace fragment IDs only when divided."""
    if piece_count < 0:
        raise ValueError("invalid piece count")
    logical = exclusion_id or factory()
    if piece_count <= 1:
        return tuple((logical, fragment_id or factory()) for _ in range(piece_count))
    return tuple((logical, factory()) for _ in range(piece_count))


def transactional_edit(snapshot, mutate, prepare, commit, restore):
    """Apply canonical mutation and derived replacement as one rollback unit."""
    replacement = None
    try:
        mutate()
        replacement = prepare()
        commit(replacement)
        return replacement
    except Exception:
        restore(snapshot)
        if replacement is not None and hasattr(replacement, "discard"):
            replacement.discard(replacement.replacement)
        raise
