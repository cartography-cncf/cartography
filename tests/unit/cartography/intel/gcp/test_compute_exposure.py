import json
import logging
from unittest.mock import MagicMock

from googleapiclient.errors import HttpError

import cartography.intel.gcp.instancegroup
from tests.data.gcp.compute_exposure import INSTANCE_GROUP_RESPONSES


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


def test_transform_gcp_instance_groups_with_non_v1_uris():
    responses = [
        {
            "id": "projects/sample-project-123456/zones/us-central1-a/instanceGroups",
            "items": [
                {
                    "name": "ig-beta",
                    "selfLink": "https://www.googleapis.com/compute/beta/projects/sample-project-123456/zones/us-central1-a/instanceGroups/ig-beta",
                    "network": "https://www.googleapis.com/compute/alpha/projects/sample-project-123456/global/networks/default",
                    "subnetwork": "https://www.googleapis.com/compute/beta/projects/sample-project-123456/regions/us-central1/subnetworks/default",
                    "_members": [
                        {
                            "instance": "https://www.googleapis.com/compute/beta/projects/sample-project-123456/zones/us-central1-a/instances/vm-1",
                        },
                    ],
                },
            ],
        },
    ]

    items = cartography.intel.gcp.instancegroup.transform_gcp_instance_groups(
        responses,
        "sample-project-123456",
    )
    item = items[0]
    assert (
        item["network_partial_uri"]
        == "projects/sample-project-123456/global/networks/default"
    )
    assert (
        item["subnetwork_partial_uri"]
        == "projects/sample-project-123456/regions/us-central1/subnetworks/default"
    )
    assert item["member_instance_partial_uris"] == [
        "projects/sample-project-123456/zones/us-central1-a/instances/vm-1"
    ]


def test_get_instance_group_members_forbidden_returns_empty(monkeypatch, caplog):
    compute = MagicMock()
    req = MagicMock()
    compute.instanceGroups.return_value.listInstances.return_value = req
    compute.instanceGroups.return_value.listInstances_next.return_value = None

    resp = MagicMock()
    resp.status = 403
    error = HttpError(
        resp=resp,
        content=json.dumps(
            {
                "error": {
                    "message": "Required permission",
                    "errors": [{"reason": "forbidden"}],
                }
            }
        ).encode("utf-8"),
    )
    monkeypatch.setattr(
        "cartography.intel.gcp.instancegroup.gcp_api_execute_with_retry",
        lambda _req: (_ for _ in ()).throw(error),
    )

    with caplog.at_level(logging.WARNING):
        members = cartography.intel.gcp.instancegroup._get_instance_group_members(
            project_id="test-project",
            instance_group_name="test-group",
            zone="us-central1-a",
            region=None,
            compute=compute,
        )

    assert members == []
    assert "HTTP 403 forbidden: Required permission" in caplog.text
    assert "googleapiclient.errors.HttpError" not in caplog.text
