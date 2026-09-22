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

## 1. New Residential and Side Board combinations

1. In top orthographic view create a default 3600 mm straight Stair. Confirm `STANDARD_RESIDENTIAL`, schema `>=2`, both booleans true, thickness 18 and band 150 in Console.
2. Confirm world bounding width is 936 mm:
   ```python
   print(round(max(v.co.y for v in M.vertices)-min(v.co.y for v in M.vertices),6))
   ```
   For an X-axis Stair this must print `0.936`.
3. Use **住宅階段仕様を変更** successively for BOTH, LEFT-only, RIGHT-only, OFF/OFF. After every change inspect side orthographic, underside oblique, lower end, upper end, and exposed board inner face. The body must remain identical and visually closed with OFF/OFF; no internal void, tread/riser back, body-board gap, or z-fighting may appear.
4. For LEFT-only and RIGHT-only verify the Path center did not move and envelopes are respectively `[-0.450,+0.468]` and `[-0.468,+0.450]` in local Y. Confirm board thickness is 18 mm.
5. Confirm Side Board minimum Z equals `base_z_mm/1000`. In local XZ, the only lower-edge endpoints must be `(-b,B)` and `(0,B)`, with no notch, foot, or raised patch. At the upper end verify the clean edge from `(L-b,H)` to `(L,H)` and no board vertex uphill of `L`.
6. Set band width to 100 mm and confirm the stepped fascia depth changes while thickness remains 18 mm. Restore 150 mm. From side orthographic view confirm the strip is above/downhill of the step contour: vertical offsets go toward `-X`, horizontal offsets toward `+Z`. It must not resemble Candidate r1’s large under-stair plate. Then set Side Board thickness to 24 mm and verify only the external Y thickness changes; restore 18 mm.

## 2. Direction, Path, and accepted Stage 2 geometry

1. Set LEFT-only, note its world side, then use **上り方向を反転**. The stored LEFT boolean must remain true while the board moves to the opposite world side.
2. Use **Path座標を変更** with P0 `(1000,2000)` mm and P1 `(4000,6000)` mm. Verify the Stair and asymmetric board follow the oblique axes while the center Path remains unchanged.
3. Set base Z to 425 mm. Inspect the lower termination and confirm no vertex/board is below 0.425 m.
4. With boards OFF inspect the first step from below: it must have one flat horizontal base plane without notch. Traverse the whole visible stepped soffit: no internal void and no tread/riser back may be visible.
5. At every tread/next-riser junction inspect wireframe/solid views. The Residential tread rear and riser rear must coincide at `jg+r`; riser bottom stays `B+jh`. Confirm no former `x=jg` micro-notch and no geometry past final `L+r`.

## 3. Materials

Create Materials `Wood` and `White` once:

```python
wood=bpy.data.materials.get('Wood') or bpy.data.materials.new('Wood')
white=bpy.data.materials.get('White') or bpy.data.materials.new('White')
```

Use **階段部材Materialを変更** (do not directly edit RNA for the acceptance action).

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
5. Test atomic rejection: enter an invalid band width (`>= min(h,g)`) through redo/operator input. Confirm operation cancels and old mesh pointer, dimensions, Path, ascent, mode/schema, fields/material references, slots, ID, and transform are unchanged.
6. Save, fully exit Blender, reopen, and verify all canonical/material values and geometry. This is a Stage 3 spot test, not Stage 4 lifecycle acceptance.
7. Run **階段を再生成** and recheck geometry/materials.
8. To test `GEOMETRY_MISSING`, save first, clear mesh geometry in a controlled copy, diagnose, then run **管理状態へ復元**. Confirm treads, risers, corrected closed body, enabled boards, slots and polygon indices return.
9. Run the mesh-health helper. Finish with separate BODY and SIDE BOARD visual passes. BODY: closed underside, flat first-step bottom, no internal void, and no exposed tread/riser backs. SIDE BOARD: stepped finish strip follows the upper stair contour, lies on its exterior/upward side, does not form a large under-stair plate, has clean lower and upper terminations without notch/foot, and has no z-fighting.
