# BUILD 07-D SPECIFICATION
## 日本住宅モデラー — Multi-point Path + L / U + Landing

> **Status: FINAL / IMPLEMENTATION AUTHORITY**  
> Date: 2026-09-27  
> Build 07-C overall Acceptance を baseline とし、07-C の accepted Straight Stair / lifecycle / geometry contract を壊さず、Stair Path を Multi-point へ拡張する。

---

## 1. Purpose

Build 07-D は、Build 07-C までに完成した Standard Residential Straight Stair を維持したまま、トップビューで複数の Path point を指定して、L字 / U字 / 複数 straight flight + Landing を **1つの Managed Stair** として生成・編集できる Foundation を作る Build である。

中心目的は次の8点とする。

1. 2-point Straight Path を後方互換のまま Multi-point Path へ拡張する。
2. L-shaped Path を production 対応する。
3. U-shaped Path / multiple straight flights を production 対応する。
4. 07-D の turn transition として Landing を追加する。
5. floor-to-floor と overall riser count を Stair 全体で一貫させ、各 Flight へ riser を配分する。
6. Riser Distribution を `AUTO / MANUAL` の両方で扱う。
7. START / END / intermediate TURN をマウスで再配置し、Shift 15°拘束と alignment guide を提供する。
8. 07-E Winder / 廻り段が同じ Path / Flight / Turn Foundation を再利用できる canonical architecture を確立する。

07-D の最終目的は、Landing 自体を過剰に高機能化することではない。**一般住宅の折れ曲がり階段を後続 07-E へ安全につなぐ Multi-point / Flight / Turn Foundation** を優先する。

---

## 2. Accepted baseline

07-D は以下を baseline とする。

- Build 05-B — Wall System — ACCEPTED
- Build 06-A / 06-B / 06-C — Finish system — ACCEPTED
- Build 07-A — Stair Core + 2-point Straight Stair — ACCEPTED
- Build 07-B — Standard Residential Straight Stair — ACCEPTED
- Build 07-C — Sloped Closed Underside + Straight Stair Finish Variants — overall ACCEPTED
- `BUILD_07_C_ACCEPTANCE_RECORD.md`
- `BUILD_07_C_SPECIFICATION.md`
- `DEVELOPMENT_WORKFLOW.md`
- `ROADMAP.md`

07-D specification baseline main:

```text
commit ea781845b94c0be9359ee8f07a12927aa8bf1072
tree   32f49239c287e978149a883d82205b35f7f03b2a
```

07-C exact runtime-tested production revision remains regression authority:

```text
commit f0e38b9fd268ec50cdc6680f342f34a472d56bc6
tree   9f091ac14b6efcdce4bfbc7f652f4809ff395b9a
```

Existing 07-C saved Stair must not silently change merely because 07-D is installed.

---

## 3. Roadmap position

```text
07-A  Stair Core + 2-point Straight Stair                   ACCEPTED
  ↓
07-B  Standard Residential Straight Stair                   ACCEPTED
  ↓
07-C  Sloped Closed Underside + Straight Finish Variants   ACCEPTED
  ↓
07-D  Multi-point Path + L / U + Landing                    CURRENT
  ↓
07-E  Winder / 廻り段
  ↓
07-F  Open / Support Variants
```

07-C practical checkpoint は完了し、次の本線として 07-D へ進む。

---

## 4. Add-on identification

07-D production implementation:

```text
version = (0, 7, 3)
description = "Build 07-D: Multi-point Path + L/U + Landing"
```

Stage途中の Candidate も 07-D production code を含む場合は同じ Build identity を使用してよい。

---

## 5. Core compatibility rule

07-D は existing Straight Stair を別方式へ作り直す Build ではない。

必須：

- existing schema-1 BASIC Straight Stair を開いただけで変更しない。
- existing schema-2 07-B Straight Stair を開いただけで変更しない。
- existing schema-3 07-C Straight Stair を開いただけで変更しない。
- existing 2-point Straight Path の geometry / nosing / top-arrival / Final Riser / underside / Side Board / Material semantics を維持する。
- schema-3 Straight Stair の ordinary Regenerate は 07-C accepted production behavior を再現する。
- Multi-point 対応のためだけに `canonical_path()` / `resolve_stair_layout()` の legacy 2-point behavior を曖昧に変更しない。

推奨実装：

```text
legacy 2-point resolver
    ↓ preserve

new schema-4 Multi-point resolver
    ↓ add beside legacy path
```

必要なら `canonical_multi_path()` / `resolve_multiflight_layout()` 等の pure helper を追加し、legacy Straight resolver を regression oracle として残す。

---

## 6. Managed Stair invariant

07-D でも：

```text
1 Managed Stair = 1 Blender Mesh Object
```

Path が L / U / Custom になっても、複数の独立 Managed Stair Object に分割しない。

内部では Flight / Landing / Tread / Riser / Underbody / Side Board を複数 fragment として生成してよいが、管理単位は1 Stairである。

Normal transform:

```text
Location = (0,0,0)
Rotation = (0,0,0)
Scale    = (1,1,1)
```

Canonical data → Derived Geometry の原則を維持し、生成 Mesh から Path / Flight / Turn を逆推定しない。

---

## 7. Schema policy

07-D Multi-point current schema:

```text
schema = 4
```

### 7.1 Legacy schema

```text
schema 1 = BASIC legacy
schema 2 = 07-B Residential
schema 3 = 07-C Residential Straight
schema 4 = 07-D Multi-point capable Stair
```

Existing schema-1/2/3 Stair は load 時に自動 upgrade しない。

07-D 固有 state を明示的に commit した場合のみ schema 4 へ移行する。

例：

- Straight → L / U / Multi-point へ変更
- schema-4 Turn data を作成
- schema-4 Riser Distribution state を作成

2-point Straight Stair をマウスで START / END 移動するだけの場合は、07-C semantic state を維持できるなら無理に schema 4 へ上げない。

---

## 8. Canonical Multi-point Path

### 8.1 User-visible Path

Path は world XY の ordered control points とする。

```text
Straight
P0 -------- P1

L
P0 -------- P1
             |
             |
             P2

U / multi-flight example
P0
 |
 |
P1 -------- P2
             |
             |
             P3
```

Meaning:

```text
P0 = START
Pn = END
P1 ... P(n-1) = TURN / intermediate Path points
```

`START / END` は draw order であり、lower / upper elevation とは別である。

```text
ascent_direction = FORWARD  -> P0 から Pn へ上る
ascent_direction = REVERSE  -> Pn から P0 へ上る
```

Reverse は canonical point order を書き換えない。

### 8.2 Path point identity

schema 4 では Path point に persistent point identity を持たせることを推奨し、07-E の Turn state が Object名や point index のみに依存しない構造とする。

概念：

```text
PathPoint
├ point_id
└ xy
```

START / TURN / END role は基本的に ordered position から導出し、duplicate persistent role state を増やさない。

Legacy schema-1/2/3 point へ load 時に勝手に ID を書き込まない。schema-4 への明示 upgrade 時に必要な ID を生成する。

### 8.3 Validation

Multi-point Path は最低限：

- 2 points 以上
- all coordinates finite
- adjacent segment length > epsilon
- adjacent duplicate point 禁止
- non-adjacent self-intersection / overlap 禁止
- supported Turn geometry が成立すること

invalid candidate は Scene mutation 前に reject する。

---

## 9. Supported 07-D Path topology

### 9.1 Straight

2 points。07-C exact behavior を維持する。

### 9.2 L-shaped

3 points / 2 straight flights / 1 turn。

```text
P0 -------- P1
             |
             |
             P2
```

07-D production Turn は `LANDING`。

### 9.3 U-shaped

4 points / 3 straight flights / 2 turns を 07-D の production U foundation とする。

```text
P0
 |
 |
P1 -------- P2
             |
             |
             P3
```

典型 U preset では first / third flight は平行・反対向き、middle flight はそれらへ90°とする。

07-D は compact 180° Winder を完成させる Build ではない。一般住宅で多い廻り段 / compact switchback transition は 07-E の担当とする。

### 9.4 Custom Multi-point

07-D final Stage 3 では、2点を超える複数 straight flight を同じ canonical model で扱えることを目標とする。

07-D production Turn geometry は90° left / right turnを基本対応とする。

全体 Stair は world X/Y に対して斜め配置してよい。つまり最初の Flight が 15° / 30° 等でもよいが、Landing turn 自体は adjacent Flight 間の ±90°を production contract とする。

arbitrary 30° / 45° turn Landing は 07-D acceptance必須にしない。

---

## 10. Turn canonical foundation

Interior Path point は geometry そのものではなく、Turn transition の anchor とする。

概念：

```text
TurnSpec
├ turn_id
├ path_point_id
└ turn_mode
```

07-D supported mode:

```text
LANDING
```

07-E extension:

```text
WINDER
```

07-D では user-facing Turn mode selection を必須にしない。新規 Multi-point Stair の interior Turn は Landing として作成する。

ただし persistent architecture は、07-E で同じ Path を描き直さず：

```text
LANDING -> WINDER
```

へ変更できることを前提とする。

07-E final UX の方向性：

```text
new residential turn default = WINDER
UI choice                    = LANDING
```

07-D saved Landing を 07-E install 時に勝手に Winder へ変換してはならない。

---

## 11. 90° Landing geometry contract

07-D の quarter-turn Landing は stair centerline TURN point を基準とした derived geometry とする。

Adjacent Flight direction:

```text
incoming axis = a
outgoing axis = b
abs(dot(a,b)) ~= 0
```

つまり ±90°。

Default Landing plan size は Stair width から自動導出する。

```text
w = stair_width
```

TURN center `T` の前後で各 Flight centerline を `w/2` cut back し、その間を nominal `w x w` の Landing area とする。

概念：

```text
incoming Flight ---- [ w x w Landing ]
                          |
                          |
                     outgoing Flight
```

07-D では arbitrary landing depth / custom landing polygon の UI は必須にしない。

Landing top elevation は、上り順で preceding Flight の cumulative riser count から導出する。

```text
landing_top_z = base_z + cumulative_risers * actual_riser
```

Landing slab thickness は既存 `tread_thickness` を基本とする。

Material role は新規 `LANDING` role を増やさず、walking surface / slab は `TREAD` Material contract を継承する。

Landing underside / closed-body continuation は `UNDERSIDE`、外付け Side Board 部分は `SIDE_BOARD` を使用する。

---

## 12. Flight resolution

Path segment をそのまま独立 Straight Stair として生成しない。

まず Multi-point route と Turn cutback を解決し、実際に riser / tread を配置できる **effective Flight run** を導出する。

90° Landing turn 1個に接する segment は Landing 側で `w/2` を消費する。

したがって概念上：

```text
first / last segment with one turn:
effective_run = segment_length - w/2

segment between two Landing turns:
effective_run = segment_length - w
```

各 effective Flight run は正の有限値であり、割り当てられた riser / tread geometry が成立する必要がある。

短すぎる segment は atomically reject する。

07-E では Winder transition が異なる cutback / turn area を持てるため、raw Path segment length を直接 Flight run として固定しない。

---

## 13. Overall height and riser invariant

Stair 全体で：

```text
N = overall riser_count
h = floor_to_floor / N
H = base_z + floor_to_floor
```

`h` は全 Flight 共通。

必須：

```text
sum(flight_riser_count) = N
```

Landing は水平であり、それ自体に追加の floor-to-floor rise を勝手に加えない。

各 Flight は preceding Landing / lower floor から次 Landing / upper arrival までを担当する。

Flight i に `r_i` risers を割り当てた場合、通常の独立 tread interval は基本的に：

```text
k_i = r_i - 1
```

arrival surface は Landing または upper arrival surface が担う。

07-C top-arrival contract は final Flight で維持する。

---

## 14. Riser Distribution canonical contract

User-facing mode:

```text
Riser Distribution
● AUTO
○ MANUAL
```

Persistent state:

```text
riser_distribution_mode = AUTO | MANUAL
```

schema 4 では Flight ごとの resolved allocation を保存可能な構造を持つ。

推奨：

```text
FlightAllocation
├ stable flight / segment reference
└ riser_count
```

AUTO でも resolved allocation を deterministic canonical snapshot として保存することを推奨する。これにより将来 algorithm が変わっても ordinary Regenerate で既存 Stair の配分を勝手に変えにくくする。

---

## 15. AUTO Riser Distribution

AUTO は 07-D の default。

目的：各 Flight の effective run に対して going が極端に不均衡にならないよう riser を整数配分する。

Flight i:

```text
L_i = effective run length
r_i = allocated risers
k_i = r_i - 1 = tread intervals
```

AUTO は概念的に `L_i / k_i` が各 Flight 間で近くなるよう `k_i` を配分する。

Constraints:

```text
sum(r_i) = N
r_i >= 2 for every production Flight
sum(k_i) = N - flight_count
k_i >= 1
```

したがって：

```text
N >= 2 * flight_count
```

を満たさない topology / count は reject してよい。

Allocation algorithm は deterministic でなければならない。

推奨：

- effective run 比率を使用
- integer apportionment
- largest-remainder 等の deterministic residual distribution
- tie は canonical Flight order で解決

AUTO Path edit / overall riser_count edit / topology edit 時：

```text
new candidate Path
↓
resolve effective flights
↓
recalculate AUTO allocation
↓
validate every Flight
↓
prepare all geometry
↓
atomic commit
```

AUTO の結果は UI で確認可能にする。

---

## 16. MANUAL Riser Distribution

MANUAL では user が Flight ごとの riser count を指定する。

L example:

```text
Flight 1 Risers = 7
Flight 2 Risers = 9
Total            = 16 / 16
```

U example:

```text
Flight 1 Risers = 5
Flight 2 Risers = 6
Flight 3 Risers = 5
Total            = 16 / 16
```

Rules:

- sum must equal overall `riser_count`
- each production Flight must meet minimum count
- invalid count を自動補正しない
- invalidなら commitしない
- Path point 移動後も MANUAL count は保持する
- Path変更で going / nosing / closed-body validation が成立しなくなった場合、countを勝手に変更せず移動を reject / rollbackする

### AUTO -> MANUAL

現在の AUTO resolved allocation をそのまま MANUAL 初期値へ引き継ぐ。

### MANUAL -> AUTO

現在の Path から AUTO allocation を再計算し、candidate validation 後に commitする。

Mode switch は1 Undo step。

---

## 17. Per-Flight dimensional validation

07-C の Residential validation を Multi-flight では各 Flight の derived going に対して適用する。

例：

```text
n = nosing / overhang
q = front edge size
d = closed-body depth
v = side-board reveal
g_i = Flight i going
```

各 Flight について、既存 07-C contract に対応する validation を行う。

少なくとも：

- riser_thickness < g_i
- nosing / edge geometry が g_i に対して成立
- closed-body depth が g_i / actual_riser に対して成立
- side-board reveal / body compatibility
- finite / positive-area geometry

1 Flight でも invalidなら Stair全体の candidate を rejectする。

---

## 18. Multi-flight geometry architecture

Straight codeをコピーして独立 Stair を複数作る方式は禁止する。

推奨 derived structure：

```text
ResolvedMultiStair
├ canonical_path
├ ascent_order
├ actual_riser
├ upper_arrival
├ flights[]
│   ├ local plan axis
│   ├ lower_z / upper_z
│   ├ effective_run
│   ├ riser allocation
│   └ going
└ turns[]
    ├ TURN anchor
    ├ landing plan
    └ landing elevation
```

各 Flight は既存 part-generator logic を再利用できる local layout を持つが、Scene mutation / UUID / Material / lifecycle は Stair全体で1回だけ行う。

07-C Straight geometry functions を無理に multi-flight semantics へ変形するより、accepted straight helper を再利用可能な pure part logicへ分離する方を優先する。

---

## 19. Tread / Riser / upper-arrival semantics

各 Flight の ordinary tread/riser は accepted Straight semantics を継承する。

Landing へ到達する preceding Flight の final riser top は Landing finished top と一致する。

Outgoing Flight の first riser は Landing top から上がる。

Final Flight の upper arrival は 07-C accepted top-arrival contractを維持する。

Positive nosing の final upper cap / Final Riser semanticsを、Multi-flight化の都合で元へ戻してはならない。

Landing approach edge に tread-front nosing を適用する場合は、incoming Flight の arrival edge として一貫させる。Landing side / outgoing edgeへ無差別に nosing を回さない。

---

## 20. Closed underside / Landing continuation

07-D final productionでは Multi-flight + Landing でも 07-C CLOSED invariant を維持する。

`STEPPED_CLOSED` / `SLOPED_CLOSED` とも：

- Tread / Riser backside を下面から見せない
- Stair interior cavity を見せない
- Flight と Landing の境界に大きな gap / spike / open cavity を作らない
- Side Board ON/OFF に依存せず body 自体を閉じる
- base_z より下へ出さない

Landing 下部は horizontal transition body として閉じてよい。

Flight の underside profile は各 local Flight axis で解決し、Turn 前後で world-space transform する。

07-D Stage 1ではまず Tread / Riser / Landing の見えるL字形を成立させ、final CLOSED / Side Board integration は Stage 2で完成させる。

---

## 21. Side Board continuation

07-D final productionでは `STEPPED / SLOPED` Side Board を Multi-flight Pathへ継続させる。

必須：

- left/right meaning は各 Flight の uphill local axis に対して解決する
- Turn で board が突然内外反転しない
- Landing周囲で大きなgap / duplicate spikeを作らない
- `side_board_mode` と `underside_mode` の独立契約を維持する
- Material roleは `SIDE_BOARD`

Turn join は geometry上必要なら miter / trimmed join / dedicated Landing board fragment を用いてよい。

1つの巨大polygonへ無理に統合することより、deterministic closed fragments + clean visible joinを優先する。

---

## 22. Path creation UX

07-D は Wallに近いトップビュー Path interaction を提供する。

### 22.1 Creation presets

Creation UI convenienceとして：

```text
Path形状
- Straight
- L
- U
- Custom   # Stage 3
```

を使用してよい。

これは canonical shape enum ではない。canonical authority は `path_points[] + Turn state`。

#### Straight

既存 2-click workflow を維持する。

#### L

```text
click P0
click P1
click P2
commit
```

#### U

```text
click P0
click P1
click P2
click P3
commit
```

#### Custom

```text
LEFT CLICK = point追加
ENTER      = finalize
BACKSPACE  = 最後の未確定pointを1つ戻す
ESC / RMB  = cancel
```

Custom finalizationには最低2点必要。

Creation preview は full Mesh regenerate を毎mouse moveで要求しない。Path line / point / Landing guideの軽量previewを優先し、commit時に全geometryをprepareする。

---

## 23. Shift 15° angle constraint

07-D Stair Path の Shift拘束は **existing Wallと同じ15°刻み** とする。

```text
Shift OFF = free angle
Shift ON  = nearest 15° world-plan angle
```

対象：

- new Path segment creation
- START move
- END move
- intermediate TURN move

既存 `drawing_alignment.constrained_direction(..., step_degrees=15.0)` と同じ数学的意味を再利用する。別の丸め規則を Stairだけに実装しない。

### Anchor rule

Endpoint move：唯一の隣接 point を anchor とする。

Interior point `Pi` move：Shift angular constraint の primary anchor は canonical previous point `P(i-1)` とする。

REVERSE ascentでも editing anchor rule は canonical Path orderを基準とし、上り方向で切り替えない。

---

## 24. Path alignment / guide contract

07-D の point creation / moveでは、Wall操作のガイド思想を再利用する。

最低限：

- world X alignment
- world Y alignment
- same Stair の他 Path pointとの X/Y alignment
- previous / next Path segment の延長線
- adjacent segmentに対する90°候補
- relevant non-adjacent Flightとのparallel候補

加えて、visible managed Wall endpoints は **passive alignment reference** として使用してよい。

重要：

- StairをWallへpersistent attachmentしない
- guide / snapで座標が一致してもdependencyを作らない
- Wall split / Wall deleteでStairを自動追従させない

これはStandalone Stair contractを維持するためである。

Guide selection はscreen-space thresholdを使い、ambiguous equal candidatesを勝手に選ばない既存Wall policyを可能な限り再利用する。

---

## 25. 90° / parallel guidance

一般住宅のL/U作成を容易にするため、world X/Y alignmentだけでなく local relationship guideを提供する。

例：

```text
incoming Flight ⟂ outgoing Flight
first Flight    ∥ third Flight
```

Whole Stair が world axis に対して 30°回転していても、この local 90° / parallel guide は機能すること。

L / U production Landingが90°を要求する場合、commit前previewで valid 90° candidate を明確に示す。

unsupported oblique turnを silent auto-correct しない。guideにsnapしなかった invalid turnはwarning + no commitとする。

---

## 26. Mouse Path-point relocation

07-D 必須操作：

- START move
- END move
- every intermediate TURN move

UIは dynamic point list / operator enum等で実装してよい。

例：

```text
始点を移動
折れ点 1 を移動
折れ点 2 を移動
終点を移動
```

Move workflow：

```text
invoke
↓
preview candidate only
↓
Shift / guide resolve
↓
LEFT CLICK
↓
resolve full Path / Flight / Landing / allocation
↓
prepare geometry
↓
atomic commit
```

ESC / RMB cancel は canonical / Mesh / Material / ID を一切変更しない。

1 point move = 1 Undo step。

Path point moveでObject Transformを使用しない。

---

## 27. Numeric Path edit

Existing `Path座標を変更` は精密入力手段として維持する。

schema-4 Multi-pointでは P0/P1固定UIではなく ordered pointsを編集できるUIへ拡張する。

数値入力も mouse moveも同じ canonical `path_points[]` と同じ transaction pathを使用する。

同じvalidation / AUTO allocation / MANUAL preservation ruleを通す。

---

## 28. Transaction / rollback contract

全 Multi-point editは existing `_transactional_update` 原則を拡張する。

Scene mutation前に最低限 prepareするもの：

- canonical multi-path validation
- Turn resolution
- effective Flight resolution
- riser allocation
- per-Flight dimensions
- Landing geometry
- Tread / Riser geometry
- underside / board geometry（対応Stage）
- Material slot plan

Rollback target は少なくとも：

- old Mesh datablock
- path_points + point identity
- Turn state
- distribution mode
- Flight allocation
- all previous dimensions
- ascent direction
- Residential 07-C fields
- Material pointers / slots
- Stair ID
- Object Transform

prepare failure / post-swap commit failure のどちらでも partial commitを残さない。

MANUAL allocation invalid / short Flight / unsupported Turn / self-intersection は old geometryを保持する。

---

## 29. Managed-state diagnosis / Repair

`INVALID_CANONICAL` は Multi-point state も診断対象とする。

Repairは invalid canonical を推測修正しない。

Recoverable policyは07-Cを継承：

- ID_MISSING
- ID_CONFLICT
- TRANSFORM_CHANGED
- GEOMETRY_MISSING

Repair時：

- path / Turn / allocations / Materialsを保持
- geometry missingなら same canonicalから再生成
- transform changedなら identityへ戻して same canonical geometryを再生成
- duplicate IDのみ new Stair ID

Multi-point化を理由にRepairでAUTO再配分を勝手に行わない。保存済みcanonical allocationがvalidならそれを使用する。

---

## 30. Material contract

07-C Material rolesを維持する。

```text
BASE
TREAD
RISER
UNDERSIDE
SIDE_BOARD
```

07-Dで新規 `LANDING` Material roleは追加しない。

Landing walking surface = TREAD
Landing/body underside = UNDERSIDE
Landing-side board = SIDE_BOARD

Regenerate / Path edit / Reverse / Repair / Save-Reopen / Undo-RedoでMaterial pointer / slot semanticsを保持する。

---

## 31. Reverse ascent

`REVERSE` は Multi-pointでも whole Stairの ascent traversal を反転する。

Canonical Path point orderは変えない。

```text
FORWARD: P0 -> ... -> Pn
REVERSE: Pn -> ... -> P0
```

Turn plan geometryは同じXYを使用し、Landing elevation / Flight lower-upper order / cumulative riser orderを反転する。

MANUAL Flight allocationは物理Path segmentへ保持し、Reverseだけで countを別segmentへ移さない。

---

## 32. Creation / edit validation messages

User-facing warningは最低限原因を区別する。

例：

- Path segmentが短すぎます
- Landingを作るための有効長が不足しています
- 07-D Landing turnは90°にしてください
- Pathが自己交差しています
- Flightごとの蹴上数合計が全体蹴上数と一致しません
- このFlightでは段鼻 / 本体厚み設定が成立しません

単一の「生成できません」だけにしない。

---

## 33. Explicit non-scope

07-Dでは必須にしない：

- Winder / 廻り段 production geometry
- 90° / 180° compact Winder
- arbitrary-angle Landing
- spiral / helical stair
- curved Flight
- arbitrary custom Landing polygon
- per-turn custom Landing width/depth UI
- Path point insert/delete after creation
- automatic Wall / Floor / Room attachment
- Stair opening / Floor boolean
- Riser OFF
- Underside NONE
- open / sawtooth / center support variants
- handrail / newel / baluster
- separate Landing Material
- production UV guarantee

Spiral stairは将来の別Build候補とし、07-Dの straight-segment Multi-point modelへ無理に含めない。

---

## 34. Stage 1 — Multi-point Foundation + first visible L

目的：ユーザーが早い段階で Blender上のL字形を目視確認できること。

Implementation minimum：

- add-on identity 0.7.3
- schema-4 foundation
- legacy 2-point exact regression
- 3-point canonical L Path
- point identity / Turn foundation
- one 90° Landing
- Multi-flight layout resolver
- AUTO riser distribution foundation
- Tread / Riser / Landing basic production geometry
- whole Stair = one Managed Mesh
- Material roles remain compatible
- prepare-before-mutation transaction

Stage 1では Side Board / full CLOSED turn finishを最終完成させなくてよいが、Candidateの制約をruntime documentに明記する。

### Stage 1 runtime acceptance focus

- 07-C Straight unchanged
- L Pathが3点として保存される
- 1 Managed Stairのみ
- L字として視覚的に成立
- floor-to-floor total exact
- AUTO allocation total exact
- Landing top height consistent
- Save / reopen basic persistence
- invalid 3-point candidate rollback

---

## 35. Stage 2 — L complete + editing UX

目的：L Stairを実用レベルへ完成。

Implementation：

- START / TURN / END mouse relocation
- Shift 15° constraint
- X/Y guide
- 90° guide
- parallel / extension guide
- passive Wall endpoint alignment guide
- numeric Multi-point edit
- MANUAL riser distribution
- AUTO <-> MANUAL handoff
- 07-C nosing / SQUARE / BEVEL / ROUND integration
- STEPPED_CLOSED / SLOPED_CLOSED integration
- STEPPED / SLOPED Side Board continuation
- Material lifecycle
- Reverse
- Regenerate / Repair

### Stage 2 runtime acceptance focus

- rotated L Stair + local 90°
- Shift 15° creation / point move
- TURN move changes both adjacent flights correctly
- AUTO reallocates after Path move
- MANUAL preserves counts after Path move
- invalid MANUAL move rolls back
- Landing / underbody / board visual gaps absent
- Undo / Redo strict sequence

---

## 36. Stage 3 — U + Multi-flight

目的：U / コの字 foundationと複数Flightを完成。

Implementation：

- 4-point U preset
- 3 Flight / 2 Turn / multiple Landing
- first / third parallel-opposite U guide
- TURN 1 / TURN 2 individual relocation
- AUTO / MANUAL allocation for 3+ flights
- Custom Multi-point creation where practical
- deterministic multiple-turn regeneration
- no Path self-intersection
- no landing/flight overlap that creates visible spikes

### Stage 3 runtime acceptance focus

- U visual shape
- two Landing elevations
- full floor-to-floor exact
- all Flight allocations total exact
- move P0/P1/P2/P3 independently
- Shift / 90° / parallel guide behavior
- Reverse whole Stair
- Save/full exit/reopen
- Material preservation
- 07-C Straight and L regression

---

## 37. Stage 4 — lifecycle / full regression / practical acceptance

Final acceptance must cover：

- Candidate identity
- Straight / L / U persistence
- AUTO / MANUAL persistence
- Undo / Redo
- invalid rollback
- Geometry Repair
- Transform Repair
- duplicate ID Repair
- Material lifecycle
- Finalize
- active-only Delete
- abnormal Delete
- schema-1 BASIC regression
- schema-2 07-B regression
- schema-3 07-C regression
- Wall / Finish isolation
- practical L placement
- practical U placement
- topology / finite / zero-area / boundary / nonmanifold checks
- full automated regression
- compileall
- git diff --check

07-D overall ACCEPTED は Stage 4完了後のみ。

---

## 38. Automated test architecture

Pure/testable logicを Blender modal codeから分離する。

最低限 pure test対象：

- canonical_multi_path validation
- 90° turn validation
- path self-intersection
- Landing cutback
- effective Flight run
- ascent order / Reverse
- AUTO allocation deterministic behavior
- MANUAL allocation validation
- sum(r_i) invariant
- per-Flight going
- schema compatibility
- transaction candidate snapshot / restore semantics where pure-testable

Stageごとに dedicated `tests/test_build_07_d_stageN.py` を追加する。

Prior 07-A / 07-B / 07-C test suitesを regression target とする。

---

## 39. Runtime test policy

`DEVELOPMENT_WORKFLOW.md` を継承する。

特に Undo / Redo：

```text
UI operation
↓
Ctrl+Z
↓
Ctrl+Shift+Z
↓
then Console
```

UndoとRedoの間にPython Console操作を挟まない。

Runtime testは可能な限り：

```text
Console canonical evidence
+
必要箇所だけ目視
```

とする。

Path creation / point relocation / guide behaviorはUI目視が必要だが、commit後の point coordinates / allocation / IDs / schema / Materials / issue state はConsoleで確認する。

---

## 40. Acceptance principles

07-Dは以下を満たした場合のみoverall ACCEPTEDとする。

1. Existing 07-C Straight Stairを壊さない。
2. L / Uが1 Managed Stairとして成立する。
3. floor-to-floor totalとoverall riser countが全Flightで一貫する。
4. AUTO / MANUAL allocationがdeterministicである。
5. START / END / every TURNを安全に移動できる。
6. Shift 15°と90° / parallel guideで一般住宅Pathを作りやすい。
7. Landing + CLOSED underside + Side Boardに重大なgap / spike / cavityがない。
8. Save / reopen / Undo / Redo / Repair / Finalize / Deleteが成立する。
9. Wall / Finishへ回帰を起こさない。
10. 07-E Winderが同じ Path / Turn Foundationへ追加可能である。

---

## 41. 07-E handoff contract

07-D completion時点で次を確保する。

```text
Multi-point Path
+
persistent Turn anchors
+
resolved Flights
+
overall height/riser invariant
+
AUTO/MANUAL allocation
+
mouse point editing
+
15° / 90° / parallel guide
```

07-E はこのFoundationへ：

```text
Turn mode = WINDER
Winder turn area
Winder riser allocation
inner / outer tread geometry
side-board continuation
```

を追加する。

07-Eのために07-D accepted Landingを破壊的に再定義しない。

---

## 42. Final implementation rule

07-D では「何でも曲がる階段」を一度に作らない。

優先順位：

```text
accepted Straight compatibility
    ↓
clean Multi-point canonical model
    ↓
visible L
    ↓
editable L
    ↓
U / multi-flight
    ↓
full lifecycle
    ↓
07-E Winder
```

ユーザーがBlender上で形を確認した結果、Landing外観やPath UXに問題があれば、Stage acceptance前にSpecification addendum / correctionとして修正する。

Runtime visual evidenceは geometry formulaと同じくproduction authorityの一部として扱う。
