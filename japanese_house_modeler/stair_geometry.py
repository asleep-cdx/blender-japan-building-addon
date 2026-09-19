"""Pure canonical, layout, and basic geometry helpers for Build 07-A."""

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
    if isinstance(riser_count, bool) or int(riser_count) != riser_count:
        raise ValueError("蹴上数は整数である必要があります。")
    riser_count = int(riser_count)
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
    """Return a quad area via two triangle cross products."""
    def triangle_area(a, b, c):
        ab = tuple(b[i] - a[i] for i in range(3))
        ac = tuple(c[i] - a[i] for i in range(3))
        cross = (ab[1] * ac[2] - ab[2] * ac[1],
                 ab[2] * ac[0] - ab[0] * ac[2],
                 ab[0] * ac[1] - ab[1] * ac[0])
        return math.sqrt(sum(value * value for value in cross)) / 2.0
    a, b, c, d = (vertices[index] for index in face)
    return triangle_area(a, b, c) + triangle_area(a, c, d)


def validate_mesh_fragments(fragments):
    """Reject non-finite vertices, bad indices, and zero-area faces."""
    for fragment in fragments:
        if len(fragment.vertices) != 8 or len(fragment.faces) != 6:
            raise ValueError("Stair fragmentはclosed rectangular solidである必要があります。")
        if not all(math.isfinite(value) for vertex in fragment.vertices
                   for value in vertex):
            raise ValueError("Stair geometryに非有限座標があります。")
        for face in fragment.faces:
            if len(face) < 3 or any(index < 0 or index >= len(fragment.vertices)
                                    for index in face):
                raise ValueError("Stair geometryのface indexが不正です。")
            if _face_area(fragment.vertices, face) <= 1.0e-15:
                raise ValueError("Stair geometryにzero-area faceがあります。")
    return True


def assemble_stair_mesh(fragments):
    """Combine closed fragments into arrays for exactly one Mesh Object."""
    fragments = tuple(fragments)
    validate_mesh_fragments(fragments)
    vertices, faces = [], []
    for fragment in fragments:
        offset = len(vertices)
        vertices.extend(fragment.vertices)
        faces.extend(tuple(index + offset for index in face)
                     for face in fragment.faces)
    return StairMeshData(tuple(vertices), tuple(faces))


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
