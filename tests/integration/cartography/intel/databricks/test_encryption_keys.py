from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.encryption_keys
from tests.data.databricks.account import DATABRICKS_ACCOUNT_ID
from tests.data.databricks.encryption_keys import DATABRICKS_ENCRYPTION_KEY_AWS_ARN
from tests.data.databricks.encryption_keys import DATABRICKS_ENCRYPTION_KEY_GCP_NAME
from tests.data.databricks.encryption_keys import DATABRICKS_ENCRYPTION_KEYS
from tests.integration.cartography.intel.databricks.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _seed_cloud_keys(neo4j_session):
    neo4j_session.run(
        "MERGE (k:AWSKMSKey {arn: $arn}) SET k.lastupdated = $tag",
        arn=DATABRICKS_ENCRYPTION_KEY_AWS_ARN,
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        # GCPCryptoKey.id is the full KMS resource name, matching the value
        # Databricks reports in gcp_key_info.kms_key_id.
        "MERGE (k:GCPCryptoKey {id: $name}) SET k.lastupdated = $tag",
        name=DATABRICKS_ENCRYPTION_KEY_GCP_NAME,
        tag=TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.databricks.encryption_keys,
    "get",
    return_value=DATABRICKS_ENCRYPTION_KEYS,
)
def test_load_databricks_encryption_keys(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": DATABRICKS_ACCOUNT_ID,
    }
    _ensure_local_neo4j_has_test_account(neo4j_session)
    _seed_cloud_keys(neo4j_session)

    cartography.intel.databricks.encryption_keys.sync(
        neo4j_session,
        api_session,
        DATABRICKS_ACCOUNT_ID,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksEncryptionKey",
        ["customer_managed_key_id"],
    ) == {
        ("cmk-abc-123",),
        ("cmk-def-456",),
    }

    # EncryptionKey -> Account RESOURCE
    assert check_rels(
        neo4j_session,
        "DatabricksEncryptionKey",
        "customer_managed_key_id",
        "DatabricksAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("cmk-abc-123", DATABRICKS_ACCOUNT_ID),
        ("cmk-def-456", DATABRICKS_ACCOUNT_ID),
    }

    # EncryptionKey -> AWSKMSKey REFERENCES_KEY
    assert check_rels(
        neo4j_session,
        "DatabricksEncryptionKey",
        "customer_managed_key_id",
        "AWSKMSKey",
        "arn",
        "REFERENCES_KEY",
        rel_direction_right=True,
    ) == {("cmk-abc-123", DATABRICKS_ENCRYPTION_KEY_AWS_ARN)}

    # EncryptionKey -> GCPCryptoKey REFERENCES_KEY
    assert check_rels(
        neo4j_session,
        "DatabricksEncryptionKey",
        "customer_managed_key_id",
        "GCPCryptoKey",
        "id",
        "REFERENCES_KEY",
        rel_direction_right=True,
    ) == {("cmk-def-456", DATABRICKS_ENCRYPTION_KEY_GCP_NAME)}
