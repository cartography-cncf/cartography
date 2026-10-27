from unittest.mock import Mock

import pytest

from cartography.config import Config
from cartography.intel.databricks import start_databricks_ingestion

_ENTRA = {
    "databricks_azure_tenant_id": "00000000-0000-0000-0000-000000000000",
    "databricks_azure_client_id": "entra-client-id",
    "databricks_azure_client_secret": "entra-client-secret",
}


@pytest.mark.parametrize(
    "auth, error",
    [
        pytest.param(
            {
                "databricks_azure_client_id": "entra-client-id",
                "databricks_azure_client_secret": "entra-client-secret",
            },
            "partially configured",
            id="partial-entra",
        ),
        pytest.param(
            {**_ENTRA, "databricks_token": "pat"},
            "more than once",
            id="pat-and-entra",
        ),
        pytest.param(
            {
                "databricks_token": "pat",
                "databricks_client_id": "client-id",
                "databricks_client_secret": "client-secret",
            },
            "more than once",
            id="pat-and-oauth",
        ),
    ],
)
def test_workspace_auth_must_be_exactly_one_complete_method(auth, error):
    # Arrange
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=1,
        databricks_workspace_url="https://adb-0000000000000000.0.azuredatabricks.net",
        **auth,
    )

    # Act and assert
    with pytest.raises(ValueError, match=error):
        start_databricks_ingestion(Mock(), config)
