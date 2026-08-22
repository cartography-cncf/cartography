import pytest

from cartography.analysis.ontology.analysis import CONTAINER_RESOLVED_IMAGE
from cartography.client.container_registry import ResolvedRegistryArtifact
from cartography.client.container_registry import ResolvedRegistryReference
from cartography.intel.container_image import ContainerImageReference
from cartography.intel.external_container_images import load_external_container_images
from cartography.util import run_typed_analysis_job
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

DIGEST_A = f"sha256:{'a' * 64}"
DIGEST_B = f"sha256:{'b' * 64}"
DIGEST_C = f"sha256:{'c' * 64}"
DIGEST_INDEX = f"sha256:{'d' * 64}"
OCI_IMAGE = "application/vnd.oci.image.manifest.v1+json"
OCI_INDEX = "application/vnd.oci.image.index.v1+json"
CREATED_AT = "2024-01-02T03:04:05Z"


@pytest.fixture(autouse=True)
def _clear_external_images(neo4j_session):
    neo4j_session.run(
        "MATCH (n:Container {id: 'synthetic-container'}) DETACH DELETE n",
    ).consume()
    neo4j_session.run(
        "MATCH (n:ExternalContainerImageReference) DETACH DELETE n",
    ).consume()
    neo4j_session.run(
        "MATCH (n:ExternalContainerImage) DETACH DELETE n",
    ).consume()


def _image(
    digest: str,
    *,
    architecture: str = "amd64",
    variant: str | None = None,
) -> ResolvedRegistryArtifact:
    return ResolvedRegistryArtifact(
        digest=digest,
        media_type=OCI_IMAGE,
        type="image",
        size=512,
        os="linux",
        architecture=architecture,
        variant=variant,
        config_digest=f"sha256:{digest[-1] * 64}",
        created_at=CREATED_AT,
    )


def _index(digest: str) -> ResolvedRegistryArtifact:
    return ResolvedRegistryArtifact(
        digest=digest,
        media_type=OCI_INDEX,
        type="manifest_list",
        size=1024,
    )


def _tagged_resolution(
    *,
    repository: str,
    tag: str,
    top: ResolvedRegistryArtifact,
    children: tuple[ResolvedRegistryArtifact, ...] = (),
    registry: str = "registry.example.test",
) -> ResolvedRegistryReference:
    location = f"{registry}/{repository}:{tag}"
    return ResolvedRegistryReference(
        reference=ContainerImageReference(
            original=location,
            registry=registry,
            repository=repository,
            tag=tag,
            digest=None,
            normalized=location,
            selector=tag,
        ),
        top=top,
        children=children,
    )


def test_loads_single_image_and_manifest_list_graph(neo4j_session):
    # Arrange
    single = _image(DIGEST_A)
    amd64 = _image(DIGEST_B)
    arm64 = _image(DIGEST_C, architecture="arm64", variant="v8")
    manifest_list = _index(DIGEST_INDEX)
    resolutions = [
        _tagged_resolution(repository="public/widget", tag="stable", top=single),
        _tagged_resolution(
            repository="public/multi",
            tag="latest",
            top=manifest_list,
            children=(amd64, arm64),
        ),
    ]

    # Act
    load_external_container_images(neo4j_session, resolutions, update_tag=1)

    # Assert
    assert check_nodes(
        neo4j_session,
        "ExternalContainerImage",
        ["digest", "type", "os", "architecture", "variant", "created_at"],
    ) == {
        (DIGEST_A, "image", "linux", "amd64", None, CREATED_AT),
        (DIGEST_B, "image", "linux", "amd64", None, CREATED_AT),
        (DIGEST_C, "image", "linux", "arm64", "v8", CREATED_AT),
        (DIGEST_INDEX, "manifest_list", None, None, None, None),
    }
    assert check_nodes(neo4j_session, "Image", ["digest"]) == {
        (DIGEST_A,),
        (DIGEST_B,),
        (DIGEST_C,),
    }
    assert check_nodes(neo4j_session, "ImageManifestList", ["digest"]) == {
        (DIGEST_INDEX,),
    }
    assert check_nodes(neo4j_session, "ImageTag", ["id"]) == {
        ("registry.example.test/public/widget:stable",),
        ("registry.example.test/public/multi:latest",),
    }
    assert check_rels(
        neo4j_session,
        "ExternalContainerImage",
        "digest",
        "ExternalContainerImage",
        "digest",
        "CONTAINS_IMAGE",
    ) == {
        (DIGEST_INDEX, DIGEST_B),
        (DIGEST_INDEX, DIGEST_C),
    }

    tag_edges = neo4j_session.run(
        """
        MATCH (reference:ExternalContainerImageReference {reference_type: 'tag'})
              -[:IMAGE]->(artifact:ExternalContainerImage)
        RETURN reference.location AS location, artifact.digest AS digest
        """,
    )
    assert {(row["location"], row["digest"]) for row in tag_edges} == {
        ("registry.example.test/public/widget:stable", DIGEST_A),
        ("registry.example.test/public/multi:latest", DIGEST_INDEX),
    }
    assert check_nodes(
        neo4j_session,
        "Image",
        ["_ont_digest", "_ont_source"],
    ) == {
        (DIGEST_A, "external_container_images"),
        (DIGEST_B, "external_container_images"),
        (DIGEST_C, "external_container_images"),
    }

    records = neo4j_session.run(
        """
        MATCH (node)
        WHERE node:ExternalContainerImage
           OR node:ExternalContainerImageReference
        RETURN labels(node) AS labels
        """,
    )
    for record in records:
        labels = set(record["labels"])
        if "ExternalContainerImageReference" in labels:
            assert labels <= {"ExternalContainerImageReference", "ImageTag"}
        else:
            assert labels <= {
                "ExternalContainerImage",
                "Image",
                "ImageManifestList",
            }


def test_tag_move_replaces_only_mutable_image_edge(neo4j_session):
    # Arrange
    first = _tagged_resolution(
        repository="public/widget",
        tag="stable",
        top=_image(DIGEST_A),
    )
    moved = _tagged_resolution(
        repository="public/widget",
        tag="stable",
        top=_image(DIGEST_B),
    )
    unrelated = _tagged_resolution(
        repository="public/other",
        tag="latest",
        top=_image(DIGEST_C),
    )

    # Act
    load_external_container_images(neo4j_session, [first, unrelated], update_tag=1)
    load_external_container_images(neo4j_session, [moved], update_tag=2)

    # Assert
    assert check_nodes(neo4j_session, "ExternalContainerImage", ["digest"]) == {
        (DIGEST_A,),
        (DIGEST_B,),
        (DIGEST_C,),
    }
    assert check_nodes(
        neo4j_session,
        "ImageTag",
        ["id", "digest", "pullable_reference"],
    ) == {
        (
            "registry.example.test/public/widget:stable",
            DIGEST_B,
            f"registry.example.test/public/widget@{DIGEST_B}",
        ),
        (
            "registry.example.test/public/other:latest",
            DIGEST_C,
            f"registry.example.test/public/other@{DIGEST_C}",
        ),
    }
    assert check_rels(
        neo4j_session,
        "ImageTag",
        "id",
        "ExternalContainerImage",
        "digest",
        "IMAGE",
    ) == {
        ("registry.example.test/public/widget:stable", DIGEST_B),
        ("registry.example.test/public/other:latest", DIGEST_C),
    }
    digest_edges = neo4j_session.run(
        """
        MATCH (reference:ExternalContainerImageReference {reference_type: 'digest'})
              -[:IMAGE]->(artifact:ExternalContainerImage)
        RETURN reference.digest AS reference_digest, artifact.digest AS artifact_digest
        """,
    )
    assert {
        (row["reference_digest"], row["artifact_digest"]) for row in digest_edges
    } == {
        (DIGEST_A, DIGEST_A),
        (DIGEST_B, DIGEST_B),
        (DIGEST_C, DIGEST_C),
    }


def test_duplicate_digest_is_one_global_artifact(neo4j_session):
    # Arrange
    shared_artifact = _image(DIGEST_A)
    resolutions = [
        _tagged_resolution(
            registry="one.registry.example.test",
            repository="team/widget",
            tag="stable",
            top=shared_artifact,
        ),
        _tagged_resolution(
            registry="two.registry.example.test",
            repository="mirror/widget",
            tag="current",
            top=shared_artifact,
        ),
    ]

    # Act
    load_external_container_images(neo4j_session, resolutions, update_tag=1)

    # Assert
    count = neo4j_session.run(
        "MATCH (artifact:ExternalContainerImage {digest: $digest}) RETURN count(artifact)",
        digest=DIGEST_A,
    ).single(strict=True)[0]
    assert count == 1
    references = neo4j_session.run(
        """
        MATCH (reference:ImageTag)-[:IMAGE]->
              (artifact:ExternalContainerImage {digest: $digest})
        RETURN reference.registry AS registry, reference.repository AS repository
        """,
        digest=DIGEST_A,
    )
    assert {(row["registry"], row["repository"]) for row in references} == {
        ("one.registry.example.test", "team/widget"),
        ("two.registry.example.test", "mirror/widget"),
    }
    artifact = neo4j_session.run(
        """
        MATCH (artifact:ExternalContainerImage {digest: $digest})
        RETURN artifact.registry AS registry,
               artifact.repository AS repository,
               artifact.tag AS tag,
               artifact.pullable_reference AS pullable_reference
        """,
        digest=DIGEST_A,
    ).single(strict=True)
    assert tuple(artifact.values()) == (None, None, None, None)


def test_tagged_digest_keeps_exact_and_canonical_references(neo4j_session):
    # Arrange
    registry = "registry.example.test"
    repository = "public/widget"
    normalized = f"{registry}/{repository}:pinned@{DIGEST_A}"
    resolution = ResolvedRegistryReference(
        reference=ContainerImageReference(
            original=normalized,
            registry=registry,
            repository=repository,
            tag="pinned",
            digest=DIGEST_A,
            normalized=normalized,
            selector=DIGEST_A,
        ),
        top=_image(DIGEST_A),
    )

    # Act
    load_external_container_images(neo4j_session, [resolution], update_tag=1)

    # Assert
    canonical = f"{registry}/{repository}@{DIGEST_A}"
    assert check_nodes(
        neo4j_session,
        "ExternalContainerImageReference",
        ["id", "tag", "reference_type", "pullable_reference"],
    ) == {
        (canonical, None, "digest", canonical),
        (normalized, "pinned", "digest", normalized),
    }
    assert check_nodes(neo4j_session, "ImageTag", ["id"]) == set()
    assert check_rels(
        neo4j_session,
        "ExternalContainerImageReference",
        "id",
        "ExternalContainerImage",
        "digest",
        "IMAGE",
    ) == {
        (canonical, DIGEST_A),
        (normalized, DIGEST_A),
    }


def test_empty_success_set_is_noop(neo4j_session):
    # Arrange
    resolution = _tagged_resolution(
        repository="public/widget",
        tag="stable",
        top=_image(DIGEST_A),
    )
    load_external_container_images(neo4j_session, [resolution], update_tag=1)

    # Act
    load_external_container_images(neo4j_session, [], update_tag=2)

    # Assert
    assert check_rels(
        neo4j_session,
        "ImageTag",
        "id",
        "ExternalContainerImage",
        "digest",
        "IMAGE",
    ) == {
        ("registry.example.test/public/widget:stable", DIGEST_A),
    }


@pytest.mark.parametrize(
    ("runtime_architecture", "second_child_architecture", "expected_digest"),
    [
        pytest.param("amd64", "arm64", DIGEST_B, id="unique-platform"),
        pytest.param(None, "arm64", None, id="no-runtime-platform"),
        pytest.param("amd64", "amd64", None, id="ambiguous-platform"),
    ],
)
def test_manifest_list_runtime_resolution_requires_one_matching_platform(
    neo4j_session,
    runtime_architecture,
    second_child_architecture,
    expected_digest,
):
    # Arrange
    resolution = _tagged_resolution(
        repository="public/multi",
        tag="latest",
        top=_index(DIGEST_INDEX),
        children=(
            _image(DIGEST_B),
            _image(DIGEST_C, architecture=second_child_architecture),
        ),
    )
    load_external_container_images(neo4j_session, [resolution], update_tag=1)
    neo4j_session.run(
        """
        MERGE (container:Container {id: 'synthetic-container'})
        SET container.architecture_normalized = $architecture,
            container.lastupdated = 1
        WITH container
        MATCH (manifest_list:ExternalContainerImage {digest: $digest})
        MERGE (container)-[:HAS_IMAGE]->(manifest_list)
        """,
        architecture=runtime_architecture,
        digest=DIGEST_INDEX,
    ).consume()

    # Act
    run_typed_analysis_job(
        CONTAINER_RESOLVED_IMAGE,
        neo4j_session,
        {"UPDATE_TAG": 2},
    )

    # Assert
    expected = {("synthetic-container", expected_digest)} if expected_digest else set()
    assert (
        check_rels(
            neo4j_session,
            "Container",
            "id",
            "Image",
            "digest",
            "RESOLVED_IMAGE",
        )
        == expected
    )
