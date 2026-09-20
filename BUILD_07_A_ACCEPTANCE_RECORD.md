# Build 07-A Acceptance Record

## Acceptance status

- **Build 07-A Stage 1 — Canonical Stair + 2-point creation: ACCEPTED**
- **Build 07-A Stage 2 — Layout calculation + basic geometry: ACCEPTED**
- **Build 07-A Stage 3 — Editing + regeneration + rollback: ACCEPTED**
- **Build 07-A Stage 4 — Lifecycle / Mesh exit / regression: NOT STARTED**
- **Build 07-A overall: NOT YET ACCEPTED**

Stage 3 acceptance does **not** mean that Build 07-A overall is accepted.
Editable Mesh finalization, Stair deletion, Stage 4 lifecycle completion, final
regression, and final Build 07-A acceptance remain Stage 4 work.

## Stage 3 runtime-tested production revision and artifact

- GitHub PR: `#13 — Implement Build 07-A Stage 3 stair editing and repair`
- Blender 5.2 LTS runtime-tested Stage 3 production revision:
  `cbb87af801ffa65655dd3be11fd8a3acfb809408`
- Runtime-tested production Git tree:
  `233afeb837a590e1a3ef5a2605a611e505aafa14`
- Runtime Candidate:
  `Japanese_House_Modeler_Build_07_A_Stage3_Candidate_r3.zip`
- Blender runtime: `Blender 5.2 LTS`
- Add-on version: `(0, 7, 0)`
- Add-on description:
  `Build 07-A: Stair Core + Top-view 2-point Straight Stair`

This Acceptance Record update changes documentation only. Its commit is not a
new runtime-tested production revision. The accepted Stage 3 production
behavior remains the exact revision and tree identified above.

## Stage 3 automated evidence

The final Stage 3 production tree
`233afeb837a590e1a3ef5a2605a611e505aafa14` had the following automated and
static results:

| Check | Result |
|---|---:|
| `python -B -m unittest tests.test_build_07_a_stage1` | **22 tests PASS** |
| `python -B -m unittest tests.test_build_07_a_stage2` | **17 tests PASS** |
| `python -B -m unittest tests.test_build_07_a_stage3` | **31 tests PASS** |
| `python -B -m unittest discover -s tests` | **433 tests PASS** |
| `python -m compileall -q japanese_house_modeler tests` | **PASS** |
| `git diff --check` | **PASS** |
| Working tree | **clean** |

Automated/static evidence is recorded separately from the Blender runtime
evidence below and is not treated as Blender runtime evidence.

## Earlier accepted-stage baselines

### Stage 1

Stage 1 remains accepted. Its runtime-tested production revision was
`b6c82e80906a9404288c759bcc0650ba07d3526e`, with Git tree
`471027e9071e78d94ef872b65f780d998a37e291` and runtime candidate
`Japanese_House_Modeler_Build_07_A_Stage1_Candidate_r1.zip`.

The accepted Stage 1 foundation includes canonical Stair properties, ordered
world-XY Path points, separate draw order and ascent direction, two-click
creation and preview, cancel and invalid-input safety, persistent UUIDs,
identity Object Transform, defaults snapshotting, selection behavior, Undo /
Redo, Save / reopen, and add-on lifecycle behavior.

### Stage 2

Stage 2 remains accepted. Its runtime-tested production revision was
`cbca65810d0b9fdbc7636005607c36f9af9c1b0e`, with Git tree
`cbb61de6e2d8528288bafdad33c260895eaadd6b` and runtime candidate
`Japanese_House_Modeler_Build_07_A_Stage2_Candidate_r1.zip`.

The accepted Stage 2 scope includes canonical layout resolution, derived
run/riser/going values, FORWARD and REVERSE layout, visible Tread and Riser
geometry, one Managed Stair as one Mesh Object, width symmetry, final Riser and
upper-arrival contracts, geometry validity, derived UI, creation Undo / Redo,
invalid-create rejection, and Save / reopen compatibility.

## Stage 3 Blender 5.2 LTS runtime acceptance

| Test | Runtime gate | Result | Evidence |
|---:|---|---|---|
| 0 | Candidate / metadata / registration | **PASS** | Candidate r3 loaded with version `(0, 7, 0)` and the specified description. `edit_stair_dimensions`, `edit_stair_path`, `reverse_stair_ascent`, `regenerate_stair`, and `repair_stair` were registered. |
| 1 | New Stair NORMAL diagnosis | **PASS** | New Stair was a managed MESH with UUID, two Path points, FORWARD ascent, 248 vertices / 186 faces, identity Transform, and NORMAL state. |
| 2 | Dimension edit transaction | **PASS** | One transaction changed base Z `0→500`, floor-to-floor `2800→3000`, riser count `16→18`, width `900→1000`, tread thickness `30→25`, and riser thickness `12→10` mm. The same Object and Stair ID remained; replacement geometry had 17 Treads, 18 Risers, 280 vertices / 210 faces, Z 500–3500 mm, and NORMAL state. |
| 3 | Exact 3600 mm Path edit | **PASS** | P0 `(0,0)` and P1 `(3600,0)` mm resolved run length 3600.0 mm, going 211.8 mm, and actual riser 166.7 mm for the edited 18-riser Stair. Stair ID remained unchanged and replacement Mesh state was NORMAL. |
| 4 | Path translation | **PASS** | P0 `(1000,2000)` and P1 `(4600,2000)` mm retained the 3600 mm run and all dimensions. Canonical Path moved the Stair while Object Transform remained identity. |
| 5 | Path plan rotation | **PASS** | P0 `(0,0)` and P1 `(0,3600)` mm retained 3600 mm run, resolved forward `(0,1,0)` and left `(-1,0,0)`, retained identity Transform, and remained NORMAL. |
| 6 | Ascent reversal | **PASS** | FORWARD→REVERSE preserved Stair ID, canonical Path order, run length, upper-arrival Z, dimensions, and identity Transform while replacing Mesh and reversing lower/upper and local axes correctly. |
| 7 | Ascent reversal Undo / Redo | **PASS** | REVERSE→operator FORWARD→Undo REVERSE→Redo FORWARD restored visible geometry correctly. Stair ID and Path remained unchanged. |
| 8 | Invalid floor-to-floor rollback | **PASS** | `floor_to_floor=0` produced the expected warning. Stair ID, Mesh datablock, Path, canonical dimensions, and NORMAL usability were unchanged. |
| 9 | Invalid zero-length Path rollback | **PASS** | P0=P1 produced `Stair Pathが短すぎます。`; Stair ID, Mesh, Path, and NORMAL state were unchanged. |
| 10 | Explicit regeneration | **PASS** | Canonical values and Stair ID remained unchanged; Mesh was replaced with 280 vertices / 210 faces, Transform remained identity, and state remained NORMAL. |
| 11 | TRANSFORM_CHANGED diagnosis and gate | **PASS** | Manual X `+5 m` produced TRANSFORM_CHANGED. Normal UI actions were disabled, Repair enabled, and direct regenerate returned CANCELLED with warning and no Mesh/canonical/ID mutation. |
| 12 | Transform Repair | **PASS** | Repair discarded the manual Transform rather than baking it into Path. It preserved Stair ID and canonical Path, regenerated 280 / 210 geometry, restored identity Transform, and returned to NORMAL. |
| 13 | Single Material preservation | **PASS** | Explicit regeneration retained one slot containing the same `Stage3 Test Material` datablock on the replacement Mesh. |
| 14 | Empty-Mesh GEOMETRY_MISSING Repair | **PASS** | A valid Managed MESH with empty geometry diagnosed GEOMETRY_MISSING. Normal actions were disabled and Repair enabled. Repair preserved canonical data, ID, Material, and identity Transform; regenerated 280 / 210 geometry; and returned to NORMAL. |
| 15 | ID_CONFLICT diagnosis / Repair | **PASS** | Shift+D duplicates diagnosed ID_CONFLICT. Repair on the selected duplicate preserved the original ID, issued a new UUID only to the duplicate, replaced its Mesh, preserved Material, and returned both Stairs to NORMAL. |
| 16-r3 | OBJECT_TYPE_CHANGED policy | **PASS** | A Managed CURVE diagnosed OBJECT_TYPE_CHANGED. Normal actions and Repair were disabled. Direct Repair returned CANCELLED with warning; Object remained CURVE and no state mutated. |
| 17 | r3 Mesh→Mesh regression | **PASS** | Explicit regeneration after the r3 correction replaced the Mesh while preserving ID, Path, 280 / 210 geometry, Material, and NORMAL state. |
| 18 | ID_MISSING diagnosis / Repair | **PASS** | Clearing `stair_id` diagnosed ID_MISSING. Normal actions were disabled and Repair enabled. Repair generated a new UUID, replaced Mesh, preserved Material, regenerated 280 / 210 geometry, and returned to NORMAL. |
| 19 | INVALID_CANONICAL refusal | **PASS** | Reducing Path to one point diagnosed INVALID_CANONICAL. Repair was disabled and direct Repair returned CANCELLED. Invalid Path was neither guessed nor reconstructed from Mesh; ID and Mesh remained unchanged. |
| 20 | Invalid tread-thickness rollback | **PASS** | With actual riser about 166.7 mm, tread thickness 200 mm was rejected with the expected warning. ID, Mesh, Path, canonical values, and NORMAL state remained unchanged. |
| 21 | Invalid riser-thickness rollback | **PASS** | With going about 211.8 mm, riser thickness 250 mm was rejected with the expected warning. ID, Mesh, Path, canonical values, and NORMAL state remained unchanged. |
| 22 | Save / full exit / reopen | **PASS** | Managed state, Stair ID, Path, ascent, all dimensions, 280 / 210 geometry, one Material slot, identity Transform, and NORMAL state survived full Blender exit and reopen. |
| 23 | Dimension edit Undo / Redo | **PASS** | Width `1000→1100→Undo 1000→Redo 1100` updated visible geometry and UI correctly. ID and Path remained unchanged; geometry was 280 / 210, Material preserved, and state NORMAL. |
| 24 | Repair Undo / Redo | **PASS** | From manual X `+5 m`, Repair produced NORMAL at canonical position, Undo restored TRANSFORM_CHANGED / +5 m, and Redo restored NORMAL at canonical position. Final identity Transform, width 1100, 280 / 210 geometry, and Material were correct. |
| 25 | Invalid riser-count rollback | **PASS** | `riser_count=1` was rejected with the expected warning. ID, Mesh, Path, canonical values, Material, and NORMAL state remained unchanged. |
| 26 | Path edit Undo / Redo | **PASS** | Path `(0,0)→(0,3.6)` m was translated to `(1,1)→(1,4.6)` m; Undo restored the old Path and Redo restored the new Path. Final ID, 280 / 210 geometry, Material, identity Transform, and NORMAL state were correct. |
| 27 | Forced commit failure after Mesh swap | **PASS** | An injected exception after canonical commit began returned CANCELLED. Original Mesh, ID, Path, dimensions, ascent, and Transform were restored; replacement Mesh was removed; Mesh count was unchanged; state was NORMAL. |
| 28 | Forced Repair prepare failure | **PASS** | Injected `_prepare_candidate` failure on a TRANSFORM_CHANGED Stair returned CANCELLED before Scene mutation. Old Mesh, ID, Path, canonical values, X `+5 m` Transform, Mesh count, and TRANSFORM_CHANGED state remained unchanged. |
| 29 | Usability after failed Repair | **PASS** | After restoring normal preparation, the same Stair repaired successfully to identity Transform, 280 / 210 geometry, one Material slot, and NORMAL state. |

## Runtime defect history and final Stage 3 policy

Candidate r1 and r2 exposed a Blender 5.2 LTS restriction: a CURVE Object
cannot be changed to a Mesh merely by assigning a Mesh datablock to
`Object.data`, including an attempted temporary `data=None` detach path.
Blender reported `Object.data expected a Curve type, not Mesh`.

Both candidates demonstrated safe rollback: the old Curve data, canonical Path,
Stair ID, and relevant Transform state remained intact after failure.

Candidate r3 established the final accepted Stage 3 policy:

- Managed MESH Object with missing or empty generated geometry:
  `GEOMETRY_MISSING`, Repairable from canonical data.
- Non-MESH Managed Stair Object:
  `OBJECT_TYPE_CHANGED`, not Repairable in Stage 3.
- `OBJECT_TYPE_CHANGED` denies dimension edit, Path edit, ascent reversal,
  regeneration, future finalize, and Repair; future Delete remains allowed by
  policy.
- No `bpy.ops.object.convert`, replacement Object creation, Mesh reverse
  inference, or automatic type conversion is used.

## Stage 3 accepted scope

Stage 3 acceptance covers:

- Managed Stair diagnosis and NORMAL / abnormal operation policy;
- `ID_MISSING`, `ID_CONFLICT`, `TRANSFORM_CHANGED`, `INVALID_CANONICAL`,
  `GEOMETRY_MISSING`, and `OBJECT_TYPE_CHANGED`;
- dimension editor and numeric Path editor;
- explicit ascent reversal and explicit regeneration;
- replacement Mesh transaction;
- invalid-edit rollback and commit-failure rollback;
- Repair prepare-failure safety and continued usability after failure;
- Transform Repair without baking Transform into canonical Path;
- ID-conflict Repair and missing-ID Repair;
- empty-Mesh `GEOMETRY_MISSING` Repair;
- non-Mesh `OBJECT_TYPE_CHANGED` refusal;
- single Material preservation;
- Undo / Redo for Stage 3 editing and Repair;
- Save / reopen compatibility;
- Stair ID persistence for normal editing;
- canonical Path persistence; and
- Object Transform identity contract.

## Stage 4 deferred scope and overall non-acceptance

Stage 4 remains **NOT STARTED** and is responsible for:

- Editable Mesh finalization;
- Stair deletion;
- Stage 4 lifecycle completion;
- complete Build 07-A regression;
- prior-Build regression at the final 07-A gate; and
- final Build 07-A acceptance.

Stage 3 does not accept or introduce stepped/sloped underside, Side Boards,
nosing, part-specific Materials, multi-point Stairs, Landings, Winders, or Floor
connections.

## Acceptance conclusion

**Build 07-A Stage 1 — Canonical Stair + 2-point creation: ACCEPTED**

**Build 07-A Stage 2 — Layout calculation + basic geometry: ACCEPTED**

**Build 07-A Stage 3 — Editing + regeneration + rollback: ACCEPTED**

**Build 07-A Stage 4 — Lifecycle / Mesh exit / regression: NOT STARTED**

**Build 07-A overall: NOT YET ACCEPTED**

The runtime-tested Stage 3 production revision remains:

`cbb87af801ffa65655dd3be11fd8a3acfb809408`

with production Git tree:

`233afeb837a590e1a3ef5a2605a611e505aafa14`

Any Acceptance Record-only commit changes documentation only and must not be
treated as a new runtime-tested production revision.
