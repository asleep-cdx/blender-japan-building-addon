"""Pure Build 07-E Stage-3 Winder body and side-board geometry.

The objects in this module are *derived* geometry.  They never mutate a
managed Stair and deliberately consume the nominal/physical Stage-2 plans.
Distances are metres and Z values are world coordinates.
"""

from dataclasses import dataclass
import math

from .stair_geometry import MeshFragment, validate_mesh_fragments
from .stair_turn import EPS_LENGTH, _add, _cross, _scale, _sub, _unit


@dataclass(frozen=True)
class WinderSoffitStation:
    fraction: float
    inner: tuple
    outer: tuple
    z: float
    kind: str = "DIVIDER"


@dataclass(frozen=True)
class WinderUnderbodyPlan:
    turn_index: int
    cell_index: int
    polygon: tuple
    visible_z: float
    top_z: float
    entry_closure: bool
    exit_closure: bool
    divider_owner: str = "DESTINATION"


@dataclass(frozen=True)
class WinderPivotRelief:
    rho: float
    entry: tuple
    exit: tuple
    chord: tuple


@dataclass(frozen=True)
class WinderSideBoardProfile:
    side: str
    lower: tuple
    upper: tuple
    polygon: tuple


@dataclass(frozen=True)
class SharedCenterBoardComponent:
    polygon: tuple
    v_min: float
    v_max: float


def stepped_patch_z(tread_top_z, closed_body_depth, base_z):
    """Section 20 visible-patch equation (shell thickness is irrelevant)."""
    values = tuple(map(float, (tread_top_z, closed_body_depth, base_z)))
    if not all(math.isfinite(value) for value in values) or values[1] <= 0.0:
        raise ValueError("GEOMETRY_INVALID: Winder body depth")
    return max(values[2], values[0] - values[1])


def resolve_stepped_underbody(cells, tread_tops, body_depth, base_z, *,
                              turn_index=0, entry_z=None, exit_owned=True,
                              tread_thickness=0.03, eps_clear=1.0e-9):
    """Resolve one complete nominal-cell patch and deterministic ownership."""
    if len(cells) != len(tread_tops):
        raise ValueError("GEOMETRY_INVALID: Winder cell/Z count mismatch")
    levels = tuple(stepped_patch_z(z, body_depth, base_z) for z in tread_tops)
    plans = []
    for index, (cell, top, level) in enumerate(zip(cells, tread_tops, levels)):
        if float(top) - float(tread_thickness) - level <= eps_clear:
            raise ValueError("GEOMETRY_INVALID: Winder contact clearance")
        plans.append(WinderUnderbodyPlan(
            turn_index, index + 1, tuple(cell.polygon), level,
            float(top) - float(tread_thickness),
            index == 0 and entry_z is not None
            and abs(level - float(entry_z)) > eps_clear,
            index == len(cells) - 1 and not exit_owned))
    return tuple(plans)


def divider_closure_indices(plans, eps=1.0e-9):
    """Return destination-owned non-zero divider closures."""
    return tuple(index + 2 for index in range(len(plans) - 1)
                 if abs(plans[index + 1].visible_z
                        - plans[index].visible_z) > eps)


def pivot_relief(frame, riser_thickness, eps_length=EPS_LENGTH):
    rho = max(float(riser_thickness), 10.0 * float(eps_length))
    r0, d0 = _unit(_sub(frame.entry_outer, frame.inner_pivot), "entry ray")
    rn, dn = _unit(_sub(frame.exit_outer, frame.inner_pivot), "exit ray")
    if not 0.0 < rho < min(d0, dn):
        raise ValueError("GEOMETRY_INVALID: finite pivot relief")
    j0 = _add(frame.inner_pivot, _scale(r0, rho))
    jn = _add(frame.inner_pivot, _scale(rn, rho))
    return WinderPivotRelief(rho, j0, jn, (j0, jn))


def ray_relief_intersection(frame, relief, fraction):
    """Intersect the signed-angle ray with the finite relief chord."""
    angle = frame.theta * float(fraction)
    ray0, _ = _unit(_sub(frame.entry_outer, frame.inner_pivot), "entry ray")
    ray = (ray0[0] * math.cos(angle) - ray0[1] * math.sin(angle),
           ray0[0] * math.sin(angle) + ray0[1] * math.cos(angle))
    chord = _sub(relief.exit, relief.entry)
    denominator = _cross(ray, chord)
    if abs(denominator) <= 1.0e-12:
        raise ValueError("GEOMETRY_INVALID: relief ray intersection")
    distance = _cross(_sub(relief.entry, frame.inner_pivot), chord) / denominator
    point = _add(frame.inner_pivot, _scale(ray, distance))
    if distance <= 0.0:
        raise ValueError("GEOMETRY_INVALID: relief ray direction")
    return point


def _outer_station(frame, cells, fraction, eps=1.0e-9):
    for cell in cells:
        if abs(cell.front_fraction - fraction) <= eps:
            return cell.polygon[1]
        if abs(cell.rear_fraction - fraction) <= eps:
            return cell.polygon[-1]
    raise ValueError("GEOMETRY_INVALID: missing outer divider")


def resolve_sloped_stations(frame, cells, z_entry, z_exit,
                            riser_thickness, eps_length=EPS_LENGTH):
    """Primary event stations plus geometry-only outer-corner O station."""
    relief = pivot_relief(frame, riser_thickness, eps_length)
    fractions = sorted({0.0, 1.0} | {c.front_fraction for c in cells}
                       | {c.rear_fraction for c in cells})
    ray0, _ = _unit(_sub(frame.entry_outer, frame.inner_pivot))
    ray_o, _ = _unit(_sub(frame.outer_corner, frame.inner_pivot))
    signed = math.atan2(_cross(ray0, ray_o), ray0[0] * ray_o[0] + ray0[1] * ray_o[1])
    f_o = signed / frame.theta
    if EPS_LENGTH < f_o < 1.0 - EPS_LENGTH:
        fractions.append(f_o)
    fractions = sorted(set(round(value, 14) for value in fractions))
    primary = sorted({0.0, 1.0} | {c.front_fraction for c in cells}
                     | {c.rear_fraction for c in cells})
    stations = []
    for fraction in fractions:
        is_outer = abs(fraction - f_o) <= 1.0e-10
        outer = frame.outer_corner if is_outer else _outer_station(frame, cells, fraction)
        # Event-index interpolation and angular interpolation coincide only for
        # EQUAL; interpolate between the enclosing primary event stations.
        lo = max(i for i, value in enumerate(primary) if value <= fraction + 1e-12)
        hi = min(lo + 1, len(primary) - 1)
        z_lo = float(z_entry) + lo / (len(primary) - 1) * (float(z_exit) - float(z_entry))
        z_hi = float(z_entry) + hi / (len(primary) - 1) * (float(z_exit) - float(z_entry))
        local = 0.0 if hi == lo else ((fraction - primary[lo]) /
                                      (primary[hi] - primary[lo]))
        z = z_lo + local * (z_hi - z_lo)
        stations.append(WinderSoffitStation(
            fraction, ray_relief_intersection(frame, relief, fraction),
            outer, z, "OUTER_CORNER" if is_outer else "DIVIDER"))
    return relief, tuple(stations)


def compact_grouped_height(entry_z, exit_z, first_count, second_count):
    total = int(first_count) + int(second_count)
    if int(first_count) <= 0 or int(second_count) <= 0 or total <= 0:
        raise ValueError("GEOMETRY_INVALID: Compact-U grouped counts")
    return float(entry_z) + int(first_count) / total * (float(exit_z) - float(entry_z))


def shared_edge_splits(start, end, points, eps=1.0e-9):
    """Ordered full-3D split propagation; never deduplicate in XY only."""
    a, b = tuple(start), tuple(end)
    vector = tuple(y - x for x, y in zip(a, b))
    length2 = sum(value * value for value in vector)
    if length2 <= eps * eps:
        raise ValueError("GEOMETRY_INVALID: semantic shared edge")
    candidates = [(0.0, a), (1.0, b)]
    for raw in points:
        point = tuple(map(float, raw))
        t = sum((point[i] - a[i]) * vector[i] for i in range(3)) / length2
        projected = tuple(a[i] + t * vector[i] for i in range(3))
        if -eps <= t <= 1.0 + eps and math.dist(point, projected) <= eps:
            candidates.append((max(0.0, min(1.0, t)), point))
    result = []
    for _t, point in sorted(candidates):
        if not result or math.dist(result[-1], point) > eps:
            result.append(point)
    return tuple(result)


def union_profile_rectangles(rectangles, eps=1.0e-9):
    """Union axis-aligned seam-profile rectangles without point welding.

    This deterministic decomposition is sufficient for the piecewise-linear
    Compact-U profiles: positive-area/edge-connected cells join; point-only
    and separated-Z contacts remain separate components.
    """
    rects = [tuple(map(float, r)) for r in rectangles]
    parent = list(range(len(rects)))
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for i, a in enumerate(rects):
        for j, b in enumerate(rects[:i]):
            s_overlap = min(a[1], b[1]) - max(a[0], b[0])
            z_overlap = min(a[3], b[3]) - max(a[2], b[2])
            # area overlap, or a shared non-zero edge producing a regular union
            joins = (s_overlap > eps and z_overlap >= -eps
                     or z_overlap > eps and s_overlap >= -eps)
            if joins:
                parent[root(i)] = root(j)
    groups = {}
    for i, rect in enumerate(rects): groups.setdefault(root(i), []).append(rect)
    return tuple(tuple(group) for _, group in sorted(groups.items()))


def symmetric_board_component(polygon, thickness):
    half = float(thickness) / 2.0
    if half <= 0.0: raise ValueError("GEOMETRY_INVALID: board thickness")
    return SharedCenterBoardComponent(tuple(polygon), -half, half)


def butt_joint_plane(endpoint, tangent):
    direction, _ = _unit(tuple(tangent), "shared seam tangent")
    return (tuple(endpoint), direction)


def resolve_side_board_profile(side, lower_stations, walking_stations,
                               reveal, mode="STEPPED"):
    """Resolve independent lower-underbody and upper-walking authorities.

    Stations are ``(s, z)`` in an already resolved exterior-boundary frame.
    Geometry-only stations may be repeated in ``walking_stations`` and do not
    imply a RiseEvent.  LEFT/RIGHT is ascent-local metadata, not world X/Y.
    """
    if side not in ("LEFT", "RIGHT") or mode not in ("STEPPED", "SLOPED"):
        raise ValueError("GEOMETRY_INVALID: Winder Side Board mode")
    lower = tuple((float(s), float(z)) for s, z in lower_stations)
    walking = tuple((float(s), float(z) + float(reveal))
                    for s, z in walking_stations)
    if len(lower) < 2 or len(walking) < 2:
        raise ValueError("GEOMETRY_INVALID: Winder Side Board stations")
    if mode == "SLOPED":
        upper = (walking[0], walking[-1])
    else:
        upper = walking
    polygon = upper + tuple(reversed(lower))
    if any(not math.isfinite(value) for point in polygon for value in point):
        raise ValueError("GEOMETRY_INVALID: Winder Side Board profile")
    return WinderSideBoardProfile(side, lower, upper, polygon)


def world_side_for_uphill(side, ascent_direction):
    """Expose recomputed world ownership; no persistent/stale side cache."""
    if side not in ("LEFT", "RIGHT") or ascent_direction not in ("FORWARD", "REVERSE"):
        raise ValueError("GEOMETRY_INVALID: side ownership")
    return side if ascent_direction == "FORWARD" else (
        "RIGHT" if side == "LEFT" else "LEFT")


def subtract_box_intersection(part_box, board_box, eps=1.0e-9):
    """Deterministically subtract one positive-volume AABB and cap every cut.

    The returned disjoint boxes are a convenient clipping primitive used by
    Stage-3 callers after transforming to the seam-local ``(s,v,z)`` frame.
    A partial-height board never removes a full-height plan strip.
    """
    p = tuple(map(float, part_box)); b = tuple(map(float, board_box))
    if len(p) != 6 or len(b) != 6:
        raise ValueError("GEOMETRY_INVALID: trim bounds")
    lo = tuple(max(p[i], b[i]) for i in (0, 2, 4))
    hi = tuple(min(p[i], b[i]) for i in (1, 3, 5))
    if any(hi[i] - lo[i] <= eps for i in range(3)):
        return (p,)
    pieces = []
    x0, x1, y0, y1, z0, z1 = p
    ix0, iy0, iz0 = lo; ix1, iy1, iz1 = hi
    candidates = ((x0, ix0, y0, y1, z0, z1),
                  (ix1, x1, y0, y1, z0, z1),
                  (ix0, ix1, y0, iy0, z0, z1),
                  (ix0, ix1, iy1, y1, z0, z1),
                  (ix0, ix1, iy0, iy1, z0, iz0),
                  (ix0, ix1, iy0, iy1, iz1, z1))
    for box in candidates:
        if box[1]-box[0] > eps and box[3]-box[2] > eps and box[5]-box[4] > eps:
            pieces.append(box)
    return tuple(pieces)


def _variable_prism(polygon, bottom, top, role, ordinal):
    """Closed vertical-wall prism with per-plan-vertex bottom/top heights."""
    polygon = tuple(polygon); n = len(polygon)
    vertices = tuple((p[0], p[1], float(bottom[i])) for i, p in enumerate(polygon)) + tuple(
        (p[0], p[1], float(top[i])) for i, p in enumerate(polygon))
    faces = [tuple(reversed(range(n))), tuple(range(n, 2*n))]
    faces += [(i, (i+1)%n, (i+1)%n+n, i+n) for i in range(n)]
    fragment = MeshFragment(role, ordinal, vertices, tuple(faces))
    validate_mesh_fragments((fragment,))
    return fragment


def build_stepped_underbody_fragments(plans, ordinal_start=10000):
    result = []
    for offset, plan in enumerate(plans):
        n = len(plan.polygon)
        result.append(_variable_prism(plan.polygon,
                                      (plan.visible_z,) * n,
                                      (plan.top_z,) * n,
                                      "UNDERBODY", ordinal_start + offset))
    return tuple(result)


def high_side_pivot_closure(frame, relief, z_entry, z_exit):
    """Return the intentional Section-21.4 closure with named ownership."""
    low, high = sorted((float(z_entry), float(z_exit)))
    endpoint = relief.exit if z_exit >= z_entry else relief.entry
    return ("HIGH_SIDE_PIVOT_CLOSURE",
            ((frame.inner_pivot[0], frame.inner_pivot[1], low),
             (frame.inner_pivot[0], frame.inner_pivot[1], high),
             (endpoint[0], endpoint[1], high)))


def build_sloped_underbody_fragments(frame, cells, tread_tops, body_depth,
                                     base_z, riser_thickness, tread_thickness,
                                     ordinal_start=11000):
    """Build deterministic relief strips and a finite pivot-core solid."""
    if len(cells) != len(tread_tops):
        raise ValueError("GEOMETRY_INVALID: Winder cell/Z count mismatch")
    z0 = stepped_patch_z(tread_tops[0], body_depth, base_z)
    zn = stepped_patch_z(tread_tops[-1], body_depth, base_z)
    relief, stations = resolve_sloped_stations(
        frame, cells, z0, zn, riser_thickness)
    fragments = []
    for index, (a, b) in enumerate(zip(stations, stations[1:])):
        middle = (a.fraction + b.fraction) / 2.0
        cell_index = next(i for i, cell in enumerate(cells)
                          if cell.front_fraction - 1e-9 <= middle
                          <= cell.rear_fraction + 1e-9)
        contact = float(tread_tops[cell_index]) - float(tread_thickness)
        if max(a.z, b.z) >= contact - 1e-9:
            raise ValueError("GEOMETRY_INVALID: Winder contact clearance")
        polygon = (a.inner, a.outer, b.outer, b.inner)
        fragments.append(_variable_prism(
            polygon, (a.z, a.z, b.z, b.z), (contact,) * 4,
            "UNDERBODY", ordinal_start + index))
    # A finite triangular core closes the pivot.  Its bottom is horizontal at
    # z_low; the explicit high-side triangle remains discoverable through
    # high_side_pivot_closure and its walls are part of this closed solid.
    z_low = min(z0, zn)
    contact = min(float(value) - float(tread_thickness)
                  for value in tread_tops)
    fragments.append(_variable_prism(
        (frame.inner_pivot, relief.entry, relief.exit),
        (z_low, z0, zn), (contact, contact, contact),
        "UNDERBODY", ordinal_start + len(fragments)))
    return tuple(fragments), relief, stations, high_side_pivot_closure(
        frame, relief, z0, zn)
