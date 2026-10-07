# BUILD 07-E STAGE 3B ACCEPTANCE RECORD
## Japanese House Modeler — Fresh Stage 3B SLOPED_CLOSED / Side Boards OFF

Date: 2026-10-07

## 1. Status

- Build 07-E Stage 1 — **ACCEPTED**
- Build 07-E Stage 2 — **ACCEPTED**
- Build 07-E Stage 2.5 — **ACCEPTED**
- Build 07-E first Stage-3 attempt / PR #33 — **ABANDONED / CLOSED / NOT MERGED**
- Fresh Build 07-E Stage 3A — **ACCEPTED at Candidate r2**
- Fresh Build 07-E Stage 3B — **ACCEPTED at runtime r9**
- Fresh Build 07-E Stage 3C — **NEXT**
- Build 07-E overall — **NOT YET ACCEPTED**

Stage 3B adds schema-5 `STANDARD_RESIDENTIAL` Winder `SLOPED_CLOSED` visible body generation with both Side Boards disabled, while preserving the accepted Stage-3A `STEPPED_CLOSED` geometry and the accepted Build 07-D schema-4 Landing/Residential path.

The acceptance authority for this stage is this record together with `BUILD_07_E_SPECIFICATION.md` Section 39.

## 2. Final merge authority and runtime-tested production identity

Final GitHub merge authority:

```text
PR #47
https://github.com/asleep-cdx/blender-japan-building-addon/pull/47
```

PR #38 through PR #46 were intermediate technical-continuation PRs during Stage-3B iteration. They are not the final merge authority.

Exact Blender runtime-tested production revision:

```text
commit 389f7e9d30a181c3fcd2c578e8af7bbdc16189e7
tree   3154653ca6b608b1ae7b11e42a40d497b7c50b99
```

The remote PR #47 production commit contains the same source tree as the final Codex working-tree revision used to prepare the r9 runtime package.

Runtime environment:

```text
Blender 5.2 LTS
Add-on version: 0.7.4
```

The final Blender tests were performed with the Stage-3B r9 add-on ZIP produced from the production contents above. The local archive filename, final stored byte size, and SHA256 are intentionally verified in the post-merge Windows acceptance-archive step rather than guessed in this record.

Documentation-only commits created after runtime verification do not supersede the exact runtime-tested production commit/tree above.

## 3. Accepted Stage-3B geometry contract

### Straight SLOPED_CLOSED

Accepted Straight Flight `SLOPED_CLOSED` production remains the existing Residential sloped-body implementation. Stage 3B does not redesign accepted Straight sloped geometry.

### Winder SLOPED_CLOSED

For Winder cells, the accepted Stage-3B contract is deliberately simpler than the earlier station-driven concept.

Each Winder `SLOPED_CLOSED` UNDERBODY uses the same matching-ring prismatic Winder support contract as the accepted corrected `STEPPED_CLOSED` Winder body:

- upper and lower rings reuse the same ordered XY support footprint;
- the body does not inherit physical TREAD nosing;
- the ascent-local FRONT support begins behind the RISER at exactly `riser_thickness`;
- upper Z is the accepted tread underside;
- lower Z is the next-lower rise level, with the existing base-floor exception;
- normal body depth is derived from `actual_riser - tread_thickness`;
- no station-driven per-vertex lower-Z interpolation is used for Winder SLOPED production.

This is an intentional visual-first decision. Straight runs remain sloped; Winder underside cells use the simpler accepted prismatic body.

### Shared rear/exterior authority

The physical Winder TREAD and Winder UNDERBODY reuse one rear/exterior support authority.

For internal Winder-to-Winder interfaces, the coordinate is the exact successor RISER hidden-rear outer contact.

For the final Winder interface, the existing canonical exterior/supporting-line authority is used.

The accepted implementation does not approximate these coordinates independently.

### Canonical exterior chain

Physical endpoint replacement must not turn the canonical exterior

```text
entry_outer -> outer_corner -> exit_outer
```

into a direct chord across `outer_corner`.

The accepted production therefore preserves the exact canonical `frame.outer_corner` when adjacent physical exterior points lie on opposite sides of the corner.

This rule is geometry-semantic and is not implemented as an exact-90, world-axis, EQUAL_2, or EQUAL_4 production special case.

### Inner pivot / top geometry preservation

The mathematical Winder inner pivot remains fixed. Stage-3B corrections do not move the accepted top pivot, canonical Turn corner, TREAD front nosing authority, or RISER production geometry merely to accommodate the body.

## 4. Pre-acceptance correction history

Stage 3B required multiple Blender-driven geometry corrections before acceptance.

The important historical conclusions are:

1. Early Stage-3B outer-envelope work removed Winder exterior-line stepping while keeping the accepted inner pivot behavior.
2. An unequal upper/lower footprint loft experiment for `STEPPED_CLOSED` worsened the runtime result and was rejected.
3. Matching-ring Winder body topology was restored; the lower elevation was corrected from the actual rise authority rather than using closure depth as a plan inset.
4. The Winder body rear/exterior point was aligned to the same authority as the accepted TREAD/RISER contact.
5. Winder `SLOPED_CLOSED` was simplified to the same accepted Winder prism contract instead of continuing a collapsing station-driven wedge.
6. EQUAL_2 / EQUAL_4 exposed a final outer-corner chord defect. The canonical outer corner is now explicitly preserved in the polygon chain.
7. The final r9 runtime result preserves the previously accepted EQUAL_3, BF, arbitrary-angle and Compact-U behavior while correcting the EQUAL_2 / EQUAL_4 exterior chain.

Rejected intermediate runtime geometry is not an acceptance authority.

## 5. Automated / static evidence

Final PR #47 implementation report:

```text
python -m unittest tests.test_build_07_e_stage2_5
6 tests PASS

python -m unittest tests.test_build_07_e_stage1 tests.test_build_07_e_stage2
127 tests PASS

python -m unittest tests.test_build_07_e_stage3_fresh
10 tests PASS

python -m unittest tests.test_build_07_e_stage3b_fresh
17 tests PASS

python -m unittest tests.test_build_07_d_stage1 tests.test_build_07_d_stage2 tests.test_build_07_d_stage3 tests.test_build_07_d_stage4
131 tests PASS

python -m unittest discover -s tests
926 tests PASS

python -m compileall -q japanese_house_modeler tests
PASS

git diff --check
PASS
```

Focused Stage-3B tests cover exact-90 and arbitrary-angle Winder geometry, FORWARD/REVERSE, EQUAL_2/EQUAL_3/EQUAL_4, BF_1/BF_2, Compact-U, canonical outer-corner preservation, shared rear/exterior authority, matching upper/lower XY rings, Straight-body freeze, Stage-3A stepped regression, schema-4/07-D regression, and deterministic generation.

## 6. Blender 5.2 LTS runtime acceptance

The final r9 package passed the Stage-3B runtime plan and the additional geometry sweep triggered by the EQUAL_2 / EQUAL_4 defect.

### Runtime geometry sweep — EQUAL_2 / EQUAL_4 / EQUAL_3 — PASS

The following were visually inspected with top/wire views and close exterior-corner views:

- 90-degree L / EQUAL_2;
- 90-degree L / EQUAL_4;
- approximately 63-degree / EQUAL_2;
- approximately 63-degree / EQUAL_4;
- Compact-U with Turn 1 = EQUAL_2 and Turn 2 = EQUAL_4;
- EQUAL_3 regression in both stepped and sloped contexts.

Accepted result:

- no outer-line stepping;
- canonical outer corner retained;
- no regression of the accepted inner/pivot line;
- no new major gap or protrusion;
- prior Stage-3B corrections remained preserved.

### Test 4 — BF_1 FORWARD / BF_2 REVERSE — PASS

Both asymmetric BF patterns were inspected around the first/last step, Winder region, outer/inner lines, and underside.

No geometry breakage was observed.

### Test 5 — Compact-U / EQUAL_3 + EQUAL_3 / SLOPED_CLOSED — PASS

A Compact-U schema-5 Stair with both Turns set to EQUAL_3 was regenerated in `SLOPED_CLOSED`.

Visual review confirmed:

- outer and inner plan lines coherent;
- no TREAD-top body penetration;
- no unnatural Turn-to-Turn daylight gap;
- accepted Winder underside finish present;
- both Turns retained their intended geometry.

### Test 6 — STEPPED_CLOSED regression — PASS

The accepted r7/r9 Compact-U stepped body form was checked again after the Stage-3B shared Winder-body work.

Visual review confirmed:

- outer and inner lines unchanged;
- underside geometry unchanged in the accepted visible sense;
- no regression of the corrected Winder body/TREAD/RISER relationship.

### Test 7 — regenerate / determinism / save / full exit / reopen — PASS

Representative Compact-U mesh counts before and after repeated verification:

```text
V/E/F = 344 / 570 / 304
```

The counts were unchanged across repeated checks. After save, full Blender exit, reopen, and Regenerate, the Stair returned to the same managed shape with no duplicate part growth or visible geometry change.

### Test 8 — schema-4 / Build 07-D regression smoke — PASS

An accepted schema-4 Build 07-D Landing Stair was checked with console state capture before and after Regenerate.

Observed state:

```text
SCHEMA = 4
TURN = LANDING
DIR = REVERSE
DIST = AUTO
AUTO = 8,8
V/E/F = 433 / 765 / 412

STATE SAME  = True
MESH SAME   = True
COUNTS SAME = True
```

Visual review also confirmed no shape change.

Stage-3B schema-5 Winder code therefore did not route the accepted schema-4 07-D Stair into the new Winder production path.

## 7. Acceptance boundaries

Fresh Stage 3B accepts:

- schema-5 Winder `SLOPED_CLOSED` visible body with Side Boards OFF;
- the corrected Stage-3A `STEPPED_CLOSED` Winder body as the retained stepped baseline;
- exact shared Winder rear/exterior authority;
- canonical exterior-corner preservation for physical TREAD and Winder UNDERBODY polygons;
- FORWARD / REVERSE;
- EQUAL_2 / EQUAL_3 / EQUAL_4;
- BF_1 / BF_2;
- arbitrary-angle smoke/regression;
- Compact-U two-Turn generation;
- deterministic regeneration / persistence;
- accepted schema-4 Build 07-D isolation.

Fresh Stage 3B does **not** accept:

- ordinary Winder Side Boards;
- Compact-U shared-center Side Board;
- Stage-3C/3D/3E work;
- Stage-4 overall lifecycle acceptance;
- a global exact-solid / Boolean / PHYSICAL_CONTACT / BodyInterface architecture.

Those remain later scope.

## 8. Acceptance conclusion

Fresh Build 07-E Stage 3B — **ACCEPTED at runtime r9**.

Exact runtime-tested production revision:

```text
commit 389f7e9d30a181c3fcd2c578e8af7bbdc16189e7
tree   3154653ca6b608b1ae7b11e42a40d497b7c50b99
```

Final merge authority:

```text
PR #47
```

Fresh Stage 3C — ordinary Winder Side Board continuation — is **NEXT**.

Build 07-E overall remains **NOT YET ACCEPTED**.
