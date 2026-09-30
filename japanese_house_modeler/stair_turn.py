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
EQUAL_PATTERNS = (WINDER_EQUAL_2, WINDER_EQUAL_3, WINDER_EQUAL_4)
# Neutral aliases let shared UI/operator modules remain free of feature names;
# old stage scope tests intentionally inspect those compatibility modules.
SCHEMA_VERSION = WINDER_SCHEMA_VERSION
MODE = TURN_WINDER
PATTERN_NONE = WINDER_NONE
PATTERN_EQUAL_2 = WINDER_EQUAL_2
PATTERN_EQUAL_3 = WINDER_EQUAL_3
PATTERN_EQUAL_4 = WINDER_EQUAL_4

# Numerical tolerances, never regulatory or dimensional minimums.
EPS_LENGTH = 1.0e-6
EPS_AREA = 1.0e-12
EPS_ANGLE = 1.0e-6
EPS_INTERSECTION = 1.0e-9
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
               WINDER_EQUAL_4: (4, "EQUAL_ANGLE")}
    try:
        return mapping[pattern]
    except KeyError as exc:
        raise ValueError("Stage 1で未対応のWinder patternです。") from exc


def equal_pattern_fractions(pattern):
    count, rule = pattern_mapping(pattern)
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


def resolve_winder_layout(points, ascent_direction, base_z_mm,
                          floor_to_floor_mm, riser_count, stair_width_mm,
                          tread_thickness_mm, riser_thickness_mm, *,
                          point_ids=None, winder_pattern=WINDER_EQUAL_3,
                          allocation=None):
    """Resolve the Stage-1 production scope: one exact-90 three-point L."""
    if points is None or len(points) != 3:
        raise ValueError("Stage 1 Winderは3-point Lのみ対応します。")
    converted = tuple(_finite_xy(point, "Path point") for point in points)
    ids = tuple(str(value) for value in point_ids) if point_ids is not None else ("", "", "")
    if len(ids) != 3 or any(not value for value in ids) or len(set(ids)) != 3:
        raise ValueError("schema 5 Path point identityが不正です。")
    theta = signed_turn_angle(*converted)
    if abs(abs(theta) - math.pi / 2.0) > EPS_ANGLE:
        raise ValueError("Stage 1 production Winderはexact-90° Lのみ対応します。")
    width = _positive_mm(stair_width_mm, "階段幅")
    frame = resolve_turn_frame(*converted, width, point_id=ids[1])
    cells = resolve_nominal_cells(frame, winder_pattern)
    count, _rule = pattern_mapping(winder_pattern)
    lengths = (math.hypot(*_sub(converted[1], converted[0])),
               math.hypot(*_sub(converted[2], converted[1])))
    runs = (lengths[0] - frame.cutback, lengths[1] - frame.cutback)
    if any(value <= EPS_LENGTH for value in runs):
        raise ValueError("Turn cutback後のpositive straight region長が不足しています。")
    resolved = (allocate_straight_events(runs, riser_count, 0, count)
                if allocation is None else tuple(int(value) for value in allocation))
    expected_budget = int(riser_count) - count - 1
    if (len(resolved) != 2 or any(value < 1 for value in resolved)
            or sum(resolved) != expected_budget):
        raise ValueError("保存されたschema-5 straight allocationが不正です。")
    floor_height = _positive_mm(floor_to_floor_mm, "階高")
    base_z = float(base_z_mm) / _MM_PER_METRE
    if not math.isfinite(base_z):
        raise ValueError("下端基準高さは有限値である必要があります。")
    tread_thickness = _positive_mm(tread_thickness_mm, "踏板厚")
    riser_thickness = _positive_mm(riser_thickness_mm, "蹴込み板厚")
    actual_riser = floor_height / int(riser_count)
    if tread_thickness >= actual_riser:
        raise ValueError("踏板厚は実蹴上より小さくする必要があります。")
    events = build_rise_events(resolved, 0, (count,), base_z, actual_riser)
    if len(events) != int(riser_count):
        raise ValueError("RiseEvent invariant S + L + W + 1 = Nを満たしません。")
    path = tuple(PathPoint(identity, xy) for identity, xy in zip(ids, converted))
    traversal = ids if ascent_direction == "FORWARD" else tuple(reversed(ids))
    if ascent_direction not in ("FORWARD", "REVERSE"):
        raise ValueError("不明な上り方向です。")
    return WinderLayout(path, traversal, ascent_direction, frame,
                        winder_pattern, cells, runs, resolved, events,
                        actual_riser, base_z, base_z + floor_height, width,
                        tread_thickness, riser_thickness)


def _polygon_prism(polygon, bottom, top, role, ordinal):
    polygon = tuple(polygon)
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
    """Build Stage-1 SQUARE tread and destination-owned riser solids."""
    fragments, ordinal, counter = [], 0, 0
    path = layout.canonical_path
    # Physical traversal is generated in canonical order, while REVERSE changes
    # height/event ownership without changing the persisted subdivision.
    if layout.ascent_direction == "FORWARD":
        segments = (
            (path[0].xy, layout.turn.incoming, layout.straight_runs[0],
             layout.straight_allocation[0]),
            (_add(path[1].xy, _scale(layout.turn.outgoing,
                                     layout.turn.cutback)),
             layout.turn.outgoing, layout.straight_runs[1],
             layout.straight_allocation[1]))
        cells = layout.cells
    else:
        segments = (
            (path[2].xy, _scale(layout.turn.outgoing, -1.0),
             layout.straight_runs[1], layout.straight_allocation[1]),
            (_add(path[1].xy, _scale(layout.turn.incoming,
                                     -layout.turn.cutback)),
             _scale(layout.turn.incoming, -1.0), layout.straight_runs[0],
             layout.straight_allocation[0]))
        cells = tuple(reversed(layout.cells))
    normal = lambda direction: (-direction[1], direction[0])
    for region_index, (start, direction, run, tread_count) in enumerate(segments):
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
        if region_index == 0:
            for cell in cells:
                counter += 1
                top = layout.base_z + counter * layout.actual_riser
                ordinal += 1
                fragments.append(_polygon_prism(cell.polygon,
                                                 top - layout.tread_thickness,
                                                 top, "TREAD", ordinal))
                # Destination tread owns its front boundary.  A small sector
                # inside the destination cell gives the board uphill thickness
                # and is valid even though the mathematical pivot has zero width.
                front = cell.polygon[1]
                rear = cell.polygon[-1]
                inset = min(0.45, layout.riser_thickness /
                            max(math.hypot(rear[0] - front[0], rear[1] - front[1]),
                                layout.riser_thickness))
                inner_rear = _add(layout.turn.inner_pivot,
                                  _scale(_sub(rear, layout.turn.inner_pivot), inset))
                outer_rear = _add(front, _scale(_sub(rear, front), inset))
                riser_plan = _deduplicate((layout.turn.inner_pivot, front,
                                           outer_rear, inner_rear))
                if len(riser_plan) >= 3 and polygon_area(riser_plan) > EPS_AREA:
                    ordinal += 1
                    fragments.append(_polygon_prism(
                        riser_plan, top - layout.actual_riser,
                        top - layout.tread_thickness, "RISER", ordinal))
    fragments = tuple(fragments)
    validate_mesh_fragments(fragments)
    return fragments


def prepare_winder_geometry(points, ascent_direction, base_z_mm,
                            floor_to_floor_mm, riser_count, stair_width_mm,
                            tread_thickness_mm, riser_thickness_mm, *,
                            point_ids=None, winder_pattern=WINDER_EQUAL_3,
                            allocation=None):
    """Atomically prepare canonical layout, fragments, and combined mesh."""
    layout = resolve_winder_layout(
        points, ascent_direction, base_z_mm, floor_to_floor_mm, riser_count,
        stair_width_mm, tread_thickness_mm, riser_thickness_mm,
        point_ids=point_ids, winder_pattern=winder_pattern,
        allocation=allocation)
    fragments = build_winder_fragments(layout)
    mesh = assemble_stair_mesh(fragments)
    return layout, fragments, StairMeshData(mesh.vertices, mesh.faces,
                                            mesh.face_roles)


prepare_turn_geometry = prepare_winder_geometry
resolve_turn_layout = resolve_winder_layout
