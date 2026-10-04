# Build 07-E Stage 2.5 — Pre-Stage-3 Geometry Simplification Plan

> Status: PLANNED / PRE-STAGE-3 BASELINE PREPARATION  
> Created: 2026-10-04  
> Branch: `stage-2-5-pre-stage3-geometry-reset`  
> Base: current accepted `main` at Build 07-E Stage 2 completion  
> Base commit: `202fd3a2fc82ba5979445e89c160cf46dd95fc9f`

---

## 1. Purpose

Stage 2.5 is a small, deliberate correction stage inserted **before a fresh Stage 3 restart**.

Its purpose is **not** to add new Stage-3 functionality. Its purpose is to prepare a simpler and safer Winder visible-geometry baseline for Stage 3 while preserving the accepted Build 07-D / Build 07-E Stage-2 feature foundation.

The project reached Build 07-E Stage 2 Candidate r3 and accepted that runtime-tested result. However, later Stage-3 work revealed that several Stage-2 r2/r3 physical Winder refinements made Stage-3 underside / Side Board integration substantially more complex than the user's practical Blender workflow requires.

The user does not require CAD-style Boolean-clean internal solids. For this project, **visible exterior quality and reliable Blender usability are more important than hidden internal mesh cleanliness**.

Therefore Stage 2.5 intentionally restores the **simpler Stage-2 Candidate-r1 Winder geometry behavior** where that simplification makes Stage-3 body construction easier, while retaining later Stage-2 capabilities that are still required.

---

## 2. Why Stage 2.5 exists

The abandoned first Stage-3 attempt (PR #33) accumulated a large amount of precision-oriented geometry infrastructure, including exact internal collision / ownership work, BodyInterface authority, physical Winder body exclusion, SLOPED decomposition audits, and generalized interface reconciliation.

This precision-first direction was later found to be misaligned with the user's actual modeling requirements.

In Blender, the user accepts hidden internal intersections when:

- the visible stair shape is correct;
- there is no obvious exterior hole;
- there is no major visible spike;
- there is no exterior z-fighting;
- the generated object remains usable and editable.

The first Stage-3 branch also regressed previously accepted visible geometry during runtime testing:

- Winder top geometry became malformed in an early Stage-3 runtime candidate;
- SLOPED Winder underbody became visible through / above tread regions;
- Build 07-D Landing underside / related Residential geometry was also observed to regress in the Stage-3 runtime candidate.

These regressions showed that the branch had become too complex and too entangled with previously accepted geometry.

The decision is therefore:

> **Do not repair PR #33 further. Prepare a controlled Stage 2.5 baseline, merge that baseline, then start Stage 3 again from a clean branch.**

---

## 3. PR #33 status

PR #33, the first Build 07-E Stage-3 implementation attempt, is **ABANDONED / NOT TO BE MERGED**.

Its branch may remain in GitHub as historical/reference material, but it is not a production baseline and must not be merged into `main`.

Future Stage-3 work must start from the accepted Stage-2 baseline after Stage 2.5 is completed and merged.

Useful lessons from PR #33 may be reused selectively, but its architecture is not inherited by default.

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

Candidate r3 passed Blender 5.2 LTS runtime testing and remains the accepted Stage-2 result until Stage 2.5 itself is runtime-tested and accepted.

---

## 5. Preserved local artifacts

The user still retains the actual Stage-2 runtime ZIPs locally:

- Stage-2 Candidate r1 ZIP
- Stage-2 Candidate r2 ZIP
- Stage-2 Candidate r3 ZIP

This is important.

Stage 2.5 must **not recreate Candidate-r1 geometry from memory or visual approximation**.

The Candidate-r1 ZIP should be treated as an empirical source artifact. The exact Python source contained in that ZIP must be compared with:

- Candidate r2 ZIP;
- Candidate r3 ZIP;
- Git history;
- current accepted `main`.

The goal is to identify the exact code changes that altered Winder visible geometry from r1 -> r2 -> r3.

Do not guess.

---

## 6. Stage-2 r1 geometry characteristics to recover

The user specifically values the simpler Candidate-r1 Winder geometry because its Turn-side / inner boundary relationship was visually simple and aligned, making Stage-3 body construction easier.

Known Candidate-r1 visual characteristic to preserve/recover:

- the Winder / adjacent Straight inner-side boundary presents as a clean aligned line through the Turn;
- the geometry is simpler than the later `K_finish`-driven physical trim structure;
- this simpler boundary is considered advantageous for adding underbody and Side Board geometry in Stage 3.

Known Candidate-r1 visible defect that is explicitly accepted for now:

- a visible TREAD/RISER gap / terminal gap may exist at the Turn transition.

That gap is **not a Stage-2.5 blocker** if the recovered geometry otherwise matches Candidate r1.

The gap may be addressed later, preferably after the new Stage-3 r1 ZIP exists.

---

## 7. What Stage 2.5 must preserve

Stage 2.5 must preserve all later functionality that is not inherently tied to the r2/r3 Winder physical-geometry refinements.

Preserve, unless exact r1-source comparison proves a direct dependency requiring a narrow adjustment:

- Build 07-D accepted Multi-point Path / L / U / Landing behavior;
- Build 07-D accepted Landing underside and Residential geometry;
- schema-4 persistence and lifecycle behavior;
- Build 07-E schema-5 Turn foundation;
- per-Turn TurnSpec state;
- FORWARD / REVERSE;
- arbitrary-angle Turn support;
- BF-1 / BF-2;
- U / Compact-U state and allocation foundations;
- AUTO / MANUAL allocation behavior;
- UI / serialization / persistence added during Stage 2;
- SQUARE / BEVEL / ROUND feature support as far as compatible with the selected simplified Winder geometry baseline;
- deterministic regeneration;
- accepted 07-D regression behavior.

Stage 2.5 must not rewrite accepted 07-D geometry merely to simplify Stage 3.

---

## 8. What Stage 2.5 is allowed to simplify

The intended simplification target is the later Stage-2 Winder **visible TREAD/RISER physical geometry path**, especially changes introduced after Candidate r1 that created a more complex Turn-local physical seam authority.

Potential simplification targets include later physical-trim concepts such as:

- `K_finish` common inner finish chord;
- r2/r3-specific physical Winder trim behavior;
- exact shared rear-support / Riser-back authority where it is the source of Stage-3 seam complexity;
- precision geometry added specifically to remove Candidate-r1 visual defects.

However, Stage 2.5 must first prove from the preserved r1/r2/r3 ZIP source and Git history exactly which code changed. Do not remove concepts merely because they are named here.

---

## 9. Mandatory implementation method

Stage 2.5 implementation must proceed in two phases.

### Phase A — audit only

Before modifying production geometry:

1. inspect the actual Stage-2 Candidate-r1 ZIP source;
2. inspect Candidate-r2 ZIP source;
3. inspect Candidate-r3 ZIP source;
4. identify the exact corresponding Git revisions where possible;
5. diff the Winder production path across r1 -> r2 -> r3;
6. list the exact functions / formulas / call paths that changed Winder visible geometry;
7. distinguish geometry-only changes from UI/schema/persistence changes.

No production modification should occur until this audit is complete.

### Phase B — narrow restoration

After the audit:

- keep current accepted Stage-2 r3 codebase as the structural base;
- restore only the r1-equivalent Winder geometry portions needed to recover the simpler visible boundary;
- when possible, copy the exact Candidate-r1 function bodies / formulas / call behavior rather than reimplementing an approximation;
- do not replace entire modern files with Candidate-r1 files;
- do not lose later Stage-2 features unrelated to the Winder geometry simplification.

---

## 10. Geometry identity target

Where practical, Stage 2.5 should compare the restored Winder geometry against the actual Candidate-r1 source output numerically.

Useful comparison data includes:

- Winder TREAD vertex coordinates;
- Winder RISER vertex coordinates;
- polygon vertex order;
- Z elevations;
- ordinal / event ordering;
- FORWARD / REVERSE behavior;
- exact-90 EQUAL_3 reference fixture.

The preferred result is not merely "looks similar" but:

> **Stage-2.5 Winder visible geometry matches Candidate r1 for the chosen reference fixtures, within the project's named numerical tolerance.**

Runtime Blender visual confirmation remains mandatory after the static comparison.

---

## 11. Stage-2.5 runtime acceptance focus

Stage 2.5 should be intentionally small.

Minimum runtime checks should include:

1. exact-90 EQUAL_3 Winder visual comparison with retained Candidate-r1 behavior;
2. arbitrary-angle Winder smoke check (for example 63 degrees) to ensure later Stage-2 capability is not accidentally lost;
3. FORWARD;
4. REVERSE;
5. Build 07-D exact-90 Landing visual regression check;
6. Save -> reopen persistence smoke check.

The primary Stage-2.5 visual acceptance criterion is:

- simple, predictable Winder boundary suitable for Stage-3 underbody / Side Board construction;
- no regression of accepted 07-D Landing / Straight geometry;
- Candidate-r1 terminal gap is allowed and documented.

---

## 12. New Stage-3 philosophy after Stage 2.5

After Stage 2.5 is accepted and merged, Build 07-E Stage 3 will restart from a new branch.

The old PR #33 architecture is not the default starting point.

The new Stage-3 implementation must follow the user's actual Blender workflow requirements:

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

### Not required for Stage-3 r1

- exact positive-volume intersection elimination;
- convex decomposition audits;
- exact internal Boolean ownership;
- complete PHYSICAL_CONTACT classification;
- exact internal cavity ownership;
- exact BodyInterface union proof.

The practical goal is a useful Blender modeling aid, not a CAD/BIM watertight solid kernel.

---

## 13. Documentation / workflow rule

This Stage-2.5 plan exists specifically so future ChatGPT/Codex sessions can recover the correct project context without relying on chat history.

Before any future Stage-2.5 or restarted Stage-3 task, read this file together with:

- `ROADMAP.md`;
- `BUILD_07_E_SPECIFICATION.md`;
- `BUILD_07_E_STAGE2_ACCEPTANCE_RECORD.md` (if named differently, use the actual Stage-2 acceptance record in the repository);
- `BUILD_07_D_ACCEPTANCE_RECORD.md`;
- `DEVELOPMENT_WORKFLOW.md`.

If an old PR #33 document or comment conflicts with this Stage-2.5 plan regarding the new Stage-3 implementation strategy, this Stage-2.5 plan represents the later project decision.

---

## 14. Current decision summary

```text
Build 07-E Stage 2 r3 accepted
        ↓
PR #33 first Stage-3 attempt abandoned / never merge
        ↓
Stage 2.5 dedicated branch
        ↓
Audit retained r1/r2/r3 ZIP source
        ↓
Restore r1-equivalent Winder geometry narrowly
        ↓
Runtime test Stage 2.5
        ↓
Stage 2.5 accepted + merge to main
        ↓
Create fresh Stage-3 branch
        ↓
Implement visual-first underbody / Side Board with hidden overlap allowed
```

Do not skip the Stage-2.5 runtime check and do not restart Stage 3 from PR #33.
