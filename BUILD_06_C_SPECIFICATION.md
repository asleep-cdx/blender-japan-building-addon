# BUILD 06-C SPECIFICATION

## 日本住宅モデラー — Crown Moulding / Profile Thumbnail UI

- Target: Blender 5.2 LTS
- Repository: `asleep-cdx/blender-japan-building-addon`
- Required base branch: `main`
- Accepted code baseline reviewed for this specification: `9d050e41d989fa17f0db8b36da313e1a4c96b449`
- Reviewed baseline message: `Add development roadmap`
- Implementation start commit: **TBD at implementation handoff after this specification is committed**
- Governing roadmap: `ROADMAP.md`
- Governing predecessor specification: `BUILD_06_B_SPECIFICATION.md`
- Governing predecessor acceptance record: `BUILD_06_B_ACCEPTANCE_RECORD.md`
- Required accepted foundation: Build 05-B / Build 06-A / Build 06-B
- Build position: Crown Moulding production build on top of the accepted Finish Attachment / Baseboard foundation
- Final primary features:
  - production Crown Moulding
  - Ceiling-reference downward Profile placement
  - standard and Custom Profile support
  - Profile thumbnail selection UI
- Deliberately not part of this build:
  - Room recognition
  - Ceiling Mesh generation
  - Door / Window integration
  - automatic Opening-driven Finish Exclusion
  - Build 05-C Wall merge
  - Build 07 Stair work

---

# 1. Purpose

Build 06-C completes the initial two main Wall Finish types planned for Build 06:

```text
Build 06-A
Finish Attachment Foundation
        ↓
Build 06-B
Baseboard / 巾木
        ↓
Build 06-C
Crown Moulding / 廻り縁
+ Profile Thumbnail UI
```

Build 06-C MUST reuse the accepted Build 06-A / 06-B canonical attachment architecture.

It MUST NOT create a separate Crown-only Wall attachment system.

The governing relationship remains:

```text
canonical Wall data
        +
FinishRun / FinishSpan canonical attachment data
        +
Profile identity / revision / Run-local parameters
        +
FinishExclusion records
        +
Finish type / vertical reference
        ↓
resolved attachment path
        ↓
visible range calculation
        ↓
corner / endpoint resolution
        ↓
resolved orientation-specific Profile
        ↓
derived managed geometry
```

Generated Curve / Mesh data remains derived data.

The source of truth remains canonical Wall / Finish / Profile / Exclusion data.

---

# 2. Roadmap position

The development order established by `ROADMAP.md` MUST NOT be changed by this specification.

The sequence remains:

```text
05-B  Wall System                         ACCEPTED
05-C  Wall re-merge                       BACKLOG
06-A  Finish Attachment Foundation        ACCEPTED
06-B  Baseboard                           ACCEPTED
06-C  Crown Moulding + Thumbnail UI       THIS BUILD
07-A  Stair Core + Straight closed stair
07-A2 Stair Core open-riser validation
08-A  Minimal Room / Boundary + Floor
08-B  Ceiling + void / hole basics
09-A  Window / Door Asset Root + Anchor
09-B  Live Boolean Cutter
09-C  Finish Exclusion integration
Integration 1
07-B / 07-C / 07-D
10    Production Hardening
```

Build 06-C MUST NOT pull Build 07 / 08 / 09 features forward merely because they may eventually interact with Crown Moulding.

---

# 3. Accepted baseline

Build 06-B overall is already ACCEPTED.

The accepted baseline includes, at minimum:

```text
Persistent Wall ID
Object Pointer + expected Wall ID validation
FinishRun / FinishSpan
LEFT / RIGHT
FORWARD / REVERSE
Partial Run boundaries
Wall split dependency remap
Manual Exclusion
Exclusion fragment remap
SIMPLE
BEVEL
ROUNDED
Custom POLY
Custom BEZIER
Custom immutable project-local snapshots
Run-local Custom uniform scale
MITER
BUTT
Profile-aware shading
Material preservation
Save / reopen
Undo / Redo
Transactional rollback
Editable Mesh conversion
Legacy SIMPLE_10X60 compatibility
```

Build 06-C MUST preserve these accepted contracts.

Build 06-C does not reopen the accepted Baseboard architecture for redesign unless a demonstrable shared-foundation defect requires a correction.

---

# 4. Current implementation facts

The current accepted source already contains several Crown prerequisites.

At implementation start:

```text
JHM_FinishProperties.finish_type
    BASEBOARD
    CROWN

vertical_reference
    FLOOR
    CEILING
    ABSOLUTE

Scene defaults
    floor_reference_z_mm
    ceiling_reference_z_mm

FinishSpan Wall reference
    wall_object Pointer
    expected_wall_id

Profile families
    SIMPLE
    BEVEL
    ROUNDED
    Custom

Custom Profile canonical convention
    +X = projection direction
    +Y = positive canonical vertical direction
    min_x >= 0
    min_y >= 0
    clockwise winding
```

However, Crown is not yet a production feature.

The current production Profile placement maps canonical Profile `+Y` to world `+Z`.

Therefore simply setting:

```text
finish_type = CROWN
vertical_reference = CEILING
```

would place the Profile above the ceiling reference.

Build 06-C MUST solve this explicitly.

---

# 5. Core design decision — Crown uses derived vertical orientation

Build 06-C MUST NOT redefine accepted stored Baseboard / Custom Profile snapshots.

The canonical Profile definition remains unchanged.

The persistent Profile convention remains:

```text
canonical Profile +X = away from selected Wall face
canonical Profile +Y = positive canonical Profile vertical axis
```

For generated placement, define a derived vertical orientation:

```text
BASEBOARD
vertical_sign = +1
canonical +Y -> world +Z

CROWN
vertical_sign = -1
canonical +Y -> world -Z
```

Therefore:

```text
BASEBOARD at reference_z
world_z = reference_z + profile_y

CROWN at reference_z
world_z = reference_z - profile_y
```

For standard Profiles whose scaled canonical bounds satisfy:

```text
min_y = 0
max_y = profile_height
```

a Crown with:

```text
ceiling_reference_z = 2500 mm
Profile height = 60 mm
```

has:

```text
top    = 2500 mm
bottom = 2440 mm
```

For general Custom Profiles, vertical placement MUST use the actual **scaled resolved Profile bounds**, not only `profile_height`.

General Crown bounds:

```text
Crown bottom = reference_z - max_y
Crown top    = reference_z - min_y
```

where `min_y` and `max_y` are taken from the resolved Profile after Run-local uniform scale.

Example:

```text
Custom Profile scaled Y bounds = 10 .. 70 mm
reference_z = 2500 mm

Crown bottom = 2430 mm
Crown top    = 2490 mm
```

The Custom Profile's authored offset from the canonical origin is preserved. Build 06-C MUST NOT automatically translate a Custom Profile so that `min_y` becomes zero or force its top edge onto the reference plane.

The same principle applies horizontally: registered canonical X offsets are preserved; the implementation MUST NOT silently re-center or re-anchor Custom Profile X coordinates.

This is a derived placement rule.

It MUST NOT rewrite the stored Custom Profile contour into negative-Y canonical coordinates.

---

# 6. Why canonical Custom Profiles remain +X / +Y

The Roadmap warns not to blindly reuse Baseboard coordinate restrictions for Crown.

Build 06-C addresses that warning by separating:

```text
stored canonical Profile coordinates
```

from:

```text
Finish-type-specific derived world orientation
```

Custom Profile revision 1 may therefore continue to require:

```text
min_x >= 0
min_y >= 0
```

because `+Y` is canonical storage, not a statement that Crown must grow upward in world space.

For Crown, that same canonical `+Y` is mapped downward by `vertical_sign = -1`.

This preserves:

- accepted Custom Profile files
- registered snapshots
- Profile IDs
- Profile revisions
- Project-local Profile library
- source independence
- existing Baseboard behavior

No destructive Custom Profile migration is required for 06-C.

---

# 7. Horizontal orientation remains unchanged

Build 06-C MUST preserve the accepted Wall-side contract.

```text
LEFT / RIGHT
```

remain canonical relative to Wall:

```text
START -> END
```

Traversal remains independent:

```text
FORWARD / REVERSE
```

The existing horizontal Profile orientation is retained conceptually:

```text
horizontal_sign = +1 or -1
```

depending on canonical Wall side and traversal.

Crown MUST NOT introduce a second definition of LEFT / RIGHT.

---

# 8. Two-axis orientation parity

Build 06-C introduces two independent derived signs:

```text
horizontal_sign
vertical_sign
```

The orientation transform is conceptually:

```text
x' = horizontal_sign * x
y' = vertical_sign   * y
```

A reflection changes winding whenever the 2D transform determinant is negative:

```text
orientation_parity = horizontal_sign * vertical_sign
```

Rule:

```text
if orientation_parity > 0:
    transformed point order may remain canonical

if orientation_parity < 0:
    transformed point order MUST be reversed
    or an exactly equivalent winding-preserving method MUST be used
```

Examples:

| Horizontal | Vertical | Reflection parity | Winding action |
|---|---:|---:|---|
| +1 | +1 Baseboard | +1 | keep |
| -1 | +1 Baseboard | -1 | reverse |
| +1 | -1 Crown | -1 | reverse |
| -1 | -1 Crown | +1 | keep |

The implementation MAY use another mathematically equivalent formulation.

The result MUST preserve correct outward surface orientation.

---

# 9. Negative Object Scale remains forbidden

Build 06-C MUST NOT implement Crown by setting:

```text
Scale Z = -1
```

or:

```text
Scale X = -1
```

or any other persistent/generated negative Object Scale.

Managed Crown geometry and derived Profile objects/data MUST retain identity transform unless an existing accepted mechanism explicitly requires otherwise.

The orientation MUST be expressed in generated coordinates / contour ordering, not Object transform handedness.

This preserves predictable:

- normals
- Mesh conversion
- material behavior
- save / reopen
- downstream Blender editing

---

# 10. Smooth-edge orientation must follow parity

Custom BEZIER Profile snapshots persist canonical smooth-edge intent.

When point order is reversed because orientation parity is negative, the smooth edge indices MUST be remapped to the corresponding physical edges.

The accepted Build 06-B horizontal-only remapping rule MUST be generalized so that it depends on orientation parity, not only horizontal mirroring.

Conceptually:

```text
reverse_order = horizontal_sign * vertical_sign < 0
```

If `reverse_order` is true:

```text
canonical edge i
    -> reversed edge (n - 2 - i) mod n
```

or mathematically equivalent.

A Crown Custom BEZIER MUST NOT smooth the wrong edge because of vertical reflection.

---

# 11. Standard Profile reuse

Build 06-C SHALL reuse the accepted standard Profile identities:

```text
SIMPLE
BEVEL
ROUNDED
```

No new persistent Crown-only Profile IDs are required for revision 1.

The same canonical standard definition may be used by Baseboard and Crown.

The Finish type controls derived vertical orientation.

Expected Crown appearance:

```text
SIMPLE
    rectangular Profile hanging downward from ceiling reference

BEVEL
    vertically reflected accepted BEVEL shape
    lower room-facing corner receives the accepted chamfer relationship

ROUNDED
    vertically reflected accepted ROUNDED shape
    lower room-facing corner receives the accepted round relationship
```

This reuse MUST NOT change the accepted Baseboard appearance.

If implementation evidence proves that one shared identity cannot safely represent both uses, a later specification correction may introduce Crown-specific Profile IDs, but that redesign is NOT the default plan.

---

# 12. Custom Profile reuse

Registered Project Custom Profiles MUST be usable for both:

```text
BASEBOARD
CROWN
```

without duplicating the stored definition.

For Crown:

```text
same profile_id
same profile_revision
same schema_version
same immutable contour
same smooth-edge intent
same run-local uniform scale
different derived vertical orientation
```

The source Curve remains non-authoritative after registration.

Deleting the source Object MUST NOT invalidate Crown use.

---

# 13. Profile identity remains independent of Finish type

`finish_type` and `profile_id` are separate concepts.

Conceptually:

```text
FinishRun
├ finish_type = BASEBOARD / CROWN
├ profile_id
├ profile_revision
├ profile_schema_version
├ run-local Profile parameters
└ ...
```

Do NOT encode Crown by silently rewriting:

```text
SIMPLE -> CROWN_SIMPLE
```

unless a future explicit migration/specification introduces such identities.

For Build 06-C revision 1, `finish_type` determines placement orientation while Profile identity determines cross-section definition.

---

# 14. Derived Profile cache identity

Any derived Profile cache identity MUST include all information that changes generated Profile geometry.

At minimum this now includes:

```text
profile identity
profile revision
profile schema
run-local Profile parameters
Custom uniform scale
canonical contour / shading identity as applicable
horizontal orientation
vertical orientation
vertical reference placement
```

A Baseboard and Crown with otherwise identical Profile values MUST NOT accidentally reuse the wrong orientation-specific cached derived Profile.

---

# 15. Vertical reference contract

The accepted generic vertical resolver remains authoritative.

```text
FLOOR
CEILING
ABSOLUTE
```

remain valid canonical reference concepts.

Build 06-C MUST NOT silently change the existing meaning of `vertical_offset_mm`.

The current reference arithmetic remains compatible.

For normal Crown creation:

```text
finish_type = CROWN
vertical_reference = CEILING
vertical_offset_mm = 0
```

is the default.

For normal Baseboard creation:

```text
finish_type = BASEBOARD
vertical_reference = FLOOR
vertical_offset_mm = 0
```

remains the default.

`ABSOLUTE` remains a generic Foundation capability.

`vertical_offset_mm` keeps its existing **world-Z sign meaning**. It is not multiplied by `vertical_sign`.

Therefore, for Crown:

```text
ceiling_reference_z_mm = 2500
vertical_offset_mm = -20
```

means the Crown attachment reference is 20 mm lower:

```text
resolved reference_z = 2480 mm
```

and the Crown Profile then extends downward from that resolved reference according to its actual scaled bounds.

The implementation does not need to add a new persistent Crown-specific height field.

---

# 16. Crown reference plane

For Crown, the resolved vertical reference is the canonical placement origin plane.

With:

```text
vertical_sign = -1
```

and scaled resolved Profile bounds:

```text
min_y
max_y
```

the generated vertical range is:

```text
reference_z - max_y
    <= world Z <=
reference_z - min_y
```

For standard Profiles where `min_y = 0`, the upper edge coincides with `reference_z`.

For a valid Custom Profile where `min_y > 0`, the authored gap from the canonical origin is preserved; the upper edge does **not** automatically snap to `reference_z`.

The implementation MUST use the resolved Profile contour / bounds as authored and scaled. It MUST NOT infer Crown placement from `height_mm` alone.

---

# 17. No automatic Ceiling Mesh dependency

Build 06-C MUST NOT depend on Build 08-B Ceiling Mesh generation.

The Crown reference uses the already-persisted scene reference:

```text
ceiling_reference_z_mm
```

or another already-supported explicit vertical reference.

Future Room / Ceiling systems may update or drive that reference through later explicit architecture.

Build 06-C does not require a Ceiling Mesh to exist.

---

# 18. No automatic Wall-height / Ceiling collision system

Build 06-C is not a full 3D architectural collision system.

It MUST validate finite Profile placement and all accepted horizontal path safety rules.

It does NOT need to automatically infer:

- whether every Wall physically reaches the global ceiling
- soffits
- stepped ceilings
- vaulted ceilings
- sloped ceilings
- ceiling-to-Wall construction detail

Those belong to later specifications if required.

The Crown reference is explicit and user-controlled in 06-C.

---

# 19. Canonical generation order

Build 06-C MUST retain the Roadmap generation order:

```text
FinishRun canonical data
        ↓
Canonical span / path resolution
        ↓
Exclusion subtraction
        ↓
Visible range resolution
        ↓
Corner / endpoint resolution
        ↓
Resolved Profile
        ↓
Finish-type orientation
        ↓
Managed derived geometry
```

The implementation MUST NOT compute a Crown Miter across geometry already removed by Exclusion.

Every Exclusion-created visible-range end remains an independent BUTT end.

---

# 20. MITER behavior

The accepted XY path / Miter system is reused.

Crown vertical orientation MUST NOT change Wall-plan Miter semantics.

Supported paths remain:

- straight
- 90-degree connected Wall path
- accepted oblique connected Wall path
- accepted Continuation topology
- accepted LEFT / RIGHT and traversal combinations

Crown Miter geometry MUST:

- remain continuous on supported corners
- have no gap
- have no overlap
- have no abnormal spike
- preserve outward normals
- preserve Profile shape through the corner
- obey existing miter safety limits

---

# 21. BUTT behavior

Crown free ends use the same production meaning as Baseboard:

> Cut the generated Finish on a plane perpendicular to the local path direction and close the cross-section.

BUTT is required for:

- free Run start
- free Run end
- partial-boundary start/end
- Exclusion-created ends
- junction-aware survivor ends where accepted Exclusion logic requires independent termination

Open / hollow Crown ends are not acceptable.

---

# 22. Partial Crown placement

The accepted FinishSpan boundary model is reused.

Crown MUST support partial placement without creating a second path system.

Example:

```text
Wall 0 ------------------------ 4000 mm

Crown Run:
500 --------------------- 3200
```

The first and last partial boundaries are BUTT ends unless an accepted connected transition explicitly applies.

Partial Crown boundaries MUST survive:

- regeneration
- Undo / Redo
- save / reopen
- editable Mesh conversion

---

# 23. Manual Exclusion

Build 06-C SHALL reuse the accepted Manual Exclusion system.

Manual Exclusion applies to Crown by the same canonical Wall interval / side relationship.

Build 06-C does NOT yet automatically decide whether a Door or Window vertically intersects the Crown.

That vertical Opening logic belongs to Build 09-C.

For 06-C:

```text
Manual Exclusion
    = explicit user-authored Finish gap
```

and remains valid for both Baseboard and Crown.

---

# 24. Crown valid-empty

Crown MUST preserve the accepted distinction between:

```text
VALID_EMPTY
```

and invalid managed state.

If active Exclusion coverage removes the entire Crown Run:

- FinishRun remains managed and valid
- Finish ID remains
- FinishSpan data remains
- Profile identity / parameters remain
- vertical reference and offset remain
- Exclusion identity remains
- visible range count becomes zero
- UI should report the equivalent of `全区間除外`
- editable Mesh conversion MUST be explicitly rejected because no Crown solid exists

Removing or disabling the Exclusion later MUST regenerate the Crown from the **current** canonical data and current resolved reference values.

Required integration sequence:

1. create Crown
2. exclude the entire Run
3. change ceiling reference
4. execute bulk regeneration
5. save / close / reopen
6. remove or disable the full Exclusion
7. verify Crown returns at the new reference and extends downward using actual resolved bounds

---

# 25. Future 09-C compatibility

Build 06-C MUST leave room for future height-aware Opening exclusion.

Later Build 09-C will need to distinguish cases such as:

```text
ordinary low Window
    does not intersect Baseboard height
    -> Baseboard continues

Door that does not reach Crown height
    -> Crown continues
```

Therefore Build 06-C MUST NOT redefine `FinishExclusion` as inherently meaning a full-height Wall opening.

Manual Exclusion remains explicit Finish coverage.

---

# 26. Material contract

Crown Profile identity and Crown material assignment are separate concerns.

Existing material assignment MUST survive, where relevant:

```text
Profile parameter edit
Profile kind switch
Custom Profile switch
Manual Exclusion edit
Partial-boundary edit
Wall edit
regeneration
scene reference change + explicit regeneration
save / reopen
editable Mesh conversion
```

Changing Profile MUST NOT silently replace the Crown material.

---

# 27. Managed / editable contract

Crown follows the existing one-way contract:

```text
Managed Crown
    ↓
[編集可能Meshとして確定]
    ↓
ordinary Blender Mesh
    ↓
Add-on management ends
```

After conversion:

- normal Blender Edit Mode is allowed
- normal materials / UV / modifiers are Blender-managed
- Add-on regeneration no longer applies
- reverse conversion to managed Crown is not required

---

# 28. Editable Mesh topology

Crown editable Mesh conversion MUST preserve the existing production topology contract.

For supported generated solids:

```text
boundary edges = 0
non-manifold edges = 0
finite non-zero signed volume
identity Object scale
correct outward normals
```

For accepted orientation matrices, signed volume direction MUST remain consistent.

No post-conversion normal-flip repair should be used to hide an incorrect derived Profile winding design.

Correct winding must be produced before / during generation.

---

# 29. Standard shading

SIMPLE and BEVEL Crown regions remain flat where the canonical Profile is planar.

ROUNDED Crown MUST retain Profile-aware smoothing:

- rounded region smooth
- planar regions flat
- caps flat
- BUTT caps flat
- no accidental full-object smooth shading

Vertical reflection MUST NOT move smoothing to the wrong physical Profile edges.

---

# 30. Custom shading

Custom POLY remains hard / planar according to accepted rules.

Custom BEZIER retains its persisted smooth-edge intent.

For Crown:

- vertical reflection MUST preserve the intended physical smooth edges
- horizontal + vertical double reflection MUST also preserve them
- caps remain flat
- irregular transition faces remain flat unless explicitly part of the Profile smooth intent

Custom Mesh shading logic MUST use the **same horizontally and vertically transformed contour coordinates** as production geometry, together with the correspondingly remapped smooth-edge indices.

It is not sufficient to remap smooth-edge numbers while continuing to compare against a horizontal-only or world-up contour.

Any shading matcher that compares Profile-relative heights / distances to Mesh coordinates MUST account for `vertical_sign` consistently.

Runtime testing MUST include at least one **vertically asymmetric Custom BEZIER** Profile so that an incorrect top/bottom interpretation cannot pass merely because the Profile is vertically symmetric.

---

# 31. Finish creation UX

Build 06-C MUST make Finish type explicit before path collection starts.

The path-start operator SHOULD gain an explicit property equivalent to:

```text
finish_type
    BASEBOARD
    CROWN
```

The UI may use either:

```text
Finish type selector
+ LEFT / RIGHT start buttons
```

or:

```text
Baseboard LEFT
Baseboard RIGHT
Crown LEFT
Crown RIGHT
```

The exact layout may differ.

The user MUST NOT have to create a Baseboard first and manually corrupt hidden data into a Crown.

---

# 32. Creation defaults

When committing a new path:

For Baseboard:

```text
finish_type = BASEBOARD
vertical_reference = FLOOR
vertical_offset_mm = 0
```

For Crown:

```text
finish_type = CROWN
vertical_reference = CEILING
vertical_offset_mm = 0
```

Default standard Profile:

```text
SIMPLE
revision 1
schema 1
height 60 mm
projection 10 mm
```

may remain shared unless a later UX decision changes only user-facing defaults.

Changing these defaults must not change existing persisted Runs.

---

# 33. Finish type is not inferred from Profile

Do NOT infer Crown from:

- Profile name
- Profile dimensions
- Custom Profile source name
- vertical reference alone
- Object position
- Object name

`finish_type` is canonical.

---

# 34. Finish type conversion is not required

Build 06-C does NOT require a generic:

```text
Convert Baseboard <-> Crown
```

operator.

The initial production workflow may require the type to be selected at creation.

If implementation adds type conversion anyway, it MUST be transactional and MUST explicitly resolve:

- vertical reference
- orientation
- geometry
- safety
- material
- rollback

No silent in-place reinterpretation is allowed.

---

# 35. Path preview

The interactive path preview SHOULD represent the selected Finish type at an appropriate attachment elevation.

For Crown, the preview SHOULD be displayed near the resolved ceiling reference rather than near floor Z.

For Baseboard, the existing accepted preview behavior MUST not regress.

Preview is derived / visual-only data.

It MUST NOT become canonical Finish geometry.

If final generation rejects a path, preview MUST NOT present that path as apparently valid.

---

# 36. Production labels

The UI should stop presenting accepted production Baseboard as a test-only feature.

User-facing labels should use clear terms such as:

```text
巾木 / Baseboard
廻り縁 / Crown
```

The exact bilingual layout may vary.

Persistent enum identifiers remain:

```text
BASEBOARD
CROWN
```

---

# 37. Selected Crown UI

When a managed Crown is selected, the UI MUST expose enough state to diagnose it.

At minimum:

```text
種類: CROWN / 廻り縁
Profile name / identity
Profile dimensions or Custom scale
reference: CEILING / ABSOLUTE / etc.
reference height / relevant offset
Span count
visible range count
managed state
Manual Exclusion count
```

Profile edit, boundary edit, Exclusion operations, regeneration, repair, Mesh conversion, and deletion remain available as applicable.

---

# 38. Profile Library registration UI text

The current Project Custom Profile registration rule remains canonical +X / +Y.

The UI text MUST avoid misleading Crown users into believing `+Y` always means world-up after placement.

A suitable concept is:

```text
Custom Profile canonical coordinates
+X = Wallからの出幅方向
+Y = canonical vertical axis

Baseboard: +Y -> world up
Crown:     +Y -> world down from ceiling
```

Exact Japanese wording may differ.

The registration constraints remain authoritative.

---

# 39. Profile Thumbnail UI — goal

Build 06-C MUST complete the Roadmap requirement for Profile thumbnail selection.

The purpose is to replace a purely textual Profile choice with a visual Profile browser.

Minimum Profile set shown:

```text
SIMPLE
BEVEL
ROUNDED
all valid Project Custom Profiles
```

The UI must remain usable even if thumbnail generation fails.

---

# 40. Thumbnail data is derived

Thumbnail images / previews are NOT canonical Profile data.

They MUST be rebuildable from:

```text
standard Profile resolver
or
persisted Custom Profile snapshot
```

Do NOT make Custom Profile validity depend on:

- source Curve Object
- external PNG file
- temporary filesystem path
- thumbnail cache survival

Deleting a source Curve after registration MUST NOT remove the Profile thumbnail permanently.

It may be regenerated from the stored snapshot.

---

# 41. Thumbnail shape contract

Initial 06-C thumbnail behavior uses a **representative-shape browser**, not a promise that the thumbnail is an exact-to-scale rendering of the selected Run's current numeric dimensions.

For standard Profiles, the browser MAY use stable representative dimensions such as the current production defaults to make SIMPLE / BEVEL / ROUNDED visually distinguishable.

The selected Run's actual numeric values remain authoritative and MUST be shown separately in the Profile parameter UI.

A thumbnail MUST NOT be labeled or presented in a way that implies exact current Run dimensions unless the implementation actually renders those exact dimensions.

For Custom Profiles, the persisted snapshot contour is the representative shape source; Run-local uniform scale may remain a separate numeric value rather than forcing a unique thumbnail for every scale.

A thumbnail SHOULD depict the Profile contour clearly.

Requirements:

- preserve Profile aspect ratio
- fit within thumbnail bounds with padding
- do not stretch width and height independently
- distinguish wall-side / projection direction enough to avoid mirror confusion
- show SIMPLE / BEVEL / ROUNDED as visibly different
- show Custom contour from persisted snapshot

A context-aware Crown selector SHOULD present the Profile in Crown application orientation.

A Project library-only view MAY show canonical orientation if clearly consistent.

---

# 42. Thumbnail selection identity

Selecting a thumbnail MUST select by stable Profile identity.

Do NOT persist selection using:

```text
UI list row number
thumbnail cache index
image datablock name
temporary icon ID
```

The actual selected Profile remains:

```text
profile_id
profile_revision
profile_schema_version
```

plus Run-local parameters.

---

# 43. Thumbnail Profile apply is transactional

Clicking / applying a Profile thumbnail to a managed Finish is a managed edit.

The operation MUST:

```text
snapshot old canonical Profile values
apply provisional Profile identity/parameters
resolve Profile
resolve Finish visible ranges
validate Miter / blockers / endpoints
prepare replacement derived data
commit only on success
```

On failure:

```text
restore old Profile values
keep previous valid geometry
report error
```

Merely opening / browsing the thumbnail UI MUST NOT mutate the FinishRun.

---

# 44. Standard Profile numeric parameters remain available

Thumbnail UI selects Profile identity.

It MUST NOT remove the ability to edit Run-local numeric parameters.

For standard Profiles:

```text
height
projection
bevel where applicable
radius where applicable
```

remain editable.

For Custom Profiles:

```text
uniform scale
```

remains editable.

The exact UI may use:

- one thumbnail browser + one numeric edit dialog
- thumbnail browser with inline parameter fields
- another equivalent clear workflow

---

# 45. Thumbnail selected state

The currently assigned Profile SHOULD be visually identifiable in the thumbnail UI.

For example:

- selected card outline
- active marker
- pressed state
- explicit text marker

Exact styling is implementation-defined.

The active marker must correspond to stable Profile identity, not merely card position.

---

# 46. Thumbnail cache lifecycle

The preview cache may be rebuilt:

- on add-on registration
- on file load
- on Profile library change
- lazily when Profile UI opens

Exact strategy is implementation-defined.

Required behavior:

- no stale preview after Profile deletion
- no crash after Undo / Redo
- no dependency on deleted source Curve
- no persistent corruption if preview cache is missing
- save / reopen rebuilds usable thumbnails

---

# 47. Thumbnail fallback

If thumbnail generation fails for one Profile:

- canonical Profile data remains untouched
- the UI MUST remain operable
- a textual fallback MAY be shown
- failure of one preview MUST NOT hide all other valid Profiles
- selecting a valid Profile through fallback remains possible if practical

A preview failure is not permission to silently replace the Profile.

---

# 48. Profile deletion safety remains unchanged

Referenced Project Custom Profile deletion MUST continue to be rejected.

Unused Custom Profiles may be deleted.

Thumbnail UI MUST update accordingly.

Deleting an unused Profile:

```text
removes its browser item
does not renumber or rewrite other Profile identities
does not alter unrelated FinishRuns
```

Undo / Redo MUST remain valid.

---

# 49. Baseboard thumbnail compatibility

The thumbnail browser is not Crown-only.

It MUST work for selected Baseboard Runs as well.

Build 06-C MUST NOT leave Baseboard with one unrelated old Profile workflow while Crown receives a completely separate Profile system.

Shared UI / resolver architecture is preferred.

---

# 50. Baseboard geometry must remain unchanged

Introducing `vertical_sign` MUST preserve accepted Baseboard behavior.

For Baseboard:

```text
vertical_sign = +1
```

must reproduce the accepted 06-B geometry.

At minimum regression must cover:

- SIMPLE
- ROUNDED
- Custom BEZIER
- one LEFT / RIGHT orientation pair
- Manual Exclusion
- editable Mesh conversion

Full 06-B Blender runtime acceptance does NOT need to be repeated unless a shared-foundation defect is discovered.

---

# 51. Legacy SIMPLE_10X60 remains supported

Build 06-C MUST retain the accepted non-destructive interpretation of:

```text
SIMPLE_10X60
```

Existing old Baseboard files must not become invalid because Crown support was added.

Crown creation does not need to produce new legacy IDs.

---

# 52. Missing / corrupt Profile behavior

The existing invalid managed-state contract remains.

If Profile resolution fails because of:

- missing Profile
- missing Custom definition
- unsupported revision
- unsupported schema
- corrupt Custom snapshot

the system MUST NOT silently substitute SIMPLE.

Crown and Baseboard both follow the same rule.

---

# 53. Transactional Crown edits

All Crown canonical edits whose canonical mutation and derived regeneration occur inside one managed operation must preserve atomicity.

This includes, where applicable:

- Profile selection
- Profile parameter edit
- Custom scale edit
- Partial boundary edit
- Manual Exclusion add/edit/remove/toggle

For such operations, failure MUST leave:

```text
old valid canonical Finish state
+
old valid generated geometry
```

synchronized.

A Scene-level edit of:

```text
ceiling_reference_z_mm
```

is a **separate operation** from a later explicit `仕上げを一括再生成`.

Build 06-C MUST NOT pretend that a failed later regeneration can roll back a ceiling-reference edit that was already committed as an earlier user action.

---

# 54. Scene ceiling reference changes

Editing:

```text
scene.jhm_new_wall_defaults.ceiling_reference_z_mm
```

does not need to regenerate every Crown continuously on each keystroke.

The ceiling-reference edit itself is an independent user operation.

The existing explicit:

```text
仕上げを一括再生成
```

workflow may remain as the operation that applies current Scene reference values to derived Finish geometry.

When executed:

- all targeted derived Finish replacements succeed together or none of them are installed
- all affected Crowns regenerate from current canonical Finish data and the **current** ceiling reference
- Baseboards retain their own reference behavior
- one invalid Finish must not leave a partially updated mixed scene
- if regeneration fails, the already-entered ceiling-reference value remains unchanged
- the previous valid generated Finish geometry remains installed
- the add-on MUST report or visibly indicate that derived geometry is now **out of date with the current Scene reference and requires regeneration**

The implementation MAY use a lightweight dirty/out-of-date indication; a large new dependency-update framework is not required for 06-C.

Undo semantics remain distinct:

```text
Undo ceiling-reference edit
```

and:

```text
Undo successful bulk regeneration
```

are separate user actions when they were performed separately.

---

# 55. Wall split remap

Crown FinishSpans and Crown Manual Exclusions MUST use the same dependency remap as Baseboard.

After a valid Wall split:

- Crown logical placement remains physically equivalent
- FinishRun identity remains
- spans remap
- applicable Exclusion fragments remap
- reference validation remains pointer + expected Wall ID
- generated Crown regenerates from remapped canonical data

No Crown-specific Wall split code path should duplicate the dependency architecture.

---

# 56. Wall deletion behavior

Build 06-C MUST preserve the accepted dependency rules for Wall deletion.

Do not silently reconnect unrelated Crown spans after deletion.

If a FinishRun becomes separated according to existing dependency rules, derived geometry must reflect the canonical result or managed invalid state according to the accepted Foundation.

No automatic full-room Crown routing is introduced.

---

# 57. Reference trust

All Crown Wall references remain subject to:

```text
Object Pointer
+
expected persistent Wall ID
+
uniqueness / managed-state validation
```

Do NOT resolve Crown Wall references by Object name.

Do NOT guess among duplicate Wall IDs.

Do NOT scan for the nearest Wall to repair a broken reference.

Repair must remain explicit and uniquely provable.

---

# 58. Unsupported 06-C features

The following are explicitly out of scope:

```text
Build 05-C automatic / explicit Wall merge implementation
closed FinishRun
automatic Room recognition
automatic full-room Crown routing
Floor Mesh generation
Ceiling Mesh generation
sloped / vaulted Ceiling Crown
multi-height automatic Crown routing
Door asset generation
Window asset generation
Live Boolean Cutter
automatic Door / Window Finish Exclusion
Opening height intersection logic
Chair Rail
Picture Rail
cornice asset placement
ornamental corner blocks
coping / scribing
return-to-wall decorative Crown ends
arbitrary 3D Custom Profile
holes in Custom Profile
multiple Custom contours
concave Custom Profile revision 1 expansion
non-uniform Custom Profile scale
live source-linked Custom Profiles
automatic reverse engineering from edited Mesh
BIM semantics
quantity takeoff
construction documents
Stair generation
```

Do not substitute any of these for required Crown stability / thumbnail work.

---

# 59. Build identification

Current base version:

```text
(0, 6, 3)
```

Build 06-C implementation MAY increment add-on version according to project versioning practice.

Version number alone is not acceptance.

During implementation, the description SHOULD identify the active candidate stage.

Final accepted Build 06-C MUST identify itself unambiguously as:

```text
Build 06-C: Crown Moulding and Profile Thumbnail UI
```

or wording with the same exact meaning.

Do not leave final accepted 06-C identified as Build 06-B.

---

# 60. Build 06-C implementation stages

Build 06-C is divided into three implementation / acceptance stages.

```text
Stage 1
Crown Foundation + SIMPLE

Stage 2
BEVEL / ROUNDED / Custom Crown

Stage 3
Profile Thumbnail UI + Final 06-C Acceptance
```

Do not mark Build 06-C overall ACCEPTED until all three stages pass.

---

# 61. Stage 1 — Crown Foundation + SIMPLE

Stage 1 establishes Crown placement and orientation correctness.

Required Stage 1 production scope:

```text
explicit Crown path creation
finish_type = CROWN
default CEILING reference
vertical_sign = -1
SIMPLE Profile
LEFT / RIGHT
FORWARD / REVERSE
90-degree MITER
supported oblique MITER
free BUTT
partial Run
Manual Exclusion
Crown valid-empty / full Exclusion
junction-aware Exclusion BUTT
Material preservation
Undo / Redo
Save / reopen
Editable Mesh
Baseboard regression
```

Stage 1 MUST NOT implement thumbnail UI as a substitute for Crown geometry correctness.

---

# 62. Stage 1 pure orientation helper

Stage 1 SHOULD isolate the finish-type vertical orientation into a testable pure rule conceptually equivalent to:

```text
profile_vertical_sign(finish_type)

BASEBOARD -> +1
CROWN     -> -1
unknown   -> error
```

Exact function names may differ.

Do not scatter:

```text
if finish_type == "CROWN"
```

coordinate inversions independently across multiple modules.

---

# 63. Stage 1 placement helper

The production placement path SHOULD generalize the accepted Profile orientation API conceptually from:

```text
placement_adjusted_contour(
    profile,
    horizontal_sign,
    vertical_base
)
```

to something equivalent to:

```text
placement_adjusted_contour(
    profile,
    horizontal_sign,
    vertical_sign,
    vertical_base
)
```

Exact API may differ.

The important requirement is one authoritative orientation calculation.

---

# 64. Stage 1 cache regression

Any cache / derived Profile identity MUST distinguish:

```text
BASEBOARD + same Profile + same Z
```

from:

```text
CROWN + same Profile + same Z
```

when their vertical orientation differs.

Tests MUST catch accidental reuse.

---

# 65. Stage 1 Crown SIMPLE geometry

For:

```text
ceiling = 2500
SIMPLE height = 60
projection = 10
```

the Crown MUST occupy:

```text
Z = 2440 .. 2500 mm
```

and project into the selected side by 10 mm.

It MUST NOT occupy:

```text
2500 .. 2560 mm
```

---

# 66. Stage 1 orientation matrix

Crown SIMPLE runtime acceptance MUST cover all four canonical orientation combinations:

```text
LEFT + FORWARD
LEFT + REVERSE
RIGHT + FORWARD
RIGHT + REVERSE
```

For every case verify:

- projection is on intended Wall side
- Crown hangs downward
- no negative Object scale
- no inverted visible surface
- editable Mesh normals are outward
- signed volume direction is consistent
- identity transform is retained

---

# 67. Stage 1 Miter cases

Runtime acceptance MUST include at least:

```text
90-degree Crown Miter
one supported oblique Crown Miter
```

with non-trivial projection.

Verify:

- no gap
- no overlap
- no spike
- correct side
- correct vertical orientation
- Profile remains attached to ceiling reference
- managed state normal

---

# 68. Stage 1 Partial Run

Test a straight Crown whose first and last boundaries do not reach Wall endpoints.

Verify:

- correct partial length
- ceiling attachment
- two closed BUTT ends
- no unwanted Miter extension
- Mesh conversion closed / manifold

---

# 69. Stage 1 Manual Exclusion

Test one Crown Manual Exclusion.

Verify:

- canonical FinishSpan remains
- visible geometry splits into correct ranges
- no join across gap
- Exclusion-created ends are closed BUTT
- removing Exclusion restores geometry
- Material survives

---

# 70. Stage 1 junction-aware Exclusion

Test an Exclusion that reaches a canonical connected-Wall junction.

Verify:

- no Miter bridge across excluded junction
- surviving range terminates independently
- no spike
- no Wall penetration
- editable Mesh remains closed

This reuses the accepted 06-B topology rule.

---

# 71. Stage 1 Profile edit rollback

Test a valid Crown SIMPLE dimension edit.

Then test an unsafe edit rejected by existing Miter / blocker safety.

On failure verify:

```text
old dimensions restored
old generated Crown retained
material retained
managed state valid
```

---

# 72. Stage 1 Ceiling reference regeneration

Create Crown at one ceiling reference.

Change:

```text
ceiling_reference_z_mm
```

then use explicit global Finish regeneration.

Verify on success:

- Crown attachment placement uses the new ceiling reference
- Profile still hangs downward using actual resolved bounds
- Baseboard Floor-reference geometry does not incorrectly move with ceiling
- all targeted generated Finish replacements are committed together

Then introduce one intentionally invalid target Finish and repeat the sequence.

Verify on regeneration failure:

- the newly entered `ceiling_reference_z_mm` remains as the current Scene setting
- none of the targeted Finish objects are partially replaced
- previous generated geometry remains intact
- the user is informed that regeneration is still required because generated geometry is stale relative to the current reference
- Undo of the ceiling edit and Undo of regeneration remain conceptually separate operations

---

# 73. Stage 1 Save / reopen

Save a file containing at least:

- Crown SIMPLE
- connected Miter
- one Manual Exclusion or partial boundary
- assigned Material

Close Blender.

Reopen.

Verify:

- finish_type = CROWN
- CEILING reference persists
- Profile identity / parameters persist
- Crown orientation persists
- material persists
- explicit regeneration reproduces same result

---

# 74. Stage 1 editable Mesh

Convert Crown SIMPLE to editable Mesh.

Verify:

```text
Object type = MESH
managed Finish state removed
scale = (1,1,1)
boundary = 0
non-manifold = 0
finite non-zero signed volume
correct outward normals
material retained
```

---

# 75. Stage 1 Baseboard regression

Because Stage 1 changes shared Profile placement orientation, Blender runtime regression MUST include a small Baseboard smoke set.

At minimum:

```text
Baseboard SIMPLE at FLOOR
Baseboard ROUNDED or accepted non-SIMPLE standard Profile
one Baseboard editable Mesh conversion
```

Do NOT rerun all accepted 06-B runtime gates unless a defect appears.

Automated 06-B regression remains required.

---

# 76. Stage 1 automated tests

Add a targeted suite, preferably:

```text
tests/test_build_06_c_stage1.py
```

At minimum pure / isolated tests should cover:

- BASEBOARD vertical sign
- CROWN vertical sign
- invalid finish type
- two-axis orientation parity
- Crown vertical bounds
- winding preservation under vertical reflection
- winding preservation under horizontal + vertical double reflection
- Baseboard orientation unchanged
- cache identity distinguishes vertical orientation
- reference arithmetic remains unchanged
- unknown / non-finite orientation values reject safely

Existing regression suites MUST continue to pass.

---

# 77. Stage 1 completion gate

Stage 1 is accepted only when:

```text
Crown SIMPLE is a production managed Finish.
Crown defaults to CEILING reference.
Crown extends downward from reference.
All four side/traversal combinations are correct.
MITER is correct.
BUTT is closed.
Partial Run works.
Manual Exclusion works.
Full Exclusion is a valid-empty managed Crown and restores from current reference when re-enabled.
Junction-aware Exclusion works.
Material survives.
Undo / Redo passes.
Save / reopen passes.
Editable Mesh is closed and correctly oriented.
Baseboard regression passes.
```

Only then proceed to Stage 2.

---

# 78. Stage 2 — BEVEL / ROUNDED / Custom Crown

Stage 2 extends Crown to the accepted production Profile families.

Required:

```text
BEVEL Crown
ROUNDED Crown
Custom POLY Crown
Custom BEZIER Crown
Custom uniform scale
Profile-aware shading
Custom smooth-edge orientation parity
Profile switching
Material persistence
Manual Exclusion
Partial Run
Miter
Mesh conversion
Save / reopen
Undo / Redo
Baseboard standard / Custom regression
```

---

# 79. Stage 2 BEVEL

BEVEL Crown must be the correct vertical reflection of the accepted canonical BEVEL Profile.

Verify:

- correct lower room-facing chamfer relationship
- planar shading
- correct selected Wall side
- correct ceiling attachment
- correct Miter
- identity scale
- closed Mesh conversion

---

# 80. Stage 2 ROUNDED

ROUNDED Crown must be the correct vertical reflection of the accepted canonical ROUNDED Profile.

Verify:

- rounded region appears on intended lower room-facing corner
- rounded region smooth
- planar regions flat
- caps flat
- correct Miter
- correct normals
- closed Mesh conversion

---

# 81. Stage 2 Custom POLY

Use an existing-style registered convex Custom POLY.

Apply it to Crown.

Verify:

- same stored Profile ID / revision
- no source dependency
- correct ceiling-down orientation
- correct side projection
- correct winding
- no negative scale
- Mesh conversion closed
- source may be deleted without invalidating Crown

---

# 82. Stage 2 Custom BEZIER

Apply deterministic Custom BEZIER to Crown.

Verify:

- persisted sampled contour used
- smooth edge intent follows physical curved region
- vertical reflection does not smooth wrong edge
- double reflection does not smooth wrong edge
- planar areas / caps remain flat
- Mesh topology valid

---

# 83. Stage 2 Custom scale

Run-local Custom uniform scale remains supported.

For Crown, scale affects:

```text
projection
downward height
all contour dimensions
```

around the canonical attachment origin.

One Run's scale edit MUST NOT change another Run.

Undo / Redo required.

---

# 84. Stage 2 Profile switching

Test at minimum:

```text
SIMPLE -> ROUNDED
ROUNDED -> Custom BEZIER
Custom -> BEVEL
```

Crown must remain:

- CEILING referenced
- downward oriented
- on same canonical Wall path
- material-preserving
- Exclusion-preserving
- transactionally valid

If a switch fails safety validation, rollback to previous valid Profile / geometry.

---

# 85. Stage 2 Exclusion with curved / Custom Profiles

Test Exclusion with:

```text
ROUNDED Crown
Custom BEZIER Crown
```

Verify:

- visible ranges independent
- no Miter across gap
- each gap end closed BUTT
- Profile shading remains correct
- Mesh remains closed

---

# 86. Stage 2 Save / reopen

Persist at least:

- one ROUNDED Crown
- one Custom BEZIER Crown
- Custom source deleted
- Manual Exclusion
- Material

After reopen:

- library snapshot remains
- Crown references same Custom Profile identity
- derived thumbnails are NOT yet required in Stage 2
- regeneration succeeds
- material / shading / visible ranges persist

---

# 87. Stage 2 Baseboard regression

Because Stage 2 generalizes smooth-edge orientation, runtime smoke regression MUST include:

```text
Baseboard ROUNDED
Baseboard Custom BEZIER
```

Verify accepted appearance and Mesh shading remain unchanged.

Full 06-B Blender acceptance is not required unless regression appears.

---

# 88. Stage 2 automated tests

Add a targeted suite, preferably:

```text
tests/test_build_06_c_stage2.py
```

At minimum cover:

- vertical reflection of SIMPLE / BEVEL / ROUNDED contours
- orientation parity for all sign pairs
- smooth edge index remap under vertical reflection
- smooth edge index behavior under double reflection
- Custom scale + Crown orientation
- derived cache identity
- standard Profile identity remains unchanged
- Baseboard compatibility
- transactional Profile switch rollback where testable without Blender runtime

Existing prior suites remain mandatory.

---

# 89. Stage 2 completion gate

Stage 2 is accepted only when:

```text
SIMPLE / BEVEL / ROUNDED work for Crown.
Custom POLY works for Crown.
Custom BEZIER works for Crown.
Smooth edges remain physically correct.
All supported orientation combinations retain correct normals.
Custom scale is run-local.
Profile switching is transactional.
Exclusion works with standard and Custom Crown.
Material survives.
Save / reopen passes.
Undo / Redo passes.
Editable Mesh passes.
Baseboard standard / Custom regression passes.
```

Only then proceed to Stage 3.

---

# 90. Stage 3 — Profile Thumbnail UI

Stage 3 completes the Roadmap Profile UI requirement.

This stage MUST NOT alter accepted geometry merely to simplify UI implementation.

The browser is a view / selection layer over the existing Profile architecture.

---

# 91. Stage 3 Profile browser minimum

The browser must show:

```text
SIMPLE
BEVEL
ROUNDED
every valid Project Custom Profile
```

Each entry has at least:

- visual thumbnail or valid fallback
- display name
- active/selected indication when applicable

Custom entry may additionally show:

- source type
- revision

but this is optional if visual clarity is sufficient.

---

# 92. Stage 3 browser contexts

At minimum support:

```text
selected managed Baseboard
selected managed Crown
Project Custom Profile Library
```

A single shared component / helper is preferred.

Do not implement three unrelated Profile identity systems.

---

# 93. Stage 3 Crown thumbnail orientation

When selecting a Profile for Crown, the thumbnail SHOULD depict the final attachment orientation:

```text
ceiling at top
Profile hanging downward
Wall attachment at side
```

This helps avoid the common mistake of interpreting the canonical +Y direction as world-up.

If implementation uses canonical thumbnails globally, the Crown context MUST provide an equally clear orientation indicator.

---

# 94. Stage 3 Baseboard thumbnail orientation

Baseboard selection should depict:

```text
floor/reference at bottom
Profile rising upward
Wall attachment at side
```

or another consistent equivalent.

Baseboard and Crown previews must not be visually indistinguishable solely because the same canonical contour is stored.

---

# 95. Stage 3 Custom snapshot thumbnail

A Custom thumbnail MUST derive from the persisted snapshot.

Test:

1. register Custom BEZIER
2. verify thumbnail
3. delete source Curve
4. save
5. reopen
6. verify thumbnail can be rebuilt from snapshot

Source independence is mandatory.

---

# 96. Stage 3 selection transaction

Selecting a new Profile through thumbnails MUST use the same production validation / transaction path as textual Profile editing.

It MUST NOT directly set `profile_id` and skip:

- resolver
- Miter safety
- blocker validation
- replacement preparation
- rollback

---

# 97. Stage 3 library mutation

Profile registration / deletion must update the browser.

Required cases:

```text
register unused Custom -> thumbnail appears
Undo registration      -> thumbnail disappears
Redo                    -> thumbnail returns

delete unused Custom    -> thumbnail disappears
Undo deletion           -> thumbnail returns

delete referenced Custom -> rejected
```

No unrelated FinishRun may change.

---

# 98. Stage 3 preview cache failure

Acceptance should include one practical cache rebuild case.

For example:

- reopen `.blend`
- re-register add-on
- clear/recreate in-memory preview cache

Exact test method may depend on implementation.

Required result:

```text
Profile definitions remain valid.
Browser rebuilds.
No Profile identity changes.
```

---

# 99. Stage 3 automated tests

Add a targeted suite, preferably:

```text
tests/test_build_06_c_stage3.py
```

Pure testable components should cover as applicable:

- thumbnail contour normalization / fit math
- aspect-ratio preservation
- stable identity mapping
- browser item ordering determinism if ordering is specified
- Custom snapshot preview source
- Crown vs Baseboard orientation transform for preview
- no canonical mutation from preview calculation
- cache invalidation keys where pure-testable

Blender-specific preview/icon API behavior is validated in runtime testing.

---

# 100. Stage 3 runtime UI acceptance

Runtime acceptance MUST verify at minimum:

1. standard thumbnails are visible and distinguishable
2. Custom POLY / BEZIER thumbnails appear
3. Baseboard context works
4. Crown context works
5. selected Profile is identifiable
6. clicking/applying a thumbnail changes Profile transactionally
7. standard numeric parameter editing remains available
8. Custom uniform scale remains available
9. source deletion does not destroy Custom thumbnail
10. save / reopen rebuilds usable browser
11. unused Profile deletion updates browser
12. referenced Profile deletion remains rejected
13. Undo / Redo around Profile library mutations remains valid
14. browsing alone does not mutate canonical Finish data

---

# 101. Mixed Baseboard + Crown integration smoke

Before final 06-C acceptance, add one focused mixed scene containing on the same managed Wall topology:

```text
Baseboard
+
Crown
```

Preferably include at least one Manual Exclusion on each Finish type.

Verify:

- both FinishRuns coexist without identity collision
- both use the same Wall Pointer + expected Wall ID trust model
- Wall split remaps both correctly
- Undo restores both pre-split states
- Redo restores both remapped states
- Baseboard remains floor-oriented
- Crown remains ceiling/downward-oriented
- Exclusion identities remain attached to the correct FinishRun

Also test one **bulk regeneration failure** in the mixed scene.

Make one targeted Finish intentionally invalid, change a relevant Scene reference, then run bulk regeneration.

Verify:

- neither Baseboard nor Crown is left as the only newly updated Finish
- previous generated geometry remains installed for all targeted Finishes
- current Scene input remains as entered
- stale / regeneration-required state is reported clearly

This is a small 06-C integration smoke test, not a repeat of the entire Finish Foundation acceptance.

---

# 102. Final 06-C Baseboard regression

Before overall acceptance, perform a focused Blender regression using accepted Baseboard production behavior.

Minimum final runtime smoke:

```text
Baseboard SIMPLE
Baseboard ROUNDED
Baseboard Custom BEZIER
one Manual Exclusion
one Profile switch
one editable Mesh conversion
Material check
```

Do NOT mechanically repeat all 27 accepted Build 06-B Stage 3 runtime tests unless changes or failures indicate a broader regression risk.

---

# 103. Final 06-C Crown regression

Final Crown runtime regression MUST include:

```text
SIMPLE
BEVEL
ROUNDED
Custom POLY
Custom BEZIER
LEFT / RIGHT
FORWARD / REVERSE
90-degree Miter
oblique Miter
Partial Run
Manual Exclusion
junction-aware Exclusion
Material
Undo / Redo
Save / reopen
Mesh conversion
thumbnail browser
```

Tests may reuse well-structured scenes rather than rebuilding every case independently.

---

# 104. Automated regression requirements

At each implementation stage, run:

```text
new Stage-specific tests
all prior Build 06-C tests
Build 06-B tests
Build 06-A tests
Build 05-B tests
full test discovery
compileall
git diff --check
```

The exact test counts will depend on implementation.

Do NOT hard-code acceptance around a predicted test count before tests exist.

All final reported counts MUST come from actual execution.

---

# 105. Runtime vs pure-test evidence

Pure Python tests are not Blender runtime evidence.

Acceptance record must distinguish:

```text
Automated pure / unit tests
```

from:

```text
Blender 5.2 LTS runtime tests
```

Do not claim Blender behavior from pure tests alone.

---

# 106. Quality policy per Roadmap

Build 10 is NOT where basic quality begins.

Build 06-C itself MUST include acceptance for:

```text
save / reopen
Undo / Redo
transaction rollback
prior-feature regression
managed-state validity
editable Mesh topology
```

Build 10 will later perform cross-build hardening.

These requirements MUST NOT be deferred to Build 10.

---

# 107. Failure handling

A failed Crown operation MUST be explicit.

Do not:

- silently switch to Baseboard
- silently switch to SIMPLE
- silently disable Exclusion
- silently drop Custom Profile reference
- silently flip normals after Mesh conversion
- silently rebind to another Wall
- silently mutate Profile snapshot

Report an actionable error and retain previous valid state whenever possible.

---

# 108. Managed-state diagnostics

`diagnose_finish` or equivalent validation MUST remain finish-type aware where necessary.

A valid Crown is not invalid merely because its derived vertical direction differs from Baseboard.

But a Crown must still be diagnosed invalid for canonical problems such as:

- broken Wall pointer
- mismatched expected Wall ID
- duplicate Wall ID
- invalid boundary
- missing Profile
- corrupt Profile
- unsafe geometry
- invalid transform
- unsupported canonical configuration

---

# 109. No geometry-as-truth regression

Do not inspect the generated Crown Curve and write its current shape back into canonical data as the normal edit path.

The flow remains one-way while managed:

```text
canonical data
    ↓
derived Crown
```

Only explicit editable Mesh conversion ends management.

---

# 110. Save compatibility

Build 06-C MUST open accepted Build 06-B files without requiring destructive migration.

Existing Baseboards must preserve:

- Finish IDs
- Span data
- Exclusion data
- Profile identities
- Custom Profile library
- materials
- visible appearance
- managed validity

New fields, if any are introduced, require safe defaults.

Prefer derived rules over unnecessary persistent schema additions.

---

# 111. No required new Profile schema revision

The intended 06-C architecture does not require changing existing Profile snapshot meaning.

Therefore, do NOT increment Profile schema/revision merely because Crown uses a different derived vertical orientation.

A Profile revision is required only if the Profile Definition itself changes meaning.

A storage schema version is required only if persistent representation changes.

Derived Crown orientation alone is neither.

---

# 112. No required Custom Profile migration

Existing registered Custom Profile definitions MUST remain valid.

Do not duplicate every existing Custom definition into a Crown copy.

Do not mutate canonical point order on file load.

Do not rewrite bounds to negative Y.

Crown orientation belongs to derived placement.

---

# 113. Thumbnail metadata persistence

No persistent thumbnail image path is required.

If implementation introduces persistent thumbnail metadata, it MUST be optional / rebuildable and MUST NOT become the only way to identify or reconstruct a Profile.

Stable identity remains Profile ID / revision / schema.

---

# 114. Performance expectations

Build 06-C does not require heavy optimization.

However:

- opening the Profile browser should remain responsive for a practical project-local library
- thumbnails should be cached/reused where reasonable
- regeneration should not rasterize thumbnails
- geometry regeneration and UI preview generation should remain separate concerns

Do not add a global background rendering pipeline for thumbnails.

---

# 115. File / module organization

Exact module names are implementation-defined.

Preferred principle:

- keep pure orientation math testable outside Blender
- avoid putting all Crown logic into `ui.py`
- reuse shared Finish geometry modules
- isolate thumbnail preview/cache logic if non-trivial
- do not copy Baseboard generation into a parallel Crown generator

A small new module such as:

```text
finish_profile_orientation.py
finish_profile_previews.py
```

may be appropriate, but is not mandatory.

---

# 116. Implementation diff discipline

Stage 1 should change only what is required for Crown SIMPLE foundation.

Stage 2 should add Profile generalization / Custom Crown support.

Stage 3 should add thumbnail UI and final integration.

Avoid combining unrelated cleanup / formatting across the repository with 06-C implementation.

This keeps review and rollback tractable.

---

# 117. Stage acceptance record

Create / update:

```text
BUILD_06_C_ACCEPTANCE_RECORD.md
```

as stages are actually accepted.

The record MUST distinguish:

- Stage 1 status
- Stage 2 status
- Stage 3 status
- overall Build 06-C status
- tested GitHub revision
- runtime artifact
- automated source revision
- Blender runtime evidence
- automated test results

Do not mark a stage ACCEPTED before runtime gates for that stage are complete.

Do not mark Build 06-C overall ACCEPTED before Stage 3 and final regression complete.

---

# 118. Candidate artifact naming

Recommended runtime candidate naming:

```text
Japanese_House_Modeler_Build_06_C_Stage1_Candidate_r1.zip
Japanese_House_Modeler_Build_06_C_Stage2_Candidate_r1.zip
Japanese_House_Modeler_Build_06_C_Stage3_Candidate_r1.zip
```

Increment `rN` when a runtime defect requires a corrected candidate.

A failed candidate is not reused as accepted evidence.

---

# 119. Final archive naming

After final merge / acceptance, recommended archival convention:

```text
Japanese_House_Modeler_Build_06_C_ACCEPTED.zip
Japanese_House_Modeler_Build_06_C_ACCEPTED_REPO.zip
```

This naming is project-management convention, not a runtime requirement.

The acceptance record must still identify the exact tested revision / artifact.

---

# 120. Acceptance response to defects

If runtime testing finds a defect:

1. stop acceptance for that affected gate
2. identify whether defect is canonical, derived geometry, UI, or preview-only
3. fix the smallest correct architectural layer
4. add an automated regression where practical
5. create a new candidate revision if production code changed
6. rerun the affected gate plus necessary regression

Do not continue declaring later gates PASS on known-invalid production geometry.

---

# 121. Stage 1 explicit non-goals

Stage 1 does NOT need:

- BEVEL Crown
- ROUNDED Crown
- Custom Crown
- thumbnail UI
- Room
- Ceiling Mesh
- Opening integration

Its purpose is orientation correctness and Crown Foundation.

---

# 122. Stage 2 explicit non-goals

Stage 2 does NOT need:

- thumbnail UI finalization
- Opening-driven Exclusion
- new Custom concavity rules
- Crown-specific Profile cloud/library system

Its purpose is complete Profile geometry parity.

---

# 123. Stage 3 explicit non-goals

Stage 3 does NOT redesign Crown geometry.

It completes:

- Profile visual browsing
- integration
- final regression
- final acceptance documentation

If Stage 3 UI work reveals a geometry defect, return to the appropriate architecture layer and fix it; do not mask the defect in thumbnail/UI code.

---

# 124. Final acceptance gate

Build 06-C overall is ACCEPTED only when all of the following are true:

```text
[ ] Stage 1 ACCEPTED
[ ] Stage 2 ACCEPTED
[ ] Stage 3 ACCEPTED

[ ] Crown creation is explicit
[ ] Crown defaults to CEILING reference
[ ] Crown hangs downward from reference
[ ] SIMPLE works
[ ] BEVEL works
[ ] ROUNDED works
[ ] Custom POLY works
[ ] Custom BEZIER works
[ ] Custom scale works
[ ] LEFT/RIGHT × FORWARD/REVERSE correct
[ ] no negative Object Scale
[ ] outward normals correct
[ ] 90-degree Miter correct
[ ] supported oblique Miter correct
[ ] Partial Run correct
[ ] Manual Exclusion correct
[ ] Crown valid-empty correct
[ ] full Exclusion save/reopen/restore-at-current-reference correct
[ ] junction-aware BUTT correct
[ ] mixed Baseboard + Crown coexistence / Wall split smoke passes
[ ] bulk regeneration mixed-scene failure remains all-or-nothing
[ ] stale-after-reference-change state is reported when regeneration fails
[ ] Material preservation correct
[ ] Undo / Redo correct
[ ] failed edits rollback atomically
[ ] save / reopen correct
[ ] editable Mesh closed/manifold
[ ] Profile-aware shading correct
[ ] Profile thumbnail browser complete
[ ] Custom thumbnail source-independent
[ ] thumbnail selection uses stable identity
[ ] Baseboard regressions pass
[ ] Build 06-A regressions pass
[ ] Build 05-B regressions pass
[ ] full automated suite passes
[ ] compileall passes
[ ] diff checks pass
[ ] final build identification is correct
[ ] acceptance record is complete
```

---

# 125. Final architectural invariant

After Build 06-C the Finish architecture should be understood as:

```text
Wall canonical data
        ↓
Finish attachment
        ├── BASEBOARD
        │      reference orientation: upward
        │
        └── CROWN
               reference orientation: downward
        ↓
same canonical Profile Library
        ↓
same visible-range / Exclusion system
        ↓
same Miter / BUTT path rules
        ↓
same managed -> editable Mesh exit
```

The important result is not merely that Crown geometry exists.

The result is that:

> **one accepted Finish Attachment architecture can place the same stable Profile definitions correctly at either floor-side or ceiling-side architectural references without duplicating canonical systems.**

---

# 126. End state before Build 07-A

When Build 06-C is accepted, Build 06 must provide:

```text
Wall-attached Finish Foundation
Baseboard production workflow
Crown production workflow
Standard Profile selection
Project-local Custom Profile snapshots
Profile thumbnail UI
Manual Exclusion
Partial placement
Material preservation
Editable Mesh exit
Save / reopen
Undo / Redo
Regression coverage
```

Only after Build 06-C overall acceptance should the project proceed to the next Roadmap item:

```text
Build 07-A
Stair Core + Straight Closed Stair
```

Build 06-C does not alter that development order.
