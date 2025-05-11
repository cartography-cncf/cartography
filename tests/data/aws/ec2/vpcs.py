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
]
