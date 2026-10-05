# BUILD 07-E STAGE 2.5 ACCEPTANCE RECORD
## Japanese House Modeler — Pre-Stage-3 Winder Geometry Simplification

Date: 2026-10-05

## 1. Status

- Build 07-E Stage 1 — **ACCEPTED**
- Build 07-E Stage 2 — **ACCEPTED at Candidate r3**
- Build 07-E Stage 2.5 — **ACCEPTED**
- Build 07-E Stage 3 first attempt / PR #33 — **ABANDONED / CLOSED / NOT MERGED**
- Fresh Build 07-E Stage 3 restart — **NEXT**
- Build 07-E Stage 4 — **PENDING**
- Build 07-E overall — **NOT YET ACCEPTED**

Stage 2.5 acceptance follows `BUILD_07_E_SPECIFICATION.md` Section 39 and `BUILD_07_E_STAGE_2_5_PLAN.md`. Its purpose is to restore Candidate-r1-equivalent visible Winder TREAD/RISER production while preserving the later Stage-2 feature foundation and accepted Build 07-D geometry.

## 2. Runtime-tested production identity

GitHub PR: #34

Exact Blender runtime-tested production revision:

```text
commit 0149b5906bc80b02a39de2b8812ac9d776a8c0a7
tree   78933cab9681a17a5d793089ec939fd729fc0d35
```

The Candidate ZIP was created directly from the exact GitHub commit above.

```text
Japanese_House_Modeler_Build_07_E_Stage2_5_Candidate_r1.zip
SHA256  3ca8ae0f969c803a2f16504f07242818615079e8a5138c2faa376d58c83961a4
```

Runtime environment:

```text
Blender 5.2 LTS
Add-on version: (0, 7, 4)
Description: Build 07-E: Winder + Arbitrary-angle Turn/Landing
```

Any documentation-only commit added after runtime testing does not supersede the exact runtime-tested production commit/tree above.

## 3. Accepted Stage-2.5 production correction

Stage 2.5 keeps the accepted Stage-2 r3 codebase as the structural base but restores the Candidate-r1 per-cell visible Winder production path:

```text
physical_winder_tread_polygon(...)
resolve_winder_riser_plan(...)
```

`build_winder_fragments(...)` again resolves Winder TREAD/RISER per cell. The later r2/r3 Turn-wide `resolve_physical_winder_plans(...)` / `K_finish` helpers may remain in source but are bypassed as visible TREAD/RISER production authority for this Stage-2.5 baseline.

The correction is intentionally narrow. It does not roll the repository back and does not replace the whole current `stair_turn.py` with the historical Candidate-r1 file.

## 4. Automated / static evidence

Implementation report for the exact Stage-2.5 production contents:

```text
python -m unittest tests.test_build_07_e_stage2_5
6 tests PASS

python -m unittest tests.test_build_07_e_stage1 tests.test_build_07_e_stage2
127 tests PASS

python -m unittest tests.test_build_07_d_stage1 tests.test_build_07_d_stage2 tests.test_build_07_d_stage3 tests.test_build_07_d_stage4
131 tests PASS

python -m unittest discover -s tests
899 tests PASS

python -m compileall -q japanese_house_modeler tests
PASS

git diff --check
PASS
```

The dedicated Stage-2.5 regression fixture records Candidate-r1 authority from:

```text
commit b0d92fc15f7ec103e3cf18b6110dce2b5841fd3e
tree   e90e4bfa0e0583552bc761a200b8e51a52590470
```

The exact-90 EQUAL_3 FORWARD/REVERSE fixture compares Winder fragment geometry, vertex order, elevations, ordinals/event ordering and production-path authority against that retained source.

## 5. Blender 5.2 LTS runtime acceptance

All four grouped Stage-2.5 runtime tests passed on Candidate r1.

### Test 1 — exact-90 EQUAL_3 FORWARD / Candidate-r1 restoration — PASS

A retained managed Stage-2 stair was regenerated with Stage-2.5 Candidate r1.

Observed state:

```text
Turn 1 = WINDER / EQUAL_3
ascent = FORWARD
Mesh = 236 vertices / 178 faces
```

Visual and mesh review confirmed:

- the visible Winder top returned to the retained Stage-2 Candidate-r1 form;
- all three Winder boundaries converge on one common inner XY pivot;
- the straight/Winder relationship matches the intended simpler r1-equivalent baseline;
- no non-finite / collapsed / zero-area geometry was observed;
- the historical Candidate-r1 terminal TREAD/RISER gap is present and intentionally tolerated.

### Test 2 — exact-90 EQUAL_3 REVERSE — PASS

The same stair was reversed through the JHM UI.

Observed state:

```text
Turn 1 = WINDER / EQUAL_3
ascent = REVERSE
Mesh = 236 vertices / 178 faces
```

The REVERSE path regenerated correctly, retained the same common inner XY pivot, and preserved the expected Candidate-r1-equivalent subdivision without a major spike, giant face or collapsed Winder cell.

### Test 3 — 63-degree EQUAL_3 + Save / full exit / reopen — PASS

The exact-90 L stair was changed to an arbitrary-angle Winder using:

```text
P0 = (2.9815, 1.9802) m
P1 = (5.9793, 1.9802) m
P2 = (7.3449, 4.6603) m
```

This resolves to approximately 63 degrees.

Observed state before save:

```text
Turn 1 = WINDER / EQUAL_3
ascent = FORWARD
AUTO = 6,6
Mesh = 236 vertices / 178 faces
```

Visual review confirmed three valid Winder steps with no major spike, giant face, collapse or generation exception. The file was saved, Blender was fully exited, Blender 5.2 LTS was restarted, and the file was reopened. Path coordinates, FORWARD direction, EQUAL_3 state, mesh counts and visible geometry were preserved.

### Test 4 — Build 07-D exact-90 Landing / underside regression — PASS

An accepted Build 07-D Stage-4 schema-4 L stair fixture was opened under the Stage-2.5 add-on and regenerated once.

Console evidence after regeneration:

```text
SCHEMA=4
MANAGED=True
TRANSFORM=(0.0,0.0,0.0) (0.0,0.0,0.0) (1.0,1.0,1.0)
MESH=433 412
```

Visual review confirmed the accepted 07-D L/Landing behavior remained intact, including Landing and sloped closed underside/body presentation. No Winder-style Candidate-r1 top was introduced into the schema-4 stair, which is the required compatibility behavior. No obvious giant filler face, spike, upper-surface body penetration, major exterior gap, or visible z-fighting regression was observed.

## 6. Known intentionally accepted limitation

The historical Candidate-r1 visible terminal TREAD/RISER / Turn-transition gap remains:

```text
known r1 terminal gap = ALLOWED / NOT A STAGE-2.5 BLOCKER
```

This is not repaired during Stage 2.5. Reintroducing the r2/r3 Turn-wide physical-plan / `K_finish` complexity solely to close this gap would defeat the purpose of the correction stage.

## 7. Compatibility / preservation conclusion

Stage 2.5 preserves the later Stage-2 foundation required for the restarted Stage 3, including schema-5 Turn state, FORWARD/REVERSE, arbitrary-angle Winder support, BF patterns, U / Compact-U foundation, allocation behavior and serialization/lifecycle infrastructure.

The runtime regression test also confirms that an accepted schema-4 Build 07-D Landing stair remains on the schema-4 production path and does not silently become schema 5 or adopt Stage-2.5 Winder geometry.

## 8. Acceptance conclusion

Build 07-E Stage 2.5 — **ACCEPTED** at the exact runtime-tested production revision:

```text
commit 0149b5906bc80b02a39de2b8812ac9d776a8c0a7
tree   78933cab9681a17a5d793089ec939fd729fc0d35
```

Accepted runtime Candidate:

```text
Japanese_House_Modeler_Build_07_E_Stage2_5_Candidate_r1.zip
SHA256  3ca8ae0f969c803a2f16504f07242818615079e8a5138c2faa376d58c83961a4
```

Fresh Build 07-E Stage 3 must start from `main` only after PR #34 is merged. The abandoned PR #33 architecture is not the new Stage-3 baseline.

Build 07-E overall remains **NOT YET ACCEPTED**; Stage 4 remains the final overall acceptance stage.
