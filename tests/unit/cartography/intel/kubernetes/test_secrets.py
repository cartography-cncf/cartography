from unittest.mock import MagicMock
from unittest.mock import patch

from kubernetes.client.exceptions import ApiException

from cartography.intel.kubernetes.secrets import sync_secrets


def _make_api_exception(status: int) -> ApiException:
    return ApiException(status=status, reason="Forbidden")


@patch("cartography.intel.kubernetes.secrets.cleanup")
@patch("cartography.intel.kubernetes.secrets.load_secrets")
def test_sync_secrets_skips_load_and_cleanup_on_forbidden(
    mock_load_secrets, mock_cleanup, caplog
):
    mock_client = MagicMock()
    mock_client.name = "my-cluster"
    mock_client.core.list_secret_for_all_namespaces.__name__ = (
        "list_secret_for_all_namespaces"
    )
    mock_client.core.list_secret_for_all_namespaces.side_effect = _make_api_exception(
        403
    )

    with caplog.at_level("WARNING"):
        sync_secrets(
            session=MagicMock(),
            client=mock_client,
            update_tag=1,
            common_job_parameters={"CLUSTER_ID": "cluster-id"},
        )

    mock_load_secrets.assert_not_called()
    mock_cleanup.assert_not_called()
    assert any(
        "lacks permission to list secrets" in record.message
        for record in caplog.records
    )


@patch("cartography.intel.kubernetes.secrets.cleanup")
@patch("cartography.intel.kubernetes.secrets.load_secrets")
def test_sync_secrets_skips_load_and_cleanup_on_unauthorized(
    mock_load_secrets, mock_cleanup
):
    mock_client = MagicMock()
    mock_client.name = "my-cluster"
    mock_client.core.list_secret_for_all_namespaces.__name__ = (
        "list_secret_for_all_namespaces"
    )
    mock_client.core.list_secret_for_all_namespaces.side_effect = _make_api_exception(
        401
    )

    sync_secrets(
        session=MagicMock(),
        client=mock_client,
        update_tag=1,
        common_job_parameters={"CLUSTER_ID": "cluster-id"},
    )

    mock_load_secrets.assert_not_called()
    mock_cleanup.assert_not_called()
