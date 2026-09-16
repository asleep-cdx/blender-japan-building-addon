# 日本住宅モデラー

Blender 5.2 LTS向けの、日本住宅を寸法ベースでモデリングするためのアドオンです。

## Build 06-A

実装済み：

- 3D Viewport のサイドバー「日本住宅」タブにあるUI
- 永続IDと明示接続を持つ芯線ベースのWall生成・編集・分割・安全な削除
- Wall接合と、Wall参照をcanonical stateとして保持するFinishRun
- transaction-safeなFinish再生成、分割/削除remap、管理状態診断
- 床/天井基準の一括再生成、および通常編集可能なMeshへの確定

Build 06-AはBlender 5.2 LTSでformal acceptance済みです。`BREAK` join、closed Finish、Profile Library、開口、部屋認識、床/天井Mesh生成はBuild 06-Aの対象外です。

## インストール

1. `japanese_house_modeler` フォルダをZIP化します（ZIPの直下にこのフォルダがある形にします）。
2. Blenderの **Edit > Preferences > Add-ons** で **Install from Disk** を選び、ZIPを指定します。
3. 「日本住宅モデラー」を有効化します。
4. 3D Viewportで **N** を押し、「日本住宅」タブを開きます。

## Acceptance

自動テストおよびBlender runtime acceptanceの結果は、リポジトリ直下の `BUILD_06_A_ACCEPTANCE_RECORD.md` に記録しています。
