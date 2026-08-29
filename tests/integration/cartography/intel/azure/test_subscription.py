from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
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
TEST_STALE_SUBSCRIPTION_ID = "ffffffff-1111-2222-3333-444444444444"


@pytest.fixture(autouse=True)
def cleanup_test_data(neo4j_session):
    def cleanup() -> None:
        neo4j_session.run(
            """
            MATCH (n)
            WHERE (
                (n:AzureTenant AND n.id = $tenant_id)
                OR (n:AzureManagementGroup AND n.id IN $management_group_ids)
                OR (n:AzureSubscription AND n.id IN $subscription_ids)
                OR (
                    n:AzureResourceGroup
                    AND any(subscription_id IN $subscription_ids WHERE n.id CONTAINS subscription_id)
                )
            )
            DETACH DELETE n
            """,
            tenant_id=TEST_TENANT_ID,
            management_group_ids=[
                TEST_PARENT_MANAGEMENT_GROUP_ID,
                TEST_CHILD_MANAGEMENT_GROUP_ID,
            ],
            subscription_ids=[
                TEST_SUBSCRIPTION_ID,
                TEST_STALE_SUBSCRIPTION_ID,
            ],
        )

    cleanup()
    yield
    cleanup()


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
        AZURE_MANAGEMENT_GROUP_SUBSCRIPTIONS,
        set(),
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
        (AZURE_MANAGEMENT_GROUP_SUBSCRIPTIONS, set()),
        (UPDATED_AZURE_MANAGEMENT_GROUP_SUBSCRIPTIONS, set()),
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
    management_groups.cleanup(
        neo4j_session,
        second_common_job_parameters,
        cascade_delete=True,
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
@patch("cartography.intel.azure.management_groups.get_azure_management_groups")
def test_sync_subscriptions_preserves_existing_parent_only_for_failed_groups(
    mock_get_management_groups,
    mock_get_management_group_subscriptions,
    neo4j_session,
):
    # Arrange
    mock_get_management_groups.return_value = AZURE_MANAGEMENT_GROUPS
    mock_get_management_group_subscriptions.return_value = (
        [],
        {TEST_CHILD_MANAGEMENT_GROUP_ID},
    )

    neo4j_session.run(
        """
        MERGE (t:AzureTenant{id: $tenant_id})
        SET t.lastupdated = $previous_update_tag
        """,
        tenant_id=TEST_TENANT_ID,
        previous_update_tag=TEST_UPDATE_TAG - 1,
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

    # Seed graph with existing parentage from a previous sync. This is
    # prerequisite state for the partial management-group access-loss path.
    neo4j_session.run(
        """
        MATCH (t:AzureTenant{id: $tenant_id})
        MATCH (childMg:AzureManagementGroup{id: $child_management_group_id})
        MATCH (parentMg:AzureManagementGroup{id: $parent_management_group_id})
        MERGE (preserved:AzureSubscription{id: $preserved_subscription_id})
        SET preserved.lastupdated = $previous_update_tag
        MERGE (stale:AzureSubscription{id: $stale_subscription_id})
        SET stale.lastupdated = $previous_update_tag
        MERGE (t)-[:RESOURCE {lastupdated: $previous_update_tag}]->(preserved)
        MERGE (t)-[:RESOURCE {lastupdated: $previous_update_tag}]->(stale)
        MERGE (preserved)-[:PARENT {lastupdated: $previous_update_tag}]->(childMg)
        MERGE (stale)-[:PARENT {lastupdated: $previous_update_tag}]->(parentMg)
        """,
        tenant_id=TEST_TENANT_ID,
        child_management_group_id=TEST_CHILD_MANAGEMENT_GROUP_ID,
        parent_management_group_id=TEST_PARENT_MANAGEMENT_GROUP_ID,
        preserved_subscription_id=TEST_SUBSCRIPTION_ID,
        stale_subscription_id=TEST_STALE_SUBSCRIPTION_ID,
        previous_update_tag=TEST_UPDATE_TAG - 1,
    )

    subscriptions = [
        {
            "id": f"/subscriptions/{TEST_SUBSCRIPTION_ID}",
            "subscriptionId": TEST_SUBSCRIPTION_ID,
            "displayName": "Preserved Subscription",
            "state": "Enabled",
        },
        {
            "id": f"/subscriptions/{TEST_STALE_SUBSCRIPTION_ID}",
            "subscriptionId": TEST_STALE_SUBSCRIPTION_ID,
            "displayName": "Stale Subscription",
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
        (TEST_TENANT_ID, TEST_STALE_SUBSCRIPTION_ID),
    }


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


@patch("cartography.intel.azure.subscription.get_azure_management_group_subscriptions")
def test_cleanup_stale_subscription_cascade_deletes_subscription_resources(
    mock_get_management_group_subscriptions,
    neo4j_session,
):
    # Arrange
    mock_get_management_group_subscriptions.return_value = ([], set())

    stale_resource_group_id = (
        f"/subscriptions/{TEST_STALE_SUBSCRIPTION_ID}/resourceGroups/stale-rg"
    )
    neo4j_session.run(
        """
        MERGE (t:AzureTenant{id: $tenant_id})
        SET t.lastupdated = $update_tag
        MERGE (s:AzureSubscription{id: $subscription_id})
        SET s.lastupdated = $previous_update_tag
        MERGE (rg:AzureResourceGroup{id: $resource_group_id})
        SET rg.lastupdated = $previous_update_tag
        MERGE (t)-[:RESOURCE {lastupdated: $previous_update_tag}]->(s)
        MERGE (s)-[:RESOURCE {lastupdated: $previous_update_tag}]->(rg)
        """,
        tenant_id=TEST_TENANT_ID,
        subscription_id=TEST_STALE_SUBSCRIPTION_ID,
        resource_group_id=stale_resource_group_id,
        update_tag=TEST_UPDATE_TAG,
        previous_update_tag=TEST_UPDATE_TAG - 1,
    )

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_TENANT_ID,
    }

    # Act
    subscription.sync(
        neo4j_session,
        MagicMock(),
        TEST_TENANT_ID,
        [],
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert
    subscription_nodes = check_nodes(neo4j_session, "AzureSubscription", ["id"])
    resource_group_nodes = check_nodes(neo4j_session, "AzureResourceGroup", ["id"])
    assert (TEST_STALE_SUBSCRIPTION_ID,) not in subscription_nodes
    assert (stale_resource_group_id,) not in resource_group_nodes


@patch("cartography.intel.azure.subscription.get_azure_management_group_subscriptions")
@patch("cartography.intel.azure.management_groups.get_azure_management_groups")
def test_sync_subscriptions_preserves_existing_parent_when_global_enrichment_fails(
    mock_get_management_groups,
    mock_get_management_group_subscriptions,
    neo4j_session,
):
    # Arrange
    mock_get_management_groups.return_value = AZURE_MANAGEMENT_GROUPS
    mock_get_management_group_subscriptions.side_effect = HttpResponseError(
        message="management group subscription lookup failed",
    )

    # Seed graph with existing parentage from a previous sync. This is
    # prerequisite state for the global management-group enrichment failure path.
    neo4j_session.run(
        """
        MERGE (t:AzureTenant{id: $tenant_id})
        SET t.lastupdated = $previous_update_tag
        """,
        tenant_id=TEST_TENANT_ID,
        previous_update_tag=TEST_UPDATE_TAG - 1,
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

    neo4j_session.run(
        """
        MATCH (t:AzureTenant{id: $tenant_id})
        MATCH (childMg:AzureManagementGroup{id: $child_management_group_id})
        MERGE (s:AzureSubscription{id: $subscription_id})
        SET s.lastupdated = $previous_update_tag
        MERGE (t)-[:RESOURCE {lastupdated: $previous_update_tag}]->(s)
        MERGE (s)-[:PARENT {lastupdated: $previous_update_tag}]->(childMg)
        """,
        tenant_id=TEST_TENANT_ID,
        child_management_group_id=TEST_CHILD_MANAGEMENT_GROUP_ID,
        subscription_id=TEST_SUBSCRIPTION_ID,
        previous_update_tag=TEST_UPDATE_TAG - 1,
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
