"""Integration tests for the GHCR (packages + container registry) sync."""

import base64
import json
from unittest.mock import patch

import cartography.intel.github.container_image_attestations
import cartography.intel.github.container_image_tags
import cartography.intel.github.container_images
import cartography.intel.github.packages
import cartography.intel.github.supply_chain
from tests.data.github.packages import CONFIG_BLOBS_BY_DIGEST
from tests.data.github.packages import DIGEST_API_AMD64
from tests.data.github.packages import DIGEST_API_ARM64
from tests.data.github.packages import DIGEST_API_INDEX
from tests.data.github.packages import DIGEST_API_LATEST
from tests.data.github.packages import DIGEST_WORKER
from tests.data.github.packages import GET_CONTAINER_PACKAGES
from tests.data.github.packages import LAYER_DIFF_A
from tests.data.github.packages import LAYER_DIFF_B
from tests.data.github.packages import LAYER_DIFF_C
from tests.data.github.packages import MANIFESTS_BY_REFERENCE
from tests.data.github.packages import PACKAGE_VERSIONS_BY_NAME
from tests.data.github.packages import SLSA_STATEMENT_API_LATEST
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_JOB_PARAMS = {"UPDATE_TAG": TEST_UPDATE_TAG}
TEST_GITHUB_URL = "https://api.github.com/graphql"
TEST_ORG = "simpsoncorp"
FAKE_TOKEN = "fake-pat"

ORG_URL = f"https://github.com/{TEST_ORG}"
REPO_URL = f"https://github.com/{TEST_ORG}/sample_repo"


def _seed_org_and_repo(neo4j_session):
    neo4j_session.run(
        """
        MERGE (org:GitHubOrganization {id: $org_url})
        SET org.username = $org_login
        MERGE (repo:GitHubRepository {id: $repo_url})
        SET repo.name = 'sample_repo'
        MERGE (repo)-[:OWNER]->(org)
        """,
        org_url=ORG_URL,
        org_login=TEST_ORG,
        repo_url=REPO_URL,
    )


def _packages_pagination_side_effect(token, base_url, endpoint, result_key, **_kw):
    if "/packages" in endpoint and "versions" not in endpoint:
        return GET_CONTAINER_PACKAGES
    if "/versions" in endpoint:
        # endpoint shape: /orgs/{org}/packages/container/{name}/versions?...
        # parse the package name out of the path.
        path = endpoint.split("?")[0]
        parts = path.split("/")
        package_name = parts[parts.index("container") + 1]
        return PACKAGE_VERSIONS_BY_NAME.get(package_name, [])
    return []


def _manifest_side_effect(token, repository_name, reference, **kwargs):
    return MANIFESTS_BY_REFERENCE.get((repository_name, reference))


def _blob_side_effect(token, repository_name, blob_digest, **kwargs):
    return CONFIG_BLOBS_BY_DIGEST.get(blob_digest)


def _attestations_for_digest(digest):
    if digest != DIGEST_API_LATEST:
        return []
    payload = base64.b64encode(
        json.dumps(SLSA_STATEMENT_API_LATEST).encode("utf-8"),
    ).decode("ascii")
    return [
        {
            "id": 9001,
            "predicate_type": SLSA_STATEMENT_API_LATEST["predicateType"],
            "bundle": {"dsseEnvelope": {"payload": payload}},
        },
    ]


def _attestations_paginated_side_effect(token, base_url, endpoint, result_key):
    # endpoint: /orgs/{org}/attestations/{digest}?per_page=100 — digest is
    # URL-encoded (`:` -> `%3A`) so unquote before lookup.
    from urllib.parse import unquote

    digest = unquote(endpoint.split("/attestations/")[1].split("?")[0])
    return _attestations_for_digest(digest)


@patch.object(
    cartography.intel.github.container_image_attestations,
    "fetch_all_rest_api_pages",
    side_effect=_attestations_paginated_side_effect,
)
@patch.object(
    cartography.intel.github.container_images,
    "fetch_ghcr_blob",
    side_effect=_blob_side_effect,
)
@patch.object(
    cartography.intel.github.container_images,
    "fetch_ghcr_manifest",
    side_effect=_manifest_side_effect,
)
@patch(
    "cartography.intel.github.packages.fetch_all_rest_api_pages",
    side_effect=_packages_pagination_side_effect,
)
def test_sync_ghcr_full_pipeline(
    mock_pages,
    mock_manifest,
    mock_blob,
    mock_attestations,
    neo4j_session,
):
    _seed_org_and_repo(neo4j_session)

    # Act
    fetch_result = cartography.intel.github.packages.sync_packages(
        neo4j_session,
        FAKE_TOKEN,
        TEST_GITHUB_URL,
        TEST_ORG,
        TEST_UPDATE_TAG,
        TEST_JOB_PARAMS,
    )
    assert fetch_result.cleanup_safe is True
    raw_manifests, _, tag_rows, observed_skipped = (
        cartography.intel.github.container_images.sync_container_images(
            neo4j_session,
            FAKE_TOKEN,
            TEST_GITHUB_URL,
            TEST_ORG,
            fetch_result.packages,
            TEST_UPDATE_TAG,
            TEST_JOB_PARAMS,
        )
    )
    cartography.intel.github.container_image_tags.sync_container_image_tags(
        neo4j_session,
        TEST_ORG,
        tag_rows,
        TEST_UPDATE_TAG,
        TEST_JOB_PARAMS,
    )
    cartography.intel.github.container_image_attestations.sync_container_image_attestations(
        neo4j_session,
        FAKE_TOKEN,
        TEST_GITHUB_URL,
        TEST_ORG,
        raw_manifests,
        TEST_UPDATE_TAG,
        TEST_JOB_PARAMS,
        additional_observed_digests=observed_skipped,
    )

    # Packages
    assert check_nodes(neo4j_session, "GitHubPackage", ["name", "uri"]) == {
        ("api", "ghcr.io/simpsoncorp/api"),
        ("worker", "ghcr.io/simpsoncorp/worker"),
    }
    # GitHubPackage gets the ContainerRegistry generic label
    assert check_nodes(neo4j_session, "ContainerRegistry", ["name"]) >= {
        ("api",),
        ("worker",),
    }

    # HAS_PACKAGE only for the package that has a repository link
    assert check_rels(
        neo4j_session,
        "GitHubRepository",
        "id",
        "GitHubPackage",
        "name",
        "HAS_PACKAGE",
        rel_direction_right=True,
    ) == {(REPO_URL, "api")}

    # Container images: 4 manifests (latest single + index + 2 children) + worker
    image_digests = check_nodes(neo4j_session, "GitHubContainerImage", ["digest"])
    assert image_digests == {
        (DIGEST_API_LATEST,),
        (DIGEST_API_INDEX,),
        (DIGEST_API_AMD64,),
        (DIGEST_API_ARM64,),
        (DIGEST_WORKER,),
    }

    # Generic ontology labels
    assert check_nodes(neo4j_session, "Image", ["digest"]) >= {
        (DIGEST_API_LATEST,),
        (DIGEST_API_AMD64,),
        (DIGEST_API_ARM64,),
        (DIGEST_WORKER,),
    }
    assert (DIGEST_API_INDEX,) in check_nodes(
        neo4j_session,
        "ImageManifestList",
        ["digest"],
    )

    # Layers: A, B, C de-duplicated across images
    assert check_nodes(neo4j_session, "GitHubContainerImageLayer", ["diff_id"]) == {
        (LAYER_DIFF_A,),
        (LAYER_DIFF_B,),
        (LAYER_DIFF_C,),
    }
    assert check_nodes(neo4j_session, "ImageLayer", ["diff_id"]) >= {
        (LAYER_DIFF_A,),
        (LAYER_DIFF_B,),
        (LAYER_DIFF_C,),
    }

    # CONTAINS_IMAGE from the manifest list to the two children
    assert check_rels(
        neo4j_session,
        "GitHubContainerImage",
        "digest",
        "GitHubContainerImage",
        "digest",
        "CONTAINS_IMAGE",
        rel_direction_right=True,
    ) == {
        (DIGEST_API_INDEX, DIGEST_API_AMD64),
        (DIGEST_API_INDEX, DIGEST_API_ARM64),
    }

    # Tag nodes (3 unique URIs)
    assert check_nodes(neo4j_session, "GitHubContainerImageTag", ["uri"]) == {
        ("ghcr.io/simpsoncorp/api:latest",),
        ("ghcr.io/simpsoncorp/api:v1.0.0",),
        ("ghcr.io/simpsoncorp/api:v1.1.0",),
        ("ghcr.io/simpsoncorp/worker:latest",),
    }

    # Cross-registry edges expected by supply_chain.py:
    # (:ContainerRegistry)-[:REPO_IMAGE]->(:ImageTag)-[:IMAGE]->(:Image)
    assert check_rels(
        neo4j_session,
        "GitHubPackage",
        "name",
        "GitHubContainerImageTag",
        "uri",
        "REPO_IMAGE",
        rel_direction_right=True,
    ) >= {
        ("api", "ghcr.io/simpsoncorp/api:latest"),
        ("api", "ghcr.io/simpsoncorp/api:v1.0.0"),
        ("api", "ghcr.io/simpsoncorp/api:v1.1.0"),
        ("worker", "ghcr.io/simpsoncorp/worker:latest"),
    }

    # Attestation node + provenance enrichment on the image
    assert check_nodes(
        neo4j_session,
        "GitHubContainerImageAttestation",
        ["attests_digest"],
    ) == {(DIGEST_API_LATEST,)}

    enriched = neo4j_session.run(
        """
        MATCH (img:GitHubContainerImage {digest: $digest})
        RETURN img.source_uri AS uri,
               img.source_revision AS rev,
               img.source_file AS file
        """,
        digest=DIGEST_API_LATEST,
    ).single()
    assert enriched["uri"] == "https://github.com/simpsoncorp/sample_repo"
    assert enriched["rev"] == "abc123def456abc123def456abc123def4567890"
    assert enriched["file"] == ".github/workflows/build.yml"


@patch.object(
    cartography.intel.github.supply_chain,
    "get_dockerfiles_for_repos",
    return_value=[],
)
@patch.object(
    cartography.intel.github.container_image_attestations,
    "fetch_all_rest_api_pages",
    side_effect=_attestations_paginated_side_effect,
)
@patch.object(
    cartography.intel.github.container_images,
    "fetch_ghcr_blob",
    side_effect=_blob_side_effect,
)
@patch.object(
    cartography.intel.github.container_images,
    "fetch_ghcr_manifest",
    side_effect=_manifest_side_effect,
)
@patch(
    "cartography.intel.github.packages.fetch_all_rest_api_pages",
    side_effect=_packages_pagination_side_effect,
)
def test_supply_chain_package_owner_fallback(
    mock_pages,
    mock_manifest,
    mock_blob,
    mock_attestations,
    mock_dockerfiles,
    neo4j_session,
):
    """
    The package-owner fallback links GHCR images that have no provenance match
    (and no Dockerfile match) to the GitHubRepository carrying their package's
    ``HAS_PACKAGE`` rel. ``DIGEST_API_INDEX`` and its child digests have no
    SLSA attestation in the fixtures, but the ``api`` package is owned by
    ``sample_repo`` so the fallback should kick in. ``DIGEST_WORKER`` lives in
    a package without a repository link, so it should remain unmatched.
    """
    _seed_org_and_repo(neo4j_session)

    fetch_result = cartography.intel.github.packages.sync_packages(
        neo4j_session,
        FAKE_TOKEN,
        TEST_GITHUB_URL,
        TEST_ORG,
        TEST_UPDATE_TAG,
        TEST_JOB_PARAMS,
    )
    raw_manifests, _, tag_rows, observed_skipped = (
        cartography.intel.github.container_images.sync_container_images(
            neo4j_session,
            FAKE_TOKEN,
            TEST_GITHUB_URL,
            TEST_ORG,
            fetch_result.packages,
            TEST_UPDATE_TAG,
            TEST_JOB_PARAMS,
        )
    )
    cartography.intel.github.container_image_tags.sync_container_image_tags(
        neo4j_session,
        TEST_ORG,
        tag_rows,
        TEST_UPDATE_TAG,
        TEST_JOB_PARAMS,
    )
    cartography.intel.github.container_image_attestations.sync_container_image_attestations(
        neo4j_session,
        FAKE_TOKEN,
        TEST_GITHUB_URL,
        TEST_ORG,
        raw_manifests,
        TEST_UPDATE_TAG,
        TEST_JOB_PARAMS,
        additional_observed_digests=observed_skipped,
    )

    # Run the supply-chain matcher with one repo (so SLSA provenance can match
    # DIGEST_API_LATEST via its source_uri) and no dockerfiles.
    cartography.intel.github.supply_chain.sync(
        neo4j_session,
        FAKE_TOKEN,
        TEST_GITHUB_URL,
        TEST_ORG,
        TEST_UPDATE_TAG,
        TEST_JOB_PARAMS,
        [{"url": REPO_URL}],
        workflows=None,
    )

    packaged_from = neo4j_session.run(
        """
        MATCH (img:GitHubContainerImage)-[r:PACKAGED_FROM]->(repo:GitHubRepository)
        RETURN img.digest AS digest,
               repo.id AS repo_url,
               r.match_method AS method
        """,
    ).data()
    rows = {(r["digest"], r["repo_url"], r["method"]) for r in packaged_from}

    # Provenance match for the attested image
    assert (DIGEST_API_LATEST, REPO_URL, "provenance") in rows
    # Package-owner fallback for the un-attested platform images of the
    # `api` package. The manifest-list digest itself is intentionally NOT
    # linked — only its child images claim a build repo.
    assert (DIGEST_API_AMD64, REPO_URL, "package_owner_repo") in rows
    assert (DIGEST_API_ARM64, REPO_URL, "package_owner_repo") in rows
    assert not any(digest == DIGEST_API_INDEX for digest, _, _ in rows)
    # `worker` package has no repo link → its image stays unmatched
    assert not any(digest == DIGEST_WORKER for digest, _, _ in rows)


@patch.object(
    cartography.intel.github.container_image_attestations,
    "fetch_all_rest_api_pages",
    side_effect=_attestations_paginated_side_effect,
)
@patch.object(
    cartography.intel.github.container_images,
    "fetch_ghcr_blob",
    side_effect=_blob_side_effect,
)
@patch.object(
    cartography.intel.github.container_images,
    "fetch_ghcr_manifest",
    side_effect=_manifest_side_effect,
)
@patch(
    "cartography.intel.github.packages.fetch_all_rest_api_pages",
    side_effect=_packages_pagination_side_effect,
)
def test_sync_ghcr_idempotent_across_runs(
    mock_pages,
    mock_manifest,
    mock_blob,
    mock_attestations,
    neo4j_session,
):
    """
    Running the GHCR sync twice must not delete live images: the second run
    should re-tag every image, layer, and attestation with the new
    update_tag even when manifest fetches are short-circuited by the
    cross-run dedup. Regression test for the data-loss bug Kunaal flagged
    on the original PR (skipped digests vs. cleanup_lastupdated).
    """
    _seed_org_and_repo(neo4j_session)
    second_update_tag = TEST_UPDATE_TAG + 1

    def run_full_sync(update_tag):
        params = {"UPDATE_TAG": update_tag}
        fetch_result = cartography.intel.github.packages.sync_packages(
            neo4j_session,
            FAKE_TOKEN,
            TEST_GITHUB_URL,
            TEST_ORG,
            update_tag,
            params,
        )
        raw_manifests, _, tag_rows, observed_skipped = (
            cartography.intel.github.container_images.sync_container_images(
                neo4j_session,
                FAKE_TOKEN,
                TEST_GITHUB_URL,
                TEST_ORG,
                fetch_result.packages,
                update_tag,
                params,
            )
        )
        cartography.intel.github.container_image_tags.sync_container_image_tags(
            neo4j_session,
            TEST_ORG,
            tag_rows,
            update_tag,
            params,
        )
        cartography.intel.github.container_image_attestations.sync_container_image_attestations(
            neo4j_session,
            FAKE_TOKEN,
            TEST_GITHUB_URL,
            TEST_ORG,
            raw_manifests,
            update_tag,
            params,
            additional_observed_digests=observed_skipped,
        )

    run_full_sync(TEST_UPDATE_TAG)
    expected_image_digests = {
        (DIGEST_API_LATEST,),
        (DIGEST_API_INDEX,),
        (DIGEST_API_AMD64,),
        (DIGEST_API_ARM64,),
        (DIGEST_WORKER,),
    }
    assert (
        check_nodes(neo4j_session, "GitHubContainerImage", ["digest"])
        == expected_image_digests
    )

    run_full_sync(second_update_tag)

    # Every image must still be present after the second run.
    assert (
        check_nodes(neo4j_session, "GitHubContainerImage", ["digest"])
        == expected_image_digests
    )
    # Layers must survive too.
    assert check_nodes(neo4j_session, "GitHubContainerImageLayer", ["diff_id"]) == {
        (LAYER_DIFF_A,),
        (LAYER_DIFF_B,),
        (LAYER_DIFF_C,),
    }
    # And the attestation node carrying provenance for DIGEST_API_LATEST.
    assert check_nodes(
        neo4j_session,
        "GitHubContainerImageAttestation",
        ["attests_digest"],
    ) == {(DIGEST_API_LATEST,)}

    # Every surviving image's lastupdated must reflect the second run, not
    # the first — that is the bump the cross-run dedup must perform.
    rows = neo4j_session.run(
        "MATCH (img:GitHubContainerImage) RETURN img.digest AS d, img.lastupdated AS u",
    ).data()
    stale = [r for r in rows if r["u"] != second_update_tag]
    assert not stale, f"stale lastupdated on: {stale}"

    # NEXT rels (layer linked-list ordering) must also be refreshed,
    # otherwise cleanup deletes them and the chain is broken.
    next_rows = neo4j_session.run(
        """
        MATCH (:GitHubContainerImageLayer)-[r:NEXT]->(:GitHubContainerImageLayer)
        RETURN r.lastupdated AS u
        """,
    ).data()
    assert next_rows, "expected at least one NEXT rel between layers"
    stale_next = [r for r in next_rows if r["u"] != second_update_tag]
    assert not stale_next, f"stale lastupdated on NEXT rels: {stale_next}"
