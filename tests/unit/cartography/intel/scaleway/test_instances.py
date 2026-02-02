from copy import deepcopy

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


def test_transform_instances_no_public_ips():
    """Test transform when public_ips is None or empty."""
    server_no_ips = _make_server(public_ips=None)
    result = transform_instances([server_no_ips])

    instance = result["0681c477-fbb9-4820-b8d6-0eef10cfcd6d"][0]
    assert instance["public_ips"] == []


def test_transform_instances_empty_public_ips():
    """Test transform when public_ips is an empty list."""
    server_empty_ips = _make_server(public_ips=[])
    result = transform_instances([server_empty_ips])

    instance = result["0681c477-fbb9-4820-b8d6-0eef10cfcd6d"][0]
    assert instance["public_ips"] == []


def test_transform_instances_no_volumes():
    """Test transform when volumes is None or empty."""
    server_no_volumes = _make_server(volumes=None)
    result = transform_instances([server_no_volumes])

    instance = result["0681c477-fbb9-4820-b8d6-0eef10cfcd6d"][0]
    assert instance["volumes_id"] == []


def test_transform_instances_no_private_nics():
    """Test transform when private_nics is None."""
    server_no_nics = _make_server(private_nics=None)
    result = transform_instances([server_no_nics])

    instance = result["0681c477-fbb9-4820-b8d6-0eef10cfcd6d"][0]
    assert instance["private_nics"] == []
