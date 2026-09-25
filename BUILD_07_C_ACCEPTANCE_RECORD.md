# BUILD 07-C ACCEPTANCE RECORD
## Japanese House Modeler — Sloped Closed Underside + Straight Stair Finish Variants

Date: 2026-09-25

## 1. Status

- Build 07-C Stage 1 — **ACCEPTED**
- Build 07-C Stage 2 — **ACCEPTED**
- Build 07-C overall — **IN PROGRESS**
- Next implementation stage — **Stage 3: 5 mm nosing + SQUARE / BEVEL / ROUND**

Stage 1 acceptance covers foundation / compatibility / schema 3 plumbing and the user-facing stair-body thickness control.
Stage 2 acceptance adds production acceptance of `SLOPED_CLOSED` body geometry and `SLOPED` Side Board geometry. It does **not** accept Stage 3 finish geometry or final 07-C practical-placement / lifecycle scope.

## 2. Runtime-tested production revisions

### Stage 1

GitHub PR: #22

Runtime-tested exact production revision:

```text
commit 6482062def1fdca769c179dacb93f727dd4f8237
tree   a681502fa8c107c77e10a0a4323c3c8e053740af
```

Codex local report used a different commit SHA after its workspace operation, but reported the same tree SHA. Content identity was therefore established by tree equality.

Runtime Candidate:

```text
Japanese_House_Modeler_Build_07_C_Stage1_Candidate_r1.zip
SIZE    116967 bytes
SHA256  218a6af7b690c8a501f499e463a135b441fe3a47159d4ca0080588ad99ed3829
```

### Stage 2

GitHub PR: #23

Runtime-tested exact production revision:

```text
commit 63b498a3391ced44a8e6e88468ce4aea3f0425ae
tree   4e77af7f5c71727e006465d1d108e1d9cadd966c
```

Runtime Candidate:

```text
Japanese_House_Modeler_Build_07_C_Stage2_Candidate_r3.zip
SIZE    117682 bytes
SHA256  ad25b539dbcc9878c7e3b5eebe3052bdd0f88acc1d6022fc73a9bd4015345e9b
```

Runtime environment for accepted Stage 1 / Stage 2 evidence:

```text
Blender 5.2.0 LTS
Add-on version: (0, 7, 2)
Description: Build 07-C: Sloped Closed Underside + Straight Stair Finish Variants
```

## 3. Automated evidence

### Stage 1 accepted tree

```text
tests.test_build_07_a_stage1              22 PASS
tests.test_build_07_a_stage2              17 PASS
tests.test_build_07_a_stage3              31 PASS
tests.test_build_07_a_stage4              14 PASS
tests.test_build_07_b_stage1              18 PASS
tests.test_build_07_b_stage2              13 PASS
tests.test_build_07_b_stage2_correction   13 PASS
tests.test_build_07_b_stage2_followup      8 PASS
tests.test_build_07_b_stage3              23 PASS
tests.test_build_07_b_stage4              23 PASS
tests.test_build_07_c_stage1              20 PASS
full unittest discovery                  565 PASS
compileall                               PASS
git diff --check                         PASS
```

`stair_residential_geometry.py` was not changed in Stage 1. No SLOPED_CLOSED, SLOPED Side Board, nosing, BEVEL, or ROUND production geometry was introduced.

### Stage 2 final candidate

```text
tests.test_build_07_c_stage2              24 PASS
full unittest discovery                  589 PASS
compileall                               PASS
git diff --check                         PASS
```

## 4. Stage 1 resolved pre-acceptance review issue

Initial Stage 1 implementation bumped an existing schema-2 Residential Stair to schema 3 whenever the Residential settings dialog committed, including edits to legacy 07-B fields.

This was corrected before runtime acceptance.

Accepted policy:

- schema 2 + legacy 07-B Residential field edit -> remain schema 2
- schema 2 + dialog no-op -> remain schema 2
- schema 2 + `side_board_band_width_mm` / user-facing stair-body thickness change -> schema 3
- existing schema 3 -> remain schema 3
- new 07-C Residential Stair -> schema 3
- explicit BASIC -> Residential Apply -> schema 3

The accepted implementation uses `schema_version_after_residential_edit()` and limits the Stage 1 migration trigger to `side_board_band_width_mm`.

## 5. Stage 1 Blender runtime evidence

All Stage 1 runtime gates passed in Blender 5.2 LTS.

### Test 0 — Candidate identity — PASS

Confirmed:

```text
Blender 5.2.0 LTS
version (0, 7, 2)
description Build 07-C: Sloped Closed Underside + Straight Stair Finish Variants
```

### Test 1 — New Stage 1 Residential Stair — PASS

Confirmed:

```text
MODE=STANDARD_RESIDENTIAL
SCHEMA=3
UNDERSIDE=STEPPED_CLOSED
BOARD_MODE=STEPPED
BODY_DEPTH=150.0
OVERHANG=0.0
EDGE=SQUARE
EDGE_SIZE=5.0
BOARDS=(True, True)
VERTS=620
FACES=732
ISSUES=()
```

Visual geometry remained the accepted 07-B default: stepped closed body, stepped Side Boards, no nosing, no BEVEL/ROUND geometry.

### Test 2 — Existing 07-B schema-2 load compatibility — PASS

Opening a saved 07-B Residential Stair preserved:

```text
SCHEMA=2
UNDERSIDE=STEPPED_CLOSED
BOARD_MODE=STEPPED
BODY_DEPTH=150.0
OVERHANG=0.0
EDGE=SQUARE
EDGE_SIZE=5.0
VERTS=620
FACES=732
ISSUES=()
```

No silent nosing, board-shape, body-shape, Path, ID, or Material migration was observed.

### Test 3 — schema-2 ordinary Regenerate — PASS

Regenerate preserved schema 2, Path, Stair ID, board state, accepted 620/732 geometry, and `ISSUES=()`.

### Test 4 — schema migration / stair-body thickness — PASS

Sub-gates:

1. legacy Side Board thickness edit on schema 2 -> schema 2 preserved
2. body depth `150 -> 120 mm` -> schema 3
3. no-op dialog commit -> schema 2 preserved
4. Undo/Redo for the body-depth edit passed
5. visual stepped body became thinner at 120 mm without geometry breakage

Accepted body-depth edit result included:

```text
SCHEMA=3
BODY_DEPTH=120.0
VERTS=620
FACES=732
ISSUES=()
```

### Test 5 — Invalid body depth atomic rejection — PASS

Submitting 175 mm where actual riser was 175 mm produced the expected validation warning.

Post-rejection evidence:

```text
SAME_MESH=True
SAME_STATE=True
SCHEMA=2
BODY_DEPTH=150.0
VERTS=620
FACES=732
ISSUES=()
```

### Test 6 — Save / full exit / reopen — PASS

After changing body depth to 120 mm, saving, fully exiting Blender, and reopening:

```text
SCHEMA=3
BODY_DEPTH=120.0
LOC=(0,0,0)
ROT=(0,0,0)
SCALE=(1,1,1)
VERTS=620
FACES=732
ISSUES=()
```

Stair ID and canonical state were preserved.

### Test 7 — BASIC compatibility — PASS

Baseline confirmed:

```text
MODE=BASIC_TREAD_RISER
SCHEMA=1
VERTS=248
FACES=186
ISSUES=()
```

Supplemental final BASIC gate exercised Dimension, Path, Reverse, Regenerate, Transform Repair, save, full exit, and reopen. Final evidence remained:

```text
MODE=BASIC_TREAD_RISER
SCHEMA=1
LOC=(0,0,0)
ROT=(0,0,0)
SCALE=(1,1,1)
VERTS=248
FACES=186
ISSUES=()
```

### Test 8 — BASIC -> Residential Apply / Undo / Redo — PASS

Redo result:

```text
MODE=STANDARD_RESIDENTIAL
SCHEMA=3
UNDERSIDE=STEPPED_CLOSED
BOARD_MODE=STEPPED
BODY_DEPTH=150.0
OVERHANG=0.0
EDGE=SQUARE
EDGE_SIZE=5.0
VERTS=620
FACES=732
ISSUES=()
```

Supplemental exact Undo gate captured a BASIC snapshot before Apply and confirmed:

```text
UNDO_EXACT_BASIC=True
MODE=BASIC_TREAD_RISER
SCHEMA=1
VERTS=248
FACES=186
```

### Test 9 — Material preservation — PASS

Material Case A style state:

```text
PTRS=('Wood', None, 'White', None, None)
SLOTS=['Wood', 'White']
```

After body-depth `150 -> 120 mm` and Regenerate:

```text
SCHEMA=3
BODY_DEPTH=120.0
PTRS=('Wood', None, 'White', None, None)
SLOTS=['Wood', 'White']
COUNTS={0:636, 1:96}
VERTS=620
FACES=732
ISSUES=()
```

### Test 10 — Transform Repair + Undo/Redo — PASS

After intentional transform corruption, Repair, Undo, and Redo:

```text
SCHEMA=3
BODY_DEPTH=120.0
LOC=(0,0,0)
ROT=(0,0,0)
SCALE=(1,1,1)
PTRS=('Wood', None, 'White', None, None)
SLOTS=['Wood', 'White']
VERTS=620
FACES=732
ISSUES=()
```

### Test 11 — Wall / Finish isolation — PASS

Scene contained 3 Walls and 2 Finishes. After Stair creation, body-depth edit, Regenerate, transform corruption, and Repair:

```text
WALL_UNCHANGED=True
FINISH_UNCHANGED=True
WALLS=3
FINISHES=2
```

## 6. Stage 2 correction history

Stage 2 required two Blender runtime corrections before acceptance.

### Candidate r1 — rejected

Blender runtime review found:

- `SLOPED_CLOSED` visible soffit became too steep toward the upper end.
- `SLOPED` Side Board silhouette did not match the human-confirmed target.

The body slope was corrected so the main visible soffit is parallel to the canonical `actual_riser / going` pitch, while the accepted contact profile and closed full-width body construction were retained.

### Candidate r2 — rejected

Candidate r2 corrected the body slope and separated Side Board upper/lower responsibilities:

- `side_board_mode` selects the upper visible profile family.
- `underside_mode` selects the lower profile family.

Runtime review then found one remaining defect: the `SLOPED` Side Board main upper run and horizontal cap ended directly at `H`, so the Side Board had no visible rise above the top landing.

### Candidate r3 — accepted

The accepted five-point SLOPED upper profile is:

```text
A = (-reveal, B)
B = (-reveal, B + h + reveal)
C = (L - reveal, H + reveal)
D = (L + r, H + reveal)
E = (L + r, H)
```

This preserves:

- traditional front vertical closure
- one straight main upper run
- upper endpoint above `H`
- short horizontal top cap above `H`
- explicit vertical rear closure down to `H`
- no rear-plane overshoot

The lower profile remains independently selected from `underside_mode`.

## 7. Stage 2 Blender runtime evidence

All required Stage 2 runtime gates passed in Blender 5.2 LTS using Candidate r3.

### Test 0 — Candidate identity — PASS

```text
Blender=5.2.0 LTS
version=(0, 7, 2)
description=Build 07-C: Sloped Closed Underside + Straight Stair Finish Variants
```

### Test 1 — Default regression — PASS

```text
UNDERSIDE=STEPPED_CLOSED
BOARD_MODE=STEPPED
OVERHANG=0.0
VERTS=620
FACES=732
ISSUES=()
```

Accepted 07-B / Stage-1 appearance remained unchanged.

### Test 2 — SLOPED_CLOSED body — PASS

With Side Boards OFF/OFF:

- lower flat remained at `B`
- one straight visible soffit
- vertical upper closure
- no cavity, floor-filled mass, spike, giant triangle, or exposed backs
- main soffit slope matched `actual_riser / going`
- corrected candidate-r3 P2 was lower than rejected candidate-r1 P2

Representative numerical evidence:

```text
SOFFIT_SLOPE=0.6220278018234807
STAIR_SLOPE=0.6220278018234807
DIFF=0.0
NEW_IS_LOWER=True
ISSUES=()
```

Isolated underbody topology:

```text
UNDERBODY_V=66
F=95
ZEROAREA=0
BOUNDARY=0
NONMANIFOLD=0
```

### Test 3 — Side Board enable states — PASS

BOTH, LEFT, RIGHT, and OFF/OFF all passed. The body remained closed and visually normal in every state.

### Test 4 — STEPPED_CLOSED + SLOPED Side Board — PASS

Accepted visual contract:

- upper profile = one straight sloped run
- lower profile = stepped
- front vertical closure
- upper endpoint above `H`
- horizontal top cap above `H`
- vertical rear closure down to `H`
- no spike / giant triangle / diagonal rear plate / notch

Representative numerical evidence:

```text
OUTER_POINTS=5
FRONT_VERTICAL=True
DIFF=1.11e-16
C_ABOVE_H=True
D_ABOVE_H=True
TOP_CAP_HORIZONTAL=True
REAR_VERTICAL=True
REAR_END_AT_H=True
ISSUES=()
```

LEFT and RIGHT Side Board topology both passed:

```text
V=70
F=101
ZEROAREA=0
BOUNDARY=0
NONMANIFOLD=0
```

### Test 5 — SLOPED_CLOSED + STEPPED Side Board — PASS

Accepted separation:

- upper profile = stepped
- lower profile = corrected sloped body family
- no stepped lower-edge regression
- no interior gap

Evidence included:

```text
UPPER_POINTS=33
UPPER_IS_STEPPED=True
LOWER_POINTS=3
LOWER_IS_SLOPED=True
ISSUES=()
```

### Test 6 — SLOPED_CLOSED + SLOPED Side Board — PASS

Both upper and lower main slopes remained pitch-parallel.

```text
UPPER_DIFF=1.11e-16
LOWER_DIFF=0.0
TOP_ABOVE_H=True
TOP_CAP=True
REAR_VERTICAL=True
REAR_AT_H=True
LOWER_MATCH=True
ISSUES=()
```

First-step and top-end terminations were visually accepted.

### Test 7 — FORWARD / REVERSE + Undo / Redo — PASS

UI Reverse preserved physical low/high-end semantics, Side Board end semantics, and identity transform.

Redo evidence:

```text
AFTER_REDO_ASCENT=REVERSE
UNDERSIDE=SLOPED_CLOSED
BOARD_MODE=SLOPED
BOARDS=(True, True)
VERTS=346
FACES=321
TRANSFORM=((0,0,0),(0,0,0),(1,1,1))
ISSUES=()
```

Mandatory UI operation -> Ctrl+Z -> Ctrl+Shift+Z -> Console order passed without geometry breakage.

### Test 8 — Oblique two-point Path — PASS

Resolved forward / left axes remained orthonormal and geometry aligned correctly.

```text
ORTHO=0.0
F_LEN=1.0
L_LEN=1.0
TRANSFORM=((0,0,0),(0,0,0),(1,1,1))
ISSUES=()
```

### Test 9 — nonzero base_z — PASS

Tested at 500 mm:

```text
BASE_Z_MM=500.0
B=0.5
BODY_MIN_Z=0.5
LEFT_MIN_Z=0.5
RIGHT_MIN_Z=0.5
MESH_MIN_Z=0.5
WORLD_ZERO_UNUSED=True
ISSUES=()
```

Nothing remained fixed at world Z=0.

### Test 10 — Stair-body thickness — PASS

Changed `150 -> 120 mm` through the UI.

```text
BODY_DEPTH_MM=120.0
SCHEMA=3
ASCENT=REVERSE
BASE_Z_MM=500.0
UNDERSIDE=SLOPED_CLOSED
BOARD_MODE=SLOPED
TRANSFORM=identity
ISSUES=()
```

Path, floor-to-floor, riser count, tread/riser sizes, width, Side Board thickness/reveal, Stair ID, Materials, and transform remained preserved. Mandatory Undo / Redo passed.

### Test 11 — Underside shell thickness — PASS

Changed shell thickness `9.5 -> 12.0 mm`.

```text
BEFORE_SHELL=9.5
AFTER_SHELL=12.0
P_UNCHANGED=True
ISSUES=()
```

The stored value changed while the visible analytical P0/P1/P2 reference line remained unchanged.

### Test 12 — Existing 07-B schema-2 compatibility — PASS

Using the UI action `階段を再生成`:

```text
AFTER_SCHEMA=2
MODE=STANDARD_RESIDENTIAL
UNDERSIDE=STEPPED_CLOSED
BOARD_MODE=STEPPED
VERTS=620
FACES=732
ISSUES=()
```

Path and Stair ID were preserved. No migration or sloped activation occurred.

### Test 13 — BASIC schema-1 compatibility — PASS

Using the UI action `階段を再生成`:

```text
BEFORE_SCHEMA=1
AFTER_SCHEMA=1
MODE=BASIC_TREAD_RISER
VERTS=248
FACES=186
ISSUES=()
```

Path and Stair ID were preserved.

### Test 14 — Material preservation / role mapping — PASS

Distinct role mapping:

```text
SLOTS=['JHM_Base','JHM_Underside','JHM_SideBoard']
ROLE_INDICES={'TREAD':0,'RISER':0,'UNDERSIDE':1,'SIDE_BOARD':2}
ROLE_COUNTS={'TREAD':90,'RISER':96,'UNDERSIDE':95,'SIDE_BOARD':40}
INDEX_MATCH=True
ISSUES=()
```

Base fallback:

```text
SLOTS=['JHM_Base']
ROLE_INDICES={'TREAD':0,'RISER':0,'UNDERSIDE':0,'SIDE_BOARD':0}
MESH_INDICES=[0]
ISSUES=()
```

True UNASSIGNED:

```text
DATA_SLOTS=[]
PLAN_SLOTS=[]
ROLE_INDICES={'TREAD':0,'RISER':0,'UNDERSIDE':0,'SIDE_BOARD':0}
MESH_INDICES=[0]
ISSUES=()
```

Identity-deduplicated slot case:

```text
DATA_SLOTS=['JHM_Base','JHM_Underside']
PLAN_SLOTS=['JHM_Base','JHM_Underside']
ROLE_INDICES={'TREAD':0,'RISER':0,'UNDERSIDE':1,'SIDE_BOARD':1}
SLOT_COUNT=2
UNDERSIDE_SIDEBOARD_SAME=True
ISSUES=()
```

## 8. Stage 1 accepted contracts

Stage 1 accepts the following as production foundation for later 07-C stages:

- add-on identity `(0, 7, 2)` / Build 07-C description
- current Residential schema 3 for explicit 07-C creation/state
- strict load compatibility for existing schema-2 07-B Stair
- existing `side_board_band_width_mm` retained as persistent storage authority
- user-facing `階段本体厚み (mm)` editing
- `side_board_mode`, `tread_front_overhang_mm`, `tread_front_edge_mode`, and `tread_front_edge_size_mm` persistence foundation
- future identifiers `SLOPED_CLOSED`, `SLOPED`, `BEVEL`, `ROUND` may exist in data definitions but unsupported Stage 1 production states are rejected before geometry mutation
- BASIC schema-1 isolation remains intact
- Material / lifecycle / Wall / Finish isolation remain intact

## 9. Stage 2 accepted contracts

Stage 2 adds production acceptance of:

- corrected `SLOPED_CLOSED` full-width closed body geometry
- visible soffit main slope parallel to canonical `actual_riser / going`
- `SLOPED` Side Board upper profile with five-point front/main/top/rear termination
- independent upper/lower Side Board profile responsibilities:
  - `side_board_mode` -> upper profile family
  - `underside_mode` -> lower profile family
- all four visible upper/lower combinations:
  - STEPPED / STEPPED
  - SLOPED / STEPPED
  - STEPPED / SLOPED
  - SLOPED / SLOPED
- FORWARD / REVERSE and oblique two-point Path behavior for Stage-2 geometry
- nonzero base Z behavior
- existing schema-2 and BASIC schema-1 compatibility
- UNDERSIDE / SIDE_BOARD Material role mapping, fallback, UNASSIGNED, and identity dedup behavior

## 10. Not yet accepted / deferred to later 07-C stages

Stage 1 / Stage 2 acceptance does not imply production acceptance of:

- 5.0 mm nosing geometry
- BEVEL tread-front geometry
- ROUND tread-front geometry
- multi-point Path / landings
- winders
- open stairs / supports
- handrails / attachments
- final 07-C practical placement / full lifecycle acceptance

These remain later-stage work under `BUILD_07_C_SPECIFICATION.md`.

## 11. Acceptance conclusion

**Build 07-C Stage 1 is ACCEPTED.**

**Build 07-C Stage 2 is ACCEPTED.**

Build 07-C overall remains **IN PROGRESS**. The next implementation stage is Stage 3: 5 mm nosing + SQUARE / BEVEL / ROUND.

The exact Stage 2 runtime-tested add-on artifact is `Japanese_House_Modeler_Build_07_C_Stage2_Candidate_r3.zip` with the SHA256 recorded above. Documentation-only acceptance commits made after the runtime test do not supersede the runtime-tested production revision `63b498a3391ced44a8e6e88468ce4aea3f0425ae` / tree `4e77af7f5c71727e006465d1d108e1d9cadd966c`.
