"""Build 07-A Stage 1 two-point Stair creation operator."""

import math

import blf
import bpy
import gpu
from bpy_extras import view3d_utils
from gpu_extras.batch import batch_for_shader
from mathutils import Vector

from .stair_geometry import canonical_path, generate_stair_id


_PLANE_EPSILON = 1.0e-10


class JHM_OT_create_stair(bpy.types.Operator):
    """Commit one empty managed Mesh only after two valid plan clicks."""

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
        self._base_z_m = defaults.base_z_mm / 1000.0
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
                except ValueError as exc:
                    self.report({"WARNING"}, str(exc))
                    return {"RUNNING_MODAL"}
                return self._commit(context, path)
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

    def _commit(self, context, path):
        """The sole Scene-mutating path: create exactly one Mesh Object."""
        defaults = context.scene.jhm_new_stair_defaults
        mesh = bpy.data.meshes.new("JHM Stair")
        stair_object = bpy.data.objects.new("JHM Stair", mesh)
        try:
            context.collection.objects.link(stair_object)
            stair_object.location = (0.0, 0.0, 0.0)
            stair_object.rotation_euler = (0.0, 0.0, 0.0)
            stair_object.scale = (1.0, 1.0, 1.0)
            stair = stair_object.jhm_stair
            stair.is_stair = True
            stair.stair_id = generate_stair_id()
            for x, y in path:
                stair.path_points.add().xy = (x, y)
            for name in ("ascent_direction", "base_z_mm", "floor_to_floor_mm",
                         "riser_count", "stair_width_mm", "tread_thickness_mm",
                         "riser_thickness_mm"):
                setattr(stair, name, getattr(defaults, name))
        except Exception:
            bpy.data.objects.remove(stair_object, do_unlink=True)
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)
            raise
        for selected in context.selected_objects:
            selected.select_set(False)
        stair_object.select_set(True)
        context.view_layer.objects.active = stair_object
        return self._finish({"FINISHED"})

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
            vector = end - start
            arrow = []
            if vector.length > 12.0:
                direction = vector.normalized()
                left = Vector((-direction.y, direction.x))
                tip = start + vector * 0.65
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
            blf.draw(0, "END / UP")
        except Exception:
            self._remove_draw_handler()

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
