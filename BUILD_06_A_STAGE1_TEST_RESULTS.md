# Build 06-A Stage 1 実機テスト結果

- 対象: Blender 5.2 LTS
- Build: 06-A Stage 1
- 判定: **PASS**
- 例外: LEFT側から開始したFinishのオフセット方向問題は既知FAILとしてStage 2へ持ち越し

## 実機確認結果

| 項目 | 結果 |
|---|---|
| Wall生成 | PASS |
| RIGHT側Finish生成 | PASS |
| 壁厚変更時のFinish追従 | PASS |
| 壁高変更時のFinish維持 | PASS |
| 始点・終点の延長 | PASS |
| 始点・終点の短縮 | PASS |
| Wall編集時のUndo / Redo | PASS |
| Finish側からのT字接続安全拒否・rollback | PASS |
| T字接続によるWall split | PASS |
| FinishRunを1本維持したままSpan 1→2 remap | PASS |
| split後の片側Wall延長・短縮へのFinish追従 | PASS |
| split後のUndo / Redo | PASS |
| UI「壁を削除」によるWall削除 | PASS |
| Wall削除時のFinish Span 2→1更新 | PASS |
| 削除Wall側へのFinish橋渡し・残骸なし | PASS |
| 削除後のUndo / Redo | PASS |
| Object Location変更後「管理状態へ復元」 | PASS |
| Object Rotation変更後「管理状態へ復元」 | PASS |
| Object Scale変更後「管理状態へ復元」 | PASS |
| 復元後のWall topology / Finish再構築 | PASS |
| 復元操作のUndo / Redo | PASS |
| .blend保存 → Blender完全終了 → 再読込 | PASS |
| 再読込後のWall / Topology / Finish管理情報維持 | PASS |
| 再読込後の始点・終点編集とFinish追従 | PASS |
| 再読込後の接続解除 → 再接続 → 再split | PASS |
| 再読込後のFinish Span 1→2再構築 | PASS |
| 再読込後のUndo / Redo | PASS |
| Wallマテリアル保持 | PASS |

## 確認した主要挙動

### Finish依存再構築
RIGHT側Finishについて、Wallの壁厚・壁高変更、始点・終点の延長・短縮に追従することを確認した。Finishの重複生成、不要オブジェクト生成、エラーは発生しなかった。

### split / remap
既存Wallの途中へFinish反対側から枝Wallを接続すると、主Wallは2本へsplitされ、枝Wallを含めWallは3本となった。`JHM Finish`は1オブジェクトのまま維持され、Finish区間数は1から2へ更新された。split点でFinishは途切れず、60×10断面も維持された。

split後に一方の主Wallだけを延長・短縮しても、そのSpanだけが追従し、反対側Spanおよびsplit位置は正常に維持された。

### Wall削除
アドオンUIの「壁を削除」を使用。split後の片側Wallを削除すると、該当Spanのみ削除され、Finish区間数は2から1へ更新された。削除Wall側への橋渡し、空中Finish、二重化は発生しなかった。

削除後にCorner形状へ再構築された際、Finish終端が表示メッシュ外端より内側に見える状態を確認した。これはcanonicalな接続点を基準としているためと推定し、Stage 1の依存管理テストとしては許容する。最終的なCorner surface extension / trimは後続Stageで扱う。

### 管理状態へ復元
WallにBlender標準Object Transformを与えた後、「管理状態へ復元」で保存済みcanonical情報から元状態へ復元できることを確認した。

- Location変更
- Rotation変更
- Scale変更

の3系統すべてで、Wall、接続Topology、Finishが元状態へ戻り、TransformはLocation=0 / Rotation=0 / Scale=1へ復元された。Undo / Redoも正常。

### 保存・再読込
`.blend`保存後にBlenderを完全終了し、再起動して再読込した。

Wall位置・形状、Topology、FinishRun/Span、Finish形状、管理状態、マテリアルが保持された。さらに再読込後もWall編集、Finish追従、接続解除・再接続、再split、Undo / Redoが正常に機能した。

## 既知FAIL / Stage 2持ち越し

### LEFT側Finishオフセット方向
LEFT側からFinishを開始すると、Verification ProfileがWall外側ではなくWall内部へ約10 mm入る。

- Stage 1では既知FAILとして受入対象外
- RIGHT側Finishでは今回のStage 1実機テストを完了
- LEFT/RIGHTの面オフセット方向およびSurface Resolver系の修正はStage 2で実施する

## Stage 1 結論

Build 06-A Stage 1の主要目的である、WallとFinishの依存関係、split/remap、削除追従、transaction/rollback、管理状態復元、Undo/Redo、保存・再読込後の永続性について、Blender 5.2 LTS実機で受入条件を満たした。

**Stage 1: PASS**
