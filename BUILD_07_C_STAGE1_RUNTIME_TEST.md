# Build 07-C Stage 1 — Blender 5.2 LTS Runtime Test

Status: **MANUAL RUNTIME PROCEDURE — NOT AN ACCEPTANCE RECORD**

Run each numbered test separately and record PASS/FAIL before continuing. Console
output is evidence of canonical state; screenshots are separate visual evidence.
For every Undo/Redo check use exactly **JHM UI operation → Ctrl+Z →
Ctrl+Shift+Z → Console inspection**. Never issue a Console command between Undo
and Redo. Use disposable file copies for destructive tests.

## Test 0 — Candidate identity
Record candidate commit/tree/ZIP hash, `bpy.app.version_string`, and installed
add-on metadata. Expect Blender 5.2 LTS, version `(0, 7, 2)`, and description
`Build 07-C: Sloped Closed Underside + Straight Stair Finish Variants`.

## Test 1 — New Stage 1 Stair
Create a Residential Stair. Console evidence must show `STANDARD_RESIDENTIAL`,
schema 3, `STEPPED_CLOSED`, `side_board_mode == 'STEPPED'`, body depth 150 mm,
overhang 0 mm, edge `SQUARE`, edge size 5 mm, 620 vertices / 732 faces, and
NORMAL diagnosis. Visual evidence must match the accepted 07-B default exactly.

## Test 2 — Open accepted 07-B schema-2 file
Open without editing. Confirm schema remains 2, mesh/counts and diagnosis are
unchanged, and Path, Stair ID, Material pointers/slots, and Side Boards are
unchanged. Confirm visually that no nosing appeared.

## Test 3 — Ordinary regenerate of 07-B Stair
Regenerate the Test 2 Stair. Confirm schema remains 2 and the accepted 07-B
620/732 geometry, Path, ID, Materials, and NORMAL diagnosis remain unchanged.

## Test 4 — Stair-body thickness UI and Undo/Redo
Snapshot every canonical dimension, Path, ID, Material pointer/slot, transform,
and mesh. Use **住宅階段仕様を変更** to change **階段本体厚み (mm)** from 150
to 120. Perform the mandatory Undo/Redo sequence, then inspect. Expect visible
STEPPED body depth change, schema 3, NORMAL, and no change to floor-to-floor,
riser count, tread/riser thickness, width, Side Board thickness/reveal, Path,
ID, Materials, or transform.

## Test 5 — Invalid body depth atomic rejection
Snapshot Object/data identity and all Test 4 state. Submit 175 mm or greater when
actual riser is 175 mm. Expect CANCELLED/warning before mutation; mesh, canonical
values, ID, Materials, slots, and transform must be identical.

## Test 6 — Save/full-exit/reopen
Save the valid 120 mm schema-3 Stair, fully exit Blender, restart, and reopen.
Confirm edited depth, schema, geometry, Materials, ID, transform, and NORMAL state.

## Test 7 — 07-A BASIC compatibility
Open an accepted BASIC/schema-1 file. Confirm 248 vertices / 186 faces. Separately
run Dimension, Path, Reverse, Regenerate, Repair, and save/reopen. Every result
must remain `BASIC_TREAD_RISER`; 07-C fields must not convert or invalidate it.

## Test 8 — BASIC to Residential Apply
Use **住宅階段仕様を適用** on verified BASIC, then mandatory Undo/Redo. Redo must
produce schema 3, compatibility-neutral Stage 1 values (`STEPPED_CLOSED`,
`STEPPED`, 150, 0, `SQUARE`, 5), and 620/732. Verify Undo restored the exact BASIC
mesh, canonical state, Path, ID, Materials, and transform.

## Test 9 — Material preservation
On an accepted 07-B Material Case A Stair, snapshot all five pointers, effective
roles, slots, and representative face indices. Edit body depth and separately
Regenerate. Expect identical TREAD/RISER/UNDERSIDE/SIDE_BOARD semantics and slot
identity after both operations.

## Test 10 — Focused lifecycle smoke
On separate copies test Transform Repair or controlled `GEOMETRY_MISSING` Repair.
Expect the new fields and edited body depth to survive, geometry to recover, and
NORMAL diagnosis. Apply mandatory Undo/Redo where applicable.

## Test 11 — Wall / Finish isolation smoke
Snapshot a known-good managed Wall and Finish (canonical state, IDs, geometry,
Materials, and diagnosis). Perform Stage 1 Stair creation, body-depth edit,
Regenerate, and Repair on copies. Confirm every Wall/Finish snapshot is unchanged.

## Completion gate
Tabulate Test 0–11 with Console evidence files and separate visual screenshots.
Do not perform SLOPED_CLOSED, SLOPED Side Board, 5 mm nosing, BEVEL, or ROUND
visual tests: their production geometry belongs to later stages. Any failure
stops acceptance and must retain the file and traceback.
