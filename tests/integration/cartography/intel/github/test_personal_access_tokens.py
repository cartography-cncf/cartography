from unittest.mock import patch

import requests

import cartography.intel.github.personal_access_tokens
from tests.data.github.personal_access_tokens import FINE_GRAINED_PAT_REPOSITORIES
from tests.data.github.personal_access_tokens import FINE_GRAINED_PERSONAL_ACCESS_TOKENS
from tests.data.github.personal_access_tokens import SAML_CREDENTIAL_AUTHORIZATIONS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_JOB_PARAMS = {"UPDATE_TAG": TEST_UPDATE_TAG}
TEST_GITHUB_URL = "https://api.github.com/graphql"
TEST_ORGANIZATION = "simpsoncorp"
FAKE_TOKEN = "fake-pat"

ORG_URL = "https://github.com/simpsoncorp"
USER_URL = "https://github.com/hjsimpson"
SECOND_USER_URL = "https://github.com/mbsimpson"
REPO_URL = "https://github.com/simpsoncorp/sample_repo"
SECOND_REPO_URL = "https://github.com/simpsoncorp/another_repo"


def _reset_and_seed_graph(neo4j_session):
    neo4j_session.run("MATCH (n:GitHubPersonalAccessToken) DETACH DELETE n")
    neo4j_session.run(
        """
        MERGE (org:GitHubOrganization {id: $org_url})
        SET org.username = $org_login
        MERGE (user:GitHubUser {id: $user_url})
        SET user.username = "hjsimpson"
        MERGE (second_user:GitHubUser {id: $second_user_url})
        SET second_user.username = "mbsimpson"
        MERGE (repo:GitHubRepository {id: $repo_url})
        SET repo.name = "sample_repo"
        MERGE (second_repo:GitHubRepository {id: $second_repo_url})
        SET second_repo.name = "another_repo"
        MERGE (repo)-[:OWNER]->(org)
        MERGE (second_repo)-[:OWNER]->(org)
        """,
        org_url=ORG_URL,
        org_login=TEST_ORGANIZATION,
        user_url=USER_URL,
        second_user_url=SECOND_USER_URL,
        repo_url=REPO_URL,
        second_repo_url=SECOND_REPO_URL,
    )


def _seed_stale_tokens(neo4j_session):
    neo4j_session.run(
        """
        MATCH (org:GitHubOrganization {id: $org_url})
        MERGE (repo:GitHubRepository {id: $repo_url})
        MERGE (user:GitHubUser {id: $user_url})
        MERGE (fine:GitHubFineGrainedPersonalAccessToken:GitHubPersonalAccessToken {
            id: $org_url + "/personal-access-tokens/stale"
        })
        SET fine.lastupdated = 1,
            fine.source = "fine_grained_personal_access_tokens",
            fine.token_kind = "fine_grained"
        MERGE (classic:GitHubClassicPersonalAccessToken:GitHubPersonalAccessToken {
            id: $org_url + "/credential-authorizations/stale"
        })
        SET classic.lastupdated = 1,
            classic.source = "saml_credential_authorizations",
            classic.token_kind = "classic"
        MERGE (org)-[:RESOURCE {lastupdated: 1}]->(fine)
        MERGE (org)-[:RESOURCE {lastupdated: 1}]->(classic)
        MERGE (fine)-[:CAN_ACCESS {lastupdated: 1}]->(repo)
        MERGE (user)-[:OWNS {lastupdated: 1}]->(fine)
        """,
        org_url=ORG_URL,
        repo_url=REPO_URL,
        user_url=USER_URL,
    )


def _github_pages_side_effect(token, base_url, endpoint, result_key, **kwargs):
    if endpoint.endswith("/personal-access-tokens"):
        return FINE_GRAINED_PERSONAL_ACCESS_TOKENS
    if endpoint.endswith("/credential-authorizations"):
        return SAML_CREDENTIAL_AUTHORIZATIONS
    if "/personal-access-tokens/" in endpoint and endpoint.endswith("/repositories"):
        pat_id = int(endpoint.split("/personal-access-tokens/")[1].split("/")[0])
        return FINE_GRAINED_PAT_REPOSITORIES[pat_id]
    return []


def _raise_http_status(status_code):
    response = requests.Response()
    response.status_code = status_code
    error = requests.exceptions.HTTPError()
    error.response = response
    raise error


@patch(
    "cartography.intel.github.personal_access_tokens.fetch_all_rest_api_pages",
    side_effect=_github_pages_side_effect,
)
def test_sync_github_personal_access_tokens(mock_pages, neo4j_session):
    # Arrange
    _reset_and_seed_graph(neo4j_session)
    _seed_stale_tokens(neo4j_session)

    # Act
    result = cartography.intel.github.personal_access_tokens.sync(
        neo4j_session,
        TEST_JOB_PARAMS,
        FAKE_TOKEN,
        TEST_GITHUB_URL,
        TEST_ORGANIZATION,
    )

    # Assert
    assert result.cleanup_safe_sources == {
        "fine_grained_personal_access_tokens",
        "saml_credential_authorizations",
    }
    called_endpoints = [call.args[2] for call in mock_pages.call_args_list]
    assert called_endpoints == [
        "/orgs/simpsoncorp/personal-access-tokens",
        "/orgs/simpsoncorp/personal-access-tokens/25381/repositories",
        "/orgs/simpsoncorp/personal-access-tokens/25382/repositories",
        "/orgs/simpsoncorp/credential-authorizations",
    ]
    assert all("api_version" not in call.kwargs for call in mock_pages.call_args_list)
    assert check_nodes(
        neo4j_session,
        "GitHubPersonalAccessToken",
        ["id", "token_kind", "token_name", "owner_login", "owner_url", "source"],
    ) == {
        (
            f"{ORG_URL}/personal-access-tokens/25381",
            "fine_grained",
            "cartography-readonly",
            "hjsimpson",
            "https://github.com/hjsimpson",
            "fine_grained_personal_access_tokens",
        ),
        (
            f"{ORG_URL}/personal-access-tokens/25382",
            "fine_grained",
            "all-repos-readonly",
            "mbsimpson",
            "https://github.com/mbsimpson",
            "fine_grained_personal_access_tokens",
        ),
        (
            f"{ORG_URL}/credential-authorizations/161195",
            "classic",
            None,
            "hjsimpson",
            "https://github.com/hjsimpson",
            "saml_credential_authorizations",
        ),
    }
    assert check_nodes(neo4j_session, "APIKey", ["id"]) >= {
        (f"{ORG_URL}/personal-access-tokens/25381",),
        (f"{ORG_URL}/credential-authorizations/161195",),
    }
    assert check_nodes(
        neo4j_session, "GitHubFineGrainedPersonalAccessToken", ["id"]
    ) == {
        (f"{ORG_URL}/personal-access-tokens/25381",),
        (f"{ORG_URL}/personal-access-tokens/25382",),
    }
    assert check_nodes(neo4j_session, "GitHubClassicPersonalAccessToken", ["id"]) == {
        (f"{ORG_URL}/credential-authorizations/161195",),
    }
    assert check_rels(
        neo4j_session,
        "GitHubOrganization",
        "id",
        "GitHubPersonalAccessToken",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (ORG_URL, f"{ORG_URL}/personal-access-tokens/25381"),
        (ORG_URL, f"{ORG_URL}/personal-access-tokens/25382"),
        (ORG_URL, f"{ORG_URL}/credential-authorizations/161195"),
    }
    assert check_rels(
        neo4j_session,
        "GitHubUser",
        "id",
        "GitHubPersonalAccessToken",
        "id",
        "OWNS",
        rel_direction_right=True,
    ) == {
        (USER_URL, f"{ORG_URL}/personal-access-tokens/25381"),
        (SECOND_USER_URL, f"{ORG_URL}/personal-access-tokens/25382"),
        (USER_URL, f"{ORG_URL}/credential-authorizations/161195"),
    }
    assert check_rels(
        neo4j_session,
        "GitHubPersonalAccessToken",
        "id",
        "GitHubRepository",
        "id",
        "CAN_ACCESS",
        rel_direction_right=True,
    ) == {
        (f"{ORG_URL}/personal-access-tokens/25381", REPO_URL),
        (f"{ORG_URL}/personal-access-tokens/25382", SECOND_REPO_URL),
    }


@patch(
    "cartography.intel.github.personal_access_tokens.fetch_all_rest_api_pages",
    side_effect=lambda *args, **kwargs: _raise_http_status(403),
)
def test_sync_github_personal_access_tokens_preserves_stale_on_unsafe_fetch(
    mock_pages,
    neo4j_session,
):
    # Arrange
    _reset_and_seed_graph(neo4j_session)
    _seed_stale_tokens(neo4j_session)

    # Act
    result = cartography.intel.github.personal_access_tokens.sync(
        neo4j_session,
        TEST_JOB_PARAMS,
        FAKE_TOKEN,
        TEST_GITHUB_URL,
        TEST_ORGANIZATION,
    )

    # Assert
    assert result.cleanup_safe_sources == set()
    assert [call.args[2] for call in mock_pages.call_args_list] == [
        "/orgs/simpsoncorp/personal-access-tokens",
        "/orgs/simpsoncorp/credential-authorizations",
    ]
    assert check_nodes(
        neo4j_session,
        "GitHubPersonalAccessToken",
        ["id", "lastupdated"],
    ) == {
        (f"{ORG_URL}/personal-access-tokens/stale", 1),
        (f"{ORG_URL}/credential-authorizations/stale", 1),
    }
