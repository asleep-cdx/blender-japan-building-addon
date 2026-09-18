"""Blender image/icon cache for derived Profile browser thumbnails."""

import bpy
from bpy.app.handlers import persistent

from .finish_profile_previews import PREVIEW_SIZE, preview_cache_key, rasterize_preview


_CACHE = {}


def _image_is_valid(image):
    """RNA references can become invalid without becoming Python ``None``."""
    try:
        return image is not None and image.name in bpy.data.images
    except (ReferenceError, RuntimeError):
        return False


def preview_icon(item, finish_type="LIBRARY"):
    key = preview_cache_key(item, finish_type)
    image = _CACHE.get(key)
    if _image_is_valid(image):
        try:
            return image.preview.icon_id
        except (ReferenceError, RuntimeError):
            pass
    _CACHE.pop(key, None)
    pixels = rasterize_preview(item, finish_type)
    image = bpy.data.images.new("JHM_DERIVED_PROFILE_PREVIEW", PREVIEW_SIZE,
                                PREVIEW_SIZE, alpha=True)
    image.use_fake_user = False
    image.pixels.foreach_set(pixels)
    image.update()
    image.preview_ensure()
    _CACHE[key] = image
    return image.preview.icon_id


def prune_preview_cache(valid_keys):
    valid = set(valid_keys)
    for key, image in tuple(_CACHE.items()):
        if key not in valid:
            _CACHE.pop(key, None)
            if _image_is_valid(image):
                try:
                    if image.users == 0:
                        bpy.data.images.remove(image)
                except (ReferenceError, RuntimeError):
                    pass


@persistent
def clear_preview_cache(_unused=None):
    """Drop derived image references after file load or add-on unregister."""
    prune_preview_cache(())


def register_load_handler():
    if clear_preview_cache not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(clear_preview_cache)


def unregister_load_handler():
    if clear_preview_cache in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(clear_preview_cache)
