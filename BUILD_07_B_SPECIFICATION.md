# BUILD 07-B SPECIFICATION
## 日本住宅モデラー — Standard Residential Straight Stair + Stepped Closed Underside + Side Boards

> **Status: CORRECTED BY AUTHORITATIVE ADDENDUM**  
> 本文書は Build 07-B の基礎仕様であるが、2026-09-21 の Blender runtime visual review で `STEPPED_CLOSED` の設計欠陥が判明した。  
> **`BUILD_07_B_CORRECTION_ADDENDUM.md` を必ず併読し、矛盾する場合は Addendum を正とする。**  
> 特に §§17–23 と §30 のうち、Tread/Riser裏面または階段内部の視覚的露出を許す解釈は superseded である。

---

## 1. Purpose

Build 07-B は、Build 07-A で Acceptance 済みとなった standalone Managed Stair Core を維持したまま、最初の実用的な日本住宅向け Straight Stair へ拡張する Build である。

07-B の中心目的は次の4点とする。

1. `STEPPED_CLOSED` の段々閉じ下面を追加する。
2. 左右独立 ON / OFF の stepped Side Board を追加する。
3. Tread / Riser / Underside / Side Board の part-specific Material assignment を追加する。
4. Build 07-A で保存された BASIC Stair を自動変更せず、明示操作によってのみ 07-B Residential Stair へ移行できる互換性契約を確立する。

07-B は Straight Stair の住宅仕様化を対象とし、Multi-point Path、Landing、Winder、Open Stair 等は後続 Build へ残す。

---

## 2. Accepted baseline

07-B は以下を baseline とする。

- Build 05-B — Wall System
- Build 06-A — Finish Attachment Foundation
- Build 06-B — Baseboard
- Build 06-C — Crown Moulding / Profile Thumbnail UI
- Build 07-A — Stair Core + Top-view 2-point Straight Stair
- `DEVELOPMENT_WORKFLOW.md`
- `ROADMAP.md`

07-A の accepted production behavior を壊さない。

本仕様確定時に確認した `main` は次である。

```text
30def96abc42c07a58b82d327df18d7415aea47b
```

この commit を Build 07-B 実装開始時の baseline とする。

---

## 3. Roadmap position

```text
07-A  Stair Core + Top-view 2-point Straight Stair
      ACCEPTED
        ↓
07-B  Standard Residential Straight Stair
      + Stepped Closed Underside
      + Side Boards
        ↓
07-C  Sloped Closed Underside
      + Straight Stair Finish Variants
        ↓
07-D  Multi-point Path + L/U + Landing
        ↓
07-E  Winder / 廻り段
        ↓
07-F  Open / Support Variants
```

07-D で予定している以下は 07-B へ前倒ししない。

- Shift による Path 角度拘束
- START / END / intermediate Path point のマウス再配置
- Multi-point Path
- L / U Stair
- Landing

---

## 4. Add-on identification

07-B production 実装では以下を使用する。

```text
version = (0, 7, 1)
description = "Build 07-B: Standard Residential Straight Stair"
```

---

## 5. 07-B production scope

- existing 2-point Straight Stair Path
- existing FORWARD / REVERSE ascent contract
- existing Tread / Riser geometry
- explicit `assembly_mode`
- Stair schema identification
- explicit BASIC → STANDARD_RESIDENTIAL conversion
- `STEPPED_CLOSED` Underbody
- Underbody thickness
- left Side Board ON / OFF
- right Side Board ON / OFF
- Side Board thickness
- Side Board stepped band width
- part-specific Material roles
- common/base Material fallback
- Residential regeneration / Repair
- Undo / Redo
- Save / reopen
- Duplicate ID lifecycle
- Editable Mesh finalization
- dedicated Stair Delete
- oblique Straight Path
- Material persistence
- failure rollback
- 07-A BASIC compatibility

---

## 6. Explicit non-scope

07-B では以下を production 実装しない。

- `SLOPED_CLOSED`
- tread front overhang
- separate nosing
- tread-front Bevel / Round
- anti-slip groove
- user-facing Riser OFF
- `Underside = NONE`
- open Stair
- sawtooth / side / center support
- Multi-point Path
- Shift angle constraint
- mouse Path-point relocation
- L-shaped Stair
- U-shaped Stair
- Landing
- Winder / 廻り段
- automatic Floor / Wall / Room connection
- handrail / newel / baluster
- production UV / guaranteed wood-grain direction
- universal arbitrary mesh framework

---

## 7. Coordinate and terminology contract

Resolved local axes:

```text
+X = uphill / forward
+Y = left while facing uphill
+Z = up
```

Definitions:

```text
N = riser_count
h = actual_riser
g = going
t = tread_thickness
r = riser_thickness
L = run_length = (N - 1) * g
B = base_z
H = B + N*h = upper_arrival_z
w = stair_width
u = underside_thickness
s = side_board_thickness
b = side_board_band_width
```

`START / END` は Path draw order の意味だけを持つ。高さ側の終端は必ず `lower termination` / `upper termination` と表現し、`ascent_direction` から解決する。

---

## 8. Existing 07-A geometric contract

Tread `j = 1 ... N-1`:

```text
X = [(j-1)g, jg]
Y = [-w/2, +w/2]
top Z    = B + jh
bottom Z = B + jh - t
```

Riser `k = 1 ... N-1`:

```text
X = [(k-1)g, (k-1)g + r]
bottom Z = B + (k-1)h
top Z    = B + kh - t
```

Final Riser `k=N`:

```text
X = [L, L+r]
bottom Z = B + (N-1)h
top Z    = H
```

Upper arrival reference remains:

```text
X = L
Z = H
```

`L+r` は Final Riser の外形であり、新しい arrival line ではない。

---

## 9. Managed Object contract

07-B でも:

```text
1 Managed Stair = 1 Blender Mesh Object
```

Normal managed Transform:

```text
Location = (0,0,0)
Rotation = (0,0,0)
Scale    = (1,1,1)
```

Tread / Riser / Underbody / Side Board は独立 Generator とするが、最終的には1つの Managed Mesh Object へ組み立てる。

---

## 10. Assembly mode

07-B は明示的な assembly mode を導入する。

```text
BASIC_TREAD_RISER
STANDARD_RESIDENTIAL
```

### BASIC_TREAD_RISER
07-A-compatible:

```text
Tread + Riser
```

### STANDARD_RESIDENTIAL

```text
Tread
+ Riser
+ STEPPED_CLOSED Underbody
+ optional Left Side Board
+ optional Right Side Board
+ part-specific Materials
```

---

## 11. Schema version and assembly mode are separate

Conceptual hidden property:

```text
stair_schema_version
```

- schema version = stored-data schema
- assembly mode = user-selected Stair assembly

They are not synonyms. Future schema revisions may legally remain BASIC.

---

## 12. Legacy 07-A behavior

Old files with no 07-B fields must default semantically to:

```text
assembly_mode = BASIC_TREAD_RISER
stair_schema_version = 1
```

Loading an old file must not automatically:

- add Underbody
- add Side Boards
- rewrite UUID / Path
- regenerate geometry
- change Materials
- convert to Residential

No load-time automatic migration / Repair.

---

## 13. New 07-B Stair creation

New 07-B Stair is explicitly committed as:

```text
assembly_mode = STANDARD_RESIDENTIAL
stair_schema_version = 2
underside_mode = STEPPED_CLOSED
left_side_board_enabled = True
right_side_board_enabled = True
```

Fixed defaults:

```text
underside_thickness_mm = 9.5
side_board_thickness_mm = 18.0
side_board_band_width_mm = 150.0
```

These values are the 07-B production defaults.

---

## 14. BASIC mode validation

When `assembly_mode = BASIC_TREAD_RISER`, only BASIC-required canonical fields participate in validity.

Unused Residential values must not make a BASIC Stair `INVALID_CANONICAL`.

---

## 15. Explicit BASIC → Residential conversion

For selected NORMAL BASIC Stair add:

```text
住宅階段仕様を適用
```

Ordinary edit/regenerate/Repair never performs conversion implicitly.

Operation matrix:

| Operation | Result |
|---|---|
| Load / Save / reopen | BASIC unchanged |
| Dimension edit | BASIC regenerated |
| Numeric Path edit | BASIC |
| Reverse | BASIC |
| Explicit regenerate | BASIC |
| GEOMETRY_MISSING Repair | BASIC restored |
| Transform / ID Repair | BASIC preserved |
| Finalize / Delete | existing lifecycle |
| 住宅階段仕様を適用 | STANDARD_RESIDENTIAL |
| Undo after apply | exact BASIC state restored |

---

## 16. Residential apply transaction

Prepare before Scene mutation:

- Residential canonical candidate
- Underbody profile
- Side Board profile(s)
- Material baseline / overrides
- complete geometry
- material-role mapping

Rollback target must include:

- old Mesh
- old canonical values
- assembly mode
- schema version
- Material references / slots
- Stair ID
- Object Transform

No partial conversion is allowed.

---

## 17. STEPPED_CLOSED design intent

Underbody is an independent geometry responsibility because visible shape, thickness, termination and Material must be controlled independently.

It is derived analytically from canonical dimensions / resolved Stair layout. It is **not** reconstructed from existing Mesh Boolean analysis.

It directly follows the accepted Tread/Riser lower exterior with no arbitrary air gap and leaves the space below the Stair open.

---

## 18. Underbody analytical inner profile `U_inner`

Start:

```text
(r, B)
```

For `k = 1 ... N-1` the analytical sequence includes:

```text
((k-1)g + r, B + (k-1)h)
→ ((k-1)g + r, B + kh - t)
→ (kg,             B + kh - t)
→ (kg,             B + kh)
→ (kg + r,         B + kh)
```

Consecutive duplicate points are removed.

Final inner endpoint:

```text
(L+r, B+(N-1)h)
```

`x=kg` is the uphill-side edge / step transition of Tread `k`, not the tread front/nosing edge.

---

## 19. Underbody outer profile `U_outer`

Given `u = underside_thickness`:

- inner horizontal segment → translate by `-Z*u`
- inner vertical segment → translate by `+X*u`
- adjacent translated lines → connect at their geometric intersection

07-B has one fixed join rule: **translated-line intersection**.

---

## 20. Underbody lower termination

Clip at:

```text
Z = B
```

Endpoints:

```text
U_inner_lower = (r, B)
U_outer_lower = (r+u, B)
```

Join these along base plane. Underbody must not extend below `base_z`.

After clipping, remove duplicate consecutive points and zero-length edges.

---

## 21. Underbody upper termination

Underbody does **not** wrap around Final Riser rear face.

```text
U_inner_upper = (L+r, B+(N-1)h)
U_outer_upper = (L+r, B+(N-1)h-u)
```

Close along:

```text
X = L+r
```

Therefore:

```text
upper arrival reference = L
Final Riser max X       = L+r
Underbody max X         = L+r
```

No `L+r+u` uphill extension and no extra tread/riser.

---

## 22. Underbody width / lateral closure

Extrude closed XZ Underbody profile over:

```text
Y = [-w/2, +w/2]
```

Correct closure rule:

> Tread side faces + Riser side faces + Underbody lateral faces together form the closed visible Stair body when Side Boards are OFF.

Underbody alone is not described as one surface that closes the whole Stair side.

---

## 23. Underbody thickness supported range

Fixed default:

```text
u = 9.5 mm
```

For the selected lower/upper termination construction, 07-B supports:

```text
0 < u < min(h - t, r)
```

This is a 07-B supported-range rule, not a universal theorem for all stepped underbody constructions.

Final profile validity still requires:

- finite coordinates
- no duplicate consecutive points after cleanup
- no zero-length edges
- positive area
- no self-intersection
- valid winding / triangulation
- closed extrusion

---

## 24. Side Board design intent

Side Board is a decorative stepped fascia, not the closure mechanism of the Stair body.

`Left OFF / Right OFF` must still produce a closed-looking Stair body.

The Side Board is intentionally allowed to project below the main Tread/Riser/Underbody body.

---

## 25. Side Board reference profile `S_ref`

Derived analytically from ideal walking-step profile:

```text
(0,B)
→ (0,B+h)
→ (g,B+h)
→ (g,B+2h)
→ (2g,B+2h)
...
→ (L,H)
```

It does not include future 07-C nosing / front overhang.

---

## 26. Side Board band generation

Define `b = side_board_band_width`.

- horizontal `S_ref` segment → translate by `-Z*b`
- vertical `S_ref` segment → translate by `+X*b`
- adjacent translated lines → connect at intersection

This creates a continuous stepped band rather than a global vertical offset.

---

## 27. Side Board lower termination

Clip at:

```text
Z = B
```

No geometry below `base_z`.

Cleanup duplicate / zero-length edges and validate polygon.

---

## 28. Side Board upper termination

Walking-side inner endpoint:

```text
(L,H)
```

The Side Board must not extend farther uphill than the Final Riser outer face:

```text
X_upper_limit = L+r
```

Generation rule:

1. Build the complete closed stepped Side Board band polygon first.
2. Clip the **entire closed polygon** to the half-plane:

```text
X <= L+r
```

3. Include the new clipping boundary in the polygon.
4. Remove duplicate consecutive points and zero-length edges.
5. Revalidate polygon simplicity, winding and positive area.
6. Only then extrude the clipped polygon along local Y.

For the current 07-B band construction, the resulting maximum uphill extent is:

```text
X_side_upper = L + min(b,r)
```

and therefore:

```text
X_side_upper <= L+r
```

Do not implement this by moving only the endpoint of the outer profile.

Underbody and Side Board intentionally use different upper-termination logic.

For the standard default case:

```text
h = 175 mm
b = 150 mm
r = 12 mm
```

the upper clipping boundary produced by `X <= L+r` can form a visible vertical end face whose height is:

```text
h + b = 325 mm
```

for the relevant band geometry.

This is an expected consequence of the current band-and-clip rule, not an arithmetic error. Its visual appearance must be explicitly checked during Stage 3 / final runtime acceptance.

---
## 29. Side Board supported range

Fixed default:

```text
b = 150 mm
```

07-B guarantees simple band construction within:

```text
0 < b < min(h,g)
```

This is a 07-B supported-range decision, not a claim that larger bands are mathematically impossible.

---

## 30. Side Board visible projection below body

Example:

```text
t = 30 mm
u = 9.5 mm
b = 150 mm
```

produces Side Board regions substantially deeper than the core body. This is intentional.

Correct contact statement:

> Side Board inner face contacts the Stair body where their extents overlap. Where the Side Board projects below the Stair body, its inner face is exposed and is treated as a normal visible finished face.

Do not thicken the Stair body to fill the whole Side Board band.

---

## 31. Side Board thickness and Y placement

Define `s = side_board_thickness`.

Fixed default:

```text
s = 18 mm
```

`stair_width_mm` retains its accepted 07-A meaning: Tread/Riser body width.

LEFT:

```text
inner Y = +w/2
outer Y = +w/2 + s
```

RIGHT:

```text
inner Y = -w/2
outer Y = -w/2 - s
```

For `w=900, s=18`, both ON gives overall width `936 mm`.

One-side-only configurations are intentionally asymmetric around the Path centerline. Path itself never moves.

---

## 32. LEFT / RIGHT semantics under Reverse

LEFT / RIGHT means left/right **while facing uphill**.

Therefore, with:

```text
left_side_board_enabled = True
right_side_board_enabled = False
```

`FORWARD → REVERSE` keeps booleans unchanged but moves the generated board to the opposite world-space side.

This is required behavior and must be tested.

---

## 33. Four Side Board cases

Required:

```text
A Left ON  / Right ON
B Left ON  / Right OFF
C Left OFF / Right ON
D Left OFF / Right OFF
```

Verify:

- no unintended hole
- correct outer width
- correct side
- correct Reverse behavior
- lower / upper termination
- no unintended gap
- no visible z-fighting

---

## 34. Proposed 07-B canonical properties

Existing 07-A fields remain unchanged.

Add conceptually:

```text
assembly_mode
stair_schema_version
underside_mode
underside_thickness_mm
left_side_board_enabled
right_side_board_enabled
side_board_thickness_mm
side_board_band_width_mm
base_material
tread_material
riser_material
underside_material
side_board_material
```

07-B user-visible underside production value is only:

```text
STEPPED_CLOSED
```

Unsupported `SLOPED_CLOSED` / `NONE` choices are not exposed yet.

---

## 35. Material role contract

Roles:

```text
TREAD
RISER
UNDERSIDE
SIDE_BOARD
```

LEFT / RIGHT Side Boards share one role in 07-B.

Canonical references:

```text
base_material
optional overrides:
  tread_material
  riser_material
  underside_material
  side_board_material
```

Resolution per role:

```text
role override != None → override
else base_material != None → base_material
else → UNASSIGNED
```

`UNASSIGNED` is a real derived assignment state. It must not silently fall through to another role's Material.

Canonical meaning is not encoded as Material slot numbers.

### Mixed assigned / unassigned roles

07-B must support cases such as:

```text
Base       = None
Tread      = Wood
Riser      = None
Underside  = None
Side Board = None
```

Expected result:

```text
Tread      → Wood
Riser      → UNASSIGNED
Underside  → UNASSIGNED
Side Board → UNASSIGNED
```

When at least one role has a Material and another role is `UNASSIGNED`, the derived Mesh Material-slot mapping must preserve that distinction.

Preferred implementation contract:

- create/use an **empty Material slot** representing `UNASSIGNED` where Blender requires a slot index for those faces;
- the empty slot contains no Material datablock;
- do not generate a substitute/fallback Material datablock;
- do not map `UNASSIGNED` faces onto another role's Material slot.

If implementation discovery shows that the Blender 5.2 Mesh API cannot reliably represent a mixed empty-slot case, Stage 3 must stop and the specification must be amended rather than silently changing Material semantics.

---

## 36. Legacy Material migration during explicit apply

BASIC Stair:

- zero Materials → proposed `base_material=None`
- exactly one Material → apply dialog may propose that datablock as base
- multiple Materials → do not infer semantics automatically

For multiple Materials, explicit apply must require a base choice or explicit None. Slot 0 may be preselected for convenience but is not silently committed as semantic truth.

After Residential conversion, canonical Material datablock references are authoritative.

---

## 37. Deterministic Material slot assembly

For Residential, resolve effective role assignments in stable role order:

```text
TREAD
RISER
UNDERSIDE
SIDE_BOARD
```

Rules:

1. Resolve each role to either a Material datablock or `UNASSIGNED`.
2. Deduplicate identical Material datablocks by identity.
3. Preserve `UNASSIGNED` as a separate derived state.
4. If mixed assigned/unassigned roles exist, provide a derived empty slot for `UNASSIGNED` faces rather than reusing a real Material slot.
5. Do not auto-create a substitute Material datablock.
6. The Mesh slot order is derived and may change; canonical meaning remains role → Material/UNASSIGNED.

For BASIC mode, preserve accepted 07-A Material behavior.

---
## 38. Generic geometry foundation — limited scope

Current 07-A Box Fragment validator is too restrictive for stepped concave profiles.

07-B adds only this limited primitive:

> simple, hole-free, non-self-intersecting 2D polygon profile extruded a constant distance along one axis into a closed solid.

Use for:

- Stepped Underbody
- Left Side Board
- Right Side Board

Tread/Riser continue using Box generator.

Do not build a universal arbitrary mesh framework.

---

## 39. Concave profile support

Stepped profiles are concave. End caps require deterministic concave polygon triangulation.

Required:

- valid winding
- no triangle outside polygon
- no zero-area triangles
- closed side-wall generation
- outward-consistent orientation

Naive fan triangulation is not sufficient.

---

## 40. Part-level validation

Each generated Part independently validates:

- finite coordinates
- valid indices
- no duplicate index inside one face
- non-zero area
- valid source-profile winding
- no self-intersection
- valid cap triangulation
- closed-solid edge incidence
- outward orientation

A valid Part must not depend on another Part being present.

---

## 41. Assembly-level validation

After all Parts are prepared:

- intended interfaces align
- no unintended exterior gaps
- no unintended exterior visible overlap / coplanar z-fighting
- lower / upper terminations complete
- Side Board OFF cases visually closed
- LEFT / RIGHT follows ascent axes
- finite geometry
- no zero-area faces
- no unintended non-manifold edge

Internal contact faces between separately closed fragments are allowed. Boolean union is not required.

---

## 42. Generator independence

Required architecture:

```text
resolve_stair_layout()
        ↓
build_tread_fragments()
build_riser_fragments()
build_stepped_underbody_fragment()
build_side_board_fragment(LEFT)
build_side_board_fragment(RIGHT)
        ↓
assemble residential Mesh
```

- Underbody works without Side Boards.
- LEFT works without RIGHT.
- RIGHT works without LEFT.
- no Generator reverse-infers from existing Mesh.

---

## 43. Oblique Path contract

No 07-B geometry may assume world-X alignment.

All use resolved:

```text
forward axis
left axis
up axis
```
Oblique Straight Stair must orient Treads, Risers, Underbody and Side Boards consistently while Object Transform remains identity.

---

## 44. Residential canonical validation

For `STANDARD_RESIDENTIAL`, validate at least:

- accepted 07-A Stair layout
- `underside_mode == STEPPED_CLOSED`
- finite positive Underbody thickness and supported range
- finite positive Side Board thickness
- finite positive Side Board band width
- generated Underbody profile validity
- generated enabled Side Board profile validity
- Material references valid or None

Side Board validation is feature-aware:

- `side_board_thickness_mm` must be finite and `> 0` even when both Side Boards are OFF.
- `side_board_band_width_mm` must be finite and `> 0` even when both Side Boards are OFF.
- the dimensional relation:

```text
b < min(h,g)
```

is required only when at least one Side Board is enabled.
- Side Board profile generation / clipping validation is required only for enabled Side Boards.

Therefore a Residential Stair with both Side Boards OFF is not blocked by an otherwise-unused `b < min(h,g)` relation after later Stair dimension edits, while malformed/non-finite/non-positive stored Side Board values are still rejected.

Validation is feature-aware. Disabled features must not be blocked by unrelated generation constraints.

---
## 45. Managed-state diagnosis

Keep existing state classes unless truly necessary:

```text
NORMAL
ID_MISSING
ID_CONFLICT
TRANSFORM_CHANGED
INVALID_CANONICAL
GEOMETRY_MISSING
OBJECT_TYPE_CHANGED
```

Invalid Residential canonical data maps to `INVALID_CANONICAL`.

BASIC ignores unused Residential constraints.

---

## 46. Residential regeneration transaction

```text
canonical snapshot
↓
resolve layout
↓
prepare Tread
prepare Riser
prepare Underbody
prepare enabled Side Boards
↓
resolve Material roles
↓
validate parts
validate assembly
↓
build replacement Mesh
assign Materials / polygon indices
↓
swap Mesh
commit canonical
```

No Scene mutation before candidate preparation succeeds.

Rollback restores at minimum:

- old Mesh
- dimensions / Path / ascent
- assembly mode / schema
- Underbody values
- Side Board values
- Material references
- Stair ID
- Object Transform

---

## 47. Existing operations

Existing operations continue and dispatch by assembly mode:

```text
階段寸法を変更
Path座標を変更
上り方向を反転
階段を再生成
管理状態へ復元
編集可能Meshとして確定
階段を削除
```

BASIC remains BASIC. Residential remains Residential.

---

## 48. Residential settings editor

Add dedicated action:

```text
住宅階段仕様を変更
```

Residential fields:

- underside thickness
- Left Side Board ON/OFF
- Right Side Board ON/OFF
- Side Board thickness
- Side Board band width

Execution policy:

```text
target assembly_mode = STANDARD_RESIDENTIAL
managed state        = NORMAL
```

This action is available only for a NORMAL `STANDARD_RESIDENTIAL` Stair.

The UI enabled state and the operator's execute-time validation must use the same central operation policy. A stale UI state must not allow direct operator invocation to bypass the NORMAL-only rule.

Do not overload the accepted 07-A dimension dialog with all 07-B options.

---

## 49. Material editor

Add dedicated action conceptually:

```text
階段部材Materialを変更
```

Fields:

- Base Material
- Tread override
- Riser override
- Underside override
- Side Board override

Execution policy:

```text
target assembly_mode = STANDARD_RESIDENTIAL
managed state        = NORMAL
```

This action is available only for a NORMAL `STANDARD_RESIDENTIAL` Stair.

The UI and operator execute-time gate must share the same rule.

BASIC Stair Material behavior remains the accepted 07-A behavior; 07-B does not add a separate BASIC part-material editor.

---
## 50. Reverse behavior

Residential `FORWARD ↔ REVERSE` must:

- keep Path order
- keep Stair ID
- keep assembly mode / schema
- keep Side Board booleans
- keep Material references
- regenerate all parts using reversed resolved axes
- move LEFT/RIGHT boards to opposite world-space sides as required
- preserve run length / lower-upper heights

---

## 51. Repair

For Residential `GEOMETRY_MISSING` with valid canonical data, Repair regenerates:

- Treads
- Risers
- Underbody
- enabled Side Boards
- Material slots / face assignments

`INVALID_CANONICAL` remains non-repairable; JHM does not guess dimensions.

`OBJECT_TYPE_CHANGED` Repair remains unsupported unless a later spec changes it. Delete remains allowed.

---

## 52. Editable Mesh / Delete / Save

Accepted 07-A lifecycle remains.

Finalize keeps the current Residential Mesh and Materials and exits management without regeneration.

Dedicated Delete works for BASIC / Residential and allowed abnormal managed states.

Save/reopen preserves:

- assembly mode
- schema
- Path / ascent / dimensions
- Underbody settings
- Side Board settings
- Material references
- Stair ID
- visible state
- identity Transform

No load-time automatic regeneration/conversion.

---

## 53. Stage plan

### Stage 1 — Residential Foundation / Compatibility

Implement and internally test:

- assembly mode / schema
- 07-A BASIC compatibility
- 07-B Residential property/default data model
- BASIC → Residential transition candidate data
- transition snapshot / rollback model
- Material canonical schema
- limited extruded-profile foundation
- concave triangulation
- mode-aware validation
- transaction snapshot expansion

**Stage 1 public-scope rule:**

- do not yet enable user-facing creation of a complete `STANDARD_RESIDENTIAL` Stair;
- do not yet enable the user-facing `住宅階段仕様を適用` action;
- ordinary user-facing Stair creation remains BASIC-compatible during the Stage 1 candidate;
- Residential defaults / transition are exercised through pure/internal tests only.

Stage 1 acceptance proves the data model and geometry foundation, not the completed Residential feature.

### Stage 2 — STEPPED_CLOSED Underbody

Implement and test:

- analytical `U_inner`
- offset `U_outer`
- lower / upper termination
- lateral closure
- thickness
- oblique Path
- FORWARD / REVERSE
- finite / closed / valid geometry
- body appearance with **both Side Boards OFF**
- Stage-level Save / Undo spot checks

**Stage 2 public-scope rule:**

- this is an intermediate development configuration, not the finished 07-B user feature;
- runtime testing may construct `STANDARD_RESIDENTIAL` test state through controlled internal/test setup;
- user-facing complete Residential creation / explicit apply remains disabled until Stage 3.

### Stage 3 — Side Boards + Part Materials

Implement and test:

- four Left/Right cases
- band profile
- full-polygon upper clipping at `X <= L+r`
- lower / upper Side Board termination
- thickness / band width
- intentional below-body projection
- Reverse LEFT/RIGHT world-side change
- base + role Material overrides
- mixed assigned/unassigned Material roles
- slot / face mapping
- Save / Undo spot checks

**Stage 3 activation gate:**

Only after Underbody, Side Board generators and Material assignment are all present and runtime-tested may Stage 3 enable:

- new user-facing 07-B `STANDARD_RESIDENTIAL` Stair creation;
- user-facing `住宅階段仕様を適用`;
- `住宅階段仕様を変更`;
- `階段部材Materialを変更`.

### Stage 4 — Lifecycle / Full Regression

- Dimension / Path edit / Reverse / regenerate / Repair
- failure rollback
- duplicate ID
- Save/full exit/reopen
- Undo/Redo
- Editable Mesh / Delete
- BASIC compatibility regression
- 07-A regression
- Wall / Finish regression
- final visual acceptance
- Build 07-B Acceptance Record

Stage 4 is the complete operational and compatibility gate, but Save/Undo coverage for new canonical data is not deferred exclusively to Stage 4; Stage 2/3 retain their own spot checks.

---
## 54. Automated test requirements

### Stage 1

- legacy defaults produce BASIC
- Residential property/default candidate data exists without public activation
- schema != assembly mode
- BASIC ignores unused Residential constraints
- BASIC → Residential candidate transition / rollback state
- public Residential creation/apply remains disabled in Stage 1
- Material base/override resolution
- mixed role resolution distinguishes Material vs `UNASSIGNED`
- identical Material pointer deduplication
- simple polygon extrusion
- concave triangulation
- invalid/self-intersecting profile rejection

### Stage 2

- exact standard `U_inner`
- exact lower / upper endpoints
- exact standard `U_outer`
- lower `Z=B` cap
- upper `X=L+r` cap
- no `L+r+u` extension
- supported thickness range boundaries
- cleanup / self-intersection / positive area
- closed extrusion
- oblique Path
- Reverse
- Underbody generator independent from Side Board
- both Side Boards OFF Stage-2 body case
- public complete Residential creation/apply still disabled

### Stage 3

- exact `S_ref`
- Side Board outer band
- lower clipping
- closed-band polygon clipped as a whole to `X <= L+r`
- resulting `X_side_upper = L + min(b,r)`
- no endpoint-only trim shortcut
- four Left/Right cases
- Reverse world-side swap
- thickness external to Stair width
- Path centerline unchanged
- exposed inner Side Board face valid
- NORMAL + STANDARD_RESIDENTIAL gates for settings/material operators
- Material role partial override
- `Base=None, Tread=Material, others=None`
- mixed `UNASSIGNED` role preservation
- empty-slot/no-substitute-Material rule
- all-None Material case
- Material dedupe
- Stage-3 public activation of Residential creation/apply

### Stage 4

- BASIC edits remain BASIC
- explicit Residential apply only
- apply Undo model
- Residential regenerate / invalid rollback
- Material rollback
- state diagnosis / Repair policy
- finalization / deletion
- serialization-facing fields
- Stage 1–4 regression
- full prior discovery
- compileall
- `git diff --check`

Do not predict test counts in this specification.

---
## 55. Blender runtime acceptance — compatibility

At minimum:

1. Open accepted 07-A BASIC Stair with 07-B add-on.
2. No automatic geometry change.
3. Save/reopen remains BASIC.
4. Dimension edit remains BASIC.
5. Numeric Path edit remains BASIC.
6. Reverse remains BASIC.
7. Regenerate remains BASIC.
8. GEOMETRY_MISSING Repair restores BASIC only.
9. Explicit `住宅階段仕様を適用` adds Residential geometry.
10. Undo apply restores exact BASIC state.

---

## 56. Blender runtime acceptance — Underbody

Verify visually/numerically:

- lower termination
- upper termination
- no extent beyond `L+r`
- stepped horizontal/vertical underside appearance
- no floor-solid mass
- no unintended visible air gap
- no exterior z-fighting
- body closure with both Side Boards OFF
- oblique Path
- FORWARD / REVERSE
- nonzero `base_z`
- thickness edit
- invalid thickness atomic rejection

Required views: side, underside, lower oblique, upper oblique, top as needed.

---

## 57. Blender runtime acceptance — Side Boards

Verify all four ON/OFF cases and:

- correct world side
- correct external width
- no body hole when OFF
- intentional below-body projection
- exposed inner Side Board surface
- lower / upper termination
- full polygon clipping at `X <= L+r`
- no extension beyond Final Riser outer limit
- thickness change
- band-width change
- invalid band atomic rejection
- Reverse swaps world-space side for LEFT/RIGHT semantics

For the standard default geometry where:

```text
h = 175 mm
b = 150 mm
r = 12 mm
```

explicitly inspect the upper clipped end face produced by `b > r`.

The clipping rule can produce an upper-end vertical boundary with height:

```text
h + b = 325 mm
```

for the relevant band geometry.

Acceptance requires that this reads as an intentional residential Side Board termination rather than an accidental oversized plate. If mathematically valid but visually unacceptable, Stage 3 / final visual acceptance fails and the Side Board upper-termination specification must be revised before Build 07-B acceptance.

---
## 58. Blender runtime acceptance — Materials

Test at least these three cases.

### Case A — Base + partial override

```text
Base       = wood
Riser      = white
Tread      = None
Underside  = None
Side Board = None
```

Expected:

```text
Tread      → wood
Riser      → white
Underside  → wood
Side Board → wood
```

### Case B — Mixed assigned / unassigned

```text
Base       = None
Tread      = wood
Riser      = None
Underside  = None
Side Board = None
```

Expected:

```text
Tread      → wood
Riser      → UNASSIGNED
Underside  → UNASSIGNED
Side Board → UNASSIGNED
```

Verify that unassigned faces do **not** inherit the Tread Material, and that no substitute Material datablock is auto-created.

### Case C — all unassigned

```text
Base       = None
Tread      = None
Riser      = None
Underside  = None
Side Board = None
```

Expected:

```text
all roles → UNASSIGNED
```

with no unexpected Material datablock/slot semantics.

For Cases A/B as applicable, verify through:

- regenerate
- dimension edit
- Reverse
- Save/reopen
- Repair
- Editable Mesh finalization

---
## 59. Blender runtime acceptance — lifecycle

At minimum:

- creation Undo/Redo
- Residential apply Undo/Redo
- Residential settings Undo/Redo
- Material edit Undo/Redo
- Reverse Undo/Redo
- Repair Undo/Redo
- Delete Undo/Redo
- Save/full Blender exit/reopen
- Editable Mesh finalization
- finalized free Mesh editing
- duplicate ID Repair
- abnormal-state operation gates
- forced prepare failure rollback
- forced commit failure rollback

---

## 60. Visual acceptance criteria

07-B is not accepted from numeric tests alone.

The Residential Straight Stair must visually satisfy:

- continuous stepped finished underside
- no unintended holes with Side Boards OFF
- Side Boards read as intentional stepped decorative bands
- below-body Side Board projection looks deliberate
- clean lower / upper terminations
- no unexplained protrusion beyond Final Riser
- no z-fighting / missing faces
- Material parts visually distinguishable
- FORWARD / REVERSE coherent

Mathematically valid but visually wrong residential geometry fails runtime acceptance.

---

## 61. Regression requirements

Do not break 07-A:

- two-point creation
- Path draw order
- ascent reversal
- 2800/16 numeric contract
- oblique Straight Stair
- invalid edit rollback
- ID / Transform state diagnosis
- Repair
- BASIC Material preservation
- Save / reopen
- Undo / Redo
- Editable Mesh
- Delete

Prior Wall / Finish tests must continue to pass. Do not modify Wall / Finish production behavior merely for Stair 07-B.

---

## 62. Completion gate

Build 07-B may be marked ACCEPTED only when:

- Stage 1 accepted
- Stage 2 accepted
- Stage 3 accepted
- Stage 4 accepted
- automated regression passes
- Blender 5.2 LTS runtime acceptance passes
- BASIC 07-A compatibility passes
- final visual acceptance passes
- Acceptance Record is updated in documentation-only commit

Runtime-tested production revision remains distinct from later documentation-only commits.

---

## 63. Future scope guards

07-C owns:

- `SLOPED_CLOSED`
- tread front overhang
- Bevel / Round

07-D owns:

- Multi-point Path
- Shift angle constraint
- mouse relocation of START / END / intermediate points
- L / U
- Landing

07-E owns Winder.

07-B must not require changing accepted Path, riser-count or upper-arrival contracts to add these later.

---

## 64. Final design decisions

The following 07-B defaults are fixed:

```text
underside_thickness_mm default = 9.5
side_board_thickness_mm default = 18.0
side_board_band_width_mm default = 150.0
```

The following reviewed design decisions are fixed for 07-B:

1. Side Board may intentionally project below the main Tread/Riser/Underbody body.
2. Underbody upper termination is `X=L+r`; it does not wrap the Final Riser rear face.
3. Side Board is generated as a closed stepped band and the complete polygon is clipped to `X <= L+r`; for the current construction the resulting maximum uphill extent is `L+min(b,r)`.
4. The new geometry foundation is limited to simple, hole-free, non-self-intersecting 2D polygon extrusion with concave-cap triangulation.
5. Existing 07-A BASIC Stair becomes Residential only through an explicit user operation; automatic migration is prohibited.
6. Mixed assigned/unassigned Material roles preserve `UNASSIGNED` without borrowing another role's Material and without auto-generating a substitute Material datablock.
7. Full user-facing Residential creation/apply/settings/material operations are activated only in Stage 3 after all required generators and Material assignment exist.

These decisions may be revisited only through an explicit later specification/correction if Blender runtime evidence shows the accepted geometry or Material semantics cannot be implemented safely.

---

## 65. Conclusion

07-B extends the accepted 07-A core without redefining its Path, rise/run, arrival, identity or lifecycle contracts.

```text
Canonical Stair
    ↓
Resolved Straight Layout
    ↓
Part Generators
    ├ Tread
    ├ Riser
    ├ STEPPED_CLOSED Underbody
    ├ Left Side Board
    └ Right Side Board
    ↓
Material Role Resolution
    ↓
Validated Candidate
    ↓
One Managed Stair Mesh
```

Legacy 07-A Stairs remain BASIC until the user explicitly applies Residential Stair specification.

07-B Residential geometry remains managed, transactional, Undo-capable, serializable, repairable from valid canonical data, and finalizable into an ordinary editable Blender Mesh.