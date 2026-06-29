import pytest

from cartography.intel.aws.ec2 import tgw_route_tables


def test_load_transit_gateway_routes_calls_load(monkeypatch):
    called = {}

    def fake_load(neo4j_session, schema, data, **kwargs):
        called["neo4j_session"] = neo4j_session
        called["schema_label"] = getattr(schema, "label", None)
        called["data"] = data
        called["kwargs"] = kwargs

    # Patch the load function used by the module
    monkeypatch.setattr(tgw_route_tables, "load", fake_load)

    sess = object()
    sample_data = [
        {
            "id": "rt1",
            "transit_gateway_route_table_id": "rtb-1",
            "destination_cidr_block": "10.0.0.0/16",
            "Region": "us-east-1",
        }
    ]

    tgw_route_tables.load_transit_gateway_routes(
        sess, sample_data, "us-east-1", "000000000000", 12345
    )

    assert called.get("neo4j_session") is sess
    assert called.get("schema_label") == "AWSTransitGatewayRoute"
    assert called.get("data") is sample_data
    assert called.get("kwargs")["AWS_ID"] == "000000000000"
    assert called.get("kwargs")["lastupdated"] == 12345


def test_cleanup_transit_gateway_route_tables_calls_graphjob(monkeypatch):
    runs = []

    class DummyJob:
        def __init__(self, schema, common):
            self.schema = schema
            self.common = common

        def run(self, sess):
            runs.append(sess)

    def fake_from_node_schema(schema, common):
        return DummyJob(schema, common)

    # Patch GraphJob.from_node_schema to return a DummyJob instance
    monkeypatch.setattr(
        tgw_route_tables.GraphJob, "from_node_schema", staticmethod(fake_from_node_schema)
    )

    sess = object()
    common = {"AWS_ID": "000000000000", "UPDATE_TAG": 12345}

    tgw_route_tables.cleanup_transit_gateway_route_tables(sess, common)

    # cleanup should have invoked run() twice: once for route tables and once for routes
    assert len(runs) == 2
    assert runs[0] is sess
    assert runs[1] is sess
