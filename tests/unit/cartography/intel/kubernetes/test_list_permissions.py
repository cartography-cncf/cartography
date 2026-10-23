from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from kubernetes.client.exceptions import ApiException

from cartography.intel.kubernetes.ingress import sync_ingress
from cartography.intel.kubernetes.nodes import sync_nodes
from cartography.intel.kubernetes.services import sync_services

COMMON = {"CLUSTER_ID": "cluster-id", "UPDATE_TAG": 1}

SYNCS = [
    pytest.param(
        "cartography.intel.kubernetes.nodes",
        "get_nodes",
        "load_nodes",
        lambda client: sync_nodes(MagicMock(), client, 1, COMMON),
        {},
        id="nodes",
    ),
    pytest.param(
        "cartography.intel.kubernetes.services",
        "get_services",
        "load_services",
        lambda client: sync_services(MagicMock(), client, [], 1, COMMON),
        None,
        id="services",
    ),
    pytest.param(
        "cartography.intel.kubernetes.ingress",
        "get_ingress",
        "load_ingresses",
        lambda client: sync_ingress(MagicMock(), client, 1, COMMON),
        None,
        id="ingress",
    ),
]


@pytest.mark.parametrize("module,getter,loader,run,expected", SYNCS)
@pytest.mark.parametrize("status", [401, 403])
def test_forbidden_list_skips_load_and_cleanup(
    module, getter, loader, run, expected, status, caplog
):
    # Arrange
    client = MagicMock(gke_cluster=None)
    client.name = "my-cluster"

    # Act
    with (
        patch(f"{module}.{getter}", side_effect=ApiException(status=status)),
        patch(f"{module}.{loader}") as mock_load,
        patch(f"{module}.cleanup") as mock_cleanup,
        caplog.at_level("WARNING"),
    ):
        result = run(client)

    # Assert
    assert result == expected
    mock_load.assert_not_called()
    mock_cleanup.assert_not_called()
    assert any("lacks permission" in r.message for r in caplog.records)


@pytest.mark.parametrize("module,getter,loader,run,expected", SYNCS)
def test_other_list_errors_raise_without_cleanup(module, getter, loader, run, expected):
    # Arrange
    client = MagicMock(gke_cluster=None)
    client.name = "my-cluster"

    # Act and assert
    with (
        patch(f"{module}.{getter}", side_effect=ApiException(status=500)),
        patch(f"{module}.cleanup") as mock_cleanup,
        pytest.raises(ApiException),
    ):
        run(client)
    mock_cleanup.assert_not_called()
