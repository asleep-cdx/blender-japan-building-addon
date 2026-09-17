"""日本住宅モデラー add-on package."""

bl_info = {
    "name": "日本住宅モデラー",
    "author": "Japanese House Modeler Contributors",
    "version": (0, 6, 3),
    "blender": (5, 2, 0),
    "location": "View3D > Sidebar > 日本住宅",
    "description": "Build 06-C Stage 2: Standard and Custom Crown Profiles",
    "category": "3D View",
}

from . import finish_operators, operators, properties, ui


_CLASSES = (
    properties.JHM_NewWallDefaults,
    properties.JHM_WallConnection,
    properties.JHM_WallProperties,
    properties.JHM_FinishSpan,
    properties.JHM_FinishExclusion,
    properties.JHM_CustomProfilePoint,
    properties.JHM_CustomProfileDefinition,
    properties.JHM_FinishProperties,
    operators.JHM_OT_create_wall,
    operators.JHM_OT_move_wall_endpoint,
    operators.JHM_OT_edit_wall_dimensions,
    operators.JHM_OT_rebuild_wall_joints,
    operators.JHM_OT_repair_wall,
    operators.JHM_OT_delete_wall,
    finish_operators.JHM_OT_start_finish_path,
    finish_operators.JHM_OT_regenerate_finish,
    finish_operators.JHM_OT_register_custom_profile,
    finish_operators.JHM_OT_delete_custom_profile,
    finish_operators.JHM_OT_edit_finish_profile,
    finish_operators.JHM_OT_add_finish_exclusion,
    finish_operators.JHM_OT_edit_finish_exclusion,
    finish_operators.JHM_OT_remove_finish_exclusion,
    finish_operators.JHM_OT_toggle_finish_exclusion,
    finish_operators.JHM_OT_edit_finish_boundaries,
    finish_operators.JHM_OT_regenerate_all_finishes,
    finish_operators.JHM_OT_repair_finish,
    finish_operators.JHM_OT_delete_finish,
    finish_operators.JHM_OT_convert_finish_mesh,
    ui.JHM_PT_house_modeler,
)


def register():
    """Register add-on classes and the separate scene/object data containers."""
    import bpy

    for cls in _CLASSES:
        bpy.utils.register_class(cls)

    bpy.types.Scene.jhm_new_wall_defaults = bpy.props.PointerProperty(
        type=properties.JHM_NewWallDefaults
    )
    bpy.types.Scene.jhm_custom_profiles = bpy.props.CollectionProperty(
        type=properties.JHM_CustomProfileDefinition)
    bpy.types.Scene.jhm_custom_profile_index = bpy.props.IntProperty(default=0, min=0)
    bpy.types.Scene.jhm_finish_regeneration_required = bpy.props.BoolProperty(
        name="仕上げ再生成が必要", default=False, options={"HIDDEN"})
    bpy.types.Object.jhm_wall = bpy.props.PointerProperty(
        type=properties.JHM_WallProperties
    )
    bpy.types.Object.jhm_finish = bpy.props.PointerProperty(
        type=properties.JHM_FinishProperties
    )


def unregister():
    """Remove every property and class owned by this add-on."""
    import bpy

    del bpy.types.Object.jhm_finish
    del bpy.types.Object.jhm_wall
    del bpy.types.Scene.jhm_new_wall_defaults
    del bpy.types.Scene.jhm_custom_profile_index
    del bpy.types.Scene.jhm_custom_profiles
    del bpy.types.Scene.jhm_finish_regeneration_required

    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
