"""Mesh-independent wall-face and safe corner geometry."""

import math

from .finish_path import resolve_interval


EPSILON = 1.0e-9


def wall_axis(start, end):
    dx, dy = float(end[0]) - float(start[0]), float(end[1]) - float(start[1])
    length = math.hypot(dx, dy)
    if not math.isfinite(length) or length <= EPSILON:
        raise ValueError("invalid Wall centerline")
    return (dx / length, dy / length), length


def side_normal(start, end, side):
    (dx, dy), _ = wall_axis(start, end)
    if side == "LEFT":
        return -dy, dx
    if side == "RIGHT":
        return dy, -dx
    raise ValueError("invalid Wall side")


def face_segment(start, end, thickness_m, side, interval=None,
                 traversal="FORWARD"):
    """Resolve a canonical interval to its physical wall-face segment."""
    axis, length = wall_axis(start, end)
    thickness = float(thickness_m)
    if not math.isfinite(thickness) or thickness <= 0:
        raise ValueError("invalid Wall thickness")
    if traversal not in {"FORWARD", "REVERSE"}:
        raise ValueError("invalid traversal direction")
    if interval is None:
        distances = (0.0, length) if traversal == "FORWARD" else (length, 0.0)
    else:
        distances = resolve_interval(*interval, length * 1000.0, traversal=traversal)
        distances = tuple(value / 1000.0 for value in distances)
    normal = side_normal(start, end, side)
    offset = thickness * 0.5
    return tuple((float(start[0]) + axis[0] * distance + normal[0] * offset,
                  float(start[1]) + axis[1] * distance + normal[1] * offset)
                 for distance in distances)


def line_intersection(first, second, parallel_epsilon=1.0e-7):
    """Intersect two infinite directed lines; reject parallel/near-parallel."""
    p, q = first[0], second[0]
    r = (first[1][0] - p[0], first[1][1] - p[1])
    s = (second[1][0] - q[0], second[1][1] - q[1])
    cross = r[0] * s[1] - r[1] * s[0]
    scale = math.hypot(*r) * math.hypot(*s)
    if scale <= EPSILON or abs(cross) <= parallel_epsilon * scale:
        return None
    qp = q[0] - p[0], q[1] - p[1]
    t = (qp[0] * s[1] - qp[1] * s[0]) / cross
    point = p[0] + t * r[0], p[1] + t * r[1]
    return point if all(math.isfinite(value) for value in point) else None


def resolve_join(first, second, miter_limit=4.0, max_reach_m=1.0):
    """Return a shared miter point, collinear endpoint, or reject unsafe join."""
    intersection = line_intersection(first, second)
    gap = math.dist(first[1], second[0])
    if intersection is None:
        # Parallel continuation is safe only when face lines meet.
        return first[1] if gap <= 1.0e-6 else None
    # The absolute cap prevents long Walls from legitimising huge spikes.
    local = max(math.dist(first[0], first[1]), math.dist(second[0], second[1]))
    reach = max(math.dist(first[1], intersection), math.dist(second[0], intersection))
    return (intersection if local > EPSILON and reach <= miter_limit * local
            and reach <= float(max_reach_m) else None)


def resolve_junction_butt(segment, adjacent_segment, endpoint,
                          miter_limit=4.0):
    """Terminate one surviving face at an adjacent canonical face line.

    The returned segment remains independent, so its Curve cap is a BUTT cap;
    the adjacent segment is context only and is never added to its range.
    """
    if endpoint == "START":
        point = resolve_join(adjacent_segment, segment, miter_limit)
        if point is None:
            raise ValueError("unsafe junction-aware Finish BUTT start")
        return point, segment[1]
    if endpoint == "END":
        point = resolve_join(segment, adjacent_segment, miter_limit)
        if point is None:
            raise ValueError("unsafe junction-aware Finish BUTT end")
        return segment[0], point
    raise ValueError("invalid Finish BUTT endpoint")


def propagate_physical_side(previous_segment, start, end, thickness_m, traversal):
    """Choose the canonical side whose traversed face continues most closely."""
    choices = []
    for side in ("LEFT", "RIGHT"):
        segment = face_segment(start, end, thickness_m, side, traversal=traversal)
        choices.append((math.dist(previous_segment[1], segment[0]), side, segment))
    choices.sort(key=lambda item: (item[0], item[1]))
    if abs(choices[0][0] - choices[1][0]) <= EPSILON:
        raise ValueError("ambiguous physical Finish side")
    return choices[0][1]


def _segment_intersects_box(first, second, minimum, maximum, epsilon=1e-9):
    """Liang-Barsky style intersection against an axis-aligned 2D box."""
    low, high = 0.0, 1.0
    delta = second[0] - first[0], second[1] - first[1]
    for axis in range(2):
        if abs(delta[axis]) <= epsilon:
            if first[axis] < minimum[axis] or first[axis] > maximum[axis]:
                return False
            continue
        enter = (minimum[axis] - first[axis]) / delta[axis]
        leave = (maximum[axis] - first[axis]) / delta[axis]
        if enter > leave:
            enter, leave = leave, enter
        low, high = max(low, enter), min(high, leave)
        if low > high:
            return False
    return True


def transition_intersects_wall_solid(first_segment, second_segment,
                                     blocker_junction, blocker_other,
                                     blocker_thickness_m, miter_limit=4.0,
                                     max_reach_m=1.0, projection_m=0.0,
                                     outward_normals=None):
    """Test a local Finish transition against a canonical blocker footprint."""
    axis, length = wall_axis(blocker_junction, blocker_other)
    thickness = float(blocker_thickness_m)
    if not math.isfinite(thickness) or thickness <= 0.0:
        raise ValueError("invalid blocker thickness")
    blocker_normal = -axis[1], axis[0]

    def local(point):
        offset = point[0] - blocker_junction[0], point[1] - blocker_junction[1]
        return (offset[0] * axis[0] + offset[1] * axis[1],
                offset[0] * blocker_normal[0] + offset[1] * blocker_normal[1])

    join = resolve_join(first_segment, second_segment, miter_limit, max_reach_m)
    if join is None:
        return True  # Existing unsafe transition stays conservatively rejected.
    polyline = (first_segment[1], join, second_segment[0])
    bounds_min = (1.0e-7, -thickness * 0.5)
    bounds_max = (length, thickness * 0.5)
    paths = [polyline]
    projection = float(projection_m)
    if not math.isfinite(projection) or projection < 0.0:
        raise ValueError("invalid Finish profile projection")
    if outward_normals is not None:
        if len(outward_normals) != 2:
            raise ValueError("invalid Finish Profile orientation")
        offset_segments = []
        for segment, normal in zip((first_segment, second_segment),
                                   outward_normals):
            nx, ny = map(float, normal)
            if (not all(map(math.isfinite, (nx, ny)))
                    or abs(math.hypot(nx, ny) - 1.0) > 1.0e-6):
                raise ValueError("invalid Finish Profile orientation")
            offset = tuple((point[0] + nx * projection,
                            point[1] + ny * projection) for point in segment)
            offset_segments.append(offset)
            paths.append(offset)
        outer_join = resolve_join(offset_segments[0], offset_segments[1],
                                  miter_limit, max_reach_m)
        if outer_join is None:
            return True
        # This is the actual one-sided SIMPLE outer corner envelope: the end
        # of the first straight edge, its resolved outer miter vertex, and the
        # start of the next straight edge.
        paths.append((offset_segments[0][1], outer_join,
                      offset_segments[1][0]))
    return any(_segment_intersects_box(local(a), local(b), bounds_min, bounds_max)
               for path in paths for a, b in zip(path, path[1:]))


def transition_blocked_by_footprints(first_segment, second_segment, blockers,
                                     miter_limit=4.0, max_reach_m=1.0,
                                     projection_m=0.0, outward_normals=None):
    """Return true only for canonical footprints supplied by trusted topology."""
    return any(transition_intersects_wall_solid(
        first_segment, second_segment, junction, other, thickness,
        miter_limit, max_reach_m, projection_m, outward_normals)
        for junction, other, thickness in blockers)


def endpoint_blocked_by_footprints(endpoint, outward_normal, blockers,
                                   projection_m):
    """Test the endpoint and resolved Profile projection against blockers."""
    projection = float(projection_m)
    if not math.isfinite(projection) or projection < 0.0:
        raise ValueError("invalid Finish profile projection")
    ray_end = (endpoint[0] + outward_normal[0] * projection,
               endpoint[1] + outward_normal[1] * projection)
    for junction, other, thickness in blockers:
        axis, length = wall_axis(junction, other)
        normal = -axis[1], axis[0]
        def local(point):
            delta = point[0] - junction[0], point[1] - junction[1]
            return (delta[0] * axis[0] + delta[1] * axis[1],
                    delta[0] * normal[0] + delta[1] * normal[1])
        thickness = float(thickness)
        if not math.isfinite(thickness) or thickness <= 0.0:
            raise ValueError("invalid blocker thickness")
        half = thickness * .5
        if _segment_intersects_box(local(endpoint), local(ray_end),
                                   (1.0e-7, -half), (length, half)):
            return True
    return False


def validate_profile_miter_space(segments, projection_m, miter_limit=4.0):
    """Reject corners whose outer SIMPLE miters consume a path segment."""
    projection = float(projection_m)
    if not math.isfinite(projection) or projection <= 0.0:
        raise ValueError("invalid Finish profile projection")
    extensions = [0.0] * (len(segments) + 1)
    joins = []
    for index, (first, second) in enumerate(zip(segments, segments[1:]), 1):
        join = resolve_join(first, second, miter_limit)
        if join is None:
            raise ValueError("unsafe Finish corner")
        joins.append(join)
        first_axis, first_length = wall_axis(first[0], first[1])
        second_axis, second_length = wall_axis(second[0], second[1])
        dot = max(-1.0, min(1.0, first_axis[0] * second_axis[0]
                            + first_axis[1] * second_axis[1]))
        angle = math.acos(dot)
        if angle <= 1.0e-7:
            extension = 0.0
        elif math.pi - angle <= 1.0e-7:
            raise ValueError("unsafe Finish corner")
        else:
            extension = projection * math.tan(angle * 0.5)
        if (not math.isfinite(extension)
                or extension > miter_limit * projection):
            raise ValueError("unsafe Finish Profile miter")
        extensions[index] = extension
    for index, segment in enumerate(segments):
        resolved_start = joins[index - 1] if index else segment[0]
        resolved_end = joins[index] if index < len(joins) else segment[1]
        length = math.dist(resolved_start, resolved_end)
        if extensions[index] + extensions[index + 1] >= length - EPSILON:
            raise ValueError("Finish区間がProfileの留め加工には短すぎます。")
    return tuple(extensions)


def resolve_surface_path(segments, miter_limit=4.0):
    """Join ordered raw segments without ever inferring a branch."""
    if not segments:
        raise ValueError("FinishRun has no spans")
    points = [segments[0][0]]
    for previous, current in zip(segments, segments[1:]):
        join = resolve_join(previous, current, miter_limit)
        if join is None:
            raise ValueError("unsafe Finish corner")
        points.append(join)
    points.append(segments[-1][1])
    return tuple(points)
