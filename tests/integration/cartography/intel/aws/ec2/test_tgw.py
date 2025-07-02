from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ec2.tgw
import tests.data.aws.ec2.tgw
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "eu-west-1"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.ec2.tgw,
    "get_transit_gateways",
    return_value=tests.data.aws.ec2.tgw.TRANSIT_GATEWAYS,
)
@patch.object(
    cartography.intel.aws.ec2.tgw,
    "get_tgw_attachments",
    return_value=tests.data.aws.ec2.tgw.TRANSIT_GATEWAY_ATTACHMENTS,
)
@patch.object(
    cartography.intel.aws.ec2.tgw,
    "get_tgw_vpc_attachments",
    return_value=tests.data.aws.ec2.tgw.TGW_VPC_ATTACHMENTS,
)
def test_sync_transit_gateways(mock_vpc_att, mock_att, mock_tgw, neo4j_session):
    boto3_session = MagicMock()

    cartography.intel.aws.ec2.tgw.sync_transit_gateways(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    assert check_nodes(neo4j_session, "AWSTransitGateway", ["arn"]) == {
        ("arn:aws:ec2:eu-west-1:000000000000:transit-gateway/tgw-0123456789abcdef0",),
    }

    assert check_nodes(
        neo4j_session, "AWSTransitGatewayAttachment", ["transit_gateway_attachment_id"]
    ) == {
        ("tgw-attach-aaaabbbbccccdef01",),
    }

    assert check_rels(
        neo4j_session,
        "AWSTransitGatewayAttachment",
        "transit_gateway_attachment_id",
        "AWSTransitGateway",
        "tgw_id",
        "ATTACHED_TO",
        rel_direction_right=True,
    ) == {
        ("tgw-attach-aaaabbbbccccdef01", "tgw-0123456789abcdef0"),
    }
