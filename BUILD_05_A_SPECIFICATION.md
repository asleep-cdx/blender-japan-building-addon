# 日本住宅モデラー — Build 05-A Specification

## 1. 目的

Build 05-Aでは、Build 04-Hまでに完成したendpoint junctionシステムを維持したまま、
**既存Wallの途中へ新しいWallの始点または終点を接続できる作図機能**を追加する。

ユーザー操作としては、既存Wallの壁芯上の途中位置へカーソルを近づけてクリックすると、
その位置が接続候補として吸着し、新しいWallを確定した時点で既存Wallを必要に応じて2本へ自動分割する。

分割後は、Wall途中という特別な接続形式を永続保存しない。
既存のSTART / END endpoint topologyだけへ正規化し、
Build 04-C～04-Hで実装済みのjunction classificationとMesh solverをそのまま利用する。

Build 05-Aの主目的は次の4点である。

1. 新規Wallの始点・終点を既存Wallの途中へ正確にスナップできるようにする。
2. 接続確定時に既存Wallを安全かつ決定的に分割する。
3. 分割前に存在したendpoint connectionを失わず、新しいWallとのjunctionへ正しく再構成する。
4. 選択中Wallのトップビュー角度をUIへ読み取り専用で表示する。

Build 04-HまでのWall生成、endpoint snap、X/Y alignment、斜め中心線extension alignment、Shift 15°拘束、
Corner / T / Cross / unsupported junction、safe fallbackを壊してはならない。

---

## 2. 基準状態

Build 05-AはGitHub `main` の以下を基準とする。

```text
58bf8078e040410d0993df53d5305f870aaab4e8
Implement Build 04-H junction safety and drawing alignment
```

Build 04-Hは以下まで確認済みである。

```text
unit tests: 66 tests / OK
Blender 5.2 LTS 実機テスト: 21項目 PASS
```

Build 05-A実装開始時に、上記commit以外を暗黙の基準にしてはならない。

---

## 3. 現在の主要ファイル状態

Build 05-A開始時点の主要blob SHAは以下である。

```text
japanese_house_modeler/drawing_alignment.py
aa8388be1a951c58135b0eb4ec84f790dc3089b4

japanese_house_modeler/joints.py
b51ca82c1398edc147d9acd8d55b0b265774a432

japanese_house_modeler/junctions.py
9cf8b5b8deed601a5db3d8012ad7b7c16da9073f

japanese_house_modeler/operators.py
1f403f65a5c2b75b1eadb72614726173bc346c19

japanese_house_modeler/connections.py
3c8a3246001a72b7084a9ec0c7dd5dbc0ab227a0

japanese_house_modeler/properties.py
f99eca3d0b416e675141404b3161742b494d832f

japanese_house_modeler/ui.py
37e07890f2ae0360d73e68f85929c71b003a001a

tests/test_joints.py
ef5d9eff52ac444ce3a63fe388fa621408b66625
```

このspecificationでは、Build 05-Aに必要な範囲だけを変更する。

---

## 4. Build 05-Bまでの開発順

```text
Build 05-A
既存Wall途中への接続
+ 必要なWall自動分割
+ split topology migration
+ 選択Wall角度表示

Build 05-B
Wall System全体の仕上げ
安定化
UX整理
既知の制約整理
回帰テスト
```

Build 05-B完了時点でWall System開発をいったん停止し、
次にfloor / ceiling / opening / door / window等のどれへ進むかを改めて決定する。

---

# Part A — Build 05-Aの範囲

## 5. 今回実装する内容

Build 05-Aでは以下を実装する。

- 新規Wall作図時の既存Wall segment interior snap
- 始点クリック時のmid-segment snap
- 終点クリック時のmid-segment snap
- endpoint snapをmid-segment snapより優先
- mid-segment snapをX/Y alignment・extension alignmentより優先
- mid-segment snapをShift 15°拘束より優先
- managed Wallのcanonical centerlineだけを使用する途中スナップ
- visible Wallだけを途中スナップ候補にする
- identity Object TransformのWallだけを途中スナップ候補にする
- segment interiorだけを途中スナップ候補にする
- endpoint境界を途中スナップ候補から除外する
- 同距離で曖昧な複数Wall候補を勝手に選ばない
- 新規Wall確定時の既存Wall自動分割
- 元Wall ObjectをSTART側segmentとして維持
- 新規split WallをEND側segmentとして生成
- thickness / heightの継承
- material slotの継承
- collection membershipの継承
- 元Wall START側の既存connection維持
- 元Wall END側の既存connectionをsplit後END側Wallへ移送
- split pointでの新しいendpoint junction構築
- 新規Wall endpointをsplit junctionへ接続
- 1つの新規Wallの両端が異なる2本の既存Wall途中へ接続するケース
- split対象Wallの既存endpoint junction回帰
- split後のaffected Walls一括再生成
- 失敗時のatomic rollback
- 1回のCtrl+Zで作図前へ戻るUndo回帰
- 選択中Wallのトップビュー角度表示
- Build 04-Hまでの全unit test回帰
- Build 05-A unit tests
- Blender 5.2 LTS実機テスト

---

## 6. 今回実装しない内容

以下はBuild 05-Aでは実装しない。

- 既存Wall同士が単に交差しているだけでの自動intersection detection
- 新規Wallが既存Wallを途中で横切っただけでの自動分割
- 新規Wallの線分内部と既存Wallの線分内部が交差した場合の自動Cross生成
- `始点を移動` / `終点を移動` operatorでのmid-segment snap
- Blender標準Delete監視
- Wall削除後の自動junction再生成
- arbitrary angle numeric input
- wall angle数値編集
- wall rotation operator
- 同方向重複Wallの自動統合
- 重複Wallの自動削除
- 同一Wall上の2点を結ぶ新Wall作成
- 同一Wall endpointと同一Wall interiorを結ぶ新Wall作成
- ambiguous overlap候補をObject名や作成順で自動選択
- midpointへ永続的な特殊connection typeを保存
- junction classificationの永続保存
- split historyの永続保存
- parent/child Wall relationの永続保存
- object UUID追加
- Blender Boolean
- BMesh boolean
- Mesh Edit Modeからcanonical dataへの逆同期
- Object Transformの自動Apply
- modifier / constraintのsplit複製
- openings
- doors
- windows
- floor
- ceiling
- manufacturer asset placement

これらはBuild 05-Bまたはそれ以降で必要性を再検討する。

---

# Part B — Wall System invariants

## 7. canonical Wall data

唯一のsource of truthは引き続き以下である。

```text
jhm_wall.start
jhm_wall.end
jhm_wall.wall_thickness
jhm_wall.wall_height
endpoint Connection topology
```

Meshは派生結果である。

Wall split後もこの原則を変更しない。

---

## 8. Wallの途中という永続connectionを作らない

Build 05-Aで最も重要な設計原則である。

途中接続を以下のようなデータとして保存してはならない。

```text
Wall A の parameter = 0.42 に Wall B が接続
```

また、以下のようなPropertyも追加してはならない。

```text
midpoint_connections
split_parameter
parent_wall
child_wall
split_id
```

Wall途中へ接続する操作が確定したら、対象Wallそのものを分割し、
接続点を通常のSTART / ENDへ変換する。

最終状態は必ず既存endpoint topologyだけで表現できなければならない。

---

## 9. Lengthを永続保存しない

Build 05-AでもWall length propertyを追加しない。

長さは常に、

```text
distance(jhm_wall.start, jhm_wall.end)
```

から導出する。

分割後の各segmentも同様である。

---

## 10. Mesh逆算禁止

途中スナップ・分割・角度表示で既存Mesh vertexをsource of truthにしてはならない。

禁止例:

- Mesh bboxからcenterlineを推定
- Mesh edgeからsplit位置を推定
- Mesh回転角からWall angleを求める
- 見た目のObject Transform後位置からcanonical endpointを逆算

使用するのは必ず保存済みcanonical dataである。

---

## 11. Object Transform

Build 04-Hと同様、managed WallにidentityでないObject Transformが存在する場合、
canonical dataと見た目が一致しない可能性がある。

そのため、以下のWallはmid-segment snap対象外とする。

```text
Location != identity
Rotation != identity
Scale != identity
その他 matrix_basis が identity でない
```

Build 05-Aでは自動Applyしない。

mid-segment snap候補から静かに除外する。

既存のendpoint snap / X-Y alignmentについてはBuild 05-Aの主目的ではないため、
既存挙動を不要に変更しない。

Object Transform Wall全般の作図補助統一はBuild 05-BのUX整理候補とする。

---

# Part C — 選択Wall角度表示

## 12. UIへ壁角度を追加する

選択中のmanaged Wallに対して、`日本住宅` N-panelの
`選択中の壁` boxへ読み取り専用の角度表示を追加する。

表示例:

```text
選択中の壁
壁厚: 130.0 mm
壁高さ: 2500.0 mm
壁角度: 45.0°
```

壁角度は編集Fieldではなくlabelとする。

---

## 13. 角度の定義

角度はトップビュー、すなわちworld XY平面上のWall centerline角度とする。

入力:

```text
start = jhm_wall.start
end   = jhm_wall.end
```

概念計算:

```python
dx = end.x - start.x
dy = end.y - start.y
angle = degrees(atan2(dy, dx)) % 180.0
```

表示範囲は必ず、

```text
0.0° <= angle < 180.0°
```

とする。

---

## 14. 描画方向に依存させない

START→ENDを逆向きに作図しても表示角度は同じでなければならない。

例:

```text
(0,0) -> (2,0)      = 0.0°
(2,0) -> (0,0)      = 0.0°

(0,0) -> (2,2)      = 45.0°
(2,2) -> (0,0)      = 45.0°

(0,0) -> (0,2)      = 90.0°
(0,2) -> (0,0)      = 90.0°

(0,0) -> (-2,2)     = 135.0°
(-2,2) -> (0,0)     = 135.0°
```

---

## 15. 角度表示精度

UIでは1桁小数表示を基本とする。

```text
壁角度: 0.0°
壁角度: 15.0°
壁角度: 45.0°
壁角度: 89.7°
壁角度: 135.0°
```

角度そのものを丸めてcanonical dataへ書き戻してはならない。

UI表示だけをformatする。

---

## 16. 角度算出不能

以下の場合、angle helperは`None`等のinvalid resultを返す。

- start/endにNaNまたはInf
- start=end
- canonical lengthがgeometry minimum以下
- malformed data

UIでは例として、

```text
壁角度: 判定不能
```

と表示する。

例外をUI drawへ伝播させてはならない。

---

## 17. angle helper

角度計算はBlender UI codeへ直接ベタ書きせず、pure helperとして実装することを推奨する。

推奨配置:

```text
japanese_house_modeler/drawing_alignment.py
```

推奨関数名例:

```python
wall_axis_angle_degrees(start, end)
```

unit test可能なpure Python helperとする。

---

# Part D — Wall途中スナップの幾何

## 18. canonical segment projection

Wall途中候補は、raw cursor world XY pointを既存Wall canonical segmentへ射影して求める。

既存Wall:

```text
S = start
E = end
```

axis:

```text
D = E - S
L = |D|
axis = D / L
```

raw cursor:

```text
P
```

line parameter:

```text
s = dot(P - S, axis)
```

projected point:

```text
Q = S + axis * s
```

ただしBuild 05-Aのmid-segment候補として有効なのは、
Qがcanonical segmentの**厳密なinterior**にある場合だけである。

---

## 19. endpoint境界をsegment snapへ含めない

endpoint付近は既存endpoint snapへ任せる。

mid-segment snap helperは少なくとも以下を除外する。

```text
s <= boundary epsilon
s >= L - boundary epsilon
```

endpointとmidpointを同じ候補系へ混ぜない。

目的:

- endpoint snap priorityを明確にする
- split直後に極端に短いWallを作らない
- endpoint位置を誤ってsplitしない
- UI highlightの意味を一意にする

---

## 20. segment projection pure helper

`drawing_alignment.py`へpure helperを追加する。

推奨interface例:

```python
SegmentProjection = namedtuple(
    "SegmentProjection",
    ("point", "parameter", "length", "axis")
)

project_to_wall_segment(raw_point, start, end)
```

返却する`parameter`はmeter単位のcenterline距離でも、0..1 normalized parameterでもよい。

ただし実装内で単位を混在させない。

推奨は既存extension helperと整合するmeter距離parameterである。

---

## 21. segment helperのinvalid条件

以下は`None`とする。

- malformed input
- NaN / Inf
- zero length Wall
- length <= `_MIN_WALL_LENGTH_M`
- projectionがSTART境界上
- projectionがEND境界上
- projectionがsegment外

raw pointがsegmentから離れているかどうかはpure helperでは判定してもよいが、
Viewport screen-space thresholdはoperator側で判定する。

---

## 22. screen-space snap threshold

Build 05-Aでは以下を基本値とする。

```text
endpoint snap       = 16 px  （既存）
mid-segment snap    = 12 px  （新規）
alignment           = 10 px  （既存）
```

推奨定数:

```python
_SEGMENT_SNAP_DISTANCE_PX = 12.0
```

mid-segment snapはendpointより少し狭くし、
endpoint近傍では既存endpoint snapを取りやすくする。

---

## 23. mid-segment候補Wall

候補Wallは以下すべてを満たさなければならない。

- `jhm_wall.is_wall == True`
- live managed Wall
- current View Layerに存在
- current Viewportでvisible
- canonical start/endがfinite
- canonical lengthが有効
- identity Object Transform
- operatorが明示的に除外すべきWallではない

新規Wall作成operatorではまだ作成中Wall Objectは存在しないためself-candidateは通常発生しない。

move endpoint operatorへこの機能を流用しないこと。

---

## 24. snap優先順位

新規Wall作図時の位置決定優先順位は以下とする。

```text
1. endpoint snap
2. mid-segment snap
3. free alignment
   - extension alignment
   - X/Y alignment
4. raw point
```

Shiftが押されている場合でも、
**実在するendpoint / segment接続候補を幾何snapとして優先**する。

すなわち:

```text
endpoint snap > segment snap > Shift 15° constraint
```

とする。

理由:

ユーザーが既存Wallへ明示的に接続しようとしている場合、
接続点の方が角度丸めより強いintentだからである。

---

## 25. extension alignmentとの関係

Build 04-Hのextension alignmentは既存Wall segmentの外側だけを対象としている。

Build 05-A後は役割が明確に分かれる。

```text
segment interior  -> mid-segment snap
segment endpoint  -> endpoint snap
segment exterior  -> extension alignment
```

同一Wall centerline上でも位置によって意味を混在させない。

---

## 26. X/Y alignmentとの関係

mid-segment snap候補がscreen threshold内に存在する場合、
X/Y alignmentよりmid-segment snapを優先する。

mid-segment snapが存在しない場合のみ、Build 04-Hのfree alignment選択へ進む。

既存のextension vs X/Y distance比較ロジックは変更しない。

---

## 27. 候補選択の決定性

候補探索順、Object名、Object作成順によって結果が変わってはならない。

mid-segment候補を複数得た場合、まずscreen-space distance最小を選ぶ。

ただし、最良候補と次点候補が実質的に同距離の場合は曖昧候補として扱う。

推奨tie epsilon:

```text
1e-6 px程度
```

exact値は実装で定数化してよい。

---

## 28. 曖昧なcandidateは自動選択しない

以下のようなケース:

```text
Wall A ─────────────
Wall B ─────────────
完全に同位置で重複
```

raw cursorからWall A / Wall Bへのprojected pointもscreen distanceも同じになる。

この場合、

```text
Wall AをObject名が小さいから選ぶ
先に作ったWallを選ぶ
collection iteration順で選ぶ
```

などをしてはならない。

mid-segment snapを成立させず、
通常alignment / raw candidateへフォールバックする。

将来必要ならBuild 05-B以降で明示選択UIを検討する。

---

## 29. 異なるprojected pointの同距離tie

異なる2本のWallから異なるprojected pointが得られ、
screen distanceがtie epsilon内で同じ場合も自動選択しない。

理由:

どちらへ接続するかはユーザーintentを推測できないためである。

---

## 30. segment snap transient state

operator内部では、少なくとも以下と同等のtransient stateが必要になる。

```text
current segment candidate point
current segment target object
current segment parameter / projection
start-side segment target object
start-side segment projection
end-side segment target object
end-side segment projection
```

命名は実装へ任せる。

ただしpersistent Propertyへ保存してはならない。

operator終了時に消えるtransient stateとする。

---

## 31. endpoint snap成立時のstate clear

endpoint snapが成立した場合、
そのクリック側のmid-segment candidate/targetは必ずclearする。

mid-segment snap成立時はendpoint snap targetをclearする。

同じclickがendpointとmidpoint両方として処理されてはならない。

---

# Part E — Viewport表示

## 32. mid-segment snap highlight

mid-segment snap候補がある場合、
projected pointに既存のsnap highlightと視覚的に整合する青いmarkerを表示する。

最低要件:

- projected candidate位置が目視できる
- endpoint snapと同様に「ここへ接続される」と認識できる
- markerはcanonical centerline上に表示される

Build 05-Aでは新しい色体系を導入しなくてよい。

---

## 33. endpoint snapとの見分け

endpoint snapは既存endpoint上へmarkerが出る。

mid-segment snapはWallの途中へmarkerが出る。

この位置差で十分区別できるため、Build 05-Aでは必須の専用iconやtext overlayを要求しない。

ただし実装が小さく安全なら、midpoint markerに小さなcross等を追加してもよい。

機能要件ではない。

---

## 34. split previewを作らない

2回目clickでWallを確定する前に、
既存Wallを実際に2分割したpreview Objectへ置換してはならない。

作図中はcandidate markerのみ表示する。

既存Wall Mesh / topology / canonical dataは変更しない。

---

# Part F — 分割のcanonical semantics

## 35. split対象

既存Wall A:

```text
A.START ---------------- A.END
```

interior point Pで分割する。

Build 05-Aでは、元Object AをSTART側segmentとして残す。

```text
A.START -------- P
```

新しいWall Object BをEND側segmentとして作る。

```text
P -------- A旧END
```

---

## 36. split後のcanonical data

分割前:

```text
A.start = S
A.end   = E
```

分割点:

```text
P
```

分割後:

```text
A.start = S
A.end   = P

B.start = P
B.end   = E
```

Aは既存Object identityを保持する。

Bは新しいmanaged Wall Objectである。

---

## 37. 元ObjectをSTART側に残す理由

分割方向を毎回固定し、
Object identityの意味を決定的にするためである。

禁止:

```text
cursor位置によって元Object側が変わる
Wall方向によって元Object側が変わる
screen orientationで元Object側が変わる
```

常にcanonical START側が元Objectである。

---

## 38. thickness / height継承

BはA分割前の以下を継承する。

```text
wall_thickness
wall_height
is_wall = True
```

分割によって寸法を変えてはならない。

---

## 39. material継承

split後BのMesh material slotsは、
分割前AのMesh material slotsと同じ順序・参照を維持する。

material datablockをduplicateする必要はない。

slot referenceを継承する。

A側もmaterialを失わない。

---

## 40. collection membership継承

Bは分割前Aが所属していたcollectionへlinkする。

Aが複数collectionへ所属している場合は、可能な限り同じcollection membershipを維持する。

current active collectionだけへ勝手に移さない。

最低でも、元Wallが見えなくなるcollection移動を起こしてはならない。

---

## 41. Object Transform

split対象Aはidentity Object Transformでなければならない。

Bもidentity transformで生成する。

canonical coordinatesはworld-space meterのため、
Object Transformで位置合わせしない。

---

## 42. object naming

Wall Object名はcanonical identityとして扱わない。

新規split Wallの名前はBlenderの通常unique namingに任せてよい。

例:

```text
Wall
Wall.001
Wall.002
```

名前をtie-breakやtopology keyに使ってはならない。

---

## 43. arbitrary custom properties

Build 05-Aでは、managed Wallのcanonical dataとして定義されていない任意custom property、modifier、constraint等の完全複製を保証しない。

ただし既存A Object自体はSTART側に残るため、
Aに付いていたObject-level metadataはSTART側へ残る。

END側Bへ何を継承するかはBuild 05-Aのcanonical Wall field、material、collectionまでを必須とする。

将来manufacturer/opening metadataを導入するときはsplit semanticsを再拡張する。

---

# Part G — topology migration

## 44. 分割前START connection

A.STARTに存在した既存connectionはA.STARTへそのまま残す。

例:

```text
X ● A.START ---------------- A.END
```

Pで分割後:

```text
X ● A.START ------ A.END(P)
```

Xとのconnectionを変更しない。

---

## 45. 分割前END connection

A.ENDに存在した既存connectionは、
新規split Wall B.ENDへ移送する。

分割前:

```text
A.START ---------------- A.END ● Junction J
```

分割後:

```text
A.START ------ A.END(P)
               \
                split junction

B.START(P) ------ B.END ● Junction J
```

旧A.ENDがJへ残ってはならない。

Jの他member側から見ても接続先がA.ENDではなくB.ENDへ更新されなければならない。

---

## 46. reciprocal topologyを維持する

connection graphはreciprocalである。

endpoint transfer時に片方向だけ書き換えてはならない。

推奨helper:

```python
transfer_endpoint_connections(
    source_object,
    source_endpoint,
    destination_object,
    destination_endpoint,
)
```

役割:

1. source endpointのvalid targetsをsnapshot
2. source-target reciprocal edgeを除去
3. destination-target reciprocal edgeを追加
4. duplicateを作らない
5. peer-peer既存edgeを壊さない

このhelperは`connections.py`へ置くのが自然である。

---

## 47. complete junction graphを維持する

既存`attach_to_junction()`はjunction member全体をcomplete reciprocal graphへする。

split point Pでは、最低限以下が同一junctionになる。

新規WallのENDがhost途中へ接続する例:

```text
A.END
B.START
NewWall.END
```

各endpointから見て他2memberへ接続している必要がある。

つまり各endpointのvalid connection countは2になる。

---

## 48. splitだけでもA/Bは接続する

split pointではA.ENDとB.STARTは必ず同一junctionにする。

新規branchを追加する場合は、その同じjunctionへbranch endpointを追加する。

結果として3-member Tになる。

---

## 49. 既存END junction transfer例

分割前A.ENDがC.START / D.STARTと3-member junctionを構成していたとする。

```text
A.END
C.START
D.START
```

Aを途中Pで分割した後、古いjunctionは、

```text
B.END
C.START
D.START
```

でなければならない。

A.ENDはPの新しいsplit junctionへ移動する。

```text
A.END(P)
B.START(P)
NewWall endpoint(P)
```

古いjunctionと新しいjunctionを混同しない。

---

## 50. topology transfer順序

推奨mutation順序:

1. 分割前A.ENDのtargetsを取得
2. Bを作成しcanonical data設定
3. A.END old connectionsをB.ENDへtransfer
4. A.endをPへ変更
5. A.ENDとB.STARTをnew split junctionとして接続
6. 新規Wall endpointをsplit junctionへattach
7. affected Walls再生成

ただしtransaction全体でatomicityを守れるなら、細部の順序は変更してよい。

---

# Part H — 新規Wall作成との統合

## 51. 始点mid-snap

ユーザーが1回目clickで既存Wall途中を選択した場合、
その時点では既存Wallを分割しない。

保存するのはtransient target情報のみ。

例:

```text
_start_point = projected point
_start_segment_target_object = host Wall
_start_segment_projection = projection data
```

実際のフィールド名は任意。

---

## 52. 終点mid-snap

2回目click前のMOUSEMOVEでは、
mid-segment candidateをpreview表示するだけである。

2回目clickで確定候補として採用された場合、
end-side target情報をfinal transactionへ渡す。

---

## 53. 1回目click後キャンセル

1回目clickがmid-segment snapだった後に、

```text
ESC
Right Mouse
```

でキャンセルした場合、既存Wallは完全に未変更でなければならない。

変更禁止:

- canonical start/end
- connection topology
- Mesh
- Object count
- material
- selection以外のpersistent state

---

## 54. 2回目click前までmutation禁止

midpoint候補をhoverしているだけでWallをsplitしてはならない。

1回目clickだけでもsplitしてはならない。

新規Wallがfinalize可能になり、2回目clickで確定した時点だけmutationを開始する。

---

## 55. finalize前validation

mutation開始前に、全対象を再検証する。

最低限:

- target Wallがまだlive
- managed Wall
- visibleである必要はfinalize時には必須ではないが、target identityが変わっていない
- Object Transform identity
- canonical start/endがcandidate取得時から安全に使用できる
- split pointがsegment interior
- split後両segmentがgeometry minimumより長い
- same-host forbidden ruleに違反しない
- new Wall lengthがvalid
- second targetもvalid

可能ならcandidate取得時のcanonical start/endとfinalize時start/endが一致していることを検証する。

modal中に別操作で対象が変化した場合は安全にcancelする。

---

## 56. 新規Wallの両端が異なるhost途中

正式対応する。

例:

```text
Host A                 Host B
──────────●       ●──────────
          \       /
           \ New /
```

実際には新規Wallは直線1本である。

startがHost A interior、endがHost B interiorなら、

- Host Aをsplit
- Host Bをsplit
- NewWall.STARTをHost A split junctionへattach
- NewWall.ENDをHost B split junctionへattach

する。

Host AとHost Bは異なるObjectでなければならない。

---

## 57. endpoint + midpoint混在

以下を正式対応する。

```text
NewWall.START -> existing endpoint snap
NewWall.END   -> another Wall mid-segment snap
```

逆も同様。

endpoint側は既存Build 04-Hまでの処理を維持し、
midpoint側だけsplit transactionを行う。

---

## 58. same host forbidden rule

新規Wallの両端が同じ既存Wallに依存するケースはBuild 05-Aでは拒否する。

対象:

```text
same Wall midpoint -> same Wall midpoint
same Wall endpoint -> same Wall midpoint
same Wall midpoint -> same Wall endpoint
```

理由:

2点とも同一直線上にあるため、新規Wallがhost Wallと重複するsegmentになりやすく、
分割・重複・topology意味が複雑になる。

Build 05-Aでは明示的に拒否して安全性を優先する。

警告文例:

```text
同じWall上の2点を結ぶ壁は作成できません。
```

拒否時は既存Wallを一切変更しない。

---

## 59. endpoint junction内の別memberとmidpoint target

新規Wallの一方がjunction endpointへsnapし、
もう一方がそのjunction memberとは別Objectのinteriorへsnapする場合は、
Object identityが異なれば原則許可する。

ただしnew Wall lengthがzeroまたはほぼzeroになる場合は通常のlength validationで拒否する。

---

# Part I — split geometry / Mesh再生成

## 60. 新しいjoint solverは作らない

split pointでT字ができた場合、
Build 04-D / 04-F / 04-Gの既存T solverを使う。

split後にCross等の既存classificationが成立する場合も既存solverを使う。

Build 05-A専用のT Mesh形状ロジックを追加しない。

---

## 61. split segmentは通常Wallとして再生成する

A/Bとも通常のmanaged Wallである。

```text
canonical data + topology -> build_wall_geometry()
```

でMeshを生成する。

split専用Mesh形式を作らない。

---

## 62. affected Walls

final transactionでは以下を再生成対象へ含める。

- 新規NewWall
- split original A
- split successor B
- split point junctionのmembers
- Aの旧START側junction membersで必要なもの
- A旧ENDからB.ENDへtransferされたjunction members
- 2つ目hostがある場合その同等group

単純に「新しい3本だけ」をregenして旧junction peerを取りこぼしてはならない。

既存`affected_walls()` / `merge_affected()`を利用・拡張してよい。

---

## 63. atomic Mesh regeneration

`regenerate_wall_meshes()`のall-or-nothing性を維持する。

split途中で一部Wallだけ新Meshになり、他が旧Meshのまま残る状態をcommitしてはならない。

---

# Part J — transaction / rollback

## 64. transaction原則

2回目clickでmutationを始めた後の処理は、ユーザー視点で1transactionである。

成功時:

```text
new Wall created
host(s) split
connections migrated
junctions rebuilt
meshes regenerated
selection set to new Wall
```

失敗時:

```text
作図前状態へ戻す
```

中間状態を残してはならない。

---

## 65. transaction開始前snapshot

少なくとも以下をsnapshotする。

- global valid connection topology
- split対象Wallのcanonical start/end
- split対象Wall thickness/height
- split対象Wall material referencesが必要ならその情報
- split対象Wall collection membershipが必要ならその情報

新規作成Objectはlistで追跡し、rollback時に削除する。

---

## 66. topology snapshot

既存`connections.snapshot_topology()`を利用できる。

rollbackでは`restore_topology(snapshot)`を使用し、
新規split Wall / NewWallを削除する前後の順序でdangling pointerを残さないよう注意する。

---

## 67. canonical rollback

元Wall Aの`end`をPへ変更した後に失敗した場合、
必ず旧Eへ戻す。

2host splitなら両方戻す。

thickness / heightは通常変更しないが、snapshotした場合は同様に戻す。

---

## 68. Mesh rollback

`regenerate_wall_meshes()`は自身のswap失敗をrollbackする既存設計を維持する。

split transaction全体が失敗した場合、
canonical data / topology / new Objectsを戻した上で、
元Meshがそのまま残っている状態を維持する。

もし実装上、元Meshを先に破棄する設計になる場合は不可。

---

## 69. 新規Object rollback

失敗時に以下を削除する。

- NewWall
- split successor Wall(s)
- それら専用に作成したMesh datablock

users == 0のMeshを残さない。

---

## 70. selection

成功後は従来どおり新規NewWallをactive / selectedにする。

split hostやsuccessorをactiveにしない。

失敗時のselection完全復元は必須ではないが、
可能なら操作前selectionを維持する。

canonical/topology safetyを優先する。

---

# Part K — Blender Undo

## 71. Ctrl+Zは1回

新規Wall作成operatorは引き続き`UNDO`対応する。

1回の作図で、

- NewWall作成
- host split
- successor作成
- topology migration
- Mesh regeneration

が行われても、Blenderユーザーからは1操作である。

Ctrl+Z 1回で作図前へ戻ることを実機確認する。

---

## 72. Undo後の期待状態

Undo後:

- NewWallが存在しない
- split successorが存在しない
- original hostが分割前start/endへ戻る
- original host Meshが分割前へ戻る
- old endpoint connectionsが元通り
- object countが作図前へ戻る
- junction classification / effective jointが作図前へ戻る

---

# Part L — 既存接合との共存

## 73. host START側にjunctionがあるケース

A.STARTがCorner / T / Cross / Continuation等へ接続済みでも、
A interior splitによりそのjunctionを壊してはならない。

AはSTART側Objectとして残るため、原則そのconnectionはそのまま保持する。

split後regenして同じeffective jointへ戻ること。

---

## 74. host END側にjunctionがあるケース

A.ENDが既存junctionへ接続済みの場合、
B.ENDへtopologyをtransferする。

transfer後、旧junctionのclassificationとeffective Meshは、
Wall identityがAからBへ変わったこと以外、幾何学的に同等でなければならない。

---

## 75. old ENDがContinuation

分割前:

```text
A ----------------●---------------- C
```

Aをinterior Pでsplit:

```text
A ----- P ----- B ----------------●---------------- C
```

旧A.END-C junctionはB.END-C junctionへ移る。

UI / Meshは引き続き`直線継続 / 直線`であること。

---

## 76. old ENDがT

A.ENDがT main / T branchのmemberでも同様にtransferする。

分割後B.ENDがそのroleを再導出する。

role自体を保存・コピーしてはならない。

canonical data + topologyから再分類する。

---

## 77. old ENDがCross

Cross junction memberでもB.ENDへtransferする。

Build 04-E～04-Gのthrough / butt role policyを変更しない。

Wall object identityが変わったことでgeometry tie-breakが不安定になってはならない。

既存role policyはcanonical geometryから導出する。

---

## 78. old ENDがunsupported

FOUR_WAY / MULTI等のunsupported endpointもtransfer可能でなければならない。

splitにより旧junctionのmember countやclassificationを勝手に変えない。

B.ENDへ同じjunction member setを移す。

---

# Part M — mid-snap edge cases

## 79. 極端に短いsplit禁止

split point Pにより、

```text
|S-P| <= _MIN_WALL_LENGTH_M
```

または

```text
|P-E| <= _MIN_WALL_LENGTH_M
```

となる場合はsplitしない。

通常endpoint snapが先に成立するが、world-space safetyとして必須である。

---

## 80. projection pointのZ

Wall System centerlineはZ=0前提である。

mid-segment projected pointは、

```text
(x, y, 0.0)
```

とする。

existing Wall canonical Zがunexpectedな場合は、Build 05-Aでは安全に候補除外してよい。

---

## 81. hidden Wall

Viewportで非表示のWallはmid-segment candidateにしない。

ユーザーが見えていないWallへ勝手にsplit接続しない。

---

## 82. malformed Wall

invalid canonical dataのWallは候補から除外する。

operatorを落としてはならない。

---

## 83. multiple overlapping hosts

完全重複Wallでcandidate ambiguityが発生した場合はsnapしない。

クリックしてもsplit targetとして記録しない。

ユーザーが明確に1本を選べるUIは05-Aでは追加しない。

---

## 84. crossing hostsの交点

2本のWallが幾何学的に交差しているがtopology接続されていない場所で、
raw cursorが両Wallのcenterline交点に正確にある場合、
両hostへのmidpoint candidateが同距離になる。

Build 05-Aではambiguousとしてmid-snapしない。

どちらをsplitするか勝手に推測しない。

---

## 85. crossing hosts付近

交点から少しずれて、一方のWallへのscreen distanceが明確に小さい場合は、そのWallをcandidateにしてよい。

ただしprojected pointはcursor raw位置ではなく選ばれたWall centerline上のQである。

---

## 86. Wall interiorを単に横切る新規Wall

例:

```text
Existing  ─────────────
                |
                | NewWall
```

NewWallの始点/終点がExisting interiorへsnapしていない場合、
線分が途中で交差してもExistingをsplitしない。

automatic intersection detectionは05-A範囲外である。

---

## 87. NewWall両端がendpoint snap

mid-segment機能を使わない通常ケースはBuild 04-Hまでと同じである。

split Objectを作成してはならない。

---

# Part N — file architecture

## 88. 推奨変更ファイル

Build 05-Aの主な変更対象:

```text
japanese_house_modeler/drawing_alignment.py
japanese_house_modeler/connections.py
japanese_house_modeler/operators.py
japanese_house_modeler/ui.py
japanese_house_modeler/wall_split.py   # 新規推奨
```

必要に応じて:

```text
japanese_house_modeler/joints.py
```

ただし既存joint solverそのものを変更する必要がない限り、
`joints.py`の大規模変更は避ける。

`junctions.py`もclassification意味を変えない限り変更不要。

`properties.py`へ新しいpersistent split Propertyを追加しない。

---

## 89. `drawing_alignment.py`

責務:

- existing extension projectionを維持
- combined X/Y helperを維持
- geometry tie keyを維持
- mid-segment pure projection helper追加
- selected Wall angle pure helper追加
- 必要ならcandidate geometry key / ambiguity helper追加

Blender dependencyを持たないpure moduleであり続けること。

---

## 90. `connections.py`

責務:

- existing reciprocal connection helpers維持
- endpoint topology transfer helper追加
- duplicate / invalid connection safety維持
- junction complete graph semantics維持

Mesh操作を入れない。

---

## 91. `wall_split.py`

Build 05-Aでは新規moduleとして分離することを推奨する。

責務候補:

- split prevalidation
- original host canonical snapshot
- successor Wall作成
- canonical data分割
- material / collection継承
- old END topology transfer orchestration
- split junction作成
- rollbackに必要なsplit object tracking

`operators.py`へsplit詳細を大量に埋め込まない。

ただし実装が十分小さく明確なら別構成も許容する。

重要なのは責務分離である。

---

## 92. `operators.py`

責務:

- Viewport candidate探索
- endpoint / midpoint / alignment priority
- transient snap state
- draw preview / highlight
- finalize validation
- transaction orchestration
- NewWall作成
- split helper呼び出し
- affected regen
- error reporting

既存Build 04-H作図挙動を維持する。

---

## 93. `ui.py`

責務:

- selected Wall angle label追加
- invalid angleを安全表示

angle mathをUIへ直接複製しない。

---

## 94. `properties.py`

原則変更不要。

Build 05-Aで以下を追加してはならない。

```text
midpoint connection collection
split parent pointer
split parameter
angle property
cached length
cached classification
```

angleはderived read-only displayである。

---

# Part O — unit tests

## 95. 既存66 testsを全て維持

Build 05-A実装後も、Build 04-Hの66 testsがすべてPASSしなければならない。

既存test expectationをBuild 05-A都合で緩めてはならない。

---

## 96. segment projection tests

最低限以下をpure testする。

- horizontal interior projection
- vertical interior projection
- 15° interior projection
- 45° interior projection
- reversed start/endでも同じworld pointへproject
- START exact boundary -> None
- END exact boundary -> None
- segment outside before START -> None
- segment outside after END -> None
- zero length -> None
- NaN -> None
- Inf -> None

---

## 97. angle helper tests

最低限:

```text
0°
15°
45°
90°
135°
reverse 0°
reverse 45°
reverse 90°
reverse 135°
negative direction normalization
zero length invalid
NaN invalid
```

reverse directionで同じ角度になることを必ず検証する。

---

## 98. topology transfer tests

mock Wall topologyで最低限以下を検証する。

- source ENDにconnection 0件
- source ENDにconnection 1件
- source ENDにconnection 2件以上
- reciprocal peerがdestination ENDへ更新
- source ENDにold peerが残らない
- peer-peer connectionが壊れない
- duplicateを作らない
- invalid targetを安全にpurge

---

## 99. split canonical tests

最低限:

分割前:

```text
S=(0,0)
E=(10,0)
P=(4,0)
```

分割後:

```text
original.start = (0,0)
original.end   = (4,0)
new.start      = (4,0)
new.end        = (10,0)
```

を検証する。

15° / 45°でもworld coordinatesが正確であること。

---

## 100. same-host rejection tests

最低限:

- same host midpoint -> midpoint
- same host endpoint -> midpoint
- same host midpoint -> endpoint

をmutation前に拒否するlogicをtestする。

---

## 101. ambiguous candidate tests

候補選択をpure/mock化できるなら、

- identical overlapping Walls -> no selected mid target
- exact equal screen distance different projections -> no selected mid target
- one candidate strictly closer -> closer candidate

を検証する。

Object iteration順を変えても結果が同じであること。

---

## 102. transaction rollback tests

Blender APIを必要としない範囲でmock testを追加する。

最低限conceptとして、

- first host split成功
- second host splitでfailure
- transaction rollback
- first host canonical復元
- topology復元
- created successor list cleanup

を検証できる構造が望ましい。

完全mockが過剰ならBlender実機testで補完する。

---

# Part P — Blender 5.2 LTS 実機acceptance tests

以下はBuild 05-A完成時に実機で確認する。

各項目はユーザーが迷わないよう、日本語で具体的な作図手順を示す。

---

## 103. 実機テスト1 — 壁角度0°表示

### 作り方

1. 既存Wallを削除する。
2. 壁厚130 mmで水平Wallを左から右へ1本描く。
3. Wallを選択する。
4. 日本住宅パネルの`選択中の壁`を見る。

### 期待結果

```text
壁角度: 0.0°
```

が表示される。

壁厚・壁高さ・接合表示も従来どおり表示される。

---

## 104. 実機テスト2 — 45°と逆向き45°の角度表示

### 作り方

1. Shiftを使って45°Wallを1本描く。
2. 選択して`壁角度: 45.0°`を確認する。
3. 別の場所で、逆方向つまり225°方向へWallを描く。
4. そのWallを選択する。

### 期待結果

両方とも、

```text
壁角度: 45.0°
```

と表示される。

225.0°表示にはならない。

---

## 105. 実機テスト3 — 90° / 135°角度表示

### 作り方

1. Shiftで垂直90°Wallを描いて選択する。
2. 角度表示を確認する。
3. 別の場所で135°Wallを描いて選択する。

### 期待結果

```text
90° Wall  -> 壁角度: 90.0°
135° Wall -> 壁角度: 135.0°
```

となる。

---

## 106. 実機テスト4 — 新Wall終点を水平host途中へ接続

### 作り方

1. 水平な既存Wallを1本長めに描く。
2. `＋壁`を押す。
3. 既存Wallから離れた下側で新Wallの始点をクリックする。
4. 2回目のclick候補を既存水平Wallの中央付近へ近づける。
5. Wall中央の壁芯上に青いsnap markerが出ることを確認する。
6. その位置でclickして新Wallを確定する。

### 期待結果

- 既存Wallがclick位置で2本へ分割される。
- 新Wallの終点が分割点へ接続される。
- 3本でT字になる。
- 新Wall側は`T字枝壁`になる。
- host側2本は`T字主壁`になる。
- 不自然な隙間や重複Meshがない。

---

## 107. 実機テスト5 — 新Wall始点を水平host途中へ接続

### 作り方

1. 水平host Wallを1本描く。
2. `＋壁`を押す。
3. 1回目clickとしてhost Wall中央付近へカーソルを寄せる。
4. 中央の壁芯上にsnap markerが出た位置をclickする。
5. そこから上方向へ新Wallを描いて2回目clickする。

### 期待結果

- hostが2分割される。
- 新Wall.STARTがsplit junctionへ接続される。
- T字Meshが正常。
- 新Wall START側のconnection countは2。

---

## 108. 実機テスト6 — 45°host途中へ接続

### 作り方

1. Shiftで45°のhost Wallを1本長めに描く。
2. `＋壁`を押す。
3. hostとは離れた位置から新Wallを描き始める。
4. 2回目clickを45°hostの中央付近へ近づける。
5. centerline上へsnapした位置で確定する。

### 期待結果

- 45°hostがcanonical centerline上の位置で正確に2分割される。
- split後2本の`壁角度`は両方45.0°。
- 新Wallとのjunctionが既存solverで安全に処理される。

---

## 109. 実機テスト7 — host厚200 mmをsplitして寸法継承

### 作り方

1. 壁厚200 mmで水平hostを1本描く。
2. 新規壁の壁厚を130 mmへ戻す。
3. host途中へ130 mmのbranch Wallを接続する。
4. split後hostのSTART側segmentを選択する。
5. split後hostのEND側segmentも選択する。

### 期待結果

hostの両segmentが、

```text
壁厚: 200.0 mm
```

を維持する。

新Wallは130.0 mm。

高さも元hostの値を継承する。

---

## 110. 実機テスト8 — host旧ENDのContinuationを維持

### 作り方

1. 水平Wall Aを左から右へ描く。
2. AのENDへ水平Wall Cをさらに右へ端点snapしてつなぎ、一直線にする。
3. Aの中央へ新しいbranch Wallを途中接続する。
4. split後、右側に新しくできたhost segmentとCのjunctionを確認する。

### 期待結果

A旧END-Cの接続は失われない。

split後右側segmentとCが、

```text
形状: 直線継続
接合: 直線
```

として維持される。

---

## 111. 実機テスト9 — host旧START junctionを維持

### 作り方

1. A.START側を別WallとCornerまたはContinuationで接続しておく。
2. A中央へbranch Wallを途中接続する。
3. split後A.START側junctionを確認する。

### 期待結果

AはSTART側Objectとして残るため、旧START junctionがそのまま維持される。

接合形状がsquareへ戻ったりconnection countが減ったりしない。

---

## 112. 実機テスト10 — host旧ENDがT junction

### 作り方

1. 3本で通常のT字を作る。
2. T junctionへ入っているmain Wallのうち1本をhost Aとする。
3. AのT junctionではない側のinteriorへ別branch Wallを途中接続する。
4. Aがsplitされた後、元のT junction側を確認する。

### 期待結果

A旧END側のT topologyが新しいsuccessor Wall側へ移り、
元T junctionが正常なT字のまま維持される。

---

## 113. 実機テスト11 — 両端を異なる2本のWall途中へ接続

### 作り方

1. 離れた位置へ平行なhost Wall AとBを2本描く。
2. `＋壁`を押す。
3. 1回目clickでAの中央へmid-segment snapする。
4. 2回目clickでBの中央へmid-segment snapする。

### 期待結果

- Aが2分割
- Bが2分割
- NewWallがA/B間に作成
- NewWall.STARTはA split junction
- NewWall.ENDはB split junction
- 両端ともconnection count 2
- 両host側でT字が成立
- エラーなし

---

## 114. 実機テスト12 — endpoint + midpoint混在

### 作り方

1. host Aを1本描く。
2. 離れたhost Bを1本描く。
3. `＋壁`を押す。
4. 1回目clickをAの既存endpointへsnapする。
5. 2回目clickをBのinteriorへmid-snapする。

### 期待結果

- Aはsplitされない。
- A endpointは従来endpoint connectionとして接続。
- Bだけsplitされる。
- NewWall両端のtopologyが正常。

逆順でも同じ意味になる。

---

## 115. 実機テスト13 — 1回目midpoint click後にキャンセル

### 作り方

1. host Wallを1本描く。
2. hostのObject数と形を目視する。
3. `＋壁`を押す。
4. 1回目clickをhost中央へmid-snapする。
5. 2回目clickをせずESCする。

### 期待結果

- hostは分割されない。
- new split Wallは増えない。
- topologyは変わらない。
- Meshも変わらない。

---

## 116. 実機テスト14 — endpoint snap priority

### 作り方

1. host Wallを1本描く。
2. `＋壁`を押す。
3. host endpointのすぐ近くへカーソルを寄せる。
4. endpoint highlightが出た位置で接続する。

### 期待結果

- endpoint snapが優先される。
- hostはsplitされない。
- 余分なsplit successor Objectが増えない。
- 通常endpoint connectionになる。

---

## 117. 実機テスト15 — Shift中でもmidpoint接続

### 作り方

1. 斜めまたは水平hostを1本描く。
2. 新Wallの始点を離れた場所でclickする。
3. Shiftを押したまま2回目candidateをhost中央へ近づける。
4. mid-snap markerが出る位置で確定する。

### 期待結果

host interiorへの明示snapがShift 15°拘束より優先される。

NewWall endpointはhost centerline上に正確に置かれる。

---

## 118. 実機テスト16 — Object Transform hostを除外

### 作り方

1. host Wallを1本描く。
2. Object Modeで`S 1.5`等を実行しScaleを未Applyのままにする。
3. `＋壁`を押す。
4. hostの見た目の中央付近へカーソルを寄せる。

### 期待結果

- mid-segment snap markerが出ない。
- hostをsplit targetとして採用しない。
- エラーなし。

---

## 119. 実機テスト17 — 完全重複hostの曖昧candidate

### 作り方

1. 同じ始点・終点を持つWallを2本完全に重ねる。
2. `＋壁`を押す。
3. 重複区間中央へカーソルを寄せる。

### 期待結果

どちらのWallをsplitするか自動選択しない。

mid-segment snapとして確定しない。

Object作成順を変えても挙動が変わらない。

---

## 120. 実機テスト18 — 同じhost上の2点を結ぶ操作を拒否

### 作り方

1. 長いhost Wallを1本描く。
2. `＋壁`を押す。
3. 1回目clickをhostの左寄りinteriorへmid-snapする。
4. 2回目clickを同じhostの右寄りinteriorへmid-snapする。

### 期待結果

警告を出してNewWall作成を拒否する。

hostをsplitしない。

Object数・topology・Meshが作図前から変化しない。

---

## 121. 実機テスト19 — 幾何交差だけでは自動splitしない

### 作り方

1. 水平host Wallを1本描く。
2. hostより下で新Wallを描き始める。
3. 2回目clickをhostより上の位置に置き、NewWallがhostを途中で横切るようにする。
4. ただし2回目click自体はhost上へsnapさせない。

### 期待結果

- NewWallとhostのcenterlineは途中で交差して見える。
- hostはsplitされない。
- Connectionは作られない。
- automatic Crossにはならない。

これはBuild 05-Aの意図した制限である。

---

## 122. 実機テスト20 — Undo 1回で分割前へ戻る

### 作り方

1. host Wallを1本描く。
2. host中央へbranch Wallをmid-snap接続し、hostが2分割されたことを確認する。
3. `Ctrl + Z`を1回実行する。

### 期待結果

- branch NewWallが消える。
- split successor Wallが消える。
- original hostが分割前の1本へ戻る。
- old topologyへ戻る。
- 接合Meshも分割前へ戻る。

---

## 123. 実機テスト21 — split後Wallを再度split

### 作り方

1. 長いhostを中央付近で1回split接続する。
2. split後右側segmentのさらに中央へ、別のbranch Wallをmid-snap接続する。

### 期待結果

右側segmentだけがさらに2分割される。

すべて通常managed Wallとして動作し、
初回split junctionも壊れない。

---

# Part Q — regression requirements

## 124. Build 04-H extension alignment

以下を維持する。

- 45° extension guide
- 15° extension guide
- arbitrary canonical angle extension
- segment exterior only
- endpoint snap priority
- extension alignment alone does not create topology
- X/Yとの距離比較
- Object Transform Wall extension除外

mid-segment機能追加でextension candidateがsegment interiorへ侵入しないこと。

---

## 125. Shift 15°

midpoint snap候補がない通常作図では、
Build 04-HまでのShift 15°補助を完全維持する。

---

## 126. T / Cross / Corner

Build 04-C～04-Gで対応済みのMesh接合を変更しない。

splitによりendpoint topologyが増えても、既存solverへ正しく入力するだけとする。

---

## 127. unsupported junction

Build 04-Hで整理した、

```text
OVERLAP
THREE_WAY
FOUR_WAY
MULTI
```

の`UNSUPPORTED` semanticsを変更しない。

split後にこれらが生じる場合も既存safe square profile behaviorを使う。

---

## 128. INVALID / FALLBACK

Build 04-Hの、

```text
INVALID -> FALLBACK
unsafe CONTINUATION -> FALLBACK
unsafe supported solver -> FALLBACK
```

を変更しない。

---

# Part R — error handling

## 129. user-facing errorは日本語

Build 05-Aで追加するwarning / errorは日本語を基本とする。

例:

```text
同じWall上の2点を結ぶ壁は作成できません。
接続先Wallが変更されたため壁を作成できませんでした。
Wallを安全に分割できませんでした。
Object TransformがあるWallは途中接続の対象にできません。
```

ただしhover候補除外のような通常状態で毎回reportを出してはならない。

---

## 130. silent candidate exclusion

以下は通常hover中にsilent exclusionでよい。

- hidden Wall
- transformed Wall
- malformed Wall
- endpoint boundary
- segment outside
- ambiguous equal candidates

ユーザーがfinalizeしようとした時点でtargetがinvalidになった場合だけwarningを出す。

---

# Part S — performance / determinism

## 131. candidate探索

現状規模ではcurrent view layerのmanaged Wallsを線形scanしてよい。

Build 05-Aでspatial indexは不要。

ただし同一MOUSEMOVE内で同じWallのprojectionを不要に複数回計算しないよう配慮する。

---

## 132. deterministic state

以下へ依存してはならない。

- Object名
- Blender自動連番
- collection iteration order
- object creation order
- Python object hash order

幾何distance / canonical coordinates / explicit ambiguity rejectionを使用する。

---

# Part T — implementation acceptance

## 133. compile/test commands

Codex実装後は最低限以下を実行する。

```text
python -m compileall japanese_house_modeler tests
python -m unittest discover -s tests -v
git diff --check
git diff --stat
git status --short
```

ローカルWindowsでの最終unit test時は`__pycache__`回避のため、

```text
python -B -m unittest discover -s tests
```

を使用してよい。

---

## 134. GitHub network禁止

Codex CloudからGitHubへのnetwork Gitは既知の403制約がある。

Build 05-A実装時、Codexへ以下を実行させない。

```text
git fetch
git pull
git push
git ls-remote
```

GitHubへの正式反映はユーザーWindows環境から行う。

Codexは与えられたlocal repository base上で実装・test・local commitまで行ってよい。

---

## 135. ZIPをCodexに作らせない

Codex Cloudの`/workspace/...` ZIP pathはユーザーが直接取得できない。

Build 05-AでもCodexへZIP作成を依頼しない。

実装patch review後、ChatGPT側でBlender実機テスト用ZIPを作成する。

---

## 136. review workflow

Build 05-Aの推奨workflow:

```text
1. このBUILD_05_A_SPECIFICATION.mdをGitHub mainへcommit/push
2. Codexへspecificationを読ませる
3. Codexは58bf807 + spec commitをbaseとしてlocal implementation
4. Codex unit tests
5. Codex local commit
6. userがpatch / full new fileをChatGPTへ提示
7. ChatGPT code review
8. 必要ならfocused修正
9. ChatGPTがBlender test ZIPを作成
10. Blender 5.2 LTS実機acceptance tests
11. pass後repo update ZIP
12. Windows repoへoverlay
13. diff / test / commit
14. git push origin main
15. GitHub commit確認
```

---

# Part U — Definition of Done

## 137. Build 05-A完了条件

以下をすべて満たした時点でBuild 05-A完了とする。

- selected Wall UIにread-only `壁角度`表示がある
- angleは0<=angle<180で方向非依存
- endpoint snapが従来どおり動く
- host interiorへmid-segment snapできる
- start click / end click両方でmid-segment snapできる
- segment exteriorは04-H extension alignmentのまま
- endpoint boundaryを誤splitしない
- transformed Wallをmid-snapしない
- ambiguous hostを勝手に選ばない
- 1host splitでT junctionを作れる
- 2host splitを1回のNewWall作図で行える
- split後original objectはcanonical START側を保持
- successorはcanonical END側を保持
- thickness / heightを継承
- materialを継承
- collection membershipを維持
- old START topologyを維持
- old END topologyをsuccessor ENDへtransfer
- reciprocal graphを維持
- existing T / Cross / Continuation等を壊さない
- same-host two-point caseを安全に拒否
- hover / first clickだけではmutationしない
- ESC cancelで何も変更しない
- transaction failureでrollback
- Ctrl+Z 1回で作図前へ戻る
- 既存66 unit testsが全PASS
- 05-A追加unit testsが全PASS
- Blender 5.2 LTS実機acceptance testsがPASS
- Windows repoからGitHub mainへ正式push済み
- final worktree clean

---

## 138. Build 05-A後に残る意図的制限

Build 05-A完了後も、以下は既知の制限として残る。

- Wall同士が単に交差しただけでは自動splitしない
- crossing pointでどちらのWallを選ぶか曖昧ならmid-snapしない
- transformed Wallはmid-snap対象外
- endpoint snap / X-Y helperのObject Transform統一は05-B候補
- Blender標準Delete後のneighbor auto-regenは未実装
- move endpointでWall途中へ接続できない
- angleは表示のみで数値編集できない
- same-host two-point Wallは作成不可
- opening / door / windowは未実装

これらはBuild 05-Bレビュー時に整理する。

---

# Final Implementation Principle

Build 05-Aで追加する「Wall途中接続」は、
新しい特殊Wall topologyを作る機能ではない。

**ユーザーのmid-segment clickを、既存Wallの安全なsplitと通常endpoint topologyへ変換する機能**である。

最終的なWall Systemは常に、

```text
Wall.start
Wall.end
Wall.thickness
Wall.height
endpoint topology
```

だけをsource of truthとし、

```text
canonical data + topology -> derived junction -> derived Mesh
```

の一方向性を維持すること。
