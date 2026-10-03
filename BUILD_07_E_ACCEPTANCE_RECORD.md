# BUILD 07-E ACCEPTANCE RECORD
## Japanese House Modeler — Winder + Arbitrary-angle Turn / Landing

Date: 2026-10-03

## 1. Status

- Build 07-E Stage 1 — **ACCEPTED**
- Build 07-E Stage 2 — **ACCEPTED**
- Build 07-E Stage 3 — **NEXT**
- Build 07-E Stage 4 — **PENDING**
- Build 07-E overall — **NOT YET ACCEPTED**

Implementation authority remains `BUILD_07_E_SPECIFICATION.md` (`FINAL / IMPLEMENTATION AUTHORITY`). This record is authoritative for Build 07-E acceptance status.

Stage 1 established the schema-5 generalized Turn / Winder foundation, RiseEvent allocation authority, explicit schema-4 AUTO L -> schema-5 Winder promotion, and exact-90-degree 3-point L EQUAL_2 / EQUAL_3 / EQUAL_4 Winder TREAD/RISER production geometry while preserving existing schema-1/2/3/4 behavior.

Stage 2 accepted BF_1 / BF_2, per-Turn U / Compact U, arbitrary-angle Landing / EQUAL Winder, full schema-5 AUTO / MANUAL allocation, and Stage-2 physical Winder finish authority including constant-distance nosing, exact shared TREAD/RISER boundaries, and the Turn-local common inner finish chord `K_finish`.

Stage 3+ scope remains deferred exactly as defined by the final specification.

## 2. Stage 1 implementation / merge identity

GitHub PR: #31

Exact runtime-tested PR revision:

```text
commit 5c806406752cdb52ef1ffaeaf8e6b6055160b030
tree   54ab4dcdbd4cc6f3283d5c6536121e21c2965558
```

Merged main revision:

```text
commit 17ecaf22fa0f94513f5f80d0363502036e0fd40b
tree   54ab4dcdbd4cc6f3283d5c6536121e21c2965558
```

The runtime-tested PR head and merged main commit have the same tree SHA, so the accepted production contents are identical.

Runtime Candidate:

```text
Japanese_House_Modeler_Build_07_E_Stage1_Candidate_r1.zip
SIZE    152026 bytes
SHA256  eab3a4ef7b5a6a1607d817c5b31c930594d10853f311909413887e79f2d981c1
```

Runtime environment:

```text
Blender 5.2.0 LTS
Add-on version: (0, 7, 4)
Description: Build 07-E: Winder + Arbitrary-angle Turn/Landing
```

Documentation / acceptance commits created after runtime review do not supersede the exact runtime-tested production revision above.

## 3. Stage 1 automated evidence

Final implementation report after the REVERSE / Winder-Riser correction:

```text
python -m unittest tests.test_build_07_e_stage1                                      25 PASS
python -m unittest tests.test_build_07_d_stage1 tests.test_build_07_d_stage2 tests.test_build_07_d_stage3 tests.test_build_07_d_stage4   131 PASS
python -m unittest discover -s tests                                                 791 PASS
python -m compileall -q japanese_house_modeler tests                                 PASS
git diff --check                                                                      PASS
git status --short --branch                                                          clean
```

The automated Stage-1 suite covers generalized Turn frame math, exact-90 reduction, numerical singularities, EQUAL_2/3/4 fractions, EQUAL_3 outer-corner preservation, nominal-cell coverage, left/right mirroring, RiseEvent invariants, canonical-order AUTO allocation, narrow-width regression, deterministic regeneration, REVERSE ascent-local front/rear ownership, exact physical Winder Riser thickness, and legacy schema regression.

## 4. Stage 1 accepted contracts

### Schema / identity

- schema 5 is the Build 07-E generalized Turn / Winder schema.
- existing schema-1/2/3/4 Stair data is not silently upgraded merely by loading or regenerating.
- accepted schema-4 exact-90 Landing behavior remains on the schema-4 resolver unless an explicit 07-E promotion is performed.
- interior `path_point_id` remains Turn identity authority; no independent persistent `turn_id` UUID is introduced.
- `winder_pattern` is the single canonical Winder pattern authority.
- EQUAL_2 / EQUAL_3 / EQUAL_4 derive their step count / equal-angle rule from that authority.

### Generalized Turn foundation

- signed Turn direction, incoming/outgoing directions, inside/outside normals, inner pivot `I`, outer corner `O`, `E_in`, `E_out`, and the Turn envelope are resolved by pure testable geometry helpers.
- left/right turns share the same generalized resolver rather than separate world-space generators.
- exact 90-degree equal-width geometry reduces to the accepted nominal square Turn envelope.
- numerical singularity checks are geometry checks, not legal-like width minima.

### EQUAL Winder nominal geometry

- Stage 1 production supports exact-90-degree 3-point L Winder patterns EQUAL_2 / EQUAL_3 / EQUAL_4.
- divider rays are derived from equal-angle fractions and intersect the ordered outer chain.
- nominal cells cover the complete Turn envelope without positive-area overlap or unintended gap.
- EQUAL_3 preserves the outer corner `O`; the central cell keeps the `Q1 -> O -> Q2` outer chain rather than cutting across `Q1 -> Q2`.

### RiseEvent / allocation

- RiseEvent authority follows the final 07-E invariant `S + L + W + 1 = N`.
- each Stage-1 Winder tread owns one Winder RiseEvent.
- Riser ownership belongs to the higher / destination surface.
- schema-5 AUTO straight allocation preserves canonical physical Path order as the tie-break authority.
- positive ordinary straight runs do not silently receive zero events.
- REVERSE changes traversal order / RiseEvent order without rewriting canonical straight allocation.

### Physical Winder TREAD / RISER

- Stage 1 produces SQUARE Winder TREAD / RISER geometry.
- physical Winder Riser front/rear ownership is ascent-local.
- REVERSE swaps each nominal cell's physical front/downhill and rear/uphill boundaries while preserving the canonical subdivision.
- Winder Riser thickness is resolved as an exact constant-distance strip from the destination tread front divider and clipped to the destination nominal cell.
- the mathematical inner pivot narrowing to zero is not itself a rejection condition.
- no extra Riser is generated on the final Winder tread's rear/uphill boundary.

### Old-house width guardrail

- width alone is not a legal-style rejection gate.
- 900 / 750 / 650 mm Stage-1 EQUAL Winder cases remain supported where the actual geometry is valid.
- 650 mm is a regression fixture, not a production minimum.
- no new `MIN_LEGAL_STAIR_WIDTH`-style threshold is accepted.

### Transaction / lifecycle foundation

- invalid candidate geometry is prepared / validated before Scene mutation.
- invalid required-cutback geometry cancels without changing canonical Stair state.
- invalid candidate rejection preserves the existing Mesh datablock pointer.
- Save -> complete Blender exit -> reopen preserves schema-5 Winder state.
- pattern Undo / Redo works through normal Blender UI history.
- repeated Regenerate is deterministic for canonical data, vertex coordinates, and face topology.
- managed Stage-1 runtime state retains identity Object Transform and unique Stair ID.

## 5. Blender 5.2 LTS runtime acceptance

All thirteen grouped Stage-1 runtime tests passed on Candidate r1.

### Test 1 — Candidate identity / schema-5 load — PASS

```text
VERSION=(0,7,4)
DESCRIPTION=Build 07-E: Winder + Arbitrary-angle Turn/Landing
BLENDER=(5,2,0)
SCHEMA=5
MODE=WINDER
PATTERNS=EQUAL_2 / EQUAL_3 / EQUAL_4
```

### Test 2 — existing schema-4 U compatibility — PASS

A pre-existing 4-point schema-4 U Landing remained:

```text
SCHEMA=4
TURN=LANDING
PATTERN=NONE
AUTO=6,5,5
ISSUES=()
```

Installing 07-E did not silently migrate it to schema 5.

### Test 3 — schema-4 U Regenerate regression — PASS

Before / after Regenerate matched exactly for schema, Turn mode, pattern, distribution, Path count, vertex count, and polygon count.

```text
REGEN={'FINISHED'}
SAME=True
ISSUES=()
```

### Test 4 — explicit schema-4 AUTO L -> EQUAL_3 Winder promotion — PASS

A 3-point schema-4 AUTO L was explicitly promoted:

```text
BEFORE=(4, LANDING, NONE, AUTO, 8,8)
AFTER =(5, WINDER, EQUAL_3, AUTO, 6,6)
PROMOTE={'FINISHED'}
ISSUES=()
```

RiseEvent accounting passed:

```text
straight allocation=(6,6)
Winder tread count=3
RiseEvents=16
6 + 6 + 3 + 1 = 16
```

Visual review accepted the 3-step Winder, complete outside corner, Straight/Winder continuity, and absence of large gap / duplicate plate / abnormal protrusion.

### Test 5 — EQUAL_2 production — PASS

```text
STATE=5 WINDER EQUAL_2 AUTO 7,6
ISSUES=()
7 + 6 + 2 + 1 = 16
```

Visual review accepted the 2-step Turn geometry.

### Test 6 — EQUAL_4 production — PASS

```text
STATE=5 WINDER EQUAL_4 AUTO 6,5
ISSUES=()
CHECK=(6,5) 4 16 16
```

Visual review accepted the 4-step Turn geometry and outer-corner preservation.

### Test 7 — REVERSE / Riser ownership — PASS

Canonical allocation remained `(6,5)` while actual REVERSE traversal used the second straight run first.

Representative REVERSE Winder events:

```text
[(6,1,1050.0),
 (7,2,1225.0),
 (8,3,1400.0),
 (9,4,1575.0)]
```

Visual review accepted REVERSE height order, EQUAL_4 subdivision, Straight/Winder joins, and absence of an obvious duplicate interface Riser.

### Test 8 — Save / full exit / reopen persistence — PASS

Before save and after complete Blender exit / reopen:

```text
5 WINDER EQUAL_4 REVERSE 6,5 3 232 176
```

matched exactly and `ISSUES=()`.

### Test 9 — Undo / Redo pattern lifecycle — PASS

The required strict sequence was used:

```text
UI pattern change
-> Ctrl+Z
-> Ctrl+Shift+Z
-> Console verification
```

Undo restored EQUAL_4 and Redo restored EQUAL_3. Final Redo state:

```text
5 WINDER EQUAL_3 REVERSE 6,6 236 178
REDO_ISSUES=()
```

### Test 10 — 750 / 650 mm narrow-width regression — PASS

```text
750 mm: ISSUES=()
650 mm: ISSUES=()
HEIGHT=2800.0
RISERS=16
```

The 650 mm EQUAL_3 REVERSE case remained visually valid; width alone did not trigger rejection.

### Test 11 — invalid candidate atomic rollback — PASS

An intentionally invalid 10000 mm width required more Turn cutback than the adjacent segment length and was rejected normally:

```text
Warning: Turn required cutbackが隣接segment長を超えます。
INVALID={'CANCELLED'}
SNAP_SAME=True
MESH_SAME_DATABLOCK=True
ISSUES=()
```

The original valid 650 mm Stair remained unchanged.

### Test 12 — repeated Regenerate determinism — PASS

Two repeated Regenerate operations produced the exact same canonical values, vertex coordinates, and polygon index layout.

```text
REGEN1={'FINISHED'} SAME1=True
REGEN2={'FINISHED'} SAME2=True
ISSUES=()
```

### Test 13 — final managed-state check — PASS

Representative final state:

```text
TRANSFORM=((0,0,0),(0,0,0),(1,1,1))
SAME_ID_OBJECTS=[('T15_L',5)]
FINAL_STATE=5 WINDER EQUAL_3 REVERSE 650.0 6,6
FINAL_ISSUES=()
```

No duplicate managed Stair ID was present. The test fixture had no Material slots, which is a valid unassigned state.

## 6. Stage 1 intentionally deferred scope

Stage 1 does **not** claim acceptance of:

- BF_1 / BF_2 production geometry
- U / Compact-U Winder production
- two-Turn Winder combination
- arbitrary-angle Landing production
- arbitrary-angle Winder production
- Winder STEPPED_CLOSED final geometry
- continuous Winder SLOPED_CLOSED
- pivot-relief core production geometry
- ordinary Winder Side Board continuation
- Compact-U shared-center Side Board
- Stage-2 thumbnail/icon completion
- Stage-3 finish geometry
- Stage-4 overall lifecycle / full-regression acceptance

Those remain later Build 07-E Stage 2 / 3 / 4 scope.

## 7. Stage 1 acceptance conclusion

Build 07-E Stage 1 — **ACCEPTED** at the exact runtime-tested production tree:

```text
commit 5c806406752cdb52ef1ffaeaf8e6b6055160b030
tree   54ab4dcdbd4cc6f3283d5c6536121e21c2965558
```

Merged main contains the same production tree at:

```text
commit 17ecaf22fa0f94513f5f80d0363502036e0fd40b
tree   54ab4dcdbd4cc6f3283d5c6536121e21c2965558
```

Accepted runtime Candidate:

```text
Japanese_House_Modeler_Build_07_E_Stage1_Candidate_r1.zip
SIZE    152026 bytes
SHA256  eab3a4ef7b5a6a1607d817c5b31c930594d10853f311909413887e79f2d981c1
```

Build 07-E overall remains **NOT YET ACCEPTED**. At the Stage-1 acceptance point, the next implementation stage was Build 07-E Stage 2.

---

## 8. Stage 2 implementation / runtime identity

GitHub PR: #32

Exact runtime-tested production revision:

```text
commit 9424da623953a32a97576ce45bec074b269d4058
tree   7d30e76ae20ad58b72cece1e298f54ee45f90a65
```

Runtime Candidate:

```text
Japanese_House_Modeler_Build_07_E_Stage2_Candidate_r3.zip
SIZE    159639 bytes
SHA256  15d48e9230b5a7e7f0b59954ccbe56acc7fb99bce3d26b39481f969f75c7b1d4
```

Runtime environment:

```text
Blender 5.2 LTS
Add-on version: (0, 7, 4)
Description: Build 07-E: Winder + Arbitrary-angle Turn/Landing
```

Candidate r1 and Candidate r2 were rejected during pre-acceptance runtime review and are not accepted artifacts.

The acceptance-record commit added after runtime testing is documentation-only and does not supersede the exact runtime-tested production revision above.

Merged main revision is recorded after PR #32 merge in the post-merge update of this Acceptance Record.

## 9. Stage 2 automated / static evidence

Final implementation report after the Candidate-r3 common-inner-finish correction:

```text
python -m unittest tests.test_build_07_e_stage1 tests.test_build_07_e_stage2   127 PASS
python -m unittest tests.test_build_07_d_stage1 tests.test_build_07_d_stage2 tests.test_build_07_d_stage3 tests.test_build_07_d_stage4   131 PASS
python -m unittest discover -s tests                                          893 PASS
python -m compileall -q japanese_house_modeler tests                          PASS
git diff --check                                                               PASS
git status --short --branch                                                   clean
```

Automated coverage includes per-Turn storage, BF patterns, U / Compact-U classification, arbitrary-angle Landing / EQUAL Winder, AUTO / MANUAL allocation, schema-4 migration guards, free-angle Path movement, REVERSE owner indices, physical front-edge modes, constant-distance nosing, exact rear-support / Riser-back reuse, `K_finish`, narrow-width regression, and deterministic physical trim.

## 10. Stage 2 accepted contracts

### Per-Turn authority / compatibility

- `TurnSpec(path_point_id, turn_mode, winder_pattern)` is the canonical per-Turn authority for materialized schema-5 state.
- no persistent independent Turn UUID is introduced.
- Stage-1 three-point schema-5 files with empty `turn_specs` retain scalar compatibility without silent load-time materialization.
- explicit schema-4 U promotion materializes all interior Turn identities; unedited Turns remain `LANDING / NONE`.
- schema-4 MANUAL may promote to generalized LANDING with explicit allocation conversion; schema-4 MANUAL -> WINDER remains blocked until AUTO.

### BF / U / Compact-U / arbitrary angle

- BF_1 and BF_2 are supported as the specified asymmetric right-angle patterns.
- U uses two persistent interior Turn identities with independent mode/pattern assignments.
- Compact-U preserves both Turn identities, uses zero ordinary middle-run allocation, and maintains the deterministic shared interface.
- arbitrary-angle generalized LANDING is production-supported.
- arbitrary-angle EQUAL Winder uses actual signed Turn angle rather than snapping production geometry to 15-degree increments.
- Shift15 remains an interaction convenience only.

### Allocation / migration

- schema-5 AUTO Path/dimension edits invalidate stale AUTO allocation and recompute from candidate geometry.
- schema-5 MANUAL uses `manual_riser_allocation` as authority and preserves the stored AUTO value independently.
- invalid MANUAL totals are rejected before canonical or Mesh mutation.
- `S + L + W + 1 = N` remains the whole-Stair RiseEvent invariant.

### Physical Winder finish

- nominal Winder cells remain separate from physical finish geometry.
- `L_face`, `L_nose`, and `L_back` are shared semantic boundary authorities.
- positive nosing remains a constant perpendicular offset at both the inner and outer endpoints of the exposed front edge.
- lower-tread rear-support and destination-Riser back boundaries reuse the same semantic edge authority.
- background-visible wedge cavities between Winder TREAD/RISER components are not accepted.
- all physical TREAD/RISER inner trim for one Turn uses one deterministic common inner finish chord `K_finish`.
- raw per-tread inner intersections are intermediate only; they are not final visible spike points.
- SQUARE / BEVEL / ROUND operate from the explicit semantic exposed front edge.
- the physical finish contract applies to exact-90 and arbitrary-angle Winder and to each Turn in U / Compact-U.

## 11. Blender 5.2 LTS Stage 2 runtime acceptance

All thirteen Stage-2 runtime tests passed on Candidate r3 after Candidate-r1 / r2 defects were corrected.

### Test 1 — Candidate / RNA / pattern registration — PASS

Confirmed schema-5 Stair/Turn RNA registration and patterns:

```text
NONE / EQUAL_2 / EQUAL_3 / EQUAL_4 / BF_1 / BF_2
```

### Test 2 — schema-4 compatibility / no silent migration — PASS

Existing schema-4 U objects remained schema 4 with empty `turn_specs`; existing Stage-1 scalar schema-5 compatibility state remained unmaterialized until explicit edit.

### Test 3 — schema-4 U -> schema-5 per-Turn promotion — PASS

Turn 1 was explicitly changed to `WINDER / EQUAL_2`; Turn 2 remained `LANDING / NONE` and schema became 5. `ISSUES=()`.

### Test 4 — independent Turn editing — PASS

The second persistent Turn was independently changed to `WINDER / EQUAL_3` while Turn 1 remained `WINDER / EQUAL_2`. `ISSUES=()`.

### Test 5 — BF_1 / BF_2 — PASS

A U stair accepted:

```text
Turn 1 = WINDER / BF_1
Turn 2 = WINDER / BF_2
ISSUES=()
```

Visual review confirmed asymmetric BF geometry without major failure.

### Test 6 — Compact-U — PASS

Representative result:

```text
CLASS=COMPACT_U
RUNS_MM=(2547.73,0.0,2515.2)
AUTO=(6,0,5)
SHARED=2
ISSUES=()
```

The middle ordinary straight region and its event allocation were both zero, and the two Turns connected through the shared interface.

### Test 7 — 63-degree EQUAL_3 Winder physical geometry — PASS after Candidate r3

Canonical evidence:

```text
ANGLE=63.0
PATTERN=EQUAL_3
CELLS=3
ISSUES=()
```

Pre-acceptance runtime defects found during this test were corrected through Candidate r2 and r3. Final visual review confirmed:

- no background-visible outer Tread/Riser wedge cavity;
- positive nosing remains visibly constant at the inner and outer ends;
- Winder inner finish follows one common line;
- acute triangular/spike-like inner termination is removed.

A small terminal alignment difference where `K_finish` meets neighboring Straight geometry remains a Stage-3 integration watchpoint rather than a Stage-2 blocker.

### Test 8 — 63-degree arbitrary-angle Landing — PASS

```text
ANGLE=63.0
TURN=[('LANDING','NONE')]
LANDINGS=1
ISSUES=()
```

Visual review found no giant face, spike, or obvious open hole. Landing front/nosing presentation and the Landing tread / destination-Riser rear-junction finish are recorded as later integration watchpoints.

### Test 9 — SQUARE / BEVEL / ROUND — PASS

Runtime Mesh counts demonstrated actual geometry changes:

```text
SQUARE  V=246 F=183
BEVEL   V=306 F=213 ISSUES=()
ROUND   V=486 F=303 ISSUES=()
```

Visual review confirmed BEVEL and ROUND were applied to the exposed front-edge geometry without regressing the common inner line or reopening the outer cavity.

### Test 10 — AUTO -> MANUAL authority — PASS

```text
MODE=MANUAL
AUTO=6,6
MANUAL=5,7
ISSUES=()
```

The saved AUTO allocation remained independent while MANUAL became active authority.

### Test 11 — invalid MANUAL atomic rejection — PASS

An invalid `5,6` MANUAL candidate was rejected. Before/after evidence remained identical:

```text
MANUAL=5,7
same Mesh datablock pointer
V=246
F=183
ISSUES=()
```

The visible Stair did not change.

### Test 12 — Candidate-r3 Compact-U + BF regression — PASS

```text
CLASS=COMPACT_U
RUNS_MM=(2547.73,0.0,2515.2)
AUTO=(6,0,5)
TURNS=[('WINDER','BF_1'),('WINDER','BF_2')]
SHARED=2
ISSUES=()
```

Visual review confirmed no reappearance of the rejected outer wedge cavity or inner spike failure.

### Test 13 — Save / full exit / reopen persistence — PASS

Before save and after complete Blender exit / reopen matched:

```text
SCHEMA=5
ASCENT=REVERSE
DIST=AUTO
AUTO=6,0,5
TURNS=[('WINDER','BF_1'),('WINDER','BF_2')]
PATH=[(45.990631,4.0),(48.988358,4.0),(48.988358,3.1),(46.023155,3.1)]
V=248
F=184
ISSUES=()
```

Visual appearance also remained unchanged after reopen.

## 12. Stage 2 resolved pre-acceptance defects

Candidate r1 and r2 exposed physical finish defects that were corrected before acceptance:

1. Winder TREAD / destination-Riser boundary divergence produced a real background-visible wedge cavity toward the outer side.
2. positive nosing tapered from the requested value at the outer side to approximately zero at the mathematical inner pivot.
3. per-tread raw physical inner miters produced an irregular sawtooth / protruding inner finish.
4. acute triangular / spike-like inner nosing terminations remained after the first correction.

The accepted Candidate r3 resolves these through shared `L_face / L_nose / L_back` authorities and the Turn-local common inner finish chord `K_finish`.

## 13. Stage 3 integration watchpoints / deferred scope

Stage 2 does **not** claim acceptance of Stage-3 CLOSED body / Side Board geometry.

The following must be explicitly revisited during Stage 3:

- small terminal alignment difference where a Turn-local `K_finish` meets neighboring Straight TREAD/RISER geometry;
- whether that terminal difference creates a T-junction, short missing strip, filler face, or local cavity when STEPPED_CLOSED / SLOPED_CLOSED is added;
- Side Board ON/OFF behavior at both Winder terminal seams;
- REVERSE seam ownership at entry/exit;
- Compact-U interaction between two independent Turn-local inner chords and the shared middle interface;
- arbitrary-angle Landing front/nosing presentation;
- arbitrary-angle Landing tread / destination-Riser rear-junction finish;
- Winder STEPPED_CLOSED final geometry;
- continuous Winder SLOPED_CLOSED with finite pivot relief / high-side closure;
- ordinary Winder Side Board continuation;
- Compact-U shared-center Side Board.

Stage 3 must consume accepted Stage-2 physical trim stations rather than silently moving or undoing `K_finish`.

## 14. Stage 2 acceptance conclusion

Build 07-E Stage 2 — **ACCEPTED** at the exact runtime-tested production revision:

```text
commit 9424da623953a32a97576ce45bec074b269d4058
tree   7d30e76ae20ad58b72cece1e298f54ee45f90a65
```

Accepted runtime Candidate:

```text
Japanese_House_Modeler_Build_07_E_Stage2_Candidate_r3.zip
SIZE    159639 bytes
SHA256  15d48e9230b5a7e7f0b59954ccbe56acc7fb99bce3d26b39481f969f75c7b1d4
```

PR #32 merge identity will be added after merge. Documentation-only commits do not replace the accepted runtime-tested production tree above.

Build 07-E overall remains **NOT YET ACCEPTED**. Next implementation stage is **Build 07-E Stage 3**.
