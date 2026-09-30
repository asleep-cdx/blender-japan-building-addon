# BUILD 07-E — FINAL REVIEW CLARIFICATIONS
## Conditions for merging Revision 1 + Revision 2 into the implementation-authority Specification

> **Status: FINAL-MERGE INPUT / NOT SEPARATE IMPLEMENTATION AUTHORITY**  
> Date: 2026-09-30  
> Based on the third-party verdict `ACCEPT WITH CLARIFICATIONS` against main commit `64d061fb42fb2abcf53cf4554cae4f5f6f29ee57`.
>
> This file records the exact clarifications required before `BUILD_07_E_SPECIFICATION.md` is promoted to `FINAL / IMPLEMENTATION AUTHORITY`. After integration, the Specification itself is the single implementation authority; Codex must not need this file to invent missing geometry.

---

# 1. Disposition of third review

The project accepts the third-party verdict:

```text
ACCEPT WITH CLARIFICATIONS
```

No 07-E user-facing scope is removed. Revision 2 geometry is accepted as the basis for FINAL integration.

The following Revision-2 areas are accepted without redesign:

- complete outer-chain preservation, including `Q1 -> O -> Q2` for the 90-degree EQUAL_3 center cell;
- finite pivot-relief core replacing the singular full-width pivot-spine production surface;
- Compact-U shared SLOPED height by Winder-event-count interpolation;
- Winder-only exact STEPPED_CLOSED patch Z rule;
- seam-local shared-center Side Board union / symmetric extrusion / 3D trim foundation;
- full-finish narrow-width regression fixtures;
- schema-4 -> schema-5 migration and RiseEvent rules already accepted from Revision 1.

The clarifications below are mandatory merge conditions.

---

# 2. Outer-angle normalization and deduplication

Revision 2 §3 remains normative with these additions.

For any angular fraction calculation, entry ray, signed Turn sweep and candidate ray must use one consistent signed-angle normalization convention. Do not mix unsigned `[0,pi]` angles with signed `theta` during the same fraction calculation.

For outer corner `O`:

```text
f_O = signed_angle(r0, normalize(O-I)) / theta
```

is evaluated on the same signed sweep as the Winder divider fractions.

If a divider ray passes through `O` within named numerical tolerance:

```text
Q_k ~= O
```

then `Q_k` and `O` are one geometry station. Do not insert a duplicate zero-length outer-chain edge and do not add an extra interpolation event.

Geometry-only outer stations never add Winder steps or RiseEvents.

---

# 3. Pivot-relief clarification and shared-edge subdivision

## 3.1 Riser-thickness dependency

Revision 2 finite pivot-relief construction remains:

```text
rho = max(riser_thickness, 10 * eps_length)
```

This means changing physical `riser_thickness` may change the local schema-5 Winder SLOPED_CLOSED pivot-relief geometry. That dependency is intentional and local to derived underbody closure geometry.

It must not change:

- canonical Path;
- stair width;
- nominal Winder tread polygons;
- Winder pattern / count;
- legal/advisory interpretation;
- schema-1/2/3 Straight geometry;
- schema-4 accepted Landing geometry.

## 3.2 HIGH_SIDE_PIVOT_CLOSURE

For Revision 2 §4.2:

```text
A_low  = (I.x, I.y,z_low)
A_high = (I.x, I.y,z_high)
J_high = high-side relief endpoint at z_high
```

`HIGH_SIDE_PIVOT_CLOSURE` is an **intentional local vertical/oblique closure face**, not an accidental triangulation artifact.

Its plan extent is limited by `rho`; its vertical extent is allowed to be `z_high - z_low`.

Stage-3 runtime review must inspect this local closure with Side Boards OFF from:

- below;
- inner/pivot side;
- ordinary residential viewing angles.

It must not create a visible giant filler wall, open cavity, spike or schema-4 regression.

## 3.3 No T-junctions on shared edges

The following is mandatory for all schema-5 Winder body/contact/Riser assembly:

> **If any incident face introduces a vertex in the interior of a shared edge, that vertex becomes a shared split point and must be inserted into every face using that edge before final assembly.**

This includes, but is not limited to:

- the `A_low -> A_high` pivot-core edge;
- relief-chord edges;
- divider closure edges;
- outer-chain edges;
- entry/exit component-interface edges;
- trim-generated board/body edges.

Rules:

1. Collect ordered split parameters along the semantic shared edge.
2. Deduplicate only by full 3D coordinate within named epsilon.
3. Split every incident polygon/triangle at the same ordered points.
4. Re-triangulate deterministically.
5. Do not leave a vertex from one face terminating in the middle of an unsplit edge of another face.

This rule supplements Revision 2 §§4.3–4.5 and is required for manifold/topology checks.

---

# 4. Compact-U Reverse / indexing convention

Revision 2 §6 is retained, with one indexing authority.

All Compact-U SLOPED height interpolation is resolved in **current uphill/ascent traversal order**, not raw canonical Path order.

Define:

```text
Turn A = first Winder Turn encountered while ascending
Turn B = second consecutive Winder Turn encountered while ascending
n1     = step_count of Turn A
n2     = step_count of Turn B
A      = visible-soffit Z at ascent entry to Turn A
B      = visible-soffit Z at ascent exit from Turn B
```

Then:

```text
M = A + n1/(n1+n2) * (B-A)
```

and the grouped station sequence is evaluated in that same ascent order.

On `REVERSE`:

- canonical Path point order and physical Winder pattern assignment remain unchanged;
- traversal Turn order is recomputed;
- `n1/n2`, `A/B` and station event indices are reassigned from the new uphill order;
- elevations are regenerated from the same RiseEvent authority;
- BF pattern identity is not renamed merely because ascent order reversed.

Do not mix canonical-order `n1/n2` with ascent-order endpoint heights.

---

# 5. STEPPED_CLOSED formula scope

Revision 2 §5 exact rule:

```text
Z_soffit_j = max(B, T_j - d)
```

is **schema-5 Winder STEPPED_CLOSED geometry only**.

It inherits the semantic meaning that `closed_body_depth` locates the visible body/soffit, but it does not replace the accepted 07-C Straight implementation such as `stepped_closure_visible_profile()`.

Therefore:

- schema-1/2/3 Straight geometry remains unchanged;
- schema-4 accepted Landing/Flight geometry remains unchanged;
- only schema-5 Winder stepped patches use the cell-level formula above;
- `underside_thickness` remains an inward shell/validation value and does not relocate the visible patch Z.

---

# 6. Side Board upper/lower authorities

Preserve accepted 07-C independence:

```text
underside_mode  -> lower board boundary
side_board_mode -> upper/visible board boundary
```

Do not infer the upper Side Board shape from the Winder soffit interpolation merely because both are sloped variants.

## 6.1 Lower boundary

The lower boundary is exactly the resolved exterior underbody boundary:

- `STEPPED_CLOSED` -> resolved stepped Winder/Flight lower boundary;
- `SLOPED_CLOSED` -> resolved sloped Winder/Flight/pivot-relief lower boundary.

Shared geometry stations and split points are reused.

## 6.2 STEPPED upper boundary on Winder

For each Winder cell `C_j` with destination tread top `T_j`:

- the horizontal upper-board segment over that cell uses the accepted Side Board reveal relationship to the destination walking surface;
- the upper stepped level is based on `T_j + reveal` where the accepted local terminal rule does not override it;
- a RiseEvent/divider transition inserts the corresponding vertical upper-profile transition;
- an inserted geometry-only outer corner `O` inside the same cell keeps that cell's same stepped upper level and adds no RiseEvent;
- entry/exit terminal/cap behavior reuses the accepted 07-C terminal semantics transformed into the local component boundary.

Thus outer-chain corners alter plan segmentation, not step count or stepped upper Z.

## 6.3 SLOPED upper boundary on Winder

For `side_board_mode = SLOPED`, derive the upper/visible board line from the **walking-surface / Side-Board upper reference**, not from underbody station Z.

Primary upper stations are the ordered Winder boundary stations associated with the RiseEvent walking sequence and accepted reveal/terminal semantics.

Between consecutive primary upper stations:

- interpolate the visible upper edge linearly in the same local progression order;
- if geometry-only outer corner `O` lies inside the interval, insert it and interpolate its upper Z using its local fraction within that interval;
- do not create an extra RiseEvent or tread at `O`;
- preserve accepted lower/upper end closures and short terminal caps where applicable.

This produces the Winder analogue of the accepted 07-C sloped visible upper finish without reusing the underbody height formula as an unrelated authority.

---

# 7. Compact-U shared-center Side Board final connection rules

Revision 2 §7 remains the base contract with the following exact additions.

## 7.1 Point-only contact does not merge components

For seam-local profile regions `R_i`:

- positive-area overlap -> union;
- shared edge segment that forms one regular polygonal region -> union;
- **point-only contact -> keep as separate closed components and do not weld the point**;
- separated Z ranges -> keep as separate closed components.

A single `SHARED_CENTER_BOARD` family may therefore contain multiple closed components.

Do not create nonmanifold point-welded board solids merely to reduce object/fragment count.

## 7.2 Ordinary-board / shared-board connection = butt-joint authority

07-E uses a deterministic **butt-joint** at each endpoint of the Compact-U shared-center interval. No implicit miter or tapered transition is invented.

Define the connection plane:

- passes through the shared seam endpoint;
- vertical in world Z;
- normal to the local shared-seam tangent in plan.

Both the ordinary board and shared board are clipped to this same plane.

At the connection plane:

1. insert the union of all profile breakpoints from both participating board cross-sections into both sides;
2. the overlapping cross-section area is treated as the internal board-to-board connection and is not duplicated as two exterior faces;
3. cross-section area belonging only to one side is closed by an endpoint cap owned by that side;
4. any thickness step between an ordinary one-sided board and the symmetric shared board is an intentional local shape;
5. no miter, bevel or automatic transition length is implied;
6. final geometry must contain no open cavity, positive-volume overlap or z-fighting duplicate face.

Example only:

```text
ordinary board may occupy v=[-s,0]
shared board occupies       v=[-s/2,+s/2]
```

The mismatch is resolved at the common butt-joint plane by the rules above, not by silently shifting canonical stair width or seam position.

## 7.3 3D trim authority

`V_shared` trims only actual positive-volume intersections with:

```text
TREAD
RISER
UNDERBODY
```

Every cut surface is capped with the trimmed part's original material role.

Do not delete an entire plan strip through all Z when the board occupies only a local Z range.

All trim-generated shared-edge split points participate in the no-T-junction rule from Section 3.3 of this clarification.

---

# 8. Old-house success guard remains mandatory

Revision 2 full-finish width fixtures remain mandatory for:

```text
900 / 800 / 750 / 700 / 650 mm
```

At every listed width, both expected-success configurations must reach final physical geometry:

```text
A: STEPPED_CLOSED + STEPPED board + BOTH ON + positive nosing
B: SLOPED_CLOSED  + SLOPED  board + BOTH ON + positive nosing
```

`650mm` is a regression sample, not a lower production bound.

If an expected-success fixture fails during implementation, do **not** delete or weaken the fixture merely to obtain green tests. Determine whether:

- the implementation violates the specification; or
- the reviewed geometry contract itself needs a documented correction.

A new legal-like width gate is never the fix.

---

# 9. FINAL merge requirements

Before FINAL promotion:

1. Merge all accepted Revision-1 rules into `BUILD_07_E_SPECIFICATION.md`.
2. Merge all accepted Revision-2 rules, superseding the clauses Revision 2 explicitly replaced.
3. Merge Sections 2–8 of this clarification into the relevant normative Specification sections.
4. Remove or explicitly replace obsolete contradictory wording, including separate persistent `turn_id` authority and independent persistent `step_count/rule` authorities.
5. Preserve schema-4 exact-90 Landing compatibility and accepted 07-C/07-D production behavior.
6. Correct ROADMAP §12.12 so generic single-180-degree mathematical examples are not read as 07-E production U acceptance requirements.
7. Change the Specification status to `FINAL / IMPLEMENTATION AUTHORITY` only after the merged text is self-contained.

No additional external/reference image becomes implementation authority.

---

# 10. Review history record

Third-party decisions received during 07-E specification design:

```text
Review 1: REVISE GEOMETRY CONTRACT
Review 2: REVISE GEOMETRY CONTRACT AGAIN
Review 3: ACCEPT WITH CLARIFICATIONS
```

The purpose of retaining the review documents is design auditability. Once the final Specification is merged, Codex implementation authority is the final `BUILD_07_E_SPECIFICATION.md`, not the historical Revision/Review files.