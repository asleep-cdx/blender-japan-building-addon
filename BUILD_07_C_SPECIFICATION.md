# BUILD 07-C SPECIFICATION
## 日本住宅モデラー — Sloped Closed Underside + Straight Stair Finish Variants

> **Status: FINAL / IMPLEMENTATION AUTHORITY**  
> Date: 2026-09-24  
> Build 07-B overall Acceptance を baseline とし、07-B の accepted canonical / lifecycle / geometry contract を壊さずに Straight Stair の finish variants を追加する。

---

## 1. Purpose

Build 07-C は、Build 07-B で Acceptance 済みとなった Standard Residential Straight Stair を維持したまま、直線住宅階段としての見た目・仕上げ選択を拡張する Build である。

中心目的は次の5点とする。

1. `SLOPED_CLOSED` の連続勾配下面を追加する。
2. Side Board に `SLOPED` variant を追加する。
3. Tread front overhang / nosing（段鼻）を追加する。
4. Tread front edge の basic `BEVEL` / `ROUND` variant を追加する。
5. Build 07-B で内部互換fieldとして保持していた closed-body depth を、ユーザー向け「階段本体厚み」として操作可能にする。

07-C は **Straight Stair の finish/detail 拡張**であり、Path topology 自体は 07-B と同じ 2-point Straight Path のままとする。

---

## 2. Accepted baseline

07-C は以下を baseline とする。

- Build 05-B — Wall System — ACCEPTED
- Build 06-A / 06-B / 06-C — Finish system — ACCEPTED
- Build 07-A — Stair Core + 2-point Straight Stair — ACCEPTED
- Build 07-B — Standard Residential Straight Stair — overall ACCEPTED
- `BUILD_07_B_ACCEPTANCE_RECORD.md`
- `BUILD_07_B_STAGE3_ACCEPTANCE.md`
- `BUILD_07_B_CORRECTION_ADDENDUM.md`
- `BUILD_07_C_PLANNING_NOTE.md`
- `DEVELOPMENT_WORKFLOW.md`
- `ROADMAP.md`

07-C specification drafting baseline:

```text
commit ececf52e759896344fc48c1fbe07a8e4d033361f
tree   2374ee4f504fb39942890030da6b758ccfe898de
```

07-B accepted production behavior is regression authority. Existing 07-B saved Stair must not silently change merely because 07-C is installed.

---

## 3. Roadmap position

```text
07-A  Stair Core + 2-point Straight Stair          ACCEPTED
  ↓
07-B  Standard Residential Straight Stair          ACCEPTED
  ↓
07-C  Sloped Closed Underside + Straight Finish Variants
  ↓
07-D  Multi-point Path + L/U + Landing
  ↓
07-E  Winder / 廻り段
  ↓
07-F  Open / Support Variants
```

07-C 完了時には Roadmap 方針どおり、手作業で用意した Wall / Floor 相当の簡易シーンへ Stair を配置し、直線住宅階段としての小規模実用確認を行う。

---

## 4. Add-on identification

07-C production implementation:

```text
version = (0, 7, 2)
description = "Build 07-C: Sloped Closed Underside + Straight Stair Finish Variants"
```

---

## 5. Coordinate and terminology contract

07-B を継承する。

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
H = B + N*h
w = stair_width
u = underside_thickness
d = closed_body_depth / stair_body_thickness
s = side_board_thickness
v = side_board_reveal
n = tread_front_overhang
q = tread_front_edge_size
```

`START / END` は Path draw order。高さ側は `lower / upper` とし、FORWARD / REVERSE から解決する。

---

## 6. Production scope

- existing 2-point Straight Stair Path
- FORWARD / REVERSE
- BASIC / STANDARD_RESIDENTIAL separation
- schema compatibility
- `STEPPED_CLOSED` preservation
- new `SLOPED_CLOSED`
- user-facing stair-body thickness / closed-body depth
- existing external Side Boards
- `STEPPED` Side Board preservation
- new `SLOPED` Side Board variant
- tread front overhang / nosing
- tread front edge `SQUARE / BEVEL / ROUND`
- existing part Materials
- Regenerate / Repair / rollback
- Save / full exit / reopen
- Undo / Redo
- duplicate-ID lifecycle
- Editable Mesh finalization
- active-only Delete
- oblique Straight Path
- Wall / Finish isolation regression
- practical straight-stair placement smoke test

---

## 7. Explicit non-scope

07-C では実装しない。

- Multi-point Path
- Shift angle constraint
- mouse Path-point relocation
- L / U Stair
- Landing
- Winder / 廻り段
- Riser OFF
- `Underside = NONE`
- Open Stair
- sawtooth / stringer support variants
- center support
- handrail / newel / baluster
- anti-slip groove
- separate nosing Material role
- arbitrary custom nosing / Side Board Profile
- production UV / guaranteed wood-grain direction
- automatic Floor / Wall / Room connection

---

## 8. CLOSED invariant

`STANDARD_RESIDENTIAL + STEPPED_CLOSED` と `STANDARD_RESIDENTIAL + SLOPED_CLOSED` は、どちらも CLOSED Stair である。

必須：

- Tread / Riser backside を Stair interior として露出させない。
- Stair interior cavity を下面から見せない。
- Side Board ON/OFF に依存せず body 自体が閉じている。
- lower termination / upper termination が閉じている。
- body は `base_z` より下へ出ない。
- floor まで埋める巨大solidにしない。

`SLOPED_CLOSED` と `STEPPED_CLOSED` の差は visible soffit shape だけである。

Nosingとして意図的に突出したTread前端の下面・前面・側面は exterior finish として見えてよい。ただし、その後ろから Stair interior、Riser backside、closed body内部を見せてはならない。

---

## 9. Managed Object / transaction contract

07-Cでも:

```text
1 Managed Stair = 1 Blender Mesh Object
```

Normal transform:

```text
Location = (0,0,0)
Rotation = (0,0,0)
Scale    = (1,1,1)
```

全 geometry / material candidate は Scene mutation 前に prepare / validate する。

Rollback target は最低限:

- old Mesh datablock
- canonical dimensions
- Path / ascent
- assembly mode / schema
- Residential / 07-C fields
- Material pointers / slots
- Stair ID
- Object Transform

prepare failure / post-swap commit failure のどちらでも partial commit を残さない。

---

## 10. Assembly mode / schema policy

Assembly modeは変更しない。

```text
BASIC_TREAD_RISER
STANDARD_RESIDENTIAL
```

07-C current schema:

```text
schema = 3
```

### Existing 07-B schema 2 file

開いただけでは:

- schemaを書き換えない
- geometryを再生成しない
- UUID / Path / Materialsを変更しない
- 07-C固有fieldを理由に見た目を変えない

Legacy semantic defaults:

```text
side_board_mode = STEPPED
tread_front_overhang_mm = 0.0
tread_front_edge_mode = SQUARE
tread_front_edge_size_mm = 5.0
```

つまり **既存07-B fileはnosingなしのまま**である。

07-C固有状態を明示commitした場合:

```text
stair_schema_version = max(current, 3)
```

### New 07-C Stair final default

Build 07-C完成時の新規Residential Stair:

```text
assembly_mode = STANDARD_RESIDENTIAL
stair_schema_version = 3
underside_mode = STEPPED_CLOSED
side_board_mode = STEPPED
closed_body_depth = 150.0 mm
tread_front_overhang_mm = 5.0
tread_front_edge_mode = SQUARE
tread_front_edge_size_mm = 5.0
```

**新規07-C Stairの段鼻突出量は5.0 mmを既定値とする。**

Stage 1 / Stage 2の途中Buildでは、まだnosing geometryを有効化しない。Stage 3でnosing production geometryを導入すると同時に、新規Stair creation defaultを5.0 mmへ有効化する。

---

## 11. Canonical 07-C fields

### Existing storage authority retained

```text
side_board_band_width_mm
```

schema compatibility のため rename / delete しない。同じ意味のduplicate persistent propertyも追加しない。

07-C UI label:

```text
階段本体厚み (mm)
```

説明上は「段形状からvisible soffitまでの本体下面深さ」であり、`underside_thickness_mm`（下面シェル厚）とは別概念。

Default:

```text
150.0 mm
```

### New persistent fields

```text
side_board_mode
    STEPPED
    SLOPED

tread_front_overhang_mm

tread_front_edge_mode
    SQUARE
    BEVEL
    ROUND

tread_front_edge_size_mm
```

Legacy-compatible property defaults may remain overhang 0.0 so old files stay unchanged. Final new-07-C Stair creation explicitly sets overhang 5.0 mm.

### underside_mode extension

```text
STEPPED_CLOSED
SLOPED_CLOSED
```

Existing / semantic default remains `STEPPED_CLOSED`.

---

## 12. Residential settings UI

Existing `住宅階段仕様を変更` dialogを拡張する。

Recommended order:

```text
下面形式
    段々閉じ
    勾配閉じ

階段本体厚み (mm)        # default 150.0
下面シェル厚 (mm)

左Side Board
右Side Board
側板形状
    段々
    勾配
側板厚 (mm)
側板突出量 (mm)

段鼻突出量 (mm)          # new Stair default 5.0
踏板前縁
    角
    面取り
    丸
前縁サイズ (mm)          # BEVEL / ROUND時のみ有効
```

Material editingは既存の別operatorを維持する。Dialog commitは1 Undo step。

---

## 13. Stair-body thickness / closed-body depth

```text
d = side_board_band_width_mm / 1000
```

`d` は visible soffit location を決める。Defaultは150 mm。

`underside_thickness_mm` はphysical shell thicknessであり、visible soffit depthを決めない。

Validation baseline:

```text
0 < d < min(h, g)
```

selected profileは finite / positive-area / simple / no zero-length / no self-intersection / valid triangulation が必要。

Depth editはPath、Tread/Riser dimensions、Stair width、Side Board thickness/revealを変更しない。

---

## 14. STEPPED_CLOSED preservation

Accepted 07-B `STEPPED_CLOSED` contractを壊さない。

Existing schema-2 07-B Stairをordinary Regenerateしても、07-B accepted stepped bodyを再現する。

Nosing / front edge finishは exterior Tread detailであり、stepped body canonical referenceを勝手に移動しない。

---

## 15. SLOPED_CLOSED — human-confirmed body shape

SLOPED_CLOSEDのside-view targetは、2026-09-24に人間確認した参照画像1・2の形を正とする。

見た目の契約:

1. 一段目の下部は `Z=B` に**一つの水平底面**を持つ。
2. その水平底面の後端から、上階側まで**一本の連続した斜め直線soffit**で上がる。
3. 最上段側は**縦のupper closure**で閉じる。
4. Side BoardをOFFにしても、この本体形状だけでCLOSED Stairとして成立する。
5. 階段下の空間は残し、床までsolidで埋めない。

### Analytical contract

Upper legal plane:

```text
X_upper = L + r
```

Lower flat:

```text
P0 = (r, B)
P1 = (g + d, B)
```

### Stage 2 Blender runtime visual correction (2026-09-24)

Candidate r1 originally used the following endpoint:

```text
P2 = (L + r, B + (N - 1)h - d)
```

This formula is **superseded**. Blender runtime visual review showed that it
made the visible soffit progressively too steep toward the upper end.

The accepted corrected analytical contract uses the canonical Stair pitch:

```text
m = h / g

P0 = (r, B)
P1 = (g + d, B)

P2 = (
    L + r,
    B + m * ((L + r) - (g + d))
)
```

Required slope invariant:

```text
(P2.z - P1.z) / (P2.x - P1.x) ≈ h / g
```

Visible lower path:

```text
P0 -> P1 -> P2
```

The closed polygon then meets the accepted upper contact/body path on `X=L+r`, producing the required vertical upper closure.

Supported positive sloped run requires:

```text
g + d < L + r
```

Reject atomically if the sloped line crosses the contact profile, creates nonpositive depth/area, self-intersects, falls below B, or extends beyond L+r.

Full width:

```text
Y = [-w/2, +w/2]
```

BOTH / LEFT / RIGHT / OFF-OFF board states must all remain visually CLOSED.

---

## 16. Side Board modes

Side Boardは外付けfinish componentでありbody closure mechanismではない。

Side Boardの上下silhouetteは独立した二つのmodeで決定する。

- `side_board_mode` controls the upper / visible Side Board profile.
- `underside_mode` controls the Side Board lower profile.

Therefore, `SLOPED_CLOSED` では `side_board_mode == STEPPED` の場合も
Side Boardの下端はSection 15の修正済みsloped body undersideに従う。

Extrusion remains external:

```text
LEFT  = [+w/2, +w/2+s]
RIGHT = [-w/2-s, -w/2]
```

### STEPPED

Accepted 07-B Stage 3 board geometryをそのまま維持する。

### SLOPED — human-confirmed visual contract

SLOPED Side Boardのtargetは、2026-09-24に人間確認した参照画像3を正とする。

**重要: SLOPED boardの主要なvisible outlineを階段段形状のsawtoothにしない。斜めの直線仕上げとする。**

必須:

- 主たるvisible longitudinal edgeは、lower側からupper側まで一本のstraight slopeとして読む。
- 07-B STEPPED boardのような段々のvisible upper contourにはしない。
- lower terminationは07-Bでacceptした考え方を継承し、**一段目下部と揃う**。`base_z`より下へ出さない。
- lower endは必要なvertical/front closure + horizontal bottom capで閉じ、最下段周辺にmicro-notchを作らない。
- upper terminationは参照画像3の形を再現し、`X=L+r`を越えない。
- upper sideではstraight sloped runを終えた後、**vertical rear closure と短いhorizontal top cap**で閉じる。
- r6型のspike / giant triangle / diagonal rear plateを作らない。
- LEFT / RIGHT semanticsはuphill-relative。
- Side Board inner faceとbodyの間からinterior cavityを見せない。

`side_board_reveal_mm` はSLOPED boardでもvisible projection controlとして保持する。ただしSLOPED modeでは、revealを理由にsawtooth upper edgeを再導入しない。exact offset/intersection helperはStage 2でpure geometryとして定義し、上記visual/end-condition contractを満たすこと。

`side_board_mode` と `underside_mode` は独立。以下の全組み合わせを
validationの範囲で許可し、上端/下端profileを次のとおり生成する。

```text
STEPPED_CLOSED + STEPPED board = upper stepped / lower stepped
STEPPED_CLOSED + SLOPED board  = upper sloped  / lower stepped
SLOPED_CLOSED  + STEPPED board = upper stepped / lower sloped
SLOPED_CLOSED  + SLOPED board  = upper sloped  / lower sloped
```

---

## 17. Nosing / tread-front overhang

「踏板前出し」は **段鼻（nosing）を作る機能**として扱う。

```text
n = tread_front_overhang_mm / 1000
```

Existing 07-B / legacy semantic default:

```text
n = 0
```

Final new 07-C Stair creation default:

```text
n = 5.0 mm
```

Validation:

```text
0 <= n < g
```

Residential independent Tread `j = 1 .. N-1`:

```text
07-B:
x0 = (j - 1)g
x1 = jg + r

07-C:
x_front = (j - 1)g - n
x_rear  = jg + r
```

Only downhill/front extent changes。Tread top/bottom Z、rear plane `jg+r`、Riser geometry、Final Riserは変えない。上階到達面に追加Treadを作らない。

Side Board enabled時は基本supported relation:

```text
n <= side_board_reveal
```

invalid combinationはScene mutation前にrejectする。

---

## 18. Tread front edge finish

全faceはMaterial role `TREAD` のまま。

### SQUARE

既存rectangular front。

### BEVEL

```text
n > 0
0 < q < t/2
q <= n
```

Front XZ sectionに上下対称45° chamferを作る。

```text
(x_front + q, z0)
-> (x_front,     z0 + q)
-> (x_front,     z1 - q)
-> (x_front + q, z1)
```

### ROUND

同じsupported rangeを使う。上下front cornerをquarter-circle arcへ置換する。

Deterministic production geometry:

```text
4 linear segments per quarter arc
```

Managed canonical representationをunapplied Bevel Modifierへ依存させない。

Final new-07-C Stairのedge mode defaultは `SQUARE`。`q=5.0 mm` はstored defaultとしてよいがSQUARE時はinactive。

---

## 19. BASIC compatibility

`BASIC_TREAD_RISER` は accepted 07-A geometryのまま。

Ordinary BASIC operationは underbody / Side Board / nosing / bevel / round を追加しない。assembly mode、Path、IDを書き換えない。Residential-only fieldsはBASIC validityに参加しない。

Explicit BASIC -> Residential Applyはcurrent Residential schemaへ移行し、Undoでexact BASICへ戻る。

---

## 20. Material contract

Roles remain:

```text
TREAD
RISER
UNDERSIDE
SIDE_BOARD
```

No NOSING role。

- nosing / BEVEL / ROUND -> `TREAD`
- SLOPED_CLOSED -> `UNDERSIDE`
- SLOPED Side Board -> `SIDE_BOARD`

Base fallback / override / true UNASSIGNED / slot dedup semanticsは07-Bを維持。

---

## 21. State / lifecycle policy

07-B policyを維持する。

- normal-only operationsはabnormal stateでblock
- Repairはrecoverable stateのみ
- `INVALID_CANONICAL`をguess repairしない
- Deleteはmanaged abnormal Stairでも可能
- new fieldsはResidentialでrelevantな場合だけcanonical validationへ参加

Undo/Redo minimum:

- underside mode
- stair-body thickness
- Side Board mode
- nosing amount
- SQUARE / BEVEL / ROUND
- edge size
- combined settings

また Regenerate / dimensions / Path / Reverse / Material / Repair / Save-reopen / duplicate ID / Transform Repair / Finalize / Delete を維持する。

---

## 22. Stage plan

### Stage 1 — Foundation / Compatibility + Stair-body Thickness UI

Implement:

- version / description 0.7.2
- schema 3 foundation
- new canonical identifiers/fields/default semantics
- `SLOPED_CLOSED` and `side_board_mode` data identifiers/validators only
- user-facing `階段本体厚み (mm)` mapped to existing `side_board_band_width_mm`
- extended Residential settings transaction
- existing schema2 07-B compatibility
- no SLOPED production geometry yet
- no nosing production geometry yet
- old 07-B file ordinary Regenerate remains accepted stepped/no-nosing geometry

Stage 1 must not silently activate final 5 mm nosing before Stage 3 geometry exists.

### Stage 2 — SLOPED_CLOSED + SLOPED Side Board

Implement:

- analytical `C_sloped`
- sloped body fragment
- all body/board combinations
- human-confirmed SLOPED Side Board straight-line outline
- lower first-step-aligned termination
- image-3 upper cap/rear termination contract
- FORWARD / REVERSE
- oblique Path
- nonzero base_z
- stair-body thickness edit
- geometry health + visual CLOSED gates

### Stage 3 — Nosing + Front Edge Variants

Implement:

- nosing overhang
- final new-Stair default `5.0 mm`
- SQUARE preservation
- BEVEL
- ROUND
- board reveal compatibility
- Material role preservation
- body/board combinations

### Stage 4 — Lifecycle / Full Regression / Practical Placement

Verify:

- every new field lifecycle
- 07-B existing-file regression
- 07-A BASIC regression
- failure rollback
- Save/full exit/reopen
- Undo/Redo
- duplicate ID / Transform / geometry Repair
- Finalize / Delete
- Material Cases A/B/C
- Wall / Finish isolation
- practical Wall/Floor-like scene placement
- final visual / numerical / topology acceptance
- Build 07-C Acceptance Record

---

## 23. Stage 1 automated acceptance requirements

Minimum:

- new constants / fields
- schema2 record semantic defaults
- schema3 current semantics
- no load-time mutation
- `side_board_band_width_mm` remains storage authority
- UI label mapping does not create duplicate persistent depth property
- default stored body depth = 150 mm
- BASIC ignores 07-C fields
- existing 07-B semantic underside = STEPPED_CLOSED
- existing 07-B semantic board = STEPPED
- existing 07-B semantic overhang = 0
- existing 07-B semantic edge = SQUARE
- invalid values reject before mutation
- default Stage1 prepare of an old 07-B Stair reproduces accepted 07-B geometry/material roles
- historical tests do not globally prohibit future 07-D/07-F identifiers

---

## 24. Stage 2 automated acceptance requirements

Minimum:

- `C_sloped` endpoints
- lower flat at `Z=B`
- one straight main sloped segment
- upper vertical closure on `X=L+r`
- no body vertex below B
- max body X = L+r
- simple valid closed profile
- no contact-profile intersection
- full-width closure
- BOTH / LEFT / RIGHT / OFF-OFF
- STEPPED / SLOPED board modes
- all underside/board combinations
- SLOPED board visible main edge is straight, not sawtooth
- SLOPED board lower termination aligns with first-step lower rule
- SLOPED board upper termination has vertical rear closure + short horizontal cap, no diagonal rear plate
- FORWARD / REVERSE
- oblique Path
- nonzero base_z
- depth edit moves visible envelope but not Path/Tread/Riser canonical dimensions
- underside shell thickness does not locate visible soffit
- 07-B STEPPED geometry unchanged

Topology checks are required but do not replace visual acceptance。

---

## 25. Stage 3 automated acceptance requirements

Minimum:

- legacy/existing overhang 0 exact 07-B Tread regression
- new 07-C Stair final default overhang 5.0 mm
- positive overhang shifts front only by `-n`
- rear remains `jg+r`
- Riser unchanged
- no extra upper Tread
- `0 <= n < g`
- board-enabled `n <= reveal`
- SQUARE exact rectangular front
- BEVEL exact 45° front section
- ROUND deterministic 4-segment quarter arcs
- q validation
- Tread fragment finite / closed / positive area
- detail faces retain `TREAD` role
- same Materials -> same slot semantics
- body closure independent of nosing

---

## 26. Blender runtime visual gates

### SLOPED_CLOSED

Inspect:

- side orthographic
- oblique underside
- lower horizontal first-step bottom
- one straight sloped soffit
- vertical upper closure
- BOTH / LEFT / RIGHT / OFF-OFF
- FORWARD / REVERSE
- oblique Path
- nonzero base_z
- at least two stair-body thickness values

Required:

- reference-image-1/2 silhouette
- no interior cavity
- no unintended Tread/Riser backside
- no floor-to-stair solid mass
- no geometry below B
- no spike/giant triangle

### SLOPED Side Board

Inspect:

- reference-image-3 silhouette
- straight sloped visible finish, not sawtooth upper outline
- first-step-aligned lower termination
- upper short horizontal cap + vertical rear closure
- no diagonal rear plate
- LEFT / RIGHT semantic correctness under Reverse

### Nosing / edge

Inspect:

- 5.0 mm nosing scale on new final 07-C Stair
- SQUARE
- BEVEL
- ROUND
- first / middle / highest independent Tread
- Side Boards ON / OFF
- no z-fighting / self-overlap / cavity behind nose
- Riser position unchanged

---

## 27. Numerical / topology gates

Representative accepted configurations must have:

- finite coordinates
- zero zero-area faces
- valid closed fragments
- no unintended boundary / non-manifold edges for closed body configuration
- min Z >= B
- body / Side Board max uphill X <= L+r
- intentional nosing extends downhill only
- managed state NORMAL

Do not freeze one universal vertex/face count across all variants。Record actual counts per representative runtime configuration。

---

## 28. Practical placement smoke test

Build 07-C Acceptance includes one small residential-use visual scene using manually prepared Wall / Floor-like geometry。

Inspect:

- stair-body thickness
- sloped underside usefulness
- Side Board appearance
- 5 mm nosing scale
- upper/lower terminations
- no unexpected dependency on Wall/Floor Object types

This is visual/usability evidence only; no automatic Wall/Floor attachment is added。

---

## 29. Regression authority

### 07-B Residential

Preserve:

- existing schema2 load behavior
- STEPPED_CLOSED closed invariant
- Tread rear extension `jg+r`
- accepted 07-B STEPPED Side Board
- reveal / thickness semantics
- r7 upper termination
- Materials
- lifecycle / Repair / rollback

### 07-A BASIC

Preserve:

- 2-point Path
- 2800 / 16 rise contract
- FORWARD / REVERSE
- oblique Path
- BASIC geometry
- Material preservation
- Repair
- Save/reopen
- Undo/Redo
- Finalize / Delete

### Wall / Finish

Stair edits must not mutate managed Wall / Finish canonical state or geometry。

---

## 30. Acceptance evidence identity

Every runtime Candidate records:

- GitHub commit SHA
- Git tree SHA
- Candidate filename
- Candidate size
- Candidate SHA256
- Blender version
- add-on version / description

Known Codex/manual-PR workflow may produce different local and GitHub commit SHAs。When content identity is in question, compare Git tree SHA / GitHub-visible content according to `DEVELOPMENT_WORKFLOW.md`。

Automated evidence and Blender runtime evidence remain separate。

---

## 31. Completion condition

Build 07-C is accepted only when:

- Stages 1–4 accepted
- existing 07-B compatibility passes
- 07-A BASIC compatibility passes
- SLOPED_CLOSED image-1/2 visual contract passes
- SLOPED Side Board image-3 visual contract passes
- 5 mm nosing / BEVEL / ROUND gates pass
- lifecycle / rollback / persistence pass
- practical placement smoke test passes
- Acceptance Record is updated in a docs-only acceptance commit distinct from runtime production revision

After 07-C Acceptance, execute the Roadmap checkpoint before 07-D。
