# 日本住宅モデラー — Build 03-A Specification

## 1. 目的

Build 03-Aでは、既存の日本住宅モデラー管理Wallについて、**始点または終点を専用のモーダル操作で移動し、そのWallの保存データとMeshを同時に更新する機能**を実装する。

これにより、ユーザーがWall形状を修正するためにBlenderのEdit ModeでMesh頂点を直接動かす必要を減らし、

`Wall data -> Mesh`

という本プロジェクトの基本構造を維持する。

Build 02-Dまでに完成した以下の作図補助機能を、既存Wall端点の移動でも利用できることを主要要件とする。

- 直接端点スナップ
- X/Yアライメント
- Shift 15°角度拘束
- アライメントガイド
- スナップ対象ハイライト
- 画面ピクセル基準判定

Build 03-Aでは壁厚・壁高さの編集、壁同士の接合処理、出隅・入隅処理は行わない。

---

## 2. 基準状態

Build 03-AはGitHub `main` の以下の状態を基準とする。

- Build 02-D実装コミット:
  - `7188375 Implement Build 02-D alignment snapping`

Build 02-DまでのBlender 5.2 LTS実機テストは完了済みである。

現在の主要仕様：

- Blender 5.2 LTS
- Wall source of truth:
  - `jhm_wall.start`
  - `jhm_wall.end`
  - `jhm_wall.wall_thickness`
  - `jhm_wall.wall_height`
- start/end:
  - world-space XY
  - Z = 0
  - meters
- UI寸法:
  - mm
- 1 Wall = 1 Blender Object
- 壁芯基準
- 直接端点スナップ:
  - 16 px
- X/Yアライメント:
  - 10 px
- Shift:
  - 15°刻み
- 新規Wallデフォルト壁厚:
  - 130 mm
- 新規Wallデフォルト壁高さ:
  - 2500 mm

---

## 3. 親仕様

以下を前提とする。

- `SPECIFICATION.md`
- `BUILD_02_A_SPECIFICATION.md`
- `BUILD_02_B_SPECIFICATION.md`
- `BUILD_02_C_SPECIFICATION.md`
- `BUILD_02_D_SPECIFICATION.md`

Build 03-AはBuild 02-A〜02-Dの挙動を壊してはならない。

---

# Part A — Build 03-Aの範囲

## 4. 実装する機能

Build 03-Aでは以下を実装する。

- 選択中Wallの始点移動
- 選択中Wallの終点移動
- 1クリックで移動先を確定するモーダル操作
- 移動中のGPUプレビュー
- 移動対象ではない反対側端点の固定
- Build 02-Dまでの直接端点スナップ
- Build 02-DまでのX/Yアライメント
- Shift 15°角度拘束
- Shift押下・解放の即時再評価
- 参照端点ハイライト
- アライメントガイド
- 確定時の `jhm_wall.start/end` 更新
- 対象Wall Meshの再生成
- Wall Object自体の維持
- Esc / 右クリックによるキャンセル
- Undo
- 選択状態・active状態の維持
- 対象Wall自身をスナップ/アライメント参照候補から除外
- 不正な極小長Wallの生成防止

---

## 5. 実装しない機能

以下はBuild 03-Aでは実装しない。

- 壁厚編集
- 壁高さ編集
- 壁厚/高さ変更時の再生成UI
- Edit Mode操作の監視
- Edit Mode MeshからWallデータへの逆同期
- Object ModeのMove/Rotate/ScaleからWallデータへの逆同期
- 既存Wall全体の移動
- 2端点同時移動
- 壁途中の編集点
- 壁途中への直接スナップ
- 任意Mesh頂点への一般スナップ
- T字接合
- 十字接合
- 出隅・入隅
- 壁厚を考慮した端部トリミング
- 自動延長
- 「接合する / しない」の属性
- ドア
- 窓
- 床
- 天井
- AI間取り図解析

---

# Part B — UI

## 6. 選択中の壁パネル

既存の3D View N-panel、

`日本住宅 > 日本住宅モデラー > 選択中の壁`

を拡張する。

現在表示している、

- 壁厚
- 壁高さ

は維持する。

その下に以下の2ボタンを追加する。

- `始点を移動`
- `終点を移動`

概念UI：

```text
選択中の壁

壁厚: 130.0 mm
壁高さ: 2500.0 mm

[ 始点を移動 ]
[ 終点を移動 ]
```

壁厚・壁高さはBuild 03-Aでは引き続きread-only表示でよい。

---

## 7. UI有効条件

ボタンは、active Objectが以下を満たす場合に使用可能とする。

`active_object.jhm_wall.is_wall == True`

管理Wall以外のObjectがactiveの場合は、

`Wallを選択してください。`

という既存表示を維持し、端点移動ボタンは表示しない、またはdisabledとする。

---

## 8. Operator構成

実装方法は以下のどちらでもよい。

### 推奨

1つのOperatorを作り、移動対象をEnum/String Propertyで指定する。

例：

- `START`
- `END`

UI側で、

- 始点ボタン → START
- 終点ボタン → END

を設定する。

### 許容

始点・終点で2つの小さなOperatorを作る方式。

ただし処理コードを大きく重複させないこと。

---

# Part C — 端点移動操作

## 9. 操作開始

ユーザーが、

`始点を移動`

または

`終点を移動`

を押した時点でモーダル編集を開始する。

新規Wall作図のような「最初の始点クリック」は不要。

移動対象端点は既に決まっているため、

**モーダル開始後の次の左クリックが移動先の確定クリック**

となる。

---

## 10. 始点を移動する場合

元Wallデータ：

- `start = S`
- `end = E`

始点移動では、

- 固定点 = E
- 移動点 = S

とする。

プレビュー候補をCとした場合、

確定後：

- `wall.start = C`
- `wall.end = E`

とする。

Eを変更してはならない。

---

## 11. 終点を移動する場合

元Wallデータ：

- `start = S`
- `end = E`

終点移動では、

- 固定点 = S
- 移動点 = E

とする。

確定後：

- `wall.start = S`
- `wall.end = C`

とする。

Sを変更してはならない。

---

## 12. 初期候補位置

Operator開始直後は、まだ3D View内でマウスを動かしていない可能性がある。

特にN-panelのボタンから起動するため、起動イベントのマウス位置をそのままXY平面座標として利用しない。

初期プレビュー候補は、

**現在保存されている移動対象端点**

とする。

例：

終点移動開始直後：

`candidate = current wall.end`

始点移動開始直後：

`candidate = current wall.start`

これにより、操作開始直後にWallプレビューが突然別位置へ飛ばないようにする。

---

## 13. マウス移動

3D View内で有効なXY平面座標を取得できたMOUSEMOVEごとに候補点を更新する。

Build 02-A以降と同じ、

- Viewport ray
- Z=0平面交差

を使用する。

有効なXY交差を取得できない場合は、最後の有効候補を維持するか、プレビュー更新を行わない。

WallデータやMeshを破壊しないこと。

---

## 14. 左クリック確定

左クリック `PRESS` で現在のraw位置を再評価し、

- 直接端点スナップ
- X/Yアライメント
- Shift拘束

を含む最終候補を決定する。

プレビューで見えていた候補と確定値が不必要に異ならないこと。

有効候補であれば端点データを更新しMesh再生成を行い、Operatorを終了する。

---

## 15. Esc / 右クリック

以下でキャンセルする。

- Esc
- Right Mouse Button

キャンセル時：

- `jhm_wall.start` を変更しない
- `jhm_wall.end` を変更しない
- Meshを変更しない
- 壁厚を変更しない
- 壁高さを変更しない
- Object Transformを変更しない

完全に操作開始前の状態を維持する。

---

# Part D — 移動中に元Meshを変更しない

## 16. 非破壊プレビュー

モーダル移動中は、対象Wallの実Meshをリアルタイム更新しない。

理由：

- Escキャンセルを単純・安全にする
- 不完全な中間状態を作らない
- 毎MOUSEMOVEでMeshを再生成しない
- Undoや例外処理を簡潔にする

移動中はGPUプレビューのみを使用する。

---

## 17. 元Wall表示

元Wall Meshはモーダル中もそのまま表示してよい。

その上に、

- 固定点
- 移動候補
- 新しい壁芯候補線
- スナップハイライト
- アライメントガイド

をGPU描画する。

Build 03-Aでは元Meshを一時的に非表示にする必要はない。

---

# Part E — プレビュー

## 18. 基本プレビュー

端点移動中は、

`固定端点 ○────────○ 移動候補`

という壁芯線プレビューを表示する。

Build 02-Dの新規Wall作図と同じ視認性を基本とする。

- 前面表示
- GPUのみ
- screen pixel基準
- 細い壁芯線
- 円形端点マーカー

Object / Mesh / Curve / Emptyをプレビュー用に作成してはならない。

---

## 19. 固定端点

移動しない反対側端点を通常マーカーで表示する。

固定端点は移動操作中に座標変更しない。

---

## 20. 移動候補

現在の解決済み候補点を通常マーカーで表示する。

直接端点スナップ中はBuild 02-Cと同様に強調リングを使用する。

---

## 21. アライメントガイド

Build 02-Dと同じX/Yアライメントガイドを表示する。

- Xアライメント
- Yアライメント
- 参照端点ハイライト

を維持する。

Shift + X/Yアライメント時も既存仕様を維持する。

---

# Part F — スナップ・アライメント・Shift

## 22. 既存ルールを再利用する

端点編集でもBuild 02-Dまでと同じ解決規則を使用する。

主要定数：

- 直接端点スナップ:
  - 16 px
- X/Yアライメント:
  - 10 px
- Shift角度拘束:
  - 15°

これらの値をBuild 03-Aで変更しない。

---

## 23. 直接端点スナップ優先

優先順位はBuild 02-Dと同じ。

**直接端点スナップ ＞ X/Yアライメント / Shift複合処理 ＞ Shift単独 ＞ raw**

直接スナップ成立時は保存済み参照端点座標へ完全一致させる。

---

## 24. 対象Wall自身を参照候補から除外

これはBuild 03-Aで重要な追加条件である。

編集中のWall Object自身については、

- `jhm_wall.start`
- `jhm_wall.end`

の両方を、

**直接端点スナップ候補およびX/Yアライメント参照候補から除外する。**

理由：

- 自分自身の反対端へ直接スナップしてゼロ長Wallになることを避ける
- 自分自身の保存済み移動前端点へ吸着し続けることを避ける
- 自己参照による不自然なガイドを防ぐ

他のWallの端点だけを参照対象とする。

---

## 25. 非表示Wall除外

Build 02-C / 02-Dと同じく、

- 非表示Object
- 非表示Collection
- View Layer除外
- Local Viewで不可視
- 投影不能
- 画面外

の参照端点は候補外とする。

---

## 26. Shift押下・解放

移動中にShiftを押す・離すだけで、マウス移動なしでも最後のraw候補から即時再評価する。

Build 02-B以降の操作感を維持する。

---

## 27. Shift角度の基準点

端点移動時のShift角度拘束は、

**移動しない固定端点**

を基準とする。

例：

終点移動：

`fixed = wall.start`

始点移動：

`fixed = wall.end`

したがって、始点移動時は元のstart→end方向ではなく、

`fixed end -> moving start`

方向として15°拘束計算してよい。

最終的なWallの幾何形状として同じ15°系列になるため問題ない。

---

# Part G — 最小Wall長

## 28. 最小長

確定候補Cと固定端点Fについて、

`|C - F| > 1e-6 m`

を満たすこと。

Build 02-A以降と同じ技術的退化防止閾値とする。

---

## 29. 短すぎる場合

候補が最小長以下の場合は確定しない。

既存Wallを破壊せず、

`壁の長さが短すぎます。`

等の警告を表示し、モーダル操作を継続してよい。

---

# Part H — Source of Truth更新

## 30. 確定時のデータ更新

端点移動が正常確定した場合のみ、

始点移動：

`wall.start = final_candidate`

終点移動：

`wall.end = final_candidate`

とする。

反対端点は保存済み値を維持する。

---

## 31. exactness

直接端点スナップやX/Yアライメントが成立した場合、

保存されるstart/endは表示上近いだけでなく、

**参照元の保存済みX/Y値と数値的に一致**

すること。

---

## 32. Lengthは保存しない

Build 03-AでもWall Lengthプロパティを新設しない。

長さは常に、

`distance(start, end)`

から計算する。

---

# Part I — Mesh再生成

## 33. 再生成タイミング

Mesh再生成は左クリックで有効な端点移動を確定したときに1回だけ行う。

MOUSEMOVEごとに実Meshを再生成しない。

---

## 34. 再生成入力

再生成に使用する唯一の寸法入力は、

- 更新後 `start`
- 更新後 `end`
- 既存 `wall.wall_thickness`
- 既存 `wall.wall_height`

とする。

Mesh頂点から寸法や端点を推定しない。

---

## 35. 既存壁厚・高さ維持

Build 03-Aでは、

- `wall.wall_thickness`
- `wall.wall_height`

を変更してはならない。

例えば130 mm / 2500 mmのWallなら、端点移動後も130 mm / 2500 mmを維持する。

ユーザーが別値で作ったWallもその保存済み値をそのまま使う。

---

## 36. Wall Mesh生成式

Build 02-A以降の壁芯基準直方体生成式を維持する。

- start/end = 壁芯
- 壁厚 = 壁芯の両側へ半分ずつ
- Z = 0 から wall_height
- 長手方向への追加延長なし

Build 03-Aで接合用の端部延長・トリムを加えない。

---

## 37. Objectを維持する

端点移動後も同じWall Objectを維持する。

以下を勝手に新規Objectへ置換しない。

- Object identity
- Object name
- collection membership
- active/selection状態
- `jhm_wall` PropertyGroup

将来Wall同士の接続情報をObject参照で持てるようにするため、これは重要である。

---

## 38. Mesh datablock

実装上、

- 現在のMeshを安全に再構築する
- 新しいMesh datablockを作成して同じObjectへ差し替える

のどちらでもよい。

ただし以下を満たすこと。

- Wall Object自体は同じ
- 失敗時に壊れた空Meshを残さない
- 不要な孤立Mesh datablockを残さない
- 可能な範囲で既存material slots等を不必要に破壊しない

Build 03-Aの現在のWallは単純Meshであることを前提としてよい。

---

## 39. 原子的更新

可能な限り、

1. 新しいgeometryを計算
2. geometryが有効か確認
3. Mesh再生成
4. start/end更新
5. 完了

という順で処理する。

例外が発生した場合、可能な限り元Wallを有効な状態で維持する。

少なくとも、

- Wallデータだけ更新されMeshが古い
- Meshだけ更新されWallデータが古い

という不整合を残さないようにする。

---

# Part J — Transform policy

## 40. 正常な管理Wall

Build 02-A〜02-Dで通常生成されたWallは、Object Transformを使わず、保存済みworld-space start/endを基準にMeshが構築されている。

Build 03-Aもこの正常状態を前提とする。

---

## 41. 手動Object TransformがあるWall

ユーザーが管理WallをObject Modeで手動Move / Rotate / Scaleした場合、

保存済みworld-space `start/end` と見た目Meshが一致しなくなる可能性がある。

Build 03-Aではこの逆同期を実装しない。

安全のため、端点移動Operator開始時に対象WallのObject Transformを確認する。

以下から大きく外れている場合：

- location = (0, 0, 0)
- rotation = identity
- scale = (1, 1, 1)

**端点編集を拒否することを推奨する。**

警告例：

`このWallにはObject Transformがあります。Build 03-Aの端点編集対象外です。`

勝手にTransformを適用したり、start/endへ変換を焼き込んだりしない。

---

## 42. 数値誤差

identity判定は完全一致ではなく、小さなfloating-point誤差を許容してよい。

---

# Part K — Edit Modeで手動変更されたWall

## 43. 既知の不整合

Edit ModeでWall Mesh頂点を手動移動しても、

`jhm_wall.start/end`

は更新されない。

Build 03-Aでも自動検出・逆同期はしない。

---

## 44. 専用端点編集を使った場合

Edit Modeで見た目Meshだけ変更されたWallに対してBuild 03-Aの端点編集を実行した場合、

再生成のsource of truthはあくまで、

- 保存済みstart/end
- 保存済みthickness/height
- 今回確定した移動端点

である。

したがって、Edit Modeで加えた手動Mesh変更は再生成時に失われてよい。

これは仕様上正しい。

---

## 45. 今後の方針

ユーザーへは、管理Wallの形状変更には今後、

- `始点を移動`
- `終点を移動`
- 将来の壁厚/高さ編集

を使用する方針とする。

Meshから正規Wallデータを逆算する設計にはしない。

---

# Part L — Undo

## 46. Undo対応

端点移動OperatorはBlender Undoへ対応する。

Operator optionsは、

`REGISTER`, `UNDO`

を使用する。

---

## 47. Undo対象

確定後にCtrl+Zした場合、

最低限以下が操作前へ戻ること。

- Wall start
- Wall end
- Wall Mesh geometry

Wall thickness/heightはそもそも変更しない。

---

# Part M — 選択状態

## 48. 編集対象Wall

編集開始時のactive Wallを対象として固定する。

モーダル中に別Objectへ対象を切り替えない。

---

## 49. 確定後

確定後も編集対象Wallを、

- selected
- active

として維持する。

他Objectを新規選択しない。

---

## 50. キャンセル後

キャンセル時も元の対象Wallをactive/selectedとして維持することが望ましい。

---

# Part N — コード構成

## 51. 主な変更対象

Build 03-Aでは主に以下を変更する。

- `japanese_house_modeler/operators.py`
- `japanese_house_modeler/ui.py`
- `japanese_house_modeler/__init__.py`

---

## 52. properties.py

Build 03-Aでは新しい永続Propertyは原則不要。

以下を維持する。

- start
- end
- wall_thickness
- wall_height
- is_wall

したがって、

`japanese_house_modeler/properties.py`

は原則変更しない。

---

## 53. operators.py

以下を追加する。

- Wall端点移動Operator
- 確定時Wall Mesh再生成
- 必要な候補状態

Build 02-Dのスナップ・アライメント・描画処理を再利用する。

---

## 54. ui.py

`選択中の壁` セクションに、

- 始点を移動
- 終点を移動

を追加する。

既存の新規壁UIを壊さない。

---

## 55. __init__.py

新しいOperator classを `_CLASSES` へ登録するために必要な最小変更を行う。

`bl_info` versionはBuild 03-Aでは変更しなくてよい。

---

## 56. 共有処理

Build 02-Dのコードを大量コピーして端点移動Operatorを作ることは避ける。

必要であれば、以下を小さな共有helper / mixin / module-level functionへ整理してよい。

- XY平面交差
- visible Wall endpoint列挙
- direct snap
- X/Y alignment
- Shift constraint
- marker / guide描画
- wall geometry生成

ただし、

**Build 02-Dまでの新規Wall作図挙動を変えないこと**

を最優先とする。

---

## 57. リファクタリング範囲

Build 03-Aに必要な共有化は許容するが、

- 大規模ファイル分割
- 全面書き換え
- 命名総変更
- unrelated formatting
- 将来機能の先取り

はしない。

差分をレビュー可能な範囲に保つ。

---

# Part O — エラー処理

## 58. 対象Wall消失

モーダル中に何らかの理由で対象Wall Objectが削除・無効化された場合は、安全にキャンセルする。

Python例外をViewportへ放置しない。

---

## 59. Mesh再生成失敗

Mesh再生成に失敗した場合は、

- エラーをreport
- 壊れた状態を残さない
- Operatorを安全に終了

する。

---

## 60. XY交差不能

現在の視点でZ=0との交差を取得できない場合は、Build 02-Aと同等の扱いとする。

元Wallを変更しない。

---

# Part P — Blender実機テスト

## 61. テストA — 終点自由移動

1. Wallを1本作成
2. Wallを選択
3. `終点を移動`
4. マウスを自由な位置へ移動
5. GPUプレビューが表示
6. 左クリック
7. 終点が新位置へ移動
8. 始点は変化しない
9. Meshが新しいstart/endで再生成

---

## 62. テストB — 始点自由移動

テストAの始点版。

- 終点は固定
- 始点のみ更新

すること。

---

## 63. テストC — 直接端点スナップ

1. Wall AとWall Bを作る
2. Wall Aの終点編集
3. Wall Bの端点16 px以内へ近づける
4. `◎` ハイライト
5. 左クリック
6. Wall Aの編集端点がWall B保存端点へ完全一致

---

## 64. テストD — X/Yアライメント

1. 離れたWall端点を用意
2. 対象Wallの端点編集
3. 参照端点のXまたはYガイドへ近づける
4. ガイド表示
5. 左クリック
6. 保存座標が正確に一致

---

## 65. テストE — Shift + X/Y

1. 対象Wallの端点編集開始
2. Shiftで0° / 90°等へ拘束
3. 離れた既存Wall端点のX/Yガイドへ近づける
4. 角度拘束を維持したままアライメント
5. 確定

Build 02-Dと同じ複合挙動であること。

---

## 66. テストF — Shift即時更新

1. 端点編集中
2. マウスを停止
3. Shiftを押す
4. 候補が即座に15°拘束へ更新
5. Shiftを離す
6. 即座に自由/アライメント候補へ戻る

---

## 67. テストG — 自己スナップ除外

対象Wall自身の、

- 移動前端点
- 反対側端点

が直接スナップ/アライメント候補として強調されないこと。

特に反対端へ吸着してゼロ長Wallにならないこと。

---

## 68. テストH — 最小長

移動候補を固定端点と同じ位置へ近づける。

長さ `<= 1e-6 m` では確定しないこと。

既存Wallが消えたり壊れたりしないこと。

---

## 69. テストI — Esc

1. 端点編集
2. 大きく移動候補を動かす
3. Esc
4. start/endが操作前と同じ
5. Meshも操作前と同じ

---

## 70. テストJ — 右クリック

Escと同じ結果になること。

---

## 71. テストK — Ctrl+Z

1. 端点編集を確定
2. Meshと端点が変わったことを確認
3. Ctrl+Z
4. start/endとMeshが操作前へ戻る

---

## 72. テストL — 壁厚・高さ保持

例：

- thickness = 130 mm
- height = 2500 mm

のWall端点を移動。

確定後も、

- 130 mm
- 2500 mm

を維持する。

別の任意値でも同様。

---

## 73. テストM — active/selection維持

端点編集確定後も同じWallがselectedかつactiveであること。

---

## 74. テストN — 非表示Wall除外

非表示Wallの端点が、

- direct snap
- X alignment
- Y alignment

の参照候補にならないこと。

---

## 75. テストO — 元Meshの非破壊

端点編集開始後、確定前に元Wall Meshが実際には書き換えられていないこと。

Escで完全に元状態へ戻れることを確認する。

---

## 76. テストP — Edit Mode手動変更後

検証用として、

1. Wall MeshをEdit Modeで意図的に変形
2. Object Modeへ戻る
3. 専用端点編集を実行
4. 確定

再生成後は保存済みWallデータ＋今回編集した端点に基づく正常な直方体Wallへ戻ること。

Edit Mode変更を保存データへ逆同期しないこと。

---

## 77. テストQ — Object Transform異常

管理WallへObject Mode Transformを意図的に加えた場合、

Build 03-Aが採用するtransform policyに従い、安全に拒否されることを確認する。

勝手に異常なMeshを生成しないこと。

---

# Part Q — 回帰テスト

## 78. Build 02-D新規Wall作図

Build 03-A追加後も新規Wall作図について以下を確認する。

- 自由角度
- Shift 15°
- 直接端点スナップ16 px
- X/Yアライメント10 px
- アライメントガイド
- 参照端点ハイライト
- Shift + X/Y
- 矩形作図

---

## 79. Build 02-A〜02-C

以下も維持する。

- XY平面作図
- 壁芯基準Mesh
- Esc / 右クリック
- Undo
- selected/active
- 壁厚/高さスナップショット
- GPUプレビュー
- 非表示Wall除外
- 直接端点スナップ優先

---

# Part R — 完了条件

## 80. Build 03-A完了条件

Blender 5.2 LTS実機で以下を満たした時点でBuild 03-A完了とする。

- 選択Wallの始点だけを移動できる
- 選択Wallの終点だけを移動できる
- 反対端点は固定される
- 直接端点スナップ16 pxが利用できる
- X/Yアライメント10 pxが利用できる
- Shift 15°が利用できる
- Shift + X/Yが利用できる
- ガイド/ハイライトが表示される
- 対象Wall自身を参照候補にしない
- 確定時のみWallデータ更新
- 確定時のみMesh再生成
- 同じWall Objectを維持
- 壁厚・高さを維持
- Esc / 右クリックで完全キャンセル
- Ctrl+Zで元状態へ戻る
- 極小長Wallを作らない
- Object Transform異常時に安全に処理する
- Build 02-Dまでの新規Wall作図に回帰不具合がない

---

# Part S — 次段階

## 81. Build 03-B予定

Build 03-A完了後は、

**既存Wallの壁厚・壁高さ編集 + 対象Wallのみ再生成**

をBuild 03-Bとして検討する。

想定UI：

```text
選択中の壁

壁厚: [ 130.0 ] mm
壁高さ: [ 2500.0 ] mm

[ 始点を移動 ]
[ 終点を移動 ]
```

値変更時には、

`Wall data -> Mesh regenerate`

を維持する。

Build 03-Aでは壁厚・高さ編集を先取りしない。

---

## 82. その後

Wall編集基盤完成後に、

- Wall端点ごとの接続情報
- 接合する / しない
- T字接合
- 壁芯交点
- 出隅
- 入隅
- 壁厚を考慮した端部処理

へ進む。

Build 03-Aではこれらを実装しない。
