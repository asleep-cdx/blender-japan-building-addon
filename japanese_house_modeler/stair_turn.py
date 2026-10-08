"""Pure Build 07-E generalized-Turn and Stage-1 L-Winder geometry.

Schema 4 remains implemented by :mod:`stair_multiflight`.  This module is a
parallel schema-5 resolver; importantly, none of its helpers mutates Blender
state.  Operators can therefore prepare and validate a complete candidate
before replacing a managed object's mesh or canonical properties.
"""

from dataclasses import dataclass, replace
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
class PhysicalWinderBoundary:
    """One ascent-local semantic divider and its three parallel authorities."""
    index: int
    nominal_face: tuple
    direction: tuple
    uphill_normal: tuple
    nose_origin: tuple
    back_origin: tuple


@dataclass(frozen=True)
class PhysicalWinderInnerTrim:
    """One Turn-local common physical finish chord."""
    bisector: tuple
    h_finish: float
    entry_point: tuple
    exit_point: tuple
    chord: tuple


@dataclass(frozen=True)
class PhysicalWinderTreadPlan:
    cell_index: int
    polygon: tuple
    exposed_front_edge: tuple
    rear_support_edge: tuple
    inner_miter: tuple
    inner_front: tuple
    inner_rear: tuple
    inner_edge: tuple
    inner_trim: PhysicalWinderInnerTrim
    front_boundary: PhysicalWinderBoundary
    rear_boundary: PhysicalWinderBoundary
    riser_polygon: tuple
    riser_back_edge: tuple


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


@dataclass(frozen=True)
class SlopedTurnStation:
    """One shared radial station of a visual-first Winder soffit."""

    fraction: float
    inner: tuple
    outer: tuple
    lower_z: float
    event_fraction: float


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


def winder_riser_hidden_rear_outer(cell, ascent_direction, inner_pivot,
                                   riser_thickness):
    """Return the existing Riser plan's exact outer hidden-rear contact."""
    plan = resolve_winder_riser_plan(
        cell, ascent_direction, inner_pivot, riser_thickness)
    origin, outer = plan.front
    direction, _ = _unit(_sub(outer, origin), "Winder front boundary")
    centroid = _centroid(cell.polygon)
    side = (1.0 if _cross(direction, _sub(centroid, origin)) >= 0.0 else -1.0)
    candidates = tuple(
        point for point in plan.polygon
        if abs(side * _cross(direction, _sub(point, origin))
               - plan.thickness) <= EPS_LENGTH)
    if not candidates:
        raise ValueError("Winder Riser hidden rear outerを解決できません。")
    return max(candidates, key=lambda point: math.hypot(
        *_sub(point, inner_pivot)))


def winder_tread_rear_outer_authority(layout, turn_index, cells, cell_index):
    """Return the exact rear-outer support shared by Tread and stepped body."""
    cell = cells[cell_index]
    frame = layout.turns[turn_index]
    if cell_index + 1 < len(cells):
        return winder_riser_hidden_rear_outer(
            cells[cell_index + 1], layout.ascent_direction,
            frame.inner_pivot, layout.riser_thickness)
    rear = physical_cell_boundaries(
        cell, layout.ascent_direction, frame.inner_pivot).rear
    return resolve_winder_finish_outer_hit(
        frame, cell, rear, layout.riser_thickness)


def resolve_winder_finish_outer_hit(frame, cell, boundary, amount):
    """Intersect a radial finish offset with the canonical exterior chain."""
    origin, nominal_outer = boundary
    direction, _ = _unit(_sub(nominal_outer, origin), "Winder tread boundary")
    centroid = _centroid(cell.polygon)
    interior_sign = (1.0 if _cross(
        direction, _sub(centroid, origin)) >= 0.0 else -1.0)
    offset_origin = _add(
        origin, _scale((-direction[1], direction[0]),
                       -interior_sign * float(amount)))
    chain = (frame.entry_outer, frame.outer_corner, frame.exit_outer)
    nominal_is_front = tuple(nominal_outer) == tuple(cell.polygon[1])
    candidates = []
    for index, (start, end) in enumerate(zip(chain, chain[1:])):
        exterior, _ = _unit(_sub(end, start), "Turn exterior segment")
        try:
            hit = _line_intersection(offset_origin, direction, start, exterior)
        except ValueError:
            continue
        segment_length = math.hypot(*_sub(end, start))
        parameter = _dot(_sub(hit, start), exterior) / segment_length
        if not (-EPS_LENGTH <= parameter <= 1.0 + EPS_LENGTH
                or (index == 0 and parameter < 0.0)
                or (index == len(chain) - 2 and parameter > 1.0)):
            continue
        station = index + parameter
        nominal_station = min(
            ((segment_index + _dot(_sub(nominal_outer, a), unit)
              / math.hypot(*_sub(b, a)))
             for segment_index, (a, b) in enumerate(zip(chain, chain[1:]))
             for unit in (_unit(_sub(b, a), "Turn exterior segment")[0],)
             if abs(_cross(unit, _sub(nominal_outer, a))) <= EPS_LENGTH),
            key=lambda value: abs(value - station), default=None)
        if nominal_station is None:
            continue
        delta = station - nominal_station
        if ((nominal_is_front and delta < -EPS_INTERSECTION)
                or (not nominal_is_front and delta > EPS_INTERSECTION)):
            candidates.append((abs(delta), hit))
    if not candidates:
        raise ValueError("Winder finishとcanonical outer envelopeが交差しません。")
    candidates.sort(key=lambda item: item[0])
    if (len(candidates) > 1
            and abs(candidates[0][0] - candidates[1][0]) <= EPS_INTERSECTION
            and math.hypot(*_sub(candidates[0][1], candidates[1][1])) > EPS_LENGTH):
        raise ValueError("Winder finishのcanonical outer hitが一意ではありません。")
    return candidates[0][1]


def _canonical_outer_station(frame, point):
    """Return a station on the canonical exterior, including continuations."""
    chain = (frame.entry_outer, frame.outer_corner, frame.exit_outer)
    candidates = []
    for index, (start, end) in enumerate(zip(chain, chain[1:])):
        direction, length = _unit(_sub(end, start), "Turn exterior segment")
        if abs(_cross(direction, _sub(point, start))) > EPS_LENGTH:
            continue
        parameter = _dot(_sub(point, start), direction) / length
        if ((index == 0 and parameter <= 1.0 + EPS_LENGTH)
                or (index == 1 and parameter >= -EPS_LENGTH)):
            candidates.append(index + parameter)
    if not candidates:
        return None
    return min(candidates, key=lambda value: abs(value - 1.0))


def preserve_canonical_outer_chain(frame, polygon):
    """Insert the exact outer corner when an exterior edge crosses station 1."""
    polygon = tuple(polygon)
    result = []
    corner = tuple(frame.outer_corner)
    for point, following in zip(polygon, polygon[1:] + polygon[:1]):
        result.append(point)
        first = _canonical_outer_station(frame, point)
        second = _canonical_outer_station(frame, following)
        if (first is None or second is None
                or abs(first - 1.0) <= EPS_LENGTH
                or abs(second - 1.0) <= EPS_LENGTH):
            continue
        if (first - 1.0) * (second - 1.0) < 0.0:
            result.append(corner)
    result = _deduplicate(tuple(result))
    if len(result) < 3 or polygon_area(result) <= EPS_AREA:
        raise ValueError("Winder canonical outer chain topologyが不正です。")
    return result


def physical_winder_tread_polygon(cell, ascent_direction, inner_pivot,
                                  nosing=0.0, rear_extension=0.0, *,
                                  frame, rear_outer_authority=None):
    """Return a locally trimmed tread plan with extensions on radial edges only."""
    polygon = list(cell.polygon)
    boundaries = physical_cell_boundaries(cell, ascent_direction, inner_pivot)
    result = tuple(polygon)
    for boundary, amount in ((boundaries.front, float(nosing)),
                             (boundaries.rear, float(rear_extension))):
        if amount <= EPS_LENGTH:
            continue
        origin, outer = boundary
        # Both finishes extend away from the current nominal cell: the front
        # becomes the downhill nosing and the rear reaches through the uphill
        # successor Riser band.  The opposite radial boundaries naturally
        # give those extensions opposite world-space directions.
        outer_hit = resolve_winder_finish_outer_hit(
            frame, cell, boundary, amount)
        if boundary == boundaries.rear and rear_outer_authority is not None:
            outer_hit = tuple(rear_outer_authority)
        # The mathematical pivot is fixed, so the strip collapses locally
        # instead of extrapolating through it into the neighbouring sector.
        target = 1 if tuple(outer) == tuple(result[1]) else len(result) - 1
        result = tuple(outer_hit if index == target else p
                       for index, p in enumerate(result))
    if polygon_area(result) <= EPS_AREA:
        raise ValueError("physical Winder treadをtrimできません。")
    return preserve_canonical_outer_chain(frame, result)


def _centroid(polygon):
    return (sum(point[0] for point in polygon) / len(polygon),
            sum(point[1] for point in polygon) / len(polygon))


def _semantic_boundary(index, nominal, destination_point, nosing, thickness,
                       *, away=False):
    inner, outer = nominal
    direction, _ = _unit(_sub(outer, inner), "Winder semantic boundary")
    normal = (-direction[1], direction[0])
    if _dot(normal, _sub(destination_point, inner)) < 0.0:
        normal = _scale(normal, -1.0)
    if away:
        normal = _scale(normal, -1.0)
    return PhysicalWinderBoundary(
        index, nominal, direction, normal,
        _add(inner, _scale(normal, -float(nosing))),
        _add(inner, _scale(normal, float(thickness))))


def _line_chain_intersection(origin, direction, chain, preferred):
    candidates = []
    cumulative = 0.0
    for segment_index, (start, end) in enumerate(zip(chain, chain[1:])):
        edge = _sub(end, start)
        length = math.hypot(*edge)
        denominator = _cross(direction, edge)
        if abs(denominator) > EPS_INTERSECTION:
            delta = _sub(start, origin)
            line_t = _cross(delta, edge) / denominator
            edge_t = _cross(delta, direction) / denominator
            if -EPS_LENGTH <= edge_t <= 1.0 + EPS_LENGTH:
                point = _add(origin, _scale(direction, line_t))
                candidates.append((math.hypot(point[0] - preferred[0],
                                              point[1] - preferred[1]),
                                   cumulative + max(0.0, min(1.0, edge_t)) * length,
                                   point, segment_index))
        cumulative += length
    if not candidates:
        raise ValueError("GEOMETRY_INVALID: physical boundaryをouter chainへtrimできません。")
    _distance, station, point, segment_index = min(candidates)
    return point, station, segment_index


def _trim_semantic_line(origin, direction, chain, nominal_face):
    """Trim to the Turn chain or its immediate entry/exit walking extension."""
    try:
        return _line_chain_intersection(origin, direction, chain,
                                        nominal_face[1])
    except ValueError:
        displacement = _sub(origin, nominal_face[0])
        point = _add(nominal_face[1], displacement)
        total = sum(math.hypot(*_sub(b, a)) for a, b in zip(chain, chain[1:]))
        station = (0.0 if math.hypot(*_sub(nominal_face[1], chain[0])) <= EPS_LENGTH
                   else total if math.hypot(*_sub(nominal_face[1], chain[-1])) <= EPS_LENGTH
                   else math.hypot(*_sub(chain[1], chain[0])))
        return point, station, -1


def resolve_physical_winder_plans(frame, cells, ascent_direction,
                                  nosing, riser_thickness):
    """Derive shared semantic lines once and assemble finite mitered plans."""
    cells = tuple(cells)
    if not cells:
        return ()
    ordered = cells if ascent_direction == "FORWARD" else tuple(reversed(cells))
    local = tuple(physical_cell_boundaries(
        cell, ascent_direction, frame.inner_pivot) for cell in ordered)
    nominal = [local[0].front] + [item.rear for item in local]
    boundaries = []
    for index, boundary in enumerate(nominal):
        if index < len(ordered):
            boundaries.append(_semantic_boundary(
                index, boundary, _centroid(ordered[index].polygon),
                nosing, riser_thickness))
        else:
            boundaries.append(_semantic_boundary(
                index, boundary, _centroid(ordered[-1].polygon),
                nosing, riser_thickness, away=True))
    chain = _deduplicate(
        (frame.entry_outer, frame.outer_corner, frame.exit_outer)
        if ascent_direction == "FORWARD" else
        (frame.exit_outer, frame.outer_corner, frame.entry_outer))
    corner_station = (math.hypot(*_sub(frame.outer_corner, chain[0]))
                      if frame.outer_corner in chain else float("inf"))
    raw_miters = tuple(_line_intersection(
        boundaries[index].nose_origin, boundaries[index].direction,
        boundaries[index + 1].back_origin,
        boundaries[index + 1].direction)
        for index in range(len(ordered)))
    entry_ray, entry_length = _unit(
        _sub(frame.entry_outer, frame.inner_pivot), "Turn entry ray")
    exit_ray, exit_length = _unit(
        _sub(frame.exit_outer, frame.inner_pivot), "Turn exit ray")
    bisector, _ = _unit(_add(entry_ray, exit_ray), "Turn inner finish bisector")
    clearance = max(float(nosing), float(riser_thickness), 10.0 * EPS_LENGTH)
    h_finish = max(0.0, max(_dot(_sub(point, frame.inner_pivot), bisector)
                            for point in raw_miters)) + clearance
    finish_origin = _add(frame.inner_pivot, _scale(bisector, h_finish))
    finish_direction = (-bisector[1], bisector[0])
    entry_point = _line_intersection(
        finish_origin, finish_direction, frame.inner_pivot, entry_ray)
    exit_point = _line_intersection(
        finish_origin, finish_direction, frame.inner_pivot, exit_ray)
    entry_t = _dot(_sub(entry_point, frame.inner_pivot), entry_ray)
    exit_t = _dot(_sub(exit_point, frame.inner_pivot), exit_ray)
    if (entry_t <= EPS_LENGTH or exit_t <= EPS_LENGTH
            or entry_t >= entry_length - EPS_LENGTH
            or exit_t >= exit_length - EPS_LENGTH):
        raise ValueError("GEOMETRY_INVALID: common inner finish chordがTurn内に収まりません。")
    inner_trim = PhysicalWinderInnerTrim(
        bisector, h_finish, entry_point, exit_point,
        (entry_point, exit_point))
    plans = []
    for index, cell in enumerate(ordered):
        front, rear = boundaries[index], boundaries[index + 1]
        inner_miter = raw_miters[index]
        inner_front = _line_intersection(
            front.nose_origin, front.direction,
            finish_origin, finish_direction)
        inner_rear = _line_intersection(
            rear.back_origin, rear.direction,
            finish_origin, finish_direction)
        if math.hypot(*_sub(inner_rear, inner_front)) <= EPS_LENGTH:
            raise ValueError("GEOMETRY_INVALID: physical Winder inner edgeが短すぎます。")
        front_outer, front_station, _ = _trim_semantic_line(
            front.nose_origin, front.direction, chain, front.nominal_face)
        rear_outer, rear_station, _ = _trim_semantic_line(
            rear.back_origin, rear.direction, chain, rear.nominal_face)
        outer = [front_outer]
        low, high = sorted((front_station, rear_station))
        if low + EPS_LENGTH < corner_station < high - EPS_LENGTH:
            outer.append(frame.outer_corner)
        outer.append(rear_outer)
        if len(outer) == 2:
            midpoint = _scale(_add(outer[0], outer[1]), 0.5)
            outer.insert(1, midpoint)
        polygon = _deduplicate((inner_front, *outer, inner_rear))
        if len(polygon) < 3 or polygon_area(polygon) <= EPS_AREA:
            raise ValueError("GEOMETRY_INVALID: physical Winder common inner trimが不正です。")
        if any(_dot(_sub(point, frame.inner_pivot), bisector)
               < h_finish - EPS_LENGTH for point in polygon):
            raise ValueError("GEOMETRY_INVALID: physical vertexがinner finish chordを越えます。")
        front_edge = (inner_front, front_outer)
        rear_edge = (inner_rear, rear_outer)
        if plans:
            riser_back = plans[-1].rear_support_edge
        else:
            first_back_outer, _station, _segment = _trim_semantic_line(
                front.back_origin, front.direction, chain,
                front.nominal_face)
            first_back_inner = _line_intersection(
                front.back_origin, front.direction,
                finish_origin, finish_direction)
            riser_back = (first_back_inner, first_back_outer)
        face_inner = _line_intersection(
            front.nominal_face[0], front.direction,
            finish_origin, finish_direction)
        riser_polygon = _deduplicate((face_inner, front.nominal_face[1],
                                      riser_back[1], riser_back[0]))
        if len(riser_polygon) < 3 or polygon_area(riser_polygon) <= EPS_AREA:
            raise ValueError("GEOMETRY_INVALID: Winder Riser bandが不正です。")
        plans.append(PhysicalWinderTreadPlan(
            cell.index, polygon, front_edge, rear_edge, inner_miter,
            inner_front, inner_rear, (inner_front, inner_rear), inner_trim,
            front, rear, riser_polygon, riser_back))
    return tuple(plans)


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


def promotion_turn_specs(point_ids, selected_index, turn_mode, winder_pattern):
    """Materialize a schema-4 L/U only for an explicit Stage-2 edit."""
    interior = tuple(str(value) for value in point_ids[1:-1])
    if not 0 <= int(selected_index) < len(interior):
        raise ValueError("Turn indexが不正です。")
    specs = [TurnSpec(identity, TURN_LANDING, WINDER_NONE)
             for identity in interior]
    specs[int(selected_index)] = TurnSpec(
        interior[int(selected_index)], turn_mode,
        winder_pattern if turn_mode == TURN_WINDER else WINDER_NONE)
    return tuple(specs)


def prepare_schema4_promotion(point_ids, selected_index, turn_mode,
                              winder_pattern, distribution_mode,
                              physical_allocation):
    """Pure transactional candidate data for an explicit schema-4 promotion."""
    if distribution_mode == "MANUAL" and turn_mode == TURN_WINDER:
        raise ValueError("schema-4 MANUALは先にAUTOへ変更してください。")
    specs = promotion_turn_specs(point_ids, selected_index, turn_mode,
                                 winder_pattern)
    allocation = (promote_schema4_landing_allocation(physical_allocation)
                  if distribution_mode == "MANUAL" else ())
    return specs, distribution_mode, allocation


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


def active_schema5_allocation(mode, auto_allocation, manual_allocation):
    """Select the one allocation authority used for schema-5 derivation/UI."""
    if mode == "AUTO":
        return tuple(auto_allocation)
    if mode == "MANUAL":
        return tuple(manual_allocation)
    raise ValueError("schema-5 distribution modeが不正です。")


def turn_settings_available(schema_version, _distribution_mode):
    """Both schema-4 and schema-5 expose explicit Turn editing."""
    return int(schema_version) in (4, WINDER_SCHEMA_VERSION)


def path_move_validation_allocation(distribution_mode, manual_allocation):
    """AUTO recomputes for a changed Path; MANUAL retains its authority."""
    if distribution_mode == "AUTO":
        return None
    if distribution_mode == "MANUAL":
        return tuple(manual_allocation)
    raise ValueError("schema-5 distribution modeが不正です。")


def dimension_edit_auto_allocation(schema_version, distribution_mode,
                                   stored_auto_allocation):
    """Invalidate AUTO after schema-4/5 dimensions change; preserve MANUAL."""
    if (int(schema_version) in (4, WINDER_SCHEMA_VERSION)
            and distribution_mode == "AUTO"):
        return None
    return stored_auto_allocation


def compatibility_scalar_pattern(turn_specs, legacy_pattern=WINDER_NONE):
    """Return the non-authoritative scalar used by old single-Turn files."""
    specs = tuple(turn_specs or ())
    if not specs:
        return legacy_pattern
    if len(specs) == 1:
        return (specs[0].winder_pattern
                if specs[0].turn_mode == TURN_WINDER else WINDER_NONE)
    return WINDER_NONE


def reconcile_shared_interface(first, second, eps_length=EPS_LENGTH):
    """Return one exact midpoint section or reject a non-compact mismatch."""
    first, second = tuple(first), tuple(second)
    if len(first) != 2 or len(second) != 2:
        raise ValueError("Compact-U shared interfaceが不正です。")
    if any(math.hypot(a[0] - b[0], a[1] - b[1]) > eps_length
           for a, b in zip(first, second)):
        raise ValueError("GEOMETRY_INVALID: Compact-U shared interface mismatch")
    return tuple(((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
                 for a, b in zip(first, second))


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
            first = (frames[0].inner_pivot, frames[0].exit_outer)
            second = (frames[1].inner_pivot, frames[1].entry_outer)
            shared = reconcile_shared_interface(first, second)
            frames = (replace(frames[0], inner_pivot=shared[0],
                              exit_outer=shared[1]),
                      replace(frames[1], inner_pivot=shared[0],
                              entry_outer=shared[1]))
    if any(value < -EPS_LENGTH for value in runs):
        raise ValueError("GEOMETRY_INVALID: Turn cutback後のstraight regionが負です。")
    cells_by_turn = tuple(resolve_nominal_cells(frame, spec.winder_pattern)
                          if spec.turn_mode == TURN_WINDER else ()
                          for frame, spec in zip(frames, specs))
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
    event_components = []
    for index, straight_count in enumerate(resolved):
        event_components.append(("STRAIGHT_TREAD", straight_count))
        if index < len(specs):
            if specs[index].turn_mode == TURN_LANDING:
                event_components.append(("LANDING_ARRIVAL", 1))
            else:
                event_components.append(("WINDER_TREAD", counts[index]))
    if ascent_direction == "REVERSE":
        event_components.reverse()
    sequence = [(owner, local_index)
                for owner, count in event_components
                for local_index in range(1, count + 1)]
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


def _profiled_prism(polygon, bottom, top, front, mode, edge_size,
                    role, ordinal):
    """Profile only one named exposed plan edge; every other edge stays square."""
    if mode == "SQUARE":
        return _polygon_prism(polygon, bottom, top, role, ordinal)
    polygon = tuple(polygon)
    if polygon_signed_area(polygon) < 0.0:
        polygon = tuple(reversed(polygon))
    endpoints = tuple(front)
    indices = tuple(next((index for index, point in enumerate(polygon)
                          if math.hypot(point[0] - endpoint[0],
                                        point[1] - endpoint[1]) <= EPS_LENGTH), -1)
                    for endpoint in endpoints)
    if -1 in indices or (indices[1] - indices[0]) % len(polygon) not in (1, len(polygon) - 1):
        raise ValueError("exposed front edgeをphysical treadから解決できません。")
    i, j = indices
    if (j - i) % len(polygon) != 1:
        i, j = j, i
    direction, _ = _unit(_sub(polygon[j], polygon[i]), "exposed front edge")
    centroid = (sum(p[0] for p in polygon) / len(polygon),
                sum(p[1] for p in polygon) / len(polygon))
    normal = (-direction[1], direction[0])
    if _dot(normal, _sub(centroid, polygon[i])) < 0.0:
        normal = _scale(normal, -1.0)
    q = float(edge_size)
    if mode == "BEVEL":
        stations = ((q, bottom), (0.0, bottom + q),
                    (0.0, top - q), (q, top))
    elif mode == "ROUND":
        stations = [(q, bottom)]
        lower = (q, bottom + q)
        stations.extend((q + q * math.cos(-math.pi / 2.0 - k * math.pi / 8.0),
                         lower[1] + q * math.sin(-math.pi / 2.0 - k * math.pi / 8.0))
                        for k in range(1, 5))
        upper = (q, top - q)
        stations.extend((q + q * math.cos(math.pi - k * math.pi / 8.0),
                         upper[1] + q * math.sin(math.pi - k * math.pi / 8.0))
                        for k in range(0, 5))
    else:
        raise ValueError("不明なfront-edge modeです。")
    stations = tuple(stations)
    bottom_plan = list(polygon)
    top_plan = list(polygon)
    for index in (i, j):
        bottom_plan[index] = _add(polygon[index], _scale(normal, stations[0][0]))
        top_plan[index] = _add(polygon[index], _scale(normal, stations[-1][0]))
    vertices = [(x, y, bottom) for x, y in bottom_plan]
    vertices.extend((x, y, top) for x, y in top_plan)
    chains = {}
    for index in (i, j):
        chain = [index]
        for offset, z in stations[1:-1]:
            point = _add(polygon[index], _scale(normal, offset))
            chain.append(len(vertices)); vertices.append((point[0], point[1], z))
        chain.append(index + len(polygon))
        chains[index] = chain
    size = len(polygon)
    faces = [tuple(reversed(range(size))), tuple(range(size, size * 2))]
    for index in range(size):
        following = (index + 1) % size
        if index == i and following == j:
            for a, b, c, d in zip(chains[i], chains[j],
                                  chains[j][1:], chains[i][1:]):
                faces.append((a, b, c, d))
        elif following == i:
            faces.append((index, i, *chains[i][1:], index + size))
        elif index == j:
            faces.append((j, following, following + size, j + size,
                          *tuple(reversed(chains[j][1:-1]))))
        else:
            faces.append((index, following, following + size, index + size))
    fragment = MeshFragment(role, ordinal, tuple(vertices), tuple(faces))
    validate_mesh_fragments((fragment,))
    return fragment


def _straight_box(start, direction, normal, width, x0, x1, bottom, top,
                  role, ordinal):
    half = width / 2.0
    polygon = tuple(_add(start, _add(_scale(direction, x), _scale(normal, y)))
                    for x, y in ((x0, -half), (x1, -half),
                                 (x1, half), (x0, half)))
    return _polygon_prism(polygon, bottom, top, role, ordinal)


def _straight_tread(start, direction, normal, width, x0, x1, bottom, top,
                    nosing, mode, edge_size, ordinal):
    half = width / 2.0
    front = x0 - nosing
    polygon = tuple(_add(start, _add(_scale(direction, x), _scale(normal, y)))
                    for x, y in ((front, -half), (x1, -half),
                                 (x1, half), (front, half)))
    exposed = (polygon[-1], polygon[0])
    return _profiled_prism(polygon, bottom, top, exposed, mode, edge_size,
                           "TREAD", ordinal)


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
                fragments.append(_straight_tread(
                    start, direction, normal(direction), layout.width,
                    step * going, (step + 1) * going + layout.riser_thickness,
                    top - layout.tread_thickness, top, layout.nosing,
                    layout.front_edge_mode, layout.front_edge_size, ordinal))
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
                                             "TREAD", ordinal))
            landing_cell = NominalWinderCell(
                1, 0.0, 1.0, layout.turns[turn_index].envelope)
            riser = resolve_winder_riser_plan(
                landing_cell, layout.ascent_direction,
                layout.turns[turn_index].inner_pivot,
                layout.riser_thickness)
            ordinal += 1
            fragments.append(_polygon_prism(
                riser.polygon, top - layout.actual_riser,
                top - layout.tread_thickness, "RISER", ordinal))
        else:
            cells = layout.turn_cells[turn_index]
            if layout.ascent_direction == "REVERSE":
                cells = tuple(reversed(cells))
            for cell_index, cell in enumerate(cells):
                counter += 1
                top = layout.base_z + counter * layout.actual_riser
                ordinal += 1
                rear_outer_authority = winder_tread_rear_outer_authority(
                    layout, turn_index, cells, cell_index)
                tread_polygon = physical_winder_tread_polygon(
                    cell, layout.ascent_direction,
                    layout.turns[turn_index].inner_pivot, layout.nosing,
                    layout.riser_thickness,
                    frame=layout.turns[turn_index],
                    rear_outer_authority=rear_outer_authority)
                exposed = ((tread_polygon[0], tread_polygon[1])
                           if layout.ascent_direction == "FORWARD"
                           else (tread_polygon[-1], tread_polygon[0]))
                fragments.append(_profiled_prism(
                    tread_polygon, top - layout.tread_thickness, top,
                    exposed, layout.front_edge_mode, layout.front_edge_size,
                    "TREAD", ordinal))
                riser = resolve_winder_riser_plan(
                    cell, layout.ascent_direction, layout.turns[turn_index].inner_pivot,
                    layout.riser_thickness)
                ordinal += 1
                fragments.append(_polygon_prism(
                    riser.polygon, top - layout.actual_riser,
                    top - layout.tread_thickness, "RISER", ordinal))
    # UPPER_ARRIVAL is the final RiseEvent, not another ordinary tread cell.
    # Use the actual last ascent-local Straight component for its plane.
    final_start, final_direction, final_run, _count = components[-1][2]
    final_normal = normal(final_direction)
    arrival = layout.upper_arrival_z
    cap_bottom = arrival - layout.tread_thickness
    ordinal += 1
    fragments.append(_straight_box(
        final_start, final_direction, final_normal, layout.width,
        final_run, final_run + layout.riser_thickness,
        arrival - layout.actual_riser,
        cap_bottom if layout.nosing > 0.0 else arrival,
        "RISER", ordinal))
    if layout.nosing > 0.0:
        ordinal += 1
        fragments.append(_straight_tread(
            final_start, final_direction, final_normal, layout.width,
            final_run, final_run + layout.riser_thickness,
            cap_bottom, arrival, layout.nosing,
            layout.front_edge_mode, layout.front_edge_size,
            ordinal))
    fragments = tuple(fragments)
    validate_mesh_fragments(fragments)
    return fragments


def build_stepped_closed_underbody_fragments(layout, _top_fragments, fields):
    """Build setback schema-5 bodies without covering the accepted top."""
    from .stair_residential import (
        validate_stepped_closure_depth,
        validate_stepped_underbody_thickness,
    )
    from .stair_residential_geometry import build_underbody_fragment
    from .stair_geometry import StairAxes, StairLayout

    validate_stepped_underbody_thickness(
        fields, layout.actual_riser, layout.tread_thickness,
        layout.riser_thickness)
    depth = validate_stepped_closure_depth(
        fields, layout.actual_riser, min(
            run / count for run, count in zip(
                layout.straight_runs, layout.straight_allocation) if count))
    if depth - layout.tread_thickness <= EPS_LENGTH:
        raise ValueError(
            "UNDERBODY closure depthは踏板厚より大きい必要があります。")
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
                payload = (_add(start, _scale(direction, run)),
                           _scale(direction, -1.0), run, count)
            reversed_components.append((kind, index, payload))
        components = reversed_components

    bodies, counter = [], 0
    for kind, turn_index, payload in components:
        if kind == "STRAIGHT":
            start, direction, run, count = payload
            if not count:
                continue
            going = run / count
            local = StairLayout(
                (), start, _add(start, _scale(direction, run)),
                StairAxes((*direction, 0.0),
                          (-direction[1], direction[0], 0.0)),
                layout.base_z + counter * layout.actual_riser,
                (count + 1) * layout.actual_riser,
                layout.base_z + (counter + count + 1) * layout.actual_riser,
                run, count + 1, count, layout.actual_riser, going,
                layout.width, layout.tread_thickness, layout.riser_thickness)
            bodies.append(replace(
                build_underbody_fragment(local, fields),
                ordinal=len(bodies) + 1))
            counter += count
            continue

        cells = (layout.turn_cells[turn_index] if kind == TURN_WINDER else
                 (NominalWinderCell(
                     1, 0.0, 1.0, layout.turns[turn_index].envelope),))
        if layout.ascent_direction == "REVERSE":
            cells = tuple(reversed(cells))
        for cell_index, cell in enumerate(cells):
            counter += 1
            tread_top = layout.base_z + counter * layout.actual_riser
            if kind == TURN_WINDER:
                bodies.append(_build_winder_underbody_prism(
                    layout, turn_index, cells, cell_index, tread_top,
                    counter == 1, len(bodies) + 1))
            else:
                footprint = winder_underbody_support_footprint(
                    layout, turn_index, cell)
                bodies.append(_polygon_prism(
                    footprint, layout.base_z if counter == 1 else
                    tread_top - layout.actual_riser,
                    tread_top - layout.tread_thickness,
                    "UNDERBODY", len(bodies) + 1))
    bodies = tuple(bodies)
    validate_mesh_fragments(bodies)
    return bodies


def _build_winder_underbody_prism(
        layout, turn_index, cells, cell_index, tread_top, at_base, ordinal):
    """Build the shared accepted matching-ring body for one Winder tread."""
    cell = cells[cell_index]
    rear_outer = winder_tread_rear_outer_authority(
        layout, turn_index, cells, cell_index)
    footprint = winder_underbody_support_footprint(
        layout, turn_index, cell, rear_outer)
    top = tread_top - layout.tread_thickness
    bottom = layout.base_z if at_base else tread_top - layout.actual_riser
    if top - bottom <= EPS_LENGTH:
        raise ValueError("Winder UNDERBODYは実蹴上が踏板厚より大きい必要があります。")
    fragment = _polygon_prism(footprint, bottom, top, "UNDERBODY", ordinal)
    validate_mesh_fragments((fragment,))
    return fragment


def _board_strip(start, end, outside_start, outside_end,
                 lower_z, upper_start, upper_end, ordinal):
    """One closed strip with an event-owned lower ring and walking upper edge."""
    plan = (start, end, outside_end, outside_start)
    if polygon_signed_area(plan) < 0.0:
        plan = tuple(reversed(plan))
        tops = (upper_start, upper_end, upper_end, upper_start)
        tops = tuple(reversed(tops))
    else:
        tops = (upper_start, upper_end, upper_end, upper_start)
    vertices = tuple((x, y, lower_z) for x, y in plan) + tuple(
        (point[0], point[1], z) for point, z in zip(plan, tops))
    # A miter can make the sloped upper quad non-planar; triangulate it
    # explicitly so Blender does not choose a different diagonal on reload.
    faces = (_PRISM_FACES[0], (4, 5, 6), (4, 6, 7)) + _PRISM_FACES[2:]
    return MeshFragment("SIDE_BOARD", ordinal, vertices, faces)


def _board_outer_points(frame, footprint, ascent_direction):
    """Follow the accepted body's exterior, including its canonical corner."""
    points = [(station, point) for point in footprint
              if (station := _canonical_outer_station(frame, point)) is not None]
    points.sort(key=lambda item: item[0], reverse=ascent_direction == "REVERSE")
    if len(points) < 2:
        raise ValueError("Winder Side Board exterior pathを解決できません。")
    return tuple(point for _station, point in points)


def _board_outer_distance(frame, point, ascent_direction):
    """Measure a physical point along the complete canonical exterior."""
    station = _canonical_outer_station(frame, point)
    if station is None:
        raise ValueError("Winder Side Board stationがexterior上にありません。")
    first = math.hypot(*_sub(frame.outer_corner, frame.entry_outer))
    second = math.hypot(*_sub(frame.exit_outer, frame.outer_corner))
    distance = (station * first if station <= 1.0 else
                first + (station - 1.0) * second)
    return distance if ascent_direction == "FORWARD" else first + second - distance


@dataclass(frozen=True)
class _SlopedOuterEnvelope:
    """Straight-owned upper lines on the ascent-local Turn exterior."""

    chain: tuple
    corner_station: float
    length: float
    join_station: float
    corner_z: float
    incoming_at_entry: float
    incoming_pitch: float
    outgoing_at_exit: float
    outgoing_pitch: float
    global_fallback: bool

    def upper_z(self, station):
        if self.global_fallback:
            return (self.incoming_at_entry
                    + (self.outgoing_at_exit - self.incoming_at_entry)
                    * station / self.length)
        if station <= self.join_station:
            return self.incoming_at_entry + self.incoming_pitch * station
        if station <= self.corner_station:
            return self.corner_z
        return self.outgoing_at_exit + self.outgoing_pitch * (station - self.length)

    def point_at(self, station):
        if station == self.corner_station:
            return self.chain[1]
        if station == self.length:
            return self.chain[2]
        if station <= self.corner_station:
            a, b = self.chain[:2]
            fraction = station / self.corner_station
        else:
            a, b = self.chain[1:]
            fraction = ((station - self.corner_station)
                        / (self.length - self.corner_station))
        return _add(a, _scale(_sub(b, a), fraction))


def _sloped_board_principal_line(local, fields):
    """Return the analytical run between front closure and rear cap."""
    from .stair_residential_geometry import sloped_side_board_profile

    upper = sloped_side_board_profile(local, fields).outer
    # The accepted residential profile has a front vertical closure, then
    # exactly one principal sloped run, followed by rear cap/closure.
    start, end = upper[1:3]
    if end[0] - start[0] <= EPS_LENGTH:
        raise ValueError("Winder outer SLOPED Side BoardのStraight勾配が不正です。")
    return start, (end[1] - start[1]) / (end[0] - start[0])


def _resolve_winder_outer_sloped_envelope(
        frame, ascent_direction, incoming, outgoing, fields):
    """Join the adjacent Straight slopes through a level canonical corner."""
    chain = ((frame.entry_outer, frame.outer_corner, frame.exit_outer)
             if ascent_direction == "FORWARD" else
             (frame.exit_outer, frame.outer_corner, frame.entry_outer))
    corner_station = math.hypot(*_sub(chain[1], chain[0]))
    length = corner_station + math.hypot(*_sub(chain[2], chain[1]))
    in_start, in_pitch = _sloped_board_principal_line(incoming, fields)
    out_start, out_pitch = _sloped_board_principal_line(outgoing, fields)
    if in_pitch <= EPS_INTERSECTION or out_pitch <= EPS_INTERSECTION:
        raise ValueError("Winder outer SLOPED Side Boardの勾配が正ではありません。")
    incoming_at_entry = (in_start[1] + in_pitch
                         * (incoming.run_length - in_start[0]))
    outgoing_at_exit = out_start[1] - out_pitch * out_start[0]
    corner_z = outgoing_at_exit + out_pitch * (corner_station - length)
    join_station = (corner_z - incoming_at_entry) / in_pitch
    earliest_station = in_start[0] - incoming.run_length
    global_fallback = (join_station < earliest_station - EPS_LENGTH
                       or join_station > corner_station + EPS_LENGTH)
    if global_fallback:
        # The horizontal bridge cannot end at the canonical corner. Use one
        # ascent-local line across the whole Turn, anchored to both Straights.
        corner_z = (incoming_at_entry
                    + (outgoing_at_exit - incoming_at_entry)
                    * corner_station / length)
    else:
        # Only numerical drift at a true endpoint is permitted here. A
        # negative station is a real join on the incoming Straight.
        join_station = max(earliest_station, min(corner_station, join_station))
    return _SlopedOuterEnvelope(
        chain, corner_station, length, join_station, corner_z,
        incoming_at_entry, in_pitch, outgoing_at_exit, out_pitch,
        global_fallback)


def _board_outer_sloped_points(frame, points, ascent_direction, envelope):
    """Split at the bridge join or the global line's physical Turn exit."""
    stations = tuple(_board_outer_distance(frame, point, ascent_direction)
                     for point in points)
    split_station = (envelope.length if envelope.global_fallback
                     else envelope.join_station)
    result = [points[0]]
    for start, end, point in zip(stations, stations[1:], points[1:]):
        if start + EPS_LENGTH < split_station < end - EPS_LENGTH:
            result.append(envelope.point_at(split_station))
        result.append(point)
    return tuple(result)


def _board_offsets(points, thickness, outward_sign):
    """Miter a short outward strip without changing the walking boundary."""
    directions = tuple(_unit(_sub(b, a), "Side Board edge")[0]
                       for a, b in zip(points, points[1:]))
    normals = tuple((outward_sign * -direction[1],
                     outward_sign * direction[0]) for direction in directions)
    result = [_add(points[0], _scale(normals[0], thickness))]
    for index in range(1, len(points) - 1):
        a = _add(points[index], _scale(normals[index - 1], thickness))
        b = _add(points[index], _scale(normals[index], thickness))
        if abs(_cross(directions[index - 1], directions[index])) < EPS_INTERSECTION:
            result.append(a)
        else:
            result.append(_line_intersection(
                a, directions[index - 1], b, directions[index]))
    result.append(_add(points[-1], _scale(normals[-1], thickness)))
    return tuple(result)


def _board_outer_step_return_fragments(
        frame, event_outer, support_outer, reveal, thickness, outward_sign,
        ascent_direction, lower_z, upper_z, first_ordinal):
    """Continue an r2 stepped board above its lower neighbour at a RiseEvent.

    The existing board ends its low visible level at the body support plane.
    The return begins one reveal downhill of the physical divider and reaches
    that support plane without moving or skewing either existing board face.
    """
    chain = ((frame.entry_outer, frame.outer_corner, frame.exit_outer)
             if ascent_direction == "FORWARD" else
             (frame.exit_outer, frame.outer_corner, frame.entry_outer))
    distances = (0.0, math.hypot(*_sub(chain[1], chain[0])),
                 math.hypot(*_sub(chain[1], chain[0]))
                 + math.hypot(*_sub(chain[2], chain[1])))
    event_station = _board_outer_distance(frame, event_outer, ascent_direction)
    support_station = _board_outer_distance(
        frame, support_outer, ascent_direction)
    start_station = event_station - reveal
    if (start_station < -EPS_LENGTH or
            support_station <= event_station + EPS_LENGTH or
            support_station > distances[-1] + EPS_LENGTH):
        raise ValueError("Winder Side Board return区間を解決できません。")

    if abs(start_station - distances[1]) <= EPS_LENGTH:
        start = chain[1]
    elif start_station < distances[1]:
        start = _add(chain[0], _scale(
            _sub(chain[1], chain[0]), start_station / distances[1]))
    else:
        start = _add(chain[1], _scale(
            _sub(chain[2], chain[1]),
            (start_station - distances[1]) / (distances[2] - distances[1])))
    points = ((start, chain[1], support_outer)
              if start_station + EPS_LENGTH < distances[1]
              < support_station - EPS_LENGTH else (start, support_outer))
    outside = list(_board_offsets(points, thickness, outward_sign))
    # Use one canonical miter even when the corner is an endpoint (EQUAL_2/4).
    corner_outside = _board_offsets(chain, thickness, outward_sign)[1]
    for index, point in enumerate(points):
        if point == chain[1]:
            outside[index] = corner_outside
    return tuple(_board_strip(
        a, b, outside[index], outside[index + 1], lower_z,
        upper_z, upper_z, first_ordinal + index)
        for index, (a, b) in enumerate(zip(points, points[1:])))


def _clip_winder_inner_board_start(polygon):
    """Clip an analytical Straight board profile at its Turn start plane."""
    result = []
    for start, end in zip(polygon, polygon[1:] + polygon[:1]):
        start_in = start[0] >= -EPS_LENGTH
        end_in = end[0] >= -EPS_LENGTH
        if start_in:
            result.append(start)
        if start_in != end_in:
            parameter = -start[0] / (end[0] - start[0])
            result.append((0.0, start[1] + parameter * (end[1] - start[1])))
    return tuple(result)


def _winder_inner_straight_board_fragment(
        local, side, fields, *, clip_start=False, terminal_z=None):
    """Resolve both Winder-inner Straight terminals before one extrusion."""
    from .stair_geometry import extrude_xz_profile, validate_simple_polygon
    from .stair_residential_geometry import (
        side_board_profile, sloped_side_board_profile)

    profile = (sloped_side_board_profile(local, fields)
               if fields.side_board_mode == "SLOPED" else
               side_board_profile(local, fields))
    polygon = profile.polygon
    if terminal_z is not None:
        outer = profile.outer
        rear = local.run_length + local.riser_thickness
        cap_index = max(index for index, point in enumerate(outer)
                        if point[0] < rear - EPS_LENGTH)
        cap = outer[cap_index]
        if terminal_z <= cap[1] + EPS_LENGTH:
            raise ValueError("Winder inner Side Board terminal高さが不足しています。")
        elevated = (outer[:cap_index + 1]
                    + ((cap[0], terminal_z), (rear, terminal_z), outer[-1]))
        polygon = validate_simple_polygon(elevated + tuple(reversed(profile.lower)))
    if clip_start:
        polygon = validate_simple_polygon(_clip_winder_inner_board_start(polygon))
    thickness = float(fields.side_board_thickness_mm) / _MM_PER_METRE
    half = local.width / 2.0
    if side == "LEFT":
        y_min, y_max, ordinal = half, half + thickness, 1
    elif side == "RIGHT":
        y_min, y_max, ordinal = -half - thickness, -half, 2
    else:
        raise ValueError("Side Board sideはLEFTまたはRIGHTである必要があります。")
    fragment = extrude_xz_profile(
        polygon, y_min, y_max, part_type="SIDE_BOARD", ordinal=ordinal)
    forward, left = local.axes.forward, local.axes.left
    vertices = tuple((local.lower_xy[0] + forward[0] * x + left[0] * y,
                      local.lower_xy[1] + forward[1] * x + left[1] * y, z)
                     for x, y, z in fragment.vertices)
    result = MeshFragment("SIDE_BOARD", ordinal, vertices, fragment.faces)
    validate_mesh_fragments((result,))
    return result


def _winder_outer_sloped_straight_fragment(
        local, side, fields, *, start_envelope=None, end_envelope=None):
    """Join one outer Straight profile to adjacent analytical Turn envelopes."""
    from .stair_geometry import extrude_xz_profile, validate_simple_polygon
    from .stair_residential_geometry import sloped_side_board_profile

    profile = sloped_side_board_profile(local, fields)
    start, pitch = _sloped_board_principal_line(local, fields)
    rear = local.run_length + local.riser_thickness
    upper = list(profile.outer[:2])
    if start_envelope is not None and start_envelope.global_fallback:
        # The outgoing board starts reveal downhill of the physical exit.
        # Its overlap follows the global Turn line through the accepted rear
        # body support. A local transition then rejoins the unchanged main
        # Straight principal slope before its rear cap.
        front_x = upper[1][0]
        upper[1] = (front_x,
                    start_envelope.upper_z(start_envelope.length + front_x))
        upper.append((0.0, start_envelope.outgoing_at_exit))
        support_x = local.riser_thickness
        upper.append((support_x,
                      start_envelope.upper_z(start_envelope.length + support_x)))
        main_end = profile.outer[2][0]
        if main_end - support_x <= EPS_LENGTH:
            raise ValueError("Winder outer SLOPED Side Boardのoutgoing support区間が不足しています。")
        recover_x = support_x + min(
            -front_x, (main_end - support_x) / 2.0)
        upper.append((recover_x,
                      start[1] + pitch * (recover_x - start[0])))
    if end_envelope is None:
        upper.extend(profile.outer[2:])
    elif end_envelope.global_fallback:
        # Preserve the incoming principal pitch to physical Turn entry.
        # The existing rear support extends riser_thickness into the Turn.
        upper.extend((profile.outer[2],
                      (local.run_length, end_envelope.incoming_at_entry),
                      (rear, end_envelope.upper_z(local.riser_thickness)),
                      profile.outer[-1]))
    elif end_envelope.join_station < local.riser_thickness - EPS_LENGTH:
        # The level bridge starts before this board's rear support plane.
        join_x = local.run_length + end_envelope.join_station
        upper.extend(((join_x, end_envelope.corner_z),
                      (rear, end_envelope.corner_z), profile.outer[-1]))
    else:
        rear_z = start[1] + pitch * (rear - start[0])
        upper.extend((profile.outer[2], (rear, rear_z), profile.outer[-1]))
    upper = tuple(upper)
    polygon = validate_simple_polygon(upper + tuple(reversed(profile.lower)))
    thickness = float(fields.side_board_thickness_mm) / _MM_PER_METRE
    half = local.width / 2.0
    if side == "LEFT":
        y_min, y_max, ordinal = half, half + thickness, 1
    elif side == "RIGHT":
        y_min, y_max, ordinal = -half - thickness, -half, 2
    else:
        raise ValueError("Side Board sideはLEFTまたはRIGHTである必要があります。")
    fragment = extrude_xz_profile(
        polygon, y_min, y_max, part_type="SIDE_BOARD", ordinal=ordinal)
    forward, left = local.axes.forward, local.axes.left
    vertices = tuple((local.lower_xy[0] + forward[0] * x + left[0] * y,
                      local.lower_xy[1] + forward[1] * x + left[1] * y, z)
                     for x, y, z in fragment.vertices)
    result = MeshFragment("SIDE_BOARD", ordinal, vertices, fragment.faces)
    validate_mesh_fragments((result,))
    return result


def _winder_board_straight_local(layout, payload, event_count):
    """Build the accepted ascent-local Straight context for a board."""
    from .stair_geometry import StairAxes, StairLayout

    start, direction, run, count = payload
    if not count:
        raise ValueError("Winder outer SLOPED Side Boardに隣接するStraightがありません。")
    return StairLayout(
        (), start, _add(start, _scale(direction, run)),
        StairAxes((*direction, 0.0),
                  (-direction[1], direction[0], 0.0)),
        layout.base_z + event_count * layout.actual_riser,
        (count + 1) * layout.actual_riser,
        layout.base_z + (event_count + count + 1) * layout.actual_riser,
        run, count + 1, count, layout.actual_riser, run / count,
        layout.width, layout.tread_thickness, layout.riser_thickness)


def build_winder_side_board_fragments(layout, fields):
    """Add ordinary boards after the accepted top and body have been prepared."""
    from .stair_residential import validate_side_board_reveal
    from .stair_residential_geometry import build_side_board_fragment

    thickness = float(fields.side_board_thickness_mm) / _MM_PER_METRE
    goings = tuple(run / count for run, count in zip(
        layout.straight_runs, layout.straight_allocation) if count)
    reveal = validate_side_board_reveal(fields, layout.actual_riser, min(goings))
    path = layout.canonical_path
    components = []
    for index, (a, b) in enumerate(zip(path, path[1:])):
        direction, _ = _unit(_sub(b.xy, a.xy))
        cut = layout.turns[index - 1].cutback if index else 0.0
        start = _add(a.xy, _scale(direction, cut))
        components.append(("STRAIGHT", index,
                           (start, direction, layout.straight_runs[index],
                            layout.straight_allocation[index])))
        if index < len(layout.turn_specs):
            components.append((layout.turn_specs[index].turn_mode, index, None))
    if layout.ascent_direction == "REVERSE":
        components.reverse()
        components = [
            (kind, index, (_add(payload[0], _scale(payload[1], payload[2])),
                           _scale(payload[1], -1.0), payload[2], payload[3])
             if kind == "STRAIGHT" else None)
            for kind, index, payload in components]

    result, event_count, step_returns = [], 0, []
    sloped_envelopes = {}
    enabled = tuple(side for side, on in (
        ("LEFT", fields.left_side_board_enabled),
        ("RIGHT", fields.right_side_board_enabled)) if on)
    def inner_side(turn_index):
        frame = layout.turns[turn_index]
        theta = frame.theta * (1 if layout.ascent_direction == "FORWARD" else -1)
        return "LEFT" if theta > 0.0 else "RIGHT"

    for position, (kind, turn_index, payload) in enumerate(components):
        if kind == "STRAIGHT":
            start, direction, run, count = payload
            if not count:
                continue
            local = _winder_board_straight_local(layout, payload, event_count)
            for side in enabled:
                start_inner = (position > 0
                               and components[position - 1][0] == TURN_WINDER
                               and side == inner_side(components[position - 1][1]))
                end_inner = (position + 1 < len(components)
                             and components[position + 1][0] == TURN_WINDER
                             and side == inner_side(components[position + 1][1]))
                terminal_z = None
                if end_inner:
                    next_turn = components[position + 1][1]
                    terminal_z = (layout.base_z + (event_count + count
                                  + len(layout.turn_cells[next_turn]))
                                  * layout.actual_riser)
                end_outer_sloped = (
                    fields.side_board_mode == "SLOPED"
                    and position + 1 < len(components)
                    and components[position + 1][0] == TURN_WINDER
                    and side != inner_side(components[position + 1][1]))
                start_outer_sloped = (
                    fields.side_board_mode == "SLOPED"
                    and position > 0
                    and components[position - 1][0] == TURN_WINDER
                    and side != inner_side(components[position - 1][1]))
                if start_inner or end_inner:
                    board = _winder_inner_straight_board_fragment(
                        local, side, fields, clip_start=start_inner,
                        terminal_z=terminal_z)
                else:
                    start_envelope = (sloped_envelopes[position - 1]
                                      if start_outer_sloped else None)
                    end_envelope = None
                    if end_outer_sloped:
                        next_position = position + 1
                        next_turn = components[next_position][1]
                        if (next_position + 1 == len(components)
                                or components[next_position + 1][0] != "STRAIGHT"):
                            raise ValueError("Winder outer SLOPED Side Boardのoutgoing Straightがありません。")
                        end_envelope = sloped_envelopes.get(next_position)
                        if end_envelope is None:
                            following = components[next_position + 1][2]
                            outgoing = _winder_board_straight_local(
                                layout, following, event_count + count
                                + len(layout.turn_cells[next_turn]))
                            end_envelope = _resolve_winder_outer_sloped_envelope(
                                layout.turns[next_turn], layout.ascent_direction,
                                local, outgoing, fields)
                            sloped_envelopes[next_position] = end_envelope
                    board = (_winder_outer_sloped_straight_fragment(
                        local, side, fields, start_envelope=start_envelope,
                        end_envelope=end_envelope)
                        if end_envelope is not None
                        or (start_envelope is not None
                            and start_envelope.global_fallback) else
                        build_side_board_fragment(local, side, fields))
                result.append(replace(board, ordinal=len(result) + 1))
            event_count += count
            continue
        cells = layout.turn_cells[turn_index]
        if layout.ascent_direction == "REVERSE":
            cells = tuple(reversed(cells))
        frame = layout.turns[turn_index]
        ascent_theta = frame.theta * (1 if layout.ascent_direction == "FORWARD" else -1)
        outer_side = "RIGHT" if ascent_theta > 0.0 else "LEFT"
        outward_sign = -1.0 if ascent_theta > 0.0 else 1.0
        envelope = None
        if outer_side in enabled and fields.side_board_mode == "SLOPED":
            envelope = sloped_envelopes[position]
        for cell_index, cell in enumerate(cells):
            event_count += 1
            top = layout.base_z + event_count * layout.actual_riser
            rear = winder_tread_rear_outer_authority(
                layout, turn_index, cells, cell_index)
            footprint = winder_underbody_support_footprint(
                layout, turn_index, cell, rear)
            lower_z = (layout.base_z if event_count == 1 else
                       top - layout.actual_riser)
            boundaries = physical_cell_boundaries(
                cell, layout.ascent_direction, frame.inner_pivot)
            front_station = _board_outer_distance(
                frame, boundaries.front[1], layout.ascent_direction)
            rear_station = _board_outer_distance(
                frame, boundaries.rear[1], layout.ascent_direction)
            if outer_side not in enabled:
                continue
            points = _board_outer_points(
                frame, footprint, layout.ascent_direction)
            if envelope is not None:
                points = _board_outer_sloped_points(
                    frame, points, layout.ascent_direction, envelope)
            outside = _board_offsets(points, thickness, outward_sign)
            if fields.side_board_mode == "STEPPED" and cell_index:
                step_returns.append((
                    frame, boundaries.front[1], points[0], reveal,
                    thickness, outward_sign, layout.ascent_direction,
                    top - layout.actual_riser + reveal, top + reveal))
            for i, (a, b) in enumerate(zip(points, points[1:])):
                if envelope is not None:
                    upper_a = envelope.upper_z(_board_outer_distance(
                        frame, a, layout.ascent_direction))
                    upper_b = envelope.upper_z(_board_outer_distance(
                        frame, b, layout.ascent_direction))
                else:
                    upper_a = upper_b = top + reveal
                board = _board_strip(
                    a, b, outside[i], outside[i + 1], lower_z,
                    upper_a, upper_b, len(result) + 1)
                result.append(board)
    for spec in step_returns:
        result.extend(_board_outer_step_return_fragments(
            *spec, len(result) + 1))
    result = tuple(result)
    validate_mesh_fragments(result)
    return result


def winder_underbody_support_footprint(
        layout, turn_index, cell, rear_outer_authority=None):
    """Return the accepted Stage-3A Riser-rear Winder support plan."""
    boundaries = physical_cell_boundaries(
        cell, layout.ascent_direction,
        layout.turns[turn_index].inner_pivot)
    origin, outer = boundaries.front
    direction, _ = _unit(_sub(outer, origin), "Winder body boundary")
    centroid = _centroid(cell.polygon)
    side = (1.0 if _cross(direction, _sub(centroid, origin)) >= 0.0 else -1.0)
    distance = lambda point: side * _cross(direction, _sub(point, origin))
    # The Riser owns the exposed front strip.  Body support begins at its
    # hidden rear plane and never inherits the physical Tread/nosing outline.
    footprint = _clip_polygon_scalar(
        tuple(cell.polygon), distance, True, layout.riser_thickness)
    if len(footprint) < 3 or polygon_area(footprint) <= EPS_AREA:
        raise ValueError("Winder UNDERBODY setback planを解決できません。")
    if rear_outer_authority is not None:
        rear_origin, rear_outer = physical_cell_boundaries(
            cell, layout.ascent_direction,
            layout.turns[turn_index].inner_pivot).rear
        rear_direction, _ = _unit(
            _sub(rear_outer, rear_origin), "Winder body rear boundary")
        candidates = tuple(
            index for index, point in enumerate(footprint)
            if abs(_cross(rear_direction,
                          _sub(point, rear_origin))) <= EPS_LENGTH)
        if not candidates:
            raise ValueError("Winder UNDERBODY rear exterior pointを解決できません。")
        target = max(candidates, key=lambda index: math.hypot(
            *_sub(footprint[index], rear_origin)))
        footprint = tuple(
            tuple(rear_outer_authority) if index == target else point
            for index, point in enumerate(footprint))
        if polygon_area(footprint) <= EPS_AREA:
            raise ValueError("Winder UNDERBODY rear support planが不正です。")
    return preserve_canonical_outer_chain(layout.turns[turn_index], footprint)


def _turn_corner_fraction(frame):
    """Return the signed angular station of the envelope outer corner."""
    entry, _ = _unit(_sub(frame.entry_outer, frame.inner_pivot), "entry ray")
    corner, _ = _unit(_sub(frame.outer_corner, frame.inner_pivot), "corner ray")
    angle = math.atan2(_cross(entry, corner), _dot(entry, corner))
    if frame.theta < 0.0 and angle > 0.0:
        angle -= 2.0 * math.pi
    if frame.theta > 0.0 and angle < 0.0:
        angle += 2.0 * math.pi
    return angle / frame.theta


def canonical_turn_endpoint_z(ascent_direction, ascent_entry_z, ascent_exit_z):
    """Map ascent-local interface elevations onto canonical Turn endpoints."""
    if ascent_direction == "FORWARD":
        return ascent_entry_z, ascent_exit_z
    if ascent_direction == "REVERSE":
        return ascent_exit_z, ascent_entry_z
    raise ValueError("不明な上り方向です。")


def resolve_sloped_turn_stations(
        layout, turn_index, canonical_entry_z, canonical_exit_z):
    """Resolve a Turn using canonical frame.entry/frame.exit elevations.

    Divider elevations follow RiseEvent order, not angular distance.  The
    envelope corner is an extra geometry station only and is interpolated
    inside its containing event interval.  A short deterministic relief chord
    keeps the lower surface away from the singular multi-Z pivot.

    The elevation arguments always describe canonical ``fraction=0`` entry
    and ``fraction=1`` exit.  A REVERSE caller must map its ascent-local
    endpoints with :func:`canonical_turn_endpoint_z` first.
    """
    frame = layout.turns[turn_index]
    cells = layout.turn_cells[turn_index]
    if not cells:
        return ()
    fractions = [cells[0].front_fraction]
    fractions.extend(cell.rear_fraction for cell in cells)
    corner_fraction = _turn_corner_fraction(frame)
    if (EPS_ANGLE < corner_fraction < 1.0 - EPS_ANGLE
            and all(abs(corner_fraction - value) > EPS_ANGLE
                    for value in fractions)):
        fractions.append(corner_fraction)
    fractions.sort()

    entry_ray, entry_radius = _unit(
        _sub(frame.entry_outer, frame.inner_pivot), "entry ray")
    _exit_ray, exit_radius = _unit(
        _sub(frame.exit_outer, frame.inner_pivot), "exit ray")
    rho = max(layout.riser_thickness, 10.0 * EPS_LENGTH)
    if rho >= min(entry_radius, exit_radius) - EPS_LENGTH:
        raise ValueError("GEOMETRY_INVALID: Winder pivot relief is too large")
    j0 = _add(frame.inner_pivot, _scale(entry_ray, rho))
    exit_ray = _rotate(entry_ray, frame.theta)
    j1 = _add(frame.inner_pivot, _scale(exit_ray, rho))
    count = len(cells)
    stations = []
    for fraction in fractions:
        primary = next((index for index, value in enumerate(
                        (cells[0].front_fraction,)
                        + tuple(cell.rear_fraction for cell in cells))
                        if abs(value - fraction) <= EPS_ANGLE), None)
        if primary is not None:
            event_fraction = primary / count
        else:
            cell_index = next(index for index, cell in enumerate(cells)
                              if cell.front_fraction < fraction
                              < cell.rear_fraction)
            cell = cells[cell_index]
            local = ((fraction - cell.front_fraction)
                     / (cell.rear_fraction - cell.front_fraction))
            event_fraction = (cell_index + local) / count
        lower_z = sloped_turn_lower_z_at_fraction(
            cells, canonical_entry_z, canonical_exit_z, fraction)
        ray = _rotate(entry_ray, fraction * frame.theta)
        inner_hit = _ray_segment_intersection(frame.inner_pivot, ray, j0, j1)
        if inner_hit is None:
            # End rays meet the chord at an endpoint and can be numerically
            # parallel to its final ulp; reuse that exact endpoint authority.
            inner = j0 if fraction <= EPS_ANGLE else j1
        else:
            inner = inner_hit[1]
        outer = (frame.outer_corner if abs(fraction - corner_fraction) <= EPS_ANGLE
                 else divider_outer_point(frame, fraction))
        stations.append(SlopedTurnStation(
            fraction, inner, outer, lower_z, event_fraction))
    return tuple(stations)


def _turn_fraction_at_point(frame, point):
    """Return the canonical angular fraction of a Turn-plan point."""
    entry, _ = _unit(_sub(frame.entry_outer, frame.inner_pivot), "entry ray")
    ray, _ = _unit(_sub(point, frame.inner_pivot), "underbody station ray")
    angle = math.atan2(_cross(entry, ray), _dot(entry, ray))
    if frame.theta < 0.0 and angle > 0.0:
        angle -= 2.0 * math.pi
    if frame.theta > 0.0 and angle < 0.0:
        angle += 2.0 * math.pi
    return min(1.0, max(0.0, angle / frame.theta))


def sloped_turn_lower_z_at_fraction(
        cells, canonical_entry_z, canonical_exit_z, fraction):
    """Evaluate the same event-linear field used by shared Turn stations."""
    fraction = min(1.0, max(0.0, float(fraction)))
    count = len(cells)
    if not count:
        raise ValueError("Winder lower fieldにはcellが必要です。")
    if fraction <= cells[0].front_fraction + EPS_ANGLE:
        event_fraction = 0.0
    elif fraction >= cells[-1].rear_fraction - EPS_ANGLE:
        event_fraction = 1.0
    else:
        index = next(index for index, cell in enumerate(cells)
                     if cell.front_fraction - EPS_ANGLE <= fraction
                     <= cell.rear_fraction + EPS_ANGLE)
        cell = cells[index]
        local = ((fraction - cell.front_fraction)
                 / (cell.rear_fraction - cell.front_fraction))
        event_fraction = (index + local) / count
    return (canonical_entry_z
            + (canonical_exit_z - canonical_entry_z) * event_fraction)


def _clip_polygon_field(polygon, field, threshold=EPS_LENGTH):
    """Clip a polygon to ``field >= threshold`` with deterministic bisection."""
    result = []
    previous = polygon[-1]
    previous_value = field(previous) - threshold
    previous_inside = previous_value >= 0.0
    for current in polygon:
        current_value = field(current) - threshold
        current_inside = current_value >= 0.0
        if current_inside != previous_inside:
            low, high = (previous, current)
            low_value = previous_value
            for _unused in range(64):
                midpoint = _scale(_add(low, high), 0.5)
                midpoint_value = field(midpoint) - threshold
                if (midpoint_value >= 0.0) == (low_value >= 0.0):
                    low, low_value = midpoint, midpoint_value
                else:
                    high = midpoint
            result.append(_scale(_add(low, high), 0.5))
        if current_inside:
            result.append(current)
        previous = current
        previous_value = current_value
        previous_inside = current_inside
    return _deduplicate(tuple(result))


def _sloped_cell_fragment(plan, lower, top_z, ordinal):
    """Build one tread-owned body with horizontal contact and sloped soffit."""
    plan = tuple(plan)
    lower = tuple(lower)
    if polygon_signed_area(plan) < 0.0:
        plan = tuple(reversed(plan))
        lower = tuple(reversed(lower))
    if max(lower) > top_z - EPS_LENGTH * 0.5:
        raise ValueError("Winder SLOPED UNDERBODYのcontact clearanceが不足しています。")
    size = len(plan)
    vertices = tuple((point[0], point[1], z)
                     for point, z in zip(plan, lower)) + tuple(
                         (point[0], point[1], top_z) for point in plan)
    faces = [(0, index + 1, index) for index in range(1, size - 1)]
    faces.append(tuple(range(size, size * 2)))
    for index in range(size):
        following = (index + 1) % size
        faces.extend(((index, following, following + size),
                      (index, following + size, index + size)))
    return MeshFragment("UNDERBODY", ordinal, vertices, tuple(faces))


def build_sloped_closed_underbody_fragments(layout, _top_fragments, fields):
    """Build accepted Straight slopes plus validated prismatic Winder bodies."""
    from .stair_residential import (
        validate_stepped_closure_depth,
        validate_stepped_underbody_thickness,
    )
    from .stair_residential_geometry import build_underbody_fragment
    from .stair_geometry import StairAxes, StairLayout

    validate_stepped_underbody_thickness(
        fields, layout.actual_riser, layout.tread_thickness,
        layout.riser_thickness)
    goings = tuple(run / count for run, count in zip(
        layout.straight_runs, layout.straight_allocation) if count)
    depth = validate_stepped_closure_depth(
        fields, layout.actual_riser, min(goings))
    if depth - layout.tread_thickness <= EPS_LENGTH:
        raise ValueError(
            "UNDERBODY closure depthは踏板厚より大きい必要があります。")

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
        components.append(["STRAIGHT", index, segment])
        if index < len(layout.turn_specs):
            components.append([layout.turn_specs[index].turn_mode, index, None])
    if layout.ascent_direction == "REVERSE":
        components.reverse()
        for component in components:
            if component[0] == "STRAIGHT":
                start, direction, run, count = component[2]
                component[2] = (_add(start, _scale(direction, run)),
                                _scale(direction, -1.0), run, count)

    bodies, counter = [], 0
    component_counters = {}
    for position, (kind, _index, payload) in enumerate(components):
        component_counters[position] = counter
        if kind != "STRAIGHT":
            counter += (len(layout.turn_cells[_index]) if kind == TURN_WINDER
                        else 1)
            continue
        start, direction, run, count = payload
        if not count:
            continue
        going = run / count
        local = StairLayout(
            (), start, _add(start, _scale(direction, run)),
            StairAxes((*direction, 0.0),
                      (-direction[1], direction[0], 0.0)),
            layout.base_z + counter * layout.actual_riser,
            (count + 1) * layout.actual_riser,
            layout.base_z + (counter + count + 1) * layout.actual_riser,
            run, count + 1, count, layout.actual_riser, going,
            layout.width, layout.tread_thickness, layout.riser_thickness)
        bodies.append(replace(build_underbody_fragment(local, fields),
                              ordinal=len(bodies) + 1))
        counter += count

    # SLOPED_CLOSED differs from STEPPED_CLOSED on ordinary Straight Flights.
    # Winder Turns deliberately share the same validated per-tread prism.
    for position, (kind, turn_index, _payload) in enumerate(components):
        if kind != TURN_WINDER:
            continue
        cells = layout.turn_cells[turn_index]
        if layout.ascent_direction == "REVERSE":
            cells = tuple(reversed(cells))
        start_counter = component_counters[position]
        for cell_index, _cell in enumerate(cells):
            event_index = start_counter + cell_index + 1
            tread_top = layout.base_z + event_index * layout.actual_riser
            bodies.append(_build_winder_underbody_prism(
                layout, turn_index, cells, cell_index, tread_top,
                event_index == 1, len(bodies) + 1))

    bodies = tuple(bodies)
    validate_mesh_fragments(bodies)
    return bodies


def prepare_turn_residential_geometry(
        points, ascent_direction, base_z_mm, floor_to_floor_mm, riser_count,
        stair_width_mm, tread_thickness_mm, riser_thickness_mm, *,
        fields, point_ids=None, winder_pattern=WINDER_EQUAL_3,
        turn_mode=TURN_WINDER, turn_specs=None, allocation=None):
    """Prepare schema-5 closed geometry and ordinary Winder Side Boards."""
    from .stair_residential import (
        SLOPED_CLOSED, STEPPED_CLOSED, ResidentialFields, residential_fields,
        validate_mode_data,
    )

    values = (fields if isinstance(fields, ResidentialFields)
              else residential_fields(fields))
    validate_mode_data("STANDARD_RESIDENTIAL", WINDER_SCHEMA_VERSION, values)
    if values.underside_mode not in (STEPPED_CLOSED, SLOPED_CLOSED):
        raise ScopeUnsupportedError("schema-5 underside modeは未対応です。")
    layout = resolve_winder_layout(
        points, ascent_direction, base_z_mm, floor_to_floor_mm, riser_count,
        stair_width_mm, tread_thickness_mm, riser_thickness_mm,
        point_ids=point_ids, winder_pattern=winder_pattern,
        turn_mode=turn_mode, turn_specs=turn_specs, allocation=allocation,
        tread_front_overhang_mm=values.tread_front_overhang_mm,
        tread_front_edge_mode=values.tread_front_edge_mode,
        tread_front_edge_size_mm=values.tread_front_edge_size_mm)
    boards_on = values.left_side_board_enabled or values.right_side_board_enabled
    if boards_on and layout.u_classification == "COMPACT_U":
        raise ScopeUnsupportedError(
            "SCOPE_UNSUPPORTED: Compact-U Side BoardはStage 3D deferredです。")
    if boards_on and any(spec.turn_mode != TURN_WINDER
                         for spec in layout.turn_specs):
        raise ScopeUnsupportedError(
            "SCOPE_UNSUPPORTED: schema-5 mixed Landing Side Boardは未対応です。")
    top = build_winder_fragments(layout)
    underbody = (build_sloped_closed_underbody_fragments(layout, top, values)
                 if values.underside_mode == SLOPED_CLOSED else
                 build_stepped_closed_underbody_fragments(layout, top, values))
    boards = build_winder_side_board_fragments(layout, values) if boards_on else ()
    fragments = top + underbody + boards
    mesh = assemble_stair_mesh(fragments)
    return layout, fragments, StairMeshData(
        mesh.vertices, mesh.faces, mesh.face_roles)


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
