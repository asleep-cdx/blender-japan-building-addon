"""Persistent Blender properties used by the Japanese House Modeler add-on."""

import bpy


# Values are stored directly in millimetres so the add-on's UI consistently uses
# mm regardless of Blender's scene unit display.  Future mesh code can convert
# them to metres at the geometry boundary (millimetres / 1000).
_MIN_THICKNESS_MM = 0.1
_MAX_THICKNESS_MM = 10_000.0
_MIN_HEIGHT_MM = 0.1
_MAX_HEIGHT_MM = 100_000.0


class JHM_NewWallDefaults(bpy.types.PropertyGroup):
    """Defaults copied to a wall when wall creation is added in a later build."""

    wall_thickness: bpy.props.FloatProperty(
        name="壁厚",
        description="新規壁のデフォルト壁厚（mm）",
        default=105.0,
        min=_MIN_THICKNESS_MM,
        max=_MAX_THICKNESS_MM,
        precision=1,
    )
    wall_height: bpy.props.FloatProperty(
        name="壁高さ",
        description="新規壁のデフォルト壁高さ（mm）",
        default=2500.0,
        min=_MIN_HEIGHT_MM,
        max=_MAX_HEIGHT_MM,
        precision=1,
    )


class JHM_WallProperties(bpy.types.PropertyGroup):
    """Per-object wall data, deliberately separate from new-wall defaults.

    Build 02 can extend this group with start/end points and connection data while
    keeping the dimensions associated with each generated wall object.
    """

    is_wall: bpy.props.BoolProperty(
        name="日本住宅モデラーの壁",
        description="将来のWall Systemが管理するオブジェクトかどうか",
        default=False,
        options={"HIDDEN"},
    )
    wall_thickness: bpy.props.FloatProperty(
        name="壁厚",
        description="選択中の壁の壁厚（mm）",
        default=105.0,
        min=_MIN_THICKNESS_MM,
        max=_MAX_THICKNESS_MM,
        precision=1,
    )
    wall_height: bpy.props.FloatProperty(
        name="壁高さ",
        description="選択中の壁の壁高さ（mm）",
        default=2500.0,
        min=_MIN_HEIGHT_MM,
        max=_MAX_HEIGHT_MM,
        precision=1,
    )
