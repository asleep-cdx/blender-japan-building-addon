# Build 06-C Acceptance Record

## Acceptance status

- **Build 06-C Stage 1: ACCEPTED**
- **Build 06-C overall: NOT YET ACCEPTED**
- **Build 06-C Stage 2 and later stages: PENDING**

This record accepts only Build 06-C Stage 1, **Crown Foundation and SIMPLE**.

It does **not** accept Build 06-C overall. BEVEL, ROUNDED, Custom POLY/BEZIER Crown Profiles, Custom Crown shading, Profile Thumbnail UI, and all later Build 06-C stages remain outside this acceptance.

## Tested revision and runtime artifact

- Blender 5.2 LTS runtime-tested production revision:
  `70cc8d32633a223dd2554a5d3ae385b6237b86e5`
- Runtime artifact:
  `Japanese_House_Modeler_Build_06_C_Stage1_Candidate_r1.zip`
- Add-on version:
  `(0, 6, 3)`
- Accepted Stage 1 build identification:
  `Build 06-C Stage 1: Crown Foundation and SIMPLE`
- Acceptance-record-only revision:
  this later documentation commit changes only acceptance documentation and does not change the runtime-tested production behavior.

The Blender runtime evidence below was supplied from Blender 5.2 LTS execution against the runtime-tested production revision and artifact above.

Pure Python automation and repository static checks are recorded separately and are not represented as Blender runtime evidence.

---

## Automated and static verification

The accepted Stage 1 production candidate had the following automated and static verification results:

| Check | Result |
|---|---:|
| `python -B -m unittest tests.test_build_06_c_stage1` | **22 passed** |
| `python -B -m unittest tests.test_build_06_b_stage3` | **40 passed** |
| `python -B -m unittest tests.test_build_06_b_stage2b` | **20 passed** |
| `python -B -m unittest tests.test_build_06_b_stage2a` | **51 passed** |
| `python -B -m unittest tests.test_build_06_b_stage1` | **20 passed** |
| `python -B -m unittest tests.test_build_06_a` | **60 passed** |
| `python -B -m unittest tests.test_build_05_b` | **16 passed** |
| `python -B -m unittest discover -s tests` | **319 passed** |
| `python -m compileall -q japanese_house_modeler tests` | **PASS** |
| `git diff --check` | **PASS** |

These results include the Stage 1 static-review corrections for non-finite orientation rejection, selected-Finish vertical-reference diagnostics, and correct regeneration-required state preservation after failed bulk regeneration.

---

## Stage 1 Blender 5.2 LTS runtime acceptance

| # | Test | Result | Runtime evidence |
|---:|---|---|---|
| 1 | Basic Crown SIMPLE creation | **PASS** | CROWN persisted with `vertical_reference=CEILING`, `profile_id=SIMPLE`, `vertical_offset_mm=0`, identity Object scale, and ceiling-reference placement. With CEILING 2500 mm and SIMPLE height 60 mm, world Z bounds were `2.44–2.50 m`. |
| 2 | LEFT / RIGHT physical-side placement | **PASS** | Explicit LEFT and RIGHT Crown creation projected to the requested Wall face side. For a 130 mm Wall and 10 mm SIMPLE projection, the Wall face was at `0.065 m` from centerline and the outer Crown edge reached `0.075 m`. |
| 3 | FORWARD / REVERSE traversal | **PASS** | Crown paths persisted correct traversal direction for both FORWARD and REVERSE cases. LEFT/RIGHT physical-side placement remained correct and no negative Object Scale was introduced. |
| 4 | 90-degree MITER | **PASS** | Two-span L-shaped Crown generated a clean supported Miter with no abnormal gap, overlap, spike, or inversion. |
| 5 | Oblique MITER | **PASS** | A supported oblique two-span Crown generated without gap, overlap, abnormal spike, or management error. |
| 6 | Partial Run | **PASS** | A single-span Crown with persisted boundaries at `500 mm` and `3200 mm` generated only the requested interval. Both free partial boundaries terminated as closed BUTT ends. |
| 7 | Partial Run editable Mesh | **PASS** | Partial Crown converted to unmanaged editable Mesh with identity scale, `BOUNDARY 0`, `NONMANIFOLD 0`, positive signed volume, closed BUTT ends, and retained assigned material. |
| 8 | Basic Manual Exclusion | **PASS** | Manual Exclusion `1200–1800 mm` generated the expected gap and two visible ranges while retaining the canonical FinishSpan and normal managed state. |
| 9 | Manual Exclusion editable Mesh | **PASS** | Exclusion geometry converted to one editable Mesh with closed solids, `BOUNDARY 0`, `NONMANIFOLD 0`, positive signed volume, closed Exclusion-created BUTT ends, and material retention. |
| 10 | Full-exclusion valid-empty | **PASS** | Full Wall coverage remained a valid managed CROWN with one Span and one Exclusion, zero generated visible geometry, and `diagnose_finish() -> ()`. Editable Mesh conversion was explicitly rejected because no generated Finish geometry existed, while the Finish remained managed. |
| 11 | Valid-empty reference update / save / reopen / restoration | **PASS** | While fully excluded, CEILING changed to 2700 mm and bulk regeneration succeeded. Save/close/reopen retained CROWN identity, managed state, Exclusion, and reference. Disabling the Exclusion restored geometry at world Z `2.64–2.70 m`; stale state ended `False`. |
| 12 | Signed vertical offset | **PASS** | With CEILING 2700 mm and `vertical_offset_mm=-20`, explicit regeneration produced world Z bounds `2.62–2.68 m`, confirming that offset sign remains world-Z based for Crown. |
| 13 | SIMPLE dimension edit + Undo / Redo | **PASS** | SIMPLE `60×10 mm` changed to `80×20 mm`; Undo restored `60×10`, Redo restored `80×20`. With offset `-20 mm`, regenerated world Z bounds were `2.60–2.68 m`. Managed diagnostics remained normal. |
| 14 | Unsafe profile edit transaction rollback | **PASS** | An intentionally unsafe `10000 mm` projection on a two-span Miter Crown was rejected with the short-Miter safety error. Canonical dimensions remained `60×10`, the previous valid geometry remained visible, and `diagnose_finish() -> ()`. |
| 15 | Wall split dependency remap | **PASS** | A one-Span Crown attached to a Wall followed T-junction auto-splitting and remapped to two FinishSpans referencing the original and new persistent Wall IDs. Geometry remained visually continuous. Undo and Redo restored the correct one-Wall / two-Wall states. |
| 16 | Baseboard + Crown coexistence on the same Wall | **PASS** | Baseboard and Crown initially referenced the same Wall ID. T-junction splitting remapped both Finish types to the same two Wall objects and IDs with no gap or management error. Mixed-scene Undo / Redo restored both correctly. |
| 17 | Atomic bulk regeneration failure | **PASS** | With coexisting Baseboard and Crown, Crown was intentionally placed into unsupported Stage 1 `profile_id=ROUNDED`, then Scene references changed to FLOOR 100 mm / CEILING 2700 mm. Bulk regeneration failed as expected. Baseboard remained at Z `0.00–0.06 m`, Crown remained at Z `2.44–2.50 m`, and stale remained `True`; no partial update occurred. |
| 18 | Atomic bulk regeneration success | **PASS** | After restoring Crown `profile_id=SIMPLE`, bulk regeneration succeeded atomically. Baseboard moved to Z `0.10–0.16 m`, Crown moved to Z `2.64–2.70 m`, and stale became `False`. |
| 19 | Junction-aware Exclusion BUTT termination | **PASS** | On an L-shaped REVERSE path, an Exclusion reaching the canonical junction removed the Miter across the excluded junction. Surviving geometry ended independently with closed BUTT behavior and no spike, overlap, or penetration. `diagnose_finish() -> ()`. |
| 20 | Material save / reopen / regeneration | **PASS** | `Crown_Save_Test` survived save, close, reopen, preserved two Spans and one Exclusion, and remained assigned after explicit path regeneration. |
| 21 | Multiple Manual Exclusions | **PASS** | Two enabled Manual Exclusions on the two-span Crown produced three visible ranges. `Crown_Save_Test` remained assigned and `diagnose_finish() -> ()`. |
| 22 | Scene reference edit and bulk regeneration use separate Undo units | **PASS** | CEILING changed from 2500 to 2700 mm and was regenerated. First Undo reverted regeneration only while retaining CEILING 2700 and restoring the stale warning. Second Undo reverted the reference input to 2500. Two Redos restored CEILING 2700, regenerated geometry, `stale=False`, and Z `2.64–2.70 m`. |
| 23 | Existing Baseboard regression smoke | **PASS** | Existing Baseboard remained able to use ROUNDED under Build 06-C Stage 1. It persisted `BASEBOARD / FLOOR / ROUNDED`, Object scale `(1,1,1)`, Z `0.00–0.06 m`, and `diagnose_finish() -> ()`. |
| 24 | Material retention through Crown dimension and boundary edits | **PASS** | `Crown_Final_Test` survived SIMPLE dimension edit to `75×15 mm` and start/end boundary editing. |
| 25 | Managed Crown identity Transform | **PASS** | Managed Crown retained location `(0,0,0)`, rotation `(0,0,0)`, and scale `(1,1,1)`. No negative Object Scale or transform-based vertical reflection was used. |
| 26 | Editable Mesh outward normals and topology | **PASS** | Final SIMPLE Crown editable Mesh had `BAD 0` outward-normal faces, positive signed volume `0.002907161375101719`, `BOUNDARY 0`, and `NONMANIFOLD 0`. |

---

## Stage 1 completion gate

The Blender 5.2 LTS evidence above satisfies the Build 06-C Stage 1 acceptance requirements for the implemented scope:

- Crown is a first-class `finish_type=CROWN`.
- Crown Stage 1 is explicitly SIMPLE-only.
- Default Crown vertical reference is CEILING.
- Crown Profile placement is downward from the resolved reference without changing stored canonical Profile coordinates.
- Profile orientation is centralized and uses explicit horizontal / vertical orientation rather than negative Object Scale.
- LEFT / RIGHT and FORWARD / REVERSE combinations remain physically correct.
- Supported 90-degree and oblique Miter geometry remains valid.
- Free, partial, and Exclusion-created boundaries terminate as closed BUTT ends where required.
- Manual Exclusion, multiple Exclusions, full-exclusion valid-empty, and junction-aware Exclusion behavior pass.
- Partial Run behavior passes.
- Wall split remapping preserves persistent Wall attachment for Crown.
- Baseboard and Crown can coexist on the same Wall and remap together after split.
- Material assignment survives the tested Crown edit, regeneration, save/reopen, and Mesh-conversion paths.
- Managed Crown retains identity Object transforms.
- Editable Mesh output is closed, manifold, positive-volume, and outward-facing.
- Scene floor/ceiling reference changes mark Finish geometry stale.
- Bulk regeneration is atomic across mixed Baseboard/Crown scenes.
- Failed bulk regeneration preserves previous generated geometry and preserves the pre-operation stale state.
- Successful bulk regeneration clears the stale flag.
- Scene reference edits and bulk regeneration are separate Undo units.
- Existing Baseboard ROUNDED behavior remains available and was not restricted by Crown Stage 1 SIMPLE-only validation.

---

## Explicit non-acceptance / deferred scope

This Stage 1 acceptance does **not** accept or authorize the following as completed Build 06-C work:

- Crown BEVEL
- Crown ROUNDED
- Crown Custom POLY
- Crown Custom BEZIER
- Custom Crown Profile-aware shading
- Profile Thumbnail UI
- later Build 06-C stages
- Build 06-C overall

Those items remain subject to the governing `BUILD_06_C_SPECIFICATION.md` and their later implementation / review / Blender runtime acceptance.

---

## Acceptance conclusion

**Build 06-C Stage 1 — Crown Foundation and SIMPLE: ACCEPTED**

**Build 06-C overall: NOT YET ACCEPTED**

The accepted production behavior is the repository state at:

`70cc8d32633a223dd2554a5d3ae385b6237b86e5`

Any later acceptance-record-only commit must not be treated as a new production-runtime revision unless production code changes are introduced.
