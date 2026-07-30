"""Regressions for the defects found in review of PR #3089.

Each test here fails on the pre-fix code, so they are the guarantee those bugs do not come
back rather than general coverage.
"""

import asyncio
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import cartography.intel.modal.domains
import cartography.intel.modal.functions
import cartography.intel.modal.members
import cartography.intel.modal.secrets
import cartography.intel.modal.workloads
import cartography.intel.modal.workspace
import tests.data.modal.compute as compute_fx
import tests.data.modal.storage as storage_fx
from tests.integration.cartography.intel.modal.test_compute import _params
from tests.integration.cartography.intel.modal.test_compute import _seed_tenancy
from tests.integration.cartography.intel.modal.test_compute import _sync_apps
from tests.integration.cartography.intel.modal.test_compute import _sync_functions
from tests.integration.cartography.intel.modal.test_identity import (
    _ensure_local_neo4j_has_test_members,
)
from tests.integration.cartography.intel.modal.test_workspace import TEST_UPDATE_TAG
from tests.integration.cartography.intel.modal.test_workspace import TEST_WORKSPACE_ID
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

SECOND_WORKSPACE_ID = "ac-2ndWorkspaceXXXXXXXXXX"


def test_unavailable_domain_api_does_not_delete_existing_domains(neo4j_session):
    """A workspace that cannot answer DomainList told us nothing about its domains, which is
    not the same as telling us it has none. Cleanup must be skipped so existing data survives.
    """
    # Arrange: a first sync while the API is available.
    _seed_tenancy(neo4j_session)
    with patch.object(
        cartography.intel.modal.domains,
        "list_domains",
        return_value=(storage_fx.MODAL_DOMAINS, True),
    ):
        asyncio.run(
            cartography.intel.modal.domains.sync(
                neo4j_session,
                MagicMock(),
                {"UPDATE_TAG": TEST_UPDATE_TAG, "WORKSPACE_ID": TEST_WORKSPACE_ID},
            )
        )
    assert len(check_nodes(neo4j_session, "ModalDomain", ["id"])) == 2

    # Act: the add-on is gone, so the adapter reports "not available" with an empty list.
    with patch.object(
        cartography.intel.modal.domains, "list_domains", return_value=([], False)
    ):
        asyncio.run(
            cartography.intel.modal.domains.sync(
                neo4j_session,
                MagicMock(),
                {"UPDATE_TAG": TEST_UPDATE_TAG + 1, "WORKSPACE_ID": TEST_WORKSPACE_ID},
            )
        )

    # Assert: nothing was deleted.
    assert len(check_nodes(neo4j_session, "ModalDomain", ["id"])) == 2
    assert len(check_nodes(neo4j_session, "ModalDomainDNSRecord", ["id"])) == 2


def test_class_lookup_is_scoped_per_app(neo4j_session):
    """Two apps may each define a class of the same name. A method must bind to its own app's
    class, never to the other app's."""
    # Arrange: both apps define a class named "Worker", each with its own method.
    _seed_tenancy(neo4j_session)
    apps = _sync_apps(neo4j_session)
    other_app = compute_fx.TEST_STOPPED_APP_ID
    other_class_id = "cs-OtherAppWorkerXXXXXX"
    layouts = {
        compute_fx.TEST_APP_ID: {
            "functions": [
                {
                    "id": "fu-AppOneWorkerServiceXX",
                    "name": "Worker.*",
                    "app_id": compute_fx.TEST_APP_ID,
                    "web_url": None,
                    "is_web_endpoint": False,
                    "function_type": "FUNCTION_TYPE_FUNCTION",
                    "is_method": False,
                    "definition_id": None,
                    "input_plane_url": None,
                    "input_plane_region": None,
                },
            ],
            "classes": [
                {
                    "id": compute_fx.TEST_CLASS_ID,
                    "name": "Worker",
                    "app_id": compute_fx.TEST_APP_ID,
                },
            ],
        },
        other_app: {
            "functions": [
                {
                    "id": "fu-AppTwoWorkerServiceXX",
                    "name": "Worker.*",
                    "app_id": other_app,
                    "web_url": None,
                    "is_web_endpoint": False,
                    "function_type": "FUNCTION_TYPE_FUNCTION",
                    "is_method": False,
                    "definition_id": None,
                    "input_plane_url": None,
                    "input_plane_region": None,
                },
            ],
            "classes": [
                {"id": other_class_id, "name": "Worker", "app_id": other_app},
            ],
        },
    }

    # Act
    _sync_functions(neo4j_session, apps, layouts=layouts)

    # Assert: each function binds to the class of its own app.
    assert check_rels(
        neo4j_session, "ModalClass", "id", "ModalFunction", "id", "HAS_METHOD"
    ) == {
        (compute_fx.TEST_CLASS_ID, "fu-AppOneWorkerServiceXX"),
        (other_class_id, "fu-AppTwoWorkerServiceXX"),
    }


def test_created_by_does_not_cross_workspaces(neo4j_session):
    """Modal reports creators as workspace usernames, which are not globally unique. A secret
    must only attribute creation to a member of its own workspace."""
    # Arrange: two workspaces, each with a member whose display_name is "alice".
    _seed_tenancy(neo4j_session)
    _ensure_local_neo4j_has_test_members(neo4j_session)
    cartography.intel.modal.workspace.load_workspace(
        neo4j_session,
        [{"id": SECOND_WORKSPACE_ID, "name": "other-workspace"}],
        TEST_UPDATE_TAG,
    )
    cartography.intel.modal.members.load_members(
        neo4j_session,
        [
            {
                "id": "us-OtherWorkspaceAliceXX",
                "email": "alice@other.example.com",
                "display_name": "alice",
            },
        ],
        SECOND_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )
    # Project the id too: check_nodes returns a set, so two members both named "alice" would
    # otherwise collapse into one entry and hide the very collision under test.
    assert check_nodes(
        neo4j_session, "ModalWorkspaceMember", ["id", "display_name"]
    ) == {
        ("us-ydIZVCWluEtzFTbpJvjHcK", "alice"),
        ("us-2QpLmNrTvBxWsZdKfGhYjA", "bob"),
        ("us-OtherWorkspaceAliceXX", "alice"),
    }

    # Act: ingest a secret created by "alice" in the first workspace.
    with patch.object(
        cartography.intel.modal.secrets,
        "list_secrets",
        return_value=[storage_fx.MODAL_SECRETS[0]],
    ):
        asyncio.run(
            cartography.intel.modal.secrets.sync(neo4j_session, MagicMock(), _params())
        )

    # Assert: exactly one edge, to the alice of the synced workspace.
    assert check_rels(
        neo4j_session,
        "ModalSecret",
        "name",
        "ModalWorkspaceMember",
        "id",
        "CREATED_BY",
    ) == {("e2e-secret", "us-ydIZVCWluEtzFTbpJvjHcK")}


def test_non_modal_error_is_not_laundered_into_partial_success(neo4j_session):
    """A programming error inside the per-app loop must propagate, not be downgraded to
    'partial enumeration' which silently preserves stale data."""
    # Arrange
    _seed_tenancy(neo4j_session)
    apps = _sync_apps(neo4j_session)

    async def boom(_client, _env, _app_id):
        raise KeyError("a bug in our own transform, not a Modal failure")

    # Act and assert
    with (
        patch.object(
            cartography.intel.modal.workloads, "list_clusters", return_value=[]
        ),
        patch.object(cartography.intel.modal.workloads, "list_tasks", side_effect=boom),
    ):
        with pytest.raises(KeyError):
            asyncio.run(
                cartography.intel.modal.workloads.sync(
                    neo4j_session, MagicMock(), _params(), apps
                )
            )
