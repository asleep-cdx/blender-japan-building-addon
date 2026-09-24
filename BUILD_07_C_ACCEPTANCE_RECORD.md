# BUILD 07-C ACCEPTANCE RECORD
## Japanese House Modeler — Sloped Closed Underside + Straight Stair Finish Variants

Date: 2026-09-24

## 1. Status

- Build 07-C Stage 1 — **ACCEPTED**
- Build 07-C overall — **IN PROGRESS**
- Next implementation stage — **Stage 2: SLOPED_CLOSED + SLOPED Side Board geometry**

Stage 1 acceptance covers foundation / compatibility / schema 3 plumbing and the user-facing stair-body thickness control. It does **not** accept Stage 2/3 geometry.

## 2. Runtime-tested production revision

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

Runtime environment:

```text
Blender 5.2.0 LTS
Add-on version: (0, 7, 2)
Description: Build 07-C: Sloped Closed Underside + Straight Stair Finish Variants
```

## 3. Automated evidence

Automated evidence reported for the accepted Stage 1 tree:

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

## 4. Resolved pre-acceptance review issue

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

## 5. Blender runtime evidence

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

## 6. Stage 1 accepted contracts

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

## 7. Not yet accepted / deferred to later 07-C stages

Stage 1 acceptance does not imply production acceptance of:

- SLOPED_CLOSED geometry
- SLOPED Side Board geometry
- 5.0 mm nosing geometry
- BEVEL tread-front geometry
- ROUND tread-front geometry
- final 07-C practical placement / full lifecycle acceptance

These remain Stage 2 / Stage 3 / final-stage work under `BUILD_07_C_SPECIFICATION.md`.

## 8. Acceptance conclusion

**Build 07-C Stage 1 is ACCEPTED.**

The exact runtime-tested add-on artifact is `Japanese_House_Modeler_Build_07_C_Stage1_Candidate_r1.zip` with the SHA256 recorded above. Documentation-only acceptance commits made after the runtime test do not supersede the runtime-tested production revision.
