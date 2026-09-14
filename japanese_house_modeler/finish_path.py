"""Pure canonical FinishSpan boundary and vertical-reference resolution."""

import math


BOUNDARY_KINDS = frozenset({
    "WALL_START", "WALL_END", "DISTANCE_FROM_START", "DISTANCE_FROM_END",
})


def traversal_for_connection(source_endpoint, target_endpoint):
    """Return traversal pair for every legitimate endpoint orientation."""
    if source_endpoint not in {"START", "END"} or target_endpoint not in {"START", "END"}:
        raise ValueError("invalid Wall endpoint")
    return (("FORWARD" if source_endpoint == "END" else "REVERSE"),
            ("FORWARD" if target_endpoint == "START" else "REVERSE"))


def backspace_pending(spans, provisional_ids):
    """Remove only the appended tail and prune provisional identity state."""
    kept = list(spans)
    if len(kept) > 1:
        kept.pop()
    participants = {span[0] for span in kept}
    return kept, {wall: value for wall, value in provisional_ids.items()
                  if wall in participants}


def propagate_canonical_side(previous_side, previous_traversal, next_traversal):
    """Keep one traversal-relative physical side across canonical directions."""
    if previous_side not in {"LEFT", "RIGHT"} or previous_traversal not in {
            "FORWARD", "REVERSE"} or next_traversal not in {"FORWARD", "REVERSE"}:
        raise ValueError("invalid Finish side propagation")
    if previous_traversal == next_traversal:
        return previous_side
    return "RIGHT" if previous_side == "LEFT" else "LEFT"


def resolve_boundary(kind, value_mm, wall_length_mm):
    length = float(wall_length_mm)
    value = float(value_mm)
    if (kind not in BOUNDARY_KINDS or not math.isfinite(length)
            or not math.isfinite(value) or length <= 0):
        raise ValueError("invalid FinishSpan boundary")
    if kind == "WALL_START":
        result = 0.0
    elif kind == "WALL_END":
        result = length
    elif kind == "DISTANCE_FROM_START":
        result = value
    else:
        result = length - value
    if not math.isfinite(result) or result < 0.0 or result > length:
        raise ValueError("FinishSpan boundary lies outside Wall")
    return result


def resolve_interval(entry_kind, entry_value_mm, exit_kind, exit_value_mm,
                     wall_length_mm, traversal="FORWARD"):
    """Resolve a positive canonical interval and traversal-ordered endpoints."""
    first = resolve_boundary(entry_kind, entry_value_mm, wall_length_mm)
    second = resolve_boundary(exit_kind, exit_value_mm, wall_length_mm)
    if second - first <= 1.0e-7:
        raise ValueError("FinishSpan canonical entry must precede exit")
    if traversal == "FORWARD":
        return first, second
    if traversal == "REVERSE":
        return second, first
    raise ValueError("invalid traversal direction")


def resolve_vertical(reference, offset_mm, absolute_z_mm,
                     floor_z_mm=0.0, ceiling_z_mm=2500.0):
    if reference == "FLOOR":
        value = floor_z_mm + offset_mm
    elif reference == "CEILING":
        value = ceiling_z_mm + offset_mm
    elif reference == "ABSOLUTE":
        value = absolute_z_mm
    else:
        raise ValueError("invalid vertical reference")
    if not math.isfinite(float(value)):
        raise ValueError("non-finite vertical reference")
    return float(value) / 1000.0
