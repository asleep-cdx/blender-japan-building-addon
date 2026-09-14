"""Canonical Wall splitting kept separate from the drawing operator."""

import math
import bpy

from .connections import add_reciprocal, transfer_endpoint_connections
from .drawing_alignment import canonical_split_segments
from .joints import has_identity_transform
from .finish_identity import ensure_persistent_id, ensure_unique_persistent_id
from .finish_dependencies import (
    WallSplitResult, remap_finish_objects_for_split,
    restore_finish_data, snapshot_finish_data,
)
from .finish_geometry import regenerate_finish


def split_wall(host, point):
    """Split an identity-transform host and return its canonical END successor."""
    wall = host.jhm_wall
    segments = canonical_split_segments(wall.start, wall.end, point)
    if segments is None or not has_identity_transform(host):
        raise ValueError("Wallを安全に分割できませんでした。")
    start_segment, end_segment = segments
    old_end = tuple(wall.end)
    old_wall_id = wall.wall_id
    original_id = ensure_persistent_id(wall)
    old_length_mm = math.dist(wall.start[:2], wall.end[:2]) * 1000.0
    split_distance_mm = math.dist(wall.start[:2], point[:2]) * 1000.0
    finish_snapshot = snapshot_finish_data(bpy.data.objects)
    mesh = bpy.data.meshes.new("Wall")
    successor = None
    try:
        successor = bpy.data.objects.new("Wall", mesh)
        for collection in host.users_collection:
            collection.objects.link(successor)
        new_wall = successor.jhm_wall
        new_wall.is_wall = True
        existing_ids = {obj.jhm_wall.wall_id for obj in bpy.data.objects
                        if obj is not successor
                        and getattr(getattr(obj, "jhm_wall", None), "is_wall", False)
                        and obj.jhm_wall.wall_id}
        new_wall.wall_id = ensure_unique_persistent_id(new_wall, existing_ids)
        new_wall.start = end_segment[0]
        new_wall.end = end_segment[1]
        new_wall.wall_thickness = wall.wall_thickness
        new_wall.wall_height = wall.wall_height
        for material in host.data.materials:
            successor.data.materials.append(material)
        wall.end = start_segment[1]
        transfer_endpoint_connections(host, "END", successor, "END")
        add_reciprocal(host, "END", successor, "START")
        event = WallSplitResult(
            host, original_id, successor, new_wall.wall_id,
            old_length_mm, split_distance_mm,
        )
        affected_finishes = remap_finish_objects_for_split(bpy.data.objects, event)
        for finish_object in affected_finishes:
            regenerate_finish(finish_object, bpy.context.scene)
        return successor
    except Exception:
        wall.end = old_end
        wall.wall_id = old_wall_id
        restore_finish_data(finish_snapshot)
        if successor is not None:
            bpy.data.objects.remove(successor, do_unlink=True)
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
        for finish_object, _finish_id, _style, _spans, _exclusions in finish_snapshot:
            try:
                regenerate_finish(finish_object, bpy.context.scene)
            except Exception:
                pass
        raise
