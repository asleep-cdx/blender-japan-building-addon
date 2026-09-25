# BUILD 07-C ACCEPTANCE RECORD
## Japanese House Modeler — Sloped Closed Underside + Straight Stair Finish Variants

Date: 2026-09-25

## 1. Status

- Build 07-C Stage 1 — **ACCEPTED**
- Build 07-C Stage 2 — **ACCEPTED**
- Build 07-C Stage 3 — **ACCEPTED**
- Build 07-C overall — **IN PROGRESS**
- Next implementation stage — **Stage 4: lifecycle / full regression / practical placement acceptance**

Stage 1 accepted schema / compatibility / transaction foundations and user-facing stair-body thickness control.
Stage 2 accepted `SLOPED_CLOSED` body geometry and `SLOPED` Side Board geometry.
Stage 3 accepts production nosing behavior, the top-arrival nosing correction, SQUARE / BEVEL / ROUND tread-front geometry, positive-nosing STEPPED Side Board upper termination, and the associated legacy / Material / placement regression gates.

Stage 3 acceptance does **not** mark Build 07-C overall complete. Stage 4 practical-placement and lifecycle acceptance remains outstanding.

## 2. Runtime-tested production revisions

### Stage 1

GitHub PR: #22

```text
commit 6482062def1fdca769c179dacb93f727dd4f8237
tree   a681502fa8c107c77e10a0a4323c3c8e053740af
```

Runtime Candidate:

```text
Japanese_House_Modeler_Build_07_C_Stage1_Candidate_r1.zip
SIZE    116967 bytes
SHA256  218a6af7b690c8a501f499e463a135b441fe3a47159d4ca0080588ad99ed3829
```

### Stage 2

GitHub PR: #23

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

### Stage 3

GitHub PR: #24

Runtime-tested exact production revision:

```text
commit 82e00898ef28068c676693d2f8f8b36d26265d5a
tree   8ffa50464797cfb2398335a2b8b7a62225205416
```

Runtime Candidate:

```text
Japanese_House_Modeler_Build_07_C_Stage3_Candidate_r2.zip
SIZE    119151 bytes
SHA256  3796163958cd72e39566b8fe96fefbf7ad69d75687426b1ae23ead5093518822
```

Runtime environment:

```text
Blender 5.2.0 LTS
Add-on version: (0, 7, 2)
Description: Build 07-C: Sloped Closed Underside + Straight Stair Finish Variants
```

Documentation-only commits after runtime review do not supersede the exact production revisions listed above.

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

### Stage 2 accepted tree

```text
tests.test_build_07_c_stage2              24 PASS
full unittest discovery                  589 PASS
compileall                               PASS
git diff --check                         PASS
```

### Stage 3 accepted production tree

```text
tests.test_build_07_c_stage3              27 PASS
requested targeted suites                253 PASS
full unittest discovery                  616 PASS
compileall                               PASS
git diff --check                         PASS
git status --short                       clean
```

## 4. Stage 1 accepted contracts

Stage 1 accepts:

- add-on identity `(0, 7, 2)` / Build 07-C description
- current Residential schema 3 for explicit 07-C creation/state
- strict load compatibility for existing schema-2 07-B Stair
- `side_board_band_width_mm` retained as persistent storage authority
- user-facing `階段本体厚み (mm)` editing
- persistence foundation for `side_board_mode`, `tread_front_overhang_mm`, `tread_front_edge_mode`, and `tread_front_edge_size_mm`
- BASIC schema-1 isolation
- Material / lifecycle / Wall / Finish isolation

Accepted schema policy:

- schema 2 + legacy 07-B Residential field edit -> remain schema 2
- schema 2 + dialog no-op -> remain schema 2
- schema 2 + explicit 07-C production field edit -> schema 3
- existing schema 3 -> remain schema 3
- new 07-C Residential Stair -> schema 3
- explicit BASIC -> Residential Apply -> schema 3

## 5. Stage 1 runtime summary

All required Blender 5.2 LTS gates passed, including:

- new Residential creation
- existing schema-2 load / Regenerate compatibility
- schema migration only on explicit 07-C field changes
- stair-body thickness `150 -> 120 mm`
- invalid body-depth atomic rejection
- save / full exit / reopen
- BASIC compatibility
- BASIC -> Residential Apply with Undo / Redo
- Material preservation
- Transform Repair with Undo / Redo
- Wall / Finish isolation

Representative accepted default / legacy counts:

```text
Residential 620 vertices / 732 faces
BASIC       248 vertices / 186 faces
ISSUES=()
```

## 6. Stage 2 correction history

### Candidate r1 — rejected

Runtime review found:

- `SLOPED_CLOSED` visible soffit too steep near the upper end
- `SLOPED` Side Board silhouette did not match the intended target

### Candidate r2 — rejected

The body slope and Side Board upper/lower responsibility split were corrected, but the SLOPED Side Board still ended at `H` without the required visible rise above the top landing.

### Candidate r3 — accepted

Accepted SLOPED Side Board upper profile:

```text
A = (-reveal, B)
B = (-reveal, B + h + reveal)
C = (L - reveal, H + reveal)
D = (L + r, H + reveal)
E = (L + r, H)
```

Accepted responsibilities:

- `side_board_mode` -> upper visible profile family
- `underside_mode` -> lower profile family

## 7. Stage 2 accepted contracts and runtime summary

Stage 2 accepts:

- corrected `SLOPED_CLOSED` full-width closed body geometry
- visible soffit main slope parallel to `actual_riser / going`
- accepted five-point `SLOPED` Side Board upper profile
- all four body / Side Board profile combinations
- BOTH / LEFT / RIGHT / OFF board states
- FORWARD / REVERSE with mandatory Undo / Redo
- oblique two-point Path
- nonzero base Z
- stair-body thickness editing without profile regression
- stored underside-shell-thickness editing without visible reference-line drift
- existing schema-2 and BASIC schema-1 compatibility
- UNDERSIDE / SIDE_BOARD Material mapping, fallback, UNASSIGNED, and identity dedup

Representative accepted SLOPED/SLOPED state:

```text
UNDERSIDE=SLOPED_CLOSED
BOARD_MODE=SLOPED
BOARDS=(True, True)
VERTS=346
FACES=321
TRANSFORM=identity
ISSUES=()
```

## 8. Stage 3 correction history

### Candidate r1 — runtime rejected

Candidate r1 correctly introduced the new-stair 5 mm ordinary tread nosing but omitted the required upper-arrival nosing.

Runtime review confirmed the ordinary 5 mm noses and then stopped the remaining Stage-3 profile gates.

### Candidate r2 — accepted

Candidate r2 added the human-confirmed top-arrival finish and the positive-nosing STEPPED Side Board upper termination.

The accepted top-arrival cap contract is:

```text
n = tread_front_overhang
t = tread_thickness
L = run_length
r = riser_thickness
H = B + floor_to_floor

x_front  = L - n
x_rear   = L + r
z_bottom = H - t
z_top    = H
Y        = [-w/2, +w/2]
```

The cap is a dedicated `TREAD` finish fragment associated with the arrival edge. It is not an extra stair step and does not change `independent_tread_count = N - 1`.

For positive nosing, the Final Riser terminates at `H - t`, with the top-arrival cap occupying `H - t .. H`. Runtime measurement confirmed the intended visible-riser relationship and floor-height semantics.

For `n = 0`, no arrival cap is generated and the accepted legacy Final Riser geometry remains unchanged.

## 9. Stage 3 accepted runtime evidence

All grouped Stage-3 runtime gates passed in Blender 5.2 LTS using Candidate r2.

### Test 0 — Candidate identity — PASS

```text
BLENDER=5.2.0 LTS
VERSION=(0,7,2)
DESCRIPTION=Build 07-C: Sloped Closed Underside + Straight Stair Finish Variants
```

### Test 1 — new default / top-arrival / finished height / thickness / Side Board — PASS

Confirmed:

- new Residential Stair default nose `5.0 mm`
- SQUARE ordinary nosing present on every independent Tread
- dedicated top-arrival nosing present
- stepped Side Board upper rise / cap / rear closure visually accepted
- sloped Side Board top termination remained visually accepted
- a temporary plane placed at `Z=2800 mm` aligned exactly with the top-arrival nosing top
- therefore `floor_to_floor=2800 mm` means finished top = `2800 mm`

30 / 40 mm linkage:

```text
TREAD_T=40.0
CAP_Z=(2.76,2.8)
FINAL_RISER_Z=(2.625,2.76)
H=2.8
```

Changing tread thickness changed the top-arrival nosing thickness while keeping the finished top fixed at `H`.

### Test 2 — schema-2 / prior schema-3 zero-nosing compatibility — PASS

Existing 07-B schema-2 fixture before / after ordinary Regenerate:

```text
SCHEMA=2
NOSE=0.0
EDGE=SQUARE
V=620
F=732
ISSUES=()
```

Existing Stage-2 schema-3 zero-nosing fixture before / after Regenerate:

```text
SCHEMA=3
NOSE=0.0
EDGE=SQUARE
UNDERSIDE=SLOPED_CLOSED
BOARD=SLOPED
V=346
F=321
ISSUES=()
```

No silent 5 mm migration, top-arrival cap, or positive-nosing STEPPED-board rise was introduced into legacy zero-nosing files.

### Test 3 — board states + body / board matrix — PASS

BOTH, LEFT, RIGHT, and OFF/OFF all passed visually.

All four combinations passed:

- STEPPED_CLOSED + STEPPED
- STEPPED_CLOSED + SLOPED
- SLOPED_CLOSED + STEPPED
- SLOPED_CLOSED + SLOPED

Representative final state:

```text
UNDERSIDE=SLOPED_CLOSED
BOARD=SLOPED
LEFT=True
RIGHT=True
NOSE=5.0
V=354
F=327
ISSUES=()
```

No cavity, z-fighting, giant triangle, profile break, or top-arrival regression was observed.

### Test 4 — atomic invalid-value rejection — PASS

The following were rejected atomically:

- nose `70 mm` with Side Board reveal `40 mm`
- BEVEL q=`0`
- BEVEL q=`15 mm` with tread thickness `30 mm`
- ROUND q=`6 mm` with nose `5 mm`

Final evidence:

```text
ATOMIC_OK=True
```

Mesh, Stair ID, Path, Material assignment, transform, and Stage-3 fields remained unchanged after rejected submissions.

### Test 5 — BEVEL + ROUND — PASS

BEVEL:

```text
MODE=BEVEL
FIRST=(12,14)
CAP=(12,14)
FIRST_OK=True
CAP_OK=True
ZEROAREA=0
```

ROUND:

```text
MODE=ROUND
PROFILE_POINTS=12
FIRST=(24,32)
CAP=(24,32)
FIRST_OK=True
CAP_OK=True
ZEROAREA=0
```

Both ordinary Treads and the top-arrival cap use the same profile family. ROUND retains the deterministic four-chord-per-quarter-arc construction.

### Test 6 — Reverse / Undo-Redo / oblique Path / nonzero base Z — PASS

Mandatory UI Reverse -> Ctrl+Z -> Ctrl+Shift+Z -> Console discipline passed.

Final combined evidence:

```text
ASCENT=REVERSE
PATH=[(1.0,2.0),(4.0,6.0)]
OBLIQUE=True
ORTHO=0.0
BASE_Z=375.0
MESH_MIN_Z=0.375
CAP_Z=(3.145,3.175)
H=3.175
TRANSFORM=((0,0,0),(0,0,0),(1,1,1))
ISSUES=()
```

The complete Stair, ordinary noses, top-arrival cap, and Side Boards followed the oblique two-point Path and nonzero base elevation without transform drift.

### Test 7 — Material + BASIC compatibility — PASS

ROUND geometry with a distinct Tread override:

```text
SLOTS=['JHM_Tread','JHM_Base']
ROLES={'TREAD':0,'RISER':1,'UNDERSIDE':1,'SIDE_BOARD':1}
COUNTS={'TREAD':512,'RISER':96,'UNDERSIDE':95,'SIDE_BOARD':40}
TREAD_INDEX=0
CAP_ROLE=TREAD
INDEX_MATCH=True
ISSUES=()
```

The detailed ROUND front faces and top-arrival cap remained in the existing `TREAD` role. No `NOSING` role was introduced.

BASIC ordinary Regenerate remained:

```text
MODE=BASIC_TREAD_RISER
SCHEMA=1
NOSE=0.0
V=248
F=186
ISSUES=()
```

No Residential nosing / body / Side Board behavior leaked into BASIC.

## 10. Stage 3 accepted contracts

Stage 3 adds production acceptance of:

- explicit new-Residential creation default `tread_front_overhang_mm = 5.0`
- persistent / legacy semantic default `0.0` for existing files
- no silent nosing migration on ordinary Regenerate
- SQUARE rectangular tread-front geometry
- BEVEL symmetric 45-degree front treatment
- ROUND deterministic four-chord-per-quarter-arc treatment
- `0 <= n < going`
- BEVEL / ROUND q validation
- Side Board-enabled `n <= reveal`
- positive-nosing top-arrival cap with top exactly at `H`
- floor-to-floor height interpreted as the finished top of the top-arrival cap
- tread-thickness linkage for the top-arrival cap
- positive-nosing Final Riser top at `H - t`
- no extra ordinary full-depth arrival Tread and no extra stair step
- positive-nosing STEPPED Side Board upper termination:

```text
C = (L - reveal, H + reveal)
D = (L + r,      H + reveal)
E = (L + r,      H)
```

- accepted Stage-2 SLOPED Side Board five-point profile unchanged
- all new detail faces remain `TREAD`; Material roles remain exactly:
  - TREAD
  - RISER
  - UNDERSIDE
  - SIDE_BOARD
- FORWARD / REVERSE, oblique Path, nonzero base Z, Material, schema-2, prior schema-3 zero-nosing, and BASIC compatibility for Stage-3 geometry

## 11. Deferred to Stage 4 / later scope

Stage 3 acceptance does not imply final acceptance of:

- Build 07-C full lifecycle / practical-placement behavior
- broader save / reopen lifecycle coverage for all new Stage-3 profile combinations
- full final regression / integration acceptance across the complete 07-C feature set
- multi-point Path / landings
- winders
- open stairs / supports
- handrails / attachments

These remain outside Stage 3 or are explicitly deferred to Stage 4 / later builds under `BUILD_07_C_SPECIFICATION.md`.

## 12. Acceptance conclusion

**Build 07-C Stage 1 is ACCEPTED.**

**Build 07-C Stage 2 is ACCEPTED.**

**Build 07-C Stage 3 is ACCEPTED.**

Build 07-C overall remains **IN PROGRESS**. The next implementation stage is Stage 4: lifecycle / full regression / practical-placement acceptance.

The exact Stage 3 runtime-tested add-on artifact is `Japanese_House_Modeler_Build_07_C_Stage3_Candidate_r2.zip` with SHA256 `3796163958cd72e39566b8fe96fefbf7ad69d75687426b1ae23ead5093518822`.

Documentation-only acceptance commits made after the runtime test do not supersede the runtime-tested production revision `82e00898ef28068c676693d2f8f8b36d26265d5a` / tree `8ffa50464797cfb2398335a2b8b7a62225205416`.
