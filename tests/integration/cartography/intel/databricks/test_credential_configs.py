from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.credential_configs
from tests.data.databricks.account import DATABRICKS_ACCOUNT_ID
from tests.data.databricks.credential_configs import (
    DATABRICKS_CRED_CONFIG_AWS_ACCOUNT_ID,
)
from tests.data.databricks.credential_configs import DATABRICKS_CRED_CONFIG_AWS_ARN
from tests.data.databricks.credential_configs import DATABRICKS_CREDENTIAL_CONFIGS
from tests.integration.cartography.intel.databricks.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _seed_aws_nodes(neo4j_session):
    neo4j_session.run(
        "MERGE (p:AWSPrincipal {arn: $arn}) SET p.lastupdated = $tag",
        arn=DATABRICKS_CRED_CONFIG_AWS_ARN,
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (a:AWSAccount {id: $id}) SET a.lastupdated = $tag",
        id=DATABRICKS_CRED_CONFIG_AWS_ACCOUNT_ID,
        tag=TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.databricks.credential_configs,
    "get",
    return_value=DATABRICKS_CREDENTIAL_CONFIGS,
)
def test_load_databricks_credential_configs(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": DATABRICKS_ACCOUNT_ID,
    }
    _ensure_local_neo4j_has_test_account(neo4j_session)
    _seed_aws_nodes(neo4j_session)

    cartography.intel.databricks.credential_configs.sync(
        neo4j_session,
        api_session,
        DATABRICKS_ACCOUNT_ID,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksCredentialConfig",
        ["credentials_id", "aws_account_id"],
    ) == {
        ("cred-abc-123", DATABRICKS_CRED_CONFIG_AWS_ACCOUNT_ID),
        ("cred-def-456", "999988887777"),
    }

    # CredentialConfig -> Account RESOURCE
    assert check_rels(
        neo4j_session,
        "DatabricksCredentialConfig",
        "credentials_id",
        "DatabricksAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("cred-abc-123", DATABRICKS_ACCOUNT_ID),
        ("cred-def-456", DATABRICKS_ACCOUNT_ID),
    }

    # CredentialConfig -> AWSPrincipal ASSUMES_ROLE
    assert check_rels(
        neo4j_session,
        "DatabricksCredentialConfig",
        "credentials_id",
        "AWSPrincipal",
        "arn",
        "ASSUMES_ROLE",
        rel_direction_right=True,
    ) == {("cred-abc-123", DATABRICKS_CRED_CONFIG_AWS_ARN)}

    # CredentialConfig -> AWSAccount IN_ACCOUNT (only forms when the node exists)
    assert check_rels(
        neo4j_session,
        "DatabricksCredentialConfig",
        "credentials_id",
        "AWSAccount",
        "id",
        "IN_ACCOUNT",
        rel_direction_right=True,
    ) == {("cred-abc-123", DATABRICKS_CRED_CONFIG_AWS_ACCOUNT_ID)}
