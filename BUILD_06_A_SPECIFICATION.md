# BUILD 06-A SPECIFICATION

## 日本住宅モデラー — Wall Surface Attachment Foundation / Finish Path Core

- Target: Blender 5.2 LTS
- Repository: `asleep-cdx/blender-japan-building-addon`
- Required base commit: `e49e8215dbce42ae3fca2adf736f0df81791405b`
- Base message: `Implement Build 05-B wall system finalization`
- Build position: first build after Wall phase finalization
- Primary consumers: Build 06-B Baseboard, Build 06-C Crown Moulding
- Future consumers: Room/Floor/Ceiling, Door/Window opening integration, other wall-attached finish systems

---

# 1. Purpose

Build 06-A establishes the common attachment and path foundation required for wall-following interior finish elements.

This build is NOT the final baseboard feature and is NOT the final crown-moulding feature.

The central problem to solve is:

> Given managed Walls, store and regenerate which Wall face, which Wall interval, and which ordered sequence of intervals a finish element belongs to.

The canonical relationship for managed finishes becomes:

```text
canonical Wall data + Wall topology
        +
FinishRun attachment data
        +
Profile reference / vertical reference
        ↓
resolved wall-surface path
        ↓
derived managed Curve
```

The generated Curve is derived data.

The Curve geometry itself MUST NOT become the source of truth.

This extends the existing Wall principle:

```text
canonical Wall data + topology -> derived Mesh
```

into:

```text
canonical Wall data + topology + finish attachment data -> derived Finish Curve
```

Build 06-A must make that relationship safe under:

```text
Wall endpoint editing
Wall thickness editing
Wall splitting
Wall safe deletion
Wall repair
Undo / Redo
Save / reopen
```

---

# 2. Project intent

The add-on is a production accelerator for renovation-perspective modeling.

It is NOT intended to become a fully automatic CAD/BIM system.

The intended workflow remains:

```text
dimension-based managed generation
        ↓
fast architectural base modeling
        ↓
optional managed editing / regeneration
        ↓
explicit conversion to ordinary Blender geometry when needed
        ↓
free Blender Edit Mode / materials / UV / modifiers / rendering
```

Build 06-A must preserve this philosophy.

Do not add:

- automatic complete Room interpretation
- BIM semantics
- construction-document generation
- quantity takeoff
- bidirectional recovery from arbitrary edited Mesh
- automatic interpretation of every architectural special case

---

# 3. Required existing invariants

All Build 05-B Wall invariants remain mandatory.

## 3.1 Units

- Add-on UI: millimeters
- Wall canonical XY/Z geometry: meters
- Convert only at well-defined boundaries.

## 3.2 Wall canonical source

A managed Wall remains defined by:

```text
Wall.start
Wall.end
Wall.wall_thickness
Wall.wall_height
START endpoint topology
END endpoint topology
```

Wall length remains derived.

Do NOT add an independently stored Wall length.

## 3.3 Wall centerline

Wall attachment calculations start from the canonical centerline, then resolve the requested physical wall face using Wall thickness and topology.

## 3.4 One Wall = one Blender Object

Build 06-A must NOT automatically merge canonical Wall objects.

A FinishRun must be able to cross multiple collinear split Walls without requiring those Walls to be merged.

## 3.5 Object Transform

Normal managed Wall operations continue to require identity Object Transform.

A transformed Wall must not silently become an attachment target.

Do not infer canonical Wall geometry from Object Transform.

## 3.6 Mesh is not canonical

Wall Mesh remains derived.

Finish Curve geometry also becomes derived.

Manual changes to generated geometry may be overwritten while the object remains managed.

---

# 4. Build 06-A scope

Build 06-A contains the following functional areas:

```text
01. Persistent Wall identity foundation
02. Finish attachment data model
03. LEFT / RIGHT canonical wall-face semantics
04. Ordered FinishRun / FinishSpan model
05. Wall interval boundary model
06. Surface path resolver
07. Explicit user-selected path construction
08. Straight continuation and Corner path resolution
09. Safe handling of T / Cross / ambiguous branches
10. Minimal managed Curve output
11. Wall split dependency remapping
12. Wall delete dependency remapping
13. Wall edit / thickness-change regeneration
14. Managed Finish repair / rebuild rules
15. Explicit conversion to editable Mesh
16. Save / reopen persistence
17. Undo / Redo and transaction atomicity
18. Pure geometry / remap unit tests
19. Blender acceptance tests
20. Full Build 05-B regression
```

---

# 5. Deliberately out of scope

The following MUST NOT be allowed to expand Build 06-A.

```text
final baseboard Profile Library
profile thumbnail browser
custom Profile registration UI
final crown-moulding feature
waist-height paneling / wainscot
low half-wall generation
Room automatic recognition
floor Mesh generation
ceiling Mesh generation
door / window assets
door / window Boolean integration
automatic finish stops at openings
full material library
automatic UV system
Geometry Nodes ornament system
stair generation
05-C automatic Wall merge
```

A minimal test Profile may be used only to verify path generation.

---

# 6. Persistent Wall identity

Build 06-A introduces a stable identifier for managed Walls.

Add a hidden persistent string property conceptually equivalent to:

```text
wall_id
```

The identifier must be generated from a collision-resistant UUID mechanism.

The identifier must not depend on:

- Object name
- Mesh name
- collection name
- object index
- `as_pointer()`
- current selection order

## 6.1 New Walls

Every newly created managed Wall MUST receive a valid unique `wall_id`.

## 6.2 Existing 05-B Walls

Existing managed Walls from older files have no `wall_id`.

Build 06-A must support them without destructive migration.

Acceptable behavior:

```text
managed Wall with empty wall_id
        ↓
first Build 06-A identity validation / Finish use / managed operation requiring ID
        ↓
assign unique wall_id
```

A dedicated migration pass is also acceptable if it is safe, deterministic, Undo-compatible where appropriate, and does not alter Wall geometry.

## 6.3 Object names are never reference identity

Renaming:

```text
Wall.001 -> LivingRoom_West
```

must not break Finish attachment references.

---

# 7. Wall ID integrity and duplication

Standard Blender duplication may copy custom properties.

Therefore Shift+D can potentially produce:

```text
Wall A wall_id = X
Wall B wall_id = X
```

This state is invalid.

Build 06-A must detect duplicate Wall IDs.

UI managed-state status must be capable of reporting an ID-integrity problem.

Example:

```text
管理状態: 要復元（Wall ID重複）
```

## 7.1 Duplicate-ID safety rule

While duplicate Wall IDs exist, operations that would create or modify managed Finish attachments involving those ambiguous Walls MUST refuse safely.

No Finish attachment may silently bind to an arbitrary object among duplicate IDs.

## 7.2 Repair rule

Explicit repair may assign a fresh ID to the selected duplicated object.

The other object(s) must not be modified merely because one duplicate is repaired.

Existing Finish references MUST NOT be silently transferred to the repaired duplicate.

If identity ownership is ambiguous, preserve existing valid attachment references and require explicit user action rather than guessing.

## 7.3 Runtime helper

Implementation may use a small runtime index:

```text
wall_id -> managed Wall object(s)
```

but this index is cache only.

Persistent truth is stored in Blender data.

---

# 8. Finish object identity

Every managed FinishRun MUST have its own stable identifier:

```text
finish_id
```

It must be independent from Blender Object name.

Renaming the Curve must not invalidate its data.

---

# 9. Core data model

The conceptual managed hierarchy is:

```text
FinishRun
├ finish_id
├ finish_type
├ profile_id
├ vertical_reference
├ vertical_offset_mm
├ absolute_z_mm
├ join_policy
├ miter_limit
├ closed
└ spans[]
```

Each span conceptually contains:

```text
FinishSpan
├ wall_object
├ expected_wall_id
├ side
├ entry_boundary_kind
├ entry_boundary_value_mm
├ exit_boundary_kind
├ exit_boundary_value_mm
├ traversal_direction
└ order
```

Exact Blender PropertyGroup class names may differ, but these semantics are mandatory.

---

# 10. Reference strategy: Pointer + stable ID

Within a `.blend` file, Blender `PointerProperty` to the target Wall is useful and persistent.

Build 06-A SHOULD store both:

```text
wall_object      -> direct Blender Object reference
expected_wall_id -> persistent identity verification
```

The direct object pointer is the primary in-file object reference.

The ID is the integrity / recovery key.

A reference is trusted only when:

```text
wall_object is a valid managed Wall
AND
wall_object.wall_id == expected_wall_id
AND
wall_id is not ambiguous
```

This avoids making a copied string UUID alone responsible for object resolution.

If the pointer is missing but exactly one live Wall has the expected ID, explicit repair may rebind the reference.

Do not silently rebind if multiple Walls share the same ID.

---

# 11. Finish type

Build 06-A only needs enough finish typing for future extension.

At minimum reserve:

```text
BASEBOARD
CROWN
```

Build 06-A may actively expose only a test / baseboard-style type.

Do not hard-code path logic specifically to baseboard.

The attachment/path system must be reusable by 06-C Crown Moulding.

---

# 12. Canonical LEFT / RIGHT wall-face semantics

Do NOT store a Wall-wide boolean such as:

```text
inside = True
```

A partition Wall can have indoor space on both sides.

Instead define side from canonical Wall direction:

```text
Wall START -> Wall END
```

For normalized 2D direction:

```text
d = (dx, dy)
```

canonical normals are:

```text
LEFT  normal = (-dy, +dx)
RIGHT normal = (+dy, -dx)
```

after normalization.

Thus:

```text
          LEFT
            ↑

START -------------> END

            ↓
          RIGHT
```

This definition MUST remain stable regardless of Finish traversal direction.

If Finish travels from Wall END toward Wall START, the Wall's LEFT and RIGHT labels do NOT swap.

---

# 13. Physical wall-face offset

For Wall thickness `T` in meters:

```text
half = T / 2
```

canonical raw face lines are:

```text
LEFT:
    start + left_normal * half
    end   + left_normal * half

RIGHT:
    start + right_normal * half
    end   + right_normal * half
```

These raw face lines are only the first stage.

Final Finish path endpoints near junctions must be resolved against adjacent selected spans / topology.

---

# 14. FinishSpan boundary model

A FinishSpan must support whole-Wall and partial-Wall attachment.

Boundary kinds:

```text
WALL_START
WALL_END
DISTANCE_FROM_START
DISTANCE_FROM_END
```

Boundary distance values are stored in millimeters.

Examples:

Whole Wall:

```text
entry = WALL_START
exit  = WALL_END
```

500 mm from START through Wall END:

```text
entry = DISTANCE_FROM_START / 500
exit  = WALL_END
```

400 mm from END:

```text
entry = WALL_START
exit  = DISTANCE_FROM_END / 400
```

## 14.1 Boundary resolution

For Wall length `L_mm`:

```text
WALL_START            -> 0
WALL_END              -> L_mm
DISTANCE_FROM_START d -> d
DISTANCE_FROM_END d   -> L_mm - d
```

Resolved values must be finite and inside the Wall segment.

Zero-length / reversed invalid intervals must be rejected.

---

# 15. Traversal direction

Finish traversal and Wall canonical direction are separate.

Each FinishSpan stores:

```text
FORWARD
REVERSE
```

Meaning:

```text
FORWARD:
    path follows Wall START -> END

REVERSE:
    path follows Wall END -> START
```

This controls ordered path generation.

It does NOT redefine Wall LEFT / RIGHT.

---

# 16. Span order

A FinishRun is an ordered sequence.

The order is explicit.

Do not reconstruct logical order later from spatial proximity.

The generated Curve follows this order.

---

# 17. Partial path support

Build 06-A architecture MUST support paths that:

- start at a Wall endpoint
- end at a Wall endpoint
- start partway along a Wall
- end partway along a Wall
- contain only one Wall
- contain multiple Walls
- form an open chain
- potentially become closed in future

06-A UI does not need every partial-edit command to be elaborate.

But the canonical data model must not assume every span always covers the entire Wall.

---

# 18. Vertical reference foundation

Baseboards and crown mouldings need different vertical anchors.

Define:

```text
FLOOR
CEILING
ABSOLUTE
```

A FinishRun stores:

```text
vertical_reference
vertical_offset_mm
absolute_z_mm
```

## 18.1 Working reference settings

Build 06-A may introduce scene-level working defaults:

```text
floor_reference_z_mm
ceiling_reference_z_mm
```

Default:

```text
floor_reference_z_mm = 0
ceiling_reference_z_mm = 2500
```

These are working references, not a final multi-storey Room/Level model.

Future Build 08 may replace or extend them with Room/Level references.

06-A must avoid baking assumptions that only one floor level can ever exist.

## 18.2 Resolution

```text
FLOOR:
    Z = floor_reference_z_mm + vertical_offset_mm

CEILING:
    Z = ceiling_reference_z_mm + vertical_offset_mm

ABSOLUTE:
    Z = absolute_z_mm
```

Convert to meters only at geometry boundary.

---

# 19. Finish Profile coordinate convention

Even though final Profile Library belongs to 06-B/06-C, the coordinate convention is fixed in 06-A.

For a 2D cross-section:

```text
Profile +X = away from wall surface into the represented room/finish side
Profile +Y = upward
```

The Profile origin represents the attachment reference point.

For a baseboard-like profile:

```text
origin = wall face at floor reference
```

For crown moulding:

```text
origin = wall face at ceiling reference
```

Any future custom Profile must declare its attachment origin and orientation using this convention.

---

# 20. Minimal verification Profile

Build 06-A may include one internal minimal Profile purely for geometry verification.

Recommended verification cross-section:

```text
height = 60 mm
projection from wall = 10 mm
rectangular
```

This is NOT a user-facing final baseboard library.

Its purpose is to verify:

- correct wall side
- correct path
- correct Z
- correct corner behavior
- correct regeneration

If Curve bevel behavior proves unsuitable for robust corners, the implementation may use another generated representation during the prototype, but the canonical attachment model must remain independent from representation.

---

# 21. Managed output object

The preferred Build 06-A managed output is a Blender Curve Object.

Conceptually:

```text
Managed Finish Object
├ Object / Curve geometry (derived)
└ jhm_finish
   ├ canonical FinishRun data
   └ FinishSpan collection
```

The Curve spline points are derived.

They are NOT the canonical source.

---

# 22. Manual Curve editing

If a user enters Edit Mode and manually changes a managed Finish Curve:

- canonical FinishRun data is unchanged
- manual geometry changes are not reverse-engineered
- explicit regeneration rebuilds the Curve from canonical attachment data
- manual Curve edits may therefore be discarded

This mirrors managed Wall behavior.

The UI should make managed state clear.

---

# 23. Explicit conversion to editable Mesh

Provide an explicit operation conceptually named:

```text
編集可能Meshとして確定
```

Its behavior:

```text
managed Finish Curve
        ↓
ordinary Blender Mesh
        ↓
remove / disable JHM managed Finish relationship
```

After confirmation:

- object is no longer regenerated by Wall changes
- Edit Mode changes are unrestricted
- normal Blender modifiers may be used
- normal material / UV editing may be used

Do NOT implement:

```text
edited Mesh -> managed FinishRun recovery
```

Undo immediately after conversion may restore the managed state through Blender Undo.

That is acceptable.

---

# 24. Finish path creation UX

Build 06-A must avoid complete automatic room-side inference.

Initial path construction begins from a Wall explicitly chosen by the user.

When one valid managed Wall is active, UI exposes:

```text
仕上げ経路
[左側面から開始]
[右側面から開始]
```

The chosen side becomes the first attachment side.

A visible viewport preview should indicate the selected Wall face.

The preview must be distinguishable from Wall centerline guides.

---

# 25. Interactive path editing

After path creation begins, enter a modal Finish Path mode.

Minimum operations:

```text
Left Click on valid connected Wall -> append next span
Backspace                         -> remove last appended span
Enter                             -> commit FinishRun
Esc                               -> cancel entire pending FinishRun
Right Mouse                       -> same as cancel, if consistent with existing add-on modal UX
Mouse Move                        -> update candidate / preview
```

No persistent object or topology mutation occurs before final commit, except temporary non-persistent preview state.

Cancellation must leave the file unchanged.

---

# 26. Next-span selection

The add-on MUST NOT automatically choose a branch at T or Cross junctions.

If multiple continuation choices exist, the user explicitly selects the next Wall.

When arriving at a branch, no arbitrary nearest-angle heuristic may decide the route.

---

# 27. Candidate eligibility

A Wall may be a Finish Path candidate only when it is:

- a live managed Wall
- visible in the current viewport
- identity-transform managed state
- valid canonical geometry
- valid / trusted identity
- not in unresolved duplicate-ID state

Topology inconsistency must be handled conservatively.

If the required relationship cannot be trusted, do not create an attachment through it.

---

# 28. Connectedness rule

A candidate next Wall must be topologically connected to the current span endpoint / junction according to trusted reciprocal Wall topology.

Geometric proximity alone is NOT sufficient.

Two Walls merely crossing in XY without Wall topology must not become one FinishRun.

This follows Build 05-B's rule that geometric crossing alone does not imply connection.

---

# 29. Same-Wall revisit

Build 06-A should prevent accidental immediate duplication of the same Wall span.

A FinishRun may not append an identical:

```text
wall + side + interval
```

twice in succession.

General loops / closed runs may be supported later, but 06-A must not allow an infinite or ambiguous repeated-path state.

---

# 30. Surface resolver

Create a pure or mostly pure geometry layer responsible for converting canonical attachment data into resolved wall-surface path geometry.

Responsibilities:

```text
Wall centerline
+ Wall thickness
+ LEFT / RIGHT
+ span interval
+ neighbor selected span
+ trusted topology
        ↓
resolved surface segment
```

The resolver must NOT inspect final Wall Mesh vertices to determine canonical placement.

Use canonical Wall data.

---

# 31. Raw surface segment

For a single isolated span:

1. resolve canonical Wall interval
2. calculate Wall axis
3. calculate requested LEFT / RIGHT normal
4. offset centerline by half thickness
5. create the raw physical face segment
6. apply vertical reference Z

For a partial interval, interpolate along canonical Wall centerline before applying the face offset.

---

# 32. Straight continuation

Collinear split Walls must be able to behave as one continuous FinishRun.

Even though they are two Blender Objects, consecutive spans must produce a visually continuous path.

This is a key reason 05-C Wall merge is not required before Build 06.

No visible artificial gap should be introduced solely because the Wall was previously split.

---

# 33. Corner resolution

For two sequential non-collinear spans, resolve the requested face lines.

Where safe and geometrically valid, use their intersection as the shared Finish path corner.

The algorithm must work for:

- 90-degree corners
- oblique corners
- unequal Wall thickness
- reversed Wall canonical directions
- any combination of LEFT / RIGHT that represents the selected physical sides

Do not assume all corners are 90 degrees.

---

# 34. Inside / outside corner behavior

The resolver should be based on actual selected face lines, not labels such as "inside corner" inferred globally.

The geometry decides the shared intersection.

However, the result must be checked for pathological extension.

A corner must not create a path point arbitrarily far away from the real junction.

---

# 35. Miter safety / pathological corner limit

Sharp angles can create very long line intersections or extreme miter geometry.

Define a limit policy.

The implementation may express this as:

```text
miter_limit
```

or another deterministic distance/ratio threshold.

When the intersection exceeds the safe limit:

- do not generate a huge spike
- use a documented fallback

Allowed fallback for 06-A:

```text
BUTT / clipped endpoint
```

or

```text
split the Curve at that junction
```

The chosen fallback must be deterministic and tested.

Silent gigantic geometry is not acceptable.

---

# 36. T junction behavior

At a T junction, the selected Finish path determines the intended continuation.

A branch Wall may physically block one wall face while the opposite wall face remains continuous.

Build 06-A must follow this principle:

> Never route a Finish through solid Wall volume merely because two canonical host segments are collinear.

If the resolver can prove the requested selected-face continuation is exposed, it may continue.

If exposure is ambiguous or unsupported, terminate / split the path safely rather than guessing.

The user can start another FinishRun where necessary.

---

# 37. Cross junction behavior

Cross junction rules:

- user explicitly chooses the next Wall
- topology must be trusted
- generated path must not cross solid Wall volume
- unsupported / ambiguous exposed-face cases must fail safely
- no arbitrary "straight is always correct" rule

Build 06-A does not need a complete architectural room solver.

---

# 38. Free ends

An open FinishRun may terminate at a Wall free end.

The path endpoint is the resolved wall-face position corresponding to the span boundary.

No automatic cap geometry beyond the minimal Profile is required in 06-A.

---

# 39. Generated path continuity versus one physical object

Logical continuity and Blender object topology are separate concepts.

Preferred 06-A representation:

```text
1 FinishRun = 1 managed Curve Object
```

But if one unsafe corner requires a spline break, one Curve Object may contain multiple splines while remaining one FinishRun.

Do not sacrifice correctness merely to force one spline.

---

# 40. Build 05-B Wall split integration

Current Wall splitting creates:

```text
original host -> START-side segment
successor     -> END-side segment
```

Build 06-A must preserve this existing contract.

Finish dependency remapping must be added around / after canonical split behavior without redesigning that Wall contract.

---

# 41. Wall split event model

Introduce a small dependency-remap event/result concept.

Example conceptual payload:

```text
WallSplitResult
├ original_wall_object
├ original_wall_id
├ successor_wall_object
├ successor_wall_id
├ old_start
├ old_end
├ old_length_mm
└ split_distance_from_start_mm
```

Exact class shape may differ.

The purpose is to give downstream systems a stable input for remapping.

Build 06-A consumer:

```text
Finish attachment remapper
```

Future Build 09 consumers may include opening / asset attachment remappers.

Do not put Finish-specific remap code directly inside low-level pure split geometry if avoidable.

---

# 42. Successor Wall identity on split

When a Wall is split:

- original START-side Wall keeps its existing `wall_id`
- successor END-side Wall receives a NEW unique `wall_id`

Do not copy the same `wall_id` to the successor.

This is mandatory.

---

# 43. Whole-Wall Finish remap on split

Given:

```text
Wall length = 4000
Finish span = WALL_START -> WALL_END
split at 2000
```

result:

```text
original Wall:
    WALL_START -> WALL_END

successor Wall:
    WALL_START -> WALL_END
```

inside the same logical FinishRun and in correct traversal order.

No visible break should result.

---

# 44. Partial Finish remap on split

Given:

```text
Wall length = 4000
Finish physical interval = 500 -> 3500 mm from original START
split = 2000 mm
```

result must preserve the same physical attachment:

```text
original child:
    500 -> 2000

successor child:
    0 -> 1500
```

Use the canonical boundary model where possible.

The exact stored boundary kinds after remap may be normalized, but physical meaning must remain deterministic.

---

# 45. Span entirely before split

If a Finish span lies entirely on the START-side child, it remains attached to the original Wall only.

No unnecessary successor span is created.

---

# 46. Span entirely after split

If a Finish span lies entirely on the END-side child:

- attachment moves to successor
- physical position is preserved
- distances are remapped into successor coordinates

---

# 47. Split boundary exactness

If a Finish boundary lies exactly on the Wall split location:

- do not create zero-length spans
- use geometry epsilon consistently
- keep the non-zero child only
- maintain correct traversal order

---

# 48. Multiple FinishRuns referencing one Wall

Wall split remap must update ALL managed FinishRuns that reference the host Wall.

Do not update only the active Finish.

---

# 49. Wall split transaction atomicity

The following must form one logical operation:

```text
Wall split
successor creation
Wall topology migration
FinishSpan remap
Wall / Finish geometry regeneration
selection / active-object finalization where relevant
```

If any required step fails:

```text
restore original Wall canonical data
restore original topology
remove successor object / mesh if created
restore original FinishRun data
remove any generated replacement Finish objects
restore derived geometry as needed
return CANCELLED
```

No half-remapped file state is acceptable.

One Ctrl+Z must revert the entire successful operation.

---

# 50. Endpoint move that causes target Wall split

Build 05-B endpoint move can split a target host.

Build 06-A must ensure Finish remapping also occurs for that split.

The finish behavior must be the same whether host splitting originated from:

```text
new Wall creation
endpoint move
future explicit split operation
```

Use shared remap logic.

---

# 51. Wall thickness edit

Changing `wall_thickness` changes physical face position.

Every managed FinishRun referencing that Wall must regenerate its resolved path.

Canonical Finish attachment data does not change.

Only derived path geometry changes.

---

# 52. Wall centerline endpoint edit

Moving Wall START or END changes:

- Wall length
- Wall axis
- face normal
- corner intersections
- partial-boundary resolution
- connected Finish paths

All affected managed FinishRuns must regenerate.

If a stored partial boundary becomes invalid because the Wall becomes too short:

- do not silently clamp unless explicitly specified
- mark the Finish as needing repair / invalid
- fail the Wall edit safely if preserving dependency validity is required by the transaction

For 06-A, prefer transactional rejection over silent semantic change.

---

# 53. Wall safe delete with Finish dependencies

Managed Wall delete must update dependent FinishRuns before final object deletion.

If the deleted Wall is at one end of a FinishRun, shorten the run.

If the deleted Wall is in the middle:

```text
A -> B -> C
```

and B is deleted, do NOT silently connect A directly to C.

Instead split the logical finish relationship:

```text
FinishRun 1: A
FinishRun 2: C
```

with copied style/profile/reference settings and distinct `finish_id` values.

If either side contains no span, do not create an empty FinishRun.

---

# 54. Finish split on Wall delete

When one FinishRun is divided into two runs due to Wall deletion:

- first surviving run may retain original `finish_id`
- newly created later run receives a new unique `finish_id`
- span order in each run must be preserved
- profile/reference settings are copied
- generated Curve objects are regenerated
- operation is one Undo step

Deterministic recommended rule:

```text
lowest original span-order surviving run keeps original finish_id
later disconnected runs receive new IDs
```

---

# 55. Wall delete transaction

Wall delete plus Finish dependency updates must be atomic.

If Finish regeneration fails:

- Wall must remain present
- Wall topology must be restored
- Finish data must be restored
- derived Wall meshes should be restored / regenerated

Do not leave the Wall deleted with broken Finish references.

---

# 56. Wall repair integration

Existing:

```text
管理状態へ復元
```

must remain explicit.

Build 06-A may extend managed-state validation to identity integrity.

Repair must NOT infer Wall canonical data from Finish geometry.

Finish attachments depend on Wall canonical data, never the reverse.

If repair changes a duplicate `wall_id`, affected Finish references must not be guessed.

---

# 57. Standard Blender Delete remains abnormal path

Users can still use Blender's standard Delete key on a Wall.

That can bypass the add-on's safe dependency logic.

Build 06-A must at least detect stale Finish references afterward.

A FinishRun with a missing target Wall must show a managed-state problem and must not crash UI drawing or regeneration.

Explicit Finish repair may remove or split invalid spans if the result is unambiguous.

Do not silently invent a replacement Wall.

---

# 58. Finish managed-state validation

A managed Finish can have statuses such as:

```text
正常
要復元（Wall参照不整合）
要復元（Wall ID不整合）
要復元（Wall欠落）
要復元（区間不正）
要復元（経路不連続）
```

Exact Japanese wording may be adjusted for panel width.

The underlying problem categories should remain machine-readable.

---

# 59. Finish rebuild / repair

Provide explicit operations conceptually equivalent to:

```text
経路を再生成
管理状態へ復元
```

They may be one or two operators depending on implementation.

Regeneration:

- trusts valid canonical FinishRun data
- rebuilds derived Curve geometry

Repair:

- may clean stale references where safe
- may rebind pointer when exactly one Wall matches expected unique ID
- may normalize span order / derived geometry
- must not guess through ambiguous ID or topology states

---

# 60. Finish delete

Provide a managed Finish delete operation.

It deletes only the Finish object / managed finish data.

It does NOT delete the host Walls.

It does NOT merge Walls.

Undo restores the FinishRun.

---

# 61. Explicit Finish path cancellation

During modal path construction:

- no committed Finish object remains after Esc / Right Mouse
- no persistent span properties remain
- Wall canonical data remains unchanged
- Wall topology remains unchanged
- temporary preview handlers are removed

---

# 62. Exclusion interval data foundation

Build 06-A should define a future-compatible exclusion interval structure, even if full UI is deferred to 06-B.

Conceptually:

```text
FinishExclusion
├ wall_object
├ expected_wall_id
├ side
├ start_boundary
├ end_boundary
├ exclusion_type
└ source_id
```

Initial reserved exclusion types:

```text
MANUAL
DOOR
WINDOW
OTHER
```

Build 06-A may only support `MANUAL` internally or leave UI hidden.

Purpose:

- baseboard stop at door frame
- special finish omission
- future Window / Door integration

The exclusion width is separate from Boolean cutter width.

---

# 63. Exclusion data and Wall split

If exclusion intervals are already persisted in 06-A, they must use the same Wall split remap foundation as Finish spans.

Do not implement a separate incompatible coordinate model.

If exclusions are only schema placeholders in 06-A, add unit tests for boundary conversion helpers where practical.

---

# 64. Profile reference

Build 06-A stores a lightweight:

```text
profile_id
```

or equivalent.

The final library implementation belongs to 06-B.

Do not bind canonical FinishRun data to a fragile Blender Object name such as `Profile.001`.

A temporary internal Profile may have a reserved stable ID.

---

# 65. Profile snapshot policy reserved for 06-B

The project decision for 06-B is:

- standard Profiles may be parametric
- custom Profile registration should snapshot stable geometry / metadata
- changing the source Curve later must not automatically mutate old project finishes unless the user explicitly updates them

06-A must not make a data choice that prevents this.

---

# 66. Curve versus Mesh implementation boundary

The canonical attachment model must be independent from the final sweep implementation.

Build 06-A should prototype a managed Curve because that is the preferred production behavior for baseboard / crown moulding.

However:

> if Blender Curve bevel corner behavior cannot satisfy safe corner requirements, do not corrupt the attachment model to match Curve limitations.

Keep:

```text
FinishRun -> resolved path
```

as a separate layer from:

```text
resolved path -> generated Curve / geometry
```

This allows Build 06-B to improve sweep generation without migrating attachment semantics.

---

# 67. Recommended module separation

Recommended new modules:

```text
finish_identity.py
finish_path.py
finish_surface.py
finish_dependencies.py
finish_geometry.py
finish_operators.py
```

Existing modules likely updated:

```text
properties.py
operators.py
wall_split.py
ui.py
__init__.py
```

Exact filenames may differ, but responsibilities should remain separated.

## 67.1 `finish_identity.py`

Responsibilities:

- ensure/generate Wall IDs
- ensure/generate Finish IDs
- unique-ID lookup
- duplicate-ID detection
- pointer/ID reference validation

## 67.2 `finish_path.py`

Pure / mostly pure data and ordering helpers:

- boundary resolution
- interval validation
- traversal ordering
- span normalization
- disconnected-run splitting logic

## 67.3 `finish_surface.py`

Pure geometry:

- Wall axis / normal
- face offset
- partial face segment
- line intersection
- continuation resolution
- corner safety
- miter-limit decisions

No Blender Object mutation.

## 67.4 `finish_dependencies.py`

Dependency events:

- remap on Wall split
- update on Wall delete
- find FinishRuns referencing Walls
- snapshot / restore canonical Finish data

## 67.5 `finish_geometry.py`

Derived Blender representation:

- create/update Curve object
- generated spline points
- minimal Profile application
- conversion to Mesh helper where appropriate

## 67.6 `finish_operators.py`

Operators:

- start Finish path
- modal append/cancel/commit
- regenerate
- repair
- delete
- convert to editable Mesh

---

# 68. Do not create circular ownership

Wall system must not depend on Finish geometry for canonical correctness.

Dependency direction:

```text
Wall -> Finish
```

not:

```text
Wall <-> Finish
```

Wall can notify / remap dependent Finish data.

Finish never rewrites Wall centerline merely because its path changed.

---

# 69. Snapshot / restore strategy

Build 05-B currently snapshots Wall topology for rollback.

Build 06-A requires broader rollback.

At minimum snapshot enough data to restore:

```text
Wall canonical endpoints/dimensions touched by operation
Wall topology
Wall IDs if changed
FinishRun canonical data
Finish object existence
Finish IDs
Finish spans
Finish derived geometry or ability to deterministically regenerate it
```

A transaction helper is recommended.

Do not rely on Blender global Undo as the only exception rollback mechanism inside an operator.

Successful operator = one logical Undo step.

Failed operator = no persistent partial mutation.

---

# 70. Generated-object cleanup

Whenever an operation creates temporary/new Curve datablock, Mesh datablock, Object, or successor Finish object and later fails, remove unused datablocks safely.

Avoid orphan accumulation.

---

# 71. Collections and material preservation

Build 06-A minimal Curve generation does not need a complete material system.

However, regeneration must not arbitrarily relink objects to unrelated collections.

Recommended:

- preserve existing Finish object collection membership on regeneration
- when creating a new FinishRun, link to the active collection or a documented project collection strategy
- when a FinishRun splits into two objects, successor should inherit collection membership from the original Finish object

Material / UV preservation becomes a stronger requirement in later builds, but 06-A must avoid obvious destructive resets where unnecessary.

---

# 72. Object Transform for managed Finish

Managed Finish Curve should normally remain identity-transform.

Preferred for simplicity:

```text
managed Finish Object transform = identity
Curve control points = world-derived coordinates
```

If the managed Finish Object has non-identity Object Transform, status should warn and managed regeneration should refuse or explicit repair should restore identity.

Do not silently bake arbitrary transforms back into canonical Finish spans.

---

# 73. UI — selected Wall extension

The existing Wall UI remains.

When a valid Wall is selected, add a separate Finish section:

```text
仕上げ経路

[左側面から開始]
[右側面から開始]
```

Do not replace existing Wall controls.

---

# 74. UI — selected managed Finish

Conceptual minimal panel:

```text
選択中の仕上げ

種類: Baseboard Test
Profile: Simple
基準: Floor
Offset: 0.0 mm

区間数: 4
管理状態: 正常

[経路を再生成]
[管理状態へ復元]
[編集可能Meshとして確定]
[仕上げ経路を削除]
```

Read-only total path length may be shown if cheaply and reliably derived.

Do not store it independently.

---

# 75. UI — working floor / ceiling references

Expose working defaults in a compact project/scene section:

```text
床基準高さ: 0.0 mm
天井基準高さ: 2500.0 mm
```

Changing these must regenerate applicable managed FinishRuns or use an explicit Update action.

For 06-A, direct update with dependency regeneration is preferred if safe.

---

# 76. Preview

During path creation, show:

- current resolved wall-face candidate
- already selected ordered path
- candidate next span
- invalid candidate feedback where reasonable

Preview geometry must not be mistaken for committed geometry.

---

# 77. Path commit

On Enter:

1. validate all Wall references and IDs again
2. validate all span boundaries
3. resolve path
4. reject unsupported ambiguous/solid-wall-crossing transitions
5. create canonical FinishRun
6. generate managed Curve
7. select / activate new Finish object
8. commit as one Undo step

If any step fails, no FinishRun remains.

---

# 78. Finish conversion to Mesh

Conversion must:

1. validate managed Finish
2. evaluate / convert the visible generated Curve geometry
3. create or convert to ordinary Mesh
4. preserve visible appearance as far as reasonably possible
5. remove JHM managed Finish status from that result
6. leave host Walls untouched
7. finish in a user-editable selected Mesh state

Do not keep a hidden live managed copy unless explicitly designed later.

---

# 79. Conversion and future Wall edits

After conversion, Wall edits must NOT automatically update the converted Mesh.

This is intentional.

The user has chosen to leave managed mode.

---

# 80. Save / reopen persistence

Mandatory acceptance flow:

```text
create Walls
create managed FinishRun
save .blend
close Blender
reopen Blender
open .blend
```

After reopen:

- Wall IDs preserved
- Finish ID preserved
- Wall pointers preserved where valid
- expected Wall IDs preserved
- span order preserved
- LEFT / RIGHT preserved
- boundary kinds and values preserved
- traversal directions preserved
- vertical reference preserved
- generated Curve visually matches
- managed state reports normal

Then explicit regeneration must reproduce the same result.

---

# 81. Dependency discovery after reopen

Do not depend solely on transient Python dictionaries built before save.

Any runtime index must be rebuildable from persistent Blender data after file load.

---

# 82. Load handlers

A lightweight `load_post` handler may rebuild identity/reference caches and validate duplicates if needed.

If added:

- registration must be idempotent
- unregistration must remove handlers cleanly
- loading a file must not silently modify canonical geometry unless migration is explicitly safe
- no duplicated handlers after add-on reload

---

# 83. Performance expectations

Build 06-A is not a large-scene optimization build.

Still avoid obvious O(N^3) scans during mouse movement.

Modal preview should not scan all scene data repeatedly if a simple viewport / ID cache can avoid it.

Optimization must not compromise correctness.

---

# 84. Error handling principles

Prefer:

```text
reject safely
show clear status
require explicit user choice
```

over:

```text
guess architectural intent
```

Particularly for duplicate IDs, invalid Wall references, unsupported T/Cross face exposure, invalid partial intervals, pathological corners, missing Walls after standard Delete, and transformed managed Walls.

---

# 85. Build 06-A pure test requirements

Add tests for pure helpers wherever Blender UI is not required.

Minimum geometry/data coverage:

```text
LEFT/RIGHT normal calculation
face offset with several Wall angles
partial interval resolution
FORWARD/REVERSE ordering
90-degree corner line intersection
oblique corner intersection
unequal thickness corner
parallel continuation
miter/pathological intersection rejection
duplicate-ID detection helper
reference trust validation helper
split remap before/crossing/after split
exact split-boundary behavior
delete-run partition logic
```

Tests should include reversed Wall canonical directions.

---

# 86. Split-remap test matrix

At minimum include:

- whole span crossing split
- span entirely START side
- span entirely END side
- partial span crossing
- entry exactly on split
- exit exactly on split
- REVERSE traversal crossing split
- two different FinishRuns on same Wall
- multiple spans from one FinishRun referencing same Wall where valid

No zero-length spans after remap.

---

# 87. Surface test matrix

At minimum:

- horizontal Wall LEFT
- horizontal Wall RIGHT
- vertical Wall LEFT
- vertical Wall RIGHT
- 45-degree Wall
- reversed start/end
- 90-degree corner
- 135-degree / 45-degree oblique corner
- unequal thickness
- collinear continuation
- near-parallel unsafe intersection
- pathological distant intersection

---

# 88. Identity test matrix

At minimum:

- new unique ID creation
- existing ID preserved
- empty ID receives one
- duplicate IDs detected
- object rename does not affect reference
- valid pointer + matching ID trusted
- valid pointer + wrong ID rejected
- missing pointer + unique ID candidate detectable for explicit repair
- missing pointer + duplicate ID remains ambiguous

---

# 89. Blender acceptance tests

The Build 06-A real-Blender acceptance set must include at least the following 30 scenarios.

```text
01. Existing 05-B Wall receives/preserves valid Wall ID without geometry change.
02. Newly created Wall receives unique Wall ID.
03. Rename Wall object; identity/reference remains valid.
04. Shift+D Wall; duplicate-ID state is detected safely.
05. Repair duplicated Wall; selected duplicate receives fresh identity without stealing existing Finish.
06. Create isolated LEFT-side Finish path.
07. Create isolated RIGHT-side Finish path.
08. Visual face offset matches Wall thickness.
09. One-Wall free-end FinishRun.
10. 90-degree Corner path.
11. Oblique Corner path.
12. Unequal-thickness Corner path.
13. Collinear split Walls produce one continuous logical FinishRun.
14. T junction requires explicit next-Wall choice.
15. Cross junction never chooses a branch automatically.
16. Geometric crossing without topology cannot be appended.
17. Backspace removes only last pending span.
18. Esc / Right Mouse leaves no committed Finish data/object.
19. Wall endpoint move regenerates dependent Finish.
20. Wall thickness edit moves Finish to the new physical face.
21. Wall split remaps whole-Wall Finish into two spans.
22. Wall split remaps a partial Finish interval correctly.
23. Endpoint move that splits a target host also remaps existing Finish on that host.
24. Safe delete of end Wall shortens FinishRun.
25. Safe delete of middle Wall splits FinishRun into disconnected managed runs.
26. Finish regeneration after manual Curve edit restores canonical result.
27. Convert to editable Mesh; later Wall edits do not move converted Mesh.
28. Conversion Undo/Redo is coherent.
29. Save -> close -> reopen -> managed Finish remains valid and regeneration is identical.
30. Build 05-B Wall acceptance/regression remains passing.
```

Additional tests are encouraged for failure rollback.

---

# 90. Undo / Redo requirements

One logical user action = one logical Undo step.

Specifically verify:

```text
Finish path commit
Wall split + Finish remap
endpoint move + host split + Finish remap
Wall safe delete + FinishRun split
Finish repair
Finish conversion to Mesh
Finish delete
```

Redo must recreate equivalent state.

---

# 91. Failure injection / rollback tests

Where practical, unit/integration tests should inject a controlled exception after:

- Wall successor creation
- Finish span remap
- Finish Curve creation
- FinishRun split during Wall delete

Then verify original canonical state is restored.

Static AST tests alone are not sufficient for the core remap algorithms when pure functional tests can be written.

---

# 92. Existing Wall behavior must not regress

Build 06-A must not weaken Build 05-B.

The following still must work:

- Wall create
- endpoint snap
- Shift constrained drawing
- midpoint split
- endpoint move to midpoint
- Corner / Continuation / T / Cross
- oblique Wall
- unequal thickness joints
- safe delete
- managed repair
- transformed Wall exclusion
- Shift+D topology hardening
- save / reopen
- Undo / Redo

Finish support is additive.

---

# 93. Existing Build 05-B ID-free files

Opening an old `.blend` created before Build 06-A must not fail because `wall_id` is absent/empty.

Migration must be safe and local.

Do not require the user to rebuild every Wall manually.

---

# 94. No 05-C automatic merge

Deleting a branch Wall from a previously split T host still does NOT automatically merge the remaining collinear Wall objects in Build 06-A.

Instead, Finish continuity must work across those split Walls.

The 05-C idea remains Backlog.

Future implementation may provide explicit conditional Wall merge rather than silent automatic merge.

---

# 95. Future Door / Window compatibility

Build 06-A must leave room for Build 09 to attach data such as:

```text
Wall
wall-along distance
opening interval
wall side
floor-relative height
finish stop interval
```

Finish exclusion data must not assume the Boolean cutter width equals finish-stop width.

---

# 96. Future Room compatibility

Build 06-A must not define one permanent "interior side" on Wall.

Future Room system may map:

```text
Room X -> Wall LEFT
Room Y -> Wall RIGHT
```

Finish attachment stays valid because it already uses canonical LEFT/RIGHT.

---

# 97. Future Crown compatibility

The same FinishRun / FinishSpan model must support crown moulding by changing:

```text
vertical_reference = CEILING
profile_id
finish_type
```

Path topology logic should remain shared.

Do not create a separate incompatible "crown path system" in 06-C.

---

# 98. Future Profile Library compatibility

06-B/06-C may add:

- standard Profile IDs
- thumbnail selection
- custom Profile registration
- profile snapshots
- parametric standard profiles
- original-size custom profiles
- profile update command

06-A must store profile reference in a replaceable stable manner.

---

# 99. Future stairs are independent

Build 07 Stair Core is a separate parametric system.

Do not make Finish attachment depend on stairs in 06-A.

Later, stairs may introduce stair-side baseboard/skirting, stair opening exclusions, and floor/ceiling holes as future integration points.

---

# 100. Coding constraints

Implementation must:

- favor small pure geometry helpers
- keep Blender mutation separate from pure calculations
- avoid mesh-derived canonical inference
- avoid undocumented global mutable state as truth
- use deterministic ordering
- validate finite numeric inputs
- use explicit error paths
- keep Japanese UI text readable
- preserve existing architecture unless a change is required by this specification

Do not suppress failing tests merely to complete the build.

---

# 101. Recommended implementation sequence

Recommended development order:

```text
A. identity helpers + properties
B. pure boundary/span helpers
C. pure surface resolver
D. minimal Finish property groups
E. managed Curve generator
F. modal path creation UX
G. Wall split dependency remap
H. Wall edit dependency regeneration
I. Wall safe delete dependency handling
J. repair / convert / delete Finish operators
K. persistence / Undo tests
L. full 05-B regression
```

Do not begin with thumbnail/profile-library UI.

---

# 102. Completion criteria

Build 06-A is complete only when all of the following are true:

```text
A managed FinishRun can be attached to an explicitly selected Wall side.
The run can traverse several trusted connected Walls.
Its canonical attachment survives Wall edits.
It remaps correctly when a Wall is split.
It updates safely when a Wall is deleted.
Its path is regenerated from canonical Wall/Finish data.
Its generated Curve is not the source of truth.
The user can explicitly convert it to ordinary editable Mesh.
Save/reopen preserves the relationship.
Undo/Redo remains coherent.
Build 05-B Wall behavior remains intact.
```

A pretty final baseboard design is NOT a Build 06-A completion criterion.

---

# 103. Acceptance decision rule

If a difficult junction cannot yet be resolved safely, prefer:

```text
safe refusal / FinishRun break
```

over:

```text
visually plausible but topologically incorrect automatic geometry
```

This is a renovation-perspective production tool.

Reliable partial automation is more valuable than fragile full automation.

---

# 104. Build 06-B handoff contract

When 06-A is accepted, Build 06-B may assume the following stable foundation:

```text
stable Wall identity
trusted Wall references
canonical LEFT/RIGHT
FinishRun / FinishSpan
partial intervals
ordered traversal
resolved wall-surface Path
split/delete remapping
managed Curve regeneration
explicit editable-Mesh conversion
persistence / Undo contract
```

06-B then focuses on:

```text
Baseboard standard Profiles
Profile dimensions
Profile Library
custom Profile registration
manual exclusion UI
baseboard-specific end/join behavior
Profile selection UX
```

It must not need to redesign the core Wall attachment model.

---

# 105. Required verification commands

Codex/local implementation verification should include:

```text
python -B -m unittest discover -s tests
python -m compileall -q japanese_house_modeler tests
git diff --check
```

If staged:

```text
git diff --cached --check
```

Do not weaken existing tests.

---

# 106. Codex workflow constraint for this project

Codex Cloud must work only in its local workspace.

Do NOT spend time attempting GitHub network Git from Codex Cloud.

Known unavailable operations in that environment:

```text
git fetch
git pull
git push
git ls-remote
```

Do not create ZIP files in Codex.

After implementation, report:

```text
changed files
test count
test result
compileall result
diff-check result
local commit SHA
important Blender acceptance tests
```

The implementation will be reviewed file-by-file before Windows integration.

---

# 107. Required local commit message

When implementation and local tests are complete, use one local Codex commit:

```text
Implement Build 06-A finish attachment foundation
```

Do not push it from Codex Cloud.

---

# 108. Non-negotiable architecture summary

The core rules of Build 06-A are:

```text
Wall centerline stays canonical.
Wall LEFT/RIGHT is defined by START -> END.
Finish stores attachment semantics, not generated Curve vertices.
Pointer + stable ID validates Wall references.
FinishRun is ordered; FinishSpan owns one Wall-side interval.
User chooses branch direction at ambiguous junctions.
Surface path comes from canonical Wall data, never Wall Mesh.
Wall split remaps Finish dependencies atomically.
Wall delete never guesses across a missing middle segment.
Managed Curve can be regenerated.
Editable Mesh conversion is one-way by design.
Save/reopen and Undo/Redo are first-class requirements.
```

These rules must remain stable unless a later formal specification explicitly supersedes them.
