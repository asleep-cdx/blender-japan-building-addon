# BUILD 07-E SPECIFICATION
## 日本住宅モデラー — Winder / 廻り段 + Arbitrary-angle Turn / Landing

> **Status: DRAFT / REVIEW**  
> Date: 2026-09-30  
> Build 07-D overall Acceptance を baseline とし、07-D の accepted Multi-point Path / L / U / Landing / lifecycle contract を壊さず、Turn Foundation を Winder / 廻り段および arbitrary-angle Turn / Landing へ拡張する。

---

## 1. Purpose

Build 07-E は、Build 07-D までに成立した Straight / L / U / Multi-point Landing Stair を維持したまま、日本住宅で一般的に使われる廻り段と、変形住宅で必要になる90°以外の折れ曲がり階段を **1つの Managed Stair** として生成・編集できる production foundation を完成させる Build である。

中心目的は次の10点とする。

1. 07-D の `TurnSpec` / Multi-point / Flight foundation を再利用し、`WINDER` turn mode を追加する。
2. 90° L字 Winder を production 対応する。
3. U字 / コの字の180°方向転換を、複数 Turn の Winder combination として production 対応する。
4. 2段廻り / 3段廻り / 4段廻りを標準 pattern として提供する。
5. BF-1 / BF-2 を均等角分割とは別の住宅用 pattern family として提供する。
6. Turn angle を exact 90°限定から一般化し、valid な arbitrary-angle Landing を production 対応する。
7. valid な arbitrary-angle Winder を、少なくとも equal-angle partition で production 対応する。
8. Winder step を含む overall riser / height distribution を Stair 全体で一貫させる。
9. `STEPPED_CLOSED` / `SLOPED_CLOSED` / Side Board を Winderへ継続し、とくに `SLOPED_CLOSED` は水平Landing plateauを挟まない連続した廻り下面を作る。
10. 07-E完了時点で一般住宅の直線＋折れ曲がり階段の主要ゴールとし、07-F / 07-Gを保留して08-A / 08-Bへ進める状態にする。

07-E は建築基準法適合判定ソフトを作る Build ではない。既存住宅・古い木造住宅の狭い階段もモデリング対象とし、法規上の推奨寸法と geometry validity を分離する。

---

## 2. Accepted baseline

07-E は以下を baseline とする。

- Build 05-B — Wall System — ACCEPTED
- Build 06-A / 06-B / 06-C — Finish system — ACCEPTED
- Build 07-A — Stair Core + Straight — ACCEPTED
- Build 07-B — Standard Residential Straight Stair — ACCEPTED
- Build 07-C — Sloped Closed Underside + Straight Finish Variants — ACCEPTED
- Build 07-D — Multi-point Path + L / U + Landing — overall ACCEPTED
- `BUILD_07_D_SPECIFICATION.md`
- `BUILD_07_D_ACCEPTANCE_RECORD.md`
- `DEVELOPMENT_WORKFLOW.md`
- `ROADMAP.md`

07-E specification baseline main:

```text
commit 4e46e04b9f3813810d2707ae9a773fd3f98fe9f9
tree   0db32165ec527869c19781e63f4ab783703c8539
```

07-D exact Stage-4 runtime-tested revision remains regression authority:

```text
commit 6c8cd05e7a854a28c1396a26b4282bb6ecbc052b
tree   f4c7b338560b688577314d297e422bd248e6554f
```

Existing 07-D saved Stair must not silently change merely because 07-E is installed.

---

## 3. Roadmap position

```text
07-A  Stair Core + Straight                         ACCEPTED
  ↓
07-B  Standard Residential Straight                ACCEPTED
  ↓
07-C  Sloped Closed Underside / Finish Variants    ACCEPTED
  ↓
07-D  Multi-point L / U + Landing                   ACCEPTED
  ↓
07-E  Winder + arbitrary-angle Turn / Landing       CURRENT
  ↓
07-F  HOLD
07-G  HOLD / Optional Backlog
  ↓
08-A  Minimal Room / Boundary + Floor
  ↓
08-B  Ceiling + Void / Hole
  ↓
Known Issue 8.5 correction
  ↓
Integration Core
```

07-E Acceptance後は 07-F / 07-G を一旦保留し、08-A / 08-B と早期一室Core統合試験を優先する。

---

## 4. Add-on identification

07-E production implementation:

```text
version = (0, 7, 4)
description = "Build 07-E: Winder + Arbitrary-angle Turn/Landing"
```

Stage途中の Candidate も 07-E production code を含む場合は同じ Build identity を使用してよい。

---

## 5. Core compatibility rule

07-E は既存 Stair を別方式へ作り直す Build ではない。

必須：

- schema-1 BASIC Straight を load しただけで変更しない。
- schema-2 07-B Straight を load しただけで変更しない。
- schema-3 07-C Straight を load しただけで変更しない。
- schema-4 07-D L / U / Landing を load しただけで変更しない。
- existing exact-90° Landing は 07-E install 時に Winderへ自動変換しない。
- ordinary Regenerate で accepted 07-D Landing geometry / allocation / Material / IDs を変更しない。
- 07-E Turn resolver のために legacy Straight / 07-D Landing resolver を破壊的に置換しない。

推奨：

```text
legacy Straight resolver          preserve
07-D schema-4 Landing resolver    preserve
07-E schema-5 generalized Turn    add beside / above accepted foundation
```

---

## 6. Managed Stair invariant

07-Eでも基本は：

```text
1 Managed Stair = 1 Blender Mesh Object
```

内部では Flight / Landing / Winder / Tread / Riser / Underbody / Side Board を複数 fragment として生成してよい。

Normal transform：

```text
Location = (0,0,0)
Rotation = (0,0,0)
Scale    = (1,1,1)
```

Canonical data → Derived Geometry を維持し、生成 Mesh から Turn pattern / Winder step / Path を逆推定しない。

---

## 7. Schema policy

07-E current schema:

```text
schema = 5
```

```text
schema 1 = BASIC legacy
schema 2 = 07-B Residential
schema 3 = 07-C Residential Straight
schema 4 = 07-D Multi-point / Landing
schema 5 = 07-E Winder / generalized Turn
```

Existing schema-1/2/3/4 Stair は load 時に自動 upgrade しない。

schema 5へ移行する例：

- Turn mode を `LANDING -> WINDER` へ変更
- new 07-E Winder pattern state を保存
- exact-90°以外の generalized Landing state を commit
- 07-E compact U Winder group state を保存

schema-4 exact-90° Landing を単に Regenerate / Reverse / Material editするだけなら schema 4 のまま維持する。

---

## 8. Canonical Turn model

07-DのTurn anchorを拡張する。

概念：

```text
TurnSpec
├ turn_id
├ path_point_id
├ turn_mode                LANDING | WINDER
├ winder_pattern           NONE | EQUAL_2 | EQUAL_3 | EQUAL_4 | BF_1 | BF_2
├ winder_step_count        derived / explicit canonical value
├ winder_partition_rule    NONE | EQUAL_ANGLE | BF_1 | BF_2
└ optional future partition parameters
```

Turn angle自体はPath geometryから導出する。

```text
incoming direction
+
outgoing direction
↓
signed turn angle theta
```

同じ情報を `turn_angle` として重複canonical保存しないことを基本とする。必要ならdiagnostic / cached derived valueとして扱う。

Turnは persistent `turn_id` と `path_point_id` でPath anchorへ結び付け、Object名や表示indexだけに依存しない。

---

## 9. Turn angle generalization

07-D productionでは exact ±90°のみだったが、07-Eでは single Turn を一般化する。

### 9.1 Supported concept

```text
0° < abs(theta) < 180°
```

ただし、0°近傍のcollinear point、180°近傍のsingle-point reversal、数値的に不安定な角度はgeometry validationでrejectできる。

Exact 180° reversalを1つのTurn anchorだけで無理に解決しない。U字 / コの字は既存Multi-point foundation上の2 Turnを使う。

### 9.2 Shift 15°との関係

07-D accepted Shift 15°は **操作補助** として維持する。

```text
Shift OFF = free angle
Shift ON  = nearest 15° candidate
```

ただし production Turn angle を15°刻みに限定しない。

数値Path編集またはfree mouse Pathから、geometryがvalidなら45° / 60° / 75° / 105°に限らず、63°等の任意角も扱えるArchitectureとする。

### 9.3 Existing guide compatibility

X/Y / extension / 90° / parallel guide は維持する。

90° guideは便利なcandidateであり、07-Eでは90°へ強制補正するruleではない。

---

## 10. 90° L Winder production scope

L字は1 Turnで約90°方向転換する代表caseとする。

07-E standard production pattern：

```text
2段廻り
3段廻り
4段廻り
BF-1
BF-2
```

2 / 3 / 4段廻りは equal-angle familyを基本とする。

```text
90° / 2 = 45°
90° / 3 = 30°
90° / 4 = 22.5°
```

ただし内部generatorを「3段なら必ず30°」のhard-coded presetへ固定しない。

---

## 11. Equal-angle Winder contract

Standard equal-angle Winder：

```text
step_count = n
turn sweep = theta
partition angle = theta / n
```

例：

```text
90°  / 2 = 45°
90°  / 3 = 30°
90°  / 4 = 22.5°

180° / 2 = 90°
180° / 3 = 60°
180° / 4 = 45°
180° / 5 = 36°
180° / 6 = 30°
```

後半の180°表はWinder angle subdivisionの数学的参考とする。JHMのU字productionは原則として2 Turnの組合せとして解決するため、single Turnへ180°fanを直接押し込む意味ではない。

`winder_step_count` と `winder_partition_rule` は意味上分離する。

---

## 12. BF-1 / BF-2 pattern family

BF-1 / BF-2 は equal-angle 2/3/4とは別pattern identityとする。

目的：住宅階段で使われる、Turn領域内の分割線位置を均等角から偏らせた廻り方を再現する。

Canonical identity：

```text
winder_pattern = BF_1 | BF_2
winder_partition_rule = BF_1 | BF_2
```

BF patternは「何段だから何度」として推測しない。

**DRAFT OPEN ITEM — FINAL化前に必要：**

- BF-1のnormalized plan construction
- BF-2のnormalized plan construction
- reference pivot / split ray / edge-intersection rule
- Reverse / left-turn / right-turn時のmirror rule

を図またはnormalized coordinate ruleで明文化する。

画像だけから法規上の意味や略称を推測して実装しない。

---

## 13. Winder plan geometry foundation

Winder planは fixed 900mm square を前提にしない。

Input：

```text
Path Turn anchor T
incoming unit direction a
outgoing unit direction b
stair_width w
signed turn theta
partition rule
```

Derived concept：

1. incoming / outgoing centerline corridor を width `w` でoffsetする。
2. inside / outside boundaryを解決する。
3. 有効なTurn envelope polygonを作る。
4. inside boundary交点またはderived pivotをWinder division originとして解決する。
5. partition ruleからdivision boundariesを生成する。
6. boundariesをTurn envelopeへclipする。
7. ordered tread polygonsを作る。
8. overlap / gap / self-intersection / zero-areaをvalidationする。

90° equal-angleでは、一般的な平面図のようにinside corner側から分割rayが広がる外観をproduction targetとする。

---

## 14. Stair width / legacy-house policy

07-E core geometry生成は現行法規の固定minimumへhard-codeしない。

必須：

- `stair_width = 900 mm` を前提にしない。
- 750 / 800 mm等へ変更しただけでWinderをrejectしない。
- 参考図にある300 mm / 150 mm / 85 mm等をabsolute geometry minimumとして固定しない。
- 古い木造住宅の狭いWinderも、数学的・Mesh的に成立する限りモデリングできる方向とする。
- width変更時はTurn envelope / tread polygon / underside / boardを同じcanonical widthから再解決する。

本Addonは法規適合判定ソフトではない。

将来optional advisory validationを追加してもよいが、core production gateと分離する。

---

## 15. Geometry validation policy

### 15.1 ERROR / reject

数学的またはMesh的に成立しない場合はatomic rejectする。

最低限：

- non-finite coordinate
- adjacent Path collapse
- unsupported single-point reversal
- invalid / non-positive Turn envelope area
- tread polygon self-intersection
- adjacent Winder tread positive-area overlap
- unintended gap in required walking surface coverage
- zero-area / near-zero-area polygon
- division order reversal
- partition rayが必要なboundaryへ交差しない
- Flight / Turn cutbackが成立しない
- Winder regionとunrelated Path segmentが自己交差する
- unsupported overlapping Turn regions
- underside / Side Board closureを生成できないcritical geometry

ERROR時はcanonical / Mesh / Materials / IDsをpartial commitしない。

### 15.2 WARNING / allow

Geometryとして成立しているが、非常に狭い / 急 / unusualなcaseはproduction可能とする。

例：

- narrow tread region
- old-house-like tight Winder
- unusually small inner walking width
- steep but existing accepted Stair parameters内で成立するcase

WARNINGは法規適合 / 不適合を断定しない。

---

## 16. Winder rise / step ownership

Winder stepはplan-only decorationではない。各Winder stepは実際のrise sequenceへ参加する。

Stair全体：

```text
N = overall riser_count
h = floor_to_floor / N
```

07-Eではphysical rise eventを、straight FlightまたはWinder transitionのどちらか一方へownershipさせる。

```text
sum(straight-flight rise events)
+
sum(winder rise events)
=
N
```

同じriseをFlight末端とWinder先頭で二重countしない。

Final upper floorは07-A〜07-D同様、追加の独立tread / extra riserとして数えない。

---

## 17. Winder step count and riser distribution

Winder pattern選択が2 / 3 / 4段なら、そのTurnが消費するWinder rise event countをcanonicalに確定する。

例：

```text
Turn 1 pattern = EQUAL_3
→ Turn 1 Winder steps = 3
```

AUTO distribution：

```text
overall N
- fixed Winder step counts
= remaining straight-flight rise budget
```

を基本conceptとし、remaining budgetをeffective straight runsへdeterministicに配分する。

ただしboundary ownershipの詳細はpure resolverで一意に定義し、Flight/Winder joinでriseを重複させないことを最優先する。

MANUAL distributionは07-Dの物理Flight allocationを保持しつつ、07-EではWinder step countとの整合をvalidationする。

仕様上必要ならUIを：

```text
Overall risers
Turn 1 Winder steps
Turn 2 Winder steps
Straight Flight resolved allocation
```

として見える化する。

---

## 18. AUTO / MANUAL contract extension

07-Dの `AUTO / MANUAL` authorityを維持する。

### AUTO

- Winder step count / patternを先に確定。
- remaining physical rise budgetをstraight flightsへdeterministic allocation。
- Path / width / Turn pattern変更時にcandidateを再解決。
- 全体sum invariantを満たした場合のみcommit。

### MANUAL

- user指定のstraight Flight countsを保持する。
- TurnのWinder step countを勝手に変更しない。
- sum invariantが壊れた場合は自動補正せずreject / rollback。
- AUTO→MANUALはcurrent resolved stateを初期値として引き継ぐ。

07-E implementationで必要なら、07-Dのallocation representationをschema-5用に拡張する。ただしschema-4 saved allocationをload時に書き換えない。

---

## 19. U / コの字 = overall 180° direction change

本Specificationでは、一般住宅のU字 / コの字階段を「overall 180°方向転換」と呼ぶ。

既存07-D U foundation：

```text
P0 -> P1 -> P2 -> P3
       T1    T2
```

通常は2つの約90° Turnを持つ。

07-Eでは **Turn 1 / Turn 2を個別にWinder設定**できることを基本とする。

例：

```text
Turn 1 = 2段廻り
Turn 2 = 3段廻り
```

```text
Turn 1 = BF-1
Turn 2 = 3段廻り
```

これによりU字用の全組み合わせを別presetとして大量登録しない。

---

## 20. Compact U Winder resolver

一般住宅のU字廻りでは、2つのTurn areaが近接し、middle segmentに通常のstraight treadを十分置かないcompact caseがある。

07-E productionではこのcaseを単純な「Flightが短いのでreject」で終わらせず、**supported compact U pair** として解決できることを目標とする。

Concept：

```text
Turn 1
+
short / transition middle span
+
Turn 2
↓
Composite U Winder Group
```

Canonical authorityは元のPath points / Turn IDs / each Turn patternを維持する。

Derived `U Winder Group` はgeometry resolutionのためのstructureであり、既存point IDsを破壊してsingle fake Turnへ置換しない。

Compact Uではmiddle spanにordinary straight treadが0枚でも成立するlayoutを許可できるが、rise ownership / tread coverage / side-board / underside continuityを明示的に解決する。

Separated Uでmiddle Flightが十分長い場合はordinary Flight + two Winder turnsとして扱える。

---

## 21. Arbitrary-angle Landing

07-Eでは `LANDING` も exact 90°限定から拡張する。

Input：

```text
incoming corridor
outgoing corridor
stair_width
Turn anchor
```

Derived Landingは、corridor boundaryのintersection / unionから有効なTurn polygonを解決する。

90°時は07-D accepted nominal `w x w` appearanceと互換になること。

Oblique Landingではfixed squareを無理に回転させるのではなく、incoming / outgoing width corridorを自然につなぐpolygonを生成する。

Landing top elevation / Material / underside ownershipは07-D contractを継承する。

---

## 22. Arbitrary-angle Winder

Arbitrary-angle Winder production minimumは `EQUAL_ANGLE` とする。

```text
Turn theta
Winder step count n
→ theta / n partition
```

Winder step count UIはまず2 / 3 / 4を基本とする。

BF-1 / BF-2は90°住宅patternとしてproduction対応し、arbitrary angleへ一般化することは07-E必須にしない。

Arbitrary-angle Winderでも：

- tread polygons ordered
- no overlap
- no self-intersection
- rise sequence exact
- closed underside / board対応Stageではclosure valid

を満たす。

---

## 23. Turn mode UX

07-E新規 residential Multi-point Stair のTurn defaultはRoadmap方針に従い `WINDER` を基本案とする。

UIでは各Turnを個別に選択可能にする。

例：

```text
Turn 1
Mode:    WINDER | LANDING
Pattern: 2段 | 3段 | 4段 | BF-1 | BF-2

Turn 2
Mode:    WINDER | LANDING
Pattern: 2段 | 3段 | 4段 | BF-1 | BF-2
```

Landing選択時はPattern UIを無効化 / 非表示にする。

Existing schema-4 Landingはload時にUI defaultの影響を受けない。

---

## 24. Winder pattern thumbnail UI

Patternは文字Dropdownだけでなく、平面形状を理解しやすいthumbnail / icon selectionを優先候補とする。

少なくとも：

```text
2段廻り
3段廻り
4段廻り
BF-1
BF-2
```

を視覚的に区別できること。

06-C Profile Thumbnail UIのarchitectureを再利用してよいが、Winder iconをProject Custom Profile libraryへ混在させない。

Thumbnailはpattern identityを選ぶUIであり、canonical geometry authorityではない。

---

## 25. Tread / Riser geometry

Winder treadはTurn envelope内のordered polygonとして生成する。

必須：

- tread thicknessは既存Residential fieldを継承。
- riser thicknessも既存fieldを継承。
- each Winder tread top elevationはrise sequenceからexactに決定。
- adjacent tread間のvertical riser boardを生成する。
- tread front overhang / basic front-edge treatmentはgeometryが成立する範囲で既存07-C contractを適用。
- Winder内側でnosingが自己交差 / reverseする場合はcandidate validationでrejectまたは対応範囲を明示。

Winder treadのfront edgeは各stepの進行方向 / boundary lineから決定し、Straightの単一local X axisをそのまま全Turnへ使わない。

---

## 26. STEPPED_CLOSED Winder underside

`STEPPED_CLOSED` はWinderでもclosed invariantを維持する。

下から見たとき：

- tread backsideを露出しない
- riser backsideを露出しない
- internal cavityを見せない
- Winder stepに追従するhorizontal / vertical closureが連続
- Flight ↔ Winder ↔ Flight joinに大きなgap / spikeを作らない

Winder footprintが扇形 / irregular polygonでも、単純なStraight boxの重ね合わせで内部重複を大量生成しない。

---

## 27. Continuous SLOPED_CLOSED Winder soffit

07-Eの重要production target。

Landing case：

```text
Flight slope
→ horizontal Landing underside
→ Flight slope
```

Winder caseでは水平Landing plateauを入れない。

```text
Lower Flight sloped soffit
        ↓ continuous height progression
Winder sloped / twisted soffit
        ↓
Upper Flight sloped soffit
```

要求：

- lower Flight boundaryとWinder soffitがposition-continuous。
- Winder soffitとupper Flight boundaryがposition-continuous。
- Turn途中で不要なhorizontal plateauを作らない。
- plan directionが曲がるためsingle infinite planeである必要はない。
- piecewise planar / triangulated surfaceでよい。
- visible resultとして勾配下面が曲がりながら連続して見えること。
- C0 continuityを必須とし、C1 tangent continuityは07-E必須にしない。
- underside thickness / body depth contractは07-Cを継承。
- closed body invariantを維持する。

推奨：Winder progression parameterとinside/outside boundary stationを使い、順序づけられたlower-surface stripsを生成する。

---

## 28. Side Board continuation at Winder

`STEPPED` / `SLOPED` Side BoardをWinderへ継続する。

必須：

- left/right meaningはuphill traversalに対して安定。
- Turnで突然side swapしない。
- inside / outside board pathをWinder envelope boundaryから解決。
- Flight ↔ Winder joinでlarge gap / duplicate spikeを作らない。
- compact U中心側でboard同士が不正交差しない。
- outer boardはTurn外周に沿って自然に継続。
- inner boardはpivot / newel-like tight regionで必要ならtrim / segmented joinを許可。
- Material role = `SIDE_BOARD`。

1巨大polygonより、deterministic fragments + clean visible joinを優先する。

---

## 29. Material contract

既存rolesを維持する。

```text
BASE
TREAD
RISER
UNDERSIDE
SIDE_BOARD
```

新規 `WINDER` Material roleは追加しない。

```text
Winder walking treads = TREAD
Winder risers         = RISER
Winder soffit/body    = UNDERSIDE
Winder side boards    = SIDE_BOARD
```

Regenerate / Path edit / Turn pattern edit / Reverse / Repair / Save-Reopen / Undo-Redoでpointer / slot semanticsを保持する。

---

## 30. Reverse ascent

Reverseはcanonical Path orderを書き換えず、traversalのみ反転する。

```text
FORWARD: P0 -> ... -> Pn
REVERSE: Pn -> ... -> P0
```

Winder plan footprintは同じXY routeを使用し、step elevation sequenceを反転する。

BF / equal-angle patternはReverseで別pattern identityへ勝手に変換しない。

必要なgeometry mirror / boundary orderはderived resolverで処理する。

Physical Turn pattern assignmentは同じ `turn_id` に保持する。

---

## 31. Turn edit / Path edit

07-D accepted START / END / TURN mouse relocationを維持する。

Point move後：

```text
candidate Path
↓
turn angle resolve
↓
turn envelope / pattern resolve
↓
rise allocation
↓
Flight + Winder + underside + board prepare
↓
validation
↓
atomic commit
```

Arbitrary-angle Turnを含むため、point moveで90°から外れたことだけを理由にrejectしない。

Shift 15° / X/Y / extension / 90° / parallel guideは継続する。

ESC / RMB cancelはcanonical / Mesh / Material / IDsを変更しない。

---

## 32. Numeric edit

Numeric Path editも同じschema-5 transaction pathを使用する。

ユーザーが任意角を精密入力できること。

Turn angle fieldを別入力してPathと矛盾させるUIは作らない。angleはPathからderived表示することを基本とする。

UIへderived valueを表示してよい。

例：

```text
Turn 1 Angle: 63.4° Left
Turn 2 Angle: 91.2° Right
```

---

## 33. Transaction / rollback contract

07-D `_transactional_update` 原則を継承する。

Scene mutation前に最低限prepare：

- canonical Path validation
- generalized Turn angle
- Turn envelope
- Landing / Winder mode
- Winder pattern / partition
- Winder tread polygons
- rise ownership / allocation
- straight Flight effective run
- Tread / Riser
- STEPPED_CLOSED / SLOPED_CLOSED
- Side Board
- Material plan
- topology validation where practical

Rollback target：

- old Mesh datablock
- path_points / point IDs
- Turn IDs / modes / patterns
- distribution mode / allocations
- dimensions
- ascent direction
- 07-C Residential fields
- Materials / slots
- Stair ID
- Object Transform

失敗時にpartial Winder stateを残さない。

---

## 34. Diagnose / Repair

Existing recoverable policyを継承：

- ID_MISSING
- ID_CONFLICT
- TRANSFORM_CHANGED
- GEOMETRY_MISSING

schema-5 canonicalがinvalidな場合、Repairが推測してpattern / angle / countsを変更しない。

Geometry missing / transform changedはsame valid canonicalから再生成。

Duplicate IDはStair IDだけを変更。

Repair時にWinder step count / Turn pattern / Path / Materials / allocationを保持する。

---

## 35. Save / reopen / Undo / Redo

07-E Acceptance必須。

Save / fully exit Blender / reopen後に保持：

- schema 5
- Stair ID
- Path points / point IDs
- Turn IDs
- Turn mode
- Winder pattern / step count / partition rule
- AUTO / MANUAL state
- resolved allocation authority
- Materials
- ascent direction
- Residential fields
- identity Transform

Undo / Redoは最低限：

- LANDING ↔ WINDER change
- 2/3/4/BF pattern change
- Path point move causing arbitrary angle change
- Reverse
- Material edit

をrepresentativeに確認する。

---

## 36. Finalize / Delete / lifecycle

07-D contractを維持する。

Finalize：

```text
Managed Stair
↓
ordinary editable Mesh
↓
JHM management ends
```

Deleteはactive managed Stair only。

Winderだから別Objectを選択削除するようなlifecycleへ変更しない。

Wall / Finish / Floor-like unrelated objectsをmutationしない。

---

## 37. Explicit non-scope

07-Eでは必須にしない：

- spiral / helical stair
- curved Flight centerline
- freehand curved Winder edge
- userが各Winder split lineを1本ずつ自由編集するcustom partition editor
- automatic building-code compliance judgment
- legal pass/fail表示
- variable stair width along a single Flight
- non-uniform riser heights within one Stair
- Riser OFF / Underside NONE / open support variants（07-F）
- sawtooth / center support（07-F）
- handrail / newel / baluster
- separate Winder Material role
- automatic Wall / Floor / Room attachment
- automatic Stair opening / Floor Boolean
- production UV guarantee

古い住宅の狭いgeometryを「法規値未満だから非対応」とすることも07-Eの目的ではない。

---

## 38. Stage 1 — Winder canonical foundation + first visible 90° L

目的：上面形状を最初に固め、下面・側板問題と分離する。

Implementation minimum：

- identity 0.7.4
- schema-5 foundation
- schema-1/2/3/4 regression
- `WINDER` Turn mode
- generalized Turn angle pure resolver foundation
- 90° L Winder
- EQUAL_2 / EQUAL_3 / EQUAL_4
- Turn envelope / pivot / partition
- Winder tread + riser production geometry
- Winder rise ownership
- AUTO allocation extension
- one Managed Mesh
- Material roles compatible
- transaction / rollback

Stage 1ではBF / U compact / arbitrary-angle / final underside / Side Boardを完成させなくてよい。

### Stage 1 runtime focus

- existing 07-D L Landing unchanged
- new L Winder 2/3/4 visually correct from top
- width 900 / 800 / 750 representative regeneration
- stair width変更だけでunnecessary rejectしない
- total rise exact
- Winder step elevations exact
- no tread overlap / zero-area
- Reverse basic
- Save/reopen basic
- invalid partition rollback

---

## 39. Stage 2 — U / BF patterns + arbitrary-angle Turn

目的：07-E上面 / Path機能を完成。

Implementation：

- BF-1 / BF-2 exact normalized construction
- thumbnail / icon pattern selection
- Turn 1 / Turn 2 independent pattern
- U / overall 180° Winder combination
- compact U Winder group
- separated U Winder
- arbitrary-angle Landing
- arbitrary-angle equal-angle Winder
- free-angle point relocation
- 15° Shift remains convenience only
- AUTO / MANUAL full Winder allocation
- deterministic multiple-turn regeneration

### Stage 2 runtime focus

- L 2/3/4/BF-1/BF-2
- U examples such as 2+3, BF-1+3
- compact U no false short-flight rejection
- Turn 1 / Turn 2 individual edit
- 45° Landing
- non-15-multiple oblique Landing from numeric Path
- arbitrary-angle Winder representative
- left / right turn mirror
- FORWARD / REVERSE
- width 750 / 800 / 900 representative
- invalid self-intersection / overlap rollback

---

## 40. Stage 3 — Closed underside + Side Board production finish

目的：07-Dで苦労した下面 / 側板を、上面Winder geometry確定後に独立して完成する。

Implementation：

- STEPPED_CLOSED Winder continuation
- continuous SLOPED_CLOSED Winder soffit
- Flight ↔ Winder ↔ Flight closure
- compact U underside
- STEPPED Side Board continuation
- SLOPED Side Board continuation
- inner / outer boundary mapping
- Material lifecycle
- Reverse
- Regenerate / Repair
- topology cleanup

### Stage 3 runtime focus

- SLOPED_CLOSEDに水平Landing plateauが残らない
- visible slope progression continuous through Winder
- no cavity / spike / giant filler prism
- inside / outside board no side-swap
- compact U center no board collision
- boards OFFでもbody CLOSED
- Material roles exact
- width 750 / 800 / 900
- L / U / arbitrary-angle representative

---

## 41. Stage 4 — lifecycle / full regression / practical acceptance

Final acceptance must cover：

- Candidate identity
- schema-1 / 2 / 3 / 4 regression
- schema-5 L / U / arbitrary-angle persistence
- 2 / 3 / 4 / BF patterns persistence
- AUTO / MANUAL persistence
- Undo / Redo
- invalid rollback
- Geometry Repair
- Transform Repair
- duplicate ID Repair
- Material lifecycle
- Reverse
- Finalize
- active-only Delete
- abnormal Delete
- Wall / Finish isolation
- practical Wall / Floor-like placement
- narrow-width old-house-like representative case
- topology finite / zero-area / boundary / nonmanifold
- deterministic repeated Regenerate
- full automated regression
- compileall
- git diff --check

07-E overall ACCEPTEDはStage 4完了後のみ。

---

## 42. Automated test architecture

Pure/testable logicをBlender modal codeから分離する。

最低限 pure test対象：

- signed turn angle
- generalized corridor intersection
- Turn envelope validity
- equal-angle partition
- BF-1 / BF-2 normalized partition
- tread polygon simple / area / overlap
- width-independent scaling
- Winder rise ownership
- overall riser invariant
- AUTO allocation with fixed Winder counts
- MANUAL validation
- compact U group resolution
- arbitrary-angle Landing polygon
- Reverse mapping
- schema compatibility
- deterministic geometry

Stageごとに dedicated `tests/test_build_07_e_stageN.py` を追加する。

Prior 07-A / 07-B / 07-C / 07-D suitesを regression target とする。

---

## 43. Runtime test policy

`DEVELOPMENT_WORKFLOW.md` を継承する。

原則：

```text
Console canonical evidence
+
必要箇所だけ目視
```

Undo / Redo：

```text
UI operation
↓
Ctrl+Z
↓
Ctrl+Shift+Z
↓
then Console
```

Winder tread shape / BF pattern / underside continuity / Side Board visible joinは目視が必要。

Canonical pattern / IDs / angle / allocations / topology / MaterialsはConsole evidenceを主とする。

---

## 44. Acceptance principles

07-Eは以下を満たした場合のみoverall ACCEPTEDとする。

1. Existing 07-D Straight / L / U / Landingを壊さない。
2. 90° L Winder 2/3/4段が安定して生成できる。
3. BF-1 / BF-2が明文化された同一ruleからdeterministicに生成される。
4. U / overall 180° direction-change WinderをTurn combinationとして作れる。
5. compact Uで不要なshort-middle-flight rejectを起こさない。
6. arbitrary-angle Landingをproduction生成できる。
7. arbitrary-angle equal-angle Winderをrepresentative caseで生成できる。
8. width 900に固定せず、750 / 800等でもgeometryがvalidなら作れる。
9. law-like寸法をcore reject thresholdへhard-codeしない。
10. invalid geometryはclear errorでatomic rollbackする。
11. Winder stepsを含めoverall rise / riser invariantがexactである。
12. `SLOPED_CLOSED`がWinder through-turnで連続したclosed soffitとなる。
13. `STEPPED_CLOSED` / Side BoardもWinderで重大なgap / spike / cavityを作らない。
14. Save / reopen / Undo / Redo / Repair / Finalize / Delete / Materialsが成立する。
15. Wall / Finishへ回帰を起こさない。
16. practical residential placementで重大な破綻がない。

---

## 45. Open items before FINAL

このDRAFTをFINAL / IMPLEMENTATION AUTHORITYへ上げる前に最低限以下を確定する。

1. **BF-1 normalized construction**
2. **BF-2 normalized construction**
3. BF-1 / BF-2のleft/right / Reverse mirror rule
4. compact Uでmiddle spanをどこまで0 ordinary treadとして許可するか
5. Winder step countとstraight Flight allocationのboundary ownership formula
6. arbitrary-angle Landing envelopeのexact polygon rule
7. arbitrary-angle Winderのsupported angle epsilon / singularity rule
8. thumbnail UIの最低production shape

これらを曖昧なままCodexへproduction implementationを依頼しない。

---

## 46. Final implementation rule

07-Eでは、07-D Stage 2のように上面・下面・側板の問題を同時に抱えない。

優先順位：

```text
accepted 07-D compatibility
    ↓
Winder canonical / plan geometry
    ↓
90° L 2/3/4
    ↓
BF + U / compact U
    ↓
arbitrary-angle Landing / Winder
    ↓
rise distribution
    ↓
closed underside
    ↓
Side Board
    ↓
full lifecycle / practical test
```

上面plan geometryがruntimeでacceptedになる前に、複雑なSLOPED_CLOSED / Side Board correctionへ進まない。

ユーザーのBlender runtime visual reviewでWinder踏板形状・BF pattern・compact U外観に問題があれば、Stage acceptance前にSpecification addendum / correctionとして修正する。

07-E Acceptance完了後はRoadmapどおり07-F / 07-Gを保留し、08-A / 08-Bへ進む。