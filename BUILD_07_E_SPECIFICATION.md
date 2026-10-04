# BUILD 07-E SPECIFICATION
## 日本住宅モデラー — Winder / 廻り段 + Arbitrary-angle Turn / Landing

> **Status: FINAL / IMPLEMENTATION AUTHORITY + STAGE 2.5 OVERRIDE**  
> Date: 2026-09-30  
> Stage 2.5 override added: 2026-10-05  
> Build 07-D overall Acceptance を baseline とし、07-D の accepted Multi-point Path / L / U / Landing / lifecycle contract を壊さず、Turn Foundation を Winder / 廻り段および arbitrary-angle Turn / Landing へ拡張する。
>
> **Implementation authority:** Codex は本ファイルだけで production geometry / migration / validation / lifecycle を実装できなければならない。外部画像・chat添付画像・過去のreview文書から不足する形状を推測してはならない。**ただし、末尾 Section 39 は 2026-10-05 の later project decision であり、Stage 2.5 / restarted Stage 3 に関して旧Section 15 / 20–24 / 30 / 32–38 と矛盾する場合は Section 39 を優先する。**

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

are design audit / rationale records。**Production implementation authorityは本Specificationだけ**とする。

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
├ path_point_id            # persistent Turn identity authority
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

`winder_step_count` / `winder_partition_rule`は意味上別概念だが、schema-5では独立persistent authorityにしない。diagnostic/cacheとして保持する場合、`winder_pattern`と不一致ならrecomputeする。

Turn angleはPathからderived：

```text
incoming direction
+
outgoing direction
↓
signed theta
```

同じ`turn_angle`をduplicate canonical保存しない。

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

Convention：

```text
theta > 0 = left turn
theta < 0 = right turn
```

Define：

```text
s = sign(theta)
left_normal(d) = (-d.y, d.x)
inside_normal_in  = s * left_normal(a)
inside_normal_out = s * left_normal(b)
```

For stair width `w`：

```text
incoming inside : T + (w/2)*inside_normal_in  + lambda*a
incoming outside: T - (w/2)*inside_normal_in  + lambda*a

outgoing inside : T + (w/2)*inside_normal_out + mu*b
outgoing outside: T - (w/2)*inside_normal_out + mu*b
```

Resolve：

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

Same envelope is authority for：

- arbitrary-angle Landing
- equal-angle Winder
- 90° BF Winder

Exact 90° / equal widthではaccepted 07-D nominal `w × w` Landing squareへ還元する。

Symmetric equal-width centerline cutback diagnostic：

```text
d = (w/2) * tan(abs(theta)/2)
```

これはgeometry relationであり法規minimumではない。

---

# 8. Angle range / numerical singularity / Shift

Concept：

```text
0° < abs(theta) < 180°
```

ただし次はnumerical / geometry singularityとしてrejectできる：

- adjacent segment near-zero length
- theta too close to 0° for stable distinct Turn
- theta too close to ±180° for stable single-Turn miter
- non-finite required intersection
- required cutback exceeds available adjacent Path length

`eps_length / eps_area / eps_angle`はnamed numerical toleranceであり、住宅法規minimumとして利用しない。

Exact 180° reversalを1 persistent Turnへ押し込まない。07-E production Uはexisting 4-point / two-Turn foundationを使う。

Shift 15°：

```text
Shift OFF = free angle
Shift ON  = nearest 15° candidate
```

interaction aidのみ。63°等をproduction angle restrictionでrejectしない。

---

# 9. Winder pattern construction

## 9.1 Common rays

```text
r0 = normalize(E_in  - I)
r1 = normalize(E_out - I)
```

For fraction `f`：

```text
r(f)   = rotate(r0, f*theta)
R_f(t) = I + t*r(f), t>0
```

`R_f`をordered outer chain：

```text
E_in -> O -> E_out
```

へ交差させ、nearest valid positive intersectionをdivider outer point `Q_f`とする。

Division boundary：

```text
I -> Q_f
```

## 9.2 Equal-angle patterns

```text
EQUAL_2 fractions = [1/2]
EQUAL_3 fractions = [1/3, 2/3]
EQUAL_4 fractions = [1/4, 1/2, 3/4]
```

Exact 90°：

```text
2段 = 45° + 45°
3段 = 30° + 30° + 30°
4段 = 22.5° × 4
```

Generatorを「3段=30°」へhard-codeせず`theta/n`のgeneral ruleから導出する。

Arbitrary example：

```text
theta=63°, EQUAL_3 -> 21° + 21° + 21°
```

## 9.3 BF-1 / BF-2

JHM normalized project identity。外部規格上のBF意味を主張しない。

07-E BF productionはaccepted right-angle predicate/tolerance内のapproximately/exactly 90° single Turnのみ。

```text
BF_1 fractions = [2/3] -> canonical entry order 60°,30°
BF_2 fractions = [1/3] -> canonical entry order 30°,60°
```

同じray / outer-chain algorithmを使い、fractionだけ変える。

Outside BF toleranceは`SCOPE_UNSUPPORTED`。Canonical Pathを90°へsilent snapしない。

## 9.4 Left/right / Reverse

left/rightはsigned `theta`でmirrorする。別mesh generatorを作らない。

`REVERSE`はphysical subdivision / persisted `BF_1` / `BF_2` identityを変更しない。

Example：canonical entryで`BF_1 = 60°,30°`でもReverse ascentでは上る人から`30°,60°`に見える。保存名は`BF_1`のまま。

---

# 10. Nominal Winder cells / outer-chain completeness

Turn envelopeをordered nominal cells：

```text
C_1 ... C_n
```

へ分割する。

Boundaries：

```text
D0 = entry
D1 ... D(n-1) = internal divider
Dn = exit
```

Ascent orderで：

```text
front/downhill boundary = D(j-1)
rear/uphill boundary    = Dj
```

Nominal validation：

- complete envelope coverage
- no positive-area overlap
- no unintended gap
- simple positive-area cells
- deterministic winding/order

### 10.1 Preserve every outer-chain vertex

Outer chainはexact：

```text
E_in -> O -> E_out
```

Cell interval `[f_k, f_(k+1)]` は、そのangular interval内の**全outer-chain vertex**を保持する。

Outer corner fraction：

```text
f_O = signed_angle(r0, normalize(O-I)) / theta
```

同じsigned sweep conventionだけを使う。unsigned angleとsigned `theta`を混在させない。

If：

```text
f_k < f_O < f_(k+1)
```

then `O` is required geometry station。

典型90° EQUAL_3中央cell：

```text
Q_1 -> O -> Q_2
```

`Q_1 -> Q_2`でshortcutしてはならない。

Dividerが`O`を通る場合：

```text
Q_k ~= O within named epsilon
```

は1 geometry stationへdeduplicateし、zero-length outer edgeを作らない。

Geometry-only stationはWinder step / RiseEventを増やさない。

---

# 11. RiseEvent ownership / exact Z sequence

```text
N = overall_riser_count
h = floor_to_floor / N
```

Every rise has exactly one destination owner：

```text
STRAIGHT_TREAD
LANDING_ARRIVAL
WINDER_TREAD
UPPER_ARRIVAL
```

Let：

```text
S = total independent straight-tread RiseEvents
L = total LANDING_ARRIVAL RiseEvents
W = total WINDER_TREAD RiseEvents
```

Invariant：

```text
S + L + W + 1 = N
```

`+1` = final Upper Arrival。

Maintain event counter `c=0` at `B=base_z`。

For each destination surface：

```text
c := c+1
surface_top_z = B + c*h
```

Therefore：

- straight tread j after c0 prior events: `B+(c0+j)h`
- Landing arrival: `B+(c0+1)h`
- Winder tread j: `B+(c0+j)h`
- final Upper Arrival: `B+N*h`

Compact-U zero middle straight run owns 0 straight tread events / 0 rises。

---

# 12. Riser ownership at component boundaries

Riser belongs to the higher/destination surface reached by that rise。

For Winder boundaries `D0...Dn`：

- Riser on `D0` is owned by Winder tread 1.
- Riser on internal `Dj` is owned by Winder tread `j+1`.
- Winder tread n does not create an extra riser on `Dn`.
- next destination surface after `Dn` owns the next rise/riser.

Examples：

```text
Straight -> Winder : first Winder tread owns interface riser
Winder -> Straight : first following Straight tread owns next riser
Straight -> Landing: Landing owns arrival riser
Landing -> Straight: first following Straight tread owns next riser
Winder -> Landing  : Landing owns next riser
Landing -> Winder  : first Winder tread owns next riser
```

Compact U：first tread of Turn B owns the shared-transition rise/riser。Turn A must not duplicate it。

---

# 13. AUTO allocation — exact deterministic procedure

Resolve：

```text
L = count(LANDING Turns)
W = sum(step_count of WINDER Turns)
S_budget = N - L - W - 1
```

Resolve straight regions and effective run `R_i`。

For each：

```text
R_i > eps_length -> s_i >= 1
R_i ~= 0         -> s_i = 0 only for explicitly supported zero-run transition
```

07-E primary zero-run case = Compact-U middle region。

Let `P` be positive straight regions and `m=len(P)`。

Validation：

```text
S_budget >= m
```

unless `m=0`, then `S_budget=0`。

Initial：

```text
s_i=1 for each positive straight region
s_i=0 for supported zero-run region
```

Distribute each remaining event one at a time to the region with largest current：

```text
R_i / s_i
```

Tie-break：canonical physical Path-segment order, not Reverse traversal order。

After allocation：

```text
g_i = R_i / s_i
```

Straight 07-C validators apply to ordinary positive straight regions only。

Winder cell itself has no scalar `g_i` and the zero-width inner pivot must not be passed to Straight `going` validators。

If minimum one-tread-per-positive-region cannot be met, reject before mutation with specific allocation error。

---

# 14. MANUAL / schema-4 -> schema-5 migration

## 14.1 Operations that stay schema 4

Existing exact-90 Landing ordinary load / Regenerate / Material / Reverse / exact-90 Path edit / Repair remain schema 4。

## 14.2 Explicit generalized-Landing promotion

For schema-4 physical Flight allocation `r_i`, when explicitly promoting while keeping LANDING：

```text
s_i = r_i - 1
```

For `F` straight regions：

```text
L = F-1
sum(r_i)=N
sum(s_i)+L+1=N
```

Example：

```text
schema-4 U MANUAL r=[6,5,5]
-> schema-5 LANDING s=[5,4,4]
L=2, W=0
5+4+4+2+1=16
```

Candidate must be revalidated before commit。

## 14.3 LANDING -> WINDER

Schema-4 MANUAL：

```text
LANDING -> WINDER
```

is blocked until user explicitly switches to AUTO。Do not silently invent redistribution。

Schema-4 AUTO may explicitly promote to schema 5 and run schema-5 AUTO allocation。

Valid schema-5 result may later switch AUTO→MANUAL; initial MANUAL values copy current resolved schema-5 straight-region allocation。

Schema-5 MANUAL must satisfy `S+L+W+1=N`; invalid total is rejected, not silently repaired。

## 14.4 Arbitrary-angle edit

"90°から外れたことだけでrejectしない" applies after explicit schema-5 promotion。Legacy schema-4 point edit remains exact-90 authority。

## 14.5 Rollback

Promotion failure restores：

- schema version
- old allocation
- Turn mode / pattern
- Path / point IDs
- Mesh
- Materials
- Object Transform

atomically。

---

# 15. Physical TREAD / RISER solids

Nominal plan cells and physical finish solids are separate validation layers。Nominal Winder cells `C_j` remain unchanged。

## 15.1 Physical Winder boundary authority

For each ascent-local semantic boundary `B=(P_inner,P_outer)` between a lower/downhill tread and its destination/uphill tread：

```text
u    = normalize(P_outer-P_inner)
m_up = unit normal perpendicular to u, toward destination/uphill tread

L_face = B
L_nose = B - n*m_up
L_back = B + r*m_up
```

`n` is tread front nosing and `r` is riser thickness / accepted rear-support extension。Distances are exact perpendicular distances：

```text
distance(L_nose,L_face)=n
distance(L_back,L_face)=r
```

Derive these three parallel semantic lines once per boundary and reuse them for every incident physical fragment。Do not independently recompute near-equal copies。

### 15.1.1 Physical tread plan

For Winder tread `C_j`：

```text
front physical boundary = front/downhill L_nose
rear physical boundary  = rear/uphill L_back
```

Resolve the physical tread plan from these offset lines plus the ordered Turn outer chain / immediate neighboring walking-region trim。First derive the raw intermediate：

```text
M_j = intersection(front L_nose,rear L_back)
```

`M_j` determines the safe common inner finish chord in §15.1.4; it is not the final visible inner corner。Final inner points are `L_nose ∩ K_finish` and `L_back ∩ K_finish`。The physical finish is not forced to nominal pivot `I`。

Forbidden：

- retaining `I` as physical front/rear vertex merely because it is the nominal divider origin;
- moving only the outer endpoint while keeping `I` fixed;
- tapering positive nosing toward zero at `I`;
- hiding the opening later with Stage-3 Underbody or Side Board。

The mathematical pivot remains nominal subdivision authority only。

### 15.1.2 Outer-chain and neighbor trim

Trim front/rear offset lines using the deterministic local walking domain：complete `E_in -> O -> E_out` outer chain, the immediate neighboring Winder cell, or the immediate adjacent Straight/Landing walking region at entry/exit。Do not extend into an unrelated Turn sector。

If an offset line crosses outer-corner station `O`, preserve required split stations consistently。Every trim intersection which becomes a semantic shared point is reused exactly by incident fragments。

### 15.1.3 Positive nosing at inner side

For `n>0`, every point of the resolved exposed Winder front edge lies on `L_nose`。Its signed perpendicular distance from `L_face` equals `n` within named epsilon at both endpoints。The inner endpoint may and normally does move away from `I`。

Do not accept `outer ~= n` but `inner ~= 0` solely because the nominal cell converges to `I`。If no finite local trim can preserve `n` without self-intersection or unrelated-sector intrusion, reject as `GEOMETRY_INVALID`; never silently reduce `n`。

### 15.1.4 Common inner physical finish chord

The mathematical pivot `I` remains nominal subdivision authority only。Per-tread raw `M_j` is an intermediate construction point, never automatically the final visible inner corner。All physical Winder TREAD/RISER finish geometry for one Turn uses one deterministic common inner trim authority。

#### 15.1.4.1 Turn-local trim frame

```text
R0 = normalize(E_in-I)
Rn = normalize(E_out-I)
b  = normalize(R0+Rn)
h_j = dot(M_j-I,b)
eps_l = named length epsilon
c_finish = max(n,r,10*eps_l)
h_finish = max(0,max_j(h_j))+c_finish
K_finish: dot(X-I,b)=h_finish
```

`K_finish` is perpendicular to `b`。`c_finish` is derived physical-finish regularization only, never a legal/width minimum or user-facing regulatory rule。

#### 15.1.4.2 Finite finish chord

Intersect `K_finish` with boundary rays `I+t*R0` and `I+t*Rn` to obtain finite `J_entry` and `J_exit`。Both must occur strictly before their outer-chain endpoints within epsilon; `K_chord=segment(J_entry,J_exit)` must lie inside the Turn walking envelope and every required semantic line must intersect it。Otherwise reject `GEOMETRY_INVALID` without reducing nosing。

#### 15.1.4.3 Final physical tread inner edge

For each tread：

```text
front_inner = intersection(front L_nose,K_finish)
rear_inner  = intersection(rear L_back,K_finish)
polygon = front_inner -> front outer trim -> ordered outer stations
          -> rear outer trim -> rear_inner -> close
```

Both points lie on one `K_finish`; every tread has a finite collinear inner side edge and no raw-`M_j` spike。

#### 15.1.4.4 Constant nosing remains exact

Because `front_inner` remains on `L_nose`, its distance from `L_face` equals `n`, as does the outer endpoint。The common chord must never move `front_inner` off `L_nose`。

#### 15.1.4.5 Riser inner trim

For each Riser boundary：

```text
face_inner = intersection(L_face,K_finish)
back_inner = intersection(L_back,K_finish)
```

TREAD inner points, Riser face/back, and rear-support geometry terminate on the same `K_finish`; coordinates are not independently approximated。

#### 15.1.4.6 Shared rear-support remains authoritative

After chord trimming, `lower tread rear_support_edge == destination Riser riser_back_edge` exactly, including identical `K_finish` inner and outer-trim endpoints。The common trim must not reintroduce the r1 outer wedge cavity。

#### 15.1.4.7 Removed inner core

The pivot-side triangle `I/J_entry/J_exit` is intentionally outside the Stage-2 physical finish footprint while nominal cells still converge to `I`。Entry/exit preserve deterministic contact with adjacent Straight/Landing components。No spike, giant filler face, or background-visible crack is allowed。

#### 15.1.4.8 Stage-3 relationship

Stage 3 consumes final Stage-2 trim stations as contact geometry and may not move/undo `K_finish`。Existing lower pivot-relief authority may remain distinct。Do not implement Stage 3 here。

## 15.2 Destination Riser / shared rear-support authority

The destination-owned Riser remains on `L_face` and extends uphill to `L_back`。The lower/downhill tread rear support uses the same `L_back`。

Mandatory：

```text
lower tread rear-support boundary == destination Riser back boundary
```

using identical derived coordinates and split points。The Riser band is the exact constant-distance band `L_face -> L_back`, trimmed/mitered against the same semantic trim authority。Do not derive tread and Riser from separate pivot-fixed or independently clipped approximations。

### 15.2.1 No cavity at Winder step junction

At every Winder junction, lower tread + destination Riser + destination tread/nosing form a closed physical transition。Intentional XY overlap at different Z and accepted coplanar contact are allowed。

Forbidden：background-visible wedge/open cavity, progressively widening outer gap, missing rear-support/Riser strip, or deferring a Stage-2 cavity patch to Stage 3。

## 15.3 SQUARE / BEVEL / ROUND

Keep accepted 07-C validation：

```text
q > 0 for BEVEL/ROUND
q < t/2
q <= n
```

The exposed edge for SQUARE/BEVEL/ROUND is the resolved constant-offset `L_nose` edge。Use explicit semantic edge metadata rather than brittle polygon indices。BEVEL/ROUND apply only to that edge, not rear, inner/outer side chain, or hidden partition。

## 15.4 Physical validation

In addition to finite/manifold/contact validation, require：

- requested `n>0` remains constant across both exposed-edge endpoints;
- tread rear-support `L_back` and Riser `L_back` reuse identical full XY;
- no background-visible wedge or open exterior cavity before Stage 3;
- finite deterministic inner miter;
- no unintended positive-volume inner-miter overlap;
- no zero-area cap created merely to preserve nominal `I`;
- all final Tread inner edges and all Riser inner trim points lie on one `K_finish` per Turn;
- no physical vertex protrudes onto the pivot side of `K_finish`, except explicit terminal closure;
- every tread inner side edge has length greater than `eps_l`;
- no acute zero/near-zero-area triangular inner tip;
- positive nosing remains `n` at the chord endpoint;
- rear-support/Riser-back sharing and outer wedge-cavity correction remain intact;
- no background-visible entry/exit crack;
- `K_finish` is deterministic under regeneration。

Nominal local width tending to zero at `I` remains valid。Physical nosing collapse to zero is not required and is not an acceptable solution。

---

# 16. U / Compact U

07-E production U = existing 4-point / 2 persistent Turn foundation。

```text
P0 -> P1 -> P2 -> P3
       T1    T2
```

Each Turn independently：

```text
LANDING or WINDER
EQUAL_2 / EQUAL_3 / EQUAL_4 / BF_1 / BF_2 as applicable
```

Examples：

```text
T1=EQUAL_2, T2=EQUAL_3
T1=BF_1,    T2=EQUAL_3
T1=BF_1,    T2=BF_2
```

Both-Winder U naturally yields aggregate 4/5/6/7/8 Winder treads from per-Turn combinations。07-E does **not** promise a separate single persistent 180° fan with only 2 or 3 total Winder treads。

## 16.1 Compact classification

```text
T1=P_i
T2=P_(i+1)
L_mid=length(T2-T1)

d1 = Turn1 exit cutback on middle segment
d2 = Turn2 entry cutback on middle segment
R_mid = L_mid-d1-d2
```

Classification：

```text
R_mid > +eps_length    -> SEPARATED_U
abs(R_mid)<=eps_length -> COMPACT_U
R_mid < -eps_length    -> INVALID_OVERLAP
```

For exact 90° + 90° equal width：

```text
d1=w/2
d2=w/2
COMPACT_U when L_mid ~= w
```

Actual width scales naturally。900mm fixed conditionではない。

`COMPACT_U` keeps both Path points / Turn identities and zero ordinary middle tread events。Derived Composite U group is geometry-only。

## 16.2 Shared XY transition

Turn A exit and Turn B entry reuse one exact derived cross-section。Canonical Path points are not moved。

Sub-epsilon coordinate disagreement may be resolved by deterministic midpoint of corresponding derived coordinates。Beyond tolerance -> not valid COMPACT_U。

No duplicate shared-interface Riser。

---

# 17. Arbitrary-angle Landing / Winder

## 17.1 Landing

Walking polygon：

```text
[I, E_in, O, E_out]
```

normalized winding。

Interfaces：

```text
entry = I -> E_in
exit  = I -> E_out
outer = E_in -> O -> E_out
```

Landing top Z is its `LANDING_ARRIVAL` event elevation。Material `TREAD`。Body `UNDERSIDE`。

Exact 90° reduces to accepted square。47° / 63° / 82° etc use same algorithm。

## 17.2 Winder

Arbitrary-angle Winder production minimum：same generalized envelope + EQUAL patterns。

BF remains right-angle-only in 07-E。

---

# 18. Old-house / narrow-stair hard guardrail

Core geometry validator、RNA property range、UI clamping、preset validationのいずれも、次の理由だけでrejectしてはならない：

```text
width < 900mm
width < 800mm
width < 750mm
```

Reference dimension 300 / 150 / 85mm等をuniversal minimumへhard-codeしない。

禁止例：

```text
MIN_LEGAL_STAIR_WIDTH = 750
MIN_LEGAL_WINDER_TREAD = ...
```

Narrow / steep / unusual but geometry-valid existing stair may show non-blocking advisory warning, but generationをcancelしない。

`650mm`はrequired regression sampleでありproduction lower boundではない。

Width change：same canonical Path + new widthからTurn envelope / cutback / straight run / finishをre-resolveする。

Default width 900→750等のproject default変更は07-E scope外。

---

# 19. Error classes

User-facing failure distinguishes：

```text
GEOMETRY_INVALID
SCOPE_UNSUPPORTED
ADVISORY_ONLY
```

### GEOMETRY_INVALID

Examples：

- non-finite intersection
- self-intersection
- non-positive nominal cell area
- insufficient Path length for cutback
- positive-area Turn overlap
- physical finish self-intersection that cannot be trimmed
- underbody/tread penetration
- invalid local closure for selected real physical thickness

### SCOPE_UNSUPPORTED

Examples：

- BF requested outside right-angle tolerance
- Winder production requested on >2-Turn custom topology during 07-E if not explicitly supported

Do not describe SCOPE_UNSUPPORTED as mathematical impossibility。

### ADVISORY_ONLY

- narrow/steep/tight but geometry-valid old-house-like dimensions
- future recommended/legal hints

Advisory does not block generation。

---

# 20. Winder STEPPED_CLOSED — exact schema-5 contract

This formula is **schema-5 Winder only**。It does not replace accepted 07-C Straight `stepped_closure_visible_profile()` or schema-4 Landing/Flight geometry。

For Winder cell `C_j`：

```text
T_j = destination tread top Z
d   = closed_body_depth
B   = base_z

Z_soffit_j = max(B, T_j-d)
```

Each complete nominal cell polygon owns one horizontal visible patch, including any required outer corner `O`。

Contact clearance：

```text
(T_j - tread_thickness) - Z_soffit_j > eps_clear
```

If floor clamp makes adjacent patch levels equal, omit zero-height divider face。

Internal divider `D_j`：

```text
lower = Z_soffit_j
upper = Z_soffit_(j+1)
```

Higher/destination cell owns vertical closure over full trimmed divider segment。

Entry：incoming component provides resolved visible soffit edge; if Z differs from cell1, Winder cell1 owns boundary closure。

Exit：following destination component owns next closure if required; Winder does not duplicate it。

`underside_thickness` remains inward shell/validation value and does not relocate visible patch Z。

Winder interior must be CLOSED with Side Boards OFF。

---

# 21. Winder SLOPED_CLOSED — complete outer chain + finite pivot relief

Winder SLOPED_CLOSED is a continuous turning closed soffit。No horizontal Landing plateau is inserted merely because plan direction changes。

C0 continuity required。C1 tangent continuity not required。

## 21.1 Angular fractions / geometry stations

Let primary fractions：

```text
F=[f_0...f_n]
f_0=0
f_n=1
```

Examples：

```text
EQUAL_3 -> [0,1/3,2/3,1]
BF_1    -> [0,2/3,1]
BF_2    -> [0,1/3,1]
```

`r(f)=rotate(r0,f*theta)`。

For each cell interval include：

- front divider `Q_k`
- every outer-chain corner strictly inside interval
- rear divider `Q_(k+1)`

For `O`：

```text
f_O = signed_angle(r0, normalize(O-I))/theta
```

same signed convention only。

Primary divider Zs are event-index interpolated between entry/exit visible-soffit Z：

```text
z_k = lerp(z_0,z_n,k/n)
```

Inserted outer geometry station `O` does not add event。If inside cell k：

```text
lambda_O=(f_O-f_k)/(f_(k+1)-f_k)
z_O=lerp(z_k,z_(k+1),lambda_O)
```

## 21.2 Finite pivot relief

Do not use a singular full-width coincident-XY pivot-spine strip。

Define：

```text
r   = riser_thickness
eps_l = named length epsilon
rho = max(r, 10*eps_l)
```

`rho` is local underbody closure regularization only。

Required：

```text
0 < rho < min(distance(I,E_in), distance(I,E_out))
```

and all supported rays must hit the relief chord before outer chain。

Nominal TREAD cells still extend to exact mathematical pivot `I`。

Changing physical riser thickness may change this local schema-5 Winder SLOPED_CLOSED relief geometry。It must not change Path / width / pattern / nominal tread cells / legacy schemas。

Relief endpoints：

```text
J_0 = I + rho*r(0)
J_n = I + rho*r(1)
K_inner = segment(J_0,J_n)
```

For each primary or inserted station fraction f, intersect ray `I+t*r(f)` with `K_inner` -> `P(f)`。

Station pair：

```text
Inner = P(f) at z(f)
Outer = V(f) at z(f)
```

## 21.3 Main turning strips

For every consecutive geometry station pair a,b：

```text
P_a -> V_a -> V_b -> P_b
```

Triangulate deterministically after winding normalization。Preferred diagonal：

```text
P_a -> V_b
```

Alternative diagonal only via one deterministic production/test helper when preferred diagonal violates simple-triangle checks。

Union of strips covers nominal cell plan minus only pivot-relief core。No outer corner may be omitted。

## 21.4 Pivot core lower surface

Pivot core plan：

```text
K_core = triangle(I,J_0,J_n)
```

Let：

```text
z_low=min(z_0,z_n)
z_high=max(z_0,z_n)
A_low =(I.x,I.y,z_low)
A_high=(I.x,I.y,z_high)
```

For each consecutive inner-chord station pair `P_a,P_b` create：

```text
A_low -> P_a -> P_b
```

Boundary at `z_low` joins fan directly。

High-elevation boundary receives intentional local closure：

```text
HIGH_SIDE_PIVOT_CLOSURE
A_low -> A_high -> J_high
```

where `J_high` is high-side relief endpoint at `z_high`。

This face is intentional, not accidental triangulation artifact。Its plan extent is limited by `rho`; vertical extent may be `z_high-z_low`。

Stage 3 must visually inspect Side Boards OFF from below / inner pivot / ordinary residential views。No giant filler wall / spike / open cavity。

## 21.5 Contact/body segmentation / face ownership

For Winder cell：

```text
T_j = destination tread top Z
U_j = T_j - tread_thickness
```

Underbody volume bounded by：

- physical tread/riser contact geometry above
- SLOPED lower surface below
- outer-chain closure
- pivot-core closure
- destination-owned divider closure
- entry/exit closure only where not already owned by adjacent component

All lower/contact/Riser surfaces split at same ordered geometry stations：

- primary divider stations
- inserted outer-corner stations
- physical finish trim intersections
- all semantic shared-edge split points

Divider closure is owned by higher/destination cell。Lower edge = resolved lower-surface intersection; upper edge = actual contact/Riser lower boundary。

At pivot relief, closure terminates on corresponding `P(f)` / core edge。Do not create independent coincident prism at I。

## 21.6 No T-junction on shared edges

Mandatory：

> If any incident face introduces a vertex in the interior of a semantic shared edge, that vertex becomes a shared split point and must be inserted into **every** face using that edge before final assembly.

Applies to：

- `A_low -> A_high`
- relief chord
- divider closure
- outer chain
- entry/exit interface
- trim-generated board/body edges

Procedure：

1. collect ordered split parameters on semantic shared edge;
2. deduplicate by full 3D coordinate within named epsilon;
3. insert same points in every incident polygon;
4. deterministically retriangulate;
5. no vertex may terminate in middle of another unsplit edge。

Do not weld by XY alone。

## 21.7 Interfaces / contact clearance

Winder entry/exit and adjacent component reuse exact same full-3D boundary vertices where visible soffits meet。

High-side pivot closure is owned by Winder core and not duplicated by neighbor。

For all cell/core subregions：

```text
visible_soffit_z < resolved_contact_z - eps_clear
```

Actual selected body-depth/thickness/path failure -> `GEOMETRY_INVALID`; never legal-width error。

`underside_thickness` does not move exterior visible soffit outward/downward。

---

# 22. Compact-U shared SLOPED Z / Reverse authority

For two consecutive WINDER Turns with zero ordinary middle tread events, solve SLOPED height interpolation as one derived event group only。

All indexing uses **current uphill/ascent traversal order**。

Define：

```text
Turn A = first Winder Turn encountered while ascending
Turn B = second Winder Turn encountered while ascending
n1     = step_count(Turn A)
n2     = step_count(Turn B)
A      = visible-soffit Z at ascent entry to Turn A
B      = visible-soffit Z at ascent exit from Turn B
```

Shared middle height：

```text
M = A + n1/(n1+n2) * (B-A)
```

Equivalent grouped station sequence：

```text
Turn A station k = A + k/(n1+n2)*(B-A), k=0..n1
Turn B station l = A + (n1+l)/(n1+n2)*(B-A), l=0..n2
```

Examples：

```text
EQUAL_3 + EQUAL_3 -> M at 3/6
EQUAL_2 + EQUAL_3 -> M at 2/5
BF_1    + EQUAL_3 -> M at 2/5
```

Turn identities remain separate; no middle RiseEvent is added。

On Reverse：canonical Path / physical pattern assignment unchanged; traversal order, `n1/n2`, A/B, event indices are recomputed from new uphill order。Do not mix canonical-order counts with ascent-order heights。

---

# 23. Side Board authority at Winder

Preserve accepted 07-C independence：

```text
underside_mode  -> Side Board lower boundary
side_board_mode -> Side Board upper / visible boundary
```

Combinations：

```text
STEPPED_CLOSED + STEPPED board -> upper stepped / lower stepped
STEPPED_CLOSED + SLOPED board  -> upper sloped  / lower stepped
SLOPED_CLOSED  + STEPPED board -> upper stepped / lower sloped
SLOPED_CLOSED  + SLOPED board  -> upper sloped  / lower sloped
```

LEFT / RIGHT remain uphill-relative; Reverse may move a left board to opposite world-space side。No stale side ownership allowed。

## 23.1 Lower boundary

Exactly selected UNDERBODY exterior boundary：

- STEPPED_CLOSED -> resolved stepped lower boundary
- SLOPED_CLOSED -> resolved sloped / pivot-relief lower boundary

Reuse same geometry stations / split points。

## 23.2 STEPPED upper boundary

For Winder cell `C_j` destination tread top `T_j`：

- horizontal upper level uses accepted Side Board reveal relation to destination walking surface;
- base rule：`T_j + reveal` unless accepted local terminal rule overrides;
- RiseEvent/divider transition adds corresponding vertical upper-profile transition;
- inserted geometry-only `O` inside same cell keeps same stepped upper level and adds no event;
- entry/exit terminal/cap behavior reuses accepted 07-C terminal semantics transformed to local boundary。

## 23.3 SLOPED upper boundary

Derive from walking-surface / Side-Board upper reference, **not underbody Z interpolation**。

Primary upper stations follow ordered Winder walking/RiseEvent sequence and accepted reveal/terminal semantics。

Between primary stations：linear visible upper edge interpolation。

If outer corner `O` lies inside interval, insert it and interpolate upper Z by its local fraction。No extra RiseEvent/tread。

Preserve accepted end closures / short terminal caps where applicable。

---

# 24. Compact-U shared-center Side Board

Do not build two complete coincident center boards and reject their collision。

## 24.1 Seam-local frame / profile regions

```text
s = distance along shared center path
v = plan normal across seam
z = world vertical
```

For each enabled contributor：

```text
R_i = {(s,z) | L_i(s) <= z <= U_i(s)}
```

`L_i` from underbody authority; `U_i` from Side Board upper authority / reveal / accepted terminal rules。

Invalid `L_i>U_i` -> geometry error。

## 24.2 Shared union

```text
R_shared = union(enabled R_i)
```

Rules：

- positive-area overlap -> union
- shared edge forming one regular region -> union
- **point-only contact -> separate closed components; do not weld the point**
- separated Z ranges -> separate closed components
- do not fill empty Z gap merely to make one giant board

One `SHARED_CENTER_BOARD` family may contain multiple closed components。

## 24.3 Thickness

For each closed component：

```text
v in [-side_board_thickness/2, +side_board_thickness/2]
```

This is actual board volume `V_shared`。

If center-side board disabled, no shared board and no related trim。

## 24.4 3D trim

Trim only actual positive-volume intersection with `V_shared`：

```text
TREAD
RISER
UNDERBODY
```

Conceptually：

```text
part_after = part_before \ interior(V_shared)
```

May use deterministic clipping rather than Blender Boolean, but supported fixture result must be equivalent。

Every cut is capped and keeps trimmed part material role。

Do not delete a full-height plan strip when board exists only over partial Z。

Trim-generated shared-edge points obey no-T-junction rule。

## 24.5 Ordinary/shared transition = deterministic butt joint

No implicit miter or tapered transition。

Connection plane：

- through shared seam endpoint
- vertical in world Z
- normal to local shared-seam tangent in plan

Both ordinary board and shared board clip to same plane。

At plane：

1. insert union of all profile breakpoints into both participating cross-sections;
2. overlapping cross-section area is internal connection, not duplicate exterior faces;
3. area belonging only to one side gets endpoint cap owned by that side;
4. thickness step between ordinary one-sided board and symmetric shared board is intentional local shape;
5. no miter/bevel/automatic transition implied;
6. no open cavity / positive-volume overlap / z-fighting duplicate face。

Example：

```text
ordinary may occupy v=[-s,0]
shared occupies      v=[-s/2,+s/2]
```

Do not move canonical width or seam to hide mismatch。

---

# 25. Material contract

Roles remain：

```text
BASE
TREAD
RISER
UNDERSIDE
SIDE_BOARD
```

No WINDER Material role。

```text
Winder tread  -> TREAD
Winder riser  -> RISER
Winder body   -> UNDERSIDE
Winder board  -> SIDE_BOARD
Landing top   -> TREAD
Landing body  -> UNDERSIDE
```

Regenerate / Path edit / pattern edit / Reverse / Repair / Save-Reopen / Undo-Redo preserve pointer / slot semantics。

---

# 26. Transaction / rollback / Diagnose / Repair

Candidate preparation before Scene mutation includes at least：

- canonical Path
- Turn frame / angle
- mode / pattern
- envelope / nominal cells / complete outer chain
- RiseEvent ownership / allocation
- physical Tread/Riser
- Landing/Winder geometry
- selected CLOSED underbody
- Side Board / shared-center trim
- Material slot plan
- topology/finite checks where practical

Rollback target：

- old Mesh datablock
- schema version
- path_points / point IDs
- Turn modes / patterns
- distribution mode / allocations
- dimensions
- ascent direction
- 07-C Residential fields
- Materials / slots
- Stair ID
- Object Transform

No partial schema-5 state after failure。

Repair recoverable policy remains accepted：ID_MISSING / ID_CONFLICT / TRANSFORM_CHANGED / GEOMETRY_MISSING。

Repair does not invent valid geometry from invalid canonical data。Duplicate ID repair changes Stair ID only, not point/Turn identity。

---

# 27. Save / reopen / Undo / Redo / Finalize / Delete

Acceptance must preserve：

- schema 5
- Stair ID
- Path points / point IDs
- Turn mode / pattern
- AUTO / MANUAL state / straight allocation authority
- Materials
- ascent direction
- Residential fields
- identity Transform

Undo/Redo representative：LANDING↔WINDER, pattern change, arbitrary-angle move, Reverse, Material edit。

Undo/Redo runtime policy：UI operation -> Ctrl+Z -> Ctrl+Shift+Z -> then Console。

Finalize：Managed Stair -> ordinary editable Mesh -> JHM management ends。

Delete：active managed Stair only。Internal fragment is not separate Managed Object lifecycle。

Wall / Finish / unrelated objectsをmutationしない。

---

# 28. Supported Path production scope

07-E final production acceptance requires：

```text
3-point L : 1 Turn
4-point U : 2 Turns
```

Existing 07-D custom/multi-point Landing data remains compatible。

Winder production on custom Path with 3+ Turns is not mandatory 07-E acceptance target。Pure helpers should not needlessly hard-code 2 Turns, but runtime guarantee remains L/U unless later reviewed addendum expands it。

This is scope, not mathematical impossibility。

---

# 29. Turn UI / pattern thumbnail

Each production Turn independently configurable：

```text
Mode: LANDING | WINDER
Pattern when WINDER: 2段 | 3段 | 4段 | BF-1 | BF-2
```

LANDING -> pattern disabled/hidden。

New schema-5 Winder default = EQUAL_3。

Small plan icon/thumbnail preferred。Generate normalized icon from same fraction authority; image asset is not geometry authority/runtime requirement。

General Stair panel compacting / collapsible redesign and project-wide default-width change are explicitly outside 07-E。

---

# 30. Fixed expected-success fixtures

These are regression targets, never legal minima/maxima。

## 30.1 Old-house L full-finish width matrix

```text
P0=(0,0)
T =(0,2200mm)
P2=(-2200mm,2200mm)
Mode/Pattern       = WINDER / EQUAL_3
base_z             = 0mm
floor_to_floor     = 2800mm
overall risers     = 16
tread thickness    = 30mm
riser thickness    = 20mm
body depth         = 150mm
underside shell    = 9.5mm
nosing             = 5mm
front edge         = SQUARE
side board thick   = 18mm
side board reveal  = 40mm
boards             = BOTH ON
```

Run every width：900 / 800 / 750 / 700 / 650mm。Both STEPPED_CLOSED + STEPPED board and SLOPED_CLOSED + SLOPED board must reach final physical geometry under the original reviewed contract。

## 30.2 EQUAL_3 outer-corner fixture

Width750 / exact90 / EQUAL_3 central cell preserves `Q_1 -> O -> Q_2`。At 90° `f_O=1/2` inside `[1/3,2/3]` and `z_O=(z_1+z_2)/2`。

## 30.3 Compact U full-finish fixture

```text
base_z=0mm
width=750mm
P0=(0,0)
P1=(0,2200mm)
P2=(750mm,2200mm)
P3=(750mm,0)
Turn A=WINDER/EQUAL_3
Turn B=WINDER/EQUAL_3
floor_to_floor=2800mm
overall risers=17
body depth=150mm
underside shell=9.5mm
tread thickness=30mm
riser thickness=20mm
nosing=5mm
front edge=SQUARE
side boards=BOTH ON
side board thick=18mm
side board reveal=40mm
```

## 30.4 Arbitrary-angle Landing fixture

```text
width=750mm
P0=(0,0)
T=(0,2200mm)
P2=T + 2200mm*(-sin(63°), cos(63°))
Mode=LANDING/schema5 generalized
base_z=0mm
floor_to_floor=2800mm
overall risers=16
```

## 30.5 Representative physical finish

Historical Stage-2 physical fixtures include width650 exact-90/63-degree EQUAL_3, BF_1+BF_2 U and REVERSE, with Candidate-r3 constant nosing/shared rear-support expectations。

---

# 31. Stage 1 — canonical Turn + first 90° L Winder

Implement / accept：identity 0.7.4、schema-5 foundation、path-point Turn identity、winder pattern authority、generalized frame、90° EQUAL_2/3/4 nominal cells、RiseEvent/AUTO、SQUARE Winder Tread/Riser、transaction/rollback/basic persistence、schema-1/2/3/4 regression。

---

# 32. Stage 2 — BF + U / Compact U + arbitrary-angle

Internal order：2A BF、2B U/Compact U、2C arbitrary-angle Landing、2D arbitrary-angle EQUAL Winder、2E positive nosing/front-edge finish integration。

Historical accepted scope includes BF fractions、per-Turn mode/pattern、U combinations、Compact-U、arbitrary-angle Landing/Winder、free-angle relocation、schema-5 allocation/migration、deterministic regeneration、Candidate-r3 physical Winder finish corrections。

---

# 33. Stage 3 — CLOSED underbody + Side Board

Historical reviewed order：3A STEPPED_CLOSED、3B SLOPED_CLOSED、3C ordinary Side Board、3D Compact-U shared-center Side Board、3E Material/Reverse/Repair/topology sweep。

**The first implementation attempt of Stage 3 is now ABANDONED / CLOSED / NOT MERGED. The restarted Stage 3 after Stage 2.5 follows Section 39.**

---

# 34. Stage 4 — lifecycle / full regression / practical acceptance

Cover Candidate identity、legacy/schema regressions、schema-5 persistence、patterns/allocation、migration guard、Undo/Redo、rollback、Repair、Materials、Reverse、Save/full exit/reopen、Finalize/Delete、Wall/Finish isolation、practical placement、narrow-house cases、deterministic regeneration、automated regression、compileall、diff check。07-E overall ACCEPTED only after Stage 4 runtime acceptance。

---

# 35. Automated / runtime test policy

Pure/testable logicをBlender modal codeから分離する。Prior 07-A/B/C/D suites remain regression targets。RuntimeはConsole canonical evidence + geometry visual inspectionを組み合わせる。

---

# 36. Acceptance principles

07-E overall Acceptance requires schema compatibility、general pattern rule、BF determinism、two-Turn U、Compact-U、arbitrary-angle Landing/Winder、Shift15 non-restriction、RiseEvent correctness、migration safety、physical visible geometry、CLOSED underbody、Side Boards、narrow-width support、atomic rollback、lifecycle、Materials、isolation、practical placement、repository-text implementation authority。

---

# 37. Explicit non-scope

07-E does not require spiral/helical stair、curved Flight centerline、freehand curved Winder edge、per-divider editor、code-compliance judgment、variable Flight width、non-uniform riser heights、07-F open/support variants、handrail/newel/baluster、automatic Wall/Floor/Room attachment、automatic Stair opening Boolean、production UV guarantee、default width change、general panel redesign、3+ Turn Winder guarantee。

---

# 38. Final implementation order

Historical order progressed through accepted 07-D → schema-5 foundation → Stage 1 → Stage 2 Candidate r3. The current continuation is replaced by Section 39：Stage 2.5 correction → fresh Stage 3 → Stage 4。

---

# 39. Stage 2.5 / restarted Stage 3 normative override

This section is the **later project decision adopted on 2026-10-05 after direct runtime evaluation**. It supersedes conflicting older requirements in Sections 15, 20–24, 30, 32–38 for the Stage-2.5 / restarted-Stage-3 path while preserving the historical record of why Candidate r3 was accepted at Stage 2。

## 39.1 Current status

```text
Build 07-E Stage 1          ACCEPTED
Build 07-E Stage 2 r3       ACCEPTED
PR #33 first Stage 3        ABANDONED / CLOSED / NOT MERGED
Build 07-E Stage 2.5        CURRENT
Fresh Stage 3 restart       NEXT after Stage 2.5 acceptance + merge
```

`main` remains at the accepted Stage-2 baseline until Stage 2.5 is runtime-accepted and merged。

## 39.2 Why Stage 2.5 exists

Candidate-r3 solved real isolated Winder finish defects, but the r2/r3 Turn-wide physical-plan and `K_finish` authorities increased downstream seam complexity. During the first Stage-3 implementation, precision-oriented internal-solid work became dominant and visible accepted geometry regressed in runtime, including Winder top behavior, SLOPED body penetration into visible walking regions, and previously accepted 07-D Landing/Residential body appearance。

The project goal is a practical Blender modeling aid rather than a CAD/BIM watertight-solid kernel。

Normative priority：

> **Visible exterior correctness + reliable Blender workflow > hidden internal solid cleanliness.**

## 39.3 Preserved Stage-2 runtime artifact authority

The retained runtime ZIPs were directly audited：

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

Recursive package comparison found：

```text
r1 -> r2 : japanese_house_modeler/stair_turn.py only
r2 -> r3 : japanese_house_modeler/stair_turn.py only
r1 -> r3 : japanese_house_modeler/stair_turn.py only
```

Therefore Stage 2.5 must be a narrow production-path correction, not a repository rollback。

## 39.4 Exact geometry evolution found by ZIP audit

Candidate r1 visible Winder production used the simpler per-cell path：

```text
physical_winder_tread_polygon(...)
resolve_winder_riser_plan(...)
```

Candidate r2 added Turn-wide semantic physical-plan authority：

```text
PhysicalWinderBoundary
PhysicalWinderTreadPlan
resolve_physical_winder_plans(...)
_semantic_boundary(...)
_line_chain_intersection(...)
_trim_semantic_line(...)
```

Candidate r3 then added the common inner finish chord system：

```text
PhysicalWinderInnerTrim
K_finish
inner_front
inner_rear
inner_edge
```

This history is now the restoration authority; do not infer r1 behavior from screenshots or memory。

## 39.5 Stage-2.5 implementation target

Stage 2.5 must：

1. use current accepted Stage-2 r3 codebase as the structural base;
2. preserve schema-5 Turn / BF / U / Compact-U / arbitrary-angle / migration / allocation / UI / serialization / persistence foundation;
3. restore the **Candidate-r1-equivalent visible Winder TREAD/RISER production call behavior** from commit `b0d92fc...`;
4. bypass r2/r3 Turn-wide `resolve_physical_winder_plans()` / `K_finish` production authority where required to reproduce r1 visible top geometry;
5. not replace the whole current `stair_turn.py` with the r1 file;
6. not roll the whole repository back;
7. not change accepted 07-D Landing / Straight / underside / Residential geometry;
8. not implement new Stage-3 UNDERBODY/Side Board work during Stage 2.5。

Later r2/r3 helper definitions may remain present if unused; production authority matters more than deleting code。

## 39.6 Candidate-r1 known gap is intentionally allowed

The Candidate-r1 visible terminal TREAD/RISER / Turn-transition gap is a known defect and is explicitly tolerated for Stage 2.5：

```text
known r1 terminal gap = ALLOWED / NOT A STAGE-2.5 BLOCKER
```

Do not rebuild r2/r3 physical-plan complexity merely to close it during Stage 2.5。It may be revisited after a successful fresh Stage-3 r1 exists。

## 39.7 Geometry identity target

Where practical, add pure regression comparing Stage-2.5 Winder output with Candidate-r1 source authority for selected fixtures：

- TREAD vertex coordinates;
- RISER vertex coordinates;
- polygon vertex order;
- Z elevations;
- ordinal/event ordering;
- FORWARD / REVERSE;
- exact-90 EQUAL_3 reference fixture。

Preferred result：numeric equivalence within existing named tolerance, not merely visual similarity。

## 39.8 Mandatory Stage-2.5 runtime focus

Before merge：

1. exact-90 EQUAL_3 Winder compared with retained Candidate r1;
2. confirm simple Turn/inner boundary behavior is restored;
3. 63° arbitrary-angle Winder smoke check;
4. FORWARD;
5. REVERSE;
6. Build 07-D exact-90 Landing visual regression including underside/body;
7. Save -> full Blender exit -> reopen smoke;
8. prior automated 07-D / 07-E regressions;
9. dedicated Stage-2.5 Acceptance Record。

Only after this may Stage 2.5 merge to `main` and fresh Stage 3 begin。

## 39.9 Restarted Stage-3 visual-first acceptance profile

Required：

- visible exterior geometry is coherent;
- no obvious exterior hole/daylight gap introduced by Stage 3;
- no major spike / giant filler face;
- no externally visible z-fighting;
- no missing major part;
- no nonfinite/collapsed geometry;
- no generation exception;
- deterministic regeneration/lifecycle remains stable;
- Stage-2.5 accepted Winder top is unchanged;
- accepted 07-D Landing / Straight body geometry is unchanged unless a separately approved correction is made。

Allowed internally：

- UNDERBODY may penetrate TREAD/RISER in hidden regions;
- Straight/Winder/Landing bodies may overlap internally;
- Side Board may intersect hidden geometry;
- hidden duplicate/internal faces may exist;
- separate closed components may overlap;
- exact whole-stair Boolean union is not required。

Not required for fresh Stage-3 r1：

- exact positive-volume intersection elimination;
- exact SLOPED convex decomposition;
- global PHYSICAL_CONTACT classification;
- exact internal union;
- volume conservation proof;
- internal duplicate-face cleanup;
- exact BodyInterface union proof。

## 39.10 Restarted Stage-3 order

```text
Stage 2.5 accepted + merged main
    ↓
fresh Stage-3 branch
    ↓
STEPPED_CLOSED visible body / Side Boards OFF
    ↓
SLOPED_CLOSED visible body / Side Boards OFF
    ↓
ordinary Side Board continuation
    ↓
Compact-U Side Board
    ↓
Material / Reverse / lifecycle regression
    ↓
Stage 4
```

One focused Blender runtime test at a time is preferred during active geometry iteration. High-risk visible geometry is tested before broad low-risk repetition。

## 39.11 07-D regression authority

07-D exact-90 Landing and its accepted body/underside/Residential geometry must not be rebuilt just because Stage 3 is working on schema-5 Winder geometry。

If fresh Stage 3 changes a 07-D accepted shape, treat that as regression unless a separate approved correction explicitly changes the 07-D authority。

## 39.12 Documentation precedence

For Stage 2.5 / restarted Stage 3：

```text
1. Section 39 of BUILD_07_E_SPECIFICATION.md
2. BUILD_07_E_STAGE_2_5_PLAN.md
3. Current ROADMAP.md status/order
4. Earlier sections of BUILD_07_E_SPECIFICATION.md
5. Historical review documents / PR #33 comments
```

Existing Acceptance Records remain historical truth. Do not rewrite history to claim Candidate r1 was the previously accepted Stage-2 final. Stage 2.5 is a later deliberate correction baseline。
