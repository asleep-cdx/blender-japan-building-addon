# Build 06-A Formal Acceptance Record

Build identification: **Build 06-A Stage 3 Candidate**. This record deliberately
separates pure automated evidence from Blender 5.2 LTS runtime acceptance.

**Stage 3: ACCEPTED**

**Build 06-A: ACCEPTED**

Stage 3 runtime tests 1–22 were completed in Blender 5.2 LTS against the candidate
tree, the 166-test automated suite passed, and the full Build 05-B regression passed.

| test name | stage | automated / Blender runtime | status | commit tested | notes |
|---|---:|---|---|---|---|
| Stage 1 pure transaction and remap suite | 1 | automated | PASS | e73c9f542667c1a0ac03c5a0b3083c36b66390be | Recorded in `BUILD_06_A_STAGE1_TEST_RESULTS.md`. |
| Stage 1 targeted Blender scenarios | 1 | Blender runtime | PASS | e73c9f542667c1a0ac03c5a0b3083c36b66390be | Accepted facts imported from the Stage 1 record; no Stage 3 retest claim. |
| Stage 2 orientation/miter/blocker pure suite | 2 | automated | PASS | 856c5d62b83d7af466525f3de4bc03d852f475ca | Recorded in `BUILD_06_A_STAGE2_TEST_RESULTS.md`. |
| Stage 2 targeted Blender geometry scenarios | 2 | Blender runtime | PASS | 856c5d62b83d7af466525f3de4bc03d852f475ca | Accepted facts imported from the Stage 2 record. The endpoint/corner visual-quality follow-up from Stage 2 was resolved by Stage 3 runtime test 21. |
| CPython unit suite (166 tests), including BREAK/closed rejection | 3 | automated | PASS | Stage 3 candidate tree | `python -m unittest discover -s tests -v`; this is not Blender runtime evidence. |
| Verification Profile metadata/type/orientation decision | 3 | automated | PASS | Stage 3 candidate tree | Pure metadata/type/orientation policy. |
| Managed verification Profile identity and same-name unmanaged Profile isolation | 3 | Blender runtime | PASS | 3dcd1cfffb1acf49c1e53c93ba72e62917518ed2 | Managed Profile reuse and unrelated same-name Curve isolation verified. |
| Finish ID normalization and diagnosis policy | 3 | automated | PASS | Stage 3 candidate tree | Empty, whitespace, normalized duplicate, and unique IDs covered. |
| Duplicate and normalized Finish ID diagnosis | 3 | Blender runtime | PASS | 3dcd1cfffb1acf49c1e53c93ba72e62917518ed2 | Empty/normalized duplicate identity is diagnosed without heuristic reassignment. |
| Unsupported `join_policy=BREAK` and `closed=True` rejection | 3 | Blender runtime | PASS | 3dcd1cfffb1acf49c1e53c93ba72e62917518ed2 | Persisted unsupported states reject regeneration/conversion without rewriting canonical values. |
| Exclusion interval and referenced-Wall diagnosis | 3 | Blender runtime | PASS | 3dcd1cfffb1acf49c1e53c93ba72e62917518ed2 | Invalid interval, pointer, expected ID, ownership, and managed Wall state verified. |
| FLOOR / CEILING / ABSOLUTE reference regeneration | 3 | Blender runtime | PASS | 3dcd1cfffb1acf49c1e53c93ba72e62917518ed2 | Reference-relative geometry updates and ABSOLUTE stability verified. |
| Bulk regeneration atomic rollback | 3 | Blender runtime | PASS | 3dcd1cfffb1acf49c1e53c93ba72e62917518ed2 | Injected prepare failure leaves all managed Finish geometry unchanged. |
| Editable Mesh conversion and collection/source isolation | 3 | Blender runtime | PASS | 3dcd1cfffb1acf49c1e53c93ba72e62917518ed2 | Replacement MESH is editable/selected, preserves collection placement, does not follow Wall edits, and leaves no temporary Object. |
| Mesh conversion Undo / Redo | 3 | Blender runtime | PASS | 3dcd1cfffb1acf49c1e53c93ba72e62917518ed2 | Replacement-object conversion is restored/reapplied as one logical operation. |
| Injected Mesh preparation failure rollback | 3 | Blender runtime | PASS | 3dcd1cfffb1acf49c1e53c93ba72e62917518ed2 | Original managed Finish/canonical state survives and disposable resources are cleaned. |
| Post-commit old Curve cleanup failure | 3 | Blender runtime | PASS | 3dcd1cfffb1acf49c1e53c93ba72e62917518ed2 | Cleanup failure reports WARNING, returns FINISHED, and preserves the committed Mesh. |
| Finish regenerate / repair Undo / Redo | 3 | Blender runtime | PASS | 3dcd1cfffb1acf49c1e53c93ba72e62917518ed2 | Registered operators, poll behavior, execution, and logical Undo/Redo verified. |
| Canonical state and Profile metadata save / close / reopen | 3 | Blender runtime | PASS | 3dcd1cfffb1acf49c1e53c93ba72e62917518ed2 | Finish pointers/IDs/boundaries/style and managed Profile metadata persist without name-based rebind. |
| Wall split, partial Finish remap, and endpoint move/automatic split | 3 | Blender runtime | PASS | 3dcd1cfffb1acf49c1e53c93ba72e62917518ed2 | Full/partial intervals and endpoint-driven host split remap verified. |
| Wall deletion and FinishRun partition | 3 | Blender runtime | PASS | 3dcd1cfffb1acf49c1e53c93ba72e62917518ed2 | Deleted middle Wall partitions runs without bridging surviving spans. |
| Wall rename, Shift+D conflict diagnosis, and duplicate repair | 3 | Blender runtime | PASS | 3dcd1cfffb1acf49c1e53c93ba72e62917518ed2 | Persistent identity is name-independent and duplicate ownership remains explicit. |
| Modal ESC / RMB / Backspace | 3 | Blender runtime | PASS | 3dcd1cfffb1acf49c1e53c93ba72e62917518ed2 | Cancellation and pending-path removal behavior verified. |
| Manual Curve edit to canonical regeneration | 3 | Blender runtime | PASS | 3dcd1cfffb1acf49c1e53c93ba72e62917518ed2 | Derived manual edits are replaced from persistent canonical Finish state. |
| Injected Finish regeneration failure rollback | 3 | Blender runtime | PASS | 3dcd1cfffb1acf49c1e53c93ba72e62917518ed2 | Old Curve geometry and canonical state remain intact. |
| Blocked-path final rejection | 3 | Blender runtime | PASS | 3dcd1cfffb1acf49c1e53c93ba72e62917518ed2 | T-blocker path was safely rejected at final confirmation and no invalid Finish was created. Invalid-state preview indication remains a non-blocking follow-up. |
| Finish endpoint / corner final visual quality | 3 | Blender runtime | PASS | 3dcd1cfffb1acf49c1e53c93ba72e62917518ed2 | Stage 3 runtime test 21 verified the single-span endpoint and corner geometry as the final Build 06-A visual-quality check. |
| Build identification | 3 | Blender runtime | PASS | 3dcd1cfffb1acf49c1e53c93ba72e62917518ed2 | Version `(0, 6, 3)` and Build 06-A Stage 3 Candidate description verified. |
| Full Build 05-B Wall regression | 3 | Blender runtime | PASS | 3dcd1cfffb1acf49c1e53c93ba72e62917518ed2 | Basic generation/dimensions, Continuation, 90°/oblique Corner, T/automatic split, Cross, repair, deletion, and Undo/Redo passed. |
| Stage 3 runtime tests 1–22 | 3 | Blender runtime | PASS | 3dcd1cfffb1acf49c1e53c93ba72e62917518ed2 | Formal runtime execution reported complete; automated evidence was not substituted for runtime results. |
| Build 06-A formal acceptance gate | 3 | automated + Blender runtime | PASS | 3dcd1cfffb1acf49c1e53c93ba72e62917518ed2 | 166 automated tests, Stage 3 Blender runtime tests 1–22, and full Build 05-B regression passed. |

## Post-Build-06-A follow-up

These are usability/appearance follow-ups and are not Build 06-A failures:

- Generated Finish default Flat Shade.
- Finish path preview visibility / line thickness improvement.
- Invalid-path preview indication (for example, T-blocker paths should use a clear warning color instead of normal cyan/blue).
