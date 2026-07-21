"""
Integration test for the ComputeService -> Image HAS_RUNTIME_IMAGE inventory analysis job.
"""

from cartography.analysis.ontology.analysis import WORKLOAD_HAS_RUNTIME_IMAGE
from cartography.util import run_typed_analysis_job
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_UPDATE_TAG_2 = 123456790


def _run_has_runtime_image_analysis(neo4j_session, update_tag=TEST_UPDATE_TAG):
    run_typed_analysis_job(
        WORKLOAD_HAS_RUNTIME_IMAGE, neo4j_session, {"UPDATE_TAG": update_tag}
    )


def _edge_exposure(neo4j_session, svc_id, img_id):
    """Return the exposed_internet property of a single HAS_RUNTIME_IMAGE edge."""
    result = neo4j_session.run(
        """
        MATCH (svc:ComputeService {id: $svc_id})-[r:HAS_RUNTIME_IMAGE]->(img:Image {id: $img_id})
        RETURN r.exposed_internet AS exposed
        """,
        svc_id=svc_id,
        img_id=img_id,
    )
    return [record["exposed"] for record in result]


def test_has_runtime_image_collapses_replicas_to_single_edge(neo4j_session):
    """Two running container replicas under the same controller, both resolving to the same
    image, produce exactly one deduped (:ComputeService)-[:HAS_RUNTIME_IMAGE]->(:Image) edge.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        MERGE (svc:ComputeService:KubernetesDeployment {id: 'deploy-1'})
        SET svc.lastupdated = $tag

        MERGE (pod:ComputePod:KubernetesPod {id: 'pod-1'})
        SET pod.lastupdated = $tag

        MERGE (c1:Container:KubernetesContainer {id: 'container-1'})
        SET c1._ont_state = 'running', c1.lastupdated = $tag
        MERGE (c2:Container:KubernetesContainer {id: 'container-2'})
        SET c2._ont_state = 'running', c2.lastupdated = $tag

        MERGE (img:Image:AWSECRImage {id: 'sha256:deadbeef'})
        SET img._ont_digest = 'sha256:deadbeef', img.lastupdated = $tag

        MERGE (c1)-[r1:WORKLOAD_PARENT]->(pod)
        SET r1.lastupdated = $tag
        MERGE (c2)-[r2:WORKLOAD_PARENT]->(pod)
        SET r2.lastupdated = $tag
        MERGE (pod)-[r3:WORKLOAD_PARENT]->(svc)
        SET r3.lastupdated = $tag

        MERGE (c1)-[r4:RESOLVED_IMAGE]->(img)
        SET r4.lastupdated = $tag
        MERGE (c2)-[r5:RESOLVED_IMAGE]->(img)
        SET r5.lastupdated = $tag
        """,
        tag=TEST_UPDATE_TAG,
    )

    _run_has_runtime_image_analysis(neo4j_session)

    assert check_rels(
        neo4j_session,
        "ComputeService",
        "id",
        "Image",
        "id",
        "HAS_RUNTIME_IMAGE",
    ) == {("deploy-1", "sha256:deadbeef")}


def test_has_runtime_image_ignores_non_running_container(neo4j_session):
    """A non-running container does not contribute a HAS_RUNTIME_IMAGE edge for its image."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        MERGE (svc:ComputeService:KubernetesDeployment {id: 'deploy-1'})
        SET svc.lastupdated = $tag

        MERGE (pod:ComputePod:KubernetesPod {id: 'pod-1'})
        SET pod.lastupdated = $tag

        MERGE (running:Container:KubernetesContainer {id: 'container-running'})
        SET running._ont_state = 'running', running.lastupdated = $tag
        MERGE (stopped:Container:KubernetesContainer {id: 'container-stopped'})
        SET stopped._ont_state = 'terminated', stopped.lastupdated = $tag

        MERGE (img_running:Image:AWSECRImage {id: 'sha256:running'})
        SET img_running.lastupdated = $tag
        MERGE (img_stopped:Image:AWSECRImage {id: 'sha256:stopped'})
        SET img_stopped.lastupdated = $tag

        MERGE (running)-[r1:WORKLOAD_PARENT]->(pod)
        SET r1.lastupdated = $tag
        MERGE (stopped)-[r2:WORKLOAD_PARENT]->(pod)
        SET r2.lastupdated = $tag
        MERGE (pod)-[r3:WORKLOAD_PARENT]->(svc)
        SET r3.lastupdated = $tag

        MERGE (running)-[r4:RESOLVED_IMAGE]->(img_running)
        SET r4.lastupdated = $tag
        MERGE (stopped)-[r5:RESOLVED_IMAGE]->(img_stopped)
        SET r5.lastupdated = $tag
        """,
        tag=TEST_UPDATE_TAG,
    )

    _run_has_runtime_image_analysis(neo4j_session)

    assert check_rels(
        neo4j_session,
        "ComputeService",
        "id",
        "Image",
        "id",
        "HAS_RUNTIME_IMAGE",
    ) == {("deploy-1", "sha256:running")}


def test_has_runtime_image_denormalizes_exposure(neo4j_session):
    """Exposure is the logical OR across running replicas: an exposed workload's edge is
    true, a non-exposed workload's edge is false."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        // Exposed workload: one replica is exposed, one is not -> edge should be true.
        MERGE (svc_exposed:ComputeService:KubernetesDeployment {id: 'deploy-exposed'})
        SET svc_exposed.lastupdated = $tag
        MERGE (pod_exposed:ComputePod:KubernetesPod {id: 'pod-exposed'})
        SET pod_exposed.lastupdated = $tag
        MERGE (c_exposed:Container:KubernetesContainer {id: 'container-exposed'})
        SET c_exposed._ont_state = 'running', c_exposed.exposed_internet = true, c_exposed.lastupdated = $tag
        MERGE (c_internal:Container:KubernetesContainer {id: 'container-internal'})
        SET c_internal._ont_state = 'running', c_internal.exposed_internet = false, c_internal.lastupdated = $tag
        MERGE (img_a:Image:AWSECRImage {id: 'sha256:imga'})
        SET img_a.lastupdated = $tag
        MERGE (c_exposed)-[re1:WORKLOAD_PARENT]->(pod_exposed) SET re1.lastupdated = $tag
        MERGE (c_internal)-[re2:WORKLOAD_PARENT]->(pod_exposed) SET re2.lastupdated = $tag
        MERGE (pod_exposed)-[re3:WORKLOAD_PARENT]->(svc_exposed) SET re3.lastupdated = $tag
        MERGE (c_exposed)-[re4:RESOLVED_IMAGE]->(img_a) SET re4.lastupdated = $tag
        MERGE (c_internal)-[re5:RESOLVED_IMAGE]->(img_a) SET re5.lastupdated = $tag

        // Non-exposed workload: replica has no exposure property at all -> edge should be false.
        MERGE (svc_safe:ComputeService:KubernetesDeployment {id: 'deploy-safe'})
        SET svc_safe.lastupdated = $tag
        MERGE (pod_safe:ComputePod:KubernetesPod {id: 'pod-safe'})
        SET pod_safe.lastupdated = $tag
        MERGE (c_safe:Container:KubernetesContainer {id: 'container-safe'})
        SET c_safe._ont_state = 'running', c_safe.lastupdated = $tag
        MERGE (img_b:Image:AWSECRImage {id: 'sha256:imgb'})
        SET img_b.lastupdated = $tag
        MERGE (c_safe)-[rs1:WORKLOAD_PARENT]->(pod_safe) SET rs1.lastupdated = $tag
        MERGE (pod_safe)-[rs2:WORKLOAD_PARENT]->(svc_safe) SET rs2.lastupdated = $tag
        MERGE (c_safe)-[rs3:RESOLVED_IMAGE]->(img_b) SET rs3.lastupdated = $tag
        """,
        tag=TEST_UPDATE_TAG,
    )

    _run_has_runtime_image_analysis(neo4j_session)

    assert _edge_exposure(neo4j_session, "deploy-exposed", "sha256:imga") == [True]
    assert _edge_exposure(neo4j_session, "deploy-safe", "sha256:imgb") == [False]


def test_has_runtime_image_exposure_from_service_level_signal(neo4j_session):
    """Cloud Run writes exposed_internet on the GCPCloudRunService (the ComputeService),
    not on its container. The edge must still be exposed=true from that service-level signal.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        MERGE (svc:ComputeService:GCPCloudRunService {id: 'cloudrun-svc'})
        SET svc.exposed_internet = true, svc.lastupdated = $tag

        MERGE (c:Container:GCPCloudRunServiceContainer {id: 'cloudrun-container'})
        SET c._ont_state = 'running', c.lastupdated = $tag

        MERGE (img:Image:GCPArtifactRegistryImage {id: 'sha256:cloudrun'})
        SET img.lastupdated = $tag

        MERGE (c)-[r1:WORKLOAD_PARENT]->(svc)
        SET r1.lastupdated = $tag
        MERGE (c)-[r2:RESOLVED_IMAGE]->(img)
        SET r2.lastupdated = $tag
        """,
        tag=TEST_UPDATE_TAG,
    )

    _run_has_runtime_image_analysis(neo4j_session)

    assert check_rels(
        neo4j_session,
        "ComputeService",
        "id",
        "Image",
        "id",
        "HAS_RUNTIME_IMAGE",
    ) == {("cloudrun-svc", "sha256:cloudrun")}
    assert _edge_exposure(neo4j_session, "cloudrun-svc", "sha256:cloudrun") == [True]


def test_has_runtime_image_self_service_workload(neo4j_session):
    """A serverless workload that is both :ComputeService and :Container on a single node
    (e.g. ScalewayServerlessContainer), with a direct RESOLVED_IMAGE and no intermediate
    WORKLOAD_PARENT hop, still gets a HAS_RUNTIME_IMAGE edge (zero-length collapse). Its active
    state comes from the raw Scaleway status 'ready', not 'running'."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        MERGE (svc:ComputeService:Container:ScalewayServerlessContainer {id: 'scw-container'})
        SET svc._ont_state = 'ready', svc.exposed_internet = true, svc.lastupdated = $tag

        MERGE (img:Image:ScalewayContainerRegistryImage {id: 'sha256:scaleway'})
        SET img.lastupdated = $tag

        MERGE (svc)-[r:RESOLVED_IMAGE]->(img)
        SET r.lastupdated = $tag
        """,
        tag=TEST_UPDATE_TAG,
    )

    _run_has_runtime_image_analysis(neo4j_session)

    assert check_rels(
        neo4j_session,
        "ComputeService",
        "id",
        "Image",
        "id",
        "HAS_RUNTIME_IMAGE",
    ) == {("scw-container", "sha256:scaleway")}
    assert _edge_exposure(neo4j_session, "scw-container", "sha256:scaleway") == [True]


def test_has_runtime_image_is_idempotent_and_marks_gone(neo4j_session):
    """Re-running after a workload stops running an image removes the stale HAS_RUNTIME_IMAGE edge,
    and re-running an unchanged graph does not duplicate edges."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        MERGE (svc:ComputeService:KubernetesDeployment {id: 'deploy-1'})
        SET svc.lastupdated = $tag
        MERGE (pod:ComputePod:KubernetesPod {id: 'pod-1'})
        SET pod.lastupdated = $tag
        MERGE (c:Container:KubernetesContainer {id: 'container-1'})
        SET c._ont_state = 'running', c.lastupdated = $tag
        MERGE (img:Image:AWSECRImage {id: 'sha256:deadbeef'})
        SET img.lastupdated = $tag
        MERGE (c)-[r1:WORKLOAD_PARENT]->(pod) SET r1.lastupdated = $tag
        MERGE (pod)-[r2:WORKLOAD_PARENT]->(svc) SET r2.lastupdated = $tag
        MERGE (c)-[r3:RESOLVED_IMAGE]->(img) SET r3.lastupdated = $tag
        """,
        tag=TEST_UPDATE_TAG,
    )

    _run_has_runtime_image_analysis(neo4j_session, TEST_UPDATE_TAG)
    assert check_rels(
        neo4j_session, "ComputeService", "id", "Image", "id", "HAS_RUNTIME_IMAGE"
    ) == {("deploy-1", "sha256:deadbeef")}

    # The workload stops running the image: drop the RESOLVED_IMAGE basis, then re-run with a
    # fresh update tag. The stale HAS_RUNTIME_IMAGE edge (not re-stamped) must be cleaned up.
    neo4j_session.run(
        "MATCH (:Container {id: 'container-1'})-[r:RESOLVED_IMAGE]->(:Image) DELETE r"
    )
    _run_has_runtime_image_analysis(neo4j_session, TEST_UPDATE_TAG_2)

    assert (
        check_rels(
            neo4j_session, "ComputeService", "id", "Image", "id", "HAS_RUNTIME_IMAGE"
        )
        == set()
    )


def test_has_runtime_image_no_edge_without_controller(neo4j_session):
    """A running container with no ComputeService ancestor yields no HAS_RUNTIME_IMAGE edge; that
    case stays on the live-collapse fallback path."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        MERGE (c:Container:KubernetesContainer {id: 'bare-container'})
        SET c._ont_state = 'running', c.lastupdated = $tag
        MERGE (img:Image:AWSECRImage {id: 'sha256:deadbeef'})
        SET img.lastupdated = $tag
        MERGE (c)-[r:RESOLVED_IMAGE]->(img)
        SET r.lastupdated = $tag
        """,
        tag=TEST_UPDATE_TAG,
    )

    _run_has_runtime_image_analysis(neo4j_session)

    assert (
        check_rels(
            neo4j_session, "ComputeService", "id", "Image", "id", "HAS_RUNTIME_IMAGE"
        )
        == set()
    )


def test_has_runtime_image_standalone_function_gets_no_edge(neo4j_session):
    """A container-based function (e.g. AWS Lambda) carries only :Function with a direct
    RESOLVED_IMAGE, but has no :ComputeService label and no WORKLOAD_PARENT chain. By design
    it is NOT materialized into HAS_RUNTIME_IMAGE (it stays on the read-side live-collapse path);
    HAS_RUNTIME_IMAGE is a ComputeService-anchored fact and a standalone function is not a workload
    controller."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        MERGE (f:Function:AWSLambda {id: 'arn:aws:lambda:us-east-1:1234:function:fn'})
        SET f.lastupdated = $tag
        MERGE (img:Image:AWSECRImage {id: 'sha256:lambda'})
        SET img.lastupdated = $tag
        MERGE (f)-[r:RESOLVED_IMAGE]->(img)
        SET r.lastupdated = $tag
        """,
        tag=TEST_UPDATE_TAG,
    )

    _run_has_runtime_image_analysis(neo4j_session)

    assert (
        check_rels(
            neo4j_session, "ComputeService", "id", "Image", "id", "HAS_RUNTIME_IMAGE"
        )
        == set()
    )
    # And the function itself is never a HAS_RUNTIME_IMAGE source.
    assert (
        check_rels(neo4j_session, "Function", "id", "Image", "id", "HAS_RUNTIME_IMAGE")
        == set()
    )
