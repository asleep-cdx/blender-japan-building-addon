"""Persistent identity and reference-validation helpers for managed objects."""

import uuid


def new_persistent_id():
    """Return a collision-resistant identifier suitable for Blender storage."""
    return str(uuid.uuid4())


def ensure_persistent_id(owner, attribute="wall_id"):
    """Preserve a non-empty ID, otherwise assign and return a UUID."""
    value = str(getattr(owner, attribute, "") or "").strip()
    if not value:
        value = new_persistent_id()
        setattr(owner, attribute, value)
    return value


def ensure_unique_persistent_id(owner, existing_ids, attribute="wall_id"):
    """Ensure an ID is present and not owned elsewhere in a supplied ID set."""
    current = str(getattr(owner, attribute, "") or "").strip()
    if current and current not in existing_ids:
        return current
    value = new_persistent_id()
    while value in existing_ids:
        value = new_persistent_id()
    setattr(owner, attribute, value)
    return value


def duplicate_ids(objects, id_getter=lambda item: item.wall_id):
    """Return {id: objects} for non-empty IDs owned by more than one object."""
    index = {}
    for item in objects:
        value = str(id_getter(item) or "").strip()
        if value:
            index.setdefault(value, []).append(item)
    return {key: tuple(values) for key, values in index.items() if len(values) > 1}


def id_index(objects, id_getter=lambda item: item.wall_id):
    """Build a cache index without treating it as persistent truth."""
    result = {}
    for item in objects:
        value = str(id_getter(item) or "").strip()
        if value:
            result.setdefault(value, []).append(item)
    return result


def reference_is_trusted(pointer, expected_id, candidates=(), managed=None):
    """Validate pointer + expected ID and reject every ambiguous identity."""
    if pointer is None or not expected_id:
        return False
    if managed is not None and not managed(pointer):
        return False
    actual = str(getattr(getattr(pointer, "jhm_wall", pointer), "wall_id", "") or "")
    owners = [item for item in candidates if str(
        getattr(getattr(item, "jhm_wall", item), "wall_id", "") or ""
    ) == expected_id]
    return actual == expected_id and (not candidates or owners == [pointer])


def repair_candidate(expected_id, candidates):
    """Return the sole ID owner for explicit repair, or None if ambiguous."""
    if not expected_id:
        return None
    owners = [item for item in candidates if str(
        getattr(getattr(item, "jhm_wall", item), "wall_id", "") or ""
    ) == expected_id]
    return owners[0] if len(owners) == 1 else None


def duplicate_repair_is_safe(selected, references):
    """Allow repair when no trusted Finish attachment points at selected duplicate."""
    for pointer, expected_id, pointer_known in references:
        if not pointer_known:
            return False
        if pointer is selected and expected_id:
            return False
    return True
