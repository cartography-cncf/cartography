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
    return_value=(
        [{"digest": TEST_DIGEST, "project_id": TEST_PROJECT_ID, "config": FAKE_CONFIG}],
        False,
    ),
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

    # Assert: layer_diff_ids + source_uri (from the OCI config label) on the image.
    result = neo4j_session.run(
        "MATCH (i:ScalewayContainerRegistryImage {digest: $d}) "
        "RETURN i.layer_diff_ids AS l, i.source_uri AS src",
        d=TEST_DIGEST,
    ).single()
    assert result["l"] == [DIFF_ID_1, DIFF_ID_2]
    assert result["src"] == "https://github.com/acme/app"

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


# An image with no OCI labels but a buildx SLSA provenance attestation.
FAKE_CONFIG_NO_LABELS = {
    "architecture": "amd64",
    "os": "linux",
    "config": {},
    "rootfs": {"type": "layers", "diff_ids": [DIFF_ID_1]},
    "history": [{"created_by": "COPY app /app"}],
}
SLSA_PREDICATE = {
    "buildDefinition": {
        "externalParameters": {"configSource": {"path": "Dockerfile"}},
        "resolvedDependencies": [
            {
                "uri": "https://github.com/acme/from-slsa",
                "digest": {"gitCommit": "abc123"},
            }
        ],
    },
    "metadata": {
        "https://mobyproject.org/buildkit@v1#metadata": {
            "vcs": {
                "source": "https://github.com/acme/from-slsa",
                "revision": "abc123",
            }
        }
    },
}


@patch.object(
    supply_chain,
    "get",
    return_value=(
        [
            {
                "digest": TEST_DIGEST,
                "project_id": TEST_PROJECT_ID,
                "config": FAKE_CONFIG_NO_LABELS,
                "annotations": {},
                "attestation_predicate": SLSA_PREDICATE,
            }
        ],
        False,
    ),
)
def test_scaleway_registry_image_provenance_from_attestation(_mock_get, neo4j_session):
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

    # Assert: source_uri + source_revision resolved from the SLSA attestation.
    result = neo4j_session.run(
        "MATCH (i:ScalewayContainerRegistryImage {digest: $d}) "
        "RETURN i.source_uri AS src, i.source_revision AS rev",
        d=TEST_DIGEST,
    ).single()
    assert result["src"] == "https://github.com/acme/from-slsa"
    assert result["rev"] == "abc123"


def test_registry_inventory_reload_preserves_enrichment(neo4j_session):
    """A base `{digest}` inventory reload must not clear the layer/provenance
    fields owned by the supply-chain enrichment (regression: kunaals review)."""
    from cartography.models.scaleway.container_registry.image import (
        ScalewayContainerRegistryImageEnrichmentSchema,
    )

    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)
    # Enrich the image (as supply_chain does).
    load(
        neo4j_session,
        ScalewayContainerRegistryImageEnrichmentSchema(),
        [
            {
                "digest": TEST_DIGEST,
                "layer_diff_ids": [DIFF_ID_1],
                "source_uri": "https://github.com/acme/app",
            }
        ],
        lastupdated=TEST_UPDATE_TAG,
        PROJECT_ID=TEST_PROJECT_ID,
    )
    # Re-run the base registry inventory load (digest only).
    _ensure_registry_image(neo4j_session)

    result = neo4j_session.run(
        "MATCH (i:ScalewayContainerRegistryImage {digest: $d}) "
        "RETURN i.layer_diff_ids AS l, i.source_uri AS src",
        d=TEST_DIGEST,
    ).single()
    assert result["l"] == [DIFF_ID_1]
    assert result["src"] == "https://github.com/acme/app"
