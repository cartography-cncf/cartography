"""Deleting an environment must not leave its RBAC behind.

ModalEnvironmentRole cleanup is scoped through (:ModalEnvironment)-[:RESOURCE]->, and the
entry point only iterates environments that are still listed. So an environment removed in
Modal gets its node deleted while its role nodes and HAS_ROLE bindings would survive as
orphans that still read as live permissions.
"""

import asyncio
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.modal.environment_roles
import cartography.intel.modal.environments
import tests.data.modal.environments
import tests.data.modal.identity
from tests.integration.cartography.intel.modal.test_identity import (
    _ensure_local_neo4j_has_test_members,
)
from tests.integration.cartography.intel.modal.test_workspace import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.cartography.intel.modal.test_workspace import TEST_UPDATE_TAG
from tests.integration.cartography.intel.modal.test_workspace import TEST_WORKSPACE_ID
from tests.integration.util import check_nodes

MAIN_ENV_ID = "en-C3umado26sLFrhYfZjoWjL"
PROD_ENV_ID = "en-9ZKpQr4tVbNmXsLdEfGhJk"


def _sync_environments(neo4j_session, listing, update_tag):
    with patch.object(
        cartography.intel.modal.environments,
        "list_environments",
        return_value=listing,
    ):
        asyncio.run(
            cartography.intel.modal.environments.sync(
                neo4j_session,
                MagicMock(),
                {"UPDATE_TAG": update_tag, "WORKSPACE_ID": TEST_WORKSPACE_ID},
            )
        )


def _sync_roles(neo4j_session, environment_id, update_tag):
    with patch.object(
        cartography.intel.modal.environment_roles,
        "get_environment_roles",
        return_value=tests.data.modal.identity.MODAL_ENVIRONMENT_ROLE_PRINCIPALS,
    ):
        asyncio.run(
            cartography.intel.modal.environment_roles.sync(
                neo4j_session,
                MagicMock(),
                {
                    "UPDATE_TAG": update_tag,
                    "WORKSPACE_ID": TEST_WORKSPACE_ID,
                    "ENVIRONMENT_ID": environment_id,
                },
            )
        )


def _has_role_bindings(neo4j_session):
    result = neo4j_session.run(
        """
        MATCH (p)-[:HAS_ROLE]->(r:ModalEnvironmentRole)
        RETURN r.id AS role_id, count(*) AS c
        """
    )
    return {record["role_id"] for record in result}


def test_removed_environment_does_not_orphan_its_rbac(neo4j_session):
    # Arrange: two environments, both with roles and bindings ingested.
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _ensure_local_neo4j_has_test_members(neo4j_session)
    _sync_environments(
        neo4j_session,
        tests.data.modal.environments.MODAL_ENVIRONMENTS,
        TEST_UPDATE_TAG,
    )
    _sync_roles(neo4j_session, MAIN_ENV_ID, TEST_UPDATE_TAG)
    _sync_roles(neo4j_session, PROD_ENV_ID, TEST_UPDATE_TAG)

    assert check_nodes(neo4j_session, "ModalEnvironment", ["id"]) == {
        (MAIN_ENV_ID,),
        (PROD_ENV_ID,),
    }
    # 3 builtin roles per environment.
    assert len(check_nodes(neo4j_session, "ModalEnvironmentRole", ["id"])) == 6
    assert any(rid.startswith(PROD_ENV_ID) for rid in _has_role_bindings(neo4j_session))

    # Act: 'prod' is deleted in Modal, so the next sync no longer lists it. The entry point
    # only fans out over listed environments, so prod's roles are never re-synced.
    _sync_environments(
        neo4j_session,
        [tests.data.modal.environments.MODAL_ENVIRONMENTS[0]],
        TEST_UPDATE_TAG + 1,
    )

    # Assert
    assert check_nodes(neo4j_session, "ModalEnvironment", ["id"]) == {(MAIN_ENV_ID,)}

    remaining_roles = {
        rid for (rid,) in check_nodes(neo4j_session, "ModalEnvironmentRole", ["id"])
    }
    orphaned = {rid for rid in remaining_roles if rid.startswith(PROD_ENV_ID)}
    assert (
        not orphaned
    ), f"roles of the deleted environment survived as orphans: {sorted(orphaned)}"

    orphan_bindings = {
        rid for rid in _has_role_bindings(neo4j_session) if rid.startswith(PROD_ENV_ID)
    }
    assert not orphan_bindings, (
        f"HAS_ROLE bindings to the deleted environment's roles survived: "
        f"{sorted(orphan_bindings)}"
    )

    # The surviving environment keeps its own RBAC untouched.
    assert {rid for rid in remaining_roles if rid.startswith(MAIN_ENV_ID)} == {
        f"{MAIN_ENV_ID}/contributor",
        f"{MAIN_ENV_ID}/no-access",
        f"{MAIN_ENV_ID}/viewer",
    }
