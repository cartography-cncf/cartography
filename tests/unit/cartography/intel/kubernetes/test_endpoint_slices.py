from copy import deepcopy
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from kubernetes.client.exceptions import ApiException

import cartography.intel.kubernetes.endpoint_slices as endpoint_slices_module
from cartography.intel.kubernetes.endpoint_slices import get_endpoint_slice_data
from cartography.intel.kubernetes.endpoint_slices import (
    service_pod_ids_by_qualified_name,
)
from cartography.intel.kubernetes.endpoint_slices import transform_endpoint_slices
from tests.data.kubernetes.endpoint_slices import KUBERNETES_ENDPOINT_SLICES_RAW
from tests.data.kubernetes.endpoint_slices import NAMESPACE
from tests.data.kubernetes.endpoint_slices import SERVICE_NAME
from tests.data.kubernetes.pods import KUBERNETES_PODS_DATA


def test_transform_endpoint_slices_uses_ready_pod_targets():
    [endpoint_slice] = transform_endpoint_slices(KUBERNETES_ENDPOINT_SLICES_RAW)

    assert endpoint_slice["service_qualified_name"] == f"{NAMESPACE}/{SERVICE_NAME}"
    assert endpoint_slice["ready_pod_ids"] == [KUBERNETES_PODS_DATA[0]["uid"]]
    assert endpoint_slice["port_numbers"] == [8080]
    assert endpoint_slice["port_keys"] == ["TCP/8080"]
    assert service_pod_ids_by_qualified_name([endpoint_slice]) == {
        f"{NAMESPACE}/{SERVICE_NAME}": [KUBERNETES_PODS_DATA[0]["uid"]]
    }


def test_transform_endpoint_slice_without_service_label():
    raw = deepcopy(KUBERNETES_ENDPOINT_SLICES_RAW)
    raw[0].metadata.labels.pop("kubernetes.io/service-name")

    [endpoint_slice] = transform_endpoint_slices(raw)

    assert endpoint_slice["service_qualified_name"] is None


def test_transform_endpoint_slice_defaults_protocol_to_tcp():
    raw = deepcopy(KUBERNETES_ENDPOINT_SLICES_RAW)
    raw[0].ports[0].protocol = None

    [endpoint_slice] = transform_endpoint_slices(raw)

    assert endpoint_slice["port_keys"] == ["TCP/8080"]


@pytest.mark.parametrize("status", [401, 403, 404, 500])
@patch.object(endpoint_slices_module, "get_endpoint_slices")
def test_get_endpoint_slice_data_falls_back_on_permission_and_transient_errors(
    mock_get_endpoint_slices,
    status,
):
    client = MagicMock()
    client.name = "example-cluster"
    mock_get_endpoint_slices.side_effect = ApiException(status=status)

    assert get_endpoint_slice_data(client) is None


@patch.object(endpoint_slices_module, "get_endpoint_slices")
def test_get_endpoint_slice_data_propagates_non_transient_api_errors(
    mock_get_endpoint_slices,
):
    client = MagicMock()
    mock_get_endpoint_slices.side_effect = ApiException(status=400)

    with pytest.raises(ApiException):
        get_endpoint_slice_data(client)
