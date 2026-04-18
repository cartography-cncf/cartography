from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.jfrog.repositories
import tests.data.jfrog.repositories
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_TENANT_ID = "example-tenant"
TEST_BASE_URL = "https://example.jfrog.io"


def _ensure_local_neo4j_has_test_repositories(neo4j_session):
    transformed = cartography.intel.jfrog.repositories.transform_repositories(
        tests.data.jfrog.repositories.JFROG_REPOSITORIES,
        TEST_TENANT_ID,
    )
    cartography.intel.jfrog.repositories.load_tenant(
        neo4j_session,
        TEST_TENANT_ID,
        TEST_BASE_URL,
        TEST_UPDATE_TAG,
    )
    cartography.intel.jfrog.repositories.load_repositories(
        neo4j_session,
        transformed,
        TEST_TENANT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.jfrog.repositories,
    "get_repositories",
    return_value=tests.data.jfrog.repositories.JFROG_REPOSITORIES,
)
def test_load_jfrog_repositories(mock_api, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_TENANT_ID,
    }

    cartography.intel.jfrog.repositories.sync(
        neo4j_session,
        api_session,
        TEST_BASE_URL,
        TEST_TENANT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    expected_tenant_nodes = {
        (TEST_TENANT_ID, "example.jfrog.io", TEST_BASE_URL),
    }
    assert (
        check_nodes(
            neo4j_session,
            "JFrogArtifactoryTenant",
            ["id", "name", "base_url"],
        )
        == expected_tenant_nodes
    )

    expected_repo_nodes = {
        (
            f"{TEST_TENANT_ID}:docker-prod",
            "docker-prod",
            "Docker",
            "LOCAL",
            "PRJ",
        ),
        (
            f"{TEST_TENANT_ID}:maven-remote",
            "maven-remote",
            "Maven",
            "REMOTE",
            "PRJ",
        ),
    }
    assert (
        check_nodes(
            neo4j_session,
            "JFrogArtifactoryRepository",
            ["id", "key", "package_type", "repo_type", "project_key"],
        )
        == expected_repo_nodes
    )

    expected_rels = {
        (TEST_TENANT_ID, f"{TEST_TENANT_ID}:docker-prod"),
        (TEST_TENANT_ID, f"{TEST_TENANT_ID}:maven-remote"),
    }
    assert (
        check_rels(
            neo4j_session,
            "JFrogArtifactoryTenant",
            "id",
            "JFrogArtifactoryRepository",
            "id",
            "RESOURCE",
            rel_direction_right=True,
        )
        == expected_rels
    )
