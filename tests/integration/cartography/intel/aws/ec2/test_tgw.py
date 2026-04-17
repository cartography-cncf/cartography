from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ec2.tgw
from tests.data.aws.ec2.tgw import TGW_VPC_ATTACHMENTS
from tests.data.aws.ec2.tgw import TRANSIT_GATEWAY_ATTACHMENTS
from tests.data.aws.ec2.tgw import TRANSIT_GATEWAYS
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "eu-west-1"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.ec2.tgw,
    "get_tgw_vpc_attachments",
    return_value=TGW_VPC_ATTACHMENTS,
)
@patch.object(
    cartography.intel.aws.ec2.tgw,
    "get_tgw_attachments",
    return_value=TRANSIT_GATEWAY_ATTACHMENTS,
)
@patch.object(
    cartography.intel.aws.ec2.tgw, "get_transit_gateways", return_value=TRANSIT_GATEWAYS
)
def test_sync_transit_gateways(
    mock_get_tgws, mock_get_attachments, mock_get_vpc, neo4j_session
):
    """
    Ensure that sync_transit_gateways() creates AWSTransitGateway and AWSTransitGatewayAttachment nodes
    with proper relationships.
    """
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    cartography.intel.aws.ec2.tgw.sync_transit_gateways(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Verify AWSTransitGateway nodes
    assert check_nodes(neo4j_session, "AWSTransitGateway", ["arn"]) == {
        ("arn:aws:ec2:eu-west-1:000000000000:transit-gateway/tgw-0123456789abcdef0",),
    }

    # Verify AWSTransitGatewayAttachment nodes
    assert check_nodes(neo4j_session, "AWSTransitGatewayAttachment", ["id"]) == {
        ("tgw-attach-aaaabbbbccccdef01",),
    }

    # Verify AWSTransitGatewayAttachment -[:ATTACHED_TO]-> AWSTransitGateway
    assert check_rels(
        neo4j_session,
        "AWSTransitGatewayAttachment",
        "id",
        "AWSTransitGateway",
        "arn",
        "ATTACHED_TO",
        rel_direction_right=True,
    ) == {
        (
            "tgw-attach-aaaabbbbccccdef01",
            "arn:aws:ec2:eu-west-1:000000000000:transit-gateway/tgw-0123456789abcdef0",
        ),
    }
