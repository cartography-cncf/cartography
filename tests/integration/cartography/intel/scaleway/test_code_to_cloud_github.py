"""Code-to-cloud: a Scaleway registry image with source_uri is linked to its
GitHub repository by the generic (registry-agnostic) GitHub supply-chain matcher.
"""

from unittest.mock import patch

import cartography.intel.github.supply_chain as github_supply_chain
from cartography.client.core.tx import load
from cartography.models.scaleway.container_registry.image import (
    ScalewayContainerRegistryImageEnrichmentSchema,
)
from tests.integration.cartography.intel.scaleway.test_projects import (
    _ensure_local_neo4j_has_test_projects_and_orgs,
)
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_DIGEST = "sha256:4444444444444444444444444444444444444444444444444444444444444444"
REPO_URL = "https://github.com/acme/app"


@patch.object(github_supply_chain, "get_dockerfiles_for_repos", return_value=[])
def test_scaleway_image_packaged_from_github_repo(_mock_dockerfiles, neo4j_session):
    # Arrange: a Scaleway registry image enriched with source_uri, and the
    # GitHub repository it was built from.
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)
    load(
        neo4j_session,
        ScalewayContainerRegistryImageEnrichmentSchema(),
        [{"digest": TEST_DIGEST, "source_uri": REPO_URL}],
        lastupdated=TEST_UPDATE_TAG,
        PROJECT_ID=TEST_PROJECT_ID,
    )
    neo4j_session.run(
        "MERGE (r:GitHubRepository {id: $url}) SET r.lastupdated = $tag",
        url=REPO_URL,
        tag=TEST_UPDATE_TAG,
    )

    # Act: run the GitHub supply-chain matcher (provenance arm).
    github_supply_chain.sync(
        neo4j_session,
        "fake-token",
        "https://api.github.com/graphql",
        "acme",
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
        repos=[{"url": REPO_URL}],
    )

    # Assert: the Scaleway image is PACKAGED_FROM the GitHub repository.
    assert check_rels(
        neo4j_session,
        "ScalewayContainerRegistryImage",
        "digest",
        "GitHubRepository",
        "id",
        "PACKAGED_FROM",
        rel_direction_right=True,
    ) == {(TEST_DIGEST, REPO_URL)}
