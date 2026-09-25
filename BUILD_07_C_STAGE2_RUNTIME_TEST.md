# Build 07-C Stage 2 — Blender 5.2 LTS Runtime Test

Status: **MANUAL RUNTIME PROCEDURE — NOT AN ACCEPTANCE RECORD**

Run one test at a time. Record Console output and the requested screenshots,
then mark PASS/FAIL before continuing. For Undo/Redo use exactly **JHM UI
operation → Ctrl+Z → Ctrl+Shift+Z → Console inspection**; never open the Console
between Undo and Redo. Stage 2 remains unaccepted until this procedure passes.

## Common Console evidence

With the managed Stair active as `o`, use Blender's Console to record canonical
fields, object transform, state, and actual (not hard-coded) mesh counts:

```python
import bpy, math
from japanese_house_modeler.stair_operators import stair_issues
o=bpy.context.active_object; s=o.jhm_stair; vs=[tuple(v.co) for v in o.data.vertices]
print(s.underside_mode,s.side_board_mode,s.stair_schema_version,stair_issues(o,bpy.context.scene))
print("finite",all(math.isfinite(c) for v in vs for c in v),"minZ",min(v[2] for v in vs),"verts/faces",len(vs),len(o.data.polygons))
print("transform",tuple(o.location),tuple(o.rotation_euler),tuple(o.scale))
```

For a representative SLOPED_CLOSED Stair, duplicate it to a disposable object,
separate/select only its UNDERBODY fragment if necessary, and in Edit Mode run:

```python
import bpy, bmesh
o=bpy.context.active_object; bm=bmesh.from_edit_mesh(o.data)
zero=[f.index for f in bm.faces if f.calc_area() <= 1e-12]
boundary=[e.index for e in bm.edges if len(e.link_faces)==1]
nonmanifold=[e.index for e in bm.edges if len(e.link_faces)!=2]
print("zero",zero,"boundary",boundary,"nonmanifold",nonmanifold,"V/F",len(bm.verts),len(bm.faces))
```

Also project vertices onto the canonical uphill axis (resolved from Path and
ascent direction) and record `max uphill X`; expect `<= L+r`. Record `min Z >= B`.

## Tests

0. **Candidate identity.** Record commit/tree/ZIP SHA256, Blender version 5.2
   LTS, add-on version `(0, 7, 2)`, and the unchanged Build 07-C description.
1. **Default regression.** Create a Stair; expect STEPPED_CLOSED + STEPPED,
   overhang 0, 620 vertices / 732 faces, and accepted Stage-1 appearance.
2. **SLOPED_CLOSED, boards OFF/OFF.** Side orthographic screenshot must show
   the `Z=B` lower flat, one straight soffit, vertical upper closure, no cavity,
   exposed backs, floor-filled mass, spike, or giant triangle. Record the common
   evidence and isolated-body topology evidence above. Compare against candidate
   r1: the corrected main soffit must be parallel to the canonical rise/going
   pitch and visibly less steep; upper-step projection must remain visually
   consistent instead of progressively diverging toward the top.
3. **Board enable states.** Test BOTH, LEFT, RIGHT, and OFF/OFF. The body remains
   visually CLOSED and NORMAL in every state.
4. **STEPPED_CLOSED + SLOPED board.** Confirm a straight (not sawtooth) visible
   upper edge beginning above the traditional vertical front closure, a stepped
   bottom edge, and first-step lower end. At the upper termination, the main
   slope must end visibly above `H`, the short horizontal cap must remain above
   `H`, and an explicit vertical rear closure must drop to `H`. Confirm there is
   no notch, giant triangle, spike, or diagonal rear plate.
5. **SLOPED_CLOSED + STEPPED board.** Confirm the board upper edge retains the
   accepted stepped silhouette while its entire lower edge follows the corrected
   sloped body underside. Confirm there is no stepped lower edge or interior gap.
6. **SLOPED_CLOSED + SLOPED board.** Confirm both new silhouettes, role
   separation, clean ends, and NORMAL diagnosis. Its upper edge is one clean
   slope after the front vertical closure, while its lower edge follows the same
   corrected sloped family as the body. Confirm the same visible rise above the
   top landing, horizontal cap above `H`, and vertical rear drop to `H` as Test 4.
   Tests 1/4/5/6 cover all four combinations
   as top/bottom pairs: stepped/stepped, sloped/stepped, stepped/sloped, and
   sloped/sloped.
7. **FORWARD / REVERSE.** Use the UI Reverse operator and mandatory Undo/Redo.
   Lower/upper ends move to their physical elevation roles; LEFT/RIGHT remains
   uphill-relative and neither shape breaks.
8. **Oblique Path.** Edit to an oblique two-point Path. Record resolved axes,
   bounds, visual alignment, NORMAL state, and identity Object transform.
9. **Nonzero base_z.** Set a clearly nonzero B. Confirm lower flat equals B,
   every body/board vertex is at or above B, and nothing is fixed to world Z=0.
10. **Stair-body thickness.** Change 150→120 mm through the UI and mandatory
    Undo/Redo. Confirm the analytical sloped envelope moves while Path,
    floor-to-floor, riser count, tread/riser sizes, width, board thickness/reveal,
    ID, Materials, and transform remain identical.
11. **Underside shell thickness.** Change only shell thickness. Confirm physical
    storage/regeneration changes as intended but the P0/P1/P2 visible reference
    line does not move.
12. **Existing 07-B schema-2 file.** Open and ordinarily Regenerate. Expect
    schema 2, STEPPED geometry, Materials/Path/ID unchanged, and 620/732; no
    migration or sloped activation.
13. **BASIC smoke.** On accepted schema-1 BASIC, ordinarily Regenerate and
    record 248/186, unchanged BASIC mode/schema, geometry, and Materials.
14. **Material preservation.** Assign visibly distinct Base/overrides. Confirm
    SLOPED_CLOSED faces use UNDERSIDE and SLOPED boards use SIDE_BOARD, including
    fallback, true UNASSIGNED, and identity-deduplicated slot cases.

Do not test or accept production nosing, BEVEL, ROUND, multi-point Paths,
landings, winders, open stairs, supports, handrails, or attachments here. Full
Finalize/Delete/duplicate-ID/rollback lifecycle acceptance remains Stage 4.
