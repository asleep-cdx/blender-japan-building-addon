"""Pure canonical, layout, and limited solid geometry helpers for Stairs."""

from dataclasses import dataclass
import math
import uuid


MIN_STAIR_PATH_LENGTH_M = 1.0e-6
STAGE1_PATH_POINT_COUNT = 2
IDENTITY_LOCATION = (0.0, 0.0, 0.0)
IDENTITY_ROTATION = (0.0, 0.0, 0.0)
IDENTITY_SCALE = (1.0, 1.0, 1.0)
_MM_PER_METRE = 1000.0
_BOX_FACES = (
    (0, 3, 2, 1), (4, 5, 6, 7),
    (0, 1, 5, 4), (1, 2, 6, 5),
    (2, 3, 7, 6), (3, 0, 4, 7),
)


@dataclass(frozen=True)
class StairAxes:
    """Resolved world-plan axes, independent from Blender mesh state."""

    forward: tuple
    left: tuple
    up: tuple = (0.0, 0.0, 1.0)


@dataclass(frozen=True)
class StairLayout:
    """Validated, immutable derived layout; all dimensional fields use metres."""

    canonical_path: tuple
    lower_xy: tuple
    upper_xy: tuple
    axes: StairAxes
    base_z: float
    floor_to_floor: float
    upper_arrival_z: float
    run_length: float
    riser_count: int
    independent_tread_count: int
    actual_riser: float
    going: float
    width: float
    tread_thickness: float
    riser_thickness: float

    @property
    def upper_arrival_xy(self):
        return self.upper_xy

    @property
    def forward_axis(self):
        return self.axes.forward

    @property
    def left_axis(self):
        return self.axes.left

    @property
    def run_length_mm(self):
        return self.run_length * _MM_PER_METRE

    @property
    def actual_riser_mm(self):
        return self.actual_riser * _MM_PER_METRE

    @property
    def going_mm(self):
        return self.going * _MM_PER_METRE

    @property
    def upper_arrival_z_mm(self):
        return self.upper_arrival_z * _MM_PER_METRE


@dataclass(frozen=True)
class MeshFragment:
    """One closed solid with retained future material-part identity."""

    part_type: str
    ordinal: int
    vertices: tuple
    faces: tuple = _BOX_FACES


@dataclass(frozen=True)
class StairMeshData:
    """Complete arrays ready for one Blender Mesh datablock."""

    vertices: tuple
    faces: tuple
    face_roles: tuple = ()


def generate_stair_id():
    """Return a persistent identity suitable for canonical storage."""
    return str(uuid.uuid4())


def canonical_path(points):
    """Validate and return exactly two ordered world-XY plan points."""
    if points is None or len(points) != STAGE1_PATH_POINT_COUNT:
        raise ValueError("Stage 1 Stair Pathは正確に2点である必要があります。")
    result = []
    for point in points:
        if point is None or len(point) < 2:
            raise ValueError("Stair Path点を取得できません。")
        x, y = float(point[0]), float(point[1])
        if not math.isfinite(x) or not math.isfinite(y):
            raise ValueError("Stair Path座標は有限値である必要があります。")
        result.append((x, y))
    dx = result[1][0] - result[0][0]
    dy = result[1][1] - result[0][1]
    if math.hypot(dx, dy) <= MIN_STAIR_PATH_LENGTH_M:
        raise ValueError("Stair Pathが短すぎます。")
    return tuple(result)


def resolve_lower_upper(points, ascent_direction):
    """Resolve elevation roles without changing canonical draw order."""
    path = canonical_path(points)
    if ascent_direction == "FORWARD":
        return path[0], path[1]
    if ascent_direction == "REVERSE":
        return path[1], path[0]
    raise ValueError("不明な上り方向です。")


def resolve_stair_axes(points, ascent_direction):
    """Return +X uphill, +Y left while facing uphill, and world +Z."""
    lower, upper = resolve_lower_upper(points, ascent_direction)
    dx, dy = upper[0] - lower[0], upper[1] - lower[1]
    length = math.hypot(dx, dy)
    forward = (dx / length, dy / length, 0.0)
    return StairAxes(forward, (-forward[1], forward[0], 0.0))


def _positive_finite_mm(value, label):
    value = float(value)
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{label}は0より大きい有限値である必要があります。")
    return value / _MM_PER_METRE


def resolve_stair_layout(points, ascent_direction, base_z_mm,
                         floor_to_floor_mm, riser_count, stair_width_mm,
                         tread_thickness_mm, riser_thickness_mm):
    """Validate canonical inputs and derive the complete metre-based layout."""
    path = canonical_path(points)
    base_z_mm = float(base_z_mm)
    if not math.isfinite(base_z_mm):
        raise ValueError("下端基準高さは有限値である必要があります。")
    if isinstance(riser_count, bool):
        raise ValueError("蹴上数は整数である必要があります。")
    try:
        numeric_riser_count = float(riser_count)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("蹴上数は有限の整数である必要があります。") from exc
    if (not math.isfinite(numeric_riser_count)
            or not numeric_riser_count.is_integer()):
        raise ValueError("蹴上数は有限の整数である必要があります。")
    riser_count = int(numeric_riser_count)
    if riser_count < 2:
        raise ValueError("蹴上数は2以上である必要があります。")

    floor_to_floor = _positive_finite_mm(floor_to_floor_mm, "階高")
    width = _positive_finite_mm(stair_width_mm, "階段幅")
    tread_thickness = _positive_finite_mm(tread_thickness_mm, "踏板厚")
    riser_thickness = _positive_finite_mm(riser_thickness_mm, "蹴込み板厚")
    lower, upper = resolve_lower_upper(path, ascent_direction)
    axes = resolve_stair_axes(path, ascent_direction)
    run_length = math.hypot(path[1][0] - path[0][0],
                            path[1][1] - path[0][1])
    independent_tread_count = riser_count - 1
    actual_riser = floor_to_floor / riser_count
    going = run_length / independent_tread_count
    if (tread_thickness >= actual_riser
            or math.isclose(tread_thickness, actual_riser,
                            rel_tol=1.0e-12, abs_tol=1.0e-15)):
        raise ValueError("踏板厚は実蹴上より小さくする必要があります。")
    if (riser_thickness >= going
            or math.isclose(riser_thickness, going,
                            rel_tol=1.0e-12, abs_tol=1.0e-15)):
        raise ValueError("蹴込み板厚は踏面ピッチより小さくする必要があります。")
    base_z = base_z_mm / _MM_PER_METRE
    return StairLayout(
        path, lower, upper, axes, base_z, floor_to_floor,
        base_z + floor_to_floor, run_length, riser_count,
        independent_tread_count, actual_riser, going, width,
        tread_thickness, riser_thickness,
    )


def _world_vertex(layout, x, y, z):
    forward, left = layout.axes.forward, layout.axes.left
    return (layout.lower_xy[0] + forward[0] * x + left[0] * y,
            layout.lower_xy[1] + forward[1] * x + left[1] * y, z)


def _box_fragment(layout, part_type, ordinal, x0, x1, z0, z1):
    half_width = layout.width / 2.0
    vertices = tuple(
        _world_vertex(layout, x, y, z)
        for z in (z0, z1)
        for y in (-half_width, half_width)
        for x in (x0, x1)
    )
    # The comprehension orders each Z layer as x0/y-, x1/y-, x0/y+, x1/y+.
    # Reorder into the conventional box corner order expected by _BOX_FACES.
    order = (0, 1, 3, 2, 4, 5, 7, 6)
    fragment = MeshFragment(part_type, ordinal,
                            tuple(vertices[index] for index in order))
    validate_mesh_fragments((fragment,))
    return fragment


def build_tread_fragments(layout):
    """Build N-1 independent closed tread boards without any Riser dependency."""
    fragments = []
    for ordinal in range(1, layout.independent_tread_count + 1):
        top = layout.base_z + ordinal * layout.actual_riser
        fragments.append(_box_fragment(
            layout, "TREAD", ordinal,
            (ordinal - 1) * layout.going, ordinal * layout.going,
            top - layout.tread_thickness, top))
    return tuple(fragments)


def build_riser_fragments(layout):
    """Build N closed riser boards, with thickness extending uphill."""
    fragments = []
    for ordinal in range(1, layout.riser_count + 1):
        final = ordinal == layout.riser_count
        reference_x = (layout.run_length if final
                       else (ordinal - 1) * layout.going)
        bottom = layout.base_z + (ordinal - 1) * layout.actual_riser
        top = (layout.upper_arrival_z if final else
               layout.base_z + ordinal * layout.actual_riser
               - layout.tread_thickness)
        fragments.append(_box_fragment(
            layout, "RISER", ordinal, reference_x,
            reference_x + layout.riser_thickness, bottom, top))
    return tuple(fragments)


def _face_area(vertices, face):
    """Return a 3D polygon area using a stable triangle fan."""
    def triangle_area(a, b, c):
        ab = tuple(b[i] - a[i] for i in range(3))
        ac = tuple(c[i] - a[i] for i in range(3))
        cross = (ab[1] * ac[2] - ab[2] * ac[1],
                 ab[2] * ac[0] - ab[0] * ac[2],
                 ab[0] * ac[1] - ab[1] * ac[0])
        return math.sqrt(sum(value * value for value in cross)) / 2.0
    anchor = vertices[face[0]]
    return sum(triangle_area(anchor, vertices[face[index]],
                             vertices[face[index + 1]])
               for index in range(1, len(face) - 1))


def _signed_volume(vertices, faces):
    """Return oriented volume; positive means outward face winding."""
    volume = 0.0
    for face in faces:
        anchor = vertices[face[0]]
        for index in range(1, len(face) - 1):
            b, c = vertices[face[index]], vertices[face[index + 1]]
            volume += (
                anchor[0] * (b[1] * c[2] - b[2] * c[1])
                + anchor[1] * (b[2] * c[0] - b[0] * c[2])
                + anchor[2] * (b[0] * c[1] - b[1] * c[0])
            ) / 6.0
    return volume


def validate_mesh_fragments(fragments):
    """Reject non-finite vertices, bad indices, and zero-area faces."""
    for fragment in fragments:
        if len(fragment.vertices) < 4 or len(fragment.faces) < 4:
            raise ValueError("Stair fragmentはclosed solidである必要があります。")
        if not all(math.isfinite(value) for vertex in fragment.vertices
                   for value in vertex):
            raise ValueError("Stair geometryに非有限座標があります。")
        edge_use = {}
        directed_edges = set()
        for face in fragment.faces:
            if len(face) < 3 or any(index < 0 or index >= len(fragment.vertices)
                                    for index in face):
                raise ValueError("Stair geometryのface indexが不正です。")
            if len(set(face)) != len(face):
                raise ValueError("Stair geometryのface内に重複vertex indexがあります。")
            if _face_area(fragment.vertices, face) <= 1.0e-15:
                raise ValueError("Stair geometryにzero-area faceがあります。")
            for index, start in enumerate(face):
                end = face[(index + 1) % len(face)]
                edge = tuple(sorted((start, end)))
                edge_use[edge] = edge_use.get(edge, 0) + 1
                if (start, end) in directed_edges:
                    raise ValueError("Stair geometryのface windingが一貫していません。")
                directed_edges.add((start, end))
        if not edge_use or any(count != 2 for count in edge_use.values()):
            raise ValueError("Stair fragmentはclosed manifold solidである必要があります。")
        if any((end, start) not in directed_edges
               for start, end in directed_edges):
            raise ValueError("Stair geometryのface windingが一貫していません。")
        if _signed_volume(fragment.vertices, fragment.faces) <= 1.0e-15:
            raise ValueError("Stair fragmentのfaceは外向きである必要があります。")
    return True


def _cross_2d(a, b, c):
    return ((b[0] - a[0]) * (c[1] - a[1])
            - (b[1] - a[1]) * (c[0] - a[0]))


def polygon_signed_area(points):
    """Return the signed area of a 2D polygon (CCW is positive)."""
    return sum(points[i][0] * points[(i + 1) % len(points)][1]
               - points[(i + 1) % len(points)][0] * points[i][1]
               for i in range(len(points))) / 2.0


def _segments_intersect(a, b, c, d, epsilon):
    orientations = (_cross_2d(a, b, c), _cross_2d(a, b, d),
                    _cross_2d(c, d, a), _cross_2d(c, d, b))
    if any(abs(value) <= epsilon for value in orientations):
        # Non-adjacent touching is invalid for the deliberately limited simple
        # polygon contract, including collinear overlap.
        def within(p, q, r):
            return (min(p[0], q[0]) - epsilon <= r[0] <= max(p[0], q[0]) + epsilon
                    and min(p[1], q[1]) - epsilon <= r[1] <= max(p[1], q[1]) + epsilon)
        return any(abs(value) <= epsilon and within(p, q, r)
                   for value, p, q, r in (
                       (orientations[0], a, b, c), (orientations[1], a, b, d),
                       (orientations[2], c, d, a), (orientations[3], c, d, b)))
    return ((orientations[0] > 0) != (orientations[1] > 0)
            and (orientations[2] > 0) != (orientations[3] > 0))


def validate_simple_polygon(points, *, epsilon=1.0e-12):
    """Validate a finite, hole-free, non-self-touching 2D polygon.

    A repeated closing point and consecutive duplicates are cleaned. Other
    zero-length edges and non-adjacent repeated/touching points are rejected.
    The returned polygon is deterministic and normalized counter-clockwise.
    """
    if points is None:
        raise ValueError("2D profileがありません。")
    raw = []
    for point in points:
        if point is None or len(point) != 2:
            raise ValueError("2D profile pointは2座標である必要があります。")
        converted = (float(point[0]), float(point[1]))
        if not all(math.isfinite(value) for value in converted):
            raise ValueError("2D profile座標は有限値である必要があります。")
        if not raw or converted != raw[-1]:
            raw.append(converted)
    if len(raw) > 1 and raw[0] == raw[-1]:
        raw.pop()
    if len(raw) < 3:
        raise ValueError("2D profileには3点以上が必要です。")
    for index, point in enumerate(raw):
        following = raw[(index + 1) % len(raw)]
        if math.hypot(following[0] - point[0], following[1] - point[1]) <= epsilon:
            raise ValueError("2D profileにzero-length edgeがあります。")
    count = len(raw)
    for first in range(count):
        for second in range(first + 1, count):
            if second in (first, first + 1) or (first == 0 and second == count - 1):
                continue
            if _segments_intersect(raw[first], raw[(first + 1) % count],
                                   raw[second], raw[(second + 1) % count], epsilon):
                raise ValueError("2D profileはsimple polygonである必要があります。")
    area = polygon_signed_area(raw)
    if abs(area) <= epsilon:
        raise ValueError("2D profile areaは0より大きい必要があります。")
    return tuple(raw if area > 0 else reversed(raw))


def triangulate_simple_polygon(points):
    """Deterministically ear-clip a validated polygon into CCW triangles."""
    polygon = validate_simple_polygon(points)
    remaining = list(range(len(polygon)))
    triangles = []

    def inside_triangle(point, a, b, c):
        return (_cross_2d(a, b, point) >= -1.0e-12
                and _cross_2d(b, c, point) >= -1.0e-12
                and _cross_2d(c, a, point) >= -1.0e-12)

    while len(remaining) > 3:
        for position, current in enumerate(remaining):
            previous = remaining[position - 1]
            following = remaining[(position + 1) % len(remaining)]
            a, b, c = polygon[previous], polygon[current], polygon[following]
            if _cross_2d(a, b, c) <= 1.0e-12:
                continue
            if any(inside_triangle(polygon[index], a, b, c)
                   for index in remaining
                   if index not in (previous, current, following)):
                continue
            triangles.append((previous, current, following))
            del remaining[position]
            break
        else:
            raise ValueError("2D profileをtriangulateできません。")
    triangles.append(tuple(remaining))
    return polygon, tuple(triangles)


def extrude_xz_profile(points, y_min, y_max, *, part_type="PROFILE", ordinal=1):
    """Extrude a simple XZ profile along local Y into an outward closed solid."""
    y_min, y_max = float(y_min), float(y_max)
    if not math.isfinite(y_min) or not math.isfinite(y_max) or y_max <= y_min:
        raise ValueError("Extrusion Y rangeは有限かつ正の幅である必要があります。")
    polygon, triangles = triangulate_simple_polygon(points)
    count = len(polygon)
    vertices = tuple((x, y, z) for y in (y_min, y_max) for x, z in polygon)
    faces = []
    faces.extend(triangles)  # CCW in XZ points toward -Y.
    faces.extend(tuple(index + count for index in reversed(triangle))
                 for triangle in triangles)
    faces.extend(((index + 1) % count, index, index + count,
                  (index + 1) % count + count) for index in range(count))
    fragment = MeshFragment(part_type, ordinal, vertices, tuple(faces))
    validate_mesh_fragments((fragment,))
    return fragment


def assemble_stair_mesh(fragments):
    """Combine closed fragments into arrays for exactly one Mesh Object."""
    fragments = tuple(fragments)
    validate_mesh_fragments(fragments)
    vertices, faces, face_roles = [], [], []
    for fragment in fragments:
        offset = len(vertices)
        vertices.extend(fragment.vertices)
        faces.extend(tuple(index + offset for index in face)
                     for face in fragment.faces)
        face_roles.extend((fragment.part_type,) * len(fragment.faces))
    return StairMeshData(tuple(vertices), tuple(faces), tuple(face_roles))


def prepare_stair_geometry(points, ascent_direction, base_z_mm,
                           floor_to_floor_mm, riser_count, stair_width_mm,
                           tread_thickness_mm, riser_thickness_mm):
    """Resolve and fully prepare basic Stage 2 geometry before Scene mutation."""
    layout = resolve_stair_layout(
        points, ascent_direction, base_z_mm, floor_to_floor_mm, riser_count,
        stair_width_mm, tread_thickness_mm, riser_thickness_mm)
    fragments = build_tread_fragments(layout) + build_riser_fragments(layout)
    return layout, fragments, assemble_stair_mesh(fragments)


def identity_transform_contract():
    """Expose the required transform values for runtime and pure tests."""
    return IDENTITY_LOCATION, IDENTITY_ROTATION, IDENTITY_SCALE
