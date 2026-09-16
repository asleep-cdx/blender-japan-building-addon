"""Pure Finish dependency remapping plus Blender orchestration adapters."""

from dataclasses import dataclass, replace
import math


@dataclass(frozen=True)
class SpanRecord:
    wall_id: str
    start_mm: float
    end_mm: float
    traversal: str = "FORWARD"
    payload: object = None


@dataclass(frozen=True)
class WallSplitResult:
    original_object: object
    original_id: str
    successor_object: object
    successor_id: str
    old_length_mm: float
    split_distance_mm: float


@dataclass(frozen=True)
class SemanticIntervalPiece:
    wall_part: str
    entry_kind: str
    entry_value_mm: float
    exit_kind: str
    exit_value_mm: float


def remap_semantic_interval(entry_kind, entry_value_mm, exit_kind, exit_value_mm,
                            old_length_mm, split_mm, epsilon=1e-7):
    """Split an interval while retaining meaningful endpoint-relative boundaries."""
    from .finish_path import resolve_boundary

    old_length, split = float(old_length_mm), float(split_mm)
    entry = resolve_boundary(entry_kind, entry_value_mm, old_length)
    exit = resolve_boundary(exit_kind, exit_value_mm, old_length)
    if (not math.isfinite(split) or split <= epsilon
            or split >= old_length - epsilon or exit - entry <= epsilon):
        raise ValueError("invalid semantic split interval")

    def start_boundary(kind, value, distance):
        if kind == "WALL_START":
            return kind, 0.0
        if kind == "DISTANCE_FROM_START":
            return kind, float(value)
        return "DISTANCE_FROM_START", distance

    def end_boundary(kind, value, distance):
        if kind == "WALL_END":
            return kind, 0.0
        if kind == "DISTANCE_FROM_END":
            return kind, float(value)
        return "DISTANCE_FROM_START", distance - split

    pieces = []
    if entry < split - epsilon:
        first_kind, first_value = start_boundary(entry_kind, entry_value_mm, entry)
        if exit >= split - epsilon:
            last_kind, last_value = "WALL_END", 0.0
        else:
            last_kind, last_value = start_boundary(exit_kind, exit_value_mm, exit)
        pieces.append(SemanticIntervalPiece(
            "ORIGINAL", first_kind, first_value, last_kind, last_value))
    if exit > split + epsilon:
        if entry <= split + epsilon:
            first_kind, first_value = "WALL_START", 0.0
        else:
            first_kind, first_value = end_boundary(entry_kind, entry_value_mm, entry)
        last_kind, last_value = end_boundary(exit_kind, exit_value_mm, exit)
        pieces.append(SemanticIntervalPiece(
            "SUCCESSOR", first_kind, first_value, last_kind, last_value))
    return tuple(pieces)


def remap_span_for_split(span, original_id, successor_id, split_mm, epsilon=1e-7):
    """Map one canonical interval; original owns START and successor owns END."""
    if span.wall_id != original_id:
        return (span,)
    low, high = float(span.start_mm), float(span.end_mm)
    split = float(split_mm)
    if (span.traversal not in {"FORWARD", "REVERSE"}
            or not all(math.isfinite(value) for value in (low, high, split))
            or low < 0.0 or high < 0.0
            or high - low <= epsilon or split <= epsilon):
        raise ValueError("invalid canonical split-remap interval")
    pieces = []
    if low < split - epsilon:
        pieces.append(replace(span, start_mm=low, end_mm=min(high, split)))
    if high > split + epsilon:
        pieces.append(replace(span, wall_id=successor_id,
                              start_mm=max(low, split) - split,
                              end_mm=high - split))
    if not pieces:
        # Exact boundary belongs to the segment on which a non-zero interval lies;
        # a point-only attachment is invalid.
        return ()
    if span.traversal == "REVERSE":
        pieces.reverse()
    return tuple(pieces)


def remap_run_for_split(spans, original_id, successor_id, split_mm):
    result = []
    for span in spans:
        result.extend(remap_span_for_split(
            span, original_id, successor_id, split_mm
        ))
    return tuple(result)


def partition_run_on_delete(spans, deleted_wall_id):
    """Partition at every deleted span; never bridge A -> C."""
    runs, current = [], []
    for span in spans:
        if span.wall_id == deleted_wall_id:
            if current:
                runs.append(tuple(current)); current = []
        else:
            current.append(span)
    if current:
        runs.append(tuple(current))
    return tuple(runs)


def find_finish_objects(objects, wall_object):
    result = []
    for obj in objects:
        finish = getattr(obj, "jhm_finish", None)
        if finish and finish.is_finish and wall_object in safe_reference_values(
                tuple(finish.spans) + tuple(finish.exclusions)):
            result.append(obj)
    return result


def collect_local_dependencies(finishes, changed_walls, references, neighbors):
    """Pure local dependency selection shared by production and tests."""
    changed = {wall for wall in changed_walls if wall is not None}
    neighborhood = set(changed)
    for wall in tuple(changed):
        neighborhood.update(neighbors(wall))
    return tuple(finish for finish in finishes
                 if set(references(finish)).intersection(neighborhood))


def safe_reference_values(records, getter=lambda record: record.wall_object):
    """Read dependency pointers without letting unrelated stale RNA escape."""
    result = []
    for record in records:
        try:
            pointer = getter(record)
        except ReferenceError:
            continue
        if pointer is not None:
            result.append(pointer)
    return tuple(result)


def collect_finish_dependencies(objects, changed_walls=(), strict_topology=True):
    """Collect local direct/exclusion/junction/blocker dependencies."""
    from .connections import (
        connection_collection, is_reciprocal_connection,
        is_valid_connection, junction_members,
    )

    finishes = tuple(obj for obj in objects
                     if getattr(getattr(obj, "jhm_finish", None), "is_finish", False))
    def references(obj):
        finish = obj.jhm_finish
        return safe_reference_values(tuple(finish.spans) + tuple(finish.exclusions))
    def neighbors(wall):
        result = []
        for endpoint in ("START", "END"):
            if strict_topology:
                for connection in connection_collection(wall, endpoint):
                    if (not is_valid_connection(connection)
                            or not is_reciprocal_connection(wall, endpoint,
                                                            connection)):
                        raise ValueError("changed Wallのtopologyが不正です。")
            result.extend(item[0] for item in junction_members(wall, endpoint))
        return result
    return collect_local_dependencies(finishes, changed_walls, references, neighbors)


def dependency_scope_union(before, after):
    """Public OLD dependency set UNION NEW dependency set contract."""
    from .dependency_transaction import dependency_union
    return dependency_union(before, after)


def capture_finish_dependency_state(objects, changed_walls,
                                    strict_topology=True,
                                    require_finish_topology=True):
    """Collect, strictly validate, then snapshot only local dependencies."""
    objects = tuple(objects)
    affected = collect_finish_dependencies(
        objects, changed_walls, strict_topology=strict_topology)
    walls = [obj for obj in objects
             if getattr(getattr(obj, "jhm_wall", None), "is_wall", False)]
    for finish_object in affected:
        validate_finish_references(
            finish_object, walls, require_topology=require_finish_topology)
    return affected, snapshot_finish_data(affected)


def capture_finish_repair_state(objects, repair_target):
    """Snapshot local Finish truth while tolerating target-only repair defects."""
    from .finish_identity import (
        validate_managed_wall_reference, validate_repair_target_reference,
    )
    from .joints import has_identity_transform

    objects = tuple(objects)
    affected = collect_finish_dependencies(
        objects, (repair_target,), strict_topology=False)
    walls = [obj for obj in objects
             if getattr(getattr(obj, "jhm_wall", None), "is_wall", False)]
    managed = lambda obj: getattr(getattr(obj, "jhm_wall", None), "is_wall", False)
    for finish_object in affected:
        finish = finish_object.jhm_finish
        validate_repair_snapshot_records(
            tuple(finish.spans) + tuple(finish.exclusions), repair_target,
            walls, managed, has_identity_transform,
            validate_repair_target_reference, validate_managed_wall_reference)
    return affected, snapshot_finish_data(affected)


def validate_repair_snapshot_records(records, repair_target, walls, managed,
                                     identity_transform, validate_target,
                                     validate_normal):
    """Pure repair-aware record policy used before persistent snapshotting."""
    for record in records:
        try:
            pointer = record.wall_object
        except ReferenceError:
            raise ValueError("affected FinishのWall参照が失われています。")
        if pointer is repair_target:
            validate_target(pointer, record.expected_wall_id,
                            repair_target, managed)
        else:
            validate_normal(pointer, record.expected_wall_id, walls,
                            managed, identity_transform)


def validate_finish_references(finish_object, walls, require_topology=True):
    """Apply the common Wall contract to spans and existing exclusions."""
    from .connections import connection_collection, is_reciprocal_connection
    from .finish_identity import validate_managed_wall_reference
    from .joints import has_identity_transform

    finish = finish_object.jhm_finish
    managed = lambda obj: getattr(getattr(obj, "jhm_wall", None), "is_wall", False)
    for record in tuple(finish.spans) + tuple(finish.exclusions):
        validate_managed_wall_reference(
            record.wall_object, record.expected_wall_id,
            walls, managed, has_identity_transform)
    if require_topology:
        for first, second in zip(finish.spans, finish.spans[1:]):
            source = "END" if first.traversal_direction == "FORWARD" else "START"
            target = "START" if second.traversal_direction == "FORWARD" else "END"
            if not any(link.target_object is second.wall_object
                       and link.target_endpoint == target
                       and is_reciprocal_connection(first.wall_object, source, link)
                       for link in connection_collection(first.wall_object, source)):
                raise ValueError("Finish経路の相互接続情報が不正です。")
    return True


_STYLE_FIELDS = ("finish_type", "profile_id", "profile_revision",
                 "profile_schema_version", "profile_height_mm",
                 "profile_projection_mm", "profile_bevel_mm",
                 "profile_radius_mm", "vertical_reference",
                 "vertical_offset_mm", "absolute_z_mm", "join_policy",
                 "miter_limit", "closed")
_SPAN_FIELDS = ("expected_wall_id", "side", "entry_boundary_kind",
                "entry_boundary_value_mm", "exit_boundary_kind",
                "exit_boundary_value_mm", "traversal_direction")
_EXCLUSION_FIELDS = ("expected_wall_id", "side", "start_boundary_kind",
                     "start_boundary_value_mm", "end_boundary_kind",
                     "end_boundary_value_mm", "exclusion_type", "source_id",
                     "exclusion_id", "fragment_id", "enabled")


def snapshot_finish_data(objects):
    """Snapshot persistent Finish truth for operator-level rollback."""
    snapshots = []
    for obj in objects:
        finish = getattr(obj, "jhm_finish", None)
        if not finish or not finish.is_finish:
            continue
        spans = [(span.wall_object,
                  {name: getattr(span, name) for name in _SPAN_FIELDS})
                 for span in finish.spans]
        exclusions = [(item.wall_object,
                       {name: getattr(item, name) for name in _EXCLUSION_FIELDS})
                      for item in finish.exclusions]
        snapshots.append((obj, finish.finish_id,
                          {name: getattr(finish, name) for name in _STYLE_FIELDS},
                          spans, exclusions))
    return snapshots


def restore_finish_data(snapshots):
    for obj, finish_id, style, spans, exclusions in snapshots:
        finish = obj.jhm_finish
        finish.is_finish = True
        finish.finish_id = finish_id
        for name, value in style.items():
            setattr(finish, name, value)
        finish.spans.clear()
        for pointer, values in spans:
            target = finish.spans.add()
            target.wall_object = pointer
            for name, value in values.items():
                setattr(target, name, value)
        finish.exclusions.clear()
        for pointer, values in exclusions:
            target = finish.exclusions.add()
            target.wall_object = pointer
            for name, value in values.items():
                setattr(target, name, value)


def _write_semantic(target, piece, source, original, successor, exclusion=False):
    is_original = piece.wall_part == "ORIGINAL"
    target.wall_object = original if is_original else successor
    target.expected_wall_id = (original.jhm_wall.wall_id if is_original
                               else successor.jhm_wall.wall_id)
    target.side = source["side"]
    prefix_a, prefix_b = (("start", "end") if exclusion else ("entry", "exit"))
    setattr(target, prefix_a + "_boundary_kind", piece.entry_kind)
    setattr(target, prefix_a + "_boundary_value_mm", piece.entry_value_mm)
    setattr(target, prefix_b + "_boundary_kind", piece.exit_kind)
    setattr(target, prefix_b + "_boundary_value_mm", piece.exit_value_mm)
    if exclusion:
        target.exclusion_type = source["exclusion_type"]
        target.source_id = source["source_id"]
        target.exclusion_id = source["exclusion_id"]
        target.fragment_id = source["fragment_id"]
        target.enabled = source["enabled"]
    else:
        target.traversal_direction = source["traversal_direction"]


def remap_finish_objects_for_split(objects, event):
    """Apply a validated split event to every persistent FinishRun."""
    walls = [obj for obj in objects
             if getattr(getattr(obj, "jhm_wall", None), "is_wall", False)]
    affected = []
    for obj in find_finish_objects(objects, event.original_object):
        validate_finish_references(obj, walls, require_topology=False)
        finish = obj.jhm_finish
        rewritten = []
        for span in finish.spans:
            payload = {"wall_object": span.wall_object,
                       **{name: getattr(span, name) for name in _SPAN_FIELDS}}
            if span.wall_object is event.original_object:
                pieces = list(remap_semantic_interval(
                    span.entry_boundary_kind, span.entry_boundary_value_mm,
                    span.exit_boundary_kind, span.exit_boundary_value_mm,
                    event.old_length_mm, event.split_distance_mm))
                if span.traversal_direction == "REVERSE":
                    pieces.reverse()
                rewritten.extend((piece, payload) for piece in pieces)
            else:
                rewritten.append((None, payload))
        finish.spans.clear()
        for piece, source in rewritten:
            if piece is None:
                target = finish.spans.add()
                target.wall_object = source["wall_object"]
                for name in _SPAN_FIELDS:
                    setattr(target, name, source[name])
            else:
                _write_semantic(finish.spans.add(), piece, source,
                                event.original_object, event.successor_object)

        exclusions = []
        for item in finish.exclusions:
            source = {"wall_object": item.wall_object,
                      **{name: getattr(item, name) for name in _EXCLUSION_FIELDS}}
            if item.wall_object is event.original_object:
                pieces = tuple(remap_semantic_interval(
                        item.start_boundary_kind, item.start_boundary_value_mm,
                        item.end_boundary_kind, item.end_boundary_value_mm,
                        event.old_length_mm, event.split_distance_mm))
                from .finish_exclusions import exclusion_split_identities
                identities = exclusion_split_identities(
                    source["exclusion_id"], source["fragment_id"], len(pieces))
                for piece, identity in zip(pieces, identities):
                    source = dict(source, exclusion_id=identity[0],
                                  fragment_id=identity[1])
                    exclusions.append((piece, source))
            else:
                exclusions.append((None, source))
        finish.exclusions.clear()
        for piece, source in exclusions:
            target = finish.exclusions.add()
            if piece is None:
                target.wall_object = source["wall_object"]
                for name in _EXCLUSION_FIELDS:
                    setattr(target, name, source[name])
            else:
                _write_semantic(target, piece, source, event.original_object,
                                event.successor_object, exclusion=True)
        affected.append(obj)
    return affected


def partition_records_for_delete(spans, deleted_wall_id):
    """Integration contract: partition records and reject empty output runs."""
    return tuple(run for run in partition_run_on_delete(spans, deleted_wall_id) if run)


def transactional_mutation(snapshot, mutate, restore):
    """Small testable rollback contract used by compound mutation adapters."""
    try:
        return mutate()
    except Exception:
        restore(snapshot)
        raise


def partition_finish_objects_for_delete(wall_object):
    """Partition every dependent Blender Finish object without bridging gaps."""
    import bpy
    from .finish_identity import new_persistent_id

    affected, created, empty_objects = [], [], []
    sources = find_finish_objects(bpy.data.objects, wall_object)
    walls = [obj for obj in bpy.data.objects
             if getattr(getattr(obj, "jhm_wall", None), "is_wall", False)]
    for obj in sources:
        validate_finish_references(obj, walls)
    snapshots = snapshot_finish_data(sources)
    try:
        for obj in sources:
            finish = obj.jhm_finish
            serialized = [(span.wall_object,
                           {name: getattr(span, name) for name in _SPAN_FIELDS})
                          for span in finish.spans]
            exclusions = [(item.wall_object,
                           {name: getattr(item, name) for name in _EXCLUSION_FIELDS})
                          for item in finish.exclusions
                          if item.wall_object is not wall_object]
            partitions, current = [], []
            for item in serialized:
                if item[0] is wall_object:
                    if current:
                        partitions.append(current); current = []
                else:
                    current.append(item)
            if current:
                partitions.append(current)
            if not partitions:
                empty_objects.append(obj)
                continue
            targets = [obj]
            for _partition in partitions[1:]:
                clone = obj.copy()
                clone.data = obj.data.copy()
                for collection in obj.users_collection:
                    collection.objects.link(clone)
                clone.jhm_finish.finish_id = new_persistent_id()
                targets.append(clone); created.append(clone)
            for target, partition in zip(targets, partitions):
                target.jhm_finish.spans.clear()
                partition_walls = {pointer for pointer, _values in partition}
                for pointer, values in partition:
                    span = target.jhm_finish.spans.add()
                    span.wall_object = pointer
                    for name, value in values.items():
                        setattr(span, name, value)
                target.jhm_finish.exclusions.clear()
                for pointer, values in exclusions:
                    if pointer not in partition_walls:
                        continue
                    item = target.jhm_finish.exclusions.add()
                    item.wall_object = pointer
                    for name, value in values.items():
                        setattr(item, name, value)
                affected.append(target)
        return affected, created, empty_objects
    except Exception:
        for clone in reversed(created):
            data = clone.data
            bpy.data.objects.remove(clone, do_unlink=True)
            if data.users == 0:
                bpy.data.curves.remove(data)
        restore_finish_data(snapshots)
        raise
