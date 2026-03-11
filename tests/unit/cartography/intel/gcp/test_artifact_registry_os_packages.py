from unittest.mock import MagicMock

from cartography.intel.gcp.artifact_registry.artifact import get_apt_artifacts
from cartography.intel.gcp.artifact_registry.artifact import get_yum_artifacts


def _make_os_package_client(package_name: str, version_name: str) -> MagicMock:
    client = MagicMock()
    repositories = (
        client.projects.return_value.locations.return_value.repositories.return_value
    )
    packages = repositories.packages.return_value
    versions = packages.versions.return_value

    packages_request = MagicMock()
    packages_request.execute.return_value = {
        "packages": [
            {
                "name": f"projects/test-project/locations/us-east1/repositories/repo/packages/{package_name}",
                "displayName": package_name,
            }
        ]
    }
    packages.list.return_value = packages_request
    packages.list_next.return_value = None

    versions_request = MagicMock()
    versions_request.execute.return_value = {
        "versions": [
            {
                "name": f"projects/test-project/locations/us-east1/repositories/repo/packages/{package_name}/versions/{version_name}",
                "createTime": "2024-01-06T00:00:00Z",
                "updateTime": "2024-01-06T00:00:00Z",
            }
        ]
    }
    versions.list.return_value = versions_request
    versions.list_next.return_value = None
    return client


def test_get_apt_artifacts_uses_packages_and_versions():
    client = _make_os_package_client("curl", "7.88.1")

    artifacts = get_apt_artifacts(
        client,
        "projects/test-project/locations/us-east1/repositories/repo",
    )

    assert artifacts == [
        {
            "name": "projects/test-project/locations/us-east1/repositories/repo/packages/curl/versions/7.88.1",
            "createTime": "2024-01-06T00:00:00Z",
            "updateTime": "2024-01-06T00:00:00Z",
            "packageName": "curl",
        }
    ]


def test_get_yum_artifacts_uses_packages_and_versions():
    client = _make_os_package_client("bash", "5.2.26")

    artifacts = get_yum_artifacts(
        client,
        "projects/test-project/locations/us-east1/repositories/repo",
    )

    assert artifacts == [
        {
            "name": "projects/test-project/locations/us-east1/repositories/repo/packages/bash/versions/5.2.26",
            "createTime": "2024-01-06T00:00:00Z",
            "updateTime": "2024-01-06T00:00:00Z",
            "packageName": "bash",
        }
    ]
