"""
Integration tests for the Netlify compute resources: deploys, functions, dev servers and agent
runners.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import neo4j
import requests

import cartography.intel.netlify.agentrunners
import cartography.intel.netlify.deploys
import cartography.intel.netlify.devservers
import cartography.intel.netlify.functions
import tests.data.netlify.agentrunners
import tests.data.netlify.devservers
import tests.data.netlify.functions
import tests.data.netlify.sites
import tests.data.netlify.users
from tests.integration.cartography.intel.netlify.common import common_job_parameters
from tests.integration.cartography.intel.netlify.common import (
    create_test_netlify_account,
)
from tests.integration.cartography.intel.netlify.common import create_test_netlify_users
from tests.integration.cartography.intel.netlify.common import find_secret_in_graph
from tests.integration.cartography.intel.netlify.common import TEST_ACCOUNT_ID
from tests.integration.cartography.intel.netlify.common import TEST_BASE_URL
from tests.integration.cartography.intel.netlify.common import TEST_SITE_ID
from tests.integration.cartography.intel.netlify.common import TEST_UPDATE_TAG
from tests.integration.cartography.intel.netlify.common import TEST_USER_ID
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

_DEPLOY_ID = "6b6b7982e9b39032db65efe0"
_AGENT_RUNNER_ID = "6b6b7a4e4f165dc4ef66e107"
_DEV_SERVER_ID = "6b6b7a82410ee435820212be"
_SKEW_TOKEN_PREFIX = "a5d4f63c918faf7989e2c686"


def _arrange(neo4j_session: neo4j.Session) -> None:
    """Seed the tenant, the users the compute nodes point at, and the sites they belong to."""
    create_test_netlify_account(neo4j_session)
    create_test_netlify_users(neo4j_session)
    cartography.intel.netlify.sites.load_netlify_sites(
        neo4j_session,
        cartography.intel.netlify.sites.transform_netlify_sites(
            tests.data.netlify.sites.NETLIFY_SITES,
        ),
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


def test_sync_netlify_deploys(neo4j_session: neo4j.Session) -> None:
    # Arrange
    _arrange(neo4j_session)

    # Act: no get_* to patch, the published deploy is embedded in the site payload
    cartography.intel.netlify.deploys.sync_netlify_deploys(
        neo4j_session,
        tests.data.netlify.sites.NETLIFY_SITES,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters(),
    )

    # Assert Nodes
    assert check_nodes(
        neo4j_session,
        "NetlifyDeploy",
        ["id", "state", "context", "deploy_source", "manual_deploy"],
    ) == {(_DEPLOY_ID, "ready", "production", "cli", False)}

    # Assert the secret-scan report was flattened to counts
    assert check_nodes(
        neo4j_session,
        "NetlifyDeploy",
        ["secrets_scan_files_scanned", "secrets_scan_matches_count"],
    ) == {(None, 0)}

    # Assert Relationships
    assert check_rels(
        neo4j_session,
        "NetlifySite",
        "id",
        "NetlifyDeploy",
        "id",
        "HAS_DEPLOY",
    ) == {(TEST_SITE_ID, _DEPLOY_ID)}
    assert check_rels(
        neo4j_session,
        "NetlifyDeploy",
        "id",
        "NetlifyUser",
        "id",
        "DEPLOYED_BY",
    ) == {(_DEPLOY_ID, TEST_USER_ID)}

    # The skew protection token is bearer-equivalent and must not be in the graph
    assert find_secret_in_graph(neo4j_session, _SKEW_TOKEN_PREFIX) == []


def test_deploys_skip_sites_with_no_published_deploy() -> None:
    """
    A site that has never had a successful production deploy carries `published_deploy: None`.
    Emitting a row for it would create a NetlifyDeploy with a null id.
    """
    deploys = cartography.intel.netlify.deploys.transform_netlify_deploys(
        tests.data.netlify.sites.NETLIFY_SITES_WITH_GIT,
    )
    assert [d["id"] for d in deploys] == [_DEPLOY_ID]


@patch.object(
    cartography.intel.netlify.functions,
    "get_netlify_functions",
    return_value=tests.data.netlify.functions.NETLIFY_SITE_FUNCTIONS,
)
def test_sync_netlify_functions(mock_get, neo4j_session: neo4j.Session) -> None:
    # Arrange
    _arrange(neo4j_session)
    api_session = MagicMock(spec=requests.Session)

    # Act
    cartography.intel.netlify.functions.sync_netlify_functions(
        neo4j_session,
        api_session,
        TEST_BASE_URL,
        TEST_ACCOUNT_ID,
        tests.data.netlify.sites.NETLIFY_SITES,
        TEST_UPDATE_TAG,
        common_job_parameters(),
    )

    # Assert Nodes: the abbreviated API keys were expanded, and the id is composite because
    # Netlify's own function id is a content hash that changes on every build.
    assert check_nodes(
        neo4j_session,
        "NetlifyFunction",
        ["id", "name", "runtime", "memory_mb", "region", "schedule"],
    ) == {
        (
            f"{TEST_SITE_ID}|None|hello",
            "hello",
            "nodejs24.x",
            1024,
            "us-east-2",
            None,
        ),
        (
            f"{TEST_SITE_ID}|None|scheduled",
            "scheduled",
            "nodejs24.x",
            1024,
            "us-east-2",
            "@daily",
        ),
    }

    # Assert the public invocation URL, which is what makes a function attack surface
    assert check_nodes(neo4j_session, "NetlifyFunction", ["endpoint"]) == {
        ("https://example-site.netlify.app/.netlify/functions/hello",),
        ("https://example-site.netlify.app/.netlify/functions/scheduled",),
    }

    # Assert Relationships
    assert check_rels(
        neo4j_session,
        "NetlifySite",
        "id",
        "NetlifyFunction",
        "id",
        "HAS_FUNCTION",
    ) == {
        (TEST_SITE_ID, f"{TEST_SITE_ID}|None|hello"),
        (TEST_SITE_ID, f"{TEST_SITE_ID}|None|scheduled"),
    }

    # Assert the ontology label and its projected properties
    assert check_nodes(
        neo4j_session,
        "Function",
        ["_ont_name", "_ont_runtime", "_ont_memory", "_ont_deployment_type"],
    ) == {
        ("hello", "nodejs24.x", 1024, "code"),
        ("scheduled", "nodejs24.x", 1024, "code"),
    }


def test_get_netlify_functions_accepts_a_bare_object() -> None:
    """
    The endpoint answers with a bare object rather than a one-element array when the site has a
    single function bundle, even though the published spec declares an array.
    """
    api_session = MagicMock(spec=requests.Session)
    response = MagicMock()
    response.status_code = 200
    response.headers = {}
    response.json.return_value = tests.data.netlify.functions.NETLIFY_SITE_FUNCTIONS[0]
    api_session.get.return_value = response

    bundles = cartography.intel.netlify.functions.get_netlify_functions(
        api_session,
        TEST_BASE_URL,
        TEST_SITE_ID,
    )
    assert len(bundles) == 1
    assert len(bundles[0]["functions"]) == 2


@patch.object(
    cartography.intel.netlify.devservers,
    "get_netlify_dev_servers",
    return_value=tests.data.netlify.devservers.NETLIFY_DEV_SERVERS,
)
def test_sync_netlify_dev_servers(mock_get, neo4j_session: neo4j.Session) -> None:
    # Arrange
    _arrange(neo4j_session)
    api_session = MagicMock(spec=requests.Session)

    # Act
    cartography.intel.netlify.devservers.sync_netlify_dev_servers(
        neo4j_session,
        api_session,
        TEST_BASE_URL,
        TEST_ACCOUNT_ID,
        tests.data.netlify.sites.NETLIFY_SITES,
        TEST_UPDATE_TAG,
        common_job_parameters(),
    )

    # Assert Nodes: the public hostname is the point, it exposes an unbuilt working copy
    assert check_nodes(
        neo4j_session,
        "NetlifyDevServer",
        ["id", "state", "branch", "url"],
    ) == {
        (
            _DEV_SERVER_ID,
            "starting",
            "main",
            "https://devserver-main--example-site.netlify.app",
        ),
    }

    # Assert Relationships
    assert check_rels(
        neo4j_session,
        "NetlifySite",
        "id",
        "NetlifyDevServer",
        "id",
        "HAS_DEV_SERVER",
    ) == {(TEST_SITE_ID, _DEV_SERVER_ID)}

    # Assert the ontology label and its projected properties
    assert check_nodes(
        neo4j_session,
        "ComputeInstance",
        ["id", "_ont_name", "_ont_state", "_ont_source"],
    ) == {(_DEV_SERVER_ID, "main", "starting", "netlify")}


@patch.object(
    cartography.intel.netlify.agentrunners,
    "get_netlify_agent_runners",
    return_value=tests.data.netlify.agentrunners.NETLIFY_AGENT_RUNNERS,
)
def test_sync_netlify_agent_runners(mock_get, neo4j_session: neo4j.Session) -> None:
    # Arrange
    _arrange(neo4j_session)
    api_session = MagicMock(spec=requests.Session)

    # Act
    cartography.intel.netlify.agentrunners.sync_netlify_agent_runners(
        neo4j_session,
        api_session,
        TEST_BASE_URL,
        TEST_ACCOUNT_ID,
        tests.data.netlify.sites.NETLIFY_SITES,
        TEST_UPDATE_TAG,
        common_job_parameters(),
    )

    # Assert Nodes
    assert check_nodes(
        neo4j_session,
        "NetlifyAgentRunner",
        ["id", "state", "code_origin", "latest_session_state"],
    ) == {(_AGENT_RUNNER_ID, "running", "zip", "running")}

    # Assert Relationships: the runner is a non-human principal acting for a user
    assert check_rels(
        neo4j_session,
        "NetlifySite",
        "id",
        "NetlifyAgentRunner",
        "id",
        "HAS_AGENT_RUNNER",
    ) == {(TEST_SITE_ID, _AGENT_RUNNER_ID)}
    assert check_rels(
        neo4j_session,
        "NetlifyAgentRunner",
        "id",
        "NetlifyUser",
        "id",
        "CREATED_BY",
    ) == {(_AGENT_RUNNER_ID, TEST_USER_ID)}


def test_agent_runner_transform_drops_the_contributor_list() -> None:
    """
    `contributors` repeats the creator plus everyone who has looked at the runner, which is
    session activity rather than inventory, and Neo4j cannot store the list of objects anyway.
    """
    runners = cartography.intel.netlify.agentrunners.transform_netlify_agent_runners(
        tests.data.netlify.agentrunners.NETLIFY_AGENT_RUNNERS,
    )
    assert "contributors" not in runners[0]
    assert "user" not in runners[0]
    assert runners[0]["user_id"] == TEST_USER_ID
