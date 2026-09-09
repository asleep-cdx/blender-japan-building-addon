# 日本住宅モデラー — Build 04-B Specification

## 1. 目的

Build 04-Bでは、Build 04-Aで実装したWall endpoint topologyを利用し、**接続されたWall端点群（junction）の方向関係を読み取り、junction形状を分類する基盤**を実装する。

Build 04-BではMesh形状を変更しない。

目的は、今後の出隅・入隅・T字接合・十字接合・miter / butt処理へ進む前に、

```text
このjunctionは何本のWallで構成されているか
各Wallはjunctionからどの方向へ伸びているか
どのWall同士が直線継続か
2本ならcornerかcontinuationか
3本ならT候補かその他junctionか
4本ならcross候補かその他junctionか
```

を、**保存済みWall data + Build 04-A Connection topologyのみから決定できる状態**にすることである。

---

## 2. 基準状態

Build 04-BはGitHub `main` の以下を基準とする。

- `bbbc540 Implement Build 04-A wall connections`

Build 04-AまでBlender 5.2 LTS実機テスト済み。

Build 04-Aでは以下が確認済み：

- START / END別Connection collection
- PointerPropertyによるtarget Object参照
- 双方向Connection
- 重複防止
- 自己Connection防止
- junction完全相互Connection
- 3本junction
- 4本junction
- endpoint detach / reattach
- Undo
- Object rename後もConnection維持
- .blend保存 / 再読込
- Blender標準Delete後のvalid connection count処理

---

## 3. 親仕様

以下を前提とする。

- `SPECIFICATION.md`
- `BUILD_02_A_SPECIFICATION.md`
- `BUILD_02_B_SPECIFICATION.md`
- `BUILD_02_C_SPECIFICATION.md`
- `BUILD_02_D_SPECIFICATION.md`
- `BUILD_03_A_SPECIFICATION.md`
- `BUILD_03_B_SPECIFICATION.md`
- `BUILD_04_A_SPECIFICATION.md`

Build 04-BはBuild 04-Aまでの実機テスト済み挙動を壊してはならない。

---

# Part A — Build 04-Bの範囲

## 4. 実装する機能

Build 04-Bでは以下を実装する。

- endpointからjunction memberを取得
- junction member数を取得
- 各endpointのjunctionからWall内部へ向かう方向ベクトルを取得
- endpoint pair間の角度を0〜180°で計算
- opposite / straight continuation判定
- same-direction overlap判定
- 2-member junction分類
- 3-member junction分類
- 4-member junction分類
- 5-member以上のgeneric multi-junction分類
- T候補判定
- Cross候補判定
- 2-wall corner angleの算出
- selected Wall START / ENDのclassificationをread-only UI表示
- stale connectionが存在しても分類処理が壊れない
- Connection topologyを一切変更しない
- Meshを一切変更しない
- Undo対象となる新しい編集操作は追加しない

---

## 5. 実装しない機能

以下はBuild 04-Bでは実装しない。

- Mesh trimming
- miter
- butt joint
- 出隅 / 入隅Mesh
- T字Mesh
- cross Mesh
- connected Wallの自動移動
- junctionの自動修正
- junction typeの永続Property保存
- corner typeの永続Property保存
- junction ID
- Wall途中への接続
- segment/intersection snap
- Connection追加 / 解除UI
- user-selected joint style
- wall priority
- finish-side / room-side概念
- 内壁 / 外壁属性
- opening
- door
- window
- floor
- ceiling
- AI間取り図解析

---

# Part B — 重要方針

## 6. classificationは派生データ

Build 04-Bのjunction classificationは**永続保存しない**。

以下から都度計算する。

### Topology

- `start_connections`
- `end_connections`

### Geometry

- `wall.start`
- `wall.end`

したがって、

```text
junction_type = "T"
corner_angle = 90
```

のようなPropertyをJHM_WallPropertiesへ保存してはならない。

理由：

- endpoint移動で方向が変わる
- Connection変更でmember数が変わる
- stale classificationを残さない
- source of truthを増やさない

---

## 7. Meshを参照しない

classificationでMesh vertices / edges / object bounding boxを参照してはならない。

必ず保存済み：

```text
jhm_wall.start
jhm_wall.end
```

を使う。

Edit ModeでMeshを崩してもclassificationは変化しない。

---

## 8. Object Transform

Build 04-Bはread-only classification。

Wall Object Transformがidentityでない場合でも、
分類計算そのものは保存済みWall dataから行える。

ただし、Build 03-A / 03-Bの編集Operatorのtransform拒否方針は変更しない。

Build 04-Bの分類結果はあくまでcanonical saved dataに対する結果である。

---

# Part C — 新しいclassification helper

## 9. 推奨module

新規：

```text
japanese_house_modeler/junctions.py
```

を追加することを推奨する。

役割：

- junction member取得
- endpoint direction
- angle
- classification

Build 04-Aの `connections.py` はTopology操作に集中させる。

---

## 10. connections.pyとの関係

`junctions.py` は必要に応じて以下を再利用してよい。

- `junction_members`
- `is_valid_wall_object`
- `valid_connection_count`
- `connection_collection`

Topologyを変更するhelper：

- `attach_to_junction`
- `detach_endpoint`
- `add_reciprocal`
- `remove_reciprocal`
- `restore_topology`

はclassification中に呼ばない。

---

# Part D — endpoint表現

## 11. endpoint reference

Build 04-Aと同様、

```text
(wall_object, "START")
(wall_object, "END")
```

でendpointを表現してよい。

---

## 12. junction members

classification対象endpointを含むjunction memberは、
Build 04-A `junction_members()` のvalid connected componentを使用する。

isolated endpoint：

```text
Connection count = 0
```

の場合はmember count 1として扱う。

---

# Part E — junctionからWall内部へ向かう方向

## 13. direction定義

classificationでは、各endpointについて
**junction地点から、そのWallの内部へ向かう方向**を使う。

START endpoint：

```text
direction = wall.end - wall.start
```

END endpoint：

```text
direction = wall.start - wall.end
```

XYのみ使用する。

---

## 14. normalize

directionはnormalizeする。

Zは0として扱う。

Wall長がgeometry minimum以下の場合はinvalid memberとして安全に扱う。

通常のmanaged Wallでは発生しないが、例外を出さないこと。

---

## 15. 例

Wall A：

```text
start=(0,0)
end=(4,0)
```

A ENDがjunctionなら、junctionからWall内部方向は：

```text
(-1, 0)
```

Wall B：

```text
start=(4,0)
end=(8,0)
```

B STARTが同じjunctionなら：

```text
(+1, 0)
```

この2本は180° oppositeであり、straight continuation。

---

# Part F — angle計算

## 16. pair angle

2 endpoint directionの角度を：

```text
0° <= angle <= 180°
```

で返す。

dot productを[-1, 1]へclampしてからacos等で計算する。

---

## 17. angle意味

```text
0°
```

同じ方向へ重なる。

```text
90°
```

直角corner。

```text
180°
```

一直線に反対方向へ伸びる。

---

## 18. tolerance

浮動小数誤差・自由角度作図を考慮してangular toleranceを持つ。

Build 04-B推奨：

```text
_ANGLE_TOLERANCE_DEG = 1.0
```

### opposite

```text
abs(angle - 180°) <= 1°
```

### same direction

```text
angle <= 1°
```

とする。

---

## 19. exact 90°はT条件ではない

T-junctionの分類条件は「90°であること」ではない。

T候補は：

```text
3 member
+
その中に1組のstraight continuation pairが存在
+
残り1本がそのstraight lineとsame-direction / oppositeではない
```

で判定する。

したがって3本目は90°でなくてもT候補。

例：

```text
30°
45°
90°
```

などのbranch angleでも、
他の2本がstraight continuationならT候補とする。

---

# Part G — classification enum

## 20. 内部分類

内部classification keyは英字固定値を推奨する。

例：

```text
ISOLATED
CONTINUATION
CORNER
OVERLAP
T_JUNCTION
THREE_WAY
CROSS
FOUR_WAY
MULTI
INVALID
```

UIでは日本語表示へ変換する。

---

# Part H — 1-member

## 21. ISOLATED

Connectionなしのendpoint。

```text
member_count = 1
classification = ISOLATED
```

UI：

```text
未接続
```

---

# Part I — 2-member junction

## 22. CONTINUATION

2本のdirection angleが180°±tolerance。

```text
classification = CONTINUATION
```

UI例：

```text
直線継続 (180.0°)
```

---

## 23. OVERLAP

2本のdirection angleが0°±tolerance。

```text
classification = OVERLAP
```

UI例：

```text
同方向重複 (0.0°)
```

これは正常な建築jointとは限らないため、
corner扱いしない。

---

## 24. CORNER

2本で、

- CONTINUATIONでない
- OVERLAPでない

場合：

```text
classification = CORNER
```

UI例：

```text
コーナー (90.0°)
コーナー (45.0°)
```

---

## 25. corner angle

2-member CORNERではdirection間角度をUI表示する。

このangleは0〜180°。

Build 04-Bでは「内角 / 外角」はまだ決定しない。

単にWall core direction同士の小さい方の角度を表示する。

---

# Part J — 3-member junction

## 26. T_JUNCTION

3 membersのpair全3組を調べ、

**exactly one opposite pair**

が存在する場合、基本的に：

```text
classification = T_JUNCTION
```

とする。

残り1本がstraight pairのどちらかとsame-directionである場合は
overlap ambiguityとしてT扱いしない。

---

## 27. THREE_WAY

3 membersだがstraight continuation pairがない場合：

```text
classification = THREE_WAY
```

UI：

```text
3方向接続
```

例：

- Y字
- 120° + 120° + 120°
- 45° / 135° / その他

---

## 28. 3-member overlap ambiguity

same-direction pairを含むなど、
duplicate / overlapの可能性がある場合でもPython errorにしない。

分類：

```text
THREE_WAY
```

または内部補助flag：

```text
has_overlap = True
```

を返してよい。

Build 04-Bでは新しい永続typeを増やす必要はない。

---

# Part K — 4-member junction

## 29. CROSS

4 membersの中に、
memberを重複使用しない**2組のopposite pair**が存在する場合：

```text
classification = CROSS
```

とする。

典型：

```text
左 ↔ 右
上 ↔ 下
```

---

## 30. X型cross

2本のstraight lineが90°で交差している必要はない。

例：

```text
0° / 180°
45° / 225°
```

でも2組のstraight continuationがあればCROSS。

---

## 31. FOUR_WAY

4 membersだが、
全memberを2組のopposite pairへ分割できない場合：

```text
classification = FOUR_WAY
```

UI：

```text
4方向接続
```

---

## 32. opposite pair探索

4-member CROSS判定ではpairを貪欲に1つ選んで終わらせない。

4 endpointすべてを重複なく使うpairingが存在するか調べる。

4本なので全組合せ探索で十分。

---

# Part L — 5-member以上

## 33. MULTI

5 members以上：

```text
classification = MULTI
```

UI：

```text
多方向接続 (5)
```

など。

Build 04-Bでは詳細分類しない。

---

# Part M — classification result

## 34. result構造

小さなdict / namedtuple / dataclass等を使用してよい。

概念：

```text
classification
member_count
members
directions
pair_angles
corner_angle
opposite_pairs
has_overlap
```

必要なものだけ保持する。

過剰なclass hierarchyは作らない。

---

## 35. side effect禁止

classification helperはread-only。

呼び出しても：

- Connection collection
- start/end
- Mesh
- selection
- active Object

を変更しない。

---

# Part N — UI

## 36. selected Wall UI

Build 04-A：

```text
壁厚: 130.0 mm
壁高さ: 2500.0 mm

始点接続: 1
終点接続: 0
```

へclassificationを追加する。

---

## 37. UI例

### corner

```text
始点接続: 1
始点形状: コーナー (90.0°)

終点接続: 0
終点形状: 未接続
```

### continuation

```text
始点接続: 1
始点形状: 直線継続 (180.0°)
```

### T

3-member junctionでは各member endpointのConnection countは2。

```text
始点接続: 2
始点形状: T字候補
```

### Cross

4-member junctionでは各member endpoint countは3。

```text
終点接続: 3
終点形状: 十字候補
```

---

## 38. UI名称

推奨日本語：

```text
ISOLATED      -> 未接続
CONTINUATION  -> 直線継続
CORNER        -> コーナー
OVERLAP       -> 同方向重複
T_JUNCTION    -> T字候補
THREE_WAY     -> 3方向接続
CROSS         -> 十字候補
FOUR_WAY      -> 4方向接続
MULTI         -> 多方向接続
INVALID       -> 判定不能
```

---

## 39. read-only

classification表示はread-only。

button / dropdownを追加しない。

---

# Part O — 位置一致について

## 40. classificationはTopologyを信頼

Build 04-BではConnection topologyがsource of truth。

connected endpointsについて、
座標が完全一致しているかを分類前提にしない。

理由：

- topologyとgeometryのvalidationは別責務
- endpoint移動transactionで通常は一致する
- Object Transform異常や外部編集で不整合が起こりうる
- classification自体はConnection memberの方向関係を読む

---

## 41. optional validation

任意で、
junction membersのsaved endpoint座標が一定tolerance内で一致するかチェックし、

```text
positions_consistent
```

等のread-only flagをresultに含めてもよい。

ただしBuild 04-B完了条件には必須ではない。

Topologyを自動修正してはならない。

---

# Part P — stale / deleted Wall

## 42. deleted target

Build 04-Aのvalid wall判定を再利用する。

削除済みWallはjunction memberに含めない。

classification UIがエラーを出してはならない。

---

## 43. stale collection

stale Connection entryをclassification中にpurgeしなくてよい。

read-only helperとして無視するだけでよい。

---

# Part Q — Object rename / save

## 44. rename

Object rename後もclassificationは変化しない。

PointerProperty topologyを使用する。

---

## 45. save / reopen

.blend保存→再読込後も、
Connection topologyが復元されるためclassificationも同じ結果になること。

classification自体を保存しない。

---

# Part R — endpoint移動との関係

## 46. endpoint移動

Build 03-A / 04-Aのendpoint移動後、

- start/end
- Connection

が更新されれば、
次のUI drawでclassificationが自動的に再計算される。

update callback等は不要。

---

## 47. corner angle更新

例：

2-wall cornerを90°から45°へendpoint移動した場合：

```text
コーナー (90.0°)
```

から：

```text
コーナー (45.0°)
```

へ自動更新。

永続angle Propertyは不要。

---

## 48. corner -> continuation

2-wall cornerのWall方向を変更し、
一直線になった場合：

```text
CORNER
```

から：

```text
CONTINUATION
```

へ自動更新。

---

# Part S — dimension edit

## 49. 壁厚

壁厚変更ではdirectionが変わらないためclassification不変。

---

## 50. 壁高さ

壁高さ変更でもclassification不変。

---

# Part T — Edit Mode

## 51. Meshのみ変形

Edit ModeでMeshを変形しても、
saved start/endは変わらない。

したがってclassificationも変わらない。

これは仕様どおり。

---

# Part U — ファイル変更

## 52. 主な変更対象

推奨：

```text
japanese_house_modeler/junctions.py   new
japanese_house_modeler/ui.py
```

必要に応じて：

```text
japanese_house_modeler/connections.py
```

へread-only helperを小さく追加してよい。

---

## 53. 原則変更しない

```text
properties.py
operators.py
__init__.py
```

Build 04-Bでは新しいPropertyGroup / Operatorを追加しないため、
原則変更不要。

もし変更が必要なら理由を明確にする。

---

## 54. no registration

単なるPython helper module `junctions.py` はBlender class registration不要。

`__init__.py` の `_CLASSES` へ追加しない。

---

# Part V — 回帰制限

## 55. connections.py

Build 04-Aで実機確認済みの：

- attach
- detach
- clique
- snapshot
- restore
- stale target判定

を壊さない。

classificationの都合でTopology mutation semanticsを変更しない。

---

## 56. operators.py

Build 04-A endpoint connection操作を変更しない。

04-BではOperator修正を避ける。

---

## 57. geometry

Wall Mesh geometry式を変更しない。

---

# Part W — 実機テスト

## 58. テストA — isolated

Wallを1本作成。

START / END：

```text
接続: 0
形状: 未接続
```

---

## 59. テストB — 90° corner

2本を90°でdirect snap。

該当endpoint：

```text
接続: 1
形状: コーナー (90.0°)
```

両Wallで同じ分類。

---

## 60. テストC — 45° corner

45°で2本接続。

```text
コーナー (45.0°)
```

前後1°程度の丸め差は許容。

---

## 61. テストD — straight continuation

Wall A ENDとWall B STARTを、
180°反対方向へ伸びるよう接続。

```text
接続: 1
形状: 直線継続 (180.0°)
```

---

## 62. テストE — same-direction overlap

同じjunctionから同じ方向へ2本Wallを伸ばす。

```text
同方向重複 (0.0°)
```

cornerやcontinuationにならない。

---

## 63. テストF — T 90°

3本junction：

```text
左
右
上
```

左/右がstraight continuation。

各該当endpoint：

```text
接続: 2
形状: T字候補
```

---

## 64. テストG — T斜めbranch

straight continuation pair + 45° branch。

```text
T字候補
```

であること。

branchが90°でないことによってTHREE_WAYにならない。

---

## 65. テストH — Y字

3本ともstraight pairを持たない。

例：

```text
0°
120°
240°
```

期待：

```text
3方向接続
```

---

## 66. テストI — Cross 90°

4本：

```text
左
右
上
下
```

期待：

```text
接続: 3
形状: 十字候補
```

---

## 67. テストJ — X型Cross

4本で2組のstraight continuationが斜め交差。

期待：

```text
十字候補
```

90°交差に限定されない。

---

## 68. テストK — irregular 4-way

4本だが2組のopposite pairを作れない。

期待：

```text
4方向接続
```

---

## 69. テストL — 5-way

5本junction。

期待：

```text
接続: 4
形状: 多方向接続 (5)
```

または同等表示。

---

## 70. テストM — endpoint移動で再分類

90°cornerを作る。

一方のendpoint編集で方向を45°へ変更。

期待：

```text
コーナー (90.0°)
↓
コーナー (45.0°)
```

---

## 71. テストN — corner -> continuation

2-wall cornerを端点編集し、
一直線へ変更。

期待：

```text
コーナー
↓
直線継続
```

---

## 72. テストO — Tから1本detach

T junctionからbranch Wallをfree位置へ移動。

残った2本がstraight pairなら：

```text
T字候補
↓
直線継続
```

branch側：

```text
未接続
```

---

## 73. テストP — deleted target

connected target Wallを標準Delete。

残ったendpoint：

```text
接続: 0
形状: 未接続
```

Python errorなし。

---

## 74. テストQ — rename

connected Wallをrename。

classification不変。

---

## 75. テストR — save / reopen

T / Cross junctionを保存しBlender再起動。

classificationが同じ。

---

## 76. テストS — dimension edit

corner / T / Cross状態で壁厚・壁高さを変更。

classification不変。

---

## 77. テストT — Edit Mode Mesh変形

Meshだけ崩す。

classification不変。

---

# Part X — 数値テスト

## 78. helper unit test推奨

Codex環境ではBlender GUIなしでも、
可能ならdirection / angle / classification部分をpure Pythonに近い形でテストする。

最低限：

```text
2-member 180 -> CONTINUATION
2-member 90  -> CORNER
2-member 0   -> OVERLAP
3-member T
3-member no opposite -> THREE_WAY
4-member two opposite pairs -> CROSS
4-member irregular -> FOUR_WAY
5-member -> MULTI
```

---

# Part Y — 完了条件

## 79. Build 04-B完了条件

Blender 5.2 LTS実機で以下を満たす。

- classificationはsaved start/end + Connectionのみから算出
- Meshを参照しない
- classificationを永続保存しない
- isolated判定
- 2-wall continuation判定
- 2-wall corner判定
- 2-wall overlap判定
- corner angle表示
- 3-wall T候補判定
- 3-wall generic判定
- 4-wall Cross候補判定
- 4-wall generic判定
- 5+ multi判定
- T branchは90°に限定しない
- Cross linesは90°交差に限定しない
- endpoint移動後に自動再分類
- detach後に自動再分類
- deleted targetでエラーなし
- rename後も分類維持
- save/reopen後も同じ分類
- Build 04-A Connection操作に回帰不具合なし
- Build 03-B以前に回帰不具合なし

---

# Part Z — Build 04-C候補

## 80. 次段階

Build 04-Bでjunction分類が安定した後、
Build 04-Cでは**2-wall endpoint jointの幾何処理設計**へ進む。

最初からT/Cross全部をMesh化せず、
まず2-wall junction：

```text
CONTINUATION
CORNER
```

を対象にすることを推奨。

---

## 81. Build 04-C候補

2-wall cornerについて、

- wall core directions
- wall thickness
- inner / outer boundary line
- line intersection
- miter point
- butt termination
- unequal thickness

を解析し、

「どのMesh端部頂点をどこへ置くか」

を数学的に確立する。

---

## 82. 出隅 / 入隅

Build 04-Bのangleだけでは出隅 / 入隅はまだ確定しない。

将来、

- Wall orientation
- junction ordering
- room / interior side
- wall side semantics

との関係を設計した上で分類する。

そのためBuild 04-Bでは無理に出隅 / 入隅を判定しない。
