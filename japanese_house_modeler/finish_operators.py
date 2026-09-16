"""Build 06-A managed Finish user operations."""

import bpy
import gpu
from bpy_extras import view3d_utils
from gpu_extras.batch import batch_for_shader

from .connections import is_valid_wall_object
from .finish_geometry import (
    create_finish_object, diagnose_finish, prepare_finish_regeneration,
    regenerate_finish, regenerate_finishes_atomic, validate_path_footprints,
)
from .finish_dependencies import restore_finish_data, snapshot_finish_data
from .finish_profiles import (
    BEVEL_PROFILE_ID, DEFAULT_BEVEL_MM, DEFAULT_HEIGHT_MM,
    DEFAULT_PROJECTION_MM, DEFAULT_RADIUS_MM, PROFILE_SCHEMA_VERSION,
    ROUNDED_PROFILE_ID, SIMPLE_PROFILE_ID, SIMPLE_PROFILE_REVISION, resolve_finish_profile,
    resolve_default_simple_profile, transactional_profile_edit,
)
from .finish_hardening import managed_finish_objects
from .finish_mesh import apply_profile_shading, weld_and_validate_finish_mesh
from .dependency_transaction import DependencyTransaction, OperationRecovery, recover_operation
from .finish_identity import (
    duplicate_ids, ensure_persistent_id, id_index, new_persistent_id,
)
from .finish_state import unique_rebind_candidate
from .joints import has_identity_transform
from .connections import connection_collection, is_reciprocal_connection
from .finish_surface import (
    face_segment, resolve_surface_path, validate_profile_miter_space, wall_axis,
)
from .finish_custom_profiles import (
    CUSTOM_BEZIER_SEGMENTS_PER_SPAN_R1, make_snapshot,
    profile_is_referenced,
)
from .finish_path import (
    backspace_pending, profile_horizontal_sign, propagate_canonical_side,
    traversal_for_connection,
)


def _wall_id_duplicates():
    walls = [obj for obj in bpy.data.objects if is_valid_wall_object(obj)]
    return duplicate_ids(walls, lambda obj: obj.jhm_wall.wall_id)


def _finish_poll(context):
    finish = getattr(context.active_object, "jhm_finish", None)
    return context.mode == "OBJECT" and finish is not None and finish.is_finish


def _transactional_finish_mutation(obj, scene, mutate):
    """Commit canonical and generated Finish state together."""
    snapshot = snapshot_finish_data((obj,))
    old_active_index = obj.jhm_finish.active_exclusion_index
    transaction = DependencyTransaction(snapshot, restore_finish_data)
    try:
        mutate()
        transaction.prepare((lambda: prepare_finish_regeneration(obj, scene),))
        transaction.commit()
    except Exception:
        if transaction.state not in {"ROLLED_BACK", "FINALIZED"}:
            transaction.rollback()
        obj.jhm_finish.active_exclusion_index = min(
            old_active_index, max(0, len(obj.jhm_finish.exclusions) - 1))
        raise


class JHM_OT_add_finish_exclusion(bpy.types.Operator):
    bl_idname = "jhm.add_finish_exclusion"
    bl_label = "Manual Exclusionを追加"
    bl_options = {"REGISTER", "UNDO"}
    span_index: bpy.props.IntProperty(name="対象FinishSpan", default=0, min=0)
    start_mm: bpy.props.FloatProperty(
        name="開始 (Wall始点からmm)", min=0.0, precision=2)
    end_mm: bpy.props.FloatProperty(
        name="終了 (Wall始点からmm)", min=0.0, precision=2)

    @classmethod
    def poll(cls, context): return _finish_poll(context)

    def invoke(self, context, _event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        obj, finish = context.active_object, context.active_object.jhm_finish
        if self.span_index >= len(finish.spans):
            self.report({"ERROR"}, "対象FinishSpanがありません。"); return {"CANCELLED"}
        from .finish_exclusions import (
            new_exclusion_id, normalize_distance_from_start,
        )
        def mutate():
            span = finish.spans[self.span_index]
            wall = span.wall_object.jhm_wall
            length_mm = wall_axis(wall.start, wall.end)[1] * 1000.0
            start_kind, start_value = normalize_distance_from_start(
                self.start_mm, length_mm)
            end_kind, end_value = normalize_distance_from_start(
                self.end_mm, length_mm)
            item = finish.exclusions.add()
            item.wall_object, item.expected_wall_id = span.wall_object, span.expected_wall_id
            item.side = span.side
            item.start_boundary_kind, item.start_boundary_value_mm = (
                start_kind, start_value)
            item.end_boundary_kind, item.end_boundary_value_mm = (
                end_kind, end_value)
            item.exclusion_type = "MANUAL"
            item.exclusion_id = new_exclusion_id()
            item.fragment_id = new_exclusion_id()
            item.enabled = True
            finish.active_exclusion_index = len(finish.exclusions) - 1
        try: _transactional_finish_mutation(obj, context.scene, mutate)
        except Exception as error:
            self.report({"ERROR"}, f"Exclusionを追加できませんでした: {error}"); return {"CANCELLED"}
        return {"FINISHED"}


class JHM_OT_edit_finish_exclusion(bpy.types.Operator):
    bl_idname = "jhm.edit_finish_exclusion"
    bl_label = "Exclusionを編集"
    bl_options = {"REGISTER", "UNDO"}
    start_mm: bpy.props.FloatProperty(
        name="開始 (Wall始点からmm)", min=0.0, precision=2)
    end_mm: bpy.props.FloatProperty(
        name="終了 (Wall始点からmm)", min=0.0, precision=2)

    @classmethod
    def poll(cls, context): return _finish_poll(context)

    def invoke(self, context, _event):
        finish = context.active_object.jhm_finish
        if not finish.exclusions: return {"CANCELLED"}
        item = finish.exclusions[min(finish.active_exclusion_index, len(finish.exclusions)-1)]
        from .finish_path import resolve_boundary
        wall = item.wall_object.jhm_wall
        length_mm = wall_axis(wall.start, wall.end)[1] * 1000.0
        self.start_mm = resolve_boundary(
            item.start_boundary_kind, item.start_boundary_value_mm, length_mm)
        self.end_mm = resolve_boundary(
            item.end_boundary_kind, item.end_boundary_value_mm, length_mm)
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        obj, finish = context.active_object, context.active_object.jhm_finish
        index = finish.active_exclusion_index
        if index >= len(finish.exclusions): return {"CANCELLED"}
        from .finish_exclusions import normalize_distance_from_start
        def mutate():
            item = finish.exclusions[index]
            wall = item.wall_object.jhm_wall
            length_mm = wall_axis(wall.start, wall.end)[1] * 1000.0
            item.start_boundary_kind, item.start_boundary_value_mm = (
                normalize_distance_from_start(self.start_mm, length_mm))
            item.end_boundary_kind, item.end_boundary_value_mm = (
                normalize_distance_from_start(self.end_mm, length_mm))
        try: _transactional_finish_mutation(obj, context.scene, mutate)
        except Exception as error:
            self.report({"ERROR"}, f"Exclusionを編集できませんでした: {error}"); return {"CANCELLED"}
        return {"FINISHED"}


class JHM_OT_remove_finish_exclusion(bpy.types.Operator):
    bl_idname = "jhm.remove_finish_exclusion"; bl_label = "Exclusionを削除"
    bl_options = {"REGISTER", "UNDO"}
    @classmethod
    def poll(cls, context): return _finish_poll(context)
    def execute(self, context):
        obj, finish, index = context.active_object, context.active_object.jhm_finish, context.active_object.jhm_finish.active_exclusion_index
        if index >= len(finish.exclusions): return {"CANCELLED"}
        try: _transactional_finish_mutation(obj, context.scene, lambda: finish.exclusions.remove(index))
        except Exception as error:
            self.report({"ERROR"}, str(error)); return {"CANCELLED"}
        finish.active_exclusion_index = max(0, min(index, len(finish.exclusions)-1))
        return {"FINISHED"}


class JHM_OT_toggle_finish_exclusion(bpy.types.Operator):
    bl_idname = "jhm.toggle_finish_exclusion"; bl_label = "Exclusionの有効/無効"
    bl_options = {"REGISTER", "UNDO"}
    @classmethod
    def poll(cls, context): return _finish_poll(context)
    def execute(self, context):
        obj, finish, index = context.active_object, context.active_object.jhm_finish, context.active_object.jhm_finish.active_exclusion_index
        if index >= len(finish.exclusions): return {"CANCELLED"}
        from .finish_exclusions import activated_identity
        def mutate():
            item = finish.exclusions[index]
            enabling = not item.enabled
            if enabling:
                item.exclusion_id, item.fragment_id = activated_identity(
                    item.exclusion_id, item.fragment_id)
            item.enabled = enabling
        try: _transactional_finish_mutation(obj, context.scene, mutate)
        except Exception as error:
            self.report({"ERROR"}, str(error)); return {"CANCELLED"}
        return {"FINISHED"}


class JHM_OT_edit_finish_boundaries(bpy.types.Operator):
    bl_idname = "jhm.edit_finish_boundaries"; bl_label = "開始/終了位置を変更"
    bl_options = {"REGISTER", "UNDO"}
    start_mm: bpy.props.FloatProperty(
        name="最初のSpan開始 (Wall始点からmm)", min=0.0, precision=2)
    end_mm: bpy.props.FloatProperty(
        name="最後のSpan終了 (Wall始点からmm)", min=0.0, precision=2)
    @classmethod
    def poll(cls, context): return _finish_poll(context)
    def invoke(self, context, _event):
        from .finish_path import resolve_boundary
        from .finish_exclusions import run_boundary_field
        finish = context.active_object.jhm_finish
        first, last = finish.spans[0], finish.spans[-1]
        def length(span):
            wall = span.wall_object.jhm_wall
            return wall_axis(wall.start, wall.end)[1] * 1000.0
        start_field = run_boundary_field(first.traversal_direction, "START")
        end_field = run_boundary_field(last.traversal_direction, "END")
        self.start_mm = resolve_boundary(
            getattr(first, start_field + "_boundary_kind"),
            getattr(first, start_field + "_boundary_value_mm"), length(first))
        self.end_mm = resolve_boundary(
            getattr(last, end_field + "_boundary_kind"),
            getattr(last, end_field + "_boundary_value_mm"), length(last))
        return context.window_manager.invoke_props_dialog(self)
    def execute(self, context):
        from .finish_exclusions import (
            normalize_distance_from_start, run_boundary_field,
        )
        obj, finish = context.active_object, context.active_object.jhm_finish
        def mutate():
            first, last = finish.spans[0], finish.spans[-1]
            def length(span):
                wall = span.wall_object.jhm_wall
                return wall_axis(wall.start, wall.end)[1] * 1000.0
            start_field = run_boundary_field(first.traversal_direction, "START")
            end_field = run_boundary_field(last.traversal_direction, "END")
            start = normalize_distance_from_start(self.start_mm, length(first))
            end = normalize_distance_from_start(self.end_mm, length(last))
            setattr(first, start_field + "_boundary_kind", start[0])
            setattr(first, start_field + "_boundary_value_mm", start[1])
            setattr(last, end_field + "_boundary_kind", end[0])
            setattr(last, end_field + "_boundary_value_mm", end[1])
        try: _transactional_finish_mutation(obj, context.scene, mutate)
        except Exception as error:
            self.report({"ERROR"}, str(error)); return {"CANCELLED"}
        return {"FINISHED"}


class JHM_OT_start_finish_path(bpy.types.Operator):
    """Interactively collect an explicit, topology-trusted ordered FinishRun."""

    bl_idname = "jhm.start_finish_path"
    bl_label = "仕上げ経路を開始"
    bl_options = {"REGISTER", "UNDO"}

    side: bpy.props.EnumProperty(items=(("LEFT", "左", ""), ("RIGHT", "右", "")))

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT" and is_valid_wall_object(context.active_object)

    def invoke(self, context, event):
        wall_object = context.active_object
        if not has_identity_transform(wall_object):
            self.report({"WARNING"}, "Object TransformのあるWallは使用できません。")
            return {"CANCELLED"}
        wall_id = wall_object.jhm_wall.wall_id
        if wall_id and wall_id in _wall_id_duplicates():
            self.report({"ERROR"}, "Wall IDが重複しています。先に管理状態を復元してください。")
            return {"CANCELLED"}
        self._pending = [(wall_object, self.side, "FORWARD")]
        self._pending_ids = {wall_object: wall_id or new_persistent_id()}
        self._candidate = None
        self._candidate_first_traversal = None
        self._region = next((region for region in context.area.regions
                             if region.type == "WINDOW"), None)
        self._region_data = context.space_data.region_3d
        self._draw_handle = bpy.types.SpaceView3D.draw_handler_add(
            self._draw_preview, (), "WINDOW", "POST_VIEW")
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        if event.type in {"ESC", "RIGHTMOUSE"}:
            return self._finish(context, {"CANCELLED"})
        if event.type == "BACK_SPACE" and event.value == "PRESS":
            self._pending, self._pending_ids = backspace_pending(
                self._pending, self._pending_ids)
            self._candidate = None
            self._candidate_first_traversal = None
            context.area.tag_redraw(); return {"RUNNING_MODAL"}
        if event.type == "MOUSEMOVE":
            self._candidate = self._candidate_at(context, event)
            context.area.tag_redraw(); return {"RUNNING_MODAL"}
        if event.type == "LEFTMOUSE" and event.value == "PRESS":
            if self._candidate is not None:
                if len(self._pending) == 1 and self._candidate_first_traversal:
                    first = self._pending[0]
                    self._pending[0] = (first[0], first[1],
                                        self._candidate_first_traversal)
                self._pending.append(self._candidate)
                self._pending_ids.setdefault(
                    self._candidate[0],
                    self._candidate[0].jhm_wall.wall_id or new_persistent_id())
                self._candidate = None
                self._candidate_first_traversal = None
            return {"RUNNING_MODAL"}
        if event.type in {"RET", "NUMPAD_ENTER"} and event.value == "PRESS":
            return self._commit(context)
        return {"RUNNING_MODAL"}

    def _candidate_at(self, context, event):
        coordinate = (event.mouse_region_x, event.mouse_region_y)
        origin = view3d_utils.region_2d_to_origin_3d(
            self._region, self._region_data, coordinate)
        direction = view3d_utils.region_2d_to_vector_3d(
            self._region, self._region_data, coordinate)
        hit, _location, _normal, _index, obj, _matrix = context.scene.ray_cast(
            context.evaluated_depsgraph_get(), origin, direction)
        if not hit or not is_valid_wall_object(obj) or not has_identity_transform(obj):
            return None
        if any(obj is span[0] for span in self._pending) or (obj.jhm_wall.wall_id
                                           and obj.jhm_wall.wall_id in _wall_id_duplicates()):
            return None
        current, _side, traversal = self._pending[-1]
        endpoints = ("START", "END") if len(self._pending) == 1 else (
            "END" if traversal == "FORWARD" else "START",)
        matches = [(endpoint, connection.target_endpoint)
                   for endpoint in endpoints
                   for connection in connection_collection(current, endpoint)
                   if connection.target_object is obj
                   and is_reciprocal_connection(current, endpoint, connection)]
        if len(matches) != 1:
            return None
        source_traversal, candidate_traversal = traversal_for_connection(*matches[0])
        self._candidate_first_traversal = source_traversal if len(self._pending) == 1 else None
        if len(self._pending) == 1:
            traversal = source_traversal
        side = propagate_canonical_side(
            self._pending[-1][1], traversal, candidate_traversal)
        return obj, side, candidate_traversal

    def _draw_preview(self):
        spans = list(self._pending)
        if self._candidate is not None and len(spans) == 1 \
                and self._candidate_first_traversal:
            spans[0] = (spans[0][0], spans[0][1], self._candidate_first_traversal)
        spans += ([self._candidate] if self._candidate else [])
        vertices = []
        segments_resolved = []
        for obj, side, traversal in spans:
            try:
                segment = face_segment(
                    obj.jhm_wall.start, obj.jhm_wall.end,
                    obj.jhm_wall.wall_thickness / 1000.0, side,
                    traversal=traversal)
                segments_resolved.append(segment)
                vertices.extend(segment)
            except (ReferenceError, ValueError):
                continue
        if len(vertices) < 2:
            return
        shader = gpu.shader.from_builtin("UNIFORM_COLOR")
        try:
            preview_profile = resolve_default_simple_profile()
            resolve_surface_path(segments_resolved)
            validate_profile_miter_space(
                segments_resolved, preview_profile.projection_m)
            intervals = []
            for obj, _side, traversal in spans:
                _axis, length = wall_axis(
                    obj.jhm_wall.start, obj.jhm_wall.end)
                length *= 1000.0
                intervals.append((0.0, length) if traversal == "FORWARD"
                                 else (length, 0.0))
            validate_path_footprints(
                spans, segments_resolved, intervals,
                preview_profile.projection_m)
            color = (0.1, 0.8, 1.0, 1.0)
        except ValueError:
            # Keep the raw guide visible, but never present a join which the
            # final resolver already rejects as an apparently valid cyan path.
            color = (1.0, 0.25, 0.05, 1.0)
        previous_line_width = gpu.state.line_width_get()
        try:
            gpu.state.line_width_set(3.0)
            shader.bind(); shader.uniform_float("color", color)
            batch_for_shader(
                shader, "LINES", {"pos": [(x, y, .02) for x, y in vertices]}
            ).draw(shader)
        finally:
            gpu.state.line_width_set(previous_line_width)

    def _commit(self, context):
        changed_ids = []
        try:
            self._validate_pending()
            for wall, value in self._pending_ids.items():
                if not wall.jhm_wall.wall_id:
                    wall.jhm_wall.wall_id = value; changed_ids.append(wall)
            involved_ids = {wall.jhm_wall.wall_id for wall, _side, _direction
                            in self._pending}
            if involved_ids.intersection(_wall_id_duplicates()):
                raise ValueError("Wall IDが重複しています。")

            def configure(finish):
                finish.is_finish = True
                finish.finish_id = new_persistent_id()
                for wall, side, traversal in self._pending:
                    span = finish.spans.add()
                    span.wall_object = wall
                    span.expected_wall_id = wall.jhm_wall.wall_id
                    span.side = side
                    span.traversal_direction = traversal

            obj = create_finish_object(context, configure)
        except Exception as error:
            for wall in changed_ids:
                wall.jhm_wall.wall_id = ""
            self.report({"ERROR"}, f"仕上げ経路を生成できませんでした: {error}")
            return self._finish(context, {"CANCELLED"})
        for selected in context.selected_objects:
            selected.select_set(False)
        obj.select_set(True); context.view_layer.objects.active = obj
        return self._finish(context, {"FINISHED"})

    def _validate_pending(self):
        walls = [span[0] for span in self._pending]
        if len(set(walls)) != len(walls):
            raise ValueError("同じWallを経路内で再利用できません。")
        live_walls = [obj for obj in bpy.data.objects if is_valid_wall_object(obj)]
        duplicates = duplicate_ids(live_walls, lambda obj: obj.jhm_wall.wall_id)
        for wall in walls:
            if not is_valid_wall_object(wall) or not has_identity_transform(wall):
                raise ValueError("経路内のWallが無効です。")
            if wall.jhm_wall.wall_id and wall.jhm_wall.wall_id in duplicates:
                raise ValueError("経路内のWall IDが重複しています。")
        for first, second in zip(self._pending, self._pending[1:]):
            endpoint = "END" if first[2] == "FORWARD" else "START"
            target_endpoint = "START" if second[2] == "FORWARD" else "END"
            if not any(connection.target_object is second[0]
                       and connection.target_endpoint == target_endpoint
                       and is_reciprocal_connection(first[0], endpoint, connection)
                       for connection in connection_collection(first[0], endpoint)):
                raise ValueError("経路の接続情報が変更されました。")

    def _finish(self, context, result):
        if self._draw_handle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(self._draw_handle, "WINDOW")
            self._draw_handle = None
        context.area.tag_redraw()
        return result


class JHM_OT_regenerate_finish(bpy.types.Operator):
    bl_idname = "jhm.regenerate_finish"
    bl_label = "経路を再生成"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _finish_poll(context)

    def execute(self, context):
        try:
            regenerate_finish(context.active_object, context.scene)
        except Exception as error:
            self.report({"ERROR"}, str(error)); return {"CANCELLED"}
        return {"FINISHED"}


def _profile_items(_owner, context):
    items = [("SIMPLE", "SIMPLE", "標準の矩形Profile"),
             ("BEVEL", "BEVEL", "上部室内側を45度面取り"),
             ("ROUNDED", "ROUNDED", "上部室内側を丸める")]
    if context and context.scene:
        items.extend((item.profile_id, item.display_name,
                      f"Custom Profile revision {item.profile_revision}")
                     for item in context.scene.jhm_custom_profiles)
    return items


class JHM_OT_register_custom_profile(bpy.types.Operator):
    """Snapshot the selected user Curve into the project library."""

    bl_idname = "jhm.register_custom_profile"
    bl_label = "選択CurveをCustom Profile登録"
    bl_options = {"REGISTER", "UNDO"}
    display_name: bpy.props.StringProperty(name="表示名", default="Custom Profile")

    def invoke(self, context, _event):
        if context.active_object:
            self.display_name = context.active_object.name
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        obj = context.active_object
        definition = None
        try:
            if obj is None or obj.type != "CURVE" or obj.data.dimensions != "2D":
                raise ValueError("2D Curve Objectを選択してください。")
            if not obj.matrix_basis.is_identity:
                raise ValueError("Object Transformをidentityにしてください。")
            if obj.parent is not None:
                raise ValueError("Parent付きCurveは登録元にできません。")
            if obj.constraints:
                raise ValueError("Constraint付きCurveは登録元にできません。")
            if obj.get("jhm_managed_profile") or obj.jhm_finish.is_finish:
                raise ValueError("JHM管理Curveは登録元にできません。")
            if obj.modifiers:
                raise ValueError("Modifier付きCurveは登録元にできません。")
            curve = obj.data
            if curve.shape_keys is not None:
                raise ValueError("Shape Key付きCurveは登録元にできません。")
            if (curve.bevel_depth or curve.extrude or curve.offset
                    or curve.taper_object or curve.bevel_object):
                raise ValueError("bevel/extrude/offset/taperのないCurveを使用してください。")
            if len(curve.splines) != 1:
                raise ValueError("Splineは1個だけ必要です。")
            spline = curve.splines[0]
            if not spline.use_cyclic_u or spline.type not in {"POLY", "BEZIER"}:
                raise ValueError("閉じたPOLYまたはBEZIER Splineが必要です。")
            if spline.type == "POLY":
                points = [(point.co.x, point.co.y) for point in spline.points]
                snapshot = make_snapshot("POLY", points=points)
            else:
                knots = [((point.co.x, point.co.y),
                          (point.handle_right.x, point.handle_right.y),
                          (point.handle_left.x, point.handle_left.y))
                         for point in spline.bezier_points]
                snapshot = make_snapshot("BEZIER", knots=knots)
            definition = context.scene.jhm_custom_profiles.add()
            definition.profile_id = snapshot.profile_id
            definition.profile_revision = snapshot.profile_revision
            definition.schema_version = snapshot.schema_version
            definition.display_name = self.display_name.strip() or "Custom Profile"
            definition.source_type = snapshot.source_type
            definition.source_object_name = obj.name
            definition.sampling_segments = (CUSTOM_BEZIER_SEGMENTS_PER_SPAN_R1
                                            if snapshot.source_type == "BEZIER" else 0)
            (definition.min_x, definition.max_x,
             definition.min_y, definition.max_y) = snapshot.bounds
            for index, (x, y) in enumerate(snapshot.contour):
                point = definition.points.add(); point.x = x; point.y = y
                point.smooth_to_next = index in snapshot.smooth_edges
            context.scene.jhm_custom_profile_index = len(context.scene.jhm_custom_profiles) - 1
        except Exception as error:
            if definition is not None:
                index = next((index for index, item in
                              enumerate(context.scene.jhm_custom_profiles)
                              if item == definition), None)
                if index is not None:
                    context.scene.jhm_custom_profiles.remove(index)
            self.report({"ERROR"}, f"Custom Profileを登録できませんでした: {error}")
            return {"CANCELLED"}
        return {"FINISHED"}


class JHM_OT_delete_custom_profile(bpy.types.Operator):
    bl_idname = "jhm.delete_custom_profile"
    bl_label = "選択Custom Profileを削除"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        library = context.scene.jhm_custom_profiles
        index = context.scene.jhm_custom_profile_index
        if not 0 <= index < len(library):
            self.report({"ERROR"}, "削除するCustom Profileがありません。")
            return {"CANCELLED"}
        item = library[index]
        if profile_is_referenced(context.scene.objects, item.profile_id,
                                 item.profile_revision, item.schema_version):
            self.report({"ERROR"}, "このProfileは使用中のため削除できません。")
            return {"CANCELLED"}
        library.remove(index)
        context.scene.jhm_custom_profile_index = max(0, min(index, len(library) - 1))
        return {"FINISHED"}


class JHM_OT_edit_finish_profile(bpy.types.Operator):
    """Transactionally switch or edit one Run's standard Profile."""

    bl_idname = "jhm.edit_finish_profile"
    bl_label = "Profileを変更"
    bl_options = {"REGISTER", "UNDO"}

    profile: bpy.props.EnumProperty(name="Profile", items=_profile_items)
    height_mm: bpy.props.FloatProperty(
        name="高さ (mm)", default=DEFAULT_HEIGHT_MM,
        min=0.1, max=100000.0, precision=1)
    projection_mm: bpy.props.FloatProperty(
        name="出幅 (mm)", default=DEFAULT_PROJECTION_MM,
        min=0.1, max=10000.0, precision=1)
    bevel_mm: bpy.props.FloatProperty(
        name="面取り (mm)", default=DEFAULT_BEVEL_MM,
        min=0.1, max=10000.0, precision=1)
    radius_mm: bpy.props.FloatProperty(
        name="半径 (mm)", default=DEFAULT_RADIUS_MM,
        min=0.1, max=10000.0, precision=1)
    uniform_scale: bpy.props.FloatProperty(
        name="均一スケール", default=1.0, min=0.000001, max=1000000.0)

    def draw(self, _context):
        layout = self.layout
        layout.prop(self, "profile")
        if self.profile not in (SIMPLE_PROFILE_ID, BEVEL_PROFILE_ID, ROUNDED_PROFILE_ID):
            layout.prop(self, "uniform_scale")
        else:
            layout.prop(self, "height_mm")
            layout.prop(self, "projection_mm")
        if self.profile == BEVEL_PROFILE_ID:
            layout.prop(self, "bevel_mm")
        elif self.profile == ROUNDED_PROFILE_ID:
            layout.prop(self, "radius_mm")

    @classmethod
    def poll(cls, context):
        return _finish_poll(context)

    def invoke(self, context, _event):
        try:
            resolved = resolve_finish_profile(context.active_object.jhm_finish, context.scene.jhm_custom_profiles)
        except ValueError as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}
        self.profile = resolved.profile_id
        self.height_mm = resolved.height_mm
        self.projection_mm = resolved.projection_mm
        self.bevel_mm = resolved.bevel_mm
        self.radius_mm = resolved.radius_mm
        self.uniform_scale = resolved.uniform_scale
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        obj = context.active_object
        finish = obj.jhm_finish
        custom = self.profile not in (SIMPLE_PROFILE_ID, BEVEL_PROFILE_ID,
                                      ROUNDED_PROFILE_ID)
        if custom:
            definition = next((item for item in context.scene.jhm_custom_profiles
                               if item.profile_id == self.profile), None)
            if definition is None:
                self.report({"ERROR"}, "Custom Profile定義が見つかりません。")
                return {"CANCELLED"}
            revision, schema = definition.profile_revision, definition.schema_version
        else:
            revision, schema = SIMPLE_PROFILE_REVISION, PROFILE_SCHEMA_VERSION
        new = (self.profile, revision, schema, self.height_mm, self.projection_mm,
               self.bevel_mm, self.radius_mm, self.uniform_scale)
        try:
            # Preparation performs Profile, path, miter and blocker validation
            # while the previous valid Curve remains installed.
            transactional_profile_edit(
                finish, new,
                lambda: prepare_finish_regeneration(obj, context.scene),
                context.scene.jhm_custom_profiles)
        except Exception as error:
            self.report({"ERROR"}, f"Profileを変更できませんでした: {error}")
            return {"CANCELLED"}
        return {"FINISHED"}


class JHM_OT_regenerate_all_finishes(bpy.types.Operator):
    """Explicitly apply floor/ceiling reference changes as one transaction."""

    bl_idname = "jhm.regenerate_all_finishes"
    bl_label = "仕上げを一括再生成"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        objects = managed_finish_objects(
            (obj, bool(getattr(getattr(obj, "jhm_finish", None), "is_finish", False)))
            for obj in context.scene.objects)
        try:
            regenerate_finishes_atomic(objects, context.scene)
        except Exception as error:
            self.report({"ERROR"}, f"一括再生成できませんでした: {error}")
            return {"CANCELLED"}
        self.report({"INFO"}, f"{len(objects)}件の仕上げを再生成しました。")
        return {"FINISHED"}


class JHM_OT_repair_finish(bpy.types.Operator):
    bl_idname = "jhm.repair_finish"
    bl_label = "管理状態へ復元"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _finish_poll(context)

    def execute(self, context):
        obj = context.active_object
        old_matrix = obj.matrix_basis.copy()
        old_pointers = [span.wall_object for span in obj.jhm_finish.spans]
        walls = [item for item in bpy.data.objects if is_valid_wall_object(item)]
        owners = [(wall, wall.jhm_wall.wall_id) for wall in walls]
        try:
            for span in obj.jhm_finish.spans:
                if span.wall_object not in walls or (
                        span.wall_object.jhm_wall.wall_id != span.expected_wall_id):
                    candidate = unique_rebind_candidate(span.expected_wall_id, owners)
                    if candidate is None:
                        raise ValueError("Wall参照を一意に復元できません。")
                    span.wall_object = candidate
            obj.matrix_basis.identity()
            problems = diagnose_finish(obj, context.scene)
            if problems:
                raise ValueError("Finish canonical dataを安全に復元できません。")
            regenerate_finish(obj, context.scene)
        except Exception as error:
            obj.matrix_basis = old_matrix
            for span, pointer in zip(obj.jhm_finish.spans, old_pointers):
                span.wall_object = pointer
            self.report({"ERROR"}, str(error)); return {"CANCELLED"}
        return {"FINISHED"}


class JHM_OT_delete_finish(bpy.types.Operator):
    bl_idname = "jhm.delete_finish"
    bl_label = "仕上げ経路を削除"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _finish_poll(context)

    def execute(self, context):
        obj = context.active_object
        data = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if data.users == 0:
            bpy.data.curves.remove(data)
        return {"FINISHED"}


class JHM_OT_convert_finish_mesh(bpy.types.Operator):
    bl_idname = "jhm.convert_finish_mesh"
    bl_label = "編集可能Meshとして確定"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _finish_poll(context)

    def execute(self, context):
        obj = context.active_object
        original_curve = obj.data
        prepared = None
        temporary = None
        mesh = None
        replacement_object = None

        def remove_temporary():
            if temporary is not None and temporary.name in bpy.data.objects:
                bpy.data.objects.remove(temporary, do_unlink=True)

        def discard_prepared():
            if prepared is not None:
                prepared.discard(prepared.replacement)

        def remove_mesh():
            if mesh is not None and mesh.users == 0:
                bpy.data.meshes.remove(mesh)

        def remove_replacement():
            if (replacement_object is not None
                    and replacement_object.name in bpy.data.objects):
                bpy.data.objects.remove(replacement_object, do_unlink=True)

        try:
            # Prepare every disposable resource while the managed source remains
            # untouched.  A newly-created Object has no copied Finish identity.
            prepared = prepare_finish_regeneration(obj, context.scene)
            if not prepared.ranges:
                raise ValueError("生成可能な巾木形状がありません。")
            temporary = bpy.data.objects.new(
                "JHM Finish Conversion Temporary", prepared.replacement)
            temporary.jhm_finish.is_finish = False
            temporary.jhm_finish.finish_id = ""
            context.collection.objects.link(temporary)
            depsgraph = context.evaluated_depsgraph_get()
            mesh = bpy.data.meshes.new_from_object(
                temporary.evaluated_get(depsgraph), depsgraph=depsgraph)
            if mesh is None:
                raise RuntimeError("Mesh datablockを生成できませんでした。")
            # Curve fill caps and side faces may evaluate with coincident but
            # unwelded boundary vertices.  Finalize topology while the managed
            # source still exists so any failure remains fully recoverable.
            weld_and_validate_finish_mesh(mesh)
            first_span = obj.jhm_finish.spans[0]
            apply_profile_shading(
                mesh,
                resolve_finish_profile(
                    obj.jhm_finish, context.scene.jhm_custom_profiles),
                profile_horizontal_sign(first_span.side,
                                        first_span.traversal_direction),
                prepared.ranges)
        except Exception as error:
            recovery = OperationRecovery()
            recovery.add(remove_temporary)
            recovery.add(discard_prepared)
            recovery.add(remove_mesh)
            failure = recover_operation(error, recovery)
            self.report({"ERROR"}, f"Meshへ変換できませんでした: {failure}")
            return {"CANCELLED"}

        # The evaluated Mesh no longer needs its disposable Object/Curve.  Do
        # this before the final swap so cleanup failure leaves the source valid.
        preparation_cleanup = OperationRecovery()
        preparation_cleanup.add(remove_temporary)
        preparation_cleanup.add(discard_prepared)
        try:
            preparation_cleanup()
        except Exception as error:
            recovery = OperationRecovery()
            recovery.add(remove_mesh)
            failure = recover_operation(error, recovery)
            self.report({"ERROR"}, f"Meshへ変換できませんでした: {failure}")
            return {"CANCELLED"}

        # Build and link a real Mesh Object while the original managed Finish is
        # still completely intact.  Object.data cannot change a CURVE to MESH.
        try:
            replacement_object = bpy.data.objects.new(f"{obj.name} Mesh", mesh)
            replacement_object.matrix_world = obj.matrix_world.copy()
            replacement_object.jhm_finish.is_finish = False
            replacement_object.jhm_finish.finish_id = ""
            collections = tuple(obj.users_collection) or (context.collection,)
            for collection in collections:
                collection.objects.link(replacement_object)
        except Exception as error:
            recovery = OperationRecovery()
            recovery.add(remove_replacement)
            recovery.add(remove_mesh)
            failure = recover_operation(error, recovery)
            self.report({"ERROR"}, f"Meshへ変換できませんでした: {failure}")
            return {"CANCELLED"}

        # Final commit: only now replace the original managed Object.  If the
        # removal itself fails, discard only the prepared replacement resources.
        try:
            bpy.data.objects.remove(obj, do_unlink=True)
        except Exception as error:
            recovery = OperationRecovery()
            recovery.add(remove_replacement)
            recovery.add(remove_mesh)
            failure = recover_operation(error, recovery)
            self.report({"ERROR"}, f"Meshへ変換できませんでした: {failure}")
            return {"CANCELLED"}
        cleanup_warning = None
        if original_curve.users == 0:
            try:
                bpy.data.curves.remove(original_curve)
            except Exception as error:
                # The replacement is already committed and usable.  Failure to
                # dispose zero-user old data must not turn success into CANCELLED.
                cleanup_warning = error
        for selected in context.selected_objects:
            selected.select_set(False)
        replacement_object.select_set(True)
        context.view_layer.objects.active = replacement_object
        if cleanup_warning is not None:
            self.report(
                {"WARNING"},
                f"Mesh変換は完了しましたが旧Curveの後処理に失敗しました: {cleanup_warning}",
            )
        return {"FINISHED"}
