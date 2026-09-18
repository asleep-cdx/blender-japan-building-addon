# Japanese House Modeler — Development Workflow

Version: 0.2 (draft)

この文書は Japanese House Modeler（JHM）の開発・レビュー・Blender runtime test・Codex Cloud利用時の共通運用ルールを記録する。

目的は、チャットや担当セッションが変わった場合でも、開発環境・役割分担・テスト方法・GitHub運用を誤解せず継続できるようにすることである。

この文書は機能仕様そのものではない。

- ROADMAP: 何をどの順番で作るか
- SPECIFICATION: 各Build / Stageをどう実装するか
- DEVELOPMENT_WORKFLOW: どう開発・テスト・同期・アーカイブするか
- ACCEPTANCE_RECORD: 実際に何をテストし、何が受入済みか

機能仕様については各BuildのSPECIFICATION、開発順序についてはROADMAP、受入結果については各ACCEPTANCE_RECORDを正とする。

---

# 1. 開発環境

## Blender

対象:

```text
Blender 5.2 LTS
```

Japanese House Modeler は Blender 5.2 LTS を基準として開発・runtime testを行う。

## ユーザー環境

主な開発・テスト環境:

```text
Windows 11
Google Chrome
Blender 5.2 LTS
```

ユーザーPCには原則として以下をインストールしていない:

```text
Codex CLI
Codex Desktop
ChatGPT Desktop App
```

CodexはChatGPT / Codex CloudをGoogle Chromeから使用する。

---

# 2. 開発時の役割分担

基本的な役割は以下とする。

```text
GPT
├─ Roadmap検討
├─ Specification作成・レビュー
├─ Codexへの実装指示作成
├─ コード構造・差分レビュー
├─ Blender runtime test設計
├─ Console確認コマンド作成
└─ Acceptance判断

Codex Cloud
├─ 実装
├─ automated / pure Python tests
├─ compileall
├─ git diff --check
└─ 指示された範囲のGit操作

ユーザー
├─ GitHub / PR操作
├─ Windows CMDでのlocal repository同期
├─ Candidate ZIP / ACCEPTED ZIP作成
├─ BlenderへのCandidate導入
├─ Blender 5.2 LTS runtime test
├─ UI操作
├─ Python Console実行
└─ スクリーンショット・結果の報告
```

Codexのautomated test結果をBlender runtime evidenceとして扱ってはならない。

---

# 3. Codex Cloud利用上の重要事項

## GitHub接続

このプロジェクトではCodex CloudからGitHubへの直接アクセスでHTTP 403が発生することがある。

既知の例:

```text
git clone https://github.com/...
fatal: unable to access ...
CONNECT tunnel failed, response 403
```

したがって、Codex Cloudへ安易に以下を要求しない。

```text
fresh git clone
GitHubへの直接fetchを必須とする処理
remote-tracking branchの存在を前提とする処理
```

まず既存Codex workspaceの状態を確認する。

なお、これはユーザーのWindows PC / Chrome側のGitHubアクセス制限とは区別する。
Windows側のlocal repositoryでは、従来どおりgit fetch / git pullを使用する。

## Commit SHAが異なる場合

Codex Cloud workspaceのcommit SHAとGitHub上のruntime-tested revisionのcommit SHAが異なっていても、ただちに別コードと判断しない。

squashや異なるcommit履歴によって、同一内容でもcommit SHAが異なる場合がある。

その場合はGit tree SHAを比較する。

Codex側:

```bash
git rev-parse HEAD
git rev-parse HEAD^{tree}
git status --short
```

GitHub側の対象revisionのtree SHAと比較し、

```text
local tree SHA
==
runtime candidate tree SHA
```

ならrepository内容は同一と扱える。

Acceptance Recordには必要に応じて以下を分けて記録する。

```text
runtime-tested commit SHA
runtime-tested tree SHA
automated-tested local commit SHA
automated-tested tree SHA
```

---

# 4. Codexへの指示原則

実装指示では変更対象と変更禁止範囲を明確にする。

テストだけを依頼する場合は必ず、次のような禁止事項を明記する。

```text
production codeを変更しない
testsを変更しない
documentationを変更しない
失敗時に自動修正しない
commitしない
pushしない
```

テスト失敗時は、

```text
失敗を確認
↓
原因をレビュー
↓
修正方針を決定
↓
別途修正指示
```

の順で進める。

テスト依頼と自動修正を同じ指示にまとめない。

---

# 5. Blender runtime testの基本方針

Blender runtime testは、可能な限りスクリーンショットだけで判定しない。

原則:

```text
Python Consoleで内部状態を確認
+
必要な部分だけUI / 3D Viewを目視確認
```

とする。

## Consoleで確認するもの

可能なものはPython Consoleで数値・canonical stateを直接確認する。

例:

```text
Finish ID
Wall ID
Profile ID
Profile revision
Profile schema
Finish type
vertical reference
Span count
Exclusion count
Material
Object Transform
world-space bounds
diagnose_finish()
visible range count
stale / regeneration-required
Custom Profile library state
```

UI表示だけで内部状態を推測しない。

## UI / スクリーンショットで確認するもの

Consoleでは判断できないものを目視確認する。

例:

```text
Profile thumbnailの見た目
選択中表示
Crown / Baseboardの視覚的方向
Miterのgap / overlap / spike
Profileの見た目
UIレイアウト
ブラウザ更新
smooth / flatの視覚結果
```

Console evidenceを主、スクリーンショットを補助証拠とする。

---

# 6. テストの進め方

原則として一度に大量のruntime testを実施しない。

```text
Test Nを提示
↓
ユーザーがBlenderで実行
↓
Console結果 / screenshotを報告
↓
PASS / FAILを判定
↓
次のTestへ進む
```

この方式を基本とする。

失敗が発生した場合は、後続テストを機械的に続けず原因を確認する。

---

# 7. Undo / Redoテスト

Undo / Redoをテストする場合、Undo対象operatorとUndo / Redoの間に不要な操作を挟まない。

特にPython Console操作がUndo historyやcontextへ影響する可能性があるため、

```text
対象UI操作
↓
Ctrl + Z
↓
Ctrl + Shift + Z
↓
その後Consoleで確認
```

を基本とする。

Undo直前やUndoとRedoの間にConsole確認を挟まない。

Python Consoleから

```python
bpy.ops.ed.redo()
```

を呼ぶ方法はEditor context依存になるため、通常のUndo / Redo runtime testには使用しない。

また、Python ConsoleからRNA値を直接変更した操作は、JHMのUNDO対応operatorと同じUndo checkpointを作るとは限らない。
Undo保持を検証する場合は、必要に応じてUI / JHM operatorで明示的なUndo unitを作ってから確認する。

---

# 8. Candidate運用

Runtime candidateは以下の命名を基本とする。

```text
Japanese_House_Modeler_Build_XX_X_StageN_Candidate_r1.zip
Japanese_House_Modeler_Build_XX_X_StageN_Candidate_r2.zip
...
```

Candidate ZIPはユーザーPCの以下へ作成する。

```text
C:\AI-Blender\Test_Zips
```

runtime defectを修正した場合はCandidate番号を上げる。
失敗したCandidateをaccepted candidateとして再利用しない。

Candidate ZIPは可能な限り、テスト対象として固定したexact commit SHAから作成する。

例:

```cmd
cd /d C:\AI-Blender\blender-japan-building-addon
git fetch origin
git archive --format=zip --output=C:\AI-Blender\Test_Zips\Japanese_House_Modeler_Build_06_C_Stage3_Candidate_r4.zip <TESTED_COMMIT_SHA> japanese_house_modeler
```

branch名やHEADだけに依存せず、Acceptance evidenceに使用するCandidateではexact SHAを優先する。

---

# 9. Runtime revisionの固定

Blender runtime test開始前にCandidateを作成したGit revisionを固定する。

Acceptance evidenceには最低限、

```text
GitHub commit SHA
Git tree SHA
Candidate ZIP名
Blender version
```

を記録する。

テスト途中でproduction codeが変更された場合は同じCandidateとして扱わない。
必要に応じて新しいrNを作成する。

---

# 10. Automated regression

各Build / StageのSpecificationで指定されたautomated testsを実施する。

原則として以下を区別する。

```text
Automated / pure Python evidence
≠
Blender runtime evidence
```

Automated regressionでは実測値のみ記録する。

予測したtest countや過去のtest countを新しいAcceptance Recordへ転記しない。

例:

```text
tests.test_build_xxx — NN tests PASS
full discovery — NNN tests PASS
compileall — PASS
git diff --check — PASS
```

---

# 11. compileallと__pycache__

以下を実行すると、

```bash
python -m compileall -q japanese_house_modeler tests
```

通常、

```text
__pycache__/
```

が生成される。

これらがuntrackedであり、tracked source treeに変更がない場合はproduction変更とは扱わない。

最終確認では、

```bash
git status --short
```

でtracked fileの変更有無を確認する。

---

# 12. Acceptanceの条件

StageをACCEPTEDにするには、Specificationで要求された証拠を揃える。

代表例:

```text
Automated tests
Static checks
Blender runtime tests
Regression tests
Save / reopen
Undo / Redo
Failure rollback
Managed-state validity
```

必要な範囲は各Specificationに従う。

## Runtime defectが見つかった場合

```text
Acceptance停止
↓
原因分類
  canonical
  geometry
  UI
  preview
  lifecycle
等
↓
最小範囲を修正
↓
可能ならautomated regression追加
↓
新Candidate作成
↓
影響範囲を再テスト
```

---

# 13. Acceptance Record

各Buildでは、

```text
BUILD_XX_ACCEPTANCE_RECORD.md
```

を更新する。

Acceptance Recordでは必ず、

```text
Stage status
Overall Build status
runtime-tested revision
runtime artifact
Git tree SHA
automated test revision / tree
automated test results
Blender runtime evidence
resolved pre-acceptance defects
```

を区別して記録する。

Acceptance Recordだけを変更したcommitは、新しいruntime-tested production revisionとして扱わない。

---

# 14. Pull Request / Merge / Windows同期 / ZIP作成

## 基本フロー

```text
Specification
↓
Codex implementation
↓
GitHub branch / PR
↓
Candidate ZIP作成
  C:\AI-Blender\Test_Zips
↓
Blender runtime test
↓
修正があれば新Candidate rN
↓
Automated regression
↓
Acceptance Record更新
↓
PR merge
↓
Windows local repositoryをmainへ同期
↓
ACCEPTED ZIP / ACCEPTED_REPO ZIP作成
↓
Build archiveへ保存
```

PRは以下を確認してからmergeする。

```text
runtime acceptance完了
automated regression完了
Acceptance Record更新完了
merge conflictなし
```

## Merge後のbranch

このプロジェクトでは、merge済みbranchを毎回削除することを必須としない。

過去の実装branchは調査・比較・auditの参照として役立つため、原則として残してよい。

branch数が増えすぎて管理上の問題になった場合のみ、受入済み・mainへmerge済み・必要なarchive作成済みであることを確認したうえで整理する。

Codex CloudのworkspaceやGitHubアクセスに制約があるため、単に「merge後は必ずbranch削除」という運用にはしない。

## Merge後のWindows local repository同期

ユーザーPCのlocal repository:

```text
C:\AI-Blender\blender-japan-building-addon
```

基本コマンド:

```cmd
cd /d C:\AI-Blender\blender-japan-building-addon
git status --short
git switch main
git fetch origin
git pull --ff-only origin main
git log -1 --oneline
git status --short
```

`git pull --ff-only` が失敗した場合は無理にresetせず、原因を確認してから次へ進む。

## ACCEPTED archive保存先

完成版は原則として次へ保存する。

```text
C:\AI-Blender\Build_Archives\Build_XX_X
```

例:

```text
C:\AI-Blender\Build_Archives\Build_06_C
```

フォルダがない場合:

```cmd
if not exist C:\AI-Blender\Build_Archives\Build_06_C mkdir C:\AI-Blender\Build_Archives\Build_06_C
```

## ACCEPTED ZIPの意味

Addonのみ:

```text
Japanese_House_Modeler_Build_06_C_ACCEPTED.zip
```

Repository全体:

```text
Japanese_House_Modeler_Build_06_C_ACCEPTED_REPO.zip
```

作成例:

```cmd
git archive --format=zip --output=C:\AI-Blender\Build_Archives\Build_06_C\Japanese_House_Modeler_Build_06_C_ACCEPTED.zip <ACCEPTED_MERGE_SHA> japanese_house_modeler
git archive --format=zip --output=C:\AI-Blender\Build_Archives\Build_06_C\Japanese_House_Modeler_Build_06_C_ACCEPTED_REPO.zip <ACCEPTED_MERGE_SHA>
```

`ACCEPTED.zip` はBlenderへ導入可能なaddon packageを保存する。
`ACCEPTED_REPO.zip` はSpecification、Acceptance Record、tests等を含むrepository全体を保存する。

## Stage単位のAccepted archive

必要に応じてStage単位でも同じ命名規則を使用する。

例:

```text
Japanese_House_Modeler_Build_06_B_Stage1_ACCEPTED.zip
Japanese_House_Modeler_Build_06_B_Stage1_ACCEPTED_REPO.zip
Japanese_House_Modeler_Build_06_B_Stage2A_ACCEPTED.zip
Japanese_House_Modeler_Build_06_B_Stage2A_ACCEPTED_REPO.zip
```

Buildの最終Stageまで完了したら、最終版としてStage名を外した、

```text
Japanese_House_Modeler_Build_06_B_ACCEPTED.zip
Japanese_House_Modeler_Build_06_B_ACCEPTED_REPO.zip
```

を作成する。

テスト中のCandidate ZIPは `C:\AI-Blender\Test_Zips`、
正式Acceptance後の長期保存用ZIPは `C:\AI-Blender\Build_Archives\Build_XX_X`
を基本とする。

---

# 15. Regression方針

過去に正式Acceptance済みのテストを、毎Stageですべて機械的に繰り返す必要はない。

変更差分とSpecificationを確認し、影響を受ける範囲を重点的に再テストする。

ただし、

```text
geometry core変更
canonical schema変更
dependency / transaction変更
save format変更
```

など影響範囲が広い変更では、必要に応じて過去Buildのruntime regressionを拡大する。

既存Acceptance evidenceを再利用する場合は、どのEvidenceを再利用したか明記する。

---

# 16. Canonical dataを正とする

Managed JHM objectでは、

```text
canonical data
↓
derived geometry
```

を基本とする。

生成済みMesh / Curveの見た目を解析して、通常編集経路でcanonical dataへ書き戻す設計にしない。

Blender geometryはcanonical stateから再生成できることを維持する。

---

# 17. この文書の更新

開発中に、

```text
繰り返し発生するトラブル
環境固有の制約
新しいテスト方法
Codex Cloud固有の挙動
GitHub運用ルール
Windows同期 / archive運用
```

が判明した場合は、この文書へ追記する。

単発のBuild仕様はここへ追加せず、各BuildのSpecificationへ記載する。
