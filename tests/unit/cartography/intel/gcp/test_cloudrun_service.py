from cartography.intel.gcp.cloudrun.service import transform_services


def test_transform_services_extracts_canonical_uri_hostname():
    [service] = transform_services(
        [
            {
                "name": "projects/project-1/locations/us-central1/services/service-1",
                "uri": "https://Service-1.Run.App./path",
            }
        ],
        "project-1",
    )

    assert service["uri"] == "https://Service-1.Run.App./path"
    assert service["uri_hostname"] == "service-1.run.app"
