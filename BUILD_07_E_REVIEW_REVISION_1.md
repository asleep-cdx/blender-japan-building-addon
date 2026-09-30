# BUILD 07-E — REVIEW REVISION 1
## Geometry / ownership contract corrections after third-party review

> **Status: REVIEW REVISION / SECOND-REVIEW CANDIDATE**  
> Date: 2026-09-30  
> Based on third-party review of main commit `f1ef564543549f3f5ef7d4d746e41320c0f9a734`.  
> This file is **not production implementation authority**. It records the exact contract changes proposed in response to the first review. For second review, read this together with `BUILD_07_E_SPECIFICATION.md`, `BUILD_07_E_DESIGN_RATIONALE.md`, the accepted 07-D documents, and the original third-party review brief. After second-review acceptance, these rules must be merged into `BUILD_07_E_SPECIFICATION.md` before that file is promoted to `FINAL / IMPLEMENTATION AUTHORITY`.

---

# 1. Disposition of first third-party review

Overall review verdict received:

```text
REVISE GEOMETRY CONTRACT
```

The project accepts that verdict. No requested 07-E user-facing capability is dropped.

The five mandatory review findings are accepted in substance:

1. straight-region allocation and Turn-boundary RiseEvent placement require an exact contract;
2. nominal Winder partition geometry must be separated from physical tread/nosing/riser solids;
3. STEPPED_CLOSED / SLOPED_CLOSED need explicit station, pivot, and closure ownership rules;
4. Compact U center Side Board behavior must be a supported construction rather than "detect collision and reject";
5. schema-4 -> schema-5 generalized-Landing migration must be explicit, especially for MANUAL allocation.

The review's clarification requests are also adopted unless explicitly refined below.

---

# 2. Canonical identity corrections

## 2.1 Turn identity

The accepted 07-D implementation stores stable Path point IDs and uses the interior point identity as the practical Turn anchor. 07-E does **not** introduce a second independent persistent UUID merely to duplicate that identity.

Normative schema-5 rule:

```text
turn_identity = interior path_point_id
```

A conceptual `turn_id` shown in diagrams is an alias of `path_point_id` unless a later Build introduces a demonstrated need for separate identity.

Consequences:

- ordinary load does not create new Turn UUIDs;
- schema-4 -> schema-5 promotion keeps existing point IDs exactly;
- duplicate Stair-ID repair does not rewrite point/Turn identity;
- rollback restores the original point-ID sequence together with schema and Turn state.

## 2.2 Winder pattern is the canonical authority

Do not allow `pattern`, `step_count`, and `partition_rule` to drift independently.

Canonical user-editable state:

```text
winder_pattern
```

Derived mapping:

```text
NONE      -> step_count=0, rule=NONE
EQUAL_2   -> step_count=2, rule=EQUAL_ANGLE
EQUAL_3   -> step_count=3, rule=EQUAL_ANGLE
EQUAL_4   -> step_count=4, rule=EQUAL_ANGLE
BF_1      -> step_count=2, rule=BF_1
BF_2      -> step_count=2, rule=BF_2
```

`winder_step_count` / `winder_partition_rule` may be exposed as derived diagnostics, but they are not independent persistent authorities in schema 5. Any stored cache that disagrees with `winder_pattern` is invalid/stale and must be recomputed rather than silently preferred.

## 2.3 New schema-5 residential Turn default

For a newly created schema-5 residential Winder Turn:

```text
turn_mode      = WINDER
winder_pattern = EQUAL_3
```

This default does not migrate or alter existing schema-4 Landing Stairs.

---

# 3. Exact RiseEvent and straight-region allocation contract

## 3.1 Event owners

Keep the accepted invariant:

```text
S + L + W + 1 = N
```

where:

```text
S = independent straight-tread RiseEvents
L = LANDING_ARRIVAL RiseEvents
W = WINDER_TREAD RiseEvents
1 = final UPPER_ARRIVAL RiseEvent
N = overall riser_count
h = floor_to_floor / N
```

Every physical rise is owned exactly once by its **destination surface**.

Destination owner types:

```text
STRAIGHT_TREAD
LANDING_ARRIVAL
WINDER_TREAD
UPPER_ARRIVAL
```

## 3.2 Straight-region minimum

For each resolved straight region with effective run `R_i`:

```text
R_i > eps_length  -> s_i >= 1
R_i ~= 0          -> s_i = 0 only for an explicitly supported zero-run transition
```

In 07-E, the primary supported zero-run case is the Compact-U middle region.

A positive ordinary straight region may not silently receive zero independent treads.

Going for a positive straight region:

```text
g_i = R_i / s_i
```

There is no scalar `g_i` for a Winder cell itself.

## 3.3 AUTO allocation — exact deterministic procedure

Resolve first:

```text
L = number of LANDING Turns
W = sum(step_count of WINDER Turns)
S_budget = N - L - W - 1
```

Let `P` be the set of positive straight regions and `m = len(P)`.

Validation:

```text
S_budget >= m
```

unless `m = 0`, in which case `S_budget` must be `0`.

Initial allocation:

```text
s_i = 1  for every positive straight region
s_i = 0  for supported zero-run regions
```

Distribute each remaining tread event one at a time to the positive straight region with the currently largest:

```text
R_i / s_i
```

Tie-break authority:

```text
canonical physical Path-segment order
```

not current FORWARD/REVERSE traversal order.

This deliberately extends the accepted 07-D discrete equalisation rule, where each positive Flight first received one tread interval and residual intervals went to the currently largest going.

After allocation:

```text
g_i = R_i / s_i
```

and all applicable straight-flight 07-C dimensional validators run on that `g_i`.

If the minimum one-tread-per-positive-region budget cannot be met, reject before geometry mutation with a specific allocation error.

## 3.4 Exact Z sequence

Maintain an event counter `c`, initially `0` at `B = base_z`.

For a destination surface that owns one RiseEvent:

```text
c := c + 1
surface_top_z = B + c*h
```

Therefore:

- straight tread `j` after `c0` prior events: `B + (c0+j)h`;
- Landing arrival after `c0` prior events: `B + (c0+1)h`;
- Winder tread `j` after `c0` prior events: `B + (c0+j)h`;
- final Upper Arrival: exactly `B + N*h`.

## 3.5 Riser ownership at component boundaries

A Riser belongs to the **higher/destination** surface reached by that rise.

For one Winder with division boundaries:

```text
D0 = entry boundary
D1 ... D(n-1) = internal boundaries
Dn = exit boundary
```

Rules:

- the riser on `D0` is owned by Winder tread 1;
- the riser on `Dj` is owned by Winder tread `j+1`;
- Winder tread `n` does **not** generate an extra riser on `Dn`;
- the next destination surface after `Dn` owns the next rise/riser.

Boundary examples:

```text
Straight -> Winder : first Winder tread owns interface riser
Winder -> Straight : first following Straight tread owns next riser
Straight -> Landing: Landing owns arrival riser
Landing -> Straight: first following Straight tread owns next riser
Winder -> Landing  : Landing owns next riser
Landing -> Winder  : first Winder tread owns next riser
```

Compact U with two consecutive Winder Turns:

```text
Turn 1 final tread
shared transition D
Turn 2 first tread
```

The first tread of Turn 2 owns the rise/riser at `D`. Turn 1 must not duplicate it.

---

# 4. Nominal Winder cells versus physical finish solids

This distinction is mandatory.

## 4.1 Layer A — nominal walking cells

The generalized Turn envelope is partitioned into nominal cells:

```text
C_1 ... C_n
```

with boundaries:

```text
D0 ... Dn
```

For cell `C_j` in ascent order:

```text
front/downhill boundary = D(j-1)
rear/uphill boundary    = Dj
```

Nominal-cell validation requires:

- complete coverage of the Turn envelope;
- no positive-area overlap between nominal cells;
- no unintended nominal gap;
- simple positive-area cells;
- deterministic ordering.

This is the validation to which "adjacent Winder tread positive-area overlap" applies.

### Outer-corner deduplication

A divider such as the 90° EQUAL_2/EQUAL_4 middle ray may pass exactly through outer corner `O` and therefore appear to intersect both outer-chain segments at the same coordinate.

Within `eps_length`:

```text
same XY intersection -> one Q point
```

Do not create two vertices/dividers for the same outer corner.

## 4.2 Layer B — physical TREAD solid

Physical tread finish is derived from the nominal cell and may intentionally overlap an adjacent cell in **XY projection** because it exists at a different Z.

For tread `j`:

1. start from nominal cell `C_j`;
2. extrude vertically from `top_z - t` to `top_z`;
3. apply front nosing only across the front/downhill boundary `D(j-1)`;
4. apply rear support extension only across the rear/uphill boundary `Dj` according to accepted riser-thickness semantics;
5. trim both extensions to the local inside/outside Turn boundaries and immediate neighboring walking region.

Nosing extension:

```text
n = tread_front_overhang
```

is a planar strip offset toward the downhill side of the front boundary. The strip is clipped at the first valid inner/outer boundary intersection. It is **not** required to retain constant full strip width at the mathematical pivot.

Rear extension:

```text
r = riser_thickness
```

is offset toward the uphill/destination side of the rear boundary and clipped to the immediately following walking region.

For the first/last Winder tread, the neighboring region may be a Straight or Landing interface instead of another Winder cell.

### Pivot trim

Offset front/rear strips must never be extrapolated through the inner pivot into an unrelated sector.

If an offset strip converges to the pivot, trim it to the first valid boundary intersection. A local collapse at the pivot endpoint is allowed; the entire exposed front edge must not be rejected merely because nominal Winder width tends to zero at `I`.

This prevents the old-house guardrail from being defeated by applying a Straight-style minimum going at the inner pivot.

## 4.3 Layer C — physical RISER solid

The riser owned by a destination surface lies on that destination's front boundary.

Riser thickness extends to the **uphill/destination side** of the front boundary, matching accepted Straight semantics.

The tread immediately below may extend rearward over the same plan strip at a different vertical range; intentional XY projection overlap is permitted.

## 4.4 BEVEL / ROUND ownership

`SQUARE / BEVEL / ROUND` is applied only to the exposed downhill/front edge of the physical TREAD/nosing solid.

Do not bevel/round:

- the rear boundary;
- the inner/outer side chain merely because it is a polygon edge;
- an internal nominal partition that is not the exposed front edge for that tread.

Endpoint caps close the selected front-edge profile deterministically. A zero-length endpoint at the mathematical pivot is omitted rather than turned into a zero-area cap.

Global 07-C constraints remain:

```text
q > 0 for BEVEL/ROUND
q < t/2
q <= n
```

The Straight rule `n < g_i` continues on ordinary Straight regions. Do **not** invent a Winder pseudo-going from the zero-width inner pivot and feed it to `validate_tread_front()`.

## 4.5 Physical-solid validation

Do not reject physical Winder treads merely because their XY projections overlap intentionally due to nosing/rear support.

Physical validation instead checks at least:

- non-finite coordinates;
- zero/near-zero real faces beyond numerical tolerance;
- unintended positive-volume intersection at the same vertical range;
- duplicate coplanar interior faces;
- open exterior cavity;
- front/rear strip crossing that cannot be trimmed to a valid local region.

An invalid finish combination must identify the finish rule that failed; it must not be reported as "stair width is below code".

---

# 5. Winder STEPPED_CLOSED — exact closure ownership

07-E Winder STEPPED_CLOSED is generated from nominal cells and the resolved RiseEvent sequence, not by stacking full Straight boxes.

For each Winder tread cell `C_j`, resolve its visible stepped-soffit level from the accepted Residential body-depth authority and its tread elevation. The visible level is derived from the destination tread's resolved body profile; do not derive it from a legal tread-width value or from inner-pivot width.

Normative ownership:

- each cell owns one horizontal visible soffit patch over its nominal cell footprint;
- the higher/destination cell owns the vertical closure patch on the shared divider between two adjacent visible soffit levels;
- entry/exit divider geometry shares exact interface vertices with the adjacent component resolver;
- no duplicate full-width wall is generated by both components;
- global lower termination retains the accepted `base_z` floor-clamp semantics from 07-C;
- the Winder interior must remain CLOSED with Side Boards OFF.

For implementation, the exterior visible soffit location is controlled by accepted `closed_body_depth` semantics. `underside_thickness` must not move the visible exterior soffit; it is an inward shell/validation property as in accepted 07-C.

Stage-3 runtime evidence must record horizontal patch Z values and divider-closure ownership for at least EQUAL_3 L and Compact U.

---

# 6. Winder SLOPED_CLOSED — station / pivot-spine contract

This section resolves the first review's most important open geometry item.

## 6.1 Interface authority

The Winder sloped soffit is not generated independently and patched afterward.

Resolve exact exterior visible-soffit cross-sections at:

```text
entry boundary D0
exit boundary Dn
```

from the same multi-component underbody resolver that owns adjacent Straight/Landing/Winder components.

For a Straight neighbor, the cross-section must share the **same XY endpoints and Z value** as the accepted Straight visible-soffit boundary at that cut.

For a neighboring Winder in Compact U, the first Turn's exit section and second Turn's entry section are one shared derived section.

## 6.2 Ordered lower-surface stations

For one Winder with `n` treads, create `n+1` lower-surface stations on the nominal division boundaries:

```text
S_0 ... S_n
```

Each station `S_k` is the full cross-section from the inner pivot ray endpoint to the resolved outer-chain point for divider `Dk`.

Let:

```text
z0 = visible-soffit Z at entry section
zn = visible-soffit Z at exit section
```

Intermediate station heights are indexed by RiseEvent order, not by BF/equal angular fraction:

```text
u_k = k / n
z_k = (1-u_k)*z0 + u_k*zn
```

This permits adjacent Straight Flights with different resolved goings/slopes while guaranteeing exact C0 boundary match at both ends.

Required:

```text
z_n > z_0 for FORWARD ascent
```

with the corresponding traversal reversal under REVERSE.

## 6.3 Pivot spine

All plan divider rays share the same XY inner pivot `I`, but their soffit stations may have different Z values.

Therefore the implementation must **not collapse vertices by XY alone**.

Create distinct 3D pivot-spine vertices:

```text
I_k = (I.x, I.y, z_k)
```

for `k = 0 ... n`.

For outer divider point `Q_k`:

```text
Q3_k = (Q_k.x, Q_k.y, z_k)
```

Lower-surface strip `k` between stations `k` and `k+1` is the ordered quad:

```text
I_k -> Q3_k -> Q3_(k+1) -> I_(k+1)
```

triangulated with one deterministic canonical diagonal. Recommended diagonal:

```text
I_k -> Q3_(k+1)
```

for all strips after winding normalization.

The coincident-XY sequence `I_0 ... I_n` is a real **vertical/oblique-in-Z pivot spine**, not one vertex.

## 6.4 Pivot closure / manifold rule

The body/contact/riser surfaces that meet the inner pivot must reuse the same ordered pivot-spine vertices.

Do not generate independent coincident Turn-body prisms around `I`.

Every pivot-spine edge segment must have the intended manifold boundary incidence after assembly; no zero-area side face is created merely to "cap" a point-width inner edge.

The final assembled managed Mesh must satisfy the accepted topology checks (finite, no unintended zero-area faces, boundary/nonmanifold expectations) on the representative Winder fixtures.

## 6.5 Contact-clearance validation

The generated sloped lower surface must remain below the relevant tread/riser contact geometry and may not cut through a tread or riser solid.

This is checked from actual 3D geometry / resolved contact surfaces, not by a legal-like minimum tread dimension.

If the selected body-depth/finish combination makes the surface physically impossible, reject that actual geometry combination with a body-clearance error.

## 6.6 Underside thickness direction

`closed_body_depth` continues to locate the exterior visible body/soffit according to accepted 07-C semantics.

`underside_thickness` does **not** move that exterior surface downward/outward.

If represented as an explicit shell, thickness offsets toward the Stair interior from the exterior lower surface. If the accepted solid-body representation remains in use, the existing 07-C validation semantics may be preserved; either way, visible station Z and the C0 join are independent of `underside_thickness`.

## 6.7 No Landing plateau

No intermediate station sequence may be replaced by a horizontal Landing slab merely because the plan direction changes.

C0 continuity is required. C1 tangent continuity remains non-mandatory.

---

# 7. Compact U — shared section and Side Board contract

## 7.1 Residual-run classification retained

Keep:

```text
R_mid = L_mid - d1 - d2

R_mid > +eps_length    -> SEPARATED_U
abs(R_mid)<=eps_length -> COMPACT_U
R_mid < -eps_length    -> INVALID_OVERLAP
```

`eps_length` is numerical only.

## 7.2 Shared transition section

For `COMPACT_U`, do not preserve two slightly different generated cross-sections merely because each Turn was resolved independently.

Derive one shared middle cross-section from the canonical middle Path segment and resolved Turn cutbacks.

Rules:

- canonical Path points are not moved;
- both Turn point identities remain unchanged;
- the shared section is derived geometry only;
- Turn 1 exit and Turn 2 entry reuse exactly the same section vertices;
- zero ordinary middle Straight tread events remain valid;
- no duplicate riser is created at the shared section.

When the two independently computed section coordinates differ only within `eps_length`, use the deterministic canonical midpoint of corresponding coordinates as the shared derived section. This is **not** a canonical Path snap and is not saved as a replacement Path coordinate.

If they disagree beyond numerical tolerance, the candidate is not a valid COMPACT_U classification.

## 7.3 Side Board is a continuous side-path, not per-Flight duplicates

Side Board semantics remain uphill-relative.

For each enabled physical side, first resolve one continuous side path through:

```text
Straight -> Winder -> optional shared Compact-U center segment -> Winder -> Straight
```

Do not build two independent center boards and then detect their collision.

### Coincident Compact-U center seam

In an exact compact switchback, anti-parallel Flight side boundaries may be coincident in XY along a center seam.

If the same continuous physical side path traverses coincident seam segments with opposing local outward normals:

- represent them as one `SHARED_CENTER_BOARD` path family;
- use one SIDE_BOARD material role;
- do not duplicate coincident board solids;
- board thickness `s` is centered on the coincident seam (`s/2` to each plan side) for the shared-seam interval;
- tread/underbody **physical finish solids** on both adjacent sides are trimmed by `s/2` at that shared seam so the board does not create positive-volume intersection;
- this trim is derived finish geometry only and does not rewrite canonical stair_width or Path coordinates.

If the center-side board is disabled, no shared center board is generated and no `s/2` trim is applied on that side.

If both global Side Board toggles are enabled, the outer continuous side path and center continuous side path are both generated; the center path is still a single shared family, not two colliding boards.

### Vertical self-intersection

The shared center path is parameterized in ascent order with the same RiseEvent/underbody authority as the rest of the Stair. Coincident XY projection at different elevations is allowed.

Positive-volume self-intersection at overlapping Z is not allowed. The standard Compact-U fixture in Section 11 must pass with both boards enabled; therefore "detect center collision and reject" is not an acceptable implementation for that fixture.

## 7.4 Side Board lower edge

The Side Board lower edge uses the same resolved underbody boundary authority:

- STEPPED board lower profile follows resolved stepped closure;
- SLOPED board lower profile follows the station/pivot-spine sloped closure;
- Flight/Winder/shared-section joins reuse exact boundary vertices;
- Side Board ON/OFF does not change TREAD/RISER/UNDERBODY canonical geometry except the explicit shared-center-seam finish trim described above.

---

# 8. Schema-4 -> schema-5 migration matrix

Existing schema-4 ordinary behavior remains isolated until the user invokes an explicit 07-E operation.

## 8.1 Operations that stay schema 4

For an existing exact-90° Landing Stair, the following remain schema 4 and use accepted 07-D rules:

- load/open;
- ordinary Regenerate;
- Material edit;
- Reverse;
- accepted schema-4 Path editing that remains exact 90°;
- Repair.

These operations do not gain arbitrary-angle behavior implicitly.

## 8.2 Explicit generalized-Landing promotion

An explicit 07-E generalized-Turn operation may promote a schema-4 Landing Stair to schema 5 while keeping `LANDING` mode.

For each accepted schema-4 physical Flight allocation `r_i`:

```text
s_i = r_i - 1
```

This preserves 07-D Landing semantics because for `F` straight regions:

```text
L = F - 1
sum(r_i) = N
sum(s_i) + L + 1 = N
```

Example:

```text
schema-4 U MANUAL r = [6,5,5]

schema-5 generalized Landing:
s = [5,4,4]
L = 2
W = 0

5+4+4+2+1 = 16
```

The candidate is then revalidated against the new generalized Landing geometry before commit.

If validation fails, schema, old `r_i`, Turn state, Mesh, Materials and point IDs all roll back.

## 8.3 LANDING -> WINDER

For schema-4 `MANUAL`:

```text
LANDING -> WINDER
```

remains blocked until the user explicitly returns the Stair to AUTO. Do not silently invent a new distribution.

For schema-4 `AUTO`, an explicit Winder conversion may promote to schema 5 and run the schema-5 AUTO algorithm from Section 3.

After a valid schema-5 AUTO Winder exists, the user may switch schema 5 to MANUAL and edit schema-5 straight-region allocations.

## 8.4 Arbitrary-angle point relocation

The statement "90°から外れたことだけでrejectしない" applies only after explicit schema-5/generalized-Turn promotion.

The legacy schema-4 Path move operator retains accepted 07-D exact-90° behavior.

---

# 9. BF tolerance / Reverse / mirror clarifications

## 9.1 BF near 90°

BF is available only when the Turn satisfies the same accepted right-angle predicate/tolerance used by 07-D canonical geometry.

Do not snap canonical Path geometry to 90°.

If the actual resolved `theta` is inside that tolerance:

```text
BF_1 fraction = 2/3 of actual signed theta
BF_2 fraction = 1/3 of actual signed theta
```

Because the tolerance is very small, the result remains the expected 60/30 family without rewriting Path coordinates.

Outside that production tolerance, BF is an explicit **scope unsupported** choice; use EQUAL_ANGLE or LANDING.

## 9.2 Reverse example

Canonical path entry order:

```text
BF_1 -> 60°, then 30°
```

If ascent is reversed, a person climbing the Stair encounters those same physical sectors in reverse order:

```text
30°, then 60°
```

but the persisted physical pattern identity remains:

```text
BF_1
```

Reverse does not rewrite BF_1 to BF_2.

## 9.3 Left/right Side Board semantics

LEFT / RIGHT remain relative to the current uphill traversal, as accepted previously.

Therefore Reverse may move a "left" board to the opposite world-space side. "No side swap" means no stale/wrong derived side ownership after traversal changes; it does **not** mean world-space side is fixed under Reverse.

---

# 10. Supported Path scope for 07-E acceptance

07-E final acceptance requires production Winder/generalized-Turn support for:

```text
3-point L : 1 Turn
4-point U : 2 Turns
```

Existing 07-D schema-4 Custom/multi-point Landing data remains compatible.

Winder production on a custom Path with **3 or more Turns** is not a mandatory 07-E acceptance target. Pure generalized resolvers should avoid needless hard-coding to two turns, but runtime acceptance and production guarantees are L/U scope unless explicitly expanded by a later reviewed addendum.

This limit is scope, not mathematical impossibility.

---

# 11. Fixed success fixtures

These fixtures are production regression targets, not legal minima/maxima.

## 11.1 Old-house narrow L Winder width matrix

Common settings:

```text
Path             : P0=(0,0), T=(0,2200mm), P2=(2200mm,2200mm)
Turn             : exact 90° left
Mode/Pattern     : WINDER / EQUAL_3
base_z           : 0mm
floor_to_floor   : 2800mm
overall risers   : 16
tread thickness  : 30mm
riser thickness  : 20mm
body depth       : 150mm
underside shell  : 9.5mm
nosing            : 5mm
front edge        : SQUARE
side board thick  : 18mm
side board reveal : 40mm
boards             : BOTH ON
```

Run separately with:

```text
width = 900mm
width = 800mm
width = 750mm
width = 700mm
width = 650mm
```

All five are **expected-success** cases for nominal Winder / RiseEvent allocation. Stage-3 finish acceptance must additionally pass both STEPPED_CLOSED and SLOPED_CLOSED where the selected body/board geometry remains valid.

Width alone may not be cited as failure.

## 11.2 Compact U expected-success fixture

```text
width            : 750mm
Path             : P0=(0,0), P1=(0,2200mm), P2=(750mm,2200mm), P3=(750mm,0)
Turn 1           : WINDER / EQUAL_3
Turn 2           : WINDER / EQUAL_3
floor_to_floor   : 2800mm
overall risers   : 17
body depth       : 150mm
underside shell  : 9.5mm
tread thickness  : 30mm
riser thickness  : 20mm
nosing            : 5mm
front edge        : SQUARE
side boards       : BOTH ON
side board thick  : 18mm
side board reveal : 40mm
```

Expected:

- `COMPACT_U` classification;
- zero ordinary middle Straight tread events;
- no duplicate shared-interface riser;
- shared middle section reused exactly;
- center Side Board resolved by the shared-center-path rule, not rejected for collision;
- no positive-volume board/tread/body collision;
- one Managed Stair.

## 11.3 Arbitrary-angle Landing expected-success fixture

```text
width            : 750mm
Turn angle       : 63°
Mode             : LANDING (schema 5 generalized)
floor_to_floor   : 2800mm
overall risers   : 16
positive Straight run exists on both sides
```

Expected: same generalized envelope algorithm; no angle-preset rejection.

## 11.4 Winder finish expected-success fixture

At least one width-650mm EQUAL_3 L case must pass with:

```text
nosing = 5mm
front edge = SQUARE
riser thickness = 20mm
```

The inner pivot tending to zero nominal tread width is not itself a reason to reject the nosing.

BEVEL / ROUND representative acceptance is added after SQUARE physical-solid acceptance.

---

# 12. Error classification

User-facing failure must distinguish:

```text
GEOMETRY_INVALID
SCOPE_UNSUPPORTED
ADVISORY_ONLY
```

Examples:

### GEOMETRY_INVALID

- non-finite intersection;
- self-intersection;
- zero/negative nominal cell area beyond epsilon;
- insufficient Path length for required cutback;
- unsupported positive-volume Turn overlap;
- physical finish self-intersection that cannot be trimmed;
- underbody/tread penetration.

### SCOPE_UNSUPPORTED

- BF requested on a non-right-angle Turn outside the accepted tolerance;
- Winder production requested on >2-Turn Custom topology during 07-E if not explicitly supported.

Do not describe these as mathematical impossibility.

### ADVISORY_ONLY

- narrow/steep/tight old-house-like dimensions that are still geometry-valid;
- future legal/recommended-dimension hints.

Advisory-only conditions do not cancel generation.

`650mm` is a regression sample, **not** a new production minimum.

---

# 13. Stage-order clarification

The four official Stages remain.

## Stage 1

Complete before first Winder runtime acceptance:

- schema-5 Turn/pattern foundation;
- exact RiseEvent ownership;
- AUTO straight-region allocation;
- schema-4 compatibility/promotion foundation;
- 90° L EQUAL_2/3/4 nominal geometry;
- SQUARE Winder tread/riser physical geometry with a deliberately limited finish subset documented in the Candidate runtime sheet;
- transaction / rollback / save basics.

Positive nosing/BEVEL/ROUND may be activated after the nominal/rise foundation is accepted, but their **final contract is already fixed by this revision**.

## Stage 2

Internal acceptance order:

```text
2A BF patterns
2B U / Compact U
2C arbitrary-angle Landing
2D arbitrary-angle EQUAL Winder
2E positive nosing / front-edge finish integration where not already enabled
```

Do not debug all Stage-2 families simultaneously.

## Stage 3

Internal acceptance order:

```text
3A STEPPED_CLOSED with Side Boards OFF
3B SLOPED_CLOSED with Side Boards OFF
3C Side Board continuation
3D Compact-U shared center board
3E material/reverse/repair/topology sweep
```

Side Board changes must not redesign already accepted TREAD/RISER/UNDERBODY geometry except the explicit shared-center-seam finish trim in Section 7.

## Stage 4

Lifecycle/full regression/practical acceptance as already planned.

Save/Undo/rollback checks for new canonical state are also performed at the Stage where that state first becomes production-active; Stage 4 repeats representative end-to-end cases.

---

# 14. 07-D regression authority clarification

07-E regression must preserve the **final accepted 07-D behavior**, including the Stage-2 r19 correction series and later Stage-3/Stage-4 accepted results, not an earlier intermediate Landing implementation.

In particular preserve accepted 07-D behavior for:

- outer terminal closure;
- upper reveal restoration;
- inner terminal tail;
- final Landing perimeter closure;
- U middle-Flight ownership;
- final schema-4 persistence/lifecycle/repair behavior.

The exact Stage-4 runtime Candidate remains the final 07-D overall regression package recorded by `BUILD_07_D_ACCEPTANCE_RECORD.md`; Stage-2 r19 geometry corrections are part of the accepted production lineage that Stage 3/4 retained.

---

# 15. Roadmap 180° notation clarification

Any Roadmap/example table showing:

```text
180° / 2
180° / 3
...
```

is a **mathematical angular-subdivision reference**, not a promise that 07-E will implement one persistent single-Turn 180° fan with 2 or 3 total Winder treads.

07-E production U authority remains:

```text
existing 4-point U Path
+
2 persistent Turn anchors
+
per-Turn pattern assignment
```

Compact U may derive one composite geometry group, but does not replace the two canonical Turn anchors with one fake 180° Turn.

This wording must be merged back into `ROADMAP.md` before FINAL publication.

---

# 16. Requirements for second third-party review

The second reviewer should decide whether the combined candidate:

```text
BUILD_07_E_SPECIFICATION.md
+ BUILD_07_E_DESIGN_RATIONALE.md
+ this REVIEW_REVISION_1
```

now removes implementation-design ambiguity in the first review's five mandatory areas.

Please specifically challenge:

1. whether the AUTO `s_i` allocation preserves 07-D semantics and Reverse stability;
2. whether nominal-cell versus physical-solid validation is sufficiently separated;
3. whether the SLOPED_CLOSED station + pivot-spine construction can produce a closed manifold without a hidden Landing plateau;
4. whether the Compact-U shared center Side Board rule is geometrically implementable and avoids duplicate/colliding boards;
5. whether schema-4 MANUAL generalized-Landing promotion by `s_i=r_i-1` is complete and rollback-safe;
6. whether the fixed 650mm and Compact-U fixtures protect old-house use without creating new de-facto minima;
7. whether any requirement still forces an implementer to infer geometry from reference images.

Do not begin Codex production implementation until these revision rules have passed second review and have been merged into the final Specification.
