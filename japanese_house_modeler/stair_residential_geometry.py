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


@dataclass(frozen=True)
class SideBoardProfile:
    reference: tuple
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


def side_board_reference_profile(layout):
    """Return exact analytical S_ref, independent of generated Mesh data."""
    points = [(0.0, layout.base_z)]
    for level in range(1, layout.riser_count + 1):
        x = min(level - 1, layout.riser_count - 1) * layout.going
        points.append((x, layout.base_z + level * layout.actual_riser))
        if level < layout.riser_count:
            points.append((level * layout.going,
                           layout.base_z + level * layout.actual_riser))
    return _without_consecutive_duplicates(points)


def _clip_polygon(points, axis, limit, keep_less):
    result = []
    for start, end in zip(points, points[1:] + points[:1]):
        start_in = start[axis] <= limit if keep_less else start[axis] >= limit
        end_in = end[axis] <= limit if keep_less else end[axis] >= limit
        if start_in:
            result.append(start)
        if start_in != end_in:
            delta = end[axis] - start[axis]
            ratio = (limit - start[axis]) / delta
            other = 1 - axis
            point = [0.0, 0.0]
            point[axis] = limit
            point[other] = start[other] + ratio * (end[other] - start[other])
            result.append(tuple(point))
    return list(_without_consecutive_duplicates(result))


def side_board_profile(layout, fields=ResidentialFields()):
    """Build full translated stepped band, then clip both half-planes."""
    depth = validate_stepped_closure_depth(fields, layout.actual_riser,
                                            layout.going)
    reference = side_board_reference_profile(layout)
    # First/last segments are vertical.  Every internal translated-line
    # intersection is (+X depth, -Z depth) from its reference corner.
    outer = [(reference[0][0] + depth, reference[0][1])]
    outer.extend((x + depth, z - depth) for x, z in reference[1:-1])
    outer.append((reference[-1][0] + depth, reference[-1][1]))
    complete = list(reference) + list(reversed(outer))
    lower_clipped = _clip_polygon(complete, 1, layout.base_z, False)
    upper_limit = layout.run_length + layout.riser_thickness
    clipped = _clip_polygon(lower_clipped, 0, upper_limit, True)
    polygon = validate_simple_polygon(clipped)
    return SideBoardProfile(reference, _without_consecutive_duplicates(outer),
                            polygon)


def build_side_board_fragment(layout, side, fields=ResidentialFields()):
    values = fields if isinstance(fields, ResidentialFields) else residential_fields(fields)
    thickness = float(values.side_board_thickness_mm) / 1000.0
    profile = side_board_profile(layout, values)
    half = layout.width / 2.0
    if side == "LEFT":
        y_min, y_max, ordinal = half, half + thickness, 1
    elif side == "RIGHT":
        y_min, y_max, ordinal = -half - thickness, -half, 2
    else:
        raise ValueError("Side Board sideはLEFTまたはRIGHTである必要があります。")
    local = extrude_xz_profile(profile.polygon, y_min, y_max,
                               part_type="SIDE_BOARD", ordinal=ordinal)
    forward, left = layout.axes.forward, layout.axes.left
    vertices = tuple((layout.lower_xy[0] + forward[0] * x + left[0] * y,
                      layout.lower_xy[1] + forward[1] * x + left[1] * y, z)
                     for x, y, z in local.vertices)
    fragment = MeshFragment("SIDE_BOARD", ordinal, vertices, local.faces)
    validate_mesh_fragments((fragment,))
    return fragment


def prepare_residential_geometry(
        points, ascent_direction, base_z_mm, floor_to_floor_mm, riser_count,
        stair_width_mm, tread_thickness_mm, riser_thickness_mm, *,
        assembly_mode=STANDARD_RESIDENTIAL, stair_schema_version=2,
        fields=ResidentialFields()):
    """Prepare the complete Stage 3 candidate without Scene mutation."""
    values = fields if isinstance(fields, ResidentialFields) else residential_fields(fields)
    validate_mode_data(assembly_mode, stair_schema_version, values)
    if assembly_mode != STANDARD_RESIDENTIAL or values.underside_mode != STEPPED_CLOSED:
        raise ValueError("Residential geometry configurationではありません。")
    layout = resolve_stair_layout(
        points, ascent_direction, base_z_mm, floor_to_floor_mm, riser_count,
        stair_width_mm, tread_thickness_mm, riser_thickness_mm)
    fragments = list(build_residential_tread_fragments(layout))
    fragments.extend(build_riser_fragments(layout))
    fragments.append(build_underbody_fragment(layout, values))
    if values.left_side_board_enabled:
        fragments.append(build_side_board_fragment(layout, "LEFT", values))
    if values.right_side_board_enabled:
        fragments.append(build_side_board_fragment(layout, "RIGHT", values))
    fragments = tuple(fragments)
    return layout, fragments, assemble_stair_mesh(fragments)


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
