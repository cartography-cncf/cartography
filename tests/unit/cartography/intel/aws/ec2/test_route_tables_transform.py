from cartography.intel.aws.ec2.route_tables import transform_route_table_data


def test_transform_route_table_with_vpc_endpoint_gateway():
    """Test that VPC endpoint IDs are extracted from GatewayId when routing to VPC endpoint"""
    route_tables = [
        {
            "RouteTableId": "rtb-12345",
            "OwnerId": "123456789012",
            "VpcId": "vpc-12345",
            "Routes": [
                {
                    "DestinationPrefixListId": "pl-63a5400a",
                    "GatewayId": "vpce-0bb6d13007d949b82",  # VPC endpoint ID in GatewayId field
                    "State": "active",
                    "Origin": "CreateRoute",
                },
                {
                    "DestinationCidrBlock": "0.0.0.0/0",
                    "GatewayId": "igw-12345",  # Regular internet gateway
                    "State": "active",
                    "Origin": "CreateRoute",
                },
            ],
            "Associations": [],
        }
    ]

    tables, associations, routes = transform_route_table_data(route_tables)

    assert len(routes) == 2

    # First route should extract vpc_endpoint_id from gateway_id
    vpc_endpoint_route = [
        r for r in routes if r.get("gateway_id", "").startswith("vpce-")
    ][0]
    assert vpc_endpoint_route["gateway_id"] == "vpce-0bb6d13007d949b82"
    assert vpc_endpoint_route["vpc_endpoint_id"] == "vpce-0bb6d13007d949b82"
    assert vpc_endpoint_route["destination_prefix_list_id"] == "pl-63a5400a"

    # Second route should not have vpc_endpoint_id
    igw_route = [r for r in routes if r.get("gateway_id") == "igw-12345"][0]
    assert igw_route["gateway_id"] == "igw-12345"
    assert igw_route["vpc_endpoint_id"] is None
    assert igw_route["destination_cidr_block"] == "0.0.0.0/0"


def test_transform_route_table_without_vpc_endpoint():
    """Test route transformation when there are no VPC endpoints"""
    route_tables = [
        {
            "RouteTableId": "rtb-12345",
            "OwnerId": "123456789012",
            "VpcId": "vpc-12345",
            "Routes": [
                {
                    "DestinationCidrBlock": "10.0.0.0/16",
                    "GatewayId": "local",
                    "State": "active",
                    "Origin": "CreateRouteTable",
                },
                {
                    "DestinationCidrBlock": "0.0.0.0/0",
                    "NatGatewayId": "nat-12345",
                    "State": "active",
                    "Origin": "CreateRoute",
                },
            ],
            "Associations": [],
        }
    ]

    tables, associations, routes = transform_route_table_data(route_tables)

    assert len(routes) == 2

    # Neither route should have vpc_endpoint_id
    for route in routes:
        assert route["vpc_endpoint_id"] is None


def test_transform_route_table_edge_cases():
    """Test edge cases in route transformation"""
    route_tables = [
        {
            "RouteTableId": "rtb-edge",
            "OwnerId": "123456789012",
            "VpcId": "vpc-12345",
            "Routes": [
                {
                    # Gateway ID is None
                    "DestinationCidrBlock": "10.0.0.0/16",
                    "State": "active",
                },
                {
                    # Gateway ID is empty string
                    "DestinationCidrBlock": "172.16.0.0/12",
                    "GatewayId": "",
                    "State": "blackhole",
                },
            ],
            "Associations": [],
        }
    ]

    tables, associations, routes = transform_route_table_data(route_tables)

    assert len(routes) == 2

    # Both should have vpc_endpoint_id as None
    for route in routes:
        assert route["vpc_endpoint_id"] is None
