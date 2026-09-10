# 日本住宅モデラー — Build 04-G Specification

## 1. 目的

Build 04-Gでは、Build 04-Fまでの接合処理を維持したまま、
これまで安全フォールバックとしていた

```text
異厚host pair + 斜めbranch / butt
```

を、2D footprint clipping により実Mesh対応する。

主対象：

```text
T_JUNCTION:
main pair = 130 / 200 mm
branch    = 45° / 15° など

CROSS:
through pair = 130 / 200 mm
butt pair    = 45° / 225° など
```

Build 04-Fでは異厚hostに対して90°直交だけを
4-point step profileで対応した。

Build 04-Gでは、
**guest Wall（T branch / Cross butt）の canonical rectangle から
host pair の canonical rectangle union を差し引き、
far endpointにつながる単一simple polygon componentだけを残す**
という方針を採用する。

Blender Boolean modifierは使用しない。
Meshをsource of truthにしない。
すべてcanonical Wall dataとConnection topologyから再計算する。

---

## 2. 基準状態

Build 04-GはGitHub `main` の以下を基準とする。

```text
9b0ca76 Implement Build 04-F step junction geometry
```

Build 04-FまでBlender 5.2 LTS実機テスト済み。

---

## 3. Build 05-Bまでの開発方針

壁機能は以下の順で進める。

```text
Build 04-G
異厚host + 斜めT/Cross

Build 04-H
未対応junctionの整理

Build 05-A
既存Wall途中への接続 / 交差 / 必要なWall分割

Build 05-B
壁システム全体の仕上げ・安定化
```

Build 05-B完了時点で、
壁開発をいったん停止し、
次機能の順序を改めて検討する。

---

# Part A — Build 04-Gの範囲

## 4. 実装する機能

Build 04-Gでは以下を実装する。

- T_JUNCTION の異厚main pair + oblique branch
- CROSS の異厚through pair + oblique butt pair
- 45°など一般的な斜め接続
- 15°など比較的浅い斜め接続
- guest footprintからhost unionを差し引くpure 2D clipping
- far endpointに接続するcomponentだけを採用
- concave endpoint profile
- 可変長endpoint profile
- START / END混在
- member order independence
- caller independence
- thick side reverse
- branch / butt unequal thickness
- equal ↔ unequal dimension transition
- 90° Build 04-F regression
- equal-thickness Build 04-D / 04-E regression
- shallow-angle safe fallback
- Undo / Redo
- Save / Reopen
- Material保持
- manual rebuild
- standard Delete repair
- pure geometry test

---

## 5. Build 04-Gで実装しない機能

以下は今回実装しない。

- THREE_WAY実Mesh
- FOUR_WAY実Mesh
- MULTI実Mesh
- arbitrary multi-host polygon union
- 5本以上のjunction clipping
- wall途中intersection detection
- automatic Wall split
- user-selectable through priority
- structural semantics
- interior / exterior side
- openings
- doors / windows
- floor / ceiling
- Blender Boolean modifier
- persistent evaluated Mesh topology
- general-purpose CAD boolean engine
- holesを持つWall footprint
- disconnected Wall Mesh component

---

# Part B — source of truth

## 6. canonical data

引き続き唯一のsource of truthは：

```text
jhm_wall.start
jhm_wall.end
jhm_wall.wall_thickness
jhm_wall.wall_height
Connection topology
```

---

## 7. 派生情報を保存しない

以下をProperty等へ保存してはならない。

- clipped polygon
- endpoint profile
- host union polygon
- positive / negative role
- clipping intersections
- component graph
- Cross through/butt role
- visible boundary
- polygon vertex count

毎回導出する。

---

## 8. Mesh逆算禁止

既存Meshのvertex位置から：

- Wall centerline
- endpoint
- thickness
- clipping profile

を逆算しない。

---

# Part C — 既存pathを維持

## 9. Equal T

main pairがequal thicknessなら：

```python
calculate_t_solution()
```

を最優先。

Build 04-Dの：

- 90°
- 45°
- 15°
- shallow fallback

を維持。

---

## 10. Unequal orthogonal T

main pairがunequalでbranchがexact/effectively exact 90°なら：

```python
calculate_t_step_solution()
```

を次に使用。

Build 04-Fの4-point stepを維持。

---

## 11. Unequal oblique T

上記2pathで解決せず、
かつ異厚main + oblique branchとして安全条件を満たす場合のみ
Build 04-G clipping solverを使用。

---

## 12. Equal Cross

through pairがequal thicknessなら：

```python
calculate_cross_solution()
```

を最優先。

Build 04-Eを維持。

---

## 13. Unequal orthogonal Cross

through pairがunequalでbutt axisが90°なら：

```python
calculate_cross_step_solution()
```

を使用。

Build 04-Fを維持。

---

## 14. Unequal oblique Cross

上記で解決しない異厚through + oblique buttのみ
Build 04-G clipping solverへ進む。

---

## 15. solver priority

推奨：

```text
T:
1 calculate_t_solution
2 calculate_t_step_solution
3 calculate_t_oblique_solution
4 FALLBACK

Cross:
1 calculate_cross_solution
2 calculate_cross_step_solution
3 calculate_cross_oblique_solution
4 FALLBACK
```

名称は同等であれば変更可。

---

# Part D — なぜ04-Fのstep式だけでは足りないか

## 16. 90°の場合

90°ではguestの2本のside edgeが
host centerlineのpositive / negative sideに固定される。

そのため：

```text
65 mm
100 mm
```

のように各sideへhost half-thicknessを割り当てれば
正確なstepになる。

---

## 17. 斜めの場合

45°等ではguest side edgeが、

```text
thin hostから一度外へ出る
↓
thick hostへ入り直す
↓
もう一度外へ出る
```

場合がある。

単純に「最初の交点」だけを使うと、
不要なsliver、overlap、gapを生む。

---

## 18. Build 04-Gの原則

Build 04-Gは、
局所line-intersectionの寄せ集めではなく、

```text
Guest rectangle
MINUS
Union(Host positive rectangle, Host negative rectangle)
```

を2D footprintとして評価する。

そのうえで：

```text
Guest far endpointへつながるcomponent
```

だけを採用する。

これによりexit / re-entryを正しく処理する。

---

# Part E — clippingは2Dのみ

## 19. Blender Boolean禁止

`Boolean` modifierやBMesh Boolean等を
接合処理の基礎に使用しない。

---

## 20. pure geometry

clippingは：

```text
XY / endpoint-local 2D
```

だけで行う。

Blender scene evaluationに依存しない。

pure/mock unit test可能であること。

---

## 21. extrusion

得られたsimple lower polygonを
Build 04-Fのgeneric extrusionでZ方向へ押し出す。

---

# Part F — guest endpoint-local coordinate

## 22. local basis

T branch / Cross buttの接続endpointについて：

```text
J = canonical junction
u = endpoint_data direction
n = endpoint_data normal
h = guest half-thickness
L = guest canonical length
```

---

## 23. local coordinate

world point `P` を：

```text
s = dot(P - J, u)
q = dot(P - J, n)
```

で表す。

---

## 24. meaning

```text
s = 0
```

がcanonical junction。

```text
s > 0
```

がguest内部 / far endpoint方向。

```text
q = +h
```

がlocal plus side。

```text
q = -h
```

がlocal minus side。

---

## 25. guest rectangle

guest canonical rectangleはendpoint-localで：

```text
G0 = (0, +h)
G1 = (0, -h)
G2 = (L, -h)
G3 = (L, +h)
```

---

## 26. far endpoint probe

far component識別用に：

```text
P_far = (L - eps, 0)
```

を使用する。

`eps` はcanonical lengthに対して十分小さく、
かつclipping toleranceより大きい値とする。

---

# Part G — host rectangles

## 27. main / through host

host pair各memberについて、
junction endpointからcanonical rectangleを構築する。

---

## 28. host data

各host member：

```text
J
u_host_member
n_host_member
h_host
L_host
```

---

## 29. canonical host rectangle

world XYで：

```text
J + n*h
J - n*h
J + u*L - n*h
J + u*L + n*h
```

相当の4頂点。

orientationは内部で統一。

---

## 30. evaluated host Meshは使わない

hostの現在Meshが：

- miter
- T
- Cross
- step

で変形されていても、
Build 04-G clipping hostはcanonical rectangleから構築。

理由：
今回のjunction側でmain / throughはJでsquare endpointだから。

---

## 31. other endpoint joint

hostの反対endpointで別junctionがあっても、
今回のclipがlocal範囲内に収まる限り許可。

---

# Part H — Cross role policy

## 32. `_cross_role_data()`

Build 04-Fで導入した：

```python
_cross_role_data()
```

をそのまま利用。

---

## 33. through selection

Build 04-Eからのpolicy：

```text
world-X alignment最大
tie = geometry-only canonical axis
```

を変更しない。

---

## 34. thickness role flip禁止

through 130/200だからといって
別pairへthrough roleを切り替えない。

---

# Part I — T role policy

## 35. `t_junction_roles()`

既存 helperを使用。

main pair / branchを再定義しない。

---

## 36. exact host collinearity

classificationは1° toleranceを持つが、
Mesh clipping用host pairは従来どおりeffectively exact collinearを要求。

---

# Part J — oblique判定

## 37. orthogonal path優先

04-Gは90°を再実装しない。

guest axisがhost axisとorthogonal tolerance内なら
04-Fに任せる。

---

## 38. parallel付近

guest axisがhost axisとnear parallelなら、
clipが長大になりやすい。

line angleだけで一律禁止するのではなく、
後述のlocal trim limitで判定する。

ただし数値的に完全/ほぼparallelで
2D arrangementがdegenerateになる場合はfallback。

---

## 39. 期待角度

最低限：

```text
45°
135°
15°
165°
```

等を安全条件の範囲で扱う。

---

## 40. shallow

例：

```text
2.5°
177.5°
```

は通常local trim limitを超えるためfallbackすることを期待。

---

# Part K — specialized polygon difference

## 41. 対象

今回必要なのは一般booleanではなく：

```text
one Guest rectangle
minus
union of exactly two Host rectangles
```

のみ。

---

## 42. output

出力は：

```text
0 or more simple polygon components
```

になり得る。

---

## 43. 採用component

guest far probeを含むcomponentを採用。

---

## 44. multiple far components

far probeを含むcomponentが一意に決定できない：
fallback。

---

## 45. no far component

host unionがguestをfar endpointまで切断：
fallback。

---

# Part L — arrangement-based implementation

## 46. 推奨アルゴリズム

以下のplanar segment arrangementを推奨する。

1. Guest rectangle boundary
2. Host A rectangle boundary
3. Host B rectangle boundary
4. 全edge intersectionを求める
5. 各edgeをintersection pointでsplit
6. 各subsegmentがvisible difference boundaryか判定
7. directed boundary graphを作る
8. simple cyclesをtrace
9. far componentを選択
10. connection profileを抽出

同等に安全な実装なら別方式可。

---

# Part M — edge splitting

## 47. edge

各polygon edgeを：

```text
P(t) = A + t(B-A)
0 <= t <= 1
```

として扱う。

---

## 48. pairwise intersections

異なるsource polygon間だけでなく、
必要なら全edge pairを検査。

---

## 49. proper crossing

通常交差をsplit pointとして追加。

---

## 50. endpoint touch

edge endpointが他edge上にある場合も
split pointとして扱う。

---

## 51. collinear overlap

collinear overlap時は、
overlap区間の両endpointをsplit pointへ追加。

---

## 52. dedupe

同一edge上のt値はtolerance内でdedupe。

---

# Part N — clipping tolerance

## 53. 新constant

推奨：

```text
_ANGLED_CLIP_TOLERANCE_M = 1.0e-9
```

または同等の小さいmeter tolerance。

---

## 54. junction toleranceとの区別

canonical junction一致には既存：

```text
1.0e-6 m
```

を維持。

polygon edge split / point mergeには
より小さいclipping toleranceを使用してよい。

---

## 55. overmerge禁止

130mm / 200mmのstep差等を
toleranceで潰さない。

---

# Part O — point classification

## 56. visible region

point `P` に対して：

```text
inside_visible(P)
=
inside Guest(P)
AND
NOT inside HostUnion(P)
```

---

## 57. boundary-aware classification

edge上pointを扱うため：

```text
inside
outside
boundary
```

を区別できるhelperが望ましい。

---

## 58. midpoint

split subsegmentのmidpointを用いて
局所boundary性を判定する。

---

# Part P — boundary subsegment selection

## 59. normal probes

各subsegment midpoint `M` に対し、
segment normal方向へ：

```text
M + eps*n
M - eps*n
```

を評価。

---

## 60. keep condition

片側だけがvisible regionなら、
そのsubsegmentはdifference boundary。

---

## 61. drop condition

両側visible：
内部線なのでdrop。

両側not visible：
host内部seam等なのでdrop。

---

## 62. orientation

visible regionがleft sideに来るよう
directed segment orientationを統一。

---

## 63. internal host seam

host A / BがJで共有する内部end-face部分は
両側がhost unionなので自動dropすること。

---

# Part Q — graph

## 64. vertex merge

segment endpointをtolerance内でgraph vertexへmerge。

---

## 65. simple boundary

正常ケースでは各cycle vertexが：

```text
1 incoming
1 outgoing
```

になることを期待。

---

## 66. branching

degreeが曖昧 / branching：
fallback。

---

## 67. open chain

閉じないboundary：
fallback。

---

## 68. duplicate edge

同じ幾何edgeを二重登録しない。

---

# Part R — cycle tracing

## 69. all cycles

kept directed segmentsから
全simple cycleをtrace。

---

## 70. validation

各cycleを：

```python
validate_lower_polygon()
```

相当で検証。

---

## 71. orientation

最終的にCCWへ正規化してよい。

---

## 72. zero area

reject。

---

# Part S — component selection

## 73. far probe containment

cycle polygonが：

```text
P_far
```

を含むか確認。

---

## 74. exactly one

far probeを含むcycleが1つだけであること。

---

## 75. disconnected sliver

junction近傍に小さなguest sliverが残っても、
far probeを含まないcomponentは捨てる。

これがBuild 04-Gで重要。

---

## 76. reason

斜めguestはthin hostから一度露出後、
thick hostへ再侵入することがある。

その途中sliverをWall本体へ残さない。

---

# Part T — holes

## 77. holes非対応

far component内部にhole cycleがある場合：
fallback。

---

## 78. why

Blender Mesh extrusion側は現在
hole polygonを扱わない。

---

## 79. expected

通常のT/Cross junctionではholeは発生しない。

---

# Part U — local trim safety

## 80. local trim limit

新constant推奨：

```text
_MAX_ANGLED_TRIM_FACTOR = 10.0
```

---

## 81. scale

limit：

```text
max(
    positive_host_half,
    negative_host_half,
    guest_half
) * _MAX_ANGLED_TRIM_FACTOR
```

---

## 82. profile depth

connection profile全pointについて：

```text
s = dot(P-J, guest_direction)
```

---

## 83. conditions

全point：

```text
s >= -parameter_tolerance
s < guest_length - _MIN_WALL_LENGTH_M
s <= local_trim_limit
```

を要求。

---

## 84. shallow fallback

15°程度は通常limit内。

2.5°程度は通常limit超過しfallback。

---

# Part V — host far-end safety

## 85. host far endをtrim boundaryに使わない

今回の接合はjunction local処理。

hostの反対endpoint faceを
branch/butt trim boundaryとして使用してはならない。

---

## 86. edge tags

host rectangle edgeを最低限：

```text
JUNCTION_END
SIDE_PLUS
FAR_END
SIDE_MINUS
```

等でtagできるとよい。

---

## 87. forbidden

selected connection profileが：

```text
FAR_END
```

由来segmentを含むならfallback。

---

## 88. alternate

edge tagを使わない実装なら、
host-axis parameterがfar lengthに達したcutを検出しreject。

---

# Part W — guest far endpoint safety

## 89. far edge保持

採用componentは、
guest canonical far edgeの有効部分を保持する必要がある。

---

## 90. full far edge

原則：

```text
(L,-h) -> (L,+h)
```

全体がvisibleであること。

hostがfar edgeへ到達するケースはfallback。

---

## 91. reason

今回の接合trimがWall全長へ及ぶ場合は
local junctionとして不適切。

---

# Part X — connection profile extraction

## 92. result polygon

採用far componentから、
connection側boundary chainを抽出する。

---

## 93. guest side edges

endpoint-local：

```text
q=+h
q=-h
```

のside boundary上で、
far componentが始まるcut pointを求める。

---

## 94. plus cut

local plus side：

```text
q=+h
```

上のjunction側cut point。

---

## 95. minus cut

local minus side：

```text
q=-h
```

上のjunction側cut point。

---

## 96. profile path

plus cutからminus cutまで、
**far edgeを通らないcycle path**
をconnection profileとする。

---

## 97. ordering

必ず：

```text
local plus -> local minus
```

順。

---

## 98. far path除外

もう一方のcycle pathは：

```text
plus side
far edge
minus side
```

を通るためendpoint profileではない。

---

# Part Y — variable profile length

## 99. profile point count

04-Gではprofileは固定4点ではない。

---

## 100. examples

状況により：

```text
2 points
3 points
4 points
5+ points
```

を許容。

---

## 101. no arbitrary cap

simple polygonとして安全なら
小さい固定上限を設けなくてもよい。

ただし今回inputがrectangles×3なので
実際の点数は小さい。

---

## 102. adjacent duplicate

tolerance内adjacent duplicateはcollapse可。

---

# Part Z — endpoint profile architecture

## 103. Build 04-F architectureを維持

既存：

```python
endpoint_joint_profile()
_resolved_endpoint_profiles()
endpoint_joint_pair()
build_wall_geometry()
```

を維持。

---

## 104. no architecture rollback

再び2-point pair中心へ戻さない。

---

## 105. compatibility

`endpoint_joint_pair()` は引き続き：

```text
(profile[0], profile[-1])
```

を返すcompatibility view。

---

# Part AA — T oblique solver

## 106. 推奨関数

```python
calculate_t_oblique_solution(wall_object, endpoint)
```

または同等。

---

## 107. checks

最低限：

- T_JUNCTION / count3
- `t_junction_roles()`
- all endpoint data valid
- all identity transform
- canonical J一致
- main pair exact collinear
- main thickness unequal
- not orthogonal path
- not numerically degenerate
- canonical host rectangles valid
- guest rectangle valid
- clipping result valid
- exactly one far component
- no holes
- local trim limit
- host far end未使用
- guest far edge保持

---

## 108. output

概念：

```text
main_members
branch_member
branch_profile
junction
host_axis
```

---

## 109. statuses

main：

```text
T_MAIN
```

branch：

```text
T_BRANCH
```

新status不要。

---

## 110. shared safety

solver failure時：

```text
T members 3本すべて FALLBACK
```

---

# Part AB — Cross oblique solver

## 111. 推奨関数

```python
calculate_cross_oblique_solution(wall_object, endpoint)
```

または同等。

---

## 112. role source

必ず：

```python
_cross_role_data()
```

を使用。

---

## 113. through

through 2本はJでsquare endpoint。

---

## 114. butts

butt 2本をそれぞれguestとして
through host unionからclip。

---

## 115. all-or-nothing

butt A成功
butt B失敗

ならCross全体fallback。

---

## 116. output

概念：

```text
through_members
((butt_member, profile), ...)
junction
host_axis
```

---

## 117. statuses

through：

```text
CROSS_THROUGH
```

butt：

```text
CROSS_BUTT
```

---

# Part AC — orthogonal regression

## 118. T 90° unequal

04-G solverより前に04-Fが解決。

---

## 119. Cross 90° unequal

同様。

---

## 120. exact geometry

Build 04-Fで実機確認した
65/100mmのstep profileを変えない。

---

# Part AD — equal regression

## 121. T equal 45°

Build 04-D。

---

## 122. Cross equal 45°

Build 04-E。

---

## 123. no clipping

equal hostに04-G clippingを無用に使用しない。

---

# Part AE — thick side reverse

## 124. T

main：

```text
left130 / right200
```

と：

```text
left200 / right130
```

でclipped profileが物理的にmirrorする。

---

## 125. Cross

through pairも同様。

---

## 126. role

role自体は変わらない。

---

# Part AF — branch / butt thickness

## 127. guest thickness

branch/butt thicknessは
130mm固定ではない。

---

## 128. examples

```text
host 130/200
guest 130
guest 200
```

双方を可能な限り処理。

---

## 129. safety

guestが極端に太く：

- host far endへ到達
- disconnected far component
- hole
- local trim limit超過

ならfallback。

---

# Part AG — START / END

## 130. endpoint-local basis

START / ENDの違いは
`endpoint_data()`のinward direction/normalで吸収。

---

## 131. physical invariance

同じ物理geometryなら：

- START
- END
- mixed

で同じclipped shape。

---

## 132. profile ordering

どちらでもlocal plus -> local minus。

---

# Part AH — member order

## 133. T

`t_junction_roles()`依存。

---

## 134. Cross

`_cross_role_data()`依存。

---

## 135. clipping

arrangement結果はpolygon source orderへ依存してはならない。

---

## 136. graph vertex identity

object pointer / name / creation orderを
geometry role決定へ使わない。

内部dedupe keyとしてpointerを使う場合でも、
結果geometryへ影響してはならない。

---

# Part AI — polygon validation

## 137. existing validator

Build 04-Fの：

```python
validate_lower_polygon()
```

を維持。

---

## 138. clipped component

採用cycleに対して：

- finite
- no adjacent duplicate
- nonzero area
- no self intersection
- no non-adjacent touch
- no collinear overlap

を確認。

---

## 139. tolerance

既存validatorを大きく緩めない。

---

# Part AJ — winding / normals

## 140. lower polygon

最終Wall footprintは
Build 04-Fと同じexpected windingへ正規化。

---

## 141. extrusion

既存generic extrusion：

```text
2N vertices
N+2 faces
```

を使用。

---

## 142. face normal

Solid / Material Previewで：

- black face
- inverted top/bottom
- inside-out side

を発生させない。

---

# Part AK — Wall-local fallback

## 143. shared solver safe

junction clipping自体はsafeでも、
同じWallの反対endpoint jointとの組合せで
footprint invalidになる場合がある。

---

## 144. existing policy

`MITER`
`T_BRANCH`
`CROSS_BUTT`

のvisual endpointをsquareへ戻す
Wall-local fallbackを維持。

---

## 145. oblique profile

04-G profileも同じ対象。

---

# Part AL — shared vs local

## 146. shared failure

junction geometry計算自体がunsafe：

T：
全3本fallback。

Cross：
全4本fallback。

---

## 147. local failure

junction solverはsafeだが
あるWall全体polygonだけinvalid：

そのWall visual endpointのみfallback。

---

# Part AM — dimension edit

## 148. T 45° transition

```text
main 130/130
```

→ Build04D equal oblique T。

```text
main 130/200
```

→ Build04G unequal oblique T。

```text
main 130/130
```

→ Build04Dへ戻る。

---

## 149. Cross 45° transition

equal through：
Build04E。

unequal through：
Build04G。

equal：
Build04E。

---

## 150. 90° transition

equal：
04-D/E。

unequal：
04-F。

04-Gへ誤流入しない。

---

# Part AN — endpoint move

## 151. detach

oblique step T / Crossからmemberをdetach。

---

## 152. expected

Cross -> T
T -> CORNER / CONTINUATION
等へ既存regenerationで移行。

---

# Part AO — Undo / Redo

## 153. dimension

equal ↔ unequal transitionをUndo/Redo。

---

## 154. endpoint

attach / detachをUndo/Redo。

---

## 155. geometry

clipped component、status、Materialが正しく復元。

---

# Part AP — Save / Reopen

## 156. no derived persistence

clipped polygonを保存しない。

---

## 157. reopen

canonical data/topologyから同じclippingを再導出。

---

## 158. deterministic

Save/Reopenでvertex countやprofile shapeが変わらない。

---

# Part AQ — standard Delete

## 159. no depsgraph handler

従来どおり。

---

## 160. stale mesh

standard Delete直後のstale形状は許容。

---

## 161. rebuild

`接合を再生成`で
現在topologyに応じたshapeへrepair。

---

# Part AR — Material

## 162. atomic regeneration

既存：

```python
regenerate_wall_meshes()
```

のbuild-then-swapを維持。

---

## 163. material slots

clipped polygonでvertex数が変わっても
Materialを保持。

---

# Part AS — performance

## 164. scope small

junctionあたりrectangle 3枚程度なので
O(E²) arrangementで十分。

---

## 165. no premature optimization

複雑なspatial index不要。

---

## 166. clarity

geometry correctness / determinismを優先。

---

# Part AT — failure behavior

## 167. fail safe

exceptionで壊れたMeshを残すのではなく
safe fallbackまたは既存atomic operation reject。

---

## 168. no partial Cross

片buttだけclippedは不可。

---

## 169. no partial T

branchだけ不正なのにmain statusだけT_MAIN等
shared mismatchを作らない。

---

# Part AU — pure helper tests

## 170. local transform

world→guest local→world roundtrip。

---

## 171. canonical rectangles

START/END双方で同じ物理rectangle。

---

## 172. segment intersections

- proper crossing
- endpoint touch
- collinear overlap
- parallel no-hit

---

## 173. split

multiple intersectionsを正順でsplit。

---

## 174. boundary selection

internal host seam drop。

visible boundary keep。

---

## 175. cycle

simple cycle trace。

---

## 176. component

far probe component selection。

---

## 177. sliver

junction近傍sliverを捨て、
far componentだけ採用。

---

## 178. hole

hole scenarioはreject。

---

# Part AV — T unit tests

## 179. 45° standard

```text
main 130 / 200
branch 130
angle 45°
```

valid。

---

## 180. status

main x2：

```text
T_MAIN
```

branch：

```text
T_BRANCH
```

---

## 181. build geometry

`build_wall_geometry(branch)` がNoneでない。

---

## 182. profile

profileは2点以上。

finite。

simple footprint。

---

## 183. 135°

mirror oblique directionでもvalid。

---

## 184. thick side reverse

130/200 ↔ 200/130で
expected physical shapeがmirror。

---

## 185. branch 200

45°で安全条件を満たす通常長hostならvalid。

---

## 186. 15°

valid。

---

## 187. 2.5°

local trim limit等によりfallback。

---

## 188. equal 45 regression

130/130はBuild04D pathでvalid。

---

## 189. unequal 90 regression

130/200 +90°はBuild04F path。

---

## 190. START/END mix

複数pattern。

---

## 191. main order

main pair member order reversalで同physical result。

---

## 192. caller

3 memberどこからsolverを呼んでもshared result一致。

---

## 193. position mismatch

fallback。

---

## 194. transform

fallback。

---

## 195. short guest

far component/local safety失敗でfallback。

---

## 196. short host

far-end faceが必要になる場合fallback。

---

# Part AW — explicit exit/re-entry regression

## 197. important geometry

例：

```text
host negative = 130
host positive = 200
branch = 45°
```

でbranch side edgeが：

```text
thin hostからexit
thick hostへre-enter
thick hostからfinal exit
```

するケースをpure test化。

---

## 198. expectation

最初のexitをtrim endpointとして採用しない。

---

## 199. far component

far endpointへつながるcomponentだけ残る。

---

## 200. no sliver merge

junction側に残る小さなsliverを
far Wall polygonへ誤接続しない。

---

# Part AX — Cross unit tests

## 201. 45° standard

through X：

```text
130 / 200
```

butt axis：

```text
45° / 225°
```

valid。

---

## 202. statuses

X pair：

```text
CROSS_THROUGH
```

butt pair：

```text
CROSS_BUTT
```

---

## 203. both profiles

両butt profile valid。

---

## 204. butt unequal

```text
butt 130 / 200
```

も通常長ならvalid。

---

## 205. 15°

valid。

---

## 206. shallow

2.5° pairはshared fallback。

---

## 207. 90 regression

unequal through + 90°：
Build04F。

---

## 208. equal 45 regression

Build04E。

---

## 209. role no flip

through thickness reverseでも
world-X through維持。

---

## 210. tie-break

±45 Crossの既存tie-breakを壊さない。

---

## 211. START/END

できれば全16 combinations。

---

## 212. member order

できれば全24 permutations。

---

## 213. caller independence

全memberから同role/profile set。

---

## 214. one unsafe butt

Cross全4本fallback。

---

## 215. short through host

far-end faceが必要：
shared fallback。

---

# Part AY — polygon/extrusion regression

## 216. 4-point

既存normal wall。

---

## 217. 6/8-point

Build04F step。

---

## 218. arbitrary N

Build04G clipped profileで
Nが変動してもextrusion可能。

---

## 219. formula

lower N：

```text
vertices = 2N
faces = N + 2
```

---

## 220. indices

全face index valid。

---

## 221. finite

全vertex finite。

---

## 222. winding

signed area / normals consistent。

---

# Part AZ — Build04C regression

## 223. corner

90 / 45 / 15 miter。

---

## 224. unequal corner

維持。

---

## 225. acute

fallback。

---

## 226. continuation

維持。

---

# Part BA — Build04D regression

## 227. equal T

90 / 45 / 15。

---

## 228. 179.5 main

fallback。

---

## 229. branch thickness

200 valid。

---

## 230. order

維持。

---

# Part BB — Build04E regression

## 231. equal Cross

90 / 45 / 15。

---

## 232. world-X

維持。

---

## 233. tie

維持。

---

## 234. butt unequal

維持。

---

# Part BC — Build04F regression

## 235. unequal orthogonal T

130/200 +90°。

---

## 236. step depth

65/100mm。

---

## 237. unequal orthogonal Cross

through130/200 + butt90°。

---

## 238. flat ↔ step

dimension transition。

---

# Part BD — real Blender tests: T

## 239. Test 1

T：

```text
left main 130
right main 200
branch 130
angle 45°
```

期待：

- T字候補
- T字主壁 x2
- T字枝壁
- fallbackなし

---

## 240. Test 2

Top Wireframe close-up。

期待：

- gapなし
- large overlapなし
- disconnected sliverなし
- spikeなし

---

## 241. Test 3

branch 135°。

valid。

---

## 242. Test 4

thick side reverse：

```text
left200 / right130
```

physical trimが反転。

---

## 243. Test 5

branch 200 / angle45°。

通常長hostでvalid。

---

## 244. Test 6

angle15°。

valid。

---

## 245. Test 7

angle2.5°。

安全フォールバック。

---

## 246. Test 8

main130/130 +45°。

Build04D regression。

---

## 247. Test 9

main130/200 +90°。

Build04F regression。

---

# Part BE — real Blender tests: Cross

## 248. Test 10

through X 130/200。

butt pair45/225°。

期待：

- 十字候補
- X through
- oblique butt
- fallbackなし

---

## 249. Test 11

Wireframe。

両buttにgap/spike/sliverなし。

---

## 250. Test 12

butt 130/200 unequal。

valid。

---

## 251. Test 13

butt angle15°。

valid。

---

## 252. Test 14

2.5°。

shared fallback。

---

## 253. Test 15

through厚さ左右反転。

roleはXのまま。

---

## 254. Test 16

through130/200 + butt90°。

Build04F regression。

---

## 255. Test 17

through130/130 + butt45°。

Build04E regression。

---

# Part BF — real Blender tests: deterministic

## 256. Test 18

T START/END mixed。

---

## 257. Test 19

Cross START/END mixed。

---

## 258. Test 20

Cross creation order変更。

world-X through維持。

---

# Part BG — real Blender tests: dynamic

## 259. Test 21

45° T：

```text
130/130
→ 130/200
→ 130/130
```

Build04D
→ Build04G
→ Build04D。

---

## 260. Test 22

45° Cross：

equal
→ unequal
→ equal。

04E
→ 04G
→ 04E。

---

## 261. Test 23

Undo / Redo T。

---

## 262. Test 24

Undo / Redo Cross。

---

## 263. Test 25

oblique Crossからbutt detach。

残りがTとして正常再生成。

---

## 264. Test 26

oblique Tからdetach。

2-wall CORNER等へ戻る。

---

# Part BH — persistence / repair

## 265. Test 27

standard Delete後manual rebuild。

---

## 266. Test 28

Save / Reopen。

---

## 267. Test 29

Rebuild after reopen。

---

## 268. Test 30

Material / shading。

---

# Part BI — Material / shading criteria

## 269. no anomalies

以下なし：

- black face
- face flip
- Z-fighting的な大overlap
- open hole
- non-manifold-looking gap
- spike
- detached sliver

---

## 270. perspective

Topだけでなく
斜めperspectiveでも確認。

---

# Part BJ — topology invariants

## 271. connection data

Build04Aのreciprocal topologyを変更しない。

---

## 272. no new topology type

04-Gのために新Connection Propertyを追加しない。

---

## 273. no role state

T/Cross roleを保存しない。

---

# Part BK — transform policy

## 274. nonidentity

managed Wallにnonidentity Object transformがある場合、
既存policyどおりsafe fallback / operation reject。

---

## 275. no auto bake

transformを勝手にApplyしない。

---

# Part BL — atomicity

## 276. build first

affected Wall全geometryを先に準備。

---

## 277. swap later

全成功後にMesh swap。

---

## 278. failure

部分swapを残さない。

---

# Part BM — code organization

## 279. expected file

主変更：

```text
japanese_house_modeler/joints.py
tests/test_joints.py
```

---

## 280. junctions.py

原則変更不要。

Cross/T role helperは既存で足りる。

---

## 281. operators.py

原則変更不要。

---

## 282. properties.py

変更不要。

---

## 283. ui.py

新statusなし。

変更不要。

---

## 284. connections.py

変更不要。

---

# Part BN — recommended helpers

## 285. optional

例：

```python
_world_to_endpoint_local(...)
_endpoint_local_to_world(...)
_canonical_rectangle(...)
_segment_intersections(...)
_split_segments(...)
_point_location(...)
_difference_boundary_segments(...)
_trace_boundary_cycles(...)
_select_far_component(...)
_extract_connection_profile(...)
_clip_guest_against_host_union(...)
```

名称は任意。

---

## 286. avoid monolith

1関数にboolean全処理を詰め込み過ぎない。

---

## 287. pure helpers

可能な限りbpy非依存。

---

# Part BO — determinism

## 288. sorting

floating geometryのorderingが必要な場合：

- coordinate
- segment parameter
- canonical geometric keys

を使用。

---

## 289. forbidden tie sources

- object name
- pointer
- creation order
- collection order

をgeometry tie-breakに使用しない。

---

# Part BP — tests count

## 290. expectation

Build04Fの40 testsを削らず、
04-G追加後は概ね：

```text
50 tests以上
```

を期待。

テスト数そのものよりcoverageを優先。

---

# Part BQ — debug information

## 291. no persistent debug mesh

clip polygonをsceneへ残さない。

---

## 292. temporary debug

開発用にpure helper resultをtest assertionするのは可。

---

# Part BR — completion criteria

## 293. Build04G完了

最低限以下がBlender 5.2 LTS実機で成立：

- unequal T 45°
- unequal T 135°
- unequal T 15°
- shallow T fallback
- branch thick case
- unequal Cross 45°
- unequal Cross 15°
- shallow Cross fallback
- butt unequal
- thick side reverse
- START/END
- creation/member order independence
- 90° unequal 04-F regression
- equal 45° 04-D/E regression
- equal ↔ unequal transition
- Undo/Redo
- Cross→T
- T→Corner
- Delete/rebuild
- Save/Reopen
- Material
- shading
- no sliver/gap/spike
- Build04C/D/E/F regression

---

# Part BS — safety philosophy

## 294. when unsure

曖昧なpolygon arrangement、
複数far component、
hole、
open graph、
far-end clipping、
local trim limit超過は：

```text
安全フォールバック
```

---

## 295. no forced geometry

無理にMeshを生成しない。

---

# Part BT — next stage

## 296. Build 04-H

04-G完了後は、
現在`未対応`となる：

- THREE_WAY
- FOUR_WAY
- MULTI

のうち、
実住宅で必要な範囲を整理する。

---

## 297. Build 05-A

その後：

```text
既存Wall途中への接続
途中intersection
必要に応じたWall split
```

へ進む。

---

## 298. Build 05-B

壁システムの：

- editing
- delete
- rebuild
- persistence
- UX
- regression

を総点検し、
一度「壁完成」とする。

---

## 299. checkpoint

Build 05-B完了後、
壁以外の次機能順序を
改めて検討してから進む。

---

# Part BU — Codex implementation requirements

## 300. base

実装開始前に：

```text
git log -1 --oneline
```

がBuild04G specification commitになっていることを確認。

---

## 301. network Git禁止

Codex Cloudから：

```text
git fetch
git pull
git push
git ls-remote
```

を実行しない。

---

## 302. required checks

実装後：

```text
python -m compileall -q japanese_house_modeler
python -m unittest discover -s tests -v
git diff --check
git diff --stat
git status --short
```

---

## 303. AST

addon内Python全fileをAST parse。

---

## 304. no ZIP

CodexはZIPを作成しない。

---

## 305. no PR

PR作成不要。

---

# Part BV — review requirements

## 306. final report

Codexは最低限：

- implementation summary
- clipping architecture
- far component selection
- sliver handling
- T solver
- Cross solver
- regression impact
- tests
- changed files
- diff stat
- commit SHA if any

を報告。

---

## 307. full source review

レビュー時は必要に応じて：

```text
joints.py
tests/test_joints.py
```

の完全内容を分割提示可能であること。

---

# Part BW — final invariant

## 308. final rule

Build 04-G後も：

```text
Wall canonical data + topology
        ↓
deterministic derived joint geometry
        ↓
Mesh
```

という一方向を維持する。

Meshは結果であり、
設計情報ではない。
