# Build 07-B Acceptance Record

## Current acceptance status

- **Build 07-B Stage 1 — Residential Foundation / Compatibility: ACCEPTED**
- Build 07-B Stage 2 — STEPPED_CLOSED Underbody: NOT STARTED
- Build 07-B Stage 3 — Side Boards + Part Materials: NOT STARTED
- Build 07-B Stage 4 — Lifecycle / Full Regression: NOT STARTED
- **Build 07-B overall: NOT YET ACCEPTED**

Stage 1 passed its automated gates and Blender 5.2 LTS runtime acceptance.
The accepted Stage 1 production revision remains the exact runtime-tested
implementation commit/tree listed below. This Acceptance Record commit changes
documentation only.

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

## Acceptance conclusion

**Build 07-B Stage 1 — Residential Foundation / Compatibility: ACCEPTED**

The runtime-tested production revision is
`35d9c6af3f7071b2d251daa5ea5b5ac7b9c6e3a6`, with production tree
`61cc1d94fa2416edc996805aeaacf026d5d9ace7`.

Next: **Build 07-B Stage 2 — STEPPED_CLOSED Underbody**.
