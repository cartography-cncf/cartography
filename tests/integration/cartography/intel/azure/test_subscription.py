from unittest.mock import MagicMock
from unittest.mock import patch

from azure.core.exceptions import HttpResponseError

import cartography.intel.azure.management_groups as management_groups
import cartography.intel.azure.subscription as subscription
from tests.data.azure.management_groups import AZURE_MANAGEMENT_GROUP_SUBSCRIPTIONS
from tests.data.azure.management_groups import AZURE_MANAGEMENT_GROUPS
from tests.data.azure.management_groups import TEST_CHILD_MANAGEMENT_GROUP_ID
from tests.data.azure.management_groups import TEST_PARENT_MANAGEMENT_GROUP_ID
from tests.data.azure.management_groups import TEST_SUBSCRIPTION_ID
from tests.data.azure.management_groups import TEST_TENANT_ID
from tests.data.azure.management_groups import (
    UPDATED_AZURE_MANAGEMENT_GROUP_SUBSCRIPTIONS,
)
from tests.data.azure.management_groups import UPDATED_AZURE_MANAGEMENT_GROUPS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@patch("cartography.intel.azure.subscription.get_azure_management_group_subscriptions")
@patch("cartography.intel.azure.management_groups.get_azure_management_groups")
def test_sync_subscriptions_from_a_management_group(
    mock_get_management_groups,
    mock_get_management_group_subscriptions,
    neo4j_session,
):
    # Arrange
    mock_get_management_groups.return_value = AZURE_MANAGEMENT_GROUPS
    mock_get_management_group_subscriptions.return_value = (
        AZURE_MANAGEMENT_GROUP_SUBSCRIPTIONS
    )

    neo4j_session.run(
        """
        MERGE (t:AzureTenant{id: $tenant_id})
        SET t.lastupdated = $update_tag
        """,
        tenant_id=TEST_TENANT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_TENANT_ID,
    }

    management_groups.sync(
        neo4j_session,
        MagicMock(),
        TEST_TENANT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    subscriptions = [
        {
            "id": f"/subscriptions/{TEST_SUBSCRIPTION_ID}",
            "subscriptionId": TEST_SUBSCRIPTION_ID,
            "displayName": "Test Subscription",
            "state": "Enabled",
        },
    ]

    # Act
    subscription.sync(
        neo4j_session,
        MagicMock(),
        TEST_TENANT_ID,
        subscriptions,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert
    actual_nodes = check_nodes(
        neo4j_session,
        "AzureSubscription",
        ["id", "path", "name", "state"],
    )
    assert actual_nodes == {
        (
            TEST_SUBSCRIPTION_ID,
            f"/subscriptions/{TEST_SUBSCRIPTION_ID}",
            "Test Subscription",
            "Enabled",
        ),
    }

    tenant_resource_rels = check_rels(
        neo4j_session,
        "AzureTenant",
        "id",
        "AzureSubscription",
        "id",
        "RESOURCE",
    )
    assert tenant_resource_rels == {
        (TEST_TENANT_ID, TEST_SUBSCRIPTION_ID),
    }

    subscription_parent_rels = check_rels(
        neo4j_session,
        "AzureSubscription",
        "id",
        "AzureManagementGroup",
        "id",
        "PARENT",
    )
    assert subscription_parent_rels == {
        (TEST_SUBSCRIPTION_ID, TEST_CHILD_MANAGEMENT_GROUP_ID),
    }


@patch("cartography.intel.azure.subscription.get_azure_management_group_subscriptions")
@patch("cartography.intel.azure.management_groups.get_azure_management_groups")
def test_cleanup_stale_management_group_hierarchy_and_subscription_parentage(
    mock_get_management_groups,
    mock_get_management_group_subscriptions,
    neo4j_session,
):
    # Arrange
    mock_get_management_groups.side_effect = [
        AZURE_MANAGEMENT_GROUPS,
        UPDATED_AZURE_MANAGEMENT_GROUPS,
    ]
    mock_get_management_group_subscriptions.side_effect = [
        AZURE_MANAGEMENT_GROUP_SUBSCRIPTIONS,
        UPDATED_AZURE_MANAGEMENT_GROUP_SUBSCRIPTIONS,
    ]

    neo4j_session.run(
        """
        MERGE (t:AzureTenant{id: $tenant_id})
        SET t.lastupdated = $update_tag
        """,
        tenant_id=TEST_TENANT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    subscriptions = [
        {
            "id": f"/subscriptions/{TEST_SUBSCRIPTION_ID}",
            "subscriptionId": TEST_SUBSCRIPTION_ID,
            "displayName": "Test Subscription",
            "state": "Enabled",
        },
    ]

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_TENANT_ID,
    }

    # Act
    management_groups.sync(
        neo4j_session,
        MagicMock(),
        TEST_TENANT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )
    subscription.sync(
        neo4j_session,
        MagicMock(),
        TEST_TENANT_ID,
        subscriptions,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    second_update_tag = TEST_UPDATE_TAG + 1
    second_common_job_parameters = {
        "UPDATE_TAG": second_update_tag,
        "TENANT_ID": TEST_TENANT_ID,
    }

    management_groups.sync(
        neo4j_session,
        MagicMock(),
        TEST_TENANT_ID,
        second_update_tag,
        second_common_job_parameters,
    )
    subscription.sync(
        neo4j_session,
        MagicMock(),
        TEST_TENANT_ID,
        subscriptions,
        second_update_tag,
        second_common_job_parameters,
    )

    # Assert
    management_group_nodes = check_nodes(
        neo4j_session,
        "AzureManagementGroup",
        ["id", "name"],
    )
    assert management_group_nodes == {
        (TEST_PARENT_MANAGEMENT_GROUP_ID, "test-management-group"),
    }

    management_group_parent_rels = check_rels(
        neo4j_session,
        "AzureManagementGroup",
        "id",
        "AzureManagementGroup",
        "id",
        "PARENT",
    )
    assert management_group_parent_rels == set()

    subscription_nodes = check_nodes(
        neo4j_session,
        "AzureSubscription",
        ["id", "path", "name", "state"],
    )
    assert subscription_nodes == {
        (
            TEST_SUBSCRIPTION_ID,
            f"/subscriptions/{TEST_SUBSCRIPTION_ID}",
            "Test Subscription",
            "Enabled",
        ),
    }

    tenant_resource_rels = check_rels(
        neo4j_session,
        "AzureTenant",
        "id",
        "AzureSubscription",
        "id",
        "RESOURCE",
    )
    assert tenant_resource_rels == {
        (TEST_TENANT_ID, TEST_SUBSCRIPTION_ID),
    }

    subscription_parent_rels = check_rels(
        neo4j_session,
        "AzureSubscription",
        "id",
        "AzureManagementGroup",
        "id",
        "PARENT",
    )
    assert subscription_parent_rels == set()


@patch("cartography.intel.azure.subscription.get_azure_management_group_subscriptions")
def test_sync_subscriptions_continues_when_management_group_enrichment_fails(
    mock_get_management_group_subscriptions,
    neo4j_session,
):
    # Arrange
    mock_get_management_group_subscriptions.side_effect = HttpResponseError(
        message="management group subscription lookup failed",
    )

    neo4j_session.run(
        """
        MERGE (t:AzureTenant{id: $tenant_id})
        SET t.lastupdated = $update_tag
        """,
        tenant_id=TEST_TENANT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    subscriptions = [
        {
            "id": f"/subscriptions/{TEST_SUBSCRIPTION_ID}",
            "subscriptionId": TEST_SUBSCRIPTION_ID,
            "displayName": "Test Subscription",
            "state": "Enabled",
        },
    ]

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_TENANT_ID,
    }

    # Act
    subscription.sync(
        neo4j_session,
        MagicMock(),
        TEST_TENANT_ID,
        subscriptions,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert
    actual_nodes = check_nodes(
        neo4j_session,
        "AzureSubscription",
        ["id", "path", "name", "state"],
    )
    assert actual_nodes == {
        (
            TEST_SUBSCRIPTION_ID,
            f"/subscriptions/{TEST_SUBSCRIPTION_ID}",
            "Test Subscription",
            "Enabled",
        ),
    }

    tenant_resource_rels = check_rels(
        neo4j_session,
        "AzureTenant",
        "id",
        "AzureSubscription",
        "id",
        "RESOURCE",
    )
    assert tenant_resource_rels == {
        (TEST_TENANT_ID, TEST_SUBSCRIPTION_ID),
    }

    subscription_parent_rels = check_rels(
        neo4j_session,
        "AzureSubscription",
        "id",
        "AzureManagementGroup",
        "id",
        "PARENT",
    )
    assert subscription_parent_rels == set()
