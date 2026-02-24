import cartography.intel.gcp.backendservice
import cartography.intel.gcp.cloud_armor
import cartography.intel.gcp.instancegroup
from tests.data.gcp.compute_exposure import BACKEND_SERVICE_RESPONSE
from tests.data.gcp.compute_exposure import CLOUD_ARMOR_RESPONSE
from tests.data.gcp.compute_exposure import INSTANCE_GROUP_RESPONSES


def test_transform_gcp_backend_services():
    items = cartography.intel.gcp.backendservice.transform_gcp_backend_services(
        BACKEND_SERVICE_RESPONSE,
        "test-cloud-run-483700",
    )

    assert len(items) == 1
    item = items[0]
    assert (
        item["partial_uri"]
        == "projects/test-cloud-run-483700/global/backendServices/test-backend-service"
    )
    assert item["project_id"] == "test-cloud-run-483700"
    assert item["load_balancing_scheme"] == "EXTERNAL"
    assert (
        item["security_policy_partial_uri"]
        == "projects/test-cloud-run-483700/global/securityPolicies/test-armor-policy"
    )
    assert item["backend_group_partial_uris"] == [
        "projects/test-cloud-run-483700/zones/us-central1-a/instanceGroups/test-instance-group"
    ]


def test_transform_gcp_instance_groups():
    items = cartography.intel.gcp.instancegroup.transform_gcp_instance_groups(
        INSTANCE_GROUP_RESPONSES,
        "test-cloud-run-483700",
    )

    assert len(items) == 1
    item = items[0]
    assert (
        item["partial_uri"]
        == "projects/test-cloud-run-483700/zones/us-central1-a/instanceGroups/test-instance-group"
    )
    assert item["zone"] == "us-central1-a"
    assert (
        item["network_partial_uri"]
        == "projects/test-cloud-run-483700/global/networks/default"
    )
    assert (
        item["subnetwork_partial_uri"]
        == "projects/test-cloud-run-483700/regions/us-central1/subnetworks/default"
    )
    assert item["member_instance_partial_uris"] == [
        "projects/test-cloud-run-483700/zones/us-central1-a/instances/vm-private-1",
        "projects/test-cloud-run-483700/zones/us-central1-a/instances/vm-private-2",
    ]


def test_transform_gcp_cloud_armor_policies():
    items = cartography.intel.gcp.cloud_armor.transform_gcp_cloud_armor_policies(
        CLOUD_ARMOR_RESPONSE,
        "test-cloud-run-483700",
    )

    assert len(items) == 1
    item = items[0]
    assert (
        item["partial_uri"]
        == "projects/test-cloud-run-483700/global/securityPolicies/test-armor-policy"
    )
    assert item["project_id"] == "test-cloud-run-483700"
    assert item["policy_type"] == "CLOUD_ARMOR"


def test_transform_gcp_backend_services_handles_non_v1_uri_shape():
    response = {
        "id": "projects/test-cloud-run-483700/global/backendServices",
        "items": [
            {
                "name": "bs-non-v1",
                "securityPolicy": "https://www.googleapis.com/compute/beta/projects/test-cloud-run-483700/global/securityPolicies/policy-beta",
                "backends": [
                    {
                        "group": "projects/test-cloud-run-483700/zones/us-central1-a/instanceGroups/ig-already-partial",
                    },
                ],
            },
        ],
    }

    items = cartography.intel.gcp.backendservice.transform_gcp_backend_services(
        response,
        "test-cloud-run-483700",
    )

    assert len(items) == 1
    item = items[0]
    assert (
        item["security_policy_partial_uri"]
        == "https://www.googleapis.com/compute/beta/projects/test-cloud-run-483700/global/securityPolicies/policy-beta"
    )
    assert item["backend_group_partial_uris"] == [
        "projects/test-cloud-run-483700/zones/us-central1-a/instanceGroups/ig-already-partial",
    ]


def test_transform_gcp_instance_groups_handles_non_v1_uri_shape():
    responses = [
        {
            "id": "projects/test-cloud-run-483700/zones/us-central1-a/instanceGroups",
            "items": [
                {
                    "name": "ig-non-v1",
                    "network": "https://www.googleapis.com/compute/beta/projects/test-cloud-run-483700/global/networks/default",
                    "subnetwork": "projects/test-cloud-run-483700/regions/us-central1/subnetworks/default",
                    "_members": [
                        {
                            "instance": "https://www.googleapis.com/compute/beta/projects/test-cloud-run-483700/zones/us-central1-a/instances/vm-beta",
                        },
                    ],
                },
            ],
        },
    ]

    items = cartography.intel.gcp.instancegroup.transform_gcp_instance_groups(
        responses,
        "test-cloud-run-483700",
    )

    assert len(items) == 1
    item = items[0]
    assert (
        item["network_partial_uri"]
        == "https://www.googleapis.com/compute/beta/projects/test-cloud-run-483700/global/networks/default"
    )
    assert (
        item["subnetwork_partial_uri"]
        == "projects/test-cloud-run-483700/regions/us-central1/subnetworks/default"
    )
    assert item["member_instance_partial_uris"] == [
        "https://www.googleapis.com/compute/beta/projects/test-cloud-run-483700/zones/us-central1-a/instances/vm-beta",
    ]
