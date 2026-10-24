import json
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from kubernetes.client import V1ObjectMeta
from kubernetes.client import V1PolicyRule
from kubernetes.client import V1Role
from kubernetes.client.exceptions import ApiException

from cartography.intel.kubernetes.rbac import sync_kubernetes_rbac
from cartography.intel.kubernetes.rbac import transform_roles

_LIST_FUNCTIONS = {
    "core": ["list_service_account_for_all_namespaces"],
    "rbac": [
        "list_role_for_all_namespaces",
        "list_role_binding_for_all_namespaces",
        "list_cluster_role",
        "list_cluster_role_binding",
    ],
}


def _client_failing_on(failing: str, error: ApiException) -> MagicMock:
    client = MagicMock()
    client.name = "my-cluster"
    for api_name, functions in _LIST_FUNCTIONS.items():
        for function_name in functions:
            list_func = getattr(getattr(client, api_name), function_name)
            list_func.__name__ = function_name
            if function_name == failing:
                list_func.side_effect = error
            else:
                list_func.return_value = MagicMock(
                    items=[], metadata=MagicMock(_continue=None)
                )
    return client


@patch("cartography.intel.kubernetes.rbac.cleanup")
@patch("cartography.intel.kubernetes.rbac.load_service_accounts")
def test_sync_rbac_skips_load_and_cleanup_on_forbidden(
    mock_load_service_accounts, mock_cleanup, caplog
):
    # Arrange
    mock_client = _client_failing_on(
        "list_cluster_role_binding", ApiException(status=403, reason="Forbidden")
    )

    # Act
    with caplog.at_level("WARNING"):
        sync_kubernetes_rbac(
            session=MagicMock(),
            client=mock_client,
            update_tag=1,
            common_job_parameters={"CLUSTER_ID": "cluster-id"},
        )

    # Assert
    mock_load_service_accounts.assert_not_called()
    mock_cleanup.assert_not_called()
    assert any(
        "lacks permission to list RBAC resources" in record.message
        for record in caplog.records
    )


@patch("cartography.intel.kubernetes.rbac.cleanup")
def test_sync_rbac_raises_on_other_api_errors(mock_cleanup):
    # Arrange
    mock_client = _client_failing_on(
        "list_role_for_all_namespaces",
        ApiException(status=500, reason="Internal Server Error"),
    )

    # Act and assert
    with pytest.raises(ApiException):
        sync_kubernetes_rbac(
            session=MagicMock(),
            client=mock_client,
            update_tag=1,
            common_job_parameters={"CLUSTER_ID": "cluster-id"},
        )
    mock_cleanup.assert_not_called()


def test_transform_roles_keeps_rules_with_api_field_names():
    # Arrange
    role = V1Role(
        metadata=V1ObjectMeta(name="reader", namespace="ns", uid="role-uid"),
        rules=[
            V1PolicyRule(
                api_groups=[""],
                resources=["secrets"],
                resource_names=["db"],
                verbs=["get"],
            ),
            V1PolicyRule(non_resource_urls=["/healthz"], verbs=["get"]),
        ],
    )

    # Act
    transformed = transform_roles([role], "cluster")

    # Assert
    assert json.loads(transformed[0]["rules"]) == [
        {
            "apiGroups": [""],
            "resourceNames": ["db"],
            "resources": ["secrets"],
            "verbs": ["get"],
        },
        {"nonResourceURLs": ["/healthz"], "verbs": ["get"]},
    ]
