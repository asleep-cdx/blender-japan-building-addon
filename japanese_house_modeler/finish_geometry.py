"""Derived managed Curve generation from canonical Finish attachment data."""

import bpy

from .finish_identity import reference_is_trusted
from .dependency_transaction import DependencyTransaction, PreparedChange
from .finish_path import (
    boundary_reaches_endpoint, profile_horizontal_sign, resolve_interval,
    resolve_vertical, transition_boundaries_reach, traversal_endpoints,
)
from .finish_profiles import (
    derived_profile_cache_identity, placement_adjusted_contour,
    PRODUCTION_CURVE_DIMENSIONS, resolve_finish_profile, uniform_vertical_base,
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
from .finish_hardening import (
    duplicate_finish_ids, finish_configuration_problems, finish_id_is_valid,
    finish_intervals_are_valid,
    validate_finish_configuration,
)


def managed_walls():
    return [obj for obj in bpy.data.objects
            if getattr(getattr(obj, "jhm_wall", None), "is_wall", False)]


def validate_path_footprints(spans, segments, intervals, projection_m,
                             miter_limit=4.0, endpoint_exemptions=((), ())):
    """Reject unselected junction walls obstructing a resolved Finish path."""
    for index, (first, second) in enumerate(zip(spans, spans[1:])):
        first_object, _first_side, first_traversal = first
        second_object, _second_side, _second_traversal = second
        _, first_endpoint = traversal_endpoints(first_traversal)
        blockers = []
        for blocker, endpoint in junction_members(first_object, first_endpoint):
            if blocker in {first_object, second_object}:
                continue
            wall = blocker.jhm_wall
            junction = wall.start if endpoint == "START" else wall.end
            other = wall.end if endpoint == "START" else wall.start
            blockers.append((junction, other, wall.wall_thickness / 1000.0))
        if transition_blocked_by_footprints(
                segments[index], segments[index + 1], blockers,
                miter_limit=miter_limit, projection_m=projection_m,
                outward_normals=(
                    side_normal(first_object.jhm_wall.start,
                                first_object.jhm_wall.end, first[1]),
                    side_normal(second_object.jhm_wall.start,
                                second_object.jhm_wall.end, second[1]),
                )):
            raise ValueError("選択していない接続Wallが仕上げ経路を遮っています。")

    selected = {span[0] for span in spans}
    for endpoint_index, (span_index, at_start) in enumerate(
            ((0, True), (len(spans) - 1, False))):
        wall_object, side, traversal = spans[span_index]
        wall = wall_object.jhm_wall
        arrival, departure = traversal_endpoints(traversal)
        endpoint = arrival if at_start else departure
        distance = intervals[span_index][0 if at_start else 1]
        _, length_m = wall_axis(wall.start, wall.end)
        if not boundary_reaches_endpoint(distance, length_m * 1000.0, endpoint):
            continue
        blockers = []
        for blocker, blocker_endpoint in junction_members(wall_object, endpoint):
            if blocker in selected or blocker in endpoint_exemptions[endpoint_index]:
                continue
            blocker_wall = blocker.jhm_wall
            junction = (blocker_wall.start if blocker_endpoint == "START"
                        else blocker_wall.end)
            other = (blocker_wall.end if blocker_endpoint == "START"
                     else blocker_wall.start)
            blockers.append((junction, other,
                             blocker_wall.wall_thickness / 1000.0))
        point = segments[span_index][0 if at_start else 1]
        if endpoint_blocked_by_footprints(
                point, side_normal(wall.start, wall.end, side), blockers,
                projection_m):
            raise ValueError("接続Wallが仕上げ端部を遮っています。")


def _resolved_canonical_path(finish, scene, resolved_profile=None):
    """Validate canonical truth and return unsafed span geometry metadata."""
    resolved_profile = resolved_profile or resolve_finish_profile(finish, scene.jhm_custom_profiles)
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
    spans = [(span.wall_object, span.side, span.traversal_direction)
             for span in finish.spans]
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
    defaults = scene.jhm_new_wall_defaults
    z = resolve_vertical(
        finish.vertical_reference, finish.vertical_offset_mm, finish.absolute_z_mm,
        defaults.floor_reference_z_mm, defaults.ceiling_reference_z_mm,
    )
    return tuple(spans), tuple(segments), tuple(intervals), z


def resolved_finish_points(finish, scene, resolved_profile=None):
    """Accepted Stage 1 full-path resolution when no subtraction is needed."""
    resolved_profile = resolved_profile or resolve_finish_profile(finish, scene.jhm_custom_profiles)
    spans, segments, intervals, z = _resolved_canonical_path(
        finish, scene, resolved_profile)
    from .finish_surface import validate_profile_miter_space
    validate_profile_miter_space(segments, resolved_profile.projection_m,
                                 finish.miter_limit)
    validate_path_footprints(spans, segments, intervals,
                             resolved_profile.projection_m, finish.miter_limit)
    return tuple((x, y, z) for x, y in resolve_surface_path(
        segments, finish.miter_limit))


def _visible_range_plan(finish, scene, resolved_profile=None):
    """Validate canonical data and group subtraction results before safety."""
    resolved_profile = resolved_profile or resolve_finish_profile(finish, scene.jhm_custom_profiles)
    canonical_spans, _segments, canonical_intervals, z = _resolved_canonical_path(
        finish, scene, resolved_profile)
    from .finish_exclusions import piece_reaches_boundary, subtract_intervals
    from .finish_path import resolve_boundary

    coverage = {}
    enabled_count = 0
    spans_by_wall = {}
    for span in finish.spans:
        spans_by_wall.setdefault(span.wall_object, []).append(span)
    for exclusion in finish.exclusions:
        if not exclusion.enabled:
            continue
        if not exclusion.exclusion_id or not exclusion.fragment_id:
            raise ValueError("有効なExclusionのIDがありません。")
        enabled_count += 1
        target = exclusion.wall_object
        wall = target.jhm_wall
        _, length_m = wall_axis(wall.start, wall.end)
        length_mm = length_m * 1000.0
        start = resolve_boundary(exclusion.start_boundary_kind,
                                 exclusion.start_boundary_value_mm, length_mm)
        end = resolve_boundary(exclusion.end_boundary_kind,
                               exclusion.end_boundary_value_mm, length_mm)
        if end - start <= 1.0e-7:
            raise ValueError("Exclusion区間は正の長さが必要です。")
        applicable = spans_by_wall.get(target, ())
        if not applicable or not any(span.side == exclusion.side for span in applicable):
            raise ValueError("ExclusionのWallまたは側面がFinishSpanと一致しません。")
        overlaps = False
        for span in applicable:
            if span.side != exclusion.side:
                continue
            s0, s1 = resolve_interval(
                span.entry_boundary_kind, span.entry_boundary_value_mm,
                span.exit_boundary_kind, span.exit_boundary_value_mm, length_mm)
            if start < s1 - 1.0e-7 and end > s0 + 1.0e-7:
                overlaps = True
        if not overlaps:
            raise ValueError("Exclusionが対応するFinishSpanと重なりません。")
        coverage.setdefault((target, exclusion.side), []).append((start, end))

    groups, current = [], []
    for span_index, span in enumerate(finish.spans):
        wall = span.wall_object.jhm_wall
        _, length_m = wall_axis(wall.start, wall.end)
        length_mm = length_m * 1000.0
        traversal_interval = canonical_intervals[span_index]
        ascending = tuple(sorted(traversal_interval))
        pieces = subtract_intervals(
            ascending, coverage.get((span.wall_object, span.side), ()))
        if span.traversal_direction == "REVERSE":
            pieces = tuple(reversed(pieces))
        if not pieces and current:
            groups.append(current); current = []
        for piece_index, (start, end) in enumerate(pieces):
            interval = ("DISTANCE_FROM_START", start,
                        "DISTANCE_FROM_START", end)
            segment = face_segment(wall.start, wall.end,
                                   wall.wall_thickness / 1000.0, span.side,
                                   interval, span.traversal_direction)
            # Only an uncut boundary may participate in the accepted miter
            # transition. Every exclusion boundary starts a new BUTT range.
            reaches_arrival = piece_reaches_boundary(
                (start, end), ascending, span.traversal_direction, "ARRIVAL")
            reaches_departure = piece_reaches_boundary(
                (start, end), ascending, span.traversal_direction, "DEPARTURE")
            joins_previous = piece_index == 0 and current and reaches_arrival
            if current and not joins_previous:
                groups.append(current); current = []
            effective = ((end, start) if span.traversal_direction == "REVERSE"
                         else (start, end))
            adjacent = (
                canonical_spans[span_index - 1][0] if span_index > 0 else None,
                canonical_spans[span_index + 1][0]
                if span_index + 1 < len(canonical_spans) else None,
            )
            adjacent_segments = (
                _segments[span_index - 1] if span_index > 0 else None,
                _segments[span_index + 1]
                if span_index + 1 < len(_segments) else None,
            )
            current.append((canonical_spans[span_index], segment, effective,
                            span_index, reaches_arrival, reaches_departure,
                            adjacent, adjacent_segments))
            if not reaches_departure:
                groups.append(current); current = []
    if current:
        groups.append(current)

    return tuple(tuple(group) for group in groups), z, enabled_count


def canonical_visible_range_state(finish, scene, resolved_profile=None):
    """Return canonical subtraction classification, independent of Curve data."""
    from .finish_exclusions import classify_visible_state
    groups, _z, enabled_count = _visible_range_plan(
        finish, scene, resolved_profile)
    return classify_visible_state(True, len(groups), enabled_count), len(groups)


def resolved_finish_ranges(finish, scene, resolved_profile=None):
    """Resolve and safety-check each independent visible range."""
    resolved_profile = resolved_profile or resolve_finish_profile(finish, scene.jhm_custom_profiles)
    groups, z, enabled_count = _visible_range_plan(
        finish, scene, resolved_profile)
    ranges = []
    for group in groups:
        spans = tuple(item[0] for item in group)
        segments = [item[1] for item in group]
        intervals = tuple(item[2] for item in group)
        endpoint_exemptions = [set(), set()]
        from .finish_surface import resolve_junction_butt
        first, last = group[0], group[-1]
        if first[3] > 0 and first[4]:
            segments[0] = resolve_junction_butt(
                segments[0], first[7][0], "START", finish.miter_limit)
            endpoint_exemptions[0].add(first[6][0])
        if last[3] + 1 < len(finish.spans) and last[5]:
            segments[-1] = resolve_junction_butt(
                segments[-1], last[7][1], "END", finish.miter_limit)
            endpoint_exemptions[1].add(last[6][1])
        segments = tuple(segments)
        from .finish_surface import validate_profile_miter_space
        validate_profile_miter_space(segments, resolved_profile.projection_m,
                                     finish.miter_limit)
        validate_path_footprints(
            spans, segments, intervals, resolved_profile.projection_m,
            finish.miter_limit, tuple(endpoint_exemptions))
        ranges.append(tuple((x, y, z) for x, y in resolve_surface_path(
            segments, finish.miter_limit)))
    return tuple(ranges), enabled_count


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


def diagnose_finish(obj, scene=None):
    if scene is None:
        scene = next((candidate for candidate in bpy.data.scenes
                      if obj.name in candidate.objects), None)
    walls = managed_walls()
    index = id_index(walls, lambda wall: wall.jhm_wall.wall_id)
    references, span_intervals, exclusion_intervals = [], [], []
    from .finish_identity import validate_managed_wall_reference
    from .joints import has_identity_transform
    def diagnose_reference(record):
        try:
            pointer_present = record.wall_object is not None
            pointer_exists = record.wall_object in walls
            matching = (pointer_exists
                        and record.wall_object.jhm_wall.wall_id
                        == record.expected_wall_id)
            validate_managed_wall_reference(
                record.wall_object, record.expected_wall_id, walls,
                lambda item: item.jhm_wall.is_wall, has_identity_transform)
        except ReferenceError:
            pointer_present, pointer_exists, matching = False, False, False
        except ValueError:
            pointer_exists, matching = False, False
        references.append((pointer_present, pointer_exists, matching,
                           not record.expected_wall_id
                           or len(index.get(record.expected_wall_id, ())) > 1))
        if pointer_exists:
            wall = record.wall_object.jhm_wall
            return ((wall.end[0] - wall.start[0]) ** 2
                    + (wall.end[1] - wall.start[1]) ** 2) ** .5 * 1000.0
        return None

    for span in obj.jhm_finish.spans:
        length = diagnose_reference(span)
        if length is not None:
            span_intervals.append((
                span.entry_boundary_kind, span.entry_boundary_value_mm,
                span.exit_boundary_kind, span.exit_boundary_value_mm, length,
                span.traversal_direction,
            ))
    for exclusion in obj.jhm_finish.exclusions:
        length = diagnose_reference(exclusion)
        if length is not None:
            exclusion_intervals.append((
                exclusion.start_boundary_kind, exclusion.start_boundary_value_mm,
                exclusion.end_boundary_kind, exclusion.end_boundary_value_mm, length,
            ))
    intervals_valid = finish_intervals_are_valid(
        span_intervals, exclusion_intervals)
    continuous = spans_topologically_continuous(obj.jhm_finish.spans)
    finishes = [(item, item.jhm_finish.finish_id) for item in bpy.data.objects
                if getattr(getattr(item, "jhm_finish", None), "is_finish", False)]
    extras = list(finish_configuration_problems(
        obj.jhm_finish.join_policy, obj.jhm_finish.closed))
    try:
        spans_by_wall = {}
        for span in obj.jhm_finish.spans:
            spans_by_wall.setdefault(span.wall_object, []).append(span)
        for exclusion in obj.jhm_finish.exclusions:
            if not exclusion.enabled:
                continue
            if not exclusion.exclusion_id or not exclusion.fragment_id:
                raise ValueError
            applicable = spans_by_wall.get(exclusion.wall_object, ())
            if not applicable or not any(
                    span.side == exclusion.side for span in applicable):
                raise ValueError
            wall = exclusion.wall_object.jhm_wall
            _, length_m = wall_axis(wall.start, wall.end)
            exclusion_interval = resolve_interval(
                exclusion.start_boundary_kind, exclusion.start_boundary_value_mm,
                exclusion.end_boundary_kind, exclusion.end_boundary_value_mm,
                length_m * 1000.0)
            overlaps = False
            for span in applicable:
                if span.side != exclusion.side:
                    continue
                span_interval = sorted(resolve_interval(
                    span.entry_boundary_kind, span.entry_boundary_value_mm,
                    span.exit_boundary_kind, span.exit_boundary_value_mm,
                    length_m * 1000.0, span.traversal_direction))
                if (max(span_interval[0], exclusion_interval[0]) <
                        min(span_interval[1], exclusion_interval[1])):
                    overlaps = True
            if not overlaps:
                raise ValueError
    except (AttributeError, ReferenceError, TypeError, ValueError):
        extras.append("EXCLUSION")
    try:
        resolve_finish_profile(obj.jhm_finish, scene.jhm_custom_profiles if scene else None)
    except (TypeError, ValueError):
        extras.append("PROFILE")
    if not finish_id_is_valid(obj.jhm_finish.finish_id,
                              duplicate_finish_ids(finishes)):
        extras.append("FINISH_ID")
    return finish_problem_keys(obj.matrix_basis.is_identity, references,
                               intervals_valid, continuous, len(obj.jhm_finish.spans),
                               extras)


def _production_profile(resolved, horizontal_sign, vertical_base_m):
    """Return a dimension-keyed derived Profile and optional owned cleanup."""
    sign = -1.0 if float(horizontal_sign) < 0.0 else 1.0
    identity = derived_profile_cache_identity(resolved, sign, vertical_base_m)
    vertical_base_mm = identity[-1]
    name = (f"JHM {resolved.profile_id} r{resolved.profile_revision} "
            f"{resolved.projection_mm:g}x{resolved.height_mm:g} "
            f"Z{vertical_base_mm:g} "
            + ("Negative" if sign < 0 else "Positive"))
    orientation = "NEGATIVE" if sign < 0 else "POSITIVE"
    for candidate in bpy.data.objects:
        data_type = ("CURVE" if isinstance(getattr(candidate, "data", None),
                                           bpy.types.Curve) else "")
        if (candidate.type == "CURVE" and data_type == "CURVE"
                and candidate.get("jhm_managed_profile") is True
                and candidate.get("jhm_profile_id") == resolved.profile_id
                and candidate.get("jhm_profile_revision") == resolved.profile_revision
                and candidate.get("jhm_profile_schema_version") == resolved.schema_version
                and candidate.get("jhm_profile_height_mm") == resolved.height_mm
                and candidate.get("jhm_profile_projection_mm") == resolved.projection_mm
                and candidate.get("jhm_profile_bevel_mm") == resolved.bevel_mm
                and candidate.get("jhm_profile_radius_mm") == resolved.radius_mm
                # Defaults preserve reuse of accepted pre-Stage-3 standard
                # derived Profiles; Custom Profiles always write both keys.
                and candidate.get("jhm_profile_uniform_scale", 1.0)
                == resolved.uniform_scale
                and candidate.get("jhm_profile_contour", repr(resolved.contour))
                == repr(resolved.contour)
                and candidate.get("jhm_profile_orientation") == orientation
                and candidate.get("jhm_profile_vertical_base_mm")
                == vertical_base_mm):
            for spline in candidate.data.splines:
                spline.use_smooth = False
            return candidate, None
    data = bpy.data.curves.new(name, "CURVE")
    obj = None
    try:
        data.dimensions = "2D"
        spline = data.splines.new("POLY")
        spline.points.add(len(resolved.contour) - 1)
        for target, point in zip(spline.points,
                                 placement_adjusted_contour(
                                     resolved, sign, vertical_base_m)):
            target.co = (*point, 0.0, 1.0)
        spline.use_cyclic_u = True
        spline.use_smooth = False
        obj = bpy.data.objects.new(name, data)
        bpy.context.scene.collection.objects.link(obj)
        obj["jhm_managed_profile"] = True
        obj["jhm_profile_id"] = resolved.profile_id
        obj["jhm_profile_revision"] = resolved.profile_revision
        obj["jhm_profile_schema_version"] = resolved.schema_version
        obj["jhm_profile_height_mm"] = resolved.height_mm
        obj["jhm_profile_projection_mm"] = resolved.projection_mm
        obj["jhm_profile_bevel_mm"] = resolved.bevel_mm
        obj["jhm_profile_radius_mm"] = resolved.radius_mm
        obj["jhm_profile_uniform_scale"] = resolved.uniform_scale
        obj["jhm_profile_contour"] = repr(resolved.contour)
        obj["jhm_profile_orientation"] = orientation
        obj["jhm_profile_vertical_base_mm"] = vertical_base_mm
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
    validate_finish_configuration(obj.jhm_finish.join_policy,
                                  obj.jhm_finish.closed)
    managed = [(item, item.jhm_finish.finish_id) for item in bpy.data.objects
               if getattr(getattr(item, "jhm_finish", None), "is_finish", False)]
    duplicates = duplicate_finish_ids(managed)
    if not finish_id_is_valid(obj.jhm_finish.finish_id, duplicates):
        raise ValueError("Finish IDが空、空白、または重複しています。")
    resolved_profile = resolve_finish_profile(obj.jhm_finish, scene.jhm_custom_profiles if scene else None)
    ranges, enabled_count = resolved_finish_ranges(
        obj.jhm_finish, scene, resolved_profile)
    points = tuple(point for visible in ranges for point in visible)
    vertical_base_m = uniform_vertical_base(points) if points else 0.0
    old_curve = obj.data
    curve = old_curve.copy()
    owned_profile_cleanup = None
    try:
        curve.dimensions = PRODUCTION_CURVE_DIMENSIONS
        curve.resolution_u = 1
        curve.bevel_mode = "OBJECT"
        first_span = obj.jhm_finish.spans[0]
        profile, owned_profile_cleanup = _production_profile(
            resolved_profile,
            profile_horizontal_sign(first_span.side,
                                    first_span.traversal_direction),
            vertical_base_m)
        curve.bevel_object = profile
        curve.use_fill_caps = True
        curve.splines.clear()
        for visible in ranges:
            spline = curve.splines.new("POLY")
            spline.points.add(len(visible) - 1)
            for target, point in zip(spline.points, visible):
                target.co = (point[0], point[1], 0.0, 1.0)
            spline.use_cyclic_u = False
            spline.use_smooth = False
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
    change.ranges = ranges
    change.enabled_exclusion_count = enabled_count
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
