TEST_NAT_GATEWAYS = [
    {
        "NatGatewayId": "nat-0abc1234567890001",
        "SubnetId": "subnet-0773409557644dca4",
        "VpcId": "vpc-025873e026b9e8ee6",
        "State": "available",
        "CreateTime": "2021-01-01T00:00:00+00:00",
        "ConnectivityType": "public",
        "NatGatewayAddresses": [
            {
                "AllocationId": "eipalloc-00000000000000000",
                "NetworkInterfaceId": "eni-0abc1234567890001",
                "PrivateIp": "10.1.1.100",
                "PublicIp": "192.168.1.1",
                "AssociationId": "eipassoc-00000000000000001",
            },
        ],
    },
    {
        "NatGatewayId": "nat-0def1234567890002",
        "SubnetId": "subnet-020b2f3928f190ce8",
        "VpcId": "vpc-025873e026b9e8ee6",
        "State": "available",
        "CreateTime": "2021-02-01T00:00:00+00:00",
        "ConnectivityType": "public",
        "NatGatewayAddresses": [
            {
                "AllocationId": "eipalloc-00000000000000002",
                "NetworkInterfaceId": "eni-0def1234567890002",
                "PrivateIp": "10.1.2.100",
                "PublicIp": "192.168.1.2",
                "AssociationId": "eipassoc-00000000000000002",
            },
        ],
    },
    {
        # Private NAT gateway — no NatGatewayAddresses
        "NatGatewayId": "nat-0prv1234567890003",
        "SubnetId": "subnet-0fa9c8fa7cb241479",
        "VpcId": "vpc-05326141848d1c681",
        "State": "available",
        "CreateTime": "2021-03-01T00:00:00+00:00",
        "ConnectivityType": "private",
        "NatGatewayAddresses": [],
    },
]
