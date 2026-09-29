# BUILD 07-D ACCEPTANCE RECORD
## Japanese House Modeler — Multi-point Path + L / U + Landing

Date: 2026-09-29

## 1. Status

- Build 07-D Stage 1 — **ACCEPTED**
- Build 07-D Stage 2 — **ACCEPTED**
- Build 07-D Stage 3 — NOT YET ACCEPTED
- Build 07-D Stage 4 — NOT YET ACCEPTED
- Build 07-D overall — **IN PROGRESS**

Stage 1 established the schema-4 Multi-point foundation and first visible 3-point L Stair. Stage 2 completes the 3-point L editing / guide / distribution / Residential integration scope defined for Stage 2 while preserving accepted schema-1/2/3 Straight behavior and the Stage-1 schema-4 foundation.

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

## 8. Acceptance conclusion

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

The next implementation target is Build 07-D Stage 3: U-shaped / multi-flight production. Build 07-D overall remains **IN PROGRESS** until Stage 4 acceptance.
