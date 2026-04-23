from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.cloudrun.execution as cloudrun_execution
import cartography.intel.gcp.cloudrun.revision as cloudrun_revision


def test_transform_revisions_accepts_full_service_resource_name():
    transformed = cloudrun_revision.transform_revisions(
        [
            {
                "name": "projects/test-project/locations/us-central1/services/test-service/revisions/test-service-00001-abc",
                "service": "projects/test-project/locations/us-central1/services/test-service",
                "serviceAccount": "test-sa@test-project.iam.gserviceaccount.com",
            },
        ],
        "test-project",
    )

    assert transformed[0]["service"] == (
        "projects/test-project/locations/us-central1/services/test-service"
    )


def test_get_revisions_uses_services_wildcard_parent():
    mock_client = MagicMock()
    mock_client.list_revisions.return_value = ["revision"]

    with (
        patch(
            "cartography.intel.gcp.cloudrun.revision.build_cloud_run_revision_client",
            return_value=mock_client,
        ),
        patch(
            "cartography.intel.gcp.cloudrun.revision.list_cloud_run_resources_for_location",
            side_effect=lambda **kwargs: kwargs["fetcher"](),
        ),
        patch(
            "cartography.intel.gcp.cloudrun.revision.fetch_cloud_run_resources_for_locations",
            side_effect=lambda **kwargs: kwargs["fetch_for_location"](
                "projects/test-project/locations/us-central1"
            ),
        ),
    ):
        result = cloudrun_revision.get_revisions(
            "test-project",
            ["projects/test-project/locations/us-central1"],
            MagicMock(),
        )

    assert result == ["revision"]
    mock_client.list_revisions.assert_called_once_with(
        parent="projects/test-project/locations/us-central1/services/-",
    )


def test_get_executions_uses_jobs_wildcard_parent():
    mock_client = MagicMock()
    mock_client.list_executions.return_value = ["execution"]

    with (
        patch(
            "cartography.intel.gcp.cloudrun.execution.build_cloud_run_execution_client",
            return_value=mock_client,
        ),
        patch(
            "cartography.intel.gcp.cloudrun.execution.list_cloud_run_resources_for_location",
            side_effect=lambda **kwargs: kwargs["fetcher"](),
        ),
        patch(
            "cartography.intel.gcp.cloudrun.execution.fetch_cloud_run_resources_for_locations",
            side_effect=lambda **kwargs: kwargs["fetch_for_location"](
                "projects/test-project/locations/us-central1"
            ),
        ),
    ):
        result = cloudrun_execution.get_executions(
            "test-project",
            ["projects/test-project/locations/us-central1"],
            MagicMock(),
        )

    assert result == ["execution"]
    mock_client.list_executions.assert_called_once_with(
        parent="projects/test-project/locations/us-central1/jobs/-",
    )
