from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.secretsmanager
import tests.data.gcp.secretsmanager
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_PROJECT_ID = "test-project-123"


def _create_test_project(neo4j_session):
    neo4j_session.run(
        """
        MERGE (project:GCPProject{id: $project_id})
        ON CREATE SET project.firstseen = timestamp()
        SET project.lastupdated = $update_tag
        """,
        project_id=TEST_PROJECT_ID,
        update_tag=TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.gcp.secretsmanager,
    "get_secret_versions",
    side_effect=lambda sm, secret_name: tests.data.gcp.secretsmanager.SECRET_VERSIONS_BY_SECRET.get(
        secret_name, []
    ),  # this lambda is a workaround to get the secret versions by secret name
)
@patch.object(
    cartography.intel.gcp.secretsmanager,
    "get_secrets",
    return_value=tests.data.gcp.secretsmanager.LIST_SECRETS_RESPONSE,
)
def test_sync_secretsmanager(mock_get_secrets, mock_get_secret_versions, neo4j_session):
    """Test that sync() loads secrets, secret versions, and creates relationships."""

    # Clear the database
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Arrange
    _create_test_project(neo4j_session)

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }

    # Act
    cartography.intel.gcp.secretsmanager.sync(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Check secret nodes
    assert check_nodes(
        neo4j_session,
        "GCPSecretManagerSecret",
        ["id", "name", "replication_type", "rotation_enabled"],
    ) == {
        (
            "projects/test-project-123/secrets/my-api-key",
            "my-api-key",
            "automatic",
            False,
        ),
        (
            "projects/test-project-123/secrets/db-password",
            "db-password",
            "user_managed",
            True,
        ),
    }

    # Assert - Check secret version nodes
    assert check_nodes(
        neo4j_session,
        "GCPSecretManagerSecretVersion",
        ["id", "version", "state"],
    ) == {
        ("projects/test-project-123/secrets/my-api-key/versions/1", "1", "ENABLED"),
        ("projects/test-project-123/secrets/my-api-key/versions/2", "2", "ENABLED"),
        ("projects/test-project-123/secrets/db-password/versions/1", "1", "DISABLED"),
        ("projects/test-project-123/secrets/db-password/versions/2", "2", "DESTROYED"),
        ("projects/test-project-123/secrets/db-password/versions/3", "3", "ENABLED"),
    }

    # Assert - Check GCPProject -> GCPSecretManagerSecret relationships
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPSecretManagerSecret",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_PROJECT_ID, "projects/test-project-123/secrets/my-api-key"),
        (TEST_PROJECT_ID, "projects/test-project-123/secrets/db-password"),
    }

    # Assert - Check GCPProject -> GCPSecretManagerSecretVersion relationships
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPSecretManagerSecretVersion",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_PROJECT_ID, "projects/test-project-123/secrets/my-api-key/versions/1"),
        (TEST_PROJECT_ID, "projects/test-project-123/secrets/my-api-key/versions/2"),
        (TEST_PROJECT_ID, "projects/test-project-123/secrets/db-password/versions/1"),
        (TEST_PROJECT_ID, "projects/test-project-123/secrets/db-password/versions/2"),
        (TEST_PROJECT_ID, "projects/test-project-123/secrets/db-password/versions/3"),
    }

    # Assert - Check GCPSecretManagerSecretVersion -> GCPSecretManagerSecret relationships
    assert check_rels(
        neo4j_session,
        "GCPSecretManagerSecretVersion",
        "id",
        "GCPSecretManagerSecret",
        "id",
        "VERSION_OF",
        rel_direction_right=True,
    ) == {
        (
            "projects/test-project-123/secrets/my-api-key/versions/1",
            "projects/test-project-123/secrets/my-api-key",
        ),
        (
            "projects/test-project-123/secrets/my-api-key/versions/2",
            "projects/test-project-123/secrets/my-api-key",
        ),
        (
            "projects/test-project-123/secrets/db-password/versions/1",
            "projects/test-project-123/secrets/db-password",
        ),
        (
            "projects/test-project-123/secrets/db-password/versions/2",
            "projects/test-project-123/secrets/db-password",
        ),
        (
            "projects/test-project-123/secrets/db-password/versions/3",
            "projects/test-project-123/secrets/db-password",
        ),
    }
