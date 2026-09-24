# Build 07-B Stage 4 — Blender 5.2 LTS Runtime Test

Status: **MANUAL RUNTIME PROCEDURE — NOT AN ACCEPTANCE RECORD**

This procedure closes the Build 07-B lifecycle/full-regression gate. Run one
numbered test at a time, retain the requested Console output and screenshots,
record **PASS** or **FAIL**, and only then continue. Use disposable copies where a
test corrupts or deletes data. A pure-Python test result is not Blender evidence.

## Rules and evidence

- Target Blender is **5.2 LTS**. Install the Candidate ZIP produced by the user;
  this repository task does not produce it.
- Before each destructive test save a separate test copy. Keep one known-good
  Residential Stair and one accepted 07-A BASIC Stair untouched.
- For every Undo test the order is strictly: **JHM UI operation → Ctrl+Z →
  Ctrl+Shift+Z → Python Console inspection**. Do not open or use the Console
  before Undo or between Undo and Redo. Direct RNA edits are setup/corruption,
  never evidence for an operator's Undo contract.
- Evidence for every test: operation and inputs, Console output after the UI and
  Undo/Redo sequence, relevant screenshots, result, and failure notes.
- A failure stops acceptance. Preserve the file and full traceback; do not repair
  production or weaken the expected result during this run.

## Test 0 — Candidate identity

Record, without modifying the Candidate:

1. GitHub production commit and Git tree SHA.
2. Candidate ZIP filename, byte size, and SHA256.
3. `bpy.app.version_string`.
4. Add-on version and description from `japanese_house_modeler/__init__.py` and
   Blender's installed extension information.

Expected version is `(0, 7, 1)` and description is
`Build 07-B: Standard Residential Straight Stair`. Evidence is a text record plus
the Blender Add-ons screenshot. Mark PASS/FAIL before Test 1.

## Test 1 — New Residential creation and creation Undo/Redo

Create a new Stair from the JHM UI. Immediately use Ctrl+Z and Ctrl+Shift+Z, with
no Console use between them. Then inspect the active object's `jhm_stair` record,
mesh counts, transform, and `stair_issues(object, scene)`.

Expected: `STANDARD_RESIDENTIAL`, schema `>=2`, both boards enabled, reveal 40
mm, thickness 18 mm, compatibility closed-body depth 150 mm, identity transform,
NORMAL diagnosis, and accepted r7 default geometry (620 vertices / 732 polygons).
Capture overall, underside, and upper-termination screenshots.

## Test 2 — Dimension edit and Undo/Redo

On the Residential object use **階段寸法を変更**, changing width to a clearly
different valid value. Perform the mandatory Undo/Redo sequence, then compare a
snapshot made before the UI operation with the final state.

Expected: new width after Redo; mode, schema, Stair ID, Path, ascent, all
Residential settings, five Material pointers, and identity transform preserved.
The complete body and boards regenerate and diagnosis is NORMAL.

## Test 3 — Invalid dimension prepare rejection

On a saved copy, record Object identity, `Object.data` identity, all canonical
values, five Material pointers, material slots, Stair ID, and transform. Invoke
**階段寸法を変更** with an invalid value (for example a geometrically impossible
thickness/rise combination).

Expected: operator reports rejection/CANCELLED and every snapshot item remains
identical; no replacement mesh, orphan substitute Material, or partial canonical
edit exists. Record the warning and post-rejection Console comparison.

## Test 4 — Oblique Path edit and Undo/Redo

Use **Path座標を変更** to set a clearly oblique two-point Path. Perform the
mandatory Undo/Redo sequence and then inspect the ordered Path and resolved
forward/left axes.

Expected: exact entered Path order, oblique resolved axes, complete Residential
body and boards aligned to the Path, unchanged mode/schema/ID/settings/Materials,
identity transform, and NORMAL diagnosis.

## Test 5 — Reverse and semantic left/right

Use **上り方向を反転**, then mandatory Undo/Redo. Inspect only afterward.

Expected: Path point order, ID, mode, schema, Materials, and board booleans are
unchanged; ascent is reversed. LEFT/RIGHT still mean left/right while facing
uphill, so the board's world-space side reverses correctly. Capture oblique plan
and side views and a NORMAL diagnosis.

## Test 6 — BASIC load, ordinary operations, and save/reopen

Open an accepted Build 07-A BASIC `.blend` (or a separately verified compatible
BASIC file). Merely loading it must not convert it. Save under a new filename,
fully exit Blender, restart, and reopen. One at a time, using fresh copies where
needed, run dimension edit, Path edit, Reverse, Regenerate, and a controlled
`GEOMETRY_MISSING` Repair.

Expected after every operation: `BASIC_TREAD_RISER`, original schema semantics,
07-A Material behavior, and no Residential body or Side Boards. Record state and
mesh evidence after each sub-operation; do not batch their PASS/FAIL decisions.

## Test 7 — Explicit BASIC to Residential conversion Undo/Redo

On the verified BASIC object run **住宅階段仕様を適用**. Immediately Ctrl+Z and
Ctrl+Shift+Z; do not inspect in between. After Redo compare stored snapshots.

Expected: Undo had restored the exact BASIC mesh/slots/canonical/Path/ID/transform;
Redo restores a complete Residential body, both boards, chosen Material semantics,
schema `>=2`, the same Path and ID, identity transform, and NORMAL diagnosis.
Conversion must occur only through this explicit operation.

## Test 8 — Residential settings Undo/Redo

Use **住宅階段仕様を変更** and change at least two values (for example reveal
40→55 mm and thickness 18→22 mm, or one board OFF and shell thickness). Perform
the mandatory Undo/Redo sequence.

Expected: final values equal the submitted values; unrelated canonical and all
Material pointers remain unchanged. The accepted closed body, flat lower end, and
r7 horizontal-top/vertical-rear upper termination remain intact.

## Test 9 — Material Case A and Undo/Redo

Create Materials `Wood` and `White`. Through **階段部材Materialを変更** set Base
= Wood, Tread = None, Riser = White, Underside = None, Side Board = None. Perform
the mandatory Undo/Redo sequence.

Expected effective roles: Tread Wood, Riser White, Underside Wood, Side Board
Wood. Inspect slots and representative polygon indices in Edit Mode. Both boards
use the Side Board role. No extra substitute datablock is created.

## Test 10 — Material Case B

Set Base = None, Tread = Wood, and every other override None through the UI.

Expected: exactly one Wood slot and one genuinely empty (`None`) slot. Treads use
Wood; Riser, Underside, and Side Board polygons use the empty slot and never borrow
Wood. No substitute Material datablock is generated. Record slot listing and the
set of polygon material indices.

## Test 11 — Material Case C

Set all five Material fields to None through the UI.

Expected: all roles are UNASSIGNED, no unnecessary Material datablock or slot is
created, and geometry/diagnosis remain valid. Record slots and indices.

## Test 12 — Material lifecycle chain

Restore Case A or B and take a canonical/slot/index snapshot. Separately perform
Regenerate, Dimension edit, Reverse, save/full-exit/reopen, `GEOMETRY_MISSING`
Repair, and Finalize (Finalize last on a disposable copy).

Expected after each step: the same five canonical Material pointers, effective
role meaning, slots, and representative role indices. Decide and record each step
individually. Finalize must preserve them exactly.

## Test 13 — Residential Regenerate

On a non-default Residential object run **階段を再生成**.

Expected: same complete canonical snapshot, Stair ID, ordered Path, ascent,
board configuration, Material pointers and role assignments; equivalent accepted
geometry and NORMAL diagnosis. Regenerate is not conversion or migration.

## Test 14 — `GEOMETRY_MISSING` Repair and Undo/Redo

In a saved disposable copy, empty the managed mesh in a controlled manner. Verify
the sole intended issue includes `GEOMETRY_MISSING`, then use **管理状態へ復元**.
Immediately perform mandatory Undo/Redo and inspect afterward.

Expected after Redo: Treads, Risers, corrected continuous closed body, enabled
full-depth boards, slots and polygon role indices restored from valid canonical
state; same Stair ID and canonical data, identity transform, NORMAL diagnosis.

## Test 15 — Duplicate ID Repair and Undo/Redo

Duplicate a managed Residential Stair using ordinary Blender **Shift+D**. Confirm
the source and duplicate initially share an ID and both diagnose `ID_CONFLICT`.
On the duplicate run **管理状態へ復元**, then mandatory Undo/Redo.

Expected after Redo: duplicate has a new nonempty ID; source ID is unchanged;
duplicate Path, Residential fields, Materials, geometry and transform are
otherwise unchanged and NORMAL. Remove/finalize the duplicate and verify the
source conflict clears without rewriting its ID.

## Test 16 — Transform Repair and Undo/Redo

Move, rotate, and non-uniformly scale a disposable Residential object. Confirm
`TRANSFORM_CHANGED`; run **管理状態へ復元**, then mandatory Undo/Redo.

Expected after Redo: location/rotation `(0,0,0)`, scale `(1,1,1)`, original ID,
canonical, Residential fields and Materials preserved, with NORMAL diagnosis.

## Test 17 — Abnormal-state operation gates

On separate disposable objects create `ID_CONFLICT`, `TRANSFORM_CHANGED`,
`INVALID_CANONICAL`, and `GEOMETRY_MISSING`. For each, verify both disabled UI and
direct operator result: normal-only dimension/Path/Reverse/Regenerate/Finalize
must not run. Repair is available only for recoverable states; in particular
`INVALID_CANONICAL` is not Repairable. Delete remains available in every managed
abnormal state. Preserve the main test object.

## Test 18 — Forced prepare failure rollback

Use a short script from Blender's Text Editor (not Console interaction in an Undo
sequence). Snapshot Object/data identities, canonical including mode/schema and
all `ResidentialFields`, Material pointers, slots, Stair ID, and transform. In a
`try/finally`, temporarily replace `stair_operators._prepare_candidate` with a
function that raises a unique exception, invoke a normal transactional JHM
operator, and restore the original helper in `finally`.

Expected: CANCELLED, original mesh identity and every snapshot item unchanged,
no replacement mesh/material leak, and NORMAL after restoration. The helper must
be restored even if an assertion fails; verify its identity before continuing.

## Test 19 — Forced commit failure rollback

From the Text Editor, snapshot the same values. Temporarily patch a commit helper
used only after mesh swap (for example wrap `_set_canonical`) with a fail-once
wrapper: first call raises the unique exception, subsequent calls delegate to the
original so rollback can restore canonical data. Invoke a transactional JHM
operation and restore the helper in `finally`.

Expected: CANCELLED; old `Object.data`, canonical, Materials/slots, ID, location,
rotation and scale restored; no partial Residential state; NORMAL. Verify the
original helper identity was restored. Do not use a permanently failing patch.

## Test 20 — Save, full exit, reopen

Prepare one nontrivial Residential state: oblique Path, REVERSE, nonzero `base_z`,
non-default board setting, and non-default Material assignment. Record a complete
snapshot, save, **fully exit Blender**, restart, and reopen.

Expected without load-time regeneration/migration: identical mode, schema, Path,
ascent, dimensions, `base_z`, every Residential setting, Material pointer, ID,
geometry and identity transform; NORMAL diagnosis. Record before/after evidence.

## Test 21 — Editable Mesh finalization

On a disposable object record Object and Mesh identities, vertex/face coordinates,
Materials/slots/indices, transform, ID, Path and all canonical data. Use
**編集可能Meshとして確定**, optionally mandatory Undo/Redo, then inspect.

Expected: same Object, same Mesh and geometry, Materials, transform, ID/Path/data;
only `is_stair` is False. No regeneration or replacement occurred. Enter ordinary
Blender Edit Mode, move a vertex, and confirm it behaves as an unmanaged mesh.

## Test 22 — Delete normal and abnormal objects

Select a managed Stair plus unrelated objects, making only the Stair active. Use
**階段を削除**, then mandatory Undo/Redo.

Expected after Redo: only the active managed Stair is removed; unrelated selected
objects and their data survive. Undo restores it. Repeat on a disposable abnormal
managed Stair. Confirm the operator does not directly delete Mesh or Material
datablocks and relies on object-level Blender Undo lifecycle.

## Test 23 — Final Build 07-A BASIC regression

Using accepted BASIC fixtures, record separate PASS/FAIL evidence for: two-point
Straight Path and draw order; FORWARD/REVERSE; 2800 mm / 16-riser contract;
oblique Path; invalid edit rollback; missing/conflicting ID diagnosis; transform
diagnosis and Repair; BASIC Material preservation; save/full-exit/reopen;
operator Undo/Redo; Finalize; and active-only Delete. No step may add Residential
body/boards or silently change `BASIC_TREAD_RISER`.

## Test 24 — Wall / Finish focused smoke regression

Open a known-good managed Wall + Finish scene and snapshot Wall geometry, ID and
topology plus Finish ID, spans, geometry, Materials and managed diagnosis. Create
a Stair and separately run dimension edit, Path edit, Reverse, Repair, then
Finalize/Delete on copies.

Expected after each Stair operation: every Wall and Finish snapshot remains
unchanged and normally managed. Capture focused before/after Console evidence;
full 05/06 runtime acceptance need not be repeated.

## Test 25 — Final visual acceptance gate

Inspect BOTH, LEFT-only, RIGHT-only and OFF/OFF board configurations in FORWARD,
REVERSE and an oblique Path, with visibly distinct role Materials. Use solid and
material preview views plus underside, lower-end, upper-end, and side closeups.

The gate passes only when all are visually true:

- continuous `STEPPED_CLOSED` soffit; no exposed Tread/Riser backs or cavity;
- flat first-step bottom, no micro-notch, and clean lower termination;
- accepted r7 upper termination: horizontal top and vertical rear edge, with no
  spike, giant triangle, or diagonal rear plate;
- no geometry below `base_z`, above `H`, or beyond `L+r`;
- no body/board gap or unintended z-fighting;
- full-depth external Side Boards in every enabled combination;
- correct directional/oblique behavior and visible Material-role distinction.

Topology alone cannot pass this gate. Any visually implausible residential Stair
is FAIL. Retain a labelled screenshot set for the Stage 4 acceptance review.

## Completion record

After Test 25, tabulate Test 0–25 with PASS/FAIL and evidence filenames. Record
Blender version, Candidate identity, any traceback, and all deviations. Do not
mark `BUILD_07_B_ACCEPTANCE_RECORD.md`, ROADMAP, or Build 07-B overall accepted in
this procedure; that is a separate post-runtime acceptance step.
