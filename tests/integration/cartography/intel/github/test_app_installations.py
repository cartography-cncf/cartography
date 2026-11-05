from unittest.mock import patch

import requests

import cartography.intel.github.app_installations
import cartography.intel.github.util
from tests.data.github.app_installations import APP_INSTALLATIONS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_JOB_PARAMS = {"UPDATE_TAG": TEST_UPDATE_TAG}
TEST_GITHUB_URL = "https://api.github.com/graphql"
TEST_ORGANIZATION = "simpsoncorp"
FAKE_TOKEN = "fake-pat"
ORG_URL = "https://github.com/simpsoncorp"
STALE_ID = f"{ORG_URL}/installations/999"


def _reset_and_seed_graph(neo4j_session):
    neo4j_session.run("MATCH (n:GitHubAppInstallation) DETACH DELETE n")
    neo4j_session.run(
        """
        MERGE (org:GitHubOrganization {id: $org_url})
        MERGE (stale:GitHubAppInstallation {id: $stale_id})
        SET stale.lastupdated = 1, stale.app_slug = 'removed-app'
        MERGE (org)-[:RESOURCE {lastupdated: 1}]->(stale)
        """,
        org_url=ORG_URL,
        stale_id=STALE_ID,
    )


@patch.object(
    cartography.intel.github.util,
    "fetch_all_rest_api_pages",
    return_value=APP_INSTALLATIONS,
)
def test_sync_app_installations(mock_pages, neo4j_session):
    # Arrange
    _reset_and_seed_graph(neo4j_session)

    # Act
    cartography.intel.github.app_installations.sync(
        neo4j_session,
        TEST_JOB_PARAMS,
        FAKE_TOKEN,
        TEST_GITHUB_URL,
        TEST_ORGANIZATION,
    )

    # Assert
    assert mock_pages.call_args.args[2:4] == (
        "/orgs/simpsoncorp/installations",
        "installations",
    )
    assert check_nodes(
        neo4j_session,
        "GitHubAppInstallation",
        ["id", "app_slug", "client_id", "repository_selection", "enabled"],
    ) == {
        (f"{ORG_URL}/installations/1001", "renovate", "Iv1.renovate0001", "all", True),
        (
            f"{ORG_URL}/installations/1002",
            "legacy-admin-bot",
            "Iv1.legacyadmin002",
            "selected",
            False,
        ),
    }
    rows = neo4j_session.run(
        """
        MATCH (i:GitHubAppInstallation:ThirdPartyApp)
        RETURN i.app_slug AS slug, i.write_permissions AS write,
            i.suspended_by AS suspended_by
        ORDER BY slug
        """,
    ).data()
    assert rows == [
        {
            "slug": "legacy-admin-bot",
            "write": ["administration", "organization_administration"],
            "suspended_by": "mbsimpson",
        },
        {
            "slug": "renovate",
            "write": ["checks", "contents", "pull_requests", "workflows"],
            "suspended_by": None,
        },
    ]
    assert check_rels(
        neo4j_session,
        "GitHubOrganization",
        "id",
        "GitHubAppInstallation",
        "app_slug",
        "RESOURCE",
    ) == {(ORG_URL, "renovate"), (ORG_URL, "legacy-admin-bot")}


@patch.object(cartography.intel.github.util, "fetch_all_rest_api_pages")
def test_sync_app_installations_forbidden_preserves_data(mock_pages, neo4j_session):
    # Arrange
    _reset_and_seed_graph(neo4j_session)
    response = requests.Response()
    response.status_code = 403
    mock_pages.side_effect = requests.exceptions.HTTPError(response=response)

    # Act
    cartography.intel.github.app_installations.sync(
        neo4j_session,
        TEST_JOB_PARAMS,
        FAKE_TOKEN,
        TEST_GITHUB_URL,
        TEST_ORGANIZATION,
    )

    # Assert
    assert check_nodes(neo4j_session, "GitHubAppInstallation", ["id"]) == {
        (STALE_ID,),
    }
