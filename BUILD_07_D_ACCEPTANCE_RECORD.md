# BUILD 07-D ACCEPTANCE RECORD
## Japanese House Modeler — Multi-point Path + L / U + Landing

Date: 2026-09-27

## 1. Status

- Build 07-D Stage 1 — **ACCEPTED**
- Build 07-D Stage 2 — NOT YET ACCEPTED
- Build 07-D Stage 3 — NOT YET ACCEPTED
- Build 07-D Stage 4 — NOT YET ACCEPTED
- Build 07-D overall — **IN PROGRESS**

Stage 1 establishes the schema-4 Multi-point foundation and first visible 3-point L Stair while preserving accepted schema-1/2/3 Straight behavior. Build 07-D overall is not accepted until Stage 4.

Implementation authority remains `BUILD_07_D_SPECIFICATION.md`.

## 2. Runtime-tested revision and artifact

GitHub PR: #27

Exact runtime-tested production revision:

```text
commit 6d24ef67bcad965c06fd9ce9a06ec91fb7a77b0c
tree   fbdd1a7b90fd7c6ea7032cee457dc56e2e364057
```

Runtime Candidate:

```text
Japanese_House_Modeler_Build_07_D_Stage1_Candidate_r1.zip
SIZE    125181 bytes
SHA256  05e012fdf3e1a043275b1d000f6eff9f0ced9f54e71c1dcef5985a87332c7215
```

Runtime environment:

```text
Blender 5.2.0 LTS
Add-on version: (0, 7, 3)
Description: Build 07-D: Multi-point Path + L/U + Landing
```

Documentation / acceptance commits created after runtime review do not supersede the exact runtime-tested revision above.

## 3. Automated evidence

Final Stage-1 implementation report:

```text
tests.test_build_07_d_stage1                         27 PASS
07-A targeted suites                                 84 PASS
07-B targeted suites                                 98 PASS
07-C targeted suites                                 90 PASS
python -m unittest discover -s tests                662 PASS
compileall                                            PASS
git diff --check                                     PASS
git status --short                                  clean
```

The final Stage-1 test set covers creation-only exact-90-degree projection, strict canonical 90-degree validation, deterministic AUTO allocation and reallocation, preserved allocation on ordinary Regenerate / Reverse, schema-4 managed-state diagnosis, point-identity validation, legacy schema-1/2/3 diagnosis isolation, prepare-before-mutation, and accepted Straight regression.

## 4. Stage 1 accepted contracts

Stage 1 accepts the following production behavior:

- add-on identity `(0, 7, 3)` / `Build 07-D: Multi-point Path + L/U + Landing`
- schema 4 only for explicit Multi-point Stair state
- schema 1/2/3 are not silently upgraded on read
- existing accepted 2-point Straight Stair path remains schema 3 and preserves 07-C geometry / lifecycle behavior
- 3-point L Path: `P0 = START`, `P1 = TURN`, `P2 = END`
- persistent non-empty unique point IDs for schema-4 Path points
- Stage-1 Turn mode = `LANDING`
- Stage-1 distribution mode = `AUTO`
- strict canonical 90-degree L validation
- creation-only third-click projection to an exact local +/-90-degree L candidate
- saved / numeric canonical data is not silently projected or repaired
- one Managed Stair = one Mesh Object
- identity Object Transform in normal managed state
- Landing uses existing `TREAD` Material role; no new `LANDING` Material role
- whole-Stair `actual_riser = floor_to_floor / overall_riser_count`
- sum of per-Flight riser allocations equals overall riser count
- each Stage-1 production Flight has at least two risers
- Landing elevation is derived from cumulative preceding risers
- upper arrival remains exactly `base_z + floor_to_floor`
- Reverse changes ascent traversal without reordering canonical Path points or physical Flight allocation
- schema-4 dimension edits recompute AUTO allocation when dimensions affecting the resolved layout change
- ordinary Regenerate / Reverse / Repair preserve a valid saved AUTO allocation snapshot
- invalid schema-4 point IDs, Turn state, distribution state, or saved allocation diagnose as `INVALID_CANONICAL`
- invalid L creation is rejected before Scene mutation

## 5. Runtime acceptance — all 6 grouped tests PASS

### Test 0 — Candidate identity + accepted Straight regression — PASS

Runtime identity:

```text
version=(0,7,3)
blender=(5,2,0)
description=Build 07-D: Multi-point Path + L/U + Landing
```

Representative Straight evidence:

```text
TYPE=MESH
SCHEMA=3
PATH_POINTS=2
POINT_IDS=['', '']
TRANSFORM=(0,0,0) (0,0,0) (1,1,1)
```

The user exercised dimension edits, Reverse, Regenerate, STEPPED_CLOSED / SLOPED_CLOSED, STEPPED / SLOPED Side Board, nosing / front-edge settings, and Material UI. Accepted 07-C Straight behavior remained available and schema-4 state did not leak into the Straight Stair.

### Test 1 — 3-click L creation + canonical identity — PASS

Representative evidence:

```text
TYPE=MESH
SCHEMA=4
PATH_POINTS=3
TURN=LANDING
DISTRIBUTION=AUTO
ALLOCATION=8,8
UNIQUE_IDS=3
TRANSFORM=(0,0,0) (0,0,0) (1,1,1)
```

All three Path point IDs were non-empty and unique. The resulting geometry was visibly L-shaped, with Flight 1, a horizontal Landing, Flight 2, and one selected Mesh Object.

The resolved P0-P1 / P1-P2 relation was effectively exact 90 degrees, confirming the creation-time projection path.

### Test 2 — AUTO allocation + height invariants + reallocation / Reverse — PASS

Initial 16-riser evidence:

```text
ALLOCATION=(8,8)
TOTAL=16
ACTUAL_RISER=0.175
LANDING_Z=1.4
UPPER_Z=2.8
EXPECTED_UPPER=2.8
FLIGHT 1: 8 risers, Z 0.0 -> 1.4
FLIGHT 2: 8 risers, Z 1.4 -> 2.8
```

After UI dimension edit `riser_count 16 -> 17`:

```text
RISER_COUNT=17
SAVED_ALLOCATION=8,9
SUM=17
STATE=AUTO
```

After Reverse:

- canonical Path order preserved
- point ID order preserved
- allocation `8,9` preserved on physical canonical Flights
- ascent direction changed to `REVERSE`

### Test 3 — visual L / Landing connection review — PASS

Visual review accepted:

- Flight 1 stair geometry
- horizontal Landing
- Flight 2 stair geometry
- L-shaped overall route
- Flight 1 -> Landing connection
- Landing -> Flight 2 connection
- no obvious major gap
- no unintended giant overlap
- no spike / detached fragment
- one-object management

Stage-1 deferred Side Board / CLOSED-underbody turn completion was not treated as an acceptance requirement.

### Test 4 — save / full exit / reopen + Regenerate — PASS

After save -> full Blender exit -> relaunch -> reopen:

```text
SCHEMA=4
PATH=3 points
UNIQUE_IDS=3
TURN=LANDING
MODE=AUTO
ALLOCATION=8,9
RISERS=17
TYPE=MESH
TRANSFORM=identity
MESH=264 vertices / 198 faces
```

After Regenerate:

```text
SCHEMA=4
ALLOCATION=8,9
point IDs unchanged
```

Thus Path order, point identity, Turn state, AUTO snapshot, dimensions, managed Mesh state, and identity Transform persisted across full application restart and ordinary regeneration.

### Test 5 — invalid rollback + Straight isolation — PASS

A valid schema-3 Straight Stair was recorded, then an intentionally impossible L candidate was attempted using a 4000 mm Stair width with approximately 1 m Flights.

User-facing rejection:

```text
Landing cutback後のFlight長が不足しています。
```

Rollback evidence:

```text
UNCHANGED=True
MANAGED=3 -> 3
MESHES=4 -> 4
STRAIGHT_SCHEMA=3
STRAIGHT_ID unchanged
```

No partial managed Stair, orphan Mesh, schema-only mutation, ID change, Transform change, Material change, or mutation of the existing Straight was left behind.

## 6. Stage 1 intentionally deferred scope

The following remain for later 07-D stages and are **not** claimed by Stage 1 acceptance:

- START / TURN / END mouse relocation
- Shift 15-degree constraint
- X/Y / 90-degree / parallel / extension / passive Wall alignment guides
- Multi-point numeric editing UI
- MANUAL riser distribution
- AUTO <-> MANUAL handoff
- complete Landing CLOSED-underbody connection
- complete Multi-flight Side Board connection
- complete nosing / SQUARE / BEVEL / ROUND turn integration
- U-shaped / 4-point Stair
- Custom Multi-point production path
- Winder / 廻り段

These are governed by `BUILD_07_D_SPECIFICATION.md` Stage 2 / Stage 3 / Stage 4.

## 7. Acceptance conclusion

Build 07-D Stage 1 is **ACCEPTED** at the exact runtime-tested production revision listed in Section 2.

The next implementation target is Build 07-D Stage 2: L complete + editing UX. Build 07-D overall remains IN PROGRESS until Stage 4 acceptance.
