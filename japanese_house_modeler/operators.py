"""Interactive wall creation operators for the Japanese House Modeler."""

import math

import bpy
import gpu
from bpy_extras import view3d_utils
from gpu_extras.batch import batch_for_shader
from mathutils import Vector


_MIN_WALL_LENGTH_M = 1e-6
_PLANE_INTERSECTION_EPSILON = 1e-10
_ANGLE_STEP_RAD = math.radians(15.0)
_PREVIEW_LINE_WIDTH_PX = 1.5
_PREVIEW_MARKER_RADIUS_PX = 5.5
_PREVIEW_MARKER_SEGMENTS = 32
_SNAP_DISTANCE_PX = 16.0
_SNAP_HIGHLIGHT_RADIUS_PX = 9.0
_SNAP_HIGHLIGHT_LINE_WIDTH_PX = 2.5


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
        self._space_data = context.space_data
        self._view_layer = context.view_layer
        if self._region is None or self._region_data is None:
            self.report({"ERROR"}, "3D Viewportの表示領域を取得できません。")
            return {"CANCELLED"}

        defaults = context.scene.jhm_new_wall_defaults
        # Keep one wall's preview and final geometry consistent if UI values change.
        self._wall_thickness_mm = defaults.wall_thickness
        self._wall_height_mm = defaults.wall_height
        self._start_point = None
        self._end_candidate = None
        self._last_raw_endpoint = None
        self._snap_candidate = None
        self._start_snapped = False
        self._shift_held = bool(event.shift)
        self._draw_handle = bpy.types.SpaceView3D.draw_handler_add(
            self._draw_preview, (), "WINDOW", "POST_PIXEL"
        )
        context.window_manager.modal_handler_add(self)
        self._tag_redraw()
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        if event.type in {"ESC", "RIGHTMOUSE"}:
            return self._finish({"CANCELLED"})

        self._shift_held = bool(event.shift)

        if event.type in {"LEFT_SHIFT", "RIGHT_SHIFT"}:
            if self._start_point is not None and self._last_raw_endpoint is not None:
                self._update_end_candidate(self._last_raw_endpoint)
                self._tag_redraw()
            return {"RUNNING_MODAL"}

        if event.type == "MOUSEMOVE":
            point, _ = self._xy_plane_point(event)
            self._last_raw_endpoint = point
            if self._start_point is not None and point is not None:
                self._update_end_candidate(point)
            else:
                self._end_candidate = None
                if point is not None:
                    self.snap_endpoint_candidate(point)
                else:
                    self._snap_candidate = None
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

            self._last_raw_endpoint = point

            if self._start_point is None:
                self._start_point = self.snap_endpoint_candidate(point).copy()
                self._start_snapped = self._snap_candidate is not None
                self._end_candidate = self._start_point.copy()
                self._tag_redraw()
                return {"RUNNING_MODAL"}

            endpoint = self._resolve_final_endpoint(point)
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
        """Return the closest visible saved Wall endpoint within 12 screen pixels."""
        self._snap_candidate = None
        raw_2d = view3d_utils.location_3d_to_region_2d(
            self._region, self._region_data, raw_endpoint
        )
        if raw_2d is None:
            return raw_endpoint

        closest_distance = _SNAP_DISTANCE_PX
        for wall_object in self._view_layer.objects:
            wall = getattr(wall_object, "jhm_wall", None)
            if wall is None or not wall.is_wall:
                continue
            if not wall_object.visible_get(
                view_layer=self._view_layer, viewport=self._space_data
            ):
                continue

            for saved_endpoint in (wall.start, wall.end):
                endpoint = Vector(saved_endpoint)
                endpoint_2d = view3d_utils.location_3d_to_region_2d(
                    self._region, self._region_data, endpoint
                )
                if endpoint_2d is None:
                    continue
                if not (
                    0.0 <= endpoint_2d.x <= self._region.width
                    and 0.0 <= endpoint_2d.y <= self._region.height
                ):
                    continue

                distance = (endpoint_2d - raw_2d).length
                if distance <= _SNAP_DISTANCE_PX and (
                    self._snap_candidate is None or distance < closest_distance
                ):
                    closest_distance = distance
                    self._snap_candidate = endpoint.copy()

        if self._snap_candidate is not None:
            return self._snap_candidate
        return raw_endpoint

    def resolve_endpoint_candidate(self, start_point, raw_endpoint):
        """Apply a 15-degree world-XY angle constraint while Shift is held."""
        if self._snap_candidate is not None or not self._shift_held:
            return raw_endpoint

        delta = raw_endpoint - start_point
        if delta.length <= _MIN_WALL_LENGTH_M:
            return raw_endpoint

        raw_angle = math.atan2(delta.y, delta.x)
        constrained_angle = round(raw_angle / _ANGLE_STEP_RAD) * _ANGLE_STEP_RAD
        axis = Vector(
            (math.cos(constrained_angle), math.sin(constrained_angle), 0.0)
        )
        projected_length = delta.dot(axis)
        return start_point + axis * projected_length

    def _resolve_final_endpoint(self, raw_endpoint):
        snapped_endpoint = self.snap_endpoint_candidate(raw_endpoint)
        return self.resolve_endpoint_candidate(
            self._start_point, snapped_endpoint
        )

    def _update_end_candidate(self, raw_endpoint):
        self._end_candidate = self._resolve_final_endpoint(raw_endpoint)

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
        if self._start_point is None:
            if self._snap_candidate is not None:
                self._draw_snap_highlight(self._snap_candidate)
            return
        if self._end_candidate is None:
            return
        if not self._is_valid_wall_length(self._start_point, self._end_candidate):
            if self._snap_candidate is not None:
                self._draw_snap_highlight(self._snap_candidate)
            return

        start_2d = view3d_utils.location_3d_to_region_2d(
            self._region, self._region_data, self._start_point
        )
        end_2d = view3d_utils.location_3d_to_region_2d(
            self._region, self._region_data, self._end_candidate
        )
        if start_2d is None or end_2d is None:
            return

        try:
            shader = gpu.shader.from_builtin("UNIFORM_COLOR")
            gpu.state.blend_set("ALPHA")
            gpu.state.line_width_set(_PREVIEW_LINE_WIDTH_PX)

            shader.bind()
            shader.uniform_float("color", (0.1, 0.4, 0.9, 1.0))
            batch_for_shader(
                shader,
                "LINES",
                {"pos": [tuple(start_2d), tuple(end_2d)]},
            ).draw(shader)

            for center in (start_2d, end_2d):
                marker_points = []
                for index in range(_PREVIEW_MARKER_SEGMENTS + 1):
                    angle = (math.tau * index) / _PREVIEW_MARKER_SEGMENTS
                    marker_points.append(
                        (
                            center.x + math.cos(angle) * _PREVIEW_MARKER_RADIUS_PX,
                            center.y + math.sin(angle) * _PREVIEW_MARKER_RADIUS_PX,
                        )
                    )

                batch_for_shader(
                    shader,
                    "LINE_STRIP",
                    {"pos": marker_points},
                ).draw(shader)

            if self._start_snapped:
                gpu.state.line_width_set(_SNAP_HIGHLIGHT_LINE_WIDTH_PX)
                self._draw_marker_ring(
                    shader, start_2d, _SNAP_HIGHLIGHT_RADIUS_PX
                )
            if self._snap_candidate is not None:
                gpu.state.line_width_set(_SNAP_HIGHLIGHT_LINE_WIDTH_PX)
                self._draw_marker_ring(
                    shader, end_2d, _SNAP_HIGHLIGHT_RADIUS_PX
                )
        except Exception:
            self._remove_draw_handler()
        finally:
            gpu.state.line_width_set(1.0)
            gpu.state.blend_set("NONE")

    def _draw_snap_highlight(self, endpoint):
        endpoint_2d = view3d_utils.location_3d_to_region_2d(
            self._region, self._region_data, endpoint
        )
        if endpoint_2d is None:
            return
        try:
            shader = gpu.shader.from_builtin("UNIFORM_COLOR")
            gpu.state.blend_set("ALPHA")
            gpu.state.line_width_set(_SNAP_HIGHLIGHT_LINE_WIDTH_PX)
            shader.bind()
            shader.uniform_float("color", (0.1, 0.4, 0.9, 1.0))
            self._draw_marker_ring(shader, endpoint_2d, _PREVIEW_MARKER_RADIUS_PX)
            self._draw_marker_ring(shader, endpoint_2d, _SNAP_HIGHLIGHT_RADIUS_PX)
        except Exception:
            self._remove_draw_handler()
        finally:
            gpu.state.line_width_set(1.0)
            gpu.state.blend_set("NONE")

    def _draw_marker_ring(self, shader, center, radius):
        marker_points = []
        for index in range(_PREVIEW_MARKER_SEGMENTS + 1):
            angle = (math.tau * index) / _PREVIEW_MARKER_SEGMENTS
            marker_points.append(
                (
                    center.x + math.cos(angle) * radius,
                    center.y + math.sin(angle) * radius,
                )
            )
        batch_for_shader(
            shader,
            "LINE_STRIP",
            {"pos": marker_points},
        ).draw(shader)

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
