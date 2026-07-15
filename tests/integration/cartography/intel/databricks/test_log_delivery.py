from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.log_delivery
from tests.data.databricks.account import DATABRICKS_ACCOUNT_ID
from tests.data.databricks.log_delivery import DATABRICKS_LOG_DELIVERY_BUCKET
from tests.data.databricks.log_delivery import DATABRICKS_LOG_DELIVERY_CONFIGS
from tests.integration.cartography.intel.databricks.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _seed_s3_bucket(neo4j_session):
    neo4j_session.run(
        "MERGE (b:AWSS3Bucket {name: $name}) SET b.lastupdated = $tag",
        name=DATABRICKS_LOG_DELIVERY_BUCKET,
        tag=TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.databricks.log_delivery,
    "get",
    return_value=DATABRICKS_LOG_DELIVERY_CONFIGS,
)
def test_load_databricks_log_delivery(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": DATABRICKS_ACCOUNT_ID,
    }
    _ensure_local_neo4j_has_test_account(neo4j_session)
    _seed_s3_bucket(neo4j_session)

    cartography.intel.databricks.log_delivery.sync(
        neo4j_session,
        api_session,
        DATABRICKS_ACCOUNT_ID,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksLogDelivery",
        ["config_id", "log_type"],
    ) == {
        ("log-abc-123", "AUDIT_LOGS"),
        ("log-def-456", "BILLABLE_USAGE"),
    }

    # LogDelivery -> Account RESOURCE
    assert check_rels(
        neo4j_session,
        "DatabricksLogDelivery",
        "config_id",
        "DatabricksAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("log-abc-123", DATABRICKS_ACCOUNT_ID),
        ("log-def-456", DATABRICKS_ACCOUNT_ID),
    }

    # LogDelivery -> AWSS3Bucket DELIVERS_TO (only forms when the bucket is known)
    assert check_rels(
        neo4j_session,
        "DatabricksLogDelivery",
        "config_id",
        "AWSS3Bucket",
        "name",
        "DELIVERS_TO",
        rel_direction_right=True,
    ) == {("log-abc-123", DATABRICKS_LOG_DELIVERY_BUCKET)}
