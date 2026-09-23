"""Pure Build 07-B Stage 1 residential data and transaction foundation."""

from dataclasses import dataclass, replace
import math


BASIC_TREAD_RISER = "BASIC_TREAD_RISER"
STANDARD_RESIDENTIAL = "STANDARD_RESIDENTIAL"
STEPPED_CLOSED = "STEPPED_CLOSED"
ASSEMBLY_MODES = frozenset({BASIC_TREAD_RISER, STANDARD_RESIDENTIAL})
MATERIAL_ROLES = ("TREAD", "RISER", "UNDERSIDE", "SIDE_BOARD")
UNASSIGNED = None


@dataclass(frozen=True)
class MaterialSlotPlan:
    """Derived Blender slot layout; ``None`` denotes a real empty slot."""

    slots: tuple
    role_indices: tuple

    def index_for(self, role):
        return dict(self.role_indices)[role]


@dataclass(frozen=True)
class ResidentialFields:
    underside_mode: str = STEPPED_CLOSED
    underside_thickness_mm: float = 9.5
    left_side_board_enabled: bool = True
    right_side_board_enabled: bool = True
    side_board_thickness_mm: float = 18.0
    side_board_band_width_mm: float = 150.0
    side_board_reveal_mm: float = 40.0
    base_material: object = None
    tread_material: object = None
    riser_material: object = None
    underside_material: object = None
    side_board_material: object = None


def semantic_assembly_mode(record):
    """Read legacy records as BASIC without mutating or migrating them."""
    return getattr(record, "assembly_mode", BASIC_TREAD_RISER)


def semantic_schema_version(record):
    """Read legacy records as schema 1, independently from assembly mode."""
    return getattr(record, "stair_schema_version", 1)


def residential_fields(record=None):
    defaults = ResidentialFields()
    if record is None:
        return defaults
    return ResidentialFields(**{
        name: getattr(record, name, getattr(defaults, name))
        for name in defaults.__dataclass_fields__
    })


def validate_mode_data(assembly_mode, schema_version, fields=None):
    """Validate only data active for the assembly mode."""
    if assembly_mode not in ASSEMBLY_MODES:
        raise ValueError("不明なStair assembly modeです。")
    if isinstance(schema_version, bool) or not isinstance(schema_version, int) \
            or schema_version < 1:
        raise ValueError("Stair schema versionは正の整数である必要があります。")
    if assembly_mode == BASIC_TREAD_RISER:
        return True
    values = (fields if isinstance(fields, ResidentialFields)
              else residential_fields(fields))
    if isinstance(values.underside_thickness_mm, bool):
        raise ValueError("下面厚は正の有限値である必要があります。")
    if values.underside_mode != STEPPED_CLOSED:
        raise ValueError("未対応の下面modeです。")
    if not isinstance(values.left_side_board_enabled, bool) \
            or not isinstance(values.right_side_board_enabled, bool):
        raise ValueError("Side Board enabled値はboolである必要があります。")
    for name in ("underside_thickness_mm", "side_board_thickness_mm",
                 "side_board_band_width_mm"):
        value = getattr(values, name)
        if isinstance(value, bool):
            raise ValueError(f"{name}は正の有限値である必要があります。")
        try:
            value = float(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"{name}は正の有限値である必要があります。") from exc
        if not math.isfinite(value) or value <= 0.0:
            raise ValueError(f"{name}は正の有限値である必要があります。")
    return True


def validate_stepped_underbody_thickness(fields, actual_riser,
                                          tread_thickness, riser_thickness):
    """Return the positive finite shell thickness in metres.

    The corrected closure silhouette is independent from this value.  The
    dimensional arguments are retained for source/API compatibility with the
    superseded Stage 2 helper.
    """
    values = (fields if isinstance(fields, ResidentialFields)
              else residential_fields(fields))
    try:
        thickness = float(values.underside_thickness_mm) / 1000.0
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("下面厚は正の有限値である必要があります。") from exc
    if not math.isfinite(thickness) or thickness <= 0.0:
        raise ValueError("下面厚は正の有限値である必要があります。")
    return thickness


def validate_stepped_closure_depth(fields, actual_riser, going):
    """Return the shared closure/Side-Board depth in the supported range."""
    values = (fields if isinstance(fields, ResidentialFields)
              else residential_fields(fields))
    if isinstance(values.side_board_band_width_mm, bool):
        raise ValueError("閉じ下面深さは対応範囲内の有限値である必要があります。")
    try:
        depth = float(values.side_board_band_width_mm) / 1000.0
        limit = min(float(actual_riser), float(going))
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("閉じ下面深さは対応範囲内の有限値である必要があります。") from exc
    if (not math.isfinite(depth) or not math.isfinite(limit)
            or depth <= 0.0 or depth >= limit):
        raise ValueError("閉じ下面深さは0より大きく、実蹴上と踏面ピッチの小さい方未満にしてください。")
    return depth


def validate_side_board_reveal(fields, actual_riser, going):
    """Return the stepped Side Board reveal in its supported range."""
    values = (fields if isinstance(fields, ResidentialFields)
              else residential_fields(fields))
    if isinstance(values.side_board_reveal_mm, bool):
        raise ValueError("側板突出量は対応範囲内の有限値である必要があります。")
    try:
        width = float(values.side_board_reveal_mm) / 1000.0
        limit = min(float(actual_riser), float(going))
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("側板突出量は対応範囲内の有限値である必要があります。") from exc
    if (not math.isfinite(width) or not math.isfinite(limit)
            or width <= 0.0 or width >= limit):
        raise ValueError("側板突出量は0より大きく、実蹴上と踏面ピッチの小さい方未満にしてください。")
    return width


def residential_candidate(record):
    """Return an immutable candidate; never mutate or commit Scene state."""
    candidate = StairTransitionSnapshot.capture(record)
    candidate = replace(candidate, assembly_mode=STANDARD_RESIDENTIAL,
                        stair_schema_version=max(candidate.stair_schema_version, 2))
    validate_mode_data(candidate.assembly_mode, candidate.stair_schema_version,
                       candidate.residential)
    return candidate


def resolve_material_roles(fields):
    """Resolve each role independently; None remains truly UNASSIGNED."""
    values = fields if isinstance(fields, ResidentialFields) else residential_fields(fields)
    return {role: (getattr(values, f"{role.lower()}_material")
                   if getattr(values, f"{role.lower()}_material") is not None
                   else values.base_material)
            for role in MATERIAL_ROLES}


def assemble_material_slot_plan(fields):
    """Resolve roles in stable order and deduplicate datablocks by identity.

    The empty slot is appended only when assigned and unassigned roles are
    mixed.  With every role unassigned there are no slots, and faces retain
    Blender's harmless index zero without inventing a Material datablock.
    """
    effective = resolve_material_roles(fields)
    assigned = any(value is not None for value in effective.values())
    unassigned = any(value is None for value in effective.values())
    slots = []
    indices = []
    for role in MATERIAL_ROLES:
        material = effective[role]
        if material is None:
            index = None
        else:
            index = next((i for i, existing in enumerate(slots)
                          if existing is material), None)
            if index is None:
                slots.append(material)
                index = len(slots) - 1
        indices.append((role, index))
    if assigned and unassigned:
        empty_index = len(slots)
        slots.append(None)
        indices = [(role, empty_index if index is None else index)
                   for role, index in indices]
    elif not assigned:
        indices = [(role, 0) for role, _index in indices]
    return MaterialSlotPlan(tuple(slots), tuple(indices))


@dataclass(frozen=True)
class StairTransitionSnapshot:
    """Pure rollback payload broad enough for the future apply transaction."""

    canonical_dimensions: tuple
    path_points: tuple
    ascent_direction: str
    assembly_mode: str
    stair_schema_version: int
    residential: ResidentialFields
    stair_id: str
    transform: tuple

    @classmethod
    def capture(cls, record):
        dimension_names = ("base_z_mm", "floor_to_floor_mm", "riser_count",
                           "stair_width_mm", "tread_thickness_mm",
                           "riser_thickness_mm")
        path = getattr(record, "path_points", ())
        points = tuple(tuple(getattr(point, "xy", point)) for point in path)
        transform = tuple(tuple(getattr(record, name, default)) for name, default in (
            ("location", (0.0, 0.0, 0.0)),
            ("rotation", (0.0, 0.0, 0.0)),
            ("scale", (1.0, 1.0, 1.0))))
        return cls(tuple((name, getattr(record, name)) for name in dimension_names),
                   points, getattr(record, "ascent_direction", "FORWARD"),
                   semantic_assembly_mode(record), semantic_schema_version(record),
                   residential_fields(record), getattr(record, "stair_id", ""), transform)

    def restore_values(self):
        """Return a detached value map suitable for a later atomic restore."""
        result = dict(self.canonical_dimensions)
        result.update(path_points=self.path_points,
                      ascent_direction=self.ascent_direction,
                      assembly_mode=self.assembly_mode,
                      stair_schema_version=self.stair_schema_version,
                      stair_id=self.stair_id, transform=self.transform)
        result.update(vars(self.residential))
        return result
