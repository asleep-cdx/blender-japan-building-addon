"""Canonical Wall splitting kept separate from the drawing operator."""

import math
import bpy

from .connections import (
    add_reciprocal, restore_topology, snapshot_topology,
    transfer_endpoint_connections, is_valid_wall_object,
)
from .drawing_alignment import canonical_split_segments
from .joints import has_identity_transform
from .finish_identity import ensure_persistent_id, ensure_unique_persistent_id
from .finish_dependencies import (
    WallSplitResult, remap_finish_objects_for_split,
    find_finish_objects, restore_finish_data, snapshot_finish_data,
    validate_finish_references,
)
from .dependency_transaction import OperationRecovery, recover_operation


class SplitTransactionContext:
    """Mandatory hand-off from low-level split to its complete operation."""

    def __init__(self):
        self.events = []
        self.remapped_finishes = []
        self.finalized = False

    def record_split(self, event, finishes):
        if self.finalized:
            raise RuntimeError("finalize後のsplit記録はできません。")
        self.events.append(event)
        for finish in finishes:
            if finish not in self.remapped_finishes:
                self.remapped_finishes.append(finish)

    def finalize(self, walls, before, after, scene, recovery=None):
        """Consume split/remap results in the outer operation's atomic commit."""
        if self.finalized:
            raise RuntimeError("split transactionは既にfinalizeされています。")
        from .finish_dependencies import dependency_scope_union
        from .finish_geometry import regenerate_wall_finish_dependencies_atomic
        finishes = dependency_scope_union(
            dependency_scope_union(before, after), self.remapped_finishes)
        result = regenerate_wall_finish_dependencies_atomic(
            walls, finishes, scene, restore=recovery or (lambda _snapshot: None))
        self.finalized = True
        return result


def split_wall(host, point, transaction=None):
    """Split/remap only; final regeneration belongs to the owning operation."""
    if transaction is None:
        raise ValueError("Wall splitにはdependency transactionが必要です。")
    wall = host.jhm_wall
    segments = canonical_split_segments(wall.start, wall.end, point)
    if segments is None or not has_identity_transform(host):
        raise ValueError("Wallを安全に分割できませんでした。")
    start_segment, end_segment = segments
    old_end = tuple(wall.end)
    old_wall_id = wall.wall_id
    old_length_mm = math.dist(wall.start[:2], wall.end[:2]) * 1000.0
    split_distance_mm = math.dist(wall.start[:2], point[:2]) * 1000.0
    direct_finishes = find_finish_objects(bpy.data.objects, host)
    walls = [obj for obj in bpy.data.objects if is_valid_wall_object(obj)]
    for finish_object in direct_finishes:
        validate_finish_references(finish_object, walls, require_topology=False)
    finish_snapshot = snapshot_finish_data(direct_finishes)
    topology_snapshot = snapshot_topology()
    mesh = None
    successor = None
    try:
        original_id = ensure_persistent_id(wall)
        mesh = bpy.data.meshes.new("Wall")
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
        transaction.record_split(event, affected_finishes)
        return successor
    except Exception as operation_error:
        recovery = OperationRecovery()
        recovery.add(lambda: setattr(wall, "end", old_end))
        recovery.add(lambda: setattr(wall, "wall_id", old_wall_id))
        recovery.add(lambda: restore_topology(topology_snapshot))
        recovery.add(lambda: restore_finish_data(finish_snapshot))
        recovery.add(lambda: bpy.data.objects.remove(successor, do_unlink=True)
                     if successor is not None else None)
        recovery.add(lambda: bpy.data.meshes.remove(mesh)
                     if mesh is not None and mesh.users == 0 else None)
        failure = recover_operation(operation_error, recovery)
        if failure is operation_error:
            raise
        raise failure from operation_error
