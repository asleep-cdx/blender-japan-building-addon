"""Pure production Profile resolution for managed FinishRuns."""

from dataclasses import dataclass
import math

from .finish_orientation import (
    normalized_orientation_sign, oriented_profile_contour,
)


SIMPLE_PROFILE_ID = "SIMPLE"
BEVEL_PROFILE_ID = "BEVEL"
ROUNDED_PROFILE_ID = "ROUNDED"
STANDARD_PROFILE_IDS = (SIMPLE_PROFILE_ID, BEVEL_PROFILE_ID, ROUNDED_PROFILE_ID)
LEGACY_SIMPLE_PROFILE_ID = "SIMPLE_10X60"
SIMPLE_PROFILE_REVISION = 1
BEVEL_PROFILE_REVISION = 1
ROUNDED_PROFILE_REVISION = 1
PROFILE_SCHEMA_VERSION = 1
DEFAULT_HEIGHT_MM = 60.0
DEFAULT_PROJECTION_MM = 10.0
DEFAULT_BEVEL_MM = 5.0
DEFAULT_RADIUS_MM = 5.0
ROUNDED_ARC_SEGMENTS_R1 = 16
PRODUCTION_CURVE_DIMENSIONS = "2D"


@dataclass(frozen=True)
class ProfileShading:
    """Deterministic shading intent for a standard Profile revision."""

    smooth_round: bool
    smooth_contour_edges: tuple


@dataclass(frozen=True)
class ResolvedProfile:
    """One immutable source of geometry, safety and shading information."""

    profile_id: str
    profile_revision: int
    schema_version: int
    height_mm: float
    projection_mm: float
    bevel_mm: float
    radius_mm: float
    contour: tuple
    bounds: tuple
    shading: ProfileShading
    uniform_scale: float = 1.0
    display_name: str = ""

    @property
    def profile_kind(self):
        return self.profile_id

    @property
    def height_m(self):
        return self.height_mm / 1000.0

    @property
    def projection_m(self):
        """Maximum horizontal safety extent, derived from contour bounds."""
        return max(abs(self.bounds[0]), abs(self.bounds[1]))

    @property
    def maximum_horizontal_extent_m(self):
        return self.projection_m


def _positive_dimensions(height, projection):
    if not all(math.isfinite(value) and value > 0.0
               for value in (height, projection)):
        raise ValueError("Profileの高さと出幅は有限の正数である必要があります。")


def resolve_profile(profile_id, profile_revision=0, schema_version=0,
                    height_mm=0.0, projection_mm=0.0,
                    bevel_mm=DEFAULT_BEVEL_MM, radius_mm=DEFAULT_RADIUS_MM):
    """Resolve persisted identity and Run-local values without mutating them."""
    if profile_id == LEGACY_SIMPLE_PROFILE_ID:
        profile_id = SIMPLE_PROFILE_ID
        revision, schema = SIMPLE_PROFILE_REVISION, PROFILE_SCHEMA_VERSION
        height, projection = DEFAULT_HEIGHT_MM, DEFAULT_PROJECTION_MM
    elif profile_id in STANDARD_PROFILE_IDS:
        revision, schema = int(profile_revision), int(schema_version)
        height, projection = float(height_mm), float(projection_mm)
        if revision != 1:
            raise ValueError(f"未対応の{profile_id} Profile revisionです。")
        if schema != PROFILE_SCHEMA_VERSION:
            raise ValueError("未対応のProfile schema versionです。")
    else:
        raise ValueError("Profileを解決できません。")

    bevel, radius = float(bevel_mm), float(radius_mm)
    _positive_dimensions(height, projection)
    scale = 1.0 / 1000.0
    if profile_id == SIMPLE_PROFILE_ID:
        contour_mm = ((0.0, 0.0), (0.0, height),
                      (projection, height), (projection, 0.0))
        shading = ProfileShading(False, ())
    elif profile_id == BEVEL_PROFILE_ID:
        if not math.isfinite(bevel) or not 0.0 < bevel < min(height, projection):
            raise ValueError("面取りは高さと出幅より小さい有限の正数である必要があります。")
        contour_mm = ((0.0, 0.0), (0.0, height),
                      (projection - bevel, height),
                      (projection, height - bevel), (projection, 0.0))
        shading = ProfileShading(False, ())
    else:
        if not math.isfinite(radius) or not 0.0 < radius < min(height, projection):
            raise ValueError("半径は高さと出幅より小さい有限の正数である必要があります。")
        cx, cy = projection - radius, height - radius
        arc = tuple((cx + radius * math.cos(math.pi / 2.0 -
                                            math.pi * index /
                                            (2.0 * ROUNDED_ARC_SEGMENTS_R1)),
                     cy + radius * math.sin(math.pi / 2.0 -
                                            math.pi * index /
                                            (2.0 * ROUNDED_ARC_SEGMENTS_R1)))
                    for index in range(ROUNDED_ARC_SEGMENTS_R1 + 1))
        contour_mm = ((0.0, 0.0), (0.0, height)) + arc + ((projection, 0.0),)
        # Arc consists of 16 edges, starting at contour edge 2.
        shading = ProfileShading(True, tuple(range(2, 2 + ROUNDED_ARC_SEGMENTS_R1)))

    contour = tuple((x * scale, y * scale) for x, y in contour_mm)
    xs, ys = tuple(zip(*contour))
    bounds = (min(xs), max(xs), min(ys), max(ys))
    return ResolvedProfile(profile_id, revision, schema, height, projection,
                           bevel, radius, contour, bounds, shading)


def resolve_custom_profile(profile_id, profile_revision, schema_version,
                           uniform_scale, library):
    from .finish_custom_profiles import (
        find_definition, scaled_contour, validate_uniform_scale,
    )
    definition = find_definition(library, profile_id, profile_revision,
                                 schema_version)
    scale = validate_uniform_scale(uniform_scale)
    raw = tuple((float(point.x), float(point.y)) for point in definition.points)
    contour = scaled_contour(raw, scale)
    if len(contour) < 3:
        raise ValueError("Custom Profile snapshotが不正です。")
    xs, ys = zip(*contour)
    bounds = min(xs), max(xs), min(ys), max(ys)
    smooth = tuple(index for index, point in enumerate(definition.points)
                   if getattr(point, "smooth_to_next", False))
    return ResolvedProfile(
        profile_id, int(profile_revision), int(schema_version),
        (bounds[3] - bounds[2]) * 1000.0,
        max(abs(bounds[0]), abs(bounds[1])) * 1000.0,
        0.0, 0.0, contour, bounds,
        ProfileShading(bool(smooth), smooth), scale,
        definition.display_name)


def resolve_finish_profile(finish, library=None):
    if finish.profile_id not in STANDARD_PROFILE_IDS + (LEGACY_SIMPLE_PROFILE_ID,):
        return resolve_custom_profile(
            finish.profile_id, finish.profile_revision,
            finish.profile_schema_version,
            getattr(finish, "profile_uniform_scale", 1.0), library)
    return resolve_profile(
        finish.profile_id, finish.profile_revision,
        finish.profile_schema_version, finish.profile_height_mm,
        finish.profile_projection_mm,
        getattr(finish, "profile_bevel_mm", DEFAULT_BEVEL_MM),
        getattr(finish, "profile_radius_mm", DEFAULT_RADIUS_MM))


def resolve_default_simple_profile():
    return resolve_profile(SIMPLE_PROFILE_ID, SIMPLE_PROFILE_REVISION,
                           PROFILE_SCHEMA_VERSION, DEFAULT_HEIGHT_MM,
                           DEFAULT_PROJECTION_MM)


def oriented_contour(profile, horizontal_sign, vertical_sign=1.0):
    """Return a mirrored derived contour while preserving its winding."""
    try:
        return oriented_profile_contour(
            profile.contour,
            normalized_orientation_sign(horizontal_sign),
            normalized_orientation_sign(vertical_sign))
    except (TypeError, ValueError) as error:
        raise ValueError("Profile orientationが不正です。") from error


def vertical_base_mm(vertical_base_m):
    value = float(vertical_base_m)
    if not math.isfinite(value):
        raise ValueError("Profile vertical placementが不正です。")
    return round(value * 1000.0, 6)


def placement_adjusted_contour(profile, horizontal_sign, vertical_base_m,
                               vertical_sign=1.0):
    base = vertical_base_mm(vertical_base_m) / 1000.0
    return tuple((x, y + base)
                 for x, y in oriented_contour(profile, horizontal_sign,
                                               vertical_sign))


def derived_profile_cache_identity(profile, horizontal_sign, vertical_base_m,
                                   vertical_sign=1.0):
    horizontal = normalized_orientation_sign(horizontal_sign)
    vertical = normalized_orientation_sign(vertical_sign)
    orientation = "NEGATIVE" if horizontal < 0.0 else "POSITIVE"
    return (profile.profile_id, profile.profile_revision, profile.schema_version,
            profile.height_mm, profile.projection_mm,
            profile.bevel_mm, profile.radius_mm, profile.uniform_scale,
            profile.contour, profile.shading.smooth_contour_edges, orientation,
            "UP" if vertical > 0.0 else "DOWN",
            vertical_base_mm(vertical_base_m))


def uniform_vertical_base(points, epsilon_m=1.0e-9):
    if not points:
        raise ValueError("Finish pathが空です。")
    values = [float(point[2]) for point in points]
    epsilon = float(epsilon_m)
    if (not all(math.isfinite(value) for value in values)
            or not math.isfinite(epsilon) or epsilon < 0.0
            or any(abs(value - values[0]) > epsilon for value in values[1:])):
        raise ValueError("Finish path内で異なるvertical placementは使用できません。")
    return values[0]


def production_profile_values(profile):
    """Canonical legacy migration values (kept compatible with Stage 1)."""
    return (profile.profile_id, profile.profile_revision, profile.schema_version,
            profile.height_mm, profile.projection_mm)


PROFILE_INSTANCE_FIELDS = (
    "profile_id", "profile_revision", "profile_schema_version",
    "profile_height_mm", "profile_projection_mm", "profile_bevel_mm",
    "profile_radius_mm",
    "profile_uniform_scale",
)


def transactional_profile_edit(owner, values, prepare, library=None):
    """Apply Run-local values and a derived replacement as one transaction."""
    from .dependency_transaction import DependencyTransaction

    defaults = (None, None, None, None, None, DEFAULT_BEVEL_MM,
                DEFAULT_RADIUS_MM, 1.0)
    old = tuple(getattr(owner, field, default)
                for field, default in zip(PROFILE_INSTANCE_FIELDS, defaults))
    fields = PROFILE_INSTANCE_FIELDS[:len(values)]

    def restore(snapshot):
        for field, value in zip(PROFILE_INSTANCE_FIELDS, snapshot):
            setattr(owner, field, value)

    transaction = DependencyTransaction(old, restore)
    try:
        for field, value in zip(fields, values):
            setattr(owner, field, value)
        resolve_finish_profile(owner, library)
        transaction.prepare((prepare,))
        transaction.commit()
    except Exception:
        restore(old)
        raise
    return values
