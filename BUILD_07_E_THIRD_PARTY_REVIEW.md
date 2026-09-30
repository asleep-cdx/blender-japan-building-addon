# BUILD 07-E — THIRD-PARTY REVIEW BRIEF
## Japanese House Modeler / 日本住宅モデラー

> **Status: REVIEW REQUEST**  
> Date: 2026-09-30  
> This file is not implementation authority. It tells a third-party reviewer what to inspect before `BUILD_07_E_SPECIFICATION.md` is promoted to `FINAL / IMPLEMENTATION AUTHORITY`.

---

## 1. Review goal

Review Build 07-E as an architecture / geometry / compatibility proposal before Codex implementation begins.

The reviewer should answer one of the following at the end:

```text
ACCEPT AS WRITTEN
ACCEPT WITH CLARIFICATIONS
REVISE GEOMETRY CONTRACT
REVISE STAGE SCOPE
```

For every requested change, identify the exact Specification section / invariant that should change and explain why.

Do **not** implement production code as part of this review.

---

## 2. Repository documents to read

Read at least:

```text
ROADMAP.md
DEVELOPMENT_WORKFLOW.md
BUILD_07_D_SPECIFICATION.md
BUILD_07_D_ACCEPTANCE_RECORD.md
BUILD_07_E_SPECIFICATION.md
BUILD_07_E_DESIGN_RATIONALE.md
```

Authority hierarchy for this review:

1. Accepted 07-D Specification / Acceptance Record define behavior that 07-E must preserve.
2. `BUILD_07_E_SPECIFICATION.md` is the current review candidate.
3. `BUILD_07_E_DESIGN_RATIONALE.md` explains why 07-E requirements exist and provides review context.
4. `ROADMAP.md` defines project sequencing and broader scope.

The 07-E Specification is **not yet FINAL**. The purpose of this review is to decide whether it is ready to become implementation authority.

---

## 3. Project-use context that must influence the review

JHM is a Blender modeling aid for Japanese residential renovation visualization. It is not a building-code compliance engine.

A key use case is an old house where the existing stair remains structurally unchanged while walls, floors or finishes are renovated. The stair may be narrower or tighter than a current new-build recommendation, but still has to appear accurately in the renovation perspective.

Therefore the reviewer should treat this as a hard project requirement:

> **A geometry-valid existing stair must not be rejected merely because its width or Winder dimensions are below a present-day legal / recommended value.**

The review should actively look for hidden legal-like gates in:

- geometry validators;
- canonical validation;
- RNA property min/max ranges;
- UI clamping;
- presets;
- error handling;
- automated-test assumptions.

Representative geometry-valid widths include:

```text
900 mm
800 mm
750 mm
700 mm
650 mm
```

Reference dimensions such as 300 / 150 / 85 mm must not become universal production minima unless a future separate legal-advisory feature explicitly introduces them outside the core geometry gate.

---

## 4. Reference-image restriction

Design reference images were used to discuss residential patterns, but they are not repository authority.

The reviewer should verify:

> **A competent implementer can build 07-E from repository text alone without seeing any chat image.**

In particular, verify that the text is sufficient for:

- EQUAL_2 / EQUAL_3 / EQUAL_4;
- BF_1 / BF_2;
- left/right mirror behavior;
- Reverse behavior;
- U combinations;
- Compact U;
- arbitrary-angle Landing;
- arbitrary-angle equal-angle Winder.

---

## 5. Highest-priority review questions

### 5.1 Generalized Turn geometry

Check the vector/intersection construction in `BUILD_07_E_SPECIFICATION.md` Section 10.

Questions:

- Are inside/outside normals correct for both signed turn directions?
- Is the envelope `I -> E_in -> O -> E_out` always the intended simple polygon for supported non-singular angles?
- Does exact 90° / equal width reduce to the accepted 07-D `w × w` Landing?
- Is the derived cutback relationship consistent?
- Are near-0° / near-180° failures described as numerical/geometry singularities rather than arbitrary residential-angle restrictions?

### 5.2 Equal-angle and BF patterns

Check Sections 13–14.

Expected normalized rules:

```text
EQUAL_2 = [1/2]
EQUAL_3 = [1/3, 2/3]
EQUAL_4 = [1/4, 1/2, 3/4]

BF_1 = [2/3] -> 60°, 30° at 90°
BF_2 = [1/3] -> 30°, 60° at 90°
```

Questions:

- Is step count cleanly separated from partition rule?
- Is the outer-chain ray intersection unambiguous?
- Is BF left/right behavior correctly produced by signed theta?
- Is keeping BF identity unchanged under Reverse the correct canonical behavior?

### 5.3 Rise-event ownership

Check Sections 17–19 carefully.

Current proposed invariant:

```text
S + L + W + 1 = N
```

where:

```text
S = independent straight-tread rise events
L = LANDING_ARRIVAL rise events
W = Winder-tread rise events
1 = final UPPER_ARRIVAL rise event
N = overall riser count
```

Questions:

- Does this preserve the accepted Straight / L Landing / U Landing semantics from 07-D?
- Is every physical rise owned exactly once?
- Does mixed LANDING/WINDER topology remain unambiguous?
- Is the conservative schema-4 MANUAL -> WINDER conversion rule safer than automatic redistribution?

### 5.4 Compact U

Check Section 21.

Current classification:

```text
R_mid = L_mid - d1 - d2

R_mid > +eps  -> SEPARATED_U
abs(R_mid)<=eps -> COMPACT_U
R_mid < -eps  -> INVALID_OVERLAP
```

Questions:

- Is this sufficient to cover the intended compact residential U geometry?
- Does it correctly allow zero ordinary middle tread events?
- Does it preserve both accepted canonical Turn IDs / point IDs?
- Is any additional supported topology needed before implementation?

### 5.5 Arbitrary-angle Landing / Winder

Check Sections 22–23.

Questions:

- Is arbitrary-angle Landing correctly generalized from the same Turn envelope?
- Are angle-specific generators unnecessary?
- Is arbitrary-angle `EQUAL_ANGLE` Winder sufficiently defined?
- Are BF patterns appropriately limited to approximately/exactly 90° in 07-E?

### 5.6 Old-house guardrail

Check Section 15 and Acceptance Principle 9–10.

Questions:

- Could any stated geometry validation accidentally become a legal-like minimum?
- Are property/UI ranges included in the guardrail strongly enough?
- Are 700/650mm representative valid cases protected?
- Is it clear that actual self-intersection, zero-area, overlap, insufficient Path length etc. may still reject?

### 5.7 SLOPED_CLOSED / Side Board

Check Sections 27–28.

Questions:

- Is C0 continuity sufficient for the intended visual result?
- Does the contract clearly prohibit a Landing-like horizontal plateau through a Winder?
- Are underside and board geometry derived from the same resolved Turn / RiseEvent state?
- Is Stage 3 isolation sufficient to avoid repeating the 07-D underside/side-board debugging problem?

---

## 6. Compatibility review

Verify that 07-E does not silently change:

- schema-1 BASIC Straight;
- schema-2 07-B Residential Straight;
- schema-3 07-C Residential Straight;
- schema-4 07-D Straight / L / U / Landing;
- Path point IDs;
- Stair IDs;
- accepted Material semantics;
- accepted Reverse semantics;
- Repair / Finalize / Delete lifecycle;
- Wall / Finish isolation.

Existing schema-4 exact-90° Landing must remain Landing unless the user explicitly performs a 07-E operation.

---

## 7. Scope / complexity review

The reviewer should flag requirements that are mathematically sound but unnecessarily expensive for the project's actual purpose.

However, do not recommend dropping the following merely for simplification because they are explicit user/project goals:

- old-house narrow-stair support without legal-like rejection;
- 90° Winder 2/3/4;
- BF_1 / BF_2;
- U / Compact U;
- arbitrary-angle Landing;
- arbitrary-angle equal-angle Winder;
- continuous Winder SLOPED_CLOSED;
- Winder Side Board continuation;
- accepted 07-D compatibility.

Items intentionally outside 07-E include:

- changing the project default stair width from 900 to 750mm;
- general Stair-panel collapsible/compact UI redesign;
- Riser OFF / support/open variants;
- optional tread-detail expansion;
- Floor/Room dependency;
- Door/Window integration.

---

## 8. Stage-order review

Current proposed order:

```text
Stage 1
canonical Turn + 90° EQUAL L Winder
↓
Stage 2
BF + U / Compact U + arbitrary-angle Landing/Winder
↓
Stage 3
closed underside + Side Board
↓
Stage 4
lifecycle + regression + practical acceptance
```

The reviewer should assess whether this provides sufficiently isolated failure domains and whether any dependency should move earlier/later.

---

## 9. Expected review output

Please provide:

1. Overall verdict using one of the four labels in Section 1.
2. Critical issues that must be fixed before implementation.
3. Recommended clarifications that would reduce Codex ambiguity.
4. Any mathematical concern with exact section references.
5. Any backward-compatibility concern with exact section references.
6. Any hidden old-house/legal-gate concern.
7. Any Stage-order concern.
8. If acceptable, explicitly state whether the Specification can be implemented **without reference images**.

The review should optimize for a robust Blender 5.2 LTS production implementation, not for theoretical BIM completeness.
