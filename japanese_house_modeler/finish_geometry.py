"""Derived managed Curve generation from canonical Finish attachment data."""

import bpy

from .finish_identity import reference_is_trusted
from .finish_path import resolve_interval, resolve_vertical
from .finish_surface import (
    face_segment, resolve_surface_path, transition_blocked_by_footprints,
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
    segments = []
    for span in finish.spans:
        target = span.wall_object
        if not reference_is_trusted(
                target, span.expected_wall_id, walls,
                lambda obj: obj.jhm_wall.is_wall):
            raise ValueError("Wall参照が無効またはWall IDが重複しています。")
        wall = target.jhm_wall
        interval = (span.entry_boundary_kind, span.entry_boundary_value_mm,
                    span.exit_boundary_kind, span.exit_boundary_value_mm)
        segments.append(face_segment(
            wall.start, wall.end, wall.wall_thickness / 1000.0,
            span.side, interval, span.traversal_direction,
        ))
    for index, (first, second) in enumerate(zip(finish.spans, finish.spans[1:])):
        first_endpoint = "END" if first.traversal_direction == "FORWARD" else "START"
        second_endpoint = "START" if second.traversal_direction == "FORWARD" else "END"
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
    for span in obj.jhm_finish.spans:
        try:
            pointer_present = span.wall_object is not None
            pointer_exists = span.wall_object in walls
            matching = pointer_exists and span.wall_object.jhm_wall.wall_id == span.expected_wall_id
        except ReferenceError:
            pointer_present, pointer_exists, matching = False, False, False
        references.append((pointer_present, pointer_exists, matching,
                           not span.expected_wall_id
                           or len(index.get(span.expected_wall_id, ())) > 1))
        if pointer_exists:
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


def _verification_profile():
    name = "JHM Verification Profile 10x60"
    obj = bpy.data.objects.get(name)
    if obj is not None and obj.type == "CURVE":
        return obj
    data = bpy.data.curves.new(name, "CURVE")
    data.dimensions = "2D"
    spline = data.splines.new("POLY")
    spline.points.add(3)
    for target, point in zip(spline.points,
                             ((0, 0), (.01, 0), (.01, .06), (0, .06))):
        target.co = (*point, 0.0, 1.0)
    spline.use_cyclic_u = True
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.hide_viewport = True
    obj.hide_render = True
    return obj


def regenerate_finish(obj, scene):
    """Replace only derived spline geometry; canonical spans remain untouched."""
    if obj.type != "CURVE" or not obj.jhm_finish.is_finish:
        raise ValueError("管理対象のFinish Curveではありません。")
    if not obj.matrix_basis.is_identity:
        raise ValueError("Finish Object Transformを復元してください。")
    points = resolved_finish_points(obj.jhm_finish, scene)
    curve = obj.data
    curve.dimensions = "3D"
    curve.resolution_u = 1
    curve.bevel_mode = "OBJECT"
    curve.bevel_object = _verification_profile()
    curve.splines.clear()
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for target, point in zip(spline.points, points):
        target.co = (*point, 1.0)
    spline.use_cyclic_u = bool(obj.jhm_finish.closed)
    curve.update_tag()
    return points


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
