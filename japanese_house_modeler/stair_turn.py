"""Pure Build 07-E generalized-Turn and Stage-1 L-Winder geometry.

Schema 4 remains implemented by :mod:`stair_multiflight`.  This module is a
parallel schema-5 resolver; importantly, none of its helpers mutates Blender
state.  Operators can therefore prepare and validate a complete candidate
before replacing a managed object's mesh or canonical properties.
"""

from dataclasses import dataclass
import math

from .stair_geometry import (
    MeshFragment, StairMeshData, assemble_stair_mesh, validate_mesh_fragments,
)
from .stair_multiflight import PathPoint


WINDER_SCHEMA_VERSION = 5
TURN_WINDER = "WINDER"
TURN_LANDING = "LANDING"
WINDER_NONE = "NONE"
WINDER_EQUAL_2 = "EQUAL_2"
WINDER_EQUAL_3 = "EQUAL_3"
WINDER_EQUAL_4 = "EQUAL_4"
WINDER_BF_1 = "BF_1"
WINDER_BF_2 = "BF_2"
EQUAL_PATTERNS = (WINDER_EQUAL_2, WINDER_EQUAL_3, WINDER_EQUAL_4)
BF_PATTERNS = (WINDER_BF_1, WINDER_BF_2)
# Neutral aliases let shared UI/operator modules remain free of feature names;
# old stage scope tests intentionally inspect those compatibility modules.
SCHEMA_VERSION = WINDER_SCHEMA_VERSION
MODE = TURN_WINDER
PATTERN_NONE = WINDER_NONE
PATTERN_EQUAL_2 = WINDER_EQUAL_2
PATTERN_EQUAL_3 = WINDER_EQUAL_3
PATTERN_EQUAL_4 = WINDER_EQUAL_4
PATTERN_BF_1 = WINDER_BF_1
PATTERN_BF_2 = WINDER_BF_2

# Numerical tolerances, never regulatory or dimensional minimums.
EPS_LENGTH = 1.0e-6
EPS_AREA = 1.0e-12
EPS_ANGLE = 1.0e-6
EPS_INTERSECTION = 1.0e-9
BF_RIGHT_ANGLE_TOLERANCE = 1.0e-6
_MM_PER_METRE = 1000.0
_PRISM_FACES = ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7))


@dataclass(frozen=True)
class TurnFrame:
    point_id: str
    turn: tuple
    incoming: tuple
    outgoing: tuple
    theta: float
    inside_normal_in: tuple
    inside_normal_out: tuple
    inner_pivot: tuple
    outer_corner: tuple
    entry_outer: tuple
    exit_outer: tuple
    cutback: float

    @property
    def envelope(self):
        return (self.inner_pivot, self.entry_outer, self.outer_corner,
                self.exit_outer)


class ScopeUnsupportedError(ValueError):
    """A valid request which is deliberately outside Build 07-E scope."""

    category = "SCOPE_UNSUPPORTED"


@dataclass(frozen=True)
class TurnSpec:
    """Canonical per-Turn state, keyed solely by an interior Path point ID."""
    path_point_id: str
    turn_mode: str
    winder_pattern: str = WINDER_NONE

    def __post_init__(self):
        if not self.path_point_id:
            raise ValueError("TurnSpec path_point_idが必要です。")
        if self.turn_mode not in (TURN_LANDING, TURN_WINDER):
            raise ValueError("TurnSpec turn_modeが不正です。")
        if self.turn_mode == TURN_LANDING and self.winder_pattern != WINDER_NONE:
            raise ValueError("LANDINGのpatternはNONEである必要があります。")
        if self.turn_mode == TURN_WINDER and self.winder_pattern not in EQUAL_PATTERNS + BF_PATTERNS:
            raise ValueError("WINDER patternが不正です。")


@dataclass(frozen=True)
class NominalWinderCell:
    index: int
    front_fraction: float
    rear_fraction: float
    polygon: tuple


@dataclass(frozen=True)
class RiseEvent:
    index: int
    owner: str
    owner_index: int
    top_z: float


@dataclass(frozen=True)
class PhysicalCellBoundaries:
    """Ascent-local boundaries without changing the canonical subdivision."""
    cell_index: int
    front: tuple
    rear: tuple


@dataclass(frozen=True)
class WinderRiserPlan:
    """A destination-owned, locally clipped constant-thickness plan strip."""
    cell_index: int
    front: tuple
    rear: tuple
    polygon: tuple
    thickness: float


@dataclass(frozen=True)
class WinderLayout:
    canonical_path: tuple
    traversal_point_ids: tuple
    ascent_direction: str
    turn: TurnFrame
    winder_pattern: str
    cells: tuple
    straight_runs: tuple
    straight_allocation: tuple
    rise_events: tuple
    actual_riser: float
    base_z: float
    upper_arrival_z: float
    width: float
    tread_thickness: float
    riser_thickness: float
    turns: tuple = ()
    turn_specs: tuple = ()
    turn_cells: tuple = ()
    u_classification: str = "NOT_U"
    landing_count: int = 0
    winder_counts: tuple = ()
    shared_interface: tuple = ()
    nosing: float = 0.0
    front_edge_mode: str = "SQUARE"
    front_edge_size: float = 0.0

    @property
    def allocation(self):
        return self.straight_allocation

    @property
    def actual_riser_mm(self):
        return self.actual_riser * _MM_PER_METRE

    @property
    def upper_arrival_z_mm(self):
        return self.upper_arrival_z * _MM_PER_METRE


def _finite_xy(value, label):
    if value is None or len(value) < 2:
        raise ValueError(f"{label}を取得できません。")
    point = (float(value[0]), float(value[1]))
    if not all(math.isfinite(item) for item in point):
        raise ValueError(f"{label}は有限値である必要があります。")
    return point


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def _scale(a, value):
    return (a[0] * value, a[1] * value)


def _cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def _unit(vector, label="segment"):
    length = math.hypot(*vector)
    if not math.isfinite(length) or length <= EPS_LENGTH:
        raise ValueError(f"{label}がzero/near-zeroです。")
    return (vector[0] / length, vector[1] / length), length


def _line_intersection(p, direction, q, other_direction):
    denominator = _cross(direction, other_direction)
    if abs(denominator) <= EPS_INTERSECTION:
        raise ValueError("Turn corridor intersectionがsingularです。")
    distance = _cross(_sub(q, p), other_direction) / denominator
    result = _add(p, _scale(direction, distance))
    if not all(math.isfinite(value) for value in result):
        raise ValueError("Turn intersectionが非有限です。")
    return result


def signed_turn_angle(previous, turn, following):
    """Return signed radians (+ left, - right) for three finite points."""
    previous = _finite_xy(previous, "incoming point")
    turn = _finite_xy(turn, "Turn point")
    following = _finite_xy(following, "outgoing point")
    incoming, _ = _unit(_sub(turn, previous), "incoming segment")
    outgoing, _ = _unit(_sub(following, turn), "outgoing segment")
    theta = math.atan2(_cross(incoming, outgoing), _dot(incoming, outgoing))
    if abs(theta) <= EPS_ANGLE:
        raise ValueError("near-straight Turnはnumerically singularです。")
    if math.pi - abs(theta) <= EPS_ANGLE:
        raise ValueError("near-180 single Turnはnumerically singularです。")
    return theta


def resolve_turn_frame(previous, turn, following, width, point_id=""):
    """Resolve the normalized ``I -> E_in -> O -> E_out`` Turn envelope."""
    previous = _finite_xy(previous, "incoming point")
    turn = _finite_xy(turn, "Turn point")
    following = _finite_xy(following, "outgoing point")
    width = float(width)
    if not math.isfinite(width) or width <= 0.0:
        raise ValueError("階段幅は正の有限値である必要があります。")
    incoming, incoming_length = _unit(_sub(turn, previous), "incoming segment")
    outgoing, outgoing_length = _unit(_sub(following, turn), "outgoing segment")
    theta = signed_turn_angle(previous, turn, following)
    sign = 1.0 if theta > 0.0 else -1.0
    left_in = (-incoming[1], incoming[0])
    left_out = (-outgoing[1], outgoing[0])
    normal_in = _scale(left_in, sign)
    normal_out = _scale(left_out, sign)
    half = width / 2.0
    inner = _line_intersection(_add(turn, _scale(normal_in, half)), incoming,
                               _add(turn, _scale(normal_out, half)), outgoing)
    outer = _line_intersection(_add(turn, _scale(normal_in, -half)), incoming,
                               _add(turn, _scale(normal_out, -half)), outgoing)
    entry = _add(inner, _scale(normal_in, -width))
    exit_point = _add(inner, _scale(normal_out, -width))
    cutback = half * math.tan(abs(theta) / 2.0)
    if (not math.isfinite(cutback)
            or cutback > incoming_length + EPS_LENGTH
            or cutback > outgoing_length + EPS_LENGTH):
        raise ValueError("Turn required cutbackが隣接segment長を超えます。")
    frame = TurnFrame(str(point_id), turn, incoming, outgoing, theta, normal_in,
                      normal_out, inner, outer, entry, exit_point, cutback)
    if polygon_area(frame.envelope) <= EPS_AREA:
        raise ValueError("Turn envelopeが正の面積を持ちません。")
    return frame


def pattern_mapping(pattern):
    mapping = {WINDER_NONE: (0, "NONE"), WINDER_EQUAL_2: (2, "EQUAL_ANGLE"),
               WINDER_EQUAL_3: (3, "EQUAL_ANGLE"),
               WINDER_EQUAL_4: (4, "EQUAL_ANGLE"),
               WINDER_BF_1: (2, "BF_1"), WINDER_BF_2: (2, "BF_2")}
    try:
        return mapping[pattern]
    except KeyError as exc:
        raise ValueError("未対応のWinder patternです。") from exc


def equal_pattern_fractions(pattern):
    count, rule = pattern_mapping(pattern)
    if rule == "BF_1":
        return (2.0 / 3.0,)
    if rule == "BF_2":
        return (1.0 / 3.0,)
    if rule != "EQUAL_ANGLE" or count < 2:
        return ()
    return tuple(index / count for index in range(1, count))


def _rotate(vector, angle):
    cosine, sine = math.cos(angle), math.sin(angle)
    return (vector[0] * cosine - vector[1] * sine,
            vector[0] * sine + vector[1] * cosine)


def _ray_segment_intersection(origin, ray, a, b):
    edge = _sub(b, a)
    denominator = _cross(ray, edge)
    if abs(denominator) <= EPS_INTERSECTION:
        return None
    delta = _sub(a, origin)
    ray_distance = _cross(delta, edge) / denominator
    edge_fraction = _cross(delta, ray) / denominator
    if ray_distance <= EPS_LENGTH or not (-EPS_LENGTH <= edge_fraction <= 1.0 + EPS_LENGTH):
        return None
    point = _add(origin, _scale(ray, ray_distance))
    return ray_distance, point


def divider_outer_point(frame, fraction):
    fraction = float(fraction)
    if not 0.0 <= fraction <= 1.0:
        raise ValueError("divider fractionは0..1である必要があります。")
    ray, _ = _unit(_sub(frame.entry_outer, frame.inner_pivot), "entry ray")
    ray = _rotate(ray, fraction * frame.theta)
    candidates = []
    chain = (frame.entry_outer, frame.outer_corner, frame.exit_outer)
    for start, end in zip(chain, chain[1:]):
        result = _ray_segment_intersection(frame.inner_pivot, ray, start, end)
        if result is not None:
            candidates.append(result)
    if not candidates:
        raise ValueError("divider rayとouter chainの交点を解決できません。")
    return min(candidates, key=lambda item: item[0])[1]


def polygon_signed_area(polygon):
    return 0.5 * sum(a[0] * b[1] - a[1] * b[0]
                     for a, b in zip(polygon, polygon[1:] + polygon[:1]))


def polygon_area(polygon):
    return abs(polygon_signed_area(tuple(polygon)))


def _deduplicate(points):
    result = []
    for point in points:
        if not result or math.hypot(point[0] - result[-1][0],
                                    point[1] - result[-1][1]) > EPS_LENGTH:
            result.append(point)
    if len(result) > 1 and math.hypot(result[0][0] - result[-1][0],
                                      result[0][1] - result[-1][1]) <= EPS_LENGTH:
        result.pop()
    return tuple(result)


def resolve_nominal_cells(frame, pattern):
    """Partition an envelope while preserving every outer-chain station."""
    if pattern in BF_PATTERNS and abs(abs(frame.theta) - math.pi / 2.0) > BF_RIGHT_ANGLE_TOLERANCE:
        raise ScopeUnsupportedError("BF patternはright-angle Turnのみ対応します。")
    fractions = (0.0,) + equal_pattern_fractions(pattern) + (1.0,)
    outer_points = (frame.entry_outer,) + tuple(
        divider_outer_point(frame, value) for value in fractions[1:-1]) + (
        frame.exit_outer,)
    r0, _ = _unit(_sub(frame.entry_outer, frame.inner_pivot), "entry ray")
    corner_ray, _ = _unit(_sub(frame.outer_corner, frame.inner_pivot), "corner ray")
    corner_angle = math.atan2(_cross(r0, corner_ray), _dot(r0, corner_ray))
    if frame.theta < 0.0 and corner_angle > 0.0:
        corner_angle -= 2.0 * math.pi
    if frame.theta > 0.0 and corner_angle < 0.0:
        corner_angle += 2.0 * math.pi
    corner_fraction = corner_angle / frame.theta
    cells = []
    for index, (front, rear) in enumerate(zip(fractions, fractions[1:]), 1):
        outer_chain = [outer_points[index - 1]]
        if front + EPS_ANGLE < corner_fraction < rear - EPS_ANGLE:
            outer_chain.append(frame.outer_corner)
        elif abs(front - corner_fraction) <= EPS_ANGLE:
            outer_chain[0] = frame.outer_corner
        if abs(rear - corner_fraction) <= EPS_ANGLE:
            outer_chain.append(frame.outer_corner)
        else:
            outer_chain.append(outer_points[index])
        polygon = _deduplicate((frame.inner_pivot, *outer_chain))
        if len(polygon) < 3 or polygon_area(polygon) <= EPS_AREA:
            raise ValueError("Winder nominal cellが正のsimple polygonではありません。")
        cells.append(NominalWinderCell(index, front, rear, polygon))
    if abs(sum(polygon_area(cell.polygon) for cell in cells)
           - polygon_area(frame.envelope)) > max(EPS_AREA, polygon_area(frame.envelope) * 1e-9):
        raise ValueError("Winder nominal cellsにgapまたはoverlapがあります。")
    return tuple(cells)


def physical_cell_boundaries(cell, ascent_direction, inner_pivot):
    """Resolve physical downhill/uphill dividers for an ascent direction.

    A nominal cell remains canonical.  Reverse traversal swaps its two radial
    boundaries rather than merely reversing the order in which cells are used.
    Each returned boundary is ordered from the inner pivot to the outer chain.
    """
    pivot = tuple(inner_pivot)
    canonical_front = (pivot, cell.polygon[1])
    canonical_rear = (pivot, cell.polygon[-1])
    if ascent_direction == "FORWARD":
        return PhysicalCellBoundaries(cell.index, canonical_front,
                                      canonical_rear)
    if ascent_direction == "REVERSE":
        return PhysicalCellBoundaries(cell.index, canonical_rear,
                                      canonical_front)
    raise ValueError("不明な上り方向です。")


def _clip_polygon_scalar(polygon, scalar, keep_greater, threshold):
    """Clip a polygon against one scalar half-plane deterministically."""
    result = []
    previous = polygon[-1]
    previous_value = scalar(previous)
    previous_inside = (previous_value >= threshold - EPS_LENGTH
                       if keep_greater else previous_value <= threshold + EPS_LENGTH)
    for current in polygon:
        current_value = scalar(current)
        current_inside = (current_value >= threshold - EPS_LENGTH
                          if keep_greater else current_value <= threshold + EPS_LENGTH)
        if current_inside != previous_inside:
            denominator = current_value - previous_value
            if abs(denominator) > EPS_INTERSECTION:
                fraction = (threshold - previous_value) / denominator
                result.append((_add(previous,
                                    _scale(_sub(current, previous), fraction))))
        if current_inside:
            result.append(current)
        previous, previous_value = current, current_value
        previous_inside = current_inside
    return _deduplicate(result)


def resolve_winder_riser_plan(cell, ascent_direction, inner_pivot,
                               riser_thickness):
    """Offset the physical front divider by an exact perpendicular thickness.

    The constant-distance band is intersected with the destination nominal
    cell.  This naturally trims its inner end at the mathematical pivot and
    its outer end at the local Turn chain without entering another sector.
    """
    thickness = float(riser_thickness)
    if not math.isfinite(thickness) or thickness <= 0.0:
        raise ValueError("蹴込み板厚は正の有限値である必要があります。")
    boundaries = physical_cell_boundaries(cell, ascent_direction, inner_pivot)
    origin, outer = boundaries.front
    direction, _length = _unit(_sub(outer, origin), "Winder front boundary")
    raw_signed = lambda point: _cross(direction, _sub(point, origin))
    centroid = (sum(point[0] for point in cell.polygon) / len(cell.polygon),
                sum(point[1] for point in cell.polygon) / len(cell.polygon))
    side = 1.0 if raw_signed(centroid) >= 0.0 else -1.0
    distance = lambda point: side * raw_signed(point)
    plan = _clip_polygon_scalar(tuple(cell.polygon), distance, True, 0.0)
    plan = _clip_polygon_scalar(plan, distance, False, thickness)
    if len(plan) < 3 or polygon_area(plan) <= EPS_AREA:
        raise ValueError("Winder Riser stripをlocal cell内へtrimできません。")
    return WinderRiserPlan(cell.index, boundaries.front, boundaries.rear,
                           plan, thickness)


def physical_winder_tread_polygon(cell, ascent_direction, inner_pivot,
                                  nosing=0.0, rear_extension=0.0):
    """Return a locally trimmed tread plan with extensions on radial edges only."""
    polygon = list(cell.polygon)
    boundaries = physical_cell_boundaries(cell, ascent_direction, inner_pivot)
    result = tuple(polygon)
    for boundary, amount, downhill in ((boundaries.front, float(nosing), True),
                                        (boundaries.rear, float(rear_extension), False)):
        if amount <= EPS_LENGTH:
            continue
        origin, outer = boundary
        direction, _ = _unit(_sub(outer, origin), "Winder tread boundary")
        centroid = (sum(p[0] for p in result) / len(result),
                    sum(p[1] for p in result) / len(result))
        interior_sign = 1.0 if _cross(direction, _sub(centroid, origin)) >= 0 else -1.0
        sign = -interior_sign if downhill else interior_sign
        offset = _scale((-direction[1], direction[0]), sign * amount)
        # The mathematical pivot is fixed, so the strip collapses locally
        # instead of extrapolating through it into the neighbouring sector.
        target = 1 if tuple(outer) == tuple(result[1]) else len(result) - 1
        result = tuple(_add(p, offset) if index == target else p
                       for index, p in enumerate(result))
    if polygon_area(result) <= EPS_AREA:
        raise ValueError("physical Winder treadをtrimできません。")
    return result


def allocate_straight_events(runs, overall_riser_count, landing_count,
                             winder_tread_count):
    """Apply schema-5 AUTO allocation with canonical-order tie breaking."""
    values = tuple(float(value) for value in runs)
    if any(not math.isfinite(value) or value < -EPS_LENGTH for value in values):
        raise ValueError("Straight region長が不正です。")
    budget = int(overall_riser_count) - int(landing_count) - int(winder_tread_count) - 1
    positive = tuple(index for index, value in enumerate(values) if value > EPS_LENGTH)
    if budget < len(positive) or (not positive and budget != 0):
        raise ValueError("positive straight regionへ最低1 tread eventを配分できません。")
    allocation = [0] * len(values)
    for index in positive:
        allocation[index] = 1
    for _unused in range(budget - len(positive)):
        index = min(positive, key=lambda item: (-values[item] / allocation[item], item))
        allocation[index] += 1
    return tuple(allocation)


def build_rise_events(straight_allocation, landing_count, winder_counts,
                      base_z, actual_riser):
    """Create the exact destination-owned event sequence including arrival."""
    events, counter = [], 0
    winder_counts = tuple(winder_counts)
    for region_index, count in enumerate(straight_allocation):
        for owner_index in range(1, count + 1):
            counter += 1
            events.append(RiseEvent(counter, "STRAIGHT_TREAD", owner_index,
                                    base_z + counter * actual_riser))
        if region_index < len(winder_counts):
            for owner_index in range(1, winder_counts[region_index] + 1):
                counter += 1
                events.append(RiseEvent(counter, "WINDER_TREAD", owner_index,
                                        base_z + counter * actual_riser))
    for owner_index in range(len(winder_counts), landing_count):
        counter += 1
        events.append(RiseEvent(counter, "LANDING_ARRIVAL", owner_index + 1,
                                base_z + counter * actual_riser))
    counter += 1
    events.append(RiseEvent(counter, "UPPER_ARRIVAL", 1,
                            base_z + counter * actual_riser))
    return tuple(events)


def _positive_mm(value, label):
    value = float(value)
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{label}は正の有限値である必要があります。")
    return value / _MM_PER_METRE


def canonical_turn_specs(point_ids, turn_specs=None, *, turn_mode=TURN_WINDER,
                         winder_pattern=WINDER_EQUAL_3):
    """Validate/materialize exactly one TurnSpec per interior Path identity.

    The scalar arguments are the read-only Stage-1 compatibility adapter.  A
    three-point file therefore remains byte-for-byte canonical until an
    explicit Stage-2 edit supplies ``turn_specs``.
    """
    interior = tuple(str(value) for value in point_ids[1:-1])
    if turn_specs is None:
        if len(interior) != 1:
            raise ValueError("複数Turnにはper-Turn stateが必要です。")
        pattern = WINDER_NONE if turn_mode == TURN_LANDING else winder_pattern
        return (TurnSpec(interior[0], turn_mode, pattern),)
    result = tuple(item if isinstance(item, TurnSpec) else TurnSpec(**item)
                   for item in turn_specs)
    if len(result) != len(interior) or tuple(item.path_point_id for item in result) != interior:
        raise ValueError("TurnSpecはcanonical interior path_point_id順で必要です。")
    return result


def classify_adjacent_turns(middle_length, first_exit_cutback,
                            second_entry_cutback, eps_length=EPS_LENGTH):
    remainder = float(middle_length) - float(first_exit_cutback) - float(second_entry_cutback)
    if remainder > eps_length:
        return "SEPARATED_U", remainder
    if remainder < -eps_length:
        return "INVALID_OVERLAP", remainder
    return "COMPACT_U", 0.0


def snap_angle_15(angle):
    """Interaction-only nearest-15-degree helper; resolver never calls it."""
    interval = math.pi / 12.0
    return round(float(angle) / interval) * interval


def promote_schema4_landing_allocation(physical_flight_allocation):
    """Explicit generalized-Landing migration: schema-4 r_i -> schema-5 s_i."""
    values = tuple(int(value) for value in physical_flight_allocation)
    if not values or any(value < 2 for value in values):
        raise ValueError("schema-4 Flight allocationをpromotionできません。")
    return tuple(value - 1 for value in values)


def manual_allocation_from_auto(resolved_allocation):
    """AUTO->MANUAL copies, rather than recomputes, the resolved authority."""
    return tuple(int(value) for value in resolved_allocation)


def resolve_winder_layout(points, ascent_direction, base_z_mm,
                          floor_to_floor_mm, riser_count, stair_width_mm,
                          tread_thickness_mm, riser_thickness_mm, *,
                          point_ids=None, winder_pattern=WINDER_EQUAL_3,
                          turn_mode=TURN_WINDER, turn_specs=None,
                          allocation=None, **finish):
    """Resolve a schema-5 generalized 3-point L or two-Turn 4-point U."""
    if points is None or len(points) not in (3, 4):
        raise ValueError("schema 5 production Pathは3-point Lまたは4-point Uです。")
    converted = tuple(_finite_xy(point, "Path point") for point in points)
    ids = tuple(str(value) for value in point_ids) if point_ids is not None else tuple("" for _ in converted)
    if len(ids) != len(converted) or any(not value for value in ids) or len(set(ids)) != len(ids):
        raise ValueError("schema 5 Path point identityが不正です。")
    width = _positive_mm(stair_width_mm, "階段幅")
    specs = canonical_turn_specs(ids, turn_specs, turn_mode=turn_mode,
                                 winder_pattern=winder_pattern)
    frames = tuple(resolve_turn_frame(converted[index - 1], converted[index],
                                      converted[index + 1], width, ids[index])
                   for index in range(1, len(converted) - 1))
    cells_by_turn = tuple(resolve_nominal_cells(frame, spec.winder_pattern)
                          if spec.turn_mode == TURN_WINDER else ()
                          for frame, spec in zip(frames, specs))
    counts = tuple(pattern_mapping(spec.winder_pattern)[0]
                   if spec.turn_mode == TURN_WINDER else 0 for spec in specs)
    lengths = tuple(math.hypot(*_sub(b, a)) for a, b in zip(converted, converted[1:]))
    runs = []
    for index, length in enumerate(lengths):
        entry_cut = frames[index - 1].cutback if index > 0 else 0.0
        exit_cut = frames[index].cutback if index < len(frames) else 0.0
        runs.append(length - entry_cut - exit_cut)
    classification = "NOT_U"
    shared = ()
    if len(frames) == 2:
        classification, middle = classify_adjacent_turns(lengths[1], frames[0].cutback,
                                                          frames[1].cutback)
        if classification == "INVALID_OVERLAP":
            raise ValueError("GEOMETRY_INVALID: adjacent Turn envelopes overlap")
        runs[1] = middle
        if classification == "COMPACT_U":
            # One deterministic cross-section authority; Path points stay put.
            shared = tuple((_add(a, b)[0] / 2.0, _add(a, b)[1] / 2.0)
                           for a, b in zip((frames[0].inner_pivot, frames[0].exit_outer),
                                           (frames[1].inner_pivot, frames[1].entry_outer)))
    if any(value < -EPS_LENGTH for value in runs):
        raise ValueError("GEOMETRY_INVALID: Turn cutback後のstraight regionが負です。")
    landing_count = sum(spec.turn_mode == TURN_LANDING for spec in specs)
    resolved = (allocate_straight_events(runs, riser_count, landing_count, sum(counts))
                if allocation is None else tuple(int(value) for value in allocation))
    expected_budget = int(riser_count) - landing_count - sum(counts) - 1
    if (len(resolved) != len(runs)
            or any(value < (1 if runs[index] > EPS_LENGTH else 0)
                   for index, value in enumerate(resolved))
            or any(runs[index] <= EPS_LENGTH and value != 0
                   for index, value in enumerate(resolved))
            or sum(resolved) != expected_budget):
        raise ValueError("保存されたschema-5 straight allocationが不正です。")
    floor_height = _positive_mm(floor_to_floor_mm, "階高")
    base_z = float(base_z_mm) / _MM_PER_METRE
    if not math.isfinite(base_z):
        raise ValueError("下端基準高さは有限値である必要があります。")
    tread_thickness = _positive_mm(tread_thickness_mm, "踏板厚")
    riser_thickness = _positive_mm(riser_thickness_mm, "蹴込み板厚")
    nosing = float(finish.get("tread_front_overhang_mm", 0.0)) / _MM_PER_METRE
    edge_mode = finish.get("tread_front_edge_mode", "SQUARE")
    edge_size = float(finish.get("tread_front_edge_size_mm", 0.0)) / _MM_PER_METRE
    if not math.isfinite(nosing) or nosing < 0.0:
        raise ValueError("nosingは0以上の有限値である必要があります。")
    if edge_mode not in ("SQUARE", "BEVEL", "ROUND"):
        raise ValueError("front-edge modeが不正です。")
    if edge_mode != "SQUARE" and (edge_size <= 0.0
            or edge_size >= tread_thickness / 2.0 or edge_size > nosing):
        raise ValueError("BEVEL/ROUNDはq>0, q<t/2, q<=nosingが必要です。")
    actual_riser = floor_height / int(riser_count)
    if tread_thickness >= actual_riser:
        raise ValueError("踏板厚は実蹴上より小さくする必要があります。")
    if ascent_direction not in ("FORWARD", "REVERSE"):
        raise ValueError("不明な上り方向です。")
    sequence = []
    for index, straight_count in enumerate(resolved):
        sequence.extend(("STRAIGHT_TREAD", step) for step in range(1, straight_count + 1))
        if index < len(specs):
            if specs[index].turn_mode == TURN_LANDING:
                sequence.append(("LANDING_ARRIVAL", index + 1))
            else:
                sequence.extend(("WINDER_TREAD", step) for step in range(1, counts[index] + 1))
    if ascent_direction == "REVERSE":
        sequence.reverse()
    sequence.append(("UPPER_ARRIVAL", 1))
    events = tuple(RiseEvent(index, owner, owner_index,
                             base_z + index * actual_riser)
                   for index, (owner, owner_index) in enumerate(sequence, 1))
    if len(events) != int(riser_count):
        raise ValueError("RiseEvent invariant S + L + W + 1 = Nを満たしません。")
    path = tuple(PathPoint(identity, xy) for identity, xy in zip(ids, converted))
    traversal = ids if ascent_direction == "FORWARD" else tuple(reversed(ids))
    return WinderLayout(path, traversal, ascent_direction, frames[0],
                        specs[0].winder_pattern, cells_by_turn[0], tuple(runs), resolved, events,
                        actual_riser, base_z, base_z + floor_height, width,
                        tread_thickness, riser_thickness, frames, specs,
                        cells_by_turn, classification, landing_count, counts, shared,
                        nosing, edge_mode, edge_size)


def _polygon_prism(polygon, bottom, top, role, ordinal):
    polygon = tuple(polygon)
    if polygon_signed_area(polygon) < 0.0:
        polygon = tuple(reversed(polygon))
    vertices = tuple((x, y, bottom) for x, y in polygon) + tuple(
        (x, y, top) for x, y in polygon)
    size = len(polygon)
    faces = [tuple(reversed(range(size))), tuple(range(size, size * 2))]
    faces.extend((index, (index + 1) % size, (index + 1) % size + size,
                  index + size) for index in range(size))
    return MeshFragment(role, ordinal, vertices, tuple(faces))


def _straight_box(start, direction, normal, width, x0, x1, bottom, top,
                  role, ordinal):
    half = width / 2.0
    polygon = tuple(_add(start, _add(_scale(direction, x), _scale(normal, y)))
                    for x, y in ((x0, -half), (x1, -half),
                                 (x1, half), (x0, half)))
    return _polygon_prism(polygon, bottom, top, role, ordinal)


def build_winder_fragments(layout):
    """Build top geometry from the resolved whole-stair event sequence."""
    fragments, ordinal, counter = [], 0, 0
    path = layout.canonical_path
    segments = []
    for index, (a, b) in enumerate(zip(path, path[1:])):
        direction, _ = _unit(_sub(b.xy, a.xy))
        start_cut = layout.turns[index - 1].cutback if index > 0 else 0.0
        start = _add(a.xy, _scale(direction, start_cut))
        segments.append((start, direction, layout.straight_runs[index],
                         layout.straight_allocation[index]))
    components = []
    for index, segment in enumerate(segments):
        components.append(("STRAIGHT", index, segment))
        if index < len(layout.turn_specs):
            components.append((layout.turn_specs[index].turn_mode, index, None))
    if layout.ascent_direction == "REVERSE":
        reversed_components = []
        for kind, index, payload in reversed(components):
            if kind == "STRAIGHT":
                start, direction, run, count = payload
                payload = (_add(start, _scale(direction, run)), _scale(direction, -1), run, count)
            reversed_components.append((kind, index, payload))
        components = reversed_components
    normal = lambda direction: (-direction[1], direction[0])
    for kind, turn_index, payload in components:
        if kind == "STRAIGHT":
            start, direction, run, tread_count = payload
            if not tread_count:
                continue
            going = run / tread_count
            for step in range(tread_count):
                counter += 1
                top = layout.base_z + counter * layout.actual_riser
                ordinal += 1
                fragments.append(_straight_box(start, direction, normal(direction),
                                                 layout.width, step * going,
                                                 (step + 1) * going,
                                                 top - layout.tread_thickness, top,
                                                 "TREAD", ordinal))
                ordinal += 1
                fragments.append(_straight_box(start, direction, normal(direction),
                                                 layout.width, step * going,
                                                 step * going + layout.riser_thickness,
                                                 top - layout.actual_riser,
                                                 top - layout.tread_thickness,
                                                 "RISER", ordinal))
        elif kind == TURN_LANDING:
            counter += 1
            top = layout.base_z + counter * layout.actual_riser
            ordinal += 1
            fragments.append(_polygon_prism(layout.turns[turn_index].envelope,
                                             top - layout.tread_thickness, top,
                                             "LANDING", ordinal))
        else:
            cells = layout.turn_cells[turn_index]
            if layout.ascent_direction == "REVERSE":
                cells = tuple(reversed(cells))
            for cell in cells:
                counter += 1
                top = layout.base_z + counter * layout.actual_riser
                ordinal += 1
                tread_polygon = physical_winder_tread_polygon(
                    cell, layout.ascent_direction,
                    layout.turns[turn_index].inner_pivot, layout.nosing,
                    layout.riser_thickness)
                fragments.append(_polygon_prism(tread_polygon,
                                                 top - layout.tread_thickness,
                                                 top, "TREAD", ordinal))
                riser = resolve_winder_riser_plan(
                    cell, layout.ascent_direction, layout.turns[turn_index].inner_pivot,
                    layout.riser_thickness)
                ordinal += 1
                fragments.append(_polygon_prism(
                    riser.polygon, top - layout.actual_riser,
                    top - layout.tread_thickness, "RISER", ordinal))
    fragments = tuple(fragments)
    validate_mesh_fragments(fragments)
    return fragments


def prepare_winder_geometry(points, ascent_direction, base_z_mm,
                            floor_to_floor_mm, riser_count, stair_width_mm,
                            tread_thickness_mm, riser_thickness_mm, *,
                            point_ids=None, winder_pattern=WINDER_EQUAL_3,
                            turn_mode=TURN_WINDER, turn_specs=None,
                            allocation=None, **finish):
    """Atomically prepare canonical layout, fragments, and combined mesh."""
    layout = resolve_winder_layout(
        points, ascent_direction, base_z_mm, floor_to_floor_mm, riser_count,
        stair_width_mm, tread_thickness_mm, riser_thickness_mm,
        point_ids=point_ids, winder_pattern=winder_pattern,
        turn_mode=turn_mode, turn_specs=turn_specs,
        allocation=allocation, **finish)
    fragments = build_winder_fragments(layout)
    mesh = assemble_stair_mesh(fragments)
    return layout, fragments, StairMeshData(mesh.vertices, mesh.faces,
                                            mesh.face_roles)


prepare_turn_geometry = prepare_winder_geometry
resolve_turn_layout = resolve_winder_layout
