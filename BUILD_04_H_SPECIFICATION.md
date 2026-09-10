# 日本住宅モデラー — Build 04-H Specification（改訂版）

## 1. 目的

Build 04-Hでは、Build 04-Gまでに実装した実Mesh接合を維持したまま、
「形状として判定できるが未対応のjunction」と
「対応済みjunctionだが幾何条件が危険なので安全処理へ落とすケース」を整理する。

Build 04-Hの中心目的は、新しい複雑な接合形状を増やすことではない。

目的は次の3点である。

1. 未対応junctionを決定的かつ安全に扱う。
2. junction classification と実Mesh solverの意味を揃える。
3. Build 05-Aの「既存Wall途中への接続・交差・Wall分割」へ進む前に、
   endpoint junctionの基礎ルールを安定させる。
4. 既存の斜めWallの中心線を延長した作図ガイドと位置合わせを追加し、
   45°・15°などの斜めWallを逆方向から正確に描けるようにする。

Build 04-GまでのT字・十字・コーナー形状を壊してはならない。

---

## 2. 基準状態

Build 04-HはGitHub `main` の以下を基準とする。

```text
282eae7ac8de51c456be9db617e30b42c8cc6655
Implement Build 04-G oblique joint clipping
```

Build 04-GはBlender 5.2 LTS実機テスト済み。

---

## 3. Build 05-Bまでの開発順

```text
Build 04-H
未対応・特殊junctionの整理
+ 既存斜めWallの中心線延長ガイド / 延長線位置合わせ

Build 05-A
既存Wall途中への接続 / 交差 / 必要なWall分割

Build 05-B
壁システム全体の仕上げ・安定化
```

Build 05-B完了時点で壁開発をいったん停止し、
次機能の順序を改めて検討する。

---

# Part A — Build 04-Hの範囲

## 4. 今回実装する内容

Build 04-Hでは以下を実装する。

- 4-member junctionのCROSS判定を「一意な2組の反対方向ペア」に限定する
- 曖昧な4-member接続をFOUR_WAYとして扱う
- CONTINUATIONの実Mesh適用条件を明示する
- classification上はCONTINUATIONでも、実際の中心線が十分に一直線でない場合は安全フォールバック
- 接続endpoint座標が一致しないCONTINUATIONは安全フォールバック
- Object TransformがあるCONTINUATIONは安全フォールバック
- OVERLAP / THREE_WAY / FOUR_WAY / MULTIを明示的な未対応junctionとして扱う
- INVALIDを「未対応」ではなく安全フォールバックとして扱う
- 未対応junctionではendpointをsquare profileへ戻す
- 未対応junction追加前の切り欠き形状を残さない
- 未対応memberを外したあと、再生成すれば元の対応junction形状へ戻る
- 既存のT/Cross solver failureの安全フォールバックを維持
- 既存Build 04-C～04-Gの回帰テスト
- pure/mock unit tests
- 既存Wall中心線の延長ガイド
- 延長線への始点・終点位置合わせ
- 45° / 15°など斜めWallの逆向き作図
- endpoint snap優先順位の維持
- X/Y位置合わせ・Shift 15°補助の回帰
- Blender実機テスト

---

## 5. 今回実装しない内容

以下はBuild 04-Hでは実装しない。

- THREE_WAYの実Mesh接合
- FOUR_WAYの実Mesh接合
- MULTIの実Mesh接合
- Y字接合の高度なトリム
- 任意多角度4方向接合
- 5本以上の接合形状
- 同方向重複Wallの自動統合
- 重複Wallの自動削除
- Wall途中への接続
- Wall途中intersection detection
- automatic Wall split
- 交差位置での自動分割
- Blender標準Deleteを監視して自動再生成する機能
- 任意角度数値入力
- user-selectable Cross through priority
- interior / exterior side
- structural semantics
- openings
- doors / windows
- floor / ceiling
- Blender Boolean modifier

これらはBuild 05-A / 05-Bまたはそれ以降の対象とする。

---

# Part B — source of truth

## 6. canonical Wall data

唯一のsource of truthは引き続き以下である。

```text
jhm_wall.start
jhm_wall.end
jhm_wall.wall_thickness
jhm_wall.wall_height
Connection topology
```

Mesh形状は派生結果である。

---

## 7. 保存してはいけない派生情報

以下をProperty等へ永続保存しない。

- junction classification
- T main / branch role
- Cross through / butt role
- unsupported reason
- endpoint profile
- miter point
- clipped polygon
- solver selection result

毎回canonical dataとConnection topologyから導出する。

---

## 8. Mesh逆算禁止

既存Mesh vertexから以下を逆算しない。

- Wall centerline
- endpoint
- thickness
- height
- junction role
- junction classification

---

# Part C — classification整理

## 9. 現在の分類

`junctions.py` の分類キーは維持する。

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

既存のpublic名称を不要に変更しない。

---

## 10. 2-member classification

2本接続の分類ルール自体は維持する。

```text
約180°         -> CONTINUATION
約0°           -> OVERLAP
それ以外       -> CORNER
```

ここで `_ANGLE_TOLERANCE_DEG = 1.0` は
「junctionの大まかな分類」に使用する。

重要：
classificationでCONTINUATIONになったことと、
実Meshとして安全な直線継続を適用できることは同義ではない。

Build 04-Hではこの2段階を明確に分離する。

---

## 11. 3-member classification

既存方針を維持する。

一意な反対方向ペアが1組あり、
残り1本がそのどちらとも同方向重複でなければ：

```text
T_JUNCTION
```

それ以外は：

```text
THREE_WAY
```

THREE_WAYの実Mesh接合は今回実装しない。

---

## 12. 4-member classification — 重要変更

現在の `classify_directions()` は、
3種類のpairing候補のうち
「どれか1つでも2組の反対方向ペアを作れる」場合にCROSSとしている。

Build 04-Hではこれを変更する。

CROSSとしてよいのは：

```text
2組の反対方向ペアからなるpairingが
3候補中ちょうど1つだけ存在する
```

場合のみ。

擬似コード：

```python
candidates = [
    pairing
    for pairing in pairings
    if both_pairs_are_opposite(pairing)
]

if len(candidates) == 1:
    CROSS
else:
    FOUR_WAY
```

---

## 13. 曖昧な4-member接続

例：

```text
0°
180°
0°
180°
```

の4本が同一点に接続されている場合、
複数の「反対方向ペアの組み方」が成立する。

これは通常のCrossではない。

Build 04-Hでは：

```text
FOUR_WAY
```

と分類する。

実Meshは未対応としてsquare profileへ戻す。

---

## 14. cross_junction_pairs()との整合

`cross_junction_pairs()` は既に
「候補pairingがちょうど1つ」の場合だけ結果を返す。

Build 04-Hでは：

```text
classify_directions() == CROSS
```

と

```text
cross_junction_pairs() != None
```

の意味を可能な限り一致させる。

正常な4-member CROSSなのに
classificationはCROSS、role resolverはNoneという
不要な意味のずれを残さない。

---

## 15. 5-member以上

5本以上は引き続き：

```text
MULTI
```

とする。

Build 04-Hでは実Mesh接合しない。

---

# Part D — effective joint treatment policy

## 16. classification と joint treatment を分ける

UIには現在：

```text
始点形状
始点接合
```

の2種類がある。

この考え方を維持する。

例：

```text
始点形状：4方向接続
始点接合：未対応
```

は正しい。

一方：

```text
始点形状：T字候補
始点接合：安全フォールバック
```

も正しい。

前者は「junctionの種類そのものが未対応」。
後者は「対応している種類だが、その幾何条件では安全に解けない」。

この区別をBuild 04-Hで正式ルールとする。

---

## 17. treatment matrix

`endpoint_joint_profile()` の意味を次の表に揃える。

```text
Classification    Effective treatment

ISOLATED          ISOLATED

CONTINUATION      CONTINUATION
                  ただし実Mesh安全条件NGなら FALLBACK

CORNER            MITER
                  miter安全条件NGなら FALLBACK

OVERLAP           UNSUPPORTED

T_JUNCTION        T_MAIN / T_BRANCH
                  solver全失敗なら FALLBACK

THREE_WAY         UNSUPPORTED

CROSS             CROSS_THROUGH / CROSS_BUTT
                  solver全失敗なら FALLBACK

FOUR_WAY          UNSUPPORTED

MULTI             UNSUPPORTED

INVALID           FALLBACK
```

---

## 18. unsupported と fallback の意味

Build 04-Hでは意味を明確に分ける。

### UNSUPPORTED

junction classification自体は正常にできているが、
その種類の実Mesh処理をまだ実装していない。

対象：

```text
OVERLAP
THREE_WAY
FOUR_WAY
MULTI
```

UI：

```text
未対応
```

### FALLBACK

本来は対応対象、またはデータが不正だが、
幾何安全条件を満たさないためsquare profileへ戻した。

対象例：

```text
2.5°の危険なT
2.5°の危険なCross
near-parallel miter
classification上CONTINUATIONだが実中心線が非共線
接続endpoint位置不一致
INVALID
```

UI：

```text
安全フォールバック
```

---

# Part E — CONTINUATION safety

## 19. 背景

現在は2本の方向差が180°±1°以内なら
classification上CONTINUATIONになる。

しかし：

```text
179.5°
```

のようにわずかに曲がっている2本を
実Meshで単純square endpointとして扱うと、
外周に小さなgap / overlapが発生し得る。

Build 04-Hでは、
classification toleranceと実Mesh toleranceを分離する。

---

## 20. continuation solver / validator

新しいpure helperを追加してよい。

推奨例：

```python
calculate_continuation_solution(wall_object, endpoint)
```

または同等の明確な名前。

戻り値形式はCodex側で既存設計に合わせてよいが、
以下の条件をすべて確認すること。

---

## 21. member count

CONTINUATION実Meshを適用するには：

```text
classification.key == CONTINUATION
member_count == 2
```

であること。

`junction_members()` も実際に2 endpoint memberであること。

---

## 22. endpoint validity

両memberについて：

```python
endpoint_data(...)
```

が有効であること。

zero-length、NaN等は許可しない。

---

## 23. junction position

2 memberのcanonical endpoint位置は：

```text
<= _JOINT_POSITION_TOLERANCE_M
```

で一致すること。

現在値：

```text
1e-6 m
```

位置不一致なら：

```text
FALLBACK
```

---

## 24. exact/effectively exact collinearity

classificationは±1°を許容するが、
実Mesh continuationではより厳しくする。

推奨定数：

```python
_CONTINUATION_COLLINEAR_TOLERANCE = 1.0e-6
```

2本のendpoint inward directionを `d1`, `d2` とする。

必要条件：

```python
abs(cross(d1, d2)) <= tolerance
dot(d1, d2) < 0
```

つまり実質的に同一直線上で反対方向であること。

---

## 25. 179.5°など

例：

```text
classification = CONTINUATION
actual directions = 179.5°
```

この場合、

```text
始点形状：直線継続 (...)
始点接合：安全フォールバック
```

となってよい。

classificationを無理にCORNERへ変更しない。

分類とMesh安全性を分離する。

---

## 26. unequal thickness

一直線の2本のWall厚が異なっていても
CONTINUATIONを許可する。

例：

```text
130 mm ──●── 200 mm
```

junction faceが同じ中心線直交面に揃い、
幅だけ段差になる。

これはBuild 04-Hでは有効なCONTINUATIONとする。

---

## 27. Object Transform

managed Wallの接合計算はcanonical world data前提である。

CONTINUATION solverも
両Wallについて `has_identity_transform()` を確認すること。

非identityなら：

```text
FALLBACK
```

とする。

なお `regenerate_wall_meshes()` 全体の既存Transform拒否も維持する。

---

# Part F — unsupported square profile policy

## 28. square profile

次のclassificationでは：

```text
OVERLAP
THREE_WAY
FOUR_WAY
MULTI
```

各Wall endpointは：

```python
square_endpoint_pair()
```

に基づくsquare profileを使用する。

---

## 29. stale trimを保持しない

例：

1. 正常な異厚斜めT
2. 4本目の非対向Wallを同junctionへ追加
3. FOUR_WAYになる
4. 再生成

この場合、
元のT branchにあった切り欠きを保持してはならない。

全memberが未対応junction用のsquare endpointへ戻る。

ユーザーがBuild 04-G実機試験で確認した：

```text
3本T
↓
B壁追加
↓
4方向接続・未対応
```

の挙動を正式な仕様として固定する。

---

## 30. unsupported memberを外した場合

上の状態からB壁を外し、
再生成すると：

```text
FOUR_WAY
↓
T_JUNCTION
```

へ戻る。

元の3本がTとして安全なら、
Tの切り欠き形状をcanonical dataから再生成する。

過去Mesh形状を参照して復元してはならない。

---

## 31. MULTIからの復帰

正常Crossへ5本目を追加すると：

```text
MULTI / 未対応
```

となる。

5本目を外して再生成すると：

```text
CROSS
```

へ戻り、
Build 04-E / 04-F / 04-Gの適切なsolverで再生成される。

---

# Part G — existing solver priority

## 32. CORNER

Build 04-Cを維持。

```text
safe -> MITER
unsafe -> FALLBACK
```

変更しない。

---

## 33. T

solver priorityを変更しない。

```text
1. calculate_t_solution()
   equal main

2. calculate_t_step_solution()
   unequal + orthogonal

3. calculate_t_oblique_solution()
   unequal + oblique

4. FALLBACK
```

---

## 34. CROSS

solver priorityを変更しない。

```text
1. calculate_cross_solution()
   equal through

2. calculate_cross_step_solution()
   unequal + orthogonal

3. calculate_cross_oblique_solution()
   unequal + oblique

4. FALLBACK
```

---

## 35. unsupported classificationからsolverを呼ばない

```text
OVERLAP
THREE_WAY
FOUR_WAY
MULTI
```

からT/Cross/Corner solverを無理に呼ばない。

square profile + UNSUPPORTEDで終了する。

---

# Part H — topology policy

## 36. complete reciprocal graph

既存 `attach_to_junction()` の
junction内complete reciprocal graph方針を維持する。

Build 04-HでConnection storage形式を変更しない。

---

## 37. automatic topology repairはしない

Build 04-Hでは：

- missing reciprocal link
- stale custom topology
- arbitrary corrupt connection graph

を大規模に自動修復しない。

既存の安全処理を維持する。

---

## 38. Blender標準Delete

Blender標準 `Delete` を使った直後、
他WallのMeshに古い切り欠きが残ることがある。

現状：

```text
Delete
↓
接合を再生成
↓
修復
```

は既知仕様。

Build 04-Hでは自動Delete監視を実装しない。

これはBuild 05-Bの候補とする。

---

# Part I — 既存Wall中心線の延長ガイド / 延長線位置合わせ

## 38-A. 背景

Build 04-Gの実機Test 19で、
45°CrossをSTART / END混在で手作図しようとした際、
次の制約が確認された。

既存の斜めWall A：

```text
        ／ A
       ／
      ● junction
```

に対して、
Aと完全に一直線で反対方向となるWallを
「外側からjunctionへ向かって」描こうとしても、
現在の自由位置合わせはX/Y軸しか参照しない。

必要なのは：

```text
Aのcanonical centerlineをjunctionの反対側へ延長
↓
その延長線上に新しいWallの始点を正確に置く
↓
終点をjunction endpointへsnap
```

という作図補助である。

---

## 38-B. 目的

既存managed Wallのcanonical centerlineを基準に、
そのWall segmentの外側へ伸びる延長線を作図補助として利用する。

例：

```text
新Wall始点
    ＼
     ＼  ← Aの中心線の延長
      ●────────
       ＼
        ＼ A
```

これにより：

```text
45° ↔ 225°
15° ↔ 195°
```

のような正確な反対方向Wallを、
逆向き作図でも生成できるようにする。

---

## 38-C. canonical dataのみを使用

延長線はMesh vertexから求めない。

使用するのは：

```text
jhm_wall.start
jhm_wall.end
```

のみ。

方向：

```python
axis = normalize(end - start)
```

として求める。

Wallの厚さやMesh外形から中心線を推定しない。

---

## 38-D. 対象Wall

候補にするのは：

- managed Wall
- 現在のview layerに存在
- 現在のviewportでvisible
- 有効なstart/endを持つ
- canonical length > minimum
- Object Transformがidentity

のみ。

非identity transformのWallは、
表示Meshとcanonical centerlineが一致しない可能性があるため
延長線位置合わせ候補から除外する。

---

## 38-E. segment内部には適用しない

Build 04-Hの延長線位置合わせは、
既存Wallの「途中への接続」機能ではない。

既存Wallを：

```text
START ●────────● END
```

とすると、位置合わせ対象は：

```text
← 延長領域 ●────────● 延長領域 →
```

のみ。

Wall segmentの内部：

```text
●──────×──────●
```

にはこの機能でsnapしない。

理由：

```text
Wall途中への接続
Wall途中intersection
Wall split
```

はBuild 05-Aの責務だからである。

---

## 38-F. projection

raw cursor pointを既存Wallの無限中心線へ射影する。

canonical startを `S`、
unit axisを `D`、
Wall lengthを `L`、
raw pointを `P` とする。

```python
s = dot(P - S, D)
Q = S + D * s
```

`Q` が延長候補。

ただし：

```text
s < 0
または
s > L
```

の場合だけ候補とする。

`0 <= s <= L` はWall内部なので候補にしない。

数値境界には既存のgeometry toleranceと整合する
小さなepsilonを使用してよい。

---

## 38-G. screen-space判定

既存X/Y位置合わせと同様、
ユーザー操作感はscreen-space距離で判定する。

raw point `P` と projected point `Q` をviewportへ投影し：

```text
screen distance(P, Q) <= alignment threshold
```

なら候補。

既存：

```python
_ALIGN_DISTANCE_PX = 10.0
```

を共有してよい。

別定数にする場合も、
理由なく大きなsnap範囲へ変更しない。

---

## 38-H. endpoint snapを最優先

既存endpoint snap：

```python
_SNAP_DISTANCE_PX = 16.0
```

を最優先する。

優先順位：

```text
1. 既存Wall endpoint snap
2. 延長線 / X / Yなどのalignment
3. 通常cursor位置
```

endpoint snapが成立しているとき、
延長線alignmentで位置を上書きしない。

Connection topologyを作るのも
既存どおり実endpoint snap時だけ。

---

## 38-I. 延長線alignmentはConnectionを作らない

重要。

延長線上の点：

```text
Q
```

へ位置合わせしただけでは、
その既存WallとのConnection topologyを追加しない。

例：

```text
新Wall始点 Q
      ＼
       ＼
        ● existing endpoint
```

Qは単なる幾何位置合わせ。

新Wallの終点が既存endpointへsnapした場合だけ、
その終点にConnectionを作る。

これによりBuild 05-Aの
「Wall途中接続」を先取りしない。

---

## 38-J. 始点にも使用する

現在の `_resolve_start_candidate()` は
endpoint snap後、自由位置合わせを行う。

Build 04-Hでは、
新Wallの最初のクリック候補にも
延長線alignmentを使えるようにする。

これがTest 19再現に必須。

例：

```text
既存A
        ／
       ／
      ●

新Wall：
① Aの反対側延長線上をクリック
② ● junctionをクリック
```

①がcanonical延長線へ正確に補正されること。

---

## 38-K. 終点にも使用する

新Wallの2回目クリックでも、
endpoint snapが成立していない場合は
延長線alignmentを候補にできる。

ただし：

- endpoint snapがあればendpoint snap優先
- Wall segment内部へは延長線alignmentしない
- alignmentだけではConnectionを作らない

を守る。

---

## 38-L. X/Y alignmentとの競合

既存X/Y alignmentを削除しない。

候補：

```text
X位置合わせ
Y位置合わせ
既存Wall延長線位置合わせ
```

が同時に成立し得る場合、
screen-space距離が最小の候補を採用する。

同距離とみなせる場合は
実装上の決定的なtie-breakを設ける。

推奨：

```text
extension line
X
Y
```

または同等の固定順。

member enumeration orderやobject creation orderで
結果がランダムに変わらないこと。

---

## 38-M. Shift 15°補助との関係

既存Shift 15°角度拘束を壊さない。

Build 04-Hの主目的は、
Shiftを押さなくても
既存斜めWallの正確な延長線へ合わせられること。

Shift使用時の既存挙動：

```text
0°
15°
30°
45°
...
```

は維持する。

Shiftと延長線alignmentが同時に有効な場合、
既存操作感を壊さない決定的ルールを実装する。

最低条件：

- endpoint snapは常に最優先
- Shift角度拘束を無視して勝手な角度へ曲げない
- Shift無しでは延長線projectionを利用可能

必要ならShift中は、
constrained rayとextension lineの安全な交点だけを採用してよい。

---

## 38-N. guide表示

延長線alignmentが選ばれたとき、
ユーザーが何に吸着しているか視覚的に分かるようにする。

少なくとも：

```text
既存Wallの近いendpoint
↓
projected candidate
```

まで中心線方向のガイド線を描画する。

例：

```text
projected candidate
      ●
       ＼
        ＼  guide
         ● existing Wall endpoint
          ＼
           ＼ existing Wall
```

ガイド線は既存alignment guideと同系統の表示でよい。

---

## 38-O. guide reference

延長線候補を選んだ場合、
operator内部で少なくとも以下に相当する情報を保持してよい。

```text
reference Wall
reference endpoint / extension side
canonical line anchor
canonical axis
projected candidate
```

これはmodal operatorの一時状態のみ。

Propertyへ永続保存しない。

---

## 38-P. guide clear

cursorがalignment thresholdから外れたら、
延長ガイド状態を即座にclearする。

ESC / finish / draw handler removalでも
一時状態を残さない。

---

## 38-Q. existing draw stateとの統合

現在の：

```text
_x_align_reference
_y_align_reference
_snap_candidate
_snap_target_object
_snap_target_endpoint
```

を壊さない。

延長線用stateを追加してよい。

例：

```text
_extension_align_reference
_extension_align_candidate
```

名称は既存styleに合わせる。

---

## 38-R. visible endpoint iteratorの扱い

既存 `_visible_wall_endpoints()` は
endpoint snap / X/Y alignmentに使用されている。

延長線ではWallごとにstart/end両方が必要なので、
必要なら別のprivate iterator：

```python
_visible_walls()
```

等を追加してよい。

同じvisibility条件を重複実装しすぎない。

---

## 38-S. arbitrary angle inputは今回不要

Build 04-Hでは：

```text
角度数値入力欄
2.5°など任意角度を直接タイプ
角度HUDの新規実装
```

は必須ではない。

今回の目的は
「既存Wallと同じ中心線を正確に延長する」こと。

したがって既存Wallが45°なら45°、
15°なら15°、
任意の斜め角度ならその実際のcanonical方向をそのまま利用する。

---

## 38-T. Build 05-Aとの境界

この機能で可能になるのは：

```text
既存Wallの中心線延長上に
新規Wallの始点/終点を正確に置く
```

まで。

以下はまだ行わない。

```text
既存Wall途中へ自動接続
既存Wall途中でConnection作成
既存Wall分割
交差点検出
```

それらはBuild 05-A。

---

## 38-U. extension alignmentの受入条件

次を満たすこと。

1. 45°Wallの反対延長側へ正確に位置合わせできる
2. 15°Wallでも同様
3. START側・END側のどちらの延長でも使える
4. 新Wallの最初のクリックでも使える
5. 新Wallの2回目クリックでも使える
6. endpoint snapを邪魔しない
7. X/Y alignmentを壊さない
8. Shift 15°補助を壊さない
9. Wall segment内部へはこの機能でsnapしない
10. alignmentだけでConnection topologyを作らない
11. invisible Wallを候補にしない
12. nonidentity transformed Wallを候補にしない
13. ガイド表示がcursor状態に追従する
14. object creation orderで候補選択が不安定にならない

---

# Part J — implementation boundaries

# Part J — implementation boundaries

## 39. 主な変更対象

想定：

```text
japanese_house_modeler/junctions.py
japanese_house_modeler/joints.py
japanese_house_modeler/operators.py
tests/test_joints.py
```

延長線alignmentのpure helperを別moduleへ分離する方が
明確かつテスト容易になる場合は、
小さな専用module / test fileを追加してよい。
不要な抽象化は避ける。

必要最小限にする。

---

## 40. 原則変更しないファイル

特別な理由がない限り変更しない。

```text
japanese_house_modeler/connections.py
japanese_house_modeler/properties.py
japanese_house_modeler/ui.py
japanese_house_modeler/__init__.py
```

変更が必要だと判断した場合は、
実装前に理由を説明すること。

---

## 41. API compatibility

既存の以下を壊さない。

```python
classify_junction()
classification_label()
t_junction_roles()
cross_junction_pairs()
endpoint_joint_profile()
endpoint_joint_pair()
joint_status_label()
build_wall_geometry()
regenerate_wall_meshes()
```

---

## 42. geometry generation

`build_wall_geometry()` の
可変長profile一般押し出し方式を維持する。

unsupported junctionのために
特殊Mesh生成器を追加しない。

---

# Part K — required pure tests

## 43. 既存test

Build 04-G時点の全unit testを維持する。

現在の既存testはすべてPASSすること。

---

## 44. unique Cross classification

次を確認する。

```text
0 / 180 / 90 / 270
```

結果：

```text
CROSS
```

`cross_junction_pairs()` も一意な2組を返す。

---

## 45. ambiguous duplicate Cross-like junction

次：

```text
0 / 180 / 0 / 180
```

結果：

```text
FOUR_WAY
```

CROSSにしてはならない。

---

## 46. arbitrary four-way

例：

```text
0 / 180 / 45 / 90
```

結果：

```text
FOUR_WAY
```

---

## 47. three-way unsupported

反対方向ペアを持たない3本。

例：

```text
0 / 120 / 240
```

結果：

```text
THREE_WAY
```

各member：

```text
joint treatment = UNSUPPORTED
```

有効なsquare Meshを生成できる。

---

## 48. overlap unsupported

2本が同方向。

結果：

```text
OVERLAP
UNSUPPORTED
```

square profile。

---

## 49. multi unsupported

5本以上を同junctionへ接続。

結果：

```text
MULTI
UNSUPPORTED
```

全memberで有効なsquare Meshを生成できる。

---

## 50. continuation exact 180

2本：

```text
0 / 180
```

endpoint一致。

結果：

```text
CONTINUATION
```

---

## 51. continuation START / END mix

同じ直線を：

```text
START junction
END junction
```

混在させても有効。

member orderにも依存しない。

---

## 52. continuation 179.5°

classification toleranceにより：

```text
classification = CONTINUATION
```

でもeffective treatmentは：

```text
FALLBACK
```

とする。

---

## 53. continuation position mismatch

2本の接続topologyはあるが、
canonical endpointが `> 1e-6 m` 離れている。

結果：

```text
FALLBACK
```

---

## 54. continuation Object Transform

片方に非identity Object Transform。

effective treatment：

```text
FALLBACK
```

---

## 55. continuation unequal thickness

```text
130 / 200 mm
```

の一直線接続。

結果：

```text
CONTINUATION
```

有効Mesh。

---

## 56. INVALID

接続memberのdirectionを算出不能にする
zero-length等のpure/mock caseを作る。

classification：

```text
INVALID
```

effective treatment：

```text
FALLBACK
```

現在Wallのsquare profileが作れる場合は安全に返す。

---

## 57. supported T -> FOUR_WAY -> T transition

1. valid Tを作る
2. 非対向4本目を追加
3. FOUR_WAY / UNSUPPORTEDになる
4. 4本目をdetach
5. 元のTへ戻る

Tのprofileはcanonical dataから再導出されること。

---

## 58. supported Cross -> MULTI -> Cross transition

1. valid Cross
2. 5本目追加
3. MULTI / UNSUPPORTED
4. 5本目detach
5. Crossへ復帰

through / butt roleが元の方針で再導出されること。

---

## 59. FALLBACK regression

以下はUNSUPPORTEDへ変えてはならない。

```text
危険な2.5° T
危険な2.5° Cross
unsafe miter
unsafe oblique clipping
```

対応junctionのsolver failureなので：

```text
FALLBACK
```

を維持する。

---

## 60. Build 04-G regression

最低限以下を維持する。

```text
equal angled T
unequal orthogonal T
unequal oblique T
equal angled Cross
unequal orthogonal Cross
unequal oblique Cross
15° valid
2.5° fallback
START / END mix
member order independence
caller independence
far-end safety
```

---

# Part L — testing commands

## 61. compile

最低限：

```bash
python -m compileall japanese_house_modeler tests
```

PASS。

---

## 62. unittest

```bash
python -m unittest discover -s tests -v
```

全PASS。

---

## 63. diff check

```bash
git diff --check
```

PASS。

---

## 64. worktree report

Codexは最終報告時に以下を示す。

```text
git status --short
git diff --stat
python -m compileall japanese_house_modeler tests
python -m unittest discover -s tests -v
git diff --check
```

---

# Part M — Blender 5.2 LTS実機受入試験

## 65. テスト説明ルール

ユーザー向け実機テストを提示するときは、
各テストに必ず日本語で：

```text
何本の壁を作るか
どの方向へ作るか
どの壁厚にするか
何を追加・削除するか
画面のどこを確認するか
正常ならどう見えるか
```

を簡潔に書く。

`Continuation`, `Fallback`, `Through`, `Butt` 等の英語だけで説明しない。

必要なら括弧内に内部英語名を併記してよいが、
日本語説明を主とする。

---

## 66. 実機 Test 1 — 通常の直線接続

### 操作

横一直線に2本の壁を作る。

```text
左壁 → ● → 右壁
```

両壁130 mm。

### 確認

UI：

```text
形状：直線継続
接合：直線
```

接続面に不自然な隙間や突起がない。

---

## 67. 実機 Test 2 — 異厚の直線接続

### 操作

横一直線に：

```text
130 mm ──●── 200 mm
```

と作る。

### 確認

接合は直線として成立する。

厚さの変化は接続位置で段差になるが、
中心線位置は一致する。

---

## 68. 実機 Test 3 — 同方向重複

### 操作

同じjunctionから同じ方向へ2本を伸ばす。

### 確認

```text
形状：同方向重複
接合：未対応
```

となる。

再生成しても壊れたMeshを作らない。

---

## 69. 実機 Test 4 — 3方向接続

### 操作

同一点から、
一直線の対向ペアを作らない3方向へ壁を出す。

作図補助で作りやすい角度を使ってよい。

### 確認

```text
形状：3方向接続
接合：未対応
```

各壁端は安全な四角い端部になる。

---

## 70. 実機 Test 5 — 非十字4方向接続

### 操作

まず正常なT字を作る。

そこへ、
既存3本のどれとも正確な反対方向にならない4本目を追加する。

### 確認

```text
形状：4方向接続
接合：未対応
```

になる。

元のT枝壁の切り欠きは再生成後に消え、
安全な端部へ戻る。

---

## 71. 実機 Test 6 — 4本目を外してTへ復帰

### 操作

Test 5の4本目を削除または接続解除し、
「接合を再生成」を行う。

### 確認

残った3本が再びT字として認識される。

枝壁の切り欠きが正常に復元される。

---

## 72. 実機 Test 7 — 通常Cross回帰

### 操作

横2本 + 縦2本で通常十字を作る。

### 確認

```text
十字通し壁 ×2
十字突合せ壁 ×2
```

従来どおり。

---

## 73. 実機 Test 8 — 異厚斜めCross回帰

### 操作

Build 04-Gで確認済みの：

```text
横通し壁 130 / 200
斜め突合せ壁 45° / 225°
```

を作る。

### 確認

正常な異厚斜め十字接合を維持。

---

## 74. 実機 Test 9 — Crossへ5本目追加

### 操作

正常Crossのjunctionへ5本目を追加する。

### 確認

```text
形状：多方向接続 (5)
接合：未対応
```

全体が安全な端部へ戻る。

---

## 75. 実機 Test 10 — 5本目を外してCross復帰

### 操作

Test 9の5本目を外し、
「接合を再生成」。

### 確認

元のCross形状へ正常復帰。

---

## 76. 実機 Test 11 — standard Delete repair regression

### 操作

TまたはCrossから1本をBlender標準Deleteする。

その直後の古い切り欠きが残ること自体は許容。

次に「接合を再生成」。

### 確認

現在残っているWall構成に合う形へ修復される。

---

## 77. 実機 Test 12 — Undo / Redo

### 操作

未対応4方向または5方向を作る操作について：

```text
Ctrl+Z
Ctrl+Shift+Z
```

を行う。

必要に応じて再生成。

### 確認

分類・接合形状が現在topologyに対応する。

---

## 78. 実機 Test 13 — Save / Reopen

### 操作

T / Cross / 未対応4方向を含むsceneを保存し、
Blenderを終了して再度開く。

### 確認

classification用canonical dataとConnection topologyが維持される。

---

## 79. 実機 Test 14 — Rebuild after reopen

### 操作

Test 13の再読込後、
「接合を再生成」。

### 確認

対応junctionは同じ形状を再現し、
未対応junctionは安全なsquare端部になる。

---

## 80. 実機 Test 15 — Material / shading

### 操作

異なるMaterialを複数Wallへ付け、
斜め視点・Material Preview等で確認。

### 確認

以下がない。

```text
黒い面
反転面
巨大な飛び出し
穴
不自然なgap
spike
detached sliver
```

Material slotも保持する。

---


## 80-A. 実機 Test 16 — 45°Wallの延長ガイド

### 操作

既存Wallを45°で1本作る。

そのWallの端点を越えた先へcursorを移動する。

### 確認

cursorが中心線延長の近くに来ると、
既存Wallの中心線方向へ延長ガイドが表示される。

クリックした始点が、
既存Wallのcanonical centerlineと正確に一直線になる。

---

## 80-B. 実機 Test 17 — 45°Wallを逆向きにjunctionへ作図

### 操作

既存45°Wall Aを：

```text
junction ●
          ＼
           ＼ A
```

のように作る。

次にAのjunction反対側の延長線上で
新Wallの始点をクリックする。

その後、終点を既存junctionへsnapする。

```text
新Wall
     ＼
      ＼
       ● junction
        ＼
         ＼ A
```

### 確認

新WallとAが
正確な反対方向ペアになる。

45° / 225°のような関係を
目測ではなく延長ガイドで作れる。

junction classificationが
作図順やSTART/END方向の違いで崩れない。

---

## 80-C. 実機 Test 18 — 15°Wallの延長ガイド

### 操作

Shift 15°補助等で15°Wallを作る。

そのWallの反対延長側から、
ガイドを使ってjunctionへ向かうWallを作る。

### 確認

15° / 195°相当の
正確な反対方向ペアになる。

---

## 80-D. 実機 Test 19 — Wall途中は延長snapしない

### 操作

既存Wallの中心部分付近へcursorを動かす。

### 確認

中心線に近くても、
既存segment内部では「延長線ガイド」として吸着しない。

この操作だけでWall途中Connectionを作らない。

---

## 80-E. 実機 Test 20 — endpoint snap優先

### 操作

既存Wall endpointの近くへcursorを移動する。

同じ場所が延長線上でもある状態を作る。

### 確認

既存endpoint snapのハイライトが優先される。

クリックすると従来どおりConnection topologyが作られる。

---

## 80-F. 実機 Test 21 — X/Y・Shift補助回帰

### 操作

従来どおり：

- 水平/垂直のX/Y位置合わせ
- Shift 15°角度補助

で数本Wallを作る。

### 確認

Build 02-Dまでの作図補助挙動が壊れていない。

延長線alignmentを使わない通常作図で、
勝手に斜め既存Wallへ吸着しない。

---

# Part N — acceptance criteria

## 81. 必須条件

Build 04-Hを完了とする条件：

1. normal Cross classificationが維持される
2. ambiguous duplicate 4-memberをCROSSと誤判定しない
3. unsupported分類がsquare profile + UNSUPPORTEDで安定する
4. INVALIDがFALLBACKになる
5. CONTINUATIONに実Mesh安全条件が入る
6. 179.5°等を危険な直線接続として通さない
7. unequal-thickness exact continuationを壊さない
8. T/Cross/CORNERの既存solver priorityを変更しない
9. 04-Gまでの全unit testがPASS
10. 新規unit testがPASS
11. Blender 5.2 LTS実機試験がPASS
12. canonical source-of-truth原則を維持
13. Mesh逆算を導入しない
14. Build 05-AのWall途中接続実装を先取りしない
15. 既存斜めWallの延長線へ始点・終点を正確に位置合わせできる
16. 45°Wallの逆向き作図でSTART/END混在を実機確認できる
17. 15°Wallでも延長線補助が機能する
18. Wall segment内部を延長線snap対象にしない
19. endpoint snapが延長線alignmentより優先される
20. X/Y alignment・Shift 15°補助の既存挙動を維持する
21. 延長線alignmentだけではConnection topologyを作らない

---

# Part O — Codex implementation instructions

## 82. 作業方針

CodexはGitHub network操作を行わないこと。

この環境では以下は403になることがあるため実行不要。

```text
git fetch
git pull
git push
git ls-remote
```

現在workspaceにあるrepositoryを基準に、
ローカル実装・テストのみ行う。

---

## 83. 実装前

最初に以下を確認する。

```text
git status --short
git log -3 --oneline
```

基準commitがBuild 04-G相当であることを報告する。

GitHubへ接続しようとしない。

---

## 84. 実装時

仕様書を読み、
必要最小限の変更を行う。

特に：

- Build 04-Gのclipping engineを不要に触らない
- Wall data modelを変更しない
- Connection Property schemaを変更しない
- operator drawing systemは、本仕様の「中心線延長ガイド / 延長線alignment」に必要な範囲だけ変更する
- endpoint snap / X/Y alignment / Shift 15°補助の既存挙動を不要に書き換えない
- 新しいBoolean依存を追加しない
- unsupported geometryを無理に実装しない

---

## 85. 完了報告

Codexは最後に：

```text
変更ファイル
変更内容の要約
unit test結果
compile結果
git diff --check結果
git diff --stat
git status --short
```

を報告する。

ローカルcommitは作成してよい。

ただしpushしない。

ZIPは作成しない。

---

# Part P — Build 04-H完了後

Build 04-H実機試験・正式統合完了後は：

```text
Build 05-A
```

へ進む。

Build 05-Aの中心課題：

```text
既存Wallの途中へ新規Wallを接続
既存Wall同士の途中交差
必要に応じたcanonical Wall split
split後のConnection topology構築
split後のT/Cross再生成
```

Build 04-Hではここへ踏み込まない。
