# BUILD 07-E — DESIGN RATIONALE / GEOMETRY CONTRACT NOTES
## 日本住宅モデラー — Winder / 廻り段 + Arbitrary-angle Turn / Landing

> **Status: DRAFT / REVIEW COMPANION**  
> Date: 2026-09-30  
> Companion to `BUILD_07_E_SPECIFICATION.md`. This document records **why** the 07-E requirements exist and defines geometry rules in text / formula form so that implementation and third-party review do not depend on reference images. Before `BUILD_07_E_SPECIFICATION.md` is promoted to `FINAL / IMPLEMENTATION AUTHORITY`, the normative rules in this document must be merged into or explicitly referenced by the final Specification.

---

# 1. Why this document exists

Build 07-E is the main production target for ordinary Japanese residential turning stairs. It also has to serve renovation visualization of older houses, where the existing stair may be narrower, tighter, steeper, or less regular than a present-day new-build stair.

Two requirements therefore have equal importance:

1. Generate common residential Winder / 廻り段 geometry predictably.
2. Do **not** reject an existing old-house stair merely because its dimensions do not satisfy a current legal / recommended dimension.

The project is a Blender modeling aid for renovation visualization, not a building-code compliance engine.

The intended workflow is often:

```text
existing old house
↓
structure / stair remains in place
↓
wall / floor / finish is renovated
↓
existing stair is still visible in the presentation
↓
JHM must be able to model that stair if its geometry is mathematically valid
```

This is the reason the 07-E validation policy separates **legal / recommended dimensions** from **geometry validity**.

---

# 2. Reference-image policy

Reference images supplied during design discussion are useful for identifying desired residential pattern families, but they are **not implementation authority**.

Normative rule:

> **Codex implementation must be possible from repository text alone. No production algorithm may require looking at an external or chat-attached image to infer geometry.**

Therefore:

- the names `2段廻り`, `3段廻り`, `4段廻り`, `BF-1`, `BF-2` are user-facing pattern identities;
- exact geometry is defined by normalized coordinates / vectors / partition fractions below;
- no legal meaning or expansion of the abbreviation `BF` is assumed by JHM;
- if a reference image and the final text contract disagree, the final text contract wins;
- thumbnails / icons are UI aids only and never canonical geometry authority.

---

# 3. Design rationale summary

## 3.1 Why 2 / 3 / 4 equal-angle patterns

These are compact, understandable residential presets and can be generated from one general rule:

```text
partition fraction f_j = j / n
j = 1 ... n-1
```

This avoids separate hand-coded geometry for `2-step`, `3-step`, and `4-step` cases.

## 3.2 Why BF-1 / BF-2 are separate rules

The desired BF families deliberately use an asymmetric angular split rather than equal-angle subdivision. Treating them as a special `step_count` would make the model ambiguous.

Therefore:

```text
winder_step_count
!=
winder_partition_rule
```

and the canonical model keeps both concepts separate.

## 3.3 Why arbitrary-angle Landing belongs in 07-E

07-D accepted only exact ±90° production Landing turns. Renovation work can include houses whose walls / corridors / existing stairs turn by an oblique angle that is not 45°, 60°, or any other fixed preset.

The angle must therefore be derived from Path geometry instead of selected from a hard-coded angle table.

## 3.4 Why Shift 15° is not a production restriction

Shift 15° is an input convenience inherited from 07-D. It helps draw common angles quickly but must not make a 63° or 82° Path invalid.

```text
Shift 15° = interaction aid
Turn angle = derived geometry
```

## 3.5 Why Compact U needs a specific resolver

A common 180° residential Winder can have no ordinary straight tread between its two quarter-turn regions. Treating every Path segment as a normal Flight would incorrectly reject this as a "short middle Flight".

The two existing 07-D Turn anchors are preserved, but they may resolve as one derived `Composite U Winder Group` when their turn envelopes meet with zero ordinary middle run.

## 3.6 Why Winder SLOPED_CLOSED is not a Landing underside

A Landing has a horizontal walking surface and may legitimately have a horizontal underside transition. A Winder continues to rise through the turn. Its sloped closed underside should therefore keep progressing in height through the turn rather than inserting a horizontal Landing plateau.

---

# 4. Common 2D Turn frame

All 07-E Landing / Winder plan geometry must start from one generalized Turn frame.

For an interior canonical Path point `T = P_i`:

```text
P_prev = P_(i-1)
P_next = P_(i+1)

a = normalize(T - P_prev)      # incoming direction toward T
b = normalize(P_next - T)      # outgoing direction away from T
```

Signed turn angle:

```text
theta = atan2(cross2(a, b), dot(a, b))
```

where `theta > 0` is a left turn and `theta < 0` is a right turn under the project XY convention.

Define:

```text
s = sign(theta)
left_normal(d) = (-d.y, d.x)
inside_normal_in  = s * left_normal(a)
inside_normal_out = s * left_normal(b)
```

For stair width `w`, the four corridor offset lines are:

```text
incoming inside : T + (w/2) * inside_normal_in  + lambda * a
incoming outside: T - (w/2) * inside_normal_in  + lambda * a

outgoing inside : T + (w/2) * inside_normal_out + mu * b
outgoing outside: T - (w/2) * inside_normal_out + mu * b
```

Resolve:

```text
I = intersection(incoming inside,  outgoing inside)   # inner pivot / inside corner
O = intersection(incoming outside, outgoing outside) # outer miter corner
```

Cross-section outer endpoints through the inner pivot are:

```text
E_in  = I - w * inside_normal_in
E_out = I - w * inside_normal_out
```

The normalized Turn envelope is the simple polygon whose boundary follows:

```text
I -> E_in -> O -> E_out -> I
```

with winding normalized consistently by the geometry helper.

This same envelope is used by:

- arbitrary-angle Landing;
- equal-angle Winder;
- 90° BF Winder.

For an exact 90° equal-width turn the envelope resolves to the accepted nominal `w × w` 07-D Landing square.

### Derived cutback diagnostic

For a symmetric equal-width turn, the centerline cutback magnitude is:

```text
d = (w/2) * tan(abs(theta)/2)
```

The production implementation may compute cutbacks from the actual resolved cross-sections instead of relying on this closed-form expression, but automated tests should verify equivalence for ordinary cases.

The formula is **geometry**, not a legal minimum.

---

# 5. Numerical singularity rule

07-E must not impose a building-code angle table.

It may reject only numerically / geometrically singular Turn cases, for example:

- incoming or outgoing segment has near-zero length;
- `theta` is so close to 0° that a distinct Turn cell cannot be resolved robustly;
- `theta` is so close to ±180° that a single-Turn miter is numerically singular;
- required line intersections are non-finite;
- cutback consumes more Path length than is geometrically available.

Any epsilon used here must be documented as a **numerical epsilon**, not a residential-code threshold.

A 45°, 63°, 82°, 105°, etc. Turn is not rejected because it is not a standard preset angle.

---

# 6. Equal-angle Winder — exact construction

Let the Turn envelope from section 4 be valid.

Define entry and exit rays from the inner pivot:

```text
r0 = normalize(E_in  - I)
r1 = normalize(E_out - I)
```

The signed angular sweep from `r0` to `r1` is the resolved Turn sweep.

For `n` Winder treads:

```text
fractions = [j/n for j in 1 ... n-1]
```

For each fraction `f`:

```text
r_f = rotate(r0, f * theta)
```

where the rotation uses the signed Turn direction.

Create a ray:

```text
R_f(t) = I + t * r_f,  t > 0
```

Intersect that ray with the **outer chain**:

```text
E_in -> O -> E_out
```

Select the nearest valid positive intersection. The resulting segment:

```text
I -> Q_f
```

is a Winder division boundary.

The Turn envelope is then split in canonical entry-to-exit order into `n` simple tread polygons.

Production examples:

```text
EQUAL_2 fractions = [1/2]
EQUAL_3 fractions = [1/3, 2/3]
EQUAL_4 fractions = [1/4, 1/2, 3/4]
```

For exact 90° these produce:

```text
2 steps = 45° + 45°
3 steps = 30° + 30° + 30°
4 steps = 22.5° × 4
```

For a 72° 3-step arbitrary-angle Winder the same rule produces `24° × 3`; no special 72° generator exists.

---

# 7. JHM normalized BF-1 / BF-2 — exact construction

The project intentionally defines BF-1 / BF-2 as **JHM normalized pattern rules**. These definitions are chosen to reproduce the desired asymmetric residential pattern family. They do not claim to be a legal standard or industry-standard meaning of the label `BF`.

BF-1 / BF-2 production support in 07-E is limited to an approximately / exactly 90° single Turn. If the Turn is outside the 90° production tolerance, the BF pattern is unavailable and the user must use `EQUAL_ANGLE` or `LANDING`.

For a canonical 90° Turn, use the same Turn envelope and entry-to-exit sweep as section 6.

## 7.1 BF-1

One internal division boundary:

```text
fraction = 2/3
```

Therefore canonical entry-to-exit angular spans are:

```text
60° , 30°
```

Construction is exactly the same ray / outer-chain intersection algorithm as equal-angle Winder; only the fraction list differs.

```text
BF_1 fractions = [2/3]
```

## 7.2 BF-2

One internal division boundary:

```text
fraction = 1/3
```

Therefore canonical entry-to-exit angular spans are:

```text
30° , 60°
```

```text
BF_2 fractions = [1/3]
```

## 7.3 Left / right Turn rule

Do not write separate left-turn and right-turn meshes.

Use the same fractions with signed `theta`:

```text
left turn  -> positive sweep
right turn -> negative sweep
```

This mirrors the plan naturally.

## 7.4 Reverse ascent rule

`REVERSE` does **not** rewrite canonical Path order and does not change `BF_1 <-> BF_2` identity.

Physical plan subdivision remains fixed. Only elevation / ascent traversal reverses.

If the user wants the opposite asymmetric physical partition on the same canonical Path, they explicitly choose the other pattern.

---

# 8. 180° / U reference-family mapping

JHM canonical authority remains **per Turn**, not an overall 180° preset mesh.

For a compact U with two consecutive approximately 90° Turns, the following convenience interpretation reproduces the two symmetric asymmetric families discussed during design:

```text
U BF-family 1:
Turn 1 = BF_1
Turn 2 = BF_2
aggregate angular sequence = 60°, 30°, 30°, 60°

U BF-family 2:
Turn 1 = BF_2
Turn 2 = BF_1
aggregate angular sequence = 30°, 60°, 60°, 30°
```

The first sequence corresponds to the design example in which the two central Winder sectors are 30° each and the two outside sectors are 60° each.

These may be offered later as UI convenience aliases, but canonical storage remains the individual Turn pattern assignments.

Other combinations remain possible, for example:

```text
Turn 1 = BF_1
Turn 2 = EQUAL_3
```

No Cartesian list of all U presets is stored.

---

# 9. Compact U — exact derived rule

Consider two consecutive Turn anchors:

```text
T1 = P_i
T2 = P_(i+1)
```

with middle Path segment:

```text
m = normalize(T2 - T1)
L_mid = length(T2 - T1)
```

Resolve each Turn envelope independently from the same stair width.

From Turn 1, derive the distance from `T1` along `m` to its exit cross-section:

```text
d1 = exit_cutback_on_middle_segment
```

From Turn 2, derive the distance backward from `T2` along `m` to its entry cross-section:

```text
d2 = entry_cutback_on_middle_segment
```

Define:

```text
R_mid = L_mid - d1 - d2
```

Classification:

```text
R_mid > +eps_length
    = SEPARATED_U
    = ordinary positive middle straight run remains

abs(R_mid) <= eps_length
    = COMPACT_U
    = zero ordinary middle straight run

R_mid < -eps_length
    = INVALID_OVERLAP
    = Turn envelopes require positive-area overlap
```

`eps_length` is a numerical tolerance only.

For two exact 90° equal-width Turns:

```text
d1 = w/2
d2 = w/2
COMPACT_U when L_mid ~= w
```

This is important for old houses because the rule scales with the actual stair width:

```text
w = 900 mm -> compact middle centerline separation ~= 900 mm
w = 750 mm -> compact middle centerline separation ~= 750 mm
w = 650 mm -> compact middle centerline separation ~= 650 mm
```

There is no hard-coded `900 mm` compact-U requirement.

## 9.1 COMPACT_U invariants

When `COMPACT_U`:

- the two Turn envelopes must meet at the same transition cross-section within tolerance;
- they must not have positive-area overlap;
- there must be no walking-surface gap between them;
- the middle Path segment remains canonical and keeps both point IDs / Turn IDs;
- the middle segment owns **zero ordinary straight tread events**;
- a derived `Composite U Winder Group` may be used for geometry generation only;
- the two canonical Turns must not be replaced by one fake persistent Turn.

## 9.2 SEPARATED_U

When `R_mid > eps_length`, the residual run is an ordinary straight region between the two Turn envelopes.

Whether that run can support its assigned straight tread events is validated from its actual length and allocation. Do not silently stretch either Winder to hide an invalid allocation.

## 9.3 INVALID_OVERLAP

When `R_mid < -eps_length`, reject because the two required Turn envelopes physically overlap for the chosen Path / width / angle. This is a geometry error, **not** a legal-width error.

Reducing stair width may legitimately make the same Path valid because the envelopes become smaller.

---

# 10. Arbitrary-angle Landing — exact polygon rule

Arbitrary-angle `LANDING` uses the same Turn envelope from section 4.

Walking-surface polygon:

```text
Landing polygon = [I, E_in, O, E_out]
```

with normalized winding.

Entry interface:

```text
I -> E_in
```

Exit interface:

```text
I -> E_out
```

Outer visible corner chain:

```text
E_in -> O -> E_out
```

Properties:

- exact 90° / equal width resolves to the accepted nominal `w × w` 07-D Landing footprint;
- arbitrary angle resolves from corridor geometry, not from angle-specific templates;
- a 47°, 63°, 82°, etc. Landing uses the same algorithm;
- Landing top Z remains constant across the polygon and follows 07-D cumulative-rise semantics;
- Material remains `TREAD` for walking surface and `UNDERSIDE` for closed underside/body;
- if required cutbacks consume more adjacent Path length than available, the candidate is rejected atomically.

There is no separate `45° Landing generator`, `60° Landing generator`, etc.

---

# 11. Arbitrary-angle Winder — exact reuse rule

An arbitrary-angle Winder uses:

```text
same generalized Turn envelope
+
EQUAL_ANGLE partition only (07-E production minimum)
```

Therefore:

```text
Turn theta = 63°
step count = 3
partition fractions = [1/3, 2/3]
```

and the rays are generated by `theta/3` angular increments.

BF-1 / BF-2 are **not** generalized to arbitrary theta in 07-E.

---

# 12. Exact rise-event ownership

07-E must not infer vertical ownership from visual mesh fragments. Resolve rise events before geometry generation.

Define one `RiseEvent` as one vertical increment:

```text
h = floor_to_floor / overall_riser_count
```

Every physical rise event has exactly one destination owner:

```text
STRAIGHT_TREAD
WINDER_TREAD
UPPER_ARRIVAL
```

Rules:

1. Every independent straight tread owns the rise event immediately before that tread in ascent order.
2. Every Winder tread owns exactly one rise event immediately before that Winder tread.
3. The upper floor arrival owns exactly one final rise event.
4. No event may be owned by both a Flight and a Winder.
5. No Winder tread is decorative / plan-only; it participates in the vertical sequence.

Let:

```text
S = total independent straight-tread events
W = total Winder tread count across all Turns
N = overall riser_count
```

Then:

```text
S + W + 1 = N
```

where `+1` is the final upper-arrival rise.

Equivalent component form:

```text
sum(straight_flight_rise_events)
+
sum(winder_step_count)
=
N
```

provided the final Flight rise-event count includes the `UPPER_ARRIVAL` event.

### Per straight region

For a non-final straight region:

```text
straight_flight_rise_events = number of independent straight treads on that region
```

For the final straight region:

```text
straight_flight_rise_events
= number of independent straight treads on that region + 1 upper-arrival event
```

A zero-length Compact-U middle region owns:

```text
0 straight tread events
0 rise events
```

This ownership rule is the authority for tread elevations and riser boards.

---

# 13. AUTO distribution under schema 5

Resolve in this order:

```text
1. overall N
2. all Winder patterns and W = sum(winder_step_count)
3. reserve 1 final UPPER_ARRIVAL event
4. straight independent-tread budget = N - W - 1
5. resolve effective positive straight runs
6. deterministic integer apportionment across those runs
7. add final UPPER_ARRIVAL event to final Flight ownership
8. validate every going / turn / body / board candidate
9. atomic commit
```

A positive straight run should receive enough tread events to cover that run according to the accepted geometric validation. A zero effective run receives zero straight tread events.

If `N - W - 1 < 0`, reject.

The allocator must be deterministic; ties are resolved by canonical Path / component order.

---

# 14. MANUAL migration rule

Existing schema-4 `MANUAL` allocation semantics must not be silently reinterpreted when a Landing is changed to a Winder.

Because adding Winder tread events changes vertical ownership, preserving every old schema-4 Flight count while also adding Winder counts would double-count rises.

Therefore production rule:

> When a schema-4 Stair is in `MANUAL` mode, `LANDING -> WINDER` conversion must **not** silently rewrite the user counts.

07-E initial production UX may use the conservative rule:

```text
schema-4 MANUAL + request LANDING -> WINDER
↓
reject transaction with clear message
↓
user explicitly switches to AUTO
↓
convert to schema 5 Winder
↓
user may then switch schema-5 result to MANUAL and edit explicit component allocations
```

A future dedicated MANUAL migration UI may relax this, but 07-E must not invent an unreviewed redistribution behind the user's back.

Existing schema-4 MANUAL Landing stairs remain fully supported and unchanged as long as their Turn mode remains `LANDING`.

---

# 15. Old-house / narrow-stair hard guardrail

This is a project requirement, not an optional preference.

## 15.1 Values that must NOT be core reject thresholds

`validate_winder_geometry()` or equivalent production validators must not reject solely because:

```text
stair_width < 900 mm
stair_width < 800 mm
stair_width < 750 mm
```

Nor may they hard-code the design-reference dimensions such as:

```text
300 mm
150 mm
85 mm
```

as universal generation minima.

Do not introduce hidden equivalents such as:

```text
MIN_LEGAL_STAIR_WIDTH = 750
MIN_LEGAL_WINDER_TREAD = ...
```

into the geometry gate.

## 15.2 What may reject

Reject when the chosen Path / width / turn / pattern is mathematically or mesh-invalid, including:

- Turn envelope non-finite or non-positive area;
- Winder polygon self-intersection;
- positive-area overlap between adjacent Winder treads;
- required walking-surface gap;
- zero / near-zero edge or polygon beyond numerical epsilon;
- partition ray fails to hit the required outer chain;
- Turn envelopes physically overlap in an unsupported way;
- Path self-intersection;
- required cutback exceeds available adjacent segment geometry;
- closed underside / Side Board cannot be produced without critical invalid geometry.

## 15.3 What should warn but allow

If geometry is valid, the following may produce a non-blocking advisory warning but must not automatically cancel generation:

- very narrow stair width;
- very narrow inner tread area;
- unusually steep / tight old-house-like configuration;
- dimensions that may not resemble a present-day new-build recommendation.

Warning text must not claim legal compliance or non-compliance.

## 15.4 Required tests

Automated / runtime representative tests must include at least:

```text
width 900 mm
width 800 mm
width 750 mm
width 700 mm
width 650 mm
```

for one or more geometry-valid 90° Winder cases.

PASS condition:

> Width alone does not cause rejection. If a narrower case fails, evidence must show an actual geometry failure, not a code-like minimum threshold.

This test exists specifically to protect renovation modeling of older houses.

---

# 16. SLOPED_CLOSED Winder rationale and contract

A Winder changes plan direction while continuing vertical progression.

Therefore 07-E `SLOPED_CLOSED` must not insert a horizontal Landing soffit merely because the plan turns.

Authority:

```text
lower straight soffit boundary
↓
ordered Winder lower-surface stations
↓
upper straight soffit boundary
```

Requirements:

- position continuity (`C0`) at both joins;
- monotonic elevation progression in ascent order except where existing accepted body-thickness geometry requires a local closure cap;
- no horizontal Landing plateau through the Winder turn;
- piecewise planar / triangulated surface is allowed;
- tangent continuity (`C1`) is not required in 07-E;
- no open cavity / giant filler prism / duplicate positive-volume body;
- same width / Path / rise-event authority as the top geometry.

This is deliberately implemented after Winder top-plan acceptance so plan errors and soffit errors are not debugged simultaneously.

---

# 17. Side Board rationale

The Winder Side Board should be derived from the resolved inside / outside Turn-envelope boundaries and the ordered elevation sequence.

Do not create a visually plausible but disconnected "turn board patch" whose endpoints are unrelated to the Flight board boundaries.

Requirements:

- stable left/right physical side across a Turn;
- no side swap after Reverse;
- outer board follows the outer Turn chain;
- inner board may be segmented / trimmed around a tight pivot;
- Flight ↔ Winder joins share exact derived boundary positions;
- compact U center boards must be checked for collision / overlap;
- board geometry is derived, not canonical authority.

---

# 18. Alternatives considered and intentionally rejected

The following approaches are **not** the 07-E design:

1. **Hard-code one mesh for each pattern**  
   Rejected because arbitrary-angle Winder and future patterns would duplicate logic.

2. **`3段廻り = 30°` as the internal model**  
   Rejected because `3 steps` and `partition rule` are different concepts and arbitrary theta must work.

3. **Reject stair widths below a present-day code-like number**  
   Rejected because old existing houses are a primary renovation use case.

4. **Treat every U middle segment as a normal Flight**  
   Rejected because compact U Winder legitimately has zero ordinary middle run.

5. **Replace the two U Turn IDs with one fake persistent 180° Turn**  
   Rejected because it would destroy the accepted 07-D Multi-point / point-ID architecture and make per-Turn pattern combinations difficult.

6. **Create separate 45° / 60° / 90° Landing generators**  
   Rejected because angle-specific code would not support arbitrary existing-house geometry.

7. **Use reference images as coding instructions**  
   Rejected because image interpretation is ambiguous and not durable repository authority.

8. **Solve top geometry, underside, and Side Board simultaneously**  
   Rejected because 07-D showed that combined debugging makes turn-finishing corrections expensive and difficult to isolate.

---

# 19. Why the 07-E Stage order is deliberate

```text
Stage 1
canonical Turn + 90° equal-angle L Winder
↓
Stage 2
BF + U / Compact U + arbitrary-angle Landing / Winder
↓
Stage 3
closed underside + Side Board
↓
Stage 4
lifecycle + regression + practical acceptance
```

Reasoning:

- Stage 1 proves the generalized envelope / partition model before special patterns.
- Stage 2 completes plan geometry and vertical ownership before finish surfaces.
- Stage 3 only starts after top-plan geometry is accepted in Blender.
- Stage 4 verifies that schema-5 complexity has not broken the accepted lifecycle or unrelated Wall / Finish systems.

---

# 20. Third-party review checklist

A third-party reviewer should read at least:

```text
ROADMAP.md
BUILD_07_D_SPECIFICATION.md
BUILD_07_D_ACCEPTANCE_RECORD.md
BUILD_07_E_SPECIFICATION.md
BUILD_07_E_DESIGN_RATIONALE.md
DEVELOPMENT_WORKFLOW.md
```

Review questions:

- Does 07-E preserve accepted schema-1/2/3/4 behavior without silent migration?
- Is the generalized Turn-envelope construction mathematically consistent for left/right and oblique turns?
- Does exact 90° Landing reduce to the accepted 07-D `w × w` case?
- Are `winder_step_count` and `winder_partition_rule` separated cleanly?
- Are BF-1 / BF-2 now reproducible from text alone?
- Is the BF left/right / Reverse behavior unambiguous?
- Does Compact U preserve both canonical Turn IDs while allowing zero ordinary middle run?
- Is `R_mid` classification sufficient, or is another supported compact topology needed?
- Is arbitrary-angle Landing defined without angle-specific special cases?
- Is rise-event ownership complete and free of double counting?
- Is the conservative schema-4 MANUAL -> WINDER rule preferable to an automatic migration?
- Could any validator accidentally behave as a hidden building-code gate?
- Do width 700 / 650 mm valid cases remain modelable?
- Are numerical epsilons clearly distinguished from legal minima?
- Is `SLOPED_CLOSED` continuity defined strongly enough to avoid a Landing-like horizontal plateau?
- Are Side Board ownership / joins derivable from the same Turn geometry rather than patched afterward?
- Is Stage 1/2/3 separation sufficient to avoid repeating the 07-D underside-debugging problem?
- Are any specification requirements impossible or needlessly expensive relative to the renovation-visualization goal?
- Are there contradictions between Roadmap, 07-D accepted contracts, and 07-E proposed contracts?

The reviewer should be free to recommend:

```text
ACCEPT AS WRITTEN
ACCEPT WITH CLARIFICATIONS
REVISE GEOMETRY CONTRACT
REVISE STAGE SCOPE
```

but should identify the exact conflicting section / invariant rather than relying on a visual preference alone.

---

# 21. Items that remain outside 07-E

Do not mix the following future work into 07-E implementation unless a direct blocker is discovered:

- default stair width change from 900 mm to a future project default such as 750 mm;
- general Stair-panel compacting / collapsible UI redesign;
- broad UX cleanup unrelated to Winder pattern selection;
- Riser OFF / Underside NONE / support variants (07-F);
- optional tread-detail expansion (07-G);
- Floor / Room dependency (08);
- Door / Window integration (09).

The current default may remain 900 mm during 07-E. The critical contract is that changing the width to a narrower **geometry-valid** value does not trigger a code-like rejection.

---

# 22. Merge-to-FINAL rule

Before `BUILD_07_E_SPECIFICATION.md` becomes `FINAL / IMPLEMENTATION AUTHORITY`:

1. Merge or explicitly normatively reference the exact Turn-frame, equal-angle, BF, Compact-U, arbitrary-Landing, rise-ownership, and old-house guardrail rules from this document.
2. Remove corresponding `DRAFT OPEN ITEM` wording that has been resolved here.
3. Verify the final Specification can be implemented without any reference image.
4. Verify all legal-sounding numeric dimensions are advisory / reference-only unless they are explicitly a mathematical epsilon.
5. Run third-party review against the repository documents before issuing the first Codex implementation instruction.

No production Codex implementation should start while the final Specification still requires image interpretation.