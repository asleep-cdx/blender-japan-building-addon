"""Derived managed Curve generation from canonical Finish attachment data."""

import bpy

from .finish_identity import reference_is_trusted
from .dependency_transaction import DependencyTransaction, PreparedChange
from .finish_path import (
    boundary_reaches_endpoint, profile_horizontal_sign, resolve_interval,
    resolve_vertical, transition_boundaries_reach, traversal_endpoints,
    verification_profile_points,
)
from .finish_surface import (
    endpoint_blocked_by_footprints, face_segment, resolve_surface_path,
    side_normal, transition_blocked_by_footprints, wall_axis,
)
from .connections import (
    connection_collection, is_reciprocal_connection, junction_members,
)
from .finish_identity import id_index
from .finish_state import finish_problem_keys


def managed_walls():
    return [obj for obj in bpy.data.objects
            if getattr(getattr(obj, "jhm_wall", None), "is_wall", False)]


def resolved_finish_points(finish, scene):
    walls = managed_walls()
    from .finish_dependencies import validate_finish_references
    # This also validates every persisted exclusion before dependency work.
    validate_finish_references(finish.id_data, walls)
    segments, intervals = [], []
    for span in finish.spans:
        target = span.wall_object
        if not reference_is_trusted(
                target, span.expected_wall_id, walls,
                lambda obj: obj.jhm_wall.is_wall):
            raise ValueError("Wall参照が無効またはWall IDが重複しています。")
        wall = target.jhm_wall
        interval = (span.entry_boundary_kind, span.entry_boundary_value_mm,
                    span.exit_boundary_kind, span.exit_boundary_value_mm)
        _, wall_length = wall_axis(wall.start, wall.end)
        resolved = resolve_interval(*interval, wall_length * 1000.0,
                                    traversal=span.traversal_direction)
        intervals.append(resolved)
        segments.append(face_segment(
            wall.start, wall.end, wall.wall_thickness / 1000.0,
            span.side, interval, span.traversal_direction,
        ))
    for index, (first, second) in enumerate(zip(finish.spans, finish.spans[1:])):
        _, first_endpoint = traversal_endpoints(first.traversal_direction)
        second_endpoint, _ = traversal_endpoints(second.traversal_direction)
        first_wall, second_wall = first.wall_object.jhm_wall, second.wall_object.jhm_wall
        _, first_length_m = wall_axis(first_wall.start, first_wall.end)
        _, second_length_m = wall_axis(second_wall.start, second_wall.end)
        first_length = first_length_m * 1000.0
        second_length = second_length_m * 1000.0
        if not transition_boundaries_reach(
                intervals[index], first_length, first.traversal_direction,
                intervals[index + 1], second_length,
                second.traversal_direction):
            raise ValueError("FinishSpanが接続Wall端点まで到達していません。")
        connected = any(
            connection.target_object is second.wall_object
            and connection.target_endpoint == second_endpoint
            and is_reciprocal_connection(first.wall_object, first_endpoint, connection)
            for connection in connection_collection(first.wall_object, first_endpoint))
        if not connected:
            raise ValueError("Finish経路の相互接続情報が不正です。")
        blockers = []
        for blocker, endpoint in junction_members(first.wall_object, first_endpoint):
            if blocker in {first.wall_object, second.wall_object}:
                continue
            wall = blocker.jhm_wall
            junction = wall.start if endpoint == "START" else wall.end
            other = wall.end if endpoint == "START" else wall.start
            blockers.append((junction, other, wall.wall_thickness / 1000.0))
        if transition_blocked_by_footprints(
                segments[index], segments[index + 1], blockers,
                miter_limit=finish.miter_limit):
            raise ValueError("選択していない接続Wallが仕上げ経路を遮っています。")
    # Endpoint safety applies independently of transition count, including a
    # single-span FinishRun.  Interior boundaries deliberately skip this test.
    selected = {span.wall_object for span in finish.spans}
    for span_index, at_start in ((0, True), (len(finish.spans) - 1, False)):
        span = finish.spans[span_index]
        wall = span.wall_object.jhm_wall
        arrival, departure = traversal_endpoints(span.traversal_direction)
        endpoint = arrival if at_start else departure
        distance = intervals[span_index][0 if at_start else 1]
        _, length_m = wall_axis(wall.start, wall.end)
        length = length_m * 1000.0
        if not boundary_reaches_endpoint(distance, length, endpoint):
            continue
        blockers = []
        for blocker, blocker_endpoint in junction_members(span.wall_object, endpoint):
            if blocker in selected:
                continue
            blocker_wall = blocker.jhm_wall
            junction = blocker_wall.start if blocker_endpoint == "START" else blocker_wall.end
            other = blocker_wall.end if blocker_endpoint == "START" else blocker_wall.start
            blockers.append((junction, other, blocker_wall.wall_thickness / 1000.0))
        point = segments[span_index][0 if at_start else 1]
        outward = side_normal(wall.start, wall.end, span.side)
        if endpoint_blocked_by_footprints(point, outward, blockers):
            raise ValueError("接続Wallが仕上げ端部を遮っています。")
    defaults = scene.jhm_new_wall_defaults
    z = resolve_vertical(
        finish.vertical_reference, finish.vertical_offset_mm, finish.absolute_z_mm,
        defaults.floor_reference_z_mm, defaults.ceiling_reference_z_mm,
    )
    return tuple((x, y, z) for x, y in resolve_surface_path(
        segments, finish.miter_limit
    ))


def spans_topologically_continuous(spans):
    for first, second in zip(spans, spans[1:]):
        first_endpoint = "END" if first.traversal_direction == "FORWARD" else "START"
        second_endpoint = "START" if second.traversal_direction == "FORWARD" else "END"
        try:
            if not any(connection.target_object is second.wall_object
                       and connection.target_endpoint == second_endpoint
                       and is_reciprocal_connection(first.wall_object,
                                                    first_endpoint, connection)
                       for connection in connection_collection(first.wall_object,
                                                               first_endpoint)):
                return False
        except (ReferenceError, ValueError):
            return False
    return True


def diagnose_finish(obj):
    walls = managed_walls()
    index = id_index(walls, lambda wall: wall.jhm_wall.wall_id)
    references, intervals_valid = [], True
    from .finish_identity import validate_managed_wall_reference
    from .joints import has_identity_transform
    records = tuple(obj.jhm_finish.spans) + tuple(obj.jhm_finish.exclusions)
    for span in records:
        try:
            pointer_present = span.wall_object is not None
            pointer_exists = span.wall_object in walls
            matching = pointer_exists and span.wall_object.jhm_wall.wall_id == span.expected_wall_id
            validate_managed_wall_reference(
                span.wall_object, span.expected_wall_id, walls,
                lambda item: item.jhm_wall.is_wall, has_identity_transform)
        except ReferenceError:
            pointer_present, pointer_exists, matching = False, False, False
        except ValueError:
            pointer_exists, matching = False, False
        references.append((pointer_present, pointer_exists, matching,
                           not span.expected_wall_id
                           or len(index.get(span.expected_wall_id, ())) > 1))
        if pointer_exists and span in obj.jhm_finish.spans:
            wall = span.wall_object.jhm_wall
            try:
                length = ((wall.end[0] - wall.start[0]) ** 2
                          + (wall.end[1] - wall.start[1]) ** 2) ** .5 * 1000.0
                resolve_interval(span.entry_boundary_kind,
                                 span.entry_boundary_value_mm,
                                 span.exit_boundary_kind,
                                 span.exit_boundary_value_mm, length,
                                 span.traversal_direction)
            except (ValueError, TypeError):
                intervals_valid = False
    continuous = spans_topologically_continuous(obj.jhm_finish.spans)
    return finish_problem_keys(obj.matrix_basis.is_identity, references,
                               intervals_valid, continuous, len(obj.jhm_finish.spans))


def _verification_profile(horizontal_sign):
    """Return ``(object, owned_cleanup)`` for borrowed/transaction-owned data."""
    sign = -1.0 if float(horizontal_sign) < 0.0 else 1.0
    name = "JHM Verification Profile 10x60 " + ("Negative" if sign < 0 else "Positive")
    obj = bpy.data.objects.get(name)
    if obj is not None and obj.type == "CURVE":
        return obj, None
    data = bpy.data.curves.new(name, "CURVE")
    obj = None
    try:
        data.dimensions = "2D"
        spline = data.splines.new("POLY")
        spline.points.add(3)
        for target, point in zip(spline.points,
                                 verification_profile_points(sign)):
            target.co = (*point, 0.0, 1.0)
        spline.use_cyclic_u = True
        obj = bpy.data.objects.new(name, data)
        bpy.context.scene.collection.objects.link(obj)
        obj.hide_viewport = True
        obj.hide_render = True
    except Exception as operation_error:
        errors = []
        for cleanup in (
                (lambda: bpy.data.objects.remove(obj, do_unlink=True)) if obj else None,
                lambda: bpy.data.curves.remove(data) if data.users == 0 else None):
            if cleanup is None:
                continue
            try:
                cleanup()
            except Exception as error:
                errors.append(error)
        if errors:
            from .dependency_transaction import DependencyRollbackError
            raise DependencyRollbackError(operation_error, errors) from operation_error
        raise

    def cleanup():
        profile_data = obj.data
        from .dependency_transaction import OperationRecovery
        recovery = OperationRecovery()
        recovery.add(lambda: bpy.data.objects.remove(obj, do_unlink=True))
        recovery.add(lambda: bpy.data.curves.remove(profile_data)
                     if profile_data.users == 0 else None)
        recovery()
    return obj, cleanup


def prepare_finish_regeneration(obj, scene):
    """Build a detached replacement Curve and a reversible data swap."""
    if obj.type != "CURVE" or not obj.jhm_finish.is_finish:
        raise ValueError("管理対象のFinish Curveではありません。")
    if not obj.matrix_basis.is_identity:
        raise ValueError("Finish Object Transformを復元してください。")
    points = resolved_finish_points(obj.jhm_finish, scene)
    old_curve = obj.data
    curve = old_curve.copy()
    owned_profile_cleanup = None
    try:
        curve.dimensions = "3D"
        curve.resolution_u = 1
        curve.bevel_mode = "OBJECT"
        first_span = obj.jhm_finish.spans[0]
        profile, owned_profile_cleanup = _verification_profile(
            profile_horizontal_sign(first_span.side,
                                    first_span.traversal_direction))
        curve.bevel_object = profile
        curve.splines.clear()
        spline = curve.splines.new("POLY")
        spline.points.add(len(points) - 1)
        for target, point in zip(spline.points, points):
            target.co = (*point, 1.0)
        spline.use_cyclic_u = bool(obj.jhm_finish.closed)
        curve.update_tag()
    except Exception as operation_error:
        from .dependency_transaction import OperationRecovery, recover_operation
        recovery = OperationRecovery()
        recovery.add(lambda: bpy.data.curves.remove(curve)
                     if curve.users == 0 else None)
        if owned_profile_cleanup is not None:
            recovery.add(owned_profile_cleanup)
        failure = recover_operation(operation_error, recovery)
        if failure is operation_error:
            raise
        raise failure from operation_error
    def commit(replacement):
        obj.data = replacement

    def rollback():
        obj.data = old_curve

    def discard(replacement):
        from .dependency_transaction import OperationRecovery
        recovery = OperationRecovery()
        recovery.add(lambda: bpy.data.curves.remove(replacement)
                     if replacement.users == 0 else None)
        if owned_profile_cleanup is not None:
            recovery.add(owned_profile_cleanup)
        recovery()

    def dispose_old():
        if old_curve.users == 0:
            bpy.data.curves.remove(old_curve)

    change = PreparedChange(curve, commit, rollback, discard, dispose_old)
    change.points = points
    return change


def regenerate_finishes_atomic(objects, scene):
    """Prepare all Finish Curves before performing any data assignment."""
    transaction = DependencyTransaction()
    changes = transaction.prepare(
        lambda obj=obj: prepare_finish_regeneration(obj, scene)
        for obj in objects)
    transaction.commit()
    return tuple(change.points for change in changes)


def regenerate_wall_finish_dependencies_atomic(walls, finishes, scene,
                                               snapshot=None,
                                               restore=lambda _snapshot: None):
    """Prepare Wall Meshes and Finish Curves in one production transaction."""
    from .joints import merge_affected, prepare_wall_mesh_regeneration

    transaction = prepare_wall_finish_dependency_transaction(
        walls, finishes, scene, snapshot, restore)
    return transaction.commit()


def prepare_wall_finish_dependency_transaction(walls, finishes, scene,
                                               snapshot=None,
                                               restore=lambda _snapshot: None):
    """Prepare and return a transaction whose cleanup may be deferred."""
    from .joints import merge_affected, prepare_wall_mesh_regeneration
    transaction = DependencyTransaction(snapshot, restore)
    factories = [lambda wall=wall: prepare_wall_mesh_regeneration(wall)
                 for wall in merge_affected(walls)]
    factories.extend(lambda obj=obj: prepare_finish_regeneration(obj, scene)
                     for obj in finishes)
    transaction.prepare(factories)
    return transaction


def regenerate_finish(obj, scene):
    """Atomically replace derived Curve data; canonical spans remain untouched."""
    return regenerate_finishes_atomic((obj,), scene)[0]


def create_finish_object(context, configure):
    curve = bpy.data.curves.new("JHM Finish", "CURVE")
    obj = bpy.data.objects.new("JHM Finish", curve)
    try:
        context.collection.objects.link(obj)
        configure(obj.jhm_finish)
        regenerate_finish(obj, context.scene)
        return obj
    except Exception:
        bpy.data.objects.remove(obj, do_unlink=True)
        if curve.users == 0:
            bpy.data.curves.remove(curve)
        raise


def regenerate_for_wall(wall_object, scene):
    for obj in list(bpy.data.objects):
        finish = getattr(obj, "jhm_finish", None)
        if finish and finish.is_finish and any(
                span.wall_object is wall_object for span in finish.spans):
            regenerate_finish(obj, scene)
