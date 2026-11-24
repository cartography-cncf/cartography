from dataclasses import replace

import pytest

from cartography.intel.container_image_layers import get_complete_layer_digests
from cartography.intel.container_image_layers import refresh_layer_closures
from cartography.intel.gcp.artifact_registry.supply_chain import (
    GCP_ARTIFACT_REGISTRY_LAYER_GRAPH,
)


@pytest.mark.parametrize("batch_size", [1, 2, 500])
@pytest.mark.parametrize(
    "digests",
    [[f"sha256:{index}" for index in range(10)], None],
    ids=["listed", "whole_scope"],
)
@pytest.mark.parametrize(
    ("min_label_provenance_version", "expected"),
    [
        (None, {"sha256:0", "sha256:2", "sha256:5", "sha256:7", "sha256:8"}),
        # sha256:5 was enriched before label provenance existed: read it again.
        # sha256:7 has a source, so its label may name a folder: read it again.
        # sha256:0 has no source label, and sha256:8 already has its folder.
        (2, {"sha256:0", "sha256:2", "sha256:8"}),
    ],
)
def test_get_complete_layer_digests_preserves_completeness_and_scope(
    neo4j_session, batch_size, digests, min_label_provenance_version, expected
):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n").consume()
    neo4j_session.run(
        """
        CREATE (project:GCPProject {id: 'project-1'}),
               (other:GCPProject {id: 'project-2'}),
               (project)-[:RESOURCE]->(local:GCPArtifactRegistryImageLayer {id: 'local'}),
               (project)-[:RESOURCE]->(:GCPArtifactRegistryImageLayer {id: 'unlinked'}),
               (other)-[:RESOURCE]->(:GCPArtifactRegistryImageLayer {id: 'foreign'}),
               (local)-[:NEXT]->(local)
        WITH project
        UNWIND $images AS image
        CREATE (project)-[:RESOURCE]->(img:GCPArtifactRegistryImage {
            digest: image.digest, layer_diff_ids: image.layers,
            label_provenance_version: image.version, source_uri: image.source,
            source_path_uri: image.source_path
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
            # A repeated layer needs its NEXT self-loop, which exists.
            {
                "digest": "sha256:8",
                "layers": ["local", "local"],
                "linked": True,
                "version": 1,
                "source": "https://github.com/example/app",
                "source_path": "https://github.com/example/app/tree/main/api",
            },
            # Every layer edge exists but local has no NEXT edge to unlinked.
            {
                "digest": "sha256:9",
                "layers": ["local", "unlinked"],
                "linked": True,
                "version": 1,
            },
        ],
    ).consume()

    # Act
    result = get_complete_layer_digests(
        neo4j_session,
        GCP_ARTIFACT_REGISTRY_LAYER_GRAPH,
        digests,
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


@pytest.mark.parametrize(
    ("closure_cleaned_by_reachability", "expected"),
    [
        (
            True,
            {
                ("image", 2),
                ("project_layer_link", 2),
                ("BUILT_FROM", 2),
                ("layer", 1),
                ("HAS_LAYER", 1),
                ("HEAD", 1),
                ("TAIL", 1),
                ("NEXT", 1),
            },
        ),
        (
            False,
            {
                ("image", 2),
                ("project_layer_link", 2),
                ("BUILT_FROM", 2),
                ("layer", 2),
                ("HAS_LAYER", 2),
                ("HEAD", 2),
                ("TAIL", 2),
                ("NEXT", 2),
            },
        ),
    ],
    ids=["cleaned_by_reachability", "cleaned_by_timestamp"],
)
def test_refresh_layer_closures_refreshes_what_cleanup_reads(
    neo4j_session, closure_cleaned_by_reachability, expected
):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n").consume()
    neo4j_session.run(
        """
        CREATE (project:GCPProject {id: 'project-1'})
        CREATE (img:GCPArtifactRegistryImage {
            digest: 'sha256:img', layer_diff_ids: ['sha256:a', 'sha256:b'],
            lastupdated: 1
        })
        CREATE (a:GCPArtifactRegistryImageLayer {id: 'sha256:a', lastupdated: 1})
        CREATE (b:GCPArtifactRegistryImageLayer {id: 'sha256:b', lastupdated: 1})
        CREATE (project)-[:RESOURCE {lastupdated: 1}]->(a)
        CREATE (project)-[:RESOURCE {lastupdated: 1}]->(b)
        CREATE (img)-[:HAS_LAYER {lastupdated: 1}]->(a)
        CREATE (img)-[:HAS_LAYER {lastupdated: 1}]->(b)
        CREATE (img)-[:HEAD {lastupdated: 1}]->(a)
        CREATE (img)-[:TAIL {lastupdated: 1}]->(b)
        CREATE (a)-[:NEXT {lastupdated: 1}]->(b)
        CREATE (img)-[:BUILT_FROM {
            lastupdated: 1,
            _sub_resource_label: 'GCPProject',
            _sub_resource_id: 'project-1'
        }]->(:GCPArtifactRegistryImage {digest: 'sha256:parent', lastupdated: 1})
        """
    ).consume()
    shape = replace(
        GCP_ARTIFACT_REGISTRY_LAYER_GRAPH,
        closure_cleaned_by_reachability=closure_cleaned_by_reachability,
    )

    # Act
    refresh_layer_closures(
        neo4j_session,
        shape,
        ["sha256:img"],
        {"id": "project-1"},
        2,
    )

    # Assert
    rows = neo4j_session.run(
        """
        MATCH (img:GCPArtifactRegistryImage {digest: 'sha256:img'})
        RETURN 'image' AS entity, img.lastupdated AS tag
        UNION
        MATCH (:GCPArtifactRegistryImage)-[r:BUILT_FROM]->()
        RETURN 'BUILT_FROM' AS entity, r.lastupdated AS tag
        UNION
        MATCH (layer:GCPArtifactRegistryImageLayer)
        RETURN 'layer' AS entity, layer.lastupdated AS tag
        UNION
        MATCH (:GCPProject)-[r:RESOURCE]->(:GCPArtifactRegistryImageLayer)
        RETURN 'project_layer_link' AS entity, r.lastupdated AS tag
        UNION
        MATCH ()-[r:HAS_LAYER|HEAD|TAIL|NEXT]->()
        RETURN type(r) AS entity, r.lastupdated AS tag
        """
    ).data()
    assert {(row["entity"], row["tag"]) for row in rows} == expected
