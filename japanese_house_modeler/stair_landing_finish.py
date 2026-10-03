"""Pure Build 07-E generalized Landing Residential finish authority."""

from dataclasses import dataclass
import math

from .stair_geometry import (MeshFragment, _signed_volume,
                             validate_mesh_fragments, validate_simple_polygon)
from .stair_turn import EPS_ANGLE, EPS_LENGTH


@dataclass(frozen=True)
class LandingBodyPort:
    name: str
    segment: tuple
    soffit_edge: tuple
    contact_edge: tuple
    stations: tuple


@dataclass(frozen=True)
class GeneralizedLandingFinishAuthority:
    footprint: tuple
    entry_interface: tuple
    exit_interface: tuple
    outer_chain: tuple
    z_top: float
    z_contact: float
    z_soffit: float
    z_slab_top: float
    a_entry: tuple
    a_exit: tuple
    o_inner: tuple
    cavity: tuple
    skirt: tuple
    board_footprint: tuple
    entry_port: LandingBodyPort
    exit_port: LandingBodyPort
    outside_side: str


def _cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def _scale(a, value):
    return (a[0] * value, a[1] * value)


def _unit(a):
    length = math.hypot(*a)
    if length <= EPS_LENGTH:
        raise ValueError("GEOMETRY_INVALID: Landing zero-length edge")
    return (a[0] / length, a[1] / length)


def _line_intersection(a, direction_a, b, direction_b):
    denominator = _cross(direction_a, direction_b)
    if abs(denominator) <= 1.0e-12:
        raise ValueError("GEOMETRY_INVALID: Landing offset intersection")
    distance = _cross(_sub(b, a), direction_b) / denominator
    point = _add(a, _scale(direction_a, distance))
    if not all(math.isfinite(value) for value in point):
        raise ValueError("GEOMETRY_INVALID: Landing offset coordinate")
    return point


def _convex(polygon):
    signs = []
    for a, b, c in zip(polygon, polygon[1:] + polygon[:1],
                       polygon[2:] + polygon[:2]):
        value = _cross(_sub(b, a), _sub(c, b))
        if abs(value) > 1.0e-12:
            signs.append(value > 0.0)
    return bool(signs) and all(value == signs[0] for value in signs)


def _offset_authority(semantic, distance, outward=False):
    footprint, i, entry, outer, exit_ = semantic
    first = _unit(_sub(outer, entry)); second = _unit(_sub(exit_, outer))
    raw_area = sum(a[0]*b[1]-b[0]*a[1]
                   for a,b in zip((i,entry,outer,exit_),
                                  (entry,outer,exit_,i)))
    inward = 1.0 if raw_area > 0.0 else -1.0
    sign = -inward if outward else inward
    n1 = _scale((-first[1], first[0]), sign * distance)
    n2 = _scale((-second[1], second[0]), sign * distance)
    line1 = _add(entry, n1); line2 = _add(outer, n2)
    a_entry = _line_intersection(i, _sub(entry, i), line1, first)
    a_exit = _line_intersection(i, _sub(exit_, i), line2, second)
    corner = _line_intersection(line1, first, line2, second)
    return a_entry, a_exit, corner


def _point_in_convex(point, polygon, eps=EPS_LENGTH):
    return all(_cross(_sub(b, a), _sub(point, a)) >= -eps
               for a, b in zip(polygon, polygon[1:] + polygon[:1]))


def resolve_generalized_landing_finish(frame, width, z_top, base_z,
                                       tread_thickness, riser_thickness,
                                       body_depth, underside_thickness,
                                       board_thickness=0.0,
                                       board_reveal=0.0,
                                       underside_mode="STEPPED_CLOSED",
                                       ascent_direction="FORWARD"):
    """Resolve immutable non-right Landing plan/Z/port authority."""
    if ascent_direction not in ("FORWARD","REVERSE"):
        raise ValueError("GEOMETRY_INVALID: Landing ascent direction")
    entry_outer,exit_outer=(
        (frame.entry_outer,frame.exit_outer) if ascent_direction=="FORWARD"
        else (frame.exit_outer,frame.entry_outer))
    raw = (tuple(frame.inner_pivot), tuple(entry_outer),
           tuple(frame.outer_corner), tuple(exit_outer))
    footprint = validate_simple_polygon(raw)
    if not _convex(footprint):
        raise ValueError("GEOMETRY_INVALID: Landing envelope must be convex")
    i, entry, outer, exit_ = raw
    if (abs(math.dist(i, entry) - float(width)) > EPS_LENGTH
            or abs(math.dist(i, exit_) - float(width)) > EPS_LENGTH):
        raise ValueError("GEOMETRY_INVALID: Landing interface width")
    semantic=(footprint,i,entry,outer,exit_)
    a_entry, a_exit, o_inner = _offset_authority(
        semantic, float(riser_thickness))
    if not _point_in_convex(o_inner, footprint):
        raise ValueError("GEOMETRY_INVALID: Landing inner corner")
    cavity = validate_simple_polygon((i, a_entry, o_inner, a_exit))
    skirt = validate_simple_polygon(
        (entry, outer, exit_, a_exit, o_inner, a_entry))
    board = ()
    if float(board_thickness) > 0.0:
        b_entry, b_exit, o_outer = _offset_authority(
            semantic, float(board_thickness), outward=True)
        board = validate_simple_polygon(
            (b_entry, o_outer, b_exit, exit_, outer, entry))
    z_top = float(z_top); z_contact = z_top - float(tread_thickness)
    z_soffit = max(float(base_z), z_top - float(body_depth))
    z_slab_top = z_soffit + float(underside_thickness)
    if z_soffit >= z_contact - EPS_LENGTH:
        raise ValueError("GEOMETRY_INVALID: Landing body clearance")
    if (underside_mode == "SLOPED_CLOSED"
            and not z_soffit + EPS_LENGTH < z_slab_top < z_contact - EPS_LENGTH):
        raise ValueError("GEOMETRY_INVALID: Landing slab clearance")
    def port(name, end, breakpoint):
        contact = ((i[0], i[1], z_contact),
                   (end[0], end[1], z_contact))
        soffit = ((i[0], i[1], z_soffit),
                  (end[0], end[1], z_soffit))
        stations = (i, breakpoint, end) if underside_mode == "SLOPED_CLOSED" else (i, end)
        return LandingBodyPort(name, (i, end), soffit, contact, stations)
    cross = _cross(_sub(entry, i), _sub(exit_, i))
    outside = "RIGHT" if cross > 0.0 else "LEFT"
    return GeneralizedLandingFinishAuthority(
        footprint, (i, entry), (i, exit_), (entry, outer, exit_),
        z_top, z_contact, z_soffit, z_slab_top, a_entry, a_exit,
        o_inner, cavity, skirt, board, port("ENTRY", entry, a_entry),
        port("EXIT", exit_, a_exit), outside)


def _prism(polygon, bottom, top, part_type, ordinal):
    polygon = validate_simple_polygon(polygon); count = len(polygon)
    vertices = tuple((p[0], p[1], z) for z in (bottom, top) for p in polygon)
    faces = [tuple(reversed(range(count))), tuple(range(count, 2 * count))]
    faces.extend((i, (i + 1) % count, (i + 1) % count + count, i + count)
                 for i in range(count))
    if _signed_volume(vertices, faces) < 0.0:
        faces = [tuple(reversed(face)) for face in faces]
    result = MeshFragment(part_type, ordinal, vertices, tuple(faces))
    validate_mesh_fragments((result,))
    return result


def build_generalized_landing_body(authority, underside_mode):
    """Build closed non-right Landing UNDERBODY candidate fragments."""
    if underside_mode == "STEPPED_CLOSED":
        return (_prism(authority.footprint, authority.z_soffit,
                       authority.z_contact, "UNDERBODY", 17000),)
    i,entry,outer,exit_=authority.entry_interface[0],authority.entry_interface[1],authority.outer_chain[1],authority.exit_interface[1]
    slab=validate_simple_polygon((i,authority.a_entry,entry,outer,exit_,
                                  authority.a_exit))
    skirt=authority.skirt; cavity=authority.cavity
    vertices=[]; lookup={}; faces=[]
    def vertex(point,z):
        key=(point[0],point[1],z)
        if key not in lookup: lookup[key]=len(vertices);vertices.append(key)
        return lookup[key]
    bottom=tuple(vertex(p,authority.z_soffit) for p in slab)
    slab_top=tuple(vertex(p,authority.z_slab_top) for p in slab)
    faces.append(tuple(reversed(bottom)))
    faces.extend((bottom[j],bottom[(j+1)%len(slab)],
                  slab_top[(j+1)%len(slab)],slab_top[j])
                 for j in range(len(slab)))
    skirt_bottom=tuple(vertex(p,authority.z_slab_top) for p in skirt)
    skirt_top=tuple(vertex(p,authority.z_contact) for p in skirt)
    faces.append(skirt_top)
    faces.extend((skirt_bottom[j],skirt_bottom[(j+1)%len(skirt)],
                  skirt_top[(j+1)%len(skirt)],skirt_top[j])
                 for j in range(len(skirt)))
    faces.append(tuple(vertex(p,authority.z_slab_top) for p in cavity))
    fragment=MeshFragment("UNDERBODY",17000,tuple(vertices),tuple(faces))
    if _signed_volume(fragment.vertices,fragment.faces)<0:
        fragment=MeshFragment(fragment.part_type,fragment.ordinal,
                              fragment.vertices,
                              tuple(tuple(reversed(face)) for face in fragment.faces))
    validate_mesh_fragments((fragment,))
    return (fragment,)


def build_generalized_landing_side_board(authority, enabled, reveal,
                                         ordinal=17100):
    if not enabled or not authority.board_footprint:
        return ()
    return (_prism(authority.board_footprint, authority.z_soffit,
                   authority.z_top + float(reveal), "SIDE_BOARD", ordinal),)


def prepare_generalized_landing_finish(frame, *, exact90_oracle=None, **values):
    """Dispatch exact-90 to the accepted oracle; otherwise build pure 07-E."""
    if abs(abs(frame.theta) - math.pi / 2.0) <= EPS_ANGLE:
        if exact90_oracle is None:
            raise ValueError("GEOMETRY_INVALID: exact-90 Landing oracle required")
        return exact90_oracle()
    authority = resolve_generalized_landing_finish(frame, **values)
    body = build_generalized_landing_body(authority, values["underside_mode"])
    board = build_generalized_landing_side_board(
        authority, values.get("board_enabled", False),
        values.get("board_reveal", 0.0))
    return authority, body + board
