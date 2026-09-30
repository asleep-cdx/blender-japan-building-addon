# BUILD 07-E — DESIGN RATIONALE / GEOMETRY CONTRACT NOTES
## 日本住宅モデラー — Winder / 廻り段 + Arbitrary-angle Turn / Landing

> **Status: FINAL COMPANION / NON-AUTHORITY**  
> Date: 2026-09-30  
> Companion to `BUILD_07_E_SPECIFICATION.md`.
>
> This document explains **why** the 07-E requirements exist and records the design history. The single production implementation authority is the FINAL `BUILD_07_E_SPECIFICATION.md`. If wording here is less specific or differs from the Specification, the Specification wins.

---

# 1. Why 07-E exists

Build 07-E is the main turning-stair target for ordinary Japanese residential work and renovation visualization.

Typical use：

```text
existing old house
↓
structure / stair remains
↓
wall / floor / finish is renovated
↓
stair remains visible in presentation
↓
JHM must reproduce the existing stair
```

Therefore two goals have equal importance：

1. common Winder / 廻り段 geometry must be predictable;
2. an existing old-house stair must not become unmodelable merely because it is narrower, tighter or less regular than a present-day recommendation.

JHM is a Blender modeling aid, not a building-code compliance engine.

---

# 2. Reference-image policy

Reference images helped identify desired pattern families, but they are not implementation authority.

> **Codex must be able to implement 07-E from repository text alone.**

The final Specification defines geometry by vectors, intersections, event ownership, surface stations and face ownership. Thumbnails/icons are UI aids only.

---

# 3. Main design decisions

## 3.1 Equal-angle patterns use one general rule

User-facing 2 / 3 / 4-step Winder presets are generated from fractions, not separate meshes.

```text
f_j = j/n
```

Thus a 3-step 72° Turn becomes 24° × 3; `3段` is not internally hard-coded as `30°`.

## 3.2 BF is a separate pattern family

BF is asymmetric and therefore cannot be represented merely by an equal-step count.

JHM normalized production：

```text
BF_1 = [2/3] -> 60°,30° at an exact 90° Turn
BF_2 = [1/3] -> 30°,60° at an exact 90° Turn
```

In the FINAL schema-5 contract, `winder_pattern` is the single persistent authority; `step_count` and partition rule are derived from it. They remain meaningfully distinct concepts even though they are not independent saved authorities.

## 3.3 Existing 07-D identity is reused

A Turn is anchored by the accepted persistent interior `path_point_id`. 07-E does not create a second independent persistent Turn UUID merely to duplicate the same identity.

## 3.4 Arbitrary-angle Landing belongs in 07-E

Existing houses may turn at 47°, 63°, 82° and other angles. Therefore angle comes from Path geometry. Shift 15° remains only a drawing convenience.

## 3.5 Production U remains two Turns

```text
P0 -> P1 -> P2 -> P3
       T1    T2
```

Overall 180° U geometry is a combination of two persistent Turn anchors. Per-Turn patterns such as `EQUAL_2 + EQUAL_3` or `BF_1 + BF_2` are supported. A derived Compact-U group does not replace the two canonical Turn anchors.

## 3.6 Compact U needs a zero-middle-run classification

Many residential switchbacks have no ordinary straight tread between the two turning regions. Treating every middle Path segment as a normal Flight would falsely reject such stairs.

The `R_mid` classification exists to distinguish separated U, compact U and real overlap without using a legal-like width gate.

## 3.7 RiseEvents are explicit

Landing and Winder surfaces participate in the vertical sequence rather than being plan-only decoration.

```text
S + L + W + 1 = N
```

This avoids double-counting at component boundaries and makes schema-4 -> schema-5 migration reviewable.

## 3.8 Nominal cells and physical finish solids are separate

A nominal Winder partition must cover the Turn envelope without positive-area overlap. Physical treads may intentionally overlap in XY projection because nosing and rear support exist at different Z ranges.

This distinction prevents normal nosing geometry from being incorrectly rejected as a plan-overlap error.

---

# 4. Why the old-house width guard is strict

A renovation presentation may need to reproduce an existing stair without rebuilding its structure. Therefore 07-E prohibits hidden legal-like minimum gates in：

- geometry validation;
- RNA property ranges;
- UI clamping;
- presets.

Required regression samples include 900 / 800 / 750 / 700 / 650mm, but 650mm is **not** a production lower bound.

A geometry-valid narrow stair may warn; it must not be rejected merely for being narrow.

---

# 5. Why SLOPED_CLOSED required extra design review

A Winder keeps rising while its plan direction changes. A Landing-style horizontal underside plateau is therefore not the intended result.

The first draft used a singular pivot-spine idea. Third-party review found two concrete problems：

- an EQUAL_3 center cell could omit the outer corner `O`;
- triangulating a changing-Z point pivot could create an unintended large vertical triangle.

The accepted FINAL solution therefore：

1. preserves every outer-chain vertex, including `Q1 -> O -> Q2`;
2. inserts geometry-only stations without adding RiseEvents;
3. uses a finite pivot-relief core derived from physical riser thickness and numerical epsilon;
4. creates only a localized high-side pivot closure;
5. forces all faces sharing an edge to share the same subdivision points, preventing T-junctions;
6. keeps this construction limited to schema-5 Winder SLOPED_CLOSED so accepted Straight/Landing geometry is not rewritten.

This is why the final underbody contract is more explicit than the original planning note.

---

# 6. Why STEPPED_CLOSED has a Winder-specific formula

Accepted 07-C Straight geometry contains straight-profile-specific horizontal offsets and terminal behavior. Reusing that exact XZ algorithm on a radial/turning footprint would be artificial.

The FINAL Winder rule instead interprets the same `closed_body_depth` meaning at cell level：

```text
Z_soffit_j = max(base_z, tread_top_j - closed_body_depth)
```

This is a schema-5 Winder extension, not a replacement for accepted 07-C Straight generation.

---

# 7. Why Compact-U Side Board is one shared family

Generating two independent coincident center boards and then rejecting their collision would make Compact U unreliable, especially in narrow existing houses.

The FINAL contract therefore solves a seam-local `(s,z)` profile first, then creates one `SHARED_CENTER_BOARD` family. It may contain multiple closed components if required.

Important design choices：

- lower edge comes from `underside_mode`;
- upper edge comes from `side_board_mode` and walking/reveal authority;
- point-only profile contact is not welded;
- shared thickness is centered on the center seam;
- only actual 3D overlap with TREAD/RISER/UNDERBODY is trimmed;
- ordinary/shared board ends use a deterministic butt joint, not an implicit miter or transition invented by the implementer.

---

# 8. Why Side Board upper/lower modes remain independent

Accepted 07-C already established：

```text
underside_mode  -> lower Side Board boundary
side_board_mode -> upper / visible Side Board boundary
```

07-E preserves that architecture. A SLOPED board upper edge is derived from walking-surface/reveal progression; it is not simply copied from the SLOPED underbody height.

---

# 9. Why Stage order is deliberate

```text
Stage 1
canonical Turn / RiseEvent / 90° EQUAL L Winder
↓
Stage 2
BF / U / Compact U / arbitrary-angle
↓
Stage 3
STEPPED_CLOSED / SLOPED_CLOSED / Side Board
↓
Stage 4
lifecycle / regression / practical acceptance
```

07-D showed that debugging plan geometry, underside and Side Board simultaneously creates long correction loops. 07-E deliberately accepts the top/vertical foundation first and adds finish geometry afterward.

---

# 10. Review history

07-E received three repository-based third-party reviews：

```text
Review 1: REVISE GEOMETRY CONTRACT
Review 2: REVISE GEOMETRY CONTRACT AGAIN
Review 3: ACCEPT WITH CLARIFICATIONS
```

Those reviews led to explicit rules for：

- deterministic straight allocation;
- RiseEvent ownership;
- schema migration;
- nominal vs physical geometry;
- outer-corner preservation;
- finite pivot relief;
- Compact-U shared SLOPED height;
- Winder STEPPED_CLOSED Z;
- Side Board shared-center profile / trim / butt-joint rules;
- full-finish narrow-width regression fixtures.

Historical review/revision documents remain in the repository for auditability. They are not separate implementation authorities after this FINAL Specification.

---

# 11. Intentional non-scope

07-E does not absorb：

- future project default width change (for example 900 -> 750mm);
- broad Stair panel compacting/collapsible UI redesign;
- Riser OFF / open/support variants (07-F);
- optional detail expansion (07-G);
- Floor/Room dependency (08);
- Door/Window integration (09);
- building-code compliance judgment.

Keeping these separate reduces regression risk while 07-E completes the core turning-stair geometry.
