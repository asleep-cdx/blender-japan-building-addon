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
