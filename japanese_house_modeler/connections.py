"""Persistent Wall endpoint topology helpers."""

import bpy


_ENDPOINTS = {"START", "END"}


def connection_collection(wall_object, endpoint):
    """Return the collection belonging to an endpoint, or raise for bad input."""
    if endpoint not in _ENDPOINTS:
        raise ValueError(f"Unknown Wall endpoint: {endpoint}")
    wall = getattr(wall_object, "jhm_wall", None)
    if wall is None or not wall.is_wall:
        raise ValueError("Object is not a managed Wall")
    return wall.start_connections if endpoint == "START" else wall.end_connections


def is_valid_wall_object(wall_object):
    """Return whether an object pointer still identifies a managed Wall."""
    try:
        return (
            wall_object is not None
            and bpy.data.objects.get(wall_object.name) is wall_object
            and len(wall_object.users_collection) > 0
            and getattr(wall_object, "jhm_wall", None) is not None
            and wall_object.jhm_wall.is_wall
        )
    except ReferenceError:
        return False


def is_valid_connection(connection):
    """Validate a stored target without mutating its collection."""
    try:
        return (
            connection.target_endpoint in _ENDPOINTS
            and is_valid_wall_object(connection.target_object)
        )
    except ReferenceError:
        return False


def valid_connection_count(wall_object, endpoint):
    """Count only live, managed Wall targets (safe for UI drawing)."""
    try:
        return sum(
            1
            for connection in connection_collection(wall_object, endpoint)
            if is_valid_connection(connection)
        )
    except (ReferenceError, ValueError):
        return 0


def _purge_invalid(collection):
    for index in range(len(collection) - 1, -1, -1):
        if not is_valid_connection(collection[index]):
            collection.remove(index)


def _contains(collection, target_object, target_endpoint):
    return any(
        connection.target_object is target_object
        and connection.target_endpoint == target_endpoint
        for connection in collection
        if is_valid_connection(connection)
    )


def _add_one(source_object, source_endpoint, target_object, target_endpoint):
    if source_object is target_object:
        return
    collection = connection_collection(source_object, source_endpoint)
    _purge_invalid(collection)
    if _contains(collection, target_object, target_endpoint):
        return
    connection = collection.add()
    connection.target_object = target_object
    connection.target_endpoint = target_endpoint


def add_reciprocal(source_object, source_endpoint, target_object, target_endpoint):
    """Idempotently add both halves of one edge, forbidding self links."""
    if source_object is target_object:
        return
    if not is_valid_wall_object(source_object) or not is_valid_wall_object(target_object):
        raise ValueError("Connection endpoint is not a live managed Wall")
    _add_one(source_object, source_endpoint, target_object, target_endpoint)
    try:
        _add_one(target_object, target_endpoint, source_object, source_endpoint)
    except Exception:
        _remove_one(source_object, source_endpoint, target_object, target_endpoint)
        raise


def _remove_one(source_object, source_endpoint, target_object, target_endpoint):
    collection = connection_collection(source_object, source_endpoint)
    for index in range(len(collection) - 1, -1, -1):
        connection = collection[index]
        if not is_valid_connection(connection) or (
            connection.target_object is target_object
            and connection.target_endpoint == target_endpoint
        ):
            collection.remove(index)


def remove_reciprocal(source_object, source_endpoint, target_object, target_endpoint):
    """Remove every duplicate of an edge from both endpoint collections."""
    if is_valid_wall_object(source_object):
        _remove_one(source_object, source_endpoint, target_object, target_endpoint)
    if is_valid_wall_object(target_object):
        _remove_one(target_object, target_endpoint, source_object, source_endpoint)


def detach_endpoint(source_object, source_endpoint):
    """Detach one endpoint while preserving edges among the other members."""
    collection = connection_collection(source_object, source_endpoint)
    targets = [
        (connection.target_object, connection.target_endpoint)
        for connection in collection
        if is_valid_connection(connection)
    ]
    for target_object, target_endpoint in targets:
        remove_reciprocal(
            source_object, source_endpoint, target_object, target_endpoint
        )
    _purge_invalid(collection)


def transfer_endpoint_connections(source_object, source_endpoint,
                                  destination_object, destination_endpoint):
    """Move every valid reciprocal edge, preserving the peers' other edges."""
    targets = [
        (connection.target_object, connection.target_endpoint)
        for connection in connection_collection(source_object, source_endpoint)
        if is_valid_connection(connection)
    ]
    detach_endpoint(source_object, source_endpoint)
    for target_object, target_endpoint in targets:
        if is_valid_wall_object(target_object):
            add_reciprocal(
                destination_object, destination_endpoint,
                target_object, target_endpoint,
            )


def junction_members(target_object, target_endpoint):
    """Collect the valid connected component containing a target endpoint."""
    pending = [(target_object, target_endpoint)]
    members = []
    seen = set()
    while pending:
        wall_object, endpoint = pending.pop()
        key = (wall_object.as_pointer(), endpoint)
        if key in seen or not is_valid_wall_object(wall_object):
            continue
        seen.add(key)
        members.append((wall_object, endpoint))
        collection = connection_collection(wall_object, endpoint)
        for connection in collection:
            if is_valid_connection(connection):
                pending.append(
                    (connection.target_object, connection.target_endpoint)
                )
    return members


def attach_to_junction(source_object, source_endpoint, target_object, target_endpoint):
    """Attach source and enforce a complete reciprocal graph for the junction."""
    if source_object is target_object:
        return
    members = [
        member
        for member in junction_members(target_object, target_endpoint)
        if member[0] is not source_object
    ]
    members.append((source_object, source_endpoint))
    for index, first in enumerate(members):
        for second in members[index + 1 :]:
            add_reciprocal(first[0], first[1], second[0], second[1])


def snapshot_topology():
    """Capture all valid edges so an operator can roll back atomically."""
    snapshot = []
    for wall_object in bpy.data.objects:
        if not is_valid_wall_object(wall_object):
            continue
        for endpoint in _ENDPOINTS:
            targets = []
            for connection in connection_collection(wall_object, endpoint):
                if is_valid_connection(connection):
                    targets.append(
                        (connection.target_object, connection.target_endpoint)
                    )
            snapshot.append((wall_object, endpoint, targets))
    return snapshot


def restore_topology(snapshot):
    """Restore a snapshot, dropping partial or stale edges created meanwhile."""
    for wall_object in bpy.data.objects:
        if is_valid_wall_object(wall_object):
            for endpoint in _ENDPOINTS:
                connection_collection(wall_object, endpoint).clear()
    for wall_object, endpoint, targets in snapshot:
        if not is_valid_wall_object(wall_object):
            continue
        for target_object, target_endpoint in targets:
            if is_valid_wall_object(target_object):
                _add_one(wall_object, endpoint, target_object, target_endpoint)
