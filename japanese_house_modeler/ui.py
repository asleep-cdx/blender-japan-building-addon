"""3D View sidebar panels for the Japanese House Modeler add-on."""

import bpy


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
            "jhm.create_wall", text="＋ 壁", icon="ADD"
        )

        layout.separator()
        selected_box = layout.box()
        selected_box.label(text="選択中の壁")
        active_object = context.active_object
        if active_object and active_object.jhm_wall.is_wall:
            wall = active_object.jhm_wall
            selected_box.label(text=f"壁厚: {wall.wall_thickness:.1f} mm")
            selected_box.label(text=f"壁高さ: {wall.wall_height:.1f} mm")
            selected_box.separator()
            selected_box.operator(
                "jhm.edit_wall_dimensions", text="壁寸法を変更"
            )
            selected_box.separator()
            move_start = selected_box.operator(
                "jhm.move_wall_endpoint", text="始点を移動"
            )
            move_start.endpoint = "START"
            move_end = selected_box.operator(
                "jhm.move_wall_endpoint", text="終点を移動"
            )
            move_end.endpoint = "END"
        else:
            selected_box.label(text="Wallを選択してください。")
