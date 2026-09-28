"""
Integration tests for the Netlify configuration and supply-chain resources: environment
variables, build hooks, notification hooks, deploy keys, snippets and add-on instances.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import neo4j
import requests

import cartography.intel.netlify.buildhooks
import cartography.intel.netlify.deploykeys
import cartography.intel.netlify.envvars
import cartography.intel.netlify.hooks
import cartography.intel.netlify.serviceinstances
import cartography.intel.netlify.sites
import cartography.intel.netlify.snippets
import cartography.intel.netlify.users
import tests.data.netlify.buildhooks
import tests.data.netlify.deploykeys
import tests.data.netlify.envvars
import tests.data.netlify.misc
import tests.data.netlify.sites
import tests.data.netlify.snippets
import tests.data.netlify.users
from cartography.intel.netlify.util import NetlifyPlanGatedError
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

_BUILD_HOOK_ID = "6b6b799edf0b30fd62d38f02"
_DEPLOY_KEY_ID = "6b6b79a3aab81353de5d314f"
_SITES = tests.data.netlify.sites.NETLIFY_SITES


def _arrange(neo4j_session: neo4j.Session) -> None:
    create_test_netlify_account(neo4j_session)
    create_test_netlify_users(neo4j_session)
    cartography.intel.netlify.sites.load_netlify_sites(
        neo4j_session,
        cartography.intel.netlify.sites.transform_netlify_sites(_SITES),
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.netlify.envvars,
    "get_netlify_env_vars",
    side_effect=[
        # First call is the team-wide pass, which is empty on a Free team; the second is the
        # site-scoped one.
        [],
        tests.data.netlify.envvars.NETLIFY_SITE_ENV_VARS,
    ],
)
def test_sync_netlify_env_vars(mock_get, neo4j_session: neo4j.Session) -> None:
    # Arrange
    _arrange(neo4j_session)
    api_session = MagicMock(spec=requests.Session)

    # Act
    cartography.intel.netlify.envvars.sync_netlify_env_vars(
        neo4j_session,
        api_session,
        TEST_BASE_URL,
        TEST_ACCOUNT_ID,
        _SITES,
        TEST_UPDATE_TAG,
        common_job_parameters(),
    )

    # Assert Nodes
    public_id = f"{TEST_ACCOUNT_ID}|{TEST_SITE_ID}|CARTO_PUBLIC"
    secret_id = f"{TEST_ACCOUNT_ID}|{TEST_SITE_ID}|CARTO_SECRET"
    assert check_nodes(
        neo4j_session,
        "NetlifyEnvVar",
        ["id", "key", "scope", "is_secret"],
    ) == {
        (public_id, "CARTO_PUBLIC", "site", False),
        (secret_id, "CARTO_SECRET", "site", True),
    }

    # Assert the conditional ontology label lands only on the variables Netlify marks secret
    assert check_nodes(neo4j_session, "Secret", ["id", "_ont_name", "_ont_source"]) == {
        (secret_id, "CARTO_SECRET", "netlify"),
    }

    # Assert Relationships
    assert check_rels(
        neo4j_session,
        "NetlifySite",
        "id",
        "NetlifyEnvVar",
        "id",
        "HAS_ENV_VAR",
    ) == {(TEST_SITE_ID, public_id), (TEST_SITE_ID, secret_id)}
    assert check_rels(
        neo4j_session,
        "NetlifyEnvVar",
        "id",
        "NetlifyUser",
        "id",
        "UPDATED_BY",
    ) == {(public_id, TEST_USER_ID), (secret_id, TEST_USER_ID)}

    # No value, secret or not, may reach the graph. Netlify returns a non-secret value in full,
    # and masks a secret one down to its last four characters, which is still a leak.
    assert find_secret_in_graph(neo4j_session, "hello") == []
    assert find_secret_in_graph(neo4j_session, "cr3t") == []


def test_plan_gated_team_wide_env_vars_skip_cleanup(
    neo4j_session: neo4j.Session,
) -> None:
    """
    Team-wide variables are a paid feature. If that call 403s, the ingested set is no longer
    exhaustive for the shared cleanup scope, so the deletion pass has to be held back: a team that
    dropped from a paid plan to Free would otherwise lose its previously ingested shared variables.
    """
    # Arrange: a shared variable from an earlier run, when the plan still allowed them
    _arrange(neo4j_session)
    shared_id = f"{TEST_ACCOUNT_ID}|_account|LEGACY_SHARED"
    cartography.intel.netlify.envvars.load_netlify_env_vars(
        neo4j_session,
        [
            {
                "id": shared_id,
                "key": "LEGACY_SHARED",
                "site_id": None,
                "scope": "account",
                "is_secret": False,
                "is_secret_flag": "false",
            },
        ],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG - 1,
    )
    # `or set()` only satisfies check_nodes' Optional return type. Membership rather than full
    # set equality because neo4j_session is module-scoped and other tests here leave env vars.
    assert (shared_id,) in (
        check_nodes(neo4j_session, "NetlifyEnvVar", ["id"]) or set()
    )

    # Act: the team-wide call is now plan-gated, the site-scoped one still works
    with patch.object(
        cartography.intel.netlify.envvars,
        "get_netlify_env_vars",
        side_effect=[
            NetlifyPlanGatedError("403"),
            tests.data.netlify.envvars.NETLIFY_SITE_ENV_VARS,
        ],
    ):
        cartography.intel.netlify.envvars.sync_netlify_env_vars(
            neo4j_session,
            MagicMock(spec=requests.Session),
            TEST_BASE_URL,
            TEST_ACCOUNT_ID,
            _SITES,
            TEST_UPDATE_TAG,
            common_job_parameters(),
        )

    # Assert: the stale shared variable survived, and the site variables were still ingested
    ids = check_nodes(neo4j_session, "NetlifyEnvVar", ["id"]) or set()
    assert (shared_id,) in ids
    assert (f"{TEST_ACCOUNT_ID}|{TEST_SITE_ID}|CARTO_SECRET",) in ids


def test_env_var_transform_separates_the_two_scopes() -> None:
    """
    A team-wide FOO and a site-scoped FOO are different variables with different values, so they
    must not collapse onto one node.
    """
    transformed = cartography.intel.netlify.envvars.transform_netlify_env_vars(
        [
            (None, {"key": "FOO", "is_secret": False, "values": []}),
            (TEST_SITE_ID, {"key": "FOO", "is_secret": False, "values": []}),
        ],
        TEST_ACCOUNT_ID,
    )
    assert [v["id"] for v in transformed] == [
        f"{TEST_ACCOUNT_ID}|_account|FOO",
        f"{TEST_ACCOUNT_ID}|{TEST_SITE_ID}|FOO",
    ]
    assert [v["scope"] for v in transformed] == ["account", "site"]


@patch.object(
    cartography.intel.netlify.buildhooks,
    "get_netlify_build_hooks",
    return_value=tests.data.netlify.buildhooks.NETLIFY_BUILD_HOOKS,
)
def test_sync_netlify_build_hooks(mock_get, neo4j_session: neo4j.Session) -> None:
    # Arrange
    _arrange(neo4j_session)
    api_session = MagicMock(spec=requests.Session)

    # Act
    cartography.intel.netlify.buildhooks.sync_netlify_build_hooks(
        neo4j_session,
        api_session,
        TEST_BASE_URL,
        TEST_ACCOUNT_ID,
        _SITES,
        TEST_UPDATE_TAG,
        common_job_parameters(),
    )

    # Assert Nodes
    assert check_nodes(neo4j_session, "NetlifyBuildHook", ["id", "draft"]) == {
        (_BUILD_HOOK_ID, False),
    }

    # Assert Relationships
    assert check_rels(
        neo4j_session,
        "NetlifySite",
        "id",
        "NetlifyBuildHook",
        "id",
        "HAS_BUILD_HOOK",
    ) == {(TEST_SITE_ID, _BUILD_HOOK_ID)}

    # The trigger URL deploys the site to anyone holding it, and `msg` repeats it in prose.
    assert find_secret_in_graph(neo4j_session, "api.netlify.com/build_hooks") == []


@patch.object(
    cartography.intel.netlify.hooks,
    "get_netlify_hooks",
    return_value=tests.data.netlify.misc.NETLIFY_HOOKS,
)
def test_sync_netlify_hooks(mock_get, neo4j_session: neo4j.Session) -> None:
    # Arrange
    _arrange(neo4j_session)
    api_session = MagicMock(spec=requests.Session)

    # Act
    cartography.intel.netlify.hooks.sync_netlify_hooks(
        neo4j_session,
        api_session,
        TEST_BASE_URL,
        TEST_ACCOUNT_ID,
        _SITES,
        TEST_UPDATE_TAG,
        common_job_parameters(),
    )

    # Assert Nodes
    assert check_nodes(
        neo4j_session,
        "NetlifyHook",
        ["id", "type", "event", "disabled"],
    ) == {
        ("9e9e7d7053c60b4be4c87201", "slack", "deploy_created", False),
        ("9e9e7d7053c60b4be4c87202", "url", "deploy_failed", True),
    }

    # Assert Relationships
    assert check_rels(
        neo4j_session,
        "NetlifySite",
        "id",
        "NetlifyHook",
        "id",
        "HAS_NOTIFICATION_HOOK",
    ) == {
        (TEST_SITE_ID, "9e9e7d7053c60b4be4c87201"),
        (TEST_SITE_ID, "9e9e7d7053c60b4be4c87202"),
    }

    # `data` holds the Slack incoming-webhook URL and the target webhook's token
    assert find_secret_in_graph(neo4j_session, "hooks.slack.com") == []
    assert find_secret_in_graph(neo4j_session, "webhook.example.com") == []


@patch.object(
    cartography.intel.netlify.deploykeys,
    "get_netlify_deploy_keys",
    return_value=tests.data.netlify.deploykeys.NETLIFY_DEPLOY_KEYS,
)
def test_sync_netlify_deploy_keys(mock_get, neo4j_session: neo4j.Session) -> None:
    # Arrange
    _arrange(neo4j_session)
    api_session = MagicMock(spec=requests.Session)

    # Act
    cartography.intel.netlify.deploykeys.sync_netlify_deploy_keys(
        neo4j_session,
        api_session,
        TEST_BASE_URL,
        TEST_ACCOUNT_ID,
        tests.data.netlify.sites.NETLIFY_SITES_WITH_GIT,
        TEST_UPDATE_TAG,
        common_job_parameters(),
    )

    # Assert Nodes: only the public half of the keypair is ever returned by the API
    assert check_nodes(neo4j_session, "NetlifyDeployKey", ["id"]) == {
        (_DEPLOY_KEY_ID,),
    }
    assert (
        neo4j_session.run(
            "MATCH (k:NetlifyDeployKey) RETURN k.public_key AS key",
        )
        .single()["key"]
        .startswith("ssh-rsa ")
    )

    # Assert Relationships
    assert check_rels(
        neo4j_session,
        "NetlifyAccount",
        "id",
        "NetlifyDeployKey",
        "id",
        "RESOURCE",
    ) == {(TEST_ACCOUNT_ID, _DEPLOY_KEY_ID)}


@patch.object(
    cartography.intel.netlify.snippets,
    "get_netlify_snippets",
    return_value=tests.data.netlify.snippets.NETLIFY_SNIPPETS,
)
def test_sync_netlify_snippets(mock_get, neo4j_session: neo4j.Session) -> None:
    # Arrange
    _arrange(neo4j_session)
    api_session = MagicMock(spec=requests.Session)

    # Act
    cartography.intel.netlify.snippets.sync_netlify_snippets(
        neo4j_session,
        api_session,
        TEST_BASE_URL,
        TEST_ACCOUNT_ID,
        _SITES,
        TEST_UPDATE_TAG,
        common_job_parameters(),
    )

    # Assert Nodes: Netlify's snippet id is a positional index, so it has to be site-scoped or
    # snippet 0 of every site collapses onto one node.
    assert check_nodes(
        neo4j_session,
        "NetlifySnippet",
        ["id", "snippet_index", "general_position"],
    ) == {
        (f"{TEST_SITE_ID}|0", "0", "footer"),
        (f"{TEST_SITE_ID}|1", "1", "footer"),
    }

    # Assert Relationships
    assert check_rels(
        neo4j_session,
        "NetlifySite",
        "id",
        "NetlifySnippet",
        "id",
        "HAS_SNIPPET",
    ) == {
        (TEST_SITE_ID, f"{TEST_SITE_ID}|0"),
        (TEST_SITE_ID, f"{TEST_SITE_ID}|1"),
    }


@patch.object(
    cartography.intel.netlify.serviceinstances,
    "get_netlify_service_instances",
    return_value=tests.data.netlify.misc.NETLIFY_SERVICE_INSTANCES,
)
def test_sync_netlify_service_instances(
    mock_get,
    neo4j_session: neo4j.Session,
) -> None:
    # Arrange
    _arrange(neo4j_session)
    api_session = MagicMock(spec=requests.Session)

    # Act
    cartography.intel.netlify.serviceinstances.sync_netlify_service_instances(
        neo4j_session,
        api_session,
        TEST_BASE_URL,
        TEST_ACCOUNT_ID,
        _SITES,
        TEST_UPDATE_TAG,
        common_job_parameters(),
    )

    # Assert Nodes
    assert check_nodes(
        neo4j_session,
        "NetlifyServiceInstance",
        ["id", "service_slug", "service_name"],
    ) == {("b0b07d7053c60b4be4c87401", "example-analytics", "Example Analytics")}

    # Assert Relationships
    assert check_rels(
        neo4j_session,
        "NetlifySite",
        "id",
        "NetlifyServiceInstance",
        "id",
        "HAS_SERVICE_INSTANCE",
    ) == {(TEST_SITE_ID, "b0b07d7053c60b4be4c87401")}

    # Assert the ontology label and its projected properties
    assert check_nodes(
        neo4j_session,
        "ThirdPartyApp",
        ["_ont_client_id", "_ont_name", "_ont_enabled", "_ont_source"],
    ) == {("example-analytics", "Example Analytics", True, "netlify")}

    # `config`, `env` and `auth_url` all carry credentials the add-on provisioned
    assert find_secret_in_graph(neo4j_session, "addon-live-key-abcdef") == []
    assert find_secret_in_graph(neo4j_session, "addon-live-token-123456") == []
    assert find_secret_in_graph(neo4j_session, "eyJhbGciOiJIUzI1NiJ9") == []


def test_deploy_keys_are_limited_to_keys_this_teams_sites_reference(
    neo4j_session: neo4j.Session,
) -> None:
    """
    `GET /deploy_keys` has no team filter, so it returns every key the token can see. Attributing
    all of them to the team being synced would give a multi-team token a RESOURCE edge from every
    team to every key. A site's `build_settings.deploy_key_id` is the only ownership statement the
    API makes, so it decides what is ingested.
    """
    # Arrange: the token sees two keys, but only one is referenced by a site in this team
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    create_test_netlify_account(neo4j_session)
    other_teams_key = {
        "id": "ffff7d7053c60b4be4c87999",
        "public_key": "ssh-rsa AAAAOTHERTEAMKEY",
        "created_at": "2026-07-30T16:19:47.183Z",
    }
    keys = tests.data.netlify.deploykeys.NETLIFY_DEPLOY_KEYS + [other_teams_key]
    sites = tests.data.netlify.sites.NETLIFY_SITES_WITH_GIT

    # Act
    with patch.object(
        cartography.intel.netlify.deploykeys,
        "get_netlify_deploy_keys",
        return_value=keys,
    ):
        cartography.intel.netlify.deploykeys.sync_netlify_deploy_keys(
            neo4j_session,
            MagicMock(spec=requests.Session),
            TEST_BASE_URL,
            TEST_ACCOUNT_ID,
            sites,
            TEST_UPDATE_TAG,
            common_job_parameters(),
        )

    # Assert: only the referenced key is in the graph
    assert check_nodes(neo4j_session, "NetlifyDeployKey", ["id"]) == {(_DEPLOY_KEY_ID,)}
    assert check_rels(
        neo4j_session,
        "NetlifyAccount",
        "id",
        "NetlifyDeployKey",
        "id",
        "RESOURCE",
    ) == {(TEST_ACCOUNT_ID, _DEPLOY_KEY_ID)}
