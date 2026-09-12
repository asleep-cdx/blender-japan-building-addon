"""Pure managed-Wall state decisions shared by UI and interaction code."""

import math


def has_identity_matrix(rows, epsilon=1.0e-6):
    """Return whether a matrix-like value is a finite 4x4 identity matrix."""
    try:
        return all(
            math.isfinite(float(rows[row][column]))
            and abs(float(rows[row][column]) - (1.0 if row == column else 0.0))
            <= epsilon
            for row in range(4)
            for column in range(4)
        )
    except (IndexError, TypeError, ValueError):
        return False


def drawing_candidate_eligible(is_managed, is_visible, transform_is_identity):
    """Central policy for every Wall-derived interactive drawing aid."""
    return bool(is_managed and is_visible and transform_is_identity)


def managed_state_problems(transform_is_identity, topology_is_valid):
    """Build the deterministic problem keys used by managed-state display."""
    problems = []
    if not transform_is_identity:
        problems.append("OBJECT_TRANSFORM")
    if not topology_is_valid:
        problems.append("TOPOLOGY")
    return tuple(problems)
