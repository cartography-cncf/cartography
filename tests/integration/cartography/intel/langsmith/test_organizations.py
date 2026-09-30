from unittest.mock import patch

import cartography.intel.langsmith.organizations
import tests.data.langsmith.organizations
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = tests.data.langsmith.organizations.LANGSMITH_ORG_ID


def _ensure_local_neo4j_has_test_organizations(neo4j_session):
    cartography.intel.langsmith.organizations.load_organizations(
        neo4j_session,
        [
            cartography.intel.langsmith.organizations.transform_organization(
                TEST_ORG_ID,
                tests.data.langsmith.organizations.LANGSMITH_ORG_INFO,
            )
        ],
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.langsmith.organizations,
    "get_info",
    return_value=tests.data.langsmith.organizations.LANGSMITH_ORG_INFO,
)
@patch.object(
    cartography.intel.langsmith.organizations,
    "get_organization_ids",
    return_value=[TEST_ORG_ID],
)
def test_sync_langsmith_organizations(mock_ids, mock_info, neo4j_session):
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}

    organizations = cartography.intel.langsmith.organizations.sync(
        neo4j_session,
        None,
        None,
        common_job_parameters,
    )

    assert [org["id"] for org in organizations] == [TEST_ORG_ID]
    assert check_nodes(
        neo4j_session,
        "LangSmithOrganization",
        ["id", "name", "sso_only", "pat_creation_disabled", "max_pat_expiry_days"],
    ) == {(TEST_ORG_ID, "Simpson Corp", True, False, 30)}


@patch.object(
    cartography.intel.langsmith.organizations,
    "get_info",
    return_value={"display_name": "Simpson Corp"},
)
@patch.object(
    cartography.intel.langsmith.organizations,
    "get_organization_ids",
    return_value=[TEST_ORG_ID],
)
def test_org_id_falls_back_when_info_omits_it(mock_ids, mock_info, neo4j_session):
    """OrganizationInfo.id is nullable, so the scoped org id must be used instead."""
    cartography.intel.langsmith.organizations.sync(
        neo4j_session,
        None,
        None,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    assert check_nodes(neo4j_session, "LangSmithOrganization", ["id"]) == {
        (TEST_ORG_ID,)
    }
