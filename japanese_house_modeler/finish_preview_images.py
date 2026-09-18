"""Blender image/icon cache for derived Profile browser thumbnails."""

import bpy
from bpy.app.handlers import persistent

from .finish_profile_previews import PREVIEW_SIZE, preview_cache_key, rasterize_preview


IMAGE_PREFIX = "JHM_DERIVED_PROFILE_PREVIEW"
PREVIEW_CONTEXTS = ("LIBRARY", "BASEBOARD", "CROWN")
_CACHE = {}
_REQUESTED = {}
_VALID_KEYS = set()
_FAILED_KEYS = set()
_BUILD_PENDING = False


def _image_is_valid(image):
    """RNA references can become invalid without becoming Python ``None``."""
    try:
        return image is not None and image.name in bpy.data.images
    except (ReferenceError, RuntimeError):
        return False


def cached_preview_icon(item, finish_type="LIBRARY"):
    """Read an existing icon without changing cache or Blender datablocks."""
    key = preview_cache_key(item, finish_type)
    image = _CACHE.get(key)
    if _image_is_valid(image):
        try:
            return image.preview.icon_id
        except (ReferenceError, RuntimeError):
            return 0
    return 0


def _remove_image(image):
    if _image_is_valid(image):
        try:
            if image.users == 0:
                bpy.data.images.remove(image)
        except (ReferenceError, RuntimeError):
            pass


def _build_preview_image(item, finish_type):
    """Build one derived Image transactionally, outside Panel.draw()."""
    key = preview_cache_key(item, finish_type)
    pixels = rasterize_preview(item, finish_type)
    image = None
    try:
        image = bpy.data.images.new(IMAGE_PREFIX, PREVIEW_SIZE,
                                    PREVIEW_SIZE, alpha=True)
        image.use_fake_user = False
        image["jhm_derived_profile_preview"] = True
        image.pixels.foreach_set(pixels)
        image.update()
        image.preview_ensure()
        _CACHE[key] = image
        return image.preview.icon_id
    except Exception:
        _remove_image(image)
        raise


def prune_preview_cache(valid_keys):
    valid = set(valid_keys)
    for key, image in tuple(_CACHE.items()):
        if key not in valid:
            _CACHE.pop(key, None)
            _remove_image(image)


def _cleanup_owned_orphans():
    """Remove uncached zero-user previews, including Candidate r1 leaks."""
    cached = {image.as_pointer() for image in _CACHE.values()
              if _image_is_valid(image)}
    for image in tuple(bpy.data.images):
        try:
            owned = (image.name.startswith(IMAGE_PREFIX)
                     or bool(image.get("jhm_derived_profile_preview", False)))
            if owned and image.users == 0 and image.as_pointer() not in cached:
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
    """Timer callback: maintain and build all requested preview variants."""
    global _BUILD_PENDING
    requested = tuple(_REQUESTED.items())
    _REQUESTED.clear()
    try:
        prune_preview_cache(_VALID_KEYS)
        _FAILED_KEYS.intersection_update(_VALID_KEYS)
        _cleanup_owned_orphans()
        for key, (item, finish_type) in requested:
            if key in _FAILED_KEYS or cached_preview_icon(item, finish_type):
                continue
            try:
                _build_preview_image(item, finish_type)
            except Exception:
                _FAILED_KEYS.add(key)
        _cleanup_owned_orphans()
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
        if not _image_is_valid(_CACHE.get(key)) and key not in _FAILED_KEYS:
            _REQUESTED[key] = value
    if _REQUESTED and not _BUILD_PENDING:
        _BUILD_PENDING = True
        bpy.app.timers.register(_deferred_preview_build, first_interval=0.0)


@persistent
def clear_preview_cache(_unused=None):
    """Drop derived image references after file load or add-on unregister."""
    global _BUILD_PENDING
    if bpy.app.timers.is_registered(_deferred_preview_build):
        bpy.app.timers.unregister(_deferred_preview_build)
    prune_preview_cache(())
    _REQUESTED.clear()
    _VALID_KEYS.clear()
    _FAILED_KEYS.clear()
    _BUILD_PENDING = False
    _cleanup_owned_orphans()


def register_load_handler():
    if clear_preview_cache not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(clear_preview_cache)


def unregister_load_handler():
    if clear_preview_cache in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(clear_preview_cache)
    if bpy.app.timers.is_registered(_deferred_preview_build):
        bpy.app.timers.unregister(_deferred_preview_build)
