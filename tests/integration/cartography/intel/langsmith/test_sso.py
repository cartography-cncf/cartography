from unittest.mock import patch

import cartography.intel.langsmith.sso
import tests.data.langsmith.workspace_resources
from tests.data.langsmith.organizations import LANGSMITH_ORG_ID
from tests.data.langsmith.roles import CUSTOM_ROLE_ID
from tests.data.langsmith.workspaces import WORKSPACE_DEV_ID
from tests.data.langsmith.workspaces import WORKSPACE_PROD_ID
from tests.integration.cartography.intel.langsmith.test_roles import (
    _ensure_local_neo4j_has_test_roles,
)
from tests.integration.cartography.intel.langsmith.test_workspaces import (
    _ensure_local_neo4j_has_test_workspaces,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@patch.object(cartography.intel.langsmith.sso, "get_data_planes", return_value=[])
@patch.object(
    cartography.intel.langsmith.sso,
    "get_access_policies",
    return_value=tests.data.langsmith.workspace_resources.LANGSMITH_ACCESS_POLICIES[
        "access_policies"
    ],
)
@patch.object(
    cartography.intel.langsmith.sso,
    "get_sso_settings",
    return_value=tests.data.langsmith.workspace_resources.LANGSMITH_SSO_SETTINGS,
)
def test_sync_langsmith_sso(mock_sso, mock_policies, mock_planes, neo4j_session):
    _ensure_local_neo4j_has_test_roles(neo4j_session)
    _ensure_local_neo4j_has_test_workspaces(neo4j_session)

    cartography.intel.langsmith.sso.sync(
        neo4j_session,
        None,
        LANGSMITH_ORG_ID,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": LANGSMITH_ORG_ID},
    )

    # The SAML metadata XML is reduced to a boolean rather than stored verbatim.
    assert check_nodes(
        neo4j_session,
        "LangSmithSSOProvider",
        ["name", "has_metadata_xml", "sso_groups_role_sync_enabled"],
    ) == {("okta-saml", True, True)}

    # JIT provisioning blast radius: which workspaces and which default role.
    assert check_rels(
        neo4j_session,
        "LangSmithSSOProvider",
        "name",
        "LangSmithWorkspace",
        "id",
        "PROVISIONS_INTO",
        rel_direction_right=True,
    ) == {
        ("okta-saml", WORKSPACE_PROD_ID),
        ("okta-saml", WORKSPACE_DEV_ID),
    }

    assert check_rels(
        neo4j_session,
        "LangSmithSSOProvider",
        "name",
        "LangSmithRole",
        "id",
        "DEFAULT_ROLE",
        rel_direction_right=True,
    ) == {("okta-saml", CUSTOM_ROLE_ID)}


@patch.object(cartography.intel.langsmith.sso, "get_data_planes", return_value=[])
@patch.object(
    cartography.intel.langsmith.sso,
    "get_access_policies",
    return_value=tests.data.langsmith.workspace_resources.LANGSMITH_ACCESS_POLICIES[
        "access_policies"
    ],
)
@patch.object(
    cartography.intel.langsmith.sso,
    "get_sso_settings",
    return_value=tests.data.langsmith.workspace_resources.LANGSMITH_SSO_SETTINGS,
)
def test_access_policy_conditions_are_flattened(
    mock_sso, mock_policies, mock_planes, neo4j_session
):
    """Nested condition groups cannot be stored as a Neo4j property, so they are summarized."""
    _ensure_local_neo4j_has_test_roles(neo4j_session)
    _ensure_local_neo4j_has_test_workspaces(neo4j_session)

    cartography.intel.langsmith.sso.sync(
        neo4j_session,
        None,
        LANGSMITH_ORG_ID,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": LANGSMITH_ORG_ID},
    )

    assert check_nodes(
        neo4j_session, "LangSmithAccessPolicy", ["name", "effect", "condition_summary"]
    ) == {("Production projects only", "allow", "project.tag in ['prod']")}

    assert check_rels(
        neo4j_session,
        "LangSmithAccessPolicy",
        "name",
        "LangSmithRole",
        "id",
        "ATTACHED_TO",
        rel_direction_right=True,
    ) == {("Production projects only", CUSTOM_ROLE_ID)}
