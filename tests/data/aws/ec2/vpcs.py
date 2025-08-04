TEST_VPCS = [
    {
        "OwnerId": "12345",
        "InstanceTenancy": "default",
        "CidrBlockAssociationSet": [
            {
                "AssociationId": "vpc-cidr-assoc-0daea",
                "CidrBlock": "172.31.0.0/16",
                "CidrBlockState": {"State": "associated"},
            }
        ],
        "IsDefault": True,
        "BlockPublicAccessStates": {"InternetGatewayBlockMode": "off"},
        "VpcId": "vpc-038cf",
        "State": "available",
        "CidrBlock": "172.31.0.0/16",
        "DhcpOptionsId": "dopt-036d",
    },
    {
        "OwnerId": "12345",
        "InstanceTenancy": "default",
        "CidrBlockAssociationSet": [
            {
                "AssociationId": "vpc-cidr-assoc-087ee",
                "CidrBlock": "10.1.0.0/16",
                "CidrBlockState": {"State": "associated"},
            }
        ],
        "IsDefault": False,
        "BlockPublicAccessStates": {"InternetGatewayBlockMode": "off"},
        "VpcId": "vpc-0f510",
        "State": "available",
        "CidrBlock": "10.1.0.0/16",
        "DhcpOptionsId": "dopt-036d",
    },
    {
        "OwnerId": "12345",
        "InstanceTenancy": "default",
        "Ipv6CidrBlockAssociationSet": [
            {
                "AssociationId": "vpc-ipv6-cidr-assoc-0a1b2",
                "Ipv6CidrBlock": "10.2.0.0/16",
                "Ipv6CidrBlockState": {"State": "associated"},
            }
        ],
        "IsDefault": False,
        "BlockPublicAccessStates": {"InternetGatewayBlockMode": "on"},
        "VpcId": "vpc-0a1b2",
        "State": "available",
        "CidrBlock": "10.2.0.0/16",
        "DhcpOptionsId": "dopt-036d",
    },
]
