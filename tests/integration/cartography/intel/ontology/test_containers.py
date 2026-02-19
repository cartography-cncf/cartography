import cartography.intel.ontology.containers
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _seed_image_nodes(neo4j_session) -> None:
    neo4j_session.run(
        """
        MERGE (:Image {id: 'img-direct', digest: 'sha256:direct', architecture: 'amd64'})
        MERGE (:Image {id: 'img-stale', digest: 'sha256:stale', architecture: 'amd64'})
        MERGE (:Image {id: 'img-ml-amd64', digest: 'sha256:ml-amd64', architecture: 'amd64'})
        MERGE (:Image {id: 'img-ml-arm64', digest: 'sha256:ml-arm64', architecture: 'arm64'})
        MERGE (:Image {id: 'img-aci-a', digest: 'sha256:aci', architecture: 'amd64'})
        MERGE (:Image {id: 'img-aci-b', digest: 'sha256:aci', architecture: 'amd64'})
        MERGE (:ImageManifestList {id: 'ml-main'})
        MERGE (:ImageManifestList {id: 'ml-k8s'})
        MERGE (:ImageManifestList {id: 'ml-unknown'})
        MERGE (:ImageManifestList {id: 'ml-k8s-only'})
        MERGE (:ImageManifestList {id: 'ml-aci'})
        MERGE (:ImageManifestList {id: 'ml-main'})-[:CONTAINS_IMAGE]->(:Image {id: 'img-ml-amd64'})
        MERGE (:ImageManifestList {id: 'ml-main'})-[:CONTAINS_IMAGE]->(:Image {id: 'img-ml-arm64'})
        MERGE (:ImageManifestList {id: 'ml-k8s'})-[:CONTAINS_IMAGE]->(:Image {id: 'img-ml-arm64'})
        MERGE (:ImageManifestList {id: 'ml-k8s-only'})-[:CONTAINS_IMAGE]->(:Image {id: 'img-ml-amd64'})
        MERGE (:ImageManifestList {id: 'ml-unknown'})-[:CONTAINS_IMAGE]->(:Image {id: 'img-ml-arm64'})
        """,
    )


def test_sync_resolved_image_relationships(neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _seed_image_nodes(neo4j_session)

    neo4j_session.run(
        """
        CREATE (ecs1:ECSContainer:Container {
            id: 'ecs-1',
            arn: 'ecs-1',
            lastupdated: $tag,
            architecture: 'amd64',
            architecture_source: 'runtime_api_exact'
        })
        CREATE (ecs2:ECSContainer:Container {
            id: 'ecs-2',
            arn: 'ecs-2',
            lastupdated: $tag,
            architecture: 'arm64',
            architecture_source: 'task_definition_hint'
        })
        CREATE (ecs3:ECSContainer:Container {
            id: 'ecs-3',
            arn: 'ecs-3',
            lastupdated: $tag,
            architecture: 'unknown'
        })
        CREATE (k8s1:KubernetesContainer:Container {
            id: 'k8s-1',
            lastupdated: $tag,
            architecture: 'arm64',
            architecture_source: 'image_digest_exact'
        })
        CREATE (k8s2:KubernetesContainer:Container {
            id: 'k8s-2',
            lastupdated: $tag,
            architecture: 'unknown'
        })
        CREATE (aci1:AzureContainerInstance:Container {
            id: 'aci-1',
            lastupdated: $tag,
            image_digests: ['sha256:aci']
        })
        MERGE (ecs1)-[:HAS_IMAGE]->(:Image {id: 'img-direct'})
        MERGE (ecs1)-[:HAS_IMAGE]->(:ImageManifestList {id: 'ml-main'})
        MERGE (ecs2)-[:HAS_IMAGE]->(:ImageManifestList {id: 'ml-main'})
        MERGE (ecs3)-[:HAS_IMAGE]->(:ImageManifestList {id: 'ml-unknown'})
        MERGE (k8s1)-[:HAS_IMAGE]->(:ImageManifestList {id: 'ml-k8s'})
        MERGE (k8s2)-[:HAS_IMAGE]->(:ImageManifestList {id: 'ml-k8s-only'})
        MERGE (ecs1)-[:RESOLVED_IMAGE {lastupdated: $tag}]->(:Image {id: 'img-stale'})
        """,
        tag=TEST_UPDATE_TAG,
    )

    cartography.intel.ontology.containers.sync(
        neo4j_session, TEST_UPDATE_TAG, {"UPDATE_TAG": TEST_UPDATE_TAG}
    )

    assert check_rels(
        neo4j_session,
        "ECSContainer",
        "id",
        "Image",
        "id",
        "RESOLVED_IMAGE",
        rel_direction_right=True,
    ) == {
        ("ecs-1", "img-direct"),
        ("ecs-2", "img-ml-arm64"),
    }

    assert check_rels(
        neo4j_session,
        "KubernetesContainer",
        "id",
        "Image",
        "id",
        "RESOLVED_IMAGE",
        rel_direction_right=True,
    ) == {
        ("k8s-1", "img-ml-arm64"),
    }

    assert check_rels(
        neo4j_session,
        "AzureContainerInstance",
        "id",
        "Image",
        "id",
        "RESOLVED_IMAGE",
        rel_direction_right=True,
    ) == {
        ("aci-1", "img-aci-a"),
    }
