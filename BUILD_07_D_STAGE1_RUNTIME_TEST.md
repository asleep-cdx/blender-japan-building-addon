# Build 07-D Stage 1 — Blender 5.2 LTS Runtime Test

> Candidate runtime acceptance checklist. This is not an Acceptance Record.
> Console evidence is authoritative except where the checklist explicitly asks
> for a visual shape judgement.

## Setup

Install/enable the add-on in Blender 5.2 LTS, open a new file, show the
**日本住宅** sidebar, and keep the System Console available. Use the default
2800 mm floor height, 16 risers, 900 mm width, 30 mm tread thickness, and
12 mm riser thickness unless a test says otherwise.

## Test 0 — Candidate identity and accepted Straight regression

1. In the Python Console print `bpy.context.preferences.addons` as needed and
   inspect `japanese_house_modeler.bl_info`.
2. Confirm version `(0, 7, 3)`, Blender `(5, 2, 0)`, and description
   `Build 07-D: Multi-point Path + L/U + Landing`.
3. Select **Straight**, create a two-click stair, then exercise Regenerate,
   Reverse, residential settings, nosing/top arrival, Final Riser,
   STEPPED_CLOSED and SLOPED_CLOSED, both Side Board modes, and materials.
4. In Console confirm two Path points and schema remains `3`; reopening an
   existing schema 1/2/3 file must not add point IDs or schema-4 state.

Expected: accepted 07-C Straight appearance, semantics, one managed Mesh,
and lifecycle remain unchanged.

## Test 1 — Three-click L creation and canonical identity

1. Select **L**, then click P0, P1, and P2 as a clear 90-degree L.
2. In Console inspect the active object:

```python
s = bpy.context.active_object.jhm_stair
print(len(s.path_points), s.stair_schema_version, s.turn_mode)
print([(p.point_id, tuple(p.xy)) for p in s.path_points])
print(bpy.context.active_object.type, tuple(bpy.context.active_object.location),
      tuple(bpy.context.active_object.rotation_euler), tuple(bpy.context.active_object.scale))
```

Expected: three ordered points, three non-empty unique IDs, schema `4`, turn
mode `LANDING`, one managed `MESH`, and identity Object transform. Visually it
is recognisably L-shaped.

## Test 2 — AUTO allocation and height invariants

Run:

```python
from japanese_house_modeler.stair_multiflight import resolve_multiflight_layout
s = bpy.context.active_object.jhm_stair
r = resolve_multiflight_layout(tuple(tuple(p.xy) for p in s.path_points),
    s.ascent_direction, s.base_z_mm, s.floor_to_floor_mm, s.riser_count,
    s.stair_width_mm, s.tread_thickness_mm, s.riser_thickness_mm,
    point_ids=tuple(p.point_id for p in s.path_points),
    allocation=tuple(map(int, s.auto_riser_allocation.split(','))))
print(r.allocation, sum(r.allocation), r.actual_riser,
      r.landing.top_z, r.upper_arrival_z,
      r.base_z + s.floor_to_floor_mm / 1000.0)
```

Expected: each Flight has at least two risers; the total equals the overall
count; both Flights share `actual_riser`; Landing Z follows the first traversed
Flight's cumulative risers; upper arrival exactly matches base plus floor height.
Reverse and repeat: canonical point/ID order stays unchanged while traversal and
Landing elevation follow the reversed ascent.

## Test 3 — Visual L review

Review only these visual facts: Flight 1 treads/risers, horizontal nominal
width-by-width Landing, Flight 2 treads/risers, final upper arrival, and sensible
first-pass residential proportions. Orbit closely around both joins and confirm
there is no obvious gap, spike, or unintended gross overlap. Confirm the whole
stair remains one object. Geometry judgement is the only visual evidence in
this checklist; use Console for all canonical/numeric claims.

## Test 4 — Save, full exit, and reopen

Save the `.blend`, fully exit Blender, reopen Blender 5.2 LTS, and load it.
Print the Test 1 and Test 2 evidence again, then Regenerate once.

Expected: Path coordinates/order, all point IDs, schema 4, AUTO allocation,
Landing/Flight geometry, material assignment, and the single managed object are
retained exactly. No schema 1/2/3 object is silently upgraded.

## Test 5 — Invalid rollback and Straight isolation

1. Keep a valid Straight stair and record its object pointer/name, Stair ID,
   Mesh pointer/name, materials, transform, schema, and vertex/face counts.
2. Start L creation with a duplicate/too-short point, a non-90-degree turn, or
   a segment shorter than the Landing cutback permits.
3. Confirm the warning/cancellation, then print scene managed stairs and the
   recorded Straight evidence.

Expected: no partial object, Mesh, canonical state, UUID, material mutation, or
schema-only upgrade is left by the invalid candidate; the existing Straight is
unchanged.

## Intentionally deferred after Stage 1

Stage 1 does **not** claim production completion for START/TURN/END relocation,
Shift 15-degree constraint, alignment guides, MANUAL distribution or its UI,
full numeric multi-point editing, complete closed-underbody/Side Board joins at
the turn, full nosing/BEVEL/ROUND turn integration, U/custom paths, or winders.
The L candidate intentionally provides tread/riser Flights and a TREAD-role
Landing only; do not interpret absent multi-flight finish joins as implemented.
Existing two-point Straight finish behavior remains the accepted 07-C behavior.
