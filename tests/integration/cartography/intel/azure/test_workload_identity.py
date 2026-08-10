"""
Integration test for the Azure workload-identity ontology edges
(RUNS_AS to EntraServicePrincipal, ASSUMES to AzureRoleDefinition).
"""

from typing import Any
from typing import AsyncGenerator
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import cartography.intel.azure.compute
import cartography.intel.azure.functions
import cartography.intel.azure.rbac
import cartography.intel.azure.workload_identity
import cartography.intel.microsoft.entra.service_principals
from tests.data.azure.rbac import AZURE_ROLE_ASSIGNMENTS
from tests.data.azure.rbac import AZURE_ROLE_DEFINITIONS
from tests.data.azure.rbac import ENTRA_SERVICE_PRINCIPALS
from tests.integration.cartography.intel.azure.common import (
    create_test_azure_subscription,
)
from tests.integration.cartography.intel.microsoft.entra.common import (
    create_test_entra_tenant,
)
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "12345678-1234-1234-1234-123456789012"
TEST_TENANT_ID = "tenant-123"
TEST_UPDATE_TAG = 123456789

# sp-101 is a ServicePrincipal that holds role assignment `assignment-4`
# (-> Reader role definition) in the shared RBAC fixture.
MANAGED_IDENTITY_PRINCIPAL_ID = "sp-101"
READER_ROLE_DEFINITION_ID = (
    "/subscriptions/12345678-1234-1234-1234-123456789012"
    "/providers/Microsoft.Authorization/roleDefinitions/"
    "acdd72a7-3385-48ef-bd42-f606fba81ae7"
)
VM_ID = (
    "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/"
    "TestRG/providers/Microsoft.Compute/virtualMachines/TestVM"
)
FUNCTION_APP_ID = (
    "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/"
    "TestRG/providers/Microsoft.Web/sites/TestFunc"
)


async def _async_gen(items: list[Any]) -> AsyncGenerator[Any, None]:
    for item in items:
        yield item


@patch.object(
    cartography.intel.microsoft.entra.service_principals,
    "get_entra_service_principals",
    return_value=_async_gen(ENTRA_SERVICE_PRINCIPALS),
)
@patch.object(
    cartography.intel.azure.rbac,
    "get_role_assignments",
    return_value=AZURE_ROLE_ASSIGNMENTS,
)
@patch.object(
    cartography.intel.azure.rbac,
    "get_role_definitions_by_ids",
    return_value=AZURE_ROLE_DEFINITIONS,
)
@pytest.mark.asyncio
async def test_sync_workload_identity_edges(
    mock_get_role_definitions,
    mock_get_role_assignments,
    mock_get_service_principals,
    neo4j_session,
):
    # Arrange
    create_test_azure_subscription(neo4j_session, TEST_SUBSCRIPTION_ID, TEST_UPDATE_TAG)
    create_test_entra_tenant(neo4j_session, TEST_TENANT_ID, TEST_UPDATE_TAG)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_TENANT_ID,
        "AZURE_SUBSCRIPTION_ID": TEST_SUBSCRIPTION_ID,
    }

    # The managed identity surfaces as an EntraServicePrincipal (RUNS_AS target).
    await cartography.intel.microsoft.entra.service_principals.sync_service_principals(
        neo4j_session,
        TEST_TENANT_ID,
        "client-id",
        "client-secret",
        TEST_UPDATE_TAG,
        common_job_parameters,
    )
    # Role assignments for the managed identity (ASSUMES source data).
    cartography.intel.azure.rbac.sync(
        neo4j_session,
        MagicMock(),
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )
    # A VM and a Function App whose managed identity is sp-101.
    cartography.intel.azure.compute.load_vms(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        [
            {
                "id": VM_ID,
                "name": "TestVM",
                "identity_principal_ids": [MANAGED_IDENTITY_PRINCIPAL_ID],
            }
        ],
        TEST_UPDATE_TAG,
    )
    cartography.intel.azure.functions.load_function_apps(
        neo4j_session,
        [
            {
                "id": FUNCTION_APP_ID,
                "name": "TestFunc",
                "identity_principal_ids": [MANAGED_IDENTITY_PRINCIPAL_ID],
            }
        ],
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
    )

    # Act
    cartography.intel.azure.workload_identity.sync(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
    )

    # Assert RUNS_AS -> EntraServicePrincipal (materialized when the node loads).
    assert check_rels(
        neo4j_session,
        "AzureVirtualMachine",
        "id",
        "EntraServicePrincipal",
        "id",
        "RUNS_AS",
        rel_direction_right=True,
    ) == {(VM_ID, MANAGED_IDENTITY_PRINCIPAL_ID)}
    assert check_rels(
        neo4j_session,
        "AzureFunctionApp",
        "id",
        "EntraServicePrincipal",
        "id",
        "RUNS_AS",
        rel_direction_right=True,
    ) == {(FUNCTION_APP_ID, MANAGED_IDENTITY_PRINCIPAL_ID)}

    # Assert ASSUMES -> AzureRoleDefinition (assembled from the role assignment).
    assert check_rels(
        neo4j_session,
        "AzureVirtualMachine",
        "id",
        "AzureRoleDefinition",
        "id",
        "ASSUMES",
        rel_direction_right=True,
    ) == {(VM_ID, READER_ROLE_DEFINITION_ID)}
    assert check_rels(
        neo4j_session,
        "AzureFunctionApp",
        "id",
        "AzureRoleDefinition",
        "id",
        "ASSUMES",
        rel_direction_right=True,
    ) == {(FUNCTION_APP_ID, READER_ROLE_DEFINITION_ID)}
