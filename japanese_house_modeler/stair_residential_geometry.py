"""Pure Build 07-B Residential underbody and side-board preparation."""

from dataclasses import dataclass

from .stair_geometry import (
    MeshFragment, assemble_stair_mesh, build_riser_fragments,
    build_tread_fragments, extrude_xz_profile, resolve_stair_layout,
    validate_mesh_fragments, validate_simple_polygon,
)
from .stair_residential import (
    STANDARD_RESIDENTIAL, STEPPED_CLOSED, ResidentialFields,
    residential_fields, validate_mode_data,
    validate_side_board_dimensions,
    validate_stepped_underbody_thickness,
)


@dataclass(frozen=True)
class SteppedUnderbodyProfile:
    """Validated metre-based analytical paths and their closed XZ polygon."""

    inner: tuple
    outer: tuple
    polygon: tuple


@dataclass(frozen=True)
class SideBoardProfile:
    """Analytical walking line, un-clipped band, and final clipped polygon."""

    reference: tuple
    complete_polygon: tuple
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
        points.extend((
            ((step - 1) * g + r, base + (step - 1) * h),
            ((step - 1) * g + r, base + step * h - t),
            (step * g, base + step * h - t),
            (step * g, base + step * h),
            (step * g + r, base + step * h),
        ))
    return _without_consecutive_duplicates(points)


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


def stepped_underbody_profile(layout, fields=ResidentialFields()):
    """Create and validate the exact Stage 2 closed underbody profile."""
    thickness = validate_stepped_underbody_thickness(
        fields, layout.actual_riser, layout.tread_thickness,
        layout.riser_thickness)
    inner = stepped_underbody_inner_profile(layout)
    outer = stepped_underbody_outer_profile(inner, thickness, layout.base_z)
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
    """Return ideal walking-step S_ref without mesh/nosing dependencies."""
    points = [(0.0, layout.base_z)]
    for step in range(1, layout.riser_count):
        z = layout.base_z + step * layout.actual_riser
        points.append(((step - 1) * layout.going, z))
        points.append((step * layout.going, z))
    points.append((layout.run_length, layout.upper_arrival_z))
    return _without_consecutive_duplicates(points)


def _clip_polygon(points, *, axis, limit, keep_less):
    """Sutherland-Hodgman clip against one axis-aligned half-plane."""
    result = []
    previous = points[-1]
    previous_inside = (previous[axis] <= limit if keep_less
                       else previous[axis] >= limit)
    for current in points:
        current_inside = (current[axis] <= limit if keep_less
                          else current[axis] >= limit)
        if current_inside != previous_inside:
            other = 1 - axis
            denominator = current[axis] - previous[axis]
            ratio = (limit - previous[axis]) / denominator
            intersection = [0.0, 0.0]
            intersection[axis] = limit
            intersection[other] = (previous[other]
                                   + ratio * (current[other] - previous[other]))
            result.append(tuple(intersection))
        if current_inside:
            result.append(current)
        previous, previous_inside = current, current_inside
    return _without_consecutive_duplicates(result)


def side_board_profile(layout, fields=ResidentialFields()):
    """Construct the complete stepped band, then clip lower and upper limits."""
    _thickness, band = validate_side_board_dimensions(
        fields, layout.actual_riser, layout.going)
    reference = side_board_reference_profile(layout)
    outer = [(reference[0][0] + band, reference[0][1])]
    for before, point, after in zip(reference, reference[1:], reference[2:]):
        incoming_vertical = before[0] == point[0]
        outgoing_vertical = point[0] == after[0]
        x = point[0] + band if incoming_vertical or outgoing_vertical else point[0]
        z = point[1] - band if not incoming_vertical or not outgoing_vertical else point[1]
        outer.append((x, z))
    outer.append((reference[-1][0] + band, reference[-1][1]))
    complete = validate_simple_polygon(reference + tuple(reversed(outer)))
    clipped = _clip_polygon(complete, axis=1, limit=layout.base_z, keep_less=False)
    clipped = _clip_polygon(
        clipped, axis=0, limit=layout.run_length + layout.riser_thickness,
        keep_less=True)
    return SideBoardProfile(reference, complete, validate_simple_polygon(clipped))


def build_side_board_fragment(layout, side, fields=ResidentialFields()):
    """Build one independently valid fascia on the uphill-relative side."""
    thickness, _band = validate_side_board_dimensions(
        fields, layout.actual_riser, layout.going)
    half = layout.width / 2.0
    if side == "LEFT":
        y_min, y_max, ordinal = half, half + thickness, 1
    elif side == "RIGHT":
        y_min, y_max, ordinal = -half - thickness, -half, 2
    else:
        raise ValueError("Side Board sideはLEFTまたはRIGHTである必要があります。")
    profile = side_board_profile(layout, fields)
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
    validate_side_board_dimensions(values, layout.actual_riser, layout.going)
    fragments = list(build_tread_fragments(layout) + build_riser_fragments(layout))
    fragments.append(build_underbody_fragment(layout, values))
    if values.left_side_board_enabled:
        fragments.append(build_side_board_fragment(layout, "LEFT", values))
    if values.right_side_board_enabled:
        fragments.append(build_side_board_fragment(layout, "RIGHT", values))
    fragments = tuple(fragments)
    validate_mesh_fragments(fragments)
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
    fragments = (build_tread_fragments(layout) + build_riser_fragments(layout)
                 + (build_underbody_fragment(layout, values),))
    return layout, fragments, assemble_stair_mesh(fragments)
