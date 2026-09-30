# BUILD 07-E — REVIEW REVISION 2
## Geometry contract corrections after second third-party review

> **Status: REVIEW REVISION / THIRD-REVIEW CANDIDATE**  
> Date: 2026-09-30  
> Based on second third-party review of main commit `dc4ddbf8c6b9820d4a8cd9de9ddb3236b9c9375a`.  
> This file is **not production implementation authority**. It supersedes only the Revision-1 clauses explicitly identified below. Revision-1 clauses not superseded remain proposed contract. After third-review acceptance, Revision 1 + Revision 2 must be merged into `BUILD_07_E_SPECIFICATION.md` before FINAL promotion.

---

# 1. Disposition of second review

Second-review verdict received:

```text
REVISE GEOMETRY CONTRACT AGAIN
```

The project accepts that verdict. No user-facing 07-E capability is removed.

Revision 1 is retained for:

- canonical Turn identity = interior `path_point_id`;
- `winder_pattern` as the single canonical Winder pattern authority;
- schema-5 default `EQUAL_3`;
- RiseEvent accounting and deterministic straight-region AUTO allocation;
- destination-surface Riser ownership;
- nominal-cell / physical-part separation;
- schema-4 -> schema-5 migration matrix;
- BF / Reverse / left-right rules;
- L/U production scope and Stage order;
- old-house legal-gate prohibition.

Revision 2 replaces/refines the following Revision-1 clauses:

```text
Rev1 §5                -> Rev2 §5
Rev1 §6.2–§6.7        -> Rev2 §3–§4
Rev1 §7.3–§7.4        -> Rev2 §7
Rev1 §11 fixtures      -> Rev2 §8
Rev1 §4.5 wording      -> Rev2 §9
```

---

# 2. Key correction: no singular full-width pivot-spine strip

Revision 1 used coincident-XY pivot-spine vertices for the visible sloped soffit. The second review correctly noted that a coarse quad such as

```text
I_k -> Q_k -> Q_(k+1) -> I_(k+1)
```

both omits outer-corner vertices in some cells and forces a large vertical triangle when triangulated across a point pivot whose Z changes.

07-E therefore does **not** use a singular full-width pivot-spine quad as the production visible soffit.

Instead, SLOPED_CLOSED uses a small finite **pivot relief core** derived from existing physical geometry. This is not a legal/walking-width rule and does not change nominal tread cells.

Definitions:

```text
r      = riser_thickness in metres
eps_l  = named geometry length epsilon
rho    = max(r, 10 * eps_l)
```

`rho` is a local body-closure regularization distance only.

Required:

```text
0 < rho < min(distance(I,E_in), distance(I,E_out))
```

and every supported divider ray between entry and exit must intersect the inner relief chord defined below before reaching the outer chain.

Failure is `GEOMETRY_INVALID` for the selected physical thickness/Turn geometry. It is not a stair-width/legal minimum.

Nominal Winder TREAD cells still extend to the exact mathematical pivot `I`.

---

# 3. SLOPED_CLOSED — complete outer-chain and inner-relief construction

## 3.1 Angular station fractions

Let the Winder divider fractions in canonical entry-to-exit order be:

```text
F = [f_0, f_1, ... f_n]
f_0 = 0
f_n = 1
```

Examples:

```text
EQUAL_3 -> [0, 1/3, 2/3, 1]
BF_1    -> [0, 2/3, 1]
BF_2    -> [0, 1/3, 1]
```

For any fraction `f`:

```text
r(f) = rotate(r0, f * theta)
```

where `r0` is the entry ray from inner pivot `I` toward `E_in` and `theta` is the signed Turn sweep.

## 3.2 Preserve every outer-chain vertex

The Turn outer chain is exactly:

```text
E_in -> O -> E_out
```

For each cell interval `[f_k, f_(k+1)]`, the lower-surface station list must include:

- the front divider intersection `Q_k`;
- every outer-chain corner lying strictly inside that angular interval;
- the rear divider intersection `Q_(k+1)`.

In the current generalized envelope there is at most the single corner `O`, but the algorithm is written as an ordered outer-vertex list rather than assuming a four-corner cell.

For outer corner `O`, compute:

```text
f_O = signed_angle(r0, normalize(O-I)) / theta
```

normalized to the same signed sweep and clamped only by numerical epsilon.

If:

```text
f_k < f_O < f_(k+1)
```

then `O` is a required geometry station for that cell.

Do **not** connect `Q_k` directly to `Q_(k+1)` across `O`.

## 3.3 Event-index Z at inserted geometry stations

Primary divider heights remain RiseEvent indexed.

For a single Turn with entry/exit visible-soffit heights `z_0` / `z_n`:

```text
z_k = lerp(z_0, z_n, k/n)
```

for primary divider index `k`.

An inserted geometry-only station such as `O` does not create a tread or RiseEvent.

If `O` lies in cell `k`:

```text
lambda_O = (f_O - f_k) / (f_(k+1) - f_k)
z_O      = lerp(z_k, z_(k+1), lambda_O)
```

The same local interpolation rule applies to any future inserted outer-chain vertex.

## 3.4 Inner relief chord

Define entry/exit relief points:

```text
J_0 = I + rho * r(0)
J_n = I + rho * r(1)
```

Define the finite inner relief chord:

```text
K_inner = segment(J_0, J_n)
```

For every primary or inserted angular station `f`, intersect the ray

```text
I + t * r(f), t > 0
```

with `K_inner` and call the result:

```text
P(f)
```

Required station pair:

```text
Inner station = P(f) at z(f)
Outer station = V(f) at z(f)
```

where `V(f)` is `Q_k`, `O`, or another preserved outer-chain vertex.

Because `P(f)` values have distinct XY for distinct supported angular stations, the main visible soffit does not require coincident-XY vertical pivot edges.

## 3.5 Main turning-soffit strips

For every consecutive geometry station pair `a,b` in one nominal cell, create the ordered 3D quad:

```text
P_a -> V_a -> V_b -> P_b
```

with:

```text
P_a.z = V_a.z = z_a
P_b.z = V_b.z = z_b
```

Triangulate deterministically after winding normalization using diagonal:

```text
P_a -> V_b
```

unless that diagonal violates the standard simple-triangle checks, in which case the alternative diagonal may be used only if selected by one deterministic helper shared by tests and production.

No cell may omit an outer-chain corner. The union of plan projections of the main strips must exactly cover the nominal cell **minus only the pivot-relief core described in §4**.

---

# 4. SLOPED_CLOSED — finite pivot-relief core and face ownership

## 4.1 Pivot core plan

The pivot-relief core is the triangle:

```text
K_core = triangle(I, J_0, J_n)
```

It is derived UNDERBODY closure geometry only. It does not alter:

- canonical Path;
- stair width;
- nominal Winder tread polygons;
- Winder step count;
- legal/advisory interpretation.

All primary/inserted rays intersect its outer chord `J_0 -> J_n`, producing the ordered `P(f)` sequence from §3.

## 4.2 Pivot-core lower surface

Let:

```text
z_low  = min(z_0, z_n)
z_high = max(z_0, z_n)
A_low  = (I.x, I.y, z_low)
A_high = (I.x, I.y, z_high)
```

For each consecutive inner-chord station pair `P_a, P_b`, create one lower-core triangle:

```text
A_low -> P_a -> P_b
```

using station Z values from §3.

This forms a deterministic fan over `K_core`.

The boundary whose resolved soffit height equals `z_low` joins the fan directly.

The boundary whose resolved soffit height equals `z_high` receives one local **HIGH_SIDE_PIVOT_CLOSURE** triangle over the relief distance only:

```text
A_low -> A_high -> J_high
```

where `J_high` is `J_0` or `J_n` on the high-elevation boundary.

This explicit local closure is intentional. It replaces the Revision-1 full-width vertical triangle and is bounded in plan by `rho`.

There is no horizontal Landing plateau through the Winder.

## 4.3 Exact contact/body segmentation

For each Winder cell `C_j`:

```text
T_j = destination tread top Z
U_j = T_j - tread_thickness
```

`U_j` is the nominal underside/contact ceiling for that tread cell before nosing/rear-extension trimming.

The underbody volume over the cell is bounded by:

- physical tread/riser contact geometry above;
- the resolved SLOPED lower surface below;
- outer-side closure on the cell outer chain;
- inner pivot-core closure on the relevant `K_core` sector;
- destination-owned divider closure at RiseEvent boundaries;
- entry/exit interface closure only where not already owned by the adjacent component.

All lower/contact/riser surfaces are split at the same ordered geometry stations:

```text
primary divider stations
+
inserted outer-corner stations
+
physical finish trim intersections
```

Do not weld vertices by XY alone. Weld/reuse only when the full 3D coordinate and semantic interface owner match within named epsilon.

## 4.4 Divider/Riser face ownership

For divider `D_j` between Winder tread cells `j` and `j+1`:

- Winder tread `j+1` owns the physical Riser on `D_j` as already specified by Revision 1;
- the same destination cell owns any underbody divider closure needed below that Riser/contact region;
- the lower edge of that closure is the resolved lower-surface intersection on `D_j`;
- the upper edge is the actual resolved contact/Riser lower boundary after physical tread/riser trimming;
- the lower adjacent cell does not duplicate the face.

At the pivot-relief core, the divider closure terminates on the corresponding `P(f_j)` / core edge. It does not create an independent coincident prism at `I`.

## 4.5 Entry/exit component interfaces

At Winder entry/exit, adjacent component and Winder reuse exactly the same full 3D boundary vertices wherever their visible soffit surfaces meet.

If the finite pivot core requires the high-side local closure from §4.2, that closure is owned by the Winder pivot core and is not duplicated by the adjacent Straight/Winder component.

The lower-elevation side remains an exact direct join.

## 4.6 Contact clearance

For every cell and pivot-core subregion:

```text
visible_soffit_z < resolved_contact_z - eps_clear
```

at sampled/analytic extrema required by the geometry helper.

A failure caused by actual body depth / tread thickness / path geometry is `GEOMETRY_INVALID` for that combination. It must not be converted into a legal-like minimum stair width.

---

# 5. Winder STEPPED_CLOSED — exact Z contract

Revision 1 defined ownership but not coordinates. Use the following exact production rule.

For Winder tread cell `C_j`:

```text
T_j = destination tread top Z
d   = closed_body_depth
B   = base_z

Z_soffit_j = max(B, T_j - d)
```

This deliberately follows the accepted 07-C stepped-closure use of `closed_body_depth` as the visible vertical body offset. It does not use inner-pivot tread width or any legal minimum.

Each nominal cell owns one horizontal visible patch over its **complete nominal plan polygon**, including any required outer corner `O`.

Contact-clearance requirement:

```text
(T_j - tread_thickness) - Z_soffit_j > eps_clear
```

If floor clamp produces equality between adjacent cell soffit levels, omit the zero-height divider face rather than creating a degenerate face.

For internal divider `D_j`:

```text
lower = Z_soffit_j
upper = Z_soffit_(j+1)
```

The higher/destination cell owns the vertical closure between those levels over the complete divider segment after physical trim intersections are inserted.

Entry interface:

- incoming component provides its resolved visible soffit edge;
- if its Z differs from `Z_soffit_1`, Winder cell 1, as destination, owns the required boundary closure.

Exit interface:

- following destination component owns the next required closure if its resolved soffit Z differs from `Z_soffit_n`;
- Winder does not duplicate that face.

`underside_thickness` remains an inward shell/validation property and does not relocate `Z_soffit_j`.

---

# 6. Compact U — shared SLOPED height is event-group authority

Revision 1 fixed the shared XY section but did not fix its Z.

For a Compact U consisting of two consecutive WINDER Turns and zero ordinary middle Straight tread events:

```text
n1 = Turn 1 Winder step_count
n2 = Turn 2 Winder step_count
A  = visible-soffit Z at Turn 1 entry
B  = visible-soffit Z at Turn 2 exit
```

Treat the two Winder Turns as one **soffit-height interpolation group only**. Canonical Turn identities remain separate.

Shared middle height:

```text
M = A + (n1 / (n1+n2)) * (B-A)
```

Equivalent direct station sequence:

```text
Turn1 station k: z = A + (k/(n1+n2)) * (B-A)          k=0..n1
Turn2 station l: z = A + ((n1+l)/(n1+n2)) * (B-A)     l=0..n2
```

Therefore:

```text
Turn1 exit == Turn2 entry == M
```

exactly, not by averaging two independently invented heights.

Examples:

```text
EQUAL_3 + EQUAL_3 -> M at 3/6 of A..B
EQUAL_2 + EQUAL_3 -> M at 2/5 of A..B
BF_1 + EQUAL_3    -> M at 2/5 of A..B
```

This grouping affects derived SLOPED underbody station heights only. It does not merge Turn IDs, add a middle RiseEvent, or change canonical Path.

The Revision-1 shared XY-section midpoint rule remains applicable only for sub-epsilon coordinate disagreement after classification. Z authority comes from this section.

---

# 7. Side Board — mode independence and Compact-U shared-center solid

## 7.1 Lower/upper profile authority

Preserve accepted 07-C independence:

```text
underside_mode  -> Side Board lower profile
side_board_mode -> Side Board upper/visible profile
```

Therefore:

```text
STEPPED_CLOSED + STEPPED board -> upper stepped / lower stepped
STEPPED_CLOSED + SLOPED board  -> upper sloped  / lower stepped
SLOPED_CLOSED  + STEPPED board -> upper stepped / lower sloped
SLOPED_CLOSED  + SLOPED board  -> upper sloped  / lower sloped
```

The Side Board lower edge follows the selected UNDERBODY exterior boundary, not the Side Board upper-profile mode.

This supersedes Revision 1 §7.4 wording.

## 7.2 Shared center seam local frame

For a Compact-U coincident center seam, derive one seam-local frame:

```text
s = distance along the canonical shared center path
v = plan normal across the seam
z = world vertical
```

Do not build two complete board solids and Boolean them after collision.

For every enabled contributor that requires board coverage on that seam, resolve a 2D board region in `(s,z)`:

```text
R_i = { (s,z) | L_i(s) <= z <= U_i(s) }
```

where:

- `L_i(s)` comes from `underside_mode` and the exact underbody boundary;
- `U_i(s)` comes from `side_board_mode` / reveal / accepted terminal rules.

Invalid local ordering `L_i > U_i` is an actual geometry error for that contributor.

## 7.3 Shared profile union

The shared center-board profile authority is:

```text
R_shared = union(R_i for enabled contributors)
```

The union is solved in seam-local 2D before extrusion.

Rules:

- overlapping/touching regions become one polygonal component;
- vertically separated regions remain separate closed components;
- do not fill an empty Z gap merely to make one giant board;
- each component uses material role `SIDE_BOARD`;
- disabled contributors do not add profile area.

This is one `SHARED_CENTER_BOARD` family even if its union has multiple closed components.

## 7.4 Shared board thickness

For each closed shared-profile component, extrude symmetrically across the seam:

```text
v in [-side_board_thickness/2, +side_board_thickness/2]
```

The result is the actual shared-board 3D volume `V_shared`.

## 7.5 Derived physical-part trim

Trim only where `V_shared` actually occupies volume.

The following physical finish solids are trim candidates:

```text
TREAD
RISER
UNDERBODY
```

Conceptually:

```text
part_after = part_before \ interior(V_shared)
```

Implementation may use deterministic polygon/plane clipping instead of a Blender Boolean modifier, but the resulting set must be equivalent for the supported fixture.

Every new cut surface is capped and retains the material role of the trimmed part.

Do not remove a full-height plan strip when the shared board exists only over part of that Z range.

Board ON/OFF may change these derived finish trims only; it does not change canonical width, Path, RiseEvents, Turn pattern, or tread count.

## 7.6 Ordinary-board / shared-board transition

At the start/end of a shared-center interval:

- ordinary continuous board path and shared board reuse the same centerline/seam endpoint;
- lower/upper profile breakpoints are inserted into both sides before extrusion;
- one deterministic owner retains each coincident terminal/contact face;
- no open side-board cavity, duplicate z-fighting plate, or positive-volume overlap remains.

If only one of the global uphill-relative Side Board toggles contributes to the center seam, `R_shared` is built only from that enabled contributor. No phantom board is synthesized for the disabled side.

---

# 8. Corrected fixed expected-success fixtures

These are regression fixtures, never legal minima/maxima.

## 8.1 Old-house L width matrix — full finish success

Correct the Turn chirality by using:

```text
P0 = (0,0)
T  = (0,2200mm)
P2 = (-2200mm,2200mm)
```

which is an exact 90° left Turn under the project signed-angle convention.

Common values remain:

```text
Mode/Pattern       = WINDER / EQUAL_3
base_z             = 0mm
floor_to_floor     = 2800mm
overall risers     = 16
tread thickness    = 30mm
riser thickness    = 20mm
body depth         = 150mm
underside shell    = 9.5mm
nosing             = 5mm
front edge         = SQUARE
side board thick   = 18mm
side board reveal  = 40mm
boards             = BOTH ON
```

Run all of:

```text
900mm
800mm
750mm
700mm
650mm
```

For **every width**, the following two finish configurations are expected-success production cases:

```text
A: STEPPED_CLOSED + STEPPED Side Board
B: SLOPED_CLOSED  + SLOPED  Side Board
```

The test must reach final physical geometry, not stop after nominal Winder/RiseEvent validation.

Failure is permitted only with evidence of an actual defect in the fixed geometry contract; width alone is never the reason.

`650mm` remains a regression sample, not a production lower bound.

## 8.2 EQUAL_3 outer-corner preservation fixture

Use the width-750mm exact-90° EQUAL_3 L fixture.

For the central Winder cell, the ordered plan outer chain must be:

```text
Q_1 -> O -> Q_2
```

not `Q_1 -> Q_2`.

For a 90° Turn, `O` lies at angular fraction 1/2, therefore inside the central `[1/3,2/3]` cell:

```text
lambda_O = 1/2 within that cell
z_O = (z_1 + z_2) / 2
```

The lower-surface plan coverage may not lose the triangle adjacent to `O`.

## 8.3 Compact U expected-success fixture — two finish passes

```text
base_z           = 0mm
width            = 750mm
P0=(0,0)
P1=(0,2200mm)
P2=(750mm,2200mm)
P3=(750mm,0)
Turn1            = WINDER / EQUAL_3
Turn2            = WINDER / EQUAL_3
floor_to_floor   = 2800mm
overall risers   = 17
body depth       = 150mm
underside shell  = 9.5mm
tread thickness  = 30mm
riser thickness  = 20mm
nosing            = 5mm
front edge        = SQUARE
side boards       = BOTH ON
side board thick  = 18mm
side board reveal = 40mm
```

Run both:

```text
A: STEPPED_CLOSED + STEPPED Side Board
B: SLOPED_CLOSED  + SLOPED  Side Board
```

Required in B:

```text
shared soffit M = exact 3/6 event-group height
```

Required in both:

- `COMPACT_U` classification;
- zero ordinary middle tread events;
- one shared center-board family, not two colliding full boards;
- trim applies to actual TREAD/RISER/UNDERBODY intersection with `V_shared`;
- no duplicate shared-interface Riser;
- no open exterior cavity or positive-volume board collision.

## 8.4 Arbitrary-angle Landing fixed fixture

```text
width          = 750mm
P0             = (0,0)
T              = (0,2200mm)
P2             = T + 2200mm * (-sin(63°), cos(63°))
Mode           = LANDING / schema 5 generalized
base_z         = 0mm
floor_to_floor = 2800mm
overall risers = 16
```

Both adjacent segment lengths are exactly 2200mm before Turn cutback.

Expected: generalized envelope resolver succeeds without angle-preset rejection.

---

# 9. Physical contact-face validation clarification

Do not treat every intentional coplanar contact between separately owned physical parts as an error.

Distinguish:

```text
INTENTIONAL_CONTACT
UNINTENDED_DUPLICATE
```

`INTENTIONAL_CONTACT` may exist at an exact zero-volume interface required by the accepted fragment/material architecture, provided the final assembled topology and visual closure remain valid.

Reject/remove as `UNINTENDED_DUPLICATE` when two faces with the same intended owner/role occupy the same plane/area redundantly, cause z-fighting, produce duplicate closure ownership, or violate the accepted topology checks.

07-E does not require a global redesign of all accepted 07-C/07-D fragment contact interfaces merely to remove every internal contact plane.

---

# 10. Error classes retained

Retain Revision 1:

```text
GEOMETRY_INVALID
SCOPE_UNSUPPORTED
ADVISORY_ONLY
```

The new pivot-relief `rho` is a physical/numerical closure rule, not a legal minimum. A narrow but geometry-valid Stair must not fail merely because width is below a current recommendation.

---

# 11. Stage order retained

The official Stage 1–4 division remains unchanged.

Stage 3 implementation order remains:

```text
3A  Underbody with Side Boards OFF
3B  ordinary Side Board continuation
3C  Compact-U shared-center Side Board
```

However, the contracts in this Revision are architecture authority candidates **before** Stage 3 implementation begins; Codex must not invent them during Stage 3.

---

# 12. Roadmap clarification required before FINAL

The current ROADMAP contains generic examples such as:

```text
180° / 2段
180° / 3段
...
```

07-E production U geometry is based on **two persistent Turns**, each with its own Winder pattern. Those generic single-180° equal-angle examples are not 07-E production promises.

Before `BUILD_07_E_SPECIFICATION.md` is promoted to FINAL, ROADMAP §12.12 must distinguish:

```text
single-Turn mathematical examples / future reference
```

from:

```text
07-E production U = two-Turn combination
```

and must not imply that a 2-step total 180° U is required by 07-E Acceptance.

---

# 13. Third-review decision target

Third-party review should now determine whether:

1. preserving full outer-chain vertices fixes the EQUAL_3/BF/arbitrary-angle coverage issue;
2. finite pivot relief + localized high-side closure is a sound production replacement for the singular pivot spine;
3. the exact STEPPED Z rule is compatible with accepted 07-C semantics;
4. Compact-U shared SLOPED height is now unambiguous;
5. shared-center Side Board union/extrusion/3D trim is sufficiently defined;
6. the full-finish 650–900mm fixtures adequately protect old-house use;
7. implementation can proceed from repository text without reference images or additional geometry-design decisions.

Until that review passes, Build 07-E remains non-FINAL.
