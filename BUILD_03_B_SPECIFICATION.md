# 日本住宅モデラー — Build 03-B Specification

## 1. 目的

Build 03-Bでは、既存の日本住宅モデラー管理Wallについて、**保存済みの壁厚・壁高さを専用UIから変更し、同じWall ObjectのMeshを保存済みWallデータから再生成する機能**を実装する。

Build 03-Aで確立した、

`Wall data -> Mesh regenerate`

という編集方針を、端点だけでなく壁厚・壁高さにも適用する。

Build 03-B完了後、管理Wallの基本編集は以下を専用機能で行える状態になる。

- 始点を移動
- 終点を移動
- 壁厚を変更
- 壁高さを変更

Meshを正規データとして扱わず、以下を引き続きsource of truthとする。

- `jhm_wall.start`
- `jhm_wall.end`
- `jhm_wall.wall_thickness`
- `jhm_wall.wall_height`

Build 03-Bでは、壁同士の接合、出隅・入隅、T字接合などは実装しない。

---

## 2. 基準状態

Build 03-BはGitHub `main` の以下を基準とする。

- `b9851ef Implement Build 03-A wall endpoint editing`

Build 03-AまでBlender 5.2 LTS実機テスト済み。

現在の主要仕様：

- Blender 5.2 LTS
- UI寸法単位: mm
- Mesh座標: m
- 壁芯基準
- 1 Wall = 1 Blender Object
- 新規壁デフォルト壁厚: 130 mm
- 新規壁デフォルト壁高さ: 2500 mm
- 直接端点スナップ: 16 px
- X/Yアライメント: 10 px
- Shift角度拘束: 15°
- 既存Wall端点編集: Build 03-Aで実装済み

---

## 3. 親仕様

以下を前提とする。

- `SPECIFICATION.md`
- `BUILD_02_A_SPECIFICATION.md`
- `BUILD_02_B_SPECIFICATION.md`
- `BUILD_02_C_SPECIFICATION.md`
- `BUILD_02_D_SPECIFICATION.md`
- `BUILD_03_A_SPECIFICATION.md`

Build 03-BはBuild 03-Aまでの挙動を壊してはならない。

---

# Part A — Build 03-Bの範囲

## 4. 実装する機能

Build 03-Bでは以下を実装する。

- 選択中Wallの壁厚変更
- 選択中Wallの壁高さ変更
- 壁厚・壁高さを同時に編集できるダイアログ
- ダイアログ開始時に現在値を読み込む
- OK時のみ保存値を更新
- OK時のみMesh再生成
- Cancel時は完全に無変更
- 同じWall Objectを維持
- `start/end`を変更しない
- Material slotを可能な範囲で維持
- selected / active状態を維持
- Ctrl+Z対応
- Object TransformがidentityでないWallを安全に拒否
- Edit Modeで手動変形されたMeshを保存済みWallデータから正常形状へ再生成
- 既存03-A端点編集UIを維持
- 新規Wall作図機能を維持

---

## 5. 実装しない機能

以下はBuild 03-Bでは実装しない。

- start/endの数値入力編集
- Wall全体移動
- Object Transform同期
- Edit Mode MeshからWallデータへの逆同期
- 壁途中の編集
- 壁接合
- T字接合
- 十字接合
- 出隅
- 入隅
- 壁厚を考慮した接合部トリミング
- 壁自動延長
- 接合する/しない属性
- 開口
- ドア
- 窓
- 床
- 天井
- 部屋認識
- 間取り図AI解析

---

# Part B — UI設計

## 6. 選択中Wall UI

既存の、

`日本住宅 > 日本住宅モデラー > 選択中の壁`

を拡張する。

Build 03-A時点では概ね、

```text
選択中の壁

壁厚: 130.0 mm
壁高さ: 2500.0 mm

[ 始点を移動 ]
[ 終点を移動 ]
```

となっている。

Build 03-Bでは以下とする。

```text
選択中の壁

壁厚: 130.0 mm
壁高さ: 2500.0 mm

[ 壁寸法を変更 ]

[ 始点を移動 ]
[ 終点を移動 ]
```

---

## 7. なぜ直接Propertyを編集しないか

Build 03-Bでは、N-panel上で `jhm_wall.wall_thickness` / `wall_height` を直接編集して即座にPropertyだけ変更する方式は採用しない。

理由：

- Propertyだけ先に変わりMeshが古い状態になる時間を作らない
- Mesh再生成に失敗した場合のロールバックを簡潔にする
- Cancel時に完全無変更とする
- Undo境界を明確にする
- `Wall data -> Mesh` の原子的更新を維持する

そのため、**「壁寸法を変更」ボタンから専用Operatorダイアログを開き、OK時にまとめて反映**する。

---

## 8. 壁寸法変更ダイアログ

`壁寸法を変更` を押すと小さなダイアログを開く。

表示例：

```text
壁寸法を変更

壁厚 (mm):   [ 130.0 ]
壁高さ (mm): [ 2500.0 ]

          [キャンセル] [OK]
```

Blenderの標準 `invoke_props_dialog` 等を使用してよい。

---

## 9. 初期値

ダイアログを開いた時点で、選択Wallの保存済み値を読み込む。

- thickness = `wall.wall_thickness`
- height = `wall.wall_height`

新規壁用デフォルト値 `context.scene.jhm_new_wall_defaults` を使用してはならない。

既存Wall編集では、そのWall自身の現在値を編集する。

---

# Part C — Operator

## 10. 推奨Operator

新しいOperatorを追加する。

例：

`JHM_OT_edit_wall_dimensions`

bl_idname例：

`jhm.edit_wall_dimensions`

名称は多少異なってよいが、責務が明確であること。

---

## 11. Operator options

Undoへ対応する。

推奨：

`bl_options = {"REGISTER", "UNDO"}`

または、Redo挙動を安全に実装しない場合は、少なくとも `UNDO` に対応する適切な構成とする。

最重要要件は、

**確定した1回の寸法変更をCtrl+Zで完全に戻せること。**

---

## 12. 対象Wall

Operator開始時のactive管理Wallを対象として固定する。

対象条件：

- 3D View
- Object Mode
- active objectあり
- `active_object.jhm_wall.is_wall == True`

管理Wall以外では実行しない。

---

## 13. ダイアログ中の対象切替

ダイアログを開いた後に対象Wallを曖昧にしない。

実装上可能であれば、invoke時に対象Objectを保持し、execute時も同じObjectへ適用する。

対象Objectが削除された場合は安全にキャンセルする。

別Wallへ誤適用してはならない。

---

# Part D — 編集値

## 14. 壁厚

編集値はmm。

現在のProperty制約と同じ範囲を維持する。

- minimum: `0.1 mm`
- maximum: `10,000.0 mm`

通常値は130 mmだが、130 mmへ固定しない。

ユーザーが任意の有効値へ変更できる。

---

## 15. 壁高さ

編集値はmm。

現在のProperty制約と同じ範囲を維持する。

- minimum: `0.1 mm`
- maximum: `100,000.0 mm`

通常値は2500 mmだが、2500 mmへ固定しない。

---

## 16. 表示精度

既存Propertyと同様に、

`precision=1`

相当を基本とする。

例：

- 130.0 mm
- 105.0 mm
- 2500.0 mm

---

## 17. 同時編集

1回のダイアログで、

- 壁厚だけ変更
- 壁高さだけ変更
- 両方変更

のすべてを許可する。

---

# Part E — OK / Cancel

## 18. Cancel

ダイアログでCancelした場合：

- `wall.wall_thickness`を変更しない
- `wall.wall_height`を変更しない
- `wall.start`を変更しない
- `wall.end`を変更しない
- Meshを変更しない
- Object Transformを変更しない

完全に無変更とする。

---

## 19. OK

OK時に初めて最終値を確定する。

処理対象：

- current saved start
- current saved end
- dialog thickness
- dialog height

これらから新しいWall geometryを計算する。

---

## 20. 同じ値でOK

壁厚・高さが両方とも現在値と同一の場合は、

- 何も変更せずFINISHED
- または同じgeometryを再生成

のどちらでも動作上は許容する。

ただし不要なMesh datablock生成を避けるため、**変更なしなら再生成せず終了する実装を推奨**する。

---

# Part F — Source of Truth

## 21. 正規データ

Build 03-Bでも正規データは以下のみ。

- `wall.start`
- `wall.end`
- `wall.wall_thickness`
- `wall.wall_height`

Meshは正規データではない。

---

## 22. start/end

壁寸法変更では、

- `wall.start`
- `wall.end`

を一切変更しない。

保存済みworld-space端点をそのまま使用する。

---

## 23. Length

Length Propertyを追加しない。

壁長は常に、

`distance(start, end)`

から計算する。

---

## 24. wall_thickness / wall_height

OK成功時のみ、新しい値を保存する。

```text
wall.wall_thickness = new_thickness
wall.wall_height = new_height
```

Mesh再生成とデータ更新のどちらかだけが成功した不整合状態を残さないこと。

---

# Part G — Mesh再生成

## 25. geometry入力

再生成は必ず、

- saved start
- saved end
- new thickness
- new height

から行う。

Mesh頂点からstart/endや寸法を推定しない。

---

## 26. 壁芯

既存仕様どおり、start/endは壁芯。

壁厚は壁芯の両側へ半分ずつ。

例：

130 mm壁厚

→ 壁芯から左右へ65 mm

---

## 27. 高さ

Z方向：

- bottom = 0 m
- top = `wall_height / 1000`

とする。

---

## 28. 長手方向

start/end位置を正確なWall端点とし、長手方向への追加延長を行わない。

接合処理は後続Build。

---

## 29. Mesh再生成回数

ダイアログ内で値を入力している途中に実Meshを変更しない。

OK確定時だけ1回再生成する。

---

## 30. Object identity

再生成後も同じWall Objectを維持する。

変更してはならないもの：

- Object identity
- Object name
- collection membership
- `jhm_wall` PropertyGroup
- start/end
- Object Transform

---

## 31. Mesh datablock

Build 03-Aと同様に、新しいMesh datablockを作成して同じWall Objectへ割り当てる方式を使用してよい。

または安全に既存Meshを再構築してもよい。

重要なのはWall Objectを置換しないこと。

---

## 32. Material slot

Build 03-Aと同様に、既存MeshのMaterial slotを可能な範囲で新Meshへ引き継ぐ。

Build 03-BではUVや複雑なMesh attribute保存機構までは要求しない。

---

## 33. 古いMesh

新Meshへの切替成功後、古いMeshのusersが0なら削除してよい。

不要な孤立Mesh datablockを増やさない。

---

# Part H — 原子的更新とロールバック

## 34. 基本処理順

推奨順：

1. 対象Wallと入力値を検証
2. saved start/endを読む
3. new geometryを計算
4. new Mesh datablockを構築
5. new Meshが正常であることを確認
6. 同じWall Objectへnew Meshを割り当て
7. wall_thickness / wall_heightを更新
8. 成功確定
9. old Meshを必要なら削除

---

## 35. 失敗時

途中で例外が発生した場合、

- 元Meshへ戻す
- 元wall_thicknessへ戻す
- 元wall_heightへ戻す
- start/endはそもそも変更しない
- 作成途中のnew Meshを削除
- エラーをreport

する。

---

## 36. 不整合禁止

以下の状態を残してはならない。

### NG例1

```text
Property: thickness 180 mm
Mesh: thickness 130 mm
```

### NG例2

```text
Property: height 3000 mm
Mesh: height 2500 mm
```

PropertyとMeshは同じ確定操作で同期させる。

---

# Part I — 既存Build 03-Aとの共有

## 37. geometry処理

Build 03-Aの端点編集とBuild 03-Bの寸法編集は、同じ壁芯直方体生成規則を使用する。

可能であれば、既存 `_wall_geometry` 相当の処理を小さく共有化してよい。

例：

```python
wall_geometry(start, end, thickness_mm, height_mm)
```

---

## 38. 共有化の条件

共有化する場合でも、

- Build 02-D新規Wall作図
- Build 03-A端点編集

の実機テスト済み挙動を変えない。

既存コードを大規模に書き換えない。

---

## 39. Mesh置換処理

Build 03-Aの `_commit_endpoint` とBuild 03-BでMesh置換コードが大きく重複する場合、小さなprivate helperへ共有化してよい。

ただしロールバック、Material slot維持、Object identity維持を壊さないこと。

---

## 40. 不要なリファクタリング禁止

以下は禁止。

- operators.py全面書き換え
- 大規模class hierarchy変更
- ファイル分割
- unrelated formatting
- 既存名称の総変更

Build 03-Bに必要な最小差分を優先する。

---

# Part J — Transform policy

## 41. Object Transform identity

Build 03-Aと同じ方針を使用する。

管理WallにObject Modeで、

- Move
- Rotate
- Scale

が適用され、identityから許容誤差以上外れている場合は、壁寸法編集を安全に拒否する。

---

## 42. 拒否時

警告例：

`このWallにはObject Transformがあります。壁寸法編集の対象外です。`

以下を行わない。

- Transform自動適用
- start/endへの焼き込み
- Mesh再生成
- Property変更

---

## 43. Transform判定共有

Build 03-Aの `_has_identity_transform` 相当の判定を再利用してよい。

同じ許容誤差を維持する。

---

# Part K — Edit Modeで変更されたMesh

## 44. 手動Mesh変更

Edit Modeで管理Wall Meshを手動変形しても、Wallデータには逆同期しない。

これはBuild 03-Aと同じ。

---

## 45. 壁寸法変更を適用した場合

Edit Modeで見た目Meshを変形したWallに対して、

`壁寸法を変更`

を実行しOKした場合、

以下から正常な直方体Wallへ再生成する。

- saved start
- saved end
- new thickness
- new height

Edit Modeの手動変形は失われてよい。

これは仕様上正しい。

---

# Part L — Undo

## 46. Ctrl+Z

寸法変更確定後にCtrl+Zした場合、少なくとも以下が操作前へ戻る。

- wall.wall_thickness
- wall.wall_height
- Wall Mesh geometry

---

## 47. start/end

寸法変更ではstart/endは変更しないため、Undo前後とも同じ値である。

---

# Part M — 選択状態

## 48. 確定後

寸法変更後も対象Wallを、

- selected
- active

として維持する。

---

## 49. Cancel後

Cancel時も対象Wallをselected / activeのまま維持することが望ましい。

---

# Part N — ファイル変更

## 50. 主な変更対象

Build 03-Bの主な変更対象：

- `japanese_house_modeler/operators.py`
- `japanese_house_modeler/ui.py`
- `japanese_house_modeler/__init__.py`

---

## 51. properties.py

既存の永続Propertyはすでに必要なものを持っている。

- wall_thickness
- wall_height

そのため `properties.py` は原則変更しない。

既存のmin/max/defaultを変更しない。

---

## 52. __init__.py

新しい寸法編集Operatorを登録するための最小変更のみ。

`bl_info` version変更はBuild 03-Bでは不要。

---

# Part O — 実機テスト

## 53. テストA — 壁厚のみ変更

1. 130 mm Wallを作成
2. Wall選択
3. `壁寸法を変更`
4. 壁厚を180 mmへ変更
5. 高さ2500 mmはそのまま
6. OK
7. UIが180.0 mm表示
8. Mesh実厚が180 mm
9. start/end位置は不変
10. heightも2500 mm

---

## 54. テストB — 壁高さのみ変更

1. 2500 mm Wall
2. 高さを3000 mmへ変更
3. OK
4. wall_height = 3000 mm
5. Mesh高さ = 3000 mm
6. thickness不変

---

## 55. テストC — 両方変更

例：

- thickness: 130 → 150 mm
- height: 2500 → 2700 mm

両方が同じOK操作で反映される。

---

## 56. テストD — Cancel

1. `壁寸法を変更`
2. 値を大きく変更
3. Cancel
4. Property無変更
5. Mesh無変更

---

## 57. テストE — Ctrl+Z

1. 壁厚/高さ変更をOK
2. 変更を確認
3. Ctrl+Z
4. Propertyが元値へ戻る
5. Meshも元形状へ戻る

---

## 58. テストF — 端点保持

寸法変更前後で、

- wall.start
- wall.end

が完全に同じであること。

壁芯線位置や壁長を勝手に変更しない。

---

## 59. テストG — Object identity

寸法変更前後で同じWall Objectであること。

Object名が変わらないこと。

Collection所属が変わらないこと。

---

## 60. テストH — Material slot

WallへMaterialを1つ設定してから寸法変更。

変更後もMaterial slotが残ること。

---

## 61. テストI — Edit Mode手動変形後

1. Wallを作る
2. Edit ModeでMesh頂点を意図的に変形
3. Object Modeへ戻る
4. `壁寸法を変更`
5. 例えば壁厚130→160 mm
6. OK
7. saved start/endを基準とした正常な直方体Wallへ戻る
8. thickness 160 mmになる

---

## 62. テストJ — Object Transform異常

1. Object ModeでWallをMove/Rotate/Scale
2. `壁寸法を変更`
3. 安全に拒否
4. Mesh/Property無変更

---

## 63. テストK — 03-A端点編集回帰

Build 03-B追加後も、

- 始点を移動
- 終点を移動
- direct snap
- X/Y alignment
- Shift
- Undo

が正常に動くこと。

---

## 64. テストL — 新規Wall回帰

Build 02-Dまでの新規Wall作図：

- 自由角度
- Shift 15°
- direct snap 16 px
- X/Y alignment 10 px
- guide
- 矩形作図

が壊れていないこと。

---

## 65. テストM — 任意寸法Wall

デフォルト130/2500以外のWallでも正しく編集できること。

例：

- thickness 105 mm
- height 2400 mm

から、

- thickness 135 mm
- height 2650 mm

へ変更。

---

# Part P — 完了条件

## 66. Build 03-B完了条件

Blender 5.2 LTS実機で以下を満たした時点でBuild 03-B完了とする。

- 選択Wallから壁寸法変更ダイアログを開ける
- 現在の壁厚・高さが初期値になる
- 壁厚だけ変更できる
- 壁高さだけ変更できる
- 両方同時変更できる
- Cancelで完全無変更
- OK時だけProperty更新
- OK時だけMesh再生成
- start/endを変更しない
- 同じWall Objectを維持
- Material slotを維持
- Ctrl+ZでPropertyとMeshが戻る
- Object Transform異常時は安全に拒否
- Edit Mode手動Mesh変更をsource of truthにしない
- Build 03-A端点編集に回帰不具合がない
- Build 02-Dまでの新規作図に回帰不具合がない

---

# Part Q — Build 03-B後

## 67. 基本Wall編集基盤完成

Build 03-B完了時点で、管理Wallは専用UIから、

- 始点
- 終点
- 壁厚
- 壁高さ

という主要な正規データを編集し、Meshへ再生成できる。

ここまでをWall編集基盤の第一段階完了とする。

---

## 68. 次段階候補

次はWall同士の**接続情報**を設計する。

重要なのは、接続をWall単位の1フラグではなく、

- START endpoint
- END endpoint

ごとに管理できる構造とすること。

将来候補：

- endpoint connection record
- 接続対象Wall
- 接続対象endpointまたは交点
- 接合する / しない
- corner / T / cross
- 出隅 / 入隅
- 壁厚を考慮したMesh端部処理

Build 03-Bではこれらを先取り実装しない。
