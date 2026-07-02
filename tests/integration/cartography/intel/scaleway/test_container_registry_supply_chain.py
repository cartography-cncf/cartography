from unittest.mock import patch

import cartography.intel.scaleway.container_registry.supply_chain as supply_chain
from cartography.client.core.tx import load
from cartography.models.scaleway.container_registry.image import (
    ScalewayContainerRegistryImageSchema,
)
from tests.integration.cartography.intel.scaleway.test_projects import (
    _ensure_local_neo4j_has_test_projects_and_orgs,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_DIGEST = "sha256:3333333333333333333333333333333333333333333333333333333333333333"
DIFF_ID_1 = "sha256:aaaa000000000000000000000000000000000000000000000000000000000000"
DIFF_ID_2 = "sha256:bbbb000000000000000000000000000000000000000000000000000000000000"

# A minimal OCI image config: two real layers (a base + a COPY) plus an empty
# metadata layer (WORKDIR) that carries no diff_id.
FAKE_CONFIG = {
    "architecture": "amd64",
    "os": "linux",
    "config": {
        "Labels": {"org.opencontainers.image.source": "https://github.com/acme/app"}
    },
    "rootfs": {"type": "layers", "diff_ids": [DIFF_ID_1, DIFF_ID_2]},
    "history": [
        {"created_by": "/bin/sh -c #(nop) ADD file:base in /"},
        {"created_by": "WORKDIR /app", "empty_layer": True},
        {"created_by": "COPY app /app"},
    ],
}


def _ensure_registry_image(neo4j_session):
    load(
        neo4j_session,
        ScalewayContainerRegistryImageSchema(),
        [{"digest": TEST_DIGEST}],
        lastupdated=TEST_UPDATE_TAG,
        PROJECT_ID=TEST_PROJECT_ID,
    )


@patch.object(
    supply_chain,
    "get",
    return_value=[
        {"digest": TEST_DIGEST, "project_id": TEST_PROJECT_ID, "config": FAKE_CONFIG}
    ],
)
def test_scaleway_registry_image_layers(_mock_get, neo4j_session):
    # Arrange
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": TEST_ORG_ID}
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)
    _ensure_registry_image(neo4j_session)

    # Act
    supply_chain.sync(
        neo4j_session,
        "fake-secret",
        common_job_parameters,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG,
    )

    # Assert: layer nodes (only the two non-empty layers) with commands.
    assert check_nodes(
        neo4j_session,
        "ScalewayContainerRegistryImageLayer",
        ["diff_id", "history"],
    ) == {
        (DIFF_ID_1, "/bin/sh -c #(nop) ADD file:base in /"),
        (DIFF_ID_2, "COPY app /app"),
    }
    # Cross-provider ImageLayer label (what the supply-chain matcher looks up).
    assert check_nodes(neo4j_session, "ImageLayer", ["diff_id"]) == {
        (DIFF_ID_1,),
        (DIFF_ID_2,),
    }

    # Assert: layer_diff_ids set on the image (ordered).
    result = neo4j_session.run(
        "MATCH (i:ScalewayContainerRegistryImage {digest: $d}) RETURN i.layer_diff_ids AS l",
        d=TEST_DIGEST,
    ).single()
    assert result["l"] == [DIFF_ID_1, DIFF_ID_2]

    # Assert: HAS_LAYER edges image -> layers.
    assert check_rels(
        neo4j_session,
        "ScalewayContainerRegistryImage",
        "digest",
        "ScalewayContainerRegistryImageLayer",
        "diff_id",
        "HAS_LAYER",
        rel_direction_right=True,
    ) == {(TEST_DIGEST, DIFF_ID_1), (TEST_DIGEST, DIFF_ID_2)}
