"""Pure, derived Profile preview data for the Build 06-C browser.

Nothing in this module is persisted.  In particular, browser position and
image/icon identifiers are never part of a Profile identity.
"""

from dataclasses import dataclass
import hashlib
import math

from .finish_profiles import (
    BEVEL_PROFILE_ID, BEVEL_PROFILE_REVISION, DEFAULT_BEVEL_MM,
    DEFAULT_HEIGHT_MM, DEFAULT_PROJECTION_MM, DEFAULT_RADIUS_MM,
    PROFILE_SCHEMA_VERSION, ROUNDED_PROFILE_ID, ROUNDED_PROFILE_REVISION,
    SIMPLE_PROFILE_ID, SIMPLE_PROFILE_REVISION, resolve_profile,
)


PREVIEW_SIZE = 96
PREVIEW_PADDING = 12
STANDARD_IDS = (SIMPLE_PROFILE_ID, BEVEL_PROFILE_ID, ROUNDED_PROFILE_ID)
STANDARD_REVISIONS = {
    SIMPLE_PROFILE_ID: SIMPLE_PROFILE_REVISION,
    BEVEL_PROFILE_ID: BEVEL_PROFILE_REVISION,
    ROUNDED_PROFILE_ID: ROUNDED_PROFILE_REVISION,
}


@dataclass(frozen=True)
class ProfileBrowserItem:
    profile_id: str
    profile_revision: int
    schema_version: int
    display_name: str
    source_type: str
    contour: tuple
    fallback: bool = False

    @property
    def identity(self):
        return self.profile_id, self.profile_revision, self.schema_version


def stable_profile_identity(value):
    """Extract the canonical three-part identity (never a browser index)."""
    schema = getattr(value, "profile_schema_version",
                     getattr(value, "schema_version", 0))
    return (str(value.profile_id), int(value.profile_revision), int(schema))


def validated_profile_identity(profile_id, profile_revision, schema_version,
                               library):
    """Require an exact currently available canonical browser identity."""
    requested = (str(profile_id), int(profile_revision), int(schema_version))
    if requested[0] in STANDARD_REVISIONS:
        authoritative = (requested[0], STANDARD_REVISIONS[requested[0]],
                         PROFILE_SCHEMA_VERSION)
        if requested != authoritative:
            raise ValueError("Standard Profile identityが現在の定義と一致しません。")
        return authoritative
    for definition in library or ():
        if stable_profile_identity(definition) == requested:
            return requested
    raise ValueError("指定されたCustom Profile identityが現在のLibraryにありません。")


def _standard_item(profile_id):
    profile = resolve_profile(
        profile_id, STANDARD_REVISIONS[profile_id], PROFILE_SCHEMA_VERSION,
        DEFAULT_HEIGHT_MM, DEFAULT_PROJECTION_MM,
        DEFAULT_BEVEL_MM, DEFAULT_RADIUS_MM)
    return ProfileBrowserItem(profile_id, STANDARD_REVISIONS[profile_id],
                              PROFILE_SCHEMA_VERSION, profile_id,
                              "STANDARD", profile.contour)


def browser_items(library):
    """Return standards first, then valid snapshots in stable identity order."""
    result = [_standard_item(profile_id) for profile_id in STANDARD_IDS]
    custom = []
    for definition in library or ():
        try:
            identity = stable_profile_identity(definition)
            contour = tuple((float(point.x), float(point.y))
                            for point in definition.points)
            if len(contour) < 3 or not all(math.isfinite(v) for p in contour for v in p):
                raise ValueError("invalid snapshot")
            custom.append(ProfileBrowserItem(
                *identity, str(definition.display_name or identity[0]),
                str(definition.source_type or "CUSTOM"), contour))
        except (AttributeError, TypeError, ValueError, OverflowError):
            # A corrupt definition remains canonical data to diagnose; preview
            # failure merely supplies a textual browser fallback.
            try:
                identity = stable_profile_identity(definition)
                custom.append(ProfileBrowserItem(
                    *identity, str(getattr(definition, "display_name", "")
                                   or identity[0]),
                    str(getattr(definition, "source_type", "CUSTOM")), (), True))
            except (AttributeError, TypeError, ValueError):
                continue
    result.extend(sorted(custom, key=lambda item: item.identity))
    return tuple(result)


def orient_preview(contour, finish_type):
    """Return a new contour in Baseboard-up or Crown-down UI orientation."""
    sign = -1.0 if str(finish_type).upper() == "CROWN" else 1.0
    return tuple((float(x), sign * float(y)) for x, y in contour)


def fit_contour(contour, size=PREVIEW_SIZE, padding=PREVIEW_PADDING):
    """Uniformly fit a contour into a square while preserving aspect ratio."""
    points = tuple((float(x), float(y)) for x, y in contour)
    if not points:
        raise ValueError("Profile preview contourが空です。")
    low_x, high_x = min(x for x, _ in points), max(x for x, _ in points)
    low_y, high_y = min(y for _, y in points), max(y for _, y in points)
    width, height = high_x - low_x, high_y - low_y
    usable = float(size) - 2.0 * float(padding)
    if usable <= 0.0 or width <= 0.0 or height <= 0.0:
        raise ValueError("Profile preview boundsが不正です。")
    scale = min(usable / width, usable / height)
    offset_x = (float(size) - width * scale) * 0.5
    offset_y = (float(size) - height * scale) * 0.5
    return tuple((offset_x + (x - low_x) * scale,
                  offset_y + (y - low_y) * scale) for x, y in points)


def preview_cache_key(item, finish_type="LIBRARY"):
    """Content key makes deletion/undo/snapshot changes self-invalidating."""
    payload = repr((item.identity, item.contour, str(finish_type).upper())).encode()
    return item.identity + (str(finish_type).upper(),
                            hashlib.sha256(payload).hexdigest())


def rasterize_preview(item, finish_type="LIBRARY", size=PREVIEW_SIZE):
    """Create lightweight RGBA pixels using polygon fill and reference guides."""
    if item.fallback:
        raise ValueError("Profile preview fallback")
    oriented = orient_preview(item.contour, finish_type)
    points = fit_contour(oriented, size=size)
    pixels = [0.09, 0.09, 0.09, 1.0] * (size * size)

    def inside(x, y):
        hit = False
        previous = points[-1]
        for current in points:
            if ((current[1] > y) != (previous[1] > y)):
                crossing = ((previous[0] - current[0]) * (y - current[1]) /
                            (previous[1] - current[1]) + current[0])
                if x < crossing:
                    hit = not hit
            previous = current
        return hit

    for y in range(size):
        for x in range(size):
            if inside(x + 0.5, y + 0.5):
                index = 4 * (y * size + x)
                pixels[index:index + 4] = (0.28, 0.62, 0.92, 1.0)
    # Wall at left; floor/ceiling guide according to application context.
    guide_y = PREVIEW_PADDING if str(finish_type).upper() != "CROWN" else size - PREVIEW_PADDING - 1
    for x, y in ((PREVIEW_PADDING - 3, y) for y in range(PREVIEW_PADDING - 3, size - PREVIEW_PADDING + 3)):
        index = 4 * (y * size + x); pixels[index:index + 4] = (0.9, 0.65, 0.2, 1.0)
    for x in range(PREVIEW_PADDING - 3, size - PREVIEW_PADDING + 3):
        index = 4 * (guide_y * size + x); pixels[index:index + 4] = (0.9, 0.65, 0.2, 1.0)
    return tuple(pixels)
