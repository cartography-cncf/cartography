from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ecr_pull_through_cache_rules as ecr_pull_through_cache_rules
import tests.data.aws.ecr
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789
TEST_UPDATE_TAG_2 = 987654321


def _reset_graph(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")


def _seed_relationship_targets(neo4j_session):
    secret_arn = tests.data.aws.ecr.PULL_THROUGH_CACHE_SECRET_ARN
    role_arn = tests.data.aws.ecr.PULL_THROUGH_CACHE_ROLE_ARN
    neo4j_session.run(
        """
        MERGE (secret:SecretsManagerSecret {id: $secret_arn})
        SET secret.arn = $secret_arn, secret.name = "dockerhub"
        """,
        secret_arn=secret_arn,
    )
    neo4j_session.run(
        """
        MERGE (role:AWSRole:AWSPrincipal {id: $role_arn})
        SET role.arn = $role_arn, role.name = "ecr-pull-through-cache-role"
        """,
        role_arn=role_arn,
    )


@patch.object(
    ecr_pull_through_cache_rules,
    "get_pull_through_cache_rules",
    side_effect=[
        tests.data.aws.ecr.PULL_THROUGH_CACHE_RULES,
        tests.data.aws.ecr.PULL_THROUGH_CACHE_RULES_SECOND_SYNC,
    ],
)
def test_sync_pull_through_cache_rules(mock_get_rules, neo4j_session):
    # Arrange
    _reset_graph(neo4j_session)
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    _seed_relationship_targets(neo4j_session)

    # Act
    ecr_pull_through_cache_rules.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "ECRPullThroughCacheRule",
        [
            "id",
            "registry_id",
            "ecr_repository_prefix",
            "upstream_registry_url",
            "upstream_registry",
            "upstream_repository_prefix",
            "credential_arn",
            "custom_role_arn",
            "region",
        ],
    ) == {
        (
            f"{TEST_ACCOUNT_ID}:{TEST_REGION}:docker-hub",
            TEST_ACCOUNT_ID,
            "docker-hub",
            "registry-1.docker.io",
            "docker-hub",
            "library",
            tests.data.aws.ecr.PULL_THROUGH_CACHE_SECRET_ARN,
            tests.data.aws.ecr.PULL_THROUGH_CACHE_ROLE_ARN,
            TEST_REGION,
        ),
        (
            f"{TEST_ACCOUNT_ID}:{TEST_REGION}:ROOT",
            TEST_ACCOUNT_ID,
            "ROOT",
            "public.ecr.aws",
            "ecr-public",
            "ROOT",
            None,
            None,
            TEST_REGION,
        ),
    }
    assert check_rels(
        neo4j_session,
        "ECRPullThroughCacheRule",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (f"{TEST_ACCOUNT_ID}:{TEST_REGION}:docker-hub", TEST_ACCOUNT_ID),
        (f"{TEST_ACCOUNT_ID}:{TEST_REGION}:ROOT", TEST_ACCOUNT_ID),
    }
    assert check_rels(
        neo4j_session,
        "ECRPullThroughCacheRule",
        "id",
        "SecretsManagerSecret",
        "arn",
        "USES_SECRET",
        rel_direction_right=True,
    ) == {
        (
            f"{TEST_ACCOUNT_ID}:{TEST_REGION}:docker-hub",
            tests.data.aws.ecr.PULL_THROUGH_CACHE_SECRET_ARN,
        )
    }
    assert check_rels(
        neo4j_session,
        "ECRPullThroughCacheRule",
        "id",
        "AWSRole",
        "arn",
        "ASSOCIATED_WITH",
        rel_direction_right=True,
    ) == {
        (
            f"{TEST_ACCOUNT_ID}:{TEST_REGION}:docker-hub",
            tests.data.aws.ecr.PULL_THROUGH_CACHE_ROLE_ARN,
        )
    }

    # Act
    ecr_pull_through_cache_rules.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG_2,
        {"UPDATE_TAG": TEST_UPDATE_TAG_2, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "ECRPullThroughCacheRule",
        ["id", "lastupdated"],
    ) == {
        (f"{TEST_ACCOUNT_ID}:{TEST_REGION}:ROOT", TEST_UPDATE_TAG_2),
    }
    assert (
        check_rels(
            neo4j_session,
            "ECRPullThroughCacheRule",
            "id",
            "SecretsManagerSecret",
            "arn",
            "USES_SECRET",
            rel_direction_right=True,
        )
        == set()
    )
    assert mock_get_rules.call_args_list[0].args == (
        boto3_session,
        TEST_REGION,
        TEST_ACCOUNT_ID,
    )
