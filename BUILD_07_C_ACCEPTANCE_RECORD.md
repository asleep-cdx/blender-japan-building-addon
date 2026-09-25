# BUILD 07-C ACCEPTANCE RECORD
## Japanese House Modeler — Sloped Closed Underside + Straight Stair Finish Variants

Date: 2026-09-26

## 1. Status

- Build 07-C Stage 1 — **ACCEPTED**
- Build 07-C Stage 2 — **ACCEPTED**
- Build 07-C Stage 3 — **ACCEPTED**
- Build 07-C Stage 4 — **ACCEPTED**
- Build 07-C overall — **ACCEPTED**

Build 07-C is complete. Stage 4 closed the lifecycle, persistence, rollback, legacy-regression, Wall / Finish isolation, practical-placement, and final-topology gates without requiring any production Python change.

The next project decision is the post-07-C roadmap checkpoint: evaluate whether to continue directly to Build 07-D or reprioritize 08 / 09 work. This Acceptance Record is authoritative for Build 07-C status.

## 2. Runtime-tested revisions and artifacts

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

Exact runtime-tested production revision:

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

### Stage 4

GitHub PR: #25

Exact runtime-tested Stage-4 revision:

```text
commit f0e38b9fd268ec50cdc6680f342f34a472d56bc6
tree   9f091ac14b6efcdce4bfbc7f652f4809ff395b9a
```

Runtime Candidate:

```text
Japanese_House_Modeler_Build_07_C_Stage4_Candidate_r1.zip
SIZE    119151 bytes
SHA256  71c931b9524c8cf77a89d66d52114cbfb518ca16ad04071053283c40fa704d53
```

Stage 4 changed only automated tests and runtime documentation. It did not modify production Python, so the accepted Stage-3 production geometry semantics remain unchanged.

Runtime environment:

```text
Blender 5.2.0 LTS
Add-on version: (0, 7, 2)
Description: Build 07-C: Sloped Closed Underside + Straight Stair Finish Variants
```

Documentation / acceptance commits created after runtime review do not supersede the exact runtime-tested revisions listed above.

## 3. Automated evidence

### Stage 1

```text
tests.test_build_07_c_stage1              20 PASS
full unittest discovery                  565 PASS
compileall                               PASS
git diff --check                         PASS
```

### Stage 2

```text
tests.test_build_07_c_stage2              24 PASS
full unittest discovery                  589 PASS
compileall                               PASS
git diff --check                         PASS
```

### Stage 3

```text
tests.test_build_07_c_stage3              27 PASS
requested targeted suites                253 PASS
full unittest discovery                  616 PASS
compileall                               PASS
git diff --check                         PASS
git status --short                       clean
```

### Stage 4

```text
tests.test_build_07_c_stage4              19 PASS
requested targeted 07-A / 07-B / 07-C   272 PASS
full unittest discovery                  635 PASS
compileall                               PASS
git diff --check                         PASS
git status --short                       clean
```

The Stage-4 automated suite covers complete 07-C snapshot / restore state, prepare-before-mutation transaction design, rollback contracts, invalid-candidate rejection, duplicate-ID policy, Repair policy, Finalize / Delete, Material semantics, legacy 07-B / BASIC isolation, and four representative final geometry combinations.

## 4. Stage 1 accepted contracts

Stage 1 accepted the 07-C schema / compatibility / transaction foundation:

- add-on identity `(0, 7, 2)` and Build 07-C description
- explicit 07-C Residential state at schema 3
- strict compatibility for existing schema-2 07-B Stair
- `side_board_band_width_mm` retained as persistent stair-body-thickness authority
- user-facing `階段本体厚み (mm)` editing
- persistence foundation for `side_board_mode`, `tread_front_overhang_mm`, `tread_front_edge_mode`, and `tread_front_edge_size_mm`
- BASIC schema-1 isolation
- Material / lifecycle / Wall / Finish isolation foundation

Accepted schema policy:

- schema 2 + legacy 07-B Residential field edit -> remain schema 2
- schema 2 + dialog no-op -> remain schema 2
- schema 2 + explicit 07-C production field edit -> schema 3
- existing schema 3 -> remain schema 3
- new 07-C Residential Stair -> schema 3
- explicit BASIC -> Residential Apply -> schema 3

Representative legacy counts remain:

```text
Residential 620 vertices / 732 faces
BASIC       248 vertices / 186 faces
```

## 5. Stage 2 accepted geometry

Stage 2 accepted:

- corrected `SLOPED_CLOSED` full-width closed body geometry
- visible soffit main slope parallel to `actual_riser / going`
- `side_board_mode` controls the upper visible Side Board profile
- `underside_mode` controls the lower Side Board profile
- all four body / Side Board combinations
- BOTH / LEFT / RIGHT / OFF board states
- FORWARD / REVERSE
- oblique two-point Path
- nonzero base Z
- stair-body-thickness editing
- existing schema-2 and BASIC schema-1 compatibility
- UNDERSIDE / SIDE_BOARD Material mapping, fallback, unassigned, and datablock identity dedup

Accepted SLOPED Side Board upper profile:

```text
A = (-reveal, B)
B = (-reveal, B + h + reveal)
C = (L - reveal, H + reveal)
D = (L + r, H + reveal)
E = (L + r, H)
```

Correction history:

- Candidate r1 — rejected: body soffit / Side Board silhouette incorrect
- Candidate r2 — rejected: missing accepted upper rise on SLOPED Side Board
- Candidate r3 — accepted

## 6. Stage 3 accepted geometry and finish variants

Stage 3 accepted production behavior for:

- new Residential creation default `tread_front_overhang_mm = 5.0`
- legacy / stored semantic default `0.0`
- no silent 5 mm migration during ordinary Regenerate
- SQUARE tread-front treatment
- symmetric BEVEL treatment
- deterministic ROUND treatment with four linear chords per quarter arc
- `0 <= n < going`
- BEVEL / ROUND edge-size validation
- Side Board-enabled `n <= reveal`
- TREAD / RISER / UNDERSIDE / SIDE_BOARD as the complete Material-role set; no NOSING role

Accepted positive-nosing top-arrival cap:

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

The top-arrival cap is a dedicated `TREAD` finish fragment, not an extra stair step. `independent_tread_count` remains `N - 1`.

For positive nosing, the Final Riser terminates at `H - t`; the top-arrival cap occupies `H - t .. H`. Therefore `floor_to_floor = 2800 mm` means the finished top of the top-arrival nosing is exactly Z=2800 mm.

For `n = 0`, there is no arrival cap and the accepted legacy Final Riser geometry remains unchanged.

Accepted positive-nosing STEPPED Side Board upper termination:

```text
C = (L - reveal, H + reveal)
D = (L + r,      H + reveal)
E = (L + r,      H)
```

Correction history:

- Candidate r1 — runtime rejected: ordinary 5 mm noses passed, upper-arrival nosing was missing
- Candidate r2 — accepted

Representative Stage-3 evidence included:

```text
TREAD_T=40.0
CAP_Z=(2.76,2.8)
FINAL_RISER_Z=(2.625,2.76)
H=2.8
```

```text
BEVEL FIRST=(12,14) CAP=(12,14) ZEROAREA=0
ROUND PROFILE_POINTS=12 FIRST=(24,32) CAP=(24,32) ZEROAREA=0
```

## 7. Stage 4 runtime acceptance

All eight grouped Stage-4 runtime tests passed in Blender 5.2 LTS using Candidate r1.

### Test 0 — Candidate identity — PASS

```text
BLENDER=5.2.0 LTS
VERSION=(0,7,2)
DESCRIPTION=Build 07-C: Sloped Closed Underside + Straight Stair Finish Variants
```

### Test 1 — combined Stage-3 edit / Undo-Redo / save-reopen — PASS

A non-default managed Residential Stair preserved its ID, oblique Path, REVERSE ascent, base elevation, tread / Riser thicknesses, body thickness, positive nosing, ROUND edge treatment, Material assignments / slots, geometry, and identity transform across save -> full Blender exit -> relaunch -> reopen.

Representative persisted state:

```text
PATH=[(1.0,2.0),(4.0,6.0)]
ASCENT=REVERSE
BASE=375.0
TREAD_T=32.0
RISER_T=13.0
BODY=145.0
NOSE=8.0
EDGE=ROUND
Q=4.0
V=888
F=1160
CAP_Z=(3.143,3.175)
TRANSFORM=identity
```

The combined `SLOPED_CLOSED + SLOPED` edit then passed the mandatory UI operation -> Ctrl+Z -> Ctrl+Shift+Z sequence:

```text
UNDERSIDE=SLOPED_CLOSED
BOARD=SLOPED
BODY=145.0
NOSE=8.0
EDGE=ROUND
Q=4.0
PATH=[(1.0,2.0),(4.0,6.0)]
ASCENT=REVERSE
```

### Test 2 — atomic rejection / Geometry Repair / Transform Repair — PASS

All invalid Stage-4 candidates were rejected without mutation:

```text
ATOMIC_OK=True
```

Covered invalid body thickness, `n >= going`, board/reveal conflict, BEVEL q=0, BEVEL q at tread-thickness half, and ROUND q greater than the nose.

Geometry was intentionally cleared:

```text
V=0
F=0
ISSUES=('GEOMETRY_MISSING',)
```

Repair + Undo/Redo restored canonical geometry and state:

```text
V=610
F=743
UNDERSIDE=SLOPED_CLOSED
BOARD=SLOPED
NOSE=8.0
EDGE=ROUND
PATH=[(1.0,2.0),(4.0,6.0)]
ISSUES=()
```

Transform corruption was also repaired with Undo/Redo:

```text
LOC=(0,0,0)
ROT=(0,0,0)
SCALE=(1,1,1)
ISSUES=()
```

Stair ID, Path, and Materials remained stable when ID itself was not the issue.

### Test 3 — duplicate ID / targeted Repair — PASS

`Shift+D` produced two managed Stairs carrying the same persistent ID and both reported `ID_CONFLICT`.

Repair + Undo/Redo on the duplicate changed only the conflicting duplicate ID. The original ID remained:

```text
a510be8b-f8ec-4bc9-bbdd-efafae03725b
```

Both Stairs returned to `ISSUES=()` with Stage-3 settings, Path, geometry, and Materials preserved.

### Test 4 — Material lifecycle — PASS

Distinct Base / Tread / Riser / Underside / Side Board canonical Material assignments survived:

- Regenerate
- dimension edit
- Path edit
- Reverse
- 07-C Residential settings edit
- Repair

Final evidence:

```text
MATERIAL_LIFECYCLE_OK=True
EDGE=ROUND
UNDERSIDE=SLOPED_CLOSED
BOARD=SLOPED
ISSUES=()
```

### Test 5 — Finalize / active-only Delete / abnormal-state Delete — PASS

Finalize changed only the management marker:

```text
MANAGED=True -> False
SAME_DATA=True
V=610
F=743
```

Geometry and Materials remained unchanged, and the object remained a normal editable Blender Mesh.

Deleting a managed Stair removed only the active Stair. The finalized Stair, an unrelated Cube, and shared `S4_*` Material datablocks remained.

Delete also remained available for an abnormal managed Stair:

```text
ABNORMAL=('TRANSFORM_CHANGED',)
ABNORMAL_DELETE_OK=True
```

### Test 6 — 07-B schema2 / BASIC schema1 final regression — PASS

07-B schema2 after Regenerate, dimensions, Path, Reverse, Repair, save / full exit / reopen:

```text
SCHEMA=2
MODE=STANDARD_RESIDENTIAL
NOSE=0.0
UNDERSIDE=STEPPED_CLOSED
BOARD=STEPPED
WIDTH=920.0
V=620
F=732
TRANSFORM=identity
ISSUES=()
```

No Stage-3 nosing or positive-nosing Side Board behavior leaked into the legacy file.

BASIC schema1 after dimensions with Undo/Redo, Path, Reverse, Regenerate, Repair, save / full exit / reopen:

```text
SCHEMA=1
MODE=BASIC_TREAD_RISER
WIDTH=920.0
V=248
F=186
TRANSFORM=identity
ISSUES=()
```

No Residential body, Side Board, nosing, arrival cap, BEVEL, or ROUND behavior leaked into BASIC.

### Test 7 — Wall / Finish isolation / practical placement / final topology — PASS

The integration scene contained three managed Walls and two managed Finishes. After Stair dimensions, Path, Reverse, Residential settings, Material edit, Regenerate, and Repair:

```text
WALL_FINISH_UNCHANGED=True
WALLS=3
FINISHES=2
```

The practical-placement check used manually placed lower / upper floor-like geometry. The upper floor-like plane at Z=2800 mm met the finished top-arrival elevation as intended. Visual review also accepted the lower termination, sloped Side Board transition, closed underside, nosing scale, and absence of major cavities / spikes / giant triangles.

All four final representative topology configurations passed.

A — STEPPED_CLOSED + STEPPED + SQUARE:

```text
V=632 F=744
FINITE=True ZEROAREA=0 BOUNDARY=0 NONMANIFOLD=0
MIN_Z=0.0 BODY_BOARD_MAX_X=4.012 LIMIT=4.012 TREAD_MIN_X=-0.005 ISSUES=()
```

B — STEPPED_CLOSED + SLOPED + BEVEL:

```text
V=580 F=698
FINITE=True ZEROAREA=0 BOUNDARY=0 NONMANIFOLD=0
MIN_Z=0.0 BODY_BOARD_MAX_X=4.012 LIMIT=4.012 TREAD_MIN_X=-0.005 ISSUES=()
```

C — SLOPED_CLOSED + STEPPED + ROUND:

```text
V=726 F=917
FINITE=True ZEROAREA=0 BOUNDARY=0 NONMANIFOLD=0
MIN_Z=0.0 BODY_BOARD_MAX_X=4.012 LIMIT=4.012 TREAD_MIN_X=-0.005 ISSUES=()
```

D — SLOPED_CLOSED + SLOPED + ROUND:

```text
V=610 F=743
FINITE=True ZEROAREA=0 BOUNDARY=0 NONMANIFOLD=0
MIN_Z=0.0 BODY_BOARD_MAX_X=4.012 LIMIT=4.012 TREAD_MIN_X=-0.005 ISSUES=()
```

## 8. Final accepted contracts

Build 07-C overall acceptance includes all Stage 1–4 contracts above, with these final lifecycle guarantees:

- canonical 07-C fields survive transactional edits and persistence
- failed validation remains atomic
- managed Geometry Repair rebuilds from canonical state
- Transform Repair restores identity without changing ID when ID is not the issue
- duplicate-ID Repair changes only the conflicting Stair's ID
- Finalize preserves visible Mesh and Materials while ending management
- Delete is active-object-only and available for supported abnormal states
- Material roles remain exactly TREAD / RISER / UNDERSIDE / SIDE_BOARD
- existing schema-2 07-B and schema-1 BASIC behavior remains compatible
- Stair operations do not mutate managed Walls or Finishes
- Build 07-C works in a manually prepared floor / wall-like residential placement scene without requiring Wall / Floor attachment
- representative final generated meshes are finite, closed, positive-area, bounded, and free of unintended boundary / non-manifold edges

## 9. Deferred to later builds

Build 07-C acceptance does not add or accept:

- multi-point Path
- L / U Stair
- landing
- winder / 廻り段
- open stair / support variants
- handrail / newel / baluster systems
- automatic Wall / Floor / Room attachment
- separate NOSING Material role
- schema 4

These remain later-roadmap work.

## 10. Acceptance conclusion

**Build 07-C Stage 1 is ACCEPTED.**

**Build 07-C Stage 2 is ACCEPTED.**

**Build 07-C Stage 3 is ACCEPTED.**

**Build 07-C Stage 4 is ACCEPTED.**

**Build 07-C overall is ACCEPTED.**

The exact Stage-4 runtime-tested artifact is `Japanese_House_Modeler_Build_07_C_Stage4_Candidate_r1.zip` with SHA256 `71c931b9524c8cf77a89d66d52114cbfb518ca16ad04071053283c40fa704d53`.

The exact Stage-4 runtime-tested revision is `f0e38b9fd268ec50cdc6680f342f34a472d56bc6` / tree `9f091ac14b6efcdce4bfbc7f652f4809ff395b9a`.

Acceptance/documentation commits created after the Blender runtime review do not supersede that runtime-tested revision.