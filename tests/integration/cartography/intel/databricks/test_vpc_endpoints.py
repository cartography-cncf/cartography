from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.vpc_endpoints
from tests.data.databricks.account import DATABRICKS_ACCOUNT_ID
from tests.data.databricks.vpc_endpoints import DATABRICKS_AWS_VPC_ENDPOINT_ID
from tests.data.databricks.vpc_endpoints import DATABRICKS_VPC_ENDPOINTS
from tests.integration.cartography.intel.databricks.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _seed_aws_vpc_endpoint(neo4j_session):
    neo4j_session.run(
        "MERGE (e:AWSVpcEndpoint {id: $id}) SET e.lastupdated = $tag",
        id=DATABRICKS_AWS_VPC_ENDPOINT_ID,
        tag=TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.databricks.vpc_endpoints,
    "get",
    return_value=DATABRICKS_VPC_ENDPOINTS,
)
def test_load_databricks_vpc_endpoints(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": DATABRICKS_ACCOUNT_ID,
    }
    _ensure_local_neo4j_has_test_account(neo4j_session)
    _seed_aws_vpc_endpoint(neo4j_session)

    cartography.intel.databricks.vpc_endpoints.sync(
        neo4j_session,
        api_session,
        DATABRICKS_ACCOUNT_ID,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksVpcEndpoint",
        ["vpc_endpoint_id", "aws_vpc_endpoint_id"],
    ) == {("vpce-abc-123", DATABRICKS_AWS_VPC_ENDPOINT_ID)}

    # VpcEndpoint -> Account RESOURCE
    assert check_rels(
        neo4j_session,
        "DatabricksVpcEndpoint",
        "vpc_endpoint_id",
        "DatabricksAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {("vpce-abc-123", DATABRICKS_ACCOUNT_ID)}

    # VpcEndpoint -> AWSVpcEndpoint POINTS_TO
    assert check_rels(
        neo4j_session,
        "DatabricksVpcEndpoint",
        "vpc_endpoint_id",
        "AWSVpcEndpoint",
        "id",
        "POINTS_TO",
        rel_direction_right=True,
    ) == {("vpce-abc-123", DATABRICKS_AWS_VPC_ENDPOINT_ID)}
