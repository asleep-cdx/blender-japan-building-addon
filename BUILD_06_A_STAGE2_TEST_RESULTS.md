# Build 06-A Stage 2 実機テスト結果

- 対象: Blender 5.2 LTS
- Build: 06-A Stage 2 — Path Boundary & Profile Geometry
- Stage 2開始基準: `e73c9f542667c1a0ac03c5a0b3083c36b66390be`
- 最終実機テスト版: `Japanese_House_Modeler_Build_06_A_Stage2_Blender52_Acceptance_v3.zip`
- 判定: **PASS**

## 実装・自動テスト

Codex実装では、Stage 2としてcanonical endpoint reach、traversal-aware transition、FinishRun start/end blocker safety、single-Span blocker safety、LEFT/RIGHT × FORWARD/REVERSEのProfile orientationを追加した。

静的レビュー後、以下を追加修正した。

- endpoint reach用Wall長をXYZ距離ではなくXY canonical centerline lengthへ統一
- endpoint blocker thicknessをfiniteかつ正値に限定
- mirrored Verification ProfileのwindingをBlender 5.2 runtimeで正しい向きへ統一

Codex最終報告:

- `python -m unittest discover -s tests -v` — **159 tests passed**
- `python -m compileall -q japanese_house_modeler tests` — PASS
- `git diff --check` — PASS

最終 `tests/test_build_06_a.py` のStage 2差分は、Stage 1基準に対して **+74 / -3**。

## Blender 5.2 LTS 実機確認結果

| 項目 | 結果 |
|---|---|
| LEFT + FORWARD Profile外向き10 mm | PASS |
| RIGHT + FORWARD Profile外向き10 mm | PASS |
| LEFT + REVERSE Profile外向き10 mm | PASS |
| RIGHT + REVERSE Profile外向き10 mm | PASS |
| Profile高さ +60 mm world-up | PASS |
| Positive / Negative Profile Face Orientation | PASS |
| 水平Wall LEFT / RIGHT | PASS |
| 垂直Wall LEFT / RIGHT | PASS |
| 斜めWall LEFT / RIGHT | PASS |
| 90° Corner LEFT / RIGHT | PASS |
| REVERSE 2-Span Corner | PASS |
| 斜めCorner / oblique miter | PASS |
| unequal thickness Corner 130 / 250 mm | PASS |
| Cornerで隙間・重なり・異常突出なし | PASS |
| FinishRun終端 single-Span blocker occupied side拒否 | PASS |
| FinishRun終端 opposite side許可 | PASS |
| FinishRun開始端 single-Span blocker occupied side拒否 | PASS |
| FinishRun開始端 opposite side許可 | PASS |
| T字junction occupied side拒否 | PASS |
| T字junction opposite side許可 | PASS |
| Cross junction LEFT / RIGHT拒否 | PASS |
| non-reciprocal geometric crossingをblocker扱いしない | PASS |
| partial Span 75%でjunction接続を拒否 | PASS |
| partial Spanをjunctionまで自動延長しない | PASS |
| `DISTANCE_FROM_START = Wall length` をendpoint到達として許可 | PASS |
| `DISTANCE_FROM_END = 0` をEND到達として許可 | PASS |
| endpoint reach失敗時に既存Finishを破壊しない | PASS |
| Wall始点・終点の延長・短縮へのFinish追従 | PASS |
| Wall編集時のUndo / Redo | PASS |
| split/remap: Finish Span 1→2 | PASS |
| split後の片側Wall編集への該当Span追従 | PASS |
| split位置・反対側Span維持 | PASS |
| UI「壁を削除」: Span 2→1 | PASS |
| Wall削除後のUndo / Redo | PASS |
| `.blend`保存 → Blender完全終了 → 再読込 | PASS |
| 再読込後のWall / Topology / Finish保持 | PASS |
| 再読込後のWall編集とFinish追従 | PASS |
| Finish重複・不要残骸なし | PASS |
| 管理状態正常 | PASS |

## Profile orientation修正履歴

初回Stage 2実装ではProfileの外向き方向自体は修正されたが、RIGHT側のVerification ProfileでFace Orientation反転を確認した。

- v1: LEFT正常 / RIGHT法線反転
- v2: windingを誤った向きへ統一したためLEFT / RIGHTとも法線反転
- v3: 初回runtimeで正常だったNegative ProfileのwindingへPositive / Negative双方を統一
- v3実機結果: LEFT / RIGHTともFace Orientation正常

最終Profile geometry:

- Positive: `(0,0) → (0,+60) → (+10,+60) → (+10,0)` mm
- Negative: `(0,0) → (-10,0) → (-10,+60) → (0,+60)` mm

投影方向10 mmと高さ+60 mmは維持される。

## canonical endpoint reach / partial Span

通常UIではpartial boundaryを直接指定できないため、Blender Python Consoleからcanonical FinishSpan boundaryを変更して実機確認した。

### partial endpoint

最初のSpanのexitをWall長の75%へ変更した状態で再生成すると、

`ValueError: FinishSpanが接続Wall端点まで到達していません。`

として安全に拒否された。

既存Finishは破壊されず、junctionまで自動延長もされなかった。

### numeric endpoint

以下は正常に許可された。

- `DISTANCE_FROM_START = Wall length`
- `DISTANCE_FROM_END = 0`

boundary kindが`WALL_END`でなくても、canonical centerline distanceが実endpointへ一致すれば到達として扱われることを確認した。

## blocker safety

FinishRunの内部transitionだけでなく、first / last boundary、およびsingle-Spanの両端でblocker safetyが機能することを確認した。

- occupied sideは生成拒否
- opposite sideは生成許可
- Crossでは両側拒否
- reciprocal topologyを持たない単なる幾何学crossingは無視

拒否時にFinish残骸やWall変更は発生しなかった。

## Stage 1回帰

Stage 2実装後も、Stage 1で確定した依存管理を短縮回帰セットで再確認した。

- Wall endpoint編集
- split/remap
- split後の片側Wall編集
- UI Wall削除
- Undo / Redo
- 保存 / 完全終了 / 再読込
- 再読込後のWall編集とFinish追従

すべてPASS。

## 追加確認

ユーザー作成のCurve Profileを手動でBevel Objectへ適用し、斜めCornerでpath / miter geometryが追従することを確認した。

これは将来のProfile Library / managed Profile機能の正式acceptanceではなく、path geometryに関する参考確認とする。

## 後続改良項目

### FinishデフォルトのFlat Shade

現状の生成FinishはSmooth Shade表示になる。巾木・廻り縁ではFlat Shadeの使用頻度が高いため、将来のFinish / Profile改良では以下を要望とする。

- BASEBOARD / CROWN等の生成FinishはデフォルトFlat Shade
- 必要な場合にユーザーがSmoothへ変更可能

Stage 2のPath Boundary & Profile Geometry受入条件とは別項目のため、今回のPASS判定には含めない。

### Corner surface extension / trim

Stage 1から継続管理している、single-Span終端がCorner化した場合の最終的なsurface extension / trim品質については、今回のStage 2 PASSとは別に後続実装で最終品質を確認する。

## Stage 2 結論

Build 06-A Stage 2の主要目的である、

- canonical endpoint reach
- partial interval semantics preservation
- traversal-aware transition
- FinishRun start/end blocker safety
- single-Span blocker safety
- side × traversal 4方向の外向きProfile
- +60 mm world-up
- Profile Face Orientation
- 90° / oblique / unequal-thickness miter
- Stage 1 dependency transaction回帰

について、Blender 5.2 LTS実機で受入条件を満たした。

**Stage 2: PASS**
