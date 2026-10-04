"""Pure schema-5 Residential body-component/interface authority."""
from dataclasses import dataclass
import math

from .stair_geometry import validate_simple_polygon
from .stair_geometry import MeshFragment, validate_mesh_fragments
from .stair_turn import EPS_AREA, EPS_LENGTH


@dataclass(frozen=True)
class ResidentialBodyPort:
    key: str
    local_segment: tuple
    segment: tuple
    q_direction: tuple
    profile_qz: tuple
    profile_xyz: tuple
    breakpoints: tuple


@dataclass(frozen=True)
class ResidentialBodyComponent:
    identity: tuple
    kind: str
    ascent_index: int
    authority: object
    body_fragments: tuple
    entry_port: object
    exit_port: object
    side_boards: tuple = ()
    entry_surface_ownership: object = None
    exit_surface_ownership: object = None


@dataclass(frozen=True)
class BodyInterfaceFrame:
    segment: tuple
    q_direction: tuple
    source_identity: tuple
    destination_identity: tuple


@dataclass(frozen=True)
class InterfaceStation:
    """A canonical interface split; XYZ is stored, never reconstructed later."""
    q: float
    z: float
    xyz: tuple
    tags: tuple = ()


@dataclass(frozen=True)
class BodyInterface:
    frame: BodyInterfaceFrame
    source_port: ResidentialBodyPort
    destination_port: ResidentialBodyPort
    q_stations: tuple
    z_stations: tuple
    grid_stations: tuple
    authority_stations: tuple
    semantic_stations: tuple
    overlap_cells: tuple
    source_only_cells: tuple
    destination_only_cells: tuple
    transition_cells: tuple
    closure_owner: object

    @property
    def breakpoints(self):
        """Compatibility alias for consumers migrating to full stations."""
        return self.semantic_stations

    @property
    def stations(self):
        """Compatibility name for the complete rectangular-algebra grid."""
        return self.grid_stations


@dataclass(frozen=True)
class PortSurfaceOwnership:
    """Exact pre-assembly cap ownership supplied by a component adapter."""
    component_identity: tuple
    port_key: str
    fragment_index: int
    face_indices: tuple
    port: ResidentialBodyPort


@dataclass(frozen=True)
class JoinedBodyResult:
    fragment: MeshFragment
    interfaces: tuple
    transition_owners: tuple


def _canonical_polygon(points):
    polygon = tuple(validate_simple_polygon(points))
    start = min(range(len(polygon)), key=lambda index: polygon[index])
    return polygon[start:] + polygon[:start]


def _rectilinear(profile):
    return all(abs(a[0] - b[0]) <= EPS_LENGTH
               or abs(a[1] - b[1]) <= EPS_LENGTH
               for a, b in zip(profile, profile[1:] + profile[:1]))


def _finite_pair(value, label):
    try:
        pair = tuple(value)
        if len(pair) != 2:
            raise ValueError
        pair = (float(pair[0]), float(pair[1]))
    except (TypeError, ValueError, OverflowError):
        raise ValueError("GEOMETRY_INVALID: " + label) from None
    if not all(math.isfinite(item) for item in pair):
        raise ValueError("GEOMETRY_INVALID: " + label)
    return pair


def body_port(key, segment, profile_qz, breakpoints=(), canonical_segment=None):
    """Create a validated rectilinear port and exact world XYZ authority."""
    try:
        local_a, local_b = (_finite_pair(point, "body port segment")
                            for point in tuple(segment))
    except (TypeError, ValueError):
        raise ValueError("GEOMETRY_INVALID: body port segment") from None
    canonical = segment if canonical_segment is None else canonical_segment
    try:
        a, b = (_finite_pair(point, "body port canonical segment")
                for point in tuple(canonical))
    except (TypeError, ValueError):
        raise ValueError("GEOMETRY_INVALID: body port canonical segment") from None
    length = math.dist(a, b)
    if length <= EPS_LENGTH:
        raise ValueError("GEOMETRY_INVALID: body port")
    direction = ((b[0] - a[0]) / length, (b[1] - a[1]) / length)
    direct = (math.dist(local_a, a) <= EPS_LENGTH
              and math.dist(local_b, b) <= EPS_LENGTH)
    reverse = (math.dist(local_a, b) <= EPS_LENGTH
               and math.dist(local_b, a) <= EPS_LENGTH)
    if not direct and not reverse:
        raise ValueError("GEOMETRY_INVALID: incompatible body port segment")
    transform = (lambda q: q) if direct else (lambda q: length - q)
    try:
        raw_profile = tuple(_finite_pair(point, "body port profile")
                            for point in profile_qz)
    except TypeError:
        raise ValueError("GEOMETRY_INVALID: body port profile") from None
    profile = _canonical_polygon(tuple((transform(q), z)
                                       for q, z in raw_profile))
    if not _rectilinear(profile):
        raise ValueError("GEOMETRY_INVALID: non-rectilinear body port")
    if any(q < -EPS_LENGTH or q > length + EPS_LENGTH for q, _z in profile):
        raise ValueError("GEOMETRY_INVALID: body port width")
    semantic = []
    try:
        for index, point in enumerate(breakpoints):
            values = tuple(point)
            q, z = _finite_pair(values[:2], "body port breakpoint")
            tag = str(values[2]) if len(values) == 3 else "%s:%d" % (key, index)
            if len(values) not in (2, 3):
                raise ValueError("GEOMETRY_INVALID: body port breakpoint")
            semantic.append((transform(q), z, tag))
    except TypeError:
        raise ValueError("GEOMETRY_INVALID: body port breakpoint") from None
    semantic = tuple(semantic)
    if any(q < -EPS_LENGTH or q > length + EPS_LENGTH for q, _z, _tag in semantic):
        raise ValueError("GEOMETRY_INVALID: body port breakpoint")
    xyz = tuple((a[0] + direction[0] * q, a[1] + direction[1] * q, z)
                for q, z in profile)
    return ResidentialBodyPort(str(key), (local_a, local_b), (a, b), direction,
                               profile, xyz, semantic)


def _inside(point, polygon):
    x, y = point
    inside = False
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        if (a[1] > y) != (b[1] > y):
            crossing = (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]
            if x < crossing:
                inside = not inside
    return inside


def _canonical_values(values):
    """Semantic-first, traversal-independent EPS clustering."""
    ordered = sorted((float(value), int(priority)) for value, priority in values)
    clusters = []
    for item in ordered:
        # Anchor each cluster at its minimum.  Comparing only with the prior
        # item would incorrectly chain 0, .9*EPS, and 1.8*EPS together.
        if not clusters or item[0] - clusters[-1][0][0] > EPS_LENGTH:
            clusters.append([item])
        else:
            clusters[-1].append(item)
    # Lower priority number is stronger; numeric minimum is the stable tie-break.
    return tuple(min(value for value, priority in cluster
                     if priority == min(item[1] for item in cluster))
                 for cluster in clusters)


def _snap(value, stations):
    candidates = tuple(station for station in stations
                       if abs(value - station) <= EPS_LENGTH)
    if not candidates:
        raise ValueError("GEOMETRY_INVALID: interface station cannot be snapped")
    return min(candidates, key=lambda station: (abs(value - station), station))


def _snap_port(port, qs, zs, segment, direction):
    profile = _canonical_polygon(tuple((_snap(q, qs), _snap(z, zs))
                                       for q, z in port.profile_qz))
    breaks = tuple((_snap(q, qs), _snap(z, zs), tag)
                   for q, z, tag in port.breakpoints)
    xyz = tuple((segment[0][0] + direction[0] * q,
                 segment[0][1] + direction[1] * q, z)
                for q, z in profile)
    return ResidentialBodyPort(port.key, port.local_segment, segment, direction,
                               profile, xyz, breaks)


def _normalize_port(port, canonical_segment):
    start, end = canonical_segment
    if not (math.dist(port.segment[0], start) <= EPS_LENGTH
            and math.dist(port.segment[1], end) <= EPS_LENGTH):
        raise ValueError("GEOMETRY_INVALID: incompatible body interface")
    width = math.dist(start, end)
    profile = port.profile_qz
    breaks = port.breakpoints
    direction = ((end[0] - start[0]) / width, (end[1] - start[1]) / width)
    xyz = tuple((start[0] + direction[0] * q,
                 start[1] + direction[1] * q, z) for q, z in profile)
    return ResidentialBodyPort(port.key, port.local_segment, canonical_segment,
                               direction, profile, xyz, breaks)


def resolve_body_interface(source, destination, canonical_segment=None):
    """Resolve exact rectilinear overlap and oriented symmetric difference."""
    sp, dp = source.exit_port, destination.entry_port
    if sp is None or dp is None:
        raise ValueError("GEOMETRY_INVALID: missing body port")
    if canonical_segment is None:
        segment = sp.segment
    else:
        try:
            segment = tuple(_finite_pair(point, "canonical interface segment")
                            for point in tuple(canonical_segment))
            if len(segment) != 2:
                raise ValueError
        except (TypeError, ValueError):
            raise ValueError("GEOMETRY_INVALID: canonical interface segment") from None
    if canonical_segment is None and sp.segment != dp.segment:
        raise ValueError("GEOMETRY_INVALID: explicit canonical interface required")
    sp = _normalize_port(sp, segment)
    dp = _normalize_port(dp, segment)
    semantic_by_tag = {}
    for port in (sp, dp):
        for q, z, tag in port.breakpoints:
            prior = semantic_by_tag.setdefault(tag, (q, z))
            if (abs(prior[0] - q) > EPS_LENGTH
                    or abs(prior[1] - z) > EPS_LENGTH):
                raise ValueError("GEOMETRY_INVALID: semantic station disagreement")
    tagged_q = ([(q, 1) for q, _z in sp.profile_qz]
                + [(q, 0) for q, _z, _tag in sp.breakpoints]
                + [(q, 1) for q, _z in dp.profile_qz]
                + [(q, 0) for q, _z, _tag in dp.breakpoints])
    tagged_z = ([(z, 1) for _q, z in sp.profile_qz]
                + [(z, 0) for _q, z, _tag in sp.breakpoints]
                + [(z, 1) for _q, z in dp.profile_qz]
                + [(z, 0) for _q, z, _tag in dp.breakpoints])
    qs, zs = _canonical_values(tagged_q), _canonical_values(tagged_z)
    direction = sp.q_direction
    sp = _snap_port(sp, qs, zs, segment, direction)
    dp = _snap_port(dp, qs, zs, segment, direction)
    world = lambda q, z: (segment[0][0] + direction[0] * q,
                          segment[0][1] + direction[1] * q, z)
    grid_stations = tuple(InterfaceStation(q, z, world(q, z))
                          for q in qs for z in zs)
    actual = []
    for port, side in ((sp, "SOURCE"), (dp, "DESTINATION")):
        actual.extend((_snap(q, qs), _snap(z, zs), side + "_PROFILE")
                      for q, z in port.profile_qz)
        actual.extend((_snap(q, qs), _snap(z, zs), side + "_SEMANTIC:" + tag)
                      for q, z, tag in port.breakpoints)
    grouped = {}
    for q, z, tag in actual:
        grouped.setdefault((q, z), set()).add(tag)
    authority_stations = tuple(InterfaceStation(q, z, world(q, z),
                                                tuple(sorted(tags)))
                               for (q, z), tags in sorted(grouped.items()))
    semantic_stations = tuple(station for station in authority_stations
                              if any("_SEMANTIC:" in tag for tag in station.tags))
    overlap, source_only, destination_only = [], [], []
    for q0, q1 in zip(qs, qs[1:]):
        if q1 - q0 <= EPS_LENGTH:
            continue
        for z0, z1 in zip(zs, zs[1:]):
            if z1 - z0 <= EPS_LENGTH or (q1-q0)*(z1-z0) <= EPS_AREA:
                continue
            mid = ((q0 + q1) / 2, (z0 + z1) / 2)
            occupied = (_inside(mid, sp.profile_qz), _inside(mid, dp.profile_qz))
            cell = (q0, q1, z0, z1)
            if occupied == (True, True):
                overlap.append(cell)
            elif occupied == (True, False):
                source_only.append(cell)
            elif occupied == (False, True):
                destination_only.append(cell)
    transition = tuple(source_only + destination_only)
    frame = BodyInterfaceFrame(segment, direction, source.identity,
                               destination.identity)
    return BodyInterface(frame, sp, dp, qs, zs, grid_stations,
                         authority_stations, semantic_stations, tuple(overlap),
                         tuple(source_only), tuple(destination_only), transition,
                         destination.identity if transition else None)


def _point_on_port_plane(point, port):
    a = port.segment[0]
    normal = (-port.q_direction[1], port.q_direction[0])
    return abs((point[0]-a[0])*normal[0]
               + (point[1]-a[1])*normal[1]) <= EPS_LENGTH


def port_surface_ownership(component, port_key):
    """Resolve cap faces once in the adapter, before interface assembly."""
    port = component.entry_port if port_key == "ENTRY" else component.exit_port
    if port is None:
        raise ValueError("GEOMETRY_INVALID: missing owned body port")
    matches = []
    for fragment_index, fragment in enumerate(component.body_fragments):
        indices = tuple(index for index, face in enumerate(fragment.faces)
                        if len(face) >= 3 and all(
                            _point_on_port_plane(fragment.vertices[vertex], port)
                            for vertex in face))
        if indices:
            matches.append((fragment_index, indices))
    if len(matches) != 1:
        raise ValueError("GEOMETRY_INVALID: body port cap ownership")
    fragment_index, faces = matches[0]
    return PortSurfaceOwnership(component.identity, port.key, fragment_index,
                                faces, port)


def _face_normal(vertices, face):
    a, b, c = (vertices[face[index]] for index in range(3))
    ab = tuple(b[index]-a[index] for index in range(3))
    ac = tuple(c[index]-a[index] for index in range(3))
    return (ab[1]*ac[2]-ab[2]*ac[1],
            ab[2]*ac[0]-ab[0]*ac[2],
            ab[0]*ac[1]-ab[1]*ac[0])


def join_body_component_surfaces(components, canonical_segments):
    """Consume BodyInterface authority and emit one welded UNDERBODY shell.

    Component adapters must provide one exact cap owner per internal port.
    This function removes both complete caps and reconstructs precisely the
    SOURCE_ONLY/DESTINATION_ONLY transition cells.  It never inspects Blender
    state and therefore remains candidate preparation.
    """
    components = tuple(components)
    if len(canonical_segments) != max(0, len(components)-1):
        raise ValueError("GEOMETRY_INVALID: body interface sequence")
    interfaces = tuple(resolve_body_interface(a, b, segment)
                       for a, b, segment in zip(
                           components, components[1:], canonical_segments))
    removals = {}
    ownership = []
    for index, interface in enumerate(interfaces):
        source_owner = components[index].exit_surface_ownership
        destination_owner = components[index+1].entry_surface_ownership
        if source_owner is None or destination_owner is None:
            raise ValueError("GEOMETRY_INVALID: explicit body port ownership")
        for component_index, owner in ((index, source_owner),
                                       (index+1, destination_owner)):
            key = (component_index, owner.fragment_index)
            removals.setdefault(key, set()).update(owner.face_indices)
        ownership.append((source_owner, destination_owner))

    vertices, faces, lookup = [], [], {}
    def vertex(point):
        key = tuple(float(value) for value in point)
        if key not in lookup:
            lookup[key] = len(vertices)
            vertices.append(key)
        return lookup[key]
    for component_index, component in enumerate(components):
        for fragment_index, fragment in enumerate(component.body_fragments):
            removed = removals.get((component_index, fragment_index), ())
            for face_index, face in enumerate(fragment.faces):
                if face_index not in removed:
                    faces.append(tuple(vertex(fragment.vertices[i]) for i in face))

    transition_owners = []
    for interface, (source_owner, destination_owner) in zip(interfaces, ownership):
        direction = interface.frame.q_direction
        origin = interface.frame.segment[0]
        # Component centroids select the physical source/destination half-space;
        # classification, not guessed Mesh normals, selects the desired side.
        def centroid(component):
            points = [point for fragment in component.body_fragments
                      for point in fragment.vertices]
            return tuple(sum(point[i] for point in points)/len(points)
                         for i in range(3))
        source_center = centroid(next(c for c in components
                                      if c.identity == interface.frame.source_identity))
        destination_center = centroid(next(c for c in components
                                           if c.identity == interface.frame.destination_identity))
        plane_normal = (-direction[1], direction[0], 0.0)
        source_sign = ((source_center[0]-origin[0])*plane_normal[0]
                       + (source_center[1]-origin[1])*plane_normal[1])
        destination_sign = ((destination_center[0]-origin[0])*plane_normal[0]
                            + (destination_center[1]-origin[1])*plane_normal[1])
        if source_sign*destination_sign >= -EPS_AREA:
            raise ValueError("GEOMETRY_INVALID: component interface sides")
        def emit(cell, toward_destination):
            q0, q1, z0, z1 = cell
            points = ((origin[0]+direction[0]*q0,origin[1]+direction[1]*q0,z0),
                      (origin[0]+direction[0]*q1,origin[1]+direction[1]*q1,z0),
                      (origin[0]+direction[0]*q1,origin[1]+direction[1]*q1,z1),
                      (origin[0]+direction[0]*q0,origin[1]+direction[1]*q0,z1))
            face = tuple(vertex(point) for point in points)
            desired = destination_sign if toward_destination else source_sign
            normal = _face_normal(vertices, face)
            actual = normal[0]*plane_normal[0]+normal[1]*plane_normal[1]
            if actual*desired < 0.0:
                face = tuple(reversed(face))
            faces.append(face)
        for cell in interface.source_only_cells:
            emit(cell, True)
        for cell in interface.destination_only_cells:
            emit(cell, False)
        transition_owners.extend(interface.closure_owner
                                 for _cell in interface.transition_cells)
    fragment = MeshFragment("UNDERBODY", 15000, tuple(vertices), tuple(faces))
    from .stair_winder_finish import propagate_semantic_edge_splits
    fragment = propagate_semantic_edge_splits((fragment,))[0]
    validate_mesh_fragments((fragment,))
    return JoinedBodyResult(fragment, interfaces, tuple(transition_owners))
