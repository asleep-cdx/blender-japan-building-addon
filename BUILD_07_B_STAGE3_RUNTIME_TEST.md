# Build 07-B Stage 3 — Blender 5.2 LTS runtime procedure

This is candidate verification, not an Acceptance Record. Run each numbered test separately in Blender 5.2 LTS. Use the JHM sidebar for every operation whose Undo behavior is under test; use the Python Console only after the operation/Undo/Redo sequence.

## Common console helpers

Select the Stair, open **Scripting > Python Console**, then enter:

```python
import bpy, bmesh, math
O=bpy.context.active_object; S=O.jhm_stair; M=O.data
P=lambda v:(round(v.co.x,6),round(v.co.y,6),round(v.co.z,6))
print(S.assembly_mode,S.stair_schema_version,S.stair_id,tuple(O.location),tuple(O.rotation_euler),tuple(O.scale))
print(len(M.vertices),len(M.polygons),[(i,slot.material.name if slot.material else None) for i,slot in enumerate(O.material_slots)])
```

For mesh health:

```python
bm=bmesh.new(); bm.from_mesh(M)
print('boundary',sum(not e.is_manifold for e in bm.edges),'degenerate',sum(f.calc_area()<1e-12 for f in bm.faces)); bm.free()
```

Note: the managed object is an assembly of individually closed overlapping solids, so global coincident/contact edges are not expected to weld into one shell. Judge the required visible closure in addition to the component health check.

## 1. Candidate r7 geometry tests

0. Create a default Residential Stair. Confirm BOTH ON, reveal 40 mm, thickness 18 mm, compatibility band 150 mm, r7 BOTH count `620/732`, and `stair_issues(...) == ()`.
1. Inspect the complete full-depth boards and 936 mm Y envelope: body ±0.450, LEFT +0.450..+0.468, RIGHT -0.468..-0.450.
2. **Upper termination close-up:** use side orthographic, perspective, and wireframe. Confirm the stepped reveal remains correct; the last reveal point runs horizontally to Final Riser rear; the rear edge is vertical; and there is no spike, giant triangle, diagonal closing plate, gap, or z-fighting. Numerically verify upper rear `(L+r,H)`, lower rear X `L+r`, max X `L+r`, and max Z `H`.
3. Recheck the r6-passed first-step bottom: board/body minimum Z both equal `base_z`, bottoms align, and nothing extends below base.
4. Change reveal 40 -> 60 -> 40: only the Side Board upper XZ silhouette changes. Change thickness 18 -> 24 -> 18: only Y extent changes.
5. Test BOTH, LEFT-only, RIGHT-only, OFF/OFF; then Reverse world-side swap.
6. Test an oblique Path and nonzero `base_z=425 mm`.
7. With boards OFF, visually recheck the accepted Stage 2 `jg+r` rear junction, unchanged `B+jh` Riser bottom, no micro-notch, stepped soffit, flat first-step body bottom, and closed body.

## 3. Materials

Create Materials `Wood` and `White` once:

```python
wood=bpy.data.materials.get('Wood') or bpy.data.materials.new('Wood')
white=bpy.data.materials.get('White') or bpy.data.materials.new('White')
```

Use **階段部材Materialを変更** (do not directly edit RNA for the acceptance action).

First confirm that the dialog visibly presents five usable Blender Material
datablock selectors in this order: Base Material, Tread override, Riser
override, Underside override, and Side Board override. Also open **住宅階段仕様を適用**
on a BASIC Stair and confirm its Base Material selector is visible.

Confirm Candidate r7 preserves the Candidate r5 Material UI using the registered class annotations and the actual dialogs (Blender 5.2 does not reliably enumerate these custom annotations through `bl_rna.properties`):

```python
import japanese_house_modeler.stair_operators as so
print(so.JHM_OT_edit_stair_materials.__annotations__)
print(so.JHM_OT_apply_residential_stair.__annotations__)
```

Verify the five edit `*_material_name` PropertyDeferred annotations and the apply `base_material_name` annotation exist. An empty selector means canonical `None`; then verify the actual selectors and Cases A/B/C below.

1. **Case A:** Base=Wood, Riser=White, all overrides otherwise empty. Slots must identity-dedupe to Wood/White; tread, underside and both boards visually use Wood, risers White.
2. **Case B:** Base empty, Tread=Wood, other overrides empty. Verify exactly one Wood slot plus one empty (`None`) slot. Treads use Wood and every other role uses the empty slot; no substitute Material datablock is created.
3. **Case C:** all five fields empty. Verify no material datablocks/slots are generated and all faces remain unassigned.
4. In Edit Mode select representative faces of every part and inspect Material index. Also print:
   ```python
   print(sorted(set(p.material_index for p in M.polygons)),[(i,s.material.name if s.material else None) for i,s in enumerate(O.material_slots)])
   ```
   LEFT/RIGHT boards must share the SIDE_BOARD-derived index. Regenerate and verify assignments persist.

## 4. Public operations, transaction, Undo, persistence, Repair

1. Keep or load an existing NORMAL BASIC Stair. Ordinary dimension/Path/Reverse/Regenerate/Repair and save/reopen must leave it BASIC.
2. Select it and run **住宅階段仕様を適用**. For zero legacy materials choose None; for one material verify it is proposed; for multiple materials explicitly select a Base or explicit None. Verify complete body, both boards, role assignments, and schema >=2.
3. Immediately press Ctrl-Z (no Console activity in between); confirm exact BASIC geometry, slots, canonical fields, ID, Path and transform return. Ctrl-Shift-Z and confirm Residential returns.
4. On Residential use settings and material dialogs; on BASIC confirm those two operators are unavailable. From Console try the direct operators on BASIC and confirm `CANCELLED`, proving stale UI cannot bypass the central gate.
5. Test atomic rejection: enter an invalid Side Board reveal (`>= min(h,g)`) through redo/operator input. Confirm operation cancels and old mesh pointer, dimensions, Path, ascent, mode/schema, fields/material references, slots, ID, and transform are unchanged.
6. Save, fully exit Blender, reopen, and verify all canonical/material values and geometry. This is a Stage 3 spot test, not Stage 4 lifecycle acceptance.
7. Run **階段を再生成** and recheck geometry/materials.
8. To test `GEOMETRY_MISSING`, save first, clear mesh geometry in a controlled copy, diagnose, then run **管理状態へ復元**. Confirm treads, risers, corrected closed body, enabled boards, slots and polygon indices return.
9. Run the mesh-health helper. Finish with separate BODY and SIDE BOARD visual passes. BODY: closed underside, flat first-step bottom, no internal void, and no exposed tread/riser backs. SIDE BOARD: full-depth external plate follows the stepped reveal above and the accepted body soffit below, covers the body side without a gap, has clean base/upper terminations, and has no z-fighting.
