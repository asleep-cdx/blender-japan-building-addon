# BUILD 07-D ACCEPTANCE RECORD
## Japanese House Modeler — Multi-point Path + L / U + Landing

Date: 2026-09-29

## 1. Status

- Build 07-D Stage 1 — **ACCEPTED**
- Build 07-D Stage 2 — **ACCEPTED**
- Build 07-D Stage 3 — **ACCEPTED**
- Build 07-D Stage 4 — **ACCEPTED**
- Build 07-D overall — **ACCEPTED**

Stage 1 established the schema-4 Multi-point foundation and first visible 3-point L Stair. Stage 2 completed the 3-point L editing / guide / distribution / Residential integration scope. Stage 3 completed the 4-point U / multi-flight production, editing, allocation, Residential turn ownership, material, persistence, and rollback scope. Stage 4 closed the lifecycle, legacy-regression, repair, persistence, Finalize/Delete, Wall/Finish isolation, practical-placement, and final-topology gates without requiring any production Python change.

Implementation authority remains `BUILD_07_D_SPECIFICATION.md`. This record is authoritative for Build 07-D acceptance status. Winder / 廻り段 remains Build 07-E scope.

## 2. Stage 1 accepted baseline

GitHub PR: #27

Exact runtime-tested Stage-1 production revision:

```text
commit 6d24ef67bcad965c06fd9ce9a06ec91fb7a77b0c
tree   fbdd1a7b90fd7c6ea7032cee457dc56e2e364057
```

Runtime Candidate:

```text
Japanese_House_Modeler_Build_07_D_Stage1_Candidate_r1.zip
SIZE    125181 bytes
SHA256  05e012fdf3e1a043275b1d000f6eff9f0ced9f54e71c1dcef5985a87332c7215
```

Stage-1 acceptance established schema 4 for explicit Multi-point Stair state, persistent P0/P1/P2 point IDs, strict canonical 90-degree L validation, creation-time exact-90 projection, AUTO physical Flight allocation, one Managed Stair = one Mesh Object, identity Object Transform, Landing=TREAD material role, Reverse without canonical Path reorder, prepare-before-mutation rollback, and schema-1/2/3 Straight isolation. Those accepted contracts remain in force.

## 3. Stage 2 runtime-tested revision and artifact

GitHub PR: #28

Exact runtime-tested Stage-2 production revision:

```text
commit b4869816da1b6d1d92033b4994e9bdbbf55b08a2
tree   871d7bd4971c5433e4d7bec8c7b8af06e716d03d
```

Runtime Candidate:

```text
Japanese_House_Modeler_Build_07_D_Stage2_Candidate_r19.zip
SIZE    138267 bytes
SHA256  85fefa1c0a20d1eddf968bc2d59ac874098307060aa9fcaf852e49c6def46c13
```

Runtime environment:

```text
Blender 5.2.0 LTS
Add-on version: (0, 7, 3)
Description: Build 07-D: Multi-point Path + L/U + Landing
```

Documentation / acceptance commits created after runtime review do not supersede the exact runtime-tested production revision above. Accepted runtime archives must be derived from the recorded tested revision when exact runtime identity is required.

## 4. Stage 2 automated evidence

Final r19 implementation report:

```text
python -m unittest tests.test_build_07_d_stage2                         60 PASS
python -m unittest tests.test_build_07_d_stage1 tests.test_build_07_d_stage2  87 PASS
07-A targeted suites                                                   84 PASS
07-B targeted suites                                                   98 PASS
07-C targeted suites                                                   90 PASS
python -m unittest discover -s tests                                  722 PASS
python -m compileall -q japanese_house_modeler tests                  PASS
git diff --check                                                       PASS
git status --short --branch                                           clean
```

The final Stage-2 automated set covers guide math, numeric and modal point editing, AUTO / MANUAL allocation lifecycle, invalid MANUAL atomic cancellation, Residential L geometry, Side Board ownership, SLOPED_CLOSED turn geometry, LEFT / RIGHT chirality, FORWARD / REVERSE behavior, topology validation, material-role continuity, accepted 07-C Straight regression, and preservation of the Stage-1 foundation.

## 5. Stage 2 accepted contracts

Stage 2 accepts the following production behavior in addition to the Stage-1 contracts:

### Path editing and guides

- schema-4 3-point L Path remains `P0 = START`, `P1 = TURN`, `P2 = END`.
- START / TURN / END mouse relocation is available through the Stage-2 path-point operators.
- numeric editing of all three Path points is available and validates the canonical exact-90-degree L relationship before Scene mutation.
- guide math provides the Stage-2 X/Y, right-angle, parallel / extension and 15-degree constraint foundation defined by the specification.
- invalid candidate moves are rejected without leaving partial managed geometry.
- ordinary Path edits preserve stable point identity rather than replacing the canonical Path with unrelated points.

### Riser distribution

- `AUTO` remains the default distribution mode.
- `MANUAL` is supported for the two physical Flights.
- AUTO -> MANUAL inherits the current valid physical allocation.
- MANUAL allocations must sum to the overall riser count and each physical Flight must satisfy the minimum-riser contract.
- invalid MANUAL values are rejected atomically through normal Blender operator cancellation; they do not mutate mode, saved allocation, Path, material pointers, transform, or Mesh geometry.
- validated MANUAL edits regenerate geometry and persist as physical Flight allocation.
- MANUAL -> AUTO invalidates stale manual authority and allows normal AUTO recomputation.

### Residential L geometry

- one Managed Stair remains one Mesh Object with identity transform in normal managed state.
- Landing remains `TREAD`; no separate `LANDING` material role is introduced.
- TREAD / RISER / UNDERBODY / SIDE_BOARD material-role mapping is preserved.
- LEFT and RIGHT turns use mirrored local rules rather than separate world-space special cases.
- FORWARD / REVERSE preserve canonical Path order and physical geometry ownership while changing ascent traversal.
- STEPPED_CLOSED remains on its accepted stepped-underbody production path.
- SLOPED_CLOSED uses the accepted Lower sloped UNDERBODY, horizontal Landing turn region, and Upper sloped UNDERBODY connection with the final r19 Landing perimeter closure.
- the final SLOPED_CLOSED Landing body closes the two externally exposed Landing perimeter edges up to the Landing TREAD underside while preserving a hollow centre rather than replacing the Landing with one giant solid block.
- Flight connection edges do not receive duplicate full-width closure walls.
- Lower and Upper Flight slope authorities remain unchanged by the Landing closure.

### Accepted Side Board corrections from the runtime correction series

- r14: Lower Flight outer terminal locally reaches the accepted body terminal rather than stopping one riser-thickness early.
- r16: Upper Flight outer Landing-side reveal is restored only on the exterior-continuing board; the nearby inner corner retains the accepted `x = 0` return rather than projecting backward.
- r17: Lower Flight inner Landing-side terminal receives only the narrow local terminal tail required to cover the remaining exposed UNDERBODY strip.
- those local Side Board corrections do not redesign the accepted r13 SLOPED_CLOSED Flight underside.
- STEPPED and SLOPED Side Board profile families remain supported.
- disabling an individual Side Board does not synthesize an unrelated replacement board.

### Lifecycle and isolation

- Material pointers and Mesh material slots survive accepted regeneration / Reverse / save / reopen workflows.
- canonical Path order, point IDs and physical riser allocation persist across save -> complete Blender exit -> reopen.
- accepted Straight schema-1/2/3 behavior remains isolated from schema-4 Stage-2 state.
- Repair / Regenerate do not silently rewrite valid canonical Path or point identity.

## 6. Stage 2 Blender 5.2 LTS runtime acceptance

All Stage-2 runtime test areas were completed and accepted on the r19 production revision.

### Test 0 — Candidate identity / regression — PASS

The Stage-2 Candidate loaded as Build 07-D `(0,7,3)` and accepted schema-3 Straight behavior remained available without schema-4 state leakage.

### Test 1 — rotated creation and guide behavior — PASS

3-point L creation and Stage-2 guide display / constraint behavior were exercised in Blender. Canonical L geometry remained exact and managed-state identity remained valid.

### Test 2 — START / TURN / END relocation and Undo / Redo — PASS

All three path-point relocation modes were exercised. Undo / Redo was tested in strict UI-operation -> Ctrl+Z -> Ctrl+Shift+Z order and restored the managed result correctly.

### Test 3 — numeric Path / AUTO — PASS

Numeric P0/P1/P2 editing and AUTO reallocation were exercised. Valid edits regenerated the Stair; invalid geometry was rejected without partial mutation.

### Test 4 — distribution lifecycle — PASS

AUTO -> MANUAL, valid MANUAL allocation, MANUAL -> AUTO, persistence and physical allocation semantics were exercised.

The r18 correction was runtime-verified specifically for invalid MANUAL edits. Invalid `8,7` and `2,15` edits produced a normal error report and left the pre-operation canonical state and Mesh unchanged. A valid `7,9` edit succeeded and changed only the expected MANUAL allocation / generated geometry state.

### Test 5 — Residential L visual review — PASS

Representative STEPPED_CLOSED / SLOPED_CLOSED and STEPPED / SLOPED Side Board combinations were reviewed, including opposite turn orientation and ascent reversal.

The accepted result includes the r13-r17 geometry corrections and the r19 SLOPED_CLOSED Landing closure. Final body-only inspection confirmed that the previously open Landing perimeter region is closed. Re-enabling Side Boards preserved the accepted local terminal / reveal corrections.

The user noted that some resulting internal mesh construction is not the preferred ideal hand-modelled topology, but accepted the produced exterior / working geometry for Stage 2.

### Test 6 — material and lifecycle — PASS

Material pointers / slots, Reverse, save / full exit / reopen and regeneration were exercised. Materials did not move between roles or disappear, and the saved canonical Stair state remained usable after reopen.

### Test 7 — rollback / isolation / final review — PASS

Invalid MANUAL distribution rollback was confirmed at the operator boundary with no state mutation. Existing accepted Straight behavior remained isolated. Final visual review confirmed the Stage-2 L geometry after the correction series.

A passive Wall alignment snap was not claimed as a successful snap-to-arbitrary-wall runtime result: the current Stage-2 L Stair is constrained to its canonical 90-degree geometry, so an arbitrary wall not lying on the valid Stair extension is intentionally not a valid snap target. The guide / candidate foundation remains present for future compatible geometry cases.

## 7. Stage 2 intentionally deferred scope

Stage 2 did **not** claim completion of 4-point U production, general multi-turn production, Stage-3/4 completion, or Winder geometry. Those items were handled by later Stage 3 / Stage 4 work or remain Build 07-E scope.

## 8. Stage 2 acceptance conclusion

Build 07-D Stage 1 — **ACCEPTED**.

Build 07-D Stage 2 — **ACCEPTED** at:

```text
commit b4869816da1b6d1d92033b4994e9bdbbf55b08a2
tree   871d7bd4971c5433e4d7bec8c7b8af06e716d03d
```

Accepted Stage-2 Candidate:

```text
Japanese_House_Modeler_Build_07_D_Stage2_Candidate_r19.zip
SIZE    138267 bytes
SHA256  85fefa1c0a20d1eddf968bc2d59ac874098307060aa9fcaf852e49c6def46c13
```

## 9. Stage 3 runtime-tested revision and artifact

GitHub PR: #29

Exact runtime-tested Stage-3 production revision:

```text
commit ec41d3e5b4c1730f24fb22000762ab2975978afd
tree   b2c1f3d813ed51cd59028a3d5217c3ce7c4c81c6
```

Runtime Candidate:

```text
Japanese_House_Modeler_Build_07_D_Stage3_Candidate_r4.zip
SIZE    143226 bytes
SHA256  d6c454a06d97554b9e5d6b306e06896fafa9fd3b2a5572cb6994bb922c6a0c06
```

Runtime environment:

```text
Blender 5.2 LTS
Add-on version: (0, 7, 3)
Description: Build 07-D: Multi-point Path + L/U + Landing
```

Documentation / acceptance commits created after runtime review do not supersede the exact runtime-tested production revision above.

## 10. Stage 3 automated evidence

Final implementation report:

```text
python -m unittest tests.test_build_07_d_stage3   13 PASS
Stage-1 / Stage-2 / Stage-3 combined suites      PASS
python -m unittest discover -s tests             PASS
python -m compileall -q japanese_house_modeler tests   PASS
git diff --check                                  PASS
```

## 11. Stage 3 accepted contracts

### Canonical U / multi-flight foundation

- explicit 4-point U creation persists schema-4 `P0/P1/P2/P3` with stable unique point IDs.
- a 4-point U resolves three physical Flights and two Landings.
- orthogonal canonical validation extends beyond the Stage-2 3-point L and rejects non-adjacent self-intersection / overlap.
- one Managed Stair remains one Mesh Object with identity Object Transform.
- mirrored and rotated U plans preserve canonical identity and local turn semantics.

### Relocation and guides

- START and END each expose one persistent cyan endpoint ray in the current valid endpoint direction.
- START / END candidate semantics and Shift-compatible endpoint candidate handling work on ordinary, rotated and mirrored U plans.
- Turn 1 / Turn 2 target P1 / P2 separately.
- when fixed neighboring points over-constrain an interior Turn, the move is rejected atomically without moving another point.
- valid endpoint moves remain one Undo step; strict UI operation -> Ctrl+Z -> Ctrl+Shift+Z -> Console verification passed.
- ESC, RMB and invalid operations preserve canonical points / IDs, allocation, Mesh, Materials, Stair ID and identity Transform.

### Three-Flight allocation

- AUTO produces deterministic physical allocation across three Flights, each satisfying the minimum-riser contract and summing exactly to the overall riser count.
- MANUAL accepts three explicit Flight counts.
- wrong total, below-two allocation and geometry made invalid by Path edits are rejected without mutation.
- MANUAL -> AUTO returns authority to the valid AUTO allocation.

### Multi-turn Residential geometry

- each physical Flight has one underbody owner; the middle physical Flight is not duplicated at either Turn.
- each Landing has its own underbody / closure ownership.
- SLOPED_CLOSED body-only U geometry preserves separate Landing soffits and a single constant-pitch middle Flight body rather than a global turn-to-turn wedge or repair box.
- STEPPED_CLOSED closes both Turn transitions without duplicate transition bodies.
- STEPPED and SLOPED Side Board profiles resolve through both turns with local chirality and ownership.
- mirrored and REVERSE variants do not retain stale FORWARD / opposite-side Side Board geometry.
- representative reveal / riser-thickness coverage was exercised across a 72-case pure geometry sweep.

### Reverse, materials and lifecycle

- Reverse changes traversal without canonical Path reorder or physical allocation rewrite.
- both Landing elevations recompute from the current uphill traversal.
- only the final uphill Flight owns final-arrival semantics.
- all five canonical Material pointers and effective Mesh slots remain stable across Reverse.
- save -> complete Blender exit -> reopen preserves canonical state, point IDs/order, distribution state, dimensions, Residential settings, Materials, Stair ID, Mesh result and identity Transform.
- repeated Regenerate is deterministic for the accepted runtime state.
- invalid final edits are rejected atomically while preserving the same Mesh datablock pointer and full pre-operation state.

## 12. Stage 3 Blender 5.2 LTS runtime acceptance

All eight grouped Stage-3 runtime tests passed on Candidate r4.

### Test 0 — identity and regressions — PASS

Accepted 07-C Straight and accepted Stage-2 3-point L behavior remained available under the Stage-3 package.

### Test 1 — four-click U — PASS

4-point U creation, schema-4 point identity, three Flights / two Landings, mirrored U, and rotated U creation / guide behavior were exercised successfully.

### Test 2 — AUTO and elevations — PASS

A 16-riser unequal-run U resolved deterministic 3-Flight allocation with every Flight at least two risers, exact total 16, exact floor-to-floor arrival, and cumulative Landing elevations.

### Test 3 — relocation and Undo / Redo — PASS

START and END endpoint relocation, Shift candidate behavior, valid moves, strict Undo / Redo, ESC / RMB cancel, rotated U and mirrored U passed. Turn 1 / Turn 2 mapped to P1 / P2 and rejected the over-constrained exact-90-degree move atomically. Invalid/cancel paths preserved canonical data and generated state.

### Test 4 — MANUAL rollback — PASS

AUTO -> MANUAL `6,3,7` persisted exactly. Wrong-total MANUAL input, below-two backend validation, and a too-short middle Flight were rejected without state mutation.

```text
T4 ROLLBACK = True
```

### Test 5 — Residential U geometry — PASS

Normal and mirrored SLOPED_CLOSED body-only U geometry passed Console ownership and visual review. STEPPED / SLOPED Side Boards, mirrored / REVERSE variants, and STEPPED_CLOSED boards OFF / ON were reviewed without observed large gap, hole, spike, sliver, duplicated physical middle Flight, duplicate transition body, or stale opposite-direction Side Board.

Pure geometry sweep:

```text
2 routes (normal / mirrored)
× 2 directions (FORWARD / REVERSE)
× 2 Side Board modes (STEPPED / SLOPED)
× 3 reveals (20 / 40 / 60 mm)
× 3 riser thicknesses (8 / 12 / 18 mm)
= 72 / 72 PASS
```

### Test 6 — Reverse and materials — PASS

All five Material roles were populated. REVERSE -> FORWARD -> REVERSE preserved Path, IDs, allocation, Stair ID, Material pointers, Mesh slots and identity Transform while traversal and Landing elevations recomputed correctly.

Representative evidence:

```text
FORWARD TRAV=[0,1,2] LANDING_Z=[1.05,1.575] FINAL_UPHILL=2
REVERSE TRAV=[2,1,0] LANDING_Z=[1.75,1.225] FINAL_UPHILL=0
T6 FINAL: PTS=True IDS=True ALLOC=True STAIR_ID=True MATS=True SLOTS=True XFORM=True
```

### Test 7 — persistence, regeneration, isolation — PASS

```text
T7 REOPEN = True DIFF = []
T7 REGEN: MESH=True STATE=True
T7 INVALID ROLLBACK=True MESH_PTR=True DIFF=[]
```

The invalid edit produced a normal validation message, no traceback, no visible shape mutation, and preserved the exact existing Mesh datablock pointer.

## 13. Stage 3 intentionally deferred scope

Stage 3 did **not** claim final Stage-4 lifecycle / full-regression / practical-placement acceptance or Build 07-D overall acceptance. Winder / 廻り段 remained Build 07-E scope.

## 14. Stage 3 acceptance conclusion

Build 07-D Stage 1 — **ACCEPTED**.

Build 07-D Stage 2 — **ACCEPTED**.

Build 07-D Stage 3 — **ACCEPTED** at:

```text
commit ec41d3e5b4c1730f24fb22000762ab2975978afd
tree   b2c1f3d813ed51cd59028a3d5217c3ce7c4c81c6
```

Accepted Stage-3 Candidate:

```text
Japanese_House_Modeler_Build_07_D_Stage3_Candidate_r4.zip
SIZE    143226 bytes
SHA256  d6c454a06d97554b9e5d6b306e06896fafa9fd3b2a5572cb6994bb922c6a0c06
```

## 15. Stage 4 runtime-tested revision and artifact

GitHub PR: #30

Exact runtime-tested Stage-4 revision:

```text
commit 6c8cd05e7a854a28c1396a26b4282bb6ecbc052b
tree   f4c7b338560b688577314d297e422bd248e6554f
```

Runtime Candidate:

```text
Japanese_House_Modeler_Build_07_D_Stage4_Candidate_r1.zip
SIZE    143226 bytes
SHA256  58af371ded07b33ef1ec3f465fdde2e52ebaec9d88be7f0e8eea2f8802fcbed3
```

Runtime environment:

```text
Blender 5.2.0 LTS
Add-on version: (0, 7, 3)
Description: Build 07-D: Multi-point Path + L/U + Landing
```

Stage 4 changed automated tests and runtime documentation only; production Python was not changed. The add-on production code is therefore the already accepted Stage-3 production implementation. The exact Stage-4 Candidate above is nevertheless the runtime-tested package identity for the final lifecycle/regression acceptance pass.

Acceptance/documentation commits created after the Blender runtime review do not supersede the exact Stage-4 runtime-tested revision above.

## 16. Stage 4 automated evidence

Codex Stage-4 implementation report recorded:

```text
python -m unittest tests.test_build_07_d_stage4                                      14 PASS
python -m unittest tests.test_build_07_d_stage1 tests.test_build_07_d_stage2 tests.test_build_07_d_stage3 tests.test_build_07_d_stage4   131 PASS
07-A targeted suites                                                                 84 PASS
07-B targeted suites                                                                 98 PASS
07-C targeted suites                                                                 90 PASS
python -m unittest discover -s tests                                                 766 PASS
python -m compileall -q japanese_house_modeler tests                                 PASS
git diff --check                                                                      PASS
git status --short --branch                                                          clean
```

Codex local final revision after the runtime-document wording correction was:

```text
commit 581ca0fd4e9ee17a601c2d6c9cf302551aab3193
tree   f4c7b338560b688577314d297e422bd248e6554f
```

GitHub PR head and Codex local commit SHA differ, but the tree SHA is identical; repository contents are therefore the same for acceptance purposes.

The Stage-4 automated suite covers schema-1/2/3 compatibility without implicit upgrades, schema-4 L/U persistence foundations, repair policy for `GEOMETRY_MISSING`, `TRANSFORM_CHANGED`, `ID_MISSING`, and `ID_CONFLICT`, duplicate-ID isolation, deterministic geometry, representative topology checks, Finalize/Delete contracts, and Wall/Finish isolation.

## 17. Stage 4 Blender 5.2 LTS runtime acceptance

All fifteen grouped Stage-4 runtime tests passed on Candidate r1.

### Test 1 — Candidate identity / baseline — PASS

```text
VERSION=(0,7,3)
DESCRIPTION=Build 07-D: Multi-point Path + L/U + Landing
BLENDER=(5,2,0)
```

Straight / L / U creation entry points were visible in the Stair UI.

### Test 2 — schema-1 BASIC Straight regression — PASS

A schema-1 `BASIC_TREAD_RISER` Straight fixture survived save -> complete Blender exit -> reopen and Regenerate without implicit upgrade or geometry change.

```text
STATE=True
MESH=True
SCHEMA=1
MODE=BASIC_TREAD_RISER
FINITE=True
ZERO=[]
```

### Test 3 — schema-2 07-B Straight regression — PASS

A legacy schema-2 `STANDARD_RESIDENTIAL` Straight fixture remained schema 2 after Regenerate and no-op material lifecycle operations.

```text
STATE=True
MESH=True
SCHEMA=2
MODE=STANDARD_RESIDENTIAL
FINITE=True
ZERO=[]
```

The current UI's Residential Apply path creates schema 3, so the legacy schema-2 fixture was intentionally established as legacy state before regression testing; the test validated that current 07-D ordinary handling does not silently upgrade it.

### Test 4 — schema-3 07-C Straight regression — PASS

SLOPED_CLOSED and STEPPED_CLOSED schema-3 Straight cases both survived Reverse round-trip and Regenerate with deterministic state and geometry.

```text
STATE=True
MESH=True
SCHEMA=3
FINITE=True
ZERO=[]
```

Both underside variants were visually accepted.

### Test 5 — schema-4 L / U persistence — PASS

L and U were saved, Blender was fully exited, and the same `.blend` reopened. Both retained schema, Stair ID, Path coordinates, persistent point IDs, direction, Turn/distribution state, allocation, identity transform, and mesh counts.

```text
T5 REOPEN: L=True U=True
T5 MANAGED: [('T5_L','MESH',True),('T5_U','MESH',True)]
```

L/U visual appearance and Landings remained intact.

### Test 6 — AUTO / MANUAL persistence — PASS

L remained AUTO `8,8`; U remained MANUAL `6,5,5` through save -> full exit -> reopen and subsequent Regenerate.

```text
T6 REOPEN: L=True U=True
T6 REGEN: L=True U=True
T6 FINAL: AUTO 8,8 | MANUAL 6,5,5
```

### Test 7 — Undo / Redo representative lifecycle — PASS

Path endpoint move, Reverse, and Material change each passed the required UI operation -> Ctrl+Z -> Ctrl+Shift+Z -> Console sequence.

Representative evidence:

```text
T7A RESULT: PATH_CHANGED=True IDS=True STAIR_ID=True DIR=True XFORM=True
T7B RESULT: DIR_CHANGED=True PATH=True IDS=True STAIR_ID=True
T7C RESULT: TREAD=T7_MAT XFORM=((0,0,0),(0,0,0),(1,1,1))
```

### Test 8 — invalid edit full rollback — PASS

Wrong MANUAL total, too-short Flight, and non-90-degree Landing Turn were all rejected with no canonical/material/transform/mesh mutation.

```text
T8A MANUAL ROLLBACK=True
T8B SHORT FLIGHT ROLLBACK=True
T8C NON90 ROLLBACK=True
```

Runtime validation messages included `Landing cutback後のFlight長が不足しています。` and `Landingは正確な90度Turnのみ対応します。`.

### Test 9 — Geometry / Transform Repair — PASS

Intentional empty geometry diagnosed `GEOMETRY_MISSING` and repaired back to the exact previous canonical and mesh result. Intentional Object translation diagnosed `TRANSFORM_CHANGED` and repaired to identity.

```text
T9G RESULT: CANONICAL=True MESH=True ISSUES=() FINITE=True ZERO=[]
T9T RESULT: CANONICAL=True MESH=True XFORM=((0,0,0),(0,0,0),(1,1,1)) ISSUES=() FINITE=True ZERO=[]
```

### Test 10 — duplicate Stair ID diagnosis / Repair — PASS

A/B were intentionally given the same Stair ID. Both diagnosed `ID_CONFLICT`; C remained healthy. Repairing active B assigned a new ID only to B.

```text
UNIQUE=True
B_NEW_ID=True
A_UNCHANGED=True
B_CANONICAL=True
B_MESH=True
C_UNCHANGED=True
T10 ISSUES FINAL: () () ()
```

### Test 11 — Material lifecycle / repeated Regenerate — PASS

Distinct TREAD / RISER / UNDERSIDE / SIDE_BOARD Materials were assigned to L/U. Regenerate x3, Reverse round-trip, save -> full exit -> reopen all preserved canonical Material pointers, effective slots, canonical state, mesh hash, and topology.

```text
T11 REGEN3: L=True U=True
T11 REVERSE ROUNDTRIP: L=True U=True
T11 REOPEN: L=True U=True
FINITE=True ZERO=[] BOUNDARY=0 NONMANIFOLD=0
```

No z-fighting or duplicate body was observed.

### Test 12 — Finalize transition — PASS

A schema-4 U was finalized to an ordinary editable Blender Mesh.

```text
TYPE=MESH
MANAGED=False
MESH_SAME=True
COUNTS=(656,732)
XFORM=identity
```

Managed Stair UI disappeared, Edit Mode remained available, and appearance did not change.

### Test 13 — active-only Delete / abnormal Delete — PASS

With multiple Stair/Wall/Finish/Mesh objects selected, Delete Stair removed only the active managed Stair. Wall, Finish, other Stair, and finalized Mesh remained unchanged. A second managed Stair with intentionally missing geometry could also be deleted normally.

```text
T13A RESULT: A_DELETED=True B_REMAINS=True MESH_REMAINS=True WALL_REMAINS=True FINISH_REMAINS=True
T13A HOLD: B_ID=True WALL_ID=True FINISH_ID=True FINAL_MESH=True
T13B BROKEN: 0 0 ('GEOMETRY_MISSING',)
T13B RESULT: B_DELETED=True FINAL_MESH=True WALL=True FINISH=True
```

### Test 14 — Wall / Finish isolation + practical placement — PASS

L/U Stair were placed with a simple floor-like Mesh and accepted managed Wall / Finish objects. Stair-only Regenerate, Reverse, Transform Repair, Finalize, and Delete did not mutate Wall / Finish property snapshots, transform, or evaluated geometry.

```text
T14 REPAIR BEFORE: (1,0,0) ('TRANSFORM_CHANGED',)
T14 REPAIR AFTER: identity ()
T14 FINALIZE: MESH False 644 738
T14 DELETE: U_DELETED=True L_FINALIZED=True
T14 ISOLATION: WALL=True FINISH=True
T14 REVERSE: FORWARD -> REVERSE CHANGED=True
T14 REVERSE ISOLATION: WALL=True FINISH=True
```

Visual review accepted practical floor/wall placement, finalized L appearance, and unchanged Wall / Finish geometry.

### Test 15 — final topology / visual inspection — PASS

Six representative final combinations were tested:

```text
1. Straight / FORWARD / STEPPED_CLOSED / Boards OFF
2. Straight / REVERSE / SLOPED_CLOSED / Boards SLOPED
3. L / FORWARD / STEPPED_CLOSED / Boards STEPPED
4. L / REVERSE / SLOPED_CLOSED / Boards SLOPED
5. U / FORWARD / STEPPED_CLOSED / Boards OFF
6. U / REVERSE / SLOPED_CLOSED / Boards SLOPED
```

All six returned:

```text
finite=True
zero=[]
boundary=0
nonmanifold=0
```

and each same-condition second Regenerate returned `SAME=True`. Visual review found no obvious Landing/Flight gap, closed-underside hole or spike, Side Board duplication/side swap, giant triangle, filler prism, duplicate positive-volume body, or obvious reversed face.

## 18. Final accepted contracts

Build 07-D overall acceptance includes all Stage 1–4 contracts above. In particular:

- legacy schema-1 BASIC, schema-2 07-B Residential, and schema-3 07-C Residential Straight remain compatible and are not silently upgraded by ordinary handling.
- schema-4 Multi-point supports production L and U / three-Flight Landing routes as one Managed Stair.
- persistent Stair ID and Path point IDs survive ordinary edit, regeneration, save/reopen, and accepted Repair workflows.
- AUTO and MANUAL physical Flight allocations are deterministic and persistent under their respective authority rules.
- valid START / END / TURN editing uses canonical Path data; invalid candidates rollback atomically.
- Shift 15-degree / alignment-guide foundation remains part of the accepted 07-D Path interaction contract; production Landing turns remain exact ±90 degrees.
- STEPPED_CLOSED / SLOPED_CLOSED and STEPPED / SLOPED Side Board variants are accepted across representative L/U, mirrored, and Reverse cases.
- Material role mapping, Material persistence, and deterministic regeneration remain stable.
- Geometry Repair, Transform Repair, and duplicate-ID Repair operate from canonical state without unrelated-object mutation.
- Finalize produces an ordinary editable Mesh and ends Stair management without visible geometry change.
- Delete Stair is active-object-only and remains available in supported abnormal managed states.
- Stair lifecycle operations do not mutate unrelated managed Wall / Finish objects.
- representative final Straight/L/U meshes are finite, positive-area, closed, and free of unintended boundary / non-manifold edges.
- Build 07-D remains a standalone Stair system and does not require Wall / Floor / Room attachment.

## 19. Deferred to later builds

Build 07-D acceptance does **not** add or accept:

- Winder / 廻り段 geometry; this remains Build 07-E scope.
- arbitrary-angle Landing turns such as 30 / 45 / 60 degrees; 07-D production Landing turns remain exact ±90 degrees.
- automatic conversion of saved 07-D Landing turns to Winder.
- open stair / support variants; these remain Build 07-F scope.
- handrail / newel / baluster systems.
- automatic Wall / Floor / Room attachment.

World-space Stair placement may be oblique and the accepted interaction foundation includes Shift 15-degree direction constraint; that does not change the exact-90-degree production Landing-turn contract.

## 20. Acceptance conclusion

**Build 07-D Stage 1 is ACCEPTED.**

**Build 07-D Stage 2 is ACCEPTED.**

**Build 07-D Stage 3 is ACCEPTED.**

**Build 07-D Stage 4 is ACCEPTED.**

**Build 07-D overall is ACCEPTED.**

The exact Stage-4 runtime-tested artifact is `Japanese_House_Modeler_Build_07_D_Stage4_Candidate_r1.zip` with SIZE `143226` bytes and SHA256 `58af371ded07b33ef1ec3f465fdde2e52ebaec9d88be7f0e8eea2f8802fcbed3`.

The exact Stage-4 runtime-tested revision is `6c8cd05e7a854a28c1396a26b4282bb6ecbc052b` / tree `f4c7b338560b688577314d297e422bd248e6554f`.

Stage 4 introduced no production Python change. Acceptance/documentation commits created after the Blender runtime review do not supersede that exact runtime-tested revision.
