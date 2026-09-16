# BUILD 06-B SPECIFICATION

## 日本住宅モデラー — Production Baseboard / Profile & Exclusion System

- Target: Blender 5.2 LTS
- Repository: `asleep-cdx/blender-japan-building-addon`
- Required base branch: `main`
- Required base commit: `3aa8b87cf9e62b3ba2ee484b5f464489365fdf3d`
- Base message: `Merge pull request #3 from asleep-cdx/codex/implement-build-06-a-post-acceptance-patch`
- Governing predecessor: `BUILD_06_A_SPECIFICATION.md`
- Governing correction record: `BUILD_06_A_CORRECTION_ADDENDUM.md`
- Governing acceptance record: `BUILD_06_A_ACCEPTANCE_RECORD.md`
- Build position: first production Baseboard build on top of the accepted Build 06-A Finish attachment foundation
- Primary feature: production-usable Baseboard generation, editing, exclusion and Profile handling
- Future consumer: Build 06-C Crown Moulding may reuse Profile-definition and Profile-snapshot infrastructure where appropriate

---

# 1. Purpose

Build 06-B converts the accepted Build 06-A Finish attachment foundation into a production-usable baseboard system.

Build 06-A already established the canonical attachment relationship:

```text
canonical Wall data + Wall topology
        +
FinishRun / FinishSpan canonical attachment data
        +
vertical reference
        ↓
resolved wall-surface path
        ↓
derived managed Finish geometry
```

Build 06-B extends this into:

```text
canonical Wall data + topology
        +
FinishRun / FinishSpan
        +
Profile identity / revision / actual Run parameters
        +
FinishExclusion records
        ↓
validated visible ranges
        ↓
baseboard join / end resolution
        ↓
derived managed Curve / Mesh representation
```

The generated Curve or Mesh remains derived data.

The source of truth MUST remain canonical Wall / Finish / Profile / Exclusion data.

---

# 2. Product intent

The add-on is a renovation-perspective production accelerator.

The target workflow is:

```text
managed dimension-based architectural generation
        ↓
fast room/base modeling
        ↓
managed edits while useful
        ↓
explicit conversion to ordinary Blender geometry
        ↓
free material / UV / Edit Mode / rendering work
```

Build 06-B is not a BIM system and must not expand into full room interpretation or construction-document semantics.

The feature should be practical for modeling the baseboard of a real room while preserving the explicit, safe, partially automated philosophy established by Build 05-B and Build 06-A.

---

# 3. Required accepted foundation

Build 06-B MUST preserve all accepted Build 05-B and Build 06-A invariants.

At minimum, the implementation must continue to preserve:

```text
Wall centerline is canonical.
Wall length is derived, not independently stored.
One managed Wall = one Blender Object.
Wall Mesh is derived.
Finish geometry is derived.
Wall identity uses persistent wall_id.
Finish identity uses persistent finish_id.
Wall references use pointer + expected persistent ID validation.
LEFT / RIGHT are canonical relative to Wall START -> END.
Finish traversal is separate from Wall LEFT / RIGHT.
FinishRun order is explicit.
FinishSpan supports partial intervals.
Wall split/delete dependency remapping remains canonical.
Finish dependency transactions remain atomic.
Explicit conversion to editable Mesh leaves managed mode.
Save/reopen and Undo/Redo contracts remain valid.
```

Do not redesign these systems merely to simplify Baseboard implementation.

---

# 4. Existing Build 06-A facts that 06-B must generalize

The accepted Build 06-A implementation currently has a verification-oriented Profile path.

Important existing behavior includes:

```text
profile_id default = SIMPLE_10X60
verification Profile = 10 mm projection × 60 mm height
endpoint blocker projection = 10 mm
managed Finish Curve uses the verification Profile
closed=True is unsupported
join_policy=BREAK is unsupported
FinishExclusion records exist but are not yet subtracted from generated geometry
```

These were acceptable for the Build 06-A foundation.

Build 06-B MUST generalize the fixed 10 × 60 mm assumptions without breaking the canonical attachment model.

---

# 5. Build 06-B scope

Build 06-B contains four accepted implementation stages:

```text
Stage 1
Standard Baseboard Foundation

Stage 2-A
Manual Exclusion & Partial Placement

Stage 2-B
Additional Standard Profiles & Profile-aware Shading

Stage 3
Custom Profile Registration & Final Baseboard Acceptance
```

The final Build 06-B acceptance occurs only after all four stages are accepted.

Each stage must include the tests relevant to that stage before the next stage begins.

---

# 6. Deliberately out of scope

The following MUST NOT expand Build 06-B:

```text
Build 05-C automatic collinear Wall merge
Build 06-C Crown Moulding as a production feature
closed FinishRun support
automatic Room recognition
automatic full-room routing
floor Mesh generation
ceiling Mesh generation
door/window asset creation
door/window Boolean system
automatic Door/Window exclusion generation
external/global Profile cloud library
cross-project automatic Profile synchronization
BIM semantics
quantity takeoff
construction documents
automatic stair generation
arbitrary 3D Custom Profile registration
holes/multiple contours in Custom Profiles
arbitrary Modifier evaluation during Custom Profile registration
arbitrary non-uniform Custom Profile deformation
automatic reverse engineering from edited Mesh
return-to-wall decorative end caps
ornamental end assets
full general-purpose solid collision detection
```

A later build may add these without changing the canonical 06-B contracts.

---

# 7. Build identification and versioning

The existing accepted add-on version is `(0, 6, 3)` and its description still identifies the accepted 06-A candidate state.

Build 06-B implementation MAY update version/build description when implementation begins, but version increments are not a substitute for runtime acceptance.

The final Build 06-B accepted artifact MUST be clearly identifiable as Build 06-B.

Do not use a misleading Build 06-A description in the final accepted 06-B artifact.

---

# 8. Profile architecture overview

Build 06-B separates three concepts:

```text
Profile Definition
    = reusable definition / family / revision

FinishRun Profile Instance Parameters
    = actual values used by one FinishRun

Derived orientation Profile / derived geometry
    = temporary/generated Blender representation
```

These concepts MUST NOT be collapsed into one mutable Blender Curve Object.

---

# 9. Profile Definition identity

A Profile Definition must be identified by stable data conceptually equivalent to:

```text
profile_id
profile_revision
schema_version
profile_kind
```

Exact Blender PropertyGroup class names may differ.

The identity semantics are mandatory.

---

# 10. `profile_id`

`profile_id` identifies the Profile family or stable registered Profile definition.

Examples:

```text
SIMPLE
BEVEL
ROUNDED
CUSTOM_<uuid>
```

The implementation may use internal names that differ, but they must be stable and independent of Blender Object names.

Do NOT use names such as:

```text
Curve
Curve.001
Profile.003
```

as persistent Profile identity.

---

# 11. `profile_revision`

`profile_revision` identifies the design revision of a Profile Definition.

Once a `(profile_id, profile_revision)` pair has been used by a persisted FinishRun, its meaning MUST NOT be silently redefined.

If a standard Profile generation rule changes in a way that would alter regenerated geometry, create a new revision.

Example:

```text
SIMPLE revision 1
SIMPLE revision 2
```

Old revision behavior must remain reproducible for supported saved projects.

---

# 12. `schema_version`

`schema_version` identifies the persistent data-format version.

It is distinct from `profile_revision`.

Example distinction:

```text
profile_revision
    = visual/design rule changed

schema_version
    = serialization/storage representation changed
```

A storage migration must not be disguised as a Profile design revision.

---

# 13. FinishRun stores actual parameter values

A FinishRun MUST store the actual dimensions/parameters required to reproduce its selected Profile.

Do not depend on mutable Profile defaults when regenerating an existing Run.

Conceptually:

```text
FinishRun
├ profile_id
├ profile_revision
├ profile_schema_version
├ profile_height_mm
├ profile_projection_mm
├ profile_bevel_mm
├ profile_radius_mm
└ custom_profile_scale
```

Only fields relevant to the selected Profile kind need to be active.

Exact property names may differ.

---

# 14. Run-local modification rule

Changing the Profile dimensions of one FinishRun MUST NOT silently modify other FinishRuns that reference the same Profile Definition.

Example:

```text
Run A = SIMPLE, 60 × 10 mm
Run B = SIMPLE, 60 × 10 mm
```

Changing Run A to:

```text
80 × 12 mm
```

must leave Run B unchanged.

Bulk changes require an explicit user operation on explicitly selected targets.

---

# 15. Missing Profile behavior

If a FinishRun references a Profile Definition that cannot be resolved:

```text
missing profile_id
missing revision
unsupported schema
corrupt snapshot
```

it MUST be diagnosed as an invalid managed state.

Do NOT silently replace it with SIMPLE or another default Profile.

---

# 16. Deleting a Profile in use

Initial Build 06-B behavior may reject deletion of a Project Custom Profile while any FinishRun references it.

Do not silently rebind existing Runs.

A later explicit “replace references then delete” workflow may be added outside the minimum 06-B scope.

---

# 17. Standard Profile family — initial set

Final Build 06-B standard Baseboard Profiles are:

```text
SIMPLE
BEVEL
ROUNDED
```

`COVE` and `STEPPED` are deliberately not required for 06-B acceptance.

The data model must allow additional Profile kinds later without migration of Finish attachment semantics.

---

# 18. Profile coordinate convention

The Build 06-A convention remains mandatory:

```text
Profile +X = away from the Wall surface into the represented room/finish side
Profile +Y = upward
Profile origin = attachment reference at Wall face / vertical reference
```

For Baseboard:

```text
origin = selected Wall face at floor/base vertical reference
```

This convention applies to both standard and Custom Profiles.

---

# 19. Allowed standard Profile bounds

For standard Baseboard Profiles in 06-B:

```text
min_x >= 0
min_y >= 0
```

The Profile must not intentionally extend into Wall solid or below its Baseboard reference plane.

The resolved Profile must expose bounds conceptually equivalent to:

```text
min_x
max_x
min_y
max_y
```

Do not reduce the safety contract to only one `max_projection` value.

---

# 20. Bounds are not complete collision geometry

Profile bounds are necessary but not sufficient to certify all Baseboard geometry.

06-B safety checks must also consider:

```text
resolved path
Miter extension
segment length
adjacent Miter overlap
endpoint position
blocker footprints
visible-range boundaries after Exclusion
```

A short segment where two corner solutions overlap or reverse must be rejected safely.

A Miter extension that leaves the usable visible range or enters an unselected blocker Wall must be rejected safely.

If the implementation cannot prove that the supported configuration is safe, refuse rather than guess.

---

# 21. One resolved Profile contract

Generated geometry and all Profile-sensitive safety checks MUST use the same resolved Profile parameters.

The implementation must not allow:

```text
generated projection = 20 mm
safety projection = 10 mm
```

For one regeneration operation, resolve the active Profile once into a stable representation containing at least:

```text
contour / generation data
bounds
projection range
vertical range
orientation-independent identity
```

and use that result consistently for:

```text
Curve/Profile generation
Preview validation
endpoint blocker validation
corner/Miter safety
Mesh conversion expectations
```

---

# 22. Orientation-specific generated Profiles are derived data

A user registers or selects one canonical Profile.

LEFT/RIGHT and traversal orientation MUST NOT require the user to maintain separate Profile definitions.

Orientation-specific mirrored Profile geometry is derived data.

The persistent Project Profile Library stores one canonical definition.

---

# 23. Mirroring and winding rule

Mirroring a Profile changes coordinate handedness.

Therefore a simple transform:

```text
(x, y) -> (-x, y)
```

while retaining the original point order is not sufficient.

Whenever an orientation-specific derived Profile is mirrored, the implementation MUST preserve correct contour winding / outward surface orientation.

A valid strategy is:

```text
mirror contour coordinates
then reverse point order when required
```

or an equivalent mathematically correct method.

---

# 24. Negative Object Scale is forbidden for Profile orientation

Do NOT use persistent or generated negative Object Scale such as:

```text
Scale X = -1
```

as the orientation mechanism for a managed Profile.

Derived orientation Profile objects/data should have identity transform.

This avoids handedness, normal and downstream Mesh-conversion ambiguity.

---

# 25. Normal-direction acceptance contract

At minimum, runtime acceptance must cover:

```text
LEFT + FORWARD
LEFT + REVERSE
RIGHT + FORWARD
RIGHT + REVERSE
```

for supported Profile types.

For each relevant case verify:

```text
Profile projects away from Wall solid.
Visible shape matches the same canonical Profile.
Surface orientation is not inverted.
Mesh-converted outward-facing surfaces have correct normals.
Corner geometry does not introduce flipped faces.
```

One side working while the opposite side has reversed normals is a Build 06-B failure.

---

# 26. Material separation

Profile shape identity and Finish material assignment are separate concerns.

Do not make the Profile Definition silently control or replace the Finish material.

Existing Finish material assignment must survive, where relevant:

```text
Profile parameter edits
Profile kind changes
Exclusion edits
Wall edits
regeneration
save/reopen
Mesh conversion
```

unless the user explicitly changes material.

---

# 27. Standard SIMPLE Profile

Stage 1 formally introduces:

```text
SIMPLE revision 1
```

Parameters:

```text
height_mm
projection_mm
```

Default:

```text
height_mm = 60
projection_mm = 10
```

Both values must be finite and positive.

Reasonable project-safe min/max UI limits may be used, but do not hard-code only one construction size.

---

# 28. Stage 1 UI — selected FinishRun

The selected Baseboard UI must expose at minimum:

```text
種類: BASEBOARD
Profile: SIMPLE
高さ: 60 mm
出幅: 10 mm
区間数
管理状態
```

and the existing managed operations as appropriate.

The Japanese UI label for horizontal projection should use a concept such as:

```text
出幅
```

rather than an ambiguous generic “幅”.

---

# 29. Stage 1 Profile selection

A minimum Profile selector belongs in Stage 1.

Do not defer all Profile selection UX until Custom Profile work.

In Stage 1 only SIMPLE needs to be available, but the UI/data flow should already use the Profile-resolution path rather than a hard-coded verification Profile path.

---

# 30. Replace Build 06-A verification Profile dependency

Build 06-B Stage 1 must stop treating the 10 × 60 verification Profile as the production source of Baseboard geometry.

The accepted Build 06-A Profile may remain for compatibility/testing helpers if needed, but managed production Baseboard regeneration must resolve the active Profile Definition and actual FinishRun parameters.

---

# 31. Stage 1 endpoint safety generalization

The existing endpoint blocker logic uses a 10 mm verification projection.

Stage 1 MUST replace that production assumption with the resolved Profile geometry/bounds.

Do not leave hidden 10 mm constants in production Baseboard endpoint validation.

Tests should explicitly use at least two different projection values to catch accidental fixed-size behavior.

---

# 32. Stage 1 Miter safety generalization

Miter validation must be Profile-dimension-aware for supported SIMPLE geometry.

At minimum verify:

```text
90-degree corner
oblique supported corner
short segment between corners
large projection value
blocker Wall at endpoint/junction
```

The Miter must not extend beyond a safe visible range or through unselected Wall solid.

---

# 33. Stage 1 end behavior

The initial Baseboard end behavior is:

```text
interior/corner join = MITER
free Run start/end = BUTT
partial-boundary start/end = BUTT
```

`BUTT` has a strict meaning:

> Cut the generated Baseboard on a plane perpendicular to the local path direction and close the cross-section.

An open/hollow end that merely stops the Curve is not sufficient for final production acceptance.

---

# 34. Unsupported end treatments

Build 06-B does not require:

```text
return-to-wall end
round return
ornamental end block
end-cap asset
coping
scribe-to-irregular-object
```

Do not add them to Stage 1 in place of required stability work.

---

# 35. Profile parameter edits are transactional

Editing a FinishRun Profile parameter is a managed operation.

Required behavior:

```text
snapshot previous canonical parameter state
apply provisional new parameters
resolve/validate Profile
resolve visible Baseboard geometry
validate blockers/corners/end conditions
prepare replacement derived data
commit only on complete success
```

If any validation or replacement preparation fails:

```text
restore old parameters
preserve old valid geometry
report error
```

Do not leave new dimensions with old geometry or vice versa.

---

# 36. Stage 1 Build 06-A compatibility

Existing accepted Build 06-A FinishRuns may contain:

```text
profile_id = SIMPLE_10X60
```

Build 06-B MUST interpret this legacy identifier as the compatible production equivalent of:

```text
SIMPLE revision 1
height = 60 mm
projection = 10 mm
```

Opening an old file must not require immediate destructive rewrite of all canonical Finish data.

Lazy/non-destructive compatibility interpretation is preferred.

---

# 37. Legacy first-edit rule

When a legacy `SIMPLE_10X60` FinishRun is first explicitly edited as a production Profile instance, its actual selected dimensions must then be stored explicitly under the 06-B data contract.

Compatibility must not permanently lock the Run to 60 × 10 mm.

---

# 38. Stage 1 compatibility acceptance

A Build 06-A accepted file opened in 06-B must preserve, before explicit new edits:

```text
Finish ID
FinishSpan data
Wall pointers / expected IDs
LEFT / RIGHT
traversal direction
vertical reference
10 × 60 visual dimensions
position
material assignment
shading appearance
end appearance
managed-state validity
```

Explicit regeneration must reproduce the same accepted appearance within reasonable numeric tolerance.

---

# 39. Stage 1 persistence and Undo

Stage 1 runtime acceptance must include, for the newly introduced Profile data:

```text
parameter edit
Undo
Redo
save
close Blender
reopen
regenerate
```

Do not postpone Profile-parameter persistence testing until Stage 3.

---

# 40. Stage 1 completion gate

Stage 1 is accepted only when:

```text
SIMPLE Baseboard is generated through production Profile resolution.
Height and projection can be changed per FinishRun.
Other Runs remain unchanged.
Generation and safety checks use the same resolved dimensions.
Miter and BUTT behavior pass the supported cases.
Failed dimension changes rollback atomically.
Build 06-A SIMPLE_10X60 remains visually compatible.
LEFT/RIGHT orientation and normals pass.
Relevant Undo/Redo and save/reopen pass.
```

Stage 2-A must not begin before Stage 1 acceptance.

---

# 41. Stage 2-A purpose

Stage 2-A makes the Baseboard useful in a real room by adding:

```text
Manual Exclusion
multiple visible generated ranges
valid-empty state
Exclusion editing/removal
partial Run start/end editing
Wall split tracking for active Exclusions
```

Stage 2-A uses SIMPLE only for acceptance isolation.

Do not mix BEVEL/ROUNDED debugging into Exclusion foundation work.

---

# 42. FinishExclusion canonical principle

FinishExclusion records are persistent canonical intent.

They MUST NOT destructively rewrite the original FinishSpan intervals merely because geometry is hidden.

Canonical relationship:

```text
FinishSpans
+
Enabled FinishExclusions
        ↓
visible-range calculation
```

Removing or disabling an Exclusion must restore the corresponding Baseboard without reconstructing lost Span data.

---

# 43. Exclusion identity

Build 06-B should extend the Exclusion model with stable identity semantics conceptually equivalent to:

```text
exclusion_id
fragment_id
source_id
enabled
```

Exact property names may differ.

---

# 44. `exclusion_id`

`exclusion_id` identifies one logical exclusion authored by the user or future external source.

It must be stable and independent of object names or collection order.

Use a collision-resistant persistent ID mechanism.

---

# 45. `fragment_id`

If one logical Exclusion is split into multiple persisted records because a Wall is split, each persisted fragment must be individually identifiable.

Conceptually:

```text
same exclusion_id
different fragment_id
```

This preserves logical ownership while allowing safe remap/edit/delete behavior.

A different equally explicit parent/child representation is acceptable if semantics are equivalent.

---

# 46. `source_id`

`source_id` identifies the originating external/manual source when applicable.

Future examples:

```text
Door ID
Window ID
other managed opening ID
```

`source_id` MUST NOT be overloaded as the unique identity of the Exclusion record itself.

Manual Exclusions may have empty or dedicated manual source semantics.

---

# 47. Exclusion enabled state

Build 06-B requires an explicit way to distinguish active production Exclusions from legacy 06-A records that were persisted but did not affect geometry.

An `enabled` flag or equivalent persistent compatibility state is recommended.

---

# 48. Legacy 06-A Exclusion compatibility

Build 06-A could contain valid persisted Exclusion records that were not subtracted from generated geometry.

Therefore, opening an old 06-A file in 06-B MUST NOT suddenly make existing Baseboard disappear merely because an old Exclusion record exists.

Legacy records must preserve legacy visual behavior until explicitly activated or migrated by a user-confirmed operation.

---

# 49. New 06-B Manual Exclusions

New Exclusions created through the 06-B UI are active immediately after successful validation/commit.

They use the same Wall pointer + expected persistent ID integrity model as FinishSpans.

No separate incompatible coordinate system is allowed.

---

# 50. Exclusion boundary representation

Continue to use the existing Wall-local boundary model:

```text
WALL_START
WALL_END
DISTANCE_FROM_START
DISTANCE_FROM_END
```

with millimeter values.

Do not add an independent world-coordinate-only exclusion representation.

---

# 51. Exclusion subtraction pipeline

The Stage 2-A generation pipeline is:

```text
validate canonical FinishRun / Spans / Profile / Walls
        ↓
resolve canonical Span intervals
        ↓
collect applicable enabled Exclusions
        ↓
resolve Exclusion intervals
        ↓
subtract Exclusions from Span intervals
        ↓
merge overlapping/touching exclusion coverage only for calculation
        ↓
produce visible continuous ranges
        ↓
resolve path/join safety per visible range
        ↓
apply BUTT end treatment at every visible range start/end
        ↓
generate one managed Finish object containing multiple splines/ranges as needed
```

---

# 52. Persisted Exclusions are not destructively merged

If two persisted Exclusions overlap, generation may merge their interval coverage for efficient visible-range calculation.

Do NOT replace the original records with one combined record solely because they overlap.

This is essential for future source independence.

Example:

```text
MANUAL Exclusion overlaps future DOOR Exclusion
```

Deleting the Door source later must not remove the Manual exclusion intent.

---

# 53. No join across an Exclusion gap

A Miter or continuation MUST NOT be created across a removed Exclusion gap.

Each visible continuous range is an independent generated path for join/end purposes.

Exclusion boundaries create BUTT ends in Build 06-B.

---

# 54. Validate before visible-range subtraction

Do not interpret “no visible geometry” as automatically valid.

Validation order must distinguish:

```text
valid canonical data + Exclusion result = empty
```

from:

```text
invalid Wall/Profile/Span/Exclusion data = generation failure
```

Only the first state is `valid-empty`.

---

# 55. Valid-empty state

If correct canonical data and active Exclusions remove the entire generated Baseboard:

```text
FinishRun remains valid.
FinishSpans remain persisted.
Exclusions remain persisted.
Generated visible range count = 0.
```

This is a normal managed state.

It must not be reported as broken merely because there is no visible spline geometry.

---

# 56. Valid-empty UI

When a valid-empty FinishRun is selected, the UI should make the state explicit.

Conceptually:

```text
管理状態: 正常
表示区間: 0
状態: 全区間除外
```

The user must still be able to inspect/edit/remove Exclusions.

---

# 57. Valid-empty selection

Because no visible geometry exists, the user cannot rely on viewport clicking.

The Finish object must remain discoverable/selectable through normal Blender data organization such as Outliner/object list.

Do not delete the managed Finish object merely because visible range count becomes zero.

---

# 58. Valid-empty Mesh conversion

Converting a valid-empty FinishRun to editable Mesh must refuse safely with a clear message equivalent to:

```text
生成可能な巾木形状がありません。
```

Do not generate an invalid empty Mesh as a successful conversion.

---

# 59. Exclusion removal

Removing/disabling an Exclusion must regenerate from the original persisted FinishSpan data and remaining active Exclusions.

The restored Baseboard must return without user reconstruction of the old path.

---

# 60. Wall split and Exclusion fragments

When a Wall containing an active or legacy Exclusion is split:

- use the accepted Build 06-A dependency transaction model;
- remap Exclusion references and intervals semantically;
- preserve logical exclusion identity;
- generate new fragment identity where needed;
- never silently drop coverage;
- rollback the complete Wall + Finish + Exclusion mutation if regeneration fails.

---

# 61. Partial placement editing

Stage 2-A must expose at least practical editing of the first and last effective FinishSpan boundary.

The user should be able to change where a Baseboard Run starts or ends partway along its Wall.

Reuse the existing FinishSpan boundary model.

Do not invent another “baseboard start distance” source of truth separate from the Span boundaries.

---

# 62. Partial-boundary end treatment

A partial Run boundary that does not reach a Wall endpoint creates a Baseboard free end.

In Build 06-B this end uses the same BUTT contract:

> perpendicular to local path direction and cross-section closed.

No automatic return-to-wall geometry is required.

---

# 63. Stage 2-A Preview behavior

Preview must reflect active Exclusion/partial-range rules where the corresponding edit operation provides preview.

At minimum it must not present an excluded interval as a valid committed Baseboard segment.

Invalid state feedback should remain clearly distinguishable from normal cyan path feedback established by accepted 06-A behavior.

---

# 64. Stage 2-A persistence and Undo

Runtime acceptance must include:

```text
add Exclusion
Undo
Redo
save/reopen
remove Exclusion
save/reopen
valid-empty save/reopen
partial start/end edit
Wall split with active Exclusion
```

The generated visible ranges after reopen must match pre-save state.

---

# 65. Stage 2-A completion gate

Stage 2-A is accepted only when:

```text
Manual Exclusion changes generated geometry.
Original FinishSpans remain canonical and intact.
Overlapping records are merged only for calculation.
Multiple visible ranges produce separate splines/ranges.
No Miter bridges an Exclusion gap.
Exclusion-created ends are closed BUTT ends.
valid-empty is distinct from invalid managed state.
Exclusion removal restores geometry.
Wall split preserves/remaps active Exclusions.
Relevant Undo/Redo and save/reopen pass.
Legacy 06-A Exclusion records do not suddenly alter old appearance.
```

Stage 2-B must not begin before Stage 2-A acceptance.

---

# 66. Stage 2-B purpose

Stage 2-B expands the accepted production system from SIMPLE to:

```text
SIMPLE
BEVEL
ROUNDED
```

while keeping Exclusion behavior unchanged.

It also introduces Profile-aware shading requirements.

---

# 67. BEVEL Profile

BEVEL parameters:

```text
height_mm
projection_mm
bevel_mm
```

The bevel parameter must be finite and positive.

Input constraints must prevent self-collapse or invalid contour geometry.

At minimum enforce a safe relationship equivalent to:

```text
0 < bevel_mm < min(height_mm, projection_mm)
```

or a stricter mathematically justified rule used by the actual contour definition.

---

# 68. ROUNDED Profile

ROUNDED parameters:

```text
height_mm
projection_mm
radius_mm
```

The exact standard contour must be explicitly implemented and versioned.

The radius must be finite and positive and constrained to a value that keeps the contour valid.

---

# 69. Standard Profile generation rules are versioned behavior

The geometric formulas/contours for:

```text
SIMPLE revision 1
BEVEL revision 1
ROUNDED revision 1
```

must be deterministic and remain reproducible for saved files.

Do not later modify `revision 1` geometry in place if that changes regenerated output.

Use a new revision.

---

# 70. Rounded contour resolution

ROUNDED must have sufficient geometric resolution for renovation-perspective rendering.

The specification does not require an excessive segment count.

However, a visibly coarse polygonal roundover in normal viewport/render use is not acceptable.

Use deterministic resolution appropriate for the Profile radius/shape and preserve it across save/reopen and regeneration.

---

# 71. Profile-aware shading

The accepted Build 06-A Flat Shade rule was correct for the rectangular verification Profile.

Build 06-B must generalize display rules by Profile geometry.

Acceptance intent:

```text
SIMPLE
    planar surfaces read as planar
    hard edges remain hard

BEVEL
    planar faces remain planar
    bevel boundaries remain intentional/hard where defined

ROUNDED
    rounded region appears smooth
    planar regions remain planar
    transitions between planar and rounded regions remain intentional
```

Do not simply Smooth Shade every converted Mesh.

Do not simply Flat Shade every rounded surface.

---

# 72. Curve and Mesh appearance parity

For BEVEL/ROUNDED, verify both:

```text
managed Curve appearance
editable Mesh conversion appearance
```

Mesh conversion should preserve the intended visible shape and shading as reasonably as possible.

A Curve that looks correct but converts to visibly faceted or incorrectly smoothed geometry is not final acceptance.

---

# 73. Additional standard Profile safety

For BEVEL and ROUNDED, geometry and blocker/Miter validation must still derive from the same resolved Profile contract.

Do not fall back to SIMPLE 10 mm projection checks.

Use conservative bounds/geometry rules for supported shapes.

If a custom corner case cannot be proven safe, reject it.

---

# 74. Stage 2-B completion gate

Stage 2-B is accepted only when:

```text
BEVEL and ROUNDED can be selected.
Run-local parameters persist.
Profile switching is transactional.
SIMPLE/BEVEL/ROUNDED use Profile-aware safety data.
LEFT/RIGHT normals remain correct.
Miter and BUTT results remain valid.
ROUNDED is visually smooth where intended.
Planar areas remain planar.
Mesh conversion preserves intended appearance.
Exclusion behavior remains correct for each standard Profile where tested.
Relevant Undo/Redo and save/reopen pass.
```

Stage 3 must not begin before Stage 2-B acceptance.

---

# 75. Stage 3 purpose

Stage 3 adds controlled Custom Profile registration and finalizes the production Baseboard system.

Custom registration is deliberately constrained.

The goal is stable user-defined Baseboard sections, not arbitrary Curve-to-sweep ingestion.

---

# 76. Custom Profile registration source

Initial supported source:

```text
Blender Curve Object
2D
one spline
cyclic/closed
no holes
no self-intersection
Object Transform = identity
no active Modifiers relied upon
```

Unsupported input must be rejected before registration with a clear reason.

---

# 77. Supported Custom spline types

Initial 06-B supported source spline types:

```text
POLY
BEZIER
```

NURBS and other unsupported types must be rejected in Stage 3 rather than approximated unpredictably.

---

# 78. Custom Profile normalization

Registration must validate/normalize the source under the canonical convention:

```text
+X = wall outward / room direction
+Y = upward
origin = attachment origin
```

The registration UI/help must make the required origin/orientation understandable.

The implementation must not guess a completely arbitrary origin from geometry in a way that changes meaning unpredictably.

---

# 79. Custom Baseboard allowed coordinate region

Initial Custom Baseboard Profile acceptance requires the canonical contour to satisfy the supported coordinate rule equivalent to:

```text
min_x >= 0
min_y >= 0
```

within a small numerical tolerance.

Profiles extending into the Wall or below the Baseboard reference are rejected in initial 06-B.

---

# 80. Custom Profile snapshot

Registration creates a Project-local immutable Profile snapshot/revision.

It must not remain a live dependency on the source Curve Object.

After successful registration, editing, renaming or deleting the source Curve must not alter existing registered Profile revisions.

---

# 81. Custom snapshot content

Persist enough information to reproduce the registered Profile independently of the source object.

At minimum conceptually include:

```text
profile_id
profile_revision
schema_version
display_name
source type metadata
canonical contour representation
origin convention
unit convention
bounds
sampling/resolution metadata where applicable
winding/orientation metadata
shading intent metadata where needed
```

Exact storage fields may differ.

---

# 82. BEZIER snapshot rule

For initial 06-B, BEZIER source Profiles should be converted at registration time into a deterministic evaluated 2D closed contour representation.

Do not keep the source Blender Curve as the canonical Profile truth.

The sampling/tessellation contract must be deterministic.

---

# 83. Custom sampling tolerance and point limit

Implementation must define explicit safe limits for Custom contour snapshotting.

Requirements:

```text
finite point coordinates
minimum sufficient point count
maximum point count to avoid pathological data
stable deterministic sampling for accepted BEZIER source
closed contour
no duplicate-collapse into zero area
```

The exact numeric point/tolerance limits may be chosen during implementation, but they must be documented in code/tests and not depend on random viewport state.

---

# 84. Self-intersection and hole policy

Initial Custom Profiles must contain:

```text
one outer contour
no hole
no self-intersection
```

Do not use convex hull as a substitute for the actual contour.

A concave single contour MAY be supported only if the chosen generation/end-cap implementation preserves that contour correctly.

If the implementation cannot safely close concave ends, narrow the accepted Custom Profile subset and document/test the restriction.

---

# 85. Custom BUTT end closure

A Custom Profile BUTT end must close using the actual accepted contour shape.

Do not replace the end shape with a convex hull merely for convenience.

If this cannot be implemented for a particular accepted contour class, that contour class must not be accepted for registration.

---

# 86. Custom Profile scaling

Initial Custom Profile instance sizing supports:

```text
original size
uniform scale
```

Non-uniform X/Y scaling is out of scope.

Do not present arbitrary independent “height” and “projection” deformation fields for Custom Profiles if doing so would distort decorative geometry unpredictably.

---

# 87. Custom Profile revisioning

Re-registering or modifying a Custom Profile must not silently mutate existing FinishRuns.

Preferred behavior:

```text
new Profile revision or new Profile definition
```

Existing Runs continue to reference the old revision until the user explicitly applies the new revision.

---

# 88. Custom Profile source deletion test

Runtime acceptance MUST explicitly test:

```text
register Custom Profile
create Baseboard using it
save
edit or delete source Curve Object
regenerate Baseboard
```

The registered Baseboard Profile must remain reproducible.

---

# 89. Custom orientation and normal test

Runtime acceptance MUST test mirrored/oriented Custom Profiles on both canonical Wall sides.

At minimum verify:

```text
LEFT
RIGHT
forward/reverse traversal combinations where relevant
```

Mesh-converted normals must remain outward/correct.

Do not accept a system where one side is inside-out.

---

# 90. Profile Library scope

Build 06-B Profile Library is Project-local.

It must survive save/reopen within the `.blend` project.

Build 06-B does NOT require:

```text
cross-project shared external file library
cloud sync
automatic global user library
network storage
```

Future import/export may be added later without changing Run/Profile identity semantics.

---

# 91. Profile selection UX

By final Stage 3, the Profile UI should provide practical identification and selection of:

```text
SIMPLE
BEVEL
ROUNDED
registered Custom Profiles
```

A lightweight list/selector is sufficient.

Thumbnail UI is optional unless it can be added without risking core stability.

Thumbnail browsing is not a Build 06-B completion requirement.

---

# 92. Custom Profile deletion UX

Attempting to delete a Custom Profile revision that is still referenced should be rejected or require an explicit safe replacement workflow.

For initial 06-B, safe rejection is acceptable.

The UI should report why deletion is blocked.

---

# 93. Explicit Profile replacement

Changing a FinishRun from one Profile to another is an explicit transactional operation.

The operation must update consistently:

```text
profile identity/revision
actual Profile parameters
resolved derived geometry
managed diagnosis state
```

If the new Profile cannot generate safely on the current Run, rollback completely.

---

# 94. Closed FinishRun remains unsupported

Build 06-B formally supports:

```text
closed = False
```

only.

`closed=True` must remain a clearly diagnosed/rejected unsupported configuration.

Do not silently treat a closed Run as open.

Closed-loop final-join geometry requires its own future acceptance work.

---

# 95. `join_policy=BREAK`

Unless an explicit 06-B implementation task deliberately implements and tests it, `join_policy=BREAK` remains unsupported as in accepted 06-A.

Build 06-B uses:

```text
MITER for supported continuous corners
BUTT at free/partial/exclusion range ends
```

Do not redefine `BREAK` merely as “Exclusion happened”.

---

# 96. Manual Curve editing remains non-canonical

Manual Edit Mode changes to a managed Finish Curve remain derived-only edits.

Explicit regeneration may replace those changes from canonical Baseboard data.

Build 06-B does not reverse-engineer manual Curve edits into Profile/Exclusion state.

---

# 97. Mesh conversion contract

Editable Mesh conversion retains the Build 06-A one-way managed exit contract.

It must:

```text
validate the managed FinishRun
require at least one generated visible range
preserve visible Profile shape
preserve intended shading
preserve material assignment as reasonably possible
create ordinary editable Mesh state
remove JHM managed Finish behavior from the result
leave Walls and canonical managed objects untouched
```

After conversion, future Wall/Profile/Exclusion edits do not update that Mesh.

---

# 98. Dependency transaction requirement

Every Build 06-B operation that can change canonical managed Baseboard state must participate in the accepted transaction model.

Examples:

```text
Profile parameter edit
Profile replacement
Exclusion add/edit/delete/enable
partial start/end edit
Custom Profile apply
Wall split affecting Exclusions
Wall delete affecting visible ranges
```

Preparation and commit failures must preserve the previous accepted state.

---

# 99. No destructive canonical mutation before validation

Do not irreversibly change:

```text
Profile instance parameters
Exclusion records
Span boundaries
Profile references
```

before the operation has enough recoverable state to rollback.

The user must not receive a successful result with canonical data and generated geometry out of sync.

---

# 100. Build 05-B / 06-A regression policy

Do not rerun every historical runtime scenario after every small stage.

However, each stage must run targeted regression for the dependencies it modifies.

Before final Build 06-B acceptance, perform a broader regression sufficient to prove that:

```text
Wall create/edit/move/split/delete remains functional
Wall topology remains valid
accepted 06-A Finish path creation remains functional
T-blocker rejection remains functional
Preview normal/invalid colors remain functional
managed Finish regeneration remains atomic
Mesh conversion remains functional
save/reopen remains functional
```

Do not weaken or delete existing automated tests merely to pass 06-B.

---

# 101. Automated test expectations

Each stage should add pure/CPython tests where logic is Blender-independent.

Examples:

```text
Profile parameter validation
Profile bounds
Profile revision lookup
legacy SIMPLE_10X60 interpretation
orientation/mirror winding helpers
Exclusion interval subtraction
overlap merge-for-calculation
valid-empty classification
Exclusion logical/fragment identity helpers
Custom contour validation
Custom sampling helpers where Blender-independent
```

Retain all existing Build 06-A tests.

---

# 102. Blender runtime acceptance principle

Automated tests do not replace Blender 5.2 LTS runtime acceptance for:

```text
Curve bevel/sweep appearance
normals
shading
modal/UI behavior
Undo/Redo
save/reopen
Mesh conversion
actual datablock persistence
```

Each stage requires focused Blender runtime tests for the features added in that stage.

---

# 103. Stage-by-stage runtime scope

## Stage 1

Focus on:

```text
SIMPLE dimensions
per-Run isolation
Miter/BUTT
orientation/normals
rollback
legacy SIMPLE_10X60
Undo/Redo
save/reopen
```

## Stage 2-A

Focus on:

```text
Manual Exclusion
multiple splines/ranges
overlap behavior
valid-empty
Exclusion removal
partial boundaries
Wall split remap
Undo/Redo
save/reopen
```

## Stage 2-B

Focus on:

```text
BEVEL/ROUNDED geometry
parameter constraints
Profile-aware shading
Mesh conversion appearance
orientation/normals
Exclusion compatibility
save/reopen
```

## Stage 3

Focus on:

```text
Custom registration
snapshot independence
source deletion/edit independence
Custom orientation/normals
Custom BUTT closure
Project persistence
Profile replacement/deletion safety
final regression
```

---

# 104. Recommended implementation modules

Exact file structure may differ, but responsibilities should remain separated.

Recommended additions/refactors:

```text
finish_profile.py
    Profile definitions
    standard Profile generation
    bounds
    orientation/mirroring/winding
    Profile lookup/revision compatibility

finish_exclusion.py
    Exclusion interval resolution
    interval subtraction
    overlap calculation
    valid-empty classification
    exclusion identity helpers

finish_custom_profile.py
    Custom source validation
    snapshot creation
    contour checks
    sampling

finish_geometry.py
    use resolved Profile and visible ranges
    generated Curve/splines
    caps/end closure
    regeneration transactions

finish_surface.py
    Profile-aware safety inputs
    blocker/corner/Miter geometric helpers

finish_operators.py
    Profile edits
    Exclusion edits
    partial boundary edits
    Custom registration/apply

properties.py
    persistent Profile/Run/Exclusion schema

ui.py
    production Baseboard controls
```

Do not create giant UI/operator modules if responsibilities can remain pure/testable.

---

# 105. Stage 1 recommended implementation sequence

```text
A. persistent Profile instance fields + compatibility reader
B. standard Profile registry/resolver
C. SIMPLE revision 1 generator + bounds
D. orientation/mirror/winding helper
E. Profile-aware endpoint/corner safety inputs
F. production geometry regeneration through resolved Profile
G. selected Finish Profile parameter UI/operator
H. transaction/rollback tests
I. Blender runtime acceptance
```

---

# 106. Stage 2-A recommended implementation sequence

```text
A. Exclusion identity/enabled compatibility fields
B. pure interval subtraction/merge helpers
C. visible-range model
D. multi-spline/range generation
E. BUTT closure at Exclusion ranges
F. Manual Exclusion UI/operators
G. valid-empty diagnosis/UI
H. partial start/end editing
I. Wall split Exclusion fragment remap
J. persistence/Undo/runtime acceptance
```

---

# 107. Stage 2-B recommended implementation sequence

```text
A. BEVEL revision 1
B. ROUNDED revision 1
C. parameter validators
D. resolved bounds/safety integration
E. shading policy implementation
F. Mesh-conversion appearance preservation
G. Exclusion + additional Profile regression
H. runtime acceptance
```

---

# 108. Stage 3 recommended implementation sequence

```text
A. Project Profile storage
B. source Curve validation
C. POLY snapshot
D. BEZIER deterministic sampling snapshot
E. Custom contour validation/bounds/winding
F. Custom registration UI
G. Custom apply/revision handling
H. Custom orientation/mirror/normals
I. Profile deletion/reference safety
J. final persistence/Undo/Mesh/regression acceptance
```

---

# 109. Failure-handling principles

Prefer:

```text
reject safely
preserve previous accepted state
show a specific reason
require explicit user action
```

instead of:

```text
silent fallback
silent Profile replacement
silent Exclusion loss
silent identity reassignment
visually plausible but topologically invalid geometry
```

---

# 110. User-facing diagnosis examples

Exact Japanese wording may differ, but failures should distinguish categories such as:

```text
Profile定義が見つかりません。
Profile寸法が不正です。
この寸法では角部を安全に生成できません。
参照Wallが不正です。
Exclusion参照が不正です。
このCustom Profileは自己交差しています。
Custom Profileは閉じた2D Curveである必要があります。
このProfileは使用中のため削除できません。
生成可能な巾木形状がありません。
```

Do not collapse unrelated problems into one generic “generation failed” state when a clear cause is available.

---

# 111. Performance expectations

Build 06-B is not a large-scene optimization build.

Still avoid obvious repeated full-scene scans in modal preview or simple parameter edits when persistent/reference caches already exist.

Pure interval/Profile helpers should remain lightweight.

Correctness takes priority over micro-optimization.

---

# 112. Data migration principle

Prefer compatibility interpretation over destructive eager migration where feasible.

Opening an accepted 06-A project must not immediately rewrite large amounts of canonical data solely because 06-B is installed.

Explicit user edits may upgrade the affected record into the 06-B schema.

Any migration that is required must be:

```text
safe
deterministic
non-heuristic
recoverable where appropriate
explicitly tested
```

---

# 113. Legacy Exclusion activation must be explicit

The fact that a 06-A Exclusion record is structurally valid does not mean it was visually active in 06-A.

06-B must preserve old visual behavior until activation/migration is explicit.

Do not infer user intent from the mere presence of a legacy record.

---

# 114. Profile and Exclusion are independent canonical layers

A Profile change MUST NOT silently alter Exclusion interval data.

An Exclusion edit MUST NOT silently alter Profile identity or parameters.

Both affect derived geometry, but their canonical intent is independent.

---

# 115. Final Build 06-B completion criteria

Build 06-B is complete only when all of the following are true:

```text
A Baseboard can be created on an explicitly chosen Wall side.
SIMPLE, BEVEL and ROUNDED standard Profiles are production-usable.
Profile dimensions are stored per FinishRun and can be edited safely.
Changing one Run does not modify unrelated Runs.
Generation and safety validation use the same resolved Profile data.
LEFT/RIGHT and traversal orientation do not invert normals.
Miter corners and closed BUTT ends work for supported cases.
Manual Exclusions remove Baseboard geometry without destroying Span intent.
One FinishRun may generate multiple visible splines/ranges.
Exclusion gaps are not bridged by Miter joins.
All-excluded Runs remain valid and recoverable.
Legacy 06-A Exclusions do not become active unexpectedly.
Partial Run start/end editing is usable.
Wall split preserves Exclusion intent.
Custom 2D Profiles can be registered under the defined restrictions.
Custom Profile registration is a snapshot, not a live source dependency.
Custom Profile source edit/delete does not mutate old registered Profiles.
Custom Profile orientation preserves winding/normals on both sides.
Project-local Profile definitions survive save/reopen.
Profile replacement and deletion are safe and explicit.
Material assignment is preserved across managed regeneration where relevant.
Editable Mesh conversion preserves intended visible Profile/shading.
Undo/Redo remains coherent.
Failure rollback preserves previous accepted canonical and derived state.
Build 05-B Wall behavior remains intact.
Accepted Build 06-A Finish behavior remains intact except for the intentional 06-B production extensions.
```

---

# 116. Build 06-B acceptance decision rule

A feature is not accepted merely because its numeric dimensions are correct.

For renovation-perspective production, final visual and editing behavior matter.

Examples of unacceptable outcomes:

```text
correct radius but visibly faceted rounded molding
correct left-side geometry but right-side inverted normals
correct Exclusion records but one spline bridges the removed gap
correct canonical data but failed edit leaves new parameters with old geometry
Custom source deletion breaks old project Profiles
old 06-A file opens with unexpected missing Baseboard because dormant Exclusions became active
```

When unsupported geometry cannot be proven safe, reject it rather than creating plausible but incorrect output.

---

# 117. Required verification commands

Codex/local implementation verification should include at minimum:

```text
python -B -m unittest discover -s tests
python -m compileall -q japanese_house_modeler tests
git diff --check
```

If staged:

```text
git diff --cached --check
```

Do not suppress or delete existing failing tests merely to complete the build.

---

# 118. Codex workflow constraint

Codex Cloud must work only in its local workspace.

Do NOT spend time attempting unsupported GitHub network Git operations from Codex Cloud.

Known unavailable/unreliable operations in this project workflow include:

```text
git fetch
git pull
git push
git ls-remote
```

Do not create installation ZIP files in Codex.

The user/GPT workflow will handle GitHub PR transfer and Blender installation ZIP creation separately.

---

# 119. Stage reporting requirements

After each implementation stage, Codex must report:

```text
starting commit
ending/local commit SHA
changed files
automated test count and result
compileall result
diff-check result
known unsupported behavior
required Blender 5.2 LTS runtime tests
```

Do not claim Blender runtime acceptance from CPython tests.

---

# 120. Formal acceptance record

Build 06-B should maintain a dedicated acceptance record after implementation begins, separate from the specification.

Recommended:

```text
BUILD_06_B_ACCEPTANCE_RECORD.md
```

It should distinguish:

```text
automated evidence
Blender 5.2 LTS runtime evidence
stage acceptance
final Build 06-B acceptance
post-acceptance follow-ups, if any
```

Do not overwrite the historical Build 06-A acceptance record.

---

# 121. Handoff after Build 06-B

When Build 06-B is accepted, future Baseboard-related systems may assume:

```text
production standard Baseboard Profiles
per-Run Profile parameters
Profile revision/schema semantics
Profile-aware safety bounds
orientation-safe derived mirroring
Manual Exclusion subtraction
valid-empty semantics
multiple visible generated ranges
partial placement editing
Project-local Custom Profile snapshots
Profile-aware shading
production Mesh conversion
```

Build 06-C Crown Moulding may reuse only the generic Profile infrastructure that is genuinely shared.

Do not force Baseboard-specific floor/end/exclusion assumptions into Crown behavior merely for code reuse.

---

# 122. Final instruction to implementer

Implement Build 06-B from the accepted `main` commit:

```text
3aa8b87cf9e62b3ba2ee484b5f464489365fdf3d
```

Do not restart the Wall or Finish attachment system.

Do not replace the accepted Build 06-A canonical model.

Generalize the accepted verification-oriented Profile/Exclusion foundation into a production Baseboard system in the staged order defined above.

The priorities are:

```text
1. correctness and rollback safety
2. non-destructive compatibility with accepted 06-A files
3. practical Baseboard workflow for a real room
4. stable persistent Profile/Exclusion data
5. final visual quality suitable for renovation-perspective work
6. extensibility for later Crown/Door/Window integration
```

Reliable partial automation is preferable to fragile broad automation.
