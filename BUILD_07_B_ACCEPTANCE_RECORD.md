# Build 07-B Acceptance Record

## Current acceptance status

- **Build 07-B Stage 1 — Residential Foundation / Compatibility: ACCEPTED**
- **Build 07-B Stage 2 — STEPPED_CLOSED Underbody: ACCEPTED**
- Build 07-B Stage 3 — Side Boards + Part Materials: NOT STARTED
- Build 07-B Stage 4 — Lifecycle / Full Regression: NOT STARTED
- **Build 07-B overall: NOT YET ACCEPTED**

Stages 1 and 2 passed their automated gates and Blender 5.2 LTS runtime acceptance.
Each accepted stage keeps its exact runtime-tested implementation commit/tree as
the production reference. Acceptance Record commits change documentation only.

## Runtime-tested Stage 1 production revision and artifact

- GitHub PR: `#15 — Implement Build 07-B Stage 1 residential foundation`
- Runtime-tested production commit: `35d9c6af3f7071b2d251daa5ea5b5ac7b9c6e3a6`
- Runtime-tested production tree: `61cc1d94fa2416edc996805aeaacf026d5d9ace7`
- Runtime Candidate: `Japanese_House_Modeler_Build_07_B_Stage1_Candidate_r1.zip`
- Candidate size: `109620 bytes`
- Candidate SHA256: `69EED7B01C4FF945B9D6A7D8C8CE5188922397A89D281D2D5E65443FF4E6ABAF`
- Runtime environment: Blender 5.2 LTS
- Add-on version: `(0, 7, 1)`
- Description: `Build 07-B: Standard Residential Straight Stair`

## Automated evidence

The Stage 1 implementation report recorded:

| Check | Result |
|---|---:|
| `python -m unittest tests.test_build_07_a_stage1` | **22 PASS** |
| `python -m unittest tests.test_build_07_a_stage2` | **17 PASS** |
| `python -m unittest tests.test_build_07_a_stage3` | **31 PASS** |
| `python -m unittest tests.test_build_07_a_stage4` | **14 PASS** |
| `python -m unittest tests.test_build_07_b_stage1` | **18 PASS** |
| `python -m unittest discover -s tests` | **465 PASS** |
| `python -m compileall -q japanese_house_modeler tests` | **PASS** |
| `git diff --check` | **PASS** |
| Working tree | **clean** |

Automated evidence is separate from, and was not substituted for, Blender
runtime evidence.

## Blender 5.2 LTS runtime acceptance

| Test | Runtime gate | Result | Evidence |
|---:|---|---|---|
| 0 | Add-on identity + hidden defaults | **PASS** | Version 0.7.1 and Build 07-B description loaded. Default assembly remained BASIC, schema 1. Residential defaults were present but hidden: STEPPED_CLOSED, 9.5 mm, both Side Boards enabled, 18 mm thickness, 150 mm band, Materials None. |
| 1 | New Stair remains BASIC | **PASS** | New managed Stair was BASIC/schema 1 with 2 Path points and accepted 07-A geometry: 248 vertices / 186 faces. Residential defaults did not generate Residential geometry. |
| 2 | Dimension edit remains BASIC | **PASS** | Width 900→1000 mm regenerated to 248 / 186 while preserving BASIC/schema 1 and Residential hidden values. |
| 3 | Reverse remains BASIC | **PASS** | FORWARD→REVERSE preserved BASIC/schema 1, width 1000 mm and 248 / 186 geometry. |
| 4 | Regenerate remains BASIC | **PASS** | Explicit regeneration preserved REVERSE, BASIC/schema 1, width 1000 mm and 248 / 186 geometry. |
| 5 | Save / full exit / reopen | **PASS** | Managed Stair reopened as REVERSE BASIC/schema 1, 1000 mm width, 248 / 186 geometry, with Residential hidden defaults unchanged. No migration/regeneration occurred. |
| 6 | Numeric Path edit remains BASIC | **PASS** | P1 X was changed to 1.0 m; Path regenerated correctly while preserving REVERSE, BASIC/schema 1 and 248 / 186 geometry. |
| 7 | GEOMETRY_MISSING Repair remains BASIC | **PASS** | Clearing geometry produced GEOMETRY_MISSING. Repair restored 248 / 186, REVERSE, width 1000 mm, edited P1, BASIC/schema 1. |
| 8 | BASIC ignores unused invalid Residential values | **PASS** | Setting unused Underbody thickness to -123 and Side Board band width to -456 produced no managed-state issue while assembly remained BASIC. |
| 9 | BASIC regenerate with unused invalid Residential values | **PASS** | Regeneration still succeeded at 248 / 186 with no issues and no Residential conversion. |
| 10 | Original 07-A .blend compatibility | **PASS** | An accepted 07-A file opened directly under 07-B as BASIC/schema 1, 2 Path points, 248 / 186, NORMAL state, with no Underbody/Side Board geometry added. |
| 11 | Legacy 07-A re-save / reopen | **PASS** | 07-A file saved under 07-B and reopened as BASIC/schema 1, 2 Path points, 248 / 186, NORMAL state. No automatic migration occurred. |
| 12 | Concave profile extrusion foundation | **PASS** | L-shaped concave XZ profile extruded in Blender Python to 12 vertices / 14 faces and passed generalized fragment validation. |
| 13 | Residential candidate schema semantics | **PASS** | schema 1 BASIC candidate became schema 2 Residential; schema 3 BASIC candidate remained schema 3 Residential; source records remained 1 / 3 and were not mutated. |
| 14 | Material role resolver foundation | **PASS** | Base fallback and role override worked; Base=None + Tread-only kept Riser/Underside/Side Board UNASSIGNED (None). |
| 15 | Residential public-operator scope guard | **PASS** | No Residential/apply/material operators were registered in `bpy.ops.jhm`. Stage 1 did not expose Stage 3 functionality. |
| 16 | schema 3 BASIC diagnostic legality | **PASS** | `StairState(... BASIC, schema=3)` diagnosed with no issues, confirming schema and assembly mode remain independent. |

## Runtime command correction note

One initial operator-availability probe used `hasattr(bpy.ops.jhm, ...)`.
Blender's dynamic operator namespace can report True for unregistered names, so
that probe was not a valid product test. It was replaced with inspection of
registered names via `dir(bpy.ops.jhm)`, which returned no Residential
operators as required.

A separate Python Console syntax error while defining a temporary helper for
Test 13 was a command-entry issue, not an add-on defect. The test was rerun with
a one-line construction and passed.

## Accepted Stage 1 scope

Accepted Stage 1 scope includes:

- hidden `BASIC_TREAD_RISER` / `STANDARD_RESIDENTIAL` canonical mode foundation
- independent Stair schema version
- legacy 07-A semantic defaults without load-time migration
- Residential default/property foundation
- immutable BASIC→Residential candidate/snapshot foundation
- Material base + role-override resolver with UNASSIGNED preservation
- mode-aware managed-state validation
- generalized closed MeshFragment validation
- simple 2D polygon validation
- deterministic concave-polygon triangulation
- limited XZ-profile → local-Y closed-solid extrusion
- 07-A BASIC creation/edit/reverse/regenerate/repair/save compatibility
- Stage 1 public-scope guard

Stage 1 does **not** accept or expose:

- STEPPED_CLOSED production Underbody geometry
- Side Board production geometry
- complete Residential Mesh assembly
- role-based polygon Material assignment / slot construction
- Residential create/apply/settings/Material UI or operators
- SLOPED_CLOSED, nosing/overhang, bevel/round, Multi-point Path, Landing, Winder

## Runtime-tested Stage 2 production revision and artifact

- GitHub PR: `#16 — Implement Build 07-B Stage 2: Stepped Closed Underbody`
- Runtime-tested production commit: `b31ac4523256f4ead1d51fd7bb3c67f81c0535a5`
- Runtime-tested production tree: `d6909e7f311035d82b3403c4cf6b2a8b41d7159d`
- Runtime Candidate: `Japanese_House_Modeler_Build_07_B_Stage2_Candidate_r1.zip`
- Candidate size: `112268 bytes`
- Candidate SHA256: `D3210FA19AA6226EF9D3B94179022F58F2740B879A397E499DBF3CF967E3556C`
- Runtime environment: Blender 5.2 LTS
- Add-on version: `(0, 7, 1)`
- Description: `Build 07-B: Standard Residential Straight Stair`

### Stage 2 automated evidence

| Check | Result |
|---|---:|
| `python -m unittest tests.test_build_07_a_stage1` | **22 PASS** |
| `python -m unittest tests.test_build_07_a_stage2` | **17 PASS** |
| `python -m unittest tests.test_build_07_a_stage3` | **31 PASS** |
| `python -m unittest tests.test_build_07_a_stage4` | **14 PASS** |
| `python -m unittest tests.test_build_07_b_stage1` | **18 PASS** |
| `python -m unittest tests.test_build_07_b_stage2` | **12 PASS** |
| `python -m unittest discover -s tests` | **477 PASS** |
| `python -m compileall -q japanese_house_modeler tests` | **PASS** |
| `git diff --check` | **PASS** |
| Working tree | **clean** |

### Stage 2 Blender 5.2 LTS runtime acceptance

| Test | Runtime gate | Result | Evidence |
|---:|---|---|---|
| 0 | BASIC creation regression | **PASS** | Normal UI creation remained BASIC/schema 1 with 248 vertices / 186 faces. Residential defaults remained hidden and no Underbody was added. |
| 1 | Controlled Residential generation | **PASS** | Internal Stage 2 path generated STANDARD_RESIDENTIAL/schema 2, STEPPED_CLOSED, both Side Boards OFF, 492 vertices / 548 faces, NORMAL state. Visual side view showed a thin stepped underside following Tread/Riser geometry. |
| 2 | Lower/upper numeric termination | **PASS** | Lower endpoints were (r,B) and (r+u,B); minimum Z equaled B; inner/outer upper X and maximum X equaled L+r exactly, with no L+r+u extension. |
| 3 | Underbody thickness edit | **PASS** | u 9.5→6.0 mm regenerated successfully at 492 / 548; lower/upper offset values changed correctly and state remained NORMAL. |
| 4 | Invalid thickness atomic rejection | **PASS** | u=12.0 mm boundary was rejected before Scene mutation; the existing Mesh object/data and canonical u=6.0 mm remained unchanged at 492 / 548, NORMAL. |
| 5 | Oblique Path | **PASS** | P0=(0,0), P1=(3.6,1.8) produced run≈4.0249 m with resolved forward/left axes; 492 / 548 geometry and NORMAL state were preserved. Visual inspection confirmed Path-axis following rather than world-X locking. |
| 6 | REVERSE on oblique Path | **PASS** | Path order stayed unchanged while lower/upper endpoints and forward/left axes reversed; Underbody regenerated with 492 / 548 and NORMAL state. |
| 7 | Nonzero base_z | **PASS** | base_z=425 mm produced layout B/min profile Z=0.425 m and exact lower endpoints at Z=B; 492 / 548 and NORMAL state. |
| 8 | Save / full exit / reopen | **PASS** | STANDARD_RESIDENTIAL/schema 2, REVERSE, oblique Path, base_z 425 mm, u=6.0 mm, both boards OFF, 492 / 548 and NORMAL state all persisted. |
| 9 | Undo / Redo spot | **PASS** | Width 900→1000 mm, Undo→900, Redo→1000 succeeded. Final Residential state, Underbody geometry and NORMAL diagnosis were preserved. |
| 10 | Final Mesh geometry health | **PASS** | 492 vertices, 976 edges, 548 faces; zero non-manifold edges, zero zero-area faces, all coordinates finite. |
| 11 | Side Board ON rejection | **PASS** | Candidate with Left Side Board ON was rejected rather than silently ignored; previous Mesh/canonical state remained unchanged and NORMAL. |
| 12 | Underside / side closure visual gate | **PASS** | Underside oblique inspection showed the thin stepped Underbody, no floor-solid mass, no visible unintended air gap, closed-looking body with boards OFF, no obvious exterior z-fighting, and no upper rear wrap. |
| 13 | Public-scope guard | **PASS** | No Residential/apply/material operators were registered and no Residential/Underbody controls appeared in the sidebar. |
| 14 | Existing managed Regenerate path | **PASS** | Existing “階段を再生成” correctly regenerated the controlled Residential state: schema 2, REVERSE, base_z 425 mm, width 1000 mm, u=6.0 mm, boards OFF, 492 / 548, NORMAL. |

### Accepted Stage 2 scope

Accepted Stage 2 scope includes:

- analytical `U_inner` derived from resolved canonical Stair layout
- orthogonal translated-line-intersection `U_outer`
- exact lower termination at `Z=B`
- exact upper termination at `X=L+r`
- supported Underbody range `0 < u < min(h-t, r)`
- validated simple closed XZ Underbody profile
- Stage 1 polygon validation / triangulation / extrusion reuse
- one closed full-width Underbody fragment following resolved forward/left axes
- Tread + Riser + Underbody controlled Residential assembly
- FORWARD / REVERSE, oblique Path and nonzero base_z support
- invalid-thickness pre-mutation rejection
- Save/reopen and Undo/Redo spot coverage
- BASIC compatibility and Stage 2 public-scope guard

Stage 2 does **not** accept or expose:

- Left/Right Side Board production geometry
- Side Board band/clipping
- part-specific Material polygon assignment or Material slot assembly
- Residential create/apply/settings/Material UI or operators
- completed Standard Residential user workflow
- SLOPED_CLOSED, nosing/overhang, bevel/round, Multi-point Path, Landing, Winder

## Acceptance conclusion

**Build 07-B Stage 1 — Residential Foundation / Compatibility: ACCEPTED**

**Build 07-B Stage 2 — STEPPED_CLOSED Underbody: ACCEPTED**

Build 07-B overall is **NOT YET ACCEPTED**.

The Stage 2 runtime-tested production revision is
`b31ac4523256f4ead1d51fd7bb3c67f81c0535a5`, with production tree
`d6909e7f311035d82b3403c4cf6b2a8b41d7159d`.

Next: **Build 07-B Stage 3 — Side Boards + Part Materials**.
