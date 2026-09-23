# Build 07-B Stage 3 Acceptance

Date: 2026-09-23

## Status

**Build 07-B Stage 3 — Side Boards + Part Materials: ACCEPTED**

Stage 4 lifecycle/full-regression work remains pending. Build 07-B overall is therefore not yet accepted.

## Accepted production revision

- PR: `#20 — Build 07-B Stage 3: Side Boards and part materials`
- Runtime-tested GitHub production commit: `3fa5cf549be163eac4e1c0113b96cc5d20e6b503`
- Runtime-tested production tree: `a6737816263c3c048c39ae5ee5f8d3b69190c109`
- Candidate: `Japanese_House_Modeler_Build_07_B_Stage3_Candidate_r7.zip`
- Candidate size: `116056 bytes`
- Candidate SHA256: `8C69B2B66FB53998949FEAAA35FED5D24BAB6922BEDC9FE05CF6CC7D8F36A1A4`
- Runtime environment: Blender 5.2 LTS

## Accepted Side Board contract

The final accepted Stage 3 Side Board is the full-depth external residential Side Board variant.

Default 900 mm stair / 18 mm Side Board thickness:

- Body: `[-0.450, +0.450]` m local Y
- LEFT Side Board: `[+0.450, +0.468]` m
- RIGHT Side Board: `[-0.468, -0.450]` m
- BOTH finished width: 936 mm

Canonical Side Board fields:

- `left_side_board_enabled`
- `right_side_board_enabled`
- `side_board_thickness_mm` default 18 mm
- `side_board_reveal_mm` default 40 mm

`side_board_profile_width_mm` is superseded and is not part of the accepted production canonical contract.

The Side Board lower contour reuses the accepted Stage 2 analytical closed-body lower silhouette. The first-step Side Board minimum Z equals `base_z` and does not extend below the body.

The accepted upper termination ends at the Final Riser rear plane:

- upper rear: `(L+r, H)`
- lower rear: same `X=L+r`
- rear edge: vertical
- no diagonal closing spike / giant triangle

## Geometry counts

| Configuration | Vertices | Faces |
|---|---:|---:|
| BASIC | 248 | 186 |
| STANDARD_RESIDENTIAL BOTH | 620 | 732 |
| LEFT-only | 494 | 547 |
| RIGHT-only | 494 | 547 |
| OFF/OFF | 368 | 362 |

OFF/OFF remains identical to the accepted Stage 2 closed body.

## Automated evidence

The Candidate r7 implementation report recorded:

| Check | Result |
|---|---:|
| `python -m unittest tests.test_build_07_a_stage1` | 22 PASS |
| `python -m unittest tests.test_build_07_a_stage2` | 17 PASS |
| `python -m unittest tests.test_build_07_a_stage3` | 31 PASS |
| `python -m unittest tests.test_build_07_a_stage4` | 14 PASS |
| `python -m unittest tests.test_build_07_b_stage1` | 18 PASS |
| `python -m unittest tests.test_build_07_b_stage2` | 13 PASS |
| `python -m unittest tests.test_build_07_b_stage2_correction` | 13 PASS |
| `python -m unittest tests.test_build_07_b_stage2_followup` | 8 PASS |
| `python -m unittest tests.test_build_07_b_stage3` | 23 PASS |
| `python -m unittest discover -s tests` | 522 PASS |
| `python -m compileall -q japanese_house_modeler tests` | PASS |
| `git diff --check` | PASS |
| Working tree | clean |

## Blender 5.2 LTS runtime acceptance

The following runtime gates passed on Candidate r7:

- new Residential default state: schema 2, BOTH boards, reveal 40 mm, 620 / 732, no managed-state issues;
- full-depth Side Board visual appearance;
- corrected upper termination, including exact `max X = L+r`, `max Z = H`, vertical rear edge and no r6 spike/triangle;
- first-step Side Board and body minimum Z both equal `base_z`;
- 936 mm default finished width with external 18 mm Side Boards;
- reveal 40→60 changes Side Board geometry only, leaving body fragments unchanged;
- Side Board thickness 18→24 changes only local-Y extent, not local-XZ profile;
- LEFT-only 494 / 547;
- RIGHT-only 494 / 547;
- OFF/OFF 368 / 362 with accepted Stage 2 body preserved;
- Reverse preserves canonical LEFT/RIGHT semantics and moves the boards to the corresponding world side;
- oblique Path support;
- nonzero `base_z` support;
- Stage 2 tread/riser 90-degree junction, micro-notch correction and stepped soffit preserved;
- Material Case A spot regression: Wood base, White Riser override, stable two-slot assignment;
- Regenerate preserves geometry and Materials;
- Save, full Blender exit and reopen preserve geometry, canonical state and Materials;
- `GEOMETRY_MISSING` Repair restores 620 / 732 full-depth geometry and Materials;
- Side Board reveal edit Undo/Redo works without damaging upper/lower termination;
- final Mesh health: 620 vertices, 1284 edges, 732 faces, zero non-manifold edges, zero boundary edges, zero zero-area faces, all coordinates finite.

## Material/UI contract

Accepted Stage 3 also includes:

- user-visible `STANDARD_RESIDENTIAL` creation,
- explicit BASIC→Residential conversion,
- Residential settings UI,
- five-part Material editing UI using operator `StringProperty` + `prop_search`,
- canonical Material PointerProperties,
- role order `TREAD`, `RISER`, `UNDERSIDE`, `SIDE_BOARD`,
- override → base → UNASSIGNED resolution,
- identity-based slot deduplication,
- mixed assigned/unassigned empty-slot support,
- all-unassigned = no material slots,
- stale nonempty Material name rejected before transaction without Scene mutation.

## Deferred to 07-C

Stage 3 does not add:

- `SLOPED_CLOSED`,
- sloped Side Board production geometry,
- tread-front overhang / nosing,
- front-edge Bevel / Round,
- user-facing closed-body depth control,
- Landing / Winder / Multi-point Path.

See `BUILD_07_C_PLANNING_NOTE.md` for the agreed straight-stair follow-up items.
