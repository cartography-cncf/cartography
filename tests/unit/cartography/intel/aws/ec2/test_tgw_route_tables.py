import pytest

from cartography.intel.aws.ec2 import tgw_route_tables


def test_transform_tgw_route_tables_empty():
    rts, routes = tgw_route_tables.transform_tgw_route_tables([])
    assert rts == []
    assert routes == []


def test_transform_tgw_route_tables_sample():
    sample = [
        {
            "TransitGatewayRouteTableId": "tgw-rtb-1",
            "TransitGatewayId": "tgw-1",
            "State": "available",
            "Region": "us-east-1",
            "Routes": [
                {
                    "DestinationCidrBlock": "10.0.0.0/16",
                    "State": "active",
                    "Origin": "Create",
                    "TransitGatewayAttachmentId": "tgw-attach-1",
                }
            ],
        }
    ]
    rts, routes = tgw_route_tables.transform_tgw_route_tables(sample)
    assert len(rts) == 1
    assert len(routes) == 1
    assert rts[0]["TransitGatewayRouteTableId"] == "tgw-rtb-1"
    assert routes[0]["destination_cidr_block"] == "10.0.0.0/16"
