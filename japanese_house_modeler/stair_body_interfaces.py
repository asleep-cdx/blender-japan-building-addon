"""Pure schema-5 Residential body-component/interface authority."""
from dataclasses import dataclass
import math

from .stair_geometry import validate_simple_polygon
from .stair_turn import EPS_LENGTH


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
class BodyInterface:
    frame: BodyInterfaceFrame
    source_port: ResidentialBodyPort
    destination_port: ResidentialBodyPort
    breakpoints: tuple
    overlap_cells: tuple
    transition_cells: tuple
    closure_owner: tuple


def body_port(key, segment, profile_qz, breakpoints=()):
    """Create a validated port and exact world XYZ profile."""
    a,b=map(tuple,segment); length=math.dist(a,b)
    if length<=EPS_LENGTH: raise ValueError("GEOMETRY_INVALID: body port")
    direction=((b[0]-a[0])/length,(b[1]-a[1])/length)
    profile=validate_simple_polygon(profile_qz)
    if any(q < -EPS_LENGTH or q > length+EPS_LENGTH for q,_z in profile):
        raise ValueError("GEOMETRY_INVALID: body port width")
    xyz=tuple((a[0]+direction[0]*q,a[1]+direction[1]*q,z)
              for q,z in profile)
    return ResidentialBodyPort(key,(a,b),direction,profile,xyz,
                               tuple(breakpoints))


def _inside(point, polygon):
    x,y=point; inside=False
    for a,b in zip(polygon,polygon[1:]+polygon[:1]):
        if (a[1]>y)!=(b[1]>y):
            crossing=(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]
            if x<crossing: inside=not inside
    return inside


def resolve_body_interface(source, destination):
    """Resolve exact orthogonal profile overlap/symmetric difference cells."""
    sp,dp=source.exit_port,destination.entry_port
    if sp is None or dp is None:
        raise ValueError("GEOMETRY_INVALID: missing body port")
    if not (math.dist(sp.segment[0],dp.segment[0])<=EPS_LENGTH
            and math.dist(sp.segment[1],dp.segment[1])<=EPS_LENGTH):
        raise ValueError("GEOMETRY_INVALID: incompatible body interface")
    qs=sorted({q for p in (sp.profile_qz,dp.profile_qz) for q,_z in p})
    zs=sorted({z for p in (sp.profile_qz,dp.profile_qz) for _q,z in p})
    overlap=[];transition=[]; breaks=[]
    for q in qs: breaks.append((q,sp.segment[0][0]+sp.q_direction[0]*q,
                                sp.segment[0][1]+sp.q_direction[1]*q))
    for q0,q1 in zip(qs,qs[1:]):
        for z0,z1 in zip(zs,zs[1:]):
            mid=((q0+q1)/2,(z0+z1)/2)
            s,d=_inside(mid,sp.profile_qz),_inside(mid,dp.profile_qz)
            cell=(q0,q1,z0,z1)
            if s and d: overlap.append(cell)
            elif s != d: transition.append(cell)
    frame=BodyInterfaceFrame(sp.segment,sp.q_direction,source.identity,
                             destination.identity)
    return BodyInterface(frame,sp,dp,tuple(breaks),tuple(overlap),
                         tuple(transition),destination.identity)
