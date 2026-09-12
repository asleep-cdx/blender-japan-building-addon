"""Canonical Wall splitting kept separate from the drawing operator."""

import bpy

from .connections import add_reciprocal, transfer_endpoint_connections
from .drawing_alignment import canonical_split_segments
from .joints import has_identity_transform


def split_wall(host, point):
    """Split an identity-transform host and return its canonical END successor."""
    wall = host.jhm_wall
    segments = canonical_split_segments(wall.start, wall.end, point)
    if segments is None or not has_identity_transform(host):
        raise ValueError("Wallを安全に分割できませんでした。")
    start_segment, end_segment = segments
    old_end = tuple(wall.end)
    mesh = bpy.data.meshes.new("Wall")
    successor = None
    try:
        successor = bpy.data.objects.new("Wall", mesh)
        for collection in host.users_collection:
            collection.objects.link(successor)
        new_wall = successor.jhm_wall
        new_wall.is_wall = True
        new_wall.start = end_segment[0]
        new_wall.end = end_segment[1]
        new_wall.wall_thickness = wall.wall_thickness
        new_wall.wall_height = wall.wall_height
        for material in host.data.materials:
            successor.data.materials.append(material)
        wall.end = start_segment[1]
        transfer_endpoint_connections(host, "END", successor, "END")
        add_reciprocal(host, "END", successor, "START")
        return successor
    except Exception:
        wall.end = old_end
        if successor is not None:
            bpy.data.objects.remove(successor, do_unlink=True)
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
        raise
