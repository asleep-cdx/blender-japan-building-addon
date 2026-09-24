# BUILD 07-C SPECIFICATION
## 日本住宅モデラー — Sloped Closed Underside + Straight Stair Finish Variants

> **Status: DRAFT FOR REVIEW**  
> Date: 2026-09-24  
> Build 07-B overall Acceptance を baseline とし、07-B の accepted canonical / lifecycle / geometry contract を壊さずに Straight Stair の finish variants を追加する。

---

## 1. Purpose

Build 07-C は、Build 07-B で Acceptance 済みとなった Standard Residential Straight Stair を維持したまま、直線住宅階段としての見た目・仕上げ選択を拡張する Build である。

07-C の中心目的は次の5点とする。

1. `SLOPED_CLOSED` の連続勾配下面を追加する。
2. Side Board に `SLOPED` variant を追加する。
3. Tread front overhang / nosing を追加する。
4. Tread front edge の basic `BEVEL` / `ROUND` variant を追加する。
5. Build 07-B で内部互換fieldとして保持していた closed-body depth を、明確なユーザー向け「本体下面深さ」として操作可能にする。

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

07-C specification drafting baseline `main`:

```text
commit ececf52e759896344fc48c1fbe07a8e4d033361f
tree   2374ee4f504fb39942890030da6b758ccfe898de
```

07-B accepted production behavior is regression authority. 07-C implementation must not silently change existing 07-B saved Stair geometry.

---

## 3. Roadmap position

```text
07-A  Stair Core + 2-point Straight Stair
      ACCEPTED
        ↓
07-B  Standard Residential Straight Stair
      + STEPPED_CLOSED
      + full-depth Side Boards
      + part Materials
      ACCEPTED
        ↓
07-C  SLOPED_CLOSED
      + Straight Stair Finish Variants
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

07-C production implementation では以下を使用する。

```text
version = (0, 7, 2)
description = "Build 07-C: Sloped Closed Underside + Straight Stair Finish Variants"
```

---

## 5. Coordinate and terminology contract

Resolved local axes は 07-B を継承する。

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
d = closed_body_depth
s = side_board_thickness
v = side_board_reveal
n = tread_front_overhang
q = tread_front_edge_size
```

`START / END` は Path draw order の意味だけを持つ。高さ側は `lower / upper` とし、FORWARD / REVERSE から解決する。

---

## 6. 07-C production scope

- existing 2-point Straight Stair Path
- existing FORWARD / REVERSE
- BASIC / STANDARD_RESIDENTIAL separation
- schema compatibility
- `STEPPED_CLOSED` preservation
- new `SLOPED_CLOSED`
- user-facing closed-body depth
- existing full-depth external Side Boards
- `STEPPED` Side Board preservation
- new `SLOPED` Side Board variant
- tread front overhang / nosing
- tread front edge `SQUARE / BEVEL / ROUND`
- existing part Materials
- Regenerate / Repair / failure rollback
- Save / full exit / reopen
- Undo / Redo
- duplicate-ID lifecycle
- Editable Mesh finalization
- dedicated active-only Delete
- oblique Straight Path
- Wall / Finish isolation regression
- practical straight-stair placement smoke test

---

## 7. Explicit non-scope

07-C では以下を production 実装しない。

- Multi-point Path
- Shift angle constraint
- mouse Path-point relocation
- L-shaped Stair
- U-shaped Stair
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
- arbitrary custom nosing Profile
- arbitrary custom Side Board Profile
- production UV / guaranteed wood-grain direction
- automatic Floor / Wall / Room connection
- universal arbitrary Mesh framework

---

## 8. CLOSED invariant — 07-B correctionを継承

`STANDARD_RESIDENTIAL + STEPPED_CLOSED` と `STANDARD_RESIDENTIAL + SLOPED_CLOSED` は、どちらも CLOSED Stair である。

必須：

- Tread / Riser の内部側 backside を Stair 内部として露出させない。
- Stair interior cavity を下面から見せない。
- Side Board ON/OFF に依存せず body 自体が閉じている。
- lower termination が閉じている。
- upper termination が閉じている。
- body は `base_z` より下へ出ない。
- floor まで埋める巨大solidにしない。

`SLOPED_CLOSED` と `STEPPED_CLOSED` の差は **visible soffit shape** であり、closed / open の差ではない。

### 8.1 Intentional nosing exception

07-C の Tread front overhang は finished exterior projection である。

そのため、nosing として意図的に突出した部分の下面・前面・側面が外から見えることは許容する。

ただし、その突出部の後ろから Stair interior cavity、Riser backside、または本来 closed body 内に隠れる Tread underside が見えてはならない。

---

## 9. Managed Object / transaction contract

07-C でも:

```text
1 Managed Stair = 1 Blender Mesh Object
```

Normal managed Transform:

```text
Location = (0,0,0)
Rotation = (0,0,0)
Scale    = (1,1,1)
```

すべての geometry / material candidate は Scene mutation 前に prepare / validate する。

Rollback target は最低限次を含む。

- old Mesh datablock
- canonical dimensions
- Path / ascent
- assembly mode
- schema version
- all Residential / 07-C fields
- Material pointers / slots
- Stair ID
- Object Transform

prepare failure / post-swap commit failure のどちらでも partial commit を残さない。

---

## 10. Assembly mode

07-C は 07-B の assembly mode を変更しない。

```text
BASIC_TREAD_RISER
STANDARD_RESIDENTIAL
```

BASIC ordinary operations は 07-C Residential fields を無視し、07-A accepted behavior を維持する。

---

## 11. Schema version policy

07-C の current schema は:

```text
schema = 3
```

### 11.1 Existing 07-B Residential file

07-B schema 2 file を開いただけでは:

- schema を書き換えない
- geometry を再生成しない
- new fields を明示保存しない
- UUID / Path / Materials を変更しない

07-C runtime で ordinary Regenerate を行った場合も、new 07-C fields の semantic default により 07-B accepted geometry を再現しなければならない。

### 11.2 Schema bump condition

07-C 固有状態をユーザーが明示commitした場合は:

```text
stair_schema_version = max(current, 3)
```

07-C 固有状態には最低限以下を含む。

- `underside_mode = SLOPED_CLOSED`
- `side_board_mode = SLOPED`
- nonzero tread front overhang
- front edge mode `BEVEL` / `ROUND`

既存field `side_board_band_width_mm` の値を user-facing closed-body depth として編集するだけの場合も、07-C settings operator を通じて commit した時点で schema 3 としてよい。

### 11.3 New 07-C Stair

新規 Stair は:

```text
assembly_mode = STANDARD_RESIDENTIAL
stair_schema_version = 3
```

ただし default visual geometry は 07-B accepted default と同一にする。

---

## 12. Canonical 07-C fields

07-B canonical fields は維持する。

### 12.1 Existing field retained as storage authority

```text
side_board_band_width_mm
```

この property は schema compatibility のため **rename / delete しない**。

07-C では意味を明確化し、UI label を:

```text
本体下面深さ (mm)
```

とする。

semantic name / helper として `closed_body_depth` を使用してよいが、同じ意味の duplicate persistent property を追加しない。

### 12.2 New persistent fields

Conceptual canonical additions:

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

Recommended defaults:

```text
side_board_mode = STEPPED
tread_front_overhang_mm = 0.0
tread_front_edge_mode = SQUARE
tread_front_edge_size_mm = 5.0
```

`5.0` mm edge size is stored but inactive while mode is `SQUARE`.

### 12.3 Existing underside field extension

`underside_mode` choices become:

```text
STEPPED_CLOSED
SLOPED_CLOSED
```

Default remains:

```text
STEPPED_CLOSED
```

---

## 13. Compatibility-neutral default

New 07-C Residential Stair defaults must produce the same accepted shape as 07-B default:

```text
underside_mode = STEPPED_CLOSED
side_board_mode = STEPPED
tread_front_overhang_mm = 0.0
tread_front_edge_mode = SQUARE
closed_body_depth = 150.0 mm
side_board_reveal = 40.0 mm
side_board_thickness = 18.0 mm
left_side_board = ON
right_side_board = ON
```

Expected default accepted geometry before any opt-in 07-C variant remains:

```text
620 vertices
732 faces
```

07-C installation alone must not visually alter accepted 07-B Stair files.

---

## 14. User-facing Residential settings UI

Existing `住宅階段仕様を変更` operator / dialog を拡張する。

Recommended order:

```text
下面形式
    段々閉じ
    勾配閉じ

本体下面深さ (mm)
下面厚 (mm)

左Side Board
右Side Board
側板下面形状
    段々
    勾配
側板厚 (mm)
側板突出量 (mm)

踏板前出し (mm)
踏板前縁
    角
    面取り
    丸
前縁サイズ (mm)   # BEVEL / ROUND時のみ有効表示
```

Material editing remains the existing separate Material operator.

Dialog commit は一つの Undo step とする。

---

## 15. Closed-body depth semantics

`d = side_board_band_width_mm / 1000` is the closed-body depth authority.

07-B corrected body と同じく、`d` は visible soffit location を決める。

`underside_thickness_mm` は `d` と別概念であり、visible soffit depth を決めない。

Validation baseline:

```text
0 < d < min(h, g)
```

加えて selected profile は:

- finite
- positive-area
- no duplicate consecutive points after cleanup
- no zero-length edge
- no self-intersection
- valid winding / triangulation

でなければならない。

Depth edit は Tread / Riser canonical dimensions、Path、Stair width、Side Board thickness/reveal を変更しない。

---

## 16. STEPPED_CLOSED preservation

07-C は accepted 07-B `stepped_closure_visible_profile()` contract を壊さない。

Default 07-C Stair と existing schema-2 07-B Stair の `STEPPED_CLOSED` output は 07-B accepted productionと一致すること。

Tread overhang / edge finish は exterior Tread detail として扱い、closed body silhouette の canonical reference を暗黙に移動しない。

---

## 17. SLOPED_CLOSED visible soffit

`SLOPED_CLOSED` は accepted corrected body の contact profile を再利用し、visible lower profile だけを連続勾配へ置き換える。

Body/contact inner profile は 07-B Residential Tread/Riser junction contract を維持する。

### 17.1 Upper legal plane

```text
X_upper = L + r
```

No geometry may extend uphill beyond `L+r` as a consequence of underside generation.

### 17.2 Lower flat termination

07-B の lowest-step visual ruleを継承し、lower start は `base_z` 上で閉じる。

Define:

```text
P0 = (r, B)
P1 = (g + d, B)
```

`P0 → P1` is one flat lower termination segment.

For `SLOPED_CLOSED`, a positive sloped run requires:

```text
g + d < L + r
```

If this condition is not satisfied, the selected configuration is unsupported and must be rejected before Scene mutation rather than silently generating a degenerate shape.

### 17.3 Sloped soffit endpoint

Define:

```text
P2 = (L + r, B + (N - 1)h - d)
```

Visible profile:

```text
C_sloped = [P0, P1, P2]
```

Thus:

- first-step/lower region remains flat at `Z=B`,
- the main soffit from `P1` to `P2` is one straight segment,
- upper rear remains on `X=L+r`,
- body remains above floor rather than becoming a floor-to-stair solid mass.

### 17.4 Geometry validation

`C_sloped` + accepted component-contact inner profile must form a valid simple closed XZ polygon.

Validation must reject configurations where the sloped soffit:

- crosses the inner/contact profile,
- produces zero or negative body depth,
- self-intersects,
- creates zero-area geometry,
- falls below `B`,
- extends beyond `L+r`.

Do not infer the sloped profile from existing Mesh vertices.

---

## 18. SLOPED_CLOSED lateral closure

The body spans full Stair width:

```text
Y = [-w/2, +w/2]
```

All four Side Board combinations must remain visually CLOSED:

- BOTH
- LEFT only
- RIGHT only
- OFF/OFF

Side Board enable flags never decide whether the body exists.

---

## 19. Side Board modes

07-C Side Board is still an external decorative/finish component.

LEFT / RIGHT semantics remain uphill-relative.

Side Board extrusion remains outside the body:

```text
LEFT  = [+w/2, +w/2+s]
RIGHT = [-w/2-s, -w/2]
```

### 19.1 STEPPED

`STEPPED` preserves accepted 07-B Stage 3 board geometry.

- accepted stepped upper/reveal contour
- accepted stepped lower/body contour
- accepted vertical upper rear termination
- no r6-style spike / giant triangle

### 19.2 SLOPED

`SLOPED` means:

- upper edge remains the stair-following accepted reveal contour,
- lower edge uses the same continuous sloped lower profile contract as `SLOPED_CLOSED`,
- lower start remains clipped/closed at `B`,
- upper rear remains `X=L+r` with a vertical closing rear edge,
- no diagonal giant rear plate.

This produces a board with a stair-following top and a straight sloped lower edge.

`side_board_mode` is independent from `underside_mode`.

Therefore all combinations are legal if geometry validation succeeds:

```text
STEPPED_CLOSED + STEPPED board
STEPPED_CLOSED + SLOPED board
SLOPED_CLOSED  + STEPPED board
SLOPED_CLOSED  + SLOPED board
```

The body remains CLOSED even when the board shape differs from the body soffit.

---

## 20. Side Board reveal and nosing relationship

Existing `side_board_reveal_mm` meaning is preserved.

When either Side Board is enabled and tread overhang `n > 0`, supported 07-C relationship is:

```text
n <= v
```

This keeps the nosing/downhill projection within the accepted board reveal envelope.

If both Side Boards are OFF, this relation is not required.

Invalid combinations must be rejected atomically.

---

## 21. Tread front overhang / nosing

`n = tread_front_overhang_mm / 1000`.

Default:

```text
n = 0
```

Validation baseline:

```text
0 <= n < g
```

For Residential independent Tread ordinal `j = 1 .. N-1`, accepted 07-B rear/uphill extension remains unchanged.

07-B:

```text
x0 = (j - 1)g
x1 = jg + r
```

07-C with overhang:

```text
x_front = (j - 1)g - n
x_rear  = jg + r
```

Tread top/bottom Z remain unchanged.

Riser geometry remains unchanged.

Final Riser remains unchanged.

No arrival/upper-floor Tread is invented.

The overhang changes only the downhill/front extent of each independent Tread.

---

## 22. Tread front edge mode

Front edge variants are Tread geometry, not a new material role.

All resulting faces remain Material role `TREAD`.

### 22.1 SQUARE

Existing rectangular front edge.

`q` is ignored.

### 22.2 BEVEL

Requires:

```text
n > 0
0 < q < t/2
q <= n
```

Apply a symmetric 45-degree chamfer to the two front corners of the Tread XZ section.

For front `x = x_front`, bottom `z0`, top `z1`:

```text
(x_front + q, z0)
→ (x_front,     z0 + q)
→ (x_front,     z1 - q)
→ (x_front + q, z1)
```

The remaining Tread section continues to the accepted rear plane.

### 22.3 ROUND

Requires the same supported range:

```text
n > 0
0 < q < t/2
q <= n
```

Each of the two front corners is replaced by a quarter-circle arc of radius `q` in the XZ section.

For deterministic Build 07-C production geometry:

```text
4 linear segments per quarter arc
```

No adaptive segment count in 07-C.

The upper and lower quarter arcs may retain a short vertical front segment between them.

### 22.4 No hidden Modifier dependency

Managed geometry must be deterministically regenerable from canonical fields.

Do not depend on an unapplied user-editable Bevel modifier as the canonical representation.

---

## 23. BASIC compatibility

`BASIC_TREAD_RISER` remains accepted 07-A geometry.

Ordinary BASIC operations must not:

- add underbody
- add Side Boards
- add nosing
- bevel/round Treads
- bump assembly mode
- rewrite Path / ID

07-C Residential-only fields may exist semantically/defaulted but do not participate in BASIC validity.

Explicit BASIC → Residential apply under 07-C creates current Residential schema 3 with compatibility-neutral defaults.

Undo after Apply restores the exact BASIC state.

---

## 24. Material contract

Existing roles remain:

```text
TREAD
RISER
UNDERSIDE
SIDE_BOARD
```

No new NOSING role.

- overhang / BEVEL / ROUND faces → `TREAD`
- SLOPED_CLOSED faces → `UNDERSIDE`
- SLOPED Side Board faces → `SIDE_BOARD`

Base fallback / role override / true UNASSIGNED semantics remain exactly as accepted in 07-B.

Material slot identity deduplication remains required.

---

## 25. State diagnosis / operation policy

07-B managed-state policy is preserved.

Normal-only operations remain blocked on abnormal state.

Repair continues only for recoverable states.

`INVALID_CANONICAL` remains non-repairable by guessing new canonical values.

Delete remains available for managed abnormal Stair objects.

New 07-C fields must participate in canonical validation only when relevant to Residential mode.

---

## 26. UI / Undo / lifecycle requirements

At minimum verify Undo/Redo for:

- underside mode change
- closed-body depth edit
- Side Board mode change
- overhang edit
- SQUARE → BEVEL / ROUND
- edge size edit
- combined settings edit

Also verify:

- Regenerate
- dimension edit
- Path edit
- Reverse
- Material edit
- Repair
- Save/full exit/reopen
- Duplicate ID Repair
- Transform Repair
- Finalize
- active-only Delete

---

## 27. Stage plan

### Stage 1 — 07-C Foundation / Compatibility + Closed-body Depth UI

Implement:

- version / description 0.7.2
- schema 3 foundation
- new canonical fields/defaults
- `SLOPED_CLOSED` / `side_board_mode` identifiers and validators as data foundation
- user-facing `本体下面深さ (mm)` mapped to existing `side_board_band_width_mm`
- extended Residential settings transaction
- no `SLOPED_CLOSED` production geometry yet unless explicitly included and tested as Stage 2 work
- strict 07-B schema2 compatibility
- default 07-C geometry identical to accepted 07-B

Stage 1 acceptance must prove old 07-B files do not visually migrate.

### Stage 2 — SLOPED_CLOSED + SLOPED Side Board

Implement:

- analytical `C_sloped`
- sloped closed-body fragment
- all board/body mode combinations
- SLOPED Side Board lower profile
- FORWARD / REVERSE
- oblique Path
- nonzero base_z
- depth edit
- geometry health + visual CLOSED gates

### Stage 3 — Tread Nosing + Front Edge Variants

Implement:

- overhang
- SQUARE preservation
- BEVEL
- ROUND
- board reveal compatibility
- role-based Material preservation
- all relevant body/board combinations

### Stage 4 — Lifecycle / Full Regression / Practical Placement

Verify:

- 07-C lifecycle for every new field
- 07-B default regression
- 07-A BASIC regression
- failure rollback
- Save/full exit/reopen
- Undo/Redo
- duplicate ID / Transform / geometry Repair
- Finalize / Delete
- Material Cases A/B/C
- Wall / Finish isolation
- manual Wall/Floor-like practical scene placement
- final visual / numerical / topology acceptance
- Build 07-C Acceptance Record

---

## 28. Stage 1 automated acceptance requirements

Minimum Blender-independent coverage:

- new constants / default fields
- schema 2 old record semantic defaults
- schema 3 current record semantics
- no load-time mutation design
- `side_board_band_width_mm` remains storage authority
- closed-body depth label/property mapping does not add duplicate persistent data
- BASIC ignores 07-C fields
- default current Residential remains `STEPPED_CLOSED`
- default side board remains `STEPPED`
- default overhang = 0
- default edge = `SQUARE`
- default 07-C prepare path reproduces accepted 07-B counts/roles
- invalid 07-C values rejected before mutation
- future 07-D/07-F identifiers are not globally prohibited by historical tests

---

## 29. Stage 2 automated acceptance requirements

Minimum:

- `C_sloped` exact endpoint contract
- lower flat segment at `Z=B`
- no vertex below B
- max body X = L+r
- sloped segment is one straight line
- positive sloped run required
- simple valid closed profile
- no intersection with contact/inner profile
- full-width closure
- Side Board OFF/OFF still closed
- BOTH / LEFT / RIGHT / OFF configurations
- STEPPED / SLOPED board modes
- all underside/board combinations
- FORWARD / REVERSE canonical semantics
- oblique Path resolved axes
- nonzero base_z
- depth changes move visible body/board envelope but not Path/Tread/Riser canonical dimensions
- thickness does not locate visible soffit
- 07-B STEPPED geometry unchanged

Topology checks are required but do not replace visual CLOSED acceptance.

---

## 30. Stage 3 automated acceptance requirements

Minimum:

- overhang n=0 exact 07-B Tread regression
- positive overhang shifts front only by `-n`
- rear remains `jg+r`
- Riser geometry unchanged
- no extra upper Tread
- `0 <= n < g`
- board-enabled `n <= reveal`
- SQUARE exact rectangular front
- BEVEL exact four-point front section contract
- ROUND deterministic 4-segment quarter arcs
- q range validation
- generated Tread fragment is finite / closed / non-zero-area
- new Tread detail faces keep `TREAD` role
- Material slot plan unchanged for same Materials
- body closure independent of nosing

---

## 31. Blender runtime visual gates

### 31.1 SLOPED_CLOSED

Inspect at minimum:

- side orthographic
- oblique underside
- lower termination
- upper termination
- BOTH boards
- LEFT only
- RIGHT only
- OFF/OFF
- FORWARD
- REVERSE
- oblique Path
- nonzero base_z
- at least two closed-body depth values

Required visual result:

- continuous straight sloped soffit after the lower flat segment
- no internal cavity
- no exposed unintended Tread/Riser backside
- no floor-to-stair solid mass
- no geometry below base_z
- no upper spike/giant triangle
- no body/board gap revealing interior

### 31.2 SLOPED Side Board

Inspect:

- stepped upper/reveal relation remains coherent
- lower edge is continuous slope
- vertical rear termination
- no diagonal rear plate
- LEFT/RIGHT semantic correctness under Reverse

### 31.3 Nosing / edge finish

Inspect:

- SQUARE
- overhang only
- BEVEL
- ROUND
- close-up front edge
- first / middle / highest independent Tread
- with Side Boards ON and OFF

Required:

- no self-overlap
- no z-fighting
- no visible internal cavity behind nose
- no accidental Riser displacement
- consistent repeated profile on all independent Treads

---

## 32. Final numerical / topology gates

For every final accepted representative configuration:

- all coordinates finite
- zero zero-area faces
- closed fragments valid
- assembled geometry has no unintended boundary / non-manifold edges for the accepted closed body configuration
- min Z >= B
- body / Side Board max X <= L+r except intentional Tread front overhang which extends only downhill (`-X`)
- managed state NORMAL

Do not freeze one universal vertex/face count across all finish variants.

Counts must be recorded per representative configuration at runtime rather than predicted in this specification.

---

## 33. Practical placement smoke test

Build 07-C Acceptance must include one small residential-use visual scene.

The scene may use manually prepared simple Wall / Floor-like geometry; Build 08 Floor system is not required.

At minimum place one 07-C Stair next to/within simple architectural context and inspect:

- perceived stair-body thickness
- sloped underside visual usefulness
- Side Board choice
- nosing scale
- upper/lower termination in architectural context
- no unexpected dependency on Wall / Floor Object types

This test is visual/usability evidence only and does not create new automatic Wall/Floor attachment behavior.

---

## 34. Regression authority

07-C must keep the following accepted behaviors:

### 07-B Residential

- default STEPPED_CLOSED body
- corrected closed visual invariant
- Residential Tread rear extension to `jg+r`
- full-depth external boards
- reveal/thickness semantics
- accepted upper termination
- Materials
- lifecycle / Repair / rollback

### 07-A BASIC

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

Stair edits must not mutate managed Wall / Finish canonical state or geometry.

---

## 35. Acceptance evidence identity

Every runtime Candidate must record:

- GitHub commit SHA
- Git tree SHA
- Candidate filename
- Candidate size
- Candidate SHA256
- Blender version
- add-on version / description

If Codex local commit SHA differs from GitHub because of the known environment/manual-PR workflow, tree SHA and GitHub-visible content are used to establish content identity according to the project workflow.

Automated evidence and Blender runtime evidence remain separate.

---

## 36. Completion condition

Build 07-C is accepted only when:

- Stages 1–4 are accepted,
- 07-B default compatibility passes,
- 07-A BASIC compatibility passes,
- SLOPED_CLOSED visual CLOSED gates pass,
- SLOPED Side Board gates pass,
- nosing / BEVEL / ROUND gates pass,
- lifecycle / rollback / persistence pass,
- practical placement smoke test passes,
- Acceptance Record is updated in a docs-only acceptance commit distinct from the runtime production revision.

After 07-C Acceptance, Roadmap checkpoint is executed before starting 07-D, as already planned.
