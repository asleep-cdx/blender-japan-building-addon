"""Blender image/icon cache for derived Profile browser thumbnails."""

import bpy

from .finish_profile_previews import PREVIEW_SIZE, preview_cache_key, rasterize_preview


_CACHE = {}


def preview_icon(item, finish_type="LIBRARY"):
    key = preview_cache_key(item, finish_type)
    image = _CACHE.get(key)
    if image is not None and image.name in bpy.data.images:
        return image.preview.icon_id
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
            if image and image.name in bpy.data.images and image.users == 0:
                bpy.data.images.remove(image)


def clear_preview_cache():
    prune_preview_cache(())
