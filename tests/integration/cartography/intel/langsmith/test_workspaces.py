from unittest.mock import patch

import cartography.intel.langsmith.workspaces
import tests.data.langsmith.workspaces
from tests.data.langsmith.organizations import LANGSMITH_ORG_ID
from tests.data.langsmith.workspaces import WORKSPACE_DEV_ID
from tests.data.langsmith.workspaces import WORKSPACE_PROD_ID
from tests.integration.cartography.intel.langsmith.test_organizations import (
    _ensure_local_neo4j_has_test_organizations,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_workspaces(neo4j_session):
    cartography.intel.langsmith.workspaces.load_workspaces(
        neo4j_session,
        tests.data.langsmith.workspaces.LANGSMITH_WORKSPACES,
        LANGSMITH_ORG_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.langsmith.workspaces,
    "get",
    return_value=tests.data.langsmith.workspaces.LANGSMITH_WORKSPACES,
)
def test_sync_langsmith_workspaces(mock_get, neo4j_session):
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": LANGSMITH_ORG_ID,
    }

    workspaces = cartography.intel.langsmith.workspaces.sync(
        neo4j_session, None, LANGSMITH_ORG_ID, common_job_parameters
    )

    assert {w["id"] for w in workspaces} == {WORKSPACE_PROD_ID, WORKSPACE_DEV_ID}
    assert check_nodes(
        neo4j_session, "LangSmithWorkspace", ["id", "name", "is_personal"]
    ) == {
        (WORKSPACE_PROD_ID, "Production", False),
        (WORKSPACE_DEV_ID, "Development", False),
    }
    assert check_rels(
        neo4j_session,
        "LangSmithOrganization",
        "id",
        "LangSmithWorkspace",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (LANGSMITH_ORG_ID, WORKSPACE_PROD_ID),
        (LANGSMITH_ORG_ID, WORKSPACE_DEV_ID),
    }
