"""Code-to-cloud fallback: the CircleCI supply-chain matcher links a registry image to
its code repository when a tag encodes the build revision (circleci_tag_revision) or a
config binds its registry namespace (circleci_config_binding), for no-SLSA / no-history
environments. The matcher only writes edges: no pipeline run / config node is created.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.circleci.supply_chain as circleci_supply_chain

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "org-uuid-1"
TEST_ORG_SLUG = "gh/acme"
PROJECT_SLUG = "gh/acme/app"
REPO_URL = "https://github.com/acme/app"
FULL_SHA = "a" * 40
DIGEST = "sha256:" + "1" * 64
NAMESPACE_DIGEST = "sha256:" + "2" * 64


def _seed_image(neo4j_session, digest, tag_name, uri):
    neo4j_session.run(
        """
        MERGE (reg:ContainerRegistry {id: 'reg-1'})
        MERGE (img:Image {digest: $digest})
          SET img.id = $digest, img.uri = $uri, img.lastupdated = $tag
        MERGE (t:ImageTag {id: $tag_id})
          SET t.name = $tag_name, t.lastupdated = $tag
        MERGE (reg)-[:REPO_IMAGE]->(t)
        MERGE (t)-[:IMAGE]->(img)
        """,
        digest=digest,
        uri=uri,
        tag_id=f"{digest}:{tag_name}",
        tag_name=tag_name,
        tag=TEST_UPDATE_TAG,
    )


def _seed_repo_and_project(neo4j_session):
    neo4j_session.run(
        "MERGE (r:GitHubRepository:CodeRepository {id: $url}) SET r.lastupdated = $tag",
        url=REPO_URL,
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (p:CircleCIProject {slug: $slug}) SET p.id = 'proj-1', p.lastupdated = $tag",
        slug=PROJECT_SLUG,
        tag=TEST_UPDATE_TAG,
    )


def _run_fixture():
    return {
        "id": "pipeline-run-1",
        "project_slug": PROJECT_SLUG,
        "vcs": {
            "provider_name": "GitHub",
            "target_repository_url": REPO_URL,
            "revision": FULL_SHA,
        },
    }


def _count_nodes(neo4j_session):
    return neo4j_session.run("MATCH (n) RETURN count(n) AS c").single()["c"]


def _cleanup(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")


def test_tag_revision_packaged_from_and_packaged_by(neo4j_session):
    # Arrange: an image whose tag is the build SHA, plus the repo and CircleCI project.
    _cleanup(neo4j_session)
    _seed_image(
        neo4j_session, DIGEST, FULL_SHA, "123.dkr.ecr.us-east-1.amazonaws.com/acme/app"
    )
    _seed_repo_and_project(neo4j_session)
    nodes_before = _count_nodes(neo4j_session)

    # Act
    with patch.object(
        circleci_supply_chain,
        "get_pipeline_runs",
        return_value=[_run_fixture()],
    ):
        circleci_supply_chain.sync(
            neo4j_session,
            MagicMock(),
            "https://circleci.com/api/v2",
            TEST_ORG_ID,
            TEST_ORG_SLUG,
            TEST_UPDATE_TAG,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "BASE_URL": "https://circleci.com/api/v2"},
        )

    # Assert: PACKAGED_FROM to the repo with the right method/confidence.
    packaged_from = neo4j_session.run(
        """
        MATCH (img:Image {digest: $digest})-[r:PACKAGED_FROM]->(repo:GitHubRepository)
        RETURN repo.id AS repo, r.match_method AS method, r.confidence AS confidence
        """,
        digest=DIGEST,
    ).single()
    assert packaged_from["repo"] == REPO_URL
    assert packaged_from["method"] == "circleci_tag_revision"
    assert (
        packaged_from["confidence"]
        == circleci_supply_chain.CIRCLECI_TAG_REVISION_CONFIDENCE
    )

    # Assert: PACKAGED_BY to the building CircleCI project.
    packaged_by = neo4j_session.run(
        """
        MATCH (img:Image {digest: $digest})-[:PACKAGED_BY]->(p:CircleCIProject)
        RETURN p.slug AS slug
        """,
        digest=DIGEST,
    ).single()
    assert packaged_by["slug"] == PROJECT_SLUG

    # Assert: no ephemeral pipeline-run / config nodes were created.
    assert _count_nodes(neo4j_session) == nodes_before

    _cleanup(neo4j_session)


def test_cross_provider_gating_excludes_already_matched_image(neo4j_session):
    # Arrange: an image already PACKAGED_FROM a repo in THIS run (e.g. GitHub provenance).
    _cleanup(neo4j_session)
    _seed_image(
        neo4j_session, DIGEST, FULL_SHA, "123.dkr.ecr.us-east-1.amazonaws.com/acme/app"
    )
    _seed_repo_and_project(neo4j_session)
    neo4j_session.run(
        """
        MATCH (img:Image {digest: $digest}), (repo:GitHubRepository {id: $url})
        MERGE (img)-[r:PACKAGED_FROM]->(repo)
          SET r.lastupdated = $tag, r.match_method = 'provenance'
        """,
        digest=DIGEST,
        url=REPO_URL,
        tag=TEST_UPDATE_TAG,
    )

    # Act
    with patch.object(
        circleci_supply_chain,
        "get_pipeline_runs",
        return_value=[_run_fixture()],
    ):
        circleci_supply_chain.sync(
            neo4j_session,
            MagicMock(),
            "https://circleci.com/api/v2",
            TEST_ORG_ID,
            TEST_ORG_SLUG,
            TEST_UPDATE_TAG,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "BASE_URL": "https://circleci.com/api/v2"},
        )

    # Assert: no circleci_* edge was added; the image was excluded from the residual set.
    count = neo4j_session.run(
        """
        MATCH (:Image {digest: $digest})-[r:PACKAGED_FROM]->()
        WHERE r.match_method STARTS WITH 'circleci_'
        RETURN count(r) AS c
        """,
        digest=DIGEST,
    ).single()["c"]
    assert count == 0

    _cleanup(neo4j_session)


def test_config_binding_packaged_from(neo4j_session):
    # Arrange: an image with a non-SHA tag under a namespace bound by the config.
    _cleanup(neo4j_session)
    _seed_image(neo4j_session, NAMESPACE_DIGEST, "latest", "myns/app:latest")
    _seed_repo_and_project(neo4j_session)

    run = {
        "id": "pipeline-run-1",
        "project_slug": PROJECT_SLUG,
        "vcs": {
            "provider_name": "GitHub",
            "target_repository_url": REPO_URL,
            "revision": FULL_SHA,
        },
    }

    # Act
    with (
        patch.object(circleci_supply_chain, "get_pipeline_runs", return_value=[run]),
        patch.object(
            circleci_supply_chain,
            "_get_pipeline_config",
            return_value="steps:\n  - run: docker push myns/app:latest\n",
        ),
    ):
        circleci_supply_chain.sync(
            neo4j_session,
            MagicMock(),
            "https://circleci.com/api/v2",
            TEST_ORG_ID,
            TEST_ORG_SLUG,
            TEST_UPDATE_TAG,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "BASE_URL": "https://circleci.com/api/v2"},
        )

    # Assert: low-confidence config-binding edge to the repo.
    row = neo4j_session.run(
        """
        MATCH (img:Image {digest: $digest})-[r:PACKAGED_FROM]->(repo:GitHubRepository)
        RETURN repo.id AS repo, r.match_method AS method, r.confidence AS confidence
        """,
        digest=NAMESPACE_DIGEST,
    ).single()
    assert row["repo"] == REPO_URL
    assert row["method"] == "circleci_config_binding"
    assert row["confidence"] == circleci_supply_chain.CIRCLECI_CONFIG_BINDING_CONFIDENCE

    _cleanup(neo4j_session)
