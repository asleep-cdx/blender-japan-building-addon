# Build 07-A Acceptance Record

## Final acceptance status

- **Build 07-A Stage 1 — Canonical Stair + 2-point creation: ACCEPTED**
- **Build 07-A Stage 2 — Layout calculation + basic geometry: ACCEPTED**
- **Build 07-A Stage 3 — Editing + regeneration + rollback: ACCEPTED**
- **Build 07-A Stage 4 — Lifecycle / Mesh exit / regression: ACCEPTED**
- **Build 07-A overall: ACCEPTED**

Build 07-A passed its automated regression gates and Blender 5.2 LTS runtime
acceptance. Build 07-B is NEXT; it is not started or accepted by this record.

## Runtime-tested final production revision and artifact

- GitHub PR: `#14 — Implement Build 07-A Stage 4 lifecycle and mesh exit`
- Runtime-tested production commit: `d9ef1c7feb4b9a308164bd1b47b6bfccb7680555`
- Runtime-tested production tree: `6539a90d92ecccfc3d5bf2ae31858e4bda41c261`
- Runtime Candidate: `Japanese_House_Modeler_Build_07_A_Stage4_Candidate_r1.zip`
- Runtime environment: `Blender 5.2 LTS`
- Add-on version: `(0, 7, 0)`
- Description: `Build 07-A: Stair Core + Top-view 2-point Straight Stair`

This Acceptance Record update changes documentation only. Its commit and tree
are not a new runtime-tested production revision. The accepted Build 07-A
production behavior remains the exact production commit and tree above.

## Automated evidence

The runtime-tested production tree had these results:

| Check | Result |
|---|---:|
| `python -B -m unittest tests.test_build_07_a_stage1` | **22 tests PASS** |
| `python -B -m unittest tests.test_build_07_a_stage2` | **17 tests PASS** |
| `python -B -m unittest tests.test_build_07_a_stage3` | **31 tests PASS** |
| `python -B -m unittest tests.test_build_07_a_stage4` | **14 tests PASS** |
| `python -B -m unittest discover -s tests` | **447 tests PASS** |
| `python -m compileall -q japanese_house_modeler tests` | **PASS** |
| `git diff --check` | **PASS** |
| Working tree | **clean** |

Automated evidence is separate from, and was not substituted for, Blender
runtime evidence.

## Earlier accepted-stage baselines

- Stage 1: commit `b6c82e80906a9404288c759bcc0650ba07d3526e`, tree
  `471027e9071e78d94ef872b65f780d998a37e291`, Candidate r1.
- Stage 2: commit `cbca65810d0b9fdbc7636005607c36f9af9c1b0e`, tree
  `cbb61de6e2d8528288bafdad33c260895eaadd6b`, Candidate r1.
- Stage 3: commit `cbb87af801ffa65655dd3be11fd8a3acfb809408`, tree
  `233afeb837a590e1a3ef5a2605a611e505aafa14`, Candidate r3.

The final Build 07-A production revision includes these accepted stages without
changing their acceptance history.

## Stage 4 Blender 5.2 LTS runtime acceptance

| Test | Runtime gate | Result | Evidence |
|---:|---|---|---|
| 0 | Operator / metadata gate | **PASS** | Add-on enabled; `jhm.convert_stair_mesh` and `jhm.delete_stair` registered; version and description matched. |
| 1 | NORMAL Stair finalization | **PASS** | Same Object, name, Mesh, geometry, Material state, and Transform; `is_stair` True→False; ID and Path retained; MESH and Edit Mode worked; managed UI disappeared. |
| 2 | Finalize Undo / Redo | **PASS** | Undo restored the managed UI and Redo removed it again. Final state was unmanaged MESH, 248 vertices / 186 faces, identity Transform. |
| 3 | Finalize with Material | **PASS** | `Stage4 Finalize Material`, its single slot/datablock, Object, Mesh, ID, Path, and 248 / 186 geometry were preserved. |
| 4 | Abnormal FINALIZE rejection | **PASS** | TRANSFORM_CHANGED disabled Finalize but enabled Delete. Direct conversion returned CANCELLED with the expected warning and no mutation. |
| 5 | Active-only Delete | **PASS** | With Stair and Cube selected, only the active Stair was deleted; the Cube remained present and selected. |
| 6 | Delete Undo / Redo | **PASS** | Delete removed the Stair, Undo restored it, Redo removed it, and Undo restored it again with management, ID, Path, dimensions, geometry, and type preserved. |
| 7 | Delete TRANSFORM_CHANGED | **PASS** | A Managed Stair moved +5 m was deleted without Repair. |
| 8 | Delete OBJECT_TYPE_CHANGED | **PASS** | Managed CURVE diagnosed OBJECT_TYPE_CHANGED; edit, Repair, and Finalize were disabled; Delete removed only the target. |
| 9 | ID_CONFLICT lifecycle | **PASS** | Shift+D conflicted both UUIDs. Deleting the duplicate left the original UUID unchanged and naturally returned the survivor to NORMAL. |
| 10 | Finalized Mesh exclusion | **PASS** | With `is_stair=False`, Delete poll returned False and Object/Mesh remained. Direct invocation produced expected poll rejection. |
| 11 | Save / full exit / reopen | **PASS** | Finalized MESH remained unmanaged with geometry preserved. Managed Stair retained ID, Path, ascent, dimensions, geometry, identity Transform, and NORMAL state. |
| 12 | Finalized Mesh editing | **PASS** | Manual vertex editing persisted without JHM regeneration, canonical reverse inference, or management restoration. |
| 13 | Geometry health | **PASS** | 248 vertices, 372 edges, 186 faces, finite coordinates, zero non-manifold edges, and zero zero-area faces. |
| 14 | Delete Undo with Material | **PASS** | Undo restored management, ID, Path, one Material slot, the same Material datablock/name, and 248 / 186 geometry. |
| 15 | Final numeric contract | **PASS** | P0=(0,0), P1=(3.6,0) m FORWARD: UI run 3600.0 mm, riser 175.0 mm, 15 Treads, UI going 240.0 mm, arrival 2800 mm, 248 / 186 geometry, identity Transform, NORMAL. |
| 16 | Ascent reversal regression | **PASS** | FORWARD→REVERSE kept ID and Path order; lower=(3.6,0), upper=(0,0), run 3600 mm, arrival 2800 mm, 248 / 186 geometry, NORMAL. |
| 17 | Repair regression | **PASS** | Repair of a REVERSE Stair moved +5 m retained ID, Path, and ascent; restored identity and 248 / 186 geometry; returned to NORMAL. |

The numeric contract's internal values of approximately 3599.999905 mm run and
239.999994 mm going are normal Blender `FloatVectorProperty` precision. The UI
and resolved contracts were correct.

For Save / reopen, `Stage4 Save Managed` retained UUID
`61962c28-f327-4342-88f3-fb4dc19b146c`, Path
`((-27.650967,-5.425912),(-27.247265,3.232788))`, FORWARD ascent, base Z 0 mm,
floor-to-floor 2800 mm, 16 risers, width 900 mm, tread/riser thickness 30/12
mm, 248 / 186 geometry, identity Transform, and NORMAL state.
`Stage4 Save Finalized` remained an unmanaged MESH with 248 / 186 geometry.

## Runtime test-command notes

The following corrected verification-command issues are not product defects:

- `stair_issues` was initially not imported in one Console session.
- Invalid Blender collection membership syntax was corrected to
  `Scene.objects.get(...)`.
- Reading a deleted RNA reference produced the expected `ReferenceError`;
  verification was corrected to use the retained UUID.
- Direct managed Delete on an unmanaged finalized Object produced Blender's
  expected poll `RuntimeError`; explicit `poll()` returned False.

## Final accepted scope

Accepted scope includes canonical standalone two-point Stair creation and
geometry; Stage 3 editing, reversal, rollback, diagnosis, and Repair;
NORMAL-only in-place `jhm.convert_stair_mesh`; Object/Mesh/geometry/Material/
Transform/canonical preservation; management exit and free Mesh editing;
finalize Undo/Redo and abnormal refusal; active-only `jhm.delete_stair` from
normal and abnormal states; OBJECT_TYPE_CHANGED and ID_CONFLICT deletion;
delete Undo/Redo and Material restoration; finalized Mesh exclusion; Managed
and finalized Save/reopen; geometry health; numeric contracts; and full
Stage 1–4/prior-Build regression.

Build 07-A does not add stepped/sloped underside, Side Boards, nosing,
overhang, bevel/round, groove, part-specific Materials, Landing, Winder,
Multi-point Stair, Open/Support variants, or Floor/Room/Wall connections.

## Acceptance conclusion

**Build 07-A Stage 1: ACCEPTED**

**Build 07-A Stage 2: ACCEPTED**

**Build 07-A Stage 3: ACCEPTED**

**Build 07-A Stage 4: ACCEPTED**

**Build 07-A overall: ACCEPTED**

The runtime-tested final production revision remains
`d9ef1c7feb4b9a308164bd1b47b6bfccb7680555`, with production tree
`6539a90d92ecccfc3d5bf2ae31858e4bda41c261`.

Next: **Build 07-B — Standard Residential Straight Stair + Stepped Closed
Underside + Side Boards: NEXT**. This documentation-only commit is not a new
runtime-tested production revision.
