# Build 07-A Acceptance Record

## Acceptance status

- **Build 07-A Stage 1 — Canonical Stair + 2-point creation: ACCEPTED**
- **Build 07-A Stage 2 — Layout calculation + basic geometry: NOT STARTED**
- **Build 07-A overall: NOT YET ACCEPTED**

Stage 1 acceptance does **not** mean that Build 07-A overall is accepted. Visible
Tread and Riser geometry remains Stage 2 work and is not part of this acceptance.

## Runtime-tested production revision and artifact

- Blender 5.2 LTS runtime-tested production revision:
  `b6c82e80906a9404288c759bcc0650ba07d3526e`
- Runtime-tested Git tree:
  `471027e9071e78d94ef872b65f780d998a37e291`
- Runtime Candidate:
  `Japanese_House_Modeler_Build_07_A_Stage1_Candidate_r1.zip`
- Blender runtime:
  `Blender 5.2 LTS`
- Add-on version:
  `(0, 7, 0)`
- Add-on description:
  `Build 07-A: Stair Core + Top-view 2-point Straight Stair`

This Acceptance Record update changes documentation only. Its commit is not a
new runtime-tested production revision. The accepted Stage 1 production behavior
remains the revision and tree identified above.

## Automated evidence

The final production tree had the following automated and static results:

| Check | Result |
|---|---:|
| `python -B -m unittest tests.test_build_07_a_stage1` | **22 tests PASS** |
| `python -B -m unittest discover -s tests` | **385 tests PASS** |
| `python -m compileall -q japanese_house_modeler tests` | **PASS** |
| `git diff --check` | **PASS** |
| Working tree | **clean** |

These checks apply to production tree
`471027e9071e78d94ef872b65f780d998a37e291`. Automated and static results are
recorded separately from the Blender runtime evidence below.

## Stage 1 Blender 5.2 LTS runtime acceptance

| Test | Runtime gate | Result | Evidence |
|---:|---|---|---|
| 0 | Add-on version / description | **PASS** | Version `(0, 7, 0)` and description `Build 07-A: Stair Core + Top-view 2-point Straight Stair` were displayed. |
| 1 | New Stair defaults + UI | **PASS** | Defaults were `0 / 2800 / 16 / 900 / 30 / 12 / FORWARD`. |
| 2 | FORWARD 2-point creation | **PASS** | Preview showed START / END and uphill arrow START → END. Exactly one Managed Stair Mesh Object was created with `is_stair=True`, two Path points, a persistent UUID, identity Transform, zero vertices, and active/selected state. |
| 3 | REVERSE creation | **PASS** | Canonical Path order remained P0 → P1; `ascent_direction=REVERSE`; resolved lower / upper was P1 / P0; preview arrow pointed END → START; Transform remained identity. |
| 4 | ESC cancel after START | **PASS** | Managed Stair count remained `2 → 2`; JHM Stair Mesh datablock count remained `2 → 2`. |
| 5 | Right Mouse cancel after START | **PASS** | Managed Stair count remained `2 → 2`; JHM Stair Mesh datablock count remained `2 → 2`. |
| 6 | UUID uniqueness | **PASS** | Two Managed Stairs had two unique `stair_id` values. |
| 7 | `base_z` / Path separation | **PASS** | `base_z_mm=1200`; Path retained XY canonical data only; Object Transform remained identity; vertex count was zero. |
| 8 | Zero-length Path rejection | **PASS** | Warning `Stair Pathが短すぎます。` was shown; Object and Mesh counts were unchanged. |
| 9 | Oblique 3D View creation | **PASS** | Two-point creation and preview worked from an oblique view at base Z 1200; two Path points and identity Transform were retained. |
| 10 | Defaults copied to canonical data | **PASS** | Created Stair retained base Z 500, floor-to-floor 3000, riser count 17, width 1000, tread thickness 35, riser thickness 15, REVERSE ascent, two Path points, and identity Transform. |
| 11 | Defaults snapshot during active modal | **RUNTIME N/A** | A Sidebar click is captured as the second Path click while the modal is active, so changing Sidebar defaults during that modal is not a meaningful normal runtime operation. Coverage is provided by code review and the automated Stage 1 structural test. This is not a failure. |
| 12 | Rename preserves persistent Stair ID | **PASS** | Renaming `JHM Stair.004` to `Test Stair Rename` did not change `stair_id`. |
| 13 | Save / Blender exit / reopen | **PASS** | Object name, `stair_id`, P0/P1, ascent direction, base Z, floor-to-floor, riser count, width, both thicknesses, and identity Transform were preserved. |
| 14 | Create Undo / Redo | **PASS** | Ctrl+Z removed the new Stair; Ctrl+Shift+Z restored the same Stair as a managed MESH with UUID, two Path points, identity Transform, and zero vertices. |
| 15 | Invalid view / drawing-plane rejection | **PASS** | Warning `基準平面は現在のビューrayの後方にあります。` was shown; Object and Mesh counts remained `6 / 6 → 6 / 6`. |
| 16 | `riser_count` runtime minimum | **PASS** | Assigning 1 was clamped by RNA to 2; restoring 16 produced 16. |
| 17 | Add-on disable / re-enable lifecycle | **PASS** | Disable and enable completed without Python errors; the panel and New Stair UI returned. Console result was `((0, 7, 0), True, True)` for version and the Scene/Object Stair properties. |

## Stage 1 completion gate

The automated evidence and Blender 5.2 LTS runtime evidence accept the Stage 1
foundation for:

- canonical Stair properties and exactly two ordered world-XY Path points;
- separation of Path draw order from FORWARD / REVERSE ascent direction;
- resolved lower / upper roles and local Stair axes;
- Top-view and oblique-view two-point creation on the `base_z` plane;
- transient modal preview with START / END and ascent-direction arrow;
- cancel and invalid-input safety without persistent Object or Mesh mutation;
- one Managed Stair represented by one empty Mesh Object;
- persistent, rename-independent, unique Stair UUIDs;
- identity Object Transform and separation of plan Path from vertical reference;
- new-Stair defaults and deterministic copying into canonical Stair data;
- active selection after creation, Undo / Redo, save / reopen, and add-on
  disable / re-enable lifecycle baseline.

## Deferred scope and overall non-acceptance

Stage 1 intentionally does not accept or claim completion of:

- visible Tread geometry;
- Riser-board geometry;
- layout calculation and assembled Stair geometry;
- stepped or sloped underside and Side Boards;
- dimension or Path editing;
- ascent reversal, regeneration, or repair operators;
- Editable Mesh finalization;
- L / U stairs, Landings, or Winders;
- material-part assignment or Floor connection behavior;
- Stage 2 or any later Build 07-A stage.

Visible Tread / Riser geometry remains Stage 2. Stage 2 is **NOT STARTED**, and
Build 07-A overall is **NOT YET ACCEPTED**.

## Acceptance conclusion

**Build 07-A Stage 1 — Canonical Stair + 2-point creation: ACCEPTED**

**Build 07-A Stage 2 — Layout calculation + basic geometry: NOT STARTED**

**Build 07-A overall: NOT YET ACCEPTED**

The runtime-tested Stage 1 production revision remains:

`b6c82e80906a9404288c759bcc0650ba07d3526e`

with Git tree:

`471027e9071e78d94ef872b65f780d998a37e291`

Any later Acceptance Record-only commit changes documentation only and must not
be treated as a new runtime-tested production revision.
