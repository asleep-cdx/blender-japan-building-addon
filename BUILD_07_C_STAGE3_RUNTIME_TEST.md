# Build 07-C Stage 3 — Blender 5.2 LTS Runtime Test

This is a runtime procedure, not an acceptance record. Use Blender 5.2 LTS,
install the candidate ZIP, enable **Japanese House Modeler**, open the System
Console, and keep one saved copy of every legacy fixture. Do not save over a
fixture. Unless stated otherwise, select exactly one managed Stair in Object
Mode. A failed dialog must leave the object byte-for-byte equivalent at the
observable Blender-data level.

## Test 0 — candidate identity

1. Install the candidate with **Edit > Preferences > Add-ons > Install from Disk**.
2. Expected: version is `(0, 7, 2)` and description is `Build 07-C: Sloped Closed Underside + Straight Stair Finish Variants`.
3. Console: `import japanese_house_modeler as j; print(j.bl_info['version'],j.bl_info['description'])`
4. Evidence: `(0, 7, 2)` and the exact description above.

## Test 1 — explicit new Residential default

1. Set new-Stair values to base `0`, floor-to-floor `2800`, risers `16`, width
   `900`, tread `30`, riser `12`; run **階段を作成** and draw a 3600 mm path.
2. Expected: a schema-3 Residential Stair with STEPPED_CLOSED underside,
   STEPPED boards, 150 mm body band, SQUARE front, 5 mm nose and 5 mm stored
   edge size. The nose is visibly 5 mm downhill.
3. Console: `s=bpy.context.object.jhm_stair; print(s.assembly_mode,s.stair_schema_version,s.underside_mode,s.side_board_mode,s.side_board_band_width_mm,s.tread_front_overhang_mm,s.tread_front_edge_mode,s.tread_front_edge_size_mm)`
4. Evidence: `STANDARD_RESIDENTIAL 3 STEPPED_CLOSED STEPPED 150.0 5.0 SQUARE 5.0`.

## Test 2 — accepted 07-B schema-2 fixture

1. Open a copy of the accepted 07-B file, select its Residential Stair, then
   run **階段を再生成**.
2. Expected: accepted 07-B geometry remains rectangular with no nose.
3. Console: `s=bpy.context.object.jhm_stair; print(s.stair_schema_version,s.tread_front_overhang_mm,s.tread_front_edge_mode)`
4. Evidence: `2 0.0 SQUARE`.

## Test 3 — accepted Stage-1/Stage-2 schema-3 fixture

1. Open a copy whose stored overhang is zero and run **階段を再生成**.
2. Expected: no visual migration and no 5 mm nose.
3. Console: `s=bpy.context.object.jhm_stair; print(s.stair_schema_version,s.tread_front_overhang_mm,min(v.co.x for v in bpy.context.object.data.vertices))`
4. Evidence: schema `3`, overhang `0.0`; the minimum agrees with the fixture.

## Test 4 — SQUARE 5 mm

1. Run **住宅階段仕様を変更**; set 段鼻突出量 `5`, 踏板前縁 **角**, 前縁サイズ `5`.
2. Inspect the first, middle and highest independent Tread.
3. Expected: each full rectangular front moves downhill exactly 5 mm; rear,
   top/bottom Z and all Risers remain fixed; there are 15 treads and no tread
   at the 2800 mm arrival.
4. Console: `o=bpy.context.object; s=o.jhm_stair; print(s.tread_front_overhang_mm,len([p for p in o.data.polygons if p.material_index==0]),max(v.co.z for v in o.data.vertices))`
5. Evidence: `5.0`, stable role faces, and the highest geometry does not imply
   a new arrival Tread (confirm visually with wireframe).

## Test 5 — Side Board choices

1. In **住宅階段仕様を変更**, keep SQUARE/5 mm and test BOTH, LEFT only,
   RIGHT only, and OFF/OFF by toggling **左Side Board** and **右Side Board**.
2. Expected: the requested boards alone appear; the fixed profiles do not
   move, and there is no cavity or z-fighting behind the nose.
3. Console: `s=bpy.context.object.jhm_stair; print(s.left_side_board_enabled,s.right_side_board_enabled,s.side_board_reveal_mm,s.tread_front_overhang_mm)`
4. Evidence: each toggle pair, reveal `40.0`, nose `5.0`.

## Test 6 — invalid nose greater than reveal is atomic

1. With a board enabled and reveal `40`, record the following console tuple.
2. Run **住宅階段仕様を変更**, enter nose `70`, and confirm.
3. Expected: warning/cancellation; Mesh, fields, materials, ID, Path,
   dimensions and transform are unchanged.
4. Console before and after: `o=bpy.context.object;s=o.jhm_stair;print((o.data.as_pointer(),s.stair_id,tuple(p.xy[:] for p in s.path_points),s.tread_front_overhang_mm,tuple(m.as_pointer() if m else 0 for m in o.data.materials),tuple(o.matrix_world)))`
5. Evidence: identical tuples.

## Test 7 — BEVEL

1. With nose `5`, run **住宅階段仕様を変更**; choose **面取り**, size `5`.
2. Inspect first/middle/highest Treads in wireframe.
3. Expected: symmetric 5 × 5 mm 45-degree upper/lower chamfers, horizontal
   top/bottom, fixed rear, no cavity/self-overlap, closed topology.
4. Console: `o=bpy.context.object;print(len(o.data.vertices),len(o.data.polygons),sum(1 for p in o.data.polygons if p.area<=1e-12))`
5. Evidence: deterministic counts for repeated regeneration and zero bad faces.

## Test 8 — ROUND

1. Run **住宅階段仕様を変更**; choose **丸**, nose `5`, size `5`.
2. Inspect first/middle/highest Treads.
3. Expected: both front corners are rounded; each quarter arc has exactly four
   straight chords, transitions look tangent, and topology is closed without overlap.
4. Console: `o=bpy.context.object;print(len(o.data.vertices),len(o.data.polygons),sum(1 for p in o.data.polygons if p.area<=1e-12))`
5. Evidence: deterministic counts and zero zero-area faces; visually count four
   chords on each corner of one isolated front section.

## Test 9 — edge-size validation is atomic

1. For both **面取り** and **丸**, use **住宅階段仕様を変更** to try `(n,q)`
   values `(5,0)`, `(5,15)` (with 30 mm tread), and `(5,6)`.
2. Expected: every edit is rejected (`q=0`, `q>=t/2`, `q>n`) with the exact
   pre-state preserved.
3. Console after each: `s=bpy.context.object.jhm_stair;print(s.tread_front_overhang_mm,s.tread_front_edge_mode,s.tread_front_edge_size_mm,bpy.context.object.data.as_pointer())`
4. Evidence: all four values remain those from before the attempt.

## Test 10 — body/board matrix

1. Through **住宅階段仕様を変更**, test `STEPPED_CLOSED+STEPPED`,
   `STEPPED_CLOSED+SLOPED`, `SLOPED_CLOSED+STEPPED`, and
   `SLOPED_CLOSED+SLOPED`, always SQUARE nose `5`, size `5`, BOTH boards.
2. Expected: all prepare cleanly; body and accepted board silhouettes remain
   unchanged behind the exterior nose.
3. Console: `s=bpy.context.object.jhm_stair;print(s.underside_mode,s.side_board_mode,s.tread_front_overhang_mm,len(bpy.context.object.data.polygons))`
4. Evidence: each requested pair, `5.0`, stable deterministic face count.

## Test 11 — FORWARD / REVERSE and one-step Undo

1. Start FORWARD. Run **住宅階段仕様を変更** and change nose `5` to `6`.
2. Immediately press **Ctrl+Z**, then **Ctrl+Shift+Z**. Do not open or use the
   Console between Undo and Redo. Only after Redo, open Console.
3. Run **上り方向を反転**, then repeat the same Undo/Redo discipline.
4. Expected: each dialog/reverse is one Undo step and geometry remains on the
   correct downhill end in FORWARD and REVERSE.
5. Console: `s=bpy.context.object.jhm_stair;print(s.ascent_direction,s.tread_front_overhang_mm,tuple(p.xy[:] for p in s.path_points))`
6. Evidence: direction reflects Redo, nose `6.0`, Path order unchanged.

## Test 12 — oblique two-point Path

1. Use **階段Pathを変更** and enter P0 `(1000,2000)` mm, P1 `(4000,6000)` mm;
   set SQUARE nose `5` with **住宅階段仕様を変更**.
2. Expected: a straight oblique Stair; noses remain perpendicular to ascent
   and full width. No multi-point Path is introduced.
3. Console: `s=bpy.context.object.jhm_stair;print(tuple(p.xy[:] for p in s.path_points),len(s.path_points),s.tread_front_overhang_mm)`
4. Evidence: `((1,2),(4,6))`, point count `2`, nose `5.0` (float formatting may vary).

## Test 13 — nonzero base Z

1. Run **階段寸法を変更**, set 下端基準高さ `375`; keep SQUARE nose `5`.
2. Expected: the complete Stair starts at 375 mm and all front treatment moves
   with it; dimensions and rise are otherwise unchanged.
3. Console: `s=bpy.context.object.jhm_stair;print(s.base_z_mm,min(v.co.z for v in bpy.context.object.data.vertices))`
4. Evidence: `375.0` and minimum local Z `0.375`.

## Test 14 — Material roles

1. For SQUARE, BEVEL and ROUND, run **階段部材Materialを変更**. Test Base-only,
   a distinct Tread override, deliberately empty/UNASSIGNED roles, and reuse
   the same datablock for multiple roles.
2. Expected: every detailed front face uses TREAD resolution; fallback works;
   empty remains truly unassigned; identical datablocks occupy one slot; no
   NOSING role/material exists.
3. Console: `o=bpy.context.object;print([m.name if m else None for m in o.data.materials],sorted(set(p.material_index for p in o.data.polygons)))`
4. Evidence: only required deduplicated slots/indices, stable across each mode.

## Test 15 — BASIC schema 1

1. Open an accepted BASIC schema-1 fixture and run **階段を再生成**.
2. Expected: it remains BASIC/schema 1 and its accepted geometry is unchanged;
   no nose or Residential body/boards appear.
3. Console: `s=bpy.context.object.jhm_stair;print(s.assembly_mode,s.stair_schema_version,s.tread_front_overhang_mm,len(bpy.context.object.data.vertices),len(bpy.context.object.data.polygons))`
4. Evidence: `BASIC_TREAD_RISER 1 0.0` plus the fixture's original counts.

Stage 3 remains unaccepted until every result above is recorded from Blender
5.2 LTS runtime review.
