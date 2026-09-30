# Japanese House Modeler — Development Roadmap

最終更新: 2026-09-30

この文書は、Blender 5.2 LTS 向け **Japanese House Modeler / 日本住宅モデラー** の今後の開発順序と、各Buildをまたいで維持する設計方針をまとめたロードマップである。

このロードマップは、各Buildの詳細仕様書そのものではない。詳細仕様は各 `BUILD_*_SPECIFICATION.md`、受け入れ結果は各 Acceptance Record を正とする。

---

## 1. Roadmap policy

この文書は**現在の開発計画**であり、固定された仕様ではない。

- 実装・Blender実機テスト・Architecture上の問題が見つかった場合、Build順序は変更できる。
- Accepted済みBuildを後から変更する場合は、互換性への影響を明示する。
- 詳細挙動は各 `BUILD_*_SPECIFICATION.md` を正とする。
- Accepted / NOT ACCEPTED の状態は各 Acceptance Record を正とする。
- RoadmapとAccepted済み仕様・Acceptance Recordが矛盾する場合、Accepted済み文書を優先する。
- 後続Buildの都合だけで、Accepted済みcanonical dataを安易に破壊・再定義しない。
- 新機能は可能な限り既存Foundationを再利用し、Buildごとに独立した場当たり実装を増やさない。

---

# 2. Project goal

本プロジェクトの目的は、BlenderをCAD/BIMへ置き換えることではない。

目的は、

> **日本住宅のリフォーム完成イメージや室内3Dパースを、寸法ベースで素早く組み立て、その後は通常のBlender編集へ移行できる制作補助ツールを作ること**

である。

重視するもの：

- 寸法入力による正確な初期生成
- 壁・巾木・廻り縁・階段・床・天井・建具などの面倒な初期モデリングを短縮
- 再生成可能なManaged状態
- 最終的には通常のBlender Object / Meshへ確定可能
- 手作業で十分簡単なものより、手作業負担の大きいものを優先
- BIMのような過剰な自動化やデータモデル化は避ける

---

# 3. Current status

現在の基準状態：

- **Build 05-B — ACCEPTED**
- **Build 05-C — BACKLOG**
- **Build 06-A — ACCEPTED**
- **Build 06-B — ACCEPTED**
- **Build 06-C — ACCEPTED**
- **Build 06-C overall — ACCEPTED**
- **Build 07-A — ACCEPTED**
- **Build 07-A overall — ACCEPTED**
- **Build 07-B — ACCEPTED**
- **Build 07-B overall — ACCEPTED**
- **Build 07-C — ACCEPTED**
- **Build 07-C overall — ACCEPTED**
- **Build 07-D — ACCEPTED**
- **Build 07-D overall — ACCEPTED**
- **Build 07-E — NEXT / SPECIFICATION FINAL / IMPLEMENTATION NEXT**
- **Build 07-F — HOLD after 07-E**
- **Build 07-G — HOLD / OPTIONAL BACKLOG**
- Current accepted add-on version: **0.7.3**
- Build 07-D final identification: `Build 07-D: Multi-point Path + L/U + Landing`
- Build 07-E Specification: **FINAL / IMPLEMENTATION AUTHORITY**

現時点で、Wall System、Finish Attachment Foundation、Baseboard、Crown Moulding、standalone Managed Stair Core、Standard Residential Straight Stair、07-C Straight Stair Finish Variants、および07-D Multi-point L/U + Landingまでの基盤が成立している。

07-D完了後の次の主要開発は **Build 07-E — Winder / 廻り段 + arbitrary-angle Turn / Landing extension** とし、仕様書は第三者レビュー3回を経てFINAL化済み。次はCodexによるStage 1 implementationへ進む。

Build 07は07-Eを一般住宅の直線＋折れ曲がり階段の主要ゴールとし、07-E Acceptance後はいったん07-F / 07-Gを保留して08-A / 08-Bへ進む。08-B完了後、既知問題 8.5 のFinish endpoint mismatchを修正してから、Wall / Finish / Floor / Ceiling / Stair / Voidを使う早期一室Core統合試験を実施する。

Door / Window / Boolean / Finish Exclusionを含む完全な一室統合試験はBuild 09 minimal完了後にも実施する。

---

# 4. Final development order

| Build | 内容 | 状態 |
|---|---|---|
| **05-B** | Wall System完成 | **DONE / ACCEPTED** |
| **05-C** | Wall再統合 | **BACKLOG** |
| **06-A** | Finish Attachment Foundation | **DONE / ACCEPTED** |
| **06-B** | Baseboard / 巾木 | **DONE / ACCEPTED** |
| **06-C** | Crown Moulding / 廻り縁 + Profile Thumbnail UI | **DONE / ACCEPTED** |
| **07-A** | Stair Core + Top-view 2-point Straight Stair | **DONE / ACCEPTED** |
| **07-B** | Standard Residential Straight Stair + Stepped Closed Underside + Side Boards | **DONE / ACCEPTED** |
| **07-C** | Sloped Closed Underside + Straight Stair Finish Variants | **DONE / ACCEPTED** |
| **07-D** | Multi-point Path + L/U + Landing | **DONE / ACCEPTED** |
| **07-E** | Winder / 廻り段 + arbitrary-angle Turn / Landing | **NEXT / SPEC FINAL** |
| **07-F** | Open / Support Variants | **HOLD after 07-E** |
| **07-G** | Optional Stair Detail Expansion | **HOLD / Optional Backlog** |
| **08-A** | Minimal Room / Boundary + Floor | Planned after 07-E |
| **08-B** | Ceiling + 吹抜け / 穴の基本 | Planned after 08-A |
| **8.5 Correction** | Closed Wall layout Finish endpoint mismatch修正 | Planned after 08-B |
| **Integration Core** | Wall / Finish / Floor / Ceiling / Stair / Void 一室Core統合試験 | Planned after 8.5 Correction |
| **09-A** | Window / Door Asset Root + Wall Anchor | Planned |
| **09-B** | Live Boolean Cutter | Planned |
| **09-C** | Finish Exclusion連携 | Planned |
| **Integration 1** | Door / Windowを含む一室フル実務統合試験 | Planned after 09 minimal |
| **10** | Production Hardening / UX / Compatibility / Full Regression | Planned |

---

# 5. Why this order

## 5.1 Finishを先に完成させた理由

Build 06では単なるCurve生成ではなく、

> **Wallのどの面・どの区間に、何を、どの基準高さで配置するか**

を永続化する共通Attachment Foundationを作った。

これにより、

- Baseboard
- Crown Moulding
- 将来のChair Rail
- Opening exclusion
- その他のWall付属部材

を同じ考え方で扱える。

Build 06-A / 06-B / 06-CはAcceptance済みであり、このFoundationを今後のWall付属部材へ再利用する。

## 5.2 Build 07を08/09より先に進める理由

Floor / CeilingはBlender標準機能で比較的容易に手作業代替できる。Door / WindowもAsset配置とBooleanによる手動ワークフローが存在する。

一方、住宅階段は、

- 踏板
- 蹴込み板
- 蹴上 / 踏面
- 階高
- 側板
- 下面
- 方向転換
- 踊り場
- 廻り段
- 支持方式

を相互に整合させる必要があり、手作業負担が大きい。

また、本プロジェクトのStairは **Wall / Floor / Roomを必須参照としないstandalone Managed Object** とする。
そのため、Floor / Room実装を待たずに階段システムを進められる。

## 5.3 07-E後に08へ進む理由

07-DでMulti-point L/U + LandingまでAcceptance済みとなった。次の07-Eで一般住宅に多いWinder / 廻り段と、変形住宅へ対応するarbitrary-angle Turn / Landingを追加すれば、住宅階段本線として十分な実用チェックができる段階に達する。

そのため07-E後は07-F / 07-Gを一旦保留し、**一室統合試験を早期に実施するため08-A / 08-Bを優先**する。

```text
07-D ACCEPTED
↓
07-E Winder + arbitrary-angle Turn / Landing
↓
一般住宅階段としてpractical checkpoint
↓
07-F / 07-G HOLD
↓
08-A Room / Boundary + Floor
↓
08-B Ceiling + Void / Hole
↓
Known Issue 8.5 correction
↓
Integration Core
```

Integration CoreはDoor / Window完成を待たず、Wall / Finish / Floor / Ceiling / Stair / Voidの主要Foundationを一室で組み合わせ、Architecture上の問題を早く発見するための試験とする。

07-E Acceptanceでは、正式なIntegration Coreを待たず、手作業で用意したWall / Floor相当の簡易シーンへStairを配置して小規模な住宅パース実用確認を行う。

---

# 6. Architecture decisions carried forward

## 6.1 Canonical data first

原則：

```text
Canonical Data
    ↓
Derived Geometry
```

生成されたMesh / Curveそのものを正としない。

例：

```text
Wall canonical data
    ↓
Wall Mesh
```

```text
Finish Placement
    ↓
Path calculation
    ↓
Profile sweep
    ↓
Displayed geometry
```

## 6.2 Persistent Wall ID

Wall参照にBlender Object名を使用しない。

各WallはPersistent IDを持つ。

今後Wallを参照するもの：

- Baseboard
- Crown
- Window
- Door
- Opening
- その他Attachment

はPersistent Wall IDとWall上位置を基準にする。

`.blend` 内のWall参照は、既存Foundationの **Object Pointer + expected Persistent Wall ID** による整合性検証を維持する。Object名だけ、または重複したPersistent IDだけから参照先を推測しない。

## 6.3 Wall split dependency remap

Wall分割時、依存要素は新Wallへ追従できなければならない。

概念例：

```text
Wall A
0 ---------------- 4000
```

が、

```text
Wall A
0 ------ 1500

Wall B
1500 ----------- 4000
```

へ分割された場合、元Wallの2700mm位置を参照していた要素は、Wall B上の対応位置へ移される。

最低限必要な参照情報：

- Persistent Wall ID
- Wall上のdistance / parameter
- LEFT / RIGHT side
- 分割前後の区間対応

## 6.4 Wall自身に「室内側」を持たせない

間仕切りWallでは両側とも室内になり得る。

したがって、`Wall.interior_side = LEFT` のような固定属性は持たせない。

初期操作：

> ユーザーがWallのどちら側へ配置するか選択

将来：

> Roomに面するWall sideを自動選択

へ拡張する。

## 6.5 Split Wall continuation

物理的に分割されたWallを、Finish側では必要に応じて連続として扱う。

条件例：

```text
A.END == B.START
same line
same thickness
same height
Continuation-compatible topology
```

なら、`A + B` を一続きのFinish Pathとして扱える。

このため、Wallを常に物理的に再統合する必要はない。

---

# 7. Build 05-C — Wall merge backlog

05-Cは現在Backlog。

将来実装する場合も、自動でWallを合体させるより、

> **条件を満たす分割Wallをユーザーが明示操作で統合する**

方式を優先する。

理由：Wall統合時には将来、Opening、Finish、Material、Window / Door Anchor、Room Boundaryなどの参照移行が必要になる。

そのため、Finish / Openingなどの参照Foundationが固まる前に実装しない。

---

# 8. Build 06 — Finish Attachment architecture

## 8.1 Canonical Finish Placement

Finishは生成Curveではなく、Wallへの配置情報を正とする。

概念モデル：

```text
FinishRun
├ finish_id
├ finish_type
├ Profile identity
├ vertical reference
├ vertical offset
├ join policy
├ spans[]
├ exclusions[]
└ material assignment
```

Span概念：

```text
FinishSpan
├ wall_id
├ side = LEFT / RIGHT
├ start boundary
├ end boundary
├ traversal direction
└ order
```

生成：

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
Managed derived geometry
```

この順序を基本とし、Exclusionで消える区間に対して先にMiter等の角処理を確定しない。可視区間を確定した後に、各可視区間の角・自由端・BUTT / Miter等を解決する。

## 8.2 Build 06-A — Finish Attachment Foundation

**Status: ACCEPTED**

役割：

- Persistent Wall ID
- Wall side
- Wall上区間
- Wall split remap
- Finish Path
- floor / ceiling / absolute vertical reference
- exclusion foundation
- Profile foundation
- managed geometry
- Editable Mesh conversion

06-AはBaseboard専用ではなく、後続Finish用Foundation。

## 8.3 Build 06-B — Baseboard

**Status: ACCEPTED**

完成範囲：

- SIMPLE
- BEVEL
- ROUNDED
- limited Custom Profile
- POLY / BEZIER registration
- deterministic snapshot
- Manual Exclusion
- Partial placement
- LEFT / RIGHT
- FORWARD / REVERSE
- Miter
- BUTT
- Wall split tracking
- Material preservation
- Save / reopen
- Undo / Redo
- Editable Mesh conversion
- Legacy compatibility

Build 06-BはBaseboard production baseline。

## 8.4 Build 06-C — Crown Moulding

**Status: ACCEPTED**

06-B Foundationを再利用し、Crown MouldingおよびProfile Thumbnail UIを実装した。

Acceptance済み主要範囲：

- finish_type = CROWN
- Ceiling基準配置
- Crown用vertical reference
- LEFT / RIGHT
- FORWARD / REVERSE
- 90° / oblique Miter
- Partial placement
- Manual Exclusion
- Standard SIMPLE / BEVEL / ROUNDED
- Custom POLY / BEZIER
- Custom Profile snapshot persistence
- Profile Thumbnail browser
- Material persistence
- Editable Mesh conversion
- Save / reopen
- Undo / Redo
- Baseboard + Crown mixed regression
- bulk regeneration atomicity

Build 06-C overallはAcceptance済み。

## 8.5 Known Issue — Finish endpoint mismatch on closed Wall layout

**Status: OPEN / correction planned after 08-B**

Build 06-C acceptance後、**閉じたWall配置に沿って作成したBaseboard / Crown**で、端部付近の突出・不足が報告されている。

観察されている症状：

- BaseboardとCrownの両方で発生する。
- 閉じたWall配置で再現している。
- Finish端部の一方がcornerを越えて突き出す場合がある。
- 反対側では長さが不足し、cornerまで届かない場合がある。

現時点では以下を未調査とする。

```text
FinishRun自体がclosed pathなのか
複数Runなのか
Span境界がどこにあるのか
FORWARD / REVERSEとの関係
closed Wall topologyとの関係
原因がendpoint処理かcorner処理か
```

画像だけから原因を断定しない。

**このRoadmap更新では修正自体は行わない。** 修正タイミングを08-B完了後、Integration Core開始前に置く。

Build 06-C Acceptance Recordは受入時点の履歴として保持し、Correction / maintenance workとして原因調査・修正・regression testを行う。

調査時には可能な限り以下を保存する。

- 再現用 `.blend`
- 使用Build / Candidate / commit
- Baseboard / Crown
- Finish Profile
- 作成手順
- Wall topology
- FinishRun / Span / traversal状態
- 発生箇所のスクリーンショット

---

# 9. Profile Library contract

Profileは単なる輪郭ではない。

概念的には：

```text
Profile
├ profile_id
├ revision
├ schema_version
├ name
├ category
├ contour
├ origin
├ wall direction
├ vertical direction
├ nominal width
├ nominal height
├ shading intent
└ thumbnail metadata
```

重要：

> **Wall接触面・上下方向・室内側方向を曖昧にしない**

Custom Profile登録後に上下逆・裏返しが起こらない座標契約を維持する。

## 9.1 Custom Profile initial support

初期版は万能Curve importerにしない。

許可例：

- 2D
- single spline
- closed
- no self-intersection
- no hole
- supported POLY / BEZIER
- identity transform
- snapshot-based
- no live source dependency

今後必要になった場合のみ対応範囲を拡張する。

---

# 10. Editable Mesh contract

要求：

> **最終的に通常のBlender Objectとして自由編集できる出口を必ず持つ**

Managed状態ではCurve等を使用してよい。

共通操作：

```text
[編集可能Meshとして確定]
```

実行後：

```text
Managed Object
    ↓
Editable Mesh
    ↓
Add-on管理解除
```

ルール：

- 一方向変換
- Mesh確定後は自由編集可能
- Add-onは以後そのMeshを再生成しない
- 手編集Meshからcanonical parametersへ戻す逆変換は作らない

---

# 11. Material / UV / Modifier contract

Managed状態：

- canonical parameters → 保持
- Profile assignment → 保持
- Material assignment → 原則保持
- Custom Profile reference → 保持
- 手動Mesh編集 → 保持しない
- 任意Modifier → 原則保証しない
- UV → Buildごとに保証範囲を明文化

Editable Mesh確定後：

- Add-on管理解除
- Material / UV / Modifier / Edit Mode処理は通常Blender側管理

各Build仕様書で、**再生成時に何を保持し、何を捨てるか**を明記する。

---

# 12. Build 07 — Stair System

## 12.1 Final goal — fixed project target

Build 07の最終目標は、**日本の戸建て住宅で一般的に使われる直線・折れ曲がり階段を、トップビューでPathを指定して生成できるManaged Stair System** を構築することである。

最終操作イメージ：

```text
Top View

START
  ●
  │
  │
  ●────────●
           │
           │
           ●
             END
```

ユーザーは、始点、必要な折れ点、終点を順番にクリックする。

そのPathから、Straight flight、Landing、Winder / 廻り段を組み合わせ、**全体を1つのManaged Stairとして生成・編集できること**を最終目標とする。

L字 / U字presetの数値入力だけを最終操作にしない。
Wall作成に近いPath指定を主操作とする。

ただし、Pathだけでは曲がり部分の広さ・Landing / Winderの選択・Winder段数等を一意に決められない。

したがってMulti-point Stairでは、

```text
Path geometry
+
turn mode / turn parameters
+
stair dimensions
```

の組み合わせで確定する。

Addonは曖昧なPathから無理な形状を自動決定しない。

## 12.2 Standalone Stair contract

StairはWall / Room / Floor / Ceilingを必須依存としない。

完全な空SceneでもStair単体を生成できること。

Stair自身が少なくとも以下の高さ情報を持つ。

```text
base_z
floor_to_floor
```

将来Floor System完成後には、manual numeric height または optional Floor reference を選択できる方向へ拡張可能とする。

Floor参照は後付け可能なdependencyであり、Stair Coreの必須前提にしない。

### Upper arrival / future Floor connection contract

上階Floorと接続する場合、**上階Floorの仕上げ床面そのものをStairの最後の到達面として扱う**。

例：

```text
riser_count = 16
independent_tread_count = 15

15枚目の独立踏板
↓
16回目の蹴上
↓
上階Floor仕上げ面 = 16段目の到達面
```

したがって、上階Floorを「17段目」として追加で数えない。

07-Aでは上階Floor自体を生成しないが、Stairは将来接続用の **upper arrival interface** を持てるcanonical contractとする。

少なくとも概念上、

```text
upper_arrival_z
upper_arrival_plan_position
upper_arrival_width
```

を導出可能にしておく。

将来08のFloor Systemと接続した場合は、

```text
Stair upper_arrival_z
==
Upper Floor finished top surface Z
```

を基本契約とする。

住宅階段では、上階Floorの階段開口端にも最終段の段鼻に相当する縁・見切りが付く場合がある。
この **upper-floor edge nosing / trim** は、独立踏板のnosingとは別の接続ディテールとして扱う。

07-AではFloor edge nosing自体を生成しない。
将来のFloor–Stair connectionで、上階Floor端部へ段鼻相当の納まりを追加できる余地を残す。

## 12.3 Path contract

Stair pathはcanonical dataとして保持する。

07-Aでは2点から開始し、07-Dでschema-4 Multi-point Pathをproduction対応した。

```text
path_points
├ Point 0 = START
├ intermediate TURN points...
└ Point N = END
```

PathのSTART / ENDは**クリックした描画順**を表し、高さ方向とは分離する。

```text
P0 / START = first clicked point
Pn / END   = last clicked point

ascent_direction = FORWARD  -> P0からPnへ上る
ascent_direction = REVERSE  -> PnからP0へ上る
```

07-D AcceptanceではL/Uのproduction Turnはexact ±90° Landingとした。07-EでこのTurn foundationをWinderとarbitrary-angle Landingへ拡張する。

## 12.4 Internal model must not depend on preset names

UIでは分かりやすい住宅階段名を使用してよいが、内部canonical modelを「箱型」「スケルトン」などの曖昧なpreset名に依存させない。

| Axis | Initial / Future Values |
|---|---|
| Path | Straight / Multi-point |
| Turn | None / Landing / Winder |
| Riser | On / Off |
| Underside | Stepped Closed / Sloped Closed / None (future) |
| Side Board | Left On/Off / Right On/Off |
| Support | None / Side / Sawtooth / Center / future variants |
| Tread | Solid board / future nosing detail |
| Add-on Parts | future handrail / newel / etc. |

`Underside = None` は将来のopen系を可能にする内部拡張点であり、07-Bの標準住宅階段を露出下面にするという意味ではない。

### Combination support rule

内部データを独立したAxisとして持つことは、**全てのAxisの全組み合わせを生成可能にすることを意味しない**。

各Build Specificationで対応組み合わせを明示する。
未対応の組み合わせはUIで無効化または明示的に拒否し、暗黙に不正Geometryを生成しない。

## 12.5 Riser / Tread terminology

「段数」だけで管理しない。

少なくとも以下を意味上分離する。

```text
riser_count
independent_tread_count
actual_riser
going
```

例：

```text
floor_to_floor = 2800 mm
riser_count = 16
actual_riser = 175 mm
independent_tread_count = 15
```

矛盾する固定入力を許可しない。

## 12.6 Part-generation architecture

段配置計算と各部材のgeometry生成を分離する。

```text
Canonical Stair
    ↓
Resolved Path
    ↓
Resolved riser / tread placement
    ↓
Part generators
    ├ Tread
    ├ Riser board
    ├ Stepped underside
    ├ Sloped underside
    ├ Left side board
    ├ Right side board
    └ Future support / detail parts
```

直線住宅階段Meshを一体で直接生成し、そのMesh形状を後続Buildで解析・再利用する設計にしない。

## 12.7 Managed Stairの管理単位とMesh構成は分離する

ユーザーから見た管理単位は1 Stairとする。

これは「必ず1 Mesh」または「必ず複数Mesh」を意味しない。
各BuildのSpecificationで、管理上最も安全なMesh構成を選択できる。

Build 07-A〜07-Dでは、既存JHM architectureとの整合とlifecycle単純化のため、**1 Managed Stair = 1 Managed Mesh Object** を採用している。

ただし、Tread / Riser / Underside / Side Board等のPart Generator責務は分離し、将来必要になった場合にcanonical Stair modelを壊さずMesh構成を拡張できること。

Managed状態の生成geometryを直接編集した結果をcanonical Stairへ逆推定しない。

最終的に通常Blender Meshへ確定する出口を持つ。

## 12.8 Build 07-A — Stair Core + Top-view 2-point Straight Stair

**Status: ACCEPTED**

07-AのStage 1〜4およびBuild全体はBlender 5.2 LTS runtime acceptanceを完了した。詳細なproduction revision、automated evidence、runtime evidenceは `BUILD_07_A_ACCEPTANCE_RECORD.md` を正とする。

目的：

- Stair canonical dataを確立する。
- Top Viewの2点指定でStraight Stairを作成する。
- Wall / FloorなしでStair単体を生成する。
- Pathの描画順と上り方向を分離し、`ascent_direction` contractを確定する。
- floor-to-floor / riser / tread / upper-arrival contractを確定する。
- 後続Multi-point Pathへ拡張可能なCoreを作る。

基本対象：

- tread
- riser board
- width
- tread thickness
- riser thickness
- base_z
- floor_to_floor
- riser_count
- derived actual_riser
- derived independent_tread_count / going
- dimension edit
- regeneration
- Undo / Redo
- Save / reopen
- Editable Mesh conversion

### Early Core extensibility check

07-Aの段階で、**Riser board generatorを使用しなくても、段配置計算とTread生成が成立することを内部試験で確認した。**

これはユーザー向け `Riser OFF` 機能の先行実装ではない。

## 12.9 Build 07-B — Standard Residential Straight Stair

**Status: ACCEPTED**

07-AのStair Core上に、最初の実用的な住宅直階段を完成させた。Stage 1〜4およびBuild全体はBlender 5.2 LTS runtime acceptance済み。詳細は `BUILD_07_B_ACCEPTANCE_RECORD.md` を正とする。

主要機能：

- thick solid-board treads
- riser boards
- **stepped closed underside**
- left side board ON / OFF
- right side board ON / OFF
- side-board thickness / basic visible dimensions
- part-specific Material assignment
- predictable regeneration
- Editable Mesh conversion
- Save / reopen
- Undo / Redo

### Stepped closed underside — target appearance

07-Bの段々閉じ下面は、参考画像で確認した住宅階段の外観をproduction targetとする。

これは「部材裏面の露出」ではない。

下から見た場合、

- 各段下面の**水平面**
- 段差をつなぐ**縦面**

が連続し、段形状に追従する**閉じた段々の外観**を形成する。

重要：

> 同じ位置へTread裏面と追加Underside板を二重生成することを要求しているのではない。

逆さヒナ段系の化粧側板は、階段本体側面全体を自動的に閉じる部材とはみなさない。

### 07-B correction guardrail — closed body

2026-09-21 の Blender runtime visual review により、Tread/Riser直下を薄くなぞるだけの Underbody では本節の「閉じた段々の外観」を満たさないことを確認した。

`BUILD_07_B_CORRECTION_ADDENDUM.md` を correction authority とし、07-B `STEPPED_CLOSED` は以下を必須とする。

- 下方から Tread 裏・Riser 裏・階段内部を見せない。
- Side Board ON/OFF に依存せず階段本体自体を閉鎖する。
- 水平下面と縦接続面が連続した stepped soffit を形成する。
- 一段目の底面は一つの平らな水平面とし、局所ノッチを残さない。
- topology が manifold であることだけを visual closure の代用にしない。

Open / support / ささら・力桁系の露出構成は 07-F の別系統とする。

## 12.10 Build 07-C — Sloped Closed Underside + Straight Stair Finish Variants

**Status: ACCEPTED**

実装仕様は `BUILD_07_C_SPECIFICATION.md`、runtime-tested revision / acceptance結果は `BUILD_07_C_ACCEPTANCE_RECORD.md` を正とする。

主要機能：

- `STEPPED_CLOSED`
- `SLOPED_CLOSED`
- user-facing stair-body thickness / closed-body depth
- `STEPPED` / `SLOPED` Side Board
- tread front overhang / nosing
- basic front-edge Bevel / Round
- Material preservation
- Mesh conversion regression

### Sloped Side Board variant

07-Cの `SLOPED` Side Boardは、07-Bのanalytical `STEPPED` Side Boardとは別variantとして実装した。human-confirmed visual targetは、直線勾配のvisible finish、first-step aligned lower termination、upper short horizontal cap + vertical rear closureである。

### Sloped closed underside

階段下収納・トイレ等で使う住宅階段を想定し、階段下面を連続した斜め面材で閉じる。

`SLOPED_CLOSED` も `STEPPED_CLOSED` と同じ CLOSED invariant を継承する。違いは下面の形状だけであり、下方から Tread 裏・Riser 裏・階段内部を露出させない。

床まで完全に埋めるsolid massは対象外。

### Practical checkpoint after 07-C

07-C Acceptanceで、手作業で用意した簡易Wall / Floor相当シーンへの配置、placement、visible proportion、side-board appearance、stepped / sloped underside usability、Material、Mesh conversionを確認した。

このcheckpointの結果、08 / 09へ切り替えず、07-D Multi-point Path + L / U + Landingへ進み、07-DはAcceptance済みとなった。

## 12.11 Build 07-D — Multi-point Path + L / U + Landing

**Status: ACCEPTED**

Implementation authorityは `BUILD_07_D_SPECIFICATION.md`、受入結果は `BUILD_07_D_ACCEPTANCE_RECORD.md` を正とする。

Acceptance済み主要機能：

- start + intermediate turn points + end
- L-shaped path
- U-shaped path / コの字
- multiple straight flights
- exact ±90° Landing turn
- whole Stair = one Managed Stair
- consistent total floor-to-floor
- Riser Distribution `AUTO / MANUAL`
- path edit / regeneration
- START / END / intermediate TURN mouse relocation
- Shift **15°** angle constraint foundation
- X/Y / extension / 90° / parallel alignment guides
- 07-Eへ拡張可能な Turn foundation
- Save / reopen / Undo / Redo / Repair / Finalize / Delete / Material / topology regression

07-Dではworld-spaceのStair配置自体は斜め方向へ作成可能だが、production Landing turnはexact ±90°に限定した。arbitrary-angle Landing / Winderは07-Eへ送る。

既存07-D Landingは07-E導入時に勝手にWinderへ変更しない。

## 12.12 Build 07-E — Winder / 廻り段 + arbitrary-angle Turn / Landing

**Status: NEXT / SPECIFICATION FINAL / IMPLEMENTATION NEXT**

Implementation authority：`BUILD_07_E_SPECIFICATION.md` — **FINAL / IMPLEMENTATION AUTHORITY**。

07-Eは階段Buildの主要本命とし、07-DのMulti-point / Turn foundationを拡張して一般的な住宅の廻り階段と、変形住宅の90°以外の折れ曲がり階段をproduction対応する。

### Primary production scope

- 90° Winder
- overall 180° U-turn as **two persistent Turn combination**
- arbitrary-angle Turn foundation
- arbitrary-angle Landing
- arbitrary-angle equal-angle Winder where geometry is valid
- inner / outer tread geometry
- RiseEvent / riser distribution including Winder steps
- 3-point L / 4-point U production scope
- Side Board continuation at Winder
- STEPPED_CLOSED continuation
- **continuous SLOPED_CLOSED Winder soffit**
- Material / Reverse / persistence / lifecycle compatibility

### Winder pattern UX

住宅用途の基本Winder pattern：

```text
90° Winder
├ 2段廻り
├ 3段廻り
├ 4段廻り
├ BF-1
└ BF-2
```

UIでは小さなplan thumbnail/iconを優先候補とするが、画像はgeometry authorityではない。

U字では各Turnへ個別patternを設定する。

```text
Turn 1 = EQUAL_2
Turn 2 = EQUAL_3
```

または：

```text
Turn 1 = BF_1
Turn 2 = EQUAL_3
```

U字用全組合せを別persistent presetとして大量登録しない。

### Equal-angle subdivision baseline

Single Turnのstandard Winderは、Turn角 `theta` とpatternから等角fractionを導出する。

```text
90° / EQUAL_2 = 45° + 45°
90° / EQUAL_3 = 30° + 30° + 30°
90° / EQUAL_4 = 22.5° × 4

63° / EQUAL_3 = 21° + 21° + 21°
```

**Roadmap上のsingle-Turn数学例と07-E production Uを混同しない。**

Genericな「180°を1つのTurnとして2段/3段/…へ等角分割する」式は数学的には記述できるが、**07-E production Acceptanceの約束ではない**。07-Eのoverall 180° Uは、existing 4-point Path上の**2つのpersistent Turn**へ個別patternを割り当てて構成する。

したがって、07-Eは「total 2-step single-180° U」や「total 3-step single-180° U」を必須機能としない。

### Canonical Turn authority

07-E schema-5：

```text
TurnState
├ path_point_id        # persistent Turn identity authority
├ turn_mode            LANDING / WINDER
└ winder_pattern       NONE / EQUAL_2 / EQUAL_3 / EQUAL_4 / BF_1 / BF_2
```

Derived：

```text
signed_turn_angle
winder_step_count
winder_partition_rule
```

独立persistent `turn_id`を重複作成せず、`winder_pattern`をsingle canonical pattern authorityとする。

### Arbitrary-angle Turn / Landing contract

```text
incoming direction
+
outgoing direction
↓
signed theta
```

を解決し、`LANDING` / `WINDER`を適用する。

Shift15°はinteraction aidのみ。Production Turn angleは15°刻みに限定しない。

既存07-D exact-90 Landingはschema-4 compatibilityとして保持する。

### Width / legacy-house policy

07-Eの生成可否を現行法規や参考図の固定寸法へhard-codeしない。

- width900mm前提にしない
- 750 / 700 / 650mm等をwidth aloneで拒否しない
- 300 / 150 / 85mm等をuniversal minimumにしない
- validator / RNA range / UI clamp / presetにlegal-like hidden gateを入れない
- 650mmは回帰fixtureでありproduction minimumではない

本Addonは法規適合判定ソフトではない。

### Geometry safeguards

Rejectはactual geometry / mesh failureに基づく。

例：

- non-finite intersection
- self-intersection
- non-positive nominal cell
- partition failure
- required cutback exceeding Path
- Turn overlap
- physical finish intersection that cannot be validly trimmed
- underbody/tread penetration

Failure classは`GEOMETRY_INVALID / SCOPE_UNSUPPORTED / ADVISORY_ONLY`を区別する。

### Continuous SLOPED_CLOSED at Winder

```text
Lower Flight sloped soffit
        ↓
Winder continuous turning soffit
        ↓
Upper Flight sloped soffit
```

Winderではhorizontal Landing plateauを入れない。

第三者reviewを経て、FINAL contractは：

- complete outer-chain preservation (`Q1 -> O -> Q2`等)
- finite pivot-relief core
- local high-side pivot closure
- no T-junction shared-edge subdivision
- Compact-U event-group shared Z

をtext-onlyで定義した。

### Side Board continuation

07-C accepted independenceを維持：

```text
underside_mode  -> lower Side Board boundary
side_board_mode -> upper Side Board boundary
```

Compact U中央では2枚を衝突させず、shared-center profile / symmetric thickness / actual 3D trim / deterministic butt jointを使用する。

### Final Stage structure

```text
Stage 1
schema-5 Turn / RiseEvent foundation
+ 90° EQUAL_2/3/4 L Winder top geometry

Stage 2
BF-1 / BF-2
+ per-Turn U / Compact U
+ arbitrary-angle Landing / Winder
+ schema migration / physical finish integration

Stage 3
STEPPED_CLOSED
+ continuous SLOPED_CLOSED finite pivot relief
+ ordinary Side Board
+ Compact-U shared Side Board

Stage 4
Save/Reopen
+ Undo/Redo
+ rollback / Repair
+ Finalize / Delete
+ prior Straight/Landing regression
+ practical residential placement
+ final topology / visual acceptance
```

上面・RiseEvent Geometryを先にAcceptance可能な状態へ近づけ、その後に下面・側板へ集中する。

### Practical checkpoint after 07-E

07-E Acceptanceでは実住宅に近い簡易sceneへStraight / L-U Landing / Winder / oblique Landingを配置し、狭い住宅寸法を含む実用確認を行う。

07-E Acceptance後はいったん07-F / 07-Gを保留し、08-A / 08-Bへ進む。

## 12.13 Build 07-F — Open / Support Variants

**Status: HOLD after 07-E**

対象候補：

- Riser Off
- Underside None
- open variants
- side support
- sawtooth / ささら系
- center support
- support presets
- structure variants

「スケルトン階段」という単一presetへ内部モデルを固定しない。

対応するPath / Turn / Support / Undersideの組み合わせは将来07-F Specificationで明示する。

07-E完了後は一室統合試験を早期に実施するため07-Fを保留し、08-A / 08-Bを優先する。07-Fは削除ではなく、Integration Coreや実制作で必要性を再評価して再開できるBacklogとする。

## 12.14 Build 07-G — Optional Detail Expansion

**Status: HOLD / OPTIONAL BACKLOG**

07-GはBuild 07本体の必須完了条件ではない。

候補：

- separate nosing part
- anti-slip groove
- groove count / width / depth
- tread-front offset
- groove left/right end margin
- rounded groove ends
- additional side-board detail
- decorative trim
- other production-use details

07-Gは08/09以降へ延期する。

## 12.15 Build 07 quality / scope guards

Build 07全体で以下を維持する。

- Canonical data → derived geometry
- Managed Object Transformは原則identity
- manual Mesh editをcanonicalへ逆推定しない
- failure時にpartial commitしない
- Undo / Redo
- Save / reopen
- deterministic regeneration
- Material contract
- Editable Mesh exit
- prior accepted Wall / Finish regression

さらに、

> **Independent data axes do not imply universal combination support.**

各BuildのSpecificationで対応組み合わせを定義し、未対応組み合わせを明示する。

各Buildで「次Buildのための汎用性」を理由に未使用機能を大量先行実装しない。
必要な拡張点だけをcanonical contractとして確保し、production featureは各Buildで段階的に追加する。

---

# 15. Build 08 — Room / Floor / Ceiling minimum

## 15.1 Build 08-A — Minimal Room / Boundary + Floor

Roomは自動認識だけに依存しない。

対応方針：

- Automatic boundary
- Manual boundary
- Virtual boundary

を用意する。

目的：

- Floor生成
- Room単位のWall面解決
- 将来のFinish自動配置
- Room-based material / opening / ceiling連携

最小機能から始める。

### Specification note — Floor / Ceiling / Void coordination

08-A / 08-BではFloor・Ceilingの高さ基準と穴・Voidの扱いを相互に整合させる。特に階段用Openingを「Ceilingだけの穴」として固定せず、Floor / Ceiling / Stairをまたぐ空間的な開口として後続連携できる設計にする。

## 15.2 Build 08-B — Ceiling + void / hole basics

目的：

- Ceiling生成
- Ceiling height
- basic void
- basic opening / hole
- Stair voidとの将来連携

過剰なBIM ceiling systemにはしない。

## 15.3 Post-08-B checkpoint

08-B Acceptance後は次の順で進める。

```text
Known Issue 8.5 correction
↓
Integration Core
```

Integration Core開始前に、閉じたWall layoutでBaseboard / CrownのFinish endpointが一致しない問題を調査・修正し、必要なregression testを追加する。

---

# 16. Build 09 — Window / Door system

## 16.1 Build 09-A — Asset Root + Wall Anchor

Door / Windowそのものの造形機能を大量に作らない。

既存Asset利用を前提に、`Asset Root → Wall Anchor` を作る。

保存する情報例：

- referenced Wall ID
- wall-side / anchor side
- distance along Wall
- elevation
- width / height metadata
- asset identity

## 16.2 Build 09-B — Live Boolean Cutter

Window / Door Asset RootにCutterを連携。

目的：

- Wall移動追従
- Wall寸法変更追従
- Asset移動追従
- Save / reopen
- predictable Boolean

## 16.3 Build 09-C — Finish Exclusion integration

Door / Window openingとFinish Exclusionを連携。

例：

```text
Door opening
      ↓
Wall interval
      ↓
Baseboard / Crown exclusion
```

目的：

- Door枠前でBaseboard停止
- Opening移動時にExclusion追従
- Wall split後も参照維持
- Manual Exclusionとの共存

### Specification note — 2D区間だけでFinishを切らない

OpeningとFinishの連携ではWall上の水平区間だけでなく、**Openingの垂直範囲とFinishの高さ範囲が実際に重なるか**を判定する。

例：

- 通常の腰窓がBaseboard高さと重ならない場合、Baseboardを切らない。
- 天井まで届かないDoor / OpeningがCrown高さと重ならない場合、Crownを切らない。

09-C仕様書で水平区間と垂直範囲の双方を使うExclusion条件を定義する。

---

# 17. One-room integration tests

## 17.1 Integration Core — early one-room test

実施タイミング：

```text
07-E ACCEPTED
↓
08-A ACCEPTED
↓
08-B ACCEPTED
↓
Known Issue 8.5 correction
↓
Integration Core
```

目的はDoor / Window完成を待たず、主要Foundationをなるべく早く一室へ統合してArchitecture上の問題を発見すること。

対象例：

```text
一室
├ Wall
├ Baseboard
├ Crown
├ Floor
├ Ceiling
├ Stair
└ Void / Hole
```

主な試験項目：

- closed Wall layout
- Baseboard / Crown endpoint closure
- Wall寸法変更
- Wall endpoint移動
- Wall split
- Floor / Ceiling維持
- Stair placement
- Stair upper arrival / Floor relationship
- Stair / Void coordination
- Material維持
- Save
- Blender終了
- Reopen
- Regenerate
- Editable Mesh conversion
- 一部を通常Blender編集へ移行

この試験で見つかったFoundation問題は、Door / Window実装を始める前に修正する価値が高いものを優先する。

## 17.2 Integration 1 — full one-room production test

Build 09 minimalまで揃った後、Door / Window / Boolean / Finish Exclusionを含む完全版を実施する。

対象例：

```text
LDKの一角
├ Wall
├ Baseboard
├ Crown
├ Floor
├ Ceiling
├ Door
├ Window
└ Stair
```

試験項目：

- Wall寸法変更
- Wall endpoint移動
- Wall split
- Door移動
- Window移動
- Boolean更新
- Finish exclusion更新
- Floor / Ceiling維持
- Stair placement
- Stair / Floor / Void連携
- Material維持
- Save
- Blender終了
- Reopen
- Regenerate
- Editable Mesh conversion
- 一部を通常Blender編集へ移行

Build 07はstandalone Stairとして成立させるが、Integrationでは住宅全体の他Foundationと接続した場合のArchitectureを確認する。

---

# 18. Build 07 ordering checkpoints

旧Roadmapの「07-A / 07-A2 → 08/09 → Integration 1 → 07-B/C/D」という分断順序は廃止済み。

現在のcheckpoint：

- **07-C完了時**：直線住宅階段の実用性を確認し07-Dへ進むことを決定、完了済み。
- **07-D完了時**：Multi-point L/U + LandingのAcceptance完了。07-E Winder / arbitrary-angle Turnへ進む。
- **07-E仕様FINAL時**：第三者レビューを反映し、Codex Stage 1 implementationへ進む。
- **07-E完了時**：一般住宅の折れ曲がり階段としてpractical checkpointを行い、07-F / 07-Gを保留して08-A / 08-Bへ進む。
- **08-B完了時**：Known Issue 8.5を修正後、Integration Coreを実施する。
- **Integration Core完了時**：Foundation問題を整理し、09 minimalへ進む。

07-F / 07-Gは削除ではなくHOLD / Backlogであり、Integration結果や実制作上の必要性に応じて再開できる。

---

# 19. Build 10 — Production Hardening

最終段階。

主目的：

- UX整理
- UI整理
- Error message統一
- Save compatibility
- old-file migration
- dependency repair
- performance
- full regression
- integrated workflow test
- final Editable Mesh workflow
- production documentation

ここでは新しい大規模Featureを増やすより、**既存機能を壊れにくくし、実制作で使いやすくする**ことを優先する。

### Quality policy

保存・再読込、Undo / Redo、失敗時のrollback、既存機能への回帰確認は**各BuildのAcceptance条件**とする。これらの基本品質をBuild 10まで延期しない。

Build 10では、それまで各Buildで維持してきた品質を、Build間の依存関係・保存互換・移行・修復・UX・総合Regressionの観点から**全体横断で再検証・改善する**。

---

# 20. Scope guards

本プロジェクトは以下の方向へ無制限に拡張しない。

原則として避ける：

- フルBIM化
- IFC authoring system
- 構造計算
- 法規自動判定
- 全建材カタログ管理
- 自動施工図
- パラメトリックCAD全面置換
- すべてのBlender編集をManaged状態へ逆変換

必要になった機能のみ段階的に追加する。

---

# 21. Development decision rules

新機能の優先順位を判断するときは以下を基準にする。

優先度が高い：

1. 手作業負担が大きい
2. 毎案件で繰り返す
3. 寸法ベース自動化の効果が高い
4. 後続機能のFoundationになる
5. 一室統合試験で必要
6. 既存Accepted architectureを再利用できる

優先度が低い：

1. Blender標準機能だけで簡単に代替できる
2. 使用頻度が低い
3. 実装コストに対して時間短縮効果が小さい
4. BIM的な複雑さを大きく増やす
5. 未確定Foundationへ強く依存する

---

# 22. Roadmap change protocol

今後開発順序を変更する場合：

1. `ROADMAP.md` を更新
2. 変更理由を書く
3. Accepted済みBuildへの影響を確認
4. 必要なら新Build仕様書に互換性方針を書く
5. 既存Acceptance Recordは履歴として書き換えない

Roadmap変更は許可するが、Accepted historyは消さない。

---

# 23. Current next decision

現時点：

```text
05-B  ACCEPTED
06-A  ACCEPTED
06-B  ACCEPTED
06-C  ACCEPTED
07-A  ACCEPTED
07-B  ACCEPTED
07-C  ACCEPTED
07-D  ACCEPTED
07-E  SPECIFICATION FINAL
```

次：

```text
07-E Stage 1 implementation
     + schema-5 Turn identity / pattern authority
     + exact RiseEvent allocation
     + 90° L EQUAL_2 / EQUAL_3 / EQUAL_4 Winder
     + text-only reviewed geometry contract
```

状態遷移：

```text
07-D ACCEPTED
→ 07-E SPECIFICATION FINAL
→ 07-E STAGE 1 IMPLEMENTATION NEXT
```

07-E完成後は07-F / 07-GをHOLDし、08-A / 08-Bへ進む。

---

# 24. Summary

最終方針：

```text
Wall Foundation
    ↓
Finish Foundation
    ↓
Baseboard
    ↓
Crown
    ↓
07-A Stair Core / 2-point Straight
    ↓
07-B Standard Residential Straight Stair
    ↓
07-C Sloped Underside / Straight Finish Variants
    ↓
07-D Multi-point L/U + Landing [ACCEPTED]
    ↓
07-E Winder + arbitrary-angle Turn / Landing [SPEC FINAL / NEXT]
    ↓
[07-E practical checkpoint]
    ↓
07-F / 07-G HOLD
    ↓
08-A Minimal Room / Boundary + Floor
    ↓
08-B Ceiling + Void / Hole
    ↓
Known Issue 8.5 Finish endpoint correction
    ↓
Integration Core
    ↓
09 Window / Door Anchor + Boolean + Finish Exclusion
    ↓
Integration 1 full one-room production test
    ↓
Production Hardening
```

Build 07の住宅階段mainlineの主要ゴールは07-Eとする。07-F Open / Support Variantsと07-G Detail ExpansionはBacklogとして保持し、Integration結果や実制作上の必要性から再開時期を決める。

Build 07の中心目標は、

> **Wall / Floor / Roomに必須依存せず、トップビューでPathを描き、日本住宅の直線・折れ曲がり・廻り・変形角度の階段を1つのManaged Stairとして生成・編集できること**

である。

このRoadmapを今後の開発計画の親文書とする。
