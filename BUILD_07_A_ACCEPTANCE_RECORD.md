# Build 07-A Acceptance Record

## Acceptance status

- **Build 07-A Stage 1 — Canonical Stair + 2-point creation: ACCEPTED**
- **Build 07-A Stage 2 — Layout calculation + basic geometry: ACCEPTED**
- **Build 07-A Stage 3 — Editing + regeneration + rollback: NOT STARTED**
- **Build 07-A overall: NOT YET ACCEPTED**

Stage 2 acceptance does **not** mean that Build 07-A overall is accepted.
Editing, regeneration, repair, and the remaining lifecycle scope are later-stage
work.

## Stage 2 runtime-tested production revision and artifact

- Blender 5.2 LTS runtime-tested Stage 2 production revision:
  `cbca65810d0b9fdbc7636005607c36f9af9c1b0e`
- Runtime-tested Git tree:
  `cbb61de6e2d8528288bafdad33c260895eaadd6b`
- Runtime Candidate:
  `Japanese_House_Modeler_Build_07_A_Stage2_Candidate_r1.zip`
- Blender runtime:
  `Blender 5.2 LTS`
- Add-on version:
  `(0, 7, 0)`
- Add-on description:
  `Build 07-A: Stair Core + Top-view 2-point Straight Stair`

This Acceptance Record update changes documentation only. Its commit is not a
new runtime-tested production revision. The accepted Stage 2 production
behavior remains the revision and tree identified above.

## Automated evidence

The final Stage 2 production tree had the following automated and static
results:

| Check | Result |
|---|---:|
| `python -B -m unittest tests.test_build_07_a_stage1` | **22 tests PASS** |
| `python -B -m unittest tests.test_build_07_a_stage2` | **17 tests PASS** |
| `python -B -m unittest discover -s tests` | **402 tests PASS** |
| `python -m compileall -q japanese_house_modeler tests` | **PASS** |
| `git diff --check` | **PASS** |
| Working tree | **clean** |

These checks apply to production tree
`cbb61de6e2d8528288bafdad33c260895eaadd6b`. Automated and static results are
recorded separately from the Blender runtime evidence below.

## Stage 1 acceptance baseline

Stage 1 remains accepted. Its runtime-tested production revision was
`b6c82e80906a9404288c759bcc0650ba07d3526e`, with Git tree
`471027e9071e78d94ef872b65f780d998a37e291` and runtime candidate
`Japanese_House_Modeler_Build_07_A_Stage1_Candidate_r1.zip`.

The accepted Stage 1 foundation includes canonical Stair properties, ordered
world-XY Path points, separate draw order and ascent direction, two-click
creation and preview, cancel and invalid-input safety, persistent UUIDs,
identity Object Transform, defaults snapshotting, selection behavior, Undo /
Redo, Save / reopen, and add-on lifecycle behavior. Stage 2 runtime testing
confirmed that the accepted creation UX remains available with visible
geometry.

## Stage 2 Blender 5.2 LTS runtime acceptance

| Test | Runtime gate | Result | Evidence |
|---:|---|---|---|
| 0 | Candidate / version gate | **PASS** | Version `(0, 7, 0)` and description `Build 07-A: Stair Core + Top-view 2-point Straight Stair` were displayed. |
| 1 | Visible FORWARD Stair creation | **PASS** | Defaults `0 / 2800 / 16 / 900 / 30 / 12 / FORWARD` created one visible Managed Stair Mesh Object containing 15 Treads, 16 Risers, 31 closed fragments, 248 vertices, and 186 faces. Actual riser was 175 mm, upper arrival Z was 2800 mm, and Transform was identity. The deliberately long drawn Path produced run length 28968.0 mm and expected going 1931.2 mm. |
| 2 | Runtime vertical geometry contract | **PASS** | Mesh levels were minimum 0 mm, Riser 1 top 145 mm, Tread 1 top 175 mm, Riser 2 top 320 mm, final independent Tread top 2625 mm, and final Riser / Mesh top 2800 mm. |
| 3 | 3600 mm reference numeric contract | **PASS** | FORWARD resolved run length 3600 mm, actual riser 175 mm, 15 independent Treads, going 240 mm, upper arrival Z 2800 mm, lower P0, and upper P1. REVERSE retained run length and going, resolved lower P1 / upper P0, forward `(-1, 0, 0)`, left `(0, -1, 0)`, and preserved canonical P0 → P1 storage order. |
| 4 | REVERSE visible Mesh creation | **PASS** | Canonical Path order was unchanged; `ascent_direction=REVERSE`; lower was P1 and upper arrival was P0. Visible geometry reversed correctly with 248 vertices, 186 faces, Z range 0–2800 mm, and identity Transform. |
| 5 | Width symmetry and final Riser extension | **PASS** | A REVERSE Stair with run length 28856.5 mm had local X range 0–28868.5 mm, proving exact 12.0 mm uphill extension. Local Y was -450–+450 mm, confirming 900 mm width and centerline symmetry. |
| 6 | Oblique plan Path | **PASS** | Resolved forward was `(0.563797, 0.825913, 0)` and left was `(-0.825913, 0.563797, 0)`. Both axes had squared length 1.0 and dot product 0.0. Geometry had 248 vertices, 186 faces, and Z range 0–2800 mm. |
| 7 | Invalid tread thickness rejection | **PASS** | With actual riser 175 mm and tread thickness 200 mm, warning `踏板厚は実蹴上より小さくする必要があります。` was shown. Managed Stair and JHM Stair Mesh counts remained `3 → 3`; no partial Object or orphan Mesh was created. |
| 8 | Visible Stair creation Undo / Redo | **PASS** | Ctrl+Z removed the new visible Stair and Ctrl+Shift+Z restored it as the same managed MESH with UUID, two Path points, 248 vertices, 186 faces, Z range 0–2800 mm, and identity Transform. |
| 9 | Save / Blender exit / reopen | **PASS** | Object name, managed state, UUID, Path points, ascent direction, all canonical dimensions, 248 vertices, 186 faces, Z range 0–2800 mm, and identity Transform survived a full Blender reopen. |
| 10 | Non-zero `base_z` visible geometry | **PASS** | With base Z 1200 mm and floor-to-floor 2800 mm, Mesh Z range was 1200–4000 mm and UI upper arrival was 4000 mm. Geometry retained 248 vertices, 186 faces, and identity Transform. |
| 11 | Invalid riser thickness rejection | **PASS** | Warning `蹴込み板厚は踏面ピッチより小さくする必要があります。` was shown. Managed Stair and JHM Stair Mesh counts remained `5 → 5`; no partial Object or orphan Mesh was created. |
| 12 | Blender Mesh validity / manifold | **PASS** | Mesh contained 248 vertices, 372 edges, and 186 faces. `Mesh.validate()` returned `False`, meaning no correction was required. BMesh reported 372 manifold edges and zero non-manifold edges. |
| 13 | One Managed Stair = one Mesh Object | **PASS** | Selected Stair had zero children, no parent, and zero persistent child Stair Objects. Its single Mesh contained 248 vertices, 186 polygons, and zero material slots; Stage 2 material assignment remains intentionally unimplemented. |
| 14 | Different `riser_count` geometry | **PASS** | Floor-to-floor 2800 mm and riser count 10 derived 9 independent Treads and 280 mm actual riser. Geometry contained 9 Treads, 10 Risers, 19 fragments, 152 vertices, 114 faces, and Z range 0–2800 mm, confirming it is not hard-coded to 16 risers. |
| 15 | Invalid input preserves active / selection | **PASS** | Invalid tread thickness preserved active Object `JHM Stair.006`, the same selection, 7 Managed Stairs, and 7 Meshes. This verifies pre-commit invalid-input preservation. The internal `_commit` exception rollback was code-reviewed and covered by automated/static structural evidence; a forced internal Blender commit exception was not injected. |
| 16 | Face-normal orientation | **PASS** | All 31 fragments and 186 faces were inspected; inward or reversed face count was zero. All generated Tread and Riser box normals pointed outward. |
| 17 | Derived values UI | **PASS** | The selected Managed Stair UI displayed upper arrival height, actual riser, independent Tread count, horizontal length, and going. The observed example was 2800.0 mm, 175.0 mm, 15, 7325.5 mm, and 488.4 mm respectively. |

## Stage 2 completion gate

The automated evidence and Blender 5.2 LTS runtime evidence accept the Stage 2
implementation for:

- resolved Stair layout derived from canonical inputs;
- `run_length`, `actual_riser`, `independent_tread_count`, and `going`;
- upper-arrival plan position and elevation;
- FORWARD and REVERSE layout without canonical Path reordering;
- independent Tread and Riser generators;
- one-Mesh assembly and a visible Straight Stair;
- positive, finite, count, thickness, Path, and inter-dimension validation;
- finite, closed, manifold fragment geometry with outward-facing normals;
- width symmetry around the canonical centerline;
- final Riser alignment with and uphill extension beyond the upper-arrival line;
- read-only derived-value UI;
- visible-geometry Undo / Redo and Save / reopen;
- preservation of the accepted Stage 1 creation UX and identity Transform.

## Deferred scope and overall non-acceptance

Stage 2 does not accept or claim completion of:

- dimension editing;
- numeric Path editing;
- an explicit ascent-reversal operator;
- transactional regeneration and invalid-edit rollback;
- managed-state diagnosis and operation policy;
- repair;
- Editable Mesh finalization and remaining lifecycle behavior;
- stepped or sloped underside and Side Boards;
- nosing, bevel, round, groove, or material-part assignment;
- L / U stairs, Landings, or Winders;
- Floor generation or Floor connection behavior.

Dimension and numeric Path editing, explicit ascent reversal, transactional
regeneration, state diagnosis, repair, and their Stage 3 lifecycle behavior
remain Stage 3 responsibilities. Stage 3 is **NOT STARTED**. Build 07-A overall
is **NOT YET ACCEPTED**.

## Acceptance conclusion

**Build 07-A Stage 1 — Canonical Stair + 2-point creation: ACCEPTED**

**Build 07-A Stage 2 — Layout calculation + basic geometry: ACCEPTED**

**Build 07-A Stage 3 — Editing + regeneration + rollback: NOT STARTED**

**Build 07-A overall: NOT YET ACCEPTED**

The runtime-tested Stage 2 production revision remains:

`cbca65810d0b9fdbc7636005607c36f9af9c1b0e`

with Git tree:

`cbb61de6e2d8528288bafdad33c260895eaadd6b`

Any later Acceptance Record-only commit changes documentation only and must not
be treated as a new runtime-tested production revision.
