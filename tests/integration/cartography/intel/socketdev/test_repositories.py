from unittest.mock import patch

import cartography.intel.socketdev.repositories
import tests.data.socketdev.repositories
from cartography.intel.github.repos import load_github_repos
from cartography.intel.socketdev.organizations import load_organizations
from cartography.intel.socketdev.organizations import transform as transform_orgs
from tests.data.socketdev.organizations import ORGANIZATIONS_RESPONSE
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "org-001"
TEST_ORG_SLUG = "acme-corp"


@patch.object(
    cartography.intel.socketdev.repositories,
    "get",
    return_value=(
        tests.data.socketdev.repositories.REPOSITORIES_RESPONSE["results"],
        set(),
    ),
)
def test_sync_repositories(mock_api, neo4j_session):
    """
    Test that Socket.dev repositories sync correctly and create proper nodes and relationships.
    """
    # Arrange: Load the organization first (repos need it for the sub_resource_relationship)
    orgs = transform_orgs(ORGANIZATIONS_RESPONSE)
    load_organizations(neo4j_session, orgs, TEST_UPDATE_TAG)
    load_github_repos(
        neo4j_session,
        TEST_UPDATE_TAG,
        [
            {
                "id": "https://github.com/Example/Worker",
                "name": "Worker",
                "fullname": "Example/Worker",
                "url": "https://github.com/Example/Worker",
            },
            {
                "id": "https://github.com/another-example/worker",
                "name": "worker",
                "fullname": "another-example/worker",
                "url": "https://github.com/another-example/worker",
            },
            {
                "id": "https://github.com/example/service",
                "name": "service",
                "fullname": "example/service",
                "url": "https://github.com/example/service",
            },
        ],
    )

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": TEST_ORG_ID,
        "ORG_SLUG": TEST_ORG_SLUG,
    }

    # Act
    cartography.intel.socketdev.repositories.sync_repositories(
        neo4j_session,
        "fake-token",
        TEST_ORG_SLUG,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert: Organization exists
    expected_org_nodes = {
        (TEST_ORG_ID, TEST_ORG_SLUG),
    }
    assert (
        check_nodes(neo4j_session, "SocketDevOrganization", ["id", "slug"])
        == expected_org_nodes
    )

    # Assert: Repositories preserve Socket identity and GitHub integration identity
    expected_repo_nodes = {
        (
            "repo-001",
            "frontend-app",
            "acme-corp/frontend-app",
            None,
        ),
        ("repo-002", "backend-api", "acme-corp/backend-api", None),
        (
            "repo-003",
            "worker",
            "acme-corp/worker",
            "https://github.com/Example/Worker",
        ),
        (
            "repo-004",
            "service",
            "service",
            "https://github.com/example/service",
        ),
    }
    assert (
        check_nodes(
            neo4j_session,
            "SocketDevRepository",
            ["id", "slug", "fullname", "repository_url"],
        )
        == expected_repo_nodes
    )

    # Assert: Repositories are connected to Organization
    expected_rels = {
        ("repo-001", TEST_ORG_ID),
        ("repo-002", TEST_ORG_ID),
        ("repo-003", TEST_ORG_ID),
        ("repo-004", TEST_ORG_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "SocketDevRepository",
            "id",
            "SocketDevOrganization",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert: mixed-case GitHub identities are preserved for exact URL matching.
    assert check_rels(
        neo4j_session,
        "SocketDevRepository",
        "id",
        "GitHubRepository",
        "id",
        "MONITORS",
        rel_direction_right=True,
    ) == {
        ("repo-003", "https://github.com/Example/Worker"),
        ("repo-004", "https://github.com/example/service"),
    }

    # Act: Lose the source identity during an incomplete sync
    refreshed_repositories = tests.data.socketdev.repositories.REPOSITORIES_RESPONSE[
        "results"
    ]
    repositories_without_identity = [
        refreshed_repositories[0],
        refreshed_repositories[1],
        {**refreshed_repositories[2], "integration_meta": None},
        refreshed_repositories[3],
    ]
    mock_api.return_value = (repositories_without_identity, {"repo-003"})
    next_update_tag = TEST_UPDATE_TAG + 1
    common_job_parameters["UPDATE_TAG"] = next_update_tag
    cartography.intel.socketdev.repositories.sync_repositories(
        neo4j_session,
        "fake-token",
        TEST_ORG_SLUG,
        next_update_tag,
        common_job_parameters,
    )

    # Assert: Incomplete collection preserves the previous relationship
    assert check_rels(
        neo4j_session,
        "SocketDevRepository",
        "id",
        "GitHubRepository",
        "id",
        "MONITORS",
        rel_direction_right=True,
    ) == {
        ("repo-003", "https://github.com/Example/Worker"),
        ("repo-004", "https://github.com/example/service"),
    }
    assert check_nodes(
        neo4j_session,
        "SocketDevRepository",
        ["id", "repository_url"],
    ) >= {
        ("repo-003", "https://github.com/Example/Worker"),
    }

    # Act: Confirm the identity is absent in a complete sync
    final_update_tag = next_update_tag + 1
    common_job_parameters["UPDATE_TAG"] = final_update_tag
    mock_api.return_value = (repositories_without_identity, set())
    cartography.intel.socketdev.repositories.sync_repositories(
        neo4j_session,
        "fake-token",
        TEST_ORG_SLUG,
        final_update_tag,
        common_job_parameters,
    )

    # Assert: The stale relationship is removed
    assert check_rels(
        neo4j_session,
        "SocketDevRepository",
        "id",
        "GitHubRepository",
        "id",
        "MONITORS",
        rel_direction_right=True,
    ) == {
        ("repo-004", "https://github.com/example/service"),
    }
