from unittest.mock import MagicMock

import pytest

from cartography.intel.gcp.artifact_registry import artifact
from cartography.intel.gcp.artifact_registry.artifact import (
    sync_artifact_registry_artifacts,
)
from cartography.intel.gcp.artifact_registry.artifact import transform_docker_images

PROJECT_ID = "test-gar-tag-inventory"
REPO_ID = f"projects/{PROJECT_ID}/locations/us-central1/repositories/docker-repo"
OTHER_PROJECT_ID = "test-gar-tag-inventory-other"
OTHER_REPO_ID = (
    f"projects/{OTHER_PROJECT_ID}/locations/us-central1/repositories/docker-repo"
)
DIGEST_1 = "sha256:" + "1" * 64
DIGEST_2 = "sha256:" + "2" * 64
SINGLE_IMAGE = "application/vnd.oci.image.manifest.v1+json"


def _docker_image(project_id: str, repo_id: str, digest: str, tags: list[str]):
    return {
        "name": f"{repo_id}/dockerImages/app@{digest}",
        "uri": f"us-central1-docker.pkg.dev/{project_id}/docker-repo/app@{digest}",
        "tags": tags,
        "mediaType": SINGLE_IMAGE,
        "updateTime": "2026-11-01T00:00:00Z",
    }


def _create_project(neo4j_session, project_id: str, repo_id: str) -> None:
    neo4j_session.run(
        """
        MATCH (n) WHERE n.id = $project_id OR n.project_id = $project_id
        DETACH DELETE n
        """,
        project_id=project_id,
    )
    neo4j_session.run(
        """
        MERGE (p:GCPProject {id: $project_id})
        MERGE (repo:GCPArtifactRegistryRepository {id: $repo_id})
        MERGE (p)-[:RESOURCE]->(repo)
        """,
        project_id=project_id,
        repo_id=repo_id,
    )


def _sync(
    neo4j_session,
    monkeypatch,
    project_id: str,
    repo_id: str,
    listing: list[dict],
    update_tag: int,
    cleanup_safe: bool = True,
) -> None:
    monkeypatch.setattr(
        artifact,
        "FORMAT_HANDLERS",
        {"DOCKER": (lambda _client, _repo: listing, transform_docker_images)},
    )
    sync_artifact_registry_artifacts(
        neo4j_session,
        MagicMock(),
        [{"name": repo_id, "format": "DOCKER"}],
        project_id,
        update_tag,
        {"UPDATE_TAG": update_tag},
        cleanup_safe=cleanup_safe,
        max_workers=1,
    )


def _tags(neo4j_session, project_id: str) -> set[tuple]:
    """Each tag of the project as (id, digest, tags, linked digest)."""
    return {
        (row["id"], row["digest"], tuple(row["tags"]), row["image"])
        for row in neo4j_session.run(
            """
            MATCH (:GCPProject {id: $project_id})-[:RESOURCE]->
                  (ri:GCPArtifactRegistryRepositoryImage)
            OPTIONAL MATCH (ri)-[:IMAGE]->(image:GCPArtifactRegistryImage)
            RETURN ri.id AS id, ri.digest AS digest, ri.tags AS tags,
                   image.digest AS image
            """,
            project_id=project_id,
        )
    }


def _links(neo4j_session, tag_id: str) -> set[tuple]:
    """Each link of a tag as (type, other end, lastupdated)."""
    return {
        (row["type"], row["other"], row["lastupdated"])
        for row in neo4j_session.run(
            """
            MATCH (:GCPArtifactRegistryRepositoryImage {id: $tag_id})-[r]-(other)
            RETURN type(r) AS type, other.id AS other, r.lastupdated AS lastupdated
            """,
            tag_id=tag_id,
        )
    }


def test_unchanged_tag_is_marked_seen_without_being_written_again(
    neo4j_session, monkeypatch
):
    # Arrange
    _create_project(neo4j_session, PROJECT_ID, REPO_ID)
    listing = [_docker_image(PROJECT_ID, REPO_ID, DIGEST_1, ["v1"])]
    tag_id = f"us-central1-docker.pkg.dev/{PROJECT_ID}/docker-repo/app:v1"
    _sync(neo4j_session, monkeypatch, PROJECT_ID, REPO_ID, listing, 1)

    # Act
    _sync(neo4j_session, monkeypatch, PROJECT_ID, REPO_ID, listing, 2)

    # Assert: the tag and its image are current, and its links are the ones the
    # first sync wrote.
    assert (
        neo4j_session.run(
            """
        MATCH (ri:GCPArtifactRegistryRepositoryImage {id: $id})-[:IMAGE]->(image)
        RETURN ri.lastupdated, image.lastupdated
        """,
            id=tag_id,
        )
        .single()
        .values()
        == [2, 2]
    )
    assert _links(neo4j_session, tag_id) == {
        ("RESOURCE", PROJECT_ID, 1),
        ("CONTAINS", REPO_ID, 1),
        ("REPO_IMAGE", REPO_ID, 1),
        ("IMAGE", DIGEST_1, 1),
    }


@pytest.mark.parametrize(
    ("second_listing", "expected_tags"),
    [
        pytest.param(
            [
                _docker_image(PROJECT_ID, REPO_ID, DIGEST_1, []),
                _docker_image(PROJECT_ID, REPO_ID, DIGEST_2, ["latest"]),
            ],
            {
                (
                    f"us-central1-docker.pkg.dev/{PROJECT_ID}/docker-repo/app:latest",
                    DIGEST_2,
                    ("latest",),
                    DIGEST_2,
                ),
                (
                    f"us-central1-docker.pkg.dev/{PROJECT_ID}/docker-repo/app@{DIGEST_1}",
                    DIGEST_1,
                    (),
                    DIGEST_1,
                ),
            },
            id="tag-moved-to-another-digest",
        ),
        pytest.param(
            [_docker_image(PROJECT_ID, REPO_ID, DIGEST_1, ["latest", "stable"])],
            {
                (
                    f"us-central1-docker.pkg.dev/{PROJECT_ID}/docker-repo/app:latest",
                    DIGEST_1,
                    ("latest", "stable"),
                    DIGEST_1,
                ),
                (
                    f"us-central1-docker.pkg.dev/{PROJECT_ID}/docker-repo/app:stable",
                    DIGEST_1,
                    ("latest", "stable"),
                    DIGEST_1,
                ),
            },
            id="digest-tagged-again",
        ),
    ],
)
def test_changed_tags_are_written_again(
    neo4j_session, monkeypatch, second_listing, expected_tags
):
    # Arrange
    _create_project(neo4j_session, PROJECT_ID, REPO_ID)
    first_listing = [_docker_image(PROJECT_ID, REPO_ID, DIGEST_1, ["latest"])]
    _sync(neo4j_session, monkeypatch, PROJECT_ID, REPO_ID, first_listing, 1)

    # Act
    _sync(neo4j_session, monkeypatch, PROJECT_ID, REPO_ID, second_listing, 2)

    # Assert
    assert _tags(neo4j_session, PROJECT_ID) == expected_tags


@pytest.mark.parametrize(
    ("cleanup_safe", "expected_tag_ids"),
    [
        pytest.param(
            True,
            {f"us-central1-docker.pkg.dev/{PROJECT_ID}/docker-repo/app:v2"},
            id="listing-complete",
        ),
        pytest.param(
            False,
            {
                f"us-central1-docker.pkg.dev/{PROJECT_ID}/docker-repo/app:v1",
                f"us-central1-docker.pkg.dev/{PROJECT_ID}/docker-repo/app:v2",
            },
            id="listing-incomplete",
        ),
    ],
)
def test_tags_gone_from_a_complete_listing_are_deleted(
    neo4j_session, monkeypatch, cleanup_safe, expected_tag_ids
):
    # Arrange
    _create_project(neo4j_session, PROJECT_ID, REPO_ID)
    _sync(
        neo4j_session,
        monkeypatch,
        PROJECT_ID,
        REPO_ID,
        [
            _docker_image(PROJECT_ID, REPO_ID, DIGEST_1, ["v1"]),
            _docker_image(PROJECT_ID, REPO_ID, DIGEST_2, ["v2"]),
        ],
        1,
    )

    # Act
    _sync(
        neo4j_session,
        monkeypatch,
        PROJECT_ID,
        REPO_ID,
        [_docker_image(PROJECT_ID, REPO_ID, DIGEST_2, ["v2"])],
        2,
        cleanup_safe=cleanup_safe,
    )

    # Assert
    assert {tag[0] for tag in _tags(neo4j_session, PROJECT_ID)} == expected_tag_ids


@pytest.mark.parametrize(
    "damage",
    [
        pytest.param(
            "MATCH (:GCPArtifactRegistryRepository)-[r:REPO_IMAGE]->(:ImageTag {id: $tag_id}) DELETE r",
            id="link-missing",
        ),
        pytest.param(
            """
            MATCH (ri:GCPArtifactRegistryRepositoryImage {id: $tag_id})
            MERGE (old:GCPArtifactRegistryImage {id: 'sha256:old', digest: 'sha256:old'})
            MERGE (ri)-[:IMAGE {lastupdated: 1}]->(old)
            """,
            id="extra-link-to-an-old-digest",
        ),
        pytest.param(
            "MATCH (ri:GCPArtifactRegistryRepositoryImage {id: $tag_id}) REMOVE ri:ImageTag",
            id="ontology-label-missing",
        ),
        pytest.param(
            "MATCH (ri:GCPArtifactRegistryRepositoryImage {id: $tag_id}) SET ri.digest_uri = 'edited'",
            id="property-edited",
        ),
    ],
)
def test_tag_saved_differently_from_its_listing_is_repaired(
    neo4j_session, monkeypatch, damage
):
    # Arrange
    _create_project(neo4j_session, PROJECT_ID, REPO_ID)
    listing = [_docker_image(PROJECT_ID, REPO_ID, DIGEST_1, ["v1"])]
    tag_id = f"us-central1-docker.pkg.dev/{PROJECT_ID}/docker-repo/app:v1"
    _sync(neo4j_session, monkeypatch, PROJECT_ID, REPO_ID, listing, 1)
    neo4j_session.run(damage, tag_id=tag_id)

    # Act
    _sync(neo4j_session, monkeypatch, PROJECT_ID, REPO_ID, listing, 2)

    # Assert
    assert _links(neo4j_session, tag_id) == {
        ("RESOURCE", PROJECT_ID, 2),
        ("CONTAINS", REPO_ID, 2),
        ("REPO_IMAGE", REPO_ID, 2),
        ("IMAGE", DIGEST_1, 2),
    }
    assert (
        neo4j_session.run(
            """
        MATCH (ri:ImageTag:GCPArtifactRegistryRepositoryImage {id: $tag_id})
        RETURN ri.digest_uri
        """,
            tag_id=tag_id,
        ).single()[0]
        == (f"us-central1-docker.pkg.dev/{PROJECT_ID}/docker-repo/app@{DIGEST_1}")
    )


def test_deleting_gone_tags_leaves_other_projects_alone(neo4j_session, monkeypatch):
    # Arrange: the same image is pushed to two projects.
    _create_project(neo4j_session, PROJECT_ID, REPO_ID)
    _create_project(neo4j_session, OTHER_PROJECT_ID, OTHER_REPO_ID)
    _sync(
        neo4j_session,
        monkeypatch,
        PROJECT_ID,
        REPO_ID,
        [_docker_image(PROJECT_ID, REPO_ID, DIGEST_1, ["v1"])],
        1,
    )
    _sync(
        neo4j_session,
        monkeypatch,
        OTHER_PROJECT_ID,
        OTHER_REPO_ID,
        [_docker_image(OTHER_PROJECT_ID, OTHER_REPO_ID, DIGEST_1, ["v1"])],
        1,
    )

    # Act: the first project's last tag is deleted.
    _sync(neo4j_session, monkeypatch, PROJECT_ID, REPO_ID, [], 2)

    # Assert
    assert _tags(neo4j_session, PROJECT_ID) == set()
    assert _tags(neo4j_session, OTHER_PROJECT_ID) == {
        (
            f"us-central1-docker.pkg.dev/{OTHER_PROJECT_ID}/docker-repo/app:v1",
            DIGEST_1,
            ("v1",),
            DIGEST_1,
        ),
    }
