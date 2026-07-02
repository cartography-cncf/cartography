from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.serving_endpoints
from tests.data.databricks.serving_endpoints import DATABRICKS_SERVING_ENDPOINTS
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE_ID
from tests.data.databricks.workspace import scoped
from tests.integration.cartography.intel.databricks.test_workspaces import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.databricks.serving_endpoints,
    "get",
    return_value=DATABRICKS_SERVING_ENDPOINTS,
)
def test_load_databricks_serving_endpoints(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)

    cartography.intel.databricks.serving_endpoints.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksServingEndpoint",
        ["id", "name", "endpoint_type"],
    ) == {
        (scoped("databricks-gpt-5-5"), "databricks-gpt-5-5", "FOUNDATION_MODEL_API"),
        (scoped("external-openai-proxy"), "external-openai-proxy", "EXTERNAL_MODEL"),
    }

    # Served entities, incl. the external-model egress signal.
    assert check_nodes(
        neo4j_session,
        "DatabricksServedEntity",
        ["id", "entity_type", "external_model_provider"],
    ) == {
        (
            scoped("databricks-gpt-5-5") + "/databricks-gpt-5-5",
            "FOUNDATION_MODEL",
            None,
        ),
        (scoped("external-openai-proxy") + "/openai-gpt4", "EXTERNAL_MODEL", "openai"),
    }

    assert check_rels(
        neo4j_session,
        "DatabricksServingEndpoint",
        "id",
        "DatabricksWorkspace",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (scoped("databricks-gpt-5-5"), DATABRICKS_WORKSPACE_ID),
        (scoped("external-openai-proxy"), DATABRICKS_WORKSPACE_ID),
    }

    assert check_rels(
        neo4j_session,
        "DatabricksServingEndpoint",
        "id",
        "DatabricksServedEntity",
        "id",
        "SERVES",
        rel_direction_right=True,
    ) == {
        (
            scoped("databricks-gpt-5-5"),
            scoped("databricks-gpt-5-5") + "/databricks-gpt-5-5",
        ),
        (
            scoped("external-openai-proxy"),
            scoped("external-openai-proxy") + "/openai-gpt4",
        ),
    }
