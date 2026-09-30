# BUILD 07-E — SECOND THIRD-PARTY REVIEW BRIEF
## Review after Geometry Contract Revision 1

> **Status: SECOND REVIEW REQUEST**  
> Date: 2026-09-30  
> Do not implement production code or edit repository files as part of this review.

---

## 1. Background

The first third-party review of Build 07-E, against main commit:

```text
f1ef564543549f3f5ef7d4d746e41320c0f9a734
```

returned:

```text
REVISE GEOMETRY CONTRACT
```

The project accepted that verdict and added:

```text
BUILD_07_E_REVIEW_REVISION_1.md
```

The revision responds to the first review's five mandatory findings without removing the intended 07-E scope.

The current goal is **not yet to declare FINAL**. The goal of this second review is to determine whether the revised contract is sufficiently complete to be merged into `BUILD_07_E_SPECIFICATION.md` and then promoted to `FINAL / IMPLEMENTATION AUTHORITY`.

---

## 2. Documents to read

Read at least:

```text
BUILD_07_E_THIRD_PARTY_REVIEW.md
BUILD_07_E_SPECIFICATION.md
BUILD_07_E_DESIGN_RATIONALE.md
BUILD_07_E_REVIEW_REVISION_1.md
BUILD_07_D_SPECIFICATION.md
BUILD_07_D_ACCEPTANCE_RECORD.md
BUILD_07_C_SPECIFICATION.md
ROADMAP.md
DEVELOPMENT_WORKFLOW.md
```

If checking implementation compatibility is useful, inspect the current accepted Stair code, especially:

```text
japanese_house_modeler/stair_multiflight.py
japanese_house_modeler/stair_residential.py
japanese_house_modeler/stair_residential_geometry.py
japanese_house_modeler/stair_state.py
```

Do not modify them.

---

## 3. First-review findings that must now be re-evaluated

### A. RiseEvent / straight allocation

Check Revision 1 Sections 3 and 8.

Confirm whether the following is now complete and deterministic:

```text
S + L + W + 1 = N
positive straight run -> s_i >= 1
Compact-U zero run    -> s_i = 0
AUTO initial one tread per positive region
residual -> largest current R_i/s_i
canonical physical segment order breaks ties
```

Also check the exact destination-surface riser ownership at Straight/Landing/Winder boundaries and Compact-U shared transitions.

### B. Nominal Winder cells versus physical parts

Check Revision 1 Section 4.

Confirm whether it sufficiently distinguishes:

```text
nominal plan cells
physical TREAD/nosing/rear extension
physical RISER
3D collision/topology validation
```

Pay particular attention to the zero-width mathematical inner pivot and whether positive nosing on a valid narrow Winder can be trimmed rather than falsely rejected.

### C. STEPPED_CLOSED / SLOPED_CLOSED

Check Revision 1 Sections 5–6.

For SLOPED_CLOSED, specifically review:

```text
entry/exit section authority
n+1 lower-surface stations
z_k interpolation by RiseEvent index
pivot spine I_k=(I.x,I.y,z_k)
outer station Q_k
canonical quad/triangulation
pivot manifold ownership
contact-clearance validation
underside-thickness direction
```

Determine whether this is now sufficiently explicit for implementation without an image or further geometry-design decisions.

For STEPPED_CLOSED, determine whether the horizontal-patch / destination-owned divider closure rule is sufficiently complete or still requires an exact additional formula.

### D. Compact U / Side Board

Check Revision 1 Section 7 and fixed fixture 11.2.

Review whether the proposed continuous-side-path / `SHARED_CENTER_BOARD` approach is implementable:

- one center path, not two colliding board solids;
- centered thickness on a coincident seam;
- `s/2` trim of adjacent physical finish solids;
- canonical Path and stair width unchanged;
- both board toggles ON must pass the fixed Compact-U fixture;
- positive-volume self-intersection remains invalid.

If this rule is not robust, propose a concrete alternative with the same user-visible goal rather than merely recommending collision rejection.

### E. schema-4 -> schema-5 migration

Check Revision 1 Section 8.

Review:

```text
ordinary schema-4 operation -> stays schema 4
explicit generalized LANDING promotion -> s_i = r_i - 1
schema-4 MANUAL LANDING->WINDER -> require explicit AUTO first
schema-4 AUTO LANDING->WINDER -> schema-5 AUTO recomputation
arbitrary-angle move only after explicit schema-5 promotion
rollback restores schema/r_i/Turn/IDs/Mesh
```

Determine whether this fully preserves accepted 07-D semantics.

---

## 4. Additional clarification checks

Review whether Revision 1 satisfactorily resolves the first review's additional points:

- Turn identity uses existing interior `path_point_id`; no duplicate UUID is added.
- `winder_pattern` is canonical authority; count/rule are derived mapping.
- outer-corner duplicate intersection is deduplicated.
- BF near-90 uses actual signed theta within accepted right-angle tolerance; Path is not snapped.
- new schema-5 Winder default is `EQUAL_3`.
- LEFT/RIGHT Side Board meaning remains uphill-relative under Reverse.
- 07-E acceptance-required topology is 3-point L / 4-point U; >2-Turn Winder Custom is not mandatory.
- Roadmap 180°/n notation is mathematical reference, not single-Turn 07-E production scope.
- Stage order now places RiseEvent/schema foundations early and accepts underbody before Side Boards.

---

## 5. Old-house renovation requirement

This remains a hard requirement.

The second review should confirm that no new revision accidentally creates a code-like minimum width.

Fixed expected-success width matrix:

```text
900 / 800 / 750 / 700 / 650 mm
```

`650mm` is a regression sample, not a minimum.

The reviewer should especially check that:

- no Straight `going` validator is misapplied to Winder inner-pivot width;
- body/nosing/board failure is reported as actual geometry/finish failure, not legal-width failure;
- UI/RNA clamps do not undermine the geometry contract.

---

## 6. Expected second-review output

Return one of:

```text
READY TO MERGE INTO FINAL SPEC
READY WITH MINOR CLARIFICATIONS
REVISE GEOMETRY CONTRACT AGAIN
REVISE STAGE SCOPE
```

Then provide:

1. any remaining **blocking** ambiguity;
2. exact section references;
3. any mathematical or manifold concern with the pivot-spine or shared-center-board rules;
4. any compatibility/migration concern;
5. any hidden old-house/legal-gate concern;
6. whether repository text alone is now sufficient for implementation;
7. whether the revised rules can be merged into the main Specification without changing intended 07-E user-facing scope.

If recommending another geometry revision, provide a concrete replacement rule where possible rather than only identifying the symptom.
