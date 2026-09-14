"""Persistent identity and reference-validation helpers for managed objects."""

import math
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


def validate_wall_reference(pointer, expected_id, candidates=(), managed=None,
                            identity_transform=lambda _item: True):
    """Raise unless a persistent reference and canonical Wall are trustworthy."""
    if not expected_id:
        raise ValueError("Wall参照IDが空です。")
    if not reference_is_trusted(pointer, expected_id, candidates, managed):
        raise ValueError("Wall参照が無効またはWall IDが重複しています。")
    if not identity_transform(pointer):
        raise ValueError("参照WallにObject Transformがあります。先にWallを管理状態へ復元してください。")
    wall = pointer.jhm_wall
    values = tuple(wall.start[:3]) + tuple(wall.end[:3]) + (
        wall.wall_thickness, wall.wall_height)
    if not all(math.isfinite(float(value)) for value in values):
        raise ValueError("参照Wallのcanonical寸法が有限ではありません。")
    if math.dist(tuple(wall.start[:2]), tuple(wall.end[:2])) <= 1e-9:
        raise ValueError("参照Wallが縮退しています。")
    if wall.wall_thickness <= 0.0 or wall.wall_height <= 0.0:
        raise ValueError("参照Wallの壁厚または壁高さが不正です。")
    return pointer


def validate_managed_wall_reference(pointer, expected_id, candidates,
                                    managed, identity_transform):
    """Production entry point with every mandatory policy argument required."""
    if candidates is None or managed is None or identity_transform is None:
        raise TypeError("production Wall validation policy is required")
    return validate_wall_reference(pointer, expected_id, candidates,
                                   managed, identity_transform)


def validate_repair_target_reference(pointer, expected_id, target, managed):
    """Allow only the selected repair target's transform/ID ambiguity pre-repair."""
    if pointer is not target:
        raise ValueError("repair対象外のWall参照が不正です。")
    # An empty candidate index permits duplicate ownership only; all canonical,
    # managed, pointer/ID-match and numeric checks remain active.
    return validate_wall_reference(
        pointer, expected_id, (), managed, lambda _item: True)


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
