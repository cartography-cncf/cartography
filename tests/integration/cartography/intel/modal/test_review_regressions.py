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
import tests.data.modal.identity
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


def _memberships_of(neo4j_session, *user_ids):
    """MEMBER_OF edges of specific users.

    The neo4j_session fixture is module-scoped, so the graph carries data from earlier tests in
    this file; assertions must scope to the ids they seeded rather than to the whole graph.
    """
    return {
        (r["user_id"], r["workspace_id"])
        for r in neo4j_session.run(
            """
            MATCH (u:ModalUser)-[:MEMBER_OF]->(w:ModalWorkspace)
            WHERE u.id IN $ids
            RETURN u.id AS user_id, w.id AS workspace_id
            """,
            ids=list(user_ids),
        )
    }


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
    must only attribute creation to a member of its own workspace.

    The username is resolved to a user id against the synced workspace's members, so the other
    workspace's identically-named user cannot attract the edge.
    """
    # Arrange: two workspaces, each with a member whose display_name is "alice".
    _seed_tenancy(neo4j_session)
    usernames = _ensure_local_neo4j_has_test_members(neo4j_session)
    cartography.intel.modal.workspace.load_workspace(
        neo4j_session,
        [{"id": SECOND_WORKSPACE_ID, "name": "other-workspace"}],
        TEST_UPDATE_TAG,
    )
    # A second workspace with its own "alice", a different person with a different user id.
    _ensure_local_neo4j_has_test_members(
        neo4j_session,
        workspace_id=SECOND_WORKSPACE_ID,
        raw=[
            {
                "id": "us-OtherWorkspaceAliceXX",
                "email": "alice@other.example.com",
                "display_name": "alice",
                "member_role": "MEMBER_ROLE_USER",
            },
        ],
    )
    # Project the id too: check_nodes returns a set, so two members both named "alice" would
    # otherwise collapse into one entry and hide the very collision under test.
    assert check_nodes(neo4j_session, "ModalUser", ["id", "display_name"]) == {
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
            cartography.intel.modal.secrets.sync(
                neo4j_session, MagicMock(), _params(), usernames
            )
        )

    # Assert: exactly one edge, to the alice of the synced workspace.
    assert check_rels(
        neo4j_session,
        "ModalSecret",
        "name",
        "ModalUser",
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


def test_leaving_one_workspace_does_not_destroy_the_other_membership(neo4j_session):
    """A shared identity must survive one workspace's cleanup.

    ModalUser used to carry a sub_resource_relationship to the workspace, so the generated
    cleanup DETACH DELETEd any user not seen in the workspace being synced. A person who left
    workspace A but stayed in workspace B was therefore deleted by A's sync, taking B's
    membership with them.
    """
    # Arrange: alice belongs to both workspaces, bob only to the first.
    _seed_tenancy(neo4j_session)
    shared = {
        "id": "us-SharedAliceXXXXXXXXXX",
        "email": "shared@example.com",
        "display_name": "shared-user",
        "member_role": "MEMBER_ROLE_OWNER",
    }
    only_first = {
        "id": "us-BobOnlyInFirstXXXXXXX",
        "email": "onlyfirst@example.com",
        "display_name": "only-first-user",
        "member_role": "MEMBER_ROLE_USER",
    }
    cartography.intel.modal.workspace.load_workspace(
        neo4j_session,
        [{"id": SECOND_WORKSPACE_ID, "name": "other-workspace"}],
        TEST_UPDATE_TAG,
    )
    _ensure_local_neo4j_has_test_members(
        neo4j_session, workspace_id=TEST_WORKSPACE_ID, raw=[shared, only_first]
    )
    _ensure_local_neo4j_has_test_members(
        neo4j_session, workspace_id=SECOND_WORKSPACE_ID, raw=[shared]
    )
    assert _memberships_of(neo4j_session, shared["id"], only_first["id"]) == {
        ("us-SharedAliceXXXXXXXXXX", TEST_WORKSPACE_ID),
        ("us-BobOnlyInFirstXXXXXXX", TEST_WORKSPACE_ID),
        ("us-SharedAliceXXXXXXXXXX", SECOND_WORKSPACE_ID),
    }

    # Act: the shared user leaves the first workspace, which re-syncs without them.
    with patch.object(
        cartography.intel.modal.members,
        "list_workspace_members",
        return_value=[only_first],
    ):
        asyncio.run(
            cartography.intel.modal.members.sync(
                neo4j_session,
                MagicMock(),
                {
                    "UPDATE_TAG": TEST_UPDATE_TAG + 1,
                    "WORKSPACE_ID": TEST_WORKSPACE_ID,
                },
            )
        )

    # Assert: the first workspace's membership is gone, the second is untouched, and the
    # shared identity node survives.
    assert _memberships_of(neo4j_session, shared["id"], only_first["id"]) == {
        ("us-BobOnlyInFirstXXXXXXX", TEST_WORKSPACE_ID),
        ("us-SharedAliceXXXXXXXXXX", SECOND_WORKSPACE_ID),
    }
    assert ("us-SharedAliceXXXXXXXXXX",) in check_nodes(
        neo4j_session, "ModalUser", ["id"]
    )


def test_membership_data_rides_on_the_relationship(neo4j_session):
    """Role, join date and removal date are per-workspace, so they belong on MEMBER_OF.

    member_role is deliberately duplicated: as a rel property here, and as the HAS_ROLE edge to
    a ModalWorkspaceRole node that the cross-provider rules consume.
    """
    # Arrange
    _seed_tenancy(neo4j_session)

    # Act
    _ensure_local_neo4j_has_test_members(neo4j_session)

    # Assert
    fixture_ids = [m["id"] for m in tests.data.modal.identity.MODAL_WORKSPACE_MEMBERS]
    rows = {
        (r["user"], r["role"], r["member_id"], r["joined"] is not None)
        for r in neo4j_session.run(
            """
            MATCH (u:ModalUser)-[r:MEMBER_OF]->(:ModalWorkspace)
            WHERE u.id IN $ids
            RETURN u.display_name AS user, r.member_role AS role,
                   r.member_id AS member_id, r.joined_at AS joined
            """,
            ids=fixture_ids,
        )
    }
    assert rows == {
        ("alice", "MEMBER_ROLE_OWNER", "me-u92j7zUIW7uLzofhHdpIbZ", True),
        ("bob", "MEMBER_ROLE_USER", "me-4RtYuIoPaSdFgHjKlZxCvB", True),
    }
    # And none of it leaked onto the shared identity node.
    keys = set()
    for record in neo4j_session.run(
        "MATCH (u:ModalUser) WHERE u.id IN $ids RETURN keys(u) AS ks", ids=fixture_ids
    ):
        keys.update(record["ks"])
    assert not keys & {"member_role", "member_id", "joined_at", "deleted_at"}
