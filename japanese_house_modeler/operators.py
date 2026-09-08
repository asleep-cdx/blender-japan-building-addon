"""Interactive wall creation operators for the Japanese House Modeler."""

import math

import bpy
import gpu
from bpy_extras import view3d_utils
from gpu_extras.batch import batch_for_shader
from mathutils import Vector


_MIN_WALL_LENGTH_M = 1e-6
_PLANE_INTERSECTION_EPSILON = 1e-10


class JHM_OT_create_wall(bpy.types.Operator):
    """Create one wall from two points on the world XY plane."""

    bl_idname = "jhm.create_wall"
    bl_label = "壁を作成"
    bl_description = "始点と終点をクリックして壁を作成します"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.area is not None and context.area.type == "VIEW_3D"

    def invoke(self, context, event):
        self._area = context.area
        self._region = next(
            (region for region in self._area.regions if region.type == "WINDOW"), None
        )
        self._region_data = context.space_data.region_3d
        if self._region is None or self._region_data is None:
            self.report({"ERROR"}, "3D Viewportの表示領域を取得できません。")
            return {"CANCELLED"}

        defaults = context.scene.jhm_new_wall_defaults
        # Keep one wall's preview and final geometry consistent if UI values change.
        self._wall_thickness_mm = defaults.wall_thickness
        self._wall_height_mm = defaults.wall_height
        self._start_point = None
        self._end_candidate = None
        self._draw_handle = bpy.types.SpaceView3D.draw_handler_add(
            self._draw_preview, (), "WINDOW", "POST_VIEW"
        )
        context.window_manager.modal_handler_add(self)
        self._tag_redraw()
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        if event.type in {"ESC", "RIGHTMOUSE"}:
            return self._finish({"CANCELLED"})

        if event.type == "MOUSEMOVE":
            point, _ = self._xy_plane_point(event)
            if self._start_point is not None and point is not None:
                snapped_endpoint = self.snap_endpoint_candidate(point)
                self._end_candidate = self.resolve_endpoint_candidate(
                    self._start_point, snapped_endpoint
                )
            else:
                self._end_candidate = None
            self._tag_redraw()
            return {"RUNNING_MODAL"}

        if event.type == "LEFTMOUSE" and event.value == "PRESS":
            point, error = self._xy_plane_point(event)
            if point is None:
                self.report(
                    {"WARNING"},
                    error or "XY平面上の座標を取得できません。",
                )
                return {"RUNNING_MODAL"}

            if self._start_point is None:
                self._start_point = point
                self._end_candidate = point
                self._tag_redraw()
                return {"RUNNING_MODAL"}

            snapped_endpoint = self.snap_endpoint_candidate(point)
            endpoint = self.resolve_endpoint_candidate(
                self._start_point, snapped_endpoint
            )
            if not self._is_valid_wall_length(self._start_point, endpoint):
                self.report({"WARNING"}, "壁の長さが短すぎます。")
                return {"RUNNING_MODAL"}

            return self._create_wall(context, endpoint)

        return {"RUNNING_MODAL"}

    def _xy_plane_point(self, event):
        """Intersect the viewport ray with Z=0 without using object snapping."""
        coordinate = (
            event.mouse_x - self._region.x,
            event.mouse_y - self._region.y,
        )
        try:
            origin = view3d_utils.region_2d_to_origin_3d(
                self._region, self._region_data, coordinate
            )
            direction = view3d_utils.region_2d_to_vector_3d(
                self._region, self._region_data, coordinate
            )
        except Exception:
            return None, "XY平面との交差を取得できません。視点を変更してください。"
        if abs(direction.z) <= _PLANE_INTERSECTION_EPSILON:
            return None, "トップビューまたはXY平面を見下ろす斜めビューに変更してください。"

        distance = -origin.z / direction.z
        if distance < 0.0 or not math.isfinite(distance):
            return None, "トップビューまたはXY平面を見下ろす斜めビューに変更してください。"

        point = origin + direction * distance
        if not math.isfinite(point.x) or not math.isfinite(point.y):
            return None, "XY平面との交差が数値的に不安定です。視点を変更してください。"
        return Vector((point.x, point.y, 0.0)), None

    def snap_endpoint_candidate(self, raw_endpoint):
        """Build 02-A intentionally has no snapping; Build 02-C can extend this."""
        return raw_endpoint

    def resolve_endpoint_candidate(self, start_point, raw_endpoint):
        """Leave candidates unconstrained; Build 02-B can add drawing constraints."""
        del start_point
        return raw_endpoint

    def _is_valid_wall_length(self, start_point, endpoint):
        """This is a geometry-degeneracy threshold, not a building minimum size."""
        return (endpoint - start_point).length > _MIN_WALL_LENGTH_M

    def _wall_geometry(self, start_point, endpoint):
        """Return vertices and faces for a closed cuboid centred on the wall core."""
        direction = endpoint - start_point
        length = direction.length
        if length <= _MIN_WALL_LENGTH_M:
            return None

        core_axis = direction / length
        perpendicular = Vector((-core_axis.y, core_axis.x, 0.0))
        half_thickness = self._wall_thickness_mm / 2000.0
        height = self._wall_height_mm / 1000.0
        if half_thickness <= 0.0 or height <= 0.0:
            return None

        lower = (
            start_point + perpendicular * half_thickness,
            start_point - perpendicular * half_thickness,
            endpoint - perpendicular * half_thickness,
            endpoint + perpendicular * half_thickness,
        )
        vertices = [tuple(point) for point in lower]
        vertices.extend((point.x, point.y, height) for point in lower)
        faces = (
            (0, 3, 2, 1),
            (4, 5, 6, 7),
            (0, 1, 5, 4),
            (1, 2, 6, 5),
            (2, 3, 7, 6),
            (3, 0, 4, 7),
        )
        return vertices, faces

    def _create_wall(self, context, endpoint):
        geometry = self._wall_geometry(self._start_point, endpoint)
        if geometry is None:
            self.report({"WARNING"}, "壁の寸法が不正です。")
            return {"RUNNING_MODAL"}

        mesh = None
        wall_object = None
        try:
            vertices, faces = geometry
            mesh = bpy.data.meshes.new("Wall")
            mesh.from_pydata(vertices, [], faces)
            mesh.update()
            wall_object = bpy.data.objects.new("Wall", mesh)
            context.collection.objects.link(wall_object)

            wall = wall_object.jhm_wall
            wall.is_wall = True
            wall.start = tuple(self._start_point)
            wall.end = tuple(endpoint)
            wall.wall_thickness = self._wall_thickness_mm
            wall.wall_height = self._wall_height_mm

            for selected in context.selected_objects:
                selected.select_set(False)
            wall_object.select_set(True)
            context.view_layer.objects.active = wall_object
        except Exception as error:
            if wall_object is not None:
                bpy.data.objects.remove(wall_object, do_unlink=True)
            elif mesh is not None:
                bpy.data.meshes.remove(mesh)
            self.report({"ERROR"}, f"壁を生成できませんでした: {error}")
            return self._finish({"CANCELLED"})

        return self._finish({"FINISHED"})

    def _draw_preview(self):
        if self._start_point is None or self._end_candidate is None:
            return
        geometry = self._wall_geometry(self._start_point, self._end_candidate)
        if geometry is None:
            return

        vertices, _faces = geometry
        triangles = (
            (0, 3, 2), (0, 2, 1),
            (4, 5, 6), (4, 6, 7),
            (0, 1, 5), (0, 5, 4),
            (1, 2, 6), (1, 6, 5),
            (2, 3, 7), (2, 7, 6),
            (3, 0, 4), (3, 4, 7),
        )
        edges = (
            (0, 1), (1, 2), (2, 3), (3, 0),
            (4, 5), (5, 6), (6, 7), (7, 4),
            (0, 4), (1, 5), (2, 6), (3, 7),
        )
        try:
            shader = gpu.shader.from_builtin("UNIFORM_COLOR")
            gpu.state.blend_set("ALPHA")
            shader.bind()
            shader.uniform_float("color", (0.2, 0.65, 1.0, 0.25))
            batch_for_shader(
                shader, "TRIS", {"pos": vertices}, indices=triangles
            ).draw(shader)
            shader.uniform_float("color", (0.1, 0.4, 0.9, 1.0))
            batch_for_shader(shader, "LINES", {"pos": vertices}, indices=edges).draw(shader)
        except Exception:
            self._remove_draw_handler()
        finally:
            gpu.state.blend_set("NONE")

    def _tag_redraw(self):
        if self._area is not None:
            self._area.tag_redraw()

    def _finish(self, result):
        self._remove_draw_handler()
        self._tag_redraw()
        return result

    def _remove_draw_handler(self):
        if self._draw_handle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(self._draw_handle, "WINDOW")
            self._draw_handle = None
