from unittest.mock import patch

import requests

import cartography.intel.nullify.repositories
import cartography.intel.nullify.tenant
import tests.data.nullify.repositories
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_TENANT = "acme"


def _ensure_local_neo4j_has_test_tenant(neo4j_session):
    cartography.intel.nullify.tenant.sync(neo4j_session, TEST_TENANT, TEST_UPDATE_TAG)


def _ensure_local_neo4j_has_test_repositories(neo4j_session):
    _ensure_local_neo4j_has_test_tenant(neo4j_session)
    cartography.intel.nullify.repositories.load_repositories(
        neo4j_session,
        cartography.intel.nullify.repositories.transform(
            [dict(r) for r in tests.data.nullify.repositories.NULLIFY_REPOSITORIES]
        ),
        TEST_TENANT,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.nullify.repositories,
    "get",
    return_value=tests.data.nullify.repositories.NULLIFY_REPOSITORIES,
)
def test_load_nullify_repositories(mock_api, neo4j_session):
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_TENANT,
        "BASE_URL": "https://api.acme.nullify.ai",
    }
    _ensure_local_neo4j_has_test_tenant(neo4j_session)
    # Seed the source-control nodes the repositories should MIRROR.
    neo4j_session.run(
        "MERGE (:GitHubRepository {id: 'https://github.com/acme/web-app', fullname: 'acme/web-app'})"
    )
    neo4j_session.run(
        "MERGE (:GitLabProject {id: 42, web_url: 'https://gitlab.com/acme/api'})"
    )

    # Act
    cartography.intel.nullify.repositories.sync(
        neo4j_session,
        api_session,
        "https://api.acme.nullify.ai",
        TEST_TENANT,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert repositories exist
    assert check_nodes(neo4j_session, "NullifyRepository", ["id", "repository_id"]) == {
        ("repo-1", "R1"),
        ("repo-2", "R2"),
    }

    # Assert repositories are scoped to the tenant
    assert check_rels(
        neo4j_session,
        "NullifyRepository",
        "id",
        "NullifyTenant",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("repo-1", TEST_TENANT),
        ("repo-2", TEST_TENANT),
    }

    # Assert the GitHub repository is mirrored
    assert check_rels(
        neo4j_session,
        "NullifyRepository",
        "id",
        "GitHubRepository",
        "fullname",
        "MIRRORS",
        rel_direction_right=True,
    ) == {
        ("repo-1", "acme/web-app"),
    }

    # Assert the GitLab project is mirrored
    assert check_rels(
        neo4j_session,
        "NullifyRepository",
        "id",
        "GitLabProject",
        "web_url",
        "MIRRORS",
        rel_direction_right=True,
    ) == {
        ("repo-2", "https://gitlab.com/acme/api"),
    }
