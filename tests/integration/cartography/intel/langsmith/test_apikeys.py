from unittest.mock import patch

import cartography.intel.langsmith.apikeys
import tests.data.langsmith.apikeys
from tests.data.langsmith.organizations import LANGSMITH_ORG_ID
from tests.data.langsmith.roles import CUSTOM_ROLE_ID
from tests.data.langsmith.roles import ORG_ADMIN_ROLE_ID
from tests.data.langsmith.users import BART_LS_USER_ID
from tests.data.langsmith.users import MARGE_LS_USER_ID
from tests.data.langsmith.workspaces import LANGSMITH_WORKSPACES
from tests.data.langsmith.workspaces import WORKSPACE_PROD_ID
from tests.integration.cartography.intel.langsmith.test_roles import (
    _ensure_local_neo4j_has_test_roles,
)
from tests.integration.cartography.intel.langsmith.test_users import (
    _ensure_local_neo4j_has_test_users,
)
from tests.integration.cartography.intel.langsmith.test_workspaces import (
    _ensure_local_neo4j_has_test_workspaces,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789

_BY_TYPE = {
    "service_key": tests.data.langsmith.apikeys.LANGSMITH_SERVICE_KEYS,
    "pat": tests.data.langsmith.apikeys.LANGSMITH_PATS,
    "scim_token": tests.data.langsmith.apikeys.LANGSMITH_SCIM_TOKENS,
}


def _mock_fetch_optional(client, org_id, key_type):
    rows = [dict(row) for row in _BY_TYPE[key_type]]
    for row in rows:
        row["key_type"] = key_type
    return rows


def _mock_fetch_workspace_keys(client, org_id, workspace_id):
    return []


@patch.object(
    cartography.intel.langsmith.apikeys,
    "_fetch_workspace_keys",
    side_effect=_mock_fetch_workspace_keys,
)
@patch.object(
    cartography.intel.langsmith.apikeys,
    "_fetch_optional",
    side_effect=_mock_fetch_optional,
)
@patch.object(
    cartography.intel.langsmith.apikeys,
    "get_service_accounts",
    return_value=tests.data.langsmith.apikeys.LANGSMITH_SERVICE_ACCOUNTS,
)
def test_sync_langsmith_apikeys(
    mock_accounts, mock_optional, mock_ws_keys, neo4j_session
):
    _ensure_local_neo4j_has_test_roles(neo4j_session)
    _ensure_local_neo4j_has_test_workspaces(neo4j_session)
    users = _ensure_local_neo4j_has_test_users(neo4j_session)

    cartography.intel.langsmith.apikeys.sync(
        neo4j_session,
        None,
        LANGSMITH_ORG_ID,
        users,
        LANGSMITH_WORKSPACES,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": LANGSMITH_ORG_ID},
    )

    # Only the non-secret short prefix is stored, and SCIM tokens report theirs under a
    # different field name.
    assert check_nodes(
        neo4j_session, "LangSmithApiKey", ["short_key", "key_type", "revoked_at"]
    ) == {
        ("lsv2_sk_abcd", "service_key", None),
        ("lsv2_pt_wxyz", "pat", None),
        ("lsv2_sc_1234", "scim_token", None),
    }

    assert check_nodes(neo4j_session, "LangSmithServiceAccount", ["id", "name"]) == {
        ("5a5a5a5a-0001-4001-8001-5a5a5a5a5a5a", "ci-deployer")
    }

    assert check_rels(
        neo4j_session,
        "LangSmithServiceAccount",
        "name",
        "LangSmithWorkspace",
        "id",
        "DEFAULT_WORKSPACE",
        rel_direction_right=True,
    ) == {("ci-deployer", WORKSPACE_PROD_ID)}


@patch.object(
    cartography.intel.langsmith.apikeys,
    "_fetch_workspace_keys",
    side_effect=_mock_fetch_workspace_keys,
)
@patch.object(
    cartography.intel.langsmith.apikeys,
    "_fetch_optional",
    side_effect=_mock_fetch_optional,
)
@patch.object(
    cartography.intel.langsmith.apikeys,
    "get_service_accounts",
    return_value=tests.data.langsmith.apikeys.LANGSMITH_SERVICE_ACCOUNTS,
)
def test_apikey_owner_resolves_from_either_identifier(
    mock_accounts, mock_optional, mock_ws_keys, neo4j_session
):
    """
    created_by is undocumented and carries an identity UUID on some routes and an
    ls_user_id on others. Both must resolve to the same user node.
    """
    _ensure_local_neo4j_has_test_roles(neo4j_session)
    _ensure_local_neo4j_has_test_workspaces(neo4j_session)
    users = _ensure_local_neo4j_has_test_users(neo4j_session)

    cartography.intel.langsmith.apikeys.sync(
        neo4j_session,
        None,
        LANGSMITH_ORG_ID,
        users,
        LANGSMITH_WORKSPACES,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": LANGSMITH_ORG_ID},
    )

    assert check_rels(
        neo4j_session,
        "LangSmithApiKey",
        "short_key",
        "LangSmithUser",
        "id",
        "OWNED_BY",
        rel_direction_right=True,
    ) == {
        # created_by held an org identity UUID
        ("lsv2_sk_abcd", MARGE_LS_USER_ID),
        ("lsv2_sc_1234", MARGE_LS_USER_ID),
        # created_by held an ls_user_id
        ("lsv2_pt_wxyz", BART_LS_USER_ID),
    }

    assert check_rels(
        neo4j_session,
        "LangSmithApiKey",
        "short_key",
        "LangSmithRole",
        "id",
        "ASSUMES",
        rel_direction_right=True,
    ) == {
        ("lsv2_sk_abcd", CUSTOM_ROLE_ID),
        ("lsv2_pt_wxyz", ORG_ADMIN_ROLE_ID),
    }
