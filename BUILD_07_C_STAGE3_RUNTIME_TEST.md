# Build 07-C Stage 3 Candidate r2 — Blender 5.2 LTS Runtime Test

This is a runtime procedure, not an acceptance record. Use Blender 5.2 LTS,
install the candidate ZIP, enable **Japanese House Modeler**, and test copies of
all legacy fixtures. Do not save over a fixture.

## Candidate r1 result — REJECTED

Candidate r1 passed the new-Stair 5 mm default and the `N-1` ordinary nosing
visual checks. It was rejected because the upper-arrival/Final-Riser edge had no
nosing. Runtime review stopped before the later BEVEL, ROUND, placement, and
material gates. Candidate r2 adds the dedicated arrival cap and the confirmed
STEPPED Side Board upper termination; the complete procedure below must be run.

## Test 0 — candidate identity

1. Install with **Edit > Preferences > Add-ons > Install from Disk**.
2. Expected: version `(0, 7, 2)` and description `Build 07-C: Sloped Closed Underside + Straight Stair Finish Variants`.
3. Console: `import japanese_house_modeler as j;print(j.bl_info['version'],j.bl_info['description'])`
4. Evidence: the exact version and description above.

## Test 1 — new default, SQUARE arrival, thickness, and board upper ends

1. Set base `0`, floor-to-floor `2800`, risers `16`, width `900`, tread `30`,
   riser `12`; run **階段を作成** on a 3600 mm Path.
2. Expected: schema 3, STEPPED_CLOSED + STEPPED, body band `150`, nose `5`,
   SQUARE, edge size `5`. There are 15 ordinary Treads plus one short arrival
   cap—not a 16th step. The cap bounds are `L-5 mm .. L+12 mm`, full width, and
   `2770 .. 2800 mm`; Final Riser top is `2770 mm`.
3. Console: `s=bpy.context.object.jhm_stair;print(s.stair_schema_version,s.underside_mode,s.side_board_mode,s.side_board_band_width_mm,s.tread_front_overhang_mm,s.tread_front_edge_mode,s.tread_front_edge_size_mm,s.floor_to_floor_mm,s.tread_thickness_mm)`
4. Evidence: `3 STEPPED_CLOSED STEPPED 150.0 5.0 SQUARE 5.0 2800.0 30.0`; wireframe measurement confirms the arrival band ends exactly at `2.8`.
5. Run **階段寸法を変更**, set tread thickness `40`.
6. Expected: cap becomes `2760 .. 2800 mm`; Final Riser top is `2760 mm`; H
   remains exactly `2.800`, with no need to compensate floor-to-floor.
7. Console: `s=bpy.context.object.jhm_stair;print(s.base_z_mm,s.floor_to_floor_mm,s.tread_thickness_mm,(s.base_z_mm+s.floor_to_floor_mm-s.tread_thickness_mm)/1000,(s.base_z_mm+s.floor_to_floor_mm)/1000)`
8. Evidence: `0.0 2800.0 40.0 2.76 2.8`, matching wireframe measurement of the cap and Final Riser.
9. Restore tread `30`. In **住宅階段仕様を変更**, compare Side Board shape
   **段々** then **勾配**, with BOTH boards.
10. Expected: STEPPED ends at `(L-reveal,H+reveal) -> (L+r,H+reveal) ->
    (L+r,H)`; SLOPED retains its accepted five-point end. Both meet the cap cleanly.
11. Console: `s=bpy.context.object.jhm_stair;print(s.side_board_mode,s.side_board_reveal_mm,s.floor_to_floor_mm,s.tread_thickness_mm)`
12. Evidence: selected mode, `40.0 2800.0 30.0`, and the stated visual upper end.

## Test 2 — zero-nosing legacy compatibility

1. Open a copy of an accepted 07-B schema-2 Residential file and run
   **階段を再生成**. Repeat with a Stage-1/Stage-2 schema-3 file storing nose `0`.
2. Expected: each remains at its original schema, has no arrival cap, keeps the
   Final Riser to H, and exactly reproduces accepted no-nosing geometry.
3. Console: `s=bpy.context.object.jhm_stair;print(s.stair_schema_version,s.tread_front_overhang_mm,s.tread_front_edge_mode,max(v.co.z for v in bpy.context.object.data.vertices))`
4. Evidence: schema `2` or `3`, `0.0 SQUARE`; maximum agrees with its fixture.

## Test 3 — board states and body/board matrix

1. On the r2 Stair, use **住宅階段仕様を変更** with SQUARE nose `5`, size `5`.
   Test BOTH, LEFT, RIGHT, OFF/OFF. Then with BOTH test
   STEPPED_CLOSED+STEPPED, STEPPED_CLOSED+SLOPED,
   SLOPED_CLOSED+STEPPED, and SLOPED_CLOSED+SLOPED.
2. Expected: requested boards only; all combinations prepare; no cavity,
   z-fighting, exposed interior, body/soffit regression, or cap collision.
3. Console: `s=bpy.context.object.jhm_stair;print(s.left_side_board_enabled,s.right_side_board_enabled,s.underside_mode,s.side_board_mode,s.tread_front_overhang_mm,len(bpy.context.object.data.polygons))`
4. Evidence: each requested state and a stable deterministic face count after regeneration.

## Test 4 — grouped atomic invalid values

1. Record the state tuple below. With **住宅階段仕様を変更**, try nose `<0`,
   nose `>= going`, board enabled with nose `70`/reveal `40`, and for both
   **面取り** and **丸** try `(n,q)=(5,0),(5,15),(5,6)` with tread `30`.
2. Expected: every attempt is rejected. Mesh, fields, materials, Stair ID, Path,
   dimensions, and transform remain exactly at the recorded pre-state.
3. Console before/after each: `o=bpy.context.object;s=o.jhm_stair;print((o.data.as_pointer(),s.stair_id,tuple(p.xy[:] for p in s.path_points),s.tread_front_overhang_mm,s.tread_front_edge_mode,s.tread_front_edge_size_mm,tuple(m.as_pointer() if m else 0 for m in o.data.materials),tuple(o.matrix_world)))`
4. Evidence: identical tuples for every rejected edit.

## Test 5 — BEVEL and ROUND ordinary/arrival topology

1. Run **住宅階段仕様を変更** with nose `5`, size `5`, first **面取り**, then
   **丸**. Inspect first/middle/highest ordinary Treads and the arrival cap.
2. Expected: BEVEL has symmetric 5 × 5 mm 45-degree upper/lower chamfers.
   ROUND has exactly four chords per upper and lower quarter arc. The same
   profile appears on the short arrival cap, whose top remains H. All fragments
   are finite, closed, outward, positive-area, and have no cavity or overlap.
3. Console: `o=bpy.context.object;s=o.jhm_stair;print(s.tread_front_edge_mode,len(o.data.vertices),len(o.data.polygons),sum(p.area<=1e-12 for p in o.data.polygons),(s.base_z_mm+s.floor_to_floor_mm)/1000)`
4. Evidence: deterministic counts on regenerate, zero bad faces, finished arrival
   `2.8`; wireframe measurement confirms each profiled cap ends at that height.

## Test 6 — reverse, Undo/Redo, oblique Path, and base Z

1. Run **住宅階段仕様を変更**, changing nose `5` to `6`; immediately press
   **Ctrl+Z**, then **Ctrl+Shift+Z**. Do not use Console between Undo and Redo.
2. Run **上り方向を反転**, repeat the same Undo/Redo discipline, then use
   **階段Pathを変更** for P0 `(1000,2000)` mm and P1 `(4000,6000)` mm. Finally
   run **階段寸法を変更** and set base Z `375`.
3. Expected: every UI operation is one Undo step; nose and short arrival cap
   stay on the downhill/uphill edges appropriate to direction; Path stays two
   points and oblique; finished cap top becomes `3.175` (`0.375 + 2.800`),
   while enabled board tops may extend one reveal above it.
4. Console: `s=bpy.context.object.jhm_stair;print(s.ascent_direction,s.tread_front_overhang_mm,tuple(p.xy[:] for p in s.path_points),s.base_z_mm,max(v.co.z for v in bpy.context.object.data.vertices))`
5. Evidence: Redo values, two requested Path points, `375.0`; cap inspection shows
   `3.175`, and with a board enabled overall maximum is `3.215` for 40 mm reveal.

## Test 7 — Materials and BASIC

1. For SQUARE, BEVEL, and ROUND, use **階段部材Materialを変更** to test Base
   fallback, a Tread override, true UNASSIGNED, and one identical datablock on
   multiple roles.
2. Expected: ordinary and arrival-cap detail resolves as TREAD; slots deduplicate
   by datablock identity; there is no NOSING/TOP_NOSING role.
3. Console: `o=bpy.context.object;print([m.name if m else None for m in o.data.materials],sorted(set(p.material_index for p in o.data.polygons)))`
4. Evidence: only required deduplicated slots and expected indices.
5. Open an accepted BASIC schema-1 fixture and run **階段を再生成**.
6. Expected: BASIC/schema 1 geometry remains unchanged with no Residential cap.
7. Console: `s=bpy.context.object.jhm_stair;print(s.assembly_mode,s.stair_schema_version,s.tread_front_overhang_mm,len(bpy.context.object.data.vertices),len(bpy.context.object.data.polygons))`
8. Evidence: `BASIC_TREAD_RISER 1 0.0` and the fixture's accepted counts.

Candidate r2 remains unaccepted until every gate above passes Blender 5.2 LTS
runtime review.
