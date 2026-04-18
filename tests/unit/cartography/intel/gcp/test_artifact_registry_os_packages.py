from unittest.mock import MagicMock

from google.cloud.artifactregistry_v1 import types
from google.protobuf.timestamp_pb2 import Timestamp

from cartography.intel.gcp.artifact_registry.artifact import get_apt_artifacts
from cartography.intel.gcp.artifact_registry.artifact import get_docker_images
from cartography.intel.gcp.artifact_registry.artifact import get_go_modules
from cartography.intel.gcp.artifact_registry.artifact import get_yum_artifacts


def _timestamp(value: str) -> Timestamp:
    ts = Timestamp()
    ts.FromJsonString(value)
    return ts


def _make_os_package_client(package_name: str, version_name: str) -> MagicMock:
    client = MagicMock()
    package = types.Package(
        name=f"projects/test-project/locations/us-east1/repositories/repo/packages/{package_name}",
        display_name=package_name,
        create_time=_timestamp("2024-01-06T00:00:00Z"),
        update_time=_timestamp("2024-01-06T00:00:00Z"),
    )
    version = types.Version(
        name=f"projects/test-project/locations/us-east1/repositories/repo/packages/{package_name}/versions/{version_name}",
        create_time=_timestamp("2024-01-06T00:00:00Z"),
        update_time=_timestamp("2024-01-06T00:00:00Z"),
    )
    client.list_packages.return_value = [package]
    client.list_versions.return_value = [version]
    return client


def test_get_docker_images_converts_sdk_messages_to_existing_dict_shape():
    client = MagicMock()
    client.list_docker_images.return_value = [
        types.DockerImage(
            name="projects/test-project/locations/us-central1/repositories/repo/dockerImages/my-app@sha256:abc123",
            uri="us-central1-docker.pkg.dev/test-project/repo/my-app@sha256:abc123",
            tags=["latest"],
            image_size_bytes=123,
            media_type="application/vnd.oci.image.index.v1+json",
            upload_time=_timestamp("2024-01-10T00:00:00Z"),
            build_time=_timestamp("2024-01-10T00:00:00Z"),
            update_time=_timestamp("2024-01-10T00:00:00Z"),
            image_manifests=[
                types.ImageManifest(
                    digest="sha256:def456",
                    media_type="application/vnd.oci.image.manifest.v1+json",
                    architecture="amd64",
                    os="linux",
                )
            ],
        )
    ]

    images = get_docker_images(
        client,
        "projects/test-project/locations/us-central1/repositories/repo",
    )

    assert images == [
        {
            "name": "projects/test-project/locations/us-central1/repositories/repo/dockerImages/my-app@sha256:abc123",
            "uri": "us-central1-docker.pkg.dev/test-project/repo/my-app@sha256:abc123",
            "tags": ["latest"],
            "imageSizeBytes": "123",
            "uploadTime": "2024-01-10T00:00:00Z",
            "mediaType": "application/vnd.oci.image.index.v1+json",
            "buildTime": "2024-01-10T00:00:00Z",
            "updateTime": "2024-01-10T00:00:00Z",
            "imageManifests": [
                {
                    "digest": "sha256:def456",
                    "mediaType": "application/vnd.oci.image.manifest.v1+json",
                    "architecture": "amd64",
                    "os": "linux",
                }
            ],
        }
    ]
    client.list_docker_images.assert_called_once_with(
        parent="projects/test-project/locations/us-central1/repositories/repo",
    )


def test_get_apt_artifacts_uses_generic_packages_and_versions():
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
    client.list_packages.assert_called_once_with(
        parent="projects/test-project/locations/us-east1/repositories/repo",
    )
    client.list_versions.assert_called_once_with(
        parent="projects/test-project/locations/us-east1/repositories/repo/packages/curl",
    )


def test_get_yum_artifacts_uses_generic_packages_and_versions():
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
    client.list_packages.assert_called_once_with(
        parent="projects/test-project/locations/us-east1/repositories/repo",
    )
    client.list_versions.assert_called_once_with(
        parent="projects/test-project/locations/us-east1/repositories/repo/packages/bash",
    )


def test_get_go_modules_reconstructs_modules_from_generic_packages_and_versions():
    client = _make_os_package_client("example.com%2Fpkg", "v1.2.3")

    modules = get_go_modules(
        client,
        "projects/test-project/locations/us-east1/repositories/repo",
    )

    assert modules == [
        {
            "name": "projects/test-project/locations/us-east1/repositories/repo/packages/example.com%2Fpkg/versions/v1.2.3",
            "version": "v1.2.3",
            "createTime": "2024-01-06T00:00:00Z",
            "updateTime": "2024-01-06T00:00:00Z",
            "packageName": "example.com/pkg",
        }
    ]
    client.list_packages.assert_called_once_with(
        parent="projects/test-project/locations/us-east1/repositories/repo",
    )
    client.list_versions.assert_called_once_with(
        parent="projects/test-project/locations/us-east1/repositories/repo/packages/example.com%2Fpkg",
    )
