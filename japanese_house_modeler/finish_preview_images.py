"""Transient custom ImagePreview cache for derived Profile thumbnails."""

import bpy
import bpy.utils.previews
from bpy.app.handlers import persistent

from .finish_profile_previews import PREVIEW_SIZE, preview_cache_key, rasterize_preview


# Kept only to clean Candidate r1/r2 files.  New previews never create Images.
LEGACY_IMAGE_PREFIX = "JHM_DERIVED_PROFILE_PREVIEW"
PREVIEW_CONTEXTS = ("LIBRARY", "BASEBOARD", "CROWN")
_PREVIEWS = None
_CACHE = {}
_REQUESTED = {}
_VALID_KEYS = set()
_FAILED_KEYS = set()
_BUILD_PENDING = False


def _preview_name(key):
    """ImagePreviewCollection requires a string key; content key stays source."""
    return repr(key)


def _ensure_preview_collection():
    global _PREVIEWS
    if _PREVIEWS is None:
        _PREVIEWS = bpy.utils.previews.new()
    return _PREVIEWS


def _dispose_preview_collection():
    global _PREVIEWS
    if _PREVIEWS is not None:
        bpy.utils.previews.remove(_PREVIEWS)
        _PREVIEWS = None
    _CACHE.clear()


def cached_preview_icon(item, finish_type="LIBRARY"):
    """Read an existing ImagePreview icon without modifying collection state."""
    key = preview_cache_key(item, finish_type)
    name = _CACHE.get(key)
    if _PREVIEWS is None or name is None:
        return 0
    try:
        return _PREVIEWS[name].icon_id if name in _PREVIEWS else 0
    except (KeyError, ReferenceError, RuntimeError):
        return 0


def _remove_preview(key):
    name = _CACHE.pop(key, None)
    if _PREVIEWS is not None and name is not None:
        try:
            if name in _PREVIEWS:
                del _PREVIEWS[name]
        except (KeyError, ReferenceError, RuntimeError):
            pass


def _build_custom_preview(item, finish_type):
    """Populate an ImagePreview directly with CPU raster data outside draw."""
    key = preview_cache_key(item, finish_type)
    name = _preview_name(key)
    pixels = rasterize_preview(item, finish_type)
    previews = _ensure_preview_collection()
    preview = None
    try:
        if name in previews:
            del previews[name]
        preview = previews.new(name)
        # Assigning size then pixels is Blender 5.2's supported custom-preview
        # path; is_icon_custom/is_image_custom become true automatically.
        preview.icon_size = (PREVIEW_SIZE, PREVIEW_SIZE)
        preview.icon_pixels_float = pixels
        preview.image_size = (PREVIEW_SIZE, PREVIEW_SIZE)
        preview.image_pixels_float = pixels
        _CACHE[key] = name
        return preview.icon_id
    except Exception:
        _CACHE.pop(key, None)
        try:
            if name in previews:
                del previews[name]
        except (KeyError, ReferenceError, RuntimeError):
            pass
        raise


def prune_preview_cache(valid_keys):
    valid = set(valid_keys)
    for key in tuple(_CACHE):
        if key not in valid:
            _remove_preview(key)


def _cleanup_legacy_images():
    """Remove only zero-user generated Images left by Candidates r1/r2."""
    for image in tuple(bpy.data.images):
        try:
            owned = (image.name.startswith(LEGACY_IMAGE_PREFIX)
                     or bool(image.get("jhm_derived_profile_preview", False)))
            if owned and image.users == 0:
                bpy.data.images.remove(image)
        except (ReferenceError, RuntimeError):
            continue


def _redraw_view3d():
    try:
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == "VIEW_3D":
                    area.tag_redraw()
    except (AttributeError, ReferenceError, RuntimeError):
        pass


def _deferred_preview_build():
    """Timer callback: maintain and build all requested context variants."""
    global _BUILD_PENDING
    requested = tuple(_REQUESTED.items())
    _REQUESTED.clear()
    try:
        prune_preview_cache(_VALID_KEYS)
        _FAILED_KEYS.intersection_update(_VALID_KEYS)
        _cleanup_legacy_images()
        for key, (item, finish_type) in requested:
            if key in _FAILED_KEYS or cached_preview_icon(item, finish_type):
                continue
            try:
                _build_custom_preview(item, finish_type)
            except Exception:
                _FAILED_KEYS.add(key)
    finally:
        _BUILD_PENDING = False
        _redraw_view3d()
    return None


def request_preview_build(items):
    """Idempotently enqueue current items; safe to call repeatedly from draw."""
    global _BUILD_PENDING, _VALID_KEYS
    requests = {
        preview_cache_key(item, context): (item, context)
        for item in items
        for context in PREVIEW_CONTEXTS
    }
    _VALID_KEYS = set(requests)
    for key, value in requests.items():
        if not cached_preview_icon(*value) and key not in _FAILED_KEYS:
            _REQUESTED[key] = value
    if _REQUESTED and not _BUILD_PENDING:
        _BUILD_PENDING = True
        bpy.app.timers.register(_deferred_preview_build, first_interval=0.0)


def _cancel_timer_and_requests():
    global _BUILD_PENDING
    if bpy.app.timers.is_registered(_deferred_preview_build):
        bpy.app.timers.unregister(_deferred_preview_build)
    _REQUESTED.clear()
    _VALID_KEYS.clear()
    _FAILED_KEYS.clear()
    _BUILD_PENDING = False


@persistent
def clear_preview_cache(_unused=None):
    """Recreate transient previews after file load; rebuild remains lazy."""
    _cancel_timer_and_requests()
    _dispose_preview_collection()
    _ensure_preview_collection()
    _cleanup_legacy_images()


def register_load_handler():
    _ensure_preview_collection()
    _cleanup_legacy_images()
    if clear_preview_cache not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(clear_preview_cache)


def unregister_load_handler():
    if clear_preview_cache in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(clear_preview_cache)
    _cancel_timer_and_requests()
    _dispose_preview_collection()
    _cleanup_legacy_images()
