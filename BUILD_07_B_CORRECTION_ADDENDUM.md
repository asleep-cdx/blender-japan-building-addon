# Build 07-B Correction Addendum — Closed Residential Stair Body

Date: 2026-09-21

Status: **AUTHORITATIVE CORRECTION — REQUIRED BEFORE BUILD 07-B CAN CONTINUE**

This addendum corrects the Build 07-B `STEPPED_CLOSED` geometry contract after Blender runtime visual review exposed a design error in the Stage 2 implementation.

Where this addendum conflicts with `BUILD_07_B_SPECIFICATION.md`, this addendum takes precedence.

In particular, this addendum supersedes the current intent and geometry assumptions in Specification §§17–23 and the Side Board/body contact statement in §30 to the extent that those sections allow the tread/riser backs or the stair interior to remain visually exposed.

The accepted Roadmap intent remains authoritative:

- Build 07-B `STEPPED_CLOSED` is a **closed residential stair body**.
- It is not a tread/riser assembly with exposed component backs.
- Build 07-F remains the place for open / support / sawtooth / stringer-style variants.

---

## 1. Reason for this correction

The Stage 2 implementation created a thin Underbody that directly followed the lower exterior of the existing Tread/Riser fragments.

That geometry could be:

- finite,
- manifold,
- closed as individual Mesh fragments,
- free of boundary edges,

while still producing the wrong finished stair appearance.

When Stage 3 Side Boards were added, Blender runtime inspection showed that:

- independent Tread undersides remained visible,
- Riser backs / internal voids could be seen from below,
- the stair did not read as a closed box-type residential stair.

This is a design/acceptance defect, not merely a shading issue.

Therefore:

> **Closed-fragment topology is necessary but not sufficient for `STEPPED_CLOSED` acceptance.**

---

## 2. Human-confirmed visual target

The finished Build 07-B stair must read as a normal **closed box-type residential stair**.

Viewed from below or obliquely below:

- Tread backs must not be directly visible.
- Riser backs must not be directly visible.
- Internal stair voids must not be visible.
- There must be no line of sight through the underside into the stair assembly.
- The visible underside must be a continuous stepped soffit made from horizontal underside faces and vertical connecting faces.

The important requirement is **closure**, not a particular nominal sheet thickness.

---

## 3. CLOSED means visually closed

For `STANDARD_RESIDENTIAL + STEPPED_CLOSED`, all of the following are required:

1. The visible body is closed from below.
2. The visible body is closed laterally.
3. The lower start is closed.
4. The upper termination is closed.
5. No exposed component back may substitute for the intended finished soffit.
6. No internal cavity may be visible through a gap between Tread, Riser, Underbody/closure geometry, or Side Board.

A result may not be accepted merely because:

- every individual fragment is a closed solid,
- `NONMANIFOLD == 0`,
- `BOUNDARY == 0`,
- all face areas are positive.

Those checks remain required geometry-health checks, but they do not prove the final residential body is visually closed.

---

## 4. The old Tread/Riser-following Underbody rule is superseded

The following concept is no longer the Build 07-B target:

> create a thin Underbody immediately against the accepted Tread/Riser lower exterior and treat that as the finished stepped closure.

The correction must not use “Tread/Riser underside plus a thin offset” as the visual definition of `STEPPED_CLOSED`.

Instead, the implementation must first define a **dedicated visible stepped closure silhouette** for the finished residential stair body.

The visible silhouette is the production target. Material thickness is secondary.

---

## 5. Canonical stepped closure silhouette

Use a dedicated analytical stepped closure profile, referred to in this addendum as `C_visible`.

`C_visible` must:

- be derived from canonical Stair dimensions / resolved `StairLayout`,
- never be reconstructed from the generated Mesh,
- form the visible lower boundary of the closed residential stair body,
- consist of horizontal underside segments joined by vertical segments,
- leave open space below the stair rather than filling the whole region down to the floor,
- meet the Side Board inner lower boundary without a visible gap when Side Boards are enabled,
- remain the same body-closure profile when either or both Side Boards are disabled.

### 5.1 Relationship to Side Board band depth

For Build 07-B correction, the stored `side_board_band_width_mm` value `b` is also the stepped closure-depth reference.

This is intentional so that the closed body and the decorative Side Board share one compatible lower stepped envelope.

Therefore, in corrected `STANDARD_RESIDENTIAL` geometry:

- `b` is used even when both Side Boards are OFF,
- the previous “`b < min(h,g)` only when a Side Board is enabled” exception is superseded,
- corrected Residential validation requires a finite positive `b` in the supported range needed by the shared closure profile.

The existing property name is retained for schema compatibility; this correction changes its geometric role.

### 5.2 Analytical source

The closure silhouette must be analytically consistent with the lower boundary generated from the ideal walking-step reference used for the Side Board:

- horizontal reference segments use the configured downward closure/band depth,
- vertical reference segments use the corresponding forward offset,
- adjacent translated lines meet analytically,
- the resulting lower envelope is clipped to the legal lower and upper Stair termination planes,
- cleanup and simple-polygon validation are applied.

The exact implementation may share pure helpers with Side Board profile construction, but Side Board enable flags must not control whether the body closure exists.

---

## 6. Underbody thickness semantics after correction

`underside_thickness_mm` remains a canonical field for compatibility and for giving the closure shell physical thickness.

Default remains:

`9.5 mm`

However:

> **`underside_thickness_mm` must not determine the visible closure depth or the position of `C_visible`.**

The visible stepped soffit is determined first.

Thickness is then applied **toward the enclosed stair interior**, so changing the thickness does not create a lower external notch, move the intended visible soffit downward, or reopen the body.

The former Stage 2 constraint:

`0 < u < min(h-t, r)`

was tied to the superseded Tread/Riser-following construction and is therefore no longer authoritative.

The correction implementation must replace it with validation appropriate to the new inward-thickness construction. At minimum, thickness must be finite and positive. Any additional supported-range constraint must be justified by the corrected geometry rather than copied from the superseded profile.

---

## 7. Full-width closure

The corrected stepped closure must span the complete stair body width:

`Y = [-w/2, +w/2]`

The body must remain visually closed for all four Side Board configurations:

- LEFT ON / RIGHT ON
- LEFT ON / RIGHT OFF
- LEFT OFF / RIGHT ON
- LEFT OFF / RIGHT OFF

Side Boards are not allowed to be required for body closure.

When a Side Board is enabled, the closure/body must meet its inner face without a visible gap into the stair interior.

---

## 8. Side Board role after correction

Side Board remains a decorative/finish component.

It is not the primary body-closure mechanism.

It may extend below the Tread/Riser assembly, but the inward-facing region must no longer reveal an open internal stair cavity.

The Specification §30 statement that a projecting Side Board inner face may simply remain exposed is superseded wherever that exposure reveals the stair interior.

The corrected relationship is:

- closed Stair body first,
- Side Board attached outside that closed body,
- no visible void between the two.

Side Board LEFT/RIGHT semantics remain uphill-relative.

---

## 9. Lower termination and first-step-specific rule

The body must not extend below `base_z = B`.

The lower start must be closed.

### 9.1 First-step bottom — mandatory visual rule

The **first step only** has an additional shape requirement:

> **The bottom of the first step must read as one flat horizontal face.**

In side orthographic view:

- no small local notch,
- no small raised patch,
- no intermediate step,
- no short mismatch in the first-step bottom silhouette

is allowed.

The first-step bottom must appear as one continuous horizontal lower boundary.

This requirement applies specifically to the first-step box/lowest-step region. It does **not** mean that the entire stair underside is placed at one common elevation.

After the first step, the underside continues upward as the intended stepped closed soffit.

The current Stage 2 lower-termination geometry that creates a small first-step bottom notch is superseded.

---

## 10. Upper termination

The corrected body must also close at the uphill end.

The existing no-extra-flight rules remain:

- no extra tread,
- no extra riser,
- no extension beyond the accepted final-riser outer limit unless a later specification explicitly changes it.

The corrected closure must not leave a visible cavity at the upper end.

The correction implementation must validate the final upper cap visually and numerically.

---

## 11. No solid mass to the floor

Correcting `STEPPED_CLOSED` does **not** mean filling the entire volume under the staircase down to the floor.

Required result:

- closed stepped soffit,
- open room/space remains below that soffit,
- stair interior above the soffit is hidden.

A giant floor-to-stair solid block is not the target.

---

## 12. Required visual acceptance gates

Build 07-B `STEPPED_CLOSED` may not be accepted again without explicit Blender 5.2 LTS visual inspection.

At minimum inspect:

1. side orthographic view,
2. oblique underside view,
3. close-up of the first-step bottom,
4. lower termination,
5. upper termination,
6. both Side Boards ON,
7. LEFT only,
8. RIGHT only,
9. both Side Boards OFF,
10. FORWARD,
11. REVERSE,
12. oblique Path.

The result must show:

- no exposed Tread backs from below,
- no exposed Riser backs from below,
- no visible internal void,
- continuous stepped horizontal/vertical soffit,
- no visible body/Side-Board gap,
- first-step bottom flat and notch-free,
- no geometry below `base_z`,
- no unintended exterior z-fighting.

If any of these visual gates fail, the build fails even if all topology tests pass.

---

## 13. Automated acceptance requirements

The correction tests must include, in addition to existing geometry-health tests:

- closure profile exists independently of Side Board enable flags,
- all four Side Board configurations use the same closed body profile,
- the first-step bottom has one horizontal visible lower segment and no local notch,
- no corrected closure vertex is below `B`,
- body closure spans full width,
- Side Board inner boundary and body closure have no analytical gap where they meet,
- thickness changes do not move the intended visible closure silhouette,
- BASIC Stair remains unaffected,
- FORWARD / REVERSE preserve canonical meaning,
- oblique Path uses resolved axes,
- save/reopen preserves corrected canonical state.

Topology checks remain required but are explicitly insufficient on their own.

---

## 14. Effect on previous Stage 2 acceptance

Build 07-B Stage 2 was previously marked ACCEPTED after automated tests and Blender runtime tests.

That acceptance is now **superseded for the `STEPPED_CLOSED` geometry** because the runtime acceptance criteria failed to detect the visual/design defect described here.

Historical Stage 2 evidence remains in the repository for traceability.

The corrected Stage 2 geometry must receive a new runtime-tested production revision and a new acceptance entry before Stage 3 can be accepted.

Stage 1 foundation acceptance is unaffected.

---

## 15. Effect on Stage 3 / PR #17

PR #17 was built on the superseded Stage 2 closure geometry.

It must not be merged as the accepted Stage 3 implementation.

Reusable Side Board / Material work may be ported or reapplied after the corrected Stage 2 body is accepted, but Stage 3 visual acceptance must be rerun against the corrected closed body.

---

## 16. Build 07-C guardrail

Build 07-C `SLOPED_CLOSED` inherits the same CLOSED invariant.

`SLOPED_CLOSED` means:

- a continuous sloped soffit,
- no exposed Tread backs,
- no exposed Riser backs,
- no visible stair interior,
- no floor-to-stair solid mass.

The difference from `STEPPED_CLOSED` is the visible underside shape, not whether the stair is closed.

Tread-front overhang / nosing / Bevel / Round remain Build 07-C work.

---

## 17. Build 07-F separation

Open/support stairs remain separate.

Build 07-F may intentionally expose Tread undersides or use:

- side support,
- sawtooth / stringer structures,
- center support,
- open variants,
- Riser OFF,
- Underside NONE.

Those possibilities do not weaken the Build 07-B / 07-C CLOSED contract.

---

## 18. Correction completion condition

This correction is complete only when:

- corrected Stage 2 geometry is implemented,
- Blender runtime visual gates pass,
- a new runtime-tested production revision is recorded,
- Stage 2 correction acceptance is documented,
- Stage 3 is then rebuilt/rebased/reapplied on that corrected foundation and independently accepted.

Until then:

- Build 07-B Stage 2 closure acceptance is superseded,
- Build 07-B Stage 3 is blocked,
- Build 07-B overall remains NOT ACCEPTED.


---

## 19. Pre-Stage-3 follow-up — Tread rear / Riser lower junction

This follow-up is a localized refinement to the accepted corrected Stage 2 residential geometry. It does **not** reopen the corrected closed-soffit contract and does not change BASIC Stair geometry.

### 19.1 Human-confirmed target

For `STANDARD_RESIDENTIAL`, the junction between each independent Tread and the next uphill Riser must read as a clean right-angle board junction.

The intended relationship is:

- do **not** extend the Riser downward below its current lower elevation,
- instead extend the preceding Tread uphill/rearward by exactly one `riser_thickness`,
- the Tread rear face and the uphill/rear face of the next Riser therefore lie on the same local-X plane,
- the resulting side silhouette/contact path must not contain the former small local step/notch between the Tread underside and the Riser rear face.

This is a Tread-rear extension, not a Riser-downward extension.

### 19.2 Residential Tread geometry

For independent Tread ordinal `j = 1 .. N-1`:

- existing lower/uphill start remains `x0 = (j-1)g`,
- Residential rear/uphill end becomes `x1 = jg + r`,
- top remains `B + jh`,
- bottom remains `B + jh - t`.

Thus, compared with BASIC, each Residential Tread extends uphill by exactly `r`.

For standard `r = 12 mm`, each Residential Tread therefore extends 12 mm farther uphill.

### 19.3 Riser geometry is unchanged

The existing Riser vertical placement and lower elevations remain authoritative.

In particular:

- Riser lower Z must **not** be lowered by one Tread thickness,
- the next Riser continues to start at the preceding Tread top elevation,
- the final Riser contract and upper `L+r` termination remain unchanged.

### 19.4 BASIC compatibility

`BASIC_TREAD_RISER` must retain the accepted Build 07-A Tread geometry.

Do not change the generic BASIC Tread generator in a way that changes legacy/basic output.

The preferred implementation is a Residential-specific Tread preparation path or an equally explicit mode-aware equivalent.

### 19.5 Underbody/contact profile follow-up

The corrected closed body remains mandatory.

The analytical inner/contact path must be updated so that, at each Tread/Riser rear junction:

- the Tread underside continues to the extended rear plane `x = jg + r`,
- the following vertical contact segment is on that same `x = jg + r` plane,
- no intermediate `x = jg` micro-step/notch remains solely because the old Tread ended before the Riser rear plane.

The visible corrected stepped soffit `C_visible` remains governed by the accepted closure-depth rules and must not be moved merely to implement this junction cleanup.

### 19.6 Acceptance requirements

Before Stage 3 starts, verify at minimum:

- Residential Treads end at `jg+r`,
- Riser lower Z values are unchanged,
- side orthographic close-up shows a clean right-angle Tread-rear / Riser junction,
- the former small local rear-junction notch is absent,
- first-step bottom remains flat and notch-free,
- corrected stepped soffit remains visually closed,
- lower `base_z` and upper `L+r` terminations remain unchanged,
- Mesh health remains valid,
- BASIC remains unchanged,
- Save/reopen, Regenerate and Repair still reproduce the corrected Residential result.

This follow-up must be accepted before Build 07-B Stage 3 is rebuilt on the corrected foundation.
