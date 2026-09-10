# 日本住宅モデラー — Build 04-E Specification

## 1. 目的

Build 04-Eでは、Build 04-Dまでの2-wall / T-junction geometryを維持したまま、
**4-member `CROSS`（十字接合）の実Mesh処理**を追加する。

Build 04-EのCROSSでは、4本のWallを2組のopposite pairへ分け、

- 1組を **through pair（通し壁）**
- もう1組を **butt pair（突合せ壁）**

として扱う。

through pairはcanonical junction中心までsquare buttのまま通し、
butt pairの各Wallだけをthrough pairの両側外面までtrimする。

これにより、4本の独立Wall Objectを維持したまま、
中心部で不要なMesh overlapを起こさない十字接合を生成する。

Build 04-Eでは `FOUR_WAY` / `THREE_WAY` / `MULTI` の実Mesh処理は実装しない。

---

## 2. 基準状態

Build 04-EはGitHub `main` の以下を基準とする。

```text
c941aaa Implement Build 04-D T-junction trimming
```

Build 04-DまでBlender 5.2 LTS実機テスト済み。

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
- `BUILD_04_D_SPECIFICATION.md`

Build 04-EはBuild 04-Dまでの実機テスト済み挙動を壊してはならない。

---

# Part A — Build 04-Eの範囲

## 4. 実装する機能

Build 04-Eでは以下を実装する。

- 4-member `CROSS` の2組opposite pair導出
- deterministicなthrough pair / butt pair選択
- 90° Cross Mesh
- angled Cross Mesh
- 15°程度の浅い交差への対応
- 極端に浅いCrossのsafe fallback
- butt pair各Wallのthrough外面へのtrim
- butt pair thickness差への対応
- through pair thickness一致時の処理
- through pair thickness不一致時のsafe fallback
- START / END全組み合わせへの対応
- member列挙順から独立したrole判定
- save/reopenでroleが変化しない決定規則
- CROSS joint status UI
- Tへ4本目追加した場合のCross自動生成
- Crossから1本detachした場合のT自動復帰
- dimension edit
- Undo / Redo
- Material保持
- manual rebuild / repair
- standard Delete後repair
- Build 04-D / 04-C regression

---

## 5. Build 04-Eで実装しない機能

以下は実装しない。

- `FOUR_WAY` Mesh
- generic `THREE_WAY` Mesh
- `MULTI` Mesh
- through pair 2本の異厚step boundary完全対応
- user-selectable wall priority
- interior / exterior side
- room semantic
- structural wall priority
- main wall / bearing wall semantic
- opening / boolean
- door / window
- wall途中segment intersection
- automatic intersection detection
- standard Delete depsgraph handler
- floor / ceiling
- AI間取り解析

---

# Part B — source of truth

## 6. canonical data

引き続きsource of truthは：

```text
jhm_wall.start
jhm_wall.end
jhm_wall.wall_thickness
jhm_wall.wall_height
Connection topology
```

Cross role / trim pointは派生データ。

---

## 7. canonical endpoint

butt pair Wallのvisual endpointがthrough外面までtrimされても、
canonical START / ENDはjunction中心Jに残す。

Meshのtrim点をcanonical endpointとして保存してはならない。

---

# Part C — CROSS classification

## 8. 対象

対象endpoint：

```text
classification.key == CROSS
classification.member_count == 4
```

のみ。

---

## 9. classification semantics

Build 04-Bの `classify_junction()` semanticsは変更しない。

Build 04-Bのopposite tolerance：

```text
_ANGLE_TOLERANCE_DEG = 1.0
```

も変更しない。

分類上CROSSでも、
Build 04-E Mesh solverがunsafeと判断した場合は：

```text
classification = CROSS
joint geometry = 安全フォールバック
```

とする。

---

# Part D — opposite pair partition

## 10. 4 members

4つのmember：

```text
M0
M1
M2
M3
```

について3通りのdisjoint pairingを検査する。

```text
(M0,M1) + (M2,M3)
(M0,M2) + (M1,M3)
(M0,M3) + (M1,M2)
```

---

## 11. valid partition

各pairがBuild 04-Bの `_is_opposite()` を満たすpairingを候補とする。

---

## 12. unique partition

Build 04-E Mesh solverでは、
**有効なdisjoint opposite-pair partitionが1つだけ**の場合に処理する。

0個：

```text
fallback
```

2個以上：

```text
ambiguous
fallback
```

とする。

---

## 13. ambiguous CROSS

例：

```text
0°
180°
0°
180°
```

のように分類上CROSSになり得ても、
2本の異なる交差軸を一意に決められない場合は
Mesh solverでは安全フォールバックする。

classification自体は書き換えない。

---

## 14. helper

必要なら `junctions.py` にread-only helper：

```python
cross_junction_pairs(wall_object, endpoint)
```

または同等を追加する。

概念的返り値：

```text
pair_a = ((wall, endpoint), (wall, endpoint))
pair_b = ((wall, endpoint), (wall, endpoint))
```

CROSSでない / ambiguous / invalidなら `None`。

---

# Part E — exact geometry safety

## 15. classification toleranceとMesh toleranceの分離

Build 04-Dと同じ原則。

各opposite pairはclassification上1° tolerance内でもよいが、
Mesh geometryでは十分collinearでなければならない。

---

## 16. exact-collinear requirement

pair direction：

```text
u1
u2
```

について：

```text
cross = u1.x*u2.y - u1.y*u2.x
dot   = u1.x*u2.x + u1.y*u2.y
```

を計算。

推奨：

```text
_CROSS_PAIR_COLLINEAR_TOLERANCE = 1.0e-6
```

条件：

```text
abs(cross) <= tolerance
dot < 0
```

---

## 17. 179.5°等

pairが179.5°でBuild 04-B上oppositeと判定されても、
Cross Mesh solverはfallbackする。

---

## 18. 2 axes distinct

pair A axisとpair B axisが同一直線 / near-parallelならCross Mesh不可。

交差角が極端に浅い場合はtrim safetyでfallbackしてよい。

---

# Part F — shared junction位置

## 19. canonical XY

4 member endpointのcanonical XY位置が一致していること。

既存：

```text
_JOINT_POSITION_TOLERANCE_M = 1.0e-6
```

を使用。

---

## 20. mismatch

いずれかがtolerance超過：

- topology変更なし
- endpoint補正なし
- 4本ともsquare
- `安全フォールバック`

---

# Part G — identity transform

## 21. transform条件

4 memberすべてidentity transformの場合のみCross solverを許可。

---

## 22. non-identity

1本でもObject Transformあり：

- Cross solver fallback
- managed batch regeneration自体はBuild 04-Cの安全方針に従い必要なら拒否
- transform auto apply禁止
- canonicalへbake禁止

---

# Part H — through pairのdeterministic選択

## 23. なぜ必要か

Crossでは2組のopposite pairのうち、
どちらを「通し壁」とするかを決める必要がある。

Wall priority Propertyはまだ存在しないため、
Build 04-Eでは**世界座標に基づく一時的なdeterministic rule**を使用する。

---

## 24. 禁止

through pair選択に以下を使用してはならない。

- `as_pointer()`
- Object生成順
- junction_members()列挙順
- Object name
- Collection order
- transient runtime ID

save/reopenやUndoでroleが変わり得るため。

---

## 25. axis canonicalization

各opposite pairからundirected axisを導出する。

代表unit direction `u=(x,y)` を、
符号反転しても同じaxis keyになるようcanonicalizeする。

推奨例：

```text
x < 0 の場合は -u
x ≈ 0 かつ y < 0 の場合も -u
```

結果としてcanonical axis directionを一意にする。

---

## 26. world-X priority

Build 04-Eでは、
**global X axisにより近いpairをthrough pair**とする。

例：

```text
horizontal X pair
vertical Y pair
```

ならhorizontal pairがthrough。

---

## 27. closeness

推奨：

```text
abs(dot(axis, world_X)) = abs(axis.x)
```

が大きいpairをthroughとする。

---

## 28. tie

±45°のようにXへの近さが等しい場合は、
canonicalized axis angle / Y component等による
**deterministic geometric tie-break**を使用する。

Object identityに依存してはならない。

---

## 29. role stability

同一canonical geometry / topologyなら、

- save/reopen
- member列挙順変更
- START/END組み合わせ
- どのmemberからsolverを呼ぶか

によってthrough / butt pairが変化してはならない。

---

## 30. 将来

user-selectable wall priorityは将来Buildで追加可能。

Build 04-Eのworld-X ruleはその時置換可能なderived policyとして実装する。

---

# Part I — through pair thickness

## 31. requirement

selected through pair 2本のwall thicknessが一致する場合のみ
Cross trimを有効にする。

---

## 32. tolerance

推奨：

```text
_CROSS_THROUGH_THICKNESS_TOLERANCE_MM = 1.0e-6
```

---

## 33. unequal through thickness

through A=130mm
through B=200mm

なら：

- 4本square
- 4本 `安全フォールバック`
- canonical / topology維持

---

## 34. other pair equalでもrole switchしない

重要：

selected through pairが異厚だからといって、
butt pairが等厚ならそちらを自動的にthroughへ切り替える、
という挙動は行わない。

through pair選択はgeometry policyだけで決定し、
thicknessによってroleをflipさせない。

---

## 35. butt thickness

butt pair 2本は互いに異なるthicknessでもよい。

例：

```text
through = 130 / 130
butt +side = 130
butt -side = 200
```

は対応対象。

---

# Part J — through pair geometry

## 36. through members

through pair 2本はcanonical junction Jでsquare endpoint。

Build 04-C CONTINUATIONと同じ。

---

## 37. no notch

through pairへ：

- notch
- boolean
- cut
- center opening

を追加しない。

---

## 38. central volume

through pair 2本を合わせることで、
junction中央のhost rectangular volumeを占める。

butt pairはその外面までtrimする。

---

# Part K — host boundaries

## 39. through axis

through pairのrepresentative memberから：

```text
J
u_host
n_host
h_host
```

を取得。

---

## 40. two outer faces

host outer boundaryは2本：

```text
L_plus(s)  = J + n_host*h_host + s*u_host
L_minus(s) = J - n_host*h_host + s*u_host
```

---

## 41. reference invariance

through pairのもう一方を基準にすると：

```text
u_host -> -u_host
n_host -> -n_host
```

となる。

`L_plus` / `L_minus` の名称は入れ替わってもよいが、
**2本の幾何学的boundary line集合は同じ**であること。

---

# Part L — butt member trim

## 42. butt member local data

各butt Wall：

```text
J
u_butt
n_butt
h_butt
```

---

## 43. target host side

```text
side_dot = dot(u_butt, n_host)
```

により、
そのbutt Wallがjunctionからどちら側へ伸びるか決定する。

---

## 44. target boundary

`side_dot > 0`：

```text
target = + host boundary
```

`side_dot < 0`：

```text
target = - host boundary
```

---

## 45. square side origins

```text
B_plus  = J + n_butt*h_butt
B_minus = J - n_butt*h_butt
```

---

## 46. side lines

```text
B_plus  + t*u_butt
B_minus + t*u_butt
```

---

## 47. trim pair

各side lineとtarget host boundaryをinfinite 2D line intersection。

```text
trim_plus
trim_minus
```

を取得。

butt endpoint pair：

```text
(trim_plus, trim_minus)
```

---

## 48. visual result

butt Wall end faceはthrough Wall outer face上で停止。

junction center Jまでbutt Meshが侵入しない。

---

# Part M — shared Cross solution

## 49. solver単位

endpointごとに独立してCross geometryを決めず、
**1 junction全体のshared solution**を計算する。

推奨：

```python
calculate_cross_solution(wall_object, endpoint)
```

または同等。

---

## 50. result concept

safe solution概念：

```text
through_members
butt_members
butt_trim_pair_for_member_1
butt_trim_pair_for_member_2
host_axis
host_boundaries
```

---

## 51. all-or-nothing solver

solver-level safety conditionのどれか1つでも失敗したら：

```text
solution = None
```

4 membersすべて：

```text
square endpoint
status FALLBACK
```

---

## 52. inconsistent state禁止

同じCross junctionで：

```text
through member = CROSS_THROUGH
butt member 1 = CROSS_BUTT
butt member 2 = FALLBACK
```

のようなsolver-level不一致を作らない。

ただし後述のWall-local opposite-end polygon conflictは別。

---

# Part N — Cross trim safety

## 53. line parallel

butt axisがhost axisにnear-parallelならintersectionが遠方へ飛ぶ。

safe fallback。

---

## 54. trim limit

Build 04-C / 04-Dと同じ思想。

推奨：

```text
_MAX_CROSS_TRIM_FACTOR = 10.0
```

reference：

```text
max(h_host, h_butt)
```

---

## 55. distance

各trim point：

```text
distance(trim, J)
<= max(h_host, h_butt) * _MAX_CROSS_TRIM_FACTOR
```

---

## 56. parameter

butt side line parameter：

```text
t >= 0
```

が基本。

小さなfloating error negativeは許容してよい。

明確なnegativeはfallback。

---

## 57. short wall

各butt Wallについて：

```text
trim parameter < canonical wall length - _MIN_WALL_LENGTH_M
```

を要求。

trimが反対側endpointを越えてはいけない。

---

## 58. both butt members

2本のbutt memberのうち片方でもunsafeなら、
Cross solution全体fallback。

---

# Part O — crossing angle

## 59. 90°

標準Cross：

```text
        |
        |
--------+--------
        |
        |
```

valid。

---

## 60. 45°

2 axesの交差角45°。

valid trim。

---

## 61. 15°

安全limit内ならvalid。

---

## 62. 2〜3°

extreme shallow cross。

trim pointがlimitを超えるなら：

```text
安全フォールバック
```

巨大spike禁止。

---

# Part P — statuses

## 63. status keys

valid Cross through member：

```text
CROSS_THROUGH
```

valid Cross butt member：

```text
CROSS_BUTT
```

---

## 64. UI labels

```text
CROSS_THROUGH -> 十字通し壁
CROSS_BUTT    -> 十字突合せ壁
```

---

## 65. fallback

classification CROSSだがunsafe：

```text
安全フォールバック
```

---

## 66. unsupported

`FOUR_WAY` 等：

```text
未対応
```

のまま。

---

## 67. persistent禁止

Cross status / roleはPropertyへ保存しない。

---

# Part Q — endpoint_joint_pair integration

## 68. branch order

現在の：

- ISOLATED
- CONTINUATION
- T_JUNCTION
- CORNER
- unsupported

へCROSSを追加する。

---

## 69. valid through

```text
square pair
status CROSS_THROUGH
```

---

## 70. valid butt

```text
trim pair
status CROSS_BUTT
```

---

## 71. unsafe Cross

```text
square pair
status FALLBACK
```

---

# Part R — polygon-level fallback

## 72. existing behavior

Build 04-C/04-Dの `_resolved_endpoint_pairs()` は、
WallのSTART/END jointを組み合わせた最終lower polygonを検証する。

---

## 73. CROSS_BUTT

`CROSS_BUTT` はvisual endpoint位置を変更するため、
MITER / T_BRANCHと同様にWall-local fallback対象とする。

---

## 74. invalid opposite-end interaction

Cross shared solver自体がsafeでも、
同じWallの反対endpoint jointとの組み合わせでpolygon invalidになる場合：

- 該当 `CROSS_BUTT` endpointのみsquareへ戻してよい
- statusはFALLBACK
- crashしない

---

## 75. CROSS_THROUGH

through endpointはsquareなので通常polygon fallback対象追加不要。

---

# Part S — affected Wall regeneration

## 76. existing mechanism

Build 04-Cの：

```text
affected_walls()
merge_affected()
regenerate_wall_meshes()
```

およびoperatorsのold/new junction affected setを再利用する。

---

## 77. operators変更

既存実装で4-member junction全体がregenされるなら
`operators.py` は変更しない。

必要な場合のみ最小変更。

---

# Part T — TからCrossへ

## 78. fourth Wall add

Build 04-D T junctionへ4本目をdirect snapし、
classificationがCROSSになった場合：

4本全てregen。

---

## 79. expected

selected deterministic through pair：

```text
十字通し壁 x2
```

other pair：

```text
十字突合せ壁 x2
```

butt pairはhost外面までtrim。

---

## 80. old T trim

以前のT branch trimをそのまま残してはいけない。

Cross solutionから4本全て再構築する。

---

# Part U — CrossからTへ

## 81. one member detach

Crossの任意1本をfree位置へ移動。

残る3本がT_JUNCTIONなら：

- Build 04-D role再計算
- T_MAIN x2
- T_BRANCH x1
- T trim自動復活

---

## 82. detached Wall

detachされたWall：

```text
ISOLATED
square
```

または新junction classificationに従う。

---

# Part V — CrossからCORNER等へ

## 83. multiple detach

結果が2-member CORNERならBuild 04-C miter。

CONTINUATIONならsquare butt。

既存solverを再利用する。

---

# Part W — dimension edit

## 84. through thickness equal

through pair 130/130：

valid Cross。

---

## 85. through unequal

selected through pairの1本だけ：

```text
130 -> 200
```

期待：

- Cross classification維持
- 4本 `安全フォールバック`
- square

---

## 86. equal restore

もう1本も200へ変更：

```text
200 / 200
```

Cross trim自動復活。

---

## 87. role flip禁止

thickness差によってthrough/butt role自体は切り替えない。

---

## 88. butt thickness edit

butt member：

```text
130 -> 200
```

でもvalid Cross。

そのWallのtrim pairを再計算。

---

## 89. two butt unequal

butt A=130
butt B=200

でもvalid。

---

## 90. height

height変更ではXY trim policyは同じ。

各Wall自身のheightを維持。

---

# Part X — Undo / Redo

## 91. Cross creation Undo

Tへ4本目追加しCross生成。

Ctrl+Z：

- 4本目削除
- topology Tへ復元
- Build 04-D T Mesh復元

Ctrl+Shift+Z：

- 4本目復活
- Cross Mesh復活

---

## 92. detach Undo

Cross memberをfreeへ移動。

Ctrl+Z：

- Cross topology復元
- Cross Mesh復元

---

## 93. thickness Undo

through thickness変更でfallback化。

Ctrl+Z：

- thickness復元
- Cross trim復元

Redoも確認。

---

# Part Y — standard Delete / manual repair

## 94. butt member Delete

Crossのbutt memberを標準Delete。

残る3本がTの場合、
stale Meshが一時残ってもよい。

`接合を再生成`でBuild 04-D T geometryへrepair。

---

## 95. through member Delete

Crossのthrough memberを標準Delete。

残る3本がTになる場合、
旧Cross geometryと新T geometryは大きく異なる可能性がある。

自動depsgraph repairは行わない。

残存Wallを選択して：

```text
接合を再生成
```

でT geometryへrepair。

---

## 96. delete->2 members

さらにdeleteして2-member CORNER等になった場合も、
manual rebuildでBuild 04-C geometryへrepairできること。

---

# Part Z — save / reopen

## 97. persistent data

Cross role / trim pointは保存しない。

save/reopen後：

- topology
- canonical geometry
- thickness
- Mesh

から同じstatus / role / trimが導出される。

---

## 98. deterministic policy

through pairはworld-X geometric policyにより、
save/reopen後も同じpairになること。

---

## 99. manual rebuild after reopen

`接合を再生成`しても同じCross geometryになる。

---

# Part AA — Material / shading

## 100. Material

Cross regenerationでMaterial slotsを消失させない。

Build 04-C atomic regenerationのMaterial copyを維持。

---

## 101. shading

Top/Wireframeだけでなく：

- Solid
- Material Preview
- perspective view

で確認。

黒化・反転面・異常な法線表示・巨大spikeなし。

---

# Part AB — unit / mock tests

## 102. pair partition

最低限：

- standard 0/180 + 90/270 → unique two pairs
- member order permutation →同じaxis pair集合
- START/END混在 →同じ
- ambiguous 0/180/0/180 → solver fallback

---

## 103. deterministic through selection

90° X/Y Cross：

```text
X pair = through
Y pair = butt
```

member orderに依存しない。

---

## 104. tie case

±45°等global X closenessが同じ場合でも、
geometric tie-breakにより常に同じthrough pair。

save/reopen相当としてpointer / list orderに依存しない。

---

## 105. exact collinear

各opposite pair exact 180°：

valid。

---

## 106. 179.5°

classification CROSSのままでもsolver fallback。

---

## 107. shared positions

1 endpointのみ2e-6mずれ：

all Cross fallback。

---

## 108. transform

1 member nonidentity：

all fallback / managed regen rejection。

---

## 109. 90° trim

X pair through 130/130。

Y+ / Y- butt。

期待：

```text
Y+ endpoint face = y? ではなく host +normal boundary
Y- endpoint face = opposite host boundary
```

実際の座標で2本のhost outer line上にあることを検証。

---

## 110. 45° trim

valid。

---

## 111. 15° trim

limit内ならvalid。

---

## 112. shallow

2.5°等：

all fallback。

---

## 113. through unequal

X pair 130/200：

all fallback。

---

## 114. butt unequal

X through 130/130、
Y+ butt 130、
Y- butt 200：

valid。

---

## 115. short butt

片方butt lengthがtrim距離以下：

all fallback。

---

## 116. host reference reversal

through member A基準 / B基準で：

- host boundary line集合一致
- butt trim pair一致

---

## 117. CROSS_BUTT opposite-end joint

同じWallの反対側endpointに：

- CORNER
- T_BRANCH

等があってもpolygon validまたはsafe local fallback。

crashなし。

---

# Part AC — regression tests

## 118. Build 04-D T regression

最低限：

- 90° T
- 45° T
- 15° T
- 2.5° fallback
- branch 200
- main unequal fallback
- 179.5° main pair fallback

---

## 119. Build 04-C regression

最低限：

- 90° CORNER miter
- 45° miter
- 15° miter
- acute fallback
- unequal thickness miter
- CONTINUATION

---

## 120. Build 04-B regression

classification semantics変更なし。

---

## 121. Build 04-A regression

Connection clique / attach / detach / stale target処理変更なし。

---

# Part AD — Blender実機テスト

## 122. Test 1 — standard 90° Cross

作成：

```text
X pair 130/130
Y pair 130/130
```

期待：

- classification `十字候補`
- X pair `十字通し壁`
- Y pair `十字突合せ壁`
- 中央overlapなし
- gapなし

---

## 123. Test 2 — Wireframe close-up

Top + Wireframe。

期待：

- X pair endpointはJでsquare
- Y+ endpointはhost +外面
- Y- endpointはhost -外面
- Y pairが中央Jまで入っていない

---

## 124. Test 3 — 45° Cross

2 axes angle45°。

期待：

- valid Cross
- butt pair oblique trim
- spikeなし
- gapなし

---

## 125. Test 4 — 15° Cross

期待：

- valid Cross if safety limit内
- 巨大spikeなし

---

## 126. Test 5 — 2〜3° Cross

期待：

- `十字候補`
- 4本 `安全フォールバック`
- square
- crashなし

---

## 127. Test 6 — butt unequal thickness

through X：

```text
130 / 130
```

butt Y：

```text
130 / 200
```

期待：

- valid Cross
- 両butt個別trim

---

## 128. Test 7 — through unequal

through X：

```text
130 / 200
```

期待：

- 4本安全フォールバック
- role auto-switchなし
- square

---

## 129. Test 8 — through equal restore

Test 7で2本目も200：

```text
200 / 200
```

期待：

- Cross geometry復活
- X pairがthroughのまま

---

## 130. Test 9 — START/END mix

4 memberのjunction endpointを：

```text
START
END
START
END
```

等で混在。

期待：

role / trim正常。

---

## 131. Test 10 — member order robustness

Blender通常操作上、生成順を変えた複数Crossを作る。

同じ幾何ならthrough pairが同じworld-axis policyで選ばれること。

---

## 132. Test 11 — T -> Cross

正常Tへ4本目を追加。

期待：

- T status消失
- Cross statusへ移行
- Cross geometry生成

---

## 133. Test 12 — Cross -> T

Test 11の1本をdetach。

期待：

- Build 04-D Tへ自動復帰

---

## 134. Test 13 — Cross -> CORNER

さらにWallをdetachして2本CORNERにする。

期待：

- Build 04-C miterへ自動移行

---

## 135. Test 14 — Cross creation Undo/Redo

Tへ4本目追加直後：

Ctrl+Z：

- Tへ戻る

Ctrl+Shift+Z：

- Cross復活

---

## 136. Test 15 — dimension fallback Undo/Redo

through pair片方130→200：

fallback。

Ctrl+Z：

Cross復活。

Redo：

fallback復活。

---

## 137. Test 16 — butt thickness edit

butt 130→200。

期待：

- valid Cross維持
- Material維持

---

## 138. Test 17 — standard Delete through + repair

Crossからthrough member1本を標準Delete。

残る3本を選択して：

```text
接合を再生成
```

期待：

- stale Cross geometryからT geometryへrepair

---

## 139. Test 18 — standard Delete butt + repair

butt member削除。

manual rebuildでT geometry正常。

---

## 140. Test 19 — save/reopen

Crossを保存→Blender終了→再起動→open。

期待：

- Cross classification
- through/butt role
- trim
- Material

維持。

---

## 141. Test 20 — rebuild after reopen

`接合を再生成`してもgeometry変化なし。

---

## 142. Test 21 — shading

Solid / Material Preview / perspective。

異常shadeなし。

---

# Part AE — implementation architecture

## 143. 推奨変更ファイル

```text
japanese_house_modeler/joints.py
japanese_house_modeler/junctions.py
tests/test_joints.py
```

---

## 144. ui.py

`joint_status_label()` のmappingだけを `joints.py` で拡張できるなら変更不要。

UI layout変更不要。

---

## 145. operators.py

既存affected regenerationで十分なら変更不要。

Crossのためだけに新Operatorを追加しない。

---

## 146. 原則変更しない

```text
japanese_house_modeler/connections.py
japanese_house_modeler/properties.py
japanese_house_modeler/__init__.py
```

---

# Part AF — atomicity

## 147. regeneration

Build 04-Cのatomic batch：

```text
build all geometry
create all new Mesh
copy Materials
swap all
rollback partial swap
```

を維持。

---

## 148. failure

Cross solverがfallbackすること自体は正常なgeometry結果であり、
exceptionではない。

invalid canonical data / nonidentity batch等、
既存operation rejection条件は維持。

---

# Part AG — performance

## 149. scale

1 junction最大4 memberの小規模計算。

linear scan / pair combinationで十分。

---

## 150. caching

persistent cache不要。

毎回canonical data + topologyから導出。

---

# Part AH — 完了条件

## 151. Build 04-E完了

Blender 5.2 LTS実機で：

- 90° Cross
- Wireframe no-overlap
- 45° Cross
- 15° Cross
- shallow fallback
- butt unequal thickness
- through unequal fallback
- equal restore
- START/END mix
- deterministic through pair
- T -> Cross
- Cross -> T
- Cross -> CORNER
- Undo / Redo
- dimension edit
- Material保持
- standard Delete repair
- save/reopen
- manual rebuild
- shading正常
- Build 04-D/04-C regression

を満たす。

---

# Part AI — 次段階候補

## 152. Build 04-F候補

Build 04-E後の候補：

```text
unequal through/main thicknessのstep boundary joint
```

T / Cross双方の異厚hostを一般化する。

---

## 153. その次

候補：

```text
FOUR_WAY generic geometry
```

ただしgeneric 4-wayはwall priority / clipping policyが必要になるため、
Crossより設計判断が多い。

---

## 154. 将来のwall priority

T / Crossのhost決定をユーザー制御したい場合、
将来：

```text
wall_priority
joint_priority
```

等のsemantic propertyを追加できる。

Build 04-Eでは追加しない。
