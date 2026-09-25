# Build 07-C Stage 4 Candidate — Blender 5.2 LTS Runtime Test

This is a grouped runtime procedure, not an acceptance record. Test the candidate
ZIP in Blender **5.2 LTS**, use copies of legacy fixtures, and retain screenshots
and Console output. Do not save over accepted fixtures. Build 07-C Stage 4 is
**NOT ACCEPTED** until every gate below receives Blender 5.2 LTS runtime review.

## Rules and evidence

- Keep one `.blend` evidence file containing the principal non-default Stair and
  the practical placement scene. Record the candidate ZIP SHA256 separately.
- Use UI operators for lifecycle actions. Console commands below are observation
  only unless a step explicitly says to corrupt state for Repair testing.
- For every Undo/Redo check the order is strictly: **UI operation -> Ctrl+Z ->
  Ctrl+Shift+Z -> Console verification**. Never run a Console command between
  Undo and Redo.
- A rejected edit must leave the Mesh pointer, complete canonical state, Path,
  ascent, mode/schema, Materials and slots, Stair ID, and transform unchanged.

## Test 0 — Candidate identity

1. Install and enable the candidate. In the Console run:
   `import bpy,japanese_house_modeler as j;print(j.bl_info['version'],j.bl_info['description'])`
2. Expected: `(0, 7, 2)` and `Build 07-C: Sloped Closed Underside + Straight Stair Finish Variants`.
3. Record Git commit/tree and ZIP byte size/SHA256. Confirm this document and
   `tests/test_build_07_c_stage4.py` are present; do not mark Stage 4 accepted.

## Test 1 — Full Stage-3 lifecycle, combined Undo/Redo, and full reopen

1. Create a Residential Stair, then make one **住宅階段仕様を変更** operation
   changing STEPPED_CLOSED to SLOPED_CLOSED, STEPPED board to SLOPED, nose 5 to
   8 mm, SQUARE to ROUND, edge size to 4 mm, and body thickness to 145 mm.
2. Immediately use **Ctrl+Z**, then **Ctrl+Shift+Z**, then (and only then) run:
   `o=bpy.context.object;s=o.jhm_stair;print(s.underside_mode,s.side_board_mode,s.side_board_band_width_mm,s.tread_front_overhang_mm,s.tread_front_edge_mode,s.tread_front_edge_size_mm)`
   Expected Redo state: `SLOPED_CLOSED SLOPED 145.0 8.0 ROUND 4.0`. The combined
   edit is exactly one logical Undo step.
3. Set base Z 375 mm; Path `(1000,2000)` to `(4000,6000)` mm; REVERSE; non-default
   tread/riser thickness; and distinct Base, Tread, Riser, Underside, Side Board
   Materials. Confirm identity transform and record Mesh/Stair/material pointers:
   `o=bpy.context.object;s=o.jhm_stair;print(s.stair_id,tuple(p.xy[:] for p in s.path_points),s.ascent_direction,tuple(o.location),tuple(o.rotation_euler),tuple(o.scale),[m.name if m else None for m in o.data.materials],len(o.data.vertices),len(o.data.polygons))`
4. Save, **fully exit Blender**, relaunch Blender, and reopen the file. Repeat the
   command. Expected: exact fields, Path, ascent, Stair ID, Material pointers/slot
   order, identity transform, and deterministic geometry; one managed Stair and
   no duplicate geometry. Visually confirm the arrival top is `base_z + H`.

## Test 2 — Failure rollback, geometry Repair, and Transform Repair

1. Record the full tuple:
   `o=bpy.context.object;s=o.jhm_stair;print((o.data.as_pointer(),s.stair_id,tuple(p.xy[:] for p in s.path_points),s.ascent_direction,s.assembly_mode,s.stair_schema_version,s.underside_mode,s.underside_thickness_mm,s.side_board_band_width_mm,s.left_side_board_enabled,s.right_side_board_enabled,s.side_board_mode,s.side_board_thickness_mm,s.side_board_reveal_mm,s.tread_front_overhang_mm,s.tread_front_edge_mode,s.tread_front_edge_size_mm,tuple(m.as_pointer() if m else 0 for m in o.data.materials),tuple(o.location),tuple(o.rotation_euler),tuple(o.scale)))`
2. Separately submit invalid body thickness `0`; nose `>= going`; enabled board
   with nose `> reveal`; BEVEL with `q=0`; and BEVEL/ROUND with `q >= tread
   thickness/2` and `q > n`. Each must cancel during prepare. Repeat the command
   after each rejection: the tuple and Mesh pointer must be identical, proving no
   partial property update or replacement Mesh.
3. Delete/corrupt the managed Mesh geometry to produce `GEOMETRY_MISSING`, use
   **Repair**, then **Ctrl+Z**, **Ctrl+Shift+Z**, and only then inspect. Expected:
   geometry is rebuilt from canonical state; all Stage-3 fields, Path, ascent,
   dimensions, Materials, Stair ID, and transform are preserved. Do not Repair an
   `INVALID_CANONICAL` object; its Repair control must remain unavailable.
4. Set Location `(1,2,3)`, Rotation to nonzero values, and Scale `(2,.5,3)` to
   produce `TRANSFORM_CHANGED`. Use **Repair**, **Ctrl+Z**, **Ctrl+Shift+Z**, then:
   `o=bpy.context.object;s=o.jhm_stair;print(tuple(o.location),tuple(o.rotation_euler),tuple(o.scale),s.stair_id,tuple(p.xy[:] for p in s.path_points),[m.name if m else None for m in o.data.materials])`
   Expected: `(0,0,0)`, `(0,0,0)`, `(1,1,1)` while ID, Path, geometry semantics,
   Stage-3 settings, and Materials remain unchanged. Transform/geometry Repair
   must not issue a new ID.

## Test 3 — Duplicate ID conflict and targeted Repair

1. Duplicate the managed non-default Stair normally. Both managed copies must
   diagnose `ID_CONFLICT`; record object names, IDs, geometry counts, all Stage-3
   settings, Paths, transforms, and Materials.
2. Select only one conflicting copy and run **Repair**, then **Ctrl+Z** and
   **Ctrl+Shift+Z** before Console inspection:
   `print([(o.name,o.jhm_stair.stair_id,o.jhm_stair.underside_mode,o.jhm_stair.side_board_mode,o.jhm_stair.tread_front_edge_mode,[m.name if m else None for m in o.data.materials]) for o in bpy.context.scene.objects if getattr(getattr(o,'jhm_stair',None),'is_stair',False)])`
3. Expected: only the repaired conflicting Stair has a fresh ID; the original
   survivor ID is stable. Geometry, Stage-3 settings, Path, ascent, Materials,
   and transforms are unchanged, and both objects return to NORMAL.

## Test 4 — Material roles and lifecycle persistence

1. Exercise four cases: (A) Base fallback plus a role override; (B) partial role
   assignment with genuinely unassigned fallback where applicable; (C) all
   unassigned; (D) one identical datablock assigned to every role. Expected roles
   are exactly TREAD, RISER, UNDERSIDE, SIDE_BOARD; no NOSING role; identical
   pointers deduplicate to one slot.
2. Inspect SQUARE, BEVEL, and ROUND. Ordinary nosing and the top-arrival nosing
   use TREAD; both shaped edges use TREAD; SLOPED_CLOSED uses UNDERSIDE; SLOPED
   Side Board uses SIDE_BOARD. Use Material Preview and:
   `o=bpy.context.object;print([m.name if m else None for m in o.data.materials],sorted(set(p.material_index for p in o.data.polygons)),sum(p.area<=1e-12 for p in o.data.polygons))`
3. In sequence run Regenerate, a dimensions edit, oblique Path edit, Reverse,
   combined 07-C settings edit, and Repair. Expected after every operation:
   canonical Material pointers, deduplicated slots, and face assignments persist.
   The saved/reopened result from Test 1 provides the final persistence check.

## Test 5 — Finalize and active-only Delete

1. Duplicate the tested Stair and record its Mesh pointer, vertices/faces,
   coordinates, slots, and Materials. Run **Finalize / Editable Mesh** on the
   copy. Expected: management alone is removed; Mesh pointer and visible mesh do
   not change or regenerate, Materials remain, and Edit Mode works normally.
   Later managed Stair operations ignore it, and its old ID cannot cause an
   `ID_CONFLICT`.
2. Add/retain another managed Stair, managed Wall, managed Finish, unrelated
   Mesh, and shared Material datablocks. Delete the active managed Stair.
   Expected: only that active object is removed; every other object and all
   shared Mesh/Material datablocks remain.
3. Repeat active-only Delete on an abnormal managed Stair (for example
   `GEOMETRY_MISSING` or `TRANSFORM_CHANGED`). Expected: Delete remains available
   under central policy and still removes only the active Stair.

## Test 6 — 07-B schema-2 and BASIC schema-1 full regression

1. Open a copy of the accepted 07-B default Residential fixture. Before and after
   ordinary Regenerate, dimensions, Path, Reverse, Repair, and save/full reopen,
   confirm schema 2, nose 0, STEPPED_CLOSED, STEPPED board, accepted Materials,
   Stair ID and Path. Expected: no arrival cap, Final Riser reaches H, no positive-
   nosing board rise, and exactly **620 vertices / 732 faces**. Only an explicit
   changed 07-C setting may promote schema; ordinary operations must not.
2. Open a BASIC fixture. Confirm BASIC_TREAD_RISER/schema 1 and exactly **248
   vertices / 186 faces**, with no underbody, Side Board, nosing, arrival cap,
   BEVEL, or ROUND behavior. Residential-only stored fields must not affect BASIC
   validity or output.
3. For BASIC exercise dimensions, Path, Reverse, Regenerate, Repair, save/full
   reopen, combined-operation Undo/Redo, Finalize, and active-only Delete. Each
   retains the accepted lifecycle semantics and exact assembly separation.

## Test 7 — Wall/Finish isolation, practical placement, and final topology

1. Prepare one scene with managed Walls, managed Finishes, the Stage-3 Stair, a
   lower-floor-like slab, an **upper-floor-like** slab at finished arrival
   `Z=2800 mm`, and simple Wall-like geometry beside the Stair. Record Wall and
   Finish object counts, canonical state, geometry hashes/counts, and Materials.
2. On the Stair exercise dimensions, Path, Reverse, 07-C settings, Material edit,
   Regenerate, and Repair. Expected: Wall/Finish counts, canonical state,
   geometry, and Materials remain byte-for-byte/semantically unchanged. The
   visual setup must not depend on actual managed Wall/Floor attachment.
3. At `base_z=0`, `floor_to_floor=2800`, inspect lower termination, body
   thickness, SLOPED_CLOSED and STEPPED_CLOSED, STEPPED and SLOPED Side Boards,
   5 mm nose scale, SQUARE/BEVEL/ROUND, arrival nose, and upper board rise. The
   finished arrival/nosing top is exactly `Z=2800 mm` and meets the upper slab;
   there is no major cavity, spike, overlap, or giant triangle.
4. Regenerate representatives A `STEPPED_CLOSED+STEPPED+SQUARE`, B
   `STEPPED_CLOSED+SLOPED+BEVEL`, C `SLOPED_CLOSED+STEPPED+ROUND`, and D
   `SLOPED_CLOSED+SLOPED+ROUND`. For each record deterministic counts (do not
   impose one universal count), NORMAL state, finite coordinates, positive face
   area, zero zero-area faces, no unintended boundary/non-manifold edges,
   `min Z >= B`, body/board uphill `max X <= L+r`, and only intentional noses
   extending downhill.

Record PASS/FAIL and evidence for all eight grouped tests. Do not update
`BUILD_07_C_ACCEPTANCE_RECORD.md` or `ROADMAP.md`, and do not merge, until the
Blender 5.2 LTS runtime reviewer accepts Stage 4.
