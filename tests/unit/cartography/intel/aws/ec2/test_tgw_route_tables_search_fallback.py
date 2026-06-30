import boto3

from cartography.intel.aws.ec2 import tgw_route_tables


def test_search_fallback_used(monkeypatch):
    # Patch describe to return a route table without 'Routes'
    def fake_get_rts(boto3_session, region):
        return [
            {
                "TransitGatewayRouteTableId": "tgw-rtb-test",
                "TransitGatewayId": "tgw-test",
                "State": "available",
                "Region": region,
            }
        ]

    # Patch search to return a single route for that table
    def fake_search_routes(boto3_session, region, route_table_id):
        assert route_table_id == "tgw-rtb-test"
        return [
            {
                "DestinationCidrBlock": "10.0.0.0/16",
                "State": "active",
                "Origin": "Create",
                "TransitGatewayAttachmentId": "tgw-attach-test",
            }
        ]

    called = {}

    def fake_load_routes(neo4j_session, data, region, aws_id, update_tag):
        # record that load_transit_gateway_routes was invoked and capture data
        called['loaded_routes'] = data
        called['region'] = region
        called['aws_id'] = aws_id
        called['update_tag'] = update_tag

    def fake_load_rtbs(neo4j_session, data, region, aws_id, update_tag):
        called['loaded_rtbs'] = data

    # Apply monkeypatches
    monkeypatch.setattr(tgw_route_tables, 'get_transit_gateway_route_tables', fake_get_rts)
    monkeypatch.setattr(tgw_route_tables, 'get_transit_gateway_routes_for_table', fake_search_routes)
    monkeypatch.setattr(tgw_route_tables, 'load_transit_gateway_routes', fake_load_routes)
    monkeypatch.setattr(tgw_route_tables, 'load_transit_gateway_route_tables', fake_load_rtbs)
    # Prevent cleanup from running against a fake neo4j session
    monkeypatch.setattr(tgw_route_tables, 'cleanup_transit_gateway_route_tables', lambda session, common: None)

    # Call sync (boto3_session not used by our fake_get_rts)
    tgw_route_tables.sync_transit_gateway_route_tables(
        neo4j_session=object(),
        boto3_session=boto3.Session(),
        regions=["us-east-1"],
        current_aws_account_id="000000000000",
        update_tag=123,
        common_job_parameters={"AWS_ID": "000000000000", "UPDATE_TAG": 123},
    )

    # Assertions
    assert 'loaded_routes' in called
    assert len(called['loaded_routes']) == 1
    assert called['loaded_routes'][0]['destination_cidr_block'] == '10.0.0.0/16'
    assert called['region'] == 'us-east-1'
    assert called['aws_id'] == '000000000000'
    assert called['update_tag'] == 123
