"""3D View sidebar panels for the Japanese House Modeler add-on."""

import bpy

from .connections import topology_is_consistent, valid_connection_count
from .drawing_alignment import wall_axis_angle_degrees, wall_length_m
from .junctions import classification_label, classify_junction
from .joints import joint_status_label
from .joints import has_identity_transform
from .finish_identity import duplicate_ids
from .finish_geometry import canonical_visible_range_state, diagnose_finish
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
        new_wall_box.operator("jhm.regenerate_all_finishes", text="仕上げを一括再生成")
        if context.scene.jhm_finish_regeneration_required:
            new_wall_box.label(text="仕上げ形状は参照高さに対して未更新です", icon="ERROR")

        profile_box = layout.box()
        profile_box.label(text="Project Custom Profile Library")
        profile_box.label(text="2D / 閉じた1 spline / POLY・BEZIER")
        profile_box.label(text="+X = 出幅方向 / +Y = 上方向")
        profile_box.label(text="Object Transform = identity")
        library = context.scene.jhm_custom_profiles
        if library:
            profile_box.prop(context.scene, "jhm_custom_profile_index", text="選択番号")
            for index, item in enumerate(library):
                marker = ">" if index == context.scene.jhm_custom_profile_index else " "
                profile_box.label(text=(f"{marker} {index}: {item.display_name} "
                                        f"({item.source_type}, r{item.profile_revision})"))
        else:
            profile_box.label(text="登録Profileなし")
        profile_box.operator("jhm.register_custom_profile")
        profile_box.operator("jhm.delete_custom_profile")

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
            for finish_type, label in (("BASEBOARD", "巾木"), ("CROWN", "廻り縁")):
                left = finish_box.operator(
                    "jhm.start_finish_path", text=f"{label} 左側面から開始")
                left.side, left.finish_type = "LEFT", finish_type
                right = finish_box.operator(
                    "jhm.start_finish_path", text=f"{label} 右側面から開始")
                right.side, right.finish_type = "RIGHT", finish_type
        elif (active_object and
              getattr(getattr(active_object, "jhm_finish", None), "is_finish", False)):
            finish = active_object.jhm_finish
            selected_box.label(text="選択中の仕上げ")
            selected_box.label(text=f"種類: {finish.finish_type}")
            selected_box.label(text=f"基準: {finish.vertical_reference}")
            if finish.vertical_reference == "FLOOR":
                selected_box.label(
                    text=f"基準高さ: {defaults.floor_reference_z_mm:.1f} mm")
            elif finish.vertical_reference == "CEILING":
                selected_box.label(
                    text=f"基準高さ: {defaults.ceiling_reference_z_mm:.1f} mm")
            elif finish.vertical_reference == "ABSOLUTE":
                selected_box.label(
                    text=f"絶対高さ: {finish.absolute_z_mm:.1f} mm")
            selected_box.label(
                text=f"オフセット: {finish.vertical_offset_mm:.1f} mm")
            try:
                from .finish_profiles import resolve_finish_profile
                profile = resolve_finish_profile(finish, context.scene.jhm_custom_profiles)
                selected_box.label(text=f"Profile: {profile.display_name or profile.profile_id}")
                selected_box.label(text=f"高さ: {profile.height_mm:.1f} mm")
                selected_box.label(text=f"出幅: {profile.projection_mm:.1f} mm")
                if profile.profile_id == "BEVEL":
                    selected_box.label(text=f"面取り: {profile.bevel_mm:.1f} mm")
                elif profile.profile_id == "ROUNDED":
                    selected_box.label(text=f"半径: {profile.radius_mm:.1f} mm")
                elif profile.profile_id not in ("SIMPLE", "BEVEL", "ROUNDED"):
                    selected_box.label(text=f"revision: {profile.profile_revision}")
                    selected_box.label(text=f"均一スケール: {profile.uniform_scale:g}")
            except ValueError:
                selected_box.label(text="Profile: 解決不能")
            selected_box.label(text=f"区間数: {len(finish.spans)}")
            problems = diagnose_finish(active_object, context.scene)
            selected_box.label(text="管理状態: " + status_label(problems))
            if not problems:
                try:
                    visible_state, visible_count = canonical_visible_range_state(
                        finish, context.scene)
                    selected_box.label(text=f"表示区間: {visible_count}")
                    if visible_state == "VALID_EMPTY":
                        selected_box.label(text="状態: 全区間除外")
                except (AttributeError, ReferenceError, TypeError, ValueError):
                    selected_box.label(text="表示区間: 解決不能")
            selected_box.operator(
                "jhm.edit_finish_profile",
                text="Profileを変更")
            selected_box.operator("jhm.edit_finish_boundaries", text="開始/終了位置を変更")
            exclusions = selected_box.box()
            exclusions.label(text=f"Manual Exclusion ({len(finish.exclusions)})")
            if finish.exclusions:
                exclusions.prop(finish, "active_exclusion_index", text="編集対象番号")
                for index, item in enumerate(finish.exclusions):
                    row = exclusions.row()
                    marker = ">" if index == finish.active_exclusion_index else " "
                    identity = item.exclusion_id[:8] or "legacy"
                    row.label(text=f"{marker} {index}: {identity}")
                    row.label(text="有効" if item.enabled else "無効")
                exclusions.operator("jhm.edit_finish_exclusion", text="選択項目を編集")
                exclusions.operator("jhm.toggle_finish_exclusion", text="有効/無効を切替")
                exclusions.operator("jhm.remove_finish_exclusion", text="選択項目を削除")
            exclusions.operator("jhm.add_finish_exclusion", text="Manual Exclusionを追加")
            selected_box.operator("jhm.regenerate_finish", text="経路を再生成")
            selected_box.operator("jhm.repair_finish", text="管理状態へ復元")
            selected_box.operator("jhm.convert_finish_mesh", text="編集可能Meshとして確定")
            selected_box.operator("jhm.delete_finish", text="仕上げ経路を削除")
        else:
            selected_box.label(text="選択中の壁")
            selected_box.label(text="Wallを選択してください。")
