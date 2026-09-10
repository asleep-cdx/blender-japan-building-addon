# 日本住宅モデラー — Build 04-F Specification

## 1. 目的

Build 04-Fでは、Build 04-Eまでの接合処理を維持したまま、
これまで安全フォールバックとしていた **異厚host pair** を、
日本住宅で最も重要な **直交T字 / 直交Cross** について正確なstep profileで処理する。

対象：

```text
T_JUNCTION:
main pair = 130 / 200 mm
branch    = 130 mm など

CROSS:
through pair = 130 / 200 mm
butt pair    = 130 / 130 mm、130 / 200 mm など
```

異厚hostでは、junction中心Jの両側でhost外面位置が異なるため、
1本の直線trimでは正確に接続できない。

Build 04-Fでは、butt/branch Wallの接続端を
**段差形状（step-shaped endpoint profile）** として生成し、
host 2本の実際の外面へ隙間・大きなoverlapなく接続する。

---

## 2. 基準状態

Build 04-FはGitHub `main` の以下を基準とする。

```text
caa3b3f Implement Build 04-E cross joints
```

Build 04-EまでBlender 5.2 LTS実機テスト済み。

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
- `BUILD_04_E_SPECIFICATION.md`

Build 04-FはBuild 04-Eまでの実機テスト済み挙動を壊してはならない。

---

# Part A — Build 04-Fの範囲

## 4. 実装する機能

Build 04-Fでは以下を実装する。

- T_JUNCTIONの異厚main pair対応
- CROSSの異厚through pair対応
- exact / effectively exact 90° branch/butt axis
- step-shaped endpoint profile
- 4頂点固定footprintから可変頂点simple polygon footprintへの拡張
- 可変頂点polygonのextrusion
- START / END混在
- host member順非依存
- thick side / thin sideの反転
- branch/butt thickness差への対応
- dimension editによるflat ↔ stepの自動切替
- Undo / Redo
- Save / Reopen
- Material保持
- manual rebuild
- standard Delete後repair
- Build 04-C / 04-D / 04-E regression

---

## 5. Build 04-Fで実装しない機能

以下は今回実装しない。

- 異厚host + 斜めbranch
- 異厚through + 斜めCross
- generic polygon boolean
- arbitrary-angle stepped clipping
- THREE_WAY geometry
- FOUR_WAY geometry
- MULTI geometry
- user-selectable wall priority
- structural semantics
- interior / exterior side
- openings
- doors / windows
- standard Delete depsgraph handler
- wall途中intersection detection
- floor / ceiling

---

# Part B — 重要な設計判断

## 6. なぜ単純trimでは不十分か

host pairが同厚ならouter boundaryは1本の直線：

```text
--------------------
```

で表現できる。

異厚hostでは：

```text
------------+
            |
      ------+
```

のようにjunction中心で段差が生じる。

そのためbranch/buttの2本のside lineを
単一host lineへ交差させるだけでは、

- 片側gap
- 片側overlap
- 斜めの偽boundary

のいずれかになる。

---

## 7. Build 04-Fの解

直交junctionに限定し、
branch/butt endpointを **4-point step chain** とする。

通常endpoint：

```text
P_plus
P_minus
```

異厚step endpoint：

```text
P_plus
C_plus
C_minus
P_minus
```

となる。

これをWallのfar endpoint chainと組み合わせるため、
Wall footprintは4頂点ではなく通常6頂点になる。

---

# Part C — source of truth

## 8. canonical data

source of truthは引き続き：

```text
jhm_wall.start
jhm_wall.end
jhm_wall.wall_thickness
jhm_wall.wall_height
Connection topology
```

のみ。

---

## 9. step profileは派生

以下をpersistent propertyへ保存してはならない。

- step points
- host thickness side
- positive/negative host role
- endpoint polygon points
- resolved footprint

毎回canonical data + topologyから導出する。

---

# Part D — 対象junction

## 10. T

対象：

```text
classification.key == T_JUNCTION
member_count == 3
```

かつmain pairがexact/effectively exact collinear。

---

## 11. Cross

対象：

```text
classification.key == CROSS
member_count == 4
```

かつBuild 04-Eのdeterministic through pairが決定できる。

---

## 12. classification semantics

Build 04-Bのclassificationは変更しない。

`_ANGLE_TOLERANCE_DEG = 1.0` も変更しない。

---

# Part E — equal thickness pathは維持

## 13. T equal main

main thickness：

```text
130 / 130
```

ならBuild 04-Dの既存 `calculate_t_solution()` をそのまま使用する。

既存angled T対応を壊さない。

---

## 14. Cross equal through

through thickness：

```text
130 / 130
```

ならBuild 04-Eの既存 `calculate_cross_solution()` をそのまま使用する。

90 / 45 / 15° Crossを壊さない。

---

## 15. Build 04-F path

新しいstep solverは：

```text
host pair thicknessが異なる場合のみ
```

起動する。

equal pathのgeometry/mathを無用に置換しない。

---

# Part F — orthogonal requirement

## 16. 異厚T

異厚main pairに対し、
branch axisがhost axisと実質90°の場合のみstep処理する。

推奨：

```text
_STEP_ORTHOGONAL_TOLERANCE = 1.0e-6
```

条件：

```text
abs(dot(u_branch, u_host)) <= tolerance
```

---

## 17. 異厚Cross

異厚through pairに対し、
butt axisがthrough axisと実質90°の場合のみstep処理する。

---

## 18. oblique unequal junction

例：

```text
main 130 / 200
branch 45°
```

または：

```text
through 130 / 200
butt axis 45°
```

は今回：

```text
安全フォールバック
```

とする。

---

## 19. equal host angled junction

host pairがequal thicknessなら、
Build 04-D / 04-Eのangled処理を維持。

---

# Part G — host axis canonicalization

## 20. undirected host axis

host pairの2方向から、
Build 04-Eと同様にorder/sign-independent canonical axis：

```text
u_host
```

を導出する。

---

## 21. positive / negative half

junction Jから：

```text
+u_host
```

方向へ伸びるhost memberを：

```text
host_positive
```

```text
-u_host
```

方向へ伸びるmemberを：

```text
host_negative
```

とする。

---

## 22. assignment

各host memberのendpoint direction `u_member` に対して：

```text
dot(u_member, u_host) > 0
```

ならpositive。

```text
dot(u_member, u_host) < 0
```

ならnegative。

---

## 23. identity independence

positive/negative決定に：

- object pointer
- name
- member order
- creation order
- START/END

を使用しない。

---

# Part H — host half thickness

## 24. values

```text
h_pos = host_positive.thickness / 2000
h_neg = host_negative.thickness / 2000
```

meters。

---

## 25. unequal requirement

step solverでは：

```text
abs(h_pos - h_neg) > thickness_tolerance
```

を要求。

ほぼequalならexisting flat solverへ任せる。

---

# Part I — T step geometry

## 26. coordinate concept

host axisをX、
branch outgoing directionをYと考える。

例：

```text
host_negative  <---- J ----> host_positive

branch:
                     |
                     |
                     v or ^
```

---

## 27. branch local side

branch：

```text
J
u_branch
n_branch
h_branch
```

---

## 28. branch side points at canonical junction

```text
S_plus  = J + n_branch*h_branch
S_minus = J - n_branch*h_branch
```

---

## 29. which host half each side belongs to

各side pointについて：

```text
side_axis = dot(S_side - J, u_host)
```

を計算。

orthogonalなら片方がpositive、片方がnegativeになる。

---

## 30. positive-side host

side_axis > 0なら、
そのbranch edgeはhost_positiveのouter faceまで進む。

exit parameter：

```text
t = h_pos
```

branch directionがhost normalの正負どちらでも、
`u_branch` 自体がjunctionからbranch内部へ向くため、
outgoing距離としてhalf thicknessを使用できる。

---

## 31. negative-side host

side_axis < 0なら：

```text
t = h_neg
```

---

## 32. side exit points

```text
P_plus  = S_plus  + u_branch * h_for_plus_side
P_minus = S_minus + u_branch * h_for_minus_side
```

---

## 33. center step points

junction center axis上：

```text
C_for_plus  = J + u_branch * h_for_plus_side
C_for_minus = J + u_branch * h_for_minus_side
```

---

## 34. endpoint chain

local plusからlocal minusへ：

```text
P_plus
C_for_plus
C_for_minus
P_minus
```

をstep endpoint chainとする。

---

## 35. equal side values

step solverはunequal時だけ呼ぶため、
通常 `C_for_plus != C_for_minus`。

floating tolerance内で重複する場合は
adjacent duplicateを除去してよい。

---

# Part J — host length safety

## 36. なぜ必要か

branch widthはhost axisの両側へ：

```text
h_branch
```

だけ張り出す。

host memberが極端に短い場合、
branch side pointがhost segmentの実長を越える可能性がある。

---

## 37. requirement

最低限：

```text
length(host_positive) > h_branch + epsilon
length(host_negative) > h_branch + epsilon
```

を要求。

---

## 38. failure

不足ならstep solution全体fallback。

---

# Part K — branch length safety

## 39. step depth

branchはjunctionから：

```text
max(h_pos, h_neg)
```

程度内側へtrimされる。

---

## 40. requirement

```text
branch_length > max(h_pos, h_neg) + _MIN_WALL_LENGTH_M
```

を要求。

---

## 41. failure

short branch：

```text
安全フォールバック
```

---

# Part L — Cross step geometry

## 42. deterministic through pair

Build 04-Eのworld-X policyを変更しない。

through pairはthickness差でflipしない。

---

## 43. unequal through

Build 04-Eでは：

```text
through 130 / 200
```

をfallbackした。

Build 04-Fでは、
butt axisがorthogonalならstep geometryを許可する。

---

## 44. through members

through pair 2本は引き続き：

```text
canonical Jでsquare endpoint
```

のまま。

---

## 45. each butt member

butt pairの各Wallに、
T branchと同じstep endpoint chainを生成する。

一方はhost normalの+側、
もう一方は-側へ伸びる。

---

## 46. butt thickness independent

butt A=130
butt B=200

でもよい。

各butt Wall自身の：

```text
h_butt
```

でside pointsを決める。

---

## 47. host length requirement

各butt Wallについて、
through positive / negative host member lengthが：

```text
> h_butt + epsilon
```

であること。

butt 2本のうちどちらかがunsafeならshared Cross step solution全体fallback。

---

## 48. butt length requirement

各butt Wall：

```text
length > max(h_pos, h_neg) + _MIN_WALL_LENGTH_M
```

を要求。

---

# Part M — shared all-or-nothing

## 49. T shared step solution

推奨：

```python
calculate_t_step_solution(wall_object, endpoint)
```

または同等。

---

## 50. Cross shared step solution

推奨：

```python
calculate_cross_step_solution(wall_object, endpoint)
```

または同等。

---

## 51. T

Tでstep solverがunsafeなら：

```text
3 membersすべてsquare
FALLBACK
```

---

## 52. Cross

Crossでstep solverがunsafeなら：

```text
4 membersすべてsquare
FALLBACK
```

---

## 53. partial shared success禁止

junction solver段階で：

```text
one branch side step
other side fallback
```

や、

```text
one Cross butt step
other Cross butt fallback
```

を作らない。

---

# Part N — endpoint profile abstraction

## 54. 現在の問題

Build 04-Eまではendpoint geometryは常に2点：

```text
(pair_plus, pair_minus)
```

だった。

Build 04-Fのstep endpointは4点必要。

---

## 55. profile abstraction

新たにendpointを：

```text
ordered chain of 2 or more XY points
```

として扱える内部abstractionを追加する。

推奨例：

```python
endpoint_joint_profile(wall_object, endpoint)
```

返り値概念：

```text
(points, status)
```

---

## 56. normal endpoint

通常：

```text
(points=(plus, minus), status=...)
```

---

## 57. step endpoint

異厚T branch / Cross butt：

```text
(points=(P_plus, C_plus, C_minus, P_minus), status=...)
```

---

## 58. ordering invariant

profileは必ず：

```text
local plus -> local minus
```

順。

START / ENDいずれでも同じlocal rule。

---

# Part O — endpoint_joint_pair compatibility

## 59. public/internal compatibility

既存：

```python
endpoint_joint_pair()
```

を削除しない。

---

## 60. normal

normal profileなら従来どおり2点を返す。

---

## 61. step

step profileの場合、
互換用pairとして：

```text
(profile[0], profile[-1])
```

を返してよい。

ただしBuild 04-Fの実Mesh生成はpairだけを使用してはならない。

---

## 62. status

step Tでもstatusは：

```text
T_BRANCH
```

のまま。

step Crossでも：

```text
CROSS_BUTT
```

のまま。

新しいUI status labelは不要。

---

# Part P — resolved endpoint profiles

## 63. 新resolver

推奨：

```python
_resolved_endpoint_profiles(wall_object)
```

---

## 64. output

概念：

```text
start_profile
end_profile
statuses
```

---

## 65. normal existing joints

以下は2-point profile：

- ISOLATED
- CONTINUATION
- MITER
- T_MAIN
- T_BRANCH equal-host
- CROSS_THROUGH
- CROSS_BUTT equal-host
- FALLBACK
- UNSUPPORTED

---

## 66. step joints

以下は4-point profile：

- unequal-host T_BRANCH
- unequal-through CROSS_BUTT

---

# Part Q — variable polygon footprint

## 67. lower polygon

Wall footprint：

```text
lower = start_profile + end_profile
```

とする。

各profileはlocal plus→minus順。

---

## 68. examples

normal / normal：

```text
2 + 2 = 4 vertices
```

step / normal：

```text
4 + 2 = 6 vertices
```

step / step：

```text
4 + 4 = 8 vertices
```

---

## 69. duplicate handling

隣接点がfloating tolerance内で同一なら、
polygon構築前に安全にcollapseしてよい。

---

# Part R — polygon validation一般化

## 70. current limitation

既存 `validate_lower_polygon()` は4頂点前提。

Build 04-Fでは可変頂点対応が必要。

---

## 71. requirement

最低限：

- `len(points) >= 3`
- finite
- non-zero area
- adjacent duplicateなし
- non-adjacent edge self-intersectionなし

---

## 72. backward compatibility

関数名 `validate_lower_polygon()` をそのまま一般化してよい。

既存4点テストを壊さない。

---

## 73. self intersection

N辺について、
隣接edgeと同一edgeを除外し、
non-adjacent edge同士のcrossを検査。

---

## 74. simple polygon

Build 04-Fで生成するstep footprintがsimple polygonであること。

---

# Part S — polygon-level Wall-local fallback

## 75. existing policy

MITER / T_BRANCH / CROSS_BUTTは、
反対endpoint geometryとの組合せでpolygon invalidなら
Wall-local fallback可能。

---

## 76. step profile

step T_BRANCH / CROSS_BUTTも同じpolicy。

---

## 77. fallback action

該当endpoint profileを：

```text
square 2-point profile
```

へ戻し、

```text
status = FALLBACK
```

とする。

---

## 78. shared vs local

junction solverがunsafe：
全junction members shared fallback。

junction solverはsafeだが、
1 Wallの反対endpointとの組合せだけpolygon invalid：
そのWall endpointだけlocal fallback。

この区別をコメントで明確にする。

---

# Part T — generic extrusion

## 79. current geometry

現在は4 lower verticesを前提に、
固定facesを生成している。

---

## 80. Build 04-F geometry

lower polygon頂点数：

```text
N >= 3
```

に一般化する。

---

## 81. vertices

```text
lower vertices: 0 ... N-1
upper vertices: N ... 2N-1
```

---

## 82. bottom face

lower polygon orderがCCWなら：

```text
reversed(range(N))
```

でbottom face。

---

## 83. top face

```text
range(N, 2N)
```

---

## 84. side faces

各edge i -> j：

```text
(i, j, N+j, N+i)
```

j = (i+1)%N。

---

## 85. normals

Solid / Material Previewで
face normalが外向きになること。

---

# Part U — Material preservation

## 86. existing atomic regen

Build 04-Cからの：

- new Meshを先に生成
- Material copy
- swap
- rollback

を維持。

---

## 87. variable polygon

vertex/face数が変わっても、
Material slotsを失わない。

---

# Part V — T integration

## 88. endpoint profile resolution

T_JUNCTION：

1. Build 04-D equal-host `calculate_t_solution()`
2. それが不成立で、hostがunequalならBuild 04-F step solver
3. それも不成立ならFALLBACK

という順序でよい。

---

## 89. important

Build 04-D equal angled Tが
新step solverへ誤って流れないこと。

---

# Part W — Cross integration

## 90. endpoint profile resolution

CROSS：

1. Build 04-E equal-through `calculate_cross_solution()`
2. それが不成立で、selected through pairがunequalならBuild 04-F step solver
3. それも不成立ならFALLBACK

---

## 91. role stability

Build 04-Eのthrough/butt selection helper/mathを共有する。

thicknessでroleを変えない。

---

# Part X — helper refactor

## 92. duplicate logic

必要なら以下をshared helperへ整理してよい。

- canonical axis
- positive/negative host member selection
- host pair exact collinearity
- member endpoint position validation
- identity transform validation

---

## 93. caution

大規模refactorは避ける。

Build 04-D/Eのtested mathを必要以上に書き換えない。

---

# Part Y — dimension edit behavior

## 94. T equal -> unequal

正常90°T：

```text
main 130 / 130
```

から片方を200へ変更。

Build 04-Dまではfallbackだった。

Build 04-F期待：

```text
main 130 / 200
branch step profile
T字主壁 x2
T字枝壁 x1
```

---

## 95. T unequal -> equal

200側を130へ戻す。

step profileから
Build 04-D flat trimへ自動復帰。

---

## 96. Cross equal -> unequal

正常90°Cross：

```text
through 130 / 130
```

から片方を200へ。

Build 04-Eまではfallback。

Build 04-F期待：

```text
through 130 / 200
Cross step geometry
十字通し壁 x2
十字突合せ壁 x2
```

---

## 97. Cross unequal -> equal

thicknessを揃えると
Build 04-E flat Crossへ戻る。

---

## 98. butt/branch thickness edit

branch/butt thicknessを変更しても、
host segment length safetyを満たす限りstepを再計算。

---

# Part Z — Undo / Redo

## 99. T dimension

130/130 → 130/200：

step化。

Ctrl+Z：

flat Tへ戻る。

Redo：

step T復活。

---

## 100. Cross dimension

130/130 → 130/200 through：

step Cross。

Undo：

flat Cross。

Redo：

step Cross。

---

## 101. endpoint move

step junctionをdetachした場合も、
既存old/new affected regenで正しく：

- T -> CORNER/CONTINUATION/isolated
- Cross -> T

へ戻る。

---

# Part AA — Save / Reopen

## 102. persistence

step pointsは保存しない。

保存対象はcanonical data/topologyのみ。

---

## 103. reopen

同じgeometryなら
save/reopen後も同じstep footprintを導出。

---

## 104. rebuild

`接合を再生成`しても同じstep geometry。

---

# Part AB — standard Delete

## 105. policy

standard Delete直後のstale Meshは従来どおり許容。

depsgraph handlerは追加しない。

---

## 106. repair

残存Wallを選択し：

```text
接合を再生成
```

で新classificationに応じたgeometryへrepair。

---

# Part AC — transforms

## 107. non-identity

step junction memberに1本でもnonidentity transform：

shared step solver fallback。

---

## 108. batch edit

managed dimension / endpoint operationでは
既存regenerate安全条件に従い必要ならoperation reject。

---

# Part AD — tests変更の重要事項

## 109. 既存期待値変更

Build 04-D test：

```text
test_unequal_main_thickness_falls_back_for_all
```

は90°異厚mainが今回supportedになるため、
そのままの期待値では仕様と矛盾する。

更新すること。

---

## 110. T regression replacement

旧「130/200ならfallback」テストは：

```text
90° 130/200 -> step T valid
45° 130/200 -> fallback
```

へ分離する。

---

## 111. Build 04-E test

既存：

```text
test_through_must_match_but_butts_may_differ
```

のthrough unequal部分も今回仕様変更。

更新すること。

---

## 112. Cross regression replacement

```text
90° through 130/200 -> step Cross valid
45° through 130/200 -> fallback
```

をテストする。

---

# Part AE — unit tests: polygon foundation

## 113. 4-point

従来rectangleをvalidateできる。

---

## 114. 6-point step

正しいstep polygonをvalidateできる。

---

## 115. 8-point

両endpointがstepでもsimple polygonならvalidateできる。

---

## 116. invalid

self-crossing N-gonをreject。

---

## 117. extrusion

6-point lower polygonから：

```text
12 vertices
8 faces
```

を生成する。

内訳：

- bottom 1
- top 1
- sides 6

---

# Part AF — unit tests: T step

## 118. standard 90° unequal

```text
main positive 130
main negative 200
branch 130
```

valid。

---

## 119. status

main x2：

```text
T_MAIN
```

branch：

```text
T_BRANCH
```

---

## 120. profile length

branch connection endpoint profile：

```text
4 points
```

---

## 121. expected offsets

host axis X、
branch +Y例。

branch plus/minus edgeがXのどちら側かに応じて：

```text
Y = 0.065
Y = 0.100
```

のstepを持つ。

---

## 122. reverse thick side

main positive 200
main negative 130

stepが左右反転。

---

## 123. branch END

branch junction endpointがENDでも同じphysical geometry。

---

## 124. main START/END mix

main membersのjunction endpointをSTART/END混在させても同じ。

---

## 125. member permutation

junction member列挙順を全入替してもphysical profile同一。

---

## 126. 45° unequal

fallback。

---

## 127. equal 45°

Build 04-D pathでvalid。

---

## 128. short branch

fallback。

---

## 129. short main side

branch halfwidthより短いhost memberがあればfallback。

---

## 130. branch 200

host lengths十分ならvalid step。

---

# Part AG — unit tests: Cross step

## 131. standard 90°

through X：

```text
130 / 200
```

butt Y：

```text
130 / 130
```

valid。

---

## 132. roles

X pair：

```text
CROSS_THROUGH
```

Y pair：

```text
CROSS_BUTT
```

---

## 133. profiles

Y+ / Y- butt各接続endpointが4-point step profile。

---

## 134. butt unequal

through：

```text
130 / 200
```

butt：

```text
130 / 200
```

valid。

---

## 135. role no flip

through Xが130/200でも
Y pairへthrough roleをflipしない。

---

## 136. thick side reverse

X positive/negativeの厚さ入替で
stepが左右反転するがroleはXのまま。

---

## 137. START/END combinations

少なくとも複数mix、
できれば16組み合わせをpure test。

---

## 138. member order

全24 permutationまたは十分な全探索で
through/buttとstep geometryが不変。

---

## 139. 45° unequal through

fallback。

---

## 140. equal 45°

Build 04-E pathでvalid。

---

## 141. short butt

片方でもshortならshared Cross fallback。

---

## 142. short through side

butt halfwidthを受けられないhost member長ならshared fallback。

---

# Part AH — regression tests

## 143. Build 04-E equal Cross

必ず維持：

- 90°
- 45°
- 15°
- shallow fallback
- butt unequal
- deterministic world-X
- tie-break
- START/END
- member order

---

## 144. Build 04-D equal T

必ず維持：

- 90°
- 45°
- 15°
- shallow fallback
- branch 200
- 179.5 main fallback
- START/END
- member order

---

## 145. Build 04-C

必ず維持：

- CORNER miter
- CONTINUATION
- unequal thickness miter
- acute fallback
- polygon validation
- atomic regeneration
- Material

---

# Part AI — Blender実機テスト

## 146. Test 1 — 90° T 130/200

main：

```text
left 130
right 200
```

branch：

```text
130
```

期待：

- T字候補
- main x2 = T字主壁
- branch = T字枝壁
- fallbackしない

---

## 147. Test 2 — T step Wireframe

Top + Wireframeで拡大。

期待：

branchの接続端が斜め1本ではなく、
中央で段差を持つstep形状。

---

## 148. Test 3 — T thick side reverse

left 200
right 130

期待：

step左右反転。

---

## 149. Test 4 — T branch 200

main 130/200、
branch 200。

期待：

valid step。

---

## 150. Test 5 — T 45° unequal

main 130/200、
branch 45°。

期待：

安全フォールバック。

---

## 151. Test 6 — T equal 45° regression

main 130/130、
branch 45°。

期待：

Build 04-Dと同じvalid T。

---

## 152. Test 7 — Cross 90° through 130/200

X pair：

```text
130 / 200
```

Y pair：

```text
130 / 130
```

期待：

- 十字候補
- X x2 = 十字通し壁
- Y x2 = 十字突合せ壁
- fallbackしない

---

## 153. Test 8 — Cross step Wireframe

Y+ / Y-両buttの接続端にstep。

中央gap/spikeなし。

---

## 154. Test 9 — Cross butt unequal

through X：

```text
130 / 200
```

butt Y：

```text
130 / 200
```

期待：

valid。

---

## 155. Test 10 — Cross thick side reverse

X pairの130/200を200/130に入替。

stepが左右反転。

---

## 156. Test 11 — Cross 45° unequal

selected through pair 130/200、
other axis 45°。

期待：

安全フォールバック。

---

## 157. Test 12 — Cross equal 45° regression

through equal。

期待：

Build 04-Eと同じvalid angled Cross。

---

## 158. Test 13 — START/END mix

T / Cross双方で確認。

---

## 159. Test 14 — dimension flat -> step -> flat T

main：

```text
130/130
-> 130/200
-> 130/130
```

期待：

flat T
-> step T
-> flat T

自動更新。

---

## 160. Test 15 — dimension flat -> step -> flat Cross

through：

```text
130/130
-> 130/200
-> 130/130
```

期待：

flat Cross
-> step Cross
-> flat Cross

---

## 161. Test 16 — Undo / Redo T

step化後Undo/Redo。

正常復元。

---

## 162. Test 17 — Undo / Redo Cross

同様。

---

## 163. Test 18 — Cross -> T detach

step Crossから1本detach。

残りがunequal-main orthogonal Tなら
step Tへ自動移行。

---

## 164. Test 19 — T -> CORNER detach

step Tから1本detachして2-wall cornerなら
Build 04-C miter。

---

## 165. Test 20 — standard Delete + rebuild

stale geometry後、
`接合を再生成`で正しいstep/flat geometryへrepair。

---

## 166. Test 21 — save/reopen

step T / step Crossを保存・再読込。

geometry/status/Material維持。

---

## 167. Test 22 — rebuild after reopen

形状不変。

---

## 168. Test 23 — Material / shading

Solid / Material Preview / perspective。

- Material消失なし
- black faceなし
- flipped faceなし
- strange shadingなし
- spikeなし

---

# Part AJ — implementation files

## 169. expected

主に：

```text
japanese_house_modeler/joints.py
tests/test_joints.py
```

---

## 170. junctions.py

positive/negative host assignment等を
read-only topology helperとして分離する必要があれば変更可。

---

## 171. operators.py

既存affected regenerationで足りるなら変更しない。

---

## 172. ui.py

新status labelを追加しないので原則変更不要。

---

## 173. no change expected

原則：

```text
connections.py
properties.py
__init__.py
```

変更不要。

---

# Part AK — architecture constraints

## 174. one Wall = one Object

維持。

---

## 175. no booleans

Build 04-FでBoolean modifierは使用しない。

---

## 176. no mesh-as-source

mesh verticesからcanonical endpoint/thicknessを逆算しない。

---

## 177. no persistent derived geometry

step chainは保存しない。

---

# Part AL — atomicity

## 178. regeneration

可変頂点Meshでも、
全affected Wallのgeometryを先に構築してからswap。

---

## 179. failure

1 Wallのgeometry buildがexception/Noneの場合、
既存atomic rollback方針を維持。

---

# Part AM — completion criteria

## 180. Build 04-F完了

Blender 5.2 LTS実機で最低限：

- 90° unequal T step
- T thick side reverse
- branch unequal
- unequal T angled fallback
- equal angled T regression
- 90° unequal Cross step
- butt unequal
- Cross thick side reverse
- unequal Cross angled fallback
- equal angled Cross regression
- START/END
- flat ↔ step dimension transition
- Undo/Redo
- Cross -> T
- T -> Corner
- Delete/rebuild
- save/reopen
- Material
- shading
- Build 04-C/D/E regression

を満たす。

---

# Part AN — 次段階候補

## 181. Build 04-G

候補：

```text
異厚host + angled branch/butt
```

generic polygon clipping / exact stepped boundary intersection。

---

## 182. Build 04-H候補

```text
FOUR_WAY generic geometry
```

---

## 183. wall priority

将来必要なら：

```text
wall_priority
joint_priority
```

を追加し、
Cross through pairやT host roleをuser制御可能にする。

Build 04-Fでは追加しない。
