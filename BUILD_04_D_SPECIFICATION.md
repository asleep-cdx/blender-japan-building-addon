# 日本住宅モデラー — Build 04-D Specification

## 1. 目的

Build 04-Dでは、Build 04-Cで実装した2-wall joint geometryを維持したまま、
**3-member `T_JUNCTION` の実Mesh接合**を実装する。

Build 04-DのT字接合では：

- straight pair 2本を「主壁（main walls）」とする
- 残り1本を「枝壁（branch wall）」とする
- 主壁2本はjunction中心線位置でsquare buttのまま連続させる
- 枝壁だけを、主壁の枝側外面までtrimする
- 90°だけでなく斜めbranchにも対応する
- branch thicknessは主壁と異なってよい
- 極端に浅い角度では安全fallbackする

Build 04-DではCross / generic 3-way / generic 4-way / MULTIのMesh処理はまだ実装しない。

---

## 2. 基準状態

Build 04-DはGitHub `main` の以下を基準とする。

- `6bdc9d6 Implement Build 04-C wall joints`

Build 04-CまでBlender 5.2 LTS実機テスト済み。

Build 04-Cで実機確認済み：

- 90° / 45° / 15° 2-wall miter
- extreme acute corner safe fallback
- unequal thickness 2-wall miter
- 180° straight continuation
- same-direction overlap safe square endpoint
- one Wall both endpoints miter
- third Wall add -> old miter squareへ復帰
- third Wall detach -> 2-wall miter復活
- wall thickness edit + Undo / Redo
- new Wall create + Undo / Redo
- Material保持
- standard Delete後 manual rebuild
- Solid / Material Previewで面・シェーディング正常
- atomic affected-Wall regeneration

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
- `BUILD_04_C_SPECIFICATION.md`

Build 04-DはBuild 04-Cまでの実機テスト済み挙動を壊してはならない。

---

# Part A — Build 04-Dの範囲

## 4. 実装する機能

Build 04-Dでは以下を実装する。

- `T_JUNCTION` のmain pair / branch member判定
- 90° T-junction branch trim
- angled T-junction branch trim
- 15°程度の浅いbranchへの対応
- branch thickness差への対応
- START / END全endpoint組み合わせへの対応
- main Wall Objectがどちら向きでも同じ結果
- T-junction joint status UI
- main pair / branch role表示
- unsafe T trimのsquare fallback
- endpoint移動時のT geometry再生成
- 3本目追加でTになった場合の自動trim
- Tから1本detachした場合のBuild 04-C geometry復帰
- 4本目追加でCROSS / FOUR_WAYになった場合のsquare復帰
- 4本目detachでTになった場合のtrim復活
- dimension editでT geometry更新
- Material保持
- Undo / Redo
- manual rebuild / repair
- standard Delete後のmanual repair
- save / reopen
- Build 04-C regression

---

## 5. Build 04-Dで実装しない機能

以下は実装しない。

- CROSS Mesh
- FOUR_WAY Mesh
- generic THREE_WAY Mesh
- MULTI Mesh
- 2本のmain Wall厚が異なるT字の完全trim
- stepped host boundaryへのbranch clipping
- interior / exterior side
- room side
- wall priority
- user-selectable T-joint style
- branch notch
- main wall opening / boolean
- Wall途中へのsegment T接続
- segment intersection
- standard Deleteの自動depsgraph handler
- opening / door / window
- floor / ceiling
- AI間取り図解析

---

# Part B — source of truth

## 6. canonical data

引き続きsource of truth：

```text
jhm_wall.start
jhm_wall.end
jhm_wall.wall_thickness
jhm_wall.wall_height
Connection topology
```

T trim Meshは派生データ。

---

## 7. canonical endpointはjunction中心

枝壁Mesh endpointを主壁外面まで後退/trimしても、
枝壁のcanonical START / ENDはjunction centerline位置のままとする。

例：

```text
canonical branch endpoint = J
visual branch end face = main wall outer face
```

`wall.start` / `wall.end` をtrim点へ変更してはならない。

---

# Part C — T_JUNCTION role判定

## 8. Build 04-B classificationを使用

対象endpoint：

```text
classification.key == T_JUNCTION
classification.member_count == 3
```

のみ。

---

## 9. main pair

3 membersのうち、
Build 04-Bの1° toleranceで唯一のopposite pairを：

```text
main pair
```

とする。

---

## 10. branch

main pairに含まれない残り1 memberを：

```text
branch
```

とする。

---

## 11. roleは派生データ

以下をPropertyへ保存しない。

```text
is_t_main
is_t_branch
t_role
```

毎回Topology + saved start/endから導出する。

---

## 12. junctions.py helper

Build 04-B classification semanticsを変更せず、
必要なら `junctions.py` にread-only helperを追加してよい。

推奨concept：

```python
t_junction_roles(wall_object, endpoint)
```

返り値概念：

```text
main_members = ((wall_a, endpoint_a), (wall_b, endpoint_b))
branch_member = (wall_c, endpoint_c)
```

Tでない / unsafeなら `None`。

---

## 13. role判定の一貫性

3つのmemberのどれから `t_junction_roles()` を呼んでも、
同じmain pairとbranchを返すこと。

memberの探索順に依存してroleが変わってはいけない。

---

# Part D — endpoint local geometry

## 14. endpoint inward direction

Build 04-B / 04-Cと同じ。

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

## 15. normal

```text
n = (-u.y, u.x)
```

---

## 16. half thickness

```text
h = wall_thickness_mm / 2000.0
```

meters。

---

# Part E — T-junctionの幾何方針

## 17. 主壁

main pair 2本はopposite direction。

Build 04-Dでは主壁2本を：

```text
canonical junction Jでsquare butt
```

のままとする。

つまりBuild 04-CのCONTINUATIONと同じ端部形状。

---

## 18. 主壁は削らない

Build 04-Dではbranchを受けるためにmain Wallをnotch / cut / booleanしない。

main pairの2本を合わせると連続した矩形壁になる。

---

## 19. 枝壁

branch Wallだけを、
主壁のbranch側outer boundaryまでtrimする。

枝壁がjunction centerまで食い込んだsquare endpointのままでは、
main wall内部へ重複するため、それを解消する。

---

# Part F — main pair thickness制限

## 20. Build 04-Dの安全な対応範囲

Build 04-DでT trimを有効にする条件：

```text
main wall A thickness == main wall B thickness
```

一定の小さな数値tolerance内で一致していること。

---

## 21. 理由

main pair厚が異なる場合、
junctionのhost boundaryは単一の直線ではなくstep形状になる。

完全対応には：

- main A側ray
- main B側ray
- junction step face
- branch side edgeとのpiecewise clipping

が必要になる。

これはBuild 04-Dの範囲外。

---

## 22. unequal main thickness

main pair thicknessが異なるT：

- crashしない
- canonical / topology変更なし
- 3本ともsquare endpoint
- joint status `安全フォールバック`
- manual rebuildでも同じ

とする。

---

## 23. branch thickness

branch thicknessはmain thicknessと異なってよい。

例：

```text
main A = 130 mm
main B = 130 mm
branch = 200 mm
```

は対応対象。

---

# Part G — host boundary line選択

## 24. shared junction

3 endpoint canonical位置が一致していることを確認。

推奨：

```text
_JOINT_POSITION_TOLERANCE_M = 1e-6
```

Build 04-Cと同じ。

---

## 25. main direction

main memberの片方をAとし：

```text
u_main
n_main = (-u_main.y, u_main.x)
h_main
```

を得る。

---

## 26. branch direction

```text
u_branch
```

を得る。

---

## 27. branch側判定

```text
side_dot = dot(u_branch, n_main)
```

を計算。

branchが `+n_main` 側へ伸びるなら：

```text
side_sign = +1
```

`-n_main` 側なら：

```text
side_sign = -1
```

---

## 28. host outer boundary

```text
host_offset = J + n_main * h_main * side_sign
```

host boundary line：

```text
L_host(s) = host_offset + s * u_main
```

---

## 29. main member選択に依存しない

もう一方のmain memberを基準にすると：

```text
u_main -> -u_main
n_main -> -n_main
side_sign -> -side_sign
```

となるため、
最終的なhost boundary lineは同一になること。

unit testする。

---

# Part H — branch trim

## 30. branch square side points

branch：

```text
J
u_branch
n_branch
h_branch
```

square endpoint：

```text
B_plus  = J + n_branch*h_branch
B_minus = J - n_branch*h_branch
```

---

## 31. branch side lines

```text
L_branch_plus(t)  = B_plus  + t*u_branch
L_branch_minus(t) = B_minus + t*u_branch
```

---

## 32. trim pair

branch trim endpoint pair：

```text
trim_plus  = intersection(L_branch_plus,  L_host)
trim_minus = intersection(L_branch_minus, L_host)
```

無限直線intersectionを使用。

---

## 33. trim面

```text
trim_plus
trim_minus
```

はhost boundary line上にある。

したがってbranch end faceはmain wall outer faceと同一平面になる。

---

## 34. overlapなし

正常Tではbranchのvisual Meshがjunction center Jまで入らず、
main wall外面で停止する。

---

# Part I — branch angle

## 35. 90°

標準T：

```text
        branch
          |
----------+----------
        main
```

branch end faceはmain outer faceで直線trim。

---

## 36. angled branch

例45°：

```text
       /
      /
-----+---------
```

branchの2 side edgesとhost boundary lineの交点を使うため、
branch end faceは斜めcutとなる。

---

## 37. 15°

15°程度の浅いbranchも、
安全limit内ならtrimする。

---

# Part J — T trim safety

## 38. near-parallel

branchがmainとほぼ平行の場合、
intersectionが遠方へ飛ぶ。

safe fallbackする。

---

## 39. trim factor

Build 04-Cと同じ思想。

推奨：

```text
_MAX_T_TRIM_FACTOR = 10.0
```

reference：

```text
max(h_main, h_branch)
```

---

## 40. distance check

各trim point：

```text
distance(trim_point, J)
<= max(h_main, h_branch) * _MAX_T_TRIM_FACTOR
```

を要求。

---

## 41. branch direction parameter

host boundaryはbranch側にあるため、
branch side lineのintersectionは基本的に：

```text
t >= 0
```

となる。

数値誤差toleranceを除き、
大きく負のtになる場合はunsafeとしてfallbackしてよい。

---

## 42. fallback

unsafe T：

- 3本ともsquare
- status `安全フォールバック`
- topology維持
- Python errorなし
- 巨大spikeなし

---

# Part K — transform safety

## 43. identity transform

T junction member 3本すべてidentity transformの場合のみT trimを許可。

---

## 44. non-identity

1本でもObject Transformがある場合：

- T trimしない
- operationによる危険なcanonical world-space Mesh上書きを避ける
- managed regen operationは必要に応じて安全に拒否
- transformをapply / bakeしない

Build 04-Cの方針を維持。

---

# Part L — joint status

## 45. 新status

Tが正常に解決できる場合：

main endpoint：

```text
T字主壁
```

branch endpoint：

```text
T字枝壁
```

---

## 46. fallback

T classificationだがT solver unsafe：

```text
安全フォールバック
```

3 membersすべて同じfallback状態としてよい。

---

## 47. status保存禁止

joint statusはPropertyへ保存しない。

---

# Part M — joints.py integration

## 48. endpoint_joint_pair

現在のBuild 04-C：

- ISOLATED
- CONTINUATION
- CORNER
- unsupported

に加え、

```text
T_JUNCTION
```

処理を追加する。

---

## 49. main endpoint pair

valid Tのmain member：

```text
square endpoint pair
status = T_MAIN
```

---

## 50. branch endpoint pair

valid Tのbranch member：

```text
trim pair
status = T_BRANCH
```

---

## 51. invalid T

```text
square pair
status = FALLBACK
```

---

# Part N — polygon validation

## 52. branch Wall polygon

branch trim pairを適用後、
Build 04-Cの `validate_lower_polygon()` を使用。

---

## 53. invalid polygon

trimでbranch polygonがinvalidになる場合：

- branch endpoint squareへfallback
- T junction全体をfallback扱いとしてよい
- crashしない

---

## 54. both endpoints

1本のbranch Wallが、
反対側endpointで別jointを持つ可能性がある。

例：

```text
START = T_BRANCH
END = CORNER miter
```

でもlower polygonが正常なら両方適用。

---

# Part O — affected Wall regeneration

## 55. 既存Build 04-C affected setを維持

新規Wall、endpoint移動、dimension edit、manual rebuildで
affected junction members全体をregenする。

---

## 56. 3本目追加

straight continuation A-BへCをdirect snapしT化。

affected：

```text
A
B
C
```

全てregen。

期待：

- A/B square main
- C branch trim

---

## 57. branch detach

Tからbranch Cをfreeへ移動。

affected old junction：

```text
A
B
C
```

期待：

- A/B -> CONTINUATION square
- C -> ISOLATED square

---

## 58. main detach

Tからmain Aをfreeへ移動。

残りB-CがCORNERなら：

- Build 04-C miterへ自動移行

old/new member regenを利用。

---

## 59. 4本目追加

T junctionへDを追加しCROSSまたはFOUR_WAYになる。

Build 04-Dではunsupported。

期待：

- 旧branch trim解除
- 4本ともsquare
- joint status `未対応`

---

## 60. 4本目detach

4-memberからDをfreeへ移動しTへ戻る。

期待：

- T main / branch role再計算
- branch trim自動復活

---

# Part P — dimension edit

## 61. branch thickness

branch thickness変更：

```text
130 -> 200 mm
```

branch trim pairを再計算。

main Meshはsquareのまま。

Material保持。

---

## 62. main thickness

main A/Bが両方同じ値ならT trim可能。

ただし1本だけ変更して：

```text
A=200
B=130
```

になった瞬間はBuild 04-D未対応。

期待：

- 3本square
- 安全フォールバック

---

## 63. main thickness equalへ戻す

例：

```text
A=200
B=200
```

になればmanual/managed regen後にT trim復活。

ただし各dimension editはselected Wall + junction membersをregenするため、
2本目を200へ変更した時点で自動復活してよい。

---

## 64. height

高さ変更ではXY trim位置は変わらない。

各Wallは自身のheightを維持。

---

# Part Q — Undo / Redo

## 65. T creation Undo

A-B continuationへCを追加してTを作る。

Ctrl+Z：

- C削除
- A/B continuationへ戻る
- topology復元
- Mesh復元

Ctrl+Shift+Z：

- C復活
- T trim復活

---

## 66. branch move Undo

T branch endpointをfreeへ移動。

Ctrl+Z：

- topology Tへ復元
- branch canonical endpoint復元
- T trim復元

---

## 67. thickness Undo

branch thickness変更後Ctrl+Z：

- thickness復元
- trim geometry復元

---

## 68. main unequal fallback Undo

main A thicknessを変えてfallback化。

Ctrl+Z：

- equal thickness復元
- T trim復元

---

# Part R — standard Delete / manual repair

## 69. branch Delete

Tのbranchを標準Delete。

残るmain pair：

- classification CONTINUATION
- Connection countはvalid 1
- Mesh mainは元々squareなので大きなvisual変更なし

manual rebuildで正常維持。

---

## 70. main Delete

Tのmain Wallを1本標準Delete。

残るmain+branchは2-member CORNERになる場合がある。

削除直後は旧T branch trimが残る可能性あり。

「接合を再生成」で：

- Build 04-C 2-wall miterへrepair

されること。

---

# Part S — save / reopen

## 71. persistent data

T role / trim pointは保存しない。

save/reopen後：

- Connection topology
- canonical start/end
- thickness
- Mesh

から同じT geometryが維持される。

---

## 72. manual rebuild after reopen

「接合を再生成」で同じT geometryを再構築できる。

---

# Part T — UI

## 73. valid T main

例：

```text
始点接続: 2
始点形状: T字候補
始点接合: T字主壁
```

---

## 74. valid T branch

```text
始点接続: 2
始点形状: T字候補
始点接合: T字枝壁
```

---

## 75. unsafe T

```text
始点形状: T字候補
始点接合: 安全フォールバック
```

---

# Part U — unit / mock tests

## 76. role tests

最低限：

- 0° / 180° / 90°
  - 0/180 = main pair
  - 90 = branch
- member探索順を入れ替えてもrole同じ
- START/END組み合わせでrole同じ

---

## 77. host boundary invariance

main Aを基準に計算しても、
main Bを基準に計算しても、
同じhost boundary lineになること。

---

## 78. 90° trim

main 130/130、branch 130。

期待：

- branch trim faceがmain outer boundary上
- main square
- no overlap into main center

---

## 79. 45° trim

branch side edge intersectionがhost boundary上。

---

## 80. 15° trim

limit内でvalid。

---

## 81. acute fallback

2〜3°等。

巨大trimにならずfallback。

---

## 82. branch thickness差

main 130/130、branch 200。

valid T trim。

---

## 83. main thickness差

main 130/200。

fallback。

---

## 84. position mismatch

3 endpointsの1つが1e-6超ずれている。

fallback。

---

## 85. transform

1 member non-identity。

fallback / safe operation rejection。

---

## 86. polygon

T_BRANCH + opposite endpoint CORNER等でも
valid lower polygon。

---

# Part V — Blender実機テスト

## 87. Test A — 90° standard T

main A/B：

```text
130 / 130
```

branch：

```text
130
```

期待：

- 3 endpoints `T字候補`
- A/B `T字主壁`
- branch `T字枝壁`
- branch端面がmain外面で停止
- gapなし
- main内部へのbranch overlapなし

---

## 88. Test B — wireframe close-up

Test AをTop + Wireframeで拡大。

期待：

- main A/B square butt
- branch endpoint line = main outer boundary
- junction centerまでbranch Meshが入っていない

---

## 89. Test C — 45° branch

期待：

- T字枝壁
- oblique trim
- gapなし
- spikeなし

---

## 90. Test D — 15° branch

期待：

- valid trim
- extreme spikeなし

---

## 91. Test E — acute branch

2〜3°。

期待：

- 安全フォールバック
- 3本square
- crashなし

---

## 92. Test F — thick branch

main 130/130、
branch 200。

期待：

- T trim
- branch thickness維持
- host boundary一致

---

## 93. Test G — unequal main

main 130/200。

期待：

- T字候補
- 接合 安全フォールバック
- 3本square
- crashなし

---

## 94. Test H — START/END combinations

最低でも：

- main START + main START + branch START
- main END + main START + branch END

等を確認。

role / trimがendpoint名に依存しない。

---

## 95. Test I — branch detach

T branchをfreeへ。

期待：

- main -> 直線
- branch -> 未接続
- branch square

---

## 96. Test J — main detach

main 1本をfreeへ。

残る2本がCORNERなら：

- Build 04-C miter

---

## 97. Test K — fourth Wall add

Tへ4本目を追加。

期待：

- CROSS / 4方向 classification
- 4本 joint未対応
- old T branch trim消失
- squareへ戻る

---

## 98. Test L — fourth Wall detach

Test Kから4本目をfreeへ。

期待：

- T復活
- branch trim復活

---

## 99. Test M — branch thickness edit

130 -> 200。

期待：

- trim更新
- Material保持

---

## 100. Test N — main unequal -> equal

main A 130 / main B 130でT。

Aだけ200：

- fallback

Bも200：

- T trim復活

---

## 101. Test O — Undo / Redo T creation

3本目作成直後Ctrl+Z / Ctrl+Shift+Z。

期待：

- T geometry / topology / branch Wallが正しく戻る・復活

---

## 102. Test P — Undo branch move

branch free移動後Ctrl+Z。

T trim復元。

---

## 103. Test Q — Delete main + repair

main 1本をstandard Delete。

残る2本を選択して「接合を再生成」。

期待：

- stale T trim消失
- 2-wall miterへrepair

---

## 104. Test R — Material

main / branchにMaterialを付け、
dimension edit / endpoint move。

Material維持。

---

## 105. Test S — save/reopen

Tを保存・再起動。

Mesh / topology / classification / status維持。

---

## 106. Test T — shading

Solid / Material Previewで
branch trim face、main faceのshade異常なし。

---

# Part W — regression

## 107. Build 04-C regression

以下を再確認：

- 90° 2-wall miter
- 45° miter
- 15° miter
- continuation
- overlap
- acute fallback
- unequal thickness 2-wall miter

---

## 108. Build 04-B regression

classification semanticsは変更しない。

---

## 109. Build 04-A regression

Connection clique / detach / stale targetを壊さない。

---

# Part X — 変更ファイル候補

## 110. 推奨

```text
japanese_house_modeler/joints.py
japanese_house_modeler/junctions.py
japanese_house_modeler/ui.py
tests/test_joints.py
```

---

## 111. operators.py

既存affected regenerationで十分なら変更不要。

T対応のために必要な場合のみ最小変更。

---

## 112. 原則変更不要

```text
japanese_house_modeler/connections.py
japanese_house_modeler/properties.py
japanese_house_modeler/__init__.py
```

新Operator追加は不要。

---

# Part Y — 完了条件

## 113. Build 04-D完了条件

Blender 5.2 LTS実機で：

- 90° T branch trim
- 45° branch trim
- 15° branch trim
- acute safe fallback
- branch thickness差
- unequal main thickness safe fallback
- START/END invariant
- branch detach
- main detach -> 2-wall miter
- fourth Wall add -> square unsupported
- fourth Wall detach -> T復活
- dimension edit
- Undo / Redo
- Material保持
- Delete + manual repair
- save/reopen
- shading正常
- Build 04-C regression

を満たす。

---

# Part Z — 次段階

## 114. Build 04-E候補

Build 04-Dが安定した後、
次候補は：

```text
CROSS
```

のMesh処理。

---

## 115. その前のoptional extension

必要ならCrossの前に：

```text
unequal main thickness T
```

のstep host boundary clippingを独立Buildとして実装してもよい。

Build 04-Dでは安全fallbackを優先する。
