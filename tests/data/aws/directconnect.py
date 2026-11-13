TEST_CONNECTION_ID = "dxcon-fg0123456789"
TEST_DXGW_ID = "11111111-2222-3333-4444-555555555555"
TEST_TGW_ID = "tgw-0123456789abcdef0"
TEST_VGW_ID = "vgw-0123456789abcdef0"

DESCRIBE_CONNECTIONS = [
    {
        "ownerAccount": "000000000000",
        "connectionId": TEST_CONNECTION_ID,
        "connectionName": "primary-cross-connect",
        "connectionState": "available",
        "region": "eu-west-1",
        "location": "EqLD5",
        "bandwidth": "1Gbps",
        "jumboFrameCapable": True,
        "hasLogicalRedundancy": "yes",
        "macSecCapable": True,
        "encryptionMode": "must_encrypt",
        "portEncryptionStatus": "Encryption Up",
        "awsDeviceV2": "EqLD5-abcdefgh",
        "providerName": "Example Telecom",
    },
]

DESCRIBE_DIRECT_CONNECT_GATEWAYS = [
    {
        "directConnectGatewayId": TEST_DXGW_ID,
        "directConnectGatewayName": "corp-dxgw",
        "amazonSideAsn": 64512,
        "ownerAccount": "000000000000",
        "directConnectGatewayState": "available",
    },
]

DESCRIBE_VIRTUAL_INTERFACES = [
    # A transit virtual interface attached to the Direct Connect gateway.
    {
        "ownerAccount": "000000000000",
        "virtualInterfaceId": "dxvif-ffabc123",
        "connectionId": TEST_CONNECTION_ID,
        "virtualInterfaceType": "transit",
        "virtualInterfaceName": "corp-transit-vif",
        "virtualInterfaceState": "available",
        "vlan": 101,
        "asn": 65001,
        "amazonSideAsn": 64512,
        "addressFamily": "ipv4",
        "amazonAddress": "169.254.0.1/30",
        "customerAddress": "169.254.0.2/30",
        "mtu": 8500,
        "directConnectGatewayId": TEST_DXGW_ID,
        "region": "eu-west-1",
        "routeFilterPrefixes": [],
        "bgpPeers": [
            {
                "bgpPeerId": "dxpeer-aaa111",
                "bgpStatus": "up",
                "bgpPeerState": "available",
            },
        ],
    },
    # A public virtual interface, which advertises prefixes rather than attaching to a gateway.
    {
        "ownerAccount": "000000000000",
        "virtualInterfaceId": "dxvif-ffdef456",
        "connectionId": TEST_CONNECTION_ID,
        "virtualInterfaceType": "public",
        "virtualInterfaceName": "corp-public-vif",
        "virtualInterfaceState": "available",
        "vlan": 102,
        "asn": 65001,
        "addressFamily": "ipv4",
        "region": "eu-west-1",
        "routeFilterPrefixes": [
            {"cidr": "203.0.113.0/24"},
            {"cidr": "198.51.100.0/24"},
        ],
        "bgpPeers": [
            {
                "bgpPeerId": "dxpeer-bbb222",
                "bgpStatus": "down",
                "bgpPeerState": "available",
            },
        ],
    },
]

DESCRIBE_DIRECT_CONNECT_GATEWAY_ASSOCIATIONS = [
    # Associated with a transit gateway: this is the edge that completes the on-premises path.
    {
        "directConnectGatewayId": TEST_DXGW_ID,
        "directConnectGatewayOwnerAccount": "000000000000",
        "associationState": "associated",
        "associationId": "dxgw-assoc-aaa111",
        "associatedGateway": {
            "id": TEST_TGW_ID,
            "type": "transitGateway",
            "ownerAccount": "000000000000",
            "region": "eu-west-1",
        },
        "allowedPrefixesToDirectConnectGateway": [
            {"cidr": "10.0.0.0/16"},
            {"cidr": "10.1.0.0/16"},
        ],
    },
    # Associated with a virtual private gateway, which matches no AWSTransitGateway node.
    {
        "directConnectGatewayId": TEST_DXGW_ID,
        "directConnectGatewayOwnerAccount": "000000000000",
        "associationState": "associated",
        "associationId": "dxgw-assoc-bbb222",
        "associatedGateway": {
            "id": TEST_VGW_ID,
            "type": "virtualPrivateGateway",
            "ownerAccount": "000000000000",
            "region": "eu-west-1",
        },
        "allowedPrefixesToDirectConnectGateway": [{"cidr": "172.16.0.0/12"}],
    },
]
