# Build 06-C Acceptance Record

## Acceptance status

- **Build 06-C Stage 1: ACCEPTED**
- **Build 06-C Stage 2: ACCEPTED**
- **Build 06-C Stage 3: PENDING**
- **Build 06-C overall: NOT YET ACCEPTED**

This record accepts Build 06-C Stage 1, **Crown Foundation and SIMPLE**, and Build 06-C Stage 2, **Standard and Custom Crown Profiles**.

It does **not** accept Build 06-C overall. Profile Thumbnail UI and all later Build 06-C stages remain outside this acceptance.

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

## Stage 1 explicit non-acceptance / deferred scope

At the time of Stage 1 acceptance, that acceptance did **not** accept or authorize the following as completed Build 06-C work:

- Crown BEVEL
- Crown ROUNDED
- Crown Custom POLY
- Crown Custom BEZIER
- Custom Crown Profile-aware shading
- Profile Thumbnail UI
- later Build 06-C stages
- Build 06-C overall

Those items remained subject to the governing `BUILD_06_C_SPECIFICATION.md` and later implementation, review, and Blender runtime acceptance. The Stage 2 addendum below now accepts the Stage 2 Profile items after their separate evidence was completed; Profile Thumbnail UI and later stages remain pending.

---

## Acceptance conclusion

**Build 06-C Stage 1 — Crown Foundation and SIMPLE: ACCEPTED**

**Build 06-C overall: NOT YET ACCEPTED**

The accepted production behavior is the repository state at:

`70cc8d32633a223dd2554a5d3ae385b6237b86e5`

Any later acceptance-record-only commit must not be treated as a new production-runtime revision unless production code changes are introduced.

---

# Build 06-C Stage 2 Acceptance Addendum

## Stage 2 tested revision and runtime artifact

- Blender 5.2 LTS runtime-tested production revision:
  `ce89f36ec5332da5078655458b1d4f87b1c043e7`
- Runtime artifact:
  `Japanese_House_Modeler_Build_06_C_Stage2_Candidate_r2.zip`
- Add-on version:
  `(0, 6, 3)`
- Accepted Stage 2 candidate identification:
  `Build 06-C Stage 2: Standard and Custom Crown Profiles`
- Acceptance-record-only revision:
  this later documentation commit changes only acceptance documentation and does not change the runtime-tested production behavior.

The Blender runtime evidence below was supplied from Blender 5.2 LTS execution against the Stage 2 runtime-tested production revision and artifact above. Pure Python automation and repository static checks are recorded separately and are not represented as Blender runtime evidence.

## Stage 2 automated and static verification

| Check | Result |
|---|---:|
| `python -B -m unittest tests.test_build_06_c_stage2` | **14 passed** |
| `python -B -m unittest tests.test_build_06_c_stage1` | **22 passed** |
| `python -B -m unittest tests.test_build_06_b_stage3` | **40 passed** |
| `python -B -m unittest tests.test_build_06_b_stage2b` | **20 passed** |
| `python -B -m unittest tests.test_build_06_b_stage2a` | **51 passed** |
| `python -B -m unittest tests.test_build_06_b_stage1` | **20 passed** |
| `python -B -m unittest tests.test_build_06_a` | **60 passed** |
| `python -B -m unittest tests.test_build_05_b` | **16 passed** |
| `python -B -m unittest discover -s tests` | **333 passed** |
| `python -m compileall -q japanese_house_modeler tests` | **PASS** |
| `git diff --check` | **PASS** |

## Resolved Candidate r1 pre-acceptance defect

Candidate r1, revision `b6112463cd8c2dbb4c2fe84b9b225c295e7951cc`, exposed a runtime defect during Custom BEZIER Crown editable-Mesh conversion. Conversion raised `name 'finish_vertical_sign' is not defined`.

The correction imported the existing authoritative `finish_vertical_sign` function in `finish_operators.py`; it did not duplicate or redefine the orientation rule. The corrected GitHub production revision is `ce89f36ec5332da5078655458b1d4f87b1c043e7`. Candidate r2 passed the affected editable-Mesh conversion runtime gate. The Candidate r1 failure is recorded as a resolved pre-acceptance defect and is not accepted behavior.

## Stage 2 Blender 5.2 LTS runtime acceptance

| Gate | Test | Result | Runtime evidence |
|---:|---|---|---|
| 0 | Build identification | **PASS** | Version `(0, 6, 3)`; description `Build 06-C Stage 2: Standard and Custom Crown Profiles`. |
| 1 | BEVEL Crown basic placement | **PASS** | `CROWN / CEILING`; BEVEL `80×40 mm`, bevel `10 mm`; LEFT / FORWARD; identity Object scale; real Z bounds approximately `2.42–2.50 m`; lower room-facing chamfer orientation correct; `diagnose_finish() -> ()`. |
| 2 | ROUNDED Crown basic placement | **PASS** | ROUNDED `80×40 mm`, radius `10 mm`; real Z bounds approximately `2.42–2.50 m`; lower room-facing rounded corner correct; 80 evaluated vertices; managed state normal. |
| 3 | Custom POLY Crown | **PASS** | Registered asymmetric convex Custom POLY; revision 1 / schema 1; uniform scale 1.0; source Curve deleted successfully; actual stored bounds preserved; expected Crown world-Z bounds approximately `2.426–2.497 m`, matched by actual bounds; `diagnose_finish() -> ()`. |
| 4A | Custom BEZIER Crown | **PASS** | Asymmetric BEZIER snapshot; revision 1 / schema 1; 64 persisted sampled contour points; 16 smooth edges; source Curve deleted; expected and actual world-Z bounds matched; `diagnose_finish() -> ()`. |
| 4B | Custom BEZIER editable Mesh and shading | **PASS** | Candidate r1 exposed the missing `finish_vertical_sign` import and the defect was corrected before Candidate r2. Candidate r2 conversion succeeded: TYPE MESH; `managed=False`; scale `(1,1,1)`; SMOOTH 16; FLAT 172; FACES 188; positive signed volume `0.006284231662448897`; BOUNDARY 0; NONMANIFOLD 0. Curved region visually smooth; planar regions and caps remained flat. |
| 5 | Profile switching and Material preservation | **PASS** | `SIMPLE -> ROUNDED`, `ROUNDED -> Custom BEZIER`, and `Custom BEZIER -> BEVEL`; `Crown_Stage2_Mat` survived all switches; `diagnose_finish() -> ()`. |
| 6 | Custom uniform scale, Run-local independence, Undo / Redo | **PASS** | Crown A changed `1.0 -> 1.5`; Crown B remained 1.0; Undo restored A to 1.0; Redo restored A to 1.5. Final scene: `JHM Finish = 1.5`, `JHM Finish.001 = 1.0`; diagnostics returned `()` for both; UI geometry dimensions reflected scaled height/projection. |
| 7 | Custom BEZIER Manual Exclusion and Material | **PASS** | Custom BEZIER scale 1.5; one Manual Exclusion `1200–1800 mm`; two visible ranges; `Crown_Stage2_Mat` retained; `diagnose_finish() -> ()`. |
| 8 | Custom BEZIER Exclusion editable Mesh | **PASS** | `managed=False`; scale `(1,1,1)`; material retained; SMOOTH 32; FLAT 344; FACES 376; positive signed volume `0.012001805197530217`; BOUNDARY 0; NONMANIFOLD 0; both Exclusion-created ends visibly closed as flat BUTT caps. |
| 9 | ROUNDED Crown Manual Exclusion and editable Mesh | **PASS** | SMOOTH 32; FLAT 80; FACES 112; positive signed volume `0.010706745832923636`; BOUNDARY 0; NONMANIFOLD 0; rounded region remained smooth; Exclusion BUTT caps remained flat and closed. |
| 10 | ROUNDED Crown Partial Run and 90-degree Miter | **PASS** | Two Spans; RIGHT / REVERSE traversal; 500 mm partial boundaries; identity scale; `diagnose_finish() -> ()`; central Miter had no visible gap, overlap, or abnormal spike; ROUNDED shape remained valid. |
| 11 | Save / reopen integration | **PASS** | Before save: ROUNDED Crown with `Crown_SaveReopen_Mat`; Custom BEZIER Crown with one Manual Exclusion and the same Material; Custom source Curve absent. After close/reopen: both managed Crowns remained; ROUNDED and Custom Profile identities persisted; one Custom Exclusion and the project-local snapshot persisted; source remained absent; Material persisted; diagnostics returned `()` for both; explicit regeneration succeeded; Material and visible Custom Exclusion ranges remained. |
| 12 | BEVEL Crown editable Mesh | **PASS** | TYPE MESH; `managed=False`; scale `(1,1,1)`; SMOOTH 0; FLAT 11; FACES 11; positive signed volume `0.012504539868834152`; BOUNDARY 0; NONMANIFOLD 0. |
| 13A | Baseboard ROUNDED regression | **PASS** | TYPE MESH; scale `(1,1,1)`; SMOOTH 16; FLAT 40; FACES 56; positive signed volume `0.012617348537607764`; BOUNDARY 0; NONMANIFOLD 0; accepted upward Baseboard appearance preserved. |
| 13B | Baseboard Custom BEZIER regression | **PASS** | TYPE MESH; scale `(1,1,1)`; SMOOTH 16; FLAT 172; FACES 188; positive signed volume `0.006285942941392453`; BOUNDARY 0; NONMANIFOLD 0; accepted Baseboard Custom smooth/flat behavior preserved. |
| 14 | Transactional Profile-switch rollback | **PASS** | Before: ROUNDED, height 80, projection 40, radius 10, `Crown_SaveReopen_Mat`, two Spans. Unsafe BEVEL projection `10000 mm` was rejected with `Finish区間がProfileの留め加工には短すぎます。` After rejection: all Profile values, Material, and two Spans were retained; old valid geometry remained visible; `diagnose_finish() -> ()`. |
| 15 | BEVEL Crown 90-degree Miter | **PASS** | BEVEL; two Spans; `Crown_SaveReopen_Mat` retained; `diagnose_finish() -> ()`; no visible gap, overlap, spike, or Profile corruption at Miter. |
| 16 | Custom POLY editable Mesh | **PASS** | Custom POLY source Curve deleted; CROWN; Custom Profile revision remained valid; scale 1.0; `diagnose_finish() -> ()`; TYPE MESH; `managed=False`; scale `(1,1,1)`; SMOOTH 0; FLAT 8; FACES 8; NORMAL_BAD 0; MIN_DOT `0.004501332761719823`; positive signed volume `0.0023976032021917337`; BOUNDARY 0; NONMANIFOLD 0. |

## Stage 2 completion gate

The automated/static evidence and Blender 5.2 LTS runtime evidence above satisfy the Build 06-C Stage 2 acceptance requirements:

- BEVEL and ROUNDED Crown placement, Miter behavior, shading, and closed editable-Mesh conversion pass.
- Custom POLY and asymmetric Custom BEZIER Crown retain project-local Profile identity and remain source-independent.
- Custom smooth-edge intent follows the fully oriented contour through Crown vertical reflection.
- Custom uniform scale is Run-local and works with Undo / Redo.
- Actual Custom bounds control Crown placement.
- Profile switching preserves Crown state and Material, and unsafe switches roll back transactionally.
- Manual Exclusion and Partial Run behavior remain valid; Exclusion-created ends are closed flat BUTT caps.
- Save / reopen preserves Custom snapshots, Profile identity, Exclusions, Material, shading, and regeneration.
- Baseboard ROUNDED and Custom BEZIER behavior remain compatible.
- Managed and converted objects retain identity scale; converted Meshes are closed, manifold, and positive-volume.

## Stage 2 acceptance conclusion

**Build 06-C Stage 1 — Crown Foundation and SIMPLE: ACCEPTED**

**Build 06-C Stage 2 — Standard and Custom Crown Profiles: ACCEPTED**

**Build 06-C Stage 3 — Profile Thumbnail UI: PENDING**

**Build 06-C overall: NOT YET ACCEPTED**

The accepted Stage 2 production behavior is the repository state at:

`ce89f36ec5332da5078655458b1d4f87b1c043e7`

This acceptance-record-only update is not a new production-runtime revision. Stage 3 and Build 06-C overall remain unaccepted.
