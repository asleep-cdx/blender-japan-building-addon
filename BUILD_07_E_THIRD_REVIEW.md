# BUILD 07-E — THIRD THIRD-PARTY REVIEW BRIEF
## Review after Geometry Contract Revision 2

> **Status: THIRD REVIEW REQUEST**  
> Date: 2026-09-30  
> Do not implement production code or edit repository files as part of this review.

---

# 1. Background

The first review returned:

```text
REVISE GEOMETRY CONTRACT
```

The second review returned:

```text
REVISE GEOMETRY CONTRACT AGAIN
```

The project accepted both verdicts without reducing intended 07-E user scope.

Revision 1 fixed RiseEvent allocation, canonical ownership, migration, nominal-vs-physical part separation and initial underbody/Compact-U contracts.

Revision 2 was added after the second review to address the remaining geometry issues, especially:

- EQUAL_3 outer-corner omission;
- singular pivot-spine surface ambiguity;
- Compact-U shared Z authority;
- STEPPED_CLOSED exact Z coordinates;
- Side Board mode independence and shared-center solid/trim rules;
- full-finish old-house width regression fixtures.

Current revision file:

```text
BUILD_07_E_REVIEW_REVISION_2.md
```

The goal is still **not** to implement code. Determine whether the combined Specification + Revision 1 + Revision 2 is now sufficiently complete to merge into `BUILD_07_E_SPECIFICATION.md` and promote that merged document to `FINAL / IMPLEMENTATION AUTHORITY`.

---

# 2. Documents to read

Read at least:

```text
BUILD_07_E_THIRD_PARTY_REVIEW.md
BUILD_07_E_SECOND_REVIEW.md
BUILD_07_E_SPECIFICATION.md
BUILD_07_E_DESIGN_RATIONALE.md
BUILD_07_E_REVIEW_REVISION_1.md
BUILD_07_E_REVIEW_REVISION_2.md
BUILD_07_D_SPECIFICATION.md
BUILD_07_D_ACCEPTANCE_RECORD.md
BUILD_07_C_SPECIFICATION.md
ROADMAP.md
DEVELOPMENT_WORKFLOW.md
```

Inspect accepted Stair code if needed, especially:

```text
japanese_house_modeler/stair_multiflight.py
japanese_house_modeler/stair_residential.py
japanese_house_modeler/stair_residential_geometry.py
japanese_house_modeler/stair_state.py
```

Do not modify code or docs.

---

# 3. Previously accepted Revision-1 areas

Unless Revision 2 accidentally conflicts with them, re-open these only if you find a new inconsistency:

- deterministic straight-region AUTO allocation;
- `S + L + W + 1 = N` RiseEvent accounting;
- destination-surface Riser ownership;
- `path_point_id` as Turn identity;
- `winder_pattern` as canonical pattern authority;
- schema-4 -> schema-5 migration matrix;
- BF/Reverse/left-right semantics;
- 3-point L / 4-point U production scope;
- legal-like minimum prohibition.

---

# 4. Highest-priority third-review questions

## A. Outer-chain completeness

Check Revision 2 §3.

For 90° EQUAL_3, confirm that the central cell now explicitly preserves:

```text
Q_1 -> O -> Q_2
```

and that `O` receives a geometry-only interpolated Z without adding a RiseEvent.

Questions:

- Is `f_O` well defined for both left/right signed sweeps?
- Does the ordered-outer-vertex rule also work for BF_1/BF_2 and arbitrary-angle EQUAL patterns?
- Does the main strip union cover the nominal cell minus only the explicitly defined pivot-relief core?

## B. Finite pivot-relief core

Check Revision 2 §§2–4.

Revision 2 deliberately replaces the singular full-width pivot-spine production surface with:

```text
rho = max(riser_thickness, 10*eps_length)
J_0 / J_n
inner relief chord
P(f) intersections
main turning-soffit strips
finite K_core triangle
localized HIGH_SIDE_PIVOT_CLOSURE
```

Questions:

- Is using riser thickness as the local relief distance geometrically coherent and backward-compatible with the role of that physical thickness?
- Does the chord intersect every intermediate supported ray for `0 < abs(theta) < 180°` outside the existing singularity exclusions?
- Does the finite core eliminate the ambiguous coincident-XY large vertical triangle from Revision 1?
- Is the localized high-side closure sufficiently specified for C0 closure and manifold assembly?
- Are the contact/body segmentation and destination-owned divider rules sufficient to close the body without exposing cavity?
- Does this derived relief remain clearly separate from stair width / legal minima?

If this approach is not robust, propose a concrete deterministic alternative that still avoids a singular full-width pivot surface and does not remove narrow-old-house support.

## C. STEPPED_CLOSED exact Z

Check Revision 2 §5.

Current rule:

```text
Z_soffit_j = max(B, T_j - d)
```

Questions:

- Is this consistent with accepted 07-C `closed_body_depth` semantics?
- Is the tread-bottom clearance rule sufficient?
- Are internal divider, entry and exit closure owners now unambiguous?
- Does the floor clamp avoid degenerate faces correctly?

## D. Compact-U shared SLOPED Z

Check Revision 2 §6.

Current authority:

```text
M = A + n1/(n1+n2) * (B-A)
```

and equivalent cumulative event-index station formula.

Questions:

- Does this correctly resolve EQUAL_3+EQUAL_3, EQUAL_2+EQUAL_3 and BF+EQUAL combinations?
- Is it correct that this groups derived soffit-height interpolation only while preserving two Turn identities and zero middle Straight events?
- Does any accepted Reverse behavior require an additional explicit rule?

## E. Shared-center Side Board

Check Revision 2 §7.

Confirm first that accepted 07-C mode independence has been restored:

```text
underside_mode  -> lower board edge
side_board_mode -> upper board edge
```

Then review:

```text
R_i in seam-local (s,z)
R_shared = union(enabled R_i)
component-preserving union
symmetric thickness extrusion
actual 3D trim against TREAD/RISER/UNDERBODY
capped trim faces
ordinary/shared endpoint ownership
```

Questions:

- Is this sufficiently deterministic for both Side Boards ON and one-side-OFF cases?
- Is keeping separated Z components separate correct?
- Does 3D-volume-based trim avoid the previous over-trim problem?
- Is including RISER enough to close the omission identified in second review?
- Is any exact transition formula still missing before implementation?

## F. Old-house protection

Check Revision 2 §8.1.

For every width:

```text
900 / 800 / 750 / 700 / 650 mm
```

both are now mandatory final-geometry success fixtures:

```text
STEPPED_CLOSED + STEPPED board
SLOPED_CLOSED  + SLOPED board
```

with BOTH boards ON and positive nosing.

Confirm this prevents an implementation from passing nominal Winder geometry but rejecting all narrow finished Stairs.

Also confirm `650mm` remains a regression sample rather than a production lower bound.

---

# 5. Fixture corrections to verify

Revision 2 corrected:

- old-house L fixture to an actual 90° left Turn;
- Compact U `base_z`, underside and board modes;
- 63° Landing to an exact coordinate/length formula;
- EQUAL_3 outer-corner fixture to require `Q_1 -> O -> Q_2` plan coverage.

Verify these are fixed, not merely descriptive.

---

# 6. Compatibility / accepted behavior

Verify Revision 2 does not silently break:

- schema-1/2/3 Straight;
- schema-4 exact-90° Landing;
- accepted 07-C body-depth / underside-thickness distinction;
- accepted 07-C Side Board upper/lower mode independence;
- accepted 07-C nosing/edge semantics on Straight regions;
- accepted 07-D r19 Landing perimeter / Side Board corrections;
- accepted 07-D Stage-4 lifecycle and regression behavior.

The proposed pivot-relief core applies only to schema-5 Winder SLOPED_CLOSED derived geometry. It must not alter existing schema-4 Landing geometry.

---

# 7. ROADMAP inconsistency

Revision 2 identifies that ROADMAP §12.12 still contains generic single-180° equal-angle examples such as `180° / 2段`.

07-E production U is two persistent Turns with per-Turn patterns.

Confirm that ROADMAP should be corrected before FINAL so those generic examples are not read as a 07-E acceptance promise for a 2-step total U.

---

# 8. Expected output

Please provide:

1. Overall verdict, preferably one of:

```text
ACCEPT REVISION 2 FOR FINAL MERGE
ACCEPT WITH CLARIFICATIONS
REVISE GEOMETRY CONTRACT AGAIN
REVISE STAGE SCOPE
```

2. Any blocking geometry issue with exact Revision-2 section reference.
3. Any contradiction with accepted 07-C / 07-D behavior.
4. Any remaining implementation ambiguity that would force Codex to invent geometry.
5. Any hidden narrow-house/legal-like rejection path.
6. Whether the combined repository text is now sufficient for implementation without reference images.
7. If acceptable, state whether Revision 1 + Revision 2 may be merged into `BUILD_07_E_SPECIFICATION.md` and promoted to FINAL after the ROADMAP clarification.

Do not implement code or change repository files.
