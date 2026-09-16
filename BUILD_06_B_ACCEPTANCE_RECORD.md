# Build 06-B Acceptance Record

## Acceptance status

- **Build 06-B Stage 1: ACCEPTED**
- **Build 06-B overall: IN PROGRESS**
- **Stage 2-A: NOT YET ACCEPTED**
- **Stage 2-B: NOT YET ACCEPTED**
- **Stage 3: NOT YET ACCEPTED**

This record accepts only Stage 1, **Standard Baseboard Foundation**. It does
not accept Build 06-B as a whole and does not provide acceptance evidence for
any later stage.

## Tested revisions and artifact

- Blender 5.2 LTS runtime-tested GitHub revision:
  `4b67bde3ce4648950acd1b01962bbe34f03e76d0`
- Runtime artifact:
  `Japanese_House_Modeler_Build_06_B_Stage1_Candidate_r3.zip`
- Automated-test local source revision before this record-only commit:
  `f1d174eb27c5800732e7039ff41c3995219114b8`
- Add-on version: `(0, 6, 3)`
- Accepted build identification:
  `Build 06-B Stage 1: Standard Baseboard Foundation`

The runtime evidence below was supplied from Blender 5.2 LTS execution. Pure
Python automation is recorded separately and is not represented as Blender
runtime evidence.

## Stage 1 runtime acceptance

| # | Test | Result | Runtime evidence |
|---:|---|---|---|
| 1 | Standard SIMPLE Profile and selected-Finish UI | PASS | Default 60 × 10 mm generated. UI showed BASEBOARD, SIMPLE, height, projection, span count, and managed state. |
| 2 | Run-local Profile dimensions | PASS | An individual Run changed to dimensions including 80 × 20 mm; actual geometry changed and other Runs were not implicitly modified. |
| 3 | LEFT/RIGHT × FORWARD/REVERSE orientation and normals | PASS | All four combinations projected to the intended side, used no negative Object Scale, retained identity Finish/Profile scale, and produced signed volumes with the same direction. |
| 4 | Editable Mesh conversion | PASS | After weld cleanup: `non_manifold=0`, `boundary=0`, signed volume positive, Flat Shade enabled, and scale `(1, 1, 1)`. |
| 5 | 90-degree MITER and variable projection | PASS | SIMPLE projections 10, 40, and 60 mm produced correct miters. The outer-edge skew seen with a 3D Curve was removed by the production 2D path; horizontal and vertical outer edges were straight. |
| 6 | 2D Finish path and placement-adjusted derived Profile | PASS | Finish Curve dimensions were 2D; Finish Object location was `(0, 0, 0)` and scale `(1, 1, 1)`. Canonical Profile data remained origin-based while derived Profile data carried vertical placement. |
| 7 | FLOOR / CEILING / ABSOLUTE vertical references | PASS | FLOOR base was 625.0 mm, CEILING base was 2400.0 mm, and ABSOLUTE base was 750.0 mm, each matching the expected value. Every case retained a 2D Curve, zero Object location, and identity scale. |
| 8 | Profile edit Undo / Redo | PASS | Edit 60 × 10 to 80 × 20, Undo to 60 × 10, and Redo to 80 × 20 kept canonical values and derived geometry synchronized. |
| 9 | Save / close / reopen / regenerate | PASS | SIMPLE revision, schema, dimensions, 2D Curve state, derived vertical base, identity Transform, and regenerated appearance persisted. |
| 10 | Unsafe Profile edit rollback | PASS | A 300 mm projection edit on a three-span Run with a short middle segment was rejected with `Finish区間がProfileの留め加工には短すぎます。`; old geometry remained and canonical dimensions rolled back to 60 × 10. |
| 11 | Endpoint blocker uses actual Profile side | PASS | Projection away from the blocker was accepted; projection toward it was rejected with `接続Wallが仕上げ端部を遮っています。`. |
| 12 | Oblique MITER | PASS | An approximately 45-degree connection with SIMPLE 60 × 40 mm had no gap, overlap, or abnormal spike; outer edges were straight and managed state remained normal. |
| 13 | Legacy `SIMPLE_10X60` compatibility | PASS | Explicit regeneration non-destructively retained `SIMPLE_10X60 1 1 60.0 10.0`; UI/resolved geometry showed SIMPLE 60 × 10. The first explicit edit persisted `SIMPLE 1 1 80.0 20.0`. |
| 14 | Material preservation | PASS | `JHM_Test_Material` survived Profile edit, regeneration, save/reopen, and editable Mesh conversion. The Mesh retained the material slot and polygon `material_index=0`. |
| 15 | Partial-boundary BUTT ends | PASS | A single-span interval from 200 mm to 1000 mm regenerated and converted successfully; resulting Mesh had `non_manifold=0`, `boundary=0`, signed volume `0.00048`, and Flat Shade enabled. Both partial Run ends were closed BUTT ends. |

## Automated evidence at latest local Stage 1 source

| Check | Result | Details |
|---|---|---|
| Stage 1 targeted pure suite | PASS | `python -B -m unittest tests.test_build_06_b_stage1` — 20 tests passed. |
| Full pure suite | PASS | `python -B -m unittest discover -s tests` — 186 tests passed. |
| Compile check | PASS | `python -m compileall -q japanese_house_modeler tests`. |
| Diff whitespace check | PASS | `git diff --check`. |

## Scope remaining in progress

Stage 1 acceptance does not implement or accept Stage 2-A, Stage 2-B, or
Stage 3 work. In particular, this record does not accept Manual Exclusion
geometry, BEVEL, ROUNDED, Profile-aware rounded shading, Custom Profile
registration, thumbnail browsing, closed FinishRuns, Crown Moulding,
Door/Window integration, or automatic Room recognition.
