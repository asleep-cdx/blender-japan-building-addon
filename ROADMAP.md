# Japanese House Modeler — Development Roadmap

最終更新: 2026-09-17

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
- **Build 06-B overall — ACCEPTED**
- Add-on version: **0.6.3**
- Build 06-B final identification: `Build 06-B: Custom Profile Registration and Final Baseboard`

現時点で、Wall SystemとBaseboard系Foundationは実用可能な基盤として成立している。

次のBuild候補は **06-C Crown Moulding** だが、実装開始前にこのRoadmapを基準文書として確定する。

---

# 4. Final development order

| Build | 内容 | 状態 |
|---|---|---|
| **05-B** | Wall System完成 | **DONE / ACCEPTED** |
| **05-C** | Wall再統合 | **BACKLOG** |
| **06-A** | Finish Attachment Foundation | **DONE / ACCEPTED** |
| **06-B** | Baseboard / 巾木 | **DONE / ACCEPTED** |
| **06-C** | Crown Moulding / 廻り縁 + Profile thumbnail UI | **NEXT / NOT STARTED** |
| **07-A** | Stair Core + 直線箱型階段 | Planned |
| **07-A2** | 蹴込み板なし直階段によるStair Core汎用性検証 | Planned |
| **08-A** | Minimal Room / Boundary + Floor | Planned |
| **08-B** | Ceiling + 吹抜け / 穴の基本 | Planned |
| **09-A** | Window / Door Asset Root + Wall Anchor | Planned |
| **09-B** | Live Boolean Cutter | Planned |
| **09-C** | Finish Exclusion連携 | Planned |
| **Integration 1** | 一室を最初から最後まで制作する実務統合試験 | Planned |
| **07-B** | L / U Stair + Landing | Planned |
| **07-C** | Winder / 廻り段 | Planned |
| **07-D** | Skeleton Stair / Support System拡充 | Planned |
| **10** | Production Hardening / UX / Compatibility / Full Regression | Planned |

---

# 5. Why this order

## 5.1 Finishを先に完成させる理由

Build 06では単なるCurve生成ではなく、

> **Wallのどの面・どの区間に、何を、どの基準高さで配置するか**

を永続化する共通Attachment Foundationを作る。

これにより、

- Baseboard
- Crown Moulding
- 将来のChair Rail
- Opening exclusion
- その他のWall付属部材

を同じ考え方で扱える。

## 5.2 Stair 07-Aを08/09より先にする理由

FloorはPlaneから比較的簡単に手作業できる。Ceilingも手作業代替が比較的簡単。Door / Windowも現状では AssetをAppend → 配置 → Boolean Cutter という手動ワークフローがある。

一方、階段は多数の踏板、蹴込み板、蹴上、踏面、段鼻、階高、方向転換、支持構造を手作業する負担が大きい。

したがって、**アドオン化による時間短縮効果が大きい直線階段を先に実装する**。

ただし階段全種類を完成させてから他機能へ進むのではない。

## 5.3 07-Aの後に08/09最小版へ進む理由

07-A直線階段まで完成したら、08/09の最小版へ進み、

> **一室を最初から最後まで作るIntegration 1**

を行う。

これにより、07-B/C/Dへ進む前にArchitecture上の問題を検出できる。

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

**Status: NEXT / NOT STARTED**

06-B Foundationを再利用し、Crown Mouldingを追加する。

主要テーマ：

- finish_type = CROWN の実働
- Ceiling基準配置
- Crown用vertical reference
- LEFT / RIGHT
- FORWARD / REVERSE
- inside / outside corner
- Miter / BUTT
- Partial placement
- Exclusion
- Standard Crown Profile 約3種
- Custom Profile
- Material persistence
- Editable Mesh conversion
- Save / reopen
- Undo / Redo
- Baseboard regression

### Specification note — Crown Profile orientation

既存のCeiling referenceは再利用するが、Crown Profileは**天井面から下方向へ展開するProfile**として定義する。Baseboardで成立したProfile座標制約をそのまま無条件に流用せず、Wall接触方向・室内側方向・垂直方向の意味を06-C仕様書で明示する。

### 06-Cまでに完成させるUI

Profile Libraryは最終的にサムネイル方式へ拡張する。

目標：

```text
┌────────┐ ┌────────┐ ┌────────┐
│Profile A│ │Profile B│ │Profile C│
└────────┘ └────────┘ └────────┘
```

ただしProfile identity / snapshot / geometry correctnessを優先し、UI装飾がcanonical設計を複雑化させないこと。

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

# 12. Build 07 — Stair architecture

## 12.1 Internal model must not depend on presets

UIでは「箱型階段」「スケルトン階段」のような分かりやすいプリセットを使用してよい。

ただし内部データはプリセット名に依存しない。

推奨軸：

| Axis | Values |
|---|---|
| Path | Straight / L / U |
| Direction Change | None / Landing / Winder |
| Riser | On / Off |
| Underside | Closed / Open |
| Support | None / Side Beam / Sawtooth / Center Beam |
| Add-on Parts | Handrail / Newel / etc. |

## 12.2 Riser / Tread terminology

「段数」だけで管理しない。

内部値：

```text
riser_count
tread_count
```

を分離する。

例：

```text
floor_to_floor = 2800 mm
riser_count = 16
actual_riser = 175 mm
```

上階Floor自体が最後の到達面なら、

```text
riser_count = 16
independent_tread_count = 15
```

となり得る。

### Floor-to-floor definition

階高は、**下階仕上げ床面 → 上階仕上げ床面** と定義する。Wall Heightとは別。

---

# 13. Build 07-A — Stair Core + Straight Closed Stair

目的：

- Stair Coreを確立
- Straight Stair生成
- 箱型階段を最初のproduction presetとして実装
- riser / tread / floor-to-floor contractを確定
- 後続L/U/Winder/Skeletonへ拡張可能な内部構造を作る

重要：

> 直線箱型階段だけ作れても、内部Coreが箱型専用になってはいけない。

### Specification note — riser_count / tread_count

`riser_count` と `tread_count` は意味を分離するが、**両方をユーザーが独立した固定入力として自由に設定できる、という意味ではない**。どちらを入力値とし、どちらを他の階段条件から導出するかは07-A仕様書で決定し、矛盾する組合せを作らない。

---

# 14. Build 07-A2 — Core validation with open-riser straight stair

07-A完了直後に小規模試験を行う。

最低条件：

- 07-Aと同じStair Coreを使用する
- Riser Off
- Open underside
- Straight Stairのまま箱型以外の生成経路を確認する

これにより、**Stair CoreがClosed Box presetへ固定されていないこと**を検証する。

Side Beam / Sawtooth / Center Beamなど支持桁の種類拡充は **07-D** の担当とし、07-A2では必須にしない。07-A2で完成したスケルトン階段を提供する必要はなく、Coreの汎用性確認を目的とする。

これは大規模機能追加ではなくArchitecture検証。

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

# 17. Integration 1 — One-room production test

07-A + 08 minimal + 09 minimalまで完成後、必ず実施する。

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
└ Straight Stair（必要なら）
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
- Material維持
- Save
- Blender終了
- Reopen
- Regenerate
- Editable Mesh conversion
- 一部を通常Blender編集へ移行

ここでArchitecture上の問題が出た場合、**07-B以降へ進む前にFoundationを修正する**。

---

# 18. Build 07-B / 07-C / 07-D

Integration 1を通過後、階段機能を拡張する。

## 18.1 Build 07-B — L / U + Landing

- L-shaped stair
- U-shaped stair
- Landing
- multiple flights
- consistent floor-to-floor calculation
- path-based Stair Core reuse

## 18.2 Build 07-C — Winder

- winder steps
- turning geometry
- inner / outer tread control
- minimum geometry safeguards
- L/U combination

## 18.3 Build 07-D — Skeleton / Support expansion

- open riser
- open underside
- side beam
- sawtooth
- center beam
- support presets
- structure variants

UI presetは用意してよいが、内部モデルはAxis-based designを維持する。

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
```

次候補：

```text
06-C Crown Moulding
```

ただし、06-Cの実装を開始する前に、

- このRoadmapをGitHubへ保存
- 06-Cの目的とscopeを再確認
- `BUILD_06_C_SPECIFICATION.md` を作成
- 仕様レビュー
- 実装

の順で進める。

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
Straight Stair Core
    ↓
Minimal Room / Floor / Ceiling
    ↓
Window / Door Anchor + Boolean
    ↓
Finish Exclusion Integration
    ↓
One-room Production Integration Test
    ↓
Advanced Stair
    ↓
Production Hardening
```

この順序は、

- Wall / FinishのFoundationを先に固める
- 手作業負担の大きいStraight Stairを極端に後回しにしない
- Floor / Ceiling / Openingの最小版を作る
- 一度一室を実際に完成させる
- そこでArchitectureを検証してから高度なStairへ進む

という方針に基づく。

**このRoadmapを今後の開発計画の親文書とする。**
