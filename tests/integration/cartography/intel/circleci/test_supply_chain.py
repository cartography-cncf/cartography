"""Code-to-cloud fallback: the CircleCI supply-chain matcher links a registry image to
its code repository when a tag encodes the build revision (circleci_tag_revision), for
no-SLSA / no-history environments. The matcher only writes edges: no pipeline run node is
created. Stale edges are cleaned only for images the feed re-evaluated this run.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.circleci.supply_chain as circleci_supply_chain

TEST_UPDATE_TAG = 123456789
TEST_UPDATE_TAG_2 = 223456789
TEST_ORG_ID = "org-uuid-1"
TEST_ORG_SLUG = "gh/acme"
PROJECT_SLUG = "gh/acme/app"
REPO_URL = "https://github.com/acme/app"
REPO_URL_FORK = "https://github.com/acme/fork"
FULL_SHA = "a" * 40
OTHER_SHA = "c" * 40
DIGEST = "sha256:" + "1" * 64
OTHER_DIGEST = "sha256:" + "2" * 64


def _seed_image(neo4j_session, digest, tag_name, update_tag=TEST_UPDATE_TAG):
    neo4j_session.run(
        """
        MERGE (reg:ContainerRegistry {id: 'reg-1'})
        MERGE (img:Image {digest: $digest})
          SET img.id = $digest, img.lastupdated = $tag
        MERGE (t:ImageTag {id: $tag_id})
          SET t.name = $tag_name, t.lastupdated = $tag
        MERGE (reg)-[:REPO_IMAGE]->(t)
        MERGE (t)-[:IMAGE]->(img)
        """,
        digest=digest,
        tag_id=f"{digest}:{tag_name}",
        tag_name=tag_name,
        tag=update_tag,
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


def _run_vcs(revision, repo_url, project_slug, run_id):
    return {
        "id": run_id,
        "project_slug": project_slug,
        "vcs": {
            "provider_name": "GitHub",
            "target_repository_url": repo_url,
            "revision": revision,
        },
    }


def _run_fixture():
    return _run_vcs(FULL_SHA, REPO_URL, PROJECT_SLUG, "pipeline-run-1")


def _sync(neo4j_session, update_tag=TEST_UPDATE_TAG):
    circleci_supply_chain.sync(
        neo4j_session,
        MagicMock(),
        "https://circleci.com/api/v2",
        TEST_ORG_ID,
        TEST_ORG_SLUG,
        update_tag,
        {"UPDATE_TAG": update_tag, "BASE_URL": "https://circleci.com/api/v2"},
    )


def _count_nodes(neo4j_session):
    return neo4j_session.run("MATCH (n) RETURN count(n) AS c").single()["c"]


def _circleci_packaged_from_count(neo4j_session, digest):
    return neo4j_session.run(
        """
        MATCH (:Image {digest: $digest})-[r:PACKAGED_FROM]->()
        WHERE r.match_method STARTS WITH 'circleci_'
        RETURN count(r) AS c
        """,
        digest=digest,
    ).single()["c"]


def _cleanup(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")


def test_tag_revision_packaged_from_and_packaged_by(neo4j_session):
    # Arrange: an image whose tag is the build SHA, plus the repo and CircleCI project.
    _cleanup(neo4j_session)
    _seed_image(neo4j_session, DIGEST, FULL_SHA)
    _seed_repo_and_project(neo4j_session)
    nodes_before = _count_nodes(neo4j_session)

    # Act
    with patch.object(
        circleci_supply_chain, "get_pipeline_runs", return_value=[_run_fixture()]
    ):
        _sync(neo4j_session)

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

    # Assert: no ephemeral pipeline-run nodes were created.
    assert _count_nodes(neo4j_session) == nodes_before

    _cleanup(neo4j_session)


def test_cross_provider_gating_excludes_already_matched_image(neo4j_session):
    # Arrange: an image already PACKAGED_FROM a repo in THIS run (e.g. GitHub provenance).
    _cleanup(neo4j_session)
    _seed_image(neo4j_session, DIGEST, FULL_SHA)
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
        circleci_supply_chain, "get_pipeline_runs", return_value=[_run_fixture()]
    ):
        _sync(neo4j_session)

    # Assert: no circleci_* edge was added; the image was excluded from the residual set.
    assert _circleci_packaged_from_count(neo4j_session, DIGEST) == 0

    _cleanup(neo4j_session)


def test_stale_edge_cleaned_only_for_reevaluated_images(neo4j_session):
    # Arrange: two images matched in sync 1. DIGEST's tag is FULL_SHA; OTHER_DIGEST's tag
    # is OTHER_SHA. Both resolve to REPO_URL.
    _cleanup(neo4j_session)
    _seed_image(neo4j_session, DIGEST, FULL_SHA)
    _seed_image(neo4j_session, OTHER_DIGEST, OTHER_SHA)
    _seed_repo_and_project(neo4j_session)

    feed_1 = [
        _run_vcs(FULL_SHA, REPO_URL, PROJECT_SLUG, "p1"),
        _run_vcs(OTHER_SHA, REPO_URL, PROJECT_SLUG, "p2"),
    ]
    with patch.object(circleci_supply_chain, "get_pipeline_runs", return_value=feed_1):
        _sync(neo4j_session, update_tag=TEST_UPDATE_TAG)
    assert _circleci_packaged_from_count(neo4j_session, DIGEST) == 1
    assert _circleci_packaged_from_count(neo4j_session, OTHER_DIGEST) == 1

    # Sync 2: FULL_SHA is now ambiguous (two repos) so DIGEST no longer matches but IS
    # re-evaluated (evidence in feed). OTHER_SHA is absent from the feed, so OTHER_DIGEST
    # has aged out and is not re-evaluated.
    feed_2 = [
        _run_vcs(FULL_SHA, REPO_URL, PROJECT_SLUG, "p1"),
        _run_vcs(FULL_SHA, REPO_URL_FORK, "gh/acme/fork", "p2"),
    ]
    with patch.object(circleci_supply_chain, "get_pipeline_runs", return_value=feed_2):
        _sync(neo4j_session, update_tag=TEST_UPDATE_TAG_2)

    # Re-evaluated + now ambiguous -> stale edge removed.
    assert _circleci_packaged_from_count(neo4j_session, DIGEST) == 0
    # Aged out of the feed -> edge preserved (no org-wide cleanup).
    assert _circleci_packaged_from_count(neo4j_session, OTHER_DIGEST) == 1

    _cleanup(neo4j_session)


def test_stale_circleci_edge_cleaned_when_now_matched_by_github(neo4j_session):
    # Sync 1: CircleCI matches the image to REPO_URL.
    _cleanup(neo4j_session)
    _seed_image(neo4j_session, DIGEST, FULL_SHA)
    _seed_repo_and_project(neo4j_session)
    with patch.object(
        circleci_supply_chain, "get_pipeline_runs", return_value=[_run_fixture()]
    ):
        _sync(neo4j_session, update_tag=TEST_UPDATE_TAG)
    assert _circleci_packaged_from_count(neo4j_session, DIGEST) == 1

    # Between syncs a GitHub provenance PACKAGED_FROM is created for THIS run (T2), which
    # excludes the image from the CircleCI residual set. Its stale CircleCI edge must still
    # be cleaned (the feed still carries evidence for it).
    neo4j_session.run(
        """
        MATCH (img:Image {digest: $digest}), (repo:GitHubRepository {id: $url})
        MERGE (img)-[r:PACKAGED_FROM]->(repo)
          SET r.lastupdated = $tag, r.match_method = 'provenance'
        """,
        digest=DIGEST,
        url=REPO_URL,
        tag=TEST_UPDATE_TAG_2,
    )

    with patch.object(
        circleci_supply_chain, "get_pipeline_runs", return_value=[_run_fixture()]
    ):
        _sync(neo4j_session, update_tag=TEST_UPDATE_TAG_2)

    # The stale CircleCI edge is gone; the GitHub provenance edge remains.
    assert _circleci_packaged_from_count(neo4j_session, DIGEST) == 0
    provenance = neo4j_session.run(
        """
        MATCH (:Image {digest: $digest})-[r:PACKAGED_FROM {match_method: 'provenance'}]->()
        RETURN count(r) AS c
        """,
        digest=DIGEST,
    ).single()["c"]
    assert provenance == 1

    _cleanup(neo4j_session)
