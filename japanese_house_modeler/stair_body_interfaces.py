"""Pure schema-5 Residential body-component/interface authority."""
from dataclasses import dataclass
import math

from .stair_geometry import validate_simple_polygon
from .stair_turn import EPS_AREA, EPS_LENGTH


@dataclass(frozen=True)
class ResidentialBodyPort:
    key: str
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
    stations: tuple
    overlap_cells: tuple
    source_only_cells: tuple
    destination_only_cells: tuple
    transition_cells: tuple
    closure_owner: object

    @property
    def breakpoints(self):
        """Compatibility alias for consumers migrating to full stations."""
        return self.stations


def _canonical_polygon(points):
    polygon = tuple(validate_simple_polygon(points))
    start = min(range(len(polygon)), key=lambda index: polygon[index])
    return polygon[start:] + polygon[:start]


def _rectilinear(profile):
    return all(abs(a[0] - b[0]) <= EPS_LENGTH
               or abs(a[1] - b[1]) <= EPS_LENGTH
               for a, b in zip(profile, profile[1:] + profile[:1]))


def body_port(key, segment, profile_qz, breakpoints=()):
    """Create a validated rectilinear port and exact world XYZ authority."""
    a, b = map(tuple, segment)
    length = math.dist(a, b)
    if length <= EPS_LENGTH:
        raise ValueError("GEOMETRY_INVALID: body port")
    direction = ((b[0] - a[0]) / length, (b[1] - a[1]) / length)
    profile = _canonical_polygon(tuple((float(q), float(z))
                                       for q, z in profile_qz))
    if not _rectilinear(profile):
        raise ValueError("GEOMETRY_INVALID: non-rectilinear body port")
    if any(q < -EPS_LENGTH or q > length + EPS_LENGTH for q, _z in profile):
        raise ValueError("GEOMETRY_INVALID: body port width")
    semantic = tuple((float(q), float(z)) for q, z in breakpoints)
    if any(q < -EPS_LENGTH or q > length + EPS_LENGTH for q, _z in semantic):
        raise ValueError("GEOMETRY_INVALID: body port breakpoint")
    xyz = tuple((a[0] + direction[0] * q, a[1] + direction[1] * q, z)
                for q, z in profile)
    return ResidentialBodyPort(str(key), (a, b), direction, profile, xyz,
                               semantic)


def _inside(point, polygon):
    x, y = point
    inside = False
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        if (a[1] > y) != (b[1] > y):
            crossing = (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]
            if x < crossing:
                inside = not inside
    return inside


def _canonical_values(tagged):
    """Deduplicate within EPS; input order gives semantic precedence."""
    result = []
    for value, _tag in tagged:
        if not any(abs(value - retained) <= EPS_LENGTH for retained in result):
            result.append(float(value))
    return tuple(sorted(result))


def _snap(value, stations):
    return next(station for station in stations
                if abs(value - station) <= EPS_LENGTH)


def _snap_port(port, qs, zs, segment, direction):
    profile = _canonical_polygon(tuple((_snap(q, qs), _snap(z, zs))
                                       for q, z in port.profile_qz))
    breaks = tuple((_snap(q, qs), _snap(z, zs))
                   for q, z in port.breakpoints)
    xyz = tuple((segment[0][0] + direction[0] * q,
                 segment[0][1] + direction[1] * q, z)
                for q, z in profile)
    return ResidentialBodyPort(port.key, segment, direction, profile, xyz,
                               breaks)


def _normalize_port(port, canonical_segment):
    start, end = canonical_segment
    direct = (math.dist(port.segment[0], start) <= EPS_LENGTH
              and math.dist(port.segment[1], end) <= EPS_LENGTH)
    reverse = (math.dist(port.segment[0], end) <= EPS_LENGTH
               and math.dist(port.segment[1], start) <= EPS_LENGTH)
    if not direct and not reverse:
        raise ValueError("GEOMETRY_INVALID: incompatible body interface")
    width = math.dist(start, end)
    transform = (lambda q: q) if direct else (lambda q: width - q)
    profile = _canonical_polygon(tuple((transform(q), z)
                                       for q, z in port.profile_qz))
    breaks = tuple((transform(q), z) for q, z in port.breakpoints)
    direction = ((end[0] - start[0]) / width, (end[1] - start[1]) / width)
    xyz = tuple((start[0] + direction[0] * q,
                 start[1] + direction[1] * q, z) for q, z in profile)
    return ResidentialBodyPort(port.key, canonical_segment, direction,
                               profile, xyz, breaks)


def resolve_body_interface(source, destination):
    """Resolve exact rectilinear overlap and oriented symmetric difference."""
    sp, dp = source.exit_port, destination.entry_port
    if sp is None or dp is None:
        raise ValueError("GEOMETRY_INVALID: missing body port")
    # Source's semantic inner->outer authority has precedence for sub-EPS
    # endpoint differences; destination may describe the segment in reverse.
    segment = sp.segment
    sp = _normalize_port(sp, segment)
    dp = _normalize_port(dp, segment)
    tagged_q = ([(q, "SOURCE_PROFILE") for q, _z in sp.profile_qz]
                + [(q, "SOURCE_SEMANTIC") for q, _z in sp.breakpoints]
                + [(q, "DESTINATION_PROFILE") for q, _z in dp.profile_qz]
                + [(q, "DESTINATION_SEMANTIC") for q, _z in dp.breakpoints])
    tagged_z = ([(z, "SOURCE_PROFILE") for _q, z in sp.profile_qz]
                + [(z, "SOURCE_SEMANTIC") for _q, z in sp.breakpoints]
                + [(z, "DESTINATION_PROFILE") for _q, z in dp.profile_qz]
                + [(z, "DESTINATION_SEMANTIC") for _q, z in dp.breakpoints])
    qs, zs = _canonical_values(tagged_q), _canonical_values(tagged_z)
    direction = sp.q_direction
    sp = _snap_port(sp, qs, zs, segment, direction)
    dp = _snap_port(dp, qs, zs, segment, direction)
    stations = tuple(InterfaceStation(
        q, z, (segment[0][0] + direction[0] * q,
               segment[0][1] + direction[1] * q, z),
        tuple(tag for value, tag in tagged_q if abs(value - q) <= EPS_LENGTH)
        + tuple(tag for value, tag in tagged_z if abs(value - z) <= EPS_LENGTH))
        for q in qs for z in zs)
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
    return BodyInterface(frame, sp, dp, qs, zs, stations, tuple(overlap),
                         tuple(source_only), tuple(destination_only), transition,
                         destination.identity if transition else None)
