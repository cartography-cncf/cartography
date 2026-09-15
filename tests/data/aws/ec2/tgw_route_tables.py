"""
Shaped like the real boto3 EC2 API responses.

DescribeTransitGatewayRouteTables never includes a Routes field, so routes
are fetched separately per route table via SearchTransitGatewayRoutes.
"""

TRANSIT_GATEWAY_ROUTE_TABLES = [
    {
        "TransitGatewayRouteTableId": "tgw-rtb-0123456789abcdef0",
        "TransitGatewayId": "tgw-0123456789abcdef0",
        "State": "available",
    },
]

# SearchTransitGatewayRoutes response ("Routes" list) for the route table above.
TRANSIT_GATEWAY_ROUTES = [
    {
        "DestinationCidrBlock": "10.0.0.0/16",
        "State": "active",
        "TransitGatewayAttachments": [
            {
                "TransitGatewayAttachmentId": "tgw-attach-aaaabbbbccccdef01",
                "ResourceId": "vpc-16719ae825ca14e92",
                "ResourceType": "vpc",
            },
        ],
    },
    {
        "DestinationCidrBlock": "10.1.0.0/16",
        "State": "blackhole",
        "TransitGatewayAttachments": [],
    },
]

# GetTransitGatewayRouteTableAssociations response ("Associations" list).
# The API does not echo back TransitGatewayRouteTableId or an association id;
# the fetch function injects TransitGatewayRouteTableId and synthesizes
# TransitGatewayRouteTableAssociationId, so those fields are absent here to
# match the real response shape.
TRANSIT_GATEWAY_ROUTE_TABLE_ASSOCIATIONS = [
    {
        "TransitGatewayAttachmentId": "tgw-attach-aaaabbbbccccdef01",
        "ResourceId": "vpc-16719ae825ca14e92",
        "ResourceType": "vpc",
        "State": "associated",
    },
]

# GetTransitGatewayRouteTablePropagations response
# ("TransitGatewayRouteTablePropagations" list). Same shape caveat as
# associations above.
TRANSIT_GATEWAY_ROUTE_TABLE_PROPAGATIONS = [
    {
        "TransitGatewayAttachmentId": "tgw-attach-aaaabbbbccccdef01",
        "ResourceId": "vpc-16719ae825ca14e92",
        "ResourceType": "vpc",
        "State": "enabled",
    },
]
