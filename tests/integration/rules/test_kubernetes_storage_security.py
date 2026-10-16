from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.rules.data.rules.kubernetes_storage_security import (
    kubernetes_containers_using_raw_block_persistent_storage,
)
from cartography.rules.data.rules.kubernetes_storage_security import (
    kubernetes_internet_exposed_containers_with_writable_persistent_storage,
)


def _reset_graph(neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")


def _seed_storage_graph(neo4j_session) -> None:
    neo4j_session.run(
        """
        CREATE (writable:KubernetesPersistentVolumeClaim {
            id: 'test-cluster/apps/writable-data',
            name: 'writable-data'
        })
        CREATE (read_only:KubernetesPersistentVolumeClaim {
            id: 'test-cluster/apps/read-only-data',
            name: 'read-only-data'
        })
        CREATE (block_a:KubernetesPersistentVolumeClaim {
            id: 'test-cluster/jobs/block-a',
            name: 'block-a'
        })
        CREATE (block_b:KubernetesPersistentVolumeClaim {
            id: 'test-cluster/jobs/block-b',
            name: 'block-b'
        })
        CREATE (exposed:KubernetesContainer {
            id: 'test-cluster/apps/web/api',
            name: 'api',
            namespace: 'apps',
            cluster_name: 'test-cluster',
            exposed_internet: true,
            persistent_volume_claim_read_write_ids: ['test-cluster/apps/writable-data'],
            persistent_volume_claim_mounts: '[{"claim_id":"test-cluster/apps/read-only-data","mount_path":"/reference","read_only":true},{"claim_id":"test-cluster/apps/writable-data","mount_path":"/data","read_only":false}]'
        })
        CREATE (internal:KubernetesContainer {
            id: 'test-cluster/apps/worker/worker',
            name: 'worker',
            namespace: 'apps',
            cluster_name: 'test-cluster',
            exposed_internet: false,
            persistent_volume_claim_read_write_ids: ['test-cluster/apps/writable-data']
        })
        CREATE (block:KubernetesContainer {
            id: 'test-cluster/jobs/processor/processor',
            name: 'processor',
            namespace: 'jobs',
            cluster_name: 'test-cluster',
            exposed_internet: false,
            persistent_volume_claim_devices: '[{"claim_id":"test-cluster/jobs/block-a","device_path":"/dev/xvda"},{"claim_id":"test-cluster/jobs/block-b","device_path":"/dev/xvdb"}]'
        })
        CREATE (exposed)-[:MOUNTS]->(writable)
        CREATE (exposed)-[:MOUNTS]->(read_only)
        CREATE (internal)-[:MOUNTS]->(writable)
        CREATE (block)-[:USES_BLOCK_DEVICE]->(block_b)
        CREATE (block)-[:USES_BLOCK_DEVICE]->(block_a)
        """
    ).consume()


def test_internet_exposed_writable_storage_fact(neo4j_session) -> None:
    # Arrange
    _reset_graph(neo4j_session)
    _seed_storage_graph(neo4j_session)
    fact = (
        kubernetes_internet_exposed_containers_with_writable_persistent_storage.facts[0]
    )

    # Act
    findings = neo4j_session.execute_read(read_list_of_dicts_tx, fact.cypher_query)
    count = neo4j_session.execute_read(read_list_of_dicts_tx, fact.cypher_count_query)

    # Assert
    assert findings == [
        {
            "container_name": "api",
            "container_id": "test-cluster/apps/web/api",
            "namespace": "apps",
            "cluster_name": "test-cluster",
            "claim_names": ["writable-data"],
            "claim_ids": ["test-cluster/apps/writable-data"],
            "mount_details": '[{"claim_id":"test-cluster/apps/read-only-data","mount_path":"/reference","read_only":true},{"claim_id":"test-cluster/apps/writable-data","mount_path":"/data","read_only":false}]',
        }
    ]
    assert count == [{"count": 3}]
    assert len(list(neo4j_session.run(fact.cypher_visual_query))) == 1


def test_raw_block_persistent_storage_fact(neo4j_session) -> None:
    # Arrange
    _reset_graph(neo4j_session)
    _seed_storage_graph(neo4j_session)
    fact = kubernetes_containers_using_raw_block_persistent_storage.facts[0]

    # Act
    findings = neo4j_session.execute_read(read_list_of_dicts_tx, fact.cypher_query)
    count = neo4j_session.execute_read(read_list_of_dicts_tx, fact.cypher_count_query)

    # Assert
    assert findings == [
        {
            "container_name": "processor",
            "container_id": "test-cluster/jobs/processor/processor",
            "namespace": "jobs",
            "cluster_name": "test-cluster",
            "claim_names": ["block-a", "block-b"],
            "claim_ids": ["test-cluster/jobs/block-a", "test-cluster/jobs/block-b"],
            "device_details": '[{"claim_id":"test-cluster/jobs/block-a","device_path":"/dev/xvda"},{"claim_id":"test-cluster/jobs/block-b","device_path":"/dev/xvdb"}]',
        }
    ]
    assert count == [{"count": 3}]
    assert len(list(neo4j_session.run(fact.cypher_visual_query))) == 2
