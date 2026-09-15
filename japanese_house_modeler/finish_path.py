"""Pure canonical FinishSpan boundary and vertical-reference resolution."""

import math


BOUNDARY_KINDS = frozenset({
    "WALL_START", "WALL_END", "DISTANCE_FROM_START", "DISTANCE_FROM_END",
})

# Canonical distances are persisted in millimetres.  One micron is small enough
# not to change user-authored intervals while avoiding binary conversion noise.
ENDPOINT_EPSILON_MM = 0.001


def traversal_endpoints(traversal):
    """Return the canonical arrival/departure endpoint for a traversal."""
    if traversal == "FORWARD":
        return "START", "END"
    if traversal == "REVERSE":
        return "END", "START"
    raise ValueError("invalid traversal direction")


def boundary_reaches_endpoint(distance_mm, wall_length_mm, endpoint,
                              epsilon_mm=ENDPOINT_EPSILON_MM):
    """Test endpoint reach solely in canonical Wall centerline coordinates."""
    distance, length, epsilon = map(float,
                                    (distance_mm, wall_length_mm, epsilon_mm))
    if (not all(map(math.isfinite, (distance, length, epsilon)))
            or length <= 0.0 or epsilon < 0.0
            or endpoint not in {"START", "END"}):
        raise ValueError("invalid canonical endpoint reach test")
    target = 0.0 if endpoint == "START" else length
    return abs(distance - target) <= epsilon


def profile_horizontal_sign(side, traversal):
    """Map side/traversal to the traversal-relative outward profile axis."""
    if side not in {"LEFT", "RIGHT"} or traversal not in {"FORWARD", "REVERSE"}:
        raise ValueError("invalid Finish profile orientation")
    return -1.0 if (side == "LEFT") == (traversal == "FORWARD") else 1.0


def verification_profile_points(horizontal_sign):
    """Return the 10 x 60 mm profile with winding preserved when mirrored."""
    sign = -1.0 if float(horizontal_sign) < 0.0 else 1.0
    if sign > 0.0:
        return ((0.0, 0.0), (0.0, .06), (.01, .06), (.01, 0.0))
    return ((0.0, 0.0), (-.01, 0.0), (-.01, .06), (0.0, .06))


def transition_boundaries_reach(first_interval, first_length_mm, first_traversal,
                                second_interval, second_length_mm,
                                second_traversal):
    """Require departure and arrival to reach their traversal endpoints."""
    _, departure = traversal_endpoints(first_traversal)
    arrival, _ = traversal_endpoints(second_traversal)
    return (boundary_reaches_endpoint(first_interval[1], first_length_mm,
                                      departure)
            and boundary_reaches_endpoint(second_interval[0], second_length_mm,
                                          arrival))


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
