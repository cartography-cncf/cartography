from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.storage_credentials
from tests.data.databricks.storage_credentials import DATABRICKS_STORAGE_CRED_AWS_ARN
from tests.data.databricks.storage_credentials import DATABRICKS_STORAGE_CRED_GCP_EMAIL
from tests.data.databricks.storage_credentials import DATABRICKS_STORAGE_CREDENTIALS
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE_ID
from tests.integration.cartography.intel.databricks.test_metastores import (
    _ensure_local_neo4j_has_test_metastore,
)
from tests.integration.cartography.intel.databricks.test_workspaces import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _seed_cloud_principals(neo4j_session):
    neo4j_session.run(
        "MERGE (p:AWSPrincipal {arn: $arn}) SET p.lastupdated = $tag",
        arn=DATABRICKS_STORAGE_CRED_AWS_ARN,
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (s:GCPServiceAccount {email: $email}) SET s.lastupdated = $tag",
        email=DATABRICKS_STORAGE_CRED_GCP_EMAIL,
        tag=TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.databricks.storage_credentials,
    "get",
    return_value=DATABRICKS_STORAGE_CREDENTIALS,
)
def test_load_databricks_storage_credentials(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _ensure_local_neo4j_has_test_metastore(neo4j_session)
    _seed_cloud_principals(neo4j_session)

    cartography.intel.databricks.storage_credentials.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksStorageCredential",
        ["name", "credential_type"],
    ) == {
        ("aws-uc-storage-cred", "AWS_IAM_ROLE"),
        ("gcp-uc-storage-cred", "GCP_SERVICE_ACCOUNT"),
    }

    # StorageCredential -> Workspace RESOURCE
    assert check_rels(
        neo4j_session,
        "DatabricksStorageCredential",
        "name",
        "DatabricksWorkspace",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("aws-uc-storage-cred", DATABRICKS_WORKSPACE_ID),
        ("gcp-uc-storage-cred", DATABRICKS_WORKSPACE_ID),
    }

    # AWS credential -> AWSPrincipal ASSUMES_ROLE
    assert check_rels(
        neo4j_session,
        "DatabricksStorageCredential",
        "name",
        "AWSPrincipal",
        "arn",
        "ASSUMES_ROLE",
        rel_direction_right=True,
    ) == {("aws-uc-storage-cred", DATABRICKS_STORAGE_CRED_AWS_ARN)}

    # GCP credential -> GCPServiceAccount IMPERSONATES
    assert check_rels(
        neo4j_session,
        "DatabricksStorageCredential",
        "name",
        "GCPServiceAccount",
        "email",
        "IMPERSONATES",
        rel_direction_right=True,
    ) == {("gcp-uc-storage-cred", DATABRICKS_STORAGE_CRED_GCP_EMAIL)}
