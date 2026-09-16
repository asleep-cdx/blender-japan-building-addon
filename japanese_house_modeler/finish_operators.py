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
from .finish_hardening import managed_finish_objects
from .dependency_transaction import OperationRecovery, recover_operation
from .finish_identity import (
    duplicate_ids, ensure_persistent_id, id_index, new_persistent_id,
)
from .finish_state import unique_rebind_candidate
from .joints import has_identity_transform
from .connections import connection_collection, is_reciprocal_connection
from .finish_surface import face_segment, resolve_surface_path, wall_axis
from .finish_path import (
    backspace_pending, propagate_canonical_side, traversal_for_connection,
)


def _wall_id_duplicates():
    walls = [obj for obj in bpy.data.objects if is_valid_wall_object(obj)]
    return duplicate_ids(walls, lambda obj: obj.jhm_wall.wall_id)


def _finish_poll(context):
    finish = getattr(context.active_object, "jhm_finish", None)
    return context.mode == "OBJECT" and finish is not None and finish.is_finish


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
            resolve_surface_path(segments_resolved)
            intervals = []
            for obj, _side, traversal in spans:
                _axis, length = wall_axis(
                    obj.jhm_wall.start, obj.jhm_wall.end)
                length *= 1000.0
                intervals.append((0.0, length) if traversal == "FORWARD"
                                 else (length, 0.0))
            validate_path_footprints(spans, segments_resolved, intervals)
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
            problems = diagnose_finish(obj)
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
            for polygon in mesh.polygons:
                polygon.use_smooth = False
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
