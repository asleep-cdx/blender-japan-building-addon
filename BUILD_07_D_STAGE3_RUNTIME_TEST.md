# Build 07-D Stage 3 Runtime Test

Use a clean Blender file and the Stage 3 branch package. Do not create a Candidate ZIP. For every Undo/Redo check use **UI operation → Ctrl+Z → Ctrl+Shift+Z → Console**; never open the Console between Undo and Redo.

## Test 0 — identity and regressions
Create one accepted 07-C Straight and one three-point L. Regenerate both and compare the L's sloped underbody, horizontal/hollow landing closure, r14/r16/r17 board terminals, materials, identity transform, and canonical IDs with Stage 2.

## Test 1 — four-click U
Choose **U**, click P0/P1/P2/P3, and verify one managed object, schema 4, four stable unique points, three flights, and two landings. Repeat mirrored and with a 15°/30° first flight. Confirm both turns show perpendicular guidance and the last leg prefers the local direction opposite Flight 1.

## Test 2 — AUTO and elevations
Inspect a 16-riser unequal-run U. Verify three deterministic allocations (each at least two), exact sum 16, floor-to-floor arrival, and landing Z values equal to cumulative preceding physical-flight risers.

## Test 3 — relocation and Undo/Redo
Move P0, P1, P2, and P3 separately using local 90°, parallel, axis, extension, and Shift-15° candidates. For each valid move perform Ctrl+Z then Ctrl+Shift+Z before Console inspection. Confirm one Undo step, stable IDs/materials, and atomic rejection if either neighboring turn becomes oblique or intersecting.

## Test 4 — MANUAL rollback
Switch AUTO→MANUAL, enter all three flight counts, and verify exact persistence. Try a wrong total, a count below two, and a move making the middle flight too short. Each must report ERROR/CANCELLED with no traceback and no mesh, canonical, allocation, material, or transform change. Switch back to AUTO only after validation.

## Test 5 — Residential U geometry
For left/right mirrored U routes inspect both turns in **body-only view** before enabling boards.

* **SLOPED_CLOSED / boards OFF:** inspect Landing 1 and Landing 2 separately from below. Each must have its own low horizontal soffit, closure on only the two exposed perimeter edges, a hollow centre, and no open external cavity, global turn-to-turn slope, wedge, or full solid filler. Follow the middle Flight underside from its Landing 1 start boundary to its Landing 2 terminal boundary and verify that it is one constant-pitch physical body—not two coincident bodies and not a repair box. Toggle boards OFF again after later checks to prove closure does not depend on them.
* **SLOPED_CLOSED Side Board start regression:** enable both boards and inspect every outgoing start—Turn 1 LEFT/RIGHT and Turn 2 LEFT/RIGHT. From each Landing into its outgoing Flight, the Side Board lower edge must continue onto the Turn-corrected underbody slope without exposed triangular UNDERBODY, an open triangle, notch, or lower-edge jump. Verify both the middle Flight start and its Turn 2 terminal end, then the final Flight start. Repeat with a mirrored U and with Reverse; no stale FORWARD profile or opposite-side gap may appear. Run the same check for Side Board **STEPPED** and **SLOPED** modes.
* **Side Boards:** enable one side at a time and then both. At Landing 1 and Landing 2 inspect outer and inner connections independently. Verify the middle Flight's start follows Turn 1 outgoing ownership and its end follows Turn 2 incoming ownership, with one board per physical side. Confirm the local chirality mirrors correctly, corner returns and reveals remain present, and there is no overlap flicker, filler prism, duplicated fascia, sudden side swap, or large gap. Repeat with 20, 40, and 60 mm reveal and representative 8, 12, and 18 mm riser thicknesses.
* **STEPPED_CLOSED:** inspect both incoming→Landing→outgoing transitions from above and below with boards OFF and ON. Verify both are closed, the middle Flight remains single-owner, and there is no exposed riser backside, open boundary, gap, spike, sliver, duplicate transition body, or positive-volume overlap.

## Test 6 — Reverse and materials
Assign all five roles, reverse twice, and verify unchanged plan/IDs/physical allocation/material pointers. Confirm traversal reverses, both landing elevations recompute, and only the final uphill flight owns upper arrival semantics.

## Test 7 — persistence, regeneration, isolation
Save, fully exit Blender, reopen, and verify schema, four points/IDs/order, mode, three allocations, direction, dimensions, Residential state, five material slots, Stair ID, and identity transform. Regenerate repeatedly for deterministic mesh data. Finish with one invalid Turn-2/Flight-3 edit and confirm the entire object remains byte-for-byte unchanged.
