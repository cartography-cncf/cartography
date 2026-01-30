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
        "VpcId": "vpc-0f510",  # Reference by route tables
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
                "Ipv6CidrBlock": "2001:db8::/32",
                "Ipv6CidrBlockState": {"State": "associated"},
            }
        ],
        "IsDefault": False,
        "BlockPublicAccessStates": {"InternetGatewayBlockMode": "on"},
        "VpcId": "vpc-0a1b2",
        "State": "available",
        "CidrBlock": "2001:db8::/32",
        "DhcpOptionsId": "dopt-036d",
    },
    # Additional VPCs needed for relationship tests
    {
        "OwnerId": "12345",
        "InstanceTenancy": "default",
        "CidrBlockAssociationSet": [
            {
                "AssociationId": "vpc-cidr-assoc-security-groups",
                "CidrBlock": "10.0.0.0/16",
                "CidrBlockState": {"State": "associated"},
            }
        ],
        "IsDefault": False,
        "BlockPublicAccessStates": {"InternetGatewayBlockMode": "off"},
        "VpcId": "vpc-05326141848d1c681",  # Referenced by security groups
        "State": "available",
        "CidrBlock": "10.0.0.0/16",
        "DhcpOptionsId": "dopt-036d",
    },
    {
        "OwnerId": "12345",
        "InstanceTenancy": "default",
        "CidrBlockAssociationSet": [
            {
                "AssociationId": "vpc-cidr-assoc-network-acls",
                "CidrBlock": "192.168.0.0/16",
                "CidrBlockState": {"State": "associated"},
            }
        ],
        "IsDefault": False,
        "BlockPublicAccessStates": {"InternetGatewayBlockMode": "off"},
        "VpcId": "vpc-0767",  # Referenced by network ACLs
        "State": "available",
        "CidrBlock": "192.168.0.0/16",
        "DhcpOptionsId": "dopt-036d",
    },
    {
        "OwnerId": "12345",
        "InstanceTenancy": "default",
        "CidrBlockAssociationSet": [
            {
                "AssociationId": "vpc-cidr-assoc-subnets",
                "CidrBlock": "172.16.0.0/16",
                "CidrBlockState": {"State": "associated"},
            }
        ],
        "IsDefault": False,
        "BlockPublicAccessStates": {"InternetGatewayBlockMode": "off"},
        "VpcId": "vpc-025873e026b9e8ee6",  # Referenced by subnets and security groups
        "State": "available",
        "CidrBlock": "172.16.0.0/16",
        "DhcpOptionsId": "dopt-036d",
    },
]
