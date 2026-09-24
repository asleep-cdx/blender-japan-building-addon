# Build 07-B Acceptance Record

Date: 2026-09-24

## Final acceptance status

- **Build 07-B Stage 1 — Residential Foundation / Compatibility: ACCEPTED**
- **Build 07-B Stage 2 — corrected STEPPED_CLOSED body + Tread/Riser junction follow-up: ACCEPTED**
- **Build 07-B Stage 3 — Side Boards + Part Materials: ACCEPTED**
- **Build 07-B Stage 4 — Lifecycle / Full Regression: ACCEPTED**
- **Build 07-B overall: ACCEPTED**

This file is the current Build 07-B acceptance authority.

The pre-Stage-4 consolidated record is retained verbatim as
`BUILD_07_B_ACCEPTANCE_RECORD_PRE_STAGE4.md` for historical Stage 1 / Stage 2 /
correction evidence. The authoritative Stage 3 detail remains in
`BUILD_07_B_STAGE3_ACCEPTANCE.md`. The corrected geometry contract remains governed
by `BUILD_07_B_CORRECTION_ADDENDUM.md` where it supersedes earlier historical Stage 2
wording.

## Accepted runtime production and Candidate identity

Build 07-B Stage 4 added regression tests and a runtime procedure only. No file under
`japanese_house_modeler/` changed in the Stage 4 implementation PR. Therefore the
accepted production implementation remains the Stage 3 r7 production content, while
the Stage 4 Candidate proves that exact production content through the final lifecycle
and full-regression gate.

### Production implementation authority

- Stage 3 PR: `#20 — Build 07-B Stage 3: Side Boards and part materials`
- Runtime-tested production commit: `3fa5cf549be163eac4e1c0113b96cc5d20e6b503`
- Runtime-tested production tree: `a6737816263c3c048c39ae5ee5f8d3b69190c109`
- Stage 3 accepted Candidate: `Japanese_House_Modeler_Build_07_B_Stage3_Candidate_r7.zip`
- Stage 3 Candidate size: `116056 bytes`
- Stage 3 Candidate SHA256: `8C69B2B66FB53998949FEAAA35FED5D24BAB6922BEDC9FE05CF6CC7D8F36A1A4`

### Final Stage 4 runtime Candidate

- Stage 4 PR: `#21 — Add Build 07-B Stage 4 lifecycle regression tests and runtime procedure`
- Runtime-tested Stage 4 Candidate commit: `0b593d8099e8bff46b8b4daba252d8d6dcf5c7c0`
- Runtime-tested Stage 4 Candidate tree: `e712ddd975231faa21264b0d710cec9882879851`
- Candidate: `Japanese_House_Modeler_Build_07_B_Stage4_Candidate_r1.zip`
- Candidate size: `116056 bytes`
- Candidate SHA256: `B1DBD6BEF6D85AC8DEBBA8698196830D4BB43DF831DA01EB1A2560659874760F`
- Runtime environment: Blender `5.2.0 LTS`
- Add-on version: `(0, 7, 1)`
- Description: `Build 07-B: Standard Residential Straight Stair`

The Stage 4 acceptance/documentation commit is intentionally **not** treated as a new
runtime production revision.

## Stage 4 automated evidence

The Stage 4 implementation report recorded all checks passing:

| Check | Result |
|---|---:|
| `python -m unittest tests.test_build_07_a_stage1` | **22 PASS** |
| `python -m unittest tests.test_build_07_a_stage2` | **17 PASS** |
| `python -m unittest tests.test_build_07_a_stage3` | **31 PASS** |
| `python -m unittest tests.test_build_07_a_stage4` | **14 PASS** |
| `python -m unittest tests.test_build_07_b_stage1` | **18 PASS** |
| `python -m unittest tests.test_build_07_b_stage2` | **13 PASS** |
| `python -m unittest tests.test_build_07_b_stage2_correction` | **13 PASS** |
| `python -m unittest tests.test_build_07_b_stage2_followup` | **8 PASS** |
| `python -m unittest tests.test_build_07_b_stage3` | **23 PASS** |
| `python -m unittest tests.test_build_07_b_stage4` | **23 PASS** |
| `python -m unittest discover -s tests` | **545 PASS** |
| `python -m compileall -q japanese_house_modeler tests` | **PASS** |
| `git diff --check` | **PASS** |
| Working tree after implementation commit | **clean** |

The Stage 4 structural test that previously prohibited all future geometry identifiers
was corrected before runtime acceptance. It was replaced by a compatibility test that
locks the Build 07-B Residential default to `STEPPED_CLOSED` without blocking future
07-C geometry modes. This was a test-suite forward-compatibility correction, not a
production defect.

## Blender 5.2 LTS Stage 4 runtime acceptance

All numbered gates in `BUILD_07_B_STAGE4_RUNTIME_TEST.md` completed successfully.

| Test | Runtime gate | Result |
|---:|---|---:|
| 0 | Candidate identity | **PASS** |
| 1 | Residential creation + creation Undo/Redo | **PASS** |
| 2 | Dimension edit + Undo/Redo | **PASS** |
| 3 | Invalid dimension prepare rejection / atomic preservation | **PASS** |
| 4 | Oblique Path edit + Undo/Redo | **PASS** |
| 5 | Reverse + semantic LEFT/RIGHT | **PASS** |
| 6 | 07-A BASIC load / ordinary operations / save-reopen compatibility | **PASS** |
| 7 | Explicit BASIC → Residential conversion + Undo/Redo | **PASS** |
| 8 | Residential settings + Undo/Redo | **PASS** |
| 9 | Material Case A + Undo/Redo | **PASS** |
| 10 | Material Case B / true unassigned slot | **PASS** |
| 11 | Material Case C / all unassigned | **PASS** |
| 12 | Material lifecycle chain | **PASS** |
| 13 | Residential Regenerate | **PASS** |
| 14 | `GEOMETRY_MISSING` Repair + Undo/Redo | **PASS** |
| 15 | Duplicate ID Repair + Undo/Redo | **PASS** |
| 16 | Transform Repair + Undo/Redo | **PASS** |
| 17 | Abnormal-state operation gates | **PASS** |
| 18 | Forced prepare failure rollback | **PASS** |
| 19 | Forced commit failure rollback | **PASS** |
| 20 | Nontrivial save / full exit / reopen | **PASS** |
| 21 | Editable Mesh finalization + Undo/Redo + free vertex editing | **PASS** |
| 22 | Normal and abnormal active-only Delete + Undo/Redo | **PASS** |
| 23 | Final Build 07-A BASIC regression | **PASS** |
| 24 | Wall / Finish focused smoke regression | **PASS** |
| 25 | Final visual, numerical, topology and Material acceptance | **PASS** |

## Key Stage 4 runtime evidence

### Residential lifecycle and persistence

- New Stair remained `STANDARD_RESIDENTIAL`, schema 2, and normally managed.
- Dimension, oblique Path, Reverse, Residential settings and Regenerate preserved the
  canonical mode/schema/ID/settings and regenerated the accepted geometry.
- Save → full Blender exit → reopen preserved a nontrivial Residential state including
  oblique Path, `REVERSE`, nonzero `base_z`, non-default Side Board settings, Materials,
  identity Object transform, and NORMAL diagnosis.
- `GEOMETRY_MISSING` Repair restored the full geometry and Materials; Undo returned to
  the missing-geometry state and Redo restored it again.
- Duplicate `stair_id` created by ordinary `Shift+D` was diagnosed as `ID_CONFLICT`;
  Repair assigned a new ID only to the repaired duplicate and preserved the source ID.
- Move/rotate/non-uniform-scale produced `TRANSFORM_CHANGED`; Repair restored identity
  transform while preserving ID, canonical state, geometry and Materials.

### Operation gates and rollback

- `INVALID_CANONICAL`, `GEOMETRY_MISSING`, `ID_CONFLICT`, and
  `TRANSFORM_CHANGED` gates behaved as specified.
- Normal edit/regenerate/finalize operations were blocked while abnormal.
- Repair was available only for recoverable states; `INVALID_CANONICAL` remained
  non-repairable.
- Delete remained available for managed abnormal states.
- Forced prepare failure returned `CANCELLED` with original Mesh, canonical state, ID,
  transform and counts unchanged.
- Forced commit failure after Mesh swap returned `CANCELLED`; rollback restored the
  original Mesh, canonical state, ID, transform and Material slots, and left no extra
  Mesh datablock.

### Materials

Case A:

- Base `Wood`
- Tread override `None`
- Riser override `White`
- Underside override `None`
- Side Board override `None`
- effective slots `['Wood', 'White']`
- Tread / Underside / Side Board resolve to Wood; Riser resolves to White.

Case B:

- Base `None`, Tread `Wood`, every other override `None`
- slots `['Wood', None]`
- unassigned Riser / Underside / Side Board roles did not borrow Wood.

Case C:

- all five Material pointers `None`
- no Material slots were created.

Material pointers, slots and role assignments survived Regenerate, dimension edit,
Reverse, save/reopen, Repair and Finalize.

### Final Residential geometry and topology

Accepted BOTH-board final sample:

- vertices: `620`
- edges: `1284`
- faces: `732`
- boundary edges: `0`
- non-manifold edges: `0`
- zero-area faces: `0`
- all vertex coordinates finite: `True`
- minimum Z equals `base_z`
- maximum Z equals `H`
- maximum local run X equals `L+r`
- final numerical gate: `Z_OK=True`, `X_OK=True`, `ISSUES=()`.

Visual acceptance confirmed:

- continuous `STEPPED_CLOSED` soffit;
- no exposed Tread/Riser backs or visible internal stair cavity;
- flat lower termination with no micro-notch recurrence;
- accepted r7 upper termination with horizontal top and vertical rear edge;
- no spike, giant triangle or diagonal rear plate;
- BOTH, LEFT-only, RIGHT-only and OFF/OFF Side Board configurations remain coherent;
- the closed body remains valid with Side Boards disabled;
- FORWARD / REVERSE and oblique Path behavior remain coherent;
- visibly distinct Material roles remain correct.

### BASIC / Build 07-A compatibility

Final regression reconfirmed:

- `BASIC_TREAD_RISER`, schema 1 remains BASIC under ordinary operations;
- 2800 mm / 16 risers resolves to 175 mm actual rise;
- accepted BASIC geometry remains `248 vertices / 186 faces`;
- dimension edit, Path, Reverse, Regenerate, invalid-edit rollback, ID diagnosis,
  Transform Repair, Material preservation, save/reopen, Undo/Redo, Finalize and
  active-only Delete all remained compatible;
- no BASIC operation silently added the Residential body or Side Boards.

### Wall / Finish isolation

A managed scene containing 3 Walls and 2 Finishes was snapshotted. After Stair create,
dimension edit, Path edit, Reverse, Repair and Finalize, every Wall/Finish snapshot
comparison remained `True`. Visual inspection also retained normally managed Finish
geometry and spans.

## Runtime procedure notes

The following observations were test-procedure issues and are **not production defects**:

1. An initial attempt to create `INVALID_CANONICAL` by assigning `riser_count=1` was
   clamped by Blender RNA to the property minimum of 2. Repair then correctly rebuilt
   geometry from that modified canonical value, which temporarily looked like a
   malformed stair. The invalid-canonical gate was rerun correctly by making the two
   canonical Path points identical; `INVALID_CANONICAL` was diagnosed and the expected
   UI gates passed. A fresh normal 16-riser Stair also reconfirmed ordinary G-move →
   Transform Repair with correct geometry.
2. Forced-failure tests 18 and 19 were executed through shorter Python Console
   monkeypatch commands rather than the original Text Editor presentation because that
   UI procedure was cumbersome. The same production helpers were patched, restored,
   and the required rollback invariants passed.
3. In the final BASIC active-only Delete regression, the temporary test Material could
   disappear after Blender Undo/Redo orphan lifecycle once no Object referenced it.
   The JHM Delete operator did not directly delete Mesh or Material datablocks; the
   active-only Object deletion contract and unrelated-object preservation passed.

## Build 07-B accepted scope

Build 07-B now accepts the complete Standard Residential Straight Stair workflow on the
07-A two-point straight Path foundation:

- user-visible Residential creation;
- explicit BASIC → Residential conversion;
- corrected closed stepped residential body;
- Residential Tread extension through the next Riser and clean right-angle junction;
- full-depth external LEFT / RIGHT Side Boards with independent enable switches;
- Side Board reveal and thickness controls;
- accepted lower and upper terminations;
- part Material base + role override + true UNASSIGNED semantics;
- dimension / Path / Reverse / Regenerate lifecycle;
- managed-state diagnosis and Repair;
- duplicate-ID handling;
- transactional pre-prepare and commit rollback;
- save/reopen persistence;
- Undo/Redo lifecycle;
- Editable Mesh finalization;
- active-only Delete;
- 07-A BASIC compatibility;
- Wall / Finish isolation regression.

## Deferred beyond Build 07-B

The following are not part of Build 07-B acceptance:

- `SLOPED_CLOSED` underside;
- sloped closed Side Board geometry;
- tread-front nosing / overhang;
- front-edge Bevel / Round variants;
- user-facing closed-body depth control;
- Multi-point Path;
- L/U turns and Landing;
- Winder / 廻り段;
- later open/support variants.

The straight-stair follow-up is Build 07-C. See `BUILD_07_C_PLANNING_NOTE.md` and the
project roadmap for the planned scope.
