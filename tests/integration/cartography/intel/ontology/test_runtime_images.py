import cartography.intel.ontology.runtime_images
from cartography.analysis.ontology.analysis import RESOLVED_IMAGE_JOBS
from cartography.intel.docker_scout.scanner import attach_public_image_to_target_image
from cartography.intel.docker_scout.scanner import load_public_image
from cartography.intel.trivy import _get_runtime_image_scan_targets_and_aliases
from cartography.intel.trivy import _prepare_trivy_data
from cartography.intel.trivy.scanner import sync_single_image
from cartography.util import run_typed_analysis_job
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_DIGEST = "sha256:deadbeef"


def _sync_runtime_images(neo4j_session, update_tag=TEST_UPDATE_TAG):
    params = {"UPDATE_TAG": update_tag}
    cartography.intel.ontology.runtime_images.sync(
        neo4j_session,
        update_tag,
        params,
    )
    for job in RESOLVED_IMAGE_JOBS:
        run_typed_analysis_job(job, neo4j_session, params)


def test_runtime_image_supports_scan_and_scout_without_base_lineage(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        CREATE (first:Container {id: 'container-1'})
        SET first._ont_state = 'running',
            first._ont_image = 'ghcr.io/subimagesec/subimage-outpost:latest',
            first._ont_image_digest = $digest
        CREATE (second:Container {id: 'container-2'})
        SET second._ont_state = 'running',
            second._ont_image = 'ghcr.io/subimagesec/subimage-outpost:v1',
            second._ont_image_digest = $digest
        CREATE (function:Function {id: 'function-1'})
        SET function._ont_deployment_type = 'container',
            function._ont_image = 'ghcr.io/subimagesec/subimage-outpost:latest',
            function._ont_image_digest = $digest
        """,
        digest=TEST_DIGEST,
    )

    # Act
    _sync_runtime_images(neo4j_session)
    load_public_image(
        neo4j_session,
        {
            "id": "alpine:3.20",
            "name": "alpine",
            "tag": "3.20",
            "digest": "sha256:base",
        },
        TEST_UPDATE_TAG,
    )
    attach_public_image_to_target_image(
        neo4j_session,
        {"id": "alpine:3.20", "target_digest": "deadbeef"},
        TEST_UPDATE_TAG,
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "RuntimeImage",
        ["id", "digest", "uri", "_ont_digest"],
    ) == {
        (
            f"runtime-image:{TEST_DIGEST}",
            TEST_DIGEST,
            f"ghcr.io/subimagesec/subimage-outpost@{TEST_DIGEST}",
            TEST_DIGEST,
        ),
    }
    assert neo4j_session.run(
        "MATCH (image:RuntimeImage) RETURN image.runtime_refs AS refs",
    ).single()["refs"] == [
        "ghcr.io/subimagesec/subimage-outpost:latest",
        "ghcr.io/subimagesec/subimage-outpost:v1",
    ]
    assert check_rels(
        neo4j_session,
        "Container",
        "id",
        "RuntimeImage",
        "id",
        "HAS_IMAGE",
    ) == {
        ("container-1", f"runtime-image:{TEST_DIGEST}"),
        ("container-2", f"runtime-image:{TEST_DIGEST}"),
    }
    assert check_rels(
        neo4j_session,
        "Function",
        "id",
        "RuntimeImage",
        "id",
        "RESOLVED_IMAGE",
    ) == {("function-1", f"runtime-image:{TEST_DIGEST}")}
    assert check_rels(
        neo4j_session,
        "RuntimeImage",
        "id",
        "DockerScoutPublicImage",
        "id",
        "BUILT_ON",
    ) == {(f"runtime-image:{TEST_DIGEST}", "alpine:3.20")}
    assert (
        neo4j_session.run(
            "MATCH (:RuntimeImage)-[r:BUILT_FROM]->() RETURN count(r) AS count",
        ).single()["count"]
        == 0
    )
    runtime_targets = _get_runtime_image_scan_targets_and_aliases(neo4j_session)
    assert runtime_targets == (
        {
            "ghcr.io/subimagesec/subimage-outpost:latest",
            "ghcr.io/subimagesec/subimage-outpost:v1",
        },
        {
            f"ghcr.io/subimagesec/subimage-outpost@{TEST_DIGEST}": (
                "ghcr.io/subimagesec/subimage-outpost:v1"
            ),
        },
        {
            "ghcr.io/subimagesec/subimage-outpost:latest": {TEST_DIGEST},
            "ghcr.io/subimagesec/subimage-outpost:v1": {TEST_DIGEST},
            f"ghcr.io/subimagesec/subimage-outpost@{TEST_DIGEST}": {TEST_DIGEST},
        },
    )

    platform_digest = "sha256:platform"
    trivy_data = {
        "ArtifactName": "ghcr.io/subimagesec/subimage-outpost:latest",
        "Metadata": {
            "RepoTags": ["ghcr.io/subimagesec/subimage-outpost:latest"],
            "RepoDigests": [f"ghcr.io/subimagesec/subimage-outpost@{platform_digest}"],
        },
        "Results": [
            {
                "Class": "os-pkgs",
                "Type": "alpine",
                "Vulnerabilities": [
                    {
                        "VulnerabilityID": "CVE-2026-0001",
                        "PkgName": "libcrypto",
                        "InstalledVersion": "1.0",
                        "FixedVersion": "1.1",
                        "Severity": "HIGH",
                    },
                ],
            },
        ],
    }
    prepared = _prepare_trivy_data(
        trivy_data,
        image_uris=runtime_targets[0],
        digest_aliases=runtime_targets[1],
        runtime_target_digests=runtime_targets[2],
        source="runtime-image.json",
    )
    assert prepared is not None
    prepared_data, display_uri, image_digest_override = prepared
    assert image_digest_override == TEST_DIGEST
    sync_single_image(
        neo4j_session,
        prepared_data,
        display_uri,
        TEST_UPDATE_TAG,
        image_digest_override=image_digest_override,
    )
    assert check_rels(
        neo4j_session,
        "TrivyPackage",
        "id",
        "RuntimeImage",
        "id",
        "DEPLOYED",
    ) == {("1.0|libcrypto", f"runtime-image:{TEST_DIGEST}")}
    assert check_rels(
        neo4j_session,
        "TrivyImageFinding",
        "id",
        "RuntimeImage",
        "id",
        "AFFECTS",
    ) == {("TIF|CVE-2026-0001", f"runtime-image:{TEST_DIGEST}")}


def test_provider_image_replaces_runtime_image(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        CREATE (container:Container {id: 'container-1'})
        SET container._ont_state = 'running',
            container._ont_image = 'ghcr.io/example/app:latest',
            container._ont_image_digest = $digest
        """,
        digest=TEST_DIGEST,
    )
    _sync_runtime_images(neo4j_session)
    neo4j_session.run(
        """
        MATCH (container:Container {id: 'container-1'})
        CREATE (image:Image:GitHubContainerImage {id: $digest})
        SET image.digest = $digest, image._ont_digest = $digest
        CREATE (container)-[:HAS_IMAGE {lastupdated: $update_tag}]->(image)
        """,
        digest=TEST_DIGEST,
        update_tag=TEST_UPDATE_TAG + 1,
    )

    # Act
    _sync_runtime_images(neo4j_session, TEST_UPDATE_TAG + 1)

    # Assert
    assert check_nodes(neo4j_session, "RuntimeImage", ["id"]) == set()
    assert check_rels(
        neo4j_session,
        "Container",
        "id",
        "GitHubContainerImage",
        "id",
        "HAS_IMAGE",
    ) == {("container-1", TEST_DIGEST)}
