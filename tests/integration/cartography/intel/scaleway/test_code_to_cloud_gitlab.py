"""Code-to-cloud: a Scaleway registry image with source_uri is linked to its
GitLab project by the generic (registry-agnostic) GitLab supply-chain matcher.
"""

from unittest.mock import patch

import cartography.intel.gitlab.supply_chain as gitlab_supply_chain
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
TEST_DIGEST = "sha256:5555555555555555555555555555555555555555555555555555555555555555"
PROJECT_URL = "https://gitlab.com/acme/app"


@patch.object(gitlab_supply_chain, "get_dockerfiles_for_projects", return_value=[])
def test_scaleway_image_packaged_from_gitlab_project(_mock_dockerfiles, neo4j_session):
    # Arrange: a Scaleway registry image enriched with source_uri, and the
    # GitLab project it was built from.
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)
    load(
        neo4j_session,
        ScalewayContainerRegistryImageEnrichmentSchema(),
        [{"digest": TEST_DIGEST, "source_uri": PROJECT_URL}],
        lastupdated=TEST_UPDATE_TAG,
        PROJECT_ID=TEST_PROJECT_ID,
    )
    neo4j_session.run(
        "MERGE (p:GitLabProject {web_url: $url}) SET p.lastupdated = $tag",
        url=PROJECT_URL,
        tag=TEST_UPDATE_TAG,
    )

    # Act: run the GitLab supply-chain matcher (provenance arm).
    gitlab_supply_chain.sync(
        neo4j_session,
        "https://gitlab.com",
        "fake-token",
        1,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
        projects=[{"web_url": PROJECT_URL}],
    )

    # Assert: the Scaleway image is PACKAGED_FROM the GitLab project.
    assert check_rels(
        neo4j_session,
        "ScalewayContainerRegistryImage",
        "digest",
        "GitLabProject",
        "web_url",
        "PACKAGED_FROM",
        rel_direction_right=True,
    ) == {(TEST_DIGEST, PROJECT_URL)}
