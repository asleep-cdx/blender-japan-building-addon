"""Pure/testable managed-state diagnosis and operation policy for Stairs."""

from dataclasses import dataclass

from .stair_geometry import resolve_stair_layout
from .stair_residential import (
    BASIC_TREAD_RISER, STANDARD_RESIDENTIAL, ResidentialFields,
    validate_mode_data, validate_stepped_closure_depth,
    validate_side_board_profile_width, validate_stepped_underbody_thickness,
)


NORMAL = "NORMAL"
ID_MISSING = "ID_MISSING"
ID_CONFLICT = "ID_CONFLICT"
TRANSFORM_CHANGED = "TRANSFORM_CHANGED"
INVALID_CANONICAL = "INVALID_CANONICAL"
GEOMETRY_MISSING = "GEOMETRY_MISSING"
OBJECT_TYPE_CHANGED = "OBJECT_TYPE_CHANGED"

NORMAL_ONLY_OPERATIONS = frozenset({
    "EDIT_DIMENSIONS", "EDIT_PATH", "REVERSE", "REGENERATE", "FINALIZE",
})
RECOVERABLE_ISSUES = frozenset({
    ID_MISSING, ID_CONFLICT, TRANSFORM_CHANGED, GEOMETRY_MISSING,
})
_TRANSFORM_TOLERANCE = 1.0e-6


@dataclass(frozen=True)
class StairState:
    """Blender-independent input needed to diagnose one managed Stair."""

    stair_id: str
    path_points: tuple
    ascent_direction: str
    base_z_mm: float
    floor_to_floor_mm: float
    riser_count: int
    stair_width_mm: float
    tread_thickness_mm: float
    riser_thickness_mm: float
    location: tuple = (0.0, 0.0, 0.0)
    rotation: tuple = (0.0, 0.0, 0.0)
    scale: tuple = (1.0, 1.0, 1.0)
    object_type: str = "MESH"
    has_mesh: bool = True
    vertex_count: int = 1
    face_count: int = 1
    assembly_mode: str = BASIC_TREAD_RISER
    stair_schema_version: int = 1
    residential: ResidentialFields = ResidentialFields()


def duplicate_stair_ids(records):
    """Return non-empty IDs occurring more than once among managed records."""
    counts = {}
    for record in records:
        if not getattr(record, "is_managed", True):
            continue
        stair_id = getattr(record, "stair_id", "")
        if stair_id:
            counts[stair_id] = counts.get(stair_id, 0) + 1
    return frozenset(value for value, count in counts.items() if count > 1)


def _near(values, expected):
    try:
        return all(abs(float(value) - target) <= _TRANSFORM_TOLERANCE
                   for value, target in zip(values, expected))
    except (TypeError, ValueError, OverflowError):
        return False


def diagnose_stair(state, duplicate_ids=()):
    """Return every issue deterministically; an empty tuple means NORMAL."""
    issues = []
    if not state.stair_id:
        issues.append(ID_MISSING)
    elif state.stair_id in duplicate_ids:
        issues.append(ID_CONFLICT)
    layout = None
    try:
        layout = resolve_stair_layout(
            state.path_points, state.ascent_direction, state.base_z_mm,
            state.floor_to_floor_mm, state.riser_count, state.stair_width_mm,
            state.tread_thickness_mm, state.riser_thickness_mm)
    except (TypeError, ValueError, OverflowError):
        issues.append(INVALID_CANONICAL)
    try:
        validate_mode_data(state.assembly_mode, state.stair_schema_version,
                           state.residential)
        if state.assembly_mode == STANDARD_RESIDENTIAL and layout is not None:
            validate_stepped_underbody_thickness(
                state.residential, layout.actual_riser,
                layout.tread_thickness, layout.riser_thickness)
            validate_stepped_closure_depth(
                state.residential, layout.actual_riser, layout.going)
            if (state.residential.left_side_board_enabled
                    or state.residential.right_side_board_enabled):
                validate_side_board_profile_width(
                    state.residential, layout.actual_riser, layout.going)
    except (TypeError, ValueError, OverflowError):
        if INVALID_CANONICAL not in issues:
            issues.append(INVALID_CANONICAL)
    if not (_near(state.location, (0.0, 0.0, 0.0))
            and _near(state.rotation, (0.0, 0.0, 0.0))
            and _near(state.scale, (1.0, 1.0, 1.0))):
        issues.append(TRANSFORM_CHANGED)
    if state.object_type != "MESH":
        issues.append(OBJECT_TYPE_CHANGED)
    elif (not state.has_mesh or state.vertex_count <= 0
          or state.face_count <= 0):
        issues.append(GEOMETRY_MISSING)
    return tuple(issues)


def operation_allowed(operation, issues, assembly_mode=None):
    """Central policy shared by UI and operator execute-time gates."""
    issues = tuple(issues)
    if operation in NORMAL_ONLY_OPERATIONS:
        return not issues
    if operation == "APPLY_RESIDENTIAL":
        return not issues and assembly_mode in (None, BASIC_TREAD_RISER)
    if operation in {"EDIT_RESIDENTIAL", "EDIT_MATERIALS"}:
        return not issues and assembly_mode in (None, STANDARD_RESIDENTIAL)
    if operation == "REPAIR":
        return bool(issues) and INVALID_CANONICAL not in issues \
            and set(issues).issubset(RECOVERABLE_ISSUES)
    if operation == "DELETE":
        return True
    return False


def state_label(issues):
    return "正常" if not issues else " / ".join(issues)
