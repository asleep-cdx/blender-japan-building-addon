# BUILD 05-B SPECIFICATION

## 日本住宅モデラー — Wall System Finalization / Stability / UX

- Target: Blender 5.2 LTS
- Repository: `asleep-cdx/blender-japan-building-addon`
- Required base commit: `41fde96e9aeef45558048dbdf8aed0193590f11d`
- Base message: `Implement Build 05-A wall segment splitting`
- Build position: Wall development phase finalization

---

# 1. Purpose

Build 05-B is the final Wall-focused build before the project moves on to the next major systems such as doors, windows, floors, ceilings, floor-plan-assisted modeling, and assets.

This build must not redesign the Wall data model.

The purpose is to close the Wall phase by making the existing deterministic Wall system safe and practical across the full daily workflow:

```text
create
-> snap / align
-> split
-> edit endpoint
-> edit dimensions
-> delete
-> repair
-> undo / redo
-> save / reopen
```

The source-of-truth principle remains:

```text
canonical Wall data + endpoint topology -> derived junction -> derived Mesh
```

Mesh is never the canonical source.

---

# 2. Existing invariants that MUST remain unchanged

## 2.1 Units

- UI: millimeters
- Internal canonical geometry: meters
- Convert at the geometry/UI boundary only.

## 2.2 Canonical Wall data

Each managed Wall continues to use:

```text
Wall.start
Wall.end
Wall.wall_thickness
Wall.wall_height
START endpoint topology
END endpoint topology
```

Do not add an independently stored Wall length.

Length is always derived from `start` / `end`.

## 2.3 Wall reference

Wall geometry is based on the Wall centerline / 壁芯.

## 2.4 One Wall = one Blender Object

Do not merge multiple canonical Wall segments into one mesh object automatically.

## 2.5 Object Transform

Canonical start/end are world-space saved values.

Managed geometry assumes identity Object Transform during normal managed operations.

Build 05-B must improve detection, exclusion, repair guidance, and UI status, but must NOT silently bake arbitrary Object Transform into canonical Wall data.

## 2.6 Edit Mode modifications

Manual mesh edits do not alter canonical Wall data.

Managed regeneration may overwrite those edits.

Build 05-B may provide an explicit repair/regenerate action, but must not infer canonical geometry from manually edited mesh.

---

# 3. Build 05-B scope overview

Build 05-B contains the following 13 items.

```text
01. mid-segment snap + Shift constraint coexistence
02. Object Transform candidate handling unified across drawing aids
03. Move START/END to another Wall interior, including host split
04. Delete / rebuild / abnormal-state cleanup
05. Full Build 04 through Build 05-A regression
06. Safe managed Wall delete operator
07. Minimum split-segment safety
08. Read-only Wall length display
09. Save -> close/reopen -> persistence acceptance tests
10. Undo/Redo strengthening for complex operations
11. Managed-state warning + explicit canonical repair operation
12. Standard Shift+D duplicate handling defined and hardened
13. UI button rename: visible label becomes “＋ 壁を生成”
```

The implementation should remain focused on Wall-system finalization rather than new architectural systems.

---

# 4. UI wording change — mandatory

The current new-Wall button visually appears like:

```text
＋  ＋壁
```

because Blender already draws the `ADD` icon and the text itself also contains a plus sign.

Change it so the visible result is:

```text
＋  壁を生成
```

Implementation intent:

```python
new_wall_box.operator(
    "jhm.create_wall",
    text="壁を生成",
    icon="ADD",
)
```

Do NOT use `text="＋ 壁を生成"` while also using `icon="ADD"`, because that would again display two plus signs.

This is a label-only UX change. Operator id remains unchanged.

---

# 5. Selected Wall UI final form

The selected managed Wall box should continue to show existing information and add Wall length and managed-state status.

Normal example:

```text
選択中の壁
壁厚: 130.0 mm
壁高さ: 2500.0 mm
壁長さ: 3640.0 mm
壁角度: 90.0°
管理状態: 正常

始点接続: ...
始点形状: ...
始点接合: ...

終点接続: ...
終点形状: ...
終点接合: ...

[壁寸法を変更]
[接合を再生成]
[管理状態へ復元]

[始点を移動]
[終点を移動]

[壁を削除]
```

If canonical start/end are invalid:

```text
壁長さ: 判定不能
壁角度: 判定不能
```

If Object Transform is non-identity:

```text
管理状態: 要復元（Object Transformあり）
```

If detectable topology integrity is invalid / non-reciprocal:

```text
管理状態: 要復元（接続情報不整合）
```

The status text may be split into multiple labels if Blender UI width requires it.

---

# 6. Read-only Wall length

## 6.1 Definition

Wall length is derived only from canonical `start` and `end` XY coordinates.

```text
length_m = hypot(end.x - start.x, end.y - start.y)
length_mm = length_m * 1000
```

Do not use:

- mesh dimensions
- bounding box
- Object Transform
- evaluated mesh

## 6.2 Display

Display one decimal place:

```text
壁長さ: 3640.0 mm
```

## 6.3 No editable length field in 05-B

Build 05-B MUST NOT add direct numeric Wall length editing.

Reason: direct length editing requires additional rules about which endpoint remains fixed and how attached junction topology should move.

That is intentionally deferred until after the Wall phase review.

---

# 7. mid-segment snap + Shift constraint coexistence

## 7.1 Problem observed during Build 05-A acceptance testing

Current priority is effectively:

```text
endpoint snap
> mid-segment snap
> alignment
> Shift 15°
```

This makes an H-shaped layout inconvenient.

When connecting between two parallel host Walls, the second endpoint can mid-snap to the host but cannot simultaneously remain exactly vertical/horizontal through Shift.

Build 05-B must solve this.

## 7.2 New behavior

Endpoint snap remains absolute first priority.

When a Wall start point already exists and Shift is held:

1. Determine the nearest 15-degree constrained drawing direction from the current start point.
2. Treat that direction as a forward ray.
3. For each eligible visible managed host Wall, intersect the constrained ray with the host canonical centerline segment.
4. Accept an intersection only if:
   - it lies forward on the constrained ray,
   - it lies safely inside the host segment,
   - the corresponding screen-space point is within the mid-segment snap threshold,
   - the host is otherwise eligible.
5. If exactly one closest valid intersection exists, use that point as the mid-segment snap candidate.

This produces a point satisfying BOTH:

```text
Shift constrained angle
AND
host canonical centerline
```

## 7.3 Example

Two horizontal hosts:

```text
-----------------------------
              |
              |
-----------------------------
```

Starting from the lower host and holding Shift near the upper host should allow an exact 90° vertical Wall whose endpoint splits the upper host at the ray/segment intersection.

## 7.4 Candidate priority

Required priority:

```text
1. endpoint snap
2. Shift-constrained mid-segment intersection (when Shift held and start exists)
3. normal mid-segment projection
4. X/Y / extension alignment
5. ordinary free Shift 15° candidate
6. raw point
```

Do not allow a lower-priority candidate to override an already valid higher-priority candidate.

## 7.5 Ambiguity

Equal-distance ambiguous hosts must remain rejected.

Do not break Build 05-A deterministic ambiguity semantics.

---

# 8. Unified Object Transform candidate exclusion

## 8.1 Current issue

Build 05-A already excludes transformed Walls from mid-segment snap and extension alignment, but endpoint snap / X-Y helpers can still expose canonical positions from a transformed Wall.

This produces inconsistent drawing assistance.

## 8.2 Build 05-B rule

For interactive drawing candidate discovery, a managed Wall with non-identity Object Transform must be excluded consistently from ALL Wall-derived assist candidates:

```text
endpoint snap
X alignment
Y alignment
extension alignment
mid-segment snap
Shift-constrained mid-segment intersection
```

The transformed Wall remains visible as a Blender object, but is ignored as an assist target.

## 8.3 Moving endpoint operator

The Wall being edited already rejects non-identity transform.

Candidate host Walls during endpoint movement must also follow the same unified exclusion rules.

## 8.4 No silent bake

Do not convert transformed object coordinates back into canonical start/end automatically.

Repair is explicit through the managed-state repair operation described later.

---

# 9. Move START / END to host Wall interior

## 9.1 Goal

The existing buttons:

```text
始点を移動
終点を移動
```

must gain the same safe host-interior connection capability as new-Wall drawing.

## 9.2 Behavior

When moving one endpoint of an existing Wall:

- endpoint snap to another Wall endpoint continues to work,
- mid-segment snap to another managed host Wall interior becomes supported,
- final commit splits the host only at commit time,
- the moved endpoint attaches to the split junction using ordinary endpoint topology.

## 9.3 No mutation during hover

Hover / preview must never split the host.

ESC / right-click must leave all canonical data, topology, objects, collections, and meshes unchanged.

## 9.4 Source Wall exclusion

The Wall whose endpoint is being moved must not be considered as its own midpoint host.

## 9.5 Existing junction at moved endpoint

If the moved endpoint is currently attached to a junction:

1. capture old affected members,
2. detach the moved endpoint,
3. update canonical endpoint,
4. split target host if midpoint target,
5. attach moved endpoint to new target junction,
6. regenerate old and new affected Walls atomically.

The opposite endpoint remains canonical and connected as before.

## 9.6 Host inheritance

Host split uses the same Build 05-A rules:

- original host = canonical START-side segment,
- successor = canonical END-side segment,
- thickness inherited,
- height inherited,
- materials inherited,
- collection membership inherited,
- old START topology stays on original,
- old END topology transfers to successor END.

## 9.7 Transaction

Endpoint move + host split must be one Blender Undo operation.

Any failure after mutation begins must restore:

- source Wall canonical start/end,
- host original canonical end,
- topology snapshot,
- created successor cleanup,
- derived mesh state as safely as existing atomic regeneration architecture allows.

---

# 10. Minimum split-segment safety

## 10.1 Problem

A mathematically interior projection can still lie extremely close to a host endpoint, especially at unusual zoom levels.

Creating microscopic canonical Wall segments is undesirable and can stress junction geometry.

## 10.2 Safety threshold

Introduce a dedicated split safety threshold independent from the generic degeneracy epsilon.

Recommended initial value:

```text
_MIN_SPLIT_SEGMENT_M = 0.001
```

which equals 1 mm.

This is a numerical safety threshold, not a building-code minimum Wall length.

## 10.3 Rule

A split point is valid only when BOTH resulting canonical host segments are strictly longer than the split safety threshold.

```text
distance(host.start, split) > threshold
AND
distance(split, host.end) > threshold
```

## 10.4 Endpoint priority unchanged

Endpoint snap still has the higher 16 px priority.

The split safety rule is an additional canonical safety check, not a replacement for endpoint snapping.

## 10.5 Reuse

The same rule must be used by:

- new Wall midpoint connection,
- moved endpoint midpoint connection,
- direct split helper validation.

No caller should be able to bypass it accidentally.

---

# 11. Safe managed Wall deletion

## 11.1 New operator

Add a dedicated managed delete operator, for example:

```text
jhm.delete_wall
```

Exact internal id may differ if naming conventions require it, but UI text must be:

```text
壁を削除
```

## 11.2 Confirmation

Deletion should use a Blender confirmation dialog.

Suggested message:

```text
選択中のWallを削除しますか？
```

## 11.3 Why this operator exists

Standard Blender Delete removes the object but does not guarantee immediate regeneration of connected surviving Wall meshes.

The managed delete operator must safely close topology first.

## 11.4 Transaction sequence

Recommended sequence:

1. Validate selected managed Wall still exists.
2. Snapshot topology.
3. Collect affected surviving Walls at START and END before detaching.
4. Detach START.
5. Detach END.
6. Sanitize stale/invalid topology where appropriate.
7. Regenerate surviving affected Walls from the now-updated topology.
8. Remove selected Wall object and orphaned mesh datablock.
9. Finish as one Undoable operator.

If a fallible operation fails before object removal:

- restore topology snapshot,
- leave Wall object present,
- report Japanese error,
- safely regenerate original affected state where necessary.

## 11.5 Transform state

Safe delete may delete a transformed managed Wall because deletion does not require inferring geometry from its transformed mesh.

The important requirement is safe detachment and neighbor regeneration.

## 11.6 No auto-merge after deletion

Example:

```text
------●------
      |
      |
```

If the branch is deleted, the two main Wall segments remain two canonical Wall Objects.

They may regenerate visually as a straight continuation, but Build 05-B MUST NOT automatically merge them into one Wall Object.

Automatic canonical merge is out of scope.

---

# 12. Rebuild / abnormal-state cleanup

## 12.1 Existing button

Keep:

```text
接合を再生成
```

## 12.2 Strengthen explicit rebuild

When rebuilding a managed Wall, the operation should safely clean topology entries that point to deleted/non-managed targets.

It should also detect and remove clearly non-reciprocal copied/stale edges according to the topology integrity policy defined below.

Then regenerate the selected Wall and valid connected neighbors from canonical data.

## 12.3 Standard Delete recovery

If a user used Blender standard Delete on one Wall by mistake, selecting a surviving neighbor and pressing `接合を再生成` should be sufficient to:

- discard stale connection references,
- recompute the surviving mesh from current valid topology.

This does NOT mean standard Delete becomes the recommended workflow.

The dedicated `壁を削除` button remains the supported method.

---

# 13. Managed-state status and repair

## 13.1 New read-only status

Display a simple managed-state status in the selected Wall box.

Minimum states:

```text
管理状態: 正常
管理状態: 要復元（Object Transformあり）
管理状態: 要復元（接続情報不整合）
```

Multiple problems may be combined if needed.

## 13.2 Explicit repair operator

Add a button:

```text
管理状態へ復元
```

This operation must be explicit and Undoable.

## 13.3 Repair semantics

Repair must follow the canonical-data-first rule.

It may:

1. reset Object Transform to identity,
2. remove stale / malformed / non-reciprocal connection entries that cannot be trusted,
3. regenerate the Wall mesh from saved canonical start/end/thickness/height,
4. regenerate valid connected neighbors as necessary.

It MUST NOT:

- infer new canonical start/end from current mesh,
- infer canonical dimensions from Object Transform,
- preserve arbitrary manual Edit Mode mesh changes.

## 13.4 User expectation

If a user manually moved a Wall using `G` and then chooses `管理状態へ復元`, the object returns to the canonical position stored in `Wall.start` / `Wall.end`.

That is intentional.

The action should use a confirmation dialog because it may visibly move/reset the object.

Suggested confirmation text:

```text
保存済みのWall情報から管理状態を復元します。Object Transformや手動Mesh編集は破棄されます。続行しますか？
```

---

# 14. Topology integrity hardening

## 14.1 Reciprocal topology principle

A valid stored connection edge is not merely a pointer to a live managed Wall.

For managed topology, an edge should be reciprocal:

```text
A.START -> B.END
B.END   -> A.START
```

## 14.2 New helper concept

Add a pure/safe helper concept such as:

```text
is_reciprocal_connection(source_object, source_endpoint, connection)
```

or equivalent.

It should verify that the target endpoint contains the reverse edge.

## 14.3 Avoid recursive validation loops

Do not implement reciprocity by recursively calling a function that itself requires reciprocity.

Use a direct target collection search.

## 14.4 Existing normal topology

All topology created by managed operators must remain reciprocal and complete.

Build 05-B must not change the complete-graph semantics of multi-member junctions.

## 14.5 Non-reciprocal copied/stale edge

A one-sided edge should not participate in junction classification or mesh generation as if it were trusted topology.

Explicit repair/rebuild may purge it.

---

# 15. Standard Shift+D duplicate behavior

## 15.1 Supported status

Blender standard `Shift + D` duplication of managed Walls is NOT a supported managed Wall operation in Build 05-B.

Do not attempt to silently make arbitrary Blender duplication topology-safe.

## 15.2 Why

A Blender duplicate may copy the source Wall's connection collections, but neighboring Walls do not automatically receive reciprocal references to the duplicate.

This can create one-sided topology.

## 15.3 Build 05-B hardening

Build 05-B must ensure that such one-sided copied topology:

- does not silently act as valid reciprocal junction topology,
- is reflected in managed-state status when detectable,
- can be cleared by `管理状態へ復元` / strengthened rebuild.

## 15.4 No safe duplicate operator required

A dedicated “Wallを複製” managed operator is NOT required in 05-B.

If desired, that can be considered after the Wall phase review.

---

# 16. Save / reopen persistence acceptance

No new persistence format should be introduced unless necessary.

The existing Blender property storage remains authoritative.

Build 05-B acceptance must include:

1. Create a scene containing at least:
   - Corner,
   - T junction,
   - Cross or supported multi-endpoint arrangement,
   - split Wall,
   - unequal thickness connection,
   - oblique Wall,
   - material-assigned Wall,
   - Wall linked to multiple Collections.
2. Save `.blend`.
3. Close Blender.
4. Reopen Blender 5.2 LTS.
5. Reopen the `.blend`.
6. Confirm:
   - canonical geometry unchanged,
   - connection counts unchanged,
   - classification unchanged,
   - joint mesh unchanged,
   - material and Collection membership unchanged,
   - `接合を再生成` produces the same result.

Persistence failure is a release blocker for the Wall phase.

---

# 17. Undo / Redo strengthening

Build 05-A already confirmed single-host split Undo/Redo.

Build 05-B acceptance must additionally verify one-step Undo/Redo for:

```text
A. two-host split during new Wall creation
B. endpoint move to host midpoint + host split
C. safe managed Wall delete
D. managed-state repair/reset
```

Each operation must be one logical Undo step.

Undo must restore canonical data, topology, object count, and visible joints.

Redo must restore the Build 05-B operation.

---

# 18. Existing Build 04 / 05-A regression requirements

Build 05-B is the Wall-system closeout build.

The following must continue to work.

## 18.1 Basic drawing

- horizontal Wall
- vertical Wall
- arbitrary Wall
- Shift 15° drawing
- default wall thickness / height

## 18.2 Endpoint snapping

- START endpoint snap
- END endpoint snap
- endpoint priority over midpoint
- connected endpoint complete topology

## 18.3 X / Y alignment

- X guide
- Y guide
- combined X/Y candidate
- deterministic candidate behavior

## 18.4 Extension alignment

Preserve Build 04-H:

- 45° extension
- 15° extension
- arbitrary canonical angle extension
- segment exterior only
- endpoint priority
- extension alignment alone creates no topology
- X/Y distance comparison
- transformed Wall exclusion

## 18.5 Corner

Preserve supported Corner / miter behavior.

## 18.6 Continuation

Preserve:

- 180° continuation
- unequal thickness safe continuation
- mixed endpoint direction
- unsafe near-180 fallback behavior

## 18.7 T junction

Preserve:

- branch / main classification
- oblique T
- unequal thickness host
- split-generated T topology

## 18.8 Cross

Preserve supported Cross semantics and pairing.

Ambiguous four-way remains unsupported.

## 18.9 Unsupported / fallback

Preserve Build 04-H semantics:

```text
OVERLAP
THREE_WAY
FOUR_WAY
MULTI
INVALID
unsafe CONTINUATION
unsafe supported solver
```

Unsupported / invalid cases must remain safe and deterministic.

## 18.10 Build 05-A split behavior

Preserve:

- midpoint START creation
- midpoint END creation
- two different host split
- same-host midpoint-midpoint rejection
- same-host endpoint-midpoint rejection
- same-host midpoint-endpoint rejection
- same-host endpoint-endpoint remains permitted by same-host split guard
- transformed host excluded
- ambiguous equal host candidate rejected
- old START topology retained
- old END topology transferred
- dimensions inherited
- materials inherited
- Collections inherited
- first click does not mutate
- ESC cancel does not mutate
- geometric crossing alone does not auto-split
- split Wall can be split again

---

# 19. Drawing-preview / candidate requirements

## 19.1 Visual distinction

Existing snap marker and alignment guide rendering may be reused.

Do not require new colors solely for Build 05-B.

## 19.2 No mutation from preview

All preview logic remains transient.

No object creation, topology mutation, host split, or canonical mutation from:

- mouse move,
- Shift press/release,
- first midpoint click before final new-Wall commit,
- endpoint-move hover.

## 19.3 View clipping

Candidates whose projected 2D points are unavailable should be ignored safely.

No exception should escape to Blender UI.

---

# 20. Transaction and rollback principles

Every operator that changes more than one Wall must be designed as an explicit transaction.

Applicable operations:

```text
new Wall + one/two host split
endpoint move + host split
safe delete
managed-state repair
```

Before persistent topology mutation, capture sufficient state to restore:

- topology snapshot,
- modified canonical endpoints,
- newly created successor objects,
- relevant transform state when repair modifies it.

Do not leave partial topology after exceptions.

User-facing errors must be Japanese.

---

# 21. Suggested code organization

Avoid putting all Build 05-B logic into `operators.py`.

Recommended responsibilities:

## `drawing_alignment.py`

Pure math helpers:

- constrained ray construction,
- ray/segment intersection,
- safe interior/split validation,
- derived Wall length,
- deterministic candidate comparison.

No `bpy` dependency.

## `connections.py`

Topology integrity:

- reciprocal connection check,
- stale/non-reciprocal cleanup helpers,
- existing detach/transfer/snapshot/restore.

## `wall_split.py`

Continue owning host split semantics.

Add shared split-point safety validation if appropriate.

## New optional module: `wall_state.py`

Recommended if it keeps operators small.

Possible responsibilities:

- managed-state inspection,
- transform status,
- topology-integrity status,
- canonical repair helpers.

## `operators.py`

Orchestration only:

- create Wall transaction,
- endpoint move transaction,
- safe delete,
- rebuild,
- managed-state repair.

## `ui.py`

Presentation only:

- button text change,
- length display,
- managed-state labels,
- delete and repair buttons.

---

# 22. Unit test requirements

Existing 86 tests MUST remain passing.

Add focused Build 05-B tests covering at minimum:

## Pure geometry

- canonical Wall length horizontal / vertical / oblique
- invalid length inputs
- ray/segment intersection horizontal host
- vertical host
- 15° / 45° constrained ray
- forward-ray only behavior
- parallel no-intersection
- intersection outside host rejected
- split safety threshold on both sides
- reversed host direction invariance where appropriate

## Candidate semantics

- endpoint priority preserved conceptually
- constrained midpoint unique closest
- equal-distance constrained midpoint ambiguity rejected
- transformed candidate exclusion helper if extracted pure enough

## Topology integrity

- reciprocal edge accepted
- one-sided edge detected
- stale target detected
- cleanup removes one-sided/stale edges
- normal complete junction preserved
- cleanup does not remove unrelated valid peer edges

## Endpoint move transaction support

Mock-level coverage where practical:

- old endpoint detach
- host END transfer during split
- new junction attach
- rollback after split failure

## Safe delete

Mock-level coverage where practical:

- START/END detached
- peer-peer edges preserved
- surviving neighbors identified
- topology rollback on failure concept

## Managed-state repair

Where practical without Blender:

- topology integrity status
- no mesh->canonical inference

If full Blender API mocking becomes disproportionate, keep pure topology helpers strongly tested and cover orchestration in Blender acceptance.

---

# 23. Blender 5.2 LTS acceptance test plan

The final Build 05-B implementation must be tested in Blender with clear Japanese steps.

At minimum include:

```text
01. UI “＋ 壁を生成” wording
02. Wall length 0° horizontal
03. Wall length 45° / 90°
04. Object Transform Wall excluded from endpoint snap
05. Object Transform Wall excluded from X/Y alignment
06. Object Transform Wall excluded from extension and midpoint
07. managed-state warning appears after G/R/S
08. 管理状態へ復元 resets transform and mesh to canonical
09. manual Edit Mode mesh change is overwritten by explicit repair/regenerate
10. H-shape: Shift + midpoint produces exact 90° connection
11. 45° Shift + midpoint intersection
12. endpoint still beats midpoint under Shift
13. move START to another Wall midpoint
14. move END to another Wall midpoint
15. moving connected endpoint away regenerates old junction
16. endpoint move + midpoint split Undo/Redo one step
17. split safety rejects endpoint-near microscopic split
18. safe delete isolated Wall
19. safe delete Corner member
20. safe delete T branch -> main Walls remain separate canonical objects but visually continuation
21. safe delete T main member safely updates survivors
22. safe delete Undo/Redo one step
23. standard Delete mistake + surviving neighbor “接合を再生成” repairs stale mesh/topology
24. standard Shift+D duplicated connected Wall is reported as topology inconsistency rather than trusted junction
25. 管理状態へ復元 clears unsafe one-sided copied topology
26. two-host split Undo/Redo regression
27. save / close / reopen persistence scene
28. material persistence
29. multi-Collection membership persistence
30. split Wall persistence
31. Corner regression
32. Continuation regression
33. unequal thickness regression
34. T regression
35. Cross regression
36. oblique T/Cross regression
37. unsupported junction regression
38. extension alignment regression
39. geometric crossing no auto-split regression
40. split-after-split regression
```

The exact count may expand during implementation review, but these cases must be represented.

---

# 24. Explicit non-goals for Build 05-B

Do NOT add:

- door system
- window system
- opening system
- floor system
- ceiling system
- room detection
- automatic floor-plan recognition
- asset placement
- automatic Wall merge after branch deletion
- direct numeric Wall length editing
- arbitrary Object Transform bake into canonical Wall data
- automatic split merely because two Wall centerlines geometrically cross
- safe managed duplication operator
- persistent midpoint connection type

---

# 25. Error / warning language

Build 05-B new user-facing messages should be Japanese.

Examples:

```text
このWallにはObject Transformがあります。管理状態へ復元してください。
接続情報に不整合があります。管理状態へ復元してください。
Wallを安全に削除できませんでした。
Wallを安全に分割できませんでした。
分割位置がWall端点に近すぎます。
接続先Wallが変更されたため操作を完了できませんでした。
保存済みのWall情報から管理状態を復元します。
```

Hover-time candidate exclusion should remain silent.

Do not spam reports during mouse movement.

---

# 26. Performance and determinism

Current project scale permits linear scan over visible managed Walls.

No spatial index is required in Build 05-B.

Do not make candidate choice depend on:

- Object name
- Blender numeric suffix
- Collection iteration order
- object creation order
- Python hash order

Use:

- screen distance,
- canonical coordinates,
- explicit ambiguity rejection,
- stable geometry rules.

---

# 27. Codex implementation workflow

Codex Cloud must use the local repository base already provided to it.

Known limitation:

```text
GitHub network Git from Codex Cloud -> 403
```

Therefore Codex MUST NOT waste time on:

```text
git fetch
git pull
git push
git ls-remote
```

Codex may:

- inspect local files,
- implement,
- run tests,
- run compileall,
- run git diff checks,
- create a local commit.

Codex MUST NOT create a ZIP for the user.

After implementation:

1. user copies changed diffs/files to ChatGPT one file at a time,
2. ChatGPT reviews,
3. focused fixes if needed,
4. ChatGPT packages Blender test ZIP / repo overlay as needed,
5. user performs Blender tests,
6. Windows repository receives final reviewed files,
7. Windows runs tests,
8. Windows commits and pushes to GitHub.

---

# 28. Required Codex validation commands

At minimum:

```text
python -m compileall -q japanese_house_modeler tests
python -B -m unittest discover -s tests
git diff --check
git diff --stat
git status --short
```

Report:

- total unit test count,
- PASS/FAIL,
- compile result,
- diff-check result,
- local commit SHA,
- changed file list.

---

# 29. Definition of Done — Build 05-B / Wall phase

Build 05-B is complete only when ALL of the following are true:

- UI button visibly reads `＋ 壁を生成` with only one plus icon
- selected Wall displays derived length
- selected Wall displays direction-independent angle
- managed-state status is visible
- transformed candidate Walls are excluded consistently from all drawing aids
- midpoint + Shift can create exact constrained host intersections
- H-shape can be drawn exactly using midpoint connection
- endpoint priority remains intact
- START endpoint move can attach to host midpoint
- END endpoint move can attach to host midpoint
- endpoint move midpoint commit splits host only on final click
- endpoint move cancel leaves no mutation
- split safety prevents microscopic endpoint-near segments
- safe Wall delete exists
- safe delete detaches topology and regenerates surviving neighbors
- delete does not auto-merge canonical main segments
- explicit rebuild can clean stale topology after accidental standard Delete
- topology reciprocity is validated/hardened
- standard Shift+D one-sided copied topology is not silently trusted
- explicit managed repair can reset Object Transform and regenerate canonical mesh
- repair never infers canonical data from mesh
- Undo/Redo passes for complex new operations
- save/close/reopen persistence passes
- thickness/height/material/Collection persistence remains correct
- all 86 pre-05-B unit tests remain PASS
- new 05-B tests all PASS
- Blender 5.2 LTS acceptance tests all PASS
- Build 04-H and 05-A regressions pass
- Windows worktree is clean after final commit
- GitHub `main` contains the final 05-B implementation commit

At that point the Wall system is considered complete enough to pause Wall development and review the project-wide next-stage roadmap.

---

# 30. Final principle

Build 05-B must finish the Wall system without changing its conceptual core.

The final architecture remains:

```text
User action
-> deterministic canonical Wall update
-> deterministic endpoint topology update
-> derived junction classification
-> derived mesh regeneration
```

Never reverse that flow.

Do not infer authoritative Wall data from mesh appearance.

Do not hide unsafe state through silent guesses.

Prefer explicit rejection, explicit repair, atomic transactions, and deterministic behavior.
