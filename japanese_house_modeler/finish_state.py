"""Pure managed-Finish diagnosis and conservative repair decisions."""


STATUS_LABELS = {
    "WALL_REFERENCE": "Wall参照不整合",
    "WALL_ID": "Wall ID不整合",
    "WALL_MISSING": "Wall欠落",
    "INTERVAL": "区間不正",
    "DISCONTINUOUS": "経路不連続",
    "OBJECT_TRANSFORM": "Object Transformあり",
    "FINISH_ID": "Finish ID不整合",
    "JOIN_POLICY": "未対応join_policy",
    "CLOSED": "未対応closed状態",
    "PROFILE": "Profile不整合",
}


def finish_problem_keys(transform_identity, references, intervals_valid,
                        path_continuous, span_count=None, extra_problems=()):
    """Classify status from per-span pointer validity and ID integrity."""
    problems = []
    if not transform_identity:
        problems.append("OBJECT_TRANSFORM")
    for reference in references:
        if len(reference) == 3:  # Backward-compatible pure helper input.
            pointer_present, id_matches, ambiguous = reference
            pointer_valid = pointer_present
        else:
            pointer_present, pointer_valid, id_matches, ambiguous = reference
        key = ("WALL_MISSING" if not pointer_present else
               "WALL_REFERENCE" if not pointer_valid else
               "WALL_ID" if ambiguous or not id_matches else None)
        if key and key not in problems:
            problems.append(key)
    if not intervals_valid or span_count == 0:
        problems.append("INTERVAL")
    if not path_continuous or span_count == 0:
        problems.append("DISCONTINUOUS")
    for key in extra_problems:
        if key not in problems:
            problems.append(key)
    return tuple(problems)


def status_label(problems):
    return ("正常" if not problems else
            "要復元（" + " / ".join(STATUS_LABELS[key] for key in problems) + "）")


def unique_rebind_candidate(expected_id, owners):
    """Repair may rebind only one exact owner, never an ambiguous duplicate."""
    if not expected_id:
        return None
    matches = [owner for owner in owners if owner[1] == expected_id]
    return matches[0][0] if len(matches) == 1 else None
