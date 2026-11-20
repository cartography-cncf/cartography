from unittest.mock import MagicMock

import pytest

from cartography.intel.gcp import artifact_registry
from cartography.intel.gcp.artifact_registry import artifact
from cartography.intel.gcp.artifact_registry import repository
from cartography.intel.gcp.artifact_registry.artifact import transform_docker_images
from cartography.intel.gcp.artifact_registry.repository import (
    ArtifactRegistryRepositorySyncResult,
)

PROJECT_ID = "test-gar-inventory"
REPO_ID = f"projects/{PROJECT_ID}/locations/us-central1/repositories/docker-repo"
OTHER_PROJECT_ID = "test-gar-inventory-other"
OTHER_REPO_ID = (
    f"projects/{OTHER_PROJECT_ID}/locations/us-central1/repositories/docker-repo"
)
DIGEST_1 = "sha256:" + "1" * 64
DIGEST_2 = "sha256:" + "2" * 64
AMD64 = "sha256:" + "a" * 64
ARM64 = "sha256:" + "b" * 64
SINGLE_IMAGE = "application/vnd.oci.image.manifest.v1+json"
IMAGE_INDEX = "application/vnd.oci.image.index.v1+json"


def _docker_image(project_id: str, repo_id: str, digest: str, tags: list[str]):
    return {
        "name": f"{repo_id}/dockerImages/app@{digest}",
        "uri": f"us-central1-docker.pkg.dev/{project_id}/docker-repo/app@{digest}",
        "tags": tags,
        "mediaType": SINGLE_IMAGE,
        "updateTime": "2026-11-01T00:00:00Z",
    }


def _image_index(
    project_id: str,
    repo_id: str,
    digest: str,
    tags: list[str],
    platforms: list[tuple[str, str, str | None]],
):
    """A multi-platform image; platforms are (digest, architecture, variant)."""
    return {
        **_docker_image(project_id, repo_id, digest, tags),
        "mediaType": IMAGE_INDEX,
        "imageManifests": [
            {
                "digest": platform_digest,
                "architecture": architecture,
                "os": "linux",
                "variant": variant,
                "mediaType": SINGLE_IMAGE,
            }
            for platform_digest, architecture, variant in platforms
        ],
    }


def _create_project(neo4j_session, project_id: str) -> None:
    neo4j_session.run(
        """
        MATCH (n) WHERE n.id = $project_id OR n.project_id = $project_id
        DETACH DELETE n
        """,
        project_id=project_id,
    )
    neo4j_session.run("MERGE (:GCPProject {id: $project_id})", project_id=project_id)


def _sync(
    neo4j_session,
    monkeypatch,
    project_id: str,
    repo_id: str,
    listing: list[dict],
    update_tag: int,
    listing_complete: bool = True,
) -> None:
    """Runs the Artifact Registry sync without its registry calls.

    An incomplete listing has a second repository whose images cannot be listed.
    """
    repositories = [{"name": repo_id, "format": "DOCKER"}]
    if not listing_complete:
        repositories.append({"name": f"{repo_id}-denied", "format": "DOCKER"})
    monkeypatch.setattr(
        artifact,
        "FORMAT_HANDLERS",
        {
            "DOCKER": (
                lambda _client, repo: listing if repo == repo_id else None,
                transform_docker_images,
            ),
        },
    )
    monkeypatch.setattr(
        repository,
        "get_artifact_registry_repositories",
        lambda *_args, **_kwargs: ArtifactRegistryRepositorySyncResult(
            repositories, True
        ),
    )
    monkeypatch.setattr(
        artifact_registry, "build_artifact_registry_client", MagicMock()
    )
    monkeypatch.setattr(artifact_registry, "sync_supply_chain", MagicMock())
    artifact_registry.sync(
        neo4j_session,
        MagicMock(),
        project_id,
        update_tag,
        {"UPDATE_TAG": update_tag, "PROJECT_ID": project_id},
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


def _platform_images(neo4j_session, project_id: str) -> set[tuple]:
    """Each platform image the project links as
    (manifest list, platform image, architecture, variant, Image label)."""
    return {
        (row[0], row[1], row[2], row[3], row[4])
        for row in neo4j_session.run(
            """
            MATCH (parent:GCPArtifactRegistryImage)-[r:CONTAINS_IMAGE]->
                  (child:GCPArtifactRegistryImage)
            WHERE r._sub_resource_id = $project_id
            RETURN parent.digest, child.digest, child.architecture, child.variant,
                   child:Image
            """,
            project_id=project_id,
        ).values()
    }


def test_unchanged_images_are_marked_seen_without_being_written_again(
    neo4j_session, monkeypatch
):
    # Arrange
    _create_project(neo4j_session, PROJECT_ID)
    listing = [
        _image_index(PROJECT_ID, REPO_ID, DIGEST_1, ["v1"], [(AMD64, "amd64", None)]),
    ]
    tag_id = f"us-central1-docker.pkg.dev/{PROJECT_ID}/docker-repo/app:v1"
    _sync(neo4j_session, monkeypatch, PROJECT_ID, REPO_ID, listing, 1)

    # Act
    _sync(neo4j_session, monkeypatch, PROJECT_ID, REPO_ID, listing, 2)

    # Assert: the tag, its image and the platform image are current, and their
    # links are the ones the first sync wrote.
    assert (
        neo4j_session.run(
            """
        MATCH (ri:GCPArtifactRegistryRepositoryImage {id: $id})-[:IMAGE]->
              (image)-[platform_link:CONTAINS_IMAGE]->(platform)
        RETURN ri.lastupdated, image.lastupdated, platform.lastupdated,
               platform_link.lastupdated
        """,
            id=tag_id,
        )
        .single()
        .values()
        == [2, 2, 2, 1]
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
    _create_project(neo4j_session, PROJECT_ID)
    first_listing = [_docker_image(PROJECT_ID, REPO_ID, DIGEST_1, ["latest"])]
    _sync(neo4j_session, monkeypatch, PROJECT_ID, REPO_ID, first_listing, 1)

    # Act
    _sync(neo4j_session, monkeypatch, PROJECT_ID, REPO_ID, second_listing, 2)

    # Assert
    assert _tags(neo4j_session, PROJECT_ID) == expected_tags


@pytest.mark.parametrize(
    ("second_listing", "expected_platform_images"),
    [
        pytest.param(
            [
                _image_index(
                    PROJECT_ID,
                    REPO_ID,
                    DIGEST_2,
                    ["v1"],
                    [(AMD64, "amd64", None), (ARM64, "arm64", "v8")],
                ),
            ],
            {
                (DIGEST_2, AMD64, "amd64", None, True),
                (DIGEST_2, ARM64, "arm64", "v8", True),
            },
            id="tag-moved-to-a-new-manifest-list",
        ),
        pytest.param(
            [
                _image_index(
                    PROJECT_ID, REPO_ID, DIGEST_1, ["v1"], [(AMD64, "amd64", "v3")]
                ),
            ],
            {(DIGEST_1, AMD64, "amd64", "v3", True)},
            id="platform-reported-differently",
        ),
    ],
)
def test_changed_platform_images_are_written_again(
    neo4j_session, monkeypatch, second_listing, expected_platform_images
):
    # Arrange
    _create_project(neo4j_session, PROJECT_ID)
    first_listing = [
        _image_index(PROJECT_ID, REPO_ID, DIGEST_1, ["v1"], [(AMD64, "amd64", None)]),
    ]
    _sync(neo4j_session, monkeypatch, PROJECT_ID, REPO_ID, first_listing, 1)

    # Act
    _sync(neo4j_session, monkeypatch, PROJECT_ID, REPO_ID, second_listing, 2)

    # Assert
    assert _platform_images(neo4j_session, PROJECT_ID) == expected_platform_images


@pytest.mark.parametrize(
    ("listing_complete", "expected_tag_ids", "expected_platform_images"),
    [
        pytest.param(
            True,
            {f"us-central1-docker.pkg.dev/{PROJECT_ID}/docker-repo/app:v2"},
            set(),
            id="listing-complete",
        ),
        pytest.param(
            False,
            {
                f"us-central1-docker.pkg.dev/{PROJECT_ID}/docker-repo/app:v1",
                f"us-central1-docker.pkg.dev/{PROJECT_ID}/docker-repo/app:v2",
            },
            {(DIGEST_1, AMD64, "amd64", None, True)},
            id="listing-incomplete",
        ),
    ],
)
def test_images_gone_from_a_complete_listing_are_deleted(
    neo4j_session,
    monkeypatch,
    listing_complete,
    expected_tag_ids,
    expected_platform_images,
):
    # Arrange
    _create_project(neo4j_session, PROJECT_ID)
    _sync(
        neo4j_session,
        monkeypatch,
        PROJECT_ID,
        REPO_ID,
        [
            _image_index(
                PROJECT_ID, REPO_ID, DIGEST_1, ["v1"], [(AMD64, "amd64", None)]
            ),
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
        listing_complete=listing_complete,
    )

    # Assert
    assert {tag[0] for tag in _tags(neo4j_session, PROJECT_ID)} == expected_tag_ids
    assert _platform_images(neo4j_session, PROJECT_ID) == expected_platform_images


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
    _create_project(neo4j_session, PROJECT_ID)
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


@pytest.mark.parametrize(
    ("second_listing", "expected_links"),
    [
        pytest.param(
            [_docker_image(PROJECT_ID, REPO_ID, DIGEST_1, ["v1"])],
            {
                ("RESOURCE", PROJECT_ID, 1),
                ("CONTAINS", REPO_ID, 1),
                ("REPO_IMAGE", REPO_ID, 1),
                ("IMAGE", DIGEST_1, 1),
                ("CONTAINS", "custom-inventory", 1),
                ("IMAGE", "custom-image", 1),
            },
            id="tag-unchanged",
        ),
        pytest.param(
            [_docker_image(PROJECT_ID, REPO_ID, DIGEST_2, ["v1"])],
            {
                ("RESOURCE", PROJECT_ID, 2),
                ("CONTAINS", REPO_ID, 2),
                ("REPO_IMAGE", REPO_ID, 2),
                ("IMAGE", DIGEST_2, 2),
                ("CONTAINS", "custom-inventory", 1),
                ("IMAGE", "custom-image", 1),
            },
            id="tag-moved-to-another-digest",
        ),
    ],
)
def test_links_another_writer_adds_to_a_tag_are_left_alone(
    neo4j_session, monkeypatch, second_listing, expected_links
):
    # Arrange: something other than this sync links a custom node to the tag
    # with relationship types the tag inventory also uses.
    _create_project(neo4j_session, PROJECT_ID)
    tag_id = f"us-central1-docker.pkg.dev/{PROJECT_ID}/docker-repo/app:v1"
    _sync(
        neo4j_session,
        monkeypatch,
        PROJECT_ID,
        REPO_ID,
        [_docker_image(PROJECT_ID, REPO_ID, DIGEST_1, ["v1"])],
        1,
    )
    neo4j_session.run(
        """
        MATCH (ri:GCPArtifactRegistryRepositoryImage {id: $tag_id})
        MERGE (inventory:CustomInventory {id: 'custom-inventory'})
        MERGE (image:CustomImage {id: 'custom-image'})
        MERGE (inventory)-[:CONTAINS {lastupdated: 1}]->(ri)
        MERGE (ri)-[:IMAGE {lastupdated: 1}]->(image)
        """,
        tag_id=tag_id,
    )

    # Act
    _sync(neo4j_session, monkeypatch, PROJECT_ID, REPO_ID, second_listing, 2)

    # Assert
    assert _links(neo4j_session, tag_id) == expected_links


@pytest.mark.parametrize(
    "damage",
    [
        pytest.param(
            "MATCH (child:GCPArtifactRegistryImage {digest: $digest}) REMOVE child:Image",
            id="ontology-label-missing",
        ),
        pytest.param(
            "MATCH (child:GCPArtifactRegistryImage {digest: $digest}) SET child.architecture = 'edited'",
            id="property-edited",
        ),
    ],
)
def test_platform_image_saved_differently_from_its_listing_is_repaired(
    neo4j_session, monkeypatch, damage
):
    # Arrange
    _create_project(neo4j_session, PROJECT_ID)
    listing = [
        _image_index(PROJECT_ID, REPO_ID, DIGEST_1, ["v1"], [(AMD64, "amd64", None)]),
    ]
    _sync(neo4j_session, monkeypatch, PROJECT_ID, REPO_ID, listing, 1)
    neo4j_session.run(damage, digest=AMD64)

    # Act
    _sync(neo4j_session, monkeypatch, PROJECT_ID, REPO_ID, listing, 2)

    # Assert
    assert _platform_images(neo4j_session, PROJECT_ID) == {
        (DIGEST_1, AMD64, "amd64", None, True),
    }


def test_deleting_gone_images_leaves_other_projects_alone(neo4j_session, monkeypatch):
    # Arrange: the same multi-platform image is pushed to two projects.
    _create_project(neo4j_session, PROJECT_ID)
    _create_project(neo4j_session, OTHER_PROJECT_ID)
    _sync(
        neo4j_session,
        monkeypatch,
        PROJECT_ID,
        REPO_ID,
        [
            _image_index(
                PROJECT_ID, REPO_ID, DIGEST_1, ["v1"], [(AMD64, "amd64", None)]
            ),
        ],
        1,
    )
    _sync(
        neo4j_session,
        monkeypatch,
        OTHER_PROJECT_ID,
        OTHER_REPO_ID,
        [
            _image_index(
                OTHER_PROJECT_ID,
                OTHER_REPO_ID,
                DIGEST_1,
                ["v1"],
                [(AMD64, "amd64", None)],
            ),
        ],
        1,
    )

    # Act: the first project's last image is deleted.
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
    assert _platform_images(neo4j_session, OTHER_PROJECT_ID) == {
        (DIGEST_1, AMD64, "amd64", None, True),
    }
