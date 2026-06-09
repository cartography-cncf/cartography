import datetime

import cartography.intel.aws.ecr_pull_through_cache_rules as ecr_pull_through_cache_rules

TEST_ACCOUNT_ID = "000000000000"


def test_transform_pull_through_cache_rules_handles_root_and_unknown_upstream():
    # Arrange
    created_at = datetime.datetime(2026, 1, 1, 0, 0, 1)
    updated_at = datetime.datetime(2026, 1, 2, 0, 0, 1)
    rules = [
        {
            "ecrRepositoryPrefix": "ROOT",
            "registryId": TEST_ACCOUNT_ID,
            "upstreamRegistry": "future-registry",
            "createdAt": created_at,
            "updatedAt": updated_at,
        }
    ]

    # Act
    transformed = ecr_pull_through_cache_rules.transform_pull_through_cache_rules(
        rules,
        "us-west-2",
    )

    # Assert
    assert transformed == [
        {
            "id": f"{TEST_ACCOUNT_ID}:us-west-2:ROOT",
            "registry_id": TEST_ACCOUNT_ID,
            "ecr_repository_prefix": "ROOT",
            "upstream_registry_url": None,
            "upstream_registry": "future-registry",
            "upstream_repository_prefix": None,
            "credential_arn": None,
            "custom_role_arn": None,
            "created_at": created_at,
            "updated_at": updated_at,
        }
    ]
