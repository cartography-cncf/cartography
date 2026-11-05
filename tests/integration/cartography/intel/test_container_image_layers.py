import pytest

from cartography.intel.container_image_layers import get_complete_layer_digests
from cartography.intel.gcp.artifact_registry.supply_chain import (
    GCP_ARTIFACT_REGISTRY_LAYER_GRAPH,
)


@pytest.mark.parametrize("batch_size", [1, 2, 500])
def test_get_complete_layer_digests_preserves_completeness_and_scope(
    neo4j_session, batch_size
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
            digest: image.digest, layer_diff_ids: image.layers
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
            {"digest": "sha256:0", "layers": ["local"], "linked": True},
            {"digest": "sha256:1", "layers": None, "linked": False},
            {"digest": "sha256:2", "layers": [], "linked": False},
            {"digest": "sha256:3", "layers": ["local", "missing"], "linked": True},
            {"digest": "sha256:4", "layers": ["foreign"], "linked": True},
            {"digest": "sha256:5", "layers": ["local"], "linked": True},
            # Layer nodes exist but the image edges do not, so it is refetched.
            {"digest": "sha256:6", "layers": ["local"], "linked": False},
        ],
    ).consume()

    # Act
    result = get_complete_layer_digests(
        neo4j_session,
        GCP_ARTIFACT_REGISTRY_LAYER_GRAPH,
        [f"sha256:{index}" for index in range(7)],
        {"id": "project-1"},
        batch_size=batch_size,
    )

    # Assert
    assert result == {"sha256:0", "sha256:2", "sha256:5"}


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
