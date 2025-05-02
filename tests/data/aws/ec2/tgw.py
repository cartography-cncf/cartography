import datetime

TRANSIT_GATEWAYS = [
    {
        "TransitGatewayId": "tgw-0123456789abcdef0",
        "TransitGatewayArn": "arn:aws:ec2:eu-west-1:000000000000:transit-gateway/tgw-0123456789abcdef0",
        "State": "available",
        "OwnerId": "000000000000",
        "Description": "Test Transit Gateway",
        "CreationTime": datetime.datetime(2019, 4, 17, 16, 37, 21),
        "Options": {
            "AmazonSideAsn": 64512,
            "AutoAcceptSharedAttachments": "disable",
            "DefaultRouteTableAssociation": "enable",
            "AssociationDefaultRouteTableId": "tgw-rtb-0123456789abcdef0",
            "DefaultRouteTablePropagation": "enable",
            "PropagationDefaultRouteTableId": "tgw-rtb-0123456789abcdef0",
            "VpnEcmpSupport": "enable",
            "DnsSupport": "enable",
        },
        "Tags": [
            {
                "Key": "Name",
                "Value": "test transit gateway",
            },
        ],
    },
]

TRANSIT_GATEWAY_ATTACHMENTS = [
    {
        "TransitGatewayAttachmentId": "tgw-attach-aaaabbbbccccdef01",
        "TransitGatewayId": "tgw-0123456789abcdef0",
        "TransitGatewayOwnerId": "000000000000",
        "ResourceOwnerId": "000000000000",
        "ResourceType": "vpc",
        "ResourceId": "vpc-16719ae825ca14e92",
        "State": "available",
        "Association": {
            "TransitGatewayRouteTableId": "tgw-rtb-00000000000000000",
            "State": "associated",
        },
        "CreationTime": datetime.datetime(2019, 6, 25, 14, 42, 44),
        "Tags": [
            {
                "Key": "Name",
                "Value": "tgw attachment test",
            },
        ],
    },
]

TGW_VPC_ATTACHMENTS = [
    {
        "TransitGatewayAttachmentId": "tgw-attach-aaaabbbbccccdef01",
        "TransitGatewayId": "tgw-0123456789abcdef0",
        "VpcId": "vpc-16719ae825ca14e92",
        "VpcOwnerId": "000000000000",
        "State": "available",
        "SubnetIds": [
            "subnet-62ddf961dc3c54bd3",
            "subnet-56ccdcb90a86e0ce8",
            "subnet-3236c10861031f362",
        ],
        "CreationTime": datetime.datetime(2019, 6, 25, 14, 42, 44),
        "Options": {
            "DnsSupport": "enable",
            "Ipv6Support": "disable",
        },
        "Tags": [
            {
                "Key": "Name",
                "Value": "tgw attachment test",
            },
        ],
    },
]
