"""Pure Build 06-A Stage 3 validation and managed-profile decisions."""

SUPPORTED_JOIN_POLICY = "MITER"
VERIFICATION_PROFILE_ROLE = "BUILD_06_A_VERIFICATION"
VERIFICATION_PROFILE_VERSION = 1


def finish_configuration_problems(join_policy, closed):
    """Return stable machine-readable keys for unsupported persisted state."""
    problems = []
    if join_policy != SUPPORTED_JOIN_POLICY:
        problems.append("JOIN_POLICY")
    if closed:
        problems.append("CLOSED")
    return tuple(problems)


def validate_finish_configuration(join_policy, closed):
    """Reject features deliberately outside Build 06-A without rewriting them."""
    if join_policy != SUPPORTED_JOIN_POLICY:
        raise ValueError(f"このBuildでは join_policy={join_policy} は未対応です。")
    if closed:
        raise ValueError("このBuildでは closed=True は未対応です。")
    return True


def duplicate_finish_ids(records):
    """Return duplicated normalized IDs without assigning heuristic ownership."""
    owners = {}
    for owner, finish_id in records:
        normalized = normalize_finish_id(finish_id)
        if normalized:
            owners.setdefault(normalized, []).append(owner)
    return {value: tuple(items) for value, items in owners.items()
            if len(items) > 1}


def normalize_finish_id(finish_id):
    """Normalize only for comparison; callers must not rewrite canonical state."""
    return finish_id.strip() if isinstance(finish_id, str) else ""


def finish_id_is_valid(finish_id, duplicated_ids=()):
    """Apply the shared diagnosis/regeneration/conversion identity policy."""
    normalized = normalize_finish_id(finish_id)
    return bool(normalized) and normalized not in duplicated_ids


def profile_identity_matches(object_type, data_type, metadata, orientation):
    """Decide whether persistent custom metadata identifies our exact profile."""
    return (
        object_type == "CURVE"
        and data_type == "CURVE"
        and metadata.get("jhm_managed_profile") is True
        and metadata.get("jhm_profile_role") == VERIFICATION_PROFILE_ROLE
        and metadata.get("jhm_profile_version") == VERIFICATION_PROFILE_VERSION
        and metadata.get("jhm_profile_orientation") == orientation
    )


def managed_finish_objects(records):
    """Stable pure selection used by explicit bulk regeneration."""
    return tuple(obj for obj, is_finish in records if is_finish)


def finish_intervals_are_valid(span_intervals, exclusion_intervals):
    """Validate the two canonical record kinds without collection membership."""
    from .finish_path import resolve_interval

    try:
        for interval in span_intervals:
            resolve_interval(*interval)
        for interval in exclusion_intervals:
            resolve_interval(*interval)
    except (TypeError, ValueError):
        return False
    return True
