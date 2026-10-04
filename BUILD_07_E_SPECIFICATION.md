# BUILD 07-E SPECIFICATION
## 日本住宅モデラー — Winder / 廻り段 + Arbitrary-angle Turn / Landing

> **Status: FINAL BASE SPECIFICATION + STAGE 2.5 OVERRIDE AUTHORITY**  
> Original Date: 2026-09-30  
> Stage 2.5 Override: 2026-10-05  
> Build 07-D overall Acceptance を baseline とし、07-D の accepted Multi-point Path / L / U / Landing / lifecycle contract を壊さず、Turn Foundation を Winder / 廻り段および arbitrary-angle Turn / Landing へ拡張する。
>
> **Implementation authority:** 本ファイルの既存07-E仕様を基本authorityとする。ただし、末尾の **Section 39 — Stage 2.5 / restarted Stage 3 normative override** が旧Stage-2 physical Winder trim / old Stage-3 precision contractと矛盾する場合、Section 39を優先する。`BUILD_07_E_STAGE_2_5_PLAN.md` もStage 2.5実装時の必読authorityとする。

---

# 1. Purpose

Build 07-E は、Build 07-D までに成立した Straight / L / U / Multi-point Landing Stair を維持したまま、日本住宅で一般的に使われる廻り段と、変形住宅で必要になる90°以外の折れ曲がり階段を **1つの Managed Stair** として生成・編集できる production foundation を完成させる Build である。

中心目的：

1. 07-D Multi-point / Turn foundationを再利用し、`WINDER` Turn modeを追加する。
2. 90° L字 Winderをproduction対応する。
3. U字 / コの字のoverall 180°方向転換を、既存2 Turn foundation上のper-Turn Winder combinationとしてproduction対応する。
4. 90°Turnについて、2段 / 3段 / 4段廻りをstandard equal-angle patternとして提供する。
5. BF-1 / BF-2をasymmetric pattern familyとして提供する。
6. validなarbitrary-angle Landingをproduction対応する。
7. validなarbitrary-angle Winderを少なくとも`EQUAL_ANGLE`でproduction対応する。
8. Landing / Winderを含むoverall RiseEvent / height distributionをStair全体で一貫させる。
9. `STEPPED_CLOSED` / `SLOPED_CLOSED` / Side BoardをWinderへ継続する。
10. とくに`SLOPED_CLOSED`はWinder内へ不要な水平Landing plateauを挟まず、連続したturning soffitを作る。
11. 古い既存住宅の狭い階段を、法規風minimumで生成拒否しない。
12. 07-E Acceptance後はいったん07-F / 07-GをHOLDし、08-A / 08-Bへ進む。

07-Eは建築基準法適合判定ソフトを作るBuildではない。既存住宅・古い木造住宅の再現を主要用途に含み、法規・推奨寸法とgeometry validityを明確に分離する。

---

# 2. Accepted baseline / regression authority

07-E baseline：

- Build 05-B — Wall System — ACCEPTED
- Build 06-A / 06-B / 06-C — Finish system — ACCEPTED
- Build 07-A — Stair Core + Straight — ACCEPTED
- Build 07-B — Standard Residential Straight Stair — ACCEPTED
- Build 07-C — Sloped Closed Underside + Straight Finish Variants — ACCEPTED
- Build 07-D — Multi-point Path + L / U + Landing — overall ACCEPTED
- `BUILD_07_D_SPECIFICATION.md`
- `BUILD_07_D_ACCEPTANCE_RECORD.md`
- `BUILD_07_C_SPECIFICATION.md`
- `DEVELOPMENT_WORKFLOW.md`
- `ROADMAP.md`

07-E specification drafting baseline：

```text
commit 4e46e04b9f3813810d2707ae9a773fd3f98fe9f9
tree   0db32165ec527869c19781e63f4ab783703c8539
```

07-D exact Stage-4 runtime-tested revision remains final 07-D regression authority：

```text
commit 6c8cd05e7a854a28c1396a26b4282bb6ecbc052b
tree   f4c7b338560b688577314d297e422bd248e6554f
```

07-D Stage-2 r19 correction series and later Stage-3 / Stage-4 accepted behavior are part of that regression lineage. In particular preserve accepted behavior for：

- outer terminal closure;
- upper reveal restoration;
- inner terminal tail;
- final Landing perimeter closure;
- U middle-Flight ownership;
- schema-4 persistence / Repair / lifecycle.

Existing 07-D saved Stair must not silently change merely because 07-E is installed.

---

# 3. Repository-only authority / review history

Reference images used during planning are **not implementation authority**。

Normative rule：

> **Codex implementation must be possible from repository text alone. No production algorithm may require looking at an external or chat-attached image to infer geometry.**

Consequences：

- 2段 / 3段 / 4段 / BF-1 / BF-2 are pattern identities, not image instructions.
- exact geometry is defined by vectors, intersections, event order and face ownership below.
- thumbnail/icon is UI aid only.
- if a reference image and this Specification disagree, this Specification wins.

07-E specification design was independently reviewed three times：

```text
Review 1: REVISE GEOMETRY CONTRACT
Review 2: REVISE GEOMETRY CONTRACT AGAIN
Review 3: ACCEPT WITH CLARIFICATIONS
```

Historical documents：

```text
BUILD_07_E_THIRD_PARTY_REVIEW.md
BUILD_07_E_SECOND_REVIEW.md
BUILD_07_E_THIRD_REVIEW.md
BUILD_07_E_REVIEW_REVISION_1.md
BUILD_07_E_REVIEW_REVISION_2.md
BUILD_07_E_FINAL_CLARIFICATIONS.md
BUILD_07_E_DESIGN_RATIONALE.md
```

are design audit / rationale records。Production implementation authorityは本SpecificationおよびSection 39のlater overrideとする。

---

# 4. Add-on identification / managed invariant

07-E production implementation：

```text
version = (0, 7, 4)
description = "Build 07-E: Winder + Arbitrary-angle Turn/Landing"
```

Managed state：

```text
1 Managed Stair = 1 Blender Mesh Object
```

内部ではFlight / Landing / Winder / Tread / Riser / Underbody / Side Boardを複数fragmentとして生成してよい。

Normal transform：

```text
Location = (0,0,0)
Rotation = (0,0,0)
Scale    = (1,1,1)
```

Canonical Data → Derived Geometryを維持し、生成MeshからPath / Turn mode / Winder patternを逆推定しない。

---

# 5. Core compatibility / schema policy

Current schema：

```text
schema 1 = BASIC legacy
schema 2 = 07-B Residential
schema 3 = 07-C Residential Straight
schema 4 = 07-D Multi-point / exact-90 Landing
schema 5 = 07-E Winder / generalized Turn
```

Existing schema-1/2/3/4 Stairはload時に自動upgradeしない。

Existing exact-90° schema-4 Landingについて次はschema 4のまま：

- load/open
- ordinary Regenerate
- Material edit
- Reverse
- accepted schema-4 exact-90 Path edit
- Repair

07-E Turn resolverのためにlegacy Straight / accepted schema-4 Landing resolverを破壊的に置換しない。

推奨architecture：

```text
legacy Straight resolver          preserve
07-D schema-4 Landing resolver    preserve
07-E schema-5 generalized Turn    add beside / above accepted foundation
```

Explicit schema-5 promotion examples：

- `LANDING -> WINDER`
- arbitrary-angle generalized Landing stateをcommit
- 07-E Winder pattern stateをcommit
- Compact-U Winder stateをcommit

---

# 6. Canonical Turn model

07-Eはaccepted 07-D Path point identityをTurn identityとして再利用する。

Normative：

```text
turn_identity = interior path_point_id
```

独立したpersistent `turn_id` UUIDを追加して`path_point_id`と二重管理しない。

Conceptual schema-5 Turn state：

```text
TurnSpec
├ path_point_id
├ turn_mode                LANDING | WINDER
└ winder_pattern           NONE | EQUAL_2 | EQUAL_3 | EQUAL_4 | BF_1 | BF_2
```

`winder_pattern`がsingle canonical pattern authority。

Derived mapping：

```text
NONE      -> step_count=0, rule=NONE
EQUAL_2   -> step_count=2, rule=EQUAL_ANGLE
EQUAL_3   -> step_count=3, rule=EQUAL_ANGLE
EQUAL_4   -> step_count=4, rule=EQUAL_ANGLE
BF_1      -> step_count=2, rule=BF_1
BF_2      -> step_count=2, rule=BF_2
```

`winder_step_count` / `winder_partition_rule`は独立persistent authorityにしない。Turn angleはPathからderivedする。

New schema-5 Residential Winder default：

```text
turn_mode      = WINDER
winder_pattern = EQUAL_3
```

Existing schema-4 Landingには適用しない。

---

# 7. Generalized 2D Turn frame

Interior Path point：

```text
T      = P_i
P_prev = P_(i-1)
P_next = P_(i+1)

a = normalize(T - P_prev)
b = normalize(P_next - T)
```

Signed Turn angle：

```text
theta = atan2(cross2(a,b), dot(a,b))
```

Convention：theta > 0 = left turn, theta < 0 = right turn。

For stair width `w`, resolve inside/outside offset lines and：

```text
I = intersection(incoming inside,  outgoing inside)
O = intersection(incoming outside, outgoing outside)
E_in  = I - w*inside_normal_in
E_out = I - w*inside_normal_out
```

Normalized Turn envelope：

```text
I -> E_in -> O -> E_out -> I
```

Same envelope is authority for arbitrary-angle Landing, equal-angle Winder, 90° BF Winder。Exact 90° / equal widthではaccepted 07-D nominal `w × w` Landing squareへ還元する。

---

# 8. Angle range / numerical singularity / Shift

Concept：`0° < abs(theta) < 180°`。Near-zero segment / near-straight / near-180 / non-finite intersection / excessive cutback等はgeometry singularityとしてreject可能。

Shift 15°はinteraction aidのみ。63°等をproduction restrictionでrejectしない。

---

# 9. Winder pattern construction

Common rays：

```text
r0 = normalize(E_in-I)
r1 = normalize(E_out-I)
r(f)=rotate(r0,f*theta)
```

Equal-angle patterns：

```text
EQUAL_2 = [1/2]
EQUAL_3 = [1/3,2/3]
EQUAL_4 = [1/4,1/2,3/4]
```

BF right-angle-only：

```text
BF_1=[2/3]
BF_2=[1/3]
```

Left/rightはsigned thetaでmirrorし、REVERSEはpersisted pattern identityを変更しない。

---

# 10. Nominal Winder cells / outer-chain completeness

Turn envelopeをordered nominal cellsへ分割し、complete envelope coverage / no positive-area overlap / no unintended gap / simple positive-area cells / deterministic windingを要求する。

Outer chain `E_in -> O -> E_out` の全geometry stationを保持し、90° EQUAL_3中央cell等で`O`をshortcutしてはならない。

---

# 11. RiseEvent ownership / exact Z sequence

```text
N = overall_riser_count
h = floor_to_floor/N
S + L + W + 1 = N
```

Every rise has exactly one destination owner。Compact-U zero middle straight run owns 0 straight tread events / 0 rises。

---

# 12. Riser ownership at component boundaries

Riser belongs to the higher/destination surface reached by that rise。Winder internal/entry/exit、Landing、Straight interfacesでdouble ownershipしない。Compact UではTurn B first treadがshared-transition rise/riserをownする。

---

# 13. AUTO allocation — exact deterministic procedure

Resolve `S_budget = N - L - W - 1`。Positive straight regionsは最低1 event、supported zero-runは0。Remaining eventsはlargest current `R_i/s_i`へcanonical physical Path-segment order tie-breakで配分する。

---

# 14. MANUAL / schema-4 -> schema-5 migration

Existing exact-90 schema-4 Landing ordinary operations remain schema 4。Explicit promotionのみschema 5へ。Schema-4 MANUAL LANDING→WINDERはAUTOへ明示変更するまでblock。FailureはPath/IDs/schema/allocation/mode/pattern/Mesh/Materials/Transformをatomic rollbackする。

---

# 15. Physical TREAD / RISER solids — historical Stage-2 r3 authority

> **Important 2026-10-05:** This section records the accepted Candidate-r3 Stage-2 physical geometry authority and historical rationale. For Stage 2.5 and the restarted Stage-3 baseline, **Section 39 supersedes this section where production Winder top geometry is concerned.** Candidate-r3 Acceptance history remains valid; Stage 2.5 is an intentional later baseline correction.

Candidate-r3 introduced Turn-wide semantic physical boundaries, exact shared rear-support/Riser-back authority, and a common inner physical finish chord `K_finish` to solve Stage-2 visual defects. The full historical formulas remain represented by the accepted Candidate-r3 implementation at:

```text
commit 9424da623953a32a97576ce45bec074b269d4058
tree   7d30e76ae20ad58b72cece1e298f54ee45f90a65
```

Key historical concepts include：

- `PhysicalWinderBoundary`
- `PhysicalWinderTreadPlan`
- `PhysicalWinderInnerTrim`
- `resolve_physical_winder_plans()`
- Turn-wide `K_finish`
- constant-distance positive nosing
- shared rear-support / destination-Riser back boundary

These concepts were Stage-2 r3 authority but are **not mandatory production authority after Stage 2.5**. See Section 39.

---

# 16. U / Compact U

07-E production U = existing 4-point / 2 persistent Turn foundation。Each Turn independently LANDING/WINDER + pattern。Compact classification uses middle run after both Turn cutbacks：positive=SEPARATED_U、near-zero=COMPACT_U、negative=INVALID_OVERLAP。COMPACT_U keeps both Path points / Turn identities and zero ordinary middle tread events。

---

# 17. Arbitrary-angle Landing / Winder

Landing uses generalized Turn envelope and event elevation。Exact 90° remains compatible with accepted square behavior。Arbitrary-angle Winder uses same generalized envelope + EQUAL patterns; BF remains right-angle-only。

---

# 18. Old-house / narrow-stair hard guardrail

No validator/RNA/UI/preset may reject solely because width <900/800/750mm。650mm is regression sample, not lower bound。Legal-like minima are not hard-coded geometry gates。

---

# 19. Error classes

```text
GEOMETRY_INVALID
SCOPE_UNSUPPORTED
ADVISORY_ONLY
```

Narrow/steep/tight but geometry-valid old-house dimensions are advisory-only, not generation blockers。

---

# 20. Winder STEPPED_CLOSED — historical reviewed contract

The original reviewed Stage-3 contract described schema-5 Winder stepped patches, divider ownership, exact contact clearance and closed-body behavior. **For the restarted Stage 3 after Stage 2.5, visible closure remains required, but precision/internal-contact requirements are superseded by Section 39. Hidden internal overlap is permitted.**

---

# 21. Winder SLOPED_CLOSED — historical reviewed contract

The original reviewed contract defined complete outer-chain preservation, finite pivot relief, strip/core decomposition, high-side pivot closure, shared-edge split propagation and exact contact/body segmentation. **These formulas remain historical design reference but are no longer mandatory implementation architecture for restarted Stage-3 r1 where they conflict with Section 39.**

Required visual intent remains：continuous turning closed soffit, no unintended horizontal Landing plateau, no visible exterior hole/spike/z-fighting。

---

# 22. Compact-U shared SLOPED Z / Reverse authority

Compact-U grouped ascent-order height interpolation remains a valid semantic reference. Restarted Stage 3 may use a simpler implementation provided visible geometry, deterministic Reverse behavior and event ownership remain correct。

---

# 23. Side Board authority at Winder

Preserve accepted 07-C independence：underside_mode controls lower board boundary; side_board_mode controls visible upper board variant. LEFT/RIGHT remain uphill-relative. Restarted Stage 3 may permit hidden board/body overlap; visible board shape must remain correct。

---

# 24. Compact-U shared-center Side Board

The original reviewed precision contract for shared profile union / exact 3D trim / butt-joint ownership is historical design reference. After Stage 2.5, restarted Stage-3 r1 may use a simpler visual-first implementation with hidden overlap, provided there is no visible double board, large spike, exterior z-fighting or open cavity. See Section 39.

---

# 25. Material contract

Roles remain BASE / TREAD / RISER / UNDERSIDE / SIDE_BOARD。No WINDER Material role。Regenerate / edit / Reverse / Repair / Save-Reopen / Undo-Redo preserve pointer/slot semantics。

---

# 26. Transaction / rollback / Diagnose / Repair

Candidate preparation occurs before Scene mutation。Failure leaves no partial schema-5 state。Repair policy remains accepted and does not invent geometry from invalid canonical data。

---

# 27. Save / reopen / Undo / Redo / Finalize / Delete

Preserve schema/state/IDs/Path/Turn mode-pattern/allocation/Materials/ascent/Residential fields/identity transform。Finalize converts to ordinary editable Mesh and ends management。Delete affects active managed Stair only。

---

# 28. Supported Path production scope

07-E final production acceptance requires 3-point L / 1 Turn and 4-point U / 2 Turns。3+ Turn Winder custom Path is not mandatory acceptance target。

---

# 29. Turn UI / pattern thumbnail

Each production Turn independently configures LANDING/WINDER and pattern。New schema-5 Winder default=EQUAL_3。Thumbnail is UI aid, not geometry authority。

---

# 30. Fixed expected-success fixtures

Historical fixed fixtures include narrow-width L, EQUAL_3 outer-corner, Compact-U, arbitrary-angle Landing and representative physical finish cases. For Stage 2.5, r1-equivalent visible Winder geometry identity and 07-D regression take priority over Candidate-r3 `K_finish`-specific physical assertions. Section 39 defines the Stage-2.5 acceptance target.

---

# 31. Stage 1 — canonical Turn + first 90° L Winder

**ACCEPTED.** Schema-5 foundation, path-point Turn identity, generalized frame, exact-90 EQUAL_2/3/4 nominal cells, RiseEvent/AUTO, SQUARE Winder top, transaction/rollback/basic persistence, legacy regression。

---

# 32. Stage 2 — BF + U / Compact U + arbitrary-angle

**ACCEPTED at Candidate r3.** Historical acceptance includes BF, per-Turn U/Compact-U, arbitrary-angle Landing/Winder, migration/allocation, deterministic regeneration and Candidate-r3 physical top refinements。

Candidate-r3 runtime identity：

```text
commit 9424da623953a32a97576ce45bec074b269d4058
tree   7d30e76ae20ad58b72cece1e298f54ee45f90a65
ZIP SHA256 15d48e9230b5a7e7f0b59954ccbe56acc7fb99bce3d26b39481f969f75c7b1d4
```

Stage 2.5 intentionally changes the future production baseline after this historical acceptance; it does not rewrite the historical acceptance result。

---

# 33. Stage 3 — CLOSED underbody + Side Board

**OLD FIRST ATTEMPT ABANDONED. RESTART AFTER STAGE 2.5.**

PR #33 is CLOSED / NOT MERGED / ABANDONED. Do not continue it as production baseline。

Restarted Stage 3 begins only after Stage 2.5 runtime acceptance and merge to `main`。The visual-first requirements and allowed hidden overlap are defined in Section 39。

---

# 34. Stage 4 — lifecycle / full regression / practical acceptance

Cover persistence, schema regressions, L/U/arbitrary, pattern/allocation, migration guard, Undo/Redo, rollback, Repair, Material, Reverse, Save/full exit/reopen, Finalize/Delete, Wall/Finish isolation, practical placement, deterministic Regenerate and full automated regression。07-E overall ACCEPTED only after Stage 4 runtime acceptance。

---

# 35. Automated / runtime test policy

Pure logic stays separated from Blender modal code。Prior 07-A/B/C/D suites remain regression targets。Runtime uses Console canonical evidence + visual inspection where appearance matters。

Stage 2.5 adds direct r1-equivalent Winder visible-geometry comparison and 07-D Landing/Residential regression checks. Restarted Stage 3 emphasizes visible exterior correctness and lifecycle stability rather than exact hidden-solid topology。

---

# 36. Acceptance principles

07-E overall still requires schema compatibility, deterministic patterns/Turn authority, RiseEvent correctness, migration safety, valid L/U/arbitrary-angle production, CLOSED Winder body, Side Boards, narrow-house support, atomic rollback, lifecycle, Material, isolation and practical placement。

However, after Stage 2.5 the following old precision requirements are no longer universal blockers for restarted Stage-3 r1：

- exact internal positive-volume elimination;
- exact whole-stair union;
- exact internal BodyInterface ownership;
- zero hidden overlap;
- hidden duplicate/internal faces。

Visible exterior defects remain blockers。

---

# 37. Explicit non-scope

No spiral/helical stair, curved Flight centerline, freehand curved Winder, per-divider custom editor, code-compliance judgment, variable width within one Flight, non-uniform riser heights, 07-F open/support variants, handrail/newel/baluster, automatic Wall/Floor/Room attachment, automatic Stair opening Boolean, production UV guarantee, general panel redesign, 3+ Turn Winder production guarantee。

---

# 38. Final implementation order

Updated order：

```text
accepted 07-D compatibility
    ↓
07-E Stage 1 ACCEPTED
    ↓
07-E Stage 2 Candidate r3 ACCEPTED
    ↓
Stage 2.5 — restore Candidate-r1-equivalent visible Winder top narrowly
    ↓
Stage 2.5 runtime acceptance + merge
    ↓
fresh Stage 3 branch
    ↓
visual-first STEPPED_CLOSED
    ↓
visual-first SLOPED_CLOSED
    ↓
ordinary / Compact-U Side Board
    ↓
Stage 4 lifecycle / practical acceptance
```

Do not restart Stage 3 from PR #33。

---

# 39. Stage 2.5 / restarted Stage 3 normative override

This section is the **later project decision** adopted after direct Blender runtime experience with the first Stage-3 implementation. It supersedes conflicting older geometry requirements in Sections 15, 20–24, 30, 32–38 for the Stage-2.5 / restarted-Stage-3 path。

## 39.1 Why this override exists

Candidate-r3 Stage 2 produced a high-quality isolated Winder finish, but its r2/r3 Turn-wide physical-plan and `K_finish` authorities complicated downstream body integration. The first Stage-3 branch accumulated precision-oriented internal-solid architecture and then regressed visible geometry, including Winder top, SLOPED body penetration, and previously accepted 07-D Landing/Residential geometry in runtime tests。

The project goal is a practical Blender modeling aid, not a CAD/BIM watertight-solid kernel。

Therefore：

> **Visible exterior correctness and stable Blender workflow outrank hidden internal solid cleanliness.**

## 39.2 PR #33

First Stage-3 PR #33：

```text
status = ABANDONED / CLOSED / NOT MERGED
```

Its branch is historical/reference only. Do not repair it further and do not use it as fresh Stage-3 baseline。

## 39.3 Stage-2 runtime artifact authority

The preserved runtime ZIPs were directly audited：

```text
Candidate r1
commit b0d92fc15f7ec103e3cf18b6110dce2b5841fd3e
tree   e90e4bfa0e0583552bc761a200b8e51a52590470
SHA256 8c6c7100e0a51e550525fedca0e214e95b5ca8b73874ce4c7b213d9149f62054

Candidate r2
commit 26ddf5b79bb933ea6b8bf43a3a4c585c11ddf597
tree   9c4804864dab6e07cfd54be8f38c85fae671cd1a
SHA256 2d6e34b4589ea993995903fdbe30dfd8c68559daae2438ca955ced0563fd5cac

Candidate r3
commit 9424da623953a32a97576ce45bec074b269d4058
tree   7d30e76ae20ad58b72cece1e298f54ee45f90a65
SHA256 15d48e9230b5a7e7f0b59954ccbe56acc7fb99bce3d26b39481f969f75c7b1d4
```

Recursive ZIP comparison：

```text
r1 -> r2 : stair_turn.py only
r2 -> r3 : stair_turn.py only
r1 -> r3 : stair_turn.py only
```

This proves the Stage-2.5 visible-top restoration can be narrow. Do not roll the whole repository backward。

## 39.4 Exact r1 production path to recover

Candidate r1 visible Winder TREAD/RISER production used the simpler per-cell path：

```text
physical_winder_tread_polygon(...)
resolve_winder_riser_plan(...)
```

Candidate r2 introduced：

```text
PhysicalWinderBoundary
PhysicalWinderTreadPlan
resolve_physical_winder_plans(...)
```

Candidate r3 added：

```text
PhysicalWinderInnerTrim
K_finish
inner_front
inner_rear
inner_edge
```

Stage 2.5 must：

1. keep current accepted Stage-2 r3 codebase as structural base;
2. preserve BF / U / Compact-U / arbitrary-angle / migration / allocation / UI / serialization / lifecycle functionality;
3. restore the **r1-equivalent visible Winder TREAD/RISER production call behavior** from Candidate r1;
4. bypass r2/r3 Turn-wide physical-plan / `K_finish` authority in production where necessary to reproduce r1 geometry;
5. avoid whole-file rollback;
6. avoid modifying accepted 07-D Landing / Straight body geometry。

Later helper classes/functions may remain in source if unused; production path authority matters more than code deletion。

## 39.5 Candidate-r1 known defect deliberately tolerated

Candidate r1 had a visible terminal TREAD/RISER / Turn-transition gap in some views。

For Stage 2.5：

```text
known r1 terminal gap = ALLOWED / NOT A STAGE-2.5 BLOCKER
```

Do not reintroduce r2/r3 physical-plan complexity during Stage 2.5 just to close this gap. It can be revisited after a successful restarted Stage-3 r1 exists。

## 39.6 Stage-2.5 geometry identity target

For selected reference fixtures, Stage-2.5 Winder visible geometry should be numerically equivalent to Candidate r1 within named project tolerance：

- TREAD vertices;
- RISER vertices;
- polygon ordering;
- Z elevations;
- ordinal/event ordering;
- FORWARD / REVERSE;
- exact-90 EQUAL_3 reference fixture。

Blender visual confirmation remains mandatory。

## 39.7 Stage-2.5 must preserve 07-D

Build 07-D runtime-accepted Landing / Straight / underside / Residential geometry is regression authority。

Stage 2.5 and restarted Stage 3 must not rebuild or replace 07-D exact-90 Landing geometry merely to make Winder implementation easier。

Mandatory Stage-2.5 runtime regression includes exact-90 07-D Landing visible body/underside check。

## 39.8 Restarted Stage-3 visual-first acceptance profile

Required：

- visible exterior geometry is plausible and coherent;
- no obvious exterior hole/daylight gap created by Stage 3;
- no major spike/giant filler face;
- no externally visible z-fighting;
- no missing major component;
- no nonfinite/collapsed geometry;
- no generation exception;
- lifecycle / persistence remains stable;
- Stage-2.5 accepted Winder top remains unchanged;
- accepted 07-D Landing / Straight body remains unchanged。

Allowed internally：

- UNDERBODY may penetrate TREAD/RISER in hidden regions;
- Straight/Winder/Landing bodies may overlap internally;
- Side Board may intersect hidden geometry;
- hidden duplicate/internal faces may exist;
- separate closed components may overlap;
- exact whole-stair Boolean union is not required。

Not required for restarted Stage-3 r1：

- exact SLOPED convex decomposition;
- exact intersection-volume elimination;
- global PHYSICAL_CONTACT classification;
- exact internal union;
- volume conservation proof;
- internal duplicate-face cleanup;
- exact BodyInterface union proof。

## 39.9 Restarted Stage-3 implementation order

```text
Stage 2.5 accepted + merged main
    ↓
new/fresh Stage-3 branch
    ↓
STEPPED_CLOSED visible body, Side Boards OFF
    ↓
SLOPED_CLOSED visible body, Side Boards OFF
    ↓
ordinary Side Board
    ↓
Compact-U Side Board
    ↓
Material / Reverse / lifecycle regressions
```

One focused Blender runtime test at a time is preferred. High-risk visible geometry takes priority over broad low-risk test repetition during active geometry iteration。

## 39.10 Stage-2.5 acceptance and merge rule

Stage 2.5 is not accepted merely because automated tests pass。

Before merge：

- exact-90 EQUAL_3 r1-equivalent visible Winder check;
- 63° arbitrary-angle Winder smoke check;
- FORWARD / REVERSE;
- 07-D exact-90 Landing visible regression;
- Save -> full Blender exit -> reopen smoke check;
- automated prior 07-D / 07-E regressions;
- dedicated Stage-2.5 Acceptance Record。

Only after Stage-2.5 acceptance may it merge to `main` and a fresh Stage-3 branch be created。

## 39.11 Documentation precedence

For Stage 2.5 and restarted Stage 3, precedence is：

```text
1. Section 39 of BUILD_07_E_SPECIFICATION.md
2. BUILD_07_E_STAGE_2_5_PLAN.md
3. Current ROADMAP.md status/order
4. Earlier sections of BUILD_07_E_SPECIFICATION.md
5. Historical review documents / PR #33 comments
```

Existing Acceptance Records remain historical truth and must not be rewritten to claim Candidate r1 was previously accepted as Stage 2 final. Stage 2.5 is a later deliberate correction baseline。
