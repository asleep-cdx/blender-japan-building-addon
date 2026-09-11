"""Interactive wall creation operators for the Japanese House Modeler."""

import math

import bpy
import gpu
from bpy_extras import view3d_utils
from gpu_extras.batch import batch_for_shader
from mathutils import Vector

from .connections import (
    attach_to_junction,
    detach_endpoint,
    restore_topology,
    snapshot_topology,
)
from .drawing_alignment import (
    combined_axis_alignment, extension_geometry_key, project_to_wall_extension,
)
from .joints import (
    affected_walls, has_identity_transform, merge_affected, regenerate_wall_meshes,
)


_MIN_WALL_LENGTH_M = 1e-6
_PLANE_INTERSECTION_EPSILON = 1e-10
_ANGLE_STEP_RAD = math.radians(15.0)
_PREVIEW_LINE_WIDTH_PX = 1.5
_PREVIEW_MARKER_RADIUS_PX = 5.5
_PREVIEW_MARKER_SEGMENTS = 32
_SNAP_DISTANCE_PX = 16.0
_ALIGN_DISTANCE_PX = 10.0
_SNAP_HIGHLIGHT_RADIUS_PX = 9.0
_SNAP_HIGHLIGHT_LINE_WIDTH_PX = 2.5
_ALIGN_GUIDE_LINE_WIDTH_PX = 1.0
_AXIS_EPSILON = 1e-10
_TRANSFORM_EPSILON = 1e-6


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
        self._snap_target_object = None
        self._snap_target_endpoint = None
        self._start_snap_target_object = None
        self._start_snap_target_endpoint = None
        self._x_align_reference = None
        self._y_align_reference = None
        self._extension_align_reference = None
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
            if self._last_raw_endpoint is not None:
                self._update_candidate(self._last_raw_endpoint)
                self._tag_redraw()
            return {"RUNNING_MODAL"}

        if event.type == "MOUSEMOVE":
            point, _ = self._xy_plane_point(event)
            self._last_raw_endpoint = point
            if self._start_point is not None and point is not None:
                self._update_end_candidate(point)
            else:
                if point is not None:
                    self._end_candidate = self._resolve_start_candidate(point)
                else:
                    self._end_candidate = None
                    self._snap_candidate = None
                    self._clear_alignment()
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
                self._start_point = self._resolve_start_candidate(point).copy()
                self._start_snapped = self._snap_candidate is not None
                self._start_snap_target_object = self._snap_target_object
                self._start_snap_target_endpoint = self._snap_target_endpoint
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
        """Return the closest visible saved Wall endpoint within 16 screen pixels."""
        self._snap_candidate = None
        self._snap_target_object = None
        self._snap_target_endpoint = None
        raw_2d = view3d_utils.location_3d_to_region_2d(
            self._region, self._region_data, raw_endpoint
        )
        if raw_2d is None:
            return raw_endpoint

        closest_distance = _SNAP_DISTANCE_PX
        for (
            wall_object,
            endpoint_name,
            endpoint,
            endpoint_2d,
        ) in self._visible_wall_endpoints():
            distance = (endpoint_2d - raw_2d).length
            if distance <= _SNAP_DISTANCE_PX and (
                self._snap_candidate is None or distance < closest_distance
            ):
                closest_distance = distance
                self._snap_candidate = endpoint.copy()
                self._snap_target_object = wall_object
                self._snap_target_endpoint = endpoint_name

        if self._snap_candidate is not None:
            return self._snap_candidate
        return raw_endpoint

    def _visible_wall_endpoints(self):
        """Yield saved endpoints which are visible in this viewport."""
        for wall_object in self._view_layer.objects:
            if wall_object is getattr(self, "_excluded_wall_object", None):
                continue
            wall = getattr(wall_object, "jhm_wall", None)
            if wall is None or not wall.is_wall:
                continue
            if not wall_object.visible_get(
                view_layer=self._view_layer, viewport=self._space_data
            ):
                continue

            for endpoint_name, saved_endpoint in (
                ("START", wall.start),
                ("END", wall.end),
            ):
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

                yield wall_object, endpoint_name, endpoint, endpoint_2d

    def _clear_alignment(self):
        self._x_align_reference = None
        self._y_align_reference = None
        self._extension_align_reference = None

    def _visible_extension_walls(self):
        """Yield visible identity-transform Walls with valid canonical axes."""
        for wall_object in self._view_layer.objects:
            if wall_object is getattr(self, "_excluded_wall_object", None):
                continue
            wall = getattr(wall_object, "jhm_wall", None)
            if wall is None or not wall.is_wall or not has_identity_transform(wall_object):
                continue
            if not wall_object.visible_get(
                view_layer=self._view_layer, viewport=self._space_data
            ):
                continue
            try:
                start, end = Vector(wall.start), Vector(wall.end)
            except (AttributeError, TypeError, ValueError):
                continue
            axis = end - start
            if (not all(math.isfinite(value) for value in (*start, *end))
                    or axis.length <= _MIN_WALL_LENGTH_M):
                continue
            yield wall_object, start, end

    def _screen_distance(self, first, second):
        first_2d = view3d_utils.location_3d_to_region_2d(
            self._region, self._region_data, first
        )
        second_2d = view3d_utils.location_3d_to_region_2d(
            self._region, self._region_data, second
        )
        if first_2d is None or second_2d is None:
            return None
        return (first_2d - second_2d).length

    def _resolve_start_candidate(self, raw_endpoint):
        snapped = self.snap_endpoint_candidate(raw_endpoint)
        self._clear_alignment()
        if self._snap_candidate is not None:
            return snapped
        return self._resolve_free_alignment(raw_endpoint)

    def _resolve_free_alignment(self, raw_endpoint):
        best_x = None
        best_y = None
        for _, _, endpoint, _ in self._visible_wall_endpoints():
            x_candidate = Vector((endpoint.x, raw_endpoint.y, 0.0))
            y_candidate = Vector((raw_endpoint.x, endpoint.y, 0.0))
            x_distance = self._screen_distance(raw_endpoint, x_candidate)
            y_distance = self._screen_distance(raw_endpoint, y_candidate)
            if x_distance is not None and x_distance <= _ALIGN_DISTANCE_PX:
                if best_x is None or x_distance < best_x[0]:
                    best_x = (x_distance, endpoint.copy())
            if y_distance is not None and y_distance <= _ALIGN_DISTANCE_PX:
                if best_y is None or y_distance < best_y[0]:
                    best_y = (y_distance, endpoint.copy())

        best_extension = None
        for _wall_object, start, end in self._visible_extension_walls():
            projection = project_to_wall_extension(raw_endpoint, start, end)
            if projection is None:
                continue
            projected = Vector(projection.point)
            distance = self._screen_distance(raw_endpoint, projected)
            if distance is None or distance > _ALIGN_DISTANCE_PX:
                continue
            stable_key = extension_geometry_key(projection)
            candidate = (distance, stable_key, projected,
                         Vector(projection.reference_endpoint))
            if best_extension is None or candidate[:2] < best_extension[:2]:
                best_extension = candidate

        axis_candidate = Vector(combined_axis_alignment(
            raw_endpoint,
            best_x[1] if best_x is not None else None,
            best_y[1] if best_y is not None else None,
        ))
        axis_distance = (
            self._screen_distance(raw_endpoint, axis_candidate)
            if best_x is not None or best_y is not None
            else None
        )
        if (best_extension is not None
                and (axis_distance is None or best_extension[0] <= axis_distance)):
            self._extension_align_reference = best_extension[3]
            return best_extension[2]

        if best_x is not None:
            self._x_align_reference = best_x[1]
        if best_y is not None:
            self._y_align_reference = best_y[1]
        return axis_candidate

    def resolve_endpoint_candidate(self, start_point, raw_endpoint):
        """Combine alignment with the optional 15-degree Shift constraint."""
        self._clear_alignment()
        if self._snap_candidate is not None:
            return raw_endpoint

        if not self._shift_held:
            return self._resolve_free_alignment(raw_endpoint)

        delta = raw_endpoint - start_point
        if delta.length <= _MIN_WALL_LENGTH_M:
            return raw_endpoint

        raw_angle = math.atan2(delta.y, delta.x)
        constrained_angle = round(raw_angle / _ANGLE_STEP_RAD) * _ANGLE_STEP_RAD
        axis = Vector(
            (math.cos(constrained_angle), math.sin(constrained_angle), 0.0)
        )
        projected_length = delta.dot(axis)
        constrained = start_point + axis * projected_length

        best = None
        for _, _, endpoint, _ in self._visible_wall_endpoints():
            for coordinate, component, reference_value in (
                ("x", axis.x, endpoint.x),
                ("y", axis.y, endpoint.y),
            ):
                start_value = getattr(start_point, coordinate)
                if abs(component) <= _AXIS_EPSILON:
                    if abs(start_value - reference_value) > _AXIS_EPSILON:
                        continue
                    intersection = constrained.copy()
                else:
                    parameter = (reference_value - start_value) / component
                    if parameter < 0.0:
                        continue
                    intersection = start_point + axis * parameter
                distance = self._screen_distance(raw_endpoint, intersection)
                if distance is None or distance > _ALIGN_DISTANCE_PX:
                    continue
                if best is None or distance < best[0]:
                    best = (distance, coordinate, endpoint.copy(), intersection)

        if best is None:
            return constrained
        if best[1] == "x":
            self._x_align_reference = best[2]
        else:
            self._y_align_reference = best[2]
        return best[3]

    def _resolve_final_endpoint(self, raw_endpoint):
        snapped_endpoint = self.snap_endpoint_candidate(raw_endpoint)
        return self.resolve_endpoint_candidate(
            self._start_point, snapped_endpoint
        )

    def _update_end_candidate(self, raw_endpoint):
        self._end_candidate = self._resolve_final_endpoint(raw_endpoint)

    def _update_candidate(self, raw_endpoint):
        if self._start_point is None:
            self._end_candidate = self._resolve_start_candidate(raw_endpoint)
        else:
            self._update_end_candidate(raw_endpoint)

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
        topology = None
        try:
            topology = snapshot_topology()
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

            if self._start_snap_target_object is not None:
                attach_to_junction(
                    wall_object,
                    "START",
                    self._start_snap_target_object,
                    self._start_snap_target_endpoint,
                )
            if self._snap_target_object is not None:
                attach_to_junction(
                    wall_object,
                    "END",
                    self._snap_target_object,
                    self._snap_target_endpoint,
                )

            for selected in context.selected_objects:
                selected.select_set(False)
            wall_object.select_set(True)
            context.view_layer.objects.active = wall_object
            # Keep the atomic batch as the transaction's final fallible mutation.
            regenerate_wall_meshes(affected_walls(wall_object))
        except Exception as error:
            if topology is not None:
                restore_topology(topology)
            if wall_object is not None:
                failed_mesh = wall_object.data
                bpy.data.objects.remove(wall_object, do_unlink=True)
                if failed_mesh.users == 0:
                    bpy.data.meshes.remove(failed_mesh)
            elif mesh is not None:
                bpy.data.meshes.remove(mesh)
            self.report({"ERROR"}, f"壁を生成できませんでした: {error}")
            return self._finish({"CANCELLED"})

        return self._finish({"FINISHED"})

    def _draw_preview(self):
        if self._start_point is None:
            if self._snap_candidate is not None:
                self._draw_snap_highlight(self._snap_candidate)
            elif self._end_candidate is not None:
                self._draw_alignment_guides(self._end_candidate)
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
            else:
                self._draw_alignment_guides(self._end_candidate, shader)
        except Exception:
            self._remove_draw_handler()
        finally:
            gpu.state.line_width_set(1.0)
            gpu.state.blend_set("NONE")

    def _draw_alignment_guides(self, candidate, shader=None):
        references = []
        if self._x_align_reference is not None:
            references.append(self._x_align_reference)
        if self._y_align_reference is not None:
            references.append(self._y_align_reference)
        if self._extension_align_reference is not None:
            references.append(self._extension_align_reference)
        if not references:
            return
        owns_gpu_state = shader is None
        try:
            if owns_gpu_state:
                shader = gpu.shader.from_builtin("UNIFORM_COLOR")
                gpu.state.blend_set("ALPHA")
            shader.bind()
            shader.uniform_float("color", (0.1, 0.4, 0.9, 0.65))
            gpu.state.line_width_set(_ALIGN_GUIDE_LINE_WIDTH_PX)
            candidate_2d = view3d_utils.location_3d_to_region_2d(
                self._region, self._region_data, candidate
            )
            if candidate_2d is None:
                return
            if owns_gpu_state:
                gpu.state.line_width_set(_PREVIEW_LINE_WIDTH_PX)
                self._draw_marker_ring(
                    shader, candidate_2d, _PREVIEW_MARKER_RADIUS_PX
                )
                gpu.state.line_width_set(_ALIGN_GUIDE_LINE_WIDTH_PX)
            drawn = set()
            for reference in references:
                reference_2d = view3d_utils.location_3d_to_region_2d(
                    self._region, self._region_data, reference
                )
                if reference_2d is None:
                    continue
                batch_for_shader(
                    shader, "LINES", {"pos": [tuple(reference_2d), tuple(candidate_2d)]}
                ).draw(shader)
                key = tuple(reference)
                if key not in drawn:
                    gpu.state.line_width_set(_SNAP_HIGHLIGHT_LINE_WIDTH_PX)
                    self._draw_marker_ring(
                        shader, reference_2d, _SNAP_HIGHLIGHT_RADIUS_PX
                    )
                    drawn.add(key)
                    gpu.state.line_width_set(_ALIGN_GUIDE_LINE_WIDTH_PX)
        except Exception:
            self._remove_draw_handler()
        finally:
            if owns_gpu_state:
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


class JHM_OT_move_wall_endpoint(bpy.types.Operator):
    """Move one saved endpoint of an existing managed wall."""

    bl_idname = "jhm.move_wall_endpoint"
    bl_label = "壁の端点を移動"
    bl_description = "選択中の壁の端点を次のクリック位置へ移動します"
    bl_options = {"REGISTER", "UNDO"}

    endpoint: bpy.props.EnumProperty(
        items=(
            ("START", "始点", "壁の始点を移動"),
            ("END", "終点", "壁の終点を移動"),
        ),
        default="END",
        options={"HIDDEN"},
    )

    @classmethod
    def poll(cls, context):
        active_object = context.active_object
        wall = getattr(active_object, "jhm_wall", None)
        return (
            context.area is not None
            and context.area.type == "VIEW_3D"
            and active_object is not None
            and wall is not None
            and wall.is_wall
        )

    def invoke(self, context, event):
        wall_object = context.active_object
        if context.mode != "OBJECT":
            self.report({"WARNING"}, "Object Modeで端点を編集してください。")
            return {"CANCELLED"}
        if not self._has_identity_transform(wall_object):
            self.report(
                {"WARNING"},
                "このWallにはObject Transformがあります。Build 03-Aの端点編集対象外です。",
            )
            return {"CANCELLED"}

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

        wall = wall_object.jhm_wall
        self._wall_object = wall_object
        self._excluded_wall_object = wall_object
        self._saved_start = Vector(wall.start)
        self._saved_end = Vector(wall.end)
        self._start_point = (
            self._saved_end.copy() if self.endpoint == "START" else self._saved_start.copy()
        )
        self._end_candidate = (
            self._saved_start.copy() if self.endpoint == "START" else self._saved_end.copy()
        )
        self._wall_thickness_mm = wall.wall_thickness
        self._wall_height_mm = wall.wall_height
        self._last_raw_endpoint = None
        self._snap_candidate = None
        self._snap_target_object = None
        self._snap_target_endpoint = None
        self._x_align_reference = None
        self._y_align_reference = None
        self._extension_align_reference = None
        self._start_snapped = False
        self._shift_held = bool(event.shift)
        self._draw_handle = bpy.types.SpaceView3D.draw_handler_add(
            self._draw_preview, (), "WINDOW", "POST_PIXEL"
        )
        context.window_manager.modal_handler_add(self)
        self._tag_redraw()
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        if not self._wall_is_available():
            self.report({"WARNING"}, "編集中のWallが見つかりません。")
            return self._finish({"CANCELLED"})

        if event.type in {"ESC", "RIGHTMOUSE"}:
            return self._finish({"CANCELLED"})

        self._shift_held = bool(event.shift)
        if event.type in {"LEFT_SHIFT", "RIGHT_SHIFT"}:
            if self._last_raw_endpoint is not None:
                self._update_end_candidate(self._last_raw_endpoint)
                self._tag_redraw()
            return {"RUNNING_MODAL"}

        if event.type == "MOUSEMOVE":
            point, _ = self._xy_plane_point(event)
            if point is not None:
                self._last_raw_endpoint = point
                self._update_end_candidate(point)
                self._tag_redraw()
            return {"RUNNING_MODAL"}

        if event.type == "LEFTMOUSE" and event.value == "PRESS":
            point, error = self._xy_plane_point(event)
            if point is None:
                self.report({"WARNING"}, error or "XY平面上の座標を取得できません。")
                return {"RUNNING_MODAL"}

            self._last_raw_endpoint = point
            candidate = self._resolve_final_endpoint(point)
            self._end_candidate = candidate
            if not self._is_valid_wall_length(self._start_point, candidate):
                self.report({"WARNING"}, "壁の長さが短すぎます。")
                self._tag_redraw()
                return {"RUNNING_MODAL"}
            return self._commit_endpoint(context, candidate)

        return {"RUNNING_MODAL"}

    def _commit_endpoint(self, context, candidate):
        start_point = candidate if self.endpoint == "START" else self._saved_start
        end_point = self._saved_end if self.endpoint == "START" else candidate
        if not self._is_valid_wall_length(start_point, end_point):
            self.report({"WARNING"}, "壁の寸法が不正です。")
            return {"RUNNING_MODAL"}

        wall_object = self._wall_object
        wall = wall_object.jhm_wall
        topology = None
        try:
            topology = snapshot_topology()
            old_members = affected_walls(wall_object, (self.endpoint,))
            if self.endpoint == "START":
                wall.start = tuple(candidate)
                wall.end = tuple(self._saved_end)
            else:
                wall.start = tuple(self._saved_start)
                wall.end = tuple(candidate)
            detach_endpoint(wall_object, self.endpoint)
            if self._snap_target_object is not None:
                attach_to_junction(
                    wall_object,
                    self.endpoint,
                    self._snap_target_object,
                    self._snap_target_endpoint,
                )
            # The moved core direction also changes a miter at the opposite end.
            new_members = affected_walls(wall_object)
            wall_object.select_set(True)
            context.view_layer.objects.active = wall_object
            regenerate_wall_meshes(
                merge_affected(old_members, new_members, [wall_object])
            )
        except Exception as error:
            wall.start = tuple(self._saved_start)
            wall.end = tuple(self._saved_end)
            if topology is not None:
                restore_topology(topology)
            self.report({"ERROR"}, f"壁を更新できませんでした: {error}")
            return self._finish({"CANCELLED"})

        return self._finish({"FINISHED"})

    def _wall_is_available(self):
        try:
            return bpy.data.objects.get(self._wall_object.name) is self._wall_object
        except ReferenceError:
            return False

    @staticmethod
    def _has_identity_transform(wall_object):
        matrix = wall_object.matrix_basis
        for row in range(4):
            for column in range(4):
                expected = 1.0 if row == column else 0.0
                if abs(matrix[row][column] - expected) > _TRANSFORM_EPSILON:
                    return False
        return True

    # Reuse Build 02-D's candidate resolution, geometry, and GPU drawing unchanged.
    _xy_plane_point = JHM_OT_create_wall._xy_plane_point
    snap_endpoint_candidate = JHM_OT_create_wall.snap_endpoint_candidate
    _visible_wall_endpoints = JHM_OT_create_wall._visible_wall_endpoints
    _visible_extension_walls = JHM_OT_create_wall._visible_extension_walls
    _clear_alignment = JHM_OT_create_wall._clear_alignment
    _screen_distance = JHM_OT_create_wall._screen_distance
    _resolve_free_alignment = JHM_OT_create_wall._resolve_free_alignment
    resolve_endpoint_candidate = JHM_OT_create_wall.resolve_endpoint_candidate
    _resolve_final_endpoint = JHM_OT_create_wall._resolve_final_endpoint
    _update_end_candidate = JHM_OT_create_wall._update_end_candidate
    _is_valid_wall_length = JHM_OT_create_wall._is_valid_wall_length
    _wall_geometry = JHM_OT_create_wall._wall_geometry
    _draw_preview = JHM_OT_create_wall._draw_preview
    _draw_alignment_guides = JHM_OT_create_wall._draw_alignment_guides
    _draw_snap_highlight = JHM_OT_create_wall._draw_snap_highlight
    _draw_marker_ring = JHM_OT_create_wall._draw_marker_ring
    _tag_redraw = JHM_OT_create_wall._tag_redraw
    _finish = JHM_OT_create_wall._finish
    _remove_draw_handler = JHM_OT_create_wall._remove_draw_handler


class JHM_OT_edit_wall_dimensions(bpy.types.Operator):
    """Regenerate a managed wall after editing its saved dimensions."""

    bl_idname = "jhm.edit_wall_dimensions"
    bl_label = "壁寸法を変更"
    bl_description = "選択中の壁の壁厚と壁高さを変更します"
    bl_options = {"REGISTER", "UNDO"}

    wall_thickness: bpy.props.FloatProperty(
        name="壁厚 (mm)",
        min=0.1,
        max=10000.0,
        precision=1,
    )
    wall_height: bpy.props.FloatProperty(
        name="壁高さ (mm)",
        min=0.1,
        max=100000.0,
        precision=1,
    )
    target: bpy.props.PointerProperty(
        type=bpy.types.Object,
        options={"HIDDEN"},
    )

    @classmethod
    def poll(cls, context):
        active_object = context.active_object
        wall = getattr(active_object, "jhm_wall", None)
        return (
            context.area is not None
            and context.area.type == "VIEW_3D"
            and context.mode == "OBJECT"
            and active_object is not None
            and wall is not None
            and wall.is_wall
        )

    def invoke(self, context, event):
        wall_object = context.active_object
        if not JHM_OT_move_wall_endpoint._has_identity_transform(wall_object):
            self.report(
                {"WARNING"},
                "このWallにはObject Transformがあります。壁寸法編集の対象外です。",
            )
            return {"CANCELLED"}

        wall = wall_object.jhm_wall
        self.target = wall_object
        self.wall_thickness = wall.wall_thickness
        self.wall_height = wall.wall_height
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "wall_thickness")
        layout.prop(self, "wall_height")

    def execute(self, context):
        wall_object = self.target
        try:
            wall = wall_object.jhm_wall if wall_object is not None else None
            is_available = (
                wall_object is not None
                and bpy.data.objects.get(wall_object.name) is wall_object
                and wall is not None
                and wall.is_wall
            )
        except ReferenceError:
            is_available = False
        if not is_available:
            self.report({"ERROR"}, "編集対象のWallが見つかりません。")
            return {"CANCELLED"}
        if context.mode != "OBJECT":
            self.report({"WARNING"}, "Object Modeで壁寸法を編集してください。")
            return {"CANCELLED"}
        if not JHM_OT_move_wall_endpoint._has_identity_transform(wall_object):
            self.report(
                {"WARNING"},
                "このWallにはObject Transformがあります。壁寸法編集の対象外です。",
            )
            return {"CANCELLED"}

        old_thickness = wall.wall_thickness
        old_height = wall.wall_height
        if (
            self.wall_thickness == old_thickness
            and self.wall_height == old_height
        ):
            return {"FINISHED"}

        try:
            wall.wall_thickness = self.wall_thickness
            wall.wall_height = self.wall_height
            wall_object.select_set(True)
            context.view_layer.objects.active = wall_object
            regenerate_wall_meshes(affected_walls(wall_object))
        except Exception as error:
            wall.wall_thickness = old_thickness
            wall.wall_height = old_height
            self.report({"ERROR"}, f"壁寸法を更新できませんでした: {error}")
            return {"CANCELLED"}

        return {"FINISHED"}


class JHM_OT_rebuild_wall_joints(bpy.types.Operator):
    """Repair selected Wall joints from canonical data and topology."""

    bl_idname = "jhm.rebuild_wall_joints"
    bl_label = "接合を再生成"
    bl_description = "選択中の壁と接続壁の接合Meshを再生成します"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        active_object = context.active_object
        wall = getattr(active_object, "jhm_wall", None)
        return (
            context.mode == "OBJECT"
            and active_object is not None
            and wall is not None
            and wall.is_wall
        )

    def execute(self, context):
        wall_object = context.active_object
        if not JHM_OT_move_wall_endpoint._has_identity_transform(wall_object):
            self.report(
                {"WARNING"},
                "このWallにはObject Transformがあります。接合を再生成できません。",
            )
            return {"CANCELLED"}
        try:
            regenerate_wall_meshes(affected_walls(wall_object))
        except Exception as error:
            self.report({"ERROR"}, f"接合を再生成できませんでした: {error}")
            return {"CANCELLED"}
        return {"FINISHED"}
