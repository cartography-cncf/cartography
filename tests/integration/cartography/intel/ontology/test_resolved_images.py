"""
Integration test for the Container/Function -> Image RESOLVED_IMAGE analysis job.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.cloudrun.job as cloudrun_job
import cartography.intel.gcp.cloudrun.revision as cloudrun_revision
import cartography.intel.gcp.cloudrun.service as cloudrun_service
from cartography.util import run_analysis_job
from tests.data.gcp.cloudrun import MOCK_JOB_WITH_DIGEST
from tests.data.gcp.cloudrun import MOCK_REVISION_WITH_DIGEST
from tests.data.gcp.cloudrun import MOCK_SERVICE_WITH_DIGEST
from tests.data.gcp.cloudrun import TEST_JOB_PRIMARY_DIGEST
from tests.data.gcp.cloudrun import TEST_REVISION_PRIMARY_DIGEST
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_PROJECT_ID = "test-project"
TEST_SERVICE_ID = "projects/test-project/locations/us-central1/services/test-service"
TEST_REVISION_ID = "projects/test-project/locations/us-central1/services/test-service/revisions/test-service-00001-abc"
TEST_JOB_ID = "projects/test-project/locations/us-west1/jobs/test-job"
TEST_CLOUD_RUN_LOCATIONS = [
    "projects/test-project/locations/us-central1",
    "projects/test-project/locations/us-west1",
]


def _image(
    image_id: str,
    image_type: str = "image",
    architecture: str | None = None,
    child_image_ids: list[str] | None = None,
) -> dict:
    return {
        "id": image_id,
        "type": image_type,
        "architecture": architecture,
        "child_image_ids": child_image_ids or [],
    }


def _image_tag(tag_id: str, image_ids: list[str]) -> dict:
    return {
        "id": tag_id,
        "image_ids": image_ids,
    }


def _workload(
    workload_id: str,
    architecture_normalized: str | None = None,
    image_ids: list[str] | None = None,
    image_tag_ids: list[str] | None = None,
) -> dict:
    return {
        "id": workload_id,
        "architecture_normalized": architecture_normalized,
        "image_ids": image_ids or [],
        "image_tag_ids": image_tag_ids or [],
    }


def _load_resolved_image_prerequisites(
    neo4j_session,
    images: list[dict],
    image_tags: list[dict] | None = None,
    containers: list[dict] | None = None,
    functions: list[dict] | None = None,
) -> None:
    image_tags = image_tags or []
    containers = containers or []
    functions = functions or []

    neo4j_session.run(
        """
        UNWIND $images AS image
        WITH image WHERE image.type = 'image'
        MERGE (i:ResolvedImageTestImage:Image {id: image.id})
        SET i.type = image.type,
            i._ont_architecture = image.architecture,
            i.lastupdated = $update_tag
        """,
        images=images,
        update_tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        """
        UNWIND $images AS image
        WITH image WHERE image.type = 'manifest_list'
        MERGE (i:ResolvedImageTestImage:ImageManifestList {id: image.id})
        SET i.type = image.type,
            i._ont_architecture = image.architecture,
            i.lastupdated = $update_tag
        """,
        images=images,
        update_tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        """
        UNWIND $images AS image
        UNWIND image.child_image_ids AS child_id
        MATCH (parent:ResolvedImageTestImage {id: image.id})
        MATCH (child:ResolvedImageTestImage {id: child_id})
        MERGE (parent)-[r:CONTAINS_IMAGE]->(child)
        SET r.lastupdated = $update_tag
        """,
        images=images,
        update_tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        """
        UNWIND $image_tags AS image_tag
        MERGE (tag:ResolvedImageTestImageTag:ImageTag {id: image_tag.id})
        SET tag.lastupdated = $update_tag
        WITH tag, image_tag
        UNWIND image_tag.image_ids AS image_id
        MATCH (image:ResolvedImageTestImage {id: image_id})
        MERGE (tag)-[r:IMAGE]->(image)
        SET r.lastupdated = $update_tag
        """,
        image_tags=image_tags,
        update_tag=TEST_UPDATE_TAG,
    )
    _load_workload_prerequisites(
        neo4j_session,
        "ResolvedImageTestContainer",
        "Container",
        containers,
    )
    _load_workload_prerequisites(
        neo4j_session,
        "ResolvedImageTestFunction",
        "Function",
        functions,
    )


def _load_workload_prerequisites(
    neo4j_session,
    test_label: str,
    ontology_label: str,
    workloads: list[dict],
) -> None:
    label = f"{test_label}:{ontology_label}"
    neo4j_session.run(
        f"""
        UNWIND $workloads AS workload
        MERGE (w:{label} {{id: workload.id}})
        SET w.architecture_normalized = workload.architecture_normalized,
            w.lastupdated = $update_tag
        WITH w, workload
        UNWIND workload.image_ids AS image_id
        MATCH (image:ResolvedImageTestImage {{id: image_id}})
        MERGE (w)-[r:HAS_IMAGE]->(image)
        SET r.lastupdated = $update_tag
        """,
        workloads=workloads,
        update_tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        f"""
        UNWIND $workloads AS workload
        MATCH (w:{label} {{id: workload.id}})
        UNWIND workload.image_tag_ids AS image_tag_id
        MATCH (image_tag:ResolvedImageTestImageTag {{id: image_tag_id}})
        MERGE (w)-[r:HAS_IMAGE]->(image_tag)
        SET r.lastupdated = $update_tag
        """,
        workloads=workloads,
        update_tag=TEST_UPDATE_TAG,
    )


def _run_resolved_image_analysis(neo4j_session) -> None:
    run_analysis_job(
        "resolved_image_analysis.json",
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )


def test_resolved_image_analysis_creates_rel_via_has_image(neo4j_session):
    """The analysis job should create RESOLVED_IMAGE from :Container to :Image over an existing HAS_IMAGE edge."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _load_resolved_image_prerequisites(
        neo4j_session,
        images=[_image("sha256:deadbeef")],
        containers=[_workload("container-1", image_ids=["sha256:deadbeef"])],
    )

    _run_resolved_image_analysis(neo4j_session)

    assert check_rels(
        neo4j_session,
        "Container",
        "id",
        "Image",
        "id",
        "RESOLVED_IMAGE",
    ) == {("container-1", "sha256:deadbeef")}


@patch("cartography.intel.gcp.cloudrun.service.get_services")
@patch("cartography.intel.gcp.cloudrun.revision.get_revisions")
@patch("cartography.intel.gcp.cloudrun.job.get_jobs")
def test_resolved_image_analysis_creates_rel_for_cloud_run(
    mock_get_jobs,
    mock_get_revisions,
    mock_get_services,
    neo4j_session,
):
    """Run Cloud Run service, revision and job through the real load path,
    then verify RESOLVED_IMAGE is created on the per-container :Container nodes
    for both Service and Job. Service and Job carry no ontology label of their
    own, and Revision is a pure versioning marker — none of them get
    RESOLVED_IMAGE.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Arrange: prerequisite nodes
    neo4j_session.run(
        "MERGE (p:GCPProject {id: $pid}) SET p.lastupdated = $tag",
        pid=TEST_PROJECT_ID,
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (sa:GCPServiceAccount {email: $e}) SET sa.lastupdated = $tag",
        e="test-sa@test-project.iam.gserviceaccount.com",
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (sa:GCPServiceAccount {email: $e}) SET sa.lastupdated = $tag",
        e="batch-sa@test-project.iam.gserviceaccount.com",
        tag=TEST_UPDATE_TAG,
    )

    # Arrange: image nodes that HAS_IMAGE will match (need :Image label for the analysis job)
    neo4j_session.run(
        """
        MERGE (i:Image:ECRImage {id: $digest})
        SET i.digest = $digest, i.lastupdated = $tag
        """,
        digest=TEST_REVISION_PRIMARY_DIGEST,
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        """
        MERGE (i:Image:ECRImage {id: $digest})
        SET i.digest = $digest, i.lastupdated = $tag
        """,
        digest=TEST_JOB_PRIMARY_DIGEST,
        tag=TEST_UPDATE_TAG,
    )

    # Act: sync Cloud Run through the real load path
    mock_get_services.return_value = MOCK_SERVICE_WITH_DIGEST
    mock_get_revisions.return_value = MOCK_REVISION_WITH_DIGEST
    mock_get_jobs.return_value = MOCK_JOB_WITH_DIGEST
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    mock_credentials = MagicMock()

    cloudrun_service.sync_services(
        neo4j_session,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
        TEST_CLOUD_RUN_LOCATIONS,
        mock_credentials,
    )
    cloudrun_revision.sync_revisions(
        neo4j_session,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
        TEST_CLOUD_RUN_LOCATIONS,
        mock_credentials,
    )
    cloudrun_job.sync_jobs(
        neo4j_session,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
        TEST_CLOUD_RUN_LOCATIONS,
        mock_credentials,
    )

    # Act: run the RESOLVED_IMAGE analysis job
    run_analysis_job(
        "resolved_image_analysis.json",
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert: no :Function RESOLVED_IMAGE — Service no longer carries :Function.
    assert (
        check_rels(
            neo4j_session,
            "Function",
            "id",
            "Image",
            "id",
            "RESOLVED_IMAGE",
        )
        == set()
    )

    # Assert: RESOLVED_IMAGE on :Container for both the Service-side and Job-side individual containers.
    service_primary_container_id = f"{TEST_SERVICE_ID}/containers/0"
    job_primary_container_id = f"{TEST_JOB_ID}/containers/0"
    assert check_rels(
        neo4j_session,
        "Container",
        "id",
        "Image",
        "id",
        "RESOLVED_IMAGE",
    ) == {
        (service_primary_container_id, TEST_REVISION_PRIMARY_DIGEST),
        (job_primary_container_id, TEST_JOB_PRIMARY_DIGEST),
    }

    # Assert: Revision has no RESOLVED_IMAGE (pure versioning marker).
    assert (
        check_rels(
            neo4j_session,
            "GCPCloudRunRevision",
            "id",
            "Image",
            "id",
            "RESOLVED_IMAGE",
        )
        == set()
    )

    # Assert: Service has no RESOLVED_IMAGE (orchestrator, no ontology label).
    assert (
        check_rels(
            neo4j_session,
            "GCPCloudRunService",
            "id",
            "Image",
            "id",
            "RESOLVED_IMAGE",
        )
        == set()
    )

    # Assert: Job has no RESOLVED_IMAGE (orchestrator, no ontology label).
    assert (
        check_rels(
            neo4j_session,
            "GCPCloudRunJob",
            "id",
            "Image",
            "id",
            "RESOLVED_IMAGE",
        )
        == set()
    )


def test_resolved_image_analysis_creates_rel_via_manifest_list(neo4j_session):
    """The analysis job should resolve a Container pointed at an ImageManifestList to the architecture-matching child Image."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _load_resolved_image_prerequisites(
        neo4j_session,
        images=[
            _image(
                "sha256:manifestlist",
                image_type="manifest_list",
                child_image_ids=["sha256:childamd64", "sha256:childarm64"],
            ),
            _image("sha256:childamd64", architecture="amd64"),
            _image("sha256:childarm64", architecture="arm64"),
        ],
        containers=[
            _workload(
                "container-ml-1",
                architecture_normalized="amd64",
                image_ids=["sha256:manifestlist"],
            ),
        ],
    )

    _run_resolved_image_analysis(neo4j_session)

    assert check_rels(
        neo4j_session,
        "Container",
        "id",
        "Image",
        "id",
        "RESOLVED_IMAGE",
    ) == {("container-ml-1", "sha256:childamd64")}


def test_resolved_image_analysis_creates_rel_via_container_image_tag(neo4j_session):
    """A Container HAS_IMAGE edge to an ImageTag should resolve to one concrete Image."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _load_resolved_image_prerequisites(
        neo4j_session,
        images=[_image("sha256:tagimage")],
        image_tags=[_image_tag("example/repo:latest", ["sha256:tagimage"])],
        containers=[
            _workload("container-tag-1", image_tag_ids=["example/repo:latest"]),
        ],
    )

    _run_resolved_image_analysis(neo4j_session)

    assert check_rels(
        neo4j_session,
        "Container",
        "id",
        "Image",
        "id",
        "RESOLVED_IMAGE",
    ) == {("container-tag-1", "sha256:tagimage")}


def test_resolved_image_analysis_creates_rel_via_container_image_tag_manifest_list(
    neo4j_session,
):
    """An ImageTag that points to an ImageManifestList should resolve to one architecture-matching child Image."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _load_resolved_image_prerequisites(
        neo4j_session,
        images=[
            _image(
                "sha256:tagmanifestlist",
                image_type="manifest_list",
                child_image_ids=["sha256:tagchildamd64", "sha256:tagchildarm64"],
            ),
            _image("sha256:tagchildamd64", architecture="amd64"),
            _image("sha256:tagchildarm64", architecture="arm64"),
        ],
        image_tags=[_image_tag("example/repo:latest", ["sha256:tagmanifestlist"])],
        containers=[
            _workload(
                "container-tag-ml-1",
                architecture_normalized="arm64",
                image_tag_ids=["example/repo:latest"],
            ),
        ],
    )

    _run_resolved_image_analysis(neo4j_session)

    assert check_rels(
        neo4j_session,
        "Container",
        "id",
        "Image",
        "id",
        "RESOLVED_IMAGE",
    ) == {("container-tag-ml-1", "sha256:tagchildarm64")}


def test_resolved_image_analysis_skips_container_image_tag_manifest_list_without_architecture(
    neo4j_session,
):
    """An ImageTag to ImageManifestList path should not resolve when the Container architecture is unknown."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _load_resolved_image_prerequisites(
        neo4j_session,
        images=[
            _image(
                "sha256:tagmanifestlist",
                image_type="manifest_list",
                child_image_ids=["sha256:tagchildamd64"],
            ),
            _image("sha256:tagchildamd64", architecture="amd64"),
        ],
        image_tags=[_image_tag("example/repo:latest", ["sha256:tagmanifestlist"])],
        containers=[
            _workload(
                "container-tag-ml-no-arch", image_tag_ids=["example/repo:latest"]
            ),
        ],
    )

    _run_resolved_image_analysis(neo4j_session)

    assert (
        check_rels(
            neo4j_session,
            "Container",
            "id",
            "Image",
            "id",
            "RESOLVED_IMAGE",
        )
        == set()
    )


def test_resolved_image_analysis_creates_rel_via_function_image_tag(neo4j_session):
    """A Function HAS_IMAGE edge to an ImageTag should resolve to one concrete Image."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _load_resolved_image_prerequisites(
        neo4j_session,
        images=[_image("sha256:functiontagimage")],
        image_tags=[_image_tag("example/function:latest", ["sha256:functiontagimage"])],
        functions=[
            _workload("function-tag-1", image_tag_ids=["example/function:latest"]),
        ],
    )

    _run_resolved_image_analysis(neo4j_session)

    assert check_rels(
        neo4j_session,
        "Function",
        "id",
        "Image",
        "id",
        "RESOLVED_IMAGE",
    ) == {("function-tag-1", "sha256:functiontagimage")}


def test_resolved_image_analysis_creates_rel_via_function_image_tag_manifest_list(
    neo4j_session,
):
    """A Function ImageTag to ImageManifestList path should resolve to one architecture-matching child Image."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _load_resolved_image_prerequisites(
        neo4j_session,
        images=[
            _image(
                "sha256:functiontagmanifestlist",
                image_type="manifest_list",
                child_image_ids=[
                    "sha256:functiontagchildamd64",
                    "sha256:functiontagchildarm64",
                ],
            ),
            _image("sha256:functiontagchildamd64", architecture="amd64"),
            _image("sha256:functiontagchildarm64", architecture="arm64"),
        ],
        image_tags=[
            _image_tag("example/function:latest", ["sha256:functiontagmanifestlist"]),
        ],
        functions=[
            _workload(
                "function-tag-ml-1",
                architecture_normalized="amd64",
                image_tag_ids=["example/function:latest"],
            ),
        ],
    )

    _run_resolved_image_analysis(neo4j_session)

    assert check_rels(
        neo4j_session,
        "Function",
        "id",
        "Image",
        "id",
        "RESOLVED_IMAGE",
    ) == {("function-tag-ml-1", "sha256:functiontagchildamd64")}


def test_resolved_image_analysis_creates_rel_for_gcp_artifact_registry_manifest_list(
    neo4j_session,
):
    """GAR manifest lists should resolve through CONTAINS_IMAGE to the matching platform image."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _load_resolved_image_prerequisites(
        neo4j_session,
        images=[
            _image(
                "sha256:manifestlist",
                image_type="manifest_list",
                child_image_ids=["sha256:childamd64", "sha256:childarm64"],
            ),
            _image("sha256:childamd64", architecture="amd64"),
            _image("sha256:childarm64", architecture="arm64"),
        ],
        containers=[
            _workload(
                "cloud-run-container-1",
                architecture_normalized="amd64",
                image_ids=["sha256:manifestlist"],
            ),
        ],
    )

    _run_resolved_image_analysis(neo4j_session)

    assert check_rels(
        neo4j_session,
        "Container",
        "id",
        "Image",
        "id",
        "RESOLVED_IMAGE",
    ) == {("cloud-run-container-1", "sha256:childamd64")}
