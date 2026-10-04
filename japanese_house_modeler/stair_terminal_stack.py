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


def straight_terminal_stack(kind, semantic_point, forward, left,
                            riser_thickness, boundary_riser, boundary_tread,
                            native_underbody):
    """Describe accepted terminal parts without moving any candidate vertex."""
    if kind not in ("ENTRY", "EXIT"):
        raise ValueError("GEOMETRY_INVALID: Straight terminal kind")
    r = float(riser_thickness)
    if not math.isfinite(r) or r <= EPS_LENGTH:
        raise ValueError("GEOMETRY_INVALID: Straight terminal thickness")
    forward = tuple(map(float, forward)); left = tuple(map(float, left))
    if len(forward) != 2 or len(left) != 2:
        raise ValueError("GEOMETRY_INVALID: Straight terminal axes")
    sign = 1.0
    native_point = (float(semantic_point[0]) + sign * forward[0] * r,
                    float(semantic_point[1]) + sign * forward[1] * r)
    normal = (forward[0], forward[1])
    return StraightTerminalStack(
        kind, PhysicalPlane(tuple(map(float, semantic_point)), normal),
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
