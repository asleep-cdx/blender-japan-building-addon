# BUILD 07-E — DESIGN RATIONALE / GEOMETRY CONTRACT NOTES
## 日本住宅モデラー — Winder / 廻り段 + Arbitrary-angle Turn / Landing

> **Status: REVIEW COMPANION / THIRD-PARTY REVIEW PENDING**  
> Date: 2026-09-30  
> Companion to `BUILD_07_E_SPECIFICATION.md`. This document records **why** the 07-E requirements exist and explains the geometry contract in repository text so implementation and third-party review do not depend on reference images. The Specification remains the future implementation authority after it is promoted to `FINAL / IMPLEMENTATION AUTHORITY`.

---

# 1. Why this document exists

Build 07-E is the main production target for ordinary Japanese residential turning stairs. It also has to support renovation visualization of older houses, where an existing stair may be narrower, tighter, steeper, or less regular than a present-day new-build stair.

The typical project need is:

```text
existing old house
↓
structure / stair remains in place
↓
wall / floor / finish is renovated
↓
existing stair remains visible in the presentation
↓
JHM must reproduce that existing stair
```

Therefore two requirements have equal importance:

1. Generate common residential Winder / 廻り段 geometry predictably.
2. Do **not** reject an existing old-house stair merely because its dimensions do not satisfy a current legal / recommended dimension.

JHM is a Blender modeling aid for renovation visualization, not a building-code compliance engine.

---

# 2. Reference-image policy

Reference images supplied during design discussion are useful for identifying desired pattern families, but they are **not implementation authority**.

Normative rule:

> **Codex implementation must be possible from repository text alone. No production algorithm may require looking at an external or chat-attached image to infer geometry.**

Therefore:

- `2段廻り`, `3段廻り`, `4段廻り`, `BF-1`, `BF-2` are user-facing pattern identities;
- exact geometry is defined by vectors, line intersections and partition fractions;
- no legal or industry-standard expansion of `BF` is assumed by JHM;
- thumbnails/icons are UI aids only;
- if an image and the final text contract disagree, the final text contract wins.

---

# 3. Major design decisions and reasons

## 3.1 2 / 3 / 4 equal-angle patterns

These are understandable residential presets but are generated from one rule:

```text
fraction f_j = j / n
j = 1 ... n-1
```

Thus `3段` is not internally synonymous with `30°`; a 72° Turn with 3 Winder treads becomes `24° × 3` automatically.

## 3.2 BF-1 / BF-2 are separate partition rules

The requested BF family is asymmetric. Therefore:

```text
winder_step_count
!=
winder_partition_rule
```

For JHM normalized 90° production:

```text
BF_1 fractions = [2/3]  -> 60°, 30°
BF_2 fractions = [1/3]  -> 30°, 60°
```

Both contain 2 Winder treads and 1 internal division boundary.

## 3.3 Arbitrary-angle Landing belongs in 07-E

07-D accepts exact ±90° Landing turns. Existing houses can turn by 47°, 63°, 82°, etc. Therefore the angle is derived from Path geometry instead of selected from an angle table.

## 3.4 Shift 15° is an interaction aid only

```text
Shift 15° = convenient drawing constraint
Turn angle = derived from Path
```

A free/numeric 63° Path is not invalid because 63 is not a multiple of 15.

## 3.5 Compact U needs a dedicated derived classification

A common 180° residential Winder may have zero ordinary straight tread between its two quarter-turn regions. Treating every Path segment as a normal Flight would falsely reject this as a short middle Flight.

The accepted 07-D Path points and both Turn IDs remain canonical. A `Composite U Winder Group` may exist only as derived geometry state.

## 3.6 Winder SLOPED_CLOSED is not a Landing underside

A Landing is horizontal and may have a horizontal underside transition. A Winder continues rising through the turn. Therefore its closed sloped soffit must continue vertically through the turn rather than insert a horizontal plateau.

---

# 4. Common generalized Turn frame

For an interior canonical Path point:

```text
T      = P_i
P_prev = P_(i-1)
P_next = P_(i+1)

a = normalize(T - P_prev)
b = normalize(P_next - T)
```

Signed turn angle:

```text
theta = atan2(cross2(a, b), dot(a, b))
```

Project XY convention:

```text
theta > 0 = left turn
theta < 0 = right turn
```

Define:

```text
s = sign(theta)
left_normal(d) = (-d.y, d.x)
inside_normal_in  = s * left_normal(a)
inside_normal_out = s * left_normal(b)
```

For stair width `w`:

```text
incoming inside : T + (w/2) * inside_normal_in  + lambda * a
incoming outside: T - (w/2) * inside_normal_in  + lambda * a

outgoing inside : T + (w/2) * inside_normal_out + mu * b
outgoing outside: T - (w/2) * inside_normal_out + mu * b
```

Resolve:

```text
I = intersection(incoming inside, outgoing inside)
O = intersection(incoming outside, outgoing outside)

E_in  = I - w * inside_normal_in
E_out = I - w * inside_normal_out
```

Turn envelope:

```text
I -> E_in -> O -> E_out -> I
```

This same envelope is used for:

- arbitrary-angle Landing;
- equal-angle Winder;
- 90° BF Winder.

Exact 90° / equal width reduces to the accepted 07-D nominal `w × w` Landing footprint.

For ordinary symmetric equal-width cases, the centerline cutback magnitude is:

```text
d = (w/2) * tan(abs(theta)/2)
```

This is a geometry relationship, not a legal minimum.

---

# 5. Numerical singularity rule

07-E must not impose a building-code angle table.

A Turn may be rejected when it is numerically/geometrically singular, for example:

- incoming/outgoing segment has near-zero length;
- theta is too close to 0° for a distinct stable Turn cell;
- theta is too close to ±180° for a stable single-Turn miter;
- required line intersections are non-finite;
- required cutback consumes more Path length than available.

Any `eps_length`, `eps_area`, or `eps_angle` is a **numerical tolerance**, not a residential-code threshold.

---

# 6. Equal-angle Winder exact construction

From the Turn frame:

```text
r0 = normalize(E_in  - I)
r1 = normalize(E_out - I)
```

For `n` Winder treads:

```text
fractions = [j/n for j in 1 ... n-1]
```

For each `f`:

```text
r_f = rotate(r0, f * theta)
R_f(t) = I + t * r_f, t > 0
```

Intersect the ray with the outer chain:

```text
E_in -> O -> E_out
```

Choose the nearest valid positive intersection `Q_f`. The segment `I -> Q_f` is a division boundary. Split the Turn envelope into ordered simple tread polygons.

Production fractions:

```text
EQUAL_2 = [1/2]
EQUAL_3 = [1/3, 2/3]
EQUAL_4 = [1/4, 1/2, 3/4]
```

Exact 90° therefore gives:

```text
2 steps = 45° + 45°
3 steps = 30° + 30° + 30°
4 steps = 22.5° × 4
```

---

# 7. JHM normalized BF-1 / BF-2

BF-1 / BF-2 are project-defined normalized residential pattern identities, not claims about an external legal standard.

07-E BF support is restricted to approximately/exactly 90° single Turns using the project geometry tolerance.

```text
BF_1 fractions = [2/3]
→ 60°, 30°

BF_2 fractions = [1/3]
→ 30°, 60°
```

Construction uses the same ray / outer-chain algorithm as the equal-angle family.

Left/right uses signed theta. No separate mirrored mesh generator is required.

`REVERSE` does not change BF_1 into BF_2. Plan subdivision remains fixed; only ascent/elevation traversal reverses.

---

# 8. U / overall 180° mapping

Canonical authority remains per Turn:

```text
P0 -> P1 -> P2 -> P3
       T1    T2
```

Turn 1 and Turn 2 are independently configurable.

Examples:

```text
EQUAL_2 + EQUAL_3
BF_1 + EQUAL_3
BF_1 + BF_2
```

For compact U, two reference asymmetric families are:

```text
Turn 1 = BF_1
Turn 2 = BF_2
→ 60°, 30°, 30°, 60°

Turn 1 = BF_2
Turn 2 = BF_1
→ 30°, 60°, 60°, 30°
```

These are convenience interpretations only; storage remains individual Turn assignments.

---

# 9. Compact U exact rule

Two consecutive Turn anchors:

```text
T1 = P_i
T2 = P_(i+1)
L_mid = length(T2 - T1)
```

Resolve each Turn envelope from the same actual stair width.

```text
d1 = Turn1 exit cutback on middle segment
d2 = Turn2 entry cutback on middle segment
R_mid = L_mid - d1 - d2
```

Classification:

```text
R_mid > +eps_length
    = SEPARATED_U

abs(R_mid) <= eps_length
    = COMPACT_U
    = zero ordinary middle straight run

R_mid < -eps_length
    = INVALID_OVERLAP
```

For exact 90° + 90° equal-width turns:

```text
d1 = w/2
d2 = w/2
COMPACT_U when L_mid ~= w
```

Therefore the rule scales naturally:

```text
w=900 -> compact separation ~=900 mm
w=750 -> compact separation ~=750 mm
w=650 -> compact separation ~=650 mm
```

There is no 900mm hard-coded compact-U requirement.

`COMPACT_U` keeps both canonical Turn IDs and point IDs, owns zero ordinary middle straight tread/rise events, and allows a derived composite generator only for geometry.

---

# 10. Arbitrary-angle Landing

The Landing walking polygon is the same generalized Turn envelope:

```text
Landing = [I, E_in, O, E_out]
```

with normalized winding.

```text
entry = I -> E_in
exit  = I -> E_out
outer chain = E_in -> O -> E_out
```

Thus exact 90° returns the accepted square, while 47°, 63°, 82°, etc. use the same algorithm. There is no separate angle-specific Landing generator.

---

# 11. Arbitrary-angle Winder

Arbitrary-angle Winder uses:

```text
same generalized Turn envelope
+
EQUAL_ANGLE partition
```

Example:

```text
theta = 63°
step count = 3
→ 21° + 21° + 21°
```

BF is not generalized to arbitrary theta in 07-E.

---

# 12. Exact RiseEvent ownership

This section is critical because schema 5 can mix Landing and Winder Turns.

```text
N = overall_riser_count
h = floor_to_floor / N
```

Every physical rise event has exactly one destination owner:

```text
STRAIGHT_TREAD
LANDING_ARRIVAL
WINDER_TREAD
UPPER_ARRIVAL
```

Rules:

1. Each independent straight tread owns the rise immediately before that tread.
2. Each `LANDING` Turn walking surface owns one `LANDING_ARRIVAL` rise event.
3. Each Winder tread owns one rise event immediately before that tread.
4. Upper floor arrival owns one final rise event.
5. No event may be owned twice.

Let:

```text
S = independent straight tread events
L = LANDING_ARRIVAL events
W = Winder tread events
N = overall riser count
```

Authority:

```text
S + L + W + 1 = N
```

Examples:

```text
Straight, N=16:
S=15, L=0, W=0 -> 15+0+0+1=16

L with one Landing, N=16:
S=14, L=1, W=0 -> 14+1+0+1=16

U with two Landings, N=16:
S=13, L=2, W=0 -> 13+2+0+1=16

L with 3-step Winder, N=16:
S=12, L=0, W=3 -> 12+0+3+1=16
```

A zero-run Compact-U middle region owns zero straight tread events and zero rise events.

---

# 13. AUTO allocation rationale

Resolve in this order:

```text
1. overall N
2. Turn modes
3. W = total Winder tread count
4. L = count of LANDING Turns
5. reserve 1 final UPPER_ARRIVAL event
6. straight tread budget = N - W - L - 1
7. resolve positive straight runs
8. deterministic integer apportionment
9. build ordered RiseEvents
10. geometry validation
11. atomic commit
```

A zero effective straight run receives zero straight tread events.

This keeps Landing, Winder and final arrival ownership explicit instead of hiding them inside mesh-generation code.

---

# 14. MANUAL migration rationale

Existing schema-4 MANUAL allocations were defined around Landing/Flight semantics. Changing a Landing to a Winder changes vertical ownership.

Therefore 07-E does not silently rewrite those user counts.

Conservative production rule:

```text
schema-4 MANUAL
+
LANDING -> WINDER request
↓
reject with clear message
↓
user explicitly switches to AUTO
↓
convert to schema 5 Winder
↓
user may switch schema-5 result to MANUAL
```

This is safer than inventing an unreviewed redistribution.

---

# 15. Old-house / narrow-stair hard guardrail

This is a project requirement, not an optional preference.

The geometry gate, RNA property ranges, UI clamping and presets must not reject solely because:

```text
stair_width < 900 mm
stair_width < 800 mm
stair_width < 750 mm
```

Nor may the design-reference values such as 300 / 150 / 85 mm become universal generation minima.

Do not introduce hidden equivalents such as:

```text
MIN_LEGAL_STAIR_WIDTH = 750
MIN_LEGAL_WINDER_TREAD = ...
```

Reject actual geometry failure, for example:

- non-finite / non-positive Turn envelope;
- self-intersecting tread polygon;
- positive-area overlap;
- walking-surface gap;
- zero/near-zero geometry beyond numerical epsilon;
- failed partition intersection;
- Turn overlap;
- Path self-intersection;
- required cutback exceeding available segment geometry.

If geometry remains valid, a very narrow or tight old-house configuration may warn but should generate.

Required regression widths include:

```text
900
800
750
700
650 mm
```

If an existing property-level minimum prevents such a representative valid case from even being entered, the range may be corrected without changing the project default width. The future default-width change itself remains outside 07-E.

---

# 16. SLOPED_CLOSED rationale

A Winder changes plan direction while continuing vertical progression.

Authority:

```text
lower straight soffit boundary
↓
ordered Winder lower-surface stations
↓
upper straight soffit boundary
```

Requirements:

- C0 continuity at both joins;
- continued elevation progression through the Winder;
- no horizontal Landing plateau through a Winder;
- piecewise planar / triangulated surface is allowed;
- C1 tangent continuity is not required in 07-E;
- no cavity, giant filler prism, or duplicate positive-volume body;
- same Path / width / RiseEvent authority as the top geometry.

This is intentionally Stage 3 work after top-plan acceptance.

---

# 17. Side Board rationale

Winder Side Boards derive from the same resolved inside/outside Turn boundaries and elevation sequence.

Do not patch a visually plausible disconnected board onto the turn.

Requirements:

- stable physical left/right side;
- no unexpected Reverse side-swap;
- outer board follows the outer Turn chain;
- inner board may be trimmed/segmented around a tight pivot;
- Flight/Winder joins share exact derived positions;
- Compact-U center boards are checked for collision.

---

# 18. Alternatives considered and rejected

1. **Hard-code a separate mesh per pattern** — duplicates logic and blocks arbitrary-angle reuse.
2. **Use `3段=30°` as the model** — confuses step count with partition rule.
3. **Reject below a legal-like width** — conflicts with renovation modeling of old houses.
4. **Treat every U middle segment as a normal Flight** — falsely rejects Compact U.
5. **Replace two U Turns with one fake 180° Turn** — breaks accepted point/Turn identity architecture.
6. **Separate 45°/60°/90° Landing generators** — does not support arbitrary existing-house geometry.
7. **Use reference images as coding instructions** — ambiguous and not durable repository authority.
8. **Solve top, underside and Side Board simultaneously** — repeats the 07-D debugging problem.

---

# 19. Why Stage order is deliberate

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

This isolates plan errors from finish-surface errors and preserves a clear runtime acceptance boundary between them.

---

# 20. Third-party review checklist

Reviewer should read:

```text
ROADMAP.md
BUILD_07_D_SPECIFICATION.md
BUILD_07_D_ACCEPTANCE_RECORD.md
BUILD_07_E_SPECIFICATION.md
BUILD_07_E_DESIGN_RATIONALE.md
DEVELOPMENT_WORKFLOW.md
```

Questions:

- Does schema-5 preserve accepted schema-1/2/3/4 without silent migration?
- Is the generalized Turn frame mathematically consistent for left/right and oblique turns?
- Does exact 90° reduce to the accepted 07-D square Landing?
- Are Winder step count and partition rule separated correctly?
- Are BF_1/BF_2 reproducible from text alone?
- Is BF left/right/Reverse behavior unambiguous?
- Is Compact-U `R_mid` classification sufficient?
- Is arbitrary-angle Landing free of angle-specific hard-coding?
- Is `S + L + W + 1 = N` complete for mixed Landing/Winder stairs?
- Is schema-4 MANUAL -> WINDER conversion safely handled?
- Can validator/property/UI rules accidentally become hidden building-code gates?
- Are 700/650mm geometry-valid old-house cases modelable?
- Are numerical epsilons clearly distinct from legal-like minima?
- Is Winder SLOPED_CLOSED continuity defined strongly enough?
- Are Side Boards derived from the same Turn geometry rather than patched afterward?
- Is Stage separation sufficient to avoid the 07-D underside-debugging problem?
- Are any requirements unnecessarily expensive relative to the renovation-visualization goal?
- Are there contradictions among Roadmap, 07-D accepted contracts and 07-E proposed contracts?

Reviewer should identify the exact section/invariant behind each recommendation.

---

# 21. Items intentionally outside 07-E

Do not mix in unless a direct blocker is found:

- default stair width change from 900mm to a future project default such as 750mm;
- general Stair panel compacting / collapsible UI redesign;
- broad unrelated UX cleanup;
- Riser OFF / Underside NONE / support variants (07-F);
- optional tread-detail expansion (07-G);
- Floor / Room dependency (08);
- Door / Window integration (09).

---

# 22. Review-to-FINAL rule

Before `BUILD_07_E_SPECIFICATION.md` becomes `FINAL / IMPLEMENTATION AUTHORITY`:

1. third-party review is completed;
2. accepted review changes are incorporated;
3. this rationale and the Specification are checked for contradictions;
4. all production geometry can be implemented from repository text without reference images;
5. legal-sounding dimensions are confirmed not to be core generation thresholds;
6. only then is the Specification status changed to FINAL and Codex Stage 1 implementation instructed.
