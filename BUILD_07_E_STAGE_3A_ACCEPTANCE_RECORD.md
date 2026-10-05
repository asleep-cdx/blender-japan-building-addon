# BUILD 07-E STAGE 3A ACCEPTANCE RECORD
## Japanese House Modeler — Fresh Stage 3A STEPPED_CLOSED / Side Boards OFF

Date: 2026-10-05

## 1. Status

- Build 07-E Stage 1 — **ACCEPTED**
- Build 07-E Stage 2 — **ACCEPTED**
- Build 07-E Stage 2.5 — **ACCEPTED**
- Build 07-E first Stage-3 attempt / PR #33 — **ABANDONED / CLOSED / NOT MERGED**
- Fresh Build 07-E Stage 3A — **ACCEPTED at Candidate r2**
- Fresh Build 07-E Stage 3B — **NEXT**
- Build 07-E overall — **NOT YET ACCEPTED**

Stage 3A implements only schema-5 `STANDARD_RESIDENTIAL` Winder `STEPPED_CLOSED` visible body generation with both Side Boards disabled. `SLOPED_CLOSED`, Winder Side Boards and later Stage-3 work remain deferred.

## 2. Runtime-tested production identity

GitHub PR: #35

Exact Blender runtime-tested production revision:

```text
commit 01a9b88c28451ae9ac04f268fce63bfe1a227830
tree   09527d45f2616a93c817e0922c91645d88245193
```

Accepted runtime Candidate:

```text
Japanese_House_Modeler_Build_07_E_Stage3A_Candidate_r2.zip
SHA256  d2d5353afca50b5f87f0c8722b9b36c38359eaded82d934d4dc638b38ca5f2f8
```

Candidate r1 was runtime-rejected and is not accepted:

```text
Japanese_House_Modeler_Build_07_E_Stage3A_Candidate_r1.zip
SHA256  3e31572e1a9a531dcf1af1cbbe6472353e1d23aacc54f385d55573fe85b493b2
RESULT  FAIL
```

Candidate r1 duplicated each full TREAD footprint downward as an UNDERBODY prism, obscuring the accepted nosing/RISER exterior and producing an incorrect thick-tread appearance. Candidate r2 replaces that geometry and is the accepted Stage-3A production baseline.

Runtime environment:

```text
Blender 5.2 LTS
```

Any later documentation-only commit does not supersede the exact runtime-tested production commit/tree above.

## 3. Accepted Stage-3A geometry

### Straight Flight body

Schema-5 Straight portions use the accepted Residential stepped-body semantics rather than copying physical TREAD footprints downward. The implementation reuses the existing Residential underbody helper/profile semantics in each Flight local frame.

Accepted visible behavior:

- TREAD remains a distinct thin board;
- the accepted nosing remains visibly projected;
- RISER remains visibly exposed;
- UNDERBODY is set back behind the visible finish/contact boundary;
- `STEPPED_CLOSED` body follows the accepted stepped closure profile;
- Candidate-r1 thick-tread / visible-tab behavior is removed.

### Winder body

Winder UNDERBODY is derived from accepted nominal Winder cells and is clipped behind the ascent-local RISER rear plane using the accepted riser-thickness setback. It does not reuse the full physical TREAD footprint and does not inherit the exposed nosing boundary.

The Stage-2.5 TREAD/RISER production geometry remains frozen and unchanged.

### Architecture retained

The accepted implementation remains visual-first and does **not** reintroduce the abandoned PR #33 exact-solid architecture. It does not require:

- Boolean union;
- `PHYSICAL_CONTACT` ownership;
- `BodyInterface` reconciliation;
- whole-stair watertight union;
- volume conservation proof.

Separate closed fragments and hidden overlap remain allowed when the visible exterior is coherent.

## 4. Automated / static evidence

Final Candidate-r2 implementation report:

```text
python -m unittest tests.test_build_07_e_stage2_5
6 tests PASS

python -m unittest tests.test_build_07_e_stage1 tests.test_build_07_e_stage2
127 tests PASS

python -m unittest tests.test_build_07_e_stage3_fresh
10 tests PASS

python -m unittest tests.test_build_07_d_stage1 tests.test_build_07_d_stage2 tests.test_build_07_d_stage3 tests.test_build_07_d_stage4
131 tests PASS

python -m unittest discover -s tests
909 tests PASS

python -m compileall -q japanese_house_modeler tests
PASS

git diff --check
PASS
```

Focused Fresh Stage-3A tests cover exact-90 EQUAL_3 FORWARD/REVERSE, accepted stepped-soffit Z authority, Straight nosing/body setback, Winder body setback, determinism, arbitrary-angle smoke, BF patterns, Compact-U, semantic UNDERBODY role, deferred configurations, and preservation of the Stage-2.5 TREAD/RISER signature.

## 5. Blender 5.2 LTS runtime acceptance

Candidate r2 passed the compact Stage-3A runtime plan.

### Runtime 1 — exact-90 EQUAL_3 FORWARD — PASS

Observed state:

```text
SCHEMA=5
DIR=FORWARD
ASSEMBLY=STANDARD_RESIDENTIAL
UNDERSIDE=STEPPED_CLOSED
BOARDS=False False
MESH=352 vertices / 330 faces
```

Visual review confirmed:

- normal Straight tread nosing projection;
- normal TREAD/RISER relationship;
- accepted stepped closed Straight body;
- no Candidate-r1 thick-tread effect;
- no new major spike, giant face or visible body penetration;
- Winder body exists and the known Stage-2.5 Winder TREAD/RISER gap remains deferred.

### Runtime 2 — exact-90 EQUAL_3 REVERSE — PASS

Observed state:

```text
SCHEMA=5
DIR=REVERSE
ASSEMBLY=STANDARD_RESIDENTIAL
UNDERSIDE=STEPPED_CLOSED
BOARDS=False False
MESH=352 vertices / 330 faces
```

REVERSE preserved the same visible body behavior, nosing, Straight stepped body and Winder body without the Candidate-r1 regression.

### Runtime 3 — BF_1 then BF_2 — PASS

Both patterns were regenerated in one runtime sequence.

BF_1:

```text
DIR=FORWARD
TURN=[('WINDER','BF_1')]
UNDERSIDE=STEPPED_CLOSED
BOARDS=False False
MESH=356 vertices / 338 faces
```

BF_2:

```text
DIR=FORWARD
TURN=[('WINDER','BF_2')]
UNDERSIDE=STEPPED_CLOSED
BOARDS=False False
MESH=356 vertices / 338 faces
```

Both preserved normal Straight nosing/body appearance. The remaining Winder TREAD/RISER transition gaps are the known Stage-2.5 limitation and are not Stage-3A body failures.

### Runtime 4 — Compact-U / two EQUAL_3 Turns — PASS

A fresh schema-5 Compact-U stair was created with two Winder Turns and Side Boards OFF.

Observed state:

```text
DIR=FORWARD
TURNS=[('WINDER','EQUAL_3'), ('WINDER','EQUAL_3')]
UNDERSIDE=STEPPED_CLOSED
BOARDS=False False
MESH=344 vertices / 304 faces
```

Both Turns and all three Straight Flights generated correctly. Stepped bodies, nosing and overall Compact-U form were preserved without a new major spike, giant face or body protrusion.

### Runtime 5 — Regenerate / Save / full exit / reopen — PASS

The Compact-U stair above was regenerated, saved, Blender was fully exited, Blender 5.2 LTS was restarted and the file reopened.

Observed reopened state remained:

```text
SCHEMA=5
DIR=FORWARD
TURNS=[('WINDER','EQUAL_3'), ('WINDER','EQUAL_3')]
UNDERSIDE=STEPPED_CLOSED
BOARDS=False False
MESH=344 vertices / 304 faces
```

No visible geometry or managed-state regression was observed.

### Runtime 6 — schema-4 Build 07-D regression — PASS

An accepted Build 07-D managed L stair was opened under Candidate r2 and regenerated once.

Observed state:

```text
SCHEMA=4
MANAGED=True
DIR=REVERSE
PATH=?
UNDERSIDE=SLOPED_CLOSED
MESH=433 vertices / 412 faces
```

Visual review confirmed the original accepted schema-4 form remained unchanged: L stair, Landing, `SLOPED_CLOSED` underside and left/right sloped-finish Side Boards. The stair remained schema 4 and was not routed into the new schema-5 Stage-3A Winder body path.

## 6. Known intentionally deferred limitation

The retained Stage-2.5 Candidate-r1 Winder TREAD/RISER transition gap remains visible in EQUAL_3 and BF patterns, including some Compact-U Turn transitions.

This remains intentionally deferred:

```text
known Stage-2.5 Winder TREAD/RISER gap = ALLOWED / NOT A STAGE-3A BODY BLOCKER
```

Stage 3A does not change the frozen Stage-2.5 TREAD/RISER authority solely to close this gap.

## 7. Runtime-plan note

A dedicated 63-degree Blender runtime case was intentionally skipped in the compact acceptance plan to reduce redundant runtime work. Arbitrary-angle Stage-3A geometry remains covered by the automated Fresh Stage-3A test suite. Exact-90 FORWARD/REVERSE, BF variants, multi-Turn Compact-U, persistence and schema-4 regression were exercised in Blender.

## 8. Acceptance conclusion

Fresh Build 07-E Stage 3A — **ACCEPTED at Candidate r2**.

Exact runtime-tested production revision:

```text
commit 01a9b88c28451ae9ac04f268fce63bfe1a227830
tree   09527d45f2616a93c817e0922c91645d88245193
```

Accepted runtime Candidate:

```text
Japanese_House_Modeler_Build_07_E_Stage3A_Candidate_r2.zip
SHA256  d2d5353afca50b5f87f0c8722b9b36c38359eaded82d934d4dc638b38ca5f2f8
```

Fresh Stage 3B is NEXT. Stage 3B must start from the post-merge `main` baseline and add only the next planned Stage-3 functionality while preserving this accepted Stage-3A visible body behavior.

Build 07-E overall remains **NOT YET ACCEPTED**.
