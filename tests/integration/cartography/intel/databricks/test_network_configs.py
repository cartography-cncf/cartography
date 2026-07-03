from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.network_configs
from tests.data.databricks.account import DATABRICKS_ACCOUNT_ID
from tests.data.databricks.network_configs import DATABRICKS_NETWORK_CONFIGS
from tests.data.databricks.network_configs import DATABRICKS_NETWORK_SG_IDS
from tests.data.databricks.network_configs import DATABRICKS_NETWORK_SUBNET_IDS
from tests.data.databricks.network_configs import DATABRICKS_NETWORK_VPC_ID
from tests.integration.cartography.intel.databricks.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _seed_aws_network_nodes(neo4j_session):
    neo4j_session.run(
        "MERGE (v:AWSVpc {id: $id}) SET v.lastupdated = $tag",
        id=DATABRICKS_NETWORK_VPC_ID,
        tag=TEST_UPDATE_TAG,
    )
    for subnet_id in DATABRICKS_NETWORK_SUBNET_IDS:
        neo4j_session.run(
            "MERGE (s:EC2Subnet {id: $id}) SET s.lastupdated = $tag",
            id=subnet_id,
            tag=TEST_UPDATE_TAG,
        )
    for sg_id in DATABRICKS_NETWORK_SG_IDS:
        neo4j_session.run(
            "MERGE (g:EC2SecurityGroup {id: $id}) SET g.lastupdated = $tag",
            id=sg_id,
            tag=TEST_UPDATE_TAG,
        )


@patch.object(
    cartography.intel.databricks.network_configs,
    "get",
    return_value=DATABRICKS_NETWORK_CONFIGS,
)
def test_load_databricks_network_configs(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": DATABRICKS_ACCOUNT_ID,
    }
    _ensure_local_neo4j_has_test_account(neo4j_session)
    _seed_aws_network_nodes(neo4j_session)

    cartography.intel.databricks.network_configs.sync(
        neo4j_session,
        api_session,
        DATABRICKS_ACCOUNT_ID,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksNetworkConfig",
        ["network_id", "vpc_id"],
    ) == {("net-abc-123", DATABRICKS_NETWORK_VPC_ID)}

    # NetworkConfig -> Account RESOURCE
    assert check_rels(
        neo4j_session,
        "DatabricksNetworkConfig",
        "network_id",
        "DatabricksAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {("net-abc-123", DATABRICKS_ACCOUNT_ID)}

    # NetworkConfig -> AWSVpc USES_VPC
    assert check_rels(
        neo4j_session,
        "DatabricksNetworkConfig",
        "network_id",
        "AWSVpc",
        "id",
        "USES_VPC",
        rel_direction_right=True,
    ) == {("net-abc-123", DATABRICKS_NETWORK_VPC_ID)}

    # NetworkConfig -> EC2Subnet USES_SUBNET
    assert check_rels(
        neo4j_session,
        "DatabricksNetworkConfig",
        "network_id",
        "EC2Subnet",
        "id",
        "USES_SUBNET",
        rel_direction_right=True,
    ) == {("net-abc-123", s) for s in DATABRICKS_NETWORK_SUBNET_IDS}

    # NetworkConfig -> EC2SecurityGroup USES_SECURITY_GROUP
    assert check_rels(
        neo4j_session,
        "DatabricksNetworkConfig",
        "network_id",
        "EC2SecurityGroup",
        "id",
        "USES_SECURITY_GROUP",
        rel_direction_right=True,
    ) == {("net-abc-123", g) for g in DATABRICKS_NETWORK_SG_IDS}
