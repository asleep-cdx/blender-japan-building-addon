"""Pure production Profile resolution for managed FinishRuns."""

from dataclasses import dataclass
import math


SIMPLE_PROFILE_ID = "SIMPLE"
LEGACY_SIMPLE_PROFILE_ID = "SIMPLE_10X60"
SIMPLE_PROFILE_REVISION = 1
PROFILE_SCHEMA_VERSION = 1
DEFAULT_HEIGHT_MM = 60.0
DEFAULT_PROJECTION_MM = 10.0


@dataclass(frozen=True)
class ResolvedProfile:
    """One immutable, orientation-independent Profile resolution."""

    profile_id: str
    profile_revision: int
    schema_version: int
    height_mm: float
    projection_mm: float
    contour: tuple
    bounds: tuple

    @property
    def height_m(self):
        return self.height_mm / 1000.0

    @property
    def projection_m(self):
        return self.projection_mm / 1000.0


def resolve_profile(profile_id, profile_revision=0, schema_version=0,
                    height_mm=0.0, projection_mm=0.0):
    """Resolve persisted identity and Run-local values without mutating them."""
    if profile_id == LEGACY_SIMPLE_PROFILE_ID:
        revision, schema = SIMPLE_PROFILE_REVISION, PROFILE_SCHEMA_VERSION
        height, projection = DEFAULT_HEIGHT_MM, DEFAULT_PROJECTION_MM
    elif profile_id == SIMPLE_PROFILE_ID:
        revision, schema = int(profile_revision), int(schema_version)
        height, projection = float(height_mm), float(projection_mm)
        if revision != SIMPLE_PROFILE_REVISION:
            raise ValueError("未対応のSIMPLE Profile revisionです。")
        if schema != PROFILE_SCHEMA_VERSION:
            raise ValueError("未対応のProfile schema versionです。")
    else:
        raise ValueError("Profileを解決できません。")
    if not all(math.isfinite(value) and value > 0.0
               for value in (height, projection)):
        raise ValueError("Profileの高さと出幅は有限の正数である必要があります。")
    contour = ((0.0, 0.0), (0.0, height / 1000.0),
               (projection / 1000.0, height / 1000.0),
               (projection / 1000.0, 0.0))
    return ResolvedProfile(SIMPLE_PROFILE_ID, revision, schema, height,
                           projection, contour,
                           (0.0, projection / 1000.0,
                            0.0, height / 1000.0))


def resolve_finish_profile(finish):
    return resolve_profile(finish.profile_id, finish.profile_revision,
                           finish.profile_schema_version,
                           finish.profile_height_mm,
                           finish.profile_projection_mm)


def oriented_contour(profile, horizontal_sign):
    """Return a mirrored derived contour while preserving its winding."""
    if not math.isfinite(float(horizontal_sign)):
        raise ValueError("Profile orientationが不正です。")
    if horizontal_sign >= 0.0:
        return profile.contour
    return tuple((-x, y) for x, y in reversed(profile.contour))


def production_profile_values(profile):
    """Canonical values stored when a legacy Run is explicitly edited."""
    return (profile.profile_id, profile.profile_revision, profile.schema_version,
            profile.height_mm, profile.projection_mm)


PROFILE_INSTANCE_FIELDS = (
    "profile_id", "profile_revision", "profile_schema_version",
    "profile_height_mm", "profile_projection_mm",
)


def transactional_profile_edit(owner, values, prepare):
    """Apply Run-local values and a derived replacement as one transaction."""
    from .dependency_transaction import DependencyTransaction

    old = tuple(getattr(owner, field) for field in PROFILE_INSTANCE_FIELDS)

    def restore(snapshot):
        for field, value in zip(PROFILE_INSTANCE_FIELDS, snapshot):
            setattr(owner, field, value)

    transaction = DependencyTransaction(old, restore)
    try:
        for field, value in zip(PROFILE_INSTANCE_FIELDS, values):
            setattr(owner, field, value)
        # Validate before allocating Blender data; prepare may repeat resolution
        # so geometry and safety consume this exact provisional state.
        resolve_finish_profile(owner)
        transaction.prepare((prepare,))
        transaction.commit()
    except Exception:
        restore(old)  # also covers failure before transaction.prepare()
        raise
    return values
