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
