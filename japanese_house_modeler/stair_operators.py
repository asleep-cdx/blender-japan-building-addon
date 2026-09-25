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
from .stair_residential import (
    BASIC_TREAD_RISER, STANDARD_RESIDENTIAL, ResidentialFields,
    assemble_material_slot_plan, new_residential_fields, residential_fields, semantic_assembly_mode,
    semantic_schema_version, schema_version_after_residential_edit,
)
from .stair_residential_geometry import prepare_residential_geometry


_PLANE_EPSILON = 1.0e-10
_STAIR_DEFAULT_NAMES = (
    "ascent_direction", "base_z_mm", "floor_to_floor_mm", "riser_count",
    "stair_width_mm", "tread_thickness_mm", "riser_thickness_mm",
)
_CANONICAL_NAMES = _STAIR_DEFAULT_NAMES


def _material_name(material):
    """Convert a canonical Material pointer to dialog-safe text."""
    return material.name if material is not None else ""


def _material_from_operator_name(name):
    """Resolve one dialog name without silently losing a stale selection."""
    if not name:
        return None
    material = bpy.data.materials.get(name)
    if material is None:
        raise ValueError(f"Material '{name}' が見つかりません。")
    return material


def _canonical_snapshot(stair):
    values = {
        "path_points": tuple(tuple(point.xy) for point in stair.path_points),
        **{name: getattr(stair, name) for name in _CANONICAL_NAMES},
    }
    values.update(assembly_mode=semantic_assembly_mode(stair),
                  stair_schema_version=semantic_schema_version(stair),
                  residential=residential_fields(stair))
    return values


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
        semantic_assembly_mode(stair), semantic_schema_version(stair),
        residential_fields(stair),
    )
    duplicates = duplicate_stair_ids(_managed_records(scene))
    return diagnose_stair(state, duplicates)


def _selected_stair(context):
    obj = context.active_object
    if (obj is None or not obj.select_get()
            or not getattr(getattr(obj, "jhm_stair", None), "is_stair", False)):
        return None
    return obj


def finalize_stair_management(stair):
    """End JHM management without changing canonical or generated Mesh data."""
    stair.is_stair = False


def _set_canonical(stair, values):
    stair.path_points.clear()
    for x, y in values["path_points"]:
        stair.path_points.add().xy = (x, y)
    for name in _CANONICAL_NAMES:
        setattr(stair, name, values[name])
    if "assembly_mode" in values:
        stair.assembly_mode = values["assembly_mode"]
        stair.stair_schema_version = values["stair_schema_version"]
        for name, value in vars(values["residential"]).items():
            setattr(stair, name, value)


def _prepare_candidate(values):
    if values.get("assembly_mode") == STANDARD_RESIDENTIAL:
        return prepare_residential_geometry(
            values["path_points"], values["ascent_direction"],
            values["base_z_mm"], values["floor_to_floor_mm"],
            values["riser_count"], values["stair_width_mm"],
            values["tread_thickness_mm"], values["riser_thickness_mm"],
            assembly_mode=values["assembly_mode"],
            stair_schema_version=values["stair_schema_version"],
            fields=values["residential"])[2]
    return prepare_stair_geometry(
        values["path_points"], values["ascent_direction"], values["base_z_mm"],
        values["floor_to_floor_mm"], values["riser_count"],
        values["stair_width_mm"], values["tread_thickness_mm"],
        values["riser_thickness_mm"])[2]


def regenerate_stage2_residential_for_runtime(stair_object):
    """Compatibility runtime hook, now dispatching complete Residential."""
    stair = stair_object.jhm_stair
    if semantic_assembly_mode(stair) != STANDARD_RESIDENTIAL:
        raise ValueError("controlled objectをSTANDARD_RESIDENTIALに設定してください。")
    _transactional_update(stair_object, _canonical_snapshot(stair))


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
        if candidate.get("assembly_mode") == STANDARD_RESIDENTIAL:
            plan = assemble_material_slot_plan(candidate["residential"])
            for material in plan.slots:
                replacement.materials.append(material)
            role_indices = dict(plan.role_indices)
            for polygon, role in zip(replacement.polygons, mesh_data.face_roles):
                polygon.material_index = role_indices[role]
        else:
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
        mode = semantic_assembly_mode(obj.jhm_stair) if obj else None
        if obj is None or not operation_allowed(self.operation, issues, mode):
            self.report({"WARNING"}, "現在の管理状態ではこの操作を実行できません。")
            return None
        return obj

    def _require_mode(self, context, mode):
        obj = self._require_allowed(context)
        if obj is None or semantic_assembly_mode(obj.jhm_stair) != mode:
            self.report({"WARNING"}, "現在の階段構成ではこの操作を実行できません。")
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
                    fields = new_residential_fields()
                    _layout, _fragments, mesh_data = prepare_residential_geometry(
                        path,
                        self._stair_defaults["ascent_direction"],
                        self._stair_defaults["base_z_mm"],
                        self._stair_defaults["floor_to_floor_mm"],
                        self._stair_defaults["riser_count"],
                        self._stair_defaults["stair_width_mm"],
                        self._stair_defaults["tread_thickness_mm"],
                        self._stair_defaults["riser_thickness_mm"],
                        fields=fields,
                    )
                except ValueError as exc:
                    self.report({"WARNING"}, str(exc))
                    return {"RUNNING_MODAL"}
                return self._commit(context, path, mesh_data, fields)
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

    def _commit(self, context, path, mesh_data, residential):
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
            stair.assembly_mode = STANDARD_RESIDENTIAL
            stair.stair_schema_version = 3
            for name, value in vars(residential).items():
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


class JHM_OT_apply_residential_stair(_StairOperationMixin, bpy.types.Operator):
    bl_idname = "jhm.apply_residential_stair"
    bl_label = "住宅階段仕様を適用"
    bl_options = {"REGISTER", "UNDO"}
    operation = "APPLY_RESIDENTIAL"

    base_material_name: bpy.props.StringProperty()

    def draw(self, _context):
        self.layout.prop_search(
            self, "base_material_name", bpy.data, "materials",
            text="Base Material")

    def invoke(self, context, _event):
        obj = self._require_mode(context, BASIC_TREAD_RISER)
        if obj is None:
            return {"CANCELLED"}
        materials = tuple(m for m in obj.data.materials if m is not None)
        self.base_material_name = (
            _material_name(materials[0]) if len(materials) == 1 else "")
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        obj = self._require_mode(context, BASIC_TREAD_RISER)
        if obj is None:
            return {"CANCELLED"}
        try:
            base_material = _material_from_operator_name(self.base_material_name)
        except ValueError as exc:
            self.report({"WARNING"}, str(exc))
            return {"CANCELLED"}
        candidate = _canonical_snapshot(obj.jhm_stair)
        candidate["assembly_mode"] = STANDARD_RESIDENTIAL
        candidate["stair_schema_version"] = max(3, candidate["stair_schema_version"])
        candidate["residential"] = ResidentialFields(base_material=base_material)
        return self._run_candidate(context, candidate)


class JHM_OT_edit_residential_stair(_StairOperationMixin, bpy.types.Operator):
    bl_idname = "jhm.edit_residential_stair"
    bl_label = "住宅階段仕様を変更"
    bl_options = {"REGISTER", "UNDO"}
    operation = "EDIT_RESIDENTIAL"
    underside_mode: bpy.props.EnumProperty(
        name="下面形式", items=(("STEPPED_CLOSED", "段々閉じ", ""),
                              ("SLOPED_CLOSED", "勾配閉じ", "")))
    underside_thickness_mm: bpy.props.FloatProperty(name="下面シェル厚 (mm)")
    left_side_board_enabled: bpy.props.BoolProperty(name="左Side Board")
    right_side_board_enabled: bpy.props.BoolProperty(name="右Side Board")
    side_board_thickness_mm: bpy.props.FloatProperty(name="Side Board厚 (mm)")
    side_board_reveal_mm: bpy.props.FloatProperty(name="側板突出量 (mm)")
    side_board_band_width_mm: bpy.props.FloatProperty(name="階段本体厚み (mm)")
    side_board_mode: bpy.props.EnumProperty(
        name="Side Board形状", items=(("STEPPED", "段々", ""),
                                   ("SLOPED", "勾配", "")))
    tread_front_overhang_mm: bpy.props.FloatProperty(name="段鼻突出量 (mm)")
    tread_front_edge_mode: bpy.props.EnumProperty(
        name="踏板前縁", items=(("SQUARE", "角", ""),
                              ("BEVEL", "面取り", ""),
                              ("ROUND", "丸", "")))
    tread_front_edge_size_mm: bpy.props.FloatProperty(name="前縁サイズ (mm)")

    def draw(self, _context):
        for name in ("underside_mode", "side_board_mode",
                     "side_board_band_width_mm", "underside_thickness_mm",
                     "left_side_board_enabled", "right_side_board_enabled",
                     "side_board_thickness_mm", "side_board_reveal_mm",
                     "tread_front_overhang_mm", "tread_front_edge_mode",
                     "tread_front_edge_size_mm"):
            self.layout.prop(self, name)

    def invoke(self, context, _event):
        obj = self._require_mode(context, STANDARD_RESIDENTIAL)
        if obj is None: return {"CANCELLED"}
        values = residential_fields(obj.jhm_stair)
        for name in ("underside_mode", "side_board_mode",
                     "underside_thickness_mm", "left_side_board_enabled",
                     "right_side_board_enabled", "side_board_thickness_mm",
                     "side_board_reveal_mm", "side_board_band_width_mm",
                     "tread_front_overhang_mm", "tread_front_edge_mode",
                     "tread_front_edge_size_mm"):
            setattr(self, name, getattr(values, name))
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        obj = self._require_mode(context, STANDARD_RESIDENTIAL)
        if obj is None: return {"CANCELLED"}
        candidate = _canonical_snapshot(obj.jhm_stair)
        values = vars(candidate["residential"]).copy()
        for name in ("underside_mode", "side_board_mode",
                     "underside_thickness_mm", "left_side_board_enabled",
                     "right_side_board_enabled", "side_board_thickness_mm",
                     "side_board_reveal_mm", "side_board_band_width_mm",
                     "tread_front_overhang_mm", "tread_front_edge_mode",
                     "tread_front_edge_size_mm"):
            values[name] = getattr(self, name)
        before = candidate["residential"]
        after = ResidentialFields(**values)
        candidate["residential"] = after
        candidate["stair_schema_version"] = schema_version_after_residential_edit(
            candidate["stair_schema_version"], before, after)
        return self._run_candidate(context, candidate)


class JHM_OT_edit_stair_materials(_StairOperationMixin, bpy.types.Operator):
    bl_idname = "jhm.edit_stair_materials"
    bl_label = "階段部材Materialを変更"
    bl_options = {"REGISTER", "UNDO"}
    operation = "EDIT_MATERIALS"
    base_material_name: bpy.props.StringProperty()
    tread_material_name: bpy.props.StringProperty()
    riser_material_name: bpy.props.StringProperty()
    underside_material_name: bpy.props.StringProperty()
    side_board_material_name: bpy.props.StringProperty()

    def draw(self, _context):
        layout = self.layout
        layout.prop_search(self, "base_material_name", bpy.data, "materials",
                           text="Base Material")
        layout.prop_search(self, "tread_material_name", bpy.data, "materials",
                           text="Tread override")
        layout.prop_search(self, "riser_material_name", bpy.data, "materials",
                           text="Riser override")
        layout.prop_search(self, "underside_material_name", bpy.data, "materials",
                           text="Underside override")
        layout.prop_search(self, "side_board_material_name", bpy.data, "materials",
                           text="Side Board override")

    def invoke(self, context, _event):
        obj = self._require_mode(context, STANDARD_RESIDENTIAL)
        if obj is None: return {"CANCELLED"}
        values = residential_fields(obj.jhm_stair)
        for role in ("base", "tread", "riser", "underside", "side_board"):
            setattr(self, f"{role}_material_name",
                    _material_name(getattr(values, f"{role}_material")))
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        obj = self._require_mode(context, STANDARD_RESIDENTIAL)
        if obj is None: return {"CANCELLED"}
        try:
            materials = {
                f"{role}_material": _material_from_operator_name(
                    getattr(self, f"{role}_material_name"))
                for role in ("base", "tread", "riser", "underside", "side_board")
            }
        except ValueError as exc:
            self.report({"WARNING"}, str(exc))
            return {"CANCELLED"}
        candidate = _canonical_snapshot(obj.jhm_stair)
        values = vars(candidate["residential"]).copy()
        values.update(materials)
        candidate["residential"] = ResidentialFields(**values)
        return self._run_candidate(context, candidate)


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


class JHM_OT_convert_stair_mesh(_StairOperationMixin, bpy.types.Operator):
    """Finalize the existing managed Mesh in place for unrestricted editing."""

    bl_idname = "jhm.convert_stair_mesh"
    bl_label = "編集可能Meshとして確定"
    bl_options = {"REGISTER", "UNDO"}
    operation = "FINALIZE"

    def execute(self, context):
        obj = self._require_allowed(context)
        if obj is None:
            return {"CANCELLED"}
        # The Stair already is a Mesh.  Only its management marker changes;
        # Object identity, data, geometry, materials, transform, and canonical
        # values (including stair_id and Path) deliberately remain untouched.
        finalize_stair_management(obj.jhm_stair)
        return {"FINISHED"}


class JHM_OT_delete_stair(_StairOperationMixin, bpy.types.Operator):
    """Delete only the active selected managed Stair Object."""

    bl_idname = "jhm.delete_stair"
    bl_label = "階段を削除"
    bl_options = {"REGISTER", "UNDO"}
    operation = "DELETE"

    def execute(self, context):
        obj = self._require_allowed(context)
        if obj is None:
            return {"CANCELLED"}
        # Do not invoke selection-wide bpy.ops.object.delete and do not remove
        # Object.data or Materials.  Blender's orphan management keeps this
        # direct Object removal safe for shared data and for Undo/Redo.
        bpy.data.objects.remove(obj, do_unlink=True)
        return {"FINISHED"}
