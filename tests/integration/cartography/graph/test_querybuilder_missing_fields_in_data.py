from cartography.client.core.tx import load
from tests.data.graph.querybuilder.sample_data.simple_node_missing_fields import (
    SIMPLE_NODE_MISSING_PROPS,
)
from tests.data.graph.querybuilder.sample_models.simple_node import SimpleNodeSchema
from tests.integration.util import check_nodes


def test_load_missing_fields_in_data(neo4j_session):
    # Act: load our sample data where some items only have `property1` defined and other items only have `property2`
    # defined. `SimpleNodeSchema` includes both `property1` and `property2`.
    load(neo4j_session, SimpleNodeSchema(), SIMPLE_NODE_MISSING_PROPS, lastupdated=1)

    # Assert that if we ingest a dict that has fewer fields than defined on the node schema, then the missing fields
    # will be treated as None.
    assert check_nodes(neo4j_session, "SimpleNode", ["property1", "property2"]) == {
        ("The", None),
        (None, "Quick"),
        ("Brown", None),
        (None, "Fox"),
    }
