"""Mesh-finalization helpers for managed SIMPLE Finish conversion."""

import math


MESH_WELD_DISTANCE_M = 1.0e-6
MIN_CLOSED_VOLUME_M3 = 1.0e-15


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
