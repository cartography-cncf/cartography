from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from kubernetes.client.exceptions import ApiException

import cartography.intel.kubernetes.storage as storage_module
from cartography.intel.kubernetes.storage import sync_storage
from tests.data.kubernetes.storage import RAW_PERSISTENT_VOLUME_CLAIMS
from tests.data.kubernetes.storage import RAW_PERSISTENT_VOLUMES
from tests.data.kubernetes.storage import RAW_STORAGE_CLASSES

TEST_UPDATE_TAG = 123456789
CLUSTER_ID = "my-cluster-id"
CLUSTER_NAME = "my-cluster"


def test_transform_persistent_volume_claim_without_requests():
    # Arrange
    claim = deepcopy(RAW_PERSISTENT_VOLUME_CLAIMS[0])
    claim.spec.resources.requests = None

    # Act
    result = storage_module.transform_persistent_volume_claims([claim], CLUSTER_NAME)

    # Assert
    assert result[0]["requested_storage"] is None


def test_transform_persistent_volume_claim_rounds_fractional_bytes_up():
    # Arrange
    claim = deepcopy(RAW_PERSISTENT_VOLUME_CLAIMS[0])
    claim.spec.resources.requests = {"storage": "400m"}

    # Act
    result = storage_module.transform_persistent_volume_claims([claim], CLUSTER_NAME)

    # Assert
    assert result[0]["requested_storage_bytes"] == 1


@pytest.mark.parametrize(
    ("getter_name", "status"),
    (
        ("get_storage_classes", 401),
        ("get_storage_classes", 403),
        ("get_storage_classes", 500),
        ("get_persistent_volumes", 401),
        ("get_persistent_volumes", 403),
        ("get_persistent_volumes", 500),
        ("get_persistent_volume_claims", 401),
        ("get_persistent_volume_claims", 403),
        ("get_persistent_volume_claims", 500),
    ),
    ids=[
        "storage_classes-401",
        "storage_classes-403",
        "storage_classes-500",
        "persistent_volumes-401",
        "persistent_volumes-403",
        "persistent_volumes-500",
        "persistent_volume_claims-401",
        "persistent_volume_claims-403",
        "persistent_volume_claims-500",
    ],
)
@patch.object(storage_module, "cleanup")
@patch.object(storage_module, "load_storage")
@patch.object(
    storage_module,
    "get_persistent_volume_claims",
    return_value=RAW_PERSISTENT_VOLUME_CLAIMS,
)
@patch.object(
    storage_module,
    "get_persistent_volumes",
    return_value=RAW_PERSISTENT_VOLUMES,
)
@patch.object(
    storage_module,
    "get_storage_classes",
    return_value=RAW_STORAGE_CLASSES,
)
def test_sync_storage_skips_load_and_cleanup_on_api_error(
    mock_get_storage_classes,
    mock_get_persistent_volumes,
    mock_get_persistent_volume_claims,
    mock_load_storage,
    mock_cleanup,
    getter_name,
    status,
):
    # Arrange
    getters = {
        "get_storage_classes": mock_get_storage_classes,
        "get_persistent_volumes": mock_get_persistent_volumes,
        "get_persistent_volume_claims": mock_get_persistent_volume_claims,
    }
    getters[getter_name].side_effect = ApiException(status=status)
    client = SimpleNamespace(name=CLUSTER_NAME)

    # Act
    sync_storage(
        MagicMock(),
        client,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": CLUSTER_ID},
    )

    # Assert
    getters[getter_name].assert_called_once_with(client)
    mock_load_storage.assert_not_called()
    mock_cleanup.assert_not_called()


def test_sync_storage_raises_unexpected_api_error(monkeypatch):
    # Arrange
    monkeypatch.setattr(
        storage_module,
        "get_storage_classes",
        lambda client: (_ for _ in ()).throw(ApiException(status=400)),
    )

    # Act / Assert
    with pytest.raises(ApiException):
        sync_storage(
            MagicMock(),
            SimpleNamespace(name=CLUSTER_NAME),
            TEST_UPDATE_TAG,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": CLUSTER_ID},
        )
