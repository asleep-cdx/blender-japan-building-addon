# BUILD 07-A SPECIFICATION
## 日本住宅モデラー — Stair Core + Top-view 2-point Straight Stair

---

# 1. Purpose

Build 07-Aは、今後のBuild 07-B〜07-Fで共有する **Stair Core** を確立し、トップビューの2点指定から、壁・床・Roomに依存しないStraight Stairを生成できるようにするBuildである。

07-Aの中心目的は、完成度の高い住宅階段意匠を一度に実装することではない。

最優先するのは以下である。

- canonical Stair data
- 2-point Path creation
- draw orderと上り方向の分離
- floor-to-floor / riser / tread contract
- upper-arrival contract
- basic Tread / Riser geometry
- deterministic regeneration
- invalid-input rollback
- Undo / Redo
- Save / reopen
- Editable Mesh exit
- future Multi-point / Winder / Open Stairへ拡張できるCore

07-Aの完了時点では、直線階段の基本段配置が正しく生成・編集・保存・再生成できることをAcceptance条件とする。

---

# 2. Roadmap position

Build 07 mainline:

```text
07-A Stair Core + Top-view 2-point Straight Stair
    ↓
07-B Standard Residential Straight Stair
    + Stepped Closed Underside
    + Side Boards
    ↓
07-C Sloped Closed Underside
    + Straight Stair Finish Variants
    ↓
07-D Multi-point Path + L/U + Landing
    ↓
07-E Winder / 廻り段
    ↓
07-F Open / Support Variants
```

07-GはOptional Detail Expansionであり、07-Aの必須範囲ではない。

---

# 3. Accepted baseline

07-Aは、main上でAcceptance済みの以下をbaselineとする。

- Build 05-B Wall System
- Build 06-A Finish Attachment Foundation
- Build 06-B Baseboard
- Build 06-C Crown Moulding / Profile Thumbnail UI
- DEVELOPMENT_WORKFLOW.md

既存のWall / Finish挙動を不必要に変更しない。

Build 07-A実装に伴うregressionは、少なくとも既存pure Python test discoveryが継続PASSすることを要求する。

---

# 4. Add-on identification

Build 07-A production実装ではadd-on versionを次へ進める。

```text
version = (0, 7, 0)
description = "Build 07-A: Stair Core + Top-view 2-point Straight Stair"
```

Stage開発中のCandidateでも、Build 07-A系であることが識別できること。

---

# 5. Scope

07-Aでproduction対応する。

- Top-view / XY plan based 2-point Stair Path
- Path centerline
- Path draw order
- independent ascent direction
- base_z
- floor_to_floor
- stair width
- riser_count
- derived actual_riser
- derived independent_tread_count
- derived going
- derived run_length
- upper arrival interface
- thick rectangular Tread boards
- Riser boards
- dimension editing
- ascent reversal
- explicit regeneration
- managed-state diagnosis
- basic repair
- safe deletion
- Editable Mesh finalization
- Save / reopen
- Undo / Redo

---

# 6. Explicit non-scope

07-Aでは以下をproduction実装しない。

- Stepped Closed Underside final form
- Sloped Closed Underside
- left / right Side Board
- user-facing Riser OFF
- L-shaped Stair
- U-shaped Stair
- Landing
- Winder / 廻り段
- Spiral Stair
- separate nosing part
- tread front overhang
- Bevel / Round edge treatment
- anti-slip groove
- handrail
- newel
- baluster
- side / sawtooth / center support variants
- automatic Wall connection
- automatic Room connection
- automatic Floor object generation
- automatic Ceiling connection
- Building-code compliance checker

将来拡張点をcanonical architectureに確保することと、07-Aで機能を先行実装することを混同しない。

---

# 7. Units

既存JHM contractを維持する。

UI:

```text
mm
```

Canonical plan points:

```text
world-space metres
```

Geometry:

```text
Blender metres
```

寸法Property名に `_mm` が付く値はmmとして扱う。

---

# 8. One managed Stair = one managed Blender Object in 07-A

07-Aでは、**1つのManaged Stairを1つのBlender Mesh Objectとして実装する**。

推奨名:

```text
JHM Stair
JHM Stair.001
...
```

Objectに `JHM_StairProperties` を保持する。

07-AではPersistent child Mesh objectを作らない。

重要：

> 1 Meshであることと、内部Part Generatorを分離することは別問題である。

Tread / Riserは独立した生成ロジックからmesh fragmentsを作り、最終的に1つのmanaged Meshへ統合してよい。

理由：

- selectionが単純
- delete / duplicate / save / reopenが単純
- Object Transform contractを維持しやすい
- Wallと同様に「1管理対象 = 1 Object」で扱える
- Editable Mesh finalizationが単純
- 07-A時点ではchild dependency管理を増やさない

07-B以降で別Objectが必要になった場合でも、canonical Stair modelを変更せず拡張できる設計を維持する。

---

# 9. Object Transform contract

Managed Stair Objectは常に原則として、

```text
Location = (0, 0, 0)
Rotation = (0, 0, 0)
Scale    = (1, 1, 1)
```

を維持する。

Stairの位置・方向・高さをObject Transformへcanonical保存しない。

Mesh verticesはcanonical world-space Path / dimensionsから生成する。

Object Transformを手動変更したManaged Stairは異常状態として診断可能にする。

通常Blender Transformを自由に使いたい場合は、Editable Meshとして確定してManaged状態を解除する。

---

# 10. Persistent Stair identity

各Managed StairはObject名とは独立した永続IDを持つ。

```text
stair_id = UUID
```

要件：

- create時にUUID生成
- renameしても不変
- save / reopenで不変
- regenerationで不変
- dimension editで不変

Shift+D等でObjectが複製され、同一 `stair_id` が複数存在する場合はID conflictとして検出できること。

07-Aでは選択中Stairに対する明示的Repairにより、選択Objectへ新しいUUIDを付与してconflictを解消できることを推奨する。

silent automatic ID rewriteは行わない。

---

# 11. Canonical Path model

07-AでもPathを2個の専用 `start/end` fieldだけで固定しない。

将来Multi-pointへ拡張できるCollection形式を使う。

概念：

```text
JHM_StairProperties
└ path_points[]
   ├ Point 0
   └ Point 1
```

07-A production rule:

```text
len(path_points) == 2
```

各Pointはworld XY plan coordinateをcanonicalに保持する。

Path PointのZをbase heightとして使用しない。

```text
Path = plan
base_z = vertical reference
```

を分離する。

---

# 12. Path centerline

ユーザーがトップビューで描く線は **Stair centerline** とする。

```text
          Left
           ↑

     ┌───────────────┐
P0 ●─┼───────────────┼─● P1
     └───────────────┘

           ↓
          Right
```

Stair widthはcenterlineから左右へ対称に展開する。

07-AではSide Boardをまだ生成しないため、`stair_width_mm` はTread / Riser本体の全幅とする。

将来07-BでSide Boardを追加しても、Side Board ON/OFFによってこのcanonical widthを暗黙変更しない。

---

# 13. Draw order and ascent direction are separate

Path Point名は描画順を意味する。

```text
P0 / START = first clicked point
P1 / END   = second clicked point
```

高さ方向は別Propertyとする。

```text
ascent_direction = FORWARD
ascent_direction = REVERSE
```

意味：

```text
FORWARD:
lower side = P0
upper side = P1

REVERSE:
lower side = P1
upper side = P0
```

creation default:

```text
FORWARD
```

UIから「上り方向を反転」できること。

上り方向反転でPath Pointの保存順を入れ替えない。

---

# 14. Resolved Stair local axes

canonical plan dataから、生成時にresolved axesを導出する。

```text
+X_stair = uphill / lower -> upper
+Y_stair = left when facing uphill
+Z       = world up
```

例：

```text
forward = normalize(upper_xy - lower_xy)
left    = (-forward.y, forward.x)
```

Left / Rightの意味は画面基準ではなく、**上る人から見たLeft / Right** とする。

07-AではSide Boardを生成しないが、このaxis contractを最初から固定する。

---

# 15. base_z

`base_z_mm` は下階側の仕上げ床面相当の基準高さとする。

default:

```text
0 mm
```

07-Aでは実Floor Objectを必要としない。

下階Floorが存在しなくても、数値基準だけでStairを生成できること。

---

# 16. floor_to_floor

`floor_to_floor_mm` は、

> 下階仕上げ床面相当から上階仕上げ床面相当までの垂直高さ

とする。

default:

```text
2800 mm
```

`floor_to_floor_mm > 0` を必須とする。

---

# 17. riser_count

`riser_count` は下階から上階到達面までの **蹴上回数** とする。

default:

```text
16
```

07-Aでは少なくとも、

```text
riser_count >= 2
```

を要求する。

「段数」という曖昧なUI labelだけを使用しない。

UI labelは、

```text
蹴上数
```

とする。

---

# 18. independent_tread_count

07-Aでは、

```text
independent_tread_count = riser_count - 1
```

とする。

例：

```text
riser_count = 16
independent_tread_count = 15
```

15枚の独立踏板の次に、16回目の蹴上で上階到達面へ到達する。

`independent_tread_count` はread-only derived valueとする。

---

# 19. actual_riser

```text
actual_riser_mm
=
floor_to_floor_mm / riser_count
```

例：

```text
2800 / 16 = 175 mm
```

`actual_riser_mm` はread-only derived valueとする。

07-Aでは希望蹴上寸法から自動段数提案する機能は実装しない。

---

# 20. run_length

`run_length` はresolved lower sideからupper sideまでのPath centerline XY距離である。

```text
run_length_m
=
distance(P0.xy, P1.xy)
```

FORWARD / REVERSEを変更しても距離は変わらない。

run_lengthはPathから導出されるため、07-A UIではread-onlyとする。

run_lengthを変更したい場合の専用Path edit UIは07-A必須範囲に含めない。
必要ならStairを作り直す。

---

# 21. going

07-Aでは、

```text
going_mm
=
run_length_mm / independent_tread_count
```

とする。

例：

```text
run_length = 3600 mm
riser_count = 16
independent_tread_count = 15

going = 240 mm
```

`going` は隣接するRiser基準線間の水平ピッチとする。

重要：

> goingと将来のphysical tread board depthを同一概念に固定しない。

07-Aにはnosing overhangがないため、

```text
tread board depth = going
```

でよい。

将来07-Cでfront overhang / nosingを追加した場合は、board depthとgoingを分離可能にする。

---

# 22. Upper arrival contract

07-Aは上階Floorを生成しない。

しかし、上階接続基準をStairから導出できること。

```text
upper_arrival_z_mm
=
base_z_mm + floor_to_floor_mm
```

plan position:

```text
FORWARD -> P1
REVERSE -> P0
```

upper arrival lineはそのplan positionを通り、Stair width全体に渡る線として概念化する。

将来Floor Systemと接続した場合、

```text
Stair upper_arrival_z
==
Upper Floor finished top surface Z
```

とする。

---

# 23. Upper Floor is the final arrival level

上階Floor接続時の段数contract：

```text
riser_count = N
independent_tread_count = N - 1
Upper Floor finished surface = N回目の蹴上後の到達面
```

例：

```text
riser_count = 16

Tread 1  = 175 mm
...
Tread 15 = 2625 mm
Upper Floor = 2800 mm
```

上階Floorを17段目として追加で数えない。

---

# 24. Future upper-floor edge nosing / trim

日本住宅では、上階Floorの階段開口端にも最終段の段鼻に相当する縁・見切りが存在する場合がある。

この接続ディテールは、

```text
independent tread nosing
!=
upper-floor edge nosing / trim
```

として分離する。

07-Aでは、

- Upper Floorを生成しない
- upper-floor edge nosingを生成しない

ただしupper arrival contractを保持し、将来08のFloor–Stair connectionで、Floor端部へ段鼻相当の納まりを追加できる設計余地を残す。

---

# 25. Stair width

`stair_width_mm` は07-AのTread / Riser本体幅とする。

provisional default:

```text
900 mm
```

centerlineから左右へ、

```text
width / 2
```

ずつ展開する。

`stair_width_mm > 0` を要求する。

---

# 26. Tread thickness

`tread_thickness_mm` は独立踏板の板厚。

provisional default:

```text
30 mm
```

07-Aでは矩形板のみ。

- no overhang
- no bevel
- no round
- no groove
- no separate nosing

```text
0 < tread_thickness_mm < actual_riser_mm
```

を要求する。

---

# 27. Riser-board thickness

`riser_thickness_mm` は蹴込み板厚。

provisional default:

```text
12 mm
```

07-Aでは矩形板のみ。

```text
0 < riser_thickness_mm < going_mm
```

を要求する。

---

# 28. Basic Tread geometry

resolved lower pointをoriginとするlocal stair axis上でTreadを生成する。

```text
j = 1 .. independent_tread_count
```

各Tread top elevation:

```text
Z_top(j)
=
base_z + j * actual_riser
```

plan interval:

```text
X_start(j) = (j - 1) * going
X_end(j)   = j * going
```

width:

```text
-Y = width/2
+Y = width/2
```

Treadはtop elevationから下向きに `tread_thickness` を持つclosed rectangular solidとする。

---

# 29. Basic Riser-board geometry

```text
k = 1 .. riser_count
```

Riser基準位置:

```text
X(k) = (k - 1) * going
```

ただし最終Riser:

```text
X(riser_count) = run_length
```

となる。

各Riserはfull Stair widthを持つ。

Riser-board thicknessは上り方向側へ配置することを基本とする。

07-AではTreadとRiserのvisible exteriorに意図しないgapが生じないこと。

内部部材の施工ディテールを厳密再現する必要はない。

同位置への不要なcoplanar duplicate faceは避ける。

---

# 30. Final Riser

最後のRiserはUpper Arrivalへ接続する。

07-AにはUpper Floor slabが存在しないため、最終Riser topは、

```text
upper_arrival_z
```

へ到達する。

将来Floorが接続された場合、そのFloor edge / trimが最終Riser上部と視覚的に納まる設計へ拡張する。

---

# 31. Part-generation separation

以下を分離する。

```text
resolve_stair_layout()
build_tread_fragments()
build_riser_fragments()
assemble_stair_mesh()
```

関数名は実装上変更してよいが、責務分離は維持する。

`resolve_stair_layout()` はRiser-board Meshの存在に依存してはならない。

---

# 32. Early Core extensibility test

07-Aで必須。

Riser-board generatorを呼ばず、

```text
Canonical Stair
↓
Resolved layout
↓
Tread generator
```

だけで正しいTread配置が成立することをautomated testで確認する。

これはuser-facing `Riser OFF` ではない。

07-FでOpen Stairを追加する際に、step placement coreを作り直さないためのarchitecture gateである。

---

# 33. Creation defaults

Sceneに新規Stair用default PropertyGroupを持ってよい。

provisional defaults:

```text
base_z_mm           = 0
floor_to_floor_mm   = 2800
riser_count         = 16
stair_width_mm      = 900
tread_thickness_mm  = 30
riser_thickness_mm  = 12
ascent_direction    = FORWARD
```

これらは法規適合値を保証するpresetではない。

単なる作図初期値である。

---

# 34. Top-view creation UX

新規operator:

```text
jhm.create_stair
```

UI label:

```text
階段を作成
```

基本操作：

```text
1. operator開始
2. P0を左クリック
3. マウス移動中にcenter Path preview
4. P1を左クリック
5. validation
6. Managed Stair作成
```

Cancel:

```text
ESC
Right Mouse
```

Cancel時はScene dataを変更しない。

---

# 35. Drawing plane

クリック位置は、

```text
Z = base_z
```

のworld horizontal planeとのray intersectionから取得する。

canonical Path Pointはplan XYを保持し、vertical placementは `base_z_mm` から解決する。

Viewport rayが基準planeと安定して交差しない場合は明示的Warningを出す。

トップビュー、またはXY平面を見下ろす斜めViewを想定する。

---

# 36. Creation preview

最低限表示する：

- P0 marker
- current P1 candidate
- center Path
- START / END識別
- FORWARD defaultの上り方向arrow
- width footprint outlineが低コストなら表示

previewはcanonical dataを書き換えない。

07-AではWall snapping / Wall endpoint snappingは必須ではない。

---

# 37. Minimum Path validation

以下は作成拒否。

- P0 / P1取得失敗
- non-finite coordinate
- Path length <= safety threshold
- goingを成立させられない短すぎるPath
- invalid dimensions

拒否時にpartial Managed Stairを残さない。

minimum thresholdはpure helperとして一元管理する。

---

# 38. Selected Stair UI

Managed Stair選択時に最低限表示する。

```text
種類: STAIR
管理状態
Stair ID status
Path点数: 2
上り方向: FORWARD / REVERSE
下端基準高さ
階高
上端到達高さ [read-only]
蹴上数
実蹴上 [read-only]
独立踏板枚数 [read-only]
水平長 [read-only]
踏面ピッチ / going [read-only]
階段幅
踏板厚
蹴込み板厚
```

operators:

```text
階段寸法を変更
上り方向を反転
階段を再生成
管理状態へ復元
編集可能Meshとして確定
階段を削除
```

---

# 39. Dimension edit

`jhm.edit_stair_dimensions` を用意する。

07-Aで編集可能：

- base_z_mm
- floor_to_floor_mm
- riser_count
- stair_width_mm
- tread_thickness_mm
- riser_thickness_mm

07-AではPath Point位置をnumeric dialogから編集する必要はない。

変更はtransactionalに行う。

---

# 40. Ascent reversal

`jhm.reverse_stair_ascent` を用意する。

動作：

```text
FORWARD <-> REVERSE
```

変更しないもの：

- path_points order
- stair_id
- run_length
- width
- floor_to_floor
- riser_count

再生成するもの：

- resolved lower / upper
- Tread positions
- Riser positions
- upper arrival position

Undo / Redo対応。

---

# 41. Regeneration transaction

既存Managed Stairを更新する場合、

```text
validate canonical candidate
↓
resolve layout
↓
build complete replacement Mesh
↓
validate replacement
↓
commit data swap
```

とする。

prepare失敗時は既存Mesh dataを変更しない。

partial geometryをcommitしない。

---

# 42. Invalid edit rollback

例：

- floor_to_floor <= 0
- riser_count < 2
- width <= 0
- tread thickness <= 0
- riser thickness <= 0
- tread thickness >= actual_riser
- riser thickness >= going
- non-finite values

既存Stair編集時にvalidation失敗した場合：

- operator CANCELLED
- existing canonical data unchanged
- existing Mesh data unchanged
- stair_id unchanged

とする。

---

# 43. Managed-state diagnosis

pureまたはtestable helperでManaged Stairの問題を診断できること。

最低候補：

- missing stair_id
- duplicate stair_id
- path point count != 2
- zero / invalid Path
- invalid dimensions
- non-finite values
- non-identity Object Transform
- generated geometry missing

UI status例：

```text
正常
ID_CONFLICT
TRANSFORM_CHANGED
INVALID_CANONICAL
GEOMETRY_MISSING
```

正確な内部enum名は実装に任せる。

---

# 44. Repair

`jhm.repair_stair` を用意する。

canonical dataが有効なら、

- Object Transformをidentityへ戻す
- canonical dataからgeometryを再生成

できること。

duplicate IDの場合は、選択中Stairへ新UUIDを明示的に発行するrepair pathを持ってよい。

invalid canonical valueを推測で書き換えない。

---

# 45. Safe deletion

`jhm.delete_stair` を用意する。

07-AではStairに外部dependent objectは存在しないため、選択Managed Stair Objectを安全に削除する。

将来Floor / Void等が依存するようになった場合に拡張可能なoperatorとして実装する。

標準Deleteキーを完全禁止する必要はないが、JHM UIでは専用operatorを提供する。

---

# 46. Editable Mesh finalization

07-A Stairは既にMesh Objectであるため、Curve-to-Mesh変換は不要。

`jhm.convert_stair_mesh` は、

- current managed geometryを保持
- `is_stair = False`
- JHM managed regeneration対象から除外
- Object Transformを現状のidentityのまま保持
- visible Material / geometryを保持
-通常Blender Meshとして編集可能

とする。

canonical property値がObject data内に残っていても、`is_stair=False` ならJHMは逆推定・自動再管理しない。

UndoでManaged Stairへ戻せること。

---

# 47. Material contract in 07-A

07-AではPart-specific Material UIは必須ではない。

ただし既存ObjectにMaterialが割り当てられている場合、dimension regeneration / ascent reversalで不必要に消失させないことを推奨する。

正式なTread / Riser別Material assignmentは07-Bで定義する。

---

# 48. Save / reopen

保存・Blender終了・再open後：

- is_stair
- stair_id
- path_points
- ascent_direction
- base_z
- floor_to_floor
- riser_count
- width
- tread thickness
- riser thickness
- generated geometry

が維持されること。

reopen時に自動で別IDへ変えない。

---

# 49. Undo / Redo

最低対象：

- create Stair
- dimension edit
- ascent reversal
- repair
- Editable Mesh finalization
- delete Stair

Undo / Redo検証は `DEVELOPMENT_WORKFLOW.md` に従い、対象operatorとCtrl+Z / Ctrl+Shift+Zの間に不要なPython Console操作を挟まない。

---

# 50. No Floor dependency in 07-A

07-Aでは、

```text
lower Floor object
upper Floor object
Floor opening
Void
```

を要求しない。

Stairは数値だけで完全生成できること。

将来Floor System完成後、optional referenceとして接続する。

---

# 51. No building-code compliance claim

07-Aは日本の建築法規への自動適合判定を行わない。

例えばactual riser / goingが住宅用途として適切かどうかは、07-Aでは法令判定しない。

07-Aが保証するのは、

- geometry mathの整合
- canonical consistency
- explicit invalid geometry rejection

である。

---

# 52. Module separation

推奨構成：

```text
properties.py
    JHM_StairPathPoint
    JHM_NewStairDefaults
    JHM_StairProperties

stair_geometry.py
    pure layout resolution
    tread/riser fragment generation
    mesh validation/preparation

stair_operators.py
    create/edit/reverse/regenerate/repair/finalize/delete

stair_state.py
    diagnosis / identity helpers if useful

ui.py
    new Stair UI
    selected Stair UI

__init__.py
    registration
```

実装上、責務が明確ならファイル名変更は許容する。

Wall / Finish production codeへStair logicを無理に混在させない。

---

# 53. Stage 1 — Canonical Stair + 2-point creation

Stage 1 goals:

- Stair PropertyGroups
- UUID identity
- Path Collection
- ascent_direction
- new Stair defaults
- 2-point modal operator
- preview
- cancel safety
- one Managed Mesh Object creation
- identity transform
- selected basic UI

Stage 1ではfinal Tread / Riser geometry完成を要求しない。

Stage 1がvisual runtime verificationに十分でない場合、最初のinstallable CandidateをStage 2完了後にしてよい。

---

# 54. Stage 2 — Layout calculation + basic geometry

Stage 2 goals:

- lower / upper resolution
- run_length
- actual_riser
- independent_tread_count
- going
- upper arrival
- Tread generator
- Riser generator
- assembled Mesh
- geometry validity
- early Riser-independent architecture test

ここで最初のvisible Straight Stairが成立する。

---

# 55. Stage 3 — Editing + regeneration + rollback

Stage 3 goals:

- dimension editor
- ascent reversal
- transactional regeneration
- invalid-input rejection
- geometry/canonical rollback
- managed-state diagnosis
- repair

---

# 56. Stage 4 — Lifecycle / Mesh exit / regression

Stage 4 goals:

- Save / reopen
- Undo / Redo
- duplicate-ID behavior
- Editable Mesh finalization
- delete
- complete Build 07-A automated regression
- prior Build regression
- Blender runtime acceptance

---

# 57. Automated test files

最低限、Stageごとにtestを分離できる構成を推奨する。

例：

```text
tests/test_build_07_a_stage1.py
tests/test_build_07_a_stage2.py
tests/test_build_07_a_stage3.py
tests/test_build_07_a_stage4.py
```

必要なら共有test helperを追加してよい。

---

# 58. Automated Stage 1 coverage

最低対象：

- UUID generation / uniqueness helper
- Path exactly 2 points
- draw-order persistence
- ascent enum
- lower / upper resolution
- width axis
- world XY plan contract
- identity-transform eligibility
- validation of zero-length Path
- cancel has no data mutation

---

# 59. Automated Stage 2 coverage

最低対象：

- riser_count -> tread_count
- floor_to_floor -> actual_riser
- run_length -> going
- FORWARD layout
- REVERSE layout
- horizontal Path
- vertical plan Path
- oblique Path
- width symmetry around centerline
- upper arrival Z
- upper arrival plan position
- Tread count
- Riser count
- Tread elevations
- final Riser reaches upper arrival
- Riser generator omitted -> Treads still valid
- finite Mesh coordinates
- no zero-area generated faces where applicable

---

# 60. Automated Stage 3 coverage

最低対象：

- edit base_z
- edit floor_to_floor
- edit riser_count
- edit width
- edit tread thickness
- edit riser thickness
- ascent reversal
- stair_id persistence
- invalid floor_to_floor rollback
- invalid riser_count rollback
- invalid thickness rollback
- prepare failure does not swap Mesh data
- diagnose non-identity transform
- repair from valid canonical

---

# 61. Automated Stage 4 coverage

最低対象：

- serialization-facing Property defaults
- duplicate ID detection
- finalize managed -> unmanaged state helper
- prior Build test compatibility
- full discovery
- compileall
- git diff --check

Blender save/reopenとactual Undo stackはpure Python testだけでAcceptanceしたことにしない。

---

# 62. Blender runtime acceptance — creation

Blender 5.2 LTSで確認。

最低ケース：

- empty Scene
- no Wall
- no Floor
- base_z 0
- floor_to_floor 2800
- riser_count 16
- width 900
- straight horizontal plan Path
- oblique plan Path

確認：

- 2-click creation
- preview
- centerline intent
- correct ascent
- identity transform
- exactly one Managed Stair Object
- correct counts / dimensions via Python Console

---

# 63. Blender runtime acceptance — numeric contract

例：

```text
base_z = 0
floor_to_floor = 2800
riser_count = 16
run_length = 3600
```

期待：

```text
actual_riser = 175
independent_tread_count = 15
going = 240
upper_arrival_z = 2800
```

visible Tread count:

```text
15
```

visible Riser count:

```text
16
```

上階Floorは存在しない。

---

# 64. Blender runtime acceptance — ascent reversal

同一Pathで、

```text
FORWARD
↓
REVERSE
```

を実行。

期待：

- path_points order unchanged
- stair_id unchanged
- run_length unchanged
- lower / upper side reversed
- Tread / Riser geometry reversed
- upper arrival plan position reversed
- Object Transform identity
- Undo / Redo works

---

# 65. Blender runtime acceptance — dimension edit

最低ケース：

- floor_to_floor変更
- riser_count変更
- width変更
- tread thickness変更
- riser thickness変更
- base_z変更

各変更後：

- canonical correct
- derived values correct
- Mesh regenerated
- no duplicate Stair object
- stair_id unchanged
- transform identity

---

# 66. Blender runtime acceptance — failure rollback

Managed Stairが正常な状態から無効編集を試す。

例：

- floor_to_floor <= 0
- riser_count < 2
- tread thickness >= actual_riser
- riser thickness >= going

期待：

- explicit failure
- old canonical unchanged
- old Mesh unchanged
- no partial geometry
- Stair remains managed and usable

---

# 67. Blender runtime acceptance — Save / reopen

正常Stairを保存。

Blender完全終了。

再open。

確認：

- Stair count unchanged
- stair_id unchanged
- Path unchanged
- ascent unchanged
- dimensions unchanged
- derived geometry visually unchanged
- transform identity
- managed status normal

---

# 68. Blender runtime acceptance — Editable Mesh

Managed Stairを「編集可能Meshとして確定」。

期待：

- same visible geometry
- Object type MESH
- is_stair == False
- no automatic regeneration
- standard Edit Mode possible
- Undo restores managed Stair

Meshはfiniteであり、各generated closed componentに異常なopen boundaryを作らないことを目標とする。

---

# 69. Regression

07-A Acceptance前に最低限：

```text
tests.test_build_07_a_stage1
tests.test_build_07_a_stage2
tests.test_build_07_a_stage3
tests.test_build_07_a_stage4
```

および既存test full discoveryを実行する。

さらに：

```text
python -m compileall -q japanese_house_modeler tests
git diff --check
```

を実行する。

実測test countのみAcceptance Recordへ記録する。

---

# 70. Candidate policy

Candidate naming:

```text
Japanese_House_Modeler_Build_07_A_Candidate_r1.zip
Japanese_House_Modeler_Build_07_A_Candidate_r2.zip
...
```

`C:\AI-Blender\Test_Zips` にexact tested commit SHAから作成する。

runtime defect修正時はCandidate番号を増やす。

---

# 71. Acceptance Record

最終的に、

```text
BUILD_07_A_ACCEPTANCE_RECORD.md
```

を作成する。

記録：

- tested production commit
- Git tree SHA
- Candidate ZIP
- automated tests
- Blender runtime evidence
- known defects resolved before acceptance
- unsupported features

---

# 72. Build 07-A acceptance gate

Build 07-AをACCEPTEDとするには、最低限以下が成立すること。

- Top-view 2-point creation works
- Path is canonical and persistent
- draw order and ascent direction are separate
- FORWARD / REVERSE both work
- Stair is standalone
- floor_to_floor contract works
- riser_count contract works
- N risers -> N-1 independent Treads
- run_length / going contract works
- upper arrival is correct
- Upper Floor is not generated
- future Floor connection contract is preserved
- Tread / Riser geometry is deterministic
- Riser generator independence test passes
- dimension edit works
- invalid edit rollback works
- Object Transform remains identity
- stair_id remains stable
- Save / reopen works
- Undo / Redo works
- Editable Mesh finalization works
- prior accepted test suite still passes
- compileall passes
- git diff --check passes

---

# 73. Build 07-A completion statement

07-Aの完成は、

> 「住宅階段の全意匠が完成した」

ことを意味しない。

07-Aの完成は、

> **Wall / Floor / Roomに依存しないManaged Stair Coreが成立し、トップビュー2点Pathから、正しい蹴上・踏板・上階到達関係を持つ直線階段を生成・編集・保存・再生成できる**

ことを意味する。

段々閉じ下面・左右側板は07-Bへ進む。
斜め閉じ下面・踏板前縁仕上げは07-Cへ進む。
Multi-point / L-U / Landingは07-Dへ進む。
Winderは07-Eへ進む。
Open / Support variantsは07-Fへ進む。
