"""3D View sidebar panels for the Japanese House Modeler add-on."""

import bpy


class JHM_PT_house_modeler(bpy.types.Panel):
    """Build 01 UI for new-wall defaults and selected-wall data."""

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
            "jhm.wall_creation_not_implemented", text="＋ 壁", icon="ADD"
        )

        layout.separator()
        selected_box = layout.box()
        selected_box.label(text="選択中の壁")
        active_object = context.active_object
        if active_object and active_object.jhm_wall.is_wall:
            selected_box.prop(active_object.jhm_wall, "wall_thickness", text="壁厚 (mm)")
            selected_box.prop(active_object.jhm_wall, "wall_height", text="壁高さ (mm)")
        else:
            selected_box.label(text="Wall SystemはBuild 02で実装予定です。")
