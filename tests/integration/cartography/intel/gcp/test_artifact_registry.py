from typing import Any
from typing import cast
from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.gcp.artifact_registry import sync
from cartography.intel.gcp.artifact_registry.artifact import load_docker_images
from cartography.intel.gcp.artifact_registry.artifact import transform_apt_artifacts
from cartography.intel.gcp.artifact_registry.artifact import transform_docker_images
from cartography.intel.gcp.artifact_registry.artifact import transform_maven_artifacts
from cartography.intel.gcp.artifact_registry.artifact import transform_yum_artifacts
from cartography.intel.gcp.artifact_registry.manifest import load_manifests
from cartography.intel.gcp.artifact_registry.repository import (
    ArtifactRegistryRepositorySyncResult,
)
from tests.data.gcp.artifact_registry import MOCK_APT_ARTIFACTS
from tests.data.gcp.artifact_registry import MOCK_DOCKER_IMAGES
from tests.data.gcp.artifact_registry import MOCK_HELM_CHARTS
from tests.data.gcp.artifact_registry import MOCK_MAVEN_ARTIFACTS
from tests.data.gcp.artifact_registry import MOCK_REPOSITORIES
from tests.data.gcp.artifact_registry import MOCK_YUM_ARTIFACTS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_PROJECT_ID = "test-project"
TEST_DOCKER_REPO_ID = (
    "projects/test-project/locations/us-central1/repositories/docker-repo"
)
TEST_MAVEN_REPO_ID = (
    "projects/test-project/locations/us-central1/repositories/maven-repo"
)
TEST_APT_REPO_ID = "projects/test-project/locations/us-east1/repositories/apt-repo"
TEST_YUM_REPO_ID = "projects/test-project/locations/us-east1/repositories/yum-repo"
TEST_DOCKER_IMAGE_ID = "projects/test-project/locations/us-central1/repositories/docker-repo/dockerImages/my-app@sha256:abc123"
TEST_HELM_CHART_ID = "projects/test-project/locations/us-central1/repositories/docker-repo/dockerImages/my-chart@sha256:xyz789"
TEST_MAVEN_ARTIFACT_ID = "projects/test-project/locations/us-central1/repositories/maven-repo/mavenArtifacts/com.example:my-lib:1.0.0"
TEST_APT_ARTIFACT_ID = "projects/test-project/locations/us-east1/repositories/apt-repo/packages/curl/versions/7.88.1"
TEST_YUM_ARTIFACT_ID = "projects/test-project/locations/us-east1/repositories/yum-repo/packages/bash/versions/5.2.26"
TEST_PLATFORM_IMAGE_AMD64_ID = f"{TEST_DOCKER_IMAGE_ID}@sha256:def456"
TEST_PLATFORM_IMAGE_ARM64_ID = f"{TEST_DOCKER_IMAGE_ID}@sha256:ghi789"
TEST_SINGLE_IMAGE_MEDIA_TYPE = "application/vnd.oci.image.manifest.v1+json"
TEST_MANIFEST_LIST_MEDIA_TYPE = "application/vnd.oci.image.index.v1+json"


def _create_prerequisite_nodes(neo4j_session):
    neo4j_session.run(
        "MERGE (p:GCPProject {id: $project_id}) SET p.lastupdated = $tag",
        project_id=TEST_PROJECT_ID,
        tag=TEST_UPDATE_TAG,
    )


def _clear_gar_project(neo4j_session, project_id: str):
    neo4j_session.run(
        """
        MATCH (n)
        WHERE n.id = $project_id
        OR n.id STARTS WITH $resource_prefix
        OR n.project_id = $project_id
        DETACH DELETE n
        """,
        project_id=project_id,
        resource_prefix=f"projects/{project_id}/",
    )


def _create_gar_project_and_repositories(
    neo4j_session,
    project_id: str,
    repository_ids: list[str],
):
    neo4j_session.run(
        "MERGE (p:GCPProject {id: $project_id}) SET p.lastupdated = $tag",
        project_id=project_id,
        tag=TEST_UPDATE_TAG,
    )
    for repository_id in repository_ids:
        neo4j_session.run(
            """
            MERGE (repo:GCPArtifactRegistryRepository {id: $repository_id})
            SET repo.lastupdated = $tag
            """,
            repository_id=repository_id,
            tag=TEST_UPDATE_TAG,
        )


def _make_docker_image(
    repository_id: str,
    index: int,
    media_type: str = TEST_SINGLE_IMAGE_MEDIA_TYPE,
) -> dict[str, Any]:
    digest = f"sha256:{index:064x}"
    name = f"{repository_id}/dockerImages/app-{index}@{digest}"
    return {
        "id": name,
        "name": name.split("/")[-1],
        "uri": f"us-central1-docker.pkg.dev/test-project/repo/app-{index}@{digest}",
        "digest": digest,
        "tags": ["latest"] if index % 2 == 0 else [],
        "image_size_bytes": str(index),
        "media_type": media_type,
        "upload_time": "2024-01-10T00:00:00Z",
        "build_time": "2024-01-10T00:00:00Z",
        "update_time": "2024-01-10T00:00:00Z",
        "repository_id": repository_id,
        "project_id": repository_id.split("/")[1],
    }


def _make_platform_image(parent_artifact_id: str, project_id: str, index: int) -> dict:
    digest = f"sha256:{index:064x}"
    return {
        "id": f"{parent_artifact_id}@{digest}",
        "digest": digest,
        "architecture": "amd64" if index % 2 == 0 else "arm64",
        "os": "linux",
        "os_version": None,
        "os_features": None,
        "variant": None,
        "media_type": TEST_SINGLE_IMAGE_MEDIA_TYPE,
        "parent_artifact_id": parent_artifact_id,
        "project_id": project_id,
    }


def _mock_get_docker_images(client, repo_name):
    return MOCK_DOCKER_IMAGES + MOCK_HELM_CHARTS


def _mock_get_maven_artifacts(client, repo_name):
    return MOCK_MAVEN_ARTIFACTS


def _mock_get_apt_artifacts(client, repo_name):
    return MOCK_APT_ARTIFACTS


def _mock_get_yum_artifacts(client, repo_name):
    return MOCK_YUM_ARTIFACTS


@patch(
    "cartography.intel.gcp.artifact_registry.artifact.FORMAT_HANDLERS",
    {
        "DOCKER": (_mock_get_docker_images, transform_docker_images),
        "MAVEN": (_mock_get_maven_artifacts, transform_maven_artifacts),
        "APT": (_mock_get_apt_artifacts, transform_apt_artifacts),
        "YUM": (_mock_get_yum_artifacts, transform_yum_artifacts),
    },
)
@patch(
    "cartography.intel.gcp.artifact_registry.repository.get_artifact_registry_repositories",
    return_value=ArtifactRegistryRepositorySyncResult(
        cast(list[dict[str, Any]], MOCK_REPOSITORIES),
        True,
    ),
)
@patch(
    "cartography.intel.gcp.artifact_registry.build_artifact_registry_client",
    return_value=MagicMock(name="artifact-registry-client"),
)
def test_sync_artifact_registry(
    mock_build_artifact_registry_client,
    mock_get_repositories,
    neo4j_session,
):
    _create_prerequisite_nodes(neo4j_session)

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    mock_credentials = MagicMock()

    sync(
        neo4j_session,
        mock_credentials,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )
    mock_build_artifact_registry_client.assert_called_once_with(
        credentials=mock_credentials,
    )

    # Assert: Check repository nodes
    assert check_nodes(neo4j_session, "GCPArtifactRegistryRepository", ["id"]) == {
        (TEST_DOCKER_REPO_ID,),
        (TEST_MAVEN_REPO_ID,),
        (TEST_APT_REPO_ID,),
        (TEST_YUM_REPO_ID,),
    }

    # Assert: Check container image nodes
    assert check_nodes(neo4j_session, "GCPArtifactRegistryContainerImage", ["id"]) == {
        (TEST_DOCKER_IMAGE_ID,),
    }

    # Assert: Check Helm chart nodes
    assert check_nodes(neo4j_session, "GCPArtifactRegistryHelmChart", ["id"]) == {
        (TEST_HELM_CHART_ID,),
    }

    # Assert: Check language package nodes (Maven artifact)
    assert check_nodes(neo4j_session, "GCPArtifactRegistryLanguagePackage", ["id"]) == {
        (TEST_MAVEN_ARTIFACT_ID,),
    }

    # Assert: Check generic artifact nodes (APT and YUM artifacts)
    assert check_nodes(neo4j_session, "GCPArtifactRegistryGenericArtifact", ["id"]) == {
        (TEST_APT_ARTIFACT_ID,),
        (TEST_YUM_ARTIFACT_ID,),
    }

    # Assert: Check platform image nodes
    assert check_nodes(neo4j_session, "GCPArtifactRegistryPlatformImage", ["id"]) == {
        (TEST_PLATFORM_IMAGE_AMD64_ID,),
        (TEST_PLATFORM_IMAGE_ARM64_ID,),
    }

    # Assert: Check GCPProject -> GCPArtifactRegistryRepository relationships
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPArtifactRegistryRepository",
        "id",
        "RESOURCE",
    ) == {
        (TEST_PROJECT_ID, TEST_DOCKER_REPO_ID),
        (TEST_PROJECT_ID, TEST_MAVEN_REPO_ID),
        (TEST_PROJECT_ID, TEST_APT_REPO_ID),
        (TEST_PROJECT_ID, TEST_YUM_REPO_ID),
    }

    # Assert: Check GCPProject -> GCPArtifactRegistryContainerImage relationships
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPArtifactRegistryContainerImage",
        "id",
        "RESOURCE",
    ) == {(TEST_PROJECT_ID, TEST_DOCKER_IMAGE_ID)}

    # Assert: Check GCPProject -> GCPArtifactRegistryHelmChart relationships
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPArtifactRegistryHelmChart",
        "id",
        "RESOURCE",
    ) == {(TEST_PROJECT_ID, TEST_HELM_CHART_ID)}

    # Assert: Check GCPArtifactRegistryRepository -> GCPArtifactRegistryContainerImage relationships
    assert check_rels(
        neo4j_session,
        "GCPArtifactRegistryRepository",
        "id",
        "GCPArtifactRegistryContainerImage",
        "id",
        "CONTAINS",
    ) == {(TEST_DOCKER_REPO_ID, TEST_DOCKER_IMAGE_ID)}

    # Assert: Check GCPArtifactRegistryRepository -> GCPArtifactRegistryHelmChart relationships
    assert check_rels(
        neo4j_session,
        "GCPArtifactRegistryRepository",
        "id",
        "GCPArtifactRegistryHelmChart",
        "id",
        "CONTAINS",
    ) == {(TEST_DOCKER_REPO_ID, TEST_HELM_CHART_ID)}

    # Assert: Check GCPArtifactRegistryRepository -> GCPArtifactRegistryLanguagePackage relationships
    assert check_rels(
        neo4j_session,
        "GCPArtifactRegistryRepository",
        "id",
        "GCPArtifactRegistryLanguagePackage",
        "id",
        "CONTAINS",
    ) == {(TEST_MAVEN_REPO_ID, TEST_MAVEN_ARTIFACT_ID)}

    # Assert: Check GCPProject -> GCPArtifactRegistryGenericArtifact relationships
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPArtifactRegistryGenericArtifact",
        "id",
        "RESOURCE",
    ) == {
        (TEST_PROJECT_ID, TEST_APT_ARTIFACT_ID),
        (TEST_PROJECT_ID, TEST_YUM_ARTIFACT_ID),
    }

    # Assert: Check GCPArtifactRegistryRepository -> GCPArtifactRegistryGenericArtifact relationships
    assert check_rels(
        neo4j_session,
        "GCPArtifactRegistryRepository",
        "id",
        "GCPArtifactRegistryGenericArtifact",
        "id",
        "CONTAINS",
    ) == {
        (TEST_APT_REPO_ID, TEST_APT_ARTIFACT_ID),
        (TEST_YUM_REPO_ID, TEST_YUM_ARTIFACT_ID),
    }

    # Assert: Check GCPArtifactRegistryContainerImage -> GCPArtifactRegistryPlatformImage relationships
    assert check_rels(
        neo4j_session,
        "GCPArtifactRegistryContainerImage",
        "id",
        "GCPArtifactRegistryPlatformImage",
        "id",
        "HAS_MANIFEST",
    ) == {
        (TEST_DOCKER_IMAGE_ID, TEST_PLATFORM_IMAGE_AMD64_ID),
        (TEST_DOCKER_IMAGE_ID, TEST_PLATFORM_IMAGE_ARM64_ID),
    }

    # Assert: Check ontology-standard manifest-list -> platform-image relationships
    assert check_rels(
        neo4j_session,
        "GCPArtifactRegistryContainerImage",
        "id",
        "GCPArtifactRegistryPlatformImage",
        "id",
        "CONTAINS_IMAGE",
    ) == {
        (TEST_DOCKER_IMAGE_ID, TEST_PLATFORM_IMAGE_AMD64_ID),
        (TEST_DOCKER_IMAGE_ID, TEST_PLATFORM_IMAGE_ARM64_ID),
    }


def test_load_docker_images_large_grouped_repository_relationships_are_idempotent(
    neo4j_session,
):
    project_id = "test-gar-large-container-project"
    repo_1 = f"projects/{project_id}/locations/us-central1/repositories/docker-repo-1"
    repo_2 = f"projects/{project_id}/locations/us-central1/repositories/docker-repo-2"
    _clear_gar_project(neo4j_session, project_id)
    _create_gar_project_and_repositories(neo4j_session, project_id, [repo_1, repo_2])

    docker_images = [
        _make_docker_image(
            repo_1,
            index,
            (
                TEST_MANIFEST_LIST_MEDIA_TYPE
                if index == 0
                else TEST_SINGLE_IMAGE_MEDIA_TYPE
            ),
        )
        for index in range(1005)
    ]
    docker_images.extend(
        _make_docker_image(repo_2, index) for index in range(1005, 1210)
    )

    load_docker_images(neo4j_session, docker_images, project_id, TEST_UPDATE_TAG)

    assert (
        neo4j_session.run(
            """
            MATCH (:GCPProject {id: $project_id})
            -[r:RESOURCE]->(:GCPArtifactRegistryContainerImage)
            RETURN count(r) AS count
            """,
            project_id=project_id,
        ).single()["count"]
        == 1210
    )
    assert (
        neo4j_session.run(
            """
            MATCH (:GCPArtifactRegistryRepository {id: $repo_id})
            -[r:CONTAINS]->(:GCPArtifactRegistryContainerImage)
            RETURN count(r) AS count
            """,
            repo_id=repo_1,
        ).single()["count"]
        == 1005
    )
    assert (
        neo4j_session.run(
            """
            MATCH (:GCPArtifactRegistryRepository {id: $repo_id})
            -[r:CONTAINS]->(:GCPArtifactRegistryContainerImage)
            RETURN count(r) AS count
            """,
            repo_id=repo_2,
        ).single()["count"]
        == 205
    )

    first_image_id = docker_images[0]["id"]
    result = neo4j_session.run(
        """
        MATCH (:GCPProject {id: $project_id})
        -[r:RESOURCE]->(image:GCPArtifactRegistryContainerImage {id: $image_id})
        RETURN
            image.firstseen AS node_firstseen,
            image._module_name AS node_module_name,
            image._ont_digest AS ont_digest,
            image._ont_uri AS ont_uri,
            labels(image) AS labels,
            r.firstseen AS rel_firstseen,
            r.lastupdated AS rel_lastupdated,
            r._module_name AS rel_module_name,
            r._module_version AS rel_module_version
        """,
        project_id=project_id,
        image_id=first_image_id,
    ).single()
    assert result["node_module_name"] == "cartography:gcp"
    assert result["ont_digest"] == docker_images[0]["digest"]
    assert result["ont_uri"] == docker_images[0]["uri"]
    assert "ImageManifestList" in result["labels"]
    assert "Image" not in result["labels"]
    assert result["rel_lastupdated"] == TEST_UPDATE_TAG
    assert result["rel_module_name"] == "cartography:gcp"
    assert result["rel_module_version"]

    first_node_firstseen = result["node_firstseen"]
    first_rel_firstseen = result["rel_firstseen"]
    docker_images[0]["media_type"] = TEST_SINGLE_IMAGE_MEDIA_TYPE
    load_docker_images(neo4j_session, docker_images, project_id, TEST_UPDATE_TAG + 1)

    result = neo4j_session.run(
        """
        MATCH (:GCPProject {id: $project_id})
        -[r:RESOURCE]->(image:GCPArtifactRegistryContainerImage {id: $image_id})
        RETURN
            image.firstseen AS node_firstseen,
            image.lastupdated AS node_lastupdated,
            labels(image) AS labels,
            r.firstseen AS rel_firstseen,
            r.lastupdated AS rel_lastupdated
        """,
        project_id=project_id,
        image_id=first_image_id,
    ).single()
    assert result["node_firstseen"] == first_node_firstseen
    assert result["rel_firstseen"] == first_rel_firstseen
    assert result["node_lastupdated"] == TEST_UPDATE_TAG + 1
    assert result["rel_lastupdated"] == TEST_UPDATE_TAG + 1
    assert "Image" in result["labels"]
    assert "ImageManifestList" not in result["labels"]


def test_load_manifests_large_parent_relationships_are_idempotent(neo4j_session):
    project_id = "test-gar-large-platform-project"
    repo_id = f"projects/{project_id}/locations/us-central1/repositories/docker-repo"
    _clear_gar_project(neo4j_session, project_id)
    _create_gar_project_and_repositories(neo4j_session, project_id, [repo_id])

    parent_images = [
        _make_docker_image(repo_id, 1, TEST_MANIFEST_LIST_MEDIA_TYPE),
        _make_docker_image(repo_id, 2, TEST_MANIFEST_LIST_MEDIA_TYPE),
    ]
    load_docker_images(neo4j_session, parent_images, project_id, TEST_UPDATE_TAG)

    platform_images = [
        _make_platform_image(parent_images[0]["id"], project_id, index)
        for index in range(1005)
    ]
    platform_images.extend(
        _make_platform_image(parent_images[1]["id"], project_id, index)
        for index in range(1005, 1210)
    )

    load_manifests(neo4j_session, platform_images, project_id, TEST_UPDATE_TAG)

    for rel_label in ("HAS_MANIFEST", "CONTAINS_IMAGE"):
        assert (
            neo4j_session.run(
                f"""
                MATCH (:GCPArtifactRegistryContainerImage)
                -[r:{rel_label}]->(:GCPArtifactRegistryPlatformImage)
                WHERE startNode(r).project_id = $project_id
                RETURN count(r) AS count
                """,
                project_id=project_id,
            ).single()["count"]
            == 1210
        )

    first_platform_id = platform_images[0]["id"]
    result = neo4j_session.run(
        """
        MATCH (:GCPProject {id: $project_id})
        -[r:RESOURCE]->(image:GCPArtifactRegistryPlatformImage {id: $image_id})
        RETURN
            image.firstseen AS node_firstseen,
            image._module_name AS node_module_name,
            image._ont_digest AS ont_digest,
            image._ont_architecture AS ont_architecture,
            image._ont_os AS ont_os,
            labels(image) AS labels,
            r.firstseen AS rel_firstseen,
            r.lastupdated AS rel_lastupdated,
            r._module_name AS rel_module_name,
            r._module_version AS rel_module_version
        """,
        project_id=project_id,
        image_id=first_platform_id,
    ).single()
    assert result["node_module_name"] == "cartography:gcp"
    assert result["ont_digest"] == platform_images[0]["digest"]
    assert result["ont_architecture"] == platform_images[0]["architecture"]
    assert result["ont_os"] == platform_images[0]["os"]
    assert "Image" in result["labels"]
    assert result["rel_lastupdated"] == TEST_UPDATE_TAG
    assert result["rel_module_name"] == "cartography:gcp"
    assert result["rel_module_version"]

    first_node_firstseen = result["node_firstseen"]
    first_rel_firstseen = result["rel_firstseen"]
    parent_rel_result = neo4j_session.run(
        """
        MATCH (:GCPArtifactRegistryContainerImage {id: $parent_id})
        -[has_manifest:HAS_MANIFEST]->
        (:GCPArtifactRegistryPlatformImage {id: $image_id})
        MATCH (:GCPArtifactRegistryContainerImage {id: $parent_id})
        -[contains_image:CONTAINS_IMAGE]->
        (:GCPArtifactRegistryPlatformImage {id: $image_id})
        RETURN
            has_manifest.firstseen AS has_manifest_firstseen,
            has_manifest.lastupdated AS has_manifest_lastupdated,
            has_manifest._module_name AS has_manifest_module_name,
            has_manifest._module_version AS has_manifest_module_version,
            contains_image.firstseen AS contains_image_firstseen,
            contains_image.lastupdated AS contains_image_lastupdated,
            contains_image._module_name AS contains_image_module_name,
            contains_image._module_version AS contains_image_module_version
        """,
        parent_id=platform_images[0]["parent_artifact_id"],
        image_id=first_platform_id,
    ).single()
    assert parent_rel_result["has_manifest_lastupdated"] == TEST_UPDATE_TAG
    assert parent_rel_result["has_manifest_module_name"] == "cartography:gcp"
    assert parent_rel_result["has_manifest_module_version"]
    assert parent_rel_result["contains_image_lastupdated"] == TEST_UPDATE_TAG
    assert parent_rel_result["contains_image_module_name"] == "cartography:gcp"
    assert parent_rel_result["contains_image_module_version"]

    load_manifests(neo4j_session, platform_images, project_id, TEST_UPDATE_TAG + 1)

    result = neo4j_session.run(
        """
        MATCH (:GCPProject {id: $project_id})
        -[r:RESOURCE]->(image:GCPArtifactRegistryPlatformImage {id: $image_id})
        RETURN
            image.firstseen AS node_firstseen,
            image.lastupdated AS node_lastupdated,
            r.firstseen AS rel_firstseen,
            r.lastupdated AS rel_lastupdated
        """,
        project_id=project_id,
        image_id=first_platform_id,
    ).single()
    assert result["node_firstseen"] == first_node_firstseen
    assert result["rel_firstseen"] == first_rel_firstseen
    assert result["node_lastupdated"] == TEST_UPDATE_TAG + 1
    assert result["rel_lastupdated"] == TEST_UPDATE_TAG + 1
    parent_rel_result_after_rerun = neo4j_session.run(
        """
        MATCH (:GCPArtifactRegistryContainerImage {id: $parent_id})
        -[has_manifest:HAS_MANIFEST]->
        (:GCPArtifactRegistryPlatformImage {id: $image_id})
        MATCH (:GCPArtifactRegistryContainerImage {id: $parent_id})
        -[contains_image:CONTAINS_IMAGE]->
        (:GCPArtifactRegistryPlatformImage {id: $image_id})
        RETURN
            has_manifest.firstseen AS has_manifest_firstseen,
            has_manifest.lastupdated AS has_manifest_lastupdated,
            contains_image.firstseen AS contains_image_firstseen,
            contains_image.lastupdated AS contains_image_lastupdated
        """,
        parent_id=platform_images[0]["parent_artifact_id"],
        image_id=first_platform_id,
    ).single()
    assert (
        parent_rel_result_after_rerun["has_manifest_firstseen"]
        == parent_rel_result["has_manifest_firstseen"]
    )
    assert parent_rel_result_after_rerun["has_manifest_lastupdated"] == (
        TEST_UPDATE_TAG + 1
    )
    assert (
        parent_rel_result_after_rerun["contains_image_firstseen"]
        == parent_rel_result["contains_image_firstseen"]
    )
    assert parent_rel_result_after_rerun["contains_image_lastupdated"] == (
        TEST_UPDATE_TAG + 1
    )
