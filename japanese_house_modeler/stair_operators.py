"""Build 07-A Stair creation, transactional editing, and explicit repair."""

import math
from types import SimpleNamespace

import blf
import bpy
import gpu
from bpy_extras import view3d_utils
from gpu_extras.batch import batch_for_shader
from mathutils import Vector

from .stair_geometry import (
    canonical_path, generate_stair_id, prepare_stair_geometry,
)
from .stair_state import (
    ID_CONFLICT, ID_MISSING, StairState, diagnose_stair,
    duplicate_stair_ids, operation_allowed,
)


_PLANE_EPSILON = 1.0e-10
_STAIR_DEFAULT_NAMES = (
    "ascent_direction", "base_z_mm", "floor_to_floor_mm", "riser_count",
    "stair_width_mm", "tread_thickness_mm", "riser_thickness_mm",
)
_CANONICAL_NAMES = _STAIR_DEFAULT_NAMES


def _canonical_snapshot(stair):
    return {
        "path_points": tuple(tuple(point.xy) for point in stair.path_points),
        **{name: getattr(stair, name) for name in _CANONICAL_NAMES},
    }


def _managed_records(scene):
    return tuple(SimpleNamespace(
        is_managed=True, stair_id=obj.jhm_stair.stair_id)
        for obj in scene.objects
        if getattr(getattr(obj, "jhm_stair", None), "is_stair", False))


def stair_issues(stair_object, scene):
    """Adapt Blender RNA to the pure managed-state diagnostic model."""
    stair = stair_object.jhm_stair
    mesh = getattr(stair_object, "data", None)
    state = StairState(
        stair.stair_id, tuple(tuple(point.xy) for point in stair.path_points),
        stair.ascent_direction, stair.base_z_mm, stair.floor_to_floor_mm,
        stair.riser_count, stair.stair_width_mm, stair.tread_thickness_mm,
        stair.riser_thickness_mm, tuple(stair_object.location),
        tuple(stair_object.rotation_euler), tuple(stair_object.scale),
        stair_object.type, mesh is not None,
        len(mesh.vertices) if mesh is not None and hasattr(mesh, "vertices") else 0,
        len(mesh.polygons) if mesh is not None and hasattr(mesh, "polygons") else 0,
    )
    duplicates = duplicate_stair_ids(_managed_records(scene))
    return diagnose_stair(state, duplicates)


def _selected_stair(context):
    obj = context.active_object
    if obj is None or not getattr(getattr(obj, "jhm_stair", None), "is_stair", False):
        return None
    return obj


def _set_canonical(stair, values):
    stair.path_points.clear()
    for x, y in values["path_points"]:
        stair.path_points.add().xy = (x, y)
    for name in _CANONICAL_NAMES:
        setattr(stair, name, values[name])


def _prepare_candidate(values):
    return prepare_stair_geometry(
        values["path_points"], values["ascent_direction"], values["base_z_mm"],
        values["floor_to_floor_mm"], values["riser_count"],
        values["stair_width_mm"], values["tread_thickness_mm"],
        values["riser_thickness_mm"])[2]


def _best_effort(action):
    """Run rollback/cleanup work without replacing a transaction exception."""
    try:
        action()
    except Exception:
        pass


def _cleanup_unused_data(data):
    """Best-effort cleanup; never assume an arbitrary Object.data is a Mesh."""
    if data is None:
        return

    def remove_if_unused():
        if data.users == 0 and isinstance(data, bpy.types.Mesh):
            bpy.data.meshes.remove(data)

    _best_effort(remove_if_unused)


def _transactional_update(stair_object, candidate, *, new_stair_id=None,
                          reset_transform=False):
    """Build replacement first, then atomically swap and roll back commit errors."""
    mesh_data = _prepare_candidate(candidate)
    old_data = stair_object.data
    stair = stair_object.jhm_stair
    old_canonical = _canonical_snapshot(stair)
    old_id = stair.stair_id
    old_transform = (tuple(stair_object.location),
                     tuple(stair_object.rotation_euler), tuple(stair_object.scale))
    replacement = None
    swapped = False
    try:
        base_name = old_data.name if old_data else stair_object.name
        replacement = bpy.data.meshes.new(f"{base_name} Update")
        replacement.from_pydata(mesh_data.vertices, (), mesh_data.faces)
        replacement.update()
        if not replacement.vertices or not replacement.polygons:
            raise ValueError("replacement Stair Meshが空です。")
        materials = getattr(old_data, "materials", ())
        if materials is not None:
            for material in materials:
                replacement.materials.append(material)
        stair_object.data = replacement
        swapped = True
        _set_canonical(stair, candidate)
        if new_stair_id is not None:
            stair.stair_id = new_stair_id
        if reset_transform:
            stair_object.location = (0.0, 0.0, 0.0)
            stair_object.rotation_euler = (0.0, 0.0, 0.0)
            stair_object.scale = (1.0, 1.0, 1.0)
    except Exception:
        if swapped:
            _best_effort(lambda: setattr(stair_object, "data", old_data))
            _best_effort(lambda: _set_canonical(stair, old_canonical))
            _best_effort(lambda: setattr(stair, "stair_id", old_id))
            _best_effort(lambda: setattr(stair_object, "location", old_transform[0]))
            _best_effort(
                lambda: setattr(stair_object, "rotation_euler", old_transform[1]))
            _best_effort(lambda: setattr(stair_object, "scale", old_transform[2]))
        _cleanup_unused_data(replacement)
        raise
    # The transaction is already committed.  Orphan cleanup must not turn a
    # successful edit/Repair into a failure without rollback.
    _cleanup_unused_data(old_data)


class _StairOperationMixin:
    operation = None

    @classmethod
    def poll(cls, context):
        return _selected_stair(context) is not None

    def _require_allowed(self, context):
        obj = _selected_stair(context)
        issues = stair_issues(obj, context.scene) if obj else ()
        if obj is None or not operation_allowed(self.operation, issues):
            self.report({"WARNING"}, "現在の管理状態ではこの操作を実行できません。")
            return None
        return obj

    def _run_candidate(self, context, candidate, **kwargs):
        obj = self._require_allowed(context)
        if obj is None:
            return {"CANCELLED"}
        try:
            _transactional_update(obj, candidate, **kwargs)
        except Exception as exc:
            self.report({"WARNING"}, str(exc))
            return {"CANCELLED"}
        return {"FINISHED"}


class JHM_OT_create_stair(bpy.types.Operator):
    """Commit one visible managed Mesh only after two valid plan clicks."""

    bl_idname = "jhm.create_stair"
    bl_label = "階段を作成"
    bl_description = "中心線のSTARTとENDをクリックして階段を作成します"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.area is not None and context.area.type == "VIEW_3D"

    def invoke(self, context, _event):
        self._area = context.area
        self._region = next((r for r in self._area.regions if r.type == "WINDOW"), None)
        self._region_data = context.space_data.region_3d
        if self._region is None or self._region_data is None:
            self.report({"ERROR"}, "3D Viewportの表示領域を取得できません。")
            return {"CANCELLED"}
        defaults = context.scene.jhm_new_stair_defaults
        # One modal operation is deterministic even if sidebar defaults are
        # edited before its second click.
        self._stair_defaults = {
            name: getattr(defaults, name) for name in _STAIR_DEFAULT_NAMES
        }
        self._base_z_m = self._stair_defaults["base_z_mm"] / 1000.0
        self._start_point = None
        self._candidate = None
        self._draw_handle = bpy.types.SpaceView3D.draw_handler_add(
            self._draw_preview, (), "WINDOW", "POST_PIXEL")
        context.window_manager.modal_handler_add(self)
        self._tag_redraw()
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        try:
            if event.type in {"ESC", "RIGHTMOUSE"}:
                return self._finish({"CANCELLED"})
            if event.type == "MOUSEMOVE":
                self._candidate, _error = self._plane_point(event)
                self._tag_redraw()
                return {"RUNNING_MODAL"}
            if event.type == "LEFTMOUSE" and event.value == "PRESS":
                point, error = self._plane_point(event)
                if point is None:
                    self.report({"WARNING"}, error or "基準平面との交点を取得できません。")
                    return {"RUNNING_MODAL"}
                if self._start_point is None:
                    self._start_point = point
                    self._candidate = point
                    self._tag_redraw()
                    return {"RUNNING_MODAL"}
                try:
                    path = canonical_path((self._start_point, point))
                    _layout, _fragments, mesh_data = prepare_stair_geometry(
                        path,
                        self._stair_defaults["ascent_direction"],
                        self._stair_defaults["base_z_mm"],
                        self._stair_defaults["floor_to_floor_mm"],
                        self._stair_defaults["riser_count"],
                        self._stair_defaults["stair_width_mm"],
                        self._stair_defaults["tread_thickness_mm"],
                        self._stair_defaults["riser_thickness_mm"],
                    )
                except ValueError as exc:
                    self.report({"WARNING"}, str(exc))
                    return {"RUNNING_MODAL"}
                return self._commit(context, path, mesh_data)
            return {"RUNNING_MODAL"}
        except Exception:
            self._finish({"CANCELLED"})
            raise

    def _plane_point(self, event):
        coordinate = (event.mouse_x - self._region.x, event.mouse_y - self._region.y)
        try:
            origin = view3d_utils.region_2d_to_origin_3d(
                self._region, self._region_data, coordinate)
            direction = view3d_utils.region_2d_to_vector_3d(
                self._region, self._region_data, coordinate)
        except Exception:
            return None, "基準平面との交点を取得できません。"
        if abs(direction.z) <= _PLANE_EPSILON:
            return None, "XY平面を見下ろすビューに変更してください。"
        distance = (self._base_z_m - origin.z) / direction.z
        if distance < 0.0 or not math.isfinite(distance):
            return None, "基準平面は現在のビューrayの後方にあります。"
        point = origin + direction * distance
        if not all(math.isfinite(value) for value in (point.x, point.y)):
            return None, "基準平面との交点が数値的に不安定です。"
        return Vector((point.x, point.y, self._base_z_m)), None

    def _commit(self, context, path, mesh_data):
        """The sole Scene-mutating path: create exactly one Mesh Object."""
        previous_selected = tuple(context.selected_objects)
        previous_active = context.view_layer.objects.active
        mesh = None
        stair_object = None
        try:
            mesh = bpy.data.meshes.new("JHM Stair")
            mesh.from_pydata(mesh_data.vertices, (), mesh_data.faces)
            mesh.update()
            stair_object = bpy.data.objects.new("JHM Stair", mesh)
            context.collection.objects.link(stair_object)
            stair_object.location = (0.0, 0.0, 0.0)
            stair_object.rotation_euler = (0.0, 0.0, 0.0)
            stair_object.scale = (1.0, 1.0, 1.0)
            stair = stair_object.jhm_stair
            stair.is_stair = True
            stair.stair_id = generate_stair_id()
            for x, y in path:
                stair.path_points.add().xy = (x, y)
            for name, value in self._stair_defaults.items():
                setattr(stair, name, value)
            for selected in context.selected_objects:
                selected.select_set(False)
            stair_object.select_set(True)
            context.view_layer.objects.active = stair_object
        except Exception:
            try:
                if stair_object is not None:
                    bpy.data.objects.remove(stair_object, do_unlink=True)
                if mesh is not None and mesh.users == 0:
                    bpy.data.meshes.remove(mesh)
            finally:
                self._restore_selection(
                    context, previous_selected, previous_active)
            raise
        return self._finish({"FINISHED"})

    @staticmethod
    def _restore_selection(context, previous_selected, previous_active):
        """Best-effort rollback without masking the original commit failure."""
        try:
            current_selected = tuple(context.selected_objects)
        except (AttributeError, ReferenceError, RuntimeError, TypeError):
            current_selected = ()
        for selected in current_selected:
            try:
                selected.select_set(False)
            except (AttributeError, ReferenceError, RuntimeError, TypeError):
                pass
        for selected in previous_selected:
            try:
                selected.select_set(True)
            except (AttributeError, ReferenceError, RuntimeError, TypeError):
                pass
        try:
            context.view_layer.objects.active = previous_active
        except (AttributeError, ReferenceError, RuntimeError, TypeError):
            pass

    def _draw_preview(self):
        try:
            if self._start_point is None or self._candidate is None:
                return
            start = view3d_utils.location_3d_to_region_2d(
                self._region, self._region_data, self._start_point)
            end = view3d_utils.location_3d_to_region_2d(
                self._region, self._region_data, self._candidate)
            if start is None or end is None:
                return
            shader = gpu.shader.from_builtin("UNIFORM_COLOR")
            shader.bind()
            uphill_start, uphill_end = (
                (start, end)
                if self._stair_defaults["ascent_direction"] == "FORWARD"
                else (end, start)
            )
            vector = uphill_end - uphill_start
            arrow = []
            if vector.length > 12.0:
                direction = vector.normalized()
                left = Vector((-direction.y, direction.x))
                tip = uphill_start + vector * 0.65
                arrow = [tip, tip - direction * 12 + left * 6,
                         tip, tip - direction * 12 - left * 6]
            gpu.state.line_width_set(2.0)
            shader.uniform_float("color", (0.2, 0.8, 1.0, 1.0))
            vertices = (start, end, *arrow)
            batch_for_shader(shader, "LINES", {"pos": vertices}).draw(shader)
            gpu.state.point_size_set(8.0)
            batch_for_shader(shader, "POINTS", {"pos": (start, end)}).draw(shader)
            blf.position(0, start.x + 6, start.y + 6, 0)
            blf.draw(0, "START")
            blf.position(0, end.x + 6, end.y + 6, 0)
            blf.draw(0, "END")
        except Exception:
            self._remove_draw_handler()
        finally:
            gpu.state.line_width_set(1.0)
            gpu.state.point_size_set(1.0)

    def _finish(self, result):
        self._remove_draw_handler()
        self._tag_redraw()
        return result

    def _remove_draw_handler(self):
        handle = getattr(self, "_draw_handle", None)
        if handle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(handle, "WINDOW")
            self._draw_handle = None

    def _tag_redraw(self):
        if getattr(self, "_area", None) is not None:
            self._area.tag_redraw()


class JHM_OT_edit_stair_dimensions(_StairOperationMixin, bpy.types.Operator):
    bl_idname = "jhm.edit_stair_dimensions"
    bl_label = "階段寸法を変更"
    bl_options = {"REGISTER", "UNDO"}
    operation = "EDIT_DIMENSIONS"

    base_z_mm: bpy.props.FloatProperty(name="下端基準高さ (mm)")
    floor_to_floor_mm: bpy.props.FloatProperty(name="階高 (mm)")
    riser_count: bpy.props.IntProperty(name="蹴上数")
    stair_width_mm: bpy.props.FloatProperty(name="階段幅 (mm)")
    tread_thickness_mm: bpy.props.FloatProperty(name="踏板厚 (mm)")
    riser_thickness_mm: bpy.props.FloatProperty(name="蹴込み板厚 (mm)")

    def invoke(self, context, _event):
        obj = self._require_allowed(context)
        if obj is None:
            return {"CANCELLED"}
        stair = obj.jhm_stair
        for name in _CANONICAL_NAMES:
            if name != "ascent_direction":
                setattr(self, name, getattr(stair, name))
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        obj = self._require_allowed(context)
        if obj is None:
            return {"CANCELLED"}
        candidate = _canonical_snapshot(obj.jhm_stair)
        for name in _CANONICAL_NAMES:
            if name != "ascent_direction":
                candidate[name] = getattr(self, name)
        return self._run_candidate(context, candidate)


class JHM_OT_edit_stair_path(_StairOperationMixin, bpy.types.Operator):
    bl_idname = "jhm.edit_stair_path"
    bl_label = "Path座標を変更"
    bl_options = {"REGISTER", "UNDO"}
    operation = "EDIT_PATH"

    p0_x_mm: bpy.props.FloatProperty(name="P0 X (mm)")
    p0_y_mm: bpy.props.FloatProperty(name="P0 Y (mm)")
    p1_x_mm: bpy.props.FloatProperty(name="P1 X (mm)")
    p1_y_mm: bpy.props.FloatProperty(name="P1 Y (mm)")

    def invoke(self, context, _event):
        obj = self._require_allowed(context)
        if obj is None:
            return {"CANCELLED"}
        points = tuple(tuple(point.xy) for point in obj.jhm_stair.path_points)
        self.p0_x_mm, self.p0_y_mm = (value * 1000.0 for value in points[0])
        self.p1_x_mm, self.p1_y_mm = (value * 1000.0 for value in points[1])
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        obj = self._require_allowed(context)
        if obj is None:
            return {"CANCELLED"}
        candidate = _canonical_snapshot(obj.jhm_stair)
        candidate["path_points"] = (
            (self.p0_x_mm / 1000.0, self.p0_y_mm / 1000.0),
            (self.p1_x_mm / 1000.0, self.p1_y_mm / 1000.0),
        )
        return self._run_candidate(context, candidate)


class JHM_OT_reverse_stair_ascent(_StairOperationMixin, bpy.types.Operator):
    bl_idname = "jhm.reverse_stair_ascent"
    bl_label = "上り方向を反転"
    bl_options = {"REGISTER", "UNDO"}
    operation = "REVERSE"

    def execute(self, context):
        obj = self._require_allowed(context)
        if obj is None:
            return {"CANCELLED"}
        candidate = _canonical_snapshot(obj.jhm_stair)
        candidate["ascent_direction"] = (
            "REVERSE" if candidate["ascent_direction"] == "FORWARD" else "FORWARD")
        return self._run_candidate(context, candidate)


class JHM_OT_regenerate_stair(_StairOperationMixin, bpy.types.Operator):
    bl_idname = "jhm.regenerate_stair"
    bl_label = "階段を再生成"
    bl_options = {"REGISTER", "UNDO"}
    operation = "REGENERATE"

    def execute(self, context):
        obj = self._require_allowed(context)
        if obj is None:
            return {"CANCELLED"}
        return self._run_candidate(context, _canonical_snapshot(obj.jhm_stair))


class JHM_OT_repair_stair(_StairOperationMixin, bpy.types.Operator):
    bl_idname = "jhm.repair_stair"
    bl_label = "管理状態へ復元"
    bl_options = {"REGISTER", "UNDO"}
    operation = "REPAIR"

    def execute(self, context):
        obj = self._require_allowed(context)
        if obj is None:
            return {"CANCELLED"}
        issues = stair_issues(obj, context.scene)
        new_id = (generate_stair_id()
                  if ID_CONFLICT in issues or ID_MISSING in issues else None)
        return self._run_candidate(
            context, _canonical_snapshot(obj.jhm_stair),
            new_stair_id=new_id, reset_transform=True)
