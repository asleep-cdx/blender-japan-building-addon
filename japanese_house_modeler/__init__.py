"""日本住宅モデラー Build 01 add-on package."""

bl_info = {
    "name": "日本住宅モデラー",
    "author": "Japanese House Modeler Contributors",
    "version": (0, 1, 0),
    "blender": (5, 2, 0),
    "location": "View3D > Sidebar > 日本住宅",
    "description": "Foundation UI for a future Japanese house wall system",
    "category": "3D View",
}

from . import operators, properties, ui


_CLASSES = (
    properties.JHM_NewWallDefaults,
    properties.JHM_WallProperties,
    operators.JHM_OT_wall_creation_not_implemented,
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
    bpy.types.Object.jhm_wall = bpy.props.PointerProperty(
        type=properties.JHM_WallProperties
    )


def unregister():
    """Remove every property and class owned by this add-on."""
    import bpy

    del bpy.types.Object.jhm_wall
    del bpy.types.Scene.jhm_new_wall_defaults

    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
