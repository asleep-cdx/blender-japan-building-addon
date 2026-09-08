"""Operators reserved for the Japanese House Modeler UI."""

import bpy


class JHM_OT_wall_creation_not_implemented(bpy.types.Operator):
    """Explain why wall creation is unavailable in Build 01."""

    bl_idname = "jhm.wall_creation_not_implemented"
    bl_label = "壁作成は未実装です"
    bl_description = "Build 01では壁の生成を実装していません"

    def execute(self, context):
        self.report({"INFO"}, "Wall creation is not implemented in Build 01.")
        return {"FINISHED"}
