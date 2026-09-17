"""Pure Finish-type orientation and reference-staleness rules."""

import math


def normalized_orientation_sign(value):
    """Normalize a finite orientation value without accepting NaN or infinity."""
    sign = float(value)
    if not math.isfinite(sign):
        raise ValueError("invalid Finish profile orientation")
    return -1.0 if sign < 0.0 else 1.0


def finish_vertical_sign(finish_type):
    """Return the sole authoritative canonical-Y to world-Z orientation."""
    if finish_type == "BASEBOARD":
        return 1.0
    if finish_type == "CROWN":
        return -1.0
    raise ValueError("invalid Finish type")


def orientation_parity(horizontal_sign, vertical_sign):
    """Return reflection parity, rejecting non-unit orientation values."""
    horizontal, vertical = float(horizontal_sign), float(vertical_sign)
    if (not all(math.isfinite(value) for value in (horizontal, vertical))
            or horizontal not in {-1.0, 1.0}
            or vertical not in {-1.0, 1.0}):
        raise ValueError("invalid Finish profile orientation")
    return horizontal * vertical


def oriented_profile_contour(contour, horizontal_sign, vertical_sign):
    """Reflect a canonical contour and preserve its original winding."""
    parity = orientation_parity(horizontal_sign, vertical_sign)
    transformed = tuple((float(horizontal_sign) * x,
                         float(vertical_sign) * y) for x, y in contour)
    return transformed if parity > 0.0 else tuple(reversed(transformed))


def placed_vertical_bounds(bounds, reference_z_m, vertical_sign):
    """Resolve world-Z bounds from actual contour bounds, without normalizing."""
    minimum_y, maximum_y = float(bounds[2]), float(bounds[3])
    reference = float(reference_z_m)
    sign = finish_vertical_sign("BASEBOARD" if vertical_sign == 1 else
                                "CROWN" if vertical_sign == -1 else "")
    values = (reference + sign * minimum_y, reference + sign * maximum_y)
    return min(values), max(values)


def regeneration_state_after_bulk(previous_geometry, replacements, error=None,
                                  regeneration_required=False):
    """Pure atomic bulk decision used by tests and the Blender operator policy."""
    old = tuple(previous_geometry)
    if error is not None:
        return old, bool(regeneration_required)
    new = tuple(replacements)
    if len(new) != len(old):
        raise ValueError("bulk replacement count mismatch")
    return new, False
