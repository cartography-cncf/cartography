DESCRIBE_ROUTE_TABLES = {
    "RouteTables": [
        {
            "Associations": [
                {
                    "Main": True,
                    "RouteTableAssociationId": "rtbassoc-aaaaaaaaaaaaaaaaa",
                    "RouteTableId": "rtb-aaaaaaaaaaaaaaaaa",
                    "AssociationState": {
                        "State": "associated"
                    }
                }
            ],
            "PropagatingVgws": [],
            "RouteTableId": "rtb-aaaaaaaaaaaaaaaaa",
            "Routes": [
                {
                    "DestinationCidrBlock": "172.31.0.0/16",
                    "GatewayId": "local",
                    "Origin": "CreateRouteTable",
                    "State": "active"
                },
                {
                    "DestinationCidrBlock": "0.0.0.0/0",
                    "GatewayId": "igw-aaaaaaaaaaaaaaaaa",
                    "Origin": "CreateRoute",
                    "State": "active"
                }
            ],
            "Tags": [],
            "VpcId": "vpc-aaaaaaaaaaaaaaaaa",
            "OwnerId": "000000000000"
        },
        {
            "Associations": [
                {
                    "Main": False,
                    "RouteTableAssociationId": "rtbassoc-bbbbbbbbbbbbbbbbb",
                    "RouteTableId": "rtb-bbbbbbbbbbbbbbbbb",
                    "SubnetId": "subnet-aaaaaaaaaaaaaaaaa",
                    "AssociationState": {
                        "State": "associated"
                    }
                },
                {
                    "Main": False,
                    "RouteTableAssociationId": "rtbassoc-ccccccccccccccccc",
                    "RouteTableId": "rtb-bbbbbbbbbbbbbbbbb",
                    "SubnetId": "subnet-bbbbbbbbbbbbbbbbb",
                    "AssociationState": {
                        "State": "associated"
                    }
                }
            ],
            "PropagatingVgws": [],
            "RouteTableId": "rtb-bbbbbbbbbbbbbbbbb",
            "Routes": [
                {
                    "DestinationCidrBlock": "10.1.0.0/16",
                    "GatewayId": "local",
                    "Origin": "CreateRouteTable",
                    "State": "active"
                },
                {
                    "DestinationCidrBlock": "0.0.0.0/0",
                    "GatewayId": "igw-bbbbbbbbbbbbbbbbb",
                    "Origin": "CreateRoute",
                    "State": "active"
                }
            ],
            "Tags": [
                {
                    "Key": "Customer",
                    "Value": "subimage"
                },
                {
                    "Key": "Environment",
                    "Value": "staging"
                },
                {
                    "Key": "Name",
                    "Value": "subimage-public"
                },
                {
                    "Key": "ManagedBy",
                    "Value": "terraform"
                }
            ],
            "VpcId": "vpc-bbbbbbbbbbbbbbbbb",
            "OwnerId": "000000000000"
        }
    ]
} 