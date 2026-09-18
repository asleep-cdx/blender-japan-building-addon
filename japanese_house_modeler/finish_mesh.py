"""Mesh-finalization and Profile-aware shading helpers."""

import math

from .finish_custom_profiles import oriented_edge_indices
from .finish_orientation import oriented_profile_contour
from .finish_profiles import STANDARD_PROFILE_IDS


MESH_WELD_DISTANCE_M = 1.0e-6
MIN_CLOSED_VOLUME_M3 = 1.0e-15


def polygon_should_be_smooth(profile, normal_z, epsilon=1.0e-6):
    """Return shading intent for a swept polygon from its profile normal.

    Revision-1 ROUNDED arc facets have normals between vertical and horizontal;
    caps and all planar standard-Profile regions remain flat.
    """
    z = abs(float(normal_z))
    return (profile.shading.smooth_round and math.isfinite(z)
            and epsilon < z < 1.0 - epsilon)


def _horizontal_distance_to_paths(point, path_ranges):
    """Shortest XY distance to the canonical attachment path segments."""
    px, py = float(point[0]), float(point[1])
    best = math.inf
    for path in path_ranges:
        for first, second in zip(path, path[1:]):
            ax, ay = float(first[0]), float(first[1])
            bx, by = float(second[0]), float(second[1])
            dx, dy = bx - ax, by - ay
            length_squared = dx * dx + dy * dy
            if length_squared <= 1.0e-20:
                parameter = 0.0
            else:
                parameter = max(0.0, min(1.0,
                    ((px - ax) * dx + (py - ay) * dy) / length_squared))
            closest = ax + parameter * dx, ay + parameter * dy
            best = min(best, math.hypot(px - closest[0], py - closest[1]))
    if not math.isfinite(best):
        raise ValueError("Finish attachment pathが空です。")
    return best


def _edge_signature(first, second, minimum_z, path_ranges):
    dz = abs(float(second[2]) - float(first[2]))
    length = math.sqrt(sum((float(second[index]) - float(first[index])) ** 2
                           for index in range(3)))
    endpoints = tuple(sorted((
        (float(first[2]) - minimum_z,
         _horizontal_distance_to_paths(first, path_ranges)),
        (float(second[2]) - minimum_z,
         _horizontal_distance_to_paths(second, path_ranges)),
    )))
    return endpoints, dz, length


def _signatures_match(first, second, epsilon=1.0e-6):
    flat_first = tuple(value for endpoint in first[0] for value in endpoint) + first[1:]
    flat_second = tuple(value for endpoint in second[0] for value in endpoint) + second[1:]
    return all(abs(a - b) <= epsilon
               for a, b in zip(flat_first, flat_second))


def custom_polygon_should_be_smooth(profile, coordinates, horizontal_sign,
                                    mesh_minimum_z, path_ranges,
                                    epsilon=1.0e-6, vertical_sign=1.0):
    """Match a swept quad to an explicitly smooth oriented contour edge.

    A Curve side facet has two opposite cross-section edges with the same
    height/Profile-X/length signature.  Profile-X is measured as distance to
    the explicit canonical attachment path, so equal-height opposite edges
    remain distinct.  Requiring both matches keeps caps (including
    BUTT caps) and irregular transition faces flat and avoids relying on
    evaluated polygon ordering or on ``normal.z``.
    """
    coordinates = tuple(tuple(float(value) for value in point[:3])
                        for point in coordinates)
    if len(coordinates) != 4:
        return False
    indices = oriented_edge_indices(
        len(profile.contour), profile.shading.smooth_contour_edges,
        horizontal_sign, vertical_sign)
    oriented = oriented_profile_contour(
        profile.contour, horizontal_sign, vertical_sign)
    profile_minimum_y = min(point[1] for point in oriented)
    polygon_signatures = tuple(
        _edge_signature(coordinates[index], coordinates[(index + 1) % 4],
                        mesh_minimum_z, path_ranges)
        for index in range(4))
    for index in indices:
        first, second = oriented[index], oriented[(index + 1) % len(oriented)]
        expected = (((first[1] - profile_minimum_y, abs(first[0])),
                     (second[1] - profile_minimum_y, abs(second[0]))),
                    abs(second[1] - first[1]),
                    math.hypot(second[0] - first[0], second[1] - first[1]))
        expected = (tuple(sorted(expected[0])), expected[1], expected[2])
        if sum(_signatures_match(signature, expected, epsilon)
               for signature in polygon_signatures) >= 2:
            return True
    return False


def apply_profile_shading(mesh, profile, horizontal_sign=1.0, path_ranges=(),
                          vertical_sign=1.0):
    """Apply deterministic Profile intent without changing materials."""
    custom = profile.profile_id not in STANDARD_PROFILE_IDS
    minimum_z = min((vertex.co.z for vertex in mesh.vertices), default=0.0)
    for polygon in mesh.polygons:
        if custom:
            coordinates = tuple(mesh.vertices[index].co
                                for index in polygon.vertices)
            polygon.use_smooth = custom_polygon_should_be_smooth(
                profile, coordinates, horizontal_sign, minimum_z, path_ranges,
                vertical_sign=vertical_sign)
        else:
            # Keep the accepted Stage 2-B standard Profile behavior unchanged.
            polygon.use_smooth = polygon_should_be_smooth(
                profile, polygon.normal.z)


def closed_volume_topology_is_valid(boundary_edges, non_manifold_edges,
                                    signed_volume):
    """Return whether topology counts describe a finite, closed solid."""
    volume = float(signed_volume)
    return (int(boundary_edges) == 0
            and int(non_manifold_edges) == 0
            and math.isfinite(volume)
            and abs(volume) > MIN_CLOSED_VOLUME_M3)


def weld_and_validate_finish_mesh(mesh,
                                  tolerance=MESH_WELD_DISTANCE_M):
    """Weld coincident Curve cap/side vertices and require a closed volume.

    BMesh preserves the existing face winding and per-face material indices;
    this helper deliberately performs no normal reversal or transform change.
    """
    distance = float(tolerance)
    if not math.isfinite(distance) or distance <= 0.0:
        raise ValueError("Mesh weld toleranceが不正です。")

    import bmesh

    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=distance)
        bm.normal_update()
        boundary_edges = sum(edge.is_boundary for edge in bm.edges)
        non_manifold_edges = sum(not edge.is_manifold for edge in bm.edges)
        signed_volume = bm.calc_volume(signed=True)
        if not closed_volume_topology_is_valid(
                boundary_edges, non_manifold_edges, signed_volume):
            raise ValueError(
                "Mesh topologyを閉じた立体へ確定できませんでした"
                f" (boundary={boundary_edges}, "
                f"non-manifold={non_manifold_edges})")
        bm.to_mesh(mesh)
        mesh.update()
    finally:
        bm.free()
    return signed_volume
