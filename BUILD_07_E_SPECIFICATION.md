# BUILD 07-E SPECIFICATION
## 日本住宅モデラー — Winder / 廻り段 + Arbitrary-angle Turn / Landing

> **Status: FINAL / IMPLEMENTATION AUTHORITY**  
> Date: 2026-09-30  
> Build 07-D overall Acceptance を baseline とし、07-D の accepted Multi-point Path / L / U / Landing / lifecycle contract を壊さず、Turn Foundation を Winder / 廻り段および arbitrary-angle Turn / Landing へ拡張する。
>
> **Implementation authority:** Codex は本ファイルだけで production geometry / migration / validation / lifecycle を実装できなければならない。外部画像・chat添付画像・過去のreview文書から不足する形状を推測してはならない。

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

### 15.1.4 Piecewise inner physical finish authority

The mathematical pivot `I` remains nominal subdivision authority only。Per-tread raw `M_j` is an intermediate construction point, never automatically the final visible inner corner。Physical Winder TREAD/RISER finish geometry uses a deterministic piecewise authority: exact neighboring-Straight terminal references at entry/exit and a regularized Turn-local interior authority。

#### 15.1.4.1 Turn-local trim frame

```text
R0 = normalize(E_in-I)
Rn = normalize(E_out-I)
b  = normalize(R0+Rn)             # points into envelope
h_j = dot(M_j-I,b)
eps_l = named length epsilon
c_finish = max(n,r,10*eps_l)
h_finish = max(0,max_j(h_j))+c_finish
K_finish: dot(X-I,b)=h_finish
```

`K_finish` is perpendicular to `b`。`c_finish` is derived physical-finish regularization only, never a legal/width minimum or user-facing regulatory rule。

#### 15.1.4.2 Finite finish chord

Intersect `K_finish` with boundary rays `I+t*R0` and `I+t*Rn` to obtain finite `J_entry` and `J_exit`。Both must occur strictly before their outer-chain endpoints within epsilon; `K_chord=segment(J_entry,J_exit)` must lie inside the Turn walking envelope and every required semantic line must intersect it。Otherwise reject `GEOMETRY_INVALID` without reducing nosing。

#### 15.1.4.3 Straight-compatible terminal references

Let `S_entry` and `S_exit` be the actual adjacent Straight walking-region inner-side lines through `I`, parallel to the corresponding Straight travel axes in current ascent order。FORWARD uses incoming then outgoing; REVERSE recomputes the order without changing canonical Turn identity。

```text
entry front_inner = intersection(entry L_nose,S_entry)
entry Riser face/back inner = intersection(L_face/L_back,S_entry)
exit rear_inner = intersection(exit L_back,S_exit)
```

These are actual TREAD/RISER plan vertices, not filler or cover geometry。

#### 15.1.4.4 Final physical tread inner edge

For each tread：

```text
front_inner = intersection(front L_nose,
                           S_entry for first ascent-local cell else K_finish)
rear_inner  = intersection(rear L_back,
                           S_exit for last ascent-local cell else K_finish)
polygon = front_inner -> front outer trim -> ordered outer stations
          -> rear outer trim -> rear_inner -> close
```

Interior points remain on `K_finish`。Terminal-to-interior edges are deterministic finite transition segments in the actual tread polygon。Every tread has a finite nonzero inner side edge and no raw-`M_j` spike。

#### 15.1.4.5 Constant nosing remains exact

Because every `front_inner` remains on `L_nose`, its distance from `L_face` equals `n`, as does the outer endpoint。Neither terminal nor interior trim may move `front_inner` off `L_nose`。

#### 15.1.4.6 Riser inner trim

For each Riser boundary：

```text
face_inner = intersection(L_face,
                          S_entry for entry Riser else K_finish)
back_inner = intersection(L_back,
                          S_entry for entry Riser else K_finish)
```

Interior Riser and rear-support points use `K_finish`。The entry Riser uses the exact shared `S_entry` reference。Coordinates are derived from the same named line authorities, never independently approximated。

#### 15.1.4.7 Shared rear-support remains authoritative

After piecewise trimming, `lower tread rear_support_edge == destination Riser riser_back_edge` exactly, including identical inner-authority and outer-trim endpoints。The revised trim must not reintroduce the r1 outer wedge cavity。

#### 15.1.4.8 Removed inner core

The pivot-side triangle `I/J_entry/J_exit` is intentionally outside the Stage-2 physical finish footprint while nominal cells still converge to `I`。Entry/exit preserve deterministic contact with adjacent Straight/Landing components。No spike, giant filler face, or background-visible crack is allowed。

#### 15.1.4.9 Stage-3 relationship

Stage 3 may not arbitrarily alter accepted Winder geometry, but the Build-07-E physical inner-trim authority is explicitly revised here to permit exact Straight-compatible terminal alignment。`K_finish` remains interior regularization authority and must not collapse to `I`。Underbody and Side Board consume the final revised TREAD/RISER terminal geometry; they may not hide an offset with filler, cap, cover, or cosmetic board geometry。Existing lower pivot-relief authority may remain distinct。

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
- all interior Tread/Riser trim points lie on one deterministic `K_finish` per Turn;
- entry/exit TREAD and RISER terminal points lie on their exact adjacent Straight references;
- finite transition segments connect terminal and interior authorities without filler, sliver, cavity, or T-junction;
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

Generalized WALKING envelope uses this one TurnFrame authority。Exact-right-
angle Residential BODY dispatches unchanged to the accepted schema-4 Landing
oracle; it is not approximated by the non-right builder。47° / 63° / 82°など
non-right Residential BODYは以下の明示authorityを使う。

### 17.1.1 Generalized Residential Landing finish

`K=[I,E_in,O,E_out]` is finite, simple, convex, positive-area, and has entry
and exit lengths equal to stair width within `EPS_LENGTH`; otherwise
`GEOMETRY_INVALID`。`G_entry=I->E_in`, `G_exit=I->E_out`, and the exposed outer
chain is `E_in->O->E_out`。Semantic vertices are never moved by finish logic。

With real perpendicular distance `r=riser_thickness`, offset outer edges
`E_in->O` and `O->E_out` inward.  Their intersections with `G_entry`,
`G_exit`, and each other are `A_entry`, `A_exit`, and `O_inner`。The cavity and
skirt are exactly `C=[I,A_entry,O_inner,A_exit]` and
`S=[E_in,O,E_out,A_exit,O_inner,A_entry]`。Both must be finite, simple,
positive-area; `O_inner` must lie in/on K。Invalid acute/obtuse constructions
raise `GEOMETRY_INVALID`; `r` is never silently reduced。

Let `Z_contact=Z_top-tread_thickness`, `d=side_board_band_width_mm/1000`,
`u=underside_thickness_mm/1000`, and
`Z_soffit=max(base_z,Z_top-d)`。The Landing soffit is intentionally horizontal。
For non-right `STEPPED_CLOSED`, UNDERBODY occupies `K x
[Z_soffit,Z_contact]`。For non-right `SLOPED_CLOSED`, the bottom slab occupies
`K x [Z_soffit,Z_soffit+u]` and the exposed skirt occupies
`S x [Z_soffit+u,Z_contact]`, leaving cavity C above its roof。Required
clearances are strict within `EPS_LENGTH`。

ENTRY and EXIT body ports retain their semantic plan segment, soffit edge,
contact edge, and ordered stations。SLOPED ports explicitly retain `A_entry`
or `A_exit`; they are not reconstructed from Mesh coincidence。

The Landing Side Board follows only `E_in->O->E_out` on the ascent-local
outside side。Offset both outer edges outward by real perpendicular thickness
`s`; their interface intersections and mutual miter are `B_entry`, `B_exit`,
`O_outer`。Its exact footprint is
`B=[B_entry,O_outer,B_exit,E_out,O,E_in]`。It occupies the constant vertical
interval `Z_soffit -> Z_top+reveal` for either Side Board mode。Invalid offset
or miter geometry raises `GEOMETRY_INVALID`。

`B_entry` and `B_exit` lie on the supporting lines of `I->E_in` and
`I->E_out`; positive outward thickness normally places them beyond the finite
walking-interface segments。Collinearity, perpendicular thickness, and the
`O_outer` miter—not finite-segment containment—are authoritative。

All authority resolution and UNDERBODY/SIDE_BOARD construction is pure
candidate preparation。Exact 90° continues to call the accepted schema-4
production code unchanged。

### 17.1.2 Schema-5 Residential body components and interfaces

Stage-3 resolves ascent-local `STRAIGHT_FLIGHT`, `LANDING`, and `WINDER`
components from the same event/allocation sequence as top geometry。Each keeps
its accepted/local body authority and exposes semantic ENTRY/EXIT occupied
profiles in one interface-local `(q,z)` frame。REVERSE reverses traversal and
ownership without changing canonical identity。

Each consecutive pair uses one canonical frame with semantic inner `q=0` and
outer `q=width` endpoints。After normalization,
`R_overlap=R_source∩R_destination` is internal contact and leaves no duplicate
interface face。`R_transition=R_source△R_destination` is emitted exactly once
and owned by the destination。An exact profile match leaves no exposed
interface face。Zero-middle Turn pairs use the layout's reconciled shared
interface。Resolution and final-shell validation occur during candidate
preparation; invalid topology raises `GEOMETRY_INVALID` before Scene mutation。

Canonical q is supplied by explicit semantic `INNER -> OUTER` interface
authority, never inferred from source order or world-coordinate sorting。
Component-local source and destination ports may list the physical segment in
either direction; both are transformed into that canonical q direction before
comparison。The currently supported body-port cross-sections are
rectilinear in `(q,z)`; a diagonal profile is `GEOMETRY_INVALID` rather than
being approximated by the rectangular cell algebra。Profile vertices and all
named semantic breakpoints jointly define the common q/z split stations。Grid
stations used by cell algebra are distinct from actual profile/named station
pairs; provenance belongs only to an actual canonicalized `(q,z)` pair and is
never fabricated from the q-by-z Cartesian product。
`EPS_LENGTH`-equivalent stations prefer named semantic authority over ordinary
profile authority; same-priority ties use the stable numeric minimum, making
canonicalization traversal-independent。Pair provenance survives snapping to
the final canonical coordinates。EPS clustering is bounded against one cluster
anchor; it is not transitive nearest-neighbor chaining, and no cluster spans
more than `EPS_LENGTH`。Non-finite interface input is
`GEOMETRY_INVALID`, and sliver intervals/cells are discarded before
classification。The symmetric difference retains separate `SOURCE_ONLY` and
`DESTINATION_ONLY` cells for later face orientation。If both occupied profiles
match, both sets are empty and no transition-closure owner exists。

Stage-3 distinguishes the walking/top semantic interface from the physical
UNDERBODY terminal。`COPLANAR_BODY_INTERFACE` applies only when actual body
ports share one plane and therefore consumes the `BodyInterface` region
algebra directly。Straight/Turn boundaries are initially
`RISER_MEDIATED_INTERFACE`: accepted 07-C Riser thickness remains physical,
so the Straight UNDERBODY terminal is offset from the Turn walking plane and
must not be extended, clipped, or joined by an invented UNDERSIDE filler。
Accepted TREAD/RISER geometry is never moved by Stage-3。

An exact zero-volume contact between different accepted roles may be recorded
as `PHYSICAL_CONTACT` only when it is internal, intentional, non-visible, and
has no third duplicate finish face。Same-role coincident finish faces and every
positive-volume overlap remain forbidden。

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
Outer = V(f) at z(f)   # Q or O etc.
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
P2=(-2200mm,2200mm)   # exact 90° left
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

Run every width：

```text
900mm
800mm
750mm
700mm
650mm
```

For **every width**, both must reach final physical geometry：

```text
A: STEPPED_CLOSED + STEPPED board
B: SLOPED_CLOSED  + SLOPED  board
```

Width alone may never be reason for failure。If fixture fails, investigate implementation vs reviewed contract; do not weaken/remove fixture to obtain green tests。

## 30.2 EQUAL_3 outer-corner fixture

Width750 / exact90 / EQUAL_3 central cell：

```text
Q_1 -> O -> Q_2
```

must be preserved。At 90° `f_O=1/2` inside `[1/3,2/3]`。

```text
z_O=(z_1+z_2)/2
```

No plan triangle loss adjacent O。

## 30.3 Compact U full-finish fixture

```text
base_z            = 0mm
width             = 750mm
P0=(0,0)
P1=(0,2200mm)
P2=(750mm,2200mm)
P3=(750mm,0)
Turn A            = WINDER / EQUAL_3
Turn B            = WINDER / EQUAL_3
floor_to_floor    = 2800mm
overall risers    = 17
body depth        = 150mm
underside shell   = 9.5mm
tread thickness   = 30mm
riser thickness   = 20mm
nosing             = 5mm
front edge         = SQUARE
side boards        = BOTH ON
side board thick   = 18mm
side board reveal  = 40mm
```

Run both：

```text
A: STEPPED_CLOSED + STEPPED board
B: SLOPED_CLOSED  + SLOPED  board
```

Required：

- COMPACT_U
- zero ordinary middle tread events
- no duplicate shared Riser
- one shared center-board family, not two colliding full boards
- actual TREAD/RISER/UNDERBODY trim by `V_shared`
- no open cavity / positive-volume board collision
- in B, shared soffit M = exact 3/6 event-group height

## 30.4 Arbitrary-angle Landing fixture

```text
width=750mm
P0=(0,0)
T =(0,2200mm)
P2=T + 2200mm*(-sin(63°), cos(63°))
Mode=LANDING / schema5 generalized
base_z=0mm
floor_to_floor=2800mm
overall risers=16
```

Both adjacent original segment lengths exactly2200mm。Must succeed without angle-preset reject。

## 30.5 Representative physical finish

Mandatory Stage-2 physical fixtures：

- A: width650, exact-90 L, EQUAL_3, nosing5mm, SQUARE;
- B: width650, 63-degree L, EQUAL_3, nosing5mm, SQUARE;
- C: width900, exact-90 U, Turn1=BF_1, Turn2=BF_2, nosing5mm, SQUARE;
- D: representative REVERSE case。

For every positive-nosing front edge, perpendicular offset from nominal Riser face equals requested `n` at both endpoints within epsilon; `inner ~= 0 / outer ~= n` is invalid。For every shared step boundary, lower-tread rear support equals destination-Riser back boundary exactly, with no open wedge cavity。BEVEL/ROUND use the same semantic front-edge authority。Width650 is a regression sample, not a lower bound。

---

# 31. Stage 1 — canonical Turn + first 90° L Winder

Implement / accept：

- identity 0.7.4
- schema-5 foundation
- `path_point_id` Turn identity
- `winder_pattern` authority
- generalized Turn frame pure helpers
- 90° L Winder EQUAL_2/3/4 nominal cells
- exact RiseEvent ownership / AUTO allocation
- SQUARE Winder Tread/Riser physical geometry
- transaction / rollback / basic persistence
- schema-1/2/3/4 regression

Stage 1 does not need BF / U / arbitrary-angle / final underbody / Side Board finished。

Runtime focus：EQUAL_2/3/4 appearance, total rise, Reverse basic, save/reopen, invalid rollback, width900/750/650 where applicable。

---

# 32. Stage 2 — BF + U / Compact U + arbitrary-angle

Internal order：

```text
2A BF patterns
2B U / Compact U
2C arbitrary-angle Landing
2D arbitrary-angle EQUAL Winder
2E positive nosing / front-edge finish integration where not already active
```

Implement / accept：

- BF exact fractions
- per-Turn mode/pattern
- U per-Turn combinations
- Compact-U classification/shared section
- arbitrary-angle Landing
- arbitrary-angle EQUAL Winder
- free-angle point relocation; Shift15 remains convenience
- full schema-5 AUTO / MANUAL
- schema-4 migration guards
- deterministic regeneration
- constant-distance physical Winder nosing
- finite inner physical miter instead of pivot collapse
- exact shared Tread rear-support / destination-Riser boundary reuse
- no open Winder tread/Riser cavity
- 90-degree and arbitrary-angle physical Winder finish
- U / Compact-U use the same physical boundary authority

These physical requirements are Stage 2 and must not be deferred to Stage 3。

Do not debug all families simultaneously。

---

# 33. Stage 3 — CLOSED underbody + Side Board

Internal order：

```text
3A STEPPED_CLOSED, Side Boards OFF
3B SLOPED_CLOSED, Side Boards OFF
3C ordinary Side Board continuation
3D Compact-U shared-center Side Board
3E Material / Reverse / Repair / topology sweep
```

Required：

- Winder STEPPED_CLOSED exact cell Z contract
- continuous SLOPED_CLOSED finite pivot relief
- no Landing plateau through Winder
- Winder/Flight exact joins
- ordinary STEPPED/SLOPED Side Board upper/lower authority
- Compact-U shared-center family / butt joints / 3D trims
- body remains CLOSED with Side Boards OFF
- Material lifecycle
- no cavity/spike/giant filler/duplicate positive-volume body
- width900/800/750/700/650 full-finish fixtures

Stage-3 implementation may not redesign already accepted TREAD/RISER plan authority except explicit shared-board derived trim。

---

# 34. Stage 4 — lifecycle / full regression / practical acceptance

Cover：

- Candidate identity
- schema-1/2/3/4 regression
- schema-5 L/U/arbitrary persistence
- EQUAL/BF persistence
- AUTO/MANUAL persistence
- mixed LANDING/WINDER invariant
- schema-4 migration guard
- Undo/Redo
- invalid rollback
- Repair
- duplicate Stair ID repair
- Material lifecycle
- Reverse
- Save/full exit/reopen
- Finalize
- active-only Delete
- Wall / Finish isolation
- practical Wall/Floor-like placement
- narrow old-house cases
- topology finite / zero-area / boundary / nonmanifold expectations
- deterministic repeated Regenerate
- full automated regression
- compileall
- git diff --check

07-E overall ACCEPTED only after Stage 4 runtime acceptance。

---

# 35. Automated / runtime test policy

Pure/testable logicをBlender modal codeから分離する。

Pure tests include at least：

- signed theta
- normals / corridor intersections
- Turn envelope / exact90 reduction
- cutback equivalence
- EQUAL / BF fractions
- outer-chain O preservation / dedup
- left/right mirror
- Reverse pattern identity
- nominal coverage / overlap / gaps
- RiseEvent ownership / `S+L+W+1=N`
- deterministic AUTO allocation
- schema migration
- Compact-U classification / shared height
- arbitrary Landing/Winder
- finite pivot relief / ray-chord intersections
- STEPPED patch Z
- Side Board profile component rules / point-contact separation / butt-joint ownership
- narrow-width property/UI guard
- deterministic geometry
- constant-offset Winder nose endpoints at 90-degree and 63-degree Turns
- finite inner miter not forced to nominal `I`
- exact tread rear-support / Riser-back coordinate reuse
- BF_1+BF_2 U and Compact-U semantic-boundary reuse
- REVERSE physical ownership
- SQUARE/BEVEL/ROUND semantic exposed-edge identity
- width650 physical geometry and deterministic trim points

Visual runtime additionally inspects inner nosing and outer junctions from an oblique angle where any background-visible cavity is evident。

Dedicated：

```text
tests/test_build_07_e_stage1.py
...
tests/test_build_07_e_stage4.py
```

Prior 07-A/B/C/D suites remain regression targets。

Runtime：Console canonical evidence + visual where geometry appearance matters。

Visual mandatory for Winder shape, BF, Compact U, arbitrary Landing, SLOPED underside, pivot local closure, Side Board joins。

Stage 3 specifically inspect `HIGH_SIDE_PIVOT_CLOSURE` with Side Boards OFF from below / pivot side / normal residential view。

---

# 36. Acceptance principles

07-E overall Acceptance requires all：

1. schema-1/2/3/4 accepted behavior not silently migrated/regressed。
2. EQUAL_2/3/4 from one general partition rule。
3. BF_1 `[2/3]`, BF_2 `[1/3]` text-only deterministic。
4. U as two persistent per-Turn assignments。
5. Compact U handles zero ordinary middle run without false short-flight rejection。
6. arbitrary-angle Landing from generalized envelope。
7. representative arbitrary-angle EQUAL Winder。
8. Shift15 not production angle restriction。
9. RiseEvent exact, no double count, `S+L+W+1=N`。
10. schema-4 MANUAL not silently converted to Winder。
11. physical Tread/Riser/nosing ownership deterministic; positive Winder nosing does not collapse at `I`, adjacent physical components have no open exterior cavity, and semantic shared boundaries are reused exactly。
12. EQUAL_3 central outer corner O not omitted。
13. STEPPED_CLOSED Winder uses exact schema-5 patch Z and remains CLOSED。
14. SLOPED_CLOSED uses complete outer chain + finite pivot relief + local high-side closure, no horizontal Landing plateau。
15. no T-junction on semantic shared edges。
16. Compact-U shared SLOPED height follows ascent-order event grouping。
17. Side Board lower/upper authorities preserve 07-C independence。
18. Compact-U center board uses shared profile, point-only contacts stay separate, deterministic butt joints and actual 3D trim including RISER。
19. width900/800/750/700/650 fixed full-finish fixtures pass as specified; 650 is not a lower bound。
20. legal-like minima are not hidden in validator/RNA/UI/preset。
21. invalid geometry gives clear class + atomic rollback。
22. Save/Reopen / Undo/Redo / Repair / Finalize / Delete / Materials work。
23. Wall / Finish isolation preserved。
24. Practical residential placement has no major failure。
25. implementation/review possible from repository text without reference images。

---

# 37. Explicit non-scope

07-E does not require：

- spiral/helical stair
- curved Flight centerline
- freehand curved Winder edge
- per-divider custom editor
- building-code compliance judgment / legal pass-fail
- variable width along one Flight
- non-uniform riser heights within one Stair
- Riser OFF / Underside NONE / open/support variants (07-F)
- sawtooth / center support (07-F)
- handrail/newel/baluster
- separate Winder Material role
- automatic Wall/Floor/Room attachment
- automatic Stair opening / Floor Boolean
- production UV guarantee
- default stair width 900→750 change
- general Stair panel compacting/collapsible UI redesign
- Winder production guarantee on 3+ Turn custom Path

---

# 38. Final implementation order

```text
accepted 07-D compatibility
    ↓
schema-5 Turn identity / pattern authority
    ↓
generalized Turn frame
    ↓
RiseEvent / AUTO allocation
    ↓
90° L EQUAL_2/3/4 top geometry
    ↓
BF + U / Compact U
    ↓
arbitrary-angle Landing / Winder
    ↓
physical nosing / finish integration
    ↓
STEPPED_CLOSED
    ↓
SLOPED_CLOSED finite pivot relief
    ↓
ordinary Side Board
    ↓
Compact-U shared Side Board
    ↓
full lifecycle / practical acceptance
```

Top-plan / RiseEvent authorityをruntimeで固める前に、複雑なunderbody / Side Board debuggingへ進まない。

If implementation reveals a fixed success fixture is impossible under the reviewed contract, do not silently weaken the fixture。Determine whether implementation is wrong or Specification correction/addendum is required。

07-E Acceptance完了後はRoadmapどおり07-F / 07-GをHOLDし、08-A / 08-Bへ進む。
