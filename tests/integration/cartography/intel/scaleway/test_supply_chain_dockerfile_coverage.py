"""P2 coverage: every Scaleway registry image is sent through dockerfile
analysis. The generic per-registry matcher keeps one representative per
ContainerRegistry (= namespace), which would drop both sibling images in a
namespace and same-named images across namespaces. The dedicated helper groups
per repository (namespace + image name)."""

from cartography.client.core.tx import load
from cartography.intel.supply_chain import get_unmatched_scaleway_images_with_history
from cartography.models.scaleway.container_registry.image import (
    ScalewayContainerRegistryImageEnrichmentSchema,
)
from cartography.models.scaleway.container_registry.image_tag import (
    ScalewayContainerRegistryImageTagSchema,
)
from tests.integration.cartography.intel.scaleway.test_projects import (
    _ensure_local_neo4j_has_test_projects_and_orgs,
)

TEST_UPDATE_TAG = 123456789
TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"

DIGEST_API_A = "sha256:" + "a" * 64
DIGEST_WORKER_A = "sha256:" + "b" * 64
DIGEST_API_B = "sha256:" + "c" * 64


def _diff(prefix: str) -> str:
    return "sha256:" + prefix + "0" * (64 - len(prefix))


def test_get_unmatched_scaleway_images_covers_all_repositories(neo4j_session):
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)
    # Two namespaces so we can test same-named images across namespaces.
    neo4j_session.run(
        "UNWIND ['ns-a', 'ns-b'] AS nid "
        "MERGE (n:ScalewayContainerRegistryNamespace {id: nid}) "
        "SET n.lastupdated = $tag",
        tag=TEST_UPDATE_TAG,
    )
    # api + worker in ns-a, and api in ns-b (same name, different namespace).
    load(
        neo4j_session,
        ScalewayContainerRegistryImageEnrichmentSchema(),
        [
            {"digest": DIGEST_API_A, "layer_diff_ids": [_diff("aa")]},
            {"digest": DIGEST_WORKER_A, "layer_diff_ids": [_diff("bb")]},
            {"digest": DIGEST_API_B, "layer_diff_ids": [_diff("cc")]},
        ],
        lastupdated=TEST_UPDATE_TAG,
        PROJECT_ID=TEST_PROJECT_ID,
    )
    load(
        neo4j_session,
        ScalewayContainerRegistryImageTagSchema(),
        [
            {
                "id": "tag-api-a",
                "name": "latest",
                "image_name": "api",
                "digest": DIGEST_API_A,
                "namespace_id": "ns-a",
            },
            {
                "id": "tag-worker-a",
                "name": "latest",
                "image_name": "worker",
                "digest": DIGEST_WORKER_A,
                "namespace_id": "ns-a",
            },
            {
                "id": "tag-api-b",
                "name": "latest",
                "image_name": "api",
                "digest": DIGEST_API_B,
                "namespace_id": "ns-b",
            },
        ],
        lastupdated=TEST_UPDATE_TAG,
        PROJECT_ID=TEST_PROJECT_ID,
    )

    images = get_unmatched_scaleway_images_with_history(
        neo4j_session,
        sub_resource_label="GitHubOrganization",
        sub_resource_id="acme",
        update_tag=TEST_UPDATE_TAG,
    )

    # All three are distinct repositories (ns-a/api, ns-a/worker, ns-b/api):
    # none are collapsed.
    assert {img.digest for img in images} == {
        DIGEST_API_A,
        DIGEST_WORKER_A,
        DIGEST_API_B,
    }
