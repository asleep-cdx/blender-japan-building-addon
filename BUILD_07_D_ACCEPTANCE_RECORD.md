# BUILD 07-D ACCEPTANCE RECORD
## Japanese House Modeler — Multi-point Path + L / U + Landing

Date: 2026-09-29

## 1. Status

- Build 07-D Stage 1 — **ACCEPTED**
- Build 07-D Stage 2 — **ACCEPTED**
- Build 07-D Stage 3 — **ACCEPTED**
- Build 07-D Stage 4 — NOT YET ACCEPTED
- Build 07-D overall — **IN PROGRESS**

Stage 1 established the schema-4 Multi-point foundation and first visible 3-point L Stair. Stage 2 completed the 3-point L editing / guide / distribution / Residential integration scope. Stage 3 completes the 4-point U / multi-flight production, editing, allocation, Residential turn ownership, material, persistence, and rollback scope defined for Stage 3 while preserving accepted schema-1/2/3 Straight behavior and the accepted Stage-1/2 schema-4 foundation.

Implementation authority remains `BUILD_07_D_SPECIFICATION.md`. Build 07-D overall is not accepted until Stage 4.

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

Documentation / acceptance commits created after runtime review do not supersede the exact runtime-tested production revision above. Accepted runtime archives must be derived from the production revision above, not from later documentation-only commits.

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

The following corrections are part of the Stage-2 accepted production result:

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

Stage 2 does **not** claim completion of:

- 4-point U-shaped production geometry
- more-than-two-Flight production path
- general multi-turn Stair generation
- Stage-3 U / multi-flight editing and allocation completion
- Stage-4 full lifecycle / broad practical acceptance
- Winder / 廻り段 geometry; that remains Build 07-E scope

These remain governed by `BUILD_07_D_SPECIFICATION.md` and later Build stages.

## 8. Stage 2 acceptance conclusion

Build 07-D Stage 1 is **ACCEPTED** at its recorded Stage-1 runtime-tested revision.

Build 07-D Stage 2 is **ACCEPTED** at the exact runtime-tested production revision:

```text
commit b4869816da1b6d1d92033b4994e9bdbbf55b08a2
tree   871d7bd4971c5433e4d7bec8c7b8af06e716d03d
```

The accepted Stage-2 Candidate is:

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

Documentation / acceptance commits created after this runtime review do not supersede the exact runtime-tested production revision above. Accepted runtime archives must be derived from the production revision above, not from later documentation-only commits.

## 10. Stage 3 automated evidence

Final implementation report:

```text
python -m unittest tests.test_build_07_d_stage3   13 PASS
Stage-1 / Stage-2 / Stage-3 combined suites      PASS
python -m unittest discover -s tests             PASS
python -m compileall -q japanese_house_modeler tests   PASS
git diff --check                                  PASS
```

The implementation report also confirmed a clean working tree before GitHub-side acceptance documentation.

## 11. Stage 3 accepted contracts

Stage 3 accepts the following production behavior in addition to the Stage-1 / Stage-2 contracts:

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
- in the over-constrained runtime case there is no valid candidate, so the semantic `TURN 1` / `TURN 2` candidate label is not rendered; P1/P2 target indication and atomic rejection verify the actual mapping.
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

AUTO -> MANUAL `6,3,7` persisted exactly. Wrong-total MANUAL input, below-two backend validation, and a too-short middle Flight were rejected without state mutation. Final comparison returned:

```text
T4 ROLLBACK = True
```

AUTO was then restored successfully.

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

Save -> complete Blender exit -> reopen:

```text
T7 REOPEN = True DIFF = []
```

Three repeated Regenerate operations:

```text
T7 REGEN: MESH=True STATE=True
```

Final invalid Flight-3 edit:

```text
T7 INVALID ROLLBACK=True MESH_PTR=True DIFF=[]
```

The invalid edit produced a normal validation message, no traceback, no visible shape mutation, and preserved the exact existing Mesh datablock pointer.

## 13. Stage 3 intentionally deferred scope

Stage 3 does **not** claim completion of:

- Build 07-D Stage-4 lifecycle / full-regression / practical-placement acceptance
- final Build 07-D overall acceptance
- Winder / 廻り段 geometry; that remains Build 07-E scope

## 14. Acceptance conclusion

Build 07-D Stage 1 — **ACCEPTED**.

Build 07-D Stage 2 — **ACCEPTED**.

Build 07-D Stage 3 — **ACCEPTED** at the exact runtime-tested production revision:

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

Build 07-D overall remains **IN PROGRESS**. The next implementation target is Build 07-D Stage 4: lifecycle / full regression / practical acceptance.