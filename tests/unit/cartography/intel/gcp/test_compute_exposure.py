import cartography.intel.gcp.backendservice
import cartography.intel.gcp.cloud_armor
import cartography.intel.gcp.instancegroup
from tests.data.gcp.compute_exposure import BACKEND_SERVICE_RESPONSE
from tests.data.gcp.compute_exposure import CLOUD_ARMOR_RESPONSE
from tests.data.gcp.compute_exposure import INSTANCE_GROUP_RESPONSES


def test_transform_gcp_backend_services():
    items = cartography.intel.gcp.backendservice.transform_gcp_backend_services(
        BACKEND_SERVICE_RESPONSE,
        "sample-project-123456",
    )

    assert len(items) == 1
    item = items[0]
    assert (
        item["partial_uri"]
        == "projects/sample-project-123456/global/backendServices/test-backend-service"
    )
    assert item["project_id"] == "sample-project-123456"
    assert item["load_balancing_scheme"] == "EXTERNAL"
    assert (
        item["security_policy_partial_uri"]
        == "projects/sample-project-123456/global/securityPolicies/test-armor-policy"
    )
    assert item["backend_group_partial_uris"] == [
        "projects/sample-project-123456/zones/us-central1-a/instanceGroups/test-instance-group"
    ]


def test_transform_gcp_instance_groups():
    items = cartography.intel.gcp.instancegroup.transform_gcp_instance_groups(
        INSTANCE_GROUP_RESPONSES,
        "sample-project-123456",
    )

    assert len(items) == 1
    item = items[0]
    assert (
        item["partial_uri"]
        == "projects/sample-project-123456/zones/us-central1-a/instanceGroups/test-instance-group"
    )
    assert item["zone"] == "us-central1-a"
    assert (
        item["network_partial_uri"]
        == "projects/sample-project-123456/global/networks/default"
    )
    assert (
        item["subnetwork_partial_uri"]
        == "projects/sample-project-123456/regions/us-central1/subnetworks/default"
    )
    assert item["member_instance_partial_uris"] == [
        "projects/sample-project-123456/zones/us-central1-a/instances/vm-private-1",
        "projects/sample-project-123456/zones/us-central1-a/instances/vm-private-2",
    ]


def test_transform_gcp_cloud_armor_policies():
    items = cartography.intel.gcp.cloud_armor.transform_gcp_cloud_armor_policies(
        CLOUD_ARMOR_RESPONSE,
        "sample-project-123456",
    )

    assert len(items) == 1
    item = items[0]
    assert (
        item["partial_uri"]
        == "projects/sample-project-123456/global/securityPolicies/test-armor-policy"
    )
    assert item["project_id"] == "sample-project-123456"
    assert item["policy_type"] == "CLOUD_ARMOR"
