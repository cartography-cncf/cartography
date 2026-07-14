"""End-to-end code-to-cloud chain in Neo4j, stitching the real sync/enrichment
steps together with mocked registry/OCI/GitHub data:

    (:GitHubRepository)<-[:PACKAGED_FROM]-(:Image)              # source repo
    (:ContainerRegistry)-[:REPO_IMAGE]->(:ImageTag)-[:IMAGE]->(:Image)
    (:Image)-[:HAS_LAYER]->(:ImageLayer)
    (:ScalewayServerlessContainer)-[:HAS_IMAGE]->(:Image)
    (:ScalewayServerlessContainer)-[:RESOLVED_IMAGE]->(:Image)  # runtime workload

So a query can traverse: a running Scaleway workload -> the image it runs ->
the layers it is built from -> the GitHub repository it was built from.
"""

from unittest.mock import patch

import cartography.intel.github.supply_chain as github_supply_chain
import cartography.intel.scaleway.container_registry.supply_chain as sc_supply_chain
from cartography.analysis.ontology.analysis import RESOLVED_IMAGE_JOBS
from cartography.client.core.tx import load
from cartography.models.scaleway.container_registry.image import (
    ScalewayContainerRegistryImageSchema,
)
from cartography.models.scaleway.container_registry.image_tag import (
    ScalewayContainerRegistryImageTagSchema,
)
from cartography.models.scaleway.container_registry.namespace import (
    ScalewayContainerRegistryNamespaceSchema,
)
from cartography.models.scaleway.serverless.container import (
    ScalewayServerlessContainerSchema,
)
from cartography.util import run_typed_analysis_job
from tests.integration.cartography.intel.scaleway.test_projects import (
    _ensure_local_neo4j_has_test_projects_and_orgs,
)

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"

REPO_URL = "https://github.com/acme/app"
NS_ID = "ns-app-1111"
IMAGE_DIGEST = "sha256:" + "e" * 64
LAYER_DIFF_ID = "sha256:" + "f" * 64
TAG_URI = "rg.fr-par.scw.cloud/app-ns/app:latest"
CONTAINER_ID = "ct-app-2222"

# OCI image config the (mocked) registry endpoint would return for the image:
# one layer + the source-repo label used for provenance matching.
FAKE_CONFIG = {
    "architecture": "amd64",
    "os": "linux",
    "config": {"Labels": {"org.opencontainers.image.source": REPO_URL}},
    "rootfs": {"type": "layers", "diff_ids": [LAYER_DIFF_ID]},
    "history": [{"created_by": "COPY app /app"}],
}


@patch.object(github_supply_chain, "get_dockerfiles_for_repos", return_value=[])
@patch.object(
    sc_supply_chain,
    "get",
    return_value=(
        [
            {
                "digest": IMAGE_DIGEST,
                "project_id": TEST_PROJECT_ID,
                "config": FAKE_CONFIG,
                "annotations": {},
                "attestation_predicate": None,
            }
        ],
        False,
    ),
)
def test_full_code_to_cloud_chain(_mock_sc_get, _mock_dockerfiles, neo4j_session):
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": TEST_ORG_ID}
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)

    # 1. Base registry nodes: namespace (ContainerRegistry) -> tag -> image.
    load(
        neo4j_session,
        ScalewayContainerRegistryNamespaceSchema(),
        [
            {
                "id": NS_ID,
                "name": "app-ns",
                "endpoint": "rg.fr-par.scw.cloud/app-ns",
                "is_public": False,
            }
        ],
        lastupdated=TEST_UPDATE_TAG,
        PROJECT_ID=TEST_PROJECT_ID,
    )
    load(
        neo4j_session,
        ScalewayContainerRegistryImageSchema(),
        [{"digest": IMAGE_DIGEST}],
        lastupdated=TEST_UPDATE_TAG,
        PROJECT_ID=TEST_PROJECT_ID,
    )
    load(
        neo4j_session,
        ScalewayContainerRegistryImageTagSchema(),
        [
            {
                "id": "tag-app",
                "name": "latest",
                "image_name": "app",
                "uri": TAG_URI,
                "digest": IMAGE_DIGEST,
                "namespace_id": NS_ID,
            }
        ],
        lastupdated=TEST_UPDATE_TAG,
        PROJECT_ID=TEST_PROJECT_ID,
    )

    # 2. Enrich the image from the (mocked) OCI registry: layers + source_uri.
    sc_supply_chain.sync(
        neo4j_session,
        "fake-secret",
        common_job_parameters,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG,
    )

    # 3. A running Scaleway serverless container whose image resolves to the digest.
    load(
        neo4j_session,
        ScalewayServerlessContainerSchema(),
        [
            {
                "id": CONTAINER_ID,
                "name": "app-svc",
                "namespace_id": "scn-1",
                "registry_image": TAG_URI,
                "image_digest": IMAGE_DIGEST,
                "privacy": "public",
            }
        ],
        lastupdated=TEST_UPDATE_TAG,
        PROJECT_ID=TEST_PROJECT_ID,
    )

    # 4. Mocked GitHub data: the source repository, then the provenance matcher.
    neo4j_session.run(
        "MERGE (r:GitHubRepository {id: $url}) SET r.lastupdated = $tag",
        url=REPO_URL,
        tag=TEST_UPDATE_TAG,
    )
    github_supply_chain.sync(
        neo4j_session,
        "fake-token",
        "https://api.github.com/graphql",
        "acme",
        TEST_UPDATE_TAG,
        common_job_parameters,
        repos=[{"url": REPO_URL}],
    )

    # 5. Shared ontology analysis: (:Container)-[:HAS_IMAGE]->(:Image) => RESOLVED_IMAGE.
    for job in RESOLVED_IMAGE_JOBS:
        run_typed_analysis_job(job, neo4j_session, common_job_parameters)

    # Assert the entire chain resolves in a single traversal.
    record = neo4j_session.run(
        """
        MATCH (gh:GitHubRepository {id: $url})
              <-[:PACKAGED_FROM]-(img:ScalewayContainerRegistryImage {digest: $digest})
        MATCH (ns:ScalewayContainerRegistryNamespace)
              -[:REPO_IMAGE]->(tag:ScalewayContainerRegistryImageTag)-[:IMAGE]->(img)
        MATCH (img)-[:HAS_LAYER]->(layer:ScalewayContainerRegistryImageLayer)
        MATCH (sc:ScalewayServerlessContainer {id: $container})-[:HAS_IMAGE]->(img)
        MATCH (sc)-[:RESOLVED_IMAGE]->(img)
        RETURN
            img.source_uri AS source_uri,
            ns.id AS namespace_id,
            tag.id AS tag_id,
            layer.diff_id AS layer,
            sc.id AS container_id
        """,
        url=REPO_URL,
        digest=IMAGE_DIGEST,
        container=CONTAINER_ID,
    ).single()

    assert record is not None, "full code-to-cloud chain did not resolve"
    assert record["source_uri"] == REPO_URL
    assert record["namespace_id"] == NS_ID
    assert record["tag_id"] == "tag-app"
    assert record["layer"] == LAYER_DIFF_ID
    assert record["container_id"] == CONTAINER_ID
