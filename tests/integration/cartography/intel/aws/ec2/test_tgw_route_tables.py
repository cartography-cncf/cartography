from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ec2.tgw
import cartography.intel.aws.ec2.tgw_route_tables
from cartography.intel.aws.ec2.tgw import sync_transit_gateways
from cartography.intel.aws.ec2.tgw_route_tables import sync_transit_gateway_route_tables
from tests.data.aws.ec2.tgw import TGW_VPC_ATTACHMENTS
from tests.data.aws.ec2.tgw import TRANSIT_GATEWAY_ATTACHMENTS
from tests.data.aws.ec2.tgw import TRANSIT_GATEWAYS
from tests.data.aws.ec2.tgw_route_tables import TRANSIT_GATEWAY_ROUTE_TABLE_ASSOCIATIONS
from tests.data.aws.ec2.tgw_route_tables import TRANSIT_GATEWAY_ROUTE_TABLE_PROPAGATIONS
from tests.data.aws.ec2.tgw_route_tables import TRANSIT_GATEWAY_ROUTE_TABLES
from tests.data.aws.ec2.tgw_route_tables import TRANSIT_GATEWAY_ROUTES
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "eu-west-1"
TEST_UPDATE_TAG = 123456789


def _mock_ec2_client() -> MagicMock:
    """
    Build a mock boto3 EC2 client whose get_paginator()/search_* calls return
    the fixture data shaped like the real boto3 API responses, so the id
    injection/synthesis logic in the get_* functions is exercised for real.
    """
    client = MagicMock()

    def get_paginator_side_effect(operation_name):
        paginator = MagicMock()
        if operation_name == "describe_transit_gateway_route_tables":
            paginator.paginate.return_value = [
                {"TransitGatewayRouteTables": TRANSIT_GATEWAY_ROUTE_TABLES},
            ]
        elif operation_name == "get_transit_gateway_route_table_associations":
            paginator.paginate.return_value = [
                {"Associations": TRANSIT_GATEWAY_ROUTE_TABLE_ASSOCIATIONS},
            ]
        elif operation_name == "get_transit_gateway_route_table_propagations":
            paginator.paginate.return_value = [
                {
                    "TransitGatewayRouteTablePropagations": TRANSIT_GATEWAY_ROUTE_TABLE_PROPAGATIONS,
                },
            ]
        else:
            raise ValueError(f"Unexpected paginator operation: {operation_name}")
        return paginator

    client.get_paginator.side_effect = get_paginator_side_effect
    client.search_transit_gateway_routes.return_value = {
        "Routes": TRANSIT_GATEWAY_ROUTES,
    }
    return client


@patch.object(
    cartography.intel.aws.ec2.tgw_route_tables,
    "create_boto3_client",
    return_value=_mock_ec2_client(),
)
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
    cartography.intel.aws.ec2.tgw,
    "get_transit_gateways",
    return_value=TRANSIT_GATEWAYS,
)
def test_sync_transit_gateway_route_tables(
    mock_get_tgws,
    mock_get_attachments,
    mock_get_vpc_attachments,
    mock_create_boto3_client,
    neo4j_session,
):
    """
    Ensure that sync_transit_gateway_route_tables() creates
    AWSTransitGatewayRouteTable, AWSTransitGatewayRoute,
    AWSTransitGatewayRouteTableAssociation, and
    AWSTransitGatewayRouteTablePropagation nodes with proper relationships,
    given only the boto3 client boundary is mocked.
    """
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "AWS_ID": TEST_ACCOUNT_ID,
    }
    # Seed the parent AWSTransitGateway and AWSTransitGatewayAttachment nodes
    # that the new route-table nodes link to.
    sync_transit_gateways(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Act
    sync_transit_gateway_route_tables(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert route table nodes
    assert check_nodes(
        neo4j_session, "AWSTransitGatewayRouteTable", ["id", "state"]
    ) == {
        ("tgw-rtb-0123456789abcdef0", "available"),
    }

    # Assert route nodes
    assert check_nodes(
        neo4j_session, "AWSTransitGatewayRoute", ["id", "destination_cidr_block"]
    ) == {
        (
            "tgw-rtb-0123456789abcdef0|10.0.0.0/16",
            "10.0.0.0/16",
        ),
        (
            "tgw-rtb-0123456789abcdef0|10.1.0.0/16",
            "10.1.0.0/16",
        ),
    }

    # Assert association nodes (id is synthesized route_table_id|attachment_id
    # since the API does not return TransitGatewayRouteTableAssociationId)
    assert check_nodes(
        neo4j_session, "AWSTransitGatewayRouteTableAssociation", ["id", "state"]
    ) == {
        (
            "tgw-rtb-0123456789abcdef0|tgw-attach-aaaabbbbccccdef01",
            "associated",
        ),
    }

    # Assert propagation nodes (id is synthesized the same way)
    assert check_nodes(
        neo4j_session, "AWSTransitGatewayRouteTablePropagation", ["id", "state"]
    ) == {
        (
            "tgw-rtb-0123456789abcdef0|tgw-attach-aaaabbbbccccdef01",
            "enabled",
        ),
    }

    # Assert (AWSTransitGateway)-[:CONTAINS]->(AWSTransitGatewayRouteTable)
    assert check_rels(
        neo4j_session,
        "AWSTransitGateway",
        "tgw_id",
        "AWSTransitGatewayRouteTable",
        "id",
        "CONTAINS",
        rel_direction_right=True,
    ) == {
        ("tgw-0123456789abcdef0", "tgw-rtb-0123456789abcdef0"),
    }

    # Assert (AWSTransitGatewayRouteTable)-[:HAS_ROUTE]->(AWSTransitGatewayRoute)
    assert check_rels(
        neo4j_session,
        "AWSTransitGatewayRouteTable",
        "id",
        "AWSTransitGatewayRoute",
        "id",
        "HAS_ROUTE",
        rel_direction_right=True,
    ) == {
        ("tgw-rtb-0123456789abcdef0", "tgw-rtb-0123456789abcdef0|10.0.0.0/16"),
        ("tgw-rtb-0123456789abcdef0", "tgw-rtb-0123456789abcdef0|10.1.0.0/16"),
    }

    # Assert (AWSTransitGatewayRoute)-[:ROUTES_TO_TGW]->(AWSTransitGateway)
    assert check_rels(
        neo4j_session,
        "AWSTransitGatewayRoute",
        "id",
        "AWSTransitGateway",
        "tgw_id",
        "ROUTES_TO_TGW",
        rel_direction_right=True,
    ) == {
        ("tgw-rtb-0123456789abcdef0|10.0.0.0/16", "tgw-0123456789abcdef0"),
        ("tgw-rtb-0123456789abcdef0|10.1.0.0/16", "tgw-0123456789abcdef0"),
    }

    # Assert (AWSTransitGatewayRoute)-[:ROUTES_TO_TGW_ATTACHMENT]->(AWSTransitGatewayAttachment)
    # Only the active route (with a TransitGatewayAttachments entry) has a target.
    assert check_rels(
        neo4j_session,
        "AWSTransitGatewayRoute",
        "id",
        "AWSTransitGatewayAttachment",
        "id",
        "ROUTES_TO_TGW_ATTACHMENT",
        rel_direction_right=True,
    ) == {
        (
            "tgw-rtb-0123456789abcdef0|10.0.0.0/16",
            "tgw-attach-aaaabbbbccccdef01",
        ),
    }

    # Assert (AWSTransitGatewayRouteTableAssociation)-[:ASSOCIATED_WITH]->(AWSTransitGatewayRouteTable)
    assert check_rels(
        neo4j_session,
        "AWSTransitGatewayRouteTableAssociation",
        "id",
        "AWSTransitGatewayRouteTable",
        "id",
        "ASSOCIATED_WITH",
        rel_direction_right=True,
    ) == {
        (
            "tgw-rtb-0123456789abcdef0|tgw-attach-aaaabbbbccccdef01",
            "tgw-rtb-0123456789abcdef0",
        ),
    }

    # Assert (AWSTransitGatewayRouteTable)-[:PROPAGATES]->(AWSTransitGatewayRouteTablePropagation)
    assert check_rels(
        neo4j_session,
        "AWSTransitGatewayRouteTable",
        "id",
        "AWSTransitGatewayRouteTablePropagation",
        "id",
        "PROPAGATES",
        rel_direction_right=True,
    ) == {
        (
            "tgw-rtb-0123456789abcdef0",
            "tgw-rtb-0123456789abcdef0|tgw-attach-aaaabbbbccccdef01",
        ),
    }

    # Assert AWSAccount ownership for all four new node types
    assert check_rels(
        neo4j_session,
        "AWSTransitGatewayRouteTable",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {("tgw-rtb-0123456789abcdef0", TEST_ACCOUNT_ID)}

    assert check_rels(
        neo4j_session,
        "AWSTransitGatewayRoute",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("tgw-rtb-0123456789abcdef0|10.0.0.0/16", TEST_ACCOUNT_ID),
        ("tgw-rtb-0123456789abcdef0|10.1.0.0/16", TEST_ACCOUNT_ID),
    }

    assert check_rels(
        neo4j_session,
        "AWSTransitGatewayRouteTableAssociation",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (
            "tgw-rtb-0123456789abcdef0|tgw-attach-aaaabbbbccccdef01",
            TEST_ACCOUNT_ID,
        ),
    }

    assert check_rels(
        neo4j_session,
        "AWSTransitGatewayRouteTablePropagation",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (
            "tgw-rtb-0123456789abcdef0|tgw-attach-aaaabbbbccccdef01",
            TEST_ACCOUNT_ID,
        ),
    }


@patch.object(
    cartography.intel.aws.ec2.tgw_route_tables,
    "create_boto3_client",
    return_value=_mock_ec2_client(),
)
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
    cartography.intel.aws.ec2.tgw,
    "get_transit_gateways",
    return_value=TRANSIT_GATEWAYS,
)
def test_sync_transit_gateway_route_tables_cleanup(
    mock_get_tgws,
    mock_get_attachments,
    mock_get_vpc_attachments,
    mock_create_boto3_client,
    neo4j_session,
):
    """
    Ensure that a route table, its routes, associations, and propagations
    that no longer appear in a later sync are removed by cleanup, and that
    cleanup does not fail due to leaf/parent ordering.
    """
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "AWS_ID": TEST_ACCOUNT_ID,
    }
    sync_transit_gateways(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )
    sync_transit_gateway_route_tables(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Act: sync again with a new update tag and no route tables returned,
    # simulating the route table having been deleted in AWS.
    new_update_tag = TEST_UPDATE_TAG + 1
    new_common_job_parameters = {
        "UPDATE_TAG": new_update_tag,
        "AWS_ID": TEST_ACCOUNT_ID,
    }
    empty_client = MagicMock()
    empty_client.get_paginator.return_value.paginate.return_value = [
        {"TransitGatewayRouteTables": []},
    ]
    with patch.object(
        cartography.intel.aws.ec2.tgw_route_tables,
        "create_boto3_client",
        return_value=empty_client,
    ):
        sync_transit_gateway_route_tables(
            neo4j_session,
            boto3_session,
            [TEST_REGION],
            TEST_ACCOUNT_ID,
            new_update_tag,
            new_common_job_parameters,
        )

    # Assert all four node types were cleaned up
    assert check_nodes(neo4j_session, "AWSTransitGatewayRouteTable", ["id"]) == set()
    assert check_nodes(neo4j_session, "AWSTransitGatewayRoute", ["id"]) == set()
    assert (
        check_nodes(neo4j_session, "AWSTransitGatewayRouteTableAssociation", ["id"])
        == set()
    )
    assert (
        check_nodes(neo4j_session, "AWSTransitGatewayRouteTablePropagation", ["id"])
        == set()
    )
