from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.directconnect
from cartography.intel.aws.directconnect import sync
from tests.data.aws.directconnect import DESCRIBE_CONNECTIONS
from tests.data.aws.directconnect import DESCRIBE_DIRECT_CONNECT_GATEWAY_ASSOCIATIONS
from tests.data.aws.directconnect import DESCRIBE_DIRECT_CONNECT_GATEWAYS
from tests.data.aws.directconnect import DESCRIBE_VIRTUAL_INTERFACES
from tests.data.aws.directconnect import TEST_CONNECTION_ID
from tests.data.aws.directconnect import TEST_DXGW_ID
from tests.data.aws.directconnect import TEST_TGW_ID
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "eu-west-1"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.directconnect,
    "get_dx_gateway_associations",
    return_value=DESCRIBE_DIRECT_CONNECT_GATEWAY_ASSOCIATIONS,
)
@patch.object(
    cartography.intel.aws.directconnect,
    "get_dx_virtual_interfaces",
    return_value=DESCRIBE_VIRTUAL_INTERFACES,
)
@patch.object(
    cartography.intel.aws.directconnect,
    "get_dx_gateways",
    return_value=DESCRIBE_DIRECT_CONNECT_GATEWAYS,
)
@patch.object(
    cartography.intel.aws.directconnect,
    "get_dx_connections",
    return_value=DESCRIBE_CONNECTIONS,
)
def test_sync_directconnect(
    mock_connections, mock_gateways, mock_vifs, mock_assocs, neo4j_session
):
    # Arrange
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    # A Transit Gateway that a gateway association points at.
    neo4j_session.run(
        """
        MERGE (t:AWSTransitGateway{id: $arn})
        SET t.tgw_id = $tgw_id, t.lastupdated = $update_tag
        """,
        arn=f"arn:aws:ec2:{TEST_REGION}:{TEST_ACCOUNT_ID}:transit-gateway/{TEST_TGW_ID}",
        tgw_id=TEST_TGW_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    # Act
    sync(
        neo4j_session,
        MagicMock(),
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert: the physical connection, with the attributes an auditor asks for.
    assert check_nodes(
        neo4j_session,
        "AWSDirectConnectConnection",
        ["id", "bandwidth", "location", "state"],
    ) == {(TEST_CONNECTION_ID, "1Gbps", "EqLD5", "available")}

    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSDirectConnectConnection",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {(TEST_ACCOUNT_ID, TEST_CONNECTION_ID)}

    # Assert: both virtual interfaces, and the prefixes a public VIF advertises.
    assert check_nodes(
        neo4j_session, "AWSDirectConnectVirtualInterface", ["id", "type", "vlan"]
    ) == {
        ("dxvif-ffabc123", "transit", 101),
        ("dxvif-ffdef456", "public", 102),
    }

    public_vif = neo4j_session.run(
        """
        MATCH (v:AWSDirectConnectVirtualInterface{id: 'dxvif-ffdef456'})
        RETURN v.route_filter_prefixes AS prefixes, v.bgp_peer_states AS peers
        """
    ).single()
    assert sorted(public_vif["prefixes"]) == ["198.51.100.0/24", "203.0.113.0/24"]
    assert public_vif["peers"] == ["dxpeer-bbb222:down"]

    # Assert: virtual interfaces run on their connection.
    assert check_rels(
        neo4j_session,
        "AWSDirectConnectVirtualInterface",
        "id",
        "AWSDirectConnectConnection",
        "id",
        "RUNS_ON",
        rel_direction_right=True,
    ) == {
        ("dxvif-ffabc123", TEST_CONNECTION_ID),
        ("dxvif-ffdef456", TEST_CONNECTION_ID),
    }

    # Assert: only the transit VIF attaches to the Direct Connect gateway; the public one
    # carries no gateway and must not produce an edge.
    assert check_rels(
        neo4j_session,
        "AWSDirectConnectVirtualInterface",
        "id",
        "AWSDirectConnectGateway",
        "id",
        "ATTACHED_TO",
        rel_direction_right=True,
    ) == {("dxvif-ffabc123", TEST_DXGW_ID)}

    # Assert: the associations carry the prefixes reachable from on-premises.
    assert check_nodes(
        neo4j_session,
        "AWSDirectConnectGatewayAssociation",
        ["id", "associated_gateway_type", "associated_gateway_id"],
    ) == {
        ("dxgw-assoc-aaa111", "transitGateway", TEST_TGW_ID),
        ("dxgw-assoc-bbb222", "virtualPrivateGateway", "vgw-0123456789abcdef0"),
    }

    prefixes = neo4j_session.run(
        """
        MATCH (a:AWSDirectConnectGatewayAssociation{id: 'dxgw-assoc-aaa111'})
        RETURN a.allowed_prefixes AS prefixes
        """
    ).single()["prefixes"]
    assert sorted(prefixes) == ["10.0.0.0/16", "10.1.0.0/16"]

    # Assert: the transit gateway association reaches the Transit Gateway node. The virtual
    # private gateway association matches nothing, which is expected.
    assert check_rels(
        neo4j_session,
        "AWSDirectConnectGatewayAssociation",
        "id",
        "AWSTransitGateway",
        "tgw_id",
        "ATTACHED_TO",
        rel_direction_right=True,
    ) == {("dxgw-assoc-aaa111", TEST_TGW_ID)}

    # Assert: both associations hang off their Direct Connect gateway.
    assert check_rels(
        neo4j_session,
        "AWSDirectConnectGatewayAssociation",
        "id",
        "AWSDirectConnectGateway",
        "id",
        "ASSOCIATED_WITH",
        rel_direction_right=True,
    ) == {
        ("dxgw-assoc-aaa111", TEST_DXGW_ID),
        ("dxgw-assoc-bbb222", TEST_DXGW_ID),
    }
