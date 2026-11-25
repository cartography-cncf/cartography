from cartography.intel.langsmith.sso import transform_policies


def _condition(name: str, key: str, operator: str, value: str) -> dict[str, str]:
    return {
        "attribute_name": name,
        "attribute_key": key,
        "operator": operator,
        "attribute_value": value,
    }


def test_transform_policies_summarizes_ored_groups_of_anded_conditions():
    # Arrange
    policy = {
        "id": "policy-1",
        "name": "Block sensitive projects",
        "effect": "deny",
        "role_ids": [],
        "condition_groups": [
            {
                "permission": "runs:read",
                "resource_type": "project",
                "conditions": [
                    _condition("resource_tag_key", "sensitivity", "equals", "high"),
                    _condition("resource_tag_key", "team", "not_equals", "security"),
                ],
            },
            {
                "permission": "runs:read",
                "resource_type": "run",
                "conditions": [
                    _condition(
                        "root_run_metadata", "owner", "equals", "${user.ls_user_id}"
                    ),
                ],
            },
        ],
    }

    # Act
    (transformed,) = transform_policies([policy], "org-1")

    # Assert
    assert transformed["condition_summary"] == (
        "(runs:read on project: resource_tag_key:sensitivity equals high "
        "AND resource_tag_key:team not_equals security) "
        "OR (runs:read on run: root_run_metadata:owner equals ${user.ls_user_id})"
    )
    assert transformed["condition_tag_keys"] == ["sensitivity", "team"]


def test_transform_policies_handles_a_policy_without_conditions():
    # Act
    (transformed,) = transform_policies(
        [{"id": "policy-1", "role_ids": [], "condition_groups": []}], "org-1"
    )

    # Assert
    assert transformed["condition_summary"] is None
    assert transformed["condition_tag_keys"] == []
