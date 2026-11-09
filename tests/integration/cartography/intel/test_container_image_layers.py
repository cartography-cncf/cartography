import pytest

from cartography.intel.container_image_layers import get_complete_layer_digests
from cartography.intel.container_image_layers import refresh_layer_closures
from cartography.intel.gcp.artifact_registry.supply_chain import (
    GCP_ARTIFACT_REGISTRY_LAYER_GRAPH,
)


@pytest.mark.parametrize("batch_size", [1, 2, 500])
@pytest.mark.parametrize(
    ("min_label_provenance_version", "expected"),
    [
        (None, {"sha256:0", "sha256:2", "sha256:5", "sha256:7"}),
        # sha256:5 was enriched before label provenance existed: read it again.
        # sha256:7 already has a source, which its labels could not outrank.
        (1, {"sha256:0", "sha256:2", "sha256:7"}),
    ],
)
def test_get_complete_layer_digests_preserves_completeness_and_scope(
    neo4j_session, batch_size, min_label_provenance_version, expected
):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n").consume()
    neo4j_session.run(
        """
        CREATE (project:GCPProject {id: 'project-1'}),
               (other:GCPProject {id: 'project-2'}),
               (project)-[:RESOURCE]->(:GCPArtifactRegistryImageLayer {id: 'local'}),
               (other)-[:RESOURCE]->(:GCPArtifactRegistryImageLayer {id: 'foreign'})
        WITH project
        UNWIND $images AS image
        CREATE (project)-[:RESOURCE]->(img:GCPArtifactRegistryImage {
            digest: image.digest, layer_diff_ids: image.layers,
            label_provenance_version: image.version, source_uri: image.source
        })
        WITH img, image
        OPTIONAL MATCH (layer:GCPArtifactRegistryImageLayer)
        WHERE image.linked AND layer.id IN image.layers
        FOREACH (_ IN CASE WHEN layer IS NULL THEN [] ELSE [1] END |
            CREATE (img)-[:HAS_LAYER]->(layer),
                   (img)-[:HEAD]->(layer),
                   (img)-[:TAIL]->(layer)
        )
        """,
        images=[
            {"digest": "sha256:0", "layers": ["local"], "linked": True, "version": 1},
            {"digest": "sha256:1", "layers": None, "linked": False},
            {"digest": "sha256:2", "layers": [], "linked": False, "version": 1},
            {"digest": "sha256:3", "layers": ["local", "missing"], "linked": True},
            {"digest": "sha256:4", "layers": ["foreign"], "linked": True},
            {"digest": "sha256:5", "layers": ["local"], "linked": True},
            # Layer nodes exist but the image edges do not, so it is refetched.
            {"digest": "sha256:6", "layers": ["local"], "linked": False},
            {
                "digest": "sha256:7",
                "layers": ["local"],
                "linked": True,
                "source": "https://github.com/example/app",
            },
        ],
    ).consume()

    # Act
    result = get_complete_layer_digests(
        neo4j_session,
        GCP_ARTIFACT_REGISTRY_LAYER_GRAPH,
        [f"sha256:{index}" for index in range(8)],
        {"id": "project-1"},
        batch_size=batch_size,
        min_label_provenance_version=min_label_provenance_version,
    )

    # Assert
    assert result == expected


def test_get_complete_layer_digests_with_empty_cache(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n").consume()
    neo4j_session.run(
        """
        UNWIND range(0, 500) AS i
        CREATE (:GCPArtifactRegistryImage {digest: 'sha256:' + toString(i)})
        """
    ).consume()

    # Act
    result = get_complete_layer_digests(
        neo4j_session,
        GCP_ARTIFACT_REGISTRY_LAYER_GRAPH,
        (f"sha256:{index}" for index in range(501)),
        {"id": "project-1"},
    )

    # Assert
    assert result == set()


def test_refresh_layer_closures_projects_source_to_ontology(neo4j_session):
    # Arrange: an image cached before the ontology source fields existed.
    neo4j_session.run("MATCH (n) DETACH DELETE n").consume()
    neo4j_session.run(
        """
        CREATE (:GCPProject {id: 'project-1'})-[:RESOURCE]->(:GCPArtifactRegistryImage {
            digest: 'sha256:cached', layer_diff_ids: [],
            source_uri: 'https://github.com/example/app', source_revision: 'abc123'
        })
        """
    ).consume()

    # Act
    refresh_layer_closures(
        neo4j_session,
        GCP_ARTIFACT_REGISTRY_LAYER_GRAPH,
        ["sha256:cached"],
        {"id": "project-1"},
        2,
    )

    # Assert
    assert (
        neo4j_session.run(
            """
        MATCH (img:GCPArtifactRegistryImage {digest: 'sha256:cached'})
        RETURN img._ont_source_uri AS uri, img._ont_source_revision AS revision
        """
        ).data()
        == [{"uri": "https://github.com/example/app", "revision": "abc123"}]
    )
