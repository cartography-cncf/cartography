import pytest

from cartography.config import Config
from cartography.intel.cloudflare import start_cloudflare_ingestion
from cartography.intel.cloudflare.firewallrules import transform


def test_start_cloudflare_ingestion_requires_token():
    config = Config(neo4j_uri="bolt://localhost:7687")

    with pytest.raises(RuntimeError, match="Cloudflare import is not configured"):
        start_cloudflare_ingestion(None, config)


def test_transform_flattens_filter_into_rule_properties():
    # Arrange
    data = [
        {
            "id": "rule1",
            "action": "block",
            "filter": {
                "id": "filter1",
                "description": "my filter",
                "expression": "ip.src eq 1.2.3.4",
                "paused": False,
                "ref": "FILTER1",
            },
        },
        {
            "id": "rule2",
            "action": "allow",
            "filter": None,
        },
    ]

    # Act
    transformed = transform(data)

    # Assert
    assert transformed[0] == {
        "id": "rule1",
        "action": "block",
        "filter_id": "filter1",
        "filter_description": "my filter",
        "filter_expression": "ip.src eq 1.2.3.4",
        "filter_paused": False,
        "filter_ref": "FILTER1",
    }
    assert "filter" not in transformed[0]
    assert transformed[1] == {
        "id": "rule2",
        "action": "allow",
        "filter_id": None,
        "filter_description": None,
        "filter_expression": None,
        "filter_paused": None,
        "filter_ref": None,
    }
    assert "filter" not in transformed[1]
