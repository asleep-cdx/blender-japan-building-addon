"""Pure Stage 2-A exclusion interval and managed-state helpers."""

import math
import uuid


EPSILON_MM = 1.0e-7


def new_exclusion_id():
    """Return an object-name-independent collision-resistant identity."""
    return uuid.uuid4().hex


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
