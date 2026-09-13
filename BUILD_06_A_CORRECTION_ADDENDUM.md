# BUILD 06-A CORRECTION ADDENDUM

## 日本住宅モデラー — Finish Attachment Foundation Correction Contract

- Target: Blender 5.2 LTS
- Repository: `asleep-cdx/blender-japan-building-addon`
- Governing specification: `BUILD_06_A_SPECIFICATION.md`
- Governing specification commit: `c877e0c14ace3daba34f29ec8a601683afe4ed0b`
- Build 05-B implementation base: `e49e8215dbce42ae3fca2adf736f0df81791405b`
- Current Build 06-A implementation candidate expected in the Codex local workspace: `82dd6c08f7195f6fc901c1878224d80ef19a312e`
- Date of this correction contract: 2026-09-13
- Status: **Normative correction addendum**
- Scope: Build 06-A correction only

---

# 0. Precedence and interpretation

This document supplements `BUILD_06_A_SPECIFICATION.md`.

The original Build 06-A specification remains in force except where this addendum:

- clarifies an ambiguous requirement,
- narrows an implementation choice for safety,
- adds a required validation or transaction rule discovered during implementation review,
- or records a Blender 5.2 runtime defect that the implementation must correct.

If this addendum and the original Build 06-A specification conflict, **this addendum takes precedence for Build 06-A correction work**.

This addendum does **not** redefine the overall product direction.

The canonical relationship remains:

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

The following remain canonical truths:

```text
Wall canonical data + Wall topology
FinishRun / FinishSpan canonical attachment data
```

The following remain derived data:

```text
Wall Mesh
Finish Curve
verification Profile geometry
```

Derived geometry MUST NOT become canonical truth.

---

# 1. Decision: continue the existing Build 06-A implementation

Build 06-A MUST be corrected from the current implementation.

Build 06-A MUST NOT be restarted from Build 05-B unless a later code review demonstrates that the current canonical attachment model cannot represent the required behavior.

The following current foundations remain valid and SHOULD be preserved unless a correction requires a local rewrite:

- Wall centerline as canonical geometry.
- One managed Wall = one Blender Object.
- Persistent `wall_id`.
- Pointer + expected persistent ID attachment validation.
- `FinishRun`.
- Ordered `FinishSpan`.
- LEFT / RIGHT canonical wall-face semantics.
- FORWARD / REVERSE traversal semantics.
- boundary kinds:
  - `WALL_START`
  - `WALL_END`
  - `DISTANCE_FROM_START`
  - `DISTANCE_FROM_END`
- semantic split remapping.
- FinishRun partitioning on safe Wall deletion.
- derived managed Curve output.
- one-way conversion to ordinary editable Mesh.
- topology-based T / Cross branch selection.
- canonical-geometry blocker tests rather than Wall Mesh inference.

The correction work MAY reorganize individual functions or dependency-update orchestration where required.

“Continue the existing implementation” does not mean that every current function must remain unchanged.

---

# 2. Baseline verification before correction work

Before any correction implementation begins, the Codex local workspace MUST be checked.

Run:

```bash
git rev-parse HEAD
git status --short
```

The expected pre-addendum implementation candidate is:

```text
82dd6c08f7195f6fc901c1878224d80ef19a312e
```

and the working tree is expected to be clean.

If either condition does not match:

- STOP correction implementation.
- DO NOT automatically reset, checkout, clean, or discard work.
- Report the actual HEAD.
- Report the working-tree changes.
- Resolve the discrepancy explicitly before continuing.

If this addendum is then added as a separate local commit, record that new commit as the actual **Stage 1 implementation start commit**.

Stage 2 MUST start from the accepted Stage 1 commit.

Stage 3 MUST start from the accepted Stage 2 commit.

Each stage start commit MUST be stated in the corresponding Codex implementation report.

---

# 3. Known runtime evidence at the start of correction work

The correction work is based on both code review and Blender 5.2 runtime acceptance.

## 3.1 Runtime behavior confirmed as working

The following behavior has been observed in Blender 5.2:

- the Build 06-A add-on registers successfully;
- Build 05-B Wall UI and basic existing Wall behavior remain available;
- a one-Wall FinishRun can be created;
- LEFT and RIGHT wall-face path selection can place the Finish path on opposite Wall faces;
- a two-Wall 90-degree connected path can be selected as one FinishRun;
- the 90-degree path can contain two FinishSpans;
- the Finish managed-state UI can report normal for such a run.

These observations do not by themselves certify the complete Finish geometry.

## 3.2 Runtime defect confirmed

The Build 06-A verification Profile currently projects into the Wall solid in at least the following confirmed cases:

```text
single horizontal Wall
LEFT side
full-Wall Finish
```

and:

```text
two-Wall 90-degree run
LEFT side on the tested inside-corner path
```

The canonical wall-face path is located at the Wall face, but the Profile’s 10 mm horizontal projection extends toward the Wall centerline instead of away from the Wall.

Therefore:

```text
wall-face path placement        = usable basis
verification Profile placement = known FAIL
```

RIGHT-side outward Profile placement has not yet been accepted as correct and MUST be tested after correction.

## 3.3 Code-review defects confirmed

The current implementation also contains the following correction targets:

1. Finish regeneration can occur during `split_wall()` before the outer Wall operation has completed its final topology.
2. Final Wall operations can change junction blockers without regenerating every Finish affected by that blocker change.
3. blocker validation is applied mainly between consecutive FinishSpans and does not fully cover FinishRun start/end boundaries.
4. partial intervals can be extended toward a junction by surface join logic without first proving that the canonical interval reaches that junction.
5. a referenced managed Wall can acquire non-identity Object Transform without Finish diagnosis/regeneration consistently rejecting that Wall.
6. current Finish Curve regeneration destructively clears the existing spline before replacement is fully prepared.
7. transaction rollback must cover Wall state and all affected Finish state as one compound operation.

These are correction requirements, not reasons to discard the canonical FinishRun / FinishSpan model.

---

# 4. Deliberately excluded from this correction

The correction MUST NOT expand into the following work:

```text
Build 05-C automatic collinear Wall merge
Build 06-B final baseboard Profile Library
Build 06-C final crown-moulding feature
Profile thumbnail browser
custom Profile registration UI
Room recognition
floor generation
ceiling generation
door/window asset system
door/window Boolean integration
automatic finish opening subtraction
automatic wrap-around routing around blockers
automatic complete trim resolution for every architectural special case
stair generation
BIM semantics
```

A minimal verification Profile remains allowed.

The correction MAY add internal helpers, transaction infrastructure, diagnostics, tests, and small UI controls required to make Build 06-A safe.

---

# 5. Correction stages

Build 06-A correction SHALL proceed in three accepted stages.

```text
Stage 1
Dependency Transaction Foundation

Stage 2
Path Boundary & Profile Geometry

Stage 3
Hardening & Formal Acceptance
```

Build 06-A MUST NOT be declared complete after Stage 1 or Stage 2 alone.

Each stage requires:

1. implementation,
2. automated validation,
3. patch review,
4. a Blender 5.2 acceptance ZIP,
5. Blender runtime acceptance appropriate to that stage,
6. an accepted local commit before the next stage begins.

---

# 6. Stage 1 — Dependency Transaction Foundation

Stage 1 establishes the update and rollback foundation used by all later corrections.

Stage 1 MUST NOT attempt to finish the known Profile outward-orientation defect.

That defect remains an explicit known FAIL until Stage 2.

---

# 7. Stage 1 — transaction ownership rule

Any managed operation that can change:

```text
Wall canonical geometry
Wall identity
Wall reciprocal topology
Wall existence
Finish canonical attachment references
```

MUST participate in one Finish dependency transaction.

The transaction boundary is the complete user operation.

The user MUST NOT receive a successful operation result while dependent Finish data or derived geometry still represents an intermediate topology.

The transaction MUST treat Wall and Finish state as one consistency domain.

---

# 8. Stage 1 — Wall operations that require dependency review

At minimum, the implementation MUST examine and correctly handle Finish dependencies for:

```text
Wall creation
Wall creation that splits an existing Wall
Wall endpoint move
Wall endpoint move that splits another Wall
Wall thickness edit
Wall height edit where relevant to managed-state validation
Wall safe delete
Wall repair
Wall joint rebuild / topology cleanup
```

The implementation MUST NOT rely only on this list.

The general rule is:

> Any operation that can change managed Wall canonical geometry or reciprocal topology MUST determine whether Finish dependencies are affected.

Future managed Wall split operations MUST use the same transaction mechanism.

---

# 9. Stage 1 — `split_wall()` responsibility

`split_wall()` MUST NOT finalize dependent Finish Curve geometry while an outer Wall operation is still incomplete.

Its correction responsibility is:

```text
validate split preconditions
create the successor Wall
assign a unique successor Wall ID
update original/successor canonical Wall data
transfer endpoint topology required by the split
create the reciprocal original-successor connection
remap FinishSpan references and intervals
remap FinishExclusion references and intervals when records exist
return sufficient split result information to the outer transaction
```

The final dependent Finish regeneration belongs to the outer complete Wall operation.

`split_wall()` MUST NOT return an intermediate split/remap state to the user as a successful user operation.

The implementation SHOULD make it structurally difficult for callers to forget finalization.

Acceptable designs include:

- requiring an explicit transaction context,
- making low-level split mutation private to a higher-level transaction API,
- returning a mandatory mutation result consumed by the outer transaction,
- or another design that provides equivalent guarantees.

A future standalone “split Wall” operator MUST also execute through the complete transaction/finalization path.

---

# 10. Stage 1 — affected Finish dependency scope

Affected Finish objects MUST NOT be collected only by direct Span reference to one edited Wall.

The transaction MUST consider both:

```text
pre-operation dependency scope
post-operation dependency scope
```

and update the union.

The reason is that a topology mutation can:

- add a blocker,
- remove a blocker,
- move a junction participant,
- transfer an endpoint connection,
- split one Wall into two,
- delete one Wall,
- or detach a previously connected peer.

A Finish may therefore be affected even if none of its FinishSpans directly references the newly edited Wall.

At minimum, dependency collection MUST include managed FinishRuns that are affected through:

1. direct `FinishSpan.wall_object` references to changed, split, successor, deleted, or neighboring Walls;
2. existing `FinishExclusion.wall_object` references when exclusion records exist;
3. Finish transitions that use a changed junction;
4. FinishRun start/end boundaries that use a changed junction;
5. blocker sets that change because a Wall joined or left a junction;
6. changed Wall thickness where that thickness changes the selected wall face or blocker footprint.

The implementation MAY use a conservative superset if that is simpler and remains performant for Build 06-A.

Correctness is more important than minimizing the number of regenerated Finish objects in this build.

---

# 11. Stage 1 — pre- and post-topology dependency capture

Before a topology-changing mutation, capture enough information to identify Finish dependencies that may disappear from the post-operation topology.

After the mutation, capture dependencies introduced by the new topology.

The affected set is conceptually:

```text
affected_finish =
    pre_operation_finish_dependencies
    UNION
    post_operation_finish_dependencies
```

This is required because a removed connection cannot be discovered by examining only the final topology.

The implementation MUST NOT silently lose the Finish on the detached side from the update scope.

---

# 12. Stage 1 — common referenced-Wall validation

Finish creation, Finish regeneration, Finish diagnosis, Finish conversion to editable Mesh, and Finish dependency updates MUST use one consistent referenced-Wall validation contract.

For every referenced Wall required by the operation, validate at least:

```text
Object pointer is live
Object is a managed Wall
expected_wall_id is non-empty
pointer Wall ID matches expected_wall_id
the expected Wall ID has one unambiguous owner
Object Transform satisfies the managed identity-transform rule
canonical start/end values are finite
canonical Wall length is non-degenerate
canonical thickness is finite and positive
canonical height is finite and positive
required topology references are valid and reciprocal
```

Canonical geometry MUST come from stored Wall data.

Do NOT infer canonical geometry from:

```text
Wall Mesh vertices
Object Transform
evaluated Mesh
```

A referenced Wall with non-identity Object Transform MUST NOT be accepted as normal Finish input.

The user-facing error SHOULD instruct the user to repair the Wall first.

Example:

```text
参照WallにObject Transformがあります。先にWallを管理状態へ復元してください。
```

Finish “repair” MUST NOT silently bake or adopt the transformed Wall state.

---

# 13. Stage 1 — Finish diagnosis and transformed referenced Walls

`diagnose_finish()` or its replacement MUST report an invalid managed state when a referenced Wall fails the common referenced-Wall validation.

At minimum, a transformed referenced Wall MUST not produce:

```text
管理状態: 正常
```

A dedicated problem key such as:

```text
WALL_TRANSFORM
```

or a more general:

```text
WALL_STATE
```

is acceptable.

The user-facing meaning must be clear.

---

# 14. Stage 1 — existing Exclusion records

Build 06-A does not require a full Exclusion editing or repair UI.

However, if a `FinishExclusion` record exists and a managed operation will:

```text
split it
remap it
partition it
delete it
snapshot it
restore it
```

the record MUST first satisfy the same reference integrity rule applicable to persistent attachment data:

```text
live managed Wall pointer
non-empty expected_wall_id
pointer ID matches expected_wall_id
unambiguous Wall ID owner
valid managed Wall state
```

An ambiguous or broken Exclusion reference MUST NOT be silently remapped and MUST NOT be treated as normal.

Full convenient Exclusion rebind UI MAY remain deferred.

No heuristic repair is allowed.

---

# 15. Stage 1 — prepare / commit transaction model

Stage 1 MUST introduce transaction-safe derived-geometry update behavior.

The required contract is:

```text
A. retain recoverable pre-operation state
B. perform canonical/topology mutation under transaction ownership
C. compute and validate the final state
D. prepare replacement derived data
E. after all required preparation succeeds, begin commit
F. if commit fails part-way, restore already-committed objects
G. only after complete success, dispose of obsolete old data
```

The implementation MUST NOT assume that successful preparation guarantees that every later Blender datablock assignment will succeed.

Commit itself is fallible.

Therefore rollback MUST work for:

```text
failure during prepare
failure after one derived object has been swapped
failure after multiple objects have been swapped
failure during a later swap in the same user operation
```

---

# 16. Stage 1 — preserve old data until complete success

Old recoverable data MUST NOT be irreversibly discarded before the whole compound operation succeeds.

This applies to affected:

```text
Wall Mesh datablocks
Finish Curve datablocks
Wall objects scheduled for deletion
Finish objects scheduled for deletion
canonical Finish snapshots
Wall canonical snapshots
topology snapshots
persistent IDs
```

A temporary or replacement datablock SHOULD be built separately.

For Finish regeneration, a preferred pattern is:

```text
resolve and validate canonical Finish path
        ↓
create replacement Curve datablock
        ↓
build replacement spline/profile assignment completely
        ↓
retain old Curve datablock
        ↓
commit Object.data swap
        ↓
whole transaction succeeds
        ↓
remove unused old Curve datablock
```

Equivalent transaction-safe designs are acceptable.

The implementation MUST NOT require destroying the only valid old Finish Curve before the replacement is known to be usable.

---

# 17. Stage 1 — temporary canonical mutation

It is acceptable for the implementation to temporarily mutate canonical properties during one modal/operator transaction if:

- the state is not returned to the user as a successful operation before final validation,
- complete snapshots exist,
- dependent validation uses the intended final state,
- and every failure path restores the pre-operation state.

A shadow copy of every Blender PropertyGroup is not required if snapshot/restore provides equivalent safety.

---

# 18. Stage 1 — planned deletion

For Wall/Finish deletion transactions:

- objects/data scheduled for deletion SHOULD remain recoverable until commit success;
- final-state validation MAY treat them as logically absent before physical removal;
- irreversible datablock removal SHOULD occur only after the remaining final state is validated and committed.

If physical removal must happen earlier for a Blender API reason, the implementation MUST retain enough copied state to restore the object and its canonical/derived data on failure.

---

# 19. Stage 1 — final-state regeneration rule

All dependent Finish validation and generation MUST use the **final topology of the complete Wall operation**.

For example, this order is invalid:

```text
split host Wall
remap Finish
regenerate Finish
attach new branch Wall
finish operation
```

because the regeneration does not know the final blocker set.

The required conceptual order is:

```text
snapshot dependency state
split/remap if needed
perform remaining Wall mutation
complete reciprocal topology
determine final affected Finish set
validate all affected managed data
prepare final Wall/Finish derived geometry
commit
```

---

# 20. Stage 1 — no stale derived Finish after successful Wall operation

A successful Wall operation MUST NOT leave an affected managed Finish whose current Curve represents an earlier topology or thickness state.

If an affected Finish cannot be safely resolved under the final topology:

- the complete Wall operation MUST fail safely for Build 06-A,
- and the transaction MUST restore the previous valid Wall + Finish state.

Automatic rerouting, auto-trimming, or Finish deletion is not required in Stage 1.

---

# 21. Stage 1 — minimum failure-injection tests

Stage 1 is not accepted merely because normal-path tests pass.

At least the following controlled failure cases MUST be tested.

## 21.1 Replacement Finish Curve prepare failure

Inject failure while preparing a replacement Finish Curve.

Expected:

```text
original Wall state preserved/restored
original Finish canonical data preserved/restored
original Finish Curve preserved/restored
temporary datablocks removed
no partial successor/delete artifacts
```

## 21.2 Failure while preparing a later Finish

With multiple affected managed Finish objects:

```text
Finish A prepare succeeds
Finish B prepare fails
```

Expected:

- neither Finish is left in a mixed final state;
- all temporary data is removed;
- the Wall operation is restored.

## 21.3 Commit failure after an earlier Finish swap

Inject failure after at least one affected Finish has already had replacement data assigned.

Expected:

- already-swapped objects are restored to their original datablocks/state;
- later objects remain original;
- the Wall operation is restored;
- no replacement datablock leak remains.

## 21.4 Failure after split and dependency remap

Inject failure after:

```text
host Wall split
successor creation
FinishSpan/Exclusion remap
```

but before full operation success.

Expected:

```text
original host canonical endpoint restored
original host ID restored if it changed during migration
successor removed
original topology restored
FinishSpan/Exclusion data restored
original derived Finish geometry restored
temporary data removed
```

These minimum tests belong to Stage 1.

Stage 3 expands failure testing further.

---

# 22. Stage 1 — required functional regression cases

Stage 1 acceptance MUST include at least the following dependency scenarios.

## 22.1 Add a branch on an existing Finish junction

Start with a valid managed Finish that crosses two collinear split Walls.

Add a new branch Wall at their shared junction.

If the final branch blocks the Finish side:

- final Finish validation MUST detect it;
- the Wall operation MUST fail safely in Build 06-A;
- the original Wall + Finish state MUST remain.

If the branch is on a geometrically non-blocking side:

- the Wall operation MAY succeed;
- the Finish MUST be regenerated/validated against final topology.

## 22.2 Endpoint move adds or removes blocker conditions

Moving a Wall endpoint that changes junction membership MUST update every affected Finish selected from both old and new topology.

## 22.3 Thickness change affects a selected face or blocker footprint

Changing Wall thickness MUST update dependent Finish geometry.

If the thickness change makes an affected Finish invalid under the final safety rules:

- reject the Wall dimension operation;
- restore the old dimensions and derived geometry.

## 22.4 Repair / joint rebuild changes topology trust

If cleanup/repair changes reciprocal topology or removes an untrusted connection, affected Finish objects MUST be included in dependency validation.

## 22.5 Referenced Wall transform abnormality

After creating a valid Finish, apply ordinary Blender Object Transform to a referenced Wall.

Expected:

- Finish diagnosis is not normal;
- managed Finish regeneration is rejected;
- Mesh conversion that requires regeneration is rejected;
- user is directed to repair the Wall.

---

# 23. Stage 1 acceptance boundary

Stage 1 is accepted when:

- dependency updates occur only against the final complete Wall operation state;
- affected Finish collection accounts for pre- and post-operation topology;
- common referenced-Wall validation is in use;
- Exclusion records that participate in mutation are validated;
- prepare/commit rollback protects both Wall and Finish state;
- minimum failure-injection tests pass;
- Blender runtime confirms that topology-changing operations do not leave stale managed Finish geometry.

The known verification Profile inward-projection defect MAY remain at this point and MUST be explicitly marked as a known Stage 2 issue.

---

# 24. Stage 2 — Path Boundary & Profile Geometry

Stage 2 corrects local path semantics and the actual verification Profile placement.

Stage 2 MUST use the Stage 1 transaction foundation rather than adding separate ad-hoc rollback behavior.

---

# 25. Stage 2 — internal transition canonical reach test

Before two consecutive FinishSpans are allowed to form one surface join, the canonical interval of each Span MUST actually reach the reciprocal Wall endpoint used for that transition.

Do not decide this only from boundary kind names.

Use the resolved canonical position along the Wall centerline.

For a Wall of canonical length:

```text
L
```

and a resolved canonical distance from Wall START:

```text
s
```

endpoint reach is:

```text
START reached when abs(s - 0) <= epsilon
END reached when abs(s - L) <= epsilon
```

Use a deterministic tolerance appropriate to the project’s meter/mm conversions.

The test MUST be based on the Wall centerline interval coordinate.

Do NOT compare the wall-face-offset XY point directly with the Wall centerline junction point.

---

# 26. Stage 2 — traversal-aware transition endpoint

For an ordered FinishSpan:

```text
FORWARD
```

traversal runs from canonical low interval distance to canonical high interval distance.

For:

```text
REVERSE
```

traversal runs from canonical high interval distance to canonical low interval distance.

For every consecutive pair:

```text
Span A -> Span B
```

the implementation MUST determine:

- the physical/canonical endpoint from which Span A leaves,
- the reciprocal Wall endpoint expected by topology,
- the physical/canonical endpoint at which Span B arrives.

Both canonical intervals MUST reach their required endpoint within tolerance before surface miter resolution is allowed.

If either interval does not reach the required endpoint:

```text
reject as discontinuous / invalid Finish path
```

Do not extend the interval to make it connect.

---

# 27. Stage 2 — partial intervals remain canonical

A partial interval MUST NOT be silently rewritten or logically enlarged merely to produce a corner.

Example:

```text
Wall A length = 2000 mm
FinishSpan A ends at 1500 mm
Wall B is connected at Wall A END
FinishSpan B follows Wall B
```

This MUST NOT be resolved by extending Span A from 1500 mm toward the 2000 mm Wall endpoint.

For Build 06-A:

```text
the path is invalid and regeneration/creation is rejected
```

unless Span A’s resolved canonical departure boundary actually reaches the required Wall endpoint.

The stored boundary kind/value remains unchanged.

---

# 28. Stage 2 — join adjustment after endpoint reach is proven

When the canonical interval does reach the required Wall endpoint, the derived wall-face geometry MAY be extended or shortened locally to the safe face-line intersection required for:

```text
90-degree miter
oblique miter
unequal-thickness miter
```

subject to the existing safe miter rules.

This local derived adjustment:

- does not change the stored FinishSpan boundary;
- does not redefine canonical interval meaning;
- must remain within the miter safety limits;
- must not route through a non-selected Wall solid.

Therefore the following are distinct:

```text
canonical interval reaches junction  -> required before joining
derived face point adjusted for miter -> allowed after reach is proven
```

---

# 29. Stage 2 — FinishRun start/end blocker validation

Blocker safety MUST apply not only between consecutive FinishSpans but also at FinishRun start and FinishRun end.

For the first traversed boundary and the last traversed boundary:

1. resolve the canonical interval endpoint;
2. determine whether that endpoint reaches a Wall START/END junction;
3. if it does, inspect reciprocal managed Walls connected at that junction;
4. use canonical Wall centerline + thickness footprints;
5. determine whether the local Finish endpoint occupies/intersects a connected non-selected Wall solid.

If blocked or ambiguous:

```text
reject safely
```

for Build 06-A.

Do NOT auto-trim around the blocker.

Do NOT automatically extend to another Wall.

Do NOT guess a branch.

If the Finish boundary ends inside the Wall away from START/END, endpoint topology blocker validation is not invoked merely because another Wall crosses geometrically nearby.

A non-reciprocal geometric crossing remains non-topological and MUST NOT be treated as a connected blocker.

---

# 30. Stage 2 — single-Span Finish endpoint safety

A one-Span FinishRun MUST receive the same start/end safety validation.

The absence of a second FinishSpan MUST NOT disable blocker checks at a connected Wall endpoint.

Required example:

```text
Wall A: horizontal
Finish: one Span on Wall A
Finish ends at Wall A END
Wall B: connected from Wall A END into the selected Finish side
```

Expected:

```text
Finish creation/regeneration rejected
```

if the Finish endpoint lies in Wall B’s canonical solid footprint.

The opposite non-blocked side MAY remain valid.

---

# 31. Stage 2 — Profile physical orientation contract

The verification Profile contract is:

```text
Profile horizontal axis:
from the selected Wall face away from the Wall solid

Profile vertical axis:
world +Z

Profile origin:
resolved Wall face × vertical reference
```

The Finish spline itself MUST remain on the Wall face.

Do NOT correct Profile intrusion by moving the canonical Finish path another 10 mm away from the Wall.

The 10 mm verification projection is Profile geometry, not an additional Wall-face offset.

---

# 32. Stage 2 — side + traversal orientation

Blender Curve bevel framing is traversal-relative.

Therefore Profile orientation MUST account for:

```text
canonical side: LEFT / RIGHT
traversal:      FORWARD / REVERSE
```

The four combinations MUST be tested:

```text
LEFT  + FORWARD
RIGHT + FORWARD
LEFT  + REVERSE
RIGHT + REVERSE
```

The required orientation relationship is:

```text
FORWARD + LEFT
and
REVERSE + RIGHT
```

use the same traversal-relative horizontal Profile orientation.

And:

```text
FORWARD + RIGHT
and
REVERSE + LEFT
```

use the opposite traversal-relative horizontal Profile orientation.

The runtime observation at the start of this addendum is authoritative:

```text
FORWARD + LEFT using the current positive 10 mm Profile orientation projects inward
```

The corrected implementation MUST choose the opposite physical horizontal projection for that case.

The implementation MAY use:

- mirrored verification Profile objects,
- a Profile-orientation helper,
- compatible spline/profile transform logic,
- or another deterministic solution.

A 180-degree rotation that also turns the +60 mm height downward is not acceptable.

---

# 33. Stage 2 — one ordered run, continuous physical side

The corrected Profile orientation must remain physically continuous through an ordered FinishRun, including:

```text
90-degree corner
oblique corner
unequal-thickness corner
reversed canonical direction on the next Wall
```

The existing canonical-side propagation rule may be retained if it satisfies the physical contract.

For one continuous spline, an implementation MAY derive the Profile mirror/orientation from the first ordered Span’s side + traversal relationship if Blender’s frame propagation keeps the physical side correct through the run.

If runtime testing shows frame instability at corners, the implementation MUST use a more explicit orientation method.

Correct physical output is the requirement; the exact Blender mechanism is not prescribed.

---

# 34. Stage 2 — verification Profile dimensions

The minimal Profile remains:

```text
height     = 60 mm
projection = 10 mm
```

For every accepted orientation:

```text
bottom = vertical reference
top    = vertical reference + 60 mm
```

For floor reference 0 mm:

```text
bottom Z = 0
top Z    = 0.060 m
```

Horizontal projection must occupy:

```text
Wall face -> 10 mm away from Wall solid
```

and never:

```text
Wall face -> 10 mm toward Wall centerline
```

---

# 35. Stage 2 — verification Profile acceptance matrix

Blender 5.2 runtime acceptance MUST explicitly test:

```text
single horizontal Wall LEFT
single horizontal Wall RIGHT
single vertical Wall LEFT
single vertical Wall RIGHT
oblique Wall
LEFT + FORWARD
RIGHT + FORWARD
LEFT + REVERSE
RIGHT + REVERSE
90-degree inside corner
90-degree outside corner
reversed-canonical second Wall
unequal-thickness corner
```

For each relevant case verify:

```text
path is on correct Wall face
10 mm projection is outward
60 mm dimension is upward
bottom remains at requested vertical reference
no Profile enters Wall solid
managed state is correct
```

---

# 36. Stage 2 — path acceptance matrix

Stage 2 automated and Blender acceptance MUST include at least:

1. one Span at a free Wall end;
2. one Span ending at a connected but non-blocking Wall;
3. one Span ending at a blocking Wall;
4. one Span starting at a blocking Wall;
5. T branch occupied side blocked;
6. T branch opposite side allowed where safe;
7. Cross corresponding sides blocked;
8. non-reciprocal geometric crossing ignored;
9. partial Span ending before junction followed by next Span -> reject;
10. partial Span reaching junction followed by next Span -> allow miter if otherwise safe;
11. `DISTANCE_FROM_START` resolving exactly to endpoint -> endpoint reach accepted;
12. `DISTANCE_FROM_END` resolving exactly to endpoint -> endpoint reach accepted;
13. reversed traversal partial interval;
14. 90-degree miter;
15. oblique miter;
16. unequal-thickness miter.

---

# 37. Stage 2 acceptance boundary

Stage 2 is accepted when:

- FinishRun start/end blocker safety exists;
- one-Span Finish blocker safety exists;
- internal transitions require canonical endpoint reach;
- partial interval meaning is preserved;
- miter adjustment occurs only after endpoint reach validation;
- all four side/traversal Profile orientations satisfy outward projection;
- Profile height remains +60 mm world-up;
- known runtime Profile intrusion is no longer reproducible;
- Stage 1 transaction guarantees remain intact.

---

# 38. Stage 3 — Hardening & Formal Acceptance

Stage 3 is not the first implementation of transaction safety.

Stage 1 already provides the transaction foundation and minimum failure proof.

Stage 3 expands verification, unsupported-state handling, persistence, diagnostics, and complete Build 06-A acceptance.

---

# 39. Stage 3 — extended failure injection

Extend failure tests to combinations involving:

```text
safe Wall delete
Wall repair
joint rebuild
endpoint move + split
multiple FinishRuns
Finish partition on delete
Exclusion remap
Object/data replacement
conversion to editable Mesh
```

Test that failed operations do not leave:

```text
orphan successor Walls
orphan temporary Curves
stale Curve datablocks
mixed old/new Finish geometry
broken Finish IDs
broken Wall IDs
partially remapped spans
partially remapped exclusions
half-applied topology
```

---

# 40. Stage 3 — Undo / Redo

Blender 5.2 runtime acceptance MUST cover Undo/Redo for at least:

```text
Finish creation
Finish regeneration
Wall edit that updates Finish
Wall split that remaps Finish
safe Wall delete that partitions Finish
Finish conversion to editable Mesh
duplicate Wall repair where applicable
```

Undo MUST restore the managed state expected before the operation.

Redo MUST restore the accepted post-operation state.

---

# 41. Stage 3 — save / close / reopen

Save, close Blender, reopen, and verify that persistent canonical data remains valid.

At minimum verify:

```text
wall_id
finish_id
FinishSpan pointer
FinishSpan expected_wall_id
side
boundary kind/value
traversal direction
FinishExclusion records when present
vertical reference
profile_id
miter settings
```

After reopen:

- diagnosis must match the actual managed state;
- explicit regeneration must reproduce the accepted derived geometry;
- no Object-name-based rebinding may occur.

---

# 42. Stage 3 — unsupported `join_policy`

If Build 06-A does not implement `BREAK`, the implementation MUST NOT silently ignore:

```text
join_policy = BREAK
```

Acceptable behavior:

- prevent selecting unsupported value in normal UI, and
- reject unsupported persisted state during managed regeneration with a clear error.

`MITER` remains the supported Build 06-A behavior unless explicitly implemented otherwise within the original scope.

---

# 43. Stage 3 — unsupported `closed`

If full closed-loop FinishRun validation is not implemented in Build 06-A:

```text
closed = True
```

MUST NOT simply set the Curve cyclic flag without validating the last-to-first canonical/topological connection.

For Build 06-A, the preferred safe behavior is:

```text
reject closed=True as unsupported
```

unless full closed-loop validation is implemented and accepted.

Do not silently create a geometric closing segment unsupported by canonical topology.

---

# 44. Stage 3 — verification Profile identity

The verification Profile MUST NOT be trusted only because a Blender Object has a specific name.

Use deterministic managed identification.

Acceptable implementation may include hidden custom properties or equivalent metadata identifying:

```text
managed verification Profile
Profile version
expected Build 06-A role
```

Before reuse, verify that the object/data type and required Profile role are valid.

If a same-name unrelated Curve exists, do not silently use it as the managed verification Profile.

The implementation MAY create a uniquely named replacement managed Profile.

---

# 45. Stage 3 — floor and ceiling reference updates

Build 06-A MUST provide a supported way to update existing managed Finish objects after scene-level:

```text
floor_reference_z_mm
ceiling_reference_z_mm
```

changes.

Automatic Property update callbacks are not required.

An explicit managed operation such as:

```text
仕上げを一括再生成
```

is sufficient for Build 06-A if clearly exposed and transaction-safe.

The user MUST NOT be required to manually edit generated Curve points.

---

# 46. Stage 3 — Finish ID duplicates

Persistent `finish_id` duplicates SHOULD be detectable before Build 06-A completion.

At minimum:

- duplicate non-empty Finish IDs must not be silently treated as fully healthy managed identity;
- diagnosis SHOULD expose the ambiguity.

A convenient automatic Finish duplicate-repair UI is not required unless it is needed by existing Build 06-A operations.

Do not introduce heuristic ownership reassignment.

---

# 47. Stage 3 — Exclusion diagnosis

When Exclusion records exist:

- broken pointer/ID state MUST be diagnosable;
- ambiguous Wall ownership MUST not be labeled normal;
- split/delete/remap MUST remain deterministic;
- no heuristic rebind is allowed.

A full user-facing Exclusion editing system remains out of scope.

---

# 48. Stage 3 — Preview consistency

The interactive path preview is derived UI and is not canonical truth.

The final commit validation remains authoritative.

However, Preview SHOULD avoid displaying a candidate as valid when the same current final resolver can already prove it invalid.

Where practical:

- reuse the same canonical face resolver;
- reuse endpoint/transition validation;
- show blocker-invalid candidates as unavailable or clearly invalid.

Perfect final bevel geometry preview is not required in Build 06-A.

Preview improvements MUST NOT delay safety corrections.

---

# 49. Stage 3 — Build identification

The acceptance ZIP and source tree SHOULD make the Build under test unambiguous.

Update at least one user/developer-visible location such as:

```text
README build status
internal build label
development version string
```

so that Build 06-A corrected test packages cannot easily be confused with Build 01 or earlier packages.

This is a test/release hygiene requirement, not a feature expansion.

---

# 50. Final Build 06-A acceptance gate

Build 06-A may be declared complete only after all of the following are true.

## 50.1 Original requirements

The original `BUILD_06_A_SPECIFICATION.md` acceptance requirements remain satisfied unless explicitly narrowed by this addendum.

The formal original Blender acceptance suite remains required.

## 50.2 Correction requirements

All Stage 1 requirements are accepted.

All Stage 2 requirements are accepted.

All Stage 3 requirements are accepted.

## 50.3 Build 05-B regression

The full relevant Build 05-B Wall regression suite must continue to pass.

Build 06-A corrections MUST NOT regress:

```text
Wall creation
endpoint snapping
segment splitting
junction topology
corner / T / Cross Wall mesh behavior
endpoint movement
dimension editing
safe deletion
repair
Undo / Redo behavior already guaranteed by 05-B
```

## 50.4 Automated tests

All existing automated tests must remain passing.

New tests required by this addendum must be added.

Test count alone is not acceptance.

The tests must exercise the correction contracts described here.

## 50.5 Blender 5.2 runtime acceptance

Automated pure-Python tests do not replace Blender runtime acceptance.

The corrected Build 06-A must be tested in Blender 5.2 LTS for:

```text
viewport modal behavior
actual Curve bevel orientation
actual Object/Data replacement
actual Undo / Redo
PointerProperty persistence
save / reopen
Mesh conversion
transaction rollback paths that require Blender datablocks
```

---

# 51. Required acceptance record

Maintain a correction acceptance record with at least:

```text
test name
stage
automated / Blender runtime
PASS / FAIL / BLOCKED
commit tested
notes
```

A defect discovered during runtime acceptance MUST NOT be reclassified as PASS merely because canonical path data appears correct.

For example:

```text
one-Wall LEFT path position = PASS
one-Wall LEFT Profile outward direction = FAIL
```

are separate acceptance facts.

---

# 52. Error-handling policy

Build 06-A is allowed to reject a configuration it cannot safely resolve.

When rejecting:

- preserve the previous valid managed state;
- give a useful user-facing error;
- do not guess a branch;
- do not auto-bridge disconnected partial intervals;
- do not auto-route around Wall solids;
- do not silently bake Object Transform;
- do not silently delete attachment data.

Safe refusal is preferred to plausible-looking invalid geometry.

---

# 53. No Mesh-based recovery

No correction stage may solve these problems by reverse-engineering canonical state from generated Wall Mesh or Finish Mesh/Curve geometry.

The source remains:

```text
Wall canonical data
Wall reciprocal topology
Finish canonical attachment data
```

Generated geometry is disposable derived output while managed.

---

# 54. Profile Library boundary

The Build 06-A verification Profile exists only to prove:

```text
wall-face path
physical side
vertical direction
corner continuity
managed regeneration
```

Do not turn Stage 2 into Build 06-B.

The corrected Profile orientation logic SHOULD be reusable by Build 06-B, but Build 06-A does not require:

```text
three final baseboard profiles
profile thumbnails
user profile browser
custom profile authoring
```

---

# 55. Door/window and opening boundary

FinishExclusion remains future-facing infrastructure.

This correction MUST NOT implement the Build 09 door/window opening system.

The correction only ensures that existing Exclusion records, if present, do not violate identity, transaction, split, delete, and diagnosis safety.

---

# 56. Required implementation reports

Every Codex correction stage report MUST include:

```text
starting commit
ending local commit
commit message
changed files
automated test count
test result
compileall result
git diff --check result
git diff --cached --check result
known Blender-runtime items still requiring acceptance
```

Do not fetch/pull/push/ls-remote GitHub from Codex Cloud when the environment is known to reject Git network access.

Do not create ZIP files in Codex.

ZIP packaging remains outside Codex implementation work.

---

# 57. Stage handoff rule

A later stage MUST NOT begin merely because Codex reports tests passing.

The sequence is:

```text
Codex implementation
        ↓
file-by-file / targeted code review
        ↓
accepted local source state
        ↓
Blender 5.2 acceptance ZIP
        ↓
runtime acceptance
        ↓
stage accepted
        ↓
next stage
```

If runtime testing finds a stage defect:

- fix that stage first;
- do not carry a known foundational defect into the next stage unless this addendum explicitly marks it as a later-stage known issue.

The known Profile inward-projection defect is the explicit exception allowed to remain after Stage 1 because it is assigned to Stage 2.

---

# 58. Summary of normative correction decisions

The Build 06-A correction contract is:

```text
1. Continue the current Build 06-A implementation.
2. Keep the original Build 06-A specification.
3. Apply this addendum with precedence where it clarifies or conflicts.
4. Do not finalize Finish geometry from intermediate split topology.
5. Finalize dependencies only after the complete Wall operation topology is known.
6. Collect affected FinishRuns from both old and new dependency scope.
7. Validate referenced managed Walls consistently, including Object Transform.
8. Validate existing Exclusion references before remap/partition.
9. Treat Wall + Finish updates as one transaction.
10. Prepare replacement derived data before discarding old valid data.
11. Roll back even if failure occurs during commit.
12. Prove minimum rollback behavior in Stage 1 with failure injection.
13. In Stage 2, validate canonical interval reach before surface joining.
14. Do not extend partial intervals to make disconnected spans appear connected.
15. Apply blocker safety at Run start/end as well as internal transitions.
16. Make Profile 10 mm projection physically outward and 60 mm world-up.
17. Test all LEFT/RIGHT × FORWARD/REVERSE orientation combinations.
18. Use Stage 3 for hardening and formal acceptance, not for first implementing safety.
19. Keep 05-C, 06-B Profile Library, Room recognition, opening automation, and other later features out of this correction.
20. Declare Build 06-A complete only after original acceptance + correction acceptance + Build 05-B regression pass.
```

---

# 59. Implementation principle

The goal of this correction is not to make Build 06-A larger.

The goal is to make the attachment foundation reliable enough that Build 06-B, Build 06-C, and later opening-aware finish work can reuse it without inheriting ambiguous update ownership or invalid geometry.

The preferred result is:

```text
small canonical model
        +
explicit topology
        +
conservative validation
        +
transaction-safe regeneration
        =
predictable Blender-editable architectural base geometry
```

This remains aligned with the project’s production-accelerator philosophy.

---

# END OF BUILD 06-A CORRECTION ADDENDUM
