"""Pure Build 07-B Stage 2 stepped-underbody geometry preparation."""

from dataclasses import dataclass

from .stair_geometry import (
    MeshFragment, _box_fragment, assemble_stair_mesh, build_riser_fragments,
    extrude_xz_profile, resolve_stair_layout,
    validate_mesh_fragments, validate_simple_polygon,
)
from .stair_residential import (
    STANDARD_RESIDENTIAL, STEPPED_CLOSED, ResidentialFields,
    residential_fields, validate_mode_data,
    validate_stepped_closure_depth,
    validate_stepped_underbody_thickness,
)


@dataclass(frozen=True)
class SteppedUnderbodyProfile:
    """Validated component-contact and visible paths plus closed XZ body."""

    inner: tuple
    outer: tuple
    polygon: tuple


def _without_consecutive_duplicates(points):
    result = []
    for point in points:
        point = (float(point[0]), float(point[1]))
        if not result or point != result[-1]:
            result.append(point)
    return tuple(result)


def stepped_underbody_inner_profile(layout):
    """Build U_inner analytically from the resolved Stair dimensions."""
    r, g, h, t, base = (layout.riser_thickness, layout.going,
                        layout.actual_riser, layout.tread_thickness,
                        layout.base_z)
    points = [(r, base)]
    for step in range(1, layout.riser_count):
        underside = base + step * h - t
        # A Residential Tread runs under the whole depth of the next Riser.
        # Its rear and that Riser's rear contact face are consequently one
        # clean corner at x=step*g+r, rather than the former g-to-g+r notch.
        points.extend((((step - 1) * g + r, underside),
                       (step * g + r, underside)))
    return _without_consecutive_duplicates(points)


def build_residential_tread_fragments(layout):
    """Build Residential Treads extended uphill through the next Riser."""
    fragments = []
    for ordinal in range(1, layout.independent_tread_count + 1):
        top = layout.base_z + ordinal * layout.actual_riser
        fragments.append(_box_fragment(
            layout, "TREAD", ordinal,
            (ordinal - 1) * layout.going,
            ordinal * layout.going + layout.riser_thickness,
            top - layout.tread_thickness, top))
    return tuple(fragments)


def stepped_underbody_outer_profile(inner, thickness, base_z):
    """Offset an orthogonal U_inner with translated-line intersections."""
    if len(inner) < 2:
        raise ValueError("U_innerには2点以上が必要です。")
    outer = [(inner[0][0] + thickness, base_z)]
    for index in range(1, len(inner) - 1):
        before, point, after = inner[index - 1:index + 2]
        incoming_vertical = before[0] == point[0]
        outgoing_vertical = point[0] == after[0]
        if incoming_vertical == outgoing_vertical:
            outer.append((point[0] + thickness, point[1]) if incoming_vertical
                         else (point[0], point[1] - thickness))
        else:
            vertical_x = (point[0] + thickness)
            horizontal_z = (point[1] - thickness)
            outer.append((vertical_x, horizontal_z))
    outer.append((inner[-1][0], inner[-1][1] - thickness))
    return _without_consecutive_duplicates(outer)


def stepped_closure_visible_profile(layout, closure_depth):
    """Resolve the corrected, thickness-independent visible stepped soffit.

    The first-step bottom is deliberately flattened at ``base_z`` through the
    first translated corner.  Subsequent segments follow the translated ideal
    walking-step reference and the final segment is clipped at ``L + r``.
    """
    g, h, base = layout.going, layout.actual_riser, layout.base_z
    upper_x = layout.run_length + layout.riser_thickness
    points = [(layout.riser_thickness, base),
              (min(g + closure_depth, upper_x), base)]
    for level in range(2, layout.riser_count):
        start_x = (level - 1) * g + closure_depth
        if start_x >= upper_x:
            break
        z = base + level * h - closure_depth
        points.extend(((start_x, z), (min(level * g + closure_depth,
                                          upper_x), z)))
        if points[-1][0] >= upper_x:
            break
    if points[-1][0] < upper_x:
        points.append((upper_x, base + (layout.riser_count - 1) * h
                       - closure_depth))
    return _without_consecutive_duplicates(points)


def stepped_underbody_profile(layout, fields=ResidentialFields()):
    """Create the corrected full-depth closed residential body profile."""
    # Thickness is an inward physical-shell property and never locates the
    # exterior soffit.  Validating it here keeps candidate preparation atomic.
    validate_stepped_underbody_thickness(
        fields, layout.actual_riser, layout.tread_thickness,
        layout.riser_thickness)
    depth = validate_stepped_closure_depth(
        fields, layout.actual_riser, layout.going)
    inner = stepped_underbody_inner_profile(layout)
    outer = stepped_closure_visible_profile(layout, depth)
    polygon = validate_simple_polygon(inner + tuple(reversed(outer)))
    return SteppedUnderbodyProfile(inner, outer, polygon)


def build_underbody_fragment(layout, fields=ResidentialFields()):
    """Build one closed underbody fragment, independent of Side Boards."""
    profile = stepped_underbody_profile(layout, fields)
    local = extrude_xz_profile(profile.polygon, -layout.width / 2.0,
                               layout.width / 2.0,
                               part_type="UNDERBODY")
    forward, left = layout.axes.forward, layout.axes.left
    vertices = tuple((layout.lower_xy[0] + forward[0] * x + left[0] * y,
                      layout.lower_xy[1] + forward[1] * x + left[1] * y, z)
                     for x, y, z in local.vertices)
    fragment = MeshFragment("UNDERBODY", 1, vertices, local.faces)
    validate_mesh_fragments((fragment,))
    return fragment


def prepare_stage2_residential_geometry(
        points, ascent_direction, base_z_mm, floor_to_floor_mm, riser_count,
        stair_width_mm, tread_thickness_mm, riser_thickness_mm, *,
        assembly_mode=STANDARD_RESIDENTIAL, stair_schema_version=2,
        fields=ResidentialFields()):
    """Prepare the controlled, non-public Stage 2 Residential candidate.

    Stage 2 deliberately accepts only STEPPED_CLOSED with both Side Boards off.
    Everything is validated and assembled before a caller performs Scene mutation.
    """
    values = (fields if isinstance(fields, ResidentialFields)
              else residential_fields(fields))
    validate_mode_data(assembly_mode, stair_schema_version, values)
    if assembly_mode != STANDARD_RESIDENTIAL or values.underside_mode != STEPPED_CLOSED:
        raise ValueError("Stage 2 Residential geometry configurationではありません。")
    if values.left_side_board_enabled or values.right_side_board_enabled:
        raise ValueError("Stage 2 preparationでは左右Side BoardをOFFにしてください。")
    layout = resolve_stair_layout(
        points, ascent_direction, base_z_mm, floor_to_floor_mm, riser_count,
        stair_width_mm, tread_thickness_mm, riser_thickness_mm)
    fragments = (build_residential_tread_fragments(layout)
                 + build_riser_fragments(layout)
                 + (build_underbody_fragment(layout, values),))
    return layout, fragments, assemble_stair_mesh(fragments)
