"""Property definitions for the Japanese House Modeler add-on."""

import bpy


_MIN_THICKNESS_MM = 0.1
_MAX_THICKNESS_MM = 10_000.0
_MIN_HEIGHT_MM = 0.1
_MAX_HEIGHT_MM = 100_000.0


class JHM_NewWallDefaults(bpy.types.PropertyGroup):
    """Defaults copied to a wall when wall creation is added in a later build."""

    wall_thickness: bpy.props.FloatProperty(
        name="壁厚",
        description="新規壁のデフォルト壁厚（mm）",
        default=130.0,
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
    floor_reference_z_mm: bpy.props.FloatProperty(
        name="床基準高さ", default=0.0, precision=1,
    )
    ceiling_reference_z_mm: bpy.props.FloatProperty(
        name="天井基準高さ", default=2500.0, precision=1,
    )


class JHM_WallConnection(bpy.types.PropertyGroup):
    """One persistent link to another managed Wall endpoint."""

    target_object: bpy.props.PointerProperty(
        name="接続先Wall",
        type=bpy.types.Object,
        options={"HIDDEN"},
    )
    target_endpoint: bpy.props.EnumProperty(
        name="接続先端点",
        items=(
            ("START", "始点", "接続先Wallの始点"),
            ("END", "終点", "接続先Wallの終点"),
        ),
        options={"HIDDEN"},
    )


class JHM_WallProperties(bpy.types.PropertyGroup):
    """Per-object wall data, deliberately separate from new-wall defaults.

    Start and end use world-space metres because they define the wall core line.
    Future snapping and connection features can use these points without deriving
    them from an object's mesh data.
    """

    is_wall: bpy.props.BoolProperty(
        name="日本住宅モデラーの壁",
        description="将来のWall Systemが管理するオブジェクトかどうか",
        default=False,
        options={"HIDDEN"},
    )
    wall_id: bpy.props.StringProperty(
        name="Wall ID", default="", options={"HIDDEN"},
        description="永続的なWall識別子（Object名とは独立）",
    )
    start: bpy.props.FloatVectorProperty(
        name="始点",
        description="壁芯の始点（ワールド座標、m）",
        size=3,
        subtype="XYZ",
        default=(0.0, 0.0, 0.0),
        options={"HIDDEN"},
    )
    end: bpy.props.FloatVectorProperty(
        name="終点",
        description="壁芯の終点（ワールド座標、m）",
        size=3,
        subtype="XYZ",
        default=(0.0, 0.0, 0.0),
        options={"HIDDEN"},
    )
    wall_thickness: bpy.props.FloatProperty(
        name="壁厚",
        description="選択中の壁の壁厚（mm）",
        default=130.0,
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
    start_connections: bpy.props.CollectionProperty(
        type=JHM_WallConnection,
        options={"HIDDEN"},
    )
    end_connections: bpy.props.CollectionProperty(
        type=JHM_WallConnection,
        options={"HIDDEN"},
    )


class JHM_FinishSpan(bpy.types.PropertyGroup):
    """One ordered canonical wall-face interval."""

    wall_object: bpy.props.PointerProperty(type=bpy.types.Object, options={"HIDDEN"})
    expected_wall_id: bpy.props.StringProperty(default="", options={"HIDDEN"})
    side: bpy.props.EnumProperty(items=(("LEFT", "左", ""), ("RIGHT", "右", "")))
    entry_boundary_kind: bpy.props.EnumProperty(items=tuple(
        (value, value, "") for value in
        ("WALL_START", "WALL_END", "DISTANCE_FROM_START", "DISTANCE_FROM_END")
    ), default="WALL_START")
    entry_boundary_value_mm: bpy.props.FloatProperty(default=0.0, min=0.0)
    exit_boundary_kind: bpy.props.EnumProperty(items=tuple(
        (value, value, "") for value in
        ("WALL_START", "WALL_END", "DISTANCE_FROM_START", "DISTANCE_FROM_END")
    ), default="WALL_END")
    exit_boundary_value_mm: bpy.props.FloatProperty(default=0.0, min=0.0)
    traversal_direction: bpy.props.EnumProperty(
        items=(("FORWARD", "順方向", ""), ("REVERSE", "逆方向", "")),
        default="FORWARD",
    )


class JHM_FinishExclusion(bpy.types.PropertyGroup):
    """Future-compatible opening/manual exclusion attached to a Wall face."""

    wall_object: bpy.props.PointerProperty(type=bpy.types.Object, options={"HIDDEN"})
    expected_wall_id: bpy.props.StringProperty(default="", options={"HIDDEN"})
    side: bpy.props.EnumProperty(items=(("LEFT", "左", ""), ("RIGHT", "右", "")))
    start_boundary_kind: bpy.props.EnumProperty(items=tuple(
        (value, value, "") for value in
        ("WALL_START", "WALL_END", "DISTANCE_FROM_START", "DISTANCE_FROM_END")
    ), default="WALL_START")
    start_boundary_value_mm: bpy.props.FloatProperty(default=0.0, min=0.0)
    end_boundary_kind: bpy.props.EnumProperty(items=tuple(
        (value, value, "") for value in
        ("WALL_START", "WALL_END", "DISTANCE_FROM_START", "DISTANCE_FROM_END")
    ), default="WALL_END")
    end_boundary_value_mm: bpy.props.FloatProperty(default=0.0, min=0.0)
    exclusion_type: bpy.props.EnumProperty(items=(
        ("MANUAL", "Manual", ""), ("DOOR", "Door", ""),
        ("WINDOW", "Window", ""), ("OTHER", "Other", ""),
    ), default="MANUAL")
    source_id: bpy.props.StringProperty(default="")
    exclusion_id: bpy.props.StringProperty(default="", options={"HIDDEN"})
    fragment_id: bpy.props.StringProperty(default="", options={"HIDDEN"})
    # False is intentional: persisted 06-A records remain visually inactive.
    enabled: bpy.props.BoolProperty(name="有効", default=False)


class JHM_FinishProperties(bpy.types.PropertyGroup):
    is_finish: bpy.props.BoolProperty(default=False, options={"HIDDEN"})
    finish_id: bpy.props.StringProperty(default="", options={"HIDDEN"})
    finish_type: bpy.props.EnumProperty(
        items=(("BASEBOARD", "Baseboard Test", ""), ("CROWN", "Crown", "")),
        default="BASEBOARD",
    )
    # String storage preserves the accepted 06-A ``SIMPLE_10X60`` identifier;
    # the Stage 1 selector is intentionally constrained by its edit operator.
    profile_id: bpy.props.StringProperty(default="SIMPLE")
    profile_revision: bpy.props.IntProperty(default=1, options={"HIDDEN"})
    profile_schema_version: bpy.props.IntProperty(default=1, options={"HIDDEN"})
    profile_height_mm: bpy.props.FloatProperty(
        name="高さ", default=60.0, min=0.1, max=100000.0, precision=1)
    profile_projection_mm: bpy.props.FloatProperty(
        name="出幅", default=10.0, min=0.1, max=10000.0, precision=1)
    vertical_reference: bpy.props.EnumProperty(
        items=(("FLOOR", "床", ""), ("CEILING", "天井", ""),
               ("ABSOLUTE", "絶対高さ", "")), default="FLOOR",
    )
    vertical_offset_mm: bpy.props.FloatProperty(default=0.0, precision=1)
    absolute_z_mm: bpy.props.FloatProperty(default=0.0, precision=1)
    join_policy: bpy.props.EnumProperty(
        items=(("MITER", "留め", ""), ("BREAK", "分割", "")), default="MITER",
    )
    miter_limit: bpy.props.FloatProperty(default=4.0, min=1.0, max=100.0)
    closed: bpy.props.BoolProperty(default=False)
    spans: bpy.props.CollectionProperty(type=JHM_FinishSpan)
    exclusions: bpy.props.CollectionProperty(type=JHM_FinishExclusion)
    active_exclusion_index: bpy.props.IntProperty(default=0, min=0)
