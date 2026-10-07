# BUILD 07-E STAGE 3C IMPLEMENTATION PLAN
## Japanese House Modeler — Ordinary Winder Side Board Continuation

Date: 2026-10-07

## 1. Status / authority

- Build 07-E Stage 2.5 — ACCEPTED
- Fresh Stage 3A — ACCEPTED
- Fresh Stage 3B — ACCEPTED at runtime r9
- Fresh Stage 3C — CURRENT
- Fresh Stage 3D — PENDING
- Fresh Stage 3E — PENDING
- Build 07-E overall — NOT YET ACCEPTED

This document is the focused implementation plan for Fresh Stage 3C. It must be read together with:

1. `BUILD_07_E_SPECIFICATION.md` Section 39;
2. `BUILD_07_E_STAGE_3B_ACCEPTANCE_RECORD.md`;
3. `BUILD_07_E_STAGE_3A_ACCEPTANCE_RECORD.md`;
4. `BUILD_07_D_ACCEPTANCE_RECORD.md`.

Where older Sections 20–24 conflict with the accepted Fresh Stage-3B body contract, Section 39 and this plan take precedence.

## 2. Accepted baseline that must not regress

Fresh Stage-3B runtime-tested production authority:

```text
commit 389f7e9d30a181c3fcd2c578e8af7bbdc16189e7
tree   3154653ca6b608b1ae7b11e42a40d497b7c50b99
```

Accepted runtime add-on archive:

```text
Japanese_House_Modeler_Build_07_E_Stage3B_ACCEPTED_r9.zip
size    165405 bytes
SHA256  8e8f9b81eb129060c85938a87ca53bd25372991316e4dfce79c1b9e1bb083bda
```

Stage 3C must not redesign or move:

- accepted Winder TREAD/RISER geometry;
- mathematical Winder inner pivot;
- canonical outer corner / complete outer chain;
- Stage-3B shared rear/exterior authority;
- Winder STEPPED_CLOSED prism body;
- Winder SLOPED_CLOSED prism body;
- accepted Straight Flight body geometry;
- accepted schema-4 07-D Landing/Residential geometry.

Turning Side Boards ON must not require rewriting accepted TREAD/RISER/UNDERBODY geometry.

## 3. Stage-3C goal

Add ordinary schema-5 Winder Side Board production while preserving the accepted body/top geometry.

Stage 3C supports the normal, non-shared-center cases:

- 3-point L with one Winder Turn;
- 4-point U with ordinary non-zero middle Flight;
- LEFT and RIGHT Side Board independently enabled;
- `STEPPED_CLOSED` and `SLOPED_CLOSED`;
- `STEPPED` and `SLOPED` Side Board upper modes;
- EQUAL_2 / EQUAL_3 / EQUAL_4;
- BF_1 / BF_2 where already supported;
- arbitrary-angle EQUAL Winder;
- FORWARD / REVERSE mapping.

Compact-U shared-center Side Board is explicitly Stage 3D and is not implemented in Stage 3C.

## 4. Independent lower / upper authority

Preserve the accepted 07-C independence:

```text
underside_mode  -> Side Board lower boundary
side_board_mode -> Side Board upper / visible boundary
```

Required combinations:

```text
STEPPED_CLOSED + STEPPED board
STEPPED_CLOSED + SLOPED board
SLOPED_CLOSED  + STEPPED board
SLOPED_CLOSED  + SLOPED board
```

For Straight Flights, reuse accepted existing Side Board profile helpers and terminal semantics wherever applicable.

For Winder cells, Stage-3B is now the lower-boundary authority. Do not revive the abandoned station-driven Winder SLOPED soffit / pivot-relief production model merely because the Side Board needs a lower edge.

## 5. Winder Side Board plan path

The Winder board path must be derived from accepted Turn geometry rather than from a new independent approximation.

### Outer side

Use the complete accepted exterior traversal:

```text
entry_outer -> outer_corner -> exit_outer
```

and all required physical/canonical stations already present on that traversal.

The exact canonical `frame.outer_corner` must remain present whenever the path crosses the corner. Never replace it with a chord between adjacent physical endpoints.

### Inner side

Use the accepted Turn inner-side boundary derived from the existing Winder cell/frame geometry. Preserve the mathematical pivot and the accepted entry/exit inner boundary positions. Do not move the pivot merely to make Side Board thickness easier.

### Thickness

`side_board_thickness_mm` is real plan thickness. The board thickness extends away from the walking width on the selected side; it must not consume the canonical stair width or move the tread/riser authority.

LEFT / RIGHT remain uphill-relative. REVERSE must recompute world-space side ownership from ascent traversal rather than retaining stale canonical/world-side assignment.

### Plan-corner joints

A Winder Side Board may be assembled from deterministic closed sub-fragments rather than one Boolean-unioned solid.

Allowed:

- hidden overlap between adjacent board sub-fragments;
- deterministic corner overlap/fill used only to avoid a visible gap;
- separate closed components inside one Managed Stair.

Required:

- no visible daylight gap at Turn joints;
- no major spike / giant filler face;
- no externally visible z-fighting from duplicate coplanar exterior faces;
- no board segment crossing through the walking width.

Exact Boolean union is not required.

## 6. Winder lower boundary

The lower boundary must follow the accepted body exterior on the same selected side.

For Winder cells, both `STEPPED_CLOSED` and Winder `SLOPED_CLOSED` use the accepted Stage-3B matching-ring prismatic body. Therefore Side Board lower stations must be derived from that body, not from historical Section-21 sloped interpolation.

Within one Winder body cell:

- lower Z is the accepted lower-ring Z for that cell;
- inserted outer-corner geometry within the same cell keeps that same lower Z;
- transitions between cells use the accepted per-cell body levels;
- body/base-floor handling remains unchanged.

At Straight/Winder boundaries, reuse existing Straight lower-profile authority on the Straight side and the exact accepted Winder body boundary on the Turn side.

## 7. Winder upper boundary

### STEPPED Side Board

For each Winder destination tread:

```text
upper level = destination tread top + side_board_reveal
```

subject to existing accepted terminal/cap semantics.

- horizontal upper level remains constant inside the cell;
- each real Winder RiseEvent creates the corresponding vertical upper transition;
- an inserted geometry-only outer corner adds no RiseEvent and keeps the same cell upper level.

### SLOPED Side Board

Derive the upper line from walking-surface / Side Board reveal authority, never from underbody Z interpolation.

- primary upper stations correspond to the ordered Winder walking/RiseEvent sequence;
- between primary stations, use deterministic linear interpolation;
- if the canonical outer corner lies inside an interval, insert it at its exact plan position and interpolate upper Z by its fraction;
- the outer corner adds no tread/RiseEvent;
- retain accepted front/rear terminal caps where required.

## 8. Straight / Winder continuation

The ordinary Side Board must visibly continue across:

```text
Straight -> Winder -> Straight
```

without requiring changes to the accepted top/body.

Required:

- no daylight gap at the entry/exit board seam;
- no visible board jump caused by stale LEFT/RIGHT mapping;
- no new TREAD/RISER/UNDERBODY movement;
- existing reveal and side-board thickness values remain authoritative;
- terminal overlap hidden inside a joint is acceptable under the visual-first policy.

For an ordinary two-Turn U stair with a real middle Flight, each Turn is solved independently and the existing middle-Flight board remains a normal Flight board.

## 9. Stage-3D boundary

If the selected geometry is Compact-U and enabled Side Boards would require the shared-center treatment, Stage 3C must not invent two coincident complete center boards.

Until Stage 3D:

- Side Boards OFF: existing Compact-U Stage-3B behavior remains fully supported;
- Side Boards ON in a Compact-U shared-center configuration: return a clear `SCOPE_UNSUPPORTED` / Stage-3D-deferred error before Scene mutation.

Do not silently disable a requested center board and do not generate duplicated shared-center boards.

## 10. Production architecture guidance

Prefer narrow additions around the existing `prepare_turn_residential_geometry(...)` Stage-3A/3B path.

Expected direction:

- remove the blanket Stage-3C Side Board rejection only for the supported ordinary topology;
- reuse existing `ResidentialFields`, reveal/thickness validation and accepted Straight Side Board helpers;
- add pure Winder-side chain/profile helpers in the smallest appropriate module;
- build SIDE_BOARD fragments separately from TREAD/RISER/UNDERBODY;
- append board fragments after accepted top/body preparation;
- keep candidate preparation atomic before Scene mutation.

Do not route schema-4 07-D Stairs through the schema-5 Winder board path.

## 11. Mandatory automated tests

Create focused Stage-3C tests, preferably a new:

```text
tests/test_build_07_e_stage3c_fresh.py
```

At minimum cover:

1. exact-90 L / EQUAL_3 / STEPPED_CLOSED + STEPPED board / both sides ON;
2. exact-90 L / EQUAL_3 / SLOPED_CLOSED + SLOPED board / both sides ON;
3. both mixed lower/upper combinations;
4. LEFT-only and RIGHT-only production;
5. Side Boards OFF produces the exact accepted Stage-3B non-board signature;
6. turning boards ON does not alter TREAD/RISER/UNDERBODY fragment geometry/signature;
7. EQUAL_2 and EQUAL_4 outer board traversal retains the canonical outer corner;
8. BF_1 / BF_2 smoke;
9. approximately 63-degree EQUAL Winder smoke;
10. ordinary non-Compact-U two-Turn U;
11. at least one REVERSE case proving LEFT/RIGHT is ascent-relative;
12. deterministic repeated preparation;
13. Compact-U + boards ON is explicitly Stage-3D-deferred with atomic failure;
14. Compact-U + boards OFF remains Stage-3B-compatible;
15. schema-4 Build 07-D regression remains unchanged;
16. finite / non-degenerate / valid fragment checks.

Also run the existing Stage-2.5, Stage-1/2, Fresh Stage-3A, Stage-3B, Build-07-D and full discovery suites.

## 12. Runtime focus after implementation

Blender runtime acceptance will be performed by GPT + user, not by Codex automation.

The initial runtime order should be intentionally narrow:

```text
1. 90-degree L / EQUAL_3 / STEPPED_CLOSED + STEPPED board
2. same L / SLOPED_CLOSED + SLOPED board
3. mixed combinations
4. LEFT-only / RIGHT-only
5. EQUAL_2 / EQUAL_4 outer-corner regression
6. BF and arbitrary-angle smoke
7. ordinary U
8. REVERSE
9. deterministic regenerate / save-reopen
10. schema-4 07-D smoke
```

Compact-U Side Board visual acceptance belongs to Stage 3D.

## 13. Explicit non-goals

Stage 3C does not implement:

- Compact-U shared-center board union/trim;
- Stage-3D shared-center transition;
- new Material architecture;
- Stage-3E full lifecycle sweep;
- Stage-4 final overall acceptance;
- Boolean union / exact-solid cleanup;
- handrails / balusters / newels;
- changes to Stage-3B body geometry;
- changes to accepted Winder top geometry.

## 14. Completion boundary

Codex implementation work for Stage 3C is complete only when:

- production code and focused tests are implemented;
- all requested automated suites pass;
- `python -m compileall -q japanese_house_modeler tests` passes;
- `git diff --check` passes;
- final branch/commit/tree and changed-file summary are reported.

Codex must not write the Stage-3C Acceptance Record, must not mark Stage 3C ACCEPTED, must not create a Candidate ZIP, and must not merge the PR. Those are GPT/user runtime-acceptance steps after Blender testing.
