from unittest.mock import patch

import requests

import cartography.intel.github.webhooks
from tests.data.github.webhooks import ORG_WEBHOOKS
from tests.data.github.webhooks import REPO_WEBHOOKS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_JOB_PARAMS = {"UPDATE_TAG": TEST_UPDATE_TAG}
TEST_GITHUB_URL = "https://api.github.com/graphql"
TEST_ORGANIZATION = "simpsoncorp"
FAKE_TOKEN = "fake-pat"
ORG_URL = "https://github.com/simpsoncorp"
REPO_URL = "https://github.com/simpsoncorp/sample_repo"
SECOND_REPO_URL = "https://github.com/simpsoncorp/another_repo"
STALE_ID = "https://api.github.com/orgs/simpsoncorp/hooks/1"
REPOS = [
    {"url": REPO_URL, "fullname": "simpsoncorp/sample_repo"},
    {"url": SECOND_REPO_URL, "fullname": "simpsoncorp/another_repo"},
]


def _http_error(status):
    response = requests.Response()
    response.status_code = status
    return requests.exceptions.HTTPError(response=response)


def _pages(token, base_url, endpoint, result_key, **kwargs):
    if endpoint == "/orgs/simpsoncorp/hooks":
        return ORG_WEBHOOKS
    fullname = endpoint.removeprefix("/repos/").removesuffix("/hooks")
    return REPO_WEBHOOKS[fullname]


def _pages_repo_forbidden(token, base_url, endpoint, result_key, **kwargs):
    if endpoint == "/repos/simpsoncorp/another_repo/hooks":
        raise _http_error(403)
    return _pages(token, base_url, endpoint, result_key, **kwargs)


def _reset_and_seed_graph(neo4j_session):
    neo4j_session.run("MATCH (n:GitHubWebhook) DETACH DELETE n")
    neo4j_session.run(
        """
        MERGE (org:GitHubOrganization {id: $org_url})
        MERGE (repo:GitHubRepository {id: $repo_url})
        MERGE (second_repo:GitHubRepository {id: $second_repo_url})
        MERGE (stale:GitHubWebhook {id: $stale_id})
        SET stale.lastupdated = 1
        MERGE (org)-[:RESOURCE {lastupdated: 1}]->(stale)
        """,
        org_url=ORG_URL,
        repo_url=REPO_URL,
        second_repo_url=SECOND_REPO_URL,
        stale_id=STALE_ID,
    )


@patch.object(
    cartography.intel.github.webhooks,
    "fetch_all_rest_api_pages",
    side_effect=_pages,
)
def test_sync_webhooks(mock_pages, neo4j_session):
    # Arrange
    _reset_and_seed_graph(neo4j_session)

    # Act
    cartography.intel.github.webhooks.sync(
        neo4j_session,
        TEST_JOB_PARAMS,
        FAKE_TOKEN,
        TEST_GITHUB_URL,
        TEST_ORGANIZATION,
        REPOS,
    )

    # Assert - target URLs are reduced to scheme and host; the stale hook is removed.
    assert check_nodes(
        neo4j_session,
        "GitHubWebhook",
        [
            "id",
            "scope",
            "target_scheme",
            "target_host",
            "uses_https",
            "insecure_ssl",
            "has_secret",
            "last_response_code",
        ],
    ) == {
        (
            "https://api.github.com/orgs/simpsoncorp/hooks/501",
            "organization",
            "https",
            "siem.simpsoncorp.example",
            True,
            False,
            True,
            None,
        ),
        (
            "https://api.github.com/repos/simpsoncorp/sample_repo/hooks/601",
            "repository",
            "http",
            "jenkins.simpsoncorp.example",
            False,
            True,
            False,
            200,
        ),
    }
    assert check_rels(
        neo4j_session,
        "GitHubOrganization",
        "id",
        "GitHubWebhook",
        "hook_id",
        "HAS_WEBHOOK",
    ) == {(ORG_URL, 501)}
    assert check_rels(
        neo4j_session,
        "GitHubRepository",
        "id",
        "GitHubWebhook",
        "hook_id",
        "HAS_WEBHOOK",
    ) == {(REPO_URL, 601)}
    assert check_rels(
        neo4j_session,
        "GitHubOrganization",
        "id",
        "GitHubWebhook",
        "hook_id",
        "RESOURCE",
    ) == {(ORG_URL, 501), (ORG_URL, 601)}
    stored_properties = neo4j_session.run(
        "MATCH (h:GitHubWebhook) RETURN properties(h) AS p",
    ).data()
    assert not any("abc123" in str(row["p"]) for row in stored_properties)


@patch.object(
    cartography.intel.github.webhooks,
    "fetch_all_rest_api_pages",
    side_effect=_pages_repo_forbidden,
)
def test_sync_webhooks_incomplete_inventory_skips_cleanup(mock_pages, neo4j_session):
    # Arrange
    _reset_and_seed_graph(neo4j_session)

    # Act
    cartography.intel.github.webhooks.sync(
        neo4j_session,
        TEST_JOB_PARAMS,
        FAKE_TOKEN,
        TEST_GITHUB_URL,
        TEST_ORGANIZATION,
        REPOS,
    )

    # Assert - visible hooks load, and the stale hook survives.
    assert check_nodes(neo4j_session, "GitHubWebhook", ["id"]) == {
        (STALE_ID,),
        ("https://api.github.com/orgs/simpsoncorp/hooks/501",),
        ("https://api.github.com/repos/simpsoncorp/sample_repo/hooks/601",),
    }
