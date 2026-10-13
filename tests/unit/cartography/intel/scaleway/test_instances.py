from copy import deepcopy

import pytest
from scaleway.instance.v1 import Server

from cartography.intel.scaleway.instances.instances import transform_instances
from tests.data.scaleway.instances import SCALEWAY_INSTANCES


def _make_server(**overrides) -> Server:
    """Create a copy of the test server with field overrides."""
    base = deepcopy(SCALEWAY_INSTANCES[0])
    for key, value in overrides.items():
        setattr(base, key, value)
    return base


def test_transform_instances_with_data():
    """Test transform with the default test data (has public_ips, volumes, empty private_nics)."""
    result = transform_instances(SCALEWAY_INSTANCES)

    assert "0681c477-fbb9-4820-b8d6-0eef10cfcd6d" in result
    instances = result["0681c477-fbb9-4820-b8d6-0eef10cfcd6d"]
    assert len(instances) == 1

    instance = instances[0]
    assert instance["id"] == "345627e9-18ff-47e0-b73d-3f38fddb4390"
    assert instance["name"] == "demo-server"
    assert instance["volumes_id"] == ["7c37b328-247c-4668-8ee1-701a3a3cc2e4"]


@pytest.mark.parametrize(
    "field,value,out_key",
    [
        ("public_ips", None, "public_ips"),
        ("public_ips", [], "public_ips"),
        ("volumes", None, "volumes_id"),
        ("private_nics", None, "private_nics"),
    ],
    ids=["public_ips_none", "public_ips_empty", "volumes_none", "private_nics_none"],
)
def test_transform_instances_missing_collection_field(field, value, out_key):
    """Test transform yields [] when a collection field on the server is None or empty."""
    server = _make_server(**{field: value})
    result = transform_instances([server])

    instance = result["0681c477-fbb9-4820-b8d6-0eef10cfcd6d"][0]
    assert instance[out_key] == []
