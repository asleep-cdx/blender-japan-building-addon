"""Pure Straight/Turn terminal classification; this module creates no geometry."""
from dataclasses import dataclass
import math

from .stair_turn import EPS_LENGTH


COPLANAR_BODY_INTERFACE = "COPLANAR_BODY_INTERFACE"
RISER_MEDIATED_INTERFACE = "RISER_MEDIATED_INTERFACE"
PHYSICAL_CONTACT = "PHYSICAL_CONTACT"


@dataclass(frozen=True)
class PhysicalPlane:
    point: tuple
    normal: tuple


@dataclass(frozen=True)
class StraightTerminalStack:
    terminal_kind: str
    semantic_plane: PhysicalPlane
    underbody_plane: PhysicalPlane
    boundary_riser: object
    boundary_tread: object
    native_underbody: object
    riser_thickness: float
    forward: tuple
    left: tuple
    roles: tuple = ("RISER", "TREAD", "UNDERBODY")


@dataclass(frozen=True)
class TerminalInterfaceAuthority:
    interface_class: str
    source_identity: tuple
    destination_identity: tuple
    terminal_stack: StraightTerminalStack
    winder_port: object
    plane_offset: float
    contacts: tuple = ()


@dataclass(frozen=True)
class RiserMediatedInterfaceAuthority:
    direction: str
    source_identity: tuple
    destination_identity: tuple
    straight_stack: StraightTerminalStack
    source_terminal_tread: object
    destination_entry_tread: object
    destination_boundary_riser: object
    winder_underbodies: tuple
    semantic_segment: tuple
    contacts: tuple = ()
    intersection_volumes: tuple = ()


@dataclass(frozen=True)
class StraightComponentEvents:
    canonical_segment_index: int
    ascent_component_index: int
    start: tuple
    forward: tuple
    run_length: float
    tread_count: int
    first_rise_event: int
    last_rise_event: int
    first_tread_ordinal: int
    first_riser_ordinal: int
    final_tread_ordinal: int
    final_riser_ordinal: int


def straight_terminal_stack(kind, semantic_point, forward, left,
                            riser_thickness, boundary_riser, boundary_tread,
                            native_underbody):
    """Describe accepted terminal parts without moving any candidate vertex."""
    if kind not in ("ENTRY", "EXIT"):
        raise ValueError("GEOMETRY_INVALID: Straight terminal kind")
    def pair(value, label):
        try: result=tuple(float(item) for item in value)
        except (TypeError, ValueError, OverflowError):
            raise ValueError("GEOMETRY_INVALID: "+label) from None
        if len(result)!=2 or not all(math.isfinite(item) for item in result):
            raise ValueError("GEOMETRY_INVALID: "+label)
        return result
    semantic_point=pair(semantic_point,"Straight semantic point")
    forward=pair(forward,"Straight forward axis")
    left=pair(left,"Straight left axis")
    if (abs(math.hypot(*forward)-1.0)>EPS_LENGTH
            or abs(math.hypot(*left)-1.0)>EPS_LENGTH
            or abs(forward[0]*left[0]+forward[1]*left[1])>EPS_LENGTH):
        raise ValueError("GEOMETRY_INVALID: Straight terminal axes")
    r = float(riser_thickness)
    if not math.isfinite(r) or r <= EPS_LENGTH:
        raise ValueError("GEOMETRY_INVALID: Straight terminal thickness")
    required=((boundary_riser,"RISER"),(boundary_tread,"TREAD"),
              (native_underbody,"UNDERBODY"))
    if any(value is None or getattr(value,"part_type",None)!=role
           for value,role in required):
        raise ValueError("GEOMETRY_INVALID: Straight terminal role authority")
    sign = 1.0
    native_point = (float(semantic_point[0]) + sign * forward[0] * r,
                    float(semantic_point[1]) + sign * forward[1] * r)
    normal = (forward[0], forward[1])
    return StraightTerminalStack(
        kind, PhysicalPlane(semantic_point, normal),
        PhysicalPlane(native_point, normal), boundary_riser, boundary_tread,
        native_underbody, r, forward, left)


def classify_straight_winder_terminal(stack, winder_port,
                                      source_identity, destination_identity):
    """Straight/Winder is explicitly non-coplanar and Riser-mediated."""
    delta = (stack.underbody_plane.point[0] - stack.semantic_plane.point[0],
             stack.underbody_plane.point[1] - stack.semantic_plane.point[1])
    offset = abs(delta[0]*stack.forward[0] + delta[1]*stack.forward[1])
    if abs(offset-stack.riser_thickness) > EPS_LENGTH:
        raise ValueError("GEOMETRY_INVALID: Straight terminal plane offset")
    return TerminalInterfaceAuthority(
        RISER_MEDIATED_INTERFACE, source_identity, destination_identity,
        stack, winder_port, offset)


def straight_component_events(layout):
    """Return the exact ascent-local Straight mapping used by top production."""
    path=layout.canonical_path; payload=[]
    for index,(a,b) in enumerate(zip(path,path[1:])):
        dx,dy=b.xy[0]-a.xy[0],b.xy[1]-a.xy[1]
        length=math.hypot(dx,dy); direction=(dx/length,dy/length)
        cut=layout.turns[index-1].cutback if index else 0.0
        start=(a.xy[0]+direction[0]*cut,a.xy[1]+direction[1]*cut)
        payload.append(("STRAIGHT",index,(start,direction,
                        layout.straight_runs[index],layout.straight_allocation[index])))
        if index<len(layout.turn_specs):
            count=(layout.winder_counts[index]
                   if layout.turn_specs[index].turn_mode=="WINDER" else 1)
            payload.append(("TURN",index,count))
    if layout.ascent_direction=="REVERSE":
        reversed_payload=[]
        for kind,index,data in reversed(payload):
            if kind=="STRAIGHT":
                start,direction,run,count=data
                start=(start[0]+direction[0]*run,start[1]+direction[1]*run)
                data=(start,(-direction[0],-direction[1]),run,count)
            reversed_payload.append((kind,index,data))
        payload=reversed_payload
    ordinal=rise=component_index=0; result=[]
    for kind,index,data in payload:
        if kind=="TURN":
            rise+=data; ordinal+=2*data; component_index+=1; continue
        start,direction,run,count=data
        if count:
            result.append(StraightComponentEvents(
                index,component_index,start,direction,run,count,rise+1,rise+count,
                ordinal+1,ordinal+2,ordinal+2*count-1,ordinal+2*count))
            rise+=count;ordinal+=2*count
        component_index+=1
    return tuple(result)


def accepted_straight_underbody_candidate(layout, component, fields):
    """Adapt resolved schema-5 events to unchanged accepted 07-C authority."""
    from .stair_geometry import StairAxes, StairLayout
    from .stair_residential_geometry import build_underbody_fragment
    count=component.tread_count; h=layout.actual_riser
    upper=(component.start[0]+component.forward[0]*component.run_length,
           component.start[1]+component.forward[1]*component.run_length)
    local=StairLayout((component.start,upper),component.start,upper,
        StairAxes((*component.forward,0.0),
                  (-component.forward[1],component.forward[0],0.0)),
        layout.base_z+(component.first_rise_event-1)*h,(count+1)*h,
        layout.base_z+(component.first_rise_event+count)*h,
        component.run_length,count+1,count,h,component.run_length/count,
        layout.width,layout.tread_thickness,layout.riser_thickness)
    return local,build_underbody_fragment(local,fields)


def riser_mediated_interface_parts(layout, fragments, fields):
    """Bind both L-Winder interfaces to exact ascent-local emitted parts."""
    mappings=straight_component_events(layout)
    if len(mappings)!=2 or len(layout.turns)!=1:
        raise ValueError("GEOMETRY_INVALID: focused L terminal audit")
    before,after=mappings; by_key={(p.part_type,p.ordinal):p for p in fragments}
    def part(role,ordinal):
        try:return by_key[(role,ordinal)]
        except KeyError:raise ValueError("GEOMETRY_INVALID: emitted terminal part") from None
    before_tread=part("TREAD",before.final_tread_ordinal)
    before_riser=part("RISER",before.final_riser_ordinal)
    first_winder_tread=part("TREAD",before.final_riser_ordinal+1)
    first_winder_riser=part("RISER",before.final_riser_ordinal+2)
    last_winder_tread=part("TREAD",after.first_tread_ordinal-2)
    after_tread=part("TREAD",after.first_tread_ordinal)
    after_riser=part("RISER",after.first_riser_ordinal)
    _before_local,before_body=accepted_straight_underbody_candidate(
        layout,before,fields)
    _after_local,after_body=accepted_straight_underbody_candidate(layout,after,fields)
    frame=layout.turn
    before_stack=straight_terminal_stack(
        "EXIT",frame.inner_pivot,before.forward,
        (-before.forward[1],before.forward[0]),layout.riser_thickness,
        before_riser,before_tread,before_body)
    after_stack=straight_terminal_stack(
        "ENTRY",frame.inner_pivot,after.forward,
        (-after.forward[1],after.forward[0]),layout.riser_thickness,
        after_riser,after_tread,after_body)
    bodies=tuple(p for p in fragments if p.part_type=="UNDERBODY")
    return (
        RiserMediatedInterfaceAuthority(
            "STRAIGHT_TO_WINDER",("STRAIGHT",before.canonical_segment_index),
            ("WINDER",0),before_stack,before_tread,first_winder_tread,
            first_winder_riser,bodies,(frame.inner_pivot,frame.entry_outer)),
        RiserMediatedInterfaceAuthority(
            "WINDER_TO_STRAIGHT",("WINDER",0),
            ("STRAIGHT",after.canonical_segment_index),after_stack,
            last_winder_tread,after_tread,after_riser,bodies,
            (frame.inner_pivot,frame.exit_outer)))


def convex_polygon_intersection(subject, clip):
    """Exact deterministic Sutherland-Hodgman intersection for convex plans."""
    subject=list(subject); clip=list(clip)
    area=lambda p:sum(a[0]*b[1]-a[1]*b[0]
                      for a,b in zip(p,p[1:]+p[:1]))/2
    if area(clip)<0:clip.reverse()
    for a,b in zip(clip,clip[1:]+clip[:1]):
        output=[]
        for p,q in zip(subject,subject[1:]+subject[:1]):
            cross=lambda x:(b[0]-a[0])*(x[1]-a[1])-(b[1]-a[1])*(x[0]-a[0])
            ip,iq=cross(p)>=-EPS_LENGTH,cross(q)>=-EPS_LENGTH
            if ip:output.append(p)
            if ip!=iq:
                d=(q[0]-p[0],q[1]-p[1]);e=(b[0]-a[0],b[1]-a[1])
                den=d[0]*e[1]-d[1]*e[0]
                t=((a[0]-p[0])*e[1]-(a[1]-p[1])*e[0])/den
                output.append((p[0]+t*d[0],p[1]+t*d[1]))
        subject=output
        if not subject:break
    return tuple(subject)


def constant_prism_intersection_volume(plan_a,z_a,plan_b,z_b):
    polygon=convex_polygon_intersection(tuple(plan_a),tuple(plan_b))
    if len(polygon)<3:return 0.0
    area=abs(sum(a[0]*b[1]-a[1]*b[0]
                 for a,b in zip(polygon,polygon[1:]+polygon[:1]))/2)
    height=max(0.0,min(z_a[1],z_b[1])-max(z_a[0],z_b[0]))
    return area*height
