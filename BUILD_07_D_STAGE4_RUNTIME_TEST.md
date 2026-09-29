# Build 07-D Stage 4 — Blender 5.2 LTS Runtime Test

## 目的と判定方法

対象は Blender 5.2 LTS。Stage 1～3 の production behavior を変更せず、07-D の lifecycle、persistence、repair、isolation、topology を最終確認する。各 Test は **UI操作後に Console evidence を取得し、指定箇所だけ目視**する。途中失敗を補修して続行せず、Test 単位で初期状態から再実施する。

共通 Console helper（Python Console へ一度だけ貼り付ける）:

```python
import bpy, math
def stair(o=None):
    o=o or bpy.context.active_object; s=o.jhm_stair
    return dict(name=o.name, managed=s.is_stair, id=s.stair_id, schema=s.stair_schema_version,
      points=[(p.point_id,tuple(p.xy)) for p in s.path_points], direction=s.ascent_direction,
      distribution=s.riser_distribution_mode, auto=s.auto_riser_allocation, manual=s.manual_riser_allocation,
      mode=s.assembly_mode, materials=[m.name if m else None for m in o.data.materials],
      transform=(tuple(o.location),tuple(o.rotation_euler),tuple(o.scale)),
      mesh=(len(o.data.vertices),len(o.data.polygons)) if o.type=='MESH' and o.data else None)
def topology(o=None):
    o=o or bpy.context.active_object; me=o.data
    finite=all(math.isfinite(c) for v in me.vertices for c in v.co)
    zero=[p.index for p in me.polygons if p.area <= 1e-12]
    edges={};
    for p in me.polygons:
      for k in p.edge_keys: edges[k]=edges.get(k,0)+1
    return dict(finite=finite,zero_area=zero,boundary=sum(n==1 for n in edges.values()),nonmanifold=sum(n>2 for n in edges.values()))
```

> 複数行 helper は `exec(<triple-quoted string>)` で入力してもよい。`boundary` は部品を1 Meshに結合した構造上ゼロを必須とせず、同一条件の再生成で増加しないこと、および目視破綻との組合せで判定する。

## Test 1 — Candidate identity / baseline

- **Setup:** Candidate add-onのみを有効化し、新規ファイルを開く。
- **UI操作:** Preferences > Add-ons で Japanese House Modeler を表示する。
- **Console command:** `import japanese_house_modeler as j; (j.bl_info['version'], j.bl_info['description'], bpy.app.version)`
- **Expected result:** add-on は `(0, 7, 3)` / Build 07-D、Blender は 5.2 LTS。起動時エラーなし。
- **目視:** 必要。Stair panel と Straight / L / U 作成入口を確認。
- **PASS criteria:** identity、対象runtime、UIがすべて一致する。

## Test 2 — schema-1 BASIC Straight regression

- **Setup:** accepted schema-1 BASIC Straight fixtureを開く（複製を使用）。
- **UI操作:** 選択するだけで、編集・再生成はしない。その後 Regenerate を1回実行。
- **Console command:** 操作前後で `stair()` と `topology()`。
- **Expected result:** load/resolveだけでは schema-1、Path、Stair IDを書き換えない。Regenerate後も schema-1 BASIC、canonical値、identity transformを維持。
- **目視:** 必要。旧Straightの段、最終蹴上げ、到着位置に変化なし。
- **PASS criteria:** canonical差分なし、`finite=True`、`zero_area=[]`、重大なgap/重複なし。

## Test 3 — schema-2 07-B Straight regression

- **Setup:** accepted schema-2 07-B Residential Straight fixture。
- **UI操作:** load後に Regenerate、Material編集を変更なしで確定。
- **Console command:** 各段階で `stair()` と `topology()`。
- **Expected result:** schema-2を勝手にschema-4へ上げず、Residential fields、material role/slot、Path、IDを保持。
- **目視:** 必要。07-B nosing、side board、final riser外観が維持される。
- **PASS criteria:** schema/canonical/material不変、finite、zero-areaなし。

## Test 4 — schema-3 07-C Straight regression

- **Setup:** accepted schema-3 07-C Straight fixture（STEPPED_CLOSED と SLOPED_CLOSED を各1件）。
- **UI操作:** FORWARD/REVERSEを切替後に戻し、Regenerate。
- **Console command:** 各fixtureで `stair(); topology()`。
- **Expected result:** schema-3のまま、Path順序を変えず上り方向だけが変化し、戻すと元state/geometryへ戻る。
- **目視:** 必要。closed underside、Side Board STEPPED/SLOPED、段鼻にgap/spike/cavityなし。
- **PASS criteria:** accepted 07-C behaviorと一致し、topology値が再生成で安定。

## Test 5 — schema-4 L / U persistence

- **Setup:** L StairとU Stairを各1件作成し、異なるStair IDとpoint IDsを記録。
- **UI操作:** Save Asし、**fully exit Blender**。Blenderを再起動して保存fileを開く。
- **Console command:** 終了前と再open後に各objectをactiveにして `stair()`。
- **Expected result:** schema-4、ordered Path coordinates、全point IDs、Stair ID、direction、turn/landing stateが一致。
- **目視:** 必要。各々1 Managed Stair / 1 Mesh ObjectでL/U形状を維持。
- **PASS criteria:** state完全一致、分割object化やsilent rewriteなし。

## Test 6 — AUTO / MANUAL save-full-exit-reopen

- **Setup:** schema-4 LをAUTO、UをMANUAL（例 `5,6,5`、総数16）に設定。
- **UI操作:** Save、**fully exit Blender**、再起動、reopen、各1回Regenerate。
- **Console command:** 各段階で `stair()`。
- **Expected result:** modeとsaved allocationが保持され、AUTOは同一入力から同じ配分、MANUALは指定値・合計を保持。
- **目視:** 不要（geometry破綻のみ簡易確認）。
- **PASS criteria:** allocation、Path/point IDs、材料に差分なし。

## Test 7 — Undo / Redo representative lifecycle

- **Setup:** 正常なschema-4 Lをactive選択し、事前 `stair()` を記録。
- **UI操作:** Path endpoint移動をUIで確定 → **Ctrl+Z** → **Ctrl+Shift+Z** → then Console。別途 Reverse とMaterial変更でも同じ順序を実施。**UndoとRedoの間にPython Console操作を挟まない。**
- **Console command:** Redo完了後だけ `stair(); topology()`。
- **Expected result:** Redo後は確定直後のPath/point IDs、direction、materials、meshへ戻り、identity transformを維持。
- **目視:** 必要。Undoで旧形、Redoで新形が復元。
- **PASS criteria:** UI履歴と最終canonical/geometryが一致。

## Test 8 — invalid edit full rollback

- **Setup:** 正常なL/Uについて `before=stair().copy(); mesh_before=(tuple(tuple(v.co) for v in bpy.context.object.data.vertices),tuple(tuple(p.vertices) for p in bpy.context.object.data.polygons))`。
- **UI操作:** 不正MANUAL合計、短すぎるflight、非90度turnをそれぞれ確定しようとする。
- **Console command:** `stair()==before` および `mesh_before==(tuple(tuple(v.co) for v in bpy.context.object.data.vertices),tuple(tuple(p.vertices) for p in bpy.context.object.data.polygons))`。
- **Expected result:** UIは拒否/CANCELLEDしcanonical、ID、allocation、materials、transform、meshが完全rollback。
- **目視:** 不要。
- **PASS criteria:** 両比較が `True`。

## Test 9 — GEOMETRY_MISSING / TRANSFORM_CHANGED Repair

- **Setup:** 同じ正常Uを2複製ではなく個別作成し、各 `before=stair()` を記録。片方のmeshを空にし、他方をObject Moveする。
- **UI操作:** Diagnoseで各々 `GEOMETRY_MISSING` / `TRANSFORM_CHANGED` を確認し、Repair。
- **Console command:** Repair後 `stair(); topology()`。
- **Expected result:** geometryを再構築、transformをidentityへ戻す。Path/point IDs/Stair ID/allocation/Residential fields/materialsは不要に変更しない。
- **目視:** 必要。修復形状が元Uと一致。
- **PASS criteria:** issue解消、canonical/material不変、finite・zero-areaなし。

## Test 10 — duplicate Stair ID diagnosis / Repair

- **Setup:** 正常なManaged Stair 3件 A/B/Cを作り、BのIDをAと同じにしてCは固有IDのまま。
- **UI操作:** Bのみactive選択してDiagnose (`ID_CONFLICT`) → Repair。
- **Console command:** `[(o.name,o.jhm_stair.stair_id,stair(o)) for o in (A,B,C)]`
- **Expected result:** Bだけ新しいStair ID。A/CのID、Path、point IDs、allocation、materials、meshに副作用なし。
- **目視:** 不要。
- **PASS criteria:** 全IDがunique、A/C snapshot一致、BはID以外のcanonical一致。

## Test 11 — Material lifecycle / repeated Regenerate

- **Setup:** TREAD/RISER/UNDERSIDE/SIDE_BOARDに識別可能な4材料を設定したLとU。
- **UI操作:** Regenerateを連続3回、Reverseを往復、save/reopen。
- **Console command:** 各段階で `stair(); topology()`。
- **Expected result:** material role/slotとcanonical pointersが保持され、mesh counts/topologyが同一条件でdeterministic。duplicate positive-volume bodyらしい重複外観なし。
- **目視:** 必要。LandingはTREAD、下面とSide Boardは対応材料で、z-fightingや二重bodyなし。
- **PASS criteria:** state/mesh/topology安定、材料脱落なし。

## Test 12 — Finalize transition

- **Setup:** 正常なschema-4 Uを複製し、片方を対象にする。
- **UI操作:** Finalize / 通常Meshへ変換。
- **Console command:** `o=bpy.context.active_object; (o.type,o.jhm_stair.is_stair,o.jhm_stair.stair_id,len(o.data.vertices),len(o.data.polygons))`
- **Expected result:** ordinary editable Meshとなり、`is_stair=False`。mesh/materialは維持し、Managed Stair canonical ownershipは残留しない。
- **目視:** 必要。Edit Modeで通常編集可能。
- **PASS criteria:** panelのRepair/Regenerate対象にならず、他Managed Stairには変化なし。

## Test 13 — active-only Delete / abnormal Delete

- **Setup:** Managed Stair A/B、Wall、Finish、通常Meshを作る。Aをactive選択し他も選択状態にする。
- **UI操作:** Delete StairでAを削除。次にBのmeshを欠損させ `GEOMETRY_MISSING` 状態にしてDelete Stair。
- **Console command:** `[(o.name, hasattr(o,'jhm_stair') and o.jhm_stair.is_stair) for o in bpy.context.scene.objects]`
- **Expected result:** 最初はactive-onlyのAだけ、次は異常Bだけ削除。selection-wide deleteにならず、共有mesh/material datablockを強制削除しない。
- **目視:** 不要。
- **PASS criteria:** Wall / Finish / 通常Meshが残り、abnormal Deleteも成功。

## Test 14 — Wall / Finish isolation + practical placement

- **Setup:** accepted Managed Wall/Finishを各1件と、簡易Wall/Floor相当meshを手作業で用意。L/U Stairを住宅寸法で配置する。Wall/Finish canonical snapshotを記録。
- **UI操作:** Stairだけに Regenerate、Repair、Finalize（複製側）、Delete（別複製）、Reverseを実施。
- **Console command:** 操作前後のWall/Finish ID、schema、Path/span/profile/exclusion/material値を比較し、Stair側は `stair()`。
- **Expected result:** Wall / Finish canonical data・geometry・stale状態を変更せず、Stairからpersistent dependencyを新規作成しない。
- **目視:** 必要。L/Uが簡易Wall/Floor内で住宅パース用途として重大な干渉、gap、spike、誤った到着高さを示さない。
- **PASS criteria:** isolation snapshot一致、実用配置に重大破綻なし。これはCAD/BIM統合試験ではない。

## Test 15 — final topology / visual inspection

- **Setup:** Straight/L/U、FORWARD/REVERSE、STEPPED_CLOSED/SLOPED_CLOSED、Side Board OFF/STEPPED/SLOPEDをCartesian explosionにせず代表6件で組み合わせる。
- **UI操作:** 各1回Regenerateし、Solid表示とWireframe/Face Orientationで巡回。
- **Console command:** 各objectで `topology()` を記録し、同条件の再Regenerate後にも再記録。
- **Expected result:** `finite=True`、`zero_area=[]`。unexpected open boundary / nonmanifold countが再生成で増加せず、同じgeometryは同じ結果。
- **目視:** 必要。Landing、flight接続、closed underside、Side Boardに明白な穴、内部突き抜け、重複positive-volume body、反転面、spikeなし。
- **PASS criteria:** Console条件と目視条件の両方を満たす。いずれか不一致なら **NOT ACCEPTED**。

## 最終記録

各Testについて PASS/FAIL、`.blend`名、Candidate identity、Console出力、必要なスクリーンショットを記録する。Test 1～15がすべてPASSするまでBuild 07-D overallをACCEPTEDへ更新せず、Runtime Candidate ZIP / ACCEPTED ZIPを作成しない。
