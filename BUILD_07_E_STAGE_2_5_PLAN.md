# Build 07-E Stage 2.5 — Pre-Stage-3 Geometry Simplification Plan

> **Status: PLANNED / AUDIT COMPLETE / IMPLEMENTATION NOT STARTED**  
> Updated: 2026-10-05  
> Branch: `stage-2-5-pre-stage3-geometry-reset`  
> Base: current accepted `main` at Build 07-E Stage 2 completion  
> Base commit: `202fd3a2fc82ba5979445e89c160cf46dd95fc9f`

---

## 1. Purpose

Stage 2.5 is a small, deliberate correction stage inserted **before a fresh Stage 3 restart**.

Its purpose is **not** to add new Stage-3 functionality. Its purpose is to prepare a simpler and safer Winder visible-geometry baseline for Stage 3 while preserving the accepted Build 07-D / Build 07-E Stage-2 feature foundation.

The project reached Build 07-E Stage 2 Candidate r3 and accepted that runtime-tested result. However, later Stage-3 work showed that the Stage-2 r2/r3 physical Winder refinements made Stage-3 underside / Side Board integration substantially more complex than the user's practical Blender workflow requires.

The project does not require CAD-style Boolean-clean internal solids. For this project, **visible exterior quality, predictable shape, and reliable Blender usability are more important than hidden internal mesh cleanliness**.

Therefore Stage 2.5 intentionally restores the **simpler Stage-2 Candidate-r1 Winder visible TREAD/RISER production behavior**, while retaining later Stage-2 capabilities that are not part of that geometry complication.

---

## 2. Why Stage 2.5 exists

The abandoned first Stage-3 attempt (PR #33) accumulated precision-oriented geometry infrastructure around exact internal collision / ownership, BodyInterface authority, physical Winder body exclusion, SLOPED decomposition, and generalized interface reconciliation.

That direction was later found to be misaligned with the user's actual modeling requirements.

The user accepts hidden internal intersections when:

- the visible stair shape is correct;
- there is no obvious exterior hole;
- there is no major visible spike;
- there is no exterior z-fighting;
- the generated object remains usable and editable.

The first Stage-3 branch also regressed previously accepted visible geometry during runtime testing:

- Winder top geometry became malformed in an early Stage-3 runtime candidate;
- SLOPED Winder underbody became visible through / above tread regions;
- Build 07-D Landing underside / related Residential geometry was observed to regress in the Stage-3 runtime candidate.

The decision is therefore:

> **Do not repair PR #33 further. Prepare and accept a controlled Stage 2.5 baseline, merge it to `main`, then start Stage 3 again from a new branch.**

---

## 3. PR #33 status

PR #33, the first Build 07-E Stage-3 implementation attempt, is **ABANDONED / CLOSED / NOT MERGED / NOT TO BE MERGED**.

Its branch may remain in GitHub as historical/reference material, but it is not a production baseline.

Future Stage-3 work must start from the accepted `main` after Stage 2.5 is completed and merged.

Useful isolated ideas from PR #33 may be reused only after explicit review. Its architecture is not inherited by default.

---

## 4. Current accepted baseline

Before Stage 2.5 begins, `main` remains the accepted Build 07-E Stage-2 baseline:

```text
main commit: 202fd3a2fc82ba5979445e89c160cf46dd95fc9f
```

The final runtime-tested Build 07-E Stage-2 Candidate r3 production revision was:

```text
commit: 9424da623953a32a97576ce45bec074b269d4058
tree:   7d30e76ae20ad58b72cece1e298f54ee45f90a65
ZIP:    Japanese_House_Modeler_Build_07_E_Stage2_Candidate_r3.zip
SHA256: 15d48e9230b5a7e7f0b59954ccbe56acc7fb99bce3d26b39481f969f75c7b1d4
```

Candidate r3 remains the accepted Stage-2 result until Stage 2.5 itself is runtime-tested and accepted.

---

## 5. Preserved runtime ZIP artifacts — audited 2026-10-05

The actual user-retained Stage-2 runtime ZIPs were inspected directly.

### Candidate r1

```text
ZIP:    Japanese_House_Modeler_Build_07_E_Stage2_Candidate_r1.zip
SHA256: 8c6c7100e0a51e550525fedca0e214e95b5ca8b73874ce4c7b213d9149f62054
commit: b0d92fc15f7ec103e3cf18b6110dce2b5841fd3e
tree:   e90e4bfa0e0583552bc761a200b8e51a52590470
message: Finalize Stage 2 allocation and error policies
```

### Candidate r2

```text
ZIP:    Japanese_House_Modeler_Build_07_E_Stage2_Candidate_r2.zip
SHA256: 2d6e34b4589ea993995903fdbe30dfd8c68559daae2438ca955ced0563fd5cac
commit: 26ddf5b79bb933ea6b8bf43a3a4c585c11ddf597
tree:   9c4804864dab6e07cfd54be8f38c85fae671cd1a
message: Fix physical Winder boundary geometry
```

### Candidate r3

```text
ZIP:    Japanese_House_Modeler_Build_07_E_Stage2_Candidate_r3.zip
SHA256: 15d48e9230b5a7e7f0b59954ccbe56acc7fb99bce3d26b39481f969f75c7b1d4
commit: 9424da623953a32a97576ce45bec074b269d4058
tree:   7d30e76ae20ad58b72cece1e298f54ee45f90a65
message: Add common Winder inner finish chord
```

The r1 ZIP source was matched to the Git revision above. It is therefore a concrete restoration authority, not a visual approximation target.

---

## 6. Audit result — exact changed production file

A recursive comparison of all three retained add-on ZIPs found:

```text
r1 -> r2: japanese_house_modeler/stair_turn.py only
r2 -> r3: japanese_house_modeler/stair_turn.py only
r1 -> r3: japanese_house_modeler/stair_turn.py only
```

No other packaged add-on Python file changed between the three runtime candidates.

This is a major Stage-2.5 safety result:

- accepted Build 07-D Landing / Residential implementation files did not change across r1/r2/r3;
- Stage 2.5 does not need to roll the package back wholesale;
- the restoration target can be narrowly limited to the Winder top production path in `stair_turn.py`.

Do **not** replace the whole current `stair_turn.py` with the r1 file. Current Stage-2 r3 remains the structural base.

---

## 7. Exact r1 -> r2 geometry change

Candidate r1 used the simpler per-cell production path based on:

```text
physical_winder_tread_polygon(...)
resolve_winder_riser_plan(...)
```

Each Winder cell was resolved locally from its nominal cell and local physical boundaries.

Candidate r2 introduced Turn-wide semantic physical-plan authority, including:

```text
PhysicalWinderBoundary
PhysicalWinderTreadPlan
resolve_physical_winder_plans(...)
_semantic_boundary(...)
_line_chain_intersection(...)
_trim_semantic_line(...)
```

Production `build_winder_fragments()` changed from the r1 per-cell path to:

```text
resolve_physical_winder_plans(...)
    -> plan.polygon
    -> plan.exposed_front_edge
    -> plan.riser_polygon
```

This was the first major increase in Stage-3 seam complexity.

Stage 2.5 restoration target therefore includes restoring the **r1 production call behavior** for visible Winder TREAD/RISER geometry, rather than using the r2/r3 Turn-wide physical-plan path.

---

## 8. Exact r2 -> r3 geometry change

Candidate r3 added the Turn-local common inner finish chord system:

```text
PhysicalWinderInnerTrim
K_finish / common inner physical finish chord
inner_front
inner_rear
inner_edge
```

`resolve_physical_winder_plans()` was extended so raw inner miters no longer defined the final visible inner edge. Instead, each tread/riser was trimmed to one Turn-local common chord.

This solved Stage-2 visual defects such as inner spikes / sawtooth finish, but it also created a second geometric seam authority relative to adjacent Straight geometry.

The accepted Candidate-r3 runtime record itself documented a remaining entry/exit alignment difference where `K_finish` meets the neighboring Straight geometry.

For Stage 2.5, the r3 `K_finish` system is **not** the desired production authority for the restored r1-equivalent Winder top.

---

## 9. Stage-2.5 restoration authority

Stage 2.5 must use:

> **current accepted Stage-2 r3 codebase as the structural base + exact Candidate-r1 visible Winder TREAD/RISER production behavior as the restoration source.**

The restoration must not be described as "make it look like r1".

The implementation task is:

1. keep the current r3 codebase and all unrelated Stage-2 fixes/features;
2. isolate the visible Winder TREAD/RISER production path;
3. restore the exact r1 per-cell behavior from Candidate r1 / commit `b0d92fc...`;
4. bypass r2/r3 `resolve_physical_winder_plans()` for the Stage-2.5 production path where necessary to reproduce r1 geometry;
5. do not delete later helpers merely because production no longer consumes them unless removal is proven safe and useful;
6. do not modify accepted 07-D geometry.

Preserving unused later helpers is acceptable if that reduces risk. Production authority is what matters.

---

## 10. Candidate-r1 visible behavior intentionally recovered

The user specifically values the Candidate-r1 geometry because the Winder / adjacent Straight inner-side relationship is visually simple and better suited to adding underbody / Side Board geometry.

Target characteristic:

- simple Winder inner boundary behavior;
- visually aligned Turn-side / Straight-side line relationship seen in Candidate r1;
- fewer Turn-local trim authorities for new Stage-3 body construction.

Known Candidate-r1 defect explicitly accepted during Stage 2.5:

- visible TREAD/RISER / terminal gap may remain at the Turn transition.

That gap is **not a Stage-2.5 blocker** if Stage-2.5 reproduces Candidate-r1 geometry and later Stage-2 capabilities remain intact.

Do not reintroduce r2/r3 physical-plan complexity merely to close this known r1 gap during Stage 2.5.

---

## 11. What Stage 2.5 must preserve

Preserve all later functionality not inherently tied to the r2/r3 Winder visible-geometry refinements, including:

- Build 07-D accepted Multi-point Path / L / U / Landing behavior;
- Build 07-D accepted Landing underside and Residential geometry;
- schema-4 persistence and lifecycle behavior;
- Build 07-E schema-5 Turn foundation;
- per-Turn `TurnSpec` state;
- FORWARD / REVERSE;
- arbitrary-angle Turn support;
- BF-1 / BF-2;
- U / Compact-U state and allocation foundations;
- AUTO / MANUAL allocation behavior;
- UI / serialization / persistence added during Stage 2;
- SQUARE / BEVEL / ROUND support to the extent already supported by the restored r1 production path and later non-geometric feature infrastructure;
- deterministic regeneration;
- accepted 07-D regression behavior.

Stage 2.5 must not rewrite accepted 07-D Landing / Straight body geometry merely to simplify future Stage 3.

---

## 12. Geometry identity target

Stage 2.5 should add a narrow regression fixture comparing the restored output to Candidate-r1 authority.

Preferred comparison data:

- Winder TREAD vertex coordinates;
- Winder RISER vertex coordinates;
- polygon vertex order;
- Z elevations;
- ordinal/event ordering;
- FORWARD / REVERSE behavior;
- exact-90 EQUAL_3 reference fixture.

Preferred result:

> **For selected reference fixtures, Stage-2.5 Winder visible geometry is numerically equivalent to Candidate r1 within the project's named numerical tolerance.**

Runtime Blender visual confirmation remains mandatory.

---

## 13. Stage-2.5 runtime acceptance focus

Stage 2.5 is intentionally small.

Minimum runtime checks:

1. exact-90 EQUAL_3 Winder visual comparison against retained Candidate r1;
2. confirm the simple inner/Turn boundary relationship is restored;
3. arbitrary-angle Winder smoke check, e.g. 63°;
4. FORWARD;
5. REVERSE;
6. Build 07-D exact-90 Landing visual regression check, including previously accepted underside/body appearance;
7. Save -> full Blender exit -> reopen smoke check.

Primary acceptance criteria:

- r1-equivalent Winder visible top geometry is restored;
- Stage-2 later functional foundation remains available;
- accepted 07-D Landing / Straight visible geometry is unchanged;
- no new exception / nonfinite / collapsed geometry;
- Candidate-r1 terminal gap is allowed and documented.

After runtime acceptance, create a dedicated Stage-2.5 Acceptance Record before merge.

---

## 14. Documentation authority for Stage 2.5

During Stage 2.5, read together:

- `BUILD_07_E_STAGE_2_5_PLAN.md` — current Stage-2.5 decision and restoration authority;
- `BUILD_07_E_SPECIFICATION.md` — 07-E base specification plus Stage-2.5 override/addendum;
- `ROADMAP.md` — current development order/status;
- `BUILD_07_E_ACCEPTANCE_RECORD.md` — historical accepted Stage-1/Stage-2 evidence;
- `BUILD_07_D_ACCEPTANCE_RECORD.md` — 07-D regression authority;
- `DEVELOPMENT_WORKFLOW.md` — workflow/role authority.

If the old PR #33 implementation or older r2/r3 physical-geometry wording conflicts with this Stage-2.5 restoration decision, **this Stage-2.5 plan and the later Stage-2.5 addendum in `BUILD_07_E_SPECIFICATION.md` win for the Stage-2.5 / restarted-Stage-3 path.**

Historical Acceptance Records remain history and are not rewritten to pretend Candidate r1 was previously accepted.

---

## 15. New Stage-3 philosophy after Stage 2.5

After Stage 2.5 is accepted and merged, Build 07-E Stage 3 restarts from a **new branch**.

The old PR #33 architecture is not the default starting point.

### Required

- visually correct exterior geometry;
- no obvious visible holes;
- no major visible spikes;
- no exterior z-fighting;
- generation / save / reopen / editing remains reliable;
- accepted Stage-2.5 Winder top geometry remains unchanged;
- accepted Build 07-D Landing / Straight body geometry remains unchanged unless a separately approved correction is required.

### Allowed internally

- UNDERBODY penetrating TREAD/RISER in hidden regions;
- adjacent component bodies overlapping internally;
- hidden duplicate/internal faces;
- separate overlapping closed components;
- no exact whole-stair Boolean union.

### Not required for restarted Stage-3 r1

- exact positive-volume intersection elimination;
- convex decomposition audits;
- exact internal Boolean ownership;
- complete PHYSICAL_CONTACT classification;
- exact internal cavity ownership;
- exact BodyInterface union proof.

The practical goal is a useful Blender modeling aid, not a CAD/BIM watertight-solid kernel.

---

## 16. Forbidden Stage-2.5 shortcuts

Do not:

- reset the whole repository to Candidate r1;
- replace the whole current `stair_turn.py` with the r1 file;
- restore r1 by visual approximation;
- change 07-D Landing geometry to fit future Stage 3;
- implement Stage-3 UNDERBODY or Side Board in Stage 2.5;
- repair the known Candidate-r1 terminal gap during the same restoration unless separately approved;
- merge PR #33;
- start the new Stage-3 branch before Stage 2.5 runtime acceptance and merge.

---

## 17. Current decision summary

```text
Build 07-E Stage 2 r3 accepted
        ↓
PR #33 first Stage-3 attempt ABANDONED / CLOSED / NOT MERGED
        ↓
Stage 2.5 dedicated branch
        ↓
r1/r2/r3 ZIP AUDIT COMPLETE
        ↓
restore exact r1-equivalent Winder visible production path narrowly
        ↓
run automated + Blender runtime Stage-2.5 checks
        ↓
write Stage-2.5 Acceptance Record
        ↓
Stage 2.5 accepted + merge to main
        ↓
create fresh Stage-3 branch
        ↓
implement visual-first underbody / Side Board with hidden overlap allowed
```

Do not skip the Stage-2.5 runtime check and do not restart Stage 3 from PR #33.
