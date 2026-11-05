from cartography.intel.gcp.cloudrun.service import transform_services


def test_transform_services_extracts_canonical_uri_hostname():
    # Arrange
    services = [
        {
            "name": "projects/project-1/locations/us-central1/services/service-1",
            "uri": "https://Service-1.Run.Example.COM./path",
        }
    ]

    # Act
    [service] = transform_services(services, "project-1")

    # Assert
    assert service["uri"] == "https://Service-1.Run.Example.COM./path"
    assert service["uri_hostname"] == "service-1.run.example.com"
