# 日本住宅モデラー — Build 04-A Specification

## 1. 目的

Build 04-Aでは、Wall同士の将来の接合処理の基礎として、**WallのSTART / END端点ごとに、他Wall端点との接続情報（Connection）を永続データとして保持する仕組み**を実装する。

Build 04-Aではまだ、壁厚を考慮した角のMesh処理、出隅・入隅、T字接合などは行わない。

このBuildの目的は、

```text
Wall A / END  <->  Wall B / START
```

のような「どのWallのどの端点と接続しているか」という**意味情報**を、Mesh座標とは独立した正規データとして保存することである。

今後のWall Systemでは、

- Wall geometry
- Wall endpoint topology

を分離して扱う。

Wall geometryのsource of truth：

- `jhm_wall.start`
- `jhm_wall.end`
- `jhm_wall.wall_thickness`
- `jhm_wall.wall_height`

Wall endpoint topologyのsource of truth：

- START endpoint connections
- END endpoint connections

とする。

---

## 2. 基準状態

Build 04-AはGitHub `main` の以下を基準とする。

- `dbbc26b Implement Build 03-B wall dimension editing`

Build 03-BまでBlender 5.2 LTS実機テスト済み。

現在の主要機能：

- 新規Wallの2クリック作図
- 直接端点スナップ 16 px
- X/Yアライメント 10 px
- Shift 15°拘束
- 始点移動
- 終点移動
- 壁厚変更
- 壁高さ変更
- Wall data -> Mesh再生成
- Undo
- Object Transform異常時の安全拒否

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

Build 04-AはBuild 03-Bまでの実機テスト済み挙動を壊してはならない。

---

# Part A — Build 04-Aの範囲

## 4. 実装する機能

Build 04-Aでは以下を実装する。

- Wall START endpointごとのConnection collection
- Wall END endpointごとのConnection collection
- Connection先Wall Objectの永続参照
- Connection先endpoint（START / END）の保存
- 双方向Connection
- 重複Connection防止
- 自己Connection防止
- 1端点に複数Connectionを保持
- 直接端点スナップ確定時のConnection自動登録
- 新規WallのSTART直接スナップ時のConnection登録
- 新規WallのEND直接スナップ時のConnection登録
- 既存Wall端点移動時のConnection更新
- 接続済み端点を別位置へ移動した場合の旧Connection解除
- 別の端点へ直接スナップした場合の新Connection登録
- X/YアライメントだけではConnectionを作らない
- Shift拘束だけではConnectionを作らない
- 壁寸法変更時はConnectionを維持
- START / ENDの有効Connection数をUI表示
- UndoによるConnection状態の復元
- 無効Pointerを安全に無視
- Connection情報の保存 / .blend persistence
- 既存Wallへの後方互換

---

## 5. 実装しない機能

以下はBuild 04-Aでは実装しない。

- 出隅Mesh
- 入隅Mesh
- T字接合Mesh
- 十字接合Mesh
- 壁厚を考慮した端部トリミング
- miter処理
- butt joint処理
- 自動延長
- connected Wallの連動移動
- junction全体の移動
- 壁途中へのConnection
- segment/intersection Connection
- T字の途中接続
- 接続する / しないの手動トグル
- Connection一覧の編集UI
- 手動「接続を追加」ボタン
- 手動「接続を解除」ボタン
- start/end数値入力
- Object Transform同期
- Edit Mode Mesh逆同期
- Wall削除時のグローバルdepsgraph cleanup handler
- Wall複製時のConnection自動修復
- junction ID
- 開口
- ドア
- 窓
- 床
- 天井
- AI間取り図解析

---

# Part B — Connectionデータ構造

## 6. 新しいPropertyGroup

`japanese_house_modeler/properties.py` に、Connection 1件を表すPropertyGroupを追加する。

推奨名：

```python
class JHM_WallConnection(bpy.types.PropertyGroup):
    ...
```

---

## 7. Connectionが保存する情報

Connection 1件は最低限以下を保存する。

```text
target_object
target_endpoint
```

### target_object

接続先のWall Object。

Blender Objectへの `PointerProperty` を使用する。

Object名文字列だけを保存する方式は採用しない。

理由：

- renameに強い
- 同一.blend内のObject参照として自然
- 将来Object identityを利用できる

### target_endpoint

接続先の端点。

Enum：

```text
START
END
```

---

## 8. source endpointはConnection内に保存しない

source側のendpointは、どのCollectionにConnectionが入っているかで決まる。

例：

```text
wall.start_connections
```

内のConnectionであればsource endpointはSTART。

```text
wall.end_connections
```

内ならsource endpointはEND。

したがって、Connectionごとに `source_endpoint` を重複保存しない。

---

## 9. JHM_WallPropertiesへ追加

既存 `JHM_WallProperties` へ以下を追加する。

推奨：

```python
start_connections: CollectionProperty(type=JHM_WallConnection)
end_connections: CollectionProperty(type=JHM_WallConnection)
```

既存Property：

- is_wall
- start
- end
- wall_thickness
- wall_height

は変更しない。

---

## 10. Connection数は保存しない

以下のような整数Propertyは追加しない。

```text
start_connection_count
end_connection_count
```

Connection数はCollectionから都度計算する。

---

## 11. 既存Wallとの互換性

Build 04-A導入前に作成済みのWallにはConnection collectionが空の状態で追加される。

既存Wall同士が座標上ぴったり接していても、

**Build 04-A導入時にConnectionを自動推測・自動生成してはならない。**

理由：

- 座標一致が意図的な接合とは限らない
- Meshから意味情報を推測しない
- Connectionはユーザー操作として成立した直接スナップから生成する

したがって、Build 04-A以前に作成したWallは、初期状態では：

```text
始点接続: 0
終点接続: 0
```

で正しい。

---

# Part C — Connection不変条件

## 12. 双方向

Connectionは必ず双方向とする。

例：

```text
Wall A / END -> Wall B / START
```

を登録する場合、同時に：

```text
Wall B / START -> Wall A / END
```

も登録する。

片方向だけを正常状態として残してはならない。

---

## 13. 自己Connection禁止

以下は禁止。

```text
Wall A / START -> Wall A / START
Wall A / START -> Wall A / END
Wall A / END   -> Wall A / START
Wall A / END   -> Wall A / END
```

同一Wall Object内の端点同士をConnectionとして登録しない。

---

## 14. 重複Connection禁止

同じsource endpointから同じtarget endpointへのConnectionを複数登録してはならない。

例：

```text
A END -> B START
A END -> B START
```

という重複は不可。

登録helperは既存Connectionを確認し、idempotentに動作すること。

---

## 15. 複数Connection許可

1端点には複数Connectionを持てる。

例：

```text
Wall A / END
 ├─ Wall B / START
 └─ Wall C / START
```

これは正常。

単一PointerPropertyだけでConnectionを表現してはならない。

---

# Part D — junction表現

## 16. 1つの物理junction

同じ直接スナップ地点へ3本以上のWallが集まる可能性がある。

Build 04-Aでは専用 `Junction` Objectや `junction_id` は作らない。

代わりに、同じjunctionに属するendpoint同士をConnection collectionで表現する。

---

## 17. 完全な相互Connectionを維持

同じjunctionにN個のendpointが属する場合、

**各endpointが他のN-1 endpointすべてをConnectionとして持つ状態**

を正常状態とする。

3 endpointの場合：

```text
A END <-> B START
A END <-> C START
B START <-> C START
```

となる。

各endpointの有効Connection数は2。

この完全相互Connection（clique）をBuild 04-Aのjunction不変条件とする。

---

## 18. なぜ完全相互Connectionにするか

例：

```text
A END
B START
C START
```

が同一junctionに存在する状態でAだけを後から別位置へ動かした場合、

AとのConnectionを解除しても、

```text
B START <-> C START
```

が残る必要がある。

Aだけをhubとして、

```text
B -> A <- C
```

とした場合、Aを外したときB/Cのjunction情報まで失われる。

そのためBuild 04-Aではjunction内endpoint同士を完全相互Connectionとする。

---

# Part E — Connection helper

## 19. 専用helper moduleを推奨

Connection操作は新規の小さなmoduleへ分離することを推奨する。

推奨ファイル：

```text
japanese_house_modeler/connections.py
```

このmoduleにはConnection topology操作だけを置く。

既存 `operators.py` の作図・GPU処理を大規模移動しない。

---

## 20. helperの責務

最低限、概念的に以下の処理を提供する。

```text
get endpoint collection
validate endpoint ref
find existing connection
add one reciprocal connection
remove one reciprocal connection
disconnect one endpoint from all
collect junction members
attach endpoint to junction
count valid connections
purge invalid entries on touched endpoint
```

実際の関数名はCodexに任せる。

---

## 21. endpoint参照表現

内部helperでは、

```text
(object, "START")
(object, "END")
```

のような組でendpointを扱ってよい。

小さなnamed tuple/dataclass相当を使ってもよいが、不要な大規模型システムは作らない。

---

## 22. endpoint collection helper

endpoint enumに応じて：

```text
START -> wall.start_connections
END   -> wall.end_connections
```

を返す共通helperを用意する。

START/END分岐を各Operatorへ大量重複させない。

---

# Part F — 有効Connection

## 23. 有効なtarget

Connectionを有効とみなす条件：

- `target_object` がNoneでない
- target Objectが現在の `bpy.data.objects` に存在
- targetに `jhm_wall` がある
- `target.jhm_wall.is_wall == True`
- target_endpointがSTARTまたはEND

---

## 24. stale Pointer

接続先Wallがユーザー操作で削除されると、残ったWall側のPointerPropertyが無効 / Noneになる可能性がある。

Build 04-Aではグローバル削除handlerを追加しない。

代わりに：

- UI connection countでは無効entryを数えない
- Connectionを操作するhelperは、触れたCollection内の無効entryを安全に除去してよい
- stale entryがあってもPython例外を出さない

---

## 25. 手動削除後

例：

```text
A END <-> B START
```

でB Objectを手動削除した場合、A ENDのUI countは有効Connectionとして0になってよい。

AのCollection内にstale itemが内部的に一時残っていても、Build 04-AではUIや操作が壊れなければよい。

---

# Part G — 直接スナップ対象identity

## 26. 現在の問題

Build 03-B時点のdirect snap処理は、主に：

```text
snap coordinate
```

を保持している。

Build 04-AではConnectionを作るため、

**どのWall Objectのどのendpointへスナップしたか**

も保持する必要がある。

---

## 27. direct snap target

direct snap成立時は最低限以下をstateとして保持する。

概念：

```text
snap_target_object
snap_target_endpoint
snap_candidate_coordinate
```

target_endpointは：

```text
START
END
```

---

## 28. snap解除時

direct snap範囲から外れた場合：

```text
snap_target_object = None
snap_target_endpoint = None
```

相当へ必ずクリアする。

過去のsnap target identityを次の確定へ誤使用してはならない。

---

## 29. visible endpoint列挙

既存 `_visible_wall_endpoints()` 相当は、Connection用identityを取得できるようにする。

推奨候補：

```text
wall_object
endpoint_name
endpoint_coordinate
endpoint_2d
```

を返す。

または、既存座標列挙を維持しつつ、direct snap用にidentity付きrecord列挙を追加してもよい。

重要なのはBuild 02-D / 03-Aの描画・アライメント挙動を壊さないこと。

---

## 30. tie

複数endpointが同一画面位置に重なる場合、Build 02-C以降のclosest/stable tie方針を維持する。

選ばれた1 endpointをdirect snap targetとする。

ただし、そのtargetが既存junctionの一員であれば、後述のjunction attachによりjunction全体へ接続する。

---

# Part H — 新規Wall：START snap

## 31. START direct snap

新規Wall作図で最初のクリックが既存Wall endpointへの直接スナップだった場合、

その時点の：

```text
target object
target endpoint
```

を、Wall作成完了まで別stateとして保持する。

---

## 32. START target保持

新規WallのEND候補を動かすと通常のsnap target stateは変化する。

そのためSTART用targetを別途保持する。

概念：

```text
_start_snap_target_object
_start_snap_target_endpoint
```

---

## 33. STARTがalignmentのみ

最初のクリックがX/Y alignmentによる位置合わせだった場合、Connectionを作らない。

たとえ結果座標が既存endpointと数値的に一致した場合でも、

**direct snapとして成立していない限りConnectionを作らない。**

---

# Part I — 新規Wall：END snap

## 34. END direct snap

2回目クリック時にdirect snap targetが存在する場合、

新規Wall ENDをそのtarget junctionへ接続する。

---

## 35. END alignmentのみ

X/Y alignmentのみの場合はConnectionを作らない。

Shift + alignmentでも同じ。

---

## 36. direct snap優先

Build 02-Dまでの優先順位：

```text
direct endpoint snap > alignment / Shift combination
```

を維持する。

direct snap成立時はConnection対象として扱う。

---

# Part J — 新規Wall作成後のConnection登録

## 37. Wall Object作成前には登録しない

新規WallのConnectionは、Wall Objectが正常に作成され、

```text
wall.is_wall = True
wall.start
wall.end
wall_thickness
wall_height
```

が設定可能な状態になってから登録する。

存在しないsource ObjectへのConnectionを作らない。

---

## 38. START/END登録

新規Wall作成成功時：

- STARTがdirect snapだった → STARTをtarget junctionへattach
- ENDがdirect snapだった → ENDをtarget junctionへattach

両方free/alignmentならConnection 0。

---

## 39. 作成失敗時

Wall Object / Mesh生成中またはConnection登録中に失敗した場合、

作成途中Wallを削除し、

既存Wall側へ追加済みのreciprocal Connectionも可能な限りロールバックする。

既存Wall側に「存在しない新規WallへのConnection」を残してはならない。

---

# Part K — junction attach

## 40. direct snap先が単独endpoint

target endpointに既存Connectionが0の場合：

```text
source <-> target
```

を追加する。

結果：

```text
source count = 1
target count = 1
```

---

## 41. direct snap先が既存junction

例：

```text
A END <-> B START
```

が既に存在し、C STARTをA ENDへdirect snapした場合、

C STARTはA ENDだけでなく、そのjunction全memberへ接続する。

結果：

```text
A END <-> B START
A END <-> C START
B START <-> C START
```

全endpoint count = 2。

---

## 42. junction member収集

target endpointから有効Connection graphを辿り、targetと同じjunctionに属するendpoint群を収集する。

Build 04-AではConnection graphのconnected componentとして収集してよい。

---

## 43. sourceを除外

source endpoint / source Wall自身はjunction member候補から除外する。

自己Connectionを作らない。

---

## 44. idempotent attach

すでに同じjunction memberへのConnectionが存在する場合は重複追加しない。

---

# Part L — 既存Wall端点移動

## 45. 移動開始時

Build 03-Aと同じく、モーダル移動中はConnectionを変更しない。

MOUSEMOVE中：

- Wall data変更なし
- Mesh変更なし
- Connection変更なし

GPU previewだけ更新。

---

## 46. Esc / 右クリック

キャンセル時：

- start/end変更なし
- Mesh変更なし
- Connection変更なし

---

## 47. 移動対象endpointの既存Connection

確定時、移動するendpointの現在Connectionはすべて旧junction情報とみなす。

移動によってsource endpoint位置が変わるため、旧Connectionを解除する。

---

## 48. 反対側endpoint

Wallの移動していない反対側endpointのConnectionは変更しない。

例：

START移動：

- START connections更新
- END connections維持

END移動：

- END connections更新
- START connections維持

---

## 49. free位置へ移動

接続済みendpointをdirect snapなしのfree位置へ移動して確定した場合：

1. 旧Connectionを全解除
2. 新Connectionは0
3. Mesh / saved endpointを更新

---

## 50. alignment位置へ移動

X/Y alignment、Shift、Shift + alignmentによって確定した場合も、

direct snap targetがなければ：

- 旧Connection全解除
- 新Connectionは0

とする。

---

## 51. 新しいendpointへdirect snap

接続済みendpointを別のWall endpointへdirect snapした場合：

1. 旧junctionからsource endpointをdetach
2. 新target junctionを収集
3. source endpointを新junctionへattach
4. Mesh / saved endpointを更新

---

## 52. 同じjunctionへ再snap

元と同じjunctionのendpointへ再度direct snapして確定してもよい。

- duplicateなし
- clique invariant維持
- Connection countが不必要に増えない

こと。

---

# Part M — detach

## 53. endpoint全解除

source endpointをjunctionから外す場合、

source collectionだけをclearして終わってはならない。

各target endpoint側からも、

```text
target -> source
```

reciprocal entryを削除する。

---

## 54. junction残存member

clique invariantにより、sourceを外した後も残りmember同士のConnectionはそのまま維持される。

例：

移動前：

```text
A <-> B
A <-> C
B <-> C
```

Aをdetach：

```text
B <-> C
```

が残る。

---

# Part N — 原子的更新

## 55. Connection snapshot

既存Wall端点移動確定時は、変更対象endpointの旧Connection情報を復元可能な形でsnapshotしてから topologyを変更することを推奨する。

概念：

```text
[(target_object, target_endpoint), ...]
```

---

## 56. 移動確定処理

推奨順：

1. 最終candidate確認
2. direct snap target identity確認
3. new geometry計算
4. 旧Connection snapshot
5. old Mesh保持
6. new Mesh構築
7. saved endpoint更新
8. source endpointを旧junctionからdetach
9. direct snapなら新junctionへattach
10. 成功確定
11. old Mesh削除

実装上の順序は多少変更可。

重要なのは失敗時に不整合を残さないこと。

---

## 57. 失敗時

途中失敗時は可能な限り：

- old Meshへ戻す
- old start/endへ戻す
- old Connection topologyへ戻す
- new Mesh削除
- partial reciprocal Connection削除

を行う。

以下を残してはならない。

```text
endpoint座標は旧位置だがConnectionだけ新junction
```

または：

```text
endpointは新位置だがConnectionだけ旧junction
```

---

# Part O — Undo

## 58. 新規Wall Undo

直接スナップで新規Wallを作成後Ctrl+Zした場合：

- 新規Wall ObjectがUndoされる
- target Wall側に追加されたreciprocal ConnectionもUndoされる

こと。

target側にstale Connectionを残さない。

---

## 59. endpoint移動 Undo

接続済みendpointを別位置へ移動した後Ctrl+Z：

- start/end
- Mesh
- 旧Connection
- 新Connection

すべて操作前へ戻ること。

---

## 60. dimension edit Undo

Build 03-Bの壁寸法変更Undoは既存どおり。

Connection collectionは寸法変更によって変更されない。

---

# Part P — Build 03-B寸法変更との関係

## 61. 壁厚変更

壁厚を変更してもSTART/ENDのConnection情報は維持する。

Connectionは壁芯endpoint topologyであり、壁厚値とは独立。

---

## 62. 壁高さ変更

壁高さ変更でもConnectionを維持する。

---

## 63. Edit Mode崩しから寸法再生成

Edit ModeでMeshを崩し、Build 03-Bの「壁寸法を変更」で正常形へ再生成してもConnectionを維持する。

MeshはConnectionのsource of truthではない。

---

# Part Q — UI

## 64. 選択中の壁

既存N-panel：

```text
選択中の壁

壁厚: 130.0 mm
壁高さ: 2500.0 mm

[ 壁寸法を変更 ]

[ 始点を移動 ]
[ 終点を移動 ]
```

へConnection countを追加する。

---

## 65. UI例

推奨：

```text
選択中の壁

壁厚: 130.0 mm
壁高さ: 2500.0 mm

始点接続: 1
終点接続: 2

[ 壁寸法を変更 ]

[ 始点を移動 ]
[ 終点を移動 ]
```

---

## 66. count

UI countは有効Connectionのみを数える。

stale / None targetは数えない。

---

## 67. read-only

Build 04-AではConnection countはread-only表示。

クリックして一覧編集するUIは作らない。

---

# Part R — snap visual

## 68. 表示変更なし

direct snap時の：

- `◎`
- `○`
- guide

などのGPU表現はBuild 03-Aまでと同じでよい。

Connection登録のための新しい色・アイコン表示は不要。

---

## 69. connection preview不要

MOUSEMOVE中に、

```text
このsnapでConnectionが作られます
```

という追加UIはBuild 04-Aでは不要。

direct snap highlight自体が十分な視覚フィードバックである。

---

# Part S — hidden / excluded target

## 70. visibility policy

Build 02-C / 02-Dと同じく、

- hidden Wall
- hidden Collection
- excluded View Layer
- Local View不可視
- screen外
- projection不能

のendpointはdirect snap targetにならない。

したがってConnectionも作られない。

---

# Part T — Object Transform

## 71. 新規Wall

新規Wallはこれまでどおりidentity Transformで生成。

Connection登録はworld-space saved endpointを使う。

---

## 72. endpoint編集

Build 03-Aのtransform拒否方針を維持。

Object Transform異常Wallのendpoint編集を拒否する場合、Connectionも変更しない。

---

## 73. dimension edit

Build 03-Bと同じ。

Transform異常で寸法変更拒否時、Connectionを変更しない。

---

# Part U — Edit Mode

## 74. Mesh手動編集

Edit ModeでWall Meshだけを手動変更してもConnectionは変化しない。

MeshからConnectionを推論しない。

---

## 75. 専用endpoint移動

Edit Modeで崩したWallを専用endpoint移動で再生成する場合、

Connection更新は保存済みtopology + 今回のdirect snap結果から行う。

Mesh頂点から接続相手を推定しない。

---

# Part V — Wall削除

## 76. Build 04-AのWall削除範囲

専用「Wall削除Operator」はBuild 04-Aでは実装しない。

通常のBlender DeleteでWallが削除される可能性がある。

---

## 77. 削除されたtarget

Pointerが無効になったConnectionはUI countから除外する。

他の操作でそのendpoint Connection collectionを触る際にpurgeしてよい。

---

## 78. depsgraph handler禁止

Build 04-AではWall削除を監視するpersistent depsgraph handler等を追加しない。

イベント駆動の自動cleanupは後続Buildで必要性を検討する。

---

# Part W — Wall複製

## 79. Duplicate

Shift+D等による管理Wall複製はBuild 04-Aの正式対応範囲外。

BlenderがPropertyGroup Collectionを複製した結果、Connection topologyが意味的に不整合になる可能性がある。

Build 04-Aでは自動修復しない。

将来、専用Duplicateまたはvalidation機構を検討する。

---

# Part X — ファイル構成

## 80. properties.py

主な変更：

- `JHM_WallConnection`
- `start_connections`
- `end_connections`

既存dimension Propertyを変更しない。

---

## 81. connections.py

新規追加を推奨。

役割：

- topology helperのみ

既存作図/GPUコードは移動しない。

---

## 82. operators.py

主な変更：

- direct snap target identity保持
- START snap target保持
- 新規Wall作成成功時Connection attach
- endpoint移動確定時detach / attach
- transaction / rollback統合

新しい接合Mesh処理を追加しない。

---

## 83. ui.py

- 始点接続数
- 終点接続数

のread-only表示追加。

---

## 84. __init__.py

`JHM_WallConnection` を登録する。

登録順は `JHM_WallProperties` より前。

例：

```text
JHM_NewWallDefaults
JHM_WallConnection
JHM_WallProperties
...
```

またはConnectionをNewWallDefaultsより前でもよい。

重要なのはConnection classがWallPropertiesより先に登録されること。

---

# Part Y — リファクタリング制限

## 85. 既存挙動優先

Build 04-Aはtopology追加が目的。

以下を行わない。

- operators.py全面書き換え
- GPU描画全面変更
- wall geometry式変更
- UI全面再設計
- Build番号と無関係なformatting
- 既存Operator名称総変更

---

## 86. identity付きendpoint列挙

snap target identity追加のための小規模リファクタリングは許可する。

ただしBuild 02-Dの：

- closest snap
- 16 px
- 10 px alignment
- stable tie
- visibility filter
- Shift挙動

を維持する。

---

# Part Z — 実機テスト

## 87. テストA — 既存Wall初期値

Build 04-A導入前に作成したWallを選択。

座標上他Wallと接していても：

```text
始点接続: 0
終点接続: 0
```

であること。

自動推測しないこと。

---

## 88. テストB — 2本の新規Wall

1. Wall Aを作る
2. Wall BのSTARTをA ENDへdirect snap
3. B ENDはfreeで確定

期待：

```text
A END connection count = 1
B START connection count = 1
A END -> B START
B START -> A END
```

A START / B ENDは0。

---

## 89. テストC — END direct snap

Wall BのENDをWall Aのendpointへdirect snapするケースでも双方向Connectionが作られること。

---

## 90. テストD — 新規Wall両端snap

1. Wall A endpoint
2. Wall B endpoint
3. 新規Wall C STARTをAへdirect snap
4. C ENDをBへdirect snap

期待：

- C STARTにA側Connection
- C ENDにB側Connection
- A/B側 reciprocalも存在

---

## 91. テストE — alignmentではConnectionなし

1. direct snapの16 px範囲には入れない
2. XまたはY alignmentだけを成立
3. Wall確定

期待：

```text
connection count = 0
```

該当位置が偶然同じX/YでもConnectionを作らない。

---

## 92. テストF — Shift + alignment

Shift拘束 + X/Y alignmentでもdirect snapでなければConnection 0。

---

## 93. テストG — 3本junction

1. A ENDとB STARTをdirect snapで接続
2. C STARTをA ENDへdirect snap

期待：

```text
A END count = 2
B START count = 2
C START count = 2
```

Topology：

```text
A <-> B
A <-> C
B <-> C
```

完全相互Connectionになっていること。

---

## 94. テストH — 4本junction

同一junctionへ4 endpointをdirect snap。

各endpointの有効Connection数：

```text
3
```

重複がないこと。

---

## 95. テストI — endpointをfree位置へ移動

2本junction：

```text
A END <-> B START
```

A ENDを専用「終点を移動」でfree位置へ移動。

期待：

```text
A END count = 0
B START count = 0
```

AだけMesh更新。

Bは移動しない。

---

## 96. テストJ — 3本junctionから1本を外す

移動前：

```text
A END count = 2
B START count = 2
C START count = 2
```

A ENDをfree位置へ移動。

期待：

```text
A END count = 0
B START count = 1
C START count = 1
B <-> C は維持
```

---

## 97. テストK — 別junctionへ移動

A ENDがB STARTへ接続済み。

A ENDをC STARTへdirect snapで移動。

期待：

- A-B Connection削除
- A-C Connection登録
- B count減少
- C count増加
- saved endpoint / Mesh正常更新

---

## 98. テストL — 同じjunctionへ再snap

接続済みA ENDを、同じjunctionのB STARTへ再度direct snapして確定。

期待：

- duplicate Connectionなし
- counts不変
- reciprocal invariant維持

---

## 99. テストM — 移動Cancel

接続済みendpointを移動開始し、別junctionへpreview後Esc。

期待：

- Connection完全無変更
- Mesh無変更
- endpoint無変更

右クリックでも同様。

---

## 100. テストN — endpoint移動Undo

A ENDをBからCへ接続変更して確定。

Ctrl+Z。

期待：

- A endpoint位置が元へ戻る
- Meshが元へ戻る
- A-B Connection復元
- A-C Connection削除
- B/C reciprocalも元状態へ戻る

---

## 101. テストO — 新規Wall Undo

既存Aへ新規Bをdirect snapして作成。

Connection countが1になった後Ctrl+Z。

期待：

- Bが消える
- A側Connection countが0へ戻る
- stale B Pointerを残さない

---

## 102. テストP — 壁寸法変更維持

connected Wallの壁厚/高さをBuild 03-B機能で変更。

期待：

- Connection count不変
- target identity不変
- Mesh寸法のみ更新

Ctrl+ZでもConnectionは変化しない。

---

## 103. テストQ — Edit Mode Mesh崩し

connected Wall MeshをEdit Modeで崩す。

Connection countは変わらない。

「壁寸法を変更」または専用endpoint編集で再生成しても、仕様どおりConnection topologyが維持 / 更新されること。

---

## 104. テストR — target Wall削除

A END <-> B STARTを作る。

Blender標準DeleteでBを削除。

A選択時：

- UIが壊れない
- A ENDの有効Connection countは0
- Python errorなし

---

## 105. テストS — save / reopen

Connectionを持つ.blendを保存。

Blenderを閉じて再度開く。

期待：

- target Object Pointerが復元
- endpoint enumが復元
- connection countが同じ

---

## 106. テストT — Object rename

A-B接続後、BのObject名を変更。

期待：

- PointerProperty Connectionは維持
- Aのcount変化なし

Object名文字列依存でないこと。

---

## 107. テストU — hidden target

hidden Wall endpointはdirect snapできず、Connectionも作られない。

---

## 108. テストV — Object Transform拒否

connected WallへObject Transformを加える。

endpoint編集や寸法編集が既存仕様どおり拒否され、

Connectionは変更されない。

---

# Part AA — 回帰テスト

## 109. Build 03-B

- 壁厚のみ変更
- 壁高さのみ変更
- 両方変更
- Cancel
- Undo
- Material維持

が正常。

---

## 110. Build 03-A

- 始点を移動
- 終点を移動
- direct snap
- alignment
- Shift
- Cancel
- Undo

が正常。

---

## 111. Build 02-D以前

- 新規Wall作図
- direct snap 16 px
- alignment 10 px
- Shift 15°
- guide
- 矩形作図

が正常。

---

# Part AB — 完了条件

## 112. Build 04-A完了条件

Blender 5.2 LTS実機で以下を満たした時点でBuild 04-A完了とする。

- JHM_WallConnectionが永続Propertyとして存在
- START / ENDが別Collectionを持つ
- target Object / target endpointを保存
- direct snapでConnection自動生成
- Connectionが双方向
- duplicateなし
- self connectionなし
- 1端点に複数Connection可能
- junction内が完全相互Connection
- new Wall START/END snapの両方で動作
- alignmentだけではConnectionなし
- endpoint移動で旧Connection解除
- 新junction direct snapで新Connection登録
- 3本junctionから1本を外しても残り2本Connection維持
- CancelでConnection無変更
- UndoでConnection topology復元
- 壁厚/高さ変更でConnection維持
- target削除によるstale PointerでUIが壊れない
- save/reopenでConnectionが保持される
- Object renameでConnectionが保持される
- Build 03-B以前に回帰不具合がない

---

# Part AC — 次Build

## 113. Build 04-B候補

Build 04-A完了後、Connection topologyを利用して**endpoint junctionの分類**へ進む。

候補：

```text
2-wall corner
3-wall junction
4-wall junction
collinear continuation
corner angle
T / cross候補
```

ただしBuild 04-Bでも、いきなりMesh trimmingへ進む前に、

「接続されたWallの方向関係を正しく分類できる」

ことを先に確立するのが望ましい。

---

## 114. Mesh jointはその後

junction分類が安定してから、

- 出隅
- 入隅
- miter
- butt
- T接合
- 壁厚差
- 自動端部生成

へ進む。

Build 04-AではMesh jointを先取りしない。
