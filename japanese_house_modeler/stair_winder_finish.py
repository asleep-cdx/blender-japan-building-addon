"""Pure Build 07-E Stage-3 Winder body and side-board geometry.

The objects in this module are *derived* geometry.  They never mutate a
managed Stair and deliberately consume the nominal/physical Stage-2 plans.
Distances are metres and Z values are world coordinates.
"""

from dataclasses import dataclass
import math

from .stair_geometry import MeshFragment, _signed_volume, validate_mesh_fragments
from .stair_turn import (
    EPS_LENGTH, _add, _cross, _deduplicate, _dot, _scale, _sub, _unit,
)


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


@dataclass(frozen=True)
class CompactContributorAuthority:
    """Source-derived constant terminal cross-section over a shared seam."""
    s_start: float
    s_end: float
    lower_start: float
    lower_end: float
    upper_start: float
    upper_end: float


def compact_contributor_authority(seam_length, lower_terminal,
                                  walking_terminal, reveal):
    """Resolve the reachable Compact-U rectangular-profile special case.

    A contributor is sourced from one reconciled Turn terminal section.  That
    section has one underbody terminal Z and one walking-plus-reveal terminal
    Z across the full seam, so both endpoint evaluations are intentionally
    identical.  Validation here prevents production from silently forcing a
    non-positive or partial contributor into that special case.
    """
    length=float(seam_length); lower=float(lower_terminal)
    upper=float(walking_terminal)+float(reveal)
    if not all(math.isfinite(value) for value in (length,lower,upper)) \
            or length<=EPS_LENGTH or upper<=lower+EPS_LENGTH:
        raise ValueError("GEOMETRY_INVALID: Compact-U contributor authority")
    return CompactContributorAuthority(0.0,length,lower,lower,upper,upper)


def compact_center_side(frame, ascent_direction):
    """Return the uphill-relative side facing the inside of a Compact-U."""
    effective_theta = frame.theta if ascent_direction == "FORWARD" else -frame.theta
    return "LEFT" if effective_theta > 0.0 else "RIGHT"


def side_enabled(fields, side):
    return (fields.left_side_board_enabled if side == "LEFT"
            else fields.right_side_board_enabled)


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


def propagate_semantic_edge_splits(fragments, eps=1.0e-12):
    """Propagate every production full-XYZ station to incident face edges."""
    fragments=tuple(fragments)
    stations=tuple(dict.fromkeys(vertex for fragment in fragments
                                 for vertex in fragment.vertices))
    result=[]
    for fragment in fragments:
        vertices=list(fragment.vertices)
        indices={vertex:index for index,vertex in enumerate(vertices)}
        faces=[]
        for face in fragment.faces:
            expanded=[]
            for position,start_index in enumerate(face):
                end_index=face[(position+1)%len(face)]
                start,end=vertices[start_index],vertices[end_index]
                edge=tuple(end[i]-start[i] for i in range(3))
                length2=sum(value*value for value in edge)
                candidates=[]
                if length2>eps*eps:
                    for point in stations:
                        delta=tuple(point[i]-start[i] for i in range(3))
                        t=sum(delta[i]*edge[i] for i in range(3))/length2
                        if not eps<t<1.0-eps:
                            continue
                        projected=tuple(start[i]+t*edge[i] for i in range(3))
                        if math.dist(point,projected)<=eps:
                            candidates.append((t,point))
                expanded.append(start_index)
                ordered=[]
                for t,point in sorted(candidates,key=lambda item:(item[0],item[1])):
                    if not ordered or math.dist(ordered[-1][1],point)>eps:
                        ordered.append((t,point))
                for _t,point in ordered:
                    if point not in indices:
                        indices[point]=len(vertices); vertices.append(point)
                    if expanded[-1]!=indices[point]:
                        expanded.append(indices[point])
            faces.append(tuple(expanded))
        rebuilt=MeshFragment(fragment.part_type,fragment.ordinal,
                             tuple(vertices),tuple(faces))
        try:
            validate_mesh_fragments((rebuilt,))
        except ValueError:
            # A station crossing only one face is not a shared semantic edge;
            # retaining the already-valid closed fragment avoids creating a
            # topological connection between unrelated collinear geometry.
            rebuilt=fragment
        result.append(rebuilt)
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


def exact_rectangle_union_components(rectangles, eps=1.0e-9):
    """Return exact, disjoint rectangles for each edge-connected union.

    Grid decomposition preserves every absent L-shaped region.  Cells touching
    at a point are deliberately assigned to different components.
    """
    rects = tuple(tuple(map(float, rectangle)) for rectangle in rectangles)
    if not rects:
        return ()
    xs = sorted({value for r in rects for value in r[:2]})
    zs = sorted({value for r in rects for value in r[2:]})
    cells = []
    for x0, x1 in zip(xs, xs[1:]):
        for z0, z1 in zip(zs, zs[1:]):
            if x1-x0 <= eps or z1-z0 <= eps: continue
            cx, cz = (x0+x1)/2.0, (z0+z1)/2.0
            if any(r[0]-eps <= cx <= r[1]+eps and
                   r[2]-eps <= cz <= r[3]+eps for r in rects):
                cells.append((x0,x1,z0,z1))
    parent = list(range(len(cells)))
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for i, a in enumerate(cells):
        for j, b in enumerate(cells[:i]):
            vertical = (abs(a[1]-b[0]) <= eps or abs(b[1]-a[0]) <= eps) \
                and min(a[3],b[3])-max(a[2],b[2]) > eps
            horizontal = (abs(a[3]-b[2]) <= eps or abs(b[3]-a[2]) <= eps) \
                and min(a[1],b[1])-max(a[0],b[0]) > eps
            if vertical or horizontal: parent[root(i)] = root(j)
    groups = {}
    for i, cell in enumerate(cells): groups.setdefault(root(i), []).append(cell)
    return tuple(tuple(group) for _, group in sorted(groups.items()))


def rectangle_component_boundaries(component):
    """Cancel internal grid edges and trace deterministic external loops."""
    edges = set()
    for x0,x1,z0,z1 in component:
        ring=((x0,z0),(x1,z0),(x1,z1),(x0,z1))
        for edge in zip(ring,ring[1:]+ring[:1]):
            reverse=(edge[1],edge[0])
            if reverse in edges: edges.remove(reverse)
            else: edges.add(edge)
    loops=[]
    while edges:
        first=min(edges); edges.remove(first)
        loop=[first[0],first[1]]
        while loop[-1] != loop[0]:
            choices=sorted(edge for edge in edges if edge[0]==loop[-1])
            if not choices: raise ValueError("GEOMETRY_INVALID: profile union boundary")
            edge=choices[0];edges.remove(edge);loop.append(edge[1])
        loop.pop()
        # remove collinear grid stations while preserving every profile corner
        changed=True
        while changed and len(loop)>3:
            changed=False
            for i in range(len(loop)):
                if abs(_cross(_sub(loop[i],loop[i-1]),
                              _sub(loop[(i+1)%len(loop)],loop[i])))<=1e-12:
                    del loop[i];changed=True;break
        loops.append(tuple(loop))
    return tuple(loops)


def symmetric_board_component(polygon, thickness):
    half = float(thickness) / 2.0
    if half <= 0.0: raise ValueError("GEOMETRY_INVALID: board thickness")
    return SharedCenterBoardComponent(tuple(polygon), -half, half)


def butt_joint_plane(endpoint, tangent):
    direction, _ = _unit(tuple(tangent), "shared seam tangent")
    return (tuple(endpoint), direction)


def clip_fragment_to_vertical_plane(fragment, point, normal,
                                    keep_positive=True, eps=1.0e-9):
    """Clip a closed convex fragment and cap the common vertical plane."""
    point=tuple(point[:2]); normal,_length=_unit(tuple(normal[:2]))
    def distance(vertex):
        value=(vertex[0]-point[0])*normal[0]+(vertex[1]-point[1])*normal[1]
        return value if keep_positive else -value
    polygons=[]; cut=[]
    for face in fragment.faces:
        source=[fragment.vertices[index] for index in face]; output=[]
        previous=source[-1]; dp=distance(previous); inside_p=dp>=-eps
        for current in source:
            dc=distance(current); inside_c=dc>=-eps
            if inside_c!=inside_p:
                t=dp/(dp-dc)
                intersection=tuple(round(previous[i]+t*(current[i]-previous[i]),14)
                                   for i in range(3))
                output.append(intersection); cut.append(intersection)
            if inside_c: output.append(current)
            previous,dp,inside_p=current,dc,inside_c
        cleaned=[]
        for vertex in output:
            if not cleaned or math.dist(cleaned[-1],vertex)>eps:
                cleaned.append(vertex)
        if len(cleaned)>2 and math.dist(cleaned[0],cleaned[-1])<=eps:
            cleaned.pop()
        if len(cleaned)>=3: polygons.append(tuple(cleaned))
    unique=[]
    for vertex in cut:
        if not any(math.dist(vertex,other)<=eps for other in unique):
            unique.append(vertex)
    if len(unique)>=3:
        tangent=(-normal[1],normal[0])
        center=tuple(sum(v[i] for v in unique)/len(unique) for i in range(3))
        unique.sort(key=lambda v:math.atan2(
            v[2]-center[2],(v[0]-center[0])*tangent[0]
            +(v[1]-center[1])*tangent[1]))
        if keep_positive:
            unique.reverse()
        polygons.append(tuple(unique))
    vertices=[]; indices={}; faces=[]
    for polygon in polygons:
        face=[]
        for vertex in polygon:
            if vertex not in indices:
                indices[vertex]=len(vertices); vertices.append(vertex)
            face.append(indices[vertex])
        faces.append(tuple(face))
    if len(vertices)<4: return None
    candidate=MeshFragment(fragment.part_type,fragment.ordinal,
                           tuple(vertices),tuple(faces))
    if _signed_volume(candidate.vertices,candidate.faces)<0:
        candidate=MeshFragment(candidate.part_type,candidate.ordinal,
                               candidate.vertices,
                               tuple(tuple(reversed(face))
                                     for face in candidate.faces))
    validate_mesh_fragments((candidate,))
    return candidate


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
    polygon, bottom, top = tuple(polygon), tuple(bottom), tuple(top)
    area = sum(polygon[i][0] * polygon[(i + 1) % len(polygon)][1]
               - polygon[(i + 1) % len(polygon)][0] * polygon[i][1]
               for i in range(len(polygon))) / 2.0
    if area < 0.0:
        polygon, bottom, top = (tuple(reversed(polygon)),
                                tuple(reversed(bottom)), tuple(reversed(top)))
    n = len(polygon)
    vertices = tuple((p[0], p[1], float(bottom[i])) for i, p in enumerate(polygon)) + tuple(
        (p[0], p[1], float(top[i])) for i, p in enumerate(polygon))
    faces = ([(0, i + 1, i) for i in range(1, n - 1)]
             + [(n, n + i, n + i + 1) for i in range(1, n - 1)])
    faces += [(i, (i+1)%n, (i+1)%n+n, i+n) for i in range(n)]
    # Horizontal clipping may make top and bottom meet on a contour. Collapse
    # those exact 3D vertices and discard only the resulting zero-area faces.
    unique=[]; remap={}
    for index,vertex in enumerate(vertices):
        target=next((i for i,item in enumerate(unique)
                     if math.dist(vertex,item)<=1e-12),None)
        if target is None: target=len(unique);unique.append(vertex)
        remap[index]=target
    cleaned=[]
    for face in faces:
        mapped=[]
        for index in face:
            value=remap[index]
            if not mapped or mapped[-1]!=value: mapped.append(value)
        if len(mapped)>1 and mapped[0]==mapped[-1]: mapped.pop()
        if len(set(mapped))>=3: cleaned.append(tuple(mapped))
    vertices,faces=tuple(unique),cleaned
    if _signed_volume(vertices, faces) < 0.0:
        faces = [tuple(reversed(face)) for face in faces]
    fragment = MeshFragment(role, ordinal, vertices, tuple(faces))
    validate_mesh_fragments((fragment,))
    return fragment


def _edge_board_fragment(a, b, lower_a, lower_b, upper_a, upper_b,
                         thickness, ordinal):
    """Extrude one boundary/profile interval as a closed board volume."""
    direction, _ = _unit(_sub(b, a), "Side Board boundary")
    normal = (-direction[1], direction[0])
    half = float(thickness) / 2.0
    polygon = (_add(a, _scale(normal, -half)),
               _add(b, _scale(normal, -half)),
               _add(b, _scale(normal, half)),
               _add(a, _scale(normal, half)))
    return _variable_prism(
        polygon, (lower_a, lower_b, lower_b, lower_a),
        (upper_a, upper_b, upper_b, upper_a), "SIDE_BOARD", ordinal)


def build_shared_center_board_fragment(shared_interface, lower_z, upper_z,
                                       thickness, ordinal=14000):
    """Build the single symmetric Compact-U shared-center board family."""
    if len(shared_interface) != 2 or float(upper_z) <= float(lower_z):
        raise ValueError("GEOMETRY_INVALID: shared-center board profile")
    return _edge_board_fragment(
        shared_interface[0], shared_interface[1], lower_z, lower_z,
        upper_z, upper_z, thickness, ordinal)


def build_shared_profile_component(shared_interface, profile, thickness,
                                   ordinal=14000):
    """Extrude one closed ``(s,z)`` union component symmetrically in v."""
    start, end = shared_interface
    tangent, length = _unit(_sub(end, start), "shared center seam")
    normal = (-tangent[1], tangent[0]); half = float(thickness) / 2.0
    profile = tuple(profile)
    vertices = []
    for v in (-half, half):
        vertices.extend((start[0] + tangent[0] * s + normal[0] * v,
                         start[1] + tangent[1] * s + normal[1] * v, z)
                        for s, z in profile)
    n = len(profile)
    faces = [tuple(reversed(range(n))), tuple(range(n, 2*n))]
    faces.extend((i, (i+1)%n, (i+1)%n+n, i+n) for i in range(n))
    if _signed_volume(vertices, faces) < 0.0:
        faces = [tuple(reversed(face)) for face in faces]
    fragment = MeshFragment("SIDE_BOARD", ordinal, tuple(vertices), tuple(faces))
    validate_mesh_fragments((fragment,))
    return fragment


def trim_prism_fragment_against_shared_board(fragment, shared_interface,
                                             thickness, z_min, z_max,
                                             s_min=0.0, s_max=None):
    """Clip a constant-height production prism outside the shared board strip.

    Non-prismatic/profiled parts and partial-height intersections are retained
    for the caller's more detailed splitter; supported SQUARE Compact-U parts
    use this deterministic capped path.
    """
    vertices = tuple(fragment.vertices)
    if len(vertices) % 2:
        return fragment
    n = len(vertices) // 2
    if n < 3 or any(math.dist(vertices[i][:2], vertices[i+n][:2]) > EPS_LENGTH
                    for i in range(n)):
        return fragment
    source_polygon = tuple(vertex[:2] for vertex in vertices[:n])
    source_bottom = tuple(vertex[2] for vertex in vertices[:n])
    source_top = tuple(vertex[2] for vertex in vertices[n:])
    bottom = min(source_bottom)
    top = max(source_top)
    if top <= z_min + EPS_LENGTH or bottom >= z_max - EPS_LENGTH:
        return fragment
    # A partial-height intersection must not erase the full strip. Split the
    # vertical ranges into capped prisms and clip only the overlapping range.
    start, end = shared_interface
    tangent, seam_length = _unit(_sub(end, start), "shared center seam")
    if s_max is None: s_max = seam_length
    normal = (-tangent[1], tangent[0]); half = float(thickness) / 2.0
    polygon = source_polygon
    def source_z(point, values):
        for vertex,value in zip(source_polygon,values):
            if math.dist(point,vertex)<=EPS_LENGTH: return value
        # Production variable prisms use planar/ruled faces.  Locate the point
        # in the deterministic fan and barycentrically preserve that surface.
        a=source_polygon[0]
        for i in range(1,n-1):
            b,c=source_polygon[i],source_polygon[i+1]
            den=_cross(_sub(b,a),_sub(c,a))
            if abs(den)<=1e-15: continue
            u=_cross(_sub(point,a),_sub(c,a))/den
            v=_cross(_sub(b,a),_sub(point,a))/den
            w=1.0-u-v
            if min(u,v,w)>=-EPS_LENGTH:
                return w*values[0]+u*values[i]+v*values[i+1]
        raise ValueError("GEOMETRY_INVALID: trim Z interpolation")
    def clip(poly, value, bound, keep_greater):
        out=[]
        for a,b in zip(poly,poly[1:]+poly[:1]):
            da=(value(a)-bound)*(1 if keep_greater else -1)
            db=(value(b)-bound)*(1 if keep_greater else -1)
            ia,ib=da>=-EPS_LENGTH,db>=-EPS_LENGTH
            if ia: out.append(a)
            if ia != ib:
                ratio=da/(da-db)
                out.append((a[0]+ratio*(b[0]-a[0]),a[1]+ratio*(b[1]-a[1])))
        return list(_deduplicate(out))
    sval=lambda p:_dot(_sub(p,start),tangent)
    vval=lambda p:_dot(_sub(p,start),normal)
    middle=clip(list(polygon),sval,float(s_min),True)
    middle=clip(middle,sval,float(s_max),False) if middle else []
    plan_pieces=[]
    before=clip(list(polygon),sval,float(s_min),False)
    after=clip(list(polygon),sval,float(s_max),True)
    negative=clip(middle,vval,-half,False) if middle else []
    positive=clip(middle,vval,half,True) if middle else []
    center=clip(middle,vval,-half,True) if middle else []
    center=clip(center,vval,half,False) if center else []
    for candidate in (before,negative,positive,after):
        cleaned=[]
        for point in candidate:
            if not cleaned or math.dist(point,cleaned[-1])>EPS_LENGTH:
                cleaned.append(point)
        if len(cleaned)>1 and math.dist(cleaned[0],cleaned[-1])<=EPS_LENGTH:
            cleaned.pop()
        candidate=cleaned
        changed=True
        while changed and len(candidate)>3:
            changed=False
            for index in range(len(candidate)):
                a,b,c=(candidate[index-1],candidate[index],
                       candidate[(index+1)%len(candidate)])
                if abs(_cross(_sub(b,a),_sub(c,b)))<=1e-12:
                    del candidate[index];changed=True;break
        area=abs(sum(candidate[i][0]*candidate[(i+1)%len(candidate)][1]
                     -candidate[(i+1)%len(candidate)][0]*candidate[i][1]
                     for i in range(len(candidate)))/2.0) if len(candidate)>=3 else 0.0
        if len(candidate)>=3 and area>EPS_LENGTH*EPS_LENGTH:
            plan_pieces.append(tuple(candidate))
    if not plan_pieces: return None
    pieces = []
    for plan in plan_pieces:
        bottoms=tuple(source_z(point,source_bottom) for point in plan)
        tops=tuple(source_z(point,source_top) for point in plan)
        pieces.append(_variable_prism(
            plan, bottoms, tops,
            fragment.part_type, fragment.ordinal))
    center=list(_deduplicate(center))
    if len(center)>=3:
        def contour(poly, values, bound, keep_below):
            out=[]
            for a,b in zip(poly,poly[1:]+poly[:1]):
                va,vb=values(a),values(b)
                da=(bound-va) if keep_below else (va-bound)
                db=(bound-vb) if keep_below else (vb-bound)
                ia,ib=da>=-EPS_LENGTH,db>=-EPS_LENGTH
                if ia: out.append(a)
                if ia != ib:
                    t=da/(da-db)
                    out.append((a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])))
            return list(_deduplicate(out))
        bottom_at=lambda p:source_z(p,source_bottom)
        top_at=lambda p:source_z(p,source_top)
        # Triangulation makes both source Z fields linear on every clipping
        # domain, so z=z_min/z_max contours are exact straight segments.
        for index in range(1,len(center)-1):
            triangle=[center[0],center[index],center[index+1]]
            lower_domain=contour(triangle,bottom_at,z_min,True)
            lower_native=contour(lower_domain,top_at,z_min,True) if lower_domain else []
            lower_cap=contour(lower_domain,top_at,z_min,False) if lower_domain else []
            for poly,use_cap in ((lower_native,False),(lower_cap,True)):
                if len(poly)>=3:
                    bottoms=tuple(bottom_at(p) for p in poly)
                    tops=(tuple(z_min for _ in poly) if use_cap
                          else tuple(top_at(p) for p in poly))
                    if all(t-b>=-EPS_LENGTH for b,t in zip(bottoms,tops)) \
                            and any(t-b>EPS_LENGTH for b,t in zip(bottoms,tops)):
                        pieces.append(_variable_prism(
                            tuple(poly),bottoms,tops,
                            fragment.part_type,fragment.ordinal))
            upper_domain=contour(triangle,top_at,z_max,False)
            upper_native=contour(upper_domain,bottom_at,z_max,False) if upper_domain else []
            upper_cap=contour(upper_domain,bottom_at,z_max,True) if upper_domain else []
            for poly,use_cap in ((upper_native,False),(upper_cap,True)):
                if len(poly)>=3:
                    bottoms=(tuple(bottom_at(p) for p in poly) if not use_cap
                             else tuple(z_max for _ in poly))
                    tops=tuple(top_at(p) for p in poly)
                    if all(t-b>=-EPS_LENGTH for b,t in zip(bottoms,tops)) \
                            and any(t-b>EPS_LENGTH for b,t in zip(bottoms,tops)):
                        pieces.append(_variable_prism(
                            tuple(poly),bottoms,tops,
                            fragment.part_type,fragment.ordinal))
    # Preserve bit-identical source authority at every surviving original
    # vertex; only genuinely generated contour stations retain interpolation.
    canonical=[]
    for piece in pieces:
        restored=tuple(next((source for source in vertices
                             if math.dist(vertex,source)<=EPS_LENGTH),vertex)
                       for vertex in piece.vertices)
        rebuilt=MeshFragment(piece.part_type,piece.ordinal,restored,piece.faces)
        validate_mesh_fragments((rebuilt,)); canonical.append(rebuilt)
    return tuple(canonical)


def build_high_side_closure_fragment(frame, relief, z_entry, z_exit,
                                     ordinal=11999):
    """Emit a closed local wedge owning the exact A_low/A_high/J_high face."""
    low, high = sorted((float(z_entry), float(z_exit)))
    high_point = relief.exit if z_exit >= z_entry else relief.entry
    other = relief.entry if z_exit >= z_entry else relief.exit
    vertices = ((frame.inner_pivot[0], frame.inner_pivot[1], low),
                (frame.inner_pivot[0], frame.inner_pivot[1], high),
                (high_point[0], high_point[1], high),
                (other[0], other[1], low))
    faces = ((0, 2, 1), (0, 3, 2), (0, 1, 3), (1, 2, 3))
    if _signed_volume(vertices, faces) < 0.0:
        faces = tuple(tuple(reversed(face)) for face in faces)
    fragment = MeshFragment("UNDERBODY", ordinal, vertices, faces)
    validate_mesh_fragments((fragment,))
    return fragment


def build_pivot_core_fragment(frame, stations, contact_zs,
                              ordinal=11999):
    """Build one closed pivot core from shared soffit/contact stations.

    ``stations`` supplies the visible-soffit ``P_k`` vertices and
    ``contact_zs`` supplies the physical-contact ``C_k`` heights used by the
    adjacent strips.  Keeping these as inputs (rather than inventing a core
    thickness) makes both sides of every core/strip interface bit-identical.
    """
    stations=tuple(stations)
    contact_zs=tuple(float(value) for value in contact_zs)
    if len(stations)<2: raise ValueError("GEOMETRY_INVALID: pivot stations")
    if len(contact_zs)!=len(stations):
        raise ValueError("GEOMETRY_INVALID: pivot contact stations")
    if any(contact<=station.z+EPS_LENGTH
           for station,contact in zip(stations,contact_zs)):
        raise ValueError("GEOMETRY_INVALID: pivot contact clearance")
    z0,zn=stations[0].z,stations[-1].z
    low,high=min(z0,zn),max(z0,zn)
    bottom=[(frame.inner_pivot[0],frame.inner_pivot[1],low)]
    bottom.extend((s.inner[0],s.inner[1],s.z) for s in stations)
    top=[(frame.inner_pivot[0],frame.inner_pivot[1],high)]
    top.extend((s.inner[0],s.inner[1],contact)
               for s,contact in zip(stations,contact_zs))
    vertices=tuple(bottom+top); count=len(bottom); faces=[]
    for k in range(1,count-1):
        faces.append((0,k+1,k))
        faces.append((count,count+k,count+k+1))
        faces.append((k,k+1,count+k+1,count+k))
    # End sides. Split the high side so A_low/A_high/J_high is an explicit,
    # uniquely owned semantic triangle.
    high_index=1 if z0>=zn else count-1
    low_index=count-1 if high_index==1 else 1
    faces.append((0,low_index,count+low_index,count))
    faces.append((0,count,high_index))
    faces.append((high_index,count,count+high_index))
    center=tuple(sum(v[i] for v in vertices)/len(vertices) for i in range(3))
    oriented=[]
    for face in faces:
        a,b,c=(vertices[face[i]] for i in range(3))
        ab=tuple(b[i]-a[i] for i in range(3));ac=tuple(c[i]-a[i] for i in range(3))
        normal=(ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0])
        fc=tuple(sum(vertices[j][i] for j in face)/len(face) for i in range(3))
        if sum(normal[i]*(fc[i]-center[i]) for i in range(3))<0:
            face=tuple(reversed(face))
        oriented.append(face)
    faces=oriented
    fragment=MeshFragment("UNDERBODY",ordinal,vertices,tuple(faces))
    validate_mesh_fragments((fragment,))
    return fragment


def build_winder_side_board_fragments(frame, cells, tread_tops, stations,
                                      lower_zs, side, ascent_direction,
                                      thickness, reveal, mode,
                                      ordinal_start=12000):
    """Build an enabled uphill-relative ordinary Winder Side Board.

    The lower values are the exact resolved underbody station values.  Upper
    values are independently obtained from the destination walking surfaces.
    """
    world_side = world_side_for_uphill(side, ascent_direction)
    effective_theta = frame.theta if ascent_direction == "FORWARD" else -frame.theta
    inner_world_side = "LEFT" if effective_theta > 0.0 else "RIGHT"
    use_inner = world_side == inner_world_side
    points = tuple(station.inner if use_inner else station.outer
                   for station in stations)
    lower = tuple(float(value) for value in lower_zs)
    walking = []
    for station in stations:
        middle = min(max(station.fraction, 0.0), 1.0 - 1e-12)
        cell_index = next(i for i, cell in enumerate(cells)
                          if cell.front_fraction - 1e-9 <= middle
                          <= cell.rear_fraction + 1e-9)
        walking.append(float(tread_tops[cell_index]) + float(reveal))
    if mode == "SLOPED":
        upper = tuple(walking[0] + station.fraction *
                      (walking[-1] - walking[0]) for station in stations)
    else:
        upper = tuple(walking)
    if len(points) != len(lower):
        raise ValueError("GEOMETRY_INVALID: Side Board lower station mismatch")
    return tuple(_edge_board_fragment(
        points[index], points[index + 1], lower[index], lower[index + 1],
        upper[index], upper[index + 1], thickness, ordinal_start + index)
        for index in range(len(points) - 1))


def build_stepped_underbody_fragments(plans, ordinal_start=10000):
    """Build one closed union shell with destination-owned dividers.

    Horizontal soffit/contact polygons remain one-per-cell.  Plan edges are
    then reconciled globally: an exterior edge receives its full wall, while
    a two-cell divider receives only the symmetric difference of the two
    vertical intervals.  Consequently coincident interval area is internal
    (and absent), an equal-level divider is absent, and every exposed level
    difference is emitted exactly once using the owning cell's winding.
    """
    plans=tuple(plans)
    if not plans:
        return ()
    vertices=[]; vertex_index={}; faces=[]; edge_incidents={}
    def vertex(point):
        point=tuple(float(value) for value in point)
        if point not in vertex_index:
            vertex_index[point]=len(vertices); vertices.append(point)
        return vertex_index[point]
    for plan in plans:
        polygon=tuple(plan.polygon)
        if len(polygon)<3:
            raise ValueError("GEOMETRY_INVALID: stepped cell polygon")
        if sum(a[0]*b[1]-b[0]*a[1]
               for a,b in zip(polygon,polygon[1:]+polygon[:1]))<0.0:
            polygon=tuple(reversed(polygon))
        # Nominal cells are CCW; keep the full visible patch and contact patch.
        bottom=tuple(vertex((p[0],p[1],plan.visible_z)) for p in polygon)
        top=tuple(vertex((p[0],p[1],plan.top_z)) for p in polygon)
        faces.append(tuple(reversed(bottom)))
        faces.append(top)
        for a,b in zip(polygon,polygon[1:]+polygon[:1]):
            key=tuple(sorted((tuple(a),tuple(b))))
            edge_incidents.setdefault(key,[]).append(
                (tuple(a),tuple(b),float(plan.visible_z),float(plan.top_z)))
    for incidents in edge_incidents.values():
        if len(incidents)>2:
            raise ValueError("GEOMETRY_INVALID: non-manifold stepped divider")
        levels=sorted({z for incident in incidents for z in incident[2:]})
        for low,high in zip(levels,levels[1:]):
            if high-low<=EPS_LENGTH:
                continue
            middle=(low+high)/2.0
            owners=[incident for incident in incidents
                    if incident[2]+EPS_LENGTH<middle<incident[3]-EPS_LENGTH]
            if len(owners)==2:
                continue
            if len(owners)!=1:
                continue
            a,b,_bottom,_top=owners[0]
            faces.append((vertex((a[0],a[1],low)),
                          vertex((b[0],b[1],low)),
                          vertex((b[0],b[1],high)),
                          vertex((a[0],a[1],high))))
    fragment=MeshFragment("UNDERBODY",ordinal_start,tuple(vertices),tuple(faces))
    validate_mesh_fragments((fragment,))
    return (fragment,)


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
                                     ordinal_start=11000, z_entry=None,
                                     z_exit=None):
    """Build deterministic relief strips and a finite pivot-core solid."""
    if len(cells) != len(tread_tops):
        raise ValueError("GEOMETRY_INVALID: Winder cell/Z count mismatch")
    z0 = (stepped_patch_z(tread_tops[0], body_depth, base_z)
          if z_entry is None else float(z_entry))
    zn = (stepped_patch_z(tread_tops[-1], body_depth, base_z)
          if z_exit is None else float(z_exit))
    relief, stations = resolve_sloped_stations(
        frame, cells, z0, zn, riser_thickness)
    fragments = []
    def contact_at(fraction):
        if fraction <= 1e-12:
            return float(tread_tops[0]) - float(tread_thickness)
        if fraction >= 1.0 - 1e-12:
            return float(tread_tops[-1]) - float(tread_thickness)
        for boundary in range(1, len(cells)):
            if abs(fraction - cells[boundary].front_fraction) <= 1e-9:
                return (max(float(tread_tops[boundary - 1]),
                            float(tread_tops[boundary]))
                        - float(tread_thickness))
        cell_index = next(i for i, cell in enumerate(cells)
                          if cell.front_fraction - 1e-9 <= fraction
                          <= cell.rear_fraction + 1e-9)
        return float(tread_tops[cell_index]) - float(tread_thickness)
    for index, (a, b) in enumerate(zip(stations, stations[1:])):
        middle = (a.fraction + b.fraction) / 2.0
        cell_index = next(i for i, cell in enumerate(cells)
                          if cell.front_fraction - 1e-9 <= middle
                          <= cell.rear_fraction + 1e-9)
        contact_a, contact_b = contact_at(a.fraction), contact_at(b.fraction)
        if a.z >= contact_a - 1e-9 or b.z >= contact_b - 1e-9:
            raise ValueError("GEOMETRY_INVALID: Winder contact clearance")
        polygon = (a.inner, a.outer, b.outer, b.inner)
        fragments.append(_variable_prism(
            polygon, (a.z, a.z, b.z, b.z),
            (contact_a, contact_a, contact_b, contact_b),
            "UNDERBODY", ordinal_start + index))
    # A finite triangular core closes the pivot.  Its bottom is horizontal at
    # z_low; the explicit high-side triangle remains discoverable through
    # high_side_pivot_closure and its walls are part of this closed solid.
    # The finite tetrahedral core owns the high-side closure itself.  Do not
    # also emit the earlier overlapping triangular prism.
    contact_zs=tuple(contact_at(station.fraction) for station in stations)
    core=build_pivot_core_fragment(frame,stations,contact_zs,
                                   ordinal_start+99)
    fragments.append(core)
    return tuple(fragments), relief, stations, high_side_pivot_closure(
        frame, relief, z0, zn)
