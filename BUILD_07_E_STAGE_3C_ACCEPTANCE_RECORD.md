# BUILD 07-E FRESH STAGE 3C ACCEPTANCE RECORD
## Japanese House Modeler — Ordinary Winder Side Board Continuation

Date: 2026-10-08
Authority: BUILD_07_E_SPECIFICATION.md Section 39; BUILD_07_E_STAGE_3C_PLAN.md; DEVELOPMENT_WORKFLOW.md

## 1. Acceptance decision and scope

**Fresh Build 07-E Stage 3C — ACCEPTED (Blender 5.2 LTS, Candidate r7).**

- Stage 1 / Stage 2 / Stage 2.5 / Fresh Stage 3A / Fresh Stage 3B — previously **ACCEPTED**.
- Fresh Stage 3C — **ACCEPTED within ordinary Winder Side Board scope**.
- Fresh Stage 3D (Compact-U shared-center Side Board) — **PENDING**.
- Fresh Stage 3E (Material / Reverse / lifecycle regression) — **PENDING**.
- Stage 4 and Build 07-E overall — **NOT YET ACCEPTED**.
- Old Stage-3 PR #33 remains **ABANDONED / NOT MERGED**.

The user completed the Stage-3C Blender runtime Test 1–10 acceptance sequence and approved completion on 2026-10-08. Runtime evidence was submitted as Blender Python Console results, screenshots and selected confirmed mesh files. Console results and visual review have different evidentiary roles; a Python-only regression suite is not Blender runtime evidence.

**Known qualified acceptance:** EQUAL_4 + SLOPED outer Side Board can exhibit an aesthetically undesirable change of upper-edge slope. It was expressly left unmodified at r7 and provisionally considered usable. Acceptance does **not** claim the EQUAL_4 silhouette is corrected or as visually continuous as EQUAL_2 / EQUAL_3 / BF_1 / BF_2. Revisit if later production or reference geometry requires it.

## 2. Exact runtime-tested production identity

GitHub PR: [#48](https://github.com/asleep-cdx/blender-japan-building-addon/pull/48)

```text
GitHub runtime-tested commit
d88d5c597fafb49ac8b0debeedd048ce2bd8e648

Git tree SHA
9ab5eadb8ee3fe1524a5e627a3ce7768a7932dbd

Codex final local commit for same production tree
9734388092fe6377421c206c29aee188a3435076

Codex final local tree
9ab5eadb8ee3fe1524a5e627a3ce7768a7932dbd
```

Candidate used for final r7 Blender runtime acceptance:

```text
Japanese_House_Modeler_Build_07_E_Stage3_Candidate_r7.zip
Size:    172684 bytes
SHA256:  2a0cbd92cd91f076243744ef1df83ad01d29e38098582c5209c24c287685a455
Source:  exact GitHub runtime-tested commit above
```

Runtime environment: Blender 5.2 LTS on Windows. The candidate archive was built by `git archive ... <commit> japanese_house_modeler`, checked with Windows `for %F` and `certutil -hashfile`, installed, and exercised in Blender.

Documentation-only commits made after this runtime test **must not** be described as a new runtime-tested production revision. The post-merge `main` tree is expected to differ due to acceptance documentation. Identify and archive the actual runtime-tested source separately.

## 3. Implemented geometry / correction history

Stage 3C enables independently selected LEFT and RIGHT ordinary Winder Side Boards with upper modes `STEPPED` or `SLOPED`, underbody `STEPPED_CLOSED` or `SLOPED_CLOSED`, and ordinary L or two-Turn U topology; Compact-U shared-center treatment remains deferred.

Candidate correction chronology:

1. **r2 / upper-arrival correction:** accepted Winder/upper-arrival top semantics restored without changing frozen TREAD/RISER production.
2. **r4 / outer STEPPED correction:** corrected outer Side Board continuity and return/profile, preserving accepted non-board geometry.
3. **r5 / inner joint correction:** removed per-Winder-cell inner fan/wedge boards; Turn inner boundary now joins adjacent Straight Side Boards. The local joint is not world-X/Y dependent.
4. **r6 / outer SLOPED correction:** replaced per-cell changing visible slopes with an analytic upper-edge construction and defined fallback when a level-B join is geometrically infeasible.
5. **r7 / EQUAL_2 and BF_2 correction:** corrected the outer SLOPED upper-edge physical-tread clearance while preserving EQUAL_3 / BF_1 and leaving known EQUAL_4 appearance for later.

Accepted Stage 3B TREAD, RISER, both UNDERBODY modes, the canonical outer corner, RiseEvents, allocation and accepted Build 07-D schema-4 production remain protected by fixed-signature and semantic regressions. Independent closed fragments with hidden overlap are permissible per the visual-first contract; this stage does not claim a Boolean-unioned single solid.

## 4. Automated and static evidence (Codex report; not independently rerun in Blender)

Final r7 reported:

| Suite / check | Result |
|---|---|
| Stage 2.5 | 6 PASS |
| Stage 1 + 2 | 127 PASS |
| Fresh Stage 3A | 10 PASS |
| Fresh Stage 3B | 17 PASS |
| Fresh Stage 3C | 54 PASS |
| Build 07-D Stage 1–4 | 131 PASS |
| `python -m unittest discover -s tests` | **980 PASS** |
| `python -m compileall -q japanese_house_modeler tests` | PASS |
| `git diff --check`, `git diff HEAD^ --check` | PASS |

These numbers are taken from the Codex final r7 implementation report for the production tree above. They are not inferred from the screenshots, and were not rerun after documentation-only commits.

## 5. Blender 5.2 LTS runtime acceptance

The accepted runtime program follows the numbered focus of `BUILD_07_E_STAGE_3C_PLAN.md` Section 12. The user exercised the cases with Python Console where possible, and with Blender viewport / UI screenshots for geometry.

| Runtime group | Result | Evidence / qualification |
|---|---|---|
| 1. Exact-90 L, EQUAL_3, STEPPED_CLOSED + STEPPED boards | PASS after focused corrections | Visual outer/inner joints and no major visible geometry defect; prerequisite for continuing tests |
| 2. Exact-90 L, EQUAL_3, SLOPED_CLOSED + SLOPED boards | PASS at r7 | Original outer slope failure at r5 led to r6/r7 corrections; r7 visually accepted |
| 3. Mixed underbody/board upper combinations | PASS | Runtime `STEPPED_CLOSED + SLOPED` and `SLOPED_CLOSED + STEPPED`; canonical stair issues empty; screenshots and mesh checks |
| 4. LEFT-only / RIGHT-only / both OFF and ON | PASS | Runtime independent toggles; `stair_issues=()`; no new visually defective body |
| 5. EQUAL_2 / EQUAL_3 / EQUAL_4 outer-corner regression | PASS within stated exception | EQUAL_2 corrected by r7; EQUAL_3 retained; EQUAL_4 geometric use accepted with visual slope-change follow-up expressly deferred |
| 6. BF and arbitrary-angle cases | PASS within supported scope | BF_1/BF_2 and about 63-degree EQUAL_3 passed supported smoke checks; BF on non-right-angle Turn explicitly unsupported with warning, not a geometry regression |
| 7. Ordinary two-Turn U (not Compact-U) | PASS | Both Turns `WINDER / EQUAL_3`, 16 risers, `auto_riser_allocation='4,2,3'`, `V/E/F=652/1204/670`; 0 non-manifold edges / zero-area faces; no stair issues; screenshots |
| 8. Ascent REVERSE and return | PASS | FORWARD -> REVERSE -> FORWARD or reverse-return checks preserved Stair ID, path/Turn definitions and reproducible geometry; U example `V/E/F=652/1204/670` |
| 9. Deterministic regenerate, state/change-rollback tests | PASS with Redo caveat | Two regenerations compared mesh/state identically; reveal 40 -> 60 mm changed geometry, Undo restored exact prior snapshot. Native Redo was unavailable in Python Console context (`bpy.ops.ed.redo.poll() == False`); manually re-executing the edit reproduced the 60-mm snapshot. **Do not claim native Ctrl+Shift+Z Redo was verified in that Console test.** |
| 10A/10B. Build 07-D schema-4 compatibility | PASS | Existing schema-4 L and U stairs remain schema 4 after regenerate; original snapshot matches and issues are empty. U example `T15_U`, `V/E/F=512/919/497`, before/after hash identical |

Additional runtime examples in this program:

- Stage-3C L base, REVERSE, two-Turn U: `stair_issues=()`, with manifold and zero-area checks reported zero where executed.
- Repeated REVERSE cycle returned identical full mesh coordinate and polygon signature.
- Reveals, board toggles, mixed upper/lower variants and selected patterns were evaluated with the already installed r7 production revision; no code change was made during this final acceptance suite.

The submitted runtime suite was accepted by the user as complete. The runtime test was **not** a proof of every possible angle/dimension, every mesh-intersection configuration, or an independently verified successful native Redo in the Console test.

## 6. Known scope boundaries / follow-up

1. **EQUAL_4 with SLOPED outer Side Board**: visible slope-angle transition remains. It is *accepted for this Stage 3C release as a known visual limitation*, not resolved. Do not record unconditional perfect continuity.
2. **Compact-U shared-center Side Board**: deferred to Fresh Stage 3D. Side Boards ON in the compact shared-center configuration should reject atomically instead of manufacturing doubled boards.
3. **Non-90-degree BF patterns**: explicit unsupported warning is expected by current scope; non-90-degree EQUAL patterns are the supported arbitrary-angle Winder path.
4. **Legacy physical Winder TREAD/RISER gaps**, already documented in prior stage records, are not reinterpreted as new 3C board defects.
5. **Redo**: the Console-driven reveal reapply demonstrated deterministic state restoration, not a native Redo transaction. Full lifecycle coverage continues in Fresh Stage 3E / Stage 4.
6. **Save/reopen and subsequent cross-feature lifecycle**: do not infer stronger guarantees than the runtime cases actually recorded; Stage 3E / Stage 4 remain responsible for extended lifecycle regression.

## 7. Final Stage-3C acceptance

**Fresh Stage 3C — ACCEPTED at Candidate r7**, with the explicit EQUAL_4 visual exception and Stage-3D/3E deferred items above.

Exact production authority:

```text
commit d88d5c597fafb49ac8b0debeedd048ce2bd8e648
tree   9ab5eadb8ee3fe1524a5e627a3ce7768a7932dbd
```

Next development scope: **Fresh Stage 3D (Compact-U shared-center Side Board)**; Stage 3E and Build Stage 4 follow. Build 07-E overall is **NOT YET ACCEPTED**.

Post-merge archive policy:

- Copy the **actual r7 Candidate ZIP bytes** to `C:\AI-Blender\Build_Archives\Build_07_E\` as a Stage-3C ACCEPTED Addon archive; verify its size and SHA-256 against the runtime Candidate above.
- Build the separate Stage-3C `ACCEPTED_REPO.zip` from the exact runtime-tested production commit `d88d5c59...`, **not from an unspecified post-documentation `main` HEAD**. The resulting REPO ZIP intentionally predates documentation-only acceptance commits.
- Record Windows-side archive file size / SHA-256 only after actually executing the commands; do not invent the resulting hash.
