# 日本住宅モデラー — Build 04-C Specification

## 1. 目的

Build 04-Cでは、Build 04-AのConnection topologyとBuild 04-Bのjunction classificationを利用し、
**2本のWallが1つのendpoint junctionで接続している場合の実際のWall Mesh端部処理**を実装する。

Build 04-Cで実装するMesh jointは、まず以下の2種類に限定する。

```text
CONTINUATION
CORNER
```

- `CONTINUATION`：一直線に続く2本のWall
- `CORNER`：0°/180°以外の2本のWall

`CORNER`では、2本のWall厚を考慮した**対称miter（留め接合）**を生成する。

Build 04-CではT字・十字・3方向・4方向・5本以上のMesh jointはまだ実装しない。

---

## 2. 基準状態

Build 04-CはGitHub `main` の以下を基準とする。

- `d2aaa29 Implement Build 04-B junction classification`

Build 04-BまでBlender 5.2 LTS実機テスト済み。

Build 04-Bで実機確認済み：

- 未接続
- 90° corner
- 45° corner
- straight continuation
- same-direction overlap
- T junction
- angled T branch
- generic 3-way
- Cross
- angled X Cross
- irregular 4-way
- 5-way MULTI
- endpoint移動後の再分類
- Build 04-A topology回帰なし

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
- `BUILD_04_B_SPECIFICATION.md`

Build 04-CはBuild 04-Bまでの実機テスト済み挙動を壊してはならない。

---

# Part A — Build 04-Cの範囲

## 4. 実装する機能

Build 04-Cでは以下を実装する。

- 2-member `CORNER` junctionのmiter Mesh
- 2-member `CONTINUATION` junctionのsquare butt Mesh
- unequal wall thickness対応
- arbitrary corner angle対応
- Wall START / END双方でjoint処理
- 1本のWallが両端で2-wall corner接続される場合への対応
- 新規Wall direct snap作成後のjoint自動再生成
- endpoint移動後の旧junction / 新junction Mesh自動再生成
- dimension edit後のjoint Mesh自動再生成
- 3本目追加で2-member cornerから3-member junctionになった場合、既存miterをsquareへ戻す
- 3-member junctionから1本detachして2-memberになった場合、残る2本を自動的に2-wall jointへ更新
- Material slots維持
- Object identity維持
- canonical start/end維持
- Connection topology維持
- Undo
- atomic batch mesh update
- unsafe miterの安全fallback
- selected Wallからjoint Meshを再生成できる手動repair/rebuild Operator
- read-only joint状態UI

---

## 5. 実装しない機能

以下はBuild 04-Cでは実装しない。

- T junction Mesh
- Cross Mesh
- generic 3-way Mesh
- generic 4-way Mesh
- 5+ multi-junction Mesh
- 出隅 / 入隅という意味分類
- room side
- interior / exterior side
- finish side
- wall priority
- butt priority
- user-selectable joint style
- Wall途中へのT接続
- segment intersection
- opening
- door
- window
- floor
- ceiling
- AI間取り図解析
- standard Blender Deleteの自動depsgraph監視
- Shift+D duplicate topology repair

---

# Part B — source of truth

## 6. canonical Wall dataを変更しない

Build 04-CでもWallのsource of truthは以下。

```text
jhm_wall.start
jhm_wall.end
jhm_wall.wall_thickness
jhm_wall.wall_height
Connection topology
```

miter Mesh頂点は派生データ。

---

## 7. Meshから逆算しない

joint処理後、Mesh endpointはcanonical centerline endpointより外側/内側へ伸びることがある。

それでも：

```text
wall.start
wall.end
```

を書き換えてはならない。

Lengthも引き続き保存しない。

---

## 8. centerline endpoint

Connection junction位置は保存済みWall centerline endpoint。

miter geometryがこの点を越えても、
Connection位置そのものは変化しない。

---

# Part C — joint対応classification

## 9. CORNER

Build 04-B：

```text
classification == CORNER
member_count == 2
```

の場合のみmiter対象。

---

## 10. CONTINUATION

```text
classification == CONTINUATION
member_count == 2
```

では、両WallのMesh endpointをcanonical junction位置でsquare buttとする。

現在のcuboid端部と同じ。

---

## 11. その他

以下はBuild 04-Cではsquare endpointを使用する。

```text
ISOLATED
OVERLAP
T_JUNCTION
THREE_WAY
CROSS
FOUR_WAY
MULTI
INVALID
```

つまりT/Cross等は分類表示されても、
Mesh jointはまだ生成しない。

---

# Part D — 新しいjoint geometry helper

## 12. 推奨module

新規：

```text
japanese_house_modeler/joints.py
```

を推奨する。

役割：

- endpoint square points
- 2-wall miter intersection
- miter safety validation
- endpoint joint status
- Wall polygon endpoint pair取得

`junctions.py` はclassificationに集中させる。

---

## 13. geometry builderの整理

現在 `operators.py` の：

```python
JHM_OT_create_wall._wall_geometry()
```

は単純cuboidを生成している。

Build 04-Cでは、canonical Wall Objectからjoint-aware Meshを生成できる共通helperを追加する。

推奨concept：

```text
build_wall_geometry(wall_object)
```

または：

```text
wall_lower_outline(wall_object)
wall_vertices_faces(wall_object)
```

実際の関数名は任せる。

---

## 14. preview用validation

新規Wall作成やendpoint移動の「長さが有効か」判定のため、
既存 `_wall_geometry(start, end)` を完全に削除する必要はない。

ただし正式Meshの最終生成はjoint-aware helperをsource of truthにすること。

不要な全面リファクタリングは避ける。

---

# Part E — endpoint方向とside

## 15. endpoint direction

Build 04-Bと同じ。

START：

```text
u = normalize(end - start)
```

END：

```text
u = normalize(start - end)
```

junctionからWall内部へ向かう方向。

---

## 16. endpoint perpendicular

```text
n = (-u.y, u.x)
```

とする。

---

## 17. half thickness

```text
h = wall_thickness_mm / 2000
```

meters。

---

## 18. square endpoint pair

junction位置 `J` に対し：

```text
P_plus  = J + n * h
P_minus = J - n * h
```

をsquare endpoint pairとする。

この順番は「endpointからWall内部へ向かう方向u」に対するplus/minus。

---

# Part F — 2-wall miter数学

## 19. 前提

Wall A endpoint：

```text
J_A
u_A
n_A
h_A
```

Wall B endpoint：

```text
J_B
u_B
n_B
h_B
```

通常のConnectionでは：

```text
J_A == J_B
```

---

## 20. shared junction位置

正常ケースでは同一座標。

Build 04-Cではsaved endpoint座標が一定tolerance以内であることを確認する。

推奨：

```text
_JOINT_POSITION_TOLERANCE_M = 1e-6
```

これを超えてズレている場合miterしない。

square fallback。

Topologyを自動修正しない。

---

## 21. side boundary line

Wall Aのplus side：

```text
L_A_plus(t) = J_A + n_A*h_A + t*u_A
```

Wall Aのminus side：

```text
L_A_minus(t) = J_A - n_A*h_A + t*u_A
```

Wall Bも同様。

---

## 22. miter endpoint P_plus

Wall Aのplus側endpoint vertexは：

```text
intersection(
    L_A_plus,
    L_B_minus
)
```

とする。

---

## 23. miter endpoint P_minus

Wall Aのminus側endpoint vertexは：

```text
intersection(
    L_A_minus,
    L_B_plus
)
```

とする。

---

## 24. cross-side pairing

重要：

```text
A plus  <-> B minus
A minus <-> B plus
```

のcross-side intersectionを使用する。

same-sign pairingではない。

これにより2本のWallが同じshared miter edgeを持つ。

---

## 25. partner側

Wall B側から同じ計算を行うと、
同じ2 intersection pointが逆順で得られること。

つまり両Wallのend faceが同一線上で一致する。

---

# Part G — line intersection

## 26. 2D line intersection

2D line：

```text
p + t*r
q + s*d
```

のintersectionをcross productで計算してよい。

---

## 27. parallel

```text
abs(cross(r, d))
```

が小さい場合intersectionなし。

CORNER classificationでも極端にparallelへ近い異常値があり得るため安全にfallback。

---

## 28. segmentではなくinfinite line

side boundaryは無限直線として交点を計算する。

`t < 0` のintersectionもmiterでは正常にあり得る。

単純にrejectしない。

---

# Part H — miter safety

## 29. 鋭角による巨大miter

角度が0°へ近い場合、
miter pointがjunctionから非常に遠くなる。

無制限に許可しない。

---

## 30. miter limit

推奨：

```text
_MAX_MITER_FACTOR = 10.0
```

reference：

```text
max(h_A, h_B)
```

各miter pointについて：

```text
distance(point, J) <= max(h_A, h_B) * _MAX_MITER_FACTOR
```

を要求。

---

## 31. fallback

limit超過時：

- Python errorを出さない
- topologyを変更しない
- square endpointへfallback
- UI joint statusで安全fallbackであることを示す

---

## 32. 15°拘束との関係

Shift作図の最小通常corner stepは15°。

equal thicknessならfactor 10程度で15° miterを許容できる。

1〜数度の自由角cornerで極端なmiterが発生することを防ぐ目的。

---

# Part I — Wall lower outline

## 33. 基本順序

現在のWall lower polygonはstart→end core axisに対し概念的に：

```text
start_plus
start_minus
end_minus
end_plus
```

---

## 34. endpoint local pair

START endpointでは：

```text
endpoint u = +core axis
endpoint n = +global perpendicular
```

したがって：

```text
START P_plus  -> start_plus
START P_minus -> start_minus
```

---

## 35. END endpoint

ENDでは：

```text
endpoint u = -core axis
endpoint n = -global perpendicular
```

したがってendpoint local：

```text
END P_plus  -> end_minus
END P_minus -> end_plus
```

となる。

---

## 36. 共通化

よって、

```text
START pair = (local_plus, local_minus)
END pair   = (local_plus, local_minus)
```

を取得し、

lower polygon：

```text
start_pair[0],
start_pair[1],
end_pair[0],
end_pair[1]
```

とすれば現在のvertex windingと整合する設計が可能。

実装は必ずface windingを実機確認する。

---

# Part J — height

## 37. Z

lower outline Z=0。

upper outlineは同じXYで：

```text
Z = wall_height_mm / 1000
```

---

## 38. unequal height

接続Wall同士のheightが違ってもBuild 04-Cでは許可。

各Wallは自身のheightを使用する。

高さ方向の追加trimはしない。

---

# Part K — unequal thickness

## 39. thickness別計算

Wall A / Bでwall_thicknessが違う場合、
それぞれ：

```text
h_A
h_B
```

を使用してoffset line intersectionを計算。

---

## 40. shared face

unequal thicknessでもcross-side intersectionにより、
2本が同じ2D miter edgeを共有すること。

---

# Part L — final polygon validation

## 41. invalid polygon防止

両端miter等によりWall lower polygonが自己交差・退化してはいけない。

joint-aware geometry builderは最低限：

- 4点がfinite
- polygon areaが十分
- side edgesが異常に交差しない
- height > 0

を確認する。

---

## 42. fallback方針

joint endpointを適用するとWall polygonがinvalidになる場合：

1. そのendpointをsquareへfallback
2. 再validation
3. それでもinvalidならgeometry generation failure

とする設計を推奨。

通常の住宅寸法でfailureしないこと。

---

# Part M — joint status

## 43. read-only status

Build 04-Bの形状表示に加え、
joint Meshの実際の処理状態を表示してよい。

推奨：

```text
始点接合: 未接続
始点接合: マイター
始点接合: 直線
始点接合: 未対応
始点接合: 安全フォールバック
```

---

## 44. status意味

例：

```text
ISOLATED
-> 未接続

CORNER + valid miter
-> マイター

CONTINUATION
-> 直線

T/CROSS/MULTI/OVERLAP
-> 未対応

CORNER but unsafe
-> 安全フォールバック
```

---

## 45. statusは保存しない

junction classification同様、
joint statusも派生計算。

Propertyへ保存しない。

---

# Part N — affected Walls

## 46. 重要原則

1つのWall操作で、
接続相手WallのMeshも更新が必要になる。

Build 04-Cでは単一Objectだけをregenして終わらない。

---

## 47. 新規Wall作成

新規Wallをdirect snapで作成した後：

- 新規Wall
- START junctionの全member
- END junctionの全member

をaffected setとする。

重複Objectは1回だけregen。

---

## 48. 3本目追加

2-wall corner：

```text
A <-> B
```

がmiter済み。

そこへCをsnapして3-memberになった場合：

```text
A
B
C
```

全3 Wallをregen。

Build 04-Cでは3-member joint未対応なので、
A/Bの既存miterもsquare endpointへ戻る。

---

## 49. endpoint移動前 old junction

endpoint move開始後、確定直前に、
移動対象endpointの**old junction members**をsnapshotする。

---

## 50. endpoint移動後 new junction

detach / attach後に：

- old junction members
- new junction members
- moved Wall

をaffected setとする。

---

## 51. 3→2 member

3-member junctionから1本をfree位置へ移動。

残った2本がCORNERなら、
その2本は自動miter。

CONTINUATIONならsquare butt。

---

## 52. dimension edit

Wall thickness変更はcorner miter位置を変える。

したがって：

- edited Wall
- START junction member
- END junction member

をaffected setとしてregen。

---

## 53. height-only

heightだけの変更ならpartner XYは変化しないが、
実装簡潔性のため同じaffected setをregenしてよい。

---

# Part O — batch mesh regeneration

## 54. 新helper

複数Wall Objectをatomicにregenするhelperを追加する。

概念：

```text
regenerate_wall_meshes(objects)
```

---

## 55. build first

推奨transaction：

1. affected valid Wall list確定
2. 各Wallの新geometryを計算
3. 各new Meshを作成
4. Material slotsをcopy
5. **全new Meshが正常に完成した後**
6. Object.dataを一括swap
7. old Mesh orphanを削除

---

## 56. partial failure

途中で1つでもgeometry / Mesh生成に失敗したら：

- Object.dataをswapしない
- 作成済みnew Meshを削除
- 既存Meshを完全維持

---

## 57. swap failure

swap途中で例外が起きた場合：

- swap済みObjectをold Meshへ戻す
- new Meshを削除
- old Meshを維持

---

## 58. Material

各Wallのold Mesh materialsを順番維持してnew Meshへcopy。

Build 03-A / 03-BのMaterial保持を壊さない。

---

# Part P — operation transaction

## 59. topology + canonical + mesh

endpoint moveやnew wall createでは、
Connection topologyとcanonical dataとMeshを一つのtransactionとして扱う。

---

## 60. endpoint move推奨順

概念：

1. old start/end snapshot
2. old topology snapshot
3. old junction member set取得
4. new candidate validation
5. canonical endpoint更新
6. detach / attach
7. new junction member set取得
8. affected Wall joint-aware Meshをbuild
9. 全Mesh swap
10. success

failure：

- canonical start/end restore
- topology restore
- Mesh restore
- partial new Mesh remove

---

## 61. dimension edit

概念：

1. old thickness/height
2. affected member set
3. new thickness/heightをcanonicalへ一時反映
4. affected Wall Meshをjoint-aware build
5. swap
6. success

failure：

- thickness/height restore
- old Mesh維持

---

## 62. new Wall create

概念：

1. existing topology snapshot
2. Wall Object生成
3. canonical data設定
4. Connection attach
5. affected set取得
6. affected joint-aware Mesh build/swap
7. success

failure：

- existing topology restore
- existing Wall Mesh restore
- new Wall Object/Mesh削除

---

# Part Q — Undo

## 63. new Wall Undo

2-wall cornerとして新規Wallを追加し、
既存Wallもmiterへ変わった後Ctrl+Z。

期待：

- new Wall削除
- Connection復元
- existing Wall Meshも作成前squareへ戻る

---

## 64. endpoint move Undo

corner connection変更後Ctrl+Z：

- moved Wall canonical endpoint
- topology
- moved Wall Mesh
- old partner Mesh
- new partner Mesh

すべて元へ戻る。

---

## 65. dimension Undo

connected corner Wall thickness変更後Ctrl+Z：

- thickness
- edited Wall miter
- partner Wall miter

すべて旧状態へ戻る。

---

# Part R — manual rebuild / repair

## 66. 必要性

Build 04-Cではstandard Blender Deleteを監視するdepsgraph handlerはまだ追加しない。

そのため、miter済みpartnerを標準Deleteした直後、
残存WallのMeshには旧miter形状が残る可能性がある。

---

## 67. repair Operator

selected managed Wallについてjoint-aware Meshを再生成する手動Operatorを追加する。

推奨：

```text
jhm.rebuild_wall_joints
```

UI：

```text
[ 接合を再生成 ]
```

---

## 68. repair affected set

selected Wallだけでなく：

- selected START junction members
- selected END junction members

をregenする。

stale targetは無視。

---

## 69. delete後repair

partnerを標準Delete後、
残存Wallを選択して「接合を再生成」。

期待：

- valid connection count 0
- classification 未接続
- old miter Meshがsquare endpointへ戻る

---

## 70. Undo

manual rebuild Operatorは：

```text
REGISTER
UNDO
```

とする。

---

# Part S — Object Transform

## 71. canonical geometry

joint solverはsaved canonical dataを使う。

---

## 72. transformed partner

2-wall junctionのmemberにnon-identity Object Transform Wallが含まれる場合、
Build 04-Cではそのjunctionをmiter対象にしない。

square fallback。

理由：

- canonical saved endpointとvisual Mesh位置が一致しない可能性
- partnerを勝手にtransform bakeしない

---

## 73. existing edit refusal

Build 03-A / 03-Bのtransform拒否を変更しない。

---

# Part T — Edit Mode manual mesh divergence

## 74. manual Mesh

Edit ModeでMeshを手動変更してもcanonical data / topologyは変わらない。

---

## 75. managed regeneration

以下のmanaged operationを行った場合：

- endpoint move
- dimension edit
- connection change
- 接合を再生成

joint-aware Meshをcanonical dataから再生成する。

手動Mesh divergenceは破棄される。

Build 03-A / 03-Bの思想を維持。

---

# Part U — existing Build 04-A files

## 76. connections.py

Topology semanticsを変更しない。

必要ならaffected member収集で既存helperを利用。

---

## 77. junctions.py

Build 04-B classificationをsourceとして利用。

classification semanticsをjoint都合で変更しない。

---

# Part V — UI

## 78. selected Wall

概念：

```text
壁厚: 130.0 mm
壁高さ: 2500.0 mm

始点接続: 1
始点形状: コーナー (90.0°)
始点接合: マイター

終点接続: 0
終点形状: 未接続
終点接合: 未接続

[ 壁寸法を変更 ]
[ 接合を再生成 ]

[ 始点を移動 ]
[ 終点を移動 ]
```

---

## 79. T junction

```text
始点接続: 2
始点形状: T字候補
始点接合: 未対応
```

Meshはsquare endpoint。

---

# Part W — 実機テスト

## 80. Test A — isolated regression

単独Wall。

期待：

- Meshは従来cuboid
- 接合: 未接続

---

## 81. Test B — 90° equal thickness corner

130mm / 130mm。

2本を90° direct snap。

期待：

- classification コーナー90°
- 両Wall 接合: マイター
- top viewでcornerにgapなし
- 不要な重複なし
- shared diagonal miter faceが一致

---

## 82. Test C — 45° equal thickness

45° corner。

期待：

- miter
- gapなし
- shared cut一致
- extreme spikeなし

---

## 83. Test D — 15° corner

Shift 15°でcorner。

期待：

- factor limit内
- miter生成
- finite geometry
- Blender表示正常

---

## 84. Test E — very acute free corner

例2〜3°程度。

期待：

- miter limit超過なら安全fallback
- Python errorなし
- 巨大spikeなし
- UI 安全フォールバック

---

## 85. Test F — unequal thickness 90°

例：

```text
Wall A 130 mm
Wall B 200 mm
```

期待：

- miter shared edge一致
- gapなし
- thickness値維持

---

## 86. Test G — continuation

180°2本。

期待：

- classification 直線継続
- 接合: 直線
- square butt
- gapなし
- miter斜面なし

---

## 87. Test H — overlap

0°2本。

期待：

- 同方向重複
- 接合: 未対応
- square endpoint
- crashなし

---

## 88. Test I — both endpoints

中央WallのSTART/ENDそれぞれ別Wallと2-wall CORNER接続。

期待：

- 中央Wall両端miter
- Mesh polygon正常
- face winding正常

---

## 89. Test J — add third wall

A-B corner miter済みjunctionへCをdirect snap。

期待：

- classification Tまたは3方向
- A/B/Cの接合表示 未対応
- A/Bの旧miterがsquareへ戻る

---

## 90. Test K — detach third wall

Test JからCをfree位置へ移動。

残るA-BがCORNER。

期待：

- A-B自動miter復活
- C square

---

## 91. Test L — move corner angle

90°cornerからendpoint編集で45°cornerへ。

期待：

- both Wall miter geometry更新
- Connection維持
- angle表示45°

---

## 92. Test M — move away

A-B cornerからA endpointをfree位置へ。

期待：

- A square
- B square
- connection 0
- old miter残らない

---

## 93. Test N — reconnect different partner

A-B cornerからAをCへdirect snap。

期待：

- B squareへ戻る
- A/C new miter
- topology正しい

---

## 94. Test O — thickness edit

A-B 90°corner。

A thickness 130→200。

期待：

- A/B両方miter位置更新
- shared edge維持
- Material維持

---

## 95. Test P — height edit

A height変更。

期待：

- A height変更
- miter XY正しい
- B geometry破損なし

---

## 96. Test Q — Ctrl+Z new Wall

既存AへBをsnapしmiter化。

Ctrl+Z。

期待：

- B削除
- Aが元のsquareへ戻る
- topology元へ戻る

---

## 97. Test R — Ctrl+Z endpoint move

corner partner変更。

Ctrl+Z。

期待：

- old partner miter復元
- new partner square
- moved Wall旧miter復元
- topology復元

---

## 98. Test S — Ctrl+Z dimension

thickness変更後Ctrl+Z。

期待：

- thickness復元
- both Wall miter旧位置復元

---

## 99. Test T — material

cornerの両WallへMaterial。

dimension / endpoint update後もMaterial維持。

---

## 100. Test U — Edit Mode divergence

miter WallをEdit Modeで崩す。

「接合を再生成」。

期待：

- canonical joint-aware shapeへ戻る
- Connection維持

---

## 101. Test V — standard Delete repair

A-B miter。

BをBlender標準Delete。

A：

- valid connection count 0
- classification 未接続
- Meshは一時旧miterの可能性あり

「接合を再生成」。

期待：

- A square endpointへrepair

---

## 102. Test W — save/reopen

miter cornerを保存しBlender再起動。

Mesh shape / topology / classification維持。

---

## 103. Test X — Build 04-B regression

各classification表示が以前どおり。

joint Mesh implementationによって分類が変化しない。

---

# Part X — Codex static tests

## 104. math tests

最低限pure/mocked test：

- 90° equal thickness intersection
- 45° equal thickness
- 15°
- unequal thickness
- partner side produces same shared points reversed
- 180° no miter
- near-parallel fallback
- position mismatch fallback
- miter factor fallback

---

## 105. polygon tests

- one miter endpoint
- both miter endpoints
- finite vertex
- nonzero area
- no basic self-intersection

---

# Part Y — 変更ファイル候補

## 106. 推奨

```text
japanese_house_modeler/joints.py              new
japanese_house_modeler/operators.py
japanese_house_modeler/ui.py
japanese_house_modeler/__init__.py
```

`__init__.py` はrepair Operatorを登録する場合のみ変更。

---

## 107. 必要なら

```text
japanese_house_modeler/junctions.py
```

にread-only helperを小さく追加してよい。

classification semanticsは変更しない。

---

## 108. 原則変更不要

```text
japanese_house_modeler/properties.py
japanese_house_modeler/connections.py
```

新しい永続Propertyは追加しない。

Topology semanticsを変更しない。

---

# Part Z — 完了条件

## 109. Build 04-C完了条件

Blender 5.2 LTS実機で：

- 90° 2-wall corner miter
- 45° corner miter
- 15° corner miter
- unequal thickness miter
- continuation square butt
- unsafe acute corner safe fallback
- START / END双方対応
- both-end miter Wall対応
- third Wall追加で旧miter解除
- third Wall detachで2-wall miter復活
- endpoint moveでall affected Wall更新
- dimension editでpartner joint更新
- Material保持
- Undoがgeometry/topology/canonical dataすべて復元
- manual rebuild/repair
- standard Delete後repair可能
- Build 04-B classification回帰なし
- Build 04-A topology回帰なし
- Build 03-B以前の回帰なし

を満たす。

---

# Part AA — 次Build

## 110. Build 04-D候補

Build 04-Cで2-wall jointが安定した後、

```text
T_JUNCTION
```

のMesh処理へ進む。

---

## 111. T junction

Build 04-Dでは、

- straight pair 2本
- branch Wall 1本
- thickness差
- branchが90°以外
- branch endpoint termination
- main Wall boundaryへのtrim

を設計する。

---

## 112. Crossはその後

T junctionを安定させてからCROSSへ進む。

一度にT/Cross/irregular multiを実装しない。
