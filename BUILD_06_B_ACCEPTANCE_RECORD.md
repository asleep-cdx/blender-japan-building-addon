# Build 06-B Acceptance Record

## Acceptance status

- **Build 06-B Stage 1: ACCEPTED**
- **Build 06-B Stage 2-A: ACCEPTED**
- **Build 06-B Stage 2-B: ACCEPTED**
- **Build 06-B overall: IN PROGRESS**
- **Stage 3: NOT YET ACCEPTED**

This record accepts Stage 1, **Standard Baseboard Foundation**, and Stage 2-A,
**Manual Exclusion and Partial Placement**, and Stage 2-B, **BEVEL, ROUNDED,
and Profile-aware Shading**. It does not accept Build 06-B as a whole and does
not provide acceptance evidence for Stage 3.

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
- Stage 2-A Blender 5.2 LTS runtime-tested production revision:
  `1c6b927522a4dc73b2973cd060636fa7105c27c2`
- Stage 2-A runtime artifact:
  `Japanese_House_Modeler_Build_06_B_Stage2A_Candidate_r3.zip`
- Automated-test local source revision before the Stage 2-A record-only commit:
  `e4e5bcdf9809c808f4b6ac406c7aa4ea089158c1`
- Accepted Stage 2-A build identification:
  `Build 06-B Stage 2-A: Manual Exclusion and Partial Placement`
- Stage 2-B Blender 5.2 LTS runtime-tested production revision:
  `dcd586e7704ebe0c4039b99ef58a41969d66a85f`
- Stage 2-B runtime artifact:
  `Japanese_House_Modeler_Build_06_B_Stage2B_Candidate_r1.zip`
- Automated-test local source revision before the Stage 2-B record-only commit:
  `5c313ca34e7eb83c40c3cabc92d96a300662c2b7`
- Accepted Stage 2-B build identification:
  `Build 06-B Stage 2-B: BEVEL, ROUNDED, and Profile-aware Shading`

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

## Stage 2-A runtime acceptance

The following evidence was obtained in Blender 5.2 LTS from production
revision `1c6b927522a4dc73b2973cd060636fa7105c27c2` using artifact
`Japanese_House_Modeler_Build_06_B_Stage2A_Candidate_r3.zip`.

| # | Test | Result | Runtime evidence |
|---:|---|---|---|
| 1 | Manual Exclusion basic subtraction | PASS | Adding a Manual Exclusion created a visible geometry gap while retaining the canonical FinishSpan. |
| 2 | Exclusion disable / enable | PASS | Disabling restored the original shape; enabling restored the same gap while preserving logical identity. |
| 3 | Exclusion edit | PASS | Editing persisted boundaries updated the gap position and length. |
| 4 | Multiple Manual Exclusions | PASS | Multiple records persisted and separated generated geometry into the appropriate visible ranges. |
| 5 | Exclusion remove | PASS | Removal regenerated the original geometry from the canonical FinishSpan without rebuilding the path. |
| 6 | Valid-empty | PASS | Full exclusion retained a normal managed Finish object with zero visible ranges and UI state `全区間除外`; editable Mesh conversion safely rejected it with `生成可能な巾木形状がありません。`. |
| 7 | Valid-empty save / reopen | PASS | Normal managed state, zero visible ranges, and Exclusion persistence survived save, close, and reopen. |
| 8 | Exclusion remove after reopen | PASS | Removing the reopened Exclusion fully restored the original Finish geometry. |
| 9 | Partial Run boundary editing | PASS | First/last FinishSpan boundaries were edited directly without creating an Exclusion; free ends were BUTT ends. |
| 10 | Partial Run Undo / Redo | PASS | Boundary edit, Undo, and Redo kept canonical and derived geometry synchronized. |
| 11 | Exclusion add Undo / Redo | PASS | On a Partial Run, Undo removed the added Exclusion and Redo restored the same gap without restoring geometry outside the Partial Run. |
| 12 | Exclusion + Partial Run editable Mesh conversion | PASS | Multiple visible ranges converted to one closed editable Mesh, retained the gap, and had closed BUTT ends. |
| 13 | Partial Run + Exclusion save / reopen | PASS | Reopen retained Partial Run `500.00–3200.00 mm`, Exclusion `1500.00–1900.00 mm`, the same logical ID, two visible ranges, and normal management. |
| 14 | Wall split with active Exclusion | PASS | One FinishSpan became two; one logical Exclusion became two persisted fragments sharing one `exclusion_id`, with fragment identities and physical gap preserved. |
| 15 | Wall split fragment boundaries | PASS | Fragment ranges `1500.00–2119.04 mm` and `0.00–380.96 mm` together preserved original logical coverage `1500.00–2500.00 mm`. |
| 16 | Split-fragment independent remove / edit | PASS | One fragment could be removed independently; the other remained active and geometry returned only on the removed-fragment side. |
| 17 | Wall split + Exclusion Undo / Redo | PASS | Undo restored one Wall and one logical Exclusion; Redo restored the T-junction and two fragments with the same logical ID and visible gap. |
| 18 | Wall split + active Exclusion save / reopen | PASS | Two FinishSpans, two fragments, the shared logical ID, visible gap, and normal managed state persisted. |
| 19 | Legacy 06-A Exclusion compatibility | PASS | An empty-ID, disabled legacy-equivalent record remained shown as legacy/disabled and did not change appearance. Explicit activation generated 06-B identity, enabled the record, created the gap, and retained normal management. |
| 20 | Remove Exclusion, then save / reopen | PASS | Exclusion count remained zero after reopen; full restored geometry and normal management persisted. |
| 21 | No join across Exclusion gap / junction-aware BUTT | PASS | Specifically retested after correction on `1c6b927522a4dc73b2973cd060636fa7105c27c2`: at a 90-degree L-corner an Exclusion reached the canonical junction without regeneration error or Miter bridge. The surviving span terminated independently against the adjacent Wall face with a closed BUTT, no triangle/spike or visible penetration, and editable Mesh conversion succeeded. |
| 22 | Material preservation through Exclusion edit | PASS | Material `Stage2A_Test_Mat` remained present after Exclusion boundary edit and regeneration: `JHM Finish ['Stage2A_Test_Mat']`. |

## Stage 2-A completion gate

The Blender 5.2 LTS evidence above satisfies the Stage 2-A gates:

- Manual Exclusion changes generated geometry.
- Original FinishSpans remain canonical.
- Overlapping/touching Exclusion coverage is merged for calculation only.
- Multiple visible ranges remain independent generated ranges.
- No Miter bridges an Exclusion gap.
- Exclusion-created ends are closed BUTT ends.
- Valid-empty is distinct from invalid managed state.
- Exclusion removal restores geometry from canonical FinishSpans.
- Wall split preserves and remaps active Exclusions and fragment identity.
- Undo/Redo passes.
- Save/reopen passes.
- Legacy 06-A Exclusion records do not alter old appearance unless explicitly activated.

## Stage 2-B runtime acceptance

The following evidence was obtained in Blender 5.2 LTS from production
revision `dcd586e7704ebe0c4039b99ef58a41969d66a85f` using artifact
`Japanese_House_Modeler_Build_06_B_Stage2B_Candidate_r1.zip`.

| # | Test | Result | Runtime evidence |
|---:|---|---|---|
| 1 | SIMPLE regression | PASS | SIMPLE 60 × 10 mm retained normal management, one visible range, and the unchanged rectangular Profile. |
| 2 | BEVEL generation | PASS | BEVEL 60 / 10 / bevel 5 produced the correct upper room-facing 45-degree chamfer, planar appearance, and normal management. |
| 3 | ROUNDED generation | PASS | ROUNDED 60 / 10 / radius 5 produced a visually smooth quarter-round upper room-facing corner. Planar regions remained planar, with no twist, bulge, or discontinuity. |
| 4 | ROUNDED radius edit | PASS | Editing radius 5 → 2 retained height/projection, updated derived geometry correctly, and retained normal management. |
| 5 | Profile switch Undo / Redo | PASS | ROUNDED radius 2 → BEVEL bevel 3; Undo restored ROUNDED radius 2 and Redo restored BEVEL bevel 3, with normal management throughout. |
| 6 | Invalid BEVEL rollback | PASS | Height 60 / projection 10 / bevel 10 was rejected. Previous BEVEL bevel 3 identity, parameters, geometry, and normal management remained intact. |
| 7 | BEVEL editable Mesh | PASS | `BOUNDARY 0`, `NON_MANIFOLD 0`, positive signed volume, `SMOOTH 0`, scale `(1,1,1)`, closed Mesh, and retained flat planar shading. |
| 8 | ROUNDED editable Mesh and Profile-aware shading | PASS | `BOUNDARY 0`, `NON_MANIFOLD 0`, positive signed volume, `SMOOTH 16`, `FLAT 40`, `POLYGONS 56`, scale `(1,1,1)`. Rounded regions were smooth and planar regions flat. |
| 9 | ROUNDED + Manual Exclusion | PASS | One Manual Exclusion produced two visible ranges, no join across the gap, no triangles/spikes, and retained ROUNDED shape on both ranges. |
| 10 | ROUNDED + Exclusion Mesh | PASS | `BOUNDARY 0`, `NON_MANIFOLD 0`, positive signed volume, `SMOOTH 32`, `FLAT 80`, `POLYGONS 112`, scale `(1,1,1)`. Both ranges were closed with BUTT ends. |
| 11 | Material preservation across Profile and Exclusion edits | PASS | `Stage2B_Test_Mat` remained assigned after ROUNDED → BEVEL, BEVEL parameter edit, and Exclusion edit: `JHM Finish ['Stage2B_Test_Mat']`. |
| 12 | BEVEL + Exclusion save/reopen | PASS | Reopen retained BEVEL, height 60, projection 10, bevel 4, one Manual Exclusion, two visible ranges, normal management, and `Stage2B_Test_Mat`. |
| 13 | ROUNDED 90-degree Miter | PASS | A two-span L path had no gap, overlap, triangle, or spike; the rounded Profile remained continuous through the supported Miter and management remained normal. |
| 14 | ROUNDED orientation matrix | PASS | LEFT/RIGHT × FORWARD/REVERSE all projected to the selected Wall face side with no negative scale, inversion, or twist; Miter geometry and management remained valid. |
| 15 | BEVEL orientation matrix | PASS | LEFT/RIGHT × FORWARD/REVERSE all projected to the correct side with no inversion/twist; supported Miter geometry and management remained valid. |
| 16 | BEVEL + Manual Exclusion + Mesh | PASS | `BOUNDARY 0`, `NON_MANIFOLD 0`, positive signed volume, `SMOOTH 0`, `POLYGONS 22`, scale `(1,1,1)`. The gap remained and both Exclusion-created ends were closed BUTT ends. |
| 17 | ROUNDED junction-aware Exclusion managed state | PASS | An Exclusion reaching the canonical L-junction created no Miter across the excluded junction. The survivor terminated independently with no triangle/spike or visible penetration; management remained normal with two visible ranges. |
| 18 | ROUNDED junction-aware Exclusion Mesh | PASS | `BOUNDARY 0`, `NON_MANIFOLD 0`, positive signed volume, `SMOOTH 32`, `FLAT 80`, `POLYGONS 112`, scale `(1,1,1)`. Closed topology and Profile-aware shading were preserved. |
| 19 | Material preservation through Mesh conversion | PASS | Before: `JHM Finish.003 ['Stage2B_Mesh_Mat']`; after: `JHM Finish.003 Mesh.001 ['Stage2B_Mesh_Mat']`. Material indices remained assigned while Profile-aware shading was applied. |
| 20 | Run-local Profile isolation | PASS | Run A was ROUNDED 80 / 12 / radius 4. Run B remained BEVEL 60 / 10 / bevel 5; changing Run A did not mutate Run B. |
| 21 | Invalid ROUNDED rollback + save/reopen | PASS | Height 80 / projection 12 / radius 12 was rejected. Rollback restored ROUNDED 80 / 12 / radius 4 and normal management. Reopen retained those values, two FinishSpans, one Manual Exclusion, two visible ranges, normal management, and preserved geometry. |

## Stage 2-B completion gate

The Blender 5.2 LTS evidence above satisfies the Stage 2-B gates:

- BEVEL and ROUNDED are selectable.
- Run-local parameters persist.
- Profile switching is transactional.
- SIMPLE / BEVEL / ROUNDED use Profile-aware safety data.
- LEFT / RIGHT normals and orientation remain correct.
- Miter and BUTT results remain valid.
- ROUNDED is visually smooth where intended.
- Planar areas remain planar.
- Editable Mesh preserves the intended appearance.
- BEVEL/ROUNDED Exclusion behavior remains correct.
- Undo/Redo passes.
- Save/reopen passes.
- Material preservation passes.

## Automated evidence at latest local Stage 2-B source

| Check | Result | Details |
|---|---|---|
| Stage 2-B targeted pure suite | PASS | `python -B -m unittest tests.test_build_06_b_stage2b` — 20 tests passed. |
| Stage 2-A targeted pure suite | PASS | `python -B -m unittest tests.test_build_06_b_stage2a` — 51 tests passed. |
| Stage 1 targeted pure suite | PASS | `python -B -m unittest tests.test_build_06_b_stage1` — 20 tests passed. |
| Full pure suite | PASS | `python -B -m unittest discover -s tests` — 257 tests passed. |
| Compile check | PASS | `python -m compileall -q japanese_house_modeler tests`. |
| Diff whitespace checks | PASS | `git diff --check` and `git diff --cached --check`. |

## Scope remaining in progress

Build 06-B overall remains **IN PROGRESS**. Remaining work is:

- Stage 3: Custom Profile Registration, project-local immutable Profile
  snapshot/revision, and final production Baseboard acceptance —
  **NOT YET ACCEPTED**.

This record does not accept Crown Moulding, closed FinishRuns, Door/Window
integration, automatic Room recognition, or any later build.
