"""3D View sidebar panels for the Japanese House Modeler add-on."""

import bpy

from .connections import topology_is_consistent, valid_connection_count
from .drawing_alignment import wall_axis_angle_degrees, wall_length_m
from .junctions import classification_label, classify_junction
from .joints import joint_status_label
from .joints import has_identity_transform
from .finish_identity import duplicate_ids
from .finish_geometry import diagnose_finish
from .finish_state import status_label


class JHM_PT_house_modeler(bpy.types.Panel):
    """UI for new-wall defaults and selected-wall data."""

    bl_label = "日本住宅モデラー"
    bl_idname = "JHM_PT_house_modeler"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "日本住宅"

    def draw(self, context):
        layout = self.layout
        defaults = context.scene.jhm_new_wall_defaults

        new_wall_box = layout.box()
        new_wall_box.label(text="新規壁")
        new_wall_box.prop(defaults, "wall_thickness", text="壁厚 (mm)")
        new_wall_box.prop(defaults, "wall_height", text="壁高さ (mm)")
        new_wall_box.separator()
        new_wall_box.operator(
            "jhm.create_wall", text="壁を生成", icon="ADD"
        )
        new_wall_box.separator()
        new_wall_box.prop(defaults, "floor_reference_z_mm", text="床基準高さ (mm)")
        new_wall_box.prop(defaults, "ceiling_reference_z_mm", text="天井基準高さ (mm)")

        layout.separator()
        selected_box = layout.box()
        active_object = context.active_object
        if active_object and active_object.jhm_wall.is_wall:
            selected_box.label(text="選択中の壁")
            wall = active_object.jhm_wall
            selected_box.label(text=f"壁厚: {wall.wall_thickness:.1f} mm")
            selected_box.label(text=f"壁高さ: {wall.wall_height:.1f} mm")
            length = wall_length_m(wall.start, wall.end)
            selected_box.label(
                text=(f"壁長さ: {length * 1000.0:.1f} mm" if length is not None
                      else "壁長さ: 判定不能")
            )
            angle = wall_axis_angle_degrees(wall.start, wall.end)
            selected_box.label(
                text=(f"壁角度: {angle:.1f}°" if angle is not None
                      else "壁角度: 判定不能")
            )
            state_problems = []
            if not has_identity_transform(active_object):
                state_problems.append("Object Transformあり")
            if not topology_is_consistent(active_object):
                state_problems.append("接続情報不整合")
            duplicates = duplicate_ids(
                [obj for obj in context.scene.objects
                 if getattr(getattr(obj, "jhm_wall", None), "is_wall", False)],
                lambda obj: obj.jhm_wall.wall_id,
            )
            if wall.wall_id and wall.wall_id in duplicates:
                state_problems.append("Wall ID重複")
            selected_box.label(
                text=("管理状態: 正常" if not state_problems else
                      f"管理状態: 要復元（{' / '.join(state_problems)}）")
            )
            selected_box.separator()
            selected_box.label(
                text=f"始点接続: {valid_connection_count(active_object, 'START')}"
            )
            selected_box.label(
                text="始点形状: "
                + classification_label(classify_junction(active_object, "START"))
            )
            selected_box.label(
                text="始点接合: " + joint_status_label(active_object, "START")
            )
            selected_box.separator()
            selected_box.label(
                text=f"終点接続: {valid_connection_count(active_object, 'END')}"
            )
            selected_box.label(
                text="終点形状: "
                + classification_label(classify_junction(active_object, "END"))
            )
            selected_box.label(
                text="終点接合: " + joint_status_label(active_object, "END")
            )
            selected_box.separator()
            selected_box.operator(
                "jhm.edit_wall_dimensions", text="壁寸法を変更"
            )
            selected_box.operator(
                "jhm.rebuild_wall_joints", text="接合を再生成"
            )
            selected_box.operator("jhm.repair_wall", text="管理状態へ復元")
            selected_box.separator()
            move_start = selected_box.operator(
                "jhm.move_wall_endpoint", text="始点を移動"
            )
            move_start.endpoint = "START"
            move_end = selected_box.operator(
                "jhm.move_wall_endpoint", text="終点を移動"
            )
            move_end.endpoint = "END"
            selected_box.separator()
            selected_box.operator("jhm.delete_wall", text="壁を削除")
            finish_box = layout.box()
            finish_box.label(text="仕上げ経路")
            left = finish_box.operator("jhm.start_finish_path", text="左側面から開始")
            left.side = "LEFT"
            right = finish_box.operator("jhm.start_finish_path", text="右側面から開始")
            right.side = "RIGHT"
        elif (active_object and
              getattr(getattr(active_object, "jhm_finish", None), "is_finish", False)):
            finish = active_object.jhm_finish
            selected_box.label(text="選択中の仕上げ")
            selected_box.label(text=f"種類: {finish.finish_type}")
            selected_box.label(text=f"区間数: {len(finish.spans)}")
            selected_box.label(text="管理状態: " + status_label(diagnose_finish(active_object)))
            selected_box.operator("jhm.regenerate_finish", text="経路を再生成")
            selected_box.operator("jhm.repair_finish", text="管理状態へ復元")
            selected_box.operator("jhm.convert_finish_mesh", text="編集可能Meshとして確定")
            selected_box.operator("jhm.delete_finish", text="仕上げ経路を削除")
        else:
            selected_box.label(text="選択中の壁")
            selected_box.label(text="Wallを選択してください。")
