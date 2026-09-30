# BUILD 07-E SPECIFICATION
## 日本住宅モデラー — Winder / 廻り段 + Arbitrary-angle Turn / Landing

> **Status: REVIEW CANDIDATE / THIRD-PARTY REVIEW PENDING**  
> Date: 2026-09-30  
> Build 07-D overall Acceptance を baseline とし、07-D の accepted Multi-point Path / L / U / Landing / lifecycle contract を壊さず、Turn Foundation を Winder / 廻り段および arbitrary-angle Turn / Landing へ拡張する。
>
> **重要:** この版は第三者レビュー用候補であり、まだ `FINAL / IMPLEMENTATION AUTHORITY` ではない。第三者レビューと必要な修正が完了するまで、Codexへ production implementation を依頼しない。

---

## 1. Purpose

Build 07-E は、Build 07-D までに成立した Straight / L / U / Multi-point Landing Stair を維持したまま、日本住宅で一般的に使われる廻り段と、変形住宅で必要になる90°以外の折れ曲がり階段を **1つの Managed Stair** として生成・編集できる production foundation を完成させる Build である。

中心目的は次の10点とする。

1. 07-D の `TurnSpec` / Multi-point / Flight foundation を再利用し、`WINDER` turn mode を追加する。
2. 90° L字 Winder を production 対応する。
3. U字 / コの字のoverall 180°方向転換を、既存2 Turn foundation上の Winder combination として production 対応する。
4. 90°Turnについて、2段廻り / 3段廻り / 4段廻りを標準 equal-angle pattern として提供する。
5. BF-1 / BF-2 を均等角分割とは別の住宅用 asymmetric pattern family として提供する。
6. Turn angle を exact 90°限定から一般化し、valid な arbitrary-angle Landing を production 対応する。
7. valid な arbitrary-angle Winder を、少なくとも `EQUAL_ANGLE` partition で production 対応する。
8. Winder step を含む overall riser / height distribution を Stair 全体で一貫させる。
9. `STEPPED_CLOSED` / `SLOPED_CLOSED` / Side Board を Winderへ継続し、とくに `SLOPED_CLOSED` は水平Landing plateauを挟まない連続した廻り下面を作る。
10. 07-E完了時点で一般住宅の直線＋折れ曲がり階段の主要ゴールとし、07-F / 07-Gを保留して08-A / 08-Bへ進める状態にする。

07-E は建築基準法適合判定ソフトを作る Build ではない。既存住宅・古い木造住宅の狭い階段もモデリング対象とし、法規上の推奨寸法と geometry validity を明確に分離する。

---

## 2. Accepted baseline

07-E は以下を baseline とする。

- Build 05-B — Wall System — ACCEPTED
- Build 06-A / 06-B / 06-C — Finish system — ACCEPTED
- Build 07-A — Stair Core + Straight — ACCEPTED
- Build 07-B — Standard Residential Straight Stair — ACCEPTED
- Build 07-C — Sloped Closed Underside + Straight Finish Variants — ACCEPTED
- Build 07-D — Multi-point Path + L / U + Landing — overall ACCEPTED
- `BUILD_07_D_SPECIFICATION.md`
- `BUILD_07_D_ACCEPTANCE_RECORD.md`
- `BUILD_07_E_DESIGN_RATIONALE.md`
- `DEVELOPMENT_WORKFLOW.md`
- `ROADMAP.md`

07-E specification/code baseline main:

```text
commit 4e46e04b9f3813810d2707ae9a773fd3f98fe9f9
tree   0db32165ec527869c19781e63f4ab783703c8539
```

07-D exact Stage-4 runtime-tested revision remains regression authority:

```text
commit 6c8cd05e7a854a28c1396a26b4282bb6ecbc052b
tree   f4c7b338560b688577314d297e422bd248e6554f
```

Existing 07-D saved Stair must not silently change merely because 07-E is installed.

---

## 3. Design rationale / repository-only implementation rule

`BUILD_07_E_DESIGN_RATIONALE.md` records the design reasons behind this Specification and is a required review companion. The implementation authority will remain this Specification once promoted to FINAL; the rationale document exists so a third-party reviewer can understand **why** the requirements exist and challenge them before implementation.

### 3.1 Renovation-use rationale

The target workflow includes existing old houses where:

```text
existing stair remains structurally unchanged
↓
wall / floor / finish is renovated
↓
existing stair remains visible in the presentation
↓
JHM must reproduce that existing stair
```

Therefore a stair must not become unmodelable merely because it is narrower, steeper, tighter, or less regular than a present-day new-build recommendation.

### 3.2 Reference-image rule

Reference images used during design discussion are **not implementation authority**.

Normative rule:

> **Codex implementation must be possible from repository text alone. No production algorithm may require looking at an external or chat-attached image to infer geometry.**

Consequences:

- 2段 / 3段 / 4段 / BF-1 / BF-2 are pattern identities, not image instructions.
- exact geometry is defined below by vectors, intersections and partition fractions.
- no legal or industry-standard expansion of the label `BF` is assumed.
- thumbnails/icons are UI aids only and never canonical geometry authority.
- if a reference image and this final text contract disagree, the text contract wins.

### 3.3 Alternatives intentionally rejected

07-E does **not** use the following designs:

- one hard-coded mesh generator per pattern;
- `3段廻り = 30°` as the internal data model;
- legal-like minimum stair width as a geometry gate;
- every U middle segment being forced to be a normal Flight;
- two U Turn IDs being replaced by one fake persistent 180° Turn;
- separate 45° / 60° / 90° Landing generators;
- reference images as coding instructions;
- top geometry, underside and Side Board being debugged simultaneously from Stage 1.

---

## 4. Roadmap position

```text
07-A  Stair Core + Straight                         ACCEPTED
  ↓
07-B  Standard Residential Straight                ACCEPTED
  ↓
07-C  Sloped Closed Underside / Finish Variants    ACCEPTED
  ↓
07-D  Multi-point L / U + Landing                   ACCEPTED
  ↓
07-E  Winder + arbitrary-angle Turn / Landing       CURRENT
  ↓
07-F  HOLD
07-G  HOLD / Optional Backlog
  ↓
08-A  Minimal Room / Boundary + Floor
  ↓
08-B  Ceiling + Void / Hole
  ↓
Known Issue 8.5 correction
  ↓
Integration Core
```

07-E Acceptance後は07-F / 07-Gを一旦保留し、08-A / 08-Bと早期一室Core統合試験を優先する。

---

## 5. Add-on identification

07-E production implementation:

```text
version = (0, 7, 4)
description = "Build 07-E: Winder + Arbitrary-angle Turn/Landing"
```

Stage途中の Candidate も07-E production codeを含む場合は同じBuild identityを使用してよい。

---

## 6. Core compatibility rule

07-Eは既存Stairを別方式へ作り直すBuildではない。

必須：

- schema-1 BASIC Straightをloadしただけで変更しない。
- schema-2 07-B Straightをloadしただけで変更しない。
- schema-3 07-C Straightをloadしただけで変更しない。
- schema-4 07-D L / U / Landingをloadしただけで変更しない。
- existing exact-90° Landingは07-E install時にWinderへ自動変換しない。
- ordinary Regenerateでaccepted 07-D Landing geometry / allocation / Material / IDsを変更しない。
- 07-E Turn resolverのためにlegacy Straight / 07-D Landing resolverを破壊的に置換しない。

推奨：

```text
legacy Straight resolver          preserve
07-D schema-4 Landing resolver    preserve
07-E schema-5 generalized Turn    add beside / above accepted foundation
```

---

## 7. Managed Stair invariant

07-Eでも基本は：

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

Canonical data → Derived Geometryを維持し、生成MeshからTurn pattern / Winder step / Pathを逆推定しない。

---

## 8. Schema policy

07-E current schema：

```text
schema = 5
```

```text
schema 1 = BASIC legacy
schema 2 = 07-B Residential
schema 3 = 07-C Residential Straight
schema 4 = 07-D Multi-point / Landing
schema 5 = 07-E Winder / generalized Turn
```

Existing schema-1/2/3/4 Stairはload時に自動upgradeしない。

schema 5へ移行する例：

- Turn modeを`LANDING -> WINDER`へ変更
- new 07-E Winder pattern stateを保存
- exact-90°以外のgeneralized Landing stateをcommit
- compact-U Winder stateを保存

schema-4 exact-90° Landingを単にRegenerate / Reverse / Material editするだけならschema 4のまま維持する。

---

## 9. Canonical Turn model

07-DのTurn anchorを拡張する。

```text
TurnSpec
├ turn_id
├ path_point_id
├ turn_mode                LANDING | WINDER
├ winder_pattern           NONE | EQUAL_2 | EQUAL_3 | EQUAL_4 | BF_1 | BF_2
├ winder_step_count        derived/validated canonical value
├ winder_partition_rule    NONE | EQUAL_ANGLE | BF_1 | BF_2
└ future partition parameters if later required
```

Turn angle自体はPath geometryから導出する。

```text
incoming direction
+
outgoing direction
↓
signed turn angle theta
```

同じ情報を`turn_angle`として重複canonical保存しないことを基本とする。必要ならdiagnostic / cached derived valueとして扱う。

Turnはpersistent `turn_id` と `path_point_id` でPath anchorへ結び付け、Object名や表示indexだけに依存しない。

`winder_step_count` と `winder_partition_rule` は別概念である。

---

## 10. Generalized 2D Turn frame — normative geometry

すべての07-E Landing / Winder plan geometryは同じgeneralized Turn frameから始める。

Interior Path point：

```text
T      = P_i
P_prev = P_(i-1)
P_next = P_(i+1)

a = normalize(T - P_prev)   # incoming direction toward T
b = normalize(P_next - T)   # outgoing direction away from T
```

Signed turn angle：

```text
theta = atan2(cross2(a, b), dot(a, b))
```

Project XY conventionで：

```text
theta > 0  = left turn
theta < 0  = right turn
```

Define：

```text
s = sign(theta)
left_normal(d) = (-d.y, d.x)
inside_normal_in  = s * left_normal(a)
inside_normal_out = s * left_normal(b)
```

Stair width `w` の4 corridor offset lines：

```text
incoming inside : T + (w/2) * inside_normal_in  + lambda * a
incoming outside: T - (w/2) * inside_normal_in  + lambda * a

outgoing inside : T + (w/2) * inside_normal_out + mu * b
outgoing outside: T - (w/2) * inside_normal_out + mu * b
```

Resolve：

```text
I = intersection(incoming inside,  outgoing inside)   # inner pivot / inside corner
O = intersection(incoming outside, outgoing outside) # outer miter corner
```

Cross-section outer endpoints through `I`：

```text
E_in  = I - w * inside_normal_in
E_out = I - w * inside_normal_out
```

Normalized Turn envelope：

```text
I -> E_in -> O -> E_out -> I
```

polygon windingはgeometry helper内で一貫してnormalizationする。

このsame envelopeを：

- arbitrary-angle Landing
- equal-angle Winder
- 90° BF Winder

で共有する。

Exact 90° / equal widthではaccepted 07-D nominal `w × w` Landing squareへ還元されること。

### 10.1 Derived cutback diagnostic

Symmetric equal-width turnのcenterline cutback magnitude：

```text
d = (w/2) * tan(abs(theta)/2)
```

Production実装はactual resolved cross-sectionからcutbackを求めてもよいが、pure testでordinary casesについてこのclosed-form resultと整合することを確認する。

この式はgeometryであり、法規minimumではない。

---

## 11. Turn angle generalization / numerical singularity

07-D productionはexact ±90°だったが、07-Eではsingle Turnを一般化する。

Concept：

```text
0° < abs(theta) < 180°
```

ただし、以下はnumerical / geometric singularityとしてrejectできる：

- incoming / outgoing segmentがnear-zero length
- thetaが0°へ近すぎてdistinct Turn envelopeを安定解決できない
- thetaが±180°へ近すぎてsingle-Turn miterが数値的にsingular
- required intersectionsがnon-finite
- required cutbackがavailable adjacent Path lengthを超える

`eps_length` / `eps_area` / `eps_angle` を使用する場合：

- project既存geometry tolerance方針に合わせる
- code/testsでnamed numerical epsilonとして明示する
- residential code minimumとして命名・利用しない
- 45° / 63° / 82° / 105°等をpreset外という理由でrejectしない

Exact 180° reversalをsingle Turn anchorへ押し込まず、U字は既存Multi-point 2 Turn foundationを使う。

### 11.1 Shift 15°との関係

07-D accepted Shift 15°は操作補助として維持する。

```text
Shift OFF = free angle
Shift ON  = nearest 15° candidate
```

Production Turn angle自体を15°刻みに限定しない。

90° / parallel / X/Y / extension guideもcandidate guideであり、07-Eでは90°へ強制補正するruleではない。

---

## 12. 90° L Winder production scope

L字は1 Turnで約90°方向転換する代表caseとする。

Production pattern：

```text
EQUAL_2 = 2段廻り
EQUAL_3 = 3段廻り
EQUAL_4 = 4段廻り
BF_1
BF_2
```

2/3/4はequal-angle family。

```text
90° / 2 = 45° + 45°
90° / 3 = 30° + 30° + 30°
90° / 4 = 22.5° × 4
```

ただしgeneratorを「3段なら30°」へhard-codeせず、`theta / n`のgeneral ruleから導出する。

---

## 13. Equal-angle Winder — exact construction

Turn envelopeがvalidとする。

Entry / exit rays from inner pivot：

```text
r0 = normalize(E_in  - I)
r1 = normalize(E_out - I)
```

`r0 -> r1` のsigned angular sweepはresolved Turn sweep `theta` と一致する。

`n` Winder treadsの場合：

```text
fractions = [j/n for j in 1 ... n-1]
```

各fraction `f`：

```text
r_f = rotate(r0, f * theta)
R_f(t) = I + t * r_f, t > 0
```

`R_f`をouter chain：

```text
E_in -> O -> E_out
```

へ交差させ、nearest valid positive intersection `Q_f` を選ぶ。

```text
I -> Q_f
```

をWinder division boundaryとする。

Turn envelopeをcanonical entry-to-exit orderで`n`個のsimple tread polygonsへ分割する。

```text
EQUAL_2 fractions = [1/2]
EQUAL_3 fractions = [1/3, 2/3]
EQUAL_4 fractions = [1/4, 1/2, 3/4]
```

Arbitrary-angle example：

```text
theta = 72°
n = 3
→ 24° × 3
```

72°専用generatorは作らない。

---

## 14. BF-1 / BF-2 — exact JHM normalized construction

BF-1 / BF-2はJHM project内のnormalized pattern identityとする。外部法規・業界規格上の`BF`意味を主張しない。

07-E productionではBF patternをapproximately/exactly 90° single Turnに限定する。既存07-D exact-90°判断と同等のgeometry toleranceを使用し、範囲外ならBFを使用せず`EQUAL_ANGLE`または`LANDING`を選択する。

BF patternは**2 Winder treads / 1 internal division boundary**を持つ。

### 14.1 BF-1

```text
BF_1 fractions = [2/3]
```

Canonical entry-to-exit angular spans：

```text
60° , 30°
```

### 14.2 BF-2

```text
BF_2 fractions = [1/3]
```

Canonical entry-to-exit angular spans：

```text
30° , 60°
```

### 14.3 Construction

Equal-angle Winderと同じray / outer-chain intersection algorithmを使い、fraction listだけを変える。

### 14.4 Left / right Turn

Separate left/right meshを作らない。

```text
left turn  -> positive signed theta
right turn -> negative signed theta
```

同じfractionをsigned rotationへ適用し、planを自然にmirrorする。

### 14.5 Reverse ascent

`REVERSE`はcanonical Path orderを書き換えず、`BF_1 <-> BF_2` identityも変更しない。

Physical plan subdivisionは同じ。Elevation / ascent traversalだけを反転する。

同じcanonical Pathで逆のasymmetric physical partitionが必要なら、userが明示的にもう一方のpatternを選ぶ。

---

## 15. Stair width / old-house renovation hard guardrail

これは07-Eの主要project requirementである。

### 15.1 Widthを法規風minimumでrejectしない

Core geometry validatorは、次の理由だけでrejectしてはならない：

```text
stair_width < 900 mm
stair_width < 800 mm
stair_width < 750 mm
```

また、design referenceにあった以下のような値をuniversal generation minimumへhard-codeしない：

```text
300 mm
150 mm
85 mm
```

次のようなhidden equivalentも禁止する：

```text
MIN_LEGAL_STAIR_WIDTH = 750
MIN_LEGAL_WINDER_TREAD = ...
```

07-E coreはlegal compliance engineではない。

### 15.2 Width変更時

Width変更時は：

```text
same canonical Path
+
new stair_width
↓
Turn envelope
Winder tread polygons
cutback
effective straight runs
underside
Side Board
```

を同じwidth authorityから再解決する。

### 15.3 Warningは許可

Geometryがvalidなら：

- very narrow stair
- very narrow inner tread region
- unusually tight / steep old-house-like configuration

についてnon-blocking advisory warningを表示してよい。

ただしlegal compliance / non-complianceを断定しない。

### 15.4 Required width regression

Automated / runtime representative testには少なくとも：

```text
900 mm
800 mm
750 mm
700 mm
650 mm
```

のgeometry-valid 90° Winder caseを含める。

PASS：

> Widthだけを理由にrejectされない。Narrow caseがFAILする場合はactual geometry failureのevidenceが必要で、code-like minimum thresholdであってはならない。

---

## 16. Geometry validation policy

### 16.1 ERROR / atomic reject

数学的・Mesh的に成立しない場合だけblockする。

最低限：

- non-finite coordinate
- adjacent Path collapse
- unsupported numerical single-point reversal
- invalid / non-positive Turn envelope area
- tread polygon self-intersection
- adjacent Winder tread positive-area overlap
- unintended gap in required walking-surface coverage
- zero / near-zero area polygon or edge beyond numerical tolerance
- division order reversal
- partition rayがrequired outer chainへ交差しない
- Flight / Turn cutbackがavailable segment length内で成立しない
- Winder regionとunrelated Path segmentが自己交差
- unsupported positive-area overlap of neighboring Turn envelopes
- underside / Side Boardをcritical invalid geometryなしに生成できない

ERROR時はcanonical / Mesh / Materials / IDsをpartial commitしない。

### 16.2 WARNING / allow

Geometryとして成立するがnarrow / steep / unusualなcaseはproduction可能とする。

Warningはlegal pass/fail判定ではない。

---

## 17. Exact rise-event ownership

Winderはplan decorationではなく、actual vertical sequenceへ参加する。

```text
N = overall_riser_count
h = floor_to_floor / N
```

Geometry生成前にphysical `RiseEvent` ownershipを解決する。

Every rise event has exactly one destination owner：

```text
STRAIGHT_TREAD
WINDER_TREAD
UPPER_ARRIVAL
```

Rules：

1. independent straight treadは、そのtread直前のrise eventを1つ所有する。
2. each Winder treadは、そのWinder tread直前のrise eventを1つ所有する。
3. Upper floor arrivalはfinal rise eventを1つ所有する。
4. 同じeventをFlightとWinderで二重countしない。
5. Winder treadはplan-onlyではなく必ずvertical sequenceに参加する。

Let：

```text
S = total independent straight-tread events
W = total Winder tread count across all Turns
N = overall riser_count
```

Invariant：

```text
S + W + 1 = N
```

`+1`はfinal upper-arrival rise。

Equivalent component form：

```text
sum(straight_region rise events)
+
sum(winder_step_count)
=
N
```

ただしfinal straight regionのrise-event countはupper-arrival eventを含む。

### 17.1 Straight region ownership

Non-final positive straight region：

```text
rise events = number of independent straight treads
```

Final straight region：

```text
rise events = independent straight treads + 1 upper-arrival event
```

Compact-U zero ordinary middle run：

```text
0 straight tread events
0 rise events
```

このownershipがtread elevations / riser boardsのauthorityである。

---

## 18. AUTO distribution under schema 5

Resolve order：

```text
1. overall N
2. all Winder patterns and W = sum(winder_step_count)
3. reserve 1 final UPPER_ARRIVAL event
4. straight independent-tread budget = N - W - 1
5. resolve effective positive straight runs
6. deterministic integer apportionment across those runs
7. add final UPPER_ARRIVAL event to final Flight ownership
8. validate going / turn / body / board candidate
9. atomic commit
```

Zero effective straight runは0 straight tread eventsを受け取る。

```text
N - W - 1 < 0
```

ならreject。

Allocatorはdeterministic。Tieはcanonical Path / component orderで解決する。

Path / width / Turn pattern変更時はcandidate全体を再解決し、sum invariantを満たした場合だけcommitする。

---

## 19. MANUAL distribution / schema-4 migration

### 19.1 Existing schema-4 MANUAL

Existing schema-4 MANUAL allocation semanticを、LandingをWinderへ変えるだけでsilent reinterpretしてはならない。

Winder tread eventsを追加しながら旧Flight countsをそのまま維持するとriseがdouble-countされ得る。

Initial 07-E conservative production rule：

```text
schema-4 MANUAL
+
request LANDING -> WINDER
↓
transaction reject with clear message
↓
user explicitly switches to AUTO
↓
convert to schema 5 Winder
↓
user may switch resulting schema-5 state to MANUAL
```

既存schema-4 MANUAL LandingはTurnがLANDINGのままなら完全に維持する。

### 19.2 Schema-5 MANUAL

schema-5 MANUALでは：

- Winder pattern / step countはuser選択を保持する。
- straight-region component allocationをexplicitに保持する。
- total rise-event invariantを必須とする。
- invalid totalを勝手に補正しない。
- Path/width変更でallocationがinvalidになったらtransactionをreject / rollbackする。
- AUTO→MANUAL時はcurrent resolved schema-5 component allocationを初期値にする。

UI wordingは既存07-Dと整合させつつ、schema-5で「Winder step count」と「straight allocation」が別authorityであることを曖昧にしない。

---

## 20. U / コの字 = overall 180° direction change

JHM canonical authorityは**per Turn**であり、overall 180°専用のfake persistent mesh/presetを正としない。

Existing 07-D U：

```text
P0 -> P1 -> P2 -> P3
       T1    T2
```

通常は2つの約90°Turnを持つ。

07-EではTurn 1 / Turn 2を個別設定できる。

例：

```text
Turn 1 = EQUAL_2
Turn 2 = EQUAL_3
```

```text
Turn 1 = BF_1
Turn 2 = EQUAL_3
```

この方式でU用全組み合わせを別presetとして大量登録しない。

2/3/4 per-Turn combinationにより、overall 180°側では4,5,6,7,8等のWinder tread countを自然に構成できる。

### 20.1 BF U reference families

Convenience interpretation：

```text
U BF-family 1
Turn 1 = BF_1
Turn 2 = BF_2
aggregate = 60°, 30°, 30°, 60°

U BF-family 2
Turn 1 = BF_2
Turn 2 = BF_1
aggregate = 30°, 60°, 60°, 30°
```

Canonical storageはあくまでindividual Turn assignments。

---

## 21. Compact U — exact derived rule

Two consecutive Turn anchors：

```text
T1 = P_i
T2 = P_(i+1)

m = normalize(T2 - T1)
L_mid = length(T2 - T1)
```

各Turn envelopeをsame stair widthから独立解決する。

Turn 1がmiddle segment上で消費するexit cutback：

```text
d1 = exit_cutback_on_middle_segment
```

Turn 2がmiddle segment上で消費するentry cutback：

```text
d2 = entry_cutback_on_middle_segment
```

Residual：

```text
R_mid = L_mid - d1 - d2
```

Classification：

```text
R_mid > +eps_length
    = SEPARATED_U
    = positive ordinary middle straight run remains

abs(R_mid) <= eps_length
    = COMPACT_U
    = zero ordinary middle straight run

R_mid < -eps_length
    = INVALID_OVERLAP
    = Turn envelopes require positive-area overlap
```

`eps_length`はnumerical toleranceのみ。

Two exact 90° equal-width Turns：

```text
d1 = w/2
d2 = w/2
COMPACT_U when L_mid ~= w
```

よってactual widthへscaleする：

```text
w=900 mm -> compact middle separation ~=900 mm
w=750 mm -> compact middle separation ~=750 mm
w=650 mm -> compact middle separation ~=650 mm
```

900mm固定ではない。

### 21.1 COMPACT_U invariants

- two Turn envelopesはsame transition cross-sectionでtolerance内にmeetする。
- positive-area overlapは禁止。
- walking-surface gapは禁止。
- middle Path segmentと両point IDs / Turn IDsはcanonicalに残す。
- middle segment owns 0 ordinary straight tread events / 0 rise events。
- derived `Composite U Winder Group`はgeometry resolution専用で、persistent fake Turnを作らない。

### 21.2 SEPARATED_U

`R_mid > eps_length`ならresidual runをordinary straight regionとして扱う。

Actual lengthとallocationが成立するかをvalidationし、Winderをsilent stretchしてinvalid allocationを隠さない。

### 21.3 INVALID_OVERLAP

`R_mid < -eps_length`ならchosen Path/width/anglesでrequired Turn envelopesがpositive-area overlapするためrejectする。

これはgeometry errorでありlegal-width errorではない。Widthを狭くした結果、同じPathがvalidになることは許可する。

---

## 22. Arbitrary-angle Landing — exact polygon rule

Arbitrary-angle `LANDING`はSection 10と同じTurn envelopeを使用する。

Walking surface：

```text
Landing polygon = [I, E_in, O, E_out]
```

normalized winding。

Interfaces：

```text
entry = I -> E_in
exit  = I -> E_out
outer visible chain = E_in -> O -> E_out
```

Properties：

- exact 90° / equal widthでaccepted nominal `w × w` 07-D Landingへ還元。
- arbitrary angleはcorridor geometryから導出し、fixed squareを無理に回転しない。
- 47° / 63° / 82°等もsame algorithm。
- Landing top Zはconstantで07-D cumulative-rise semanticsを継承。
- walking surface Material=`TREAD`、closed body/underside=`UNDERSIDE`。
- required cutbackがadjacent Path lengthを超えたらatomic reject。

45° / 60° / 90°専用Landing generatorを作らない。

---

## 23. Arbitrary-angle Winder

Production minimum：

```text
same generalized Turn envelope
+
EQUAL_ANGLE partition
```

Example：

```text
theta = 63°
step count = 3
fractions = [1/3, 2/3]
→ 21° + 21° + 21°
```

BF-1 / BF-2は07-Eではapproximately/exactly 90° residential patternとしてproduction対応し、arbitrary thetaへ一般化しない。

Arbitrary-angle Winderでも：

- ordered simple tread polygons
- no positive-area overlap
- no self-intersection
- exact rise sequence
- closure-valid underside / board in supported Stage

を満たす。

---

## 24. Turn mode / pattern UX

07-E new residential Multi-point StairのTurn defaultはRoadmap方針に従い`WINDER`を基本案とする。

各Turnを個別選択可能：

```text
Turn 1
Mode:    WINDER | LANDING
Pattern: 2段 | 3段 | 4段 | BF-1 | BF-2

Turn 2
Mode:    WINDER | LANDING
Pattern: 2段 | 3段 | 4段 | BF-1 | BF-2
```

Landing時はPattern UIをdisabled / hiddenにする。

Existing schema-4 Landingはload時にnew defaultの影響を受けない。

### 24.1 Thumbnail / icon minimum

Pattern selectionは文字labelだけでもcanonical correctnessを損なわないが、production UIでは小さなplan icon/thumbnailを優先する。

Minimum：

- EQUAL_2/3/4はSection 13のfractionから同じnormalized 90°turn iconを描けること。
- BF_1/BF_2はSection 14のfractionから描けること。
- icon image自体をgeometry authorityとして保存しない。
- external reference image fileをruntime dependencyにしない。
- 06-C thumbnail architectureを参考にしてよいがCustom Profile libraryへ混在させない。

---

## 25. Tread / Riser geometry

Winder treadはTurn envelope内のordered polygonとして生成する。

必須：

- tread thicknessはexisting Residential fieldを継承。
- riser thicknessもexisting fieldを継承。
- each Winder tread top elevationはRiseEvent sequenceからexactに決定。
- adjacent tread間のvertical Riser boardを生成。
- tread front overhang / basic front-edge treatmentはgeometryが成立する範囲で07-C contractを適用。
- inner regionでnosingがself-intersect / reverseする場合はsupported geometry ruleで処理できなければatomic reject。
- Winder front edgeはstep boundary / progressionから決定し、Straightの単一local X axisをTurn全体へ流用しない。

---

## 26. STEPPED_CLOSED Winder underside

`STEPPED_CLOSED`はWinderでもclosed invariantを維持する。

下から見たとき：

- tread backsideを露出しない
- riser backsideを露出しない
- internal cavityを見せない
- Winder stepへ追従するhorizontal / vertical closureが連続
- Flight ↔ Winder ↔ Flight joinにlarge gap / spikeを作らない
- Side Board ON/OFFに依存せずbody自体がclosed

Winder footprintがirregularでもStraight boxの大量重ね合わせでduplicate positive-volume bodyを作らない。

---

## 27. Continuous SLOPED_CLOSED Winder soffit

07-Eの重要production target。

Landing：

```text
Flight slope
→ horizontal Landing underside
→ Flight slope
```

Winder：

```text
Lower Flight sloped soffit
        ↓ continuous height progression
ordered Winder lower-surface stations
        ↓
Upper Flight sloped soffit
```

Requirements：

- lower Flight boundary ↔ Winder soffit C0 position continuity。
- Winder soffit ↔ upper Flight boundary C0 position continuity。
- Winder中に不要なhorizontal Landing plateauを作らない。
- ascent orderに沿うheight progressionを維持する。
- plan directionが曲がるためsingle infinite planeである必要はない。
- piecewise planar / triangulated surfaceを許可。
- C1 tangent continuityは07-E必須にしない。
- no open cavity / giant filler prism / duplicate positive-volume body。
- same Path / width / RiseEvent authorityをtop geometryと共有。
- underside thickness / body depthは07-C contract継承。

Implementationはtop-plan Winderがruntime acceptedになった後のStage 3で行う。

---

## 28. Side Board continuation at Winder

`STEPPED` / `SLOPED` Side BoardをWinderへ継続する。

Requirements：

- left/right physical sideがuphill traversalに対してstable。
- Turn / Reverseでunexpected side swapしない。
- outer boardはresolved outer Turn chainから導出。
- inner boardはresolved inner boundary / pivot regionから導出。
- Flight ↔ Winder joinはsame derived boundary positionsを共有。
- compact U centerでboard collision / positive-area overlapを検査。
- tight inner pivotではtrim / segmented joinを許可。
- Material role=`SIDE_BOARD`。
- disconnected visual patchを後付けして誤魔化さない。

1巨大polygonよりdeterministic fragments + clean visible joinを優先する。

---

## 29. Material contract

Existing rolesを維持：

```text
BASE
TREAD
RISER
UNDERSIDE
SIDE_BOARD
```

New `WINDER` Material roleは追加しない。

```text
Winder walking treads = TREAD
Winder risers         = RISER
Winder soffit/body    = UNDERSIDE
Winder side boards    = SIDE_BOARD
Landing walking       = TREAD
Landing body          = UNDERSIDE
```

Regenerate / Path edit / Turn pattern edit / Reverse / Repair / Save-Reopen / Undo-Redoでpointer / slot semanticsを保持する。

---

## 30. Reverse ascent

Reverseはcanonical Path orderを書き換えずtraversalのみ反転する。

```text
FORWARD: P0 -> ... -> Pn
REVERSE: Pn -> ... -> P0
```

Winder plan footprintはsame XY routeを使用し、elevation sequenceを反転する。

BF/equal-angle pattern identityはReverseだけで変更しない。

Physical Turn pattern assignmentはsame `turn_id`へ保持する。

---

## 31. Turn edit / Path edit

07-D accepted START / END / every TURN mouse relocationを維持する。

Point move：

```text
candidate Path
↓
turn angle / frame resolve
↓
turn envelope / pattern resolve
↓
RiseEvent allocation
↓
Flight + Landing/Winder + underside + board prepare
↓
validation
↓
atomic commit
```

90°から外れたことだけを理由にrejectしない。

Shift 15° / X/Y / extension / 90° / parallel guideは継続。

ESC / RMB cancelはcanonical / Mesh / Material / IDsを変更しない。

1 point move = 1 Undo step。

---

## 32. Numeric Path edit

Numeric Path editもsame schema-5 transaction pathを使用する。

Userがarbitrary angleを精密入力可能。

Turn angleを別canonical inputとしてPathと矛盾させるUIは作らない。AngleはPathからderived表示する。

例：

```text
Turn 1 Angle: 63.4° Left
Turn 2 Angle: 91.2° Right
```

---

## 33. Transaction / rollback contract

07-D `_transactional_update` principleを継承する。

Scene mutation前に最低限prepare：

- canonical Path validation
- generalized Turn frame / angle
- Turn envelope
- Landing/Winder mode
- Winder pattern/partition
- Winder tread polygons
- RiseEvent ownership / allocation
- effective straight runs
- Tread/Riser
- supported CLOSED underside
- Side Board
- Material slot plan
- topology validation where practical

Rollback target：

- old Mesh datablock
- path_points / point IDs
- Turn IDs / modes / patterns
- distribution mode / component allocation
- dimensions
- ascent direction
- 07-C Residential fields
- Materials / slots
- Stair ID
- Object Transform

Failure時にpartial schema-5/Winder stateを残さない。

---

## 34. Diagnose / Repair

Existing recoverable policyを継承：

- ID_MISSING
- ID_CONFLICT
- TRANSFORM_CHANGED
- GEOMETRY_MISSING

Invalid schema-5 canonicalをRepairが推測変更しない。

Geometry missing / transform changedはsame valid canonicalから再生成。

Duplicate IDはStair IDだけを変更。

Repair時にWinder step count / pattern / Path / Materials / allocationsを保持する。

---

## 35. Save / reopen / Undo / Redo

07-E Acceptance必須。

Save / fully exit Blender / reopen後に保持：

- schema 5
- Stair ID
- Path points / point IDs
- Turn IDs
- Turn mode
- Winder pattern / step count / partition rule
- AUTO / MANUAL state
- resolved component allocation authority
- Materials
- ascent direction
- Residential fields
- identity Transform

Undo / Redo representative：

- LANDING ↔ WINDER
- 2/3/4/BF pattern change
- arbitrary-angle Path point move
- Reverse
- Material edit

UndoとRedoの間にConsole操作を挟まない既存runtime policyを維持する。

---

## 36. Finalize / Delete / isolation

07-D contractを維持する。

Finalize：

```text
Managed Stair
↓
ordinary editable Mesh
↓
JHM management ends
```

Deleteはactive managed Stair only。

Winder内部fragmentを別Managed Objectとして選択削除するlifecycleへ変更しない。

Wall / Finish / floor-like unrelated objectsをmutationしない。

---

## 37. User-facing validation messages

単一の「生成できません」だけにしない。

最低限原因を区別：

- Path segmentが短すぎてTurn cutbackが成立しません
- Winder分割線がTurn外周へ正しく交差しません
- Winder踏板が自己交差しています
- 隣接するTurn領域が重複しています
- このMANUAL配分ではWinder段数を含む総蹴上数が一致しません
- schema-4 MANUAL LandingをWinderへ変更する前にAUTOへ切り替えてください
- このBF patternは90°Turn用です

Narrow width自体をerror wordingにしない。

---

## 38. Explicit non-scope

07-Eでは必須にしない：

- spiral / helical stair
- curved Flight centerline
- freehand curved Winder edge
- each split lineを1本ずつ自由編集するcustom partition editor
- automatic building-code compliance judgment
- legal pass/fail表示
- variable stair width along one Flight
- non-uniform riser heights within one Stair
- Riser OFF / Underside NONE / open/support variants（07-F）
- sawtooth / center support（07-F）
- handrail / newel / baluster
- separate Winder Material role
- automatic Wall / Floor / Room attachment
- automatic Stair opening / Floor Boolean
- production UV guarantee
- default stair width 900→750等の全体default変更
- general Stair panel compacting / collapsible UI redesign
- Winder以外の広範なUX整理

Current default widthは07-E中900mmのままでよい。重要なのはuserがnarrower geometry-valid valueへ変更したときcode-like minimumで拒否されないこと。

---

## 39. Stage 1 — canonical Turn + first visible 90° L Winder

目的：上面plan geometryを先に固め、下面・側板debuggingと分離する。

Implementation minimum：

- identity 0.7.4
- schema-5 foundation
- schema-1/2/3/4 regression
- generalized Turn frame / signed angle pure helpers
- `WINDER` Turn mode
- 90° L Winder
- EQUAL_2 / EQUAL_3 / EQUAL_4
- exact envelope / pivot / partition rules
- Winder Tread + Riser production geometry
- exact RiseEvent ownership
- AUTO allocation extension
- one Managed Mesh
- Material roles compatible
- transaction / rollback

Stage 1ではBF / compact U / arbitrary-angle production / final underside / Side Boardを完成させなくてよい。

### Stage 1 runtime focus

- existing 07-D L Landing unchanged
- L Winder EQUAL_2/3/4 top appearance
- exact total rise / Winder elevations
- no tread overlap / zero-area
- Reverse basic
- Save/reopen basic
- invalid partition rollback
- width representative 900 / 750 / 650 where geometry remains valid
- width alone does not trigger reject

---

## 40. Stage 2 — BF + U / Compact U + arbitrary-angle

目的：07-E plan / Path / vertical ownership機能を完成。

Implementation：

- BF_1 / BF_2 fractions exactly as Section 14
- generated thumbnail/icon selection from normalized rules
- Turn 1 / Turn 2 independent pattern
- U / overall 180° combination
- BF U reference combinations
- exact Compact-U `R_mid` resolver
- separated U
- arbitrary-angle Landing exact polygon
- arbitrary-angle `EQUAL_ANGLE` Winder
- free-angle point relocation
- Shift 15° remains convenience only
- AUTO schema-5 full allocation
- schema-4 MANUAL conversion guard
- schema-5 MANUAL component allocation
- deterministic multi-turn regeneration

### Stage 2 runtime focus

- L EQUAL_2/3/4/BF_1/BF_2
- BF left/right mirror
- BF identity stable across Reverse
- U 2+3 / BF_1+3 / BF_1+BF_2 examples
- Compact U no false short-middle-flight reject
- separated U remains valid
- Turn 1 / Turn 2 individual edit
- exact 45° Landing
- non-15-multiple numeric Landing, e.g. ~63°
- arbitrary-angle equal-angle Winder
- FORWARD / REVERSE
- invalid self-intersection / overlap rollback
- width 900 / 800 / 750 / 700 / 650 geometry-valid regression

---

## 41. Stage 3 — Closed underside + Side Board production finish

目的：07-Dで苦労した下面 / 側板を、Winder top geometry acceptance後に独立して完成する。

Implementation：

- STEPPED_CLOSED Winder continuation
- continuous SLOPED_CLOSED Winder soffit
- Flight ↔ Winder ↔ Flight closure
- compact U underside
- STEPPED Side Board continuation
- SLOPED Side Board continuation
- inner/outer boundary mapping from same Turn geometry
- Material lifecycle
- Reverse
- Regenerate / Repair
- topology cleanup

### Stage 3 runtime focus

- SLOPED_CLOSEDにhorizontal Landing plateauが残らない
- visible slope progression continuous through Winder
- no cavity / spike / giant filler prism / duplicate positive-volume body
- inside/outside board no side-swap
- compact U center no board collision
- boards OFFでもbody CLOSED
- Material roles exact
- width 900 / 800 / 750 / 700 / 650 representative valid cases
- L / U / arbitrary-angle representative

---

## 42. Stage 4 — lifecycle / full regression / practical acceptance

Final acceptance must cover：

- Candidate identity
- schema-1 / 2 / 3 / 4 regression
- schema-5 L / U / arbitrary-angle persistence
- EQUAL_2/3/4 + BF persistence
- AUTO / MANUAL persistence
- schema-4 MANUAL migration guard
- Undo / Redo
- invalid rollback
- Geometry Repair
- Transform Repair
- duplicate ID Repair
- Material lifecycle
- Reverse
- Finalize
- active-only Delete
- abnormal Delete
- Wall / Finish isolation
- practical Wall / Floor-like placement
- narrow-width old-house-like representative cases
- topology finite / zero-area / boundary / nonmanifold
- deterministic repeated Regenerate
- full automated regression
- compileall
- git diff --check

07-E overall ACCEPTEDはStage 4完了後のみ。

---

## 43. Automated test architecture

Pure/testable logicをBlender modal codeから分離する。

最低限 pure test対象：

- signed turn angle
- inside/outside normals
- generalized corridor-line intersections
- Turn envelope coordinates / winding / area
- exact 90° reduction to `w × w`
- cutback formula equivalence
- equal-angle fractions / outer-chain intersection
- BF_1 `[2/3]` / BF_2 `[1/3]`
- left/right signed mirror
- Reverse pattern identity stability
- tread polygon simple / area / coverage / overlap
- width-independent scaling
- RiseEvent ownership
- `S + W + 1 = N`
- AUTO allocation with fixed Winder counts
- schema-4 MANUAL conversion rejection
- schema-5 MANUAL validation
- Compact-U `R_mid` classification
- arbitrary-angle Landing polygon
- arbitrary-angle equal-angle Winder
- numerical singularity handling
- no legal-like width gate
- schema compatibility
- deterministic geometry

Stageごとにdedicated `tests/test_build_07_e_stageN.py`を追加する。

Prior 07-A / 07-B / 07-C / 07-D suitesをregression targetとする。

---

## 44. Runtime test policy

`DEVELOPMENT_WORKFLOW.md`を継承する。

原則：

```text
Console canonical evidence
+
必要箇所だけ目視
```

Undo / Redo：

```text
UI operation
↓
Ctrl+Z
↓
Ctrl+Shift+Z
↓
then Console
```

Winder tread shape / BF pattern / arbitrary Landing polygon / Compact U / underside continuity / Side Board joinは目視必要。

Canonical pattern / IDs / angle / allocations / topology / MaterialsはConsole evidenceを主とする。

Runtime testsは一度に大量提示せず、Development WorkflowどおりTest単位でPASS/FAILを判断する。

---

## 45. Acceptance principles

07-Eは以下を満たした場合のみoverall ACCEPTEDとする。

1. Existing schema-1/2/3および07-D schema-4 Straight/L/U/Landingを壊さない。
2. 90° L Winder EQUAL_2/3/4が同一general ruleから安定生成される。
3. BF_1=`[2/3]` / BF_2=`[1/3]`がtext-only ruleからdeterministicに生成される。
4. U / overall 180° Winderをper-Turn combinationとして作れる。
5. Compact Uが`R_mid` ruleでzero ordinary middle runを正しく扱い、false short-flight rejectを起こさない。
6. Arbitrary-angle Landingをsingle generalized envelope algorithmで生成できる。
7. Arbitrary-angle `EQUAL_ANGLE` Winderをrepresentative caseで生成できる。
8. Shift 15°はinteraction aidのままで、production angle restrictionにならない。
9. Width 900/800/750/700/650でgeometry-valid caseはwidth aloneでrejectされない。
10. 300/150/85等のreference dimensionsをcore reject thresholdへhard-codeしない。
11. Invalid geometryはclear error + atomic rollbackする。
12. Winderを含むRiseEvent ownershipがdouble-countせず、overall rise invariantがexact。
13. schema-4 MANUAL Landingをsilent redistributionでWinderへ変換しない。
14. `SLOPED_CLOSED`がWinder through-turnでhorizontal Landing plateauなしのcontinuous closed soffitとなる。
15. `STEPPED_CLOSED` / Side BoardもWinderで重大なgap / spike / cavity / side-swapを作らない。
16. Save/reopen / Undo/Redo / Repair / Finalize / Delete / Materialsが成立する。
17. Wall / Finishへ回帰を起こさない。
18. Practical residential placementで重大な破綻がない。
19. Reference imageなしでrepository textだけからimplementationとreviewが可能。

---

## 46. Third-party review package

第三者reviewerは少なくとも以下を読む：

```text
ROADMAP.md
BUILD_07_D_SPECIFICATION.md
BUILD_07_D_ACCEPTANCE_RECORD.md
BUILD_07_E_SPECIFICATION.md
BUILD_07_E_DESIGN_RATIONALE.md
DEVELOPMENT_WORKFLOW.md
```

Review questions：

- schema-1/2/3/4のsilent migrationを防げているか。
- Turn envelope constructionはleft/right / oblique turnで数学的に整合するか。
- exact 90° Landingが07-D nominal `w × w`へ還元するか。
- `winder_step_count`と`winder_partition_rule`が十分分離されているか。
- BF_1/BF_2は画像なしで再現可能か。
- BF left/right / Reverse contractに曖昧さがないか。
- Compact U `R_mid` classificationは十分か。
- arbitrary-angle Landingがangle-specific special caseなしで定義されているか。
- RiseEvent ownershipにdouble-count / missing eventがないか。
- schema-4 MANUAL→WINDERのconservative ruleが安全か。
- validatorがhidden building-code gateになり得る箇所がないか。
- width 700/650mmのvalid old-house caseをmodelできるか。
- numerical epsilonとlegal-like thresholdが明確に分離されているか。
- SLOPED_CLOSED contractはLanding-like plateau再発を防ぐのに十分か。
- Side Boardがsame Turn geometryからderiveされるか。
- Stage分割が07-Dのunderside debugging問題を繰り返さない構成か。
- Renovation visualization goalに対して不要に高価 / 過剰な要件がないか。
- Roadmap / 07-D accepted contract / 07-E proposed contractに矛盾がないか。

Reviewerはexact section/invariantを示して改善案を出すことを期待する。

---

## 47. Review-to-FINAL gate

このReview Candidateを`FINAL / IMPLEMENTATION AUTHORITY`へ上げる前に：

1. Third-party reviewを実施する。
2. 指摘を仕様へ採用 / 非採用判断し、必要な修正をrepositoryへ反映する。
3. `BUILD_07_E_DESIGN_RATIONALE.md`と本Specificationの矛盾をなくす。
4. Reference imageなしで全production geometry ruleがtext-onlyに再現可能であることを再確認する。
5. legal-sounding numeric valuesがcore geometry gateへ紛れ込んでいないことを確認する。
6. Statusを`FINAL / IMPLEMENTATION AUTHORITY`へ変更する。
7. その後に初めてCodex Stage 1 implementation instructionを作成する。

---

## 48. Final implementation rule

07-Eでは、07-D Stage 2のように上面・下面・側板の問題を同時に抱えない。

順序：

```text
accepted 07-D compatibility
    ↓
generalized Turn frame / canonical model
    ↓
90° L EQUAL_2/3/4
    ↓
BF + U / Compact U
    ↓
arbitrary-angle Landing / Winder
    ↓
RiseEvent distribution
    ↓
closed underside
    ↓
Side Board
    ↓
full lifecycle / practical test
```

Top-plan geometryがruntimeでacceptedになる前に、複雑なSLOPED_CLOSED / Side Board correctionへ進まない。

UserのBlender runtime visual reviewでWinder tread / BF / Compact-U geometryに問題があれば、Stage acceptance前にSpecification addendum / correctionとして修正する。

07-E Acceptance完了後はRoadmapどおり07-F / 07-Gを保留し、08-A / 08-Bへ進む。
