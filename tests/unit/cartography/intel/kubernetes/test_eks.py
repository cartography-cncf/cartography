from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from botocore.exceptions import ClientError
from kubernetes.client.models import V1ConfigMap

from cartography.intel.kubernetes import eks

EXAMPLE_CLUSTER_NAME = "example-cluster"
TEST_REGION = "us-west-2"
TEST_UPDATE_TAG = 123456789
TEST_CLUSTER_ID = "example-cluster-id"


def _list_access_entries_client_error(code: str, message: str) -> ClientError:
    return ClientError(
        {"Error": {"Code": code, "Message": message}},
        "ListAccessEntries",
    )


def _eks_client_with_list_access_entries_error(error: ClientError):
    mock_paginator = MagicMock()
    mock_paginator.paginate.side_effect = error

    mock_eks_client = MagicMock()
    mock_eks_client.get_paginator.return_value = mock_paginator
    return mock_eks_client


def test_list_access_entry_principal_arns_skips_config_map_auth_mode(caplog):
    error = _list_access_entries_client_error(
        "InvalidRequestException",
        "The cluster's authentication mode must be set to one of "
        "[API, API_AND_CONFIG_MAP] to perform this operation.",
    )
    mock_eks_client = _eks_client_with_list_access_entries_error(error)

    with caplog.at_level("INFO"):
        result = eks._list_access_entry_principal_arns(
            mock_eks_client,
            EXAMPLE_CLUSTER_NAME,
        )

    assert result == []
    assert any(
        "EKS Access Entries are unavailable" in record.message
        for record in caplog.records
    )


def test_list_access_entry_principal_arns_raises_unexpected_invalid_request():
    error = _list_access_entries_client_error(
        "InvalidRequestException",
        "The cluster is not in a valid state for this request.",
    )
    mock_eks_client = _eks_client_with_list_access_entries_error(error)

    with pytest.raises(ClientError):
        eks._list_access_entry_principal_arns(
            mock_eks_client,
            EXAMPLE_CLUSTER_NAME,
        )


@patch("cartography.intel.kubernetes.eks.cleanup")
@patch("cartography.intel.kubernetes.eks.get_oidc_provider", return_value=[])
@patch("cartography.intel.kubernetes.eks.get_access_entries", return_value=[])
def test_sync_continues_to_oidc_when_access_entries_are_unavailable(
    mock_get_access_entries,
    mock_get_oidc_provider,
    mock_cleanup,
):
    mock_k8s_client = MagicMock()
    mock_k8s_client.name = EXAMPLE_CLUSTER_NAME
    mock_k8s_client.core.read_namespaced_config_map.return_value = V1ConfigMap(
        data={},
    )
    mock_boto3_session = MagicMock()

    eks.sync(
        MagicMock(),
        mock_k8s_client,
        mock_boto3_session,
        TEST_REGION,
        TEST_UPDATE_TAG,
        TEST_CLUSTER_ID,
        EXAMPLE_CLUSTER_NAME,
    )

    mock_get_access_entries.assert_called_once_with(
        mock_boto3_session,
        TEST_REGION,
        EXAMPLE_CLUSTER_NAME,
    )
    mock_get_oidc_provider.assert_called_once_with(
        mock_boto3_session,
        TEST_REGION,
        EXAMPLE_CLUSTER_NAME,
    )
    mock_cleanup.assert_called_once()
