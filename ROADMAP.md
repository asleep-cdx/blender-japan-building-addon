# Japanese House Modeler — Development Roadmap

最終更新: 2026-10-07

この文書は、Blender 5.2 LTS 向け **Japanese House Modeler / 日本住宅モデラー** の今後の開発順序と、各Buildをまたいで維持する設計方針をまとめたロードマップである。

このロードマップは、各Buildの詳細仕様書そのものではない。詳細仕様は各 `BUILD_*_SPECIFICATION.md`、受け入れ結果は各 Acceptance Record を正とする。

---

## 1. Roadmap policy

この文書は**現在の開発計画**であり、固定された仕様ではない。

- 実装・Blender実機テスト・Architecture上の問題が見つかった場合、Build順序は変更できる。
- Accepted済みBuildを後から変更する場合は、互換性への影響を明示する。
- 詳細挙動は各 `BUILD_*_SPECIFICATION.md` を正とする。
- Accepted / NOT ACCEPTED の状態は各 Acceptance Record を正とする。
- RoadmapとAccepted済み仕様・Acceptance Recordが矛盾する場合、Accepted済み文書を優先する。
- 後続Buildの都合だけで、Accepted済みcanonical dataを安易に破壊・再定義しない。
- 新機能は可能な限り既存Foundationを再利用し、Buildごとに独立した場当たり実装を増やさない。

---

# 2. Project goal

本プロジェクトの目的は、BlenderをCAD/BIMへ置き換えることではない。

目的は、

> **日本住宅のリフォーム完成イメージや室内3Dパースを、寸法ベースで素早く組み立て、その後は通常のBlender編集へ移行できる制作補助ツールを作ること**

である。

重視するもの：

- 寸法入力による正確な初期生成
- 壁・巾木・廻り縁・階段・床・天井・建具などの面倒な初期モデリングを短縮
- 再生成可能なManaged状態
- 最終的には通常のBlender Object / Meshへ確定可能
- 手作業で十分簡単なものより、手作業負担の大きいものを優先
- BIMのような過剰な自動化やデータモデル化は避ける

---

# 3. Current status

現在の基準状態：

- **Build 05-B — ACCEPTED**
- **Build 05-C — BACKLOG**
- **Build 06-A — ACCEPTED**
- **Build 06-B — ACCEPTED**
- **Build 06-C — ACCEPTED / overall ACCEPTED**
- **Build 07-A — ACCEPTED / overall ACCEPTED**
- **Build 07-B — ACCEPTED / overall ACCEPTED**
- **Build 07-C — ACCEPTED / overall ACCEPTED**
- **Build 07-D — ACCEPTED / overall ACCEPTED**
- **Build 07-E Stage 1 — ACCEPTED**
- **Build 07-E Stage 2 — ACCEPTED at Candidate r3**
- **Build 07-E Stage 2.5 — ACCEPTED**
- **Build 07-E Stage 3 first attempt / PR #33 — ABANDONED / CLOSED / NOT MERGED**
- **Build 07-E Fresh Stage 3A — ACCEPTED at Candidate r2**
- **Build 07-E Fresh Stage 3B — ACCEPTED at runtime r9**
- **Build 07-E Fresh Stage 3C — ACCEPTED at Candidate r7 (EQUAL_4 SLOPED visual caveat)**
- **Build 07-E Fresh Stage 3D — NEXT**
- **Build 07-E overall — NOT YET ACCEPTED**
- **Build 07-F — HOLD after 07-E**
- **Build 07-G — HOLD / OPTIONAL BACKLOG**
- Current accepted add-on version: **0.7.4**

Historical accepted `main` before the Stage-3B merge (retained as an old checkpoint, **not current main**):

```text
commit c60a3205a7c0a8dce2afc30a28feb841ca379bf1
```

Accepted Fresh Stage-3A runtime production revision:

```text
commit 01a9b88c28451ae9ac04f268fce63bfe1a227830
tree   09527d45f2616a93c817e0922c91645d88245193
Candidate r2 SHA256 d2d5353afca50b5f87f0c8722b9b36c38359eaded82d934d4dc638b38ca5f2f8
```

Fresh Stage 3B has now passed Blender 5.2 LTS runtime acceptance at the exact production revision:

```text
commit 389f7e9d30a181c3fcd2c578e8af7bbdc16189e7
tree   3154653ca6b608b1ae7b11e42a40d497b7c50b99
PR     #47
```

Stage-3B acceptance covers Winder `SLOPED_CLOSED` with Side Boards OFF, the retained corrected `STEPPED_CLOSED` body, shared rear/exterior authority, and canonical outer-corner preservation.

Fresh Stage 3C ordinary Winder Side Board continuation has now passed Blender 5.2 LTS runtime acceptance at Candidate r7:

```text
PR     #48
commit d88d5c597fafb49ac8b0debeedd048ce2bd8e648
tree   9ab5eadb8ee3fe1524a5e627a3ce7768a7932dbd
Candidate size 172684 bytes
Candidate SHA256 2a0cbd92cd91f076243744ef1df83ad01d29e38098582c5209c24c287685a455
```

Stage 3C acceptance explicitly defers the visible EQUAL_4 SLOPED outer Side Board slope change; this is **not claimed resolved**. Compact-U shared-center Side Board is Stage 3D (NEXT).

Acceptance authority: `BUILD_07_E_STAGE_3B_ACCEPTANCE_RECORD.md` and `BUILD_07_E_STAGE_3C_ACCEPTANCE_RECORD.md`. Implementation scope: `BUILD_07_E_STAGE_3C_PLAN.md`.

---

# 4. Final development order

| Build | 内容 | 状態 |
|---|---|---|
| **05-B** | Wall System完成 | **DONE / ACCEPTED** |
| **05-C** | Wall再統合 | **BACKLOG** |
| **06-A** | Finish Attachment Foundation | **DONE / ACCEPTED** |
| **06-B** | Baseboard / 巾木 | **DONE / ACCEPTED** |
| **06-C** | Crown Moulding / 廻り縁 + Profile Thumbnail UI | **DONE / ACCEPTED** |
| **07-A** | Stair Core + Top-view 2-point Straight Stair | **DONE / ACCEPTED** |
| **07-B** | Standard Residential Straight Stair + Stepped Closed Underside + Side Boards | **DONE / ACCEPTED** |
| **07-C** | Sloped Closed Underside + Straight Stair Finish Variants | **DONE / ACCEPTED** |
| **07-D** | Multi-point Path + L/U + Landing | **DONE / ACCEPTED** |
| **07-E Stage 1** | Winder foundation | **DONE / ACCEPTED** |
| **07-E Stage 2** | BF/U/Compact-U/arbitrary-angle top geometry | **DONE / ACCEPTED at r3** |
| **07-E Stage 2.5** | Pre-Stage-3 Winder geometry simplification / r1-equivalent top restoration | **DONE / ACCEPTED** |
| **07-E Fresh Stage 3A** | Winder STEPPED_CLOSED / Side Boards OFF | **DONE / ACCEPTED at Candidate r2** |
| **07-E Fresh Stage 3B** | Winder SLOPED_CLOSED / Side Boards OFF + outer-chain corrections | **DONE / ACCEPTED at runtime r9** |
| **07-E Fresh Stage 3C** | ordinary Winder Side Board continuation | **DONE / ACCEPTED at runtime r7 (EQUAL_4 known limitation)** |
| **07-E Fresh Stage 3D** | Compact-U shared-center Side Board | **NEXT** |
| **07-E Fresh Stage 3E** | Material / Reverse / lifecycle regression | **PENDING** |
| **07-E Stage 4** | Lifecycle / full regression / practical acceptance | **PENDING** |
| **07-F** | Open / Support Variants | **HOLD after 07-E** |
| **07-G** | Optional Stair Detail Expansion | **HOLD / Optional Backlog** |
| **08-A** | Minimal Room / Boundary + Floor | Planned after 07-E |
| **08-B** | Ceiling + 吹抜け / 穴の基本 | Planned after 08-A |
| **8.5 Correction** | Closed Wall layout Finish endpoint mismatch修正 | Planned after 08-B |
| **Integration Core** | Wall / Finish / Floor / Ceiling / Stair / Void 一室Core統合試験 | Planned after 8.5 Correction |
| **09-A** | Window / Door Asset Root + Wall Anchor | Planned |
| **09-B** | Live Boolean Cutter | Planned |
| **09-C** | Finish Exclusion連携 | Planned |
| **Integration 1** | Door / Windowを含む一室フル実務統合試験 | Planned after 09 minimal |
| **10** | Production Hardening / UX / Compatibility / Full Regression | Planned |

---

# 5. Why this order

## 5.1 Finishを先に完成させた理由

Build 06では単なるCurve生成ではなく、**Wallのどの面・どの区間に、何を、どの基準高さで配置するか**を永続化する共通Attachment Foundationを作った。これによりBaseboard、Crown Moulding、将来のChair Rail、Opening exclusion、その他のWall付属部材を同じ考え方で扱える。

## 5.2 Build 07を08/09より先に進める理由

Floor / CeilingはBlender標準機能で比較的容易に手作業代替でき、Door / WindowもAsset配置とBooleanによる手動ワークフローが存在する。一方、住宅階段は踏板、蹴込み板、蹴上 / 踏面、階高、側板、下面、方向転換、踊り場、廻り段、支持方式を相互に整合させる必要があり、手作業負担が大きい。

StairはWall / Floor / Roomを必須参照としないstandalone Managed Objectとするため、Floor / Room実装を待たずに進める。

## 5.3 Stage 2.5をStage 3の前に追加した理由

Stage-2 Candidate r3はStage 2単体としてruntime acceptance済みである。しかしStage 3実装時、r2/r3で追加されたTurn-wide physical Winder planとcommon inner finish chord `K_finish`が、隣接Straight / underbody / Side Boardとの接続authorityを複雑化した。

Preserved runtime ZIP auditでは、r1/r2/r3のpackaged add-on差分が `japanese_house_modeler/stair_turn.py` のみに限定されることを確認した。よってRepository全体を古いrevisionへ戻すのではなく、current r3 codebaseをstructural baseにしてvisible Winder top productionだけをr1-equivalentへ戻すことが可能である。

Stage 2.5は次を目的とする：

- accepted 07-D Landing / Straight geometryを維持する;
- schema-5 / BF / U / Compact-U / arbitrary-angle / allocation / persistence foundationを維持する;
- visible Winder TREAD/RISER productionだけをCandidate-r1相当へ単純化する;
- r1に存在したterminal gapはこのStageでは既知・許容とする;
- Stage 3でtop geometryを再設計しないようbaselineを先に固定する。

## 5.4 新Stage 3のvisual-first方針

Restarted Stage 3ではCAD/BIM watertight-solid kernelを目標にしない。

Required：

- visible exterior shapeが正しい;
- obvious exterior hole / major spike / visible z-fightingがない;
- generation / regeneration / save / reopenが安定する;
- Stage-2.5 accepted Winder topを変更しない;
- 07-D accepted Landing / Straight bodyを変更しない。

Allowed internally：

- hidden UNDERBODY/TREAD/RISER penetration;
- hidden component overlap;
- hidden internal/duplicate faces;
- separate overlapping closed components;
- no exact whole-stair Boolean union。

Not required for Stage-3 r1：

- exact positive-volume exclusion;
- global collision elimination;
- convex decomposition audit;
- full PHYSICAL_CONTACT classification;
- exact BodyInterface union proof。

---

# 6. Architecture decisions carried forward

## 6.1 Canonical data first

原則：

```text
Canonical Data
    ↓
Derived Geometry
```

生成Mesh / Curveそのものをcanonical authorityとせず、Managed stateからderived geometryを再生成する。

## 6.2 Persistent Wall ID

Wall参照にBlender Object名を使用しない。Baseboard、Crown、Window、Door、Opening等はPersistent Wall IDとWall上位置を基準にする。

## 6.3 Wall split dependency remap

Wall分割時、依存要素は分割前後の区間対応、Persistent Wall ID、distance/parameter、LEFT/RIGHT sideを用いて新Wallへ追従可能とする。

## 6.4 Wall自身に固定の「室内側」を持たせない

間仕切りWallでは両側とも室内になり得るため、Wallに固定interior sideを持たせない。

## 6.5 Split Wall continuation

物理的に分割されたWallも、Finish側では必要に応じて連続Pathとして扱える。

---

# 7. Build 05-C — Wall merge backlog

05-CはBacklog。将来実装する場合も自動統合よりユーザー明示操作による統合を優先する。

---

# 8. Build 06 — Finish Attachment architecture

Build 06-A / 06-B / 06-CはAcceptance済み。Finishは生成CurveではなくWallへの配置canonical dataを正とする。Baseboard / Crown / Custom Profile / Exclusion / Wall split追従 / Material / Save-Reopen / Editable Mesh conversion等のaccepted contractを維持する。

## 8.5 Known Issue — Finish endpoint mismatch on closed Wall layout

**Status: OPEN / correction planned after 08-B**

Closed Wall layoutに沿うBaseboard / Crownで端部突出・不足が報告されている。画像のみから原因を断定せず、08-B後、Integration Core前に調査・修正する。

---

# 9. Profile Library contract

Profileは輪郭だけでなくidentity、revision、category、contour、origin、wall/vertical direction、nominal width/height、shading intent、thumbnail metadataを含む。Custom Profileはsnapshot-basedで、初期supportはsingle closed 2D spline等の限定scopeを維持する。

---

# 10. Editable Mesh contract

Managed Stair / Finish等は最終的に通常Blender Meshへ一方向変換できる。Mesh確定後はAdd-on管理を解除し、手編集Meshからcanonical parametersへ逆推定しない。

---

# 11. Material / UV / Modifier contract

Managed stateではcanonical parameters / Profile / Material等の明示された契約を保持する。Editable Mesh確定後は通常Blender側管理へ移る。

---

# 12. Build 07 — Stair System

## 12.1 Final goal

トップビューでPathを指定し、日本の戸建て住宅で一般的なStraight / L / U / Landing / Winderを1つのManaged Stairとして生成・編集可能にする。

## 12.2 Standalone Stair contract

Wall / Room / Floor / Ceilingを必須依存とせず、完全な空Sceneでも生成可能とする。`base_z` / `floor_to_floor`を保持し、future Floor connectionへ拡張可能にする。

## 12.3 Path contract

PathのSTART/ENDはクリック順、上り方向は`ascent_direction`として分離する。07-D exact-90 Landing foundationを07-E schema-5 Turnへ拡張する。

## 12.4 Internal model must not depend on preset names

Path / Turn / Riser / Underside / Side Board / Support / Tread等を独立axisとして扱う。ただし独立axisは全組合せsupportを意味しない。

## 12.5 Riser / Tread terminology

`riser_count`、`independent_tread_count`、`actual_riser`、`going`を意味上分離する。

## 12.6 Part-generation architecture

Canonical Stair → Resolved Path → riser/tread placement → Tread/Riser/Underbody/Side Board等のPart generatorsという責務分離を維持する。

## 12.7 Managed Stairの管理単位とMesh構成

現行mainlineでは1 Managed Stair = 1 Managed Mesh Object。内部fragment責務は分離する。

## 12.8 Build 07-A

**ACCEPTED** — Stair Core + 2-point Straight foundation。

## 12.9 Build 07-B

**ACCEPTED** — Standard Residential Straight Stair + STEPPED_CLOSED + Side Boards。

## 12.10 Build 07-C

**ACCEPTED** — SLOPED_CLOSED + Straight Stair Finish Variants。

## 12.11 Build 07-D

**ACCEPTED** — Multi-point Path + L/U + exact-90 Landing。`BUILD_07_D_SPECIFICATION.md` / `BUILD_07_D_ACCEPTANCE_RECORD.md`をauthorityとする。07-E/Stage 2.5/Stage 3はaccepted 07-D Landing body/undersideを無断で再構築・置換しない。

## 12.12 Build 07-E

**Status: STAGE 1/2/2.5 ACCEPTED / FRESH STAGE 3A/3B/3C ACCEPTED / STAGE 3D NEXT / BUILD 07-E OVERALL NOT YET ACCEPTED**

Authority：

- `BUILD_07_E_SPECIFICATION.md`
- `BUILD_07_E_STAGE_2_5_PLAN.md`
- `BUILD_07_E_STAGE_2_5_ACCEPTANCE_RECORD.md`
- `BUILD_07_E_STAGE_3A_ACCEPTANCE_RECORD.md`
- `BUILD_07_E_STAGE_3B_ACCEPTANCE_RECORD.md`
- `BUILD_07_E_STAGE_3C_ACCEPTANCE_RECORD.md`
- `BUILD_07_E_ACCEPTANCE_RECORD.md`
- `BUILD_07_D_ACCEPTANCE_RECORD.md`

Stage 1：schema-5 Turn/RiseEvent foundation + exact-90 EQUAL Winder foundation — ACCEPTED。

Stage 2：BF / per-Turn U / Compact-U / arbitrary-angle Landing/Winder / migration / physical top finish integration — Candidate r3でACCEPTED。

Stage 2.5：Candidate-r1-equivalent visible Winder TREAD/RISER production behaviorをnarrowly restoreした correction stage — **ACCEPTED**。

Fresh Stage 3A：Winder `STEPPED_CLOSED` visible body / Side Boards OFF — **ACCEPTED at Candidate r2**。

Fresh Stage 3B：Winder `SLOPED_CLOSED` visible body / Side Boards OFF、shared rear/exterior authority、canonical outer-corner preservation — **ACCEPTED at runtime r9**。

Fresh Stage 3C：ordinary Winder Side Board continuation — **ACCEPTED at runtime Candidate r7**。EQUAL_4/SLOPEDの外板勾配変化は既知の保留事項。Next = Fresh Stage 3D。

Old PR #33はABANDONEDであり、Fresh Stage 3のbaselineではない。

### Stage-2 runtime artifact identities

```text
r1 commit b0d92fc15f7ec103e3cf18b6110dce2b5841fd3e
   tree   e90e4bfa0e0583552bc761a200b8e51a52590470
   SHA256 8c6c7100e0a51e550525fedca0e214e95b5ca8b73874ce4c7b213d9149f62054

r2 commit 26ddf5b79bb933ea6b8bf43a3a4c585c11ddf597
   tree   9c4804864dab6e07cfd54be8f38c85fae671cd1a
   SHA256 2d6e34b4589ea993995903fdbe30dfd8c68559daae2438ca955ced0563fd5cac

r3 commit 9424da623953a32a97576ce45bec074b269d4058
   tree   7d30e76ae20ad58b72cece1e298f54ee45f90a65
   SHA256 15d48e9230b5a7e7f0b59954ccbe56acc7fb99bce3d26b39481f969f75c7b1d4
```

ZIP audit result：r1/r2/r3 packaged add-on source differs only in `japanese_house_modeler/stair_turn.py`。

### Stage 2.5 restoration target

r1 production：

```text
physical_winder_tread_polygon(...)
resolve_winder_riser_plan(...)
```

r2 added Turn-wide physical plan authority：

```text
PhysicalWinderBoundary
PhysicalWinderTreadPlan
resolve_physical_winder_plans(...)
```

r3 added common inner finish chord：

```text
PhysicalWinderInnerTrim
K_finish
inner_front / inner_rear / inner_edge
```

Stage 2.5はcurrent r3 codebaseをstructural baseとし、visible Winder top production pathのみをr1-equivalentへ戻す。Whole-file rollbackは禁止する。

### Restarted Stage 3

Internal order：

```text
3A STEPPED_CLOSED / Side Boards OFF
3B SLOPED_CLOSED / Side Boards OFF
3C ordinary Side Board continuation
3D Compact-U shared-center Side Board
3E Material / Reverse / lifecycle regression
```

ただし旧precision-first Stage 3のexact internal union/collision architectureを前提にしない。Hidden overlapを許容し、visible geometryを優先する。

## 12.13 Build 07-F

**HOLD after 07-E** — Open / Support variants。

## 12.14 Build 07-G

**HOLD / OPTIONAL BACKLOG** — optional detail expansion。

## 12.15 Build 07 quality / scope guards

Canonical data → derived geometry、identity transform、atomic failure、Undo/Redo、Save/reopen、deterministic regeneration、Material、Editable Mesh exit、prior regressionを各Stageで維持する。

---

# 15. Build 08 — Room / Floor / Ceiling minimum

08-A Minimal Room / Boundary + Floor → 08-B Ceiling + Void/Holeの順。08-B後にKnown Issue 8.5 correctionを行い、その後Integration Coreへ進む。

---

# 16. Build 09 — Window / Door system

09-A Asset Root + Wall Anchor → 09-B Live Boolean Cutter → 09-C Finish Exclusion integration。

---

# 17. One-room integration tests

Integration Coreは07-E/08-A/08-B/8.5 correction後、Door/Windowを待たず主要Foundationを一室で統合する。Integration 1は09 minimal後にDoor/Window/Boolean/Finish Exclusionを含めて行う。

---

# 18. Build 07 ordering checkpoints

- **07-C完了**：Straight practical checkpoint完了。
- **07-D完了**：Multi-point L/U + Landing ACCEPTED。
- **07-E Stage 1**：schema-5 foundation ACCEPTED。
- **07-E Stage 2**：Candidate r3 runtime ACCEPTED。
- **PR #33 Stage 3 first attempt**：runtime regressions / over-complexityによりABANDONED、CLOSED、NOT MERGED。
- **07-E Stage 2.5**：r1-equivalent Winder top geometryをnarrowly restoreし、runtime ACCEPTED / merged。
- **Fresh Stage 3A**：Winder STEPPED_CLOSED / Side Boards OFF — runtime ACCEPTED / merged。
- **Fresh Stage 3B**：Winder SLOPED_CLOSED / Side Boards OFF + canonical outer-chain corrections — runtime ACCEPTED at r9。
- **Fresh Stage 3C ACCEPTED**：ordinary Winder Side Board continuation at runtime r7（EQUAL_4 SLOPED外側側板の勾配変化は既知の保留事項）。
- **Fresh Stage 3D NEXT**：Compact-U shared-center Side Board。
- **Stage 2.5完了**：Acceptance Record作成 → main merge → fresh Stage-3 branch作成。
- **Restarted Stage 3**：visual-first CLOSED underbody + Side Board。
- **07-E完了**：practical checkpoint後07-F/07-GをHOLDして08へ。

---

# 19. Build 10 — Production Hardening

UX、Save compatibility、migration、dependency repair、performance、full regression、integrated workflowを横断的にhardeningする。基本品質をBuild 10まで延期しない。

---

# 20. Scope guards

フルBIM化、IFC authoring、構造計算、法規自動判定、全建材カタログ、自動施工図、parametric CAD全面置換、全Blender編集のManaged逆変換は原則scope外。

---

# 21. Development decision rules

手作業負担が大きい、繰り返す、寸法自動化効果が高い、Foundationになる、一室統合で必要、Accepted architectureを再利用できるものを優先する。実装コストに比べ効果が低いBIM的複雑化は避ける。

---

# 22. Roadmap change protocol

開発順序変更時：

1. `ROADMAP.md` 更新
2. 変更理由を記録
3. Accepted済みBuildへの影響確認
4. 必要ならSpecification/addendumへcompatibility方針追加
5. 既存Acceptance Recordは履歴として保持

---

# 23. Current next decision

```text
07-D                 ACCEPTED
07-E Stage 1/2/2.5  ACCEPTED
07-E Fresh Stage 3A ACCEPTED
07-E Fresh Stage 3B ACCEPTED (runtime r9)
07-E Fresh Stage 3C ACCEPTED (runtime r7; EQUAL_4 SLOPED caveat)
07-E Fresh Stage 3D NEXT
07-E overall        NOT YET ACCEPTED
```

Next:

```text
Stage-3C Acceptance Record and PR #48 merge
    ↓
Windows main sync + accepted r7 Addon copy and runtime-revision REPO archive
    ↓
Fresh Stage 3D — Compact-U shared-center Side Board
    ↓
Fresh Stage 3E — Material / Reverse / lifecycle regression
    ↓
Stage 4 — overall acceptance
```

---

# 24. Summary

```text
Wall Foundation
    ↓
Finish Foundation
    ↓
Baseboard / Crown
    ↓
07-A Stair Core
    ↓
07-B Residential Straight
    ↓
07-C Sloped Underside / Finish Variants
    ↓
07-D Multi-point L/U + Landing [ACCEPTED]
    ↓
07-E Stage 1 [ACCEPTED]
    ↓
07-E Stage 2 Candidate r3 [ACCEPTED]
    ↓
07-E Stage 2.5 [ACCEPTED — r1-equivalent Winder top simplification]
    ↓
07-E Fresh Stage 3A [ACCEPTED]
    ↓
07-E Fresh Stage 3B [ACCEPTED r9]
    ↓
07-E Fresh Stage 3C [ACCEPTED r7; EQUAL_4 SLOPED caveat]
    ↓
07-E Fresh Stage 3D [NEXT] / 3E [PENDING]
    ↓
07-E Stage 4 / overall Acceptance
    ↓
07-F / 07-G HOLD
    ↓
08-A / 08-B
    ↓
Known Issue 8.5 correction
    ↓
Integration Core
    ↓
09 minimal
    ↓
Integration 1
    ↓
Production Hardening
```

Build 07の中心目標は、Wall / Floor / Roomに必須依存せず、トップビューPathから日本住宅の直線・折れ曲がり・廻り・変形角度階段を1つのManaged Stairとして生成・編集できること。

Stage 2.5は新機能Buildではなく、fresh Stage 3のためのcontrolled baseline correctionである。詳細は `BUILD_07_E_STAGE_2_5_PLAN.md` を正とする。
