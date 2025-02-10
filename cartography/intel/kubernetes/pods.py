import logging
from typing import Dict
from typing import List

from neo4j import Session

from cartography.intel.kubernetes.util import get_epoch
from cartography.intel.kubernetes.util import K8sClient
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_pods(
    session: Session,
    client: K8sClient,
    update_tag: int,
    cluster: Dict,
) -> List[Dict]:
    pods = get_pods(client, cluster)
    load_pods(session, pods, update_tag)
    return pods


@timeit
def get_pods(client: K8sClient, cluster: Dict) -> List[Dict]:
    pods = list()
    for pod in client.core.list_pod_for_all_namespaces().items:
        containers = {}
        for container in pod.spec.containers:
            containers[container.name] = {
                "name": container.name,
                "image": container.image,
                "uid": f"{pod.metadata.uid}-{container.name}",
            }
        if pod.status and pod.status.container_statuses:
            for status in pod.status.container_statuses:
                if status.name in containers:
                    _state = "waiting"
                    if status.state.running:
                        _state = "running"
                    elif status.state.terminated:
                        _state = "terminated"
                    try:
                        image_sha = status.image_id.split("@")[1]
                    except IndexError:
                        image_sha = None
                    containers[status.name]["status"] = {
                        "image_id": status.image_id,
                        "image_sha": image_sha,
                        "ready": status.ready,
                        "started": status.started,
                        "state": _state,
                    }
        pods.append(
            {
                "uid": pod.metadata.uid,
                "name": pod.metadata.name,
                "status_phase": pod.status.phase,
                "creation_timestamp": get_epoch(pod.metadata.creation_timestamp),
                "deletion_timestamp": get_epoch(pod.metadata.deletion_timestamp),
                "namespace": pod.metadata.namespace,
                "node": pod.spec.node_name,
                "cluster_uid": cluster["uid"],
                "labels": pod.metadata.labels,
                "containers": list(containers.values()),
            },
        )
    return pods


def load_pods(session: Session, data: List[Dict], update_tag: int) -> None:
    ingestion_cypher_query = """
    UNWIND $pods as k8pod
        MERGE (pod:KubernetesPod {id: k8pod.uid})
        ON CREATE SET pod.firstseen = timestamp()
        SET pod.lastupdated = $update_tag,
            pod.name = k8pod.name,
            pod.status_phase = k8pod.status_phase,
            pod.created_at = k8pod.creation_timestamp,
            pod.deleted_at = k8pod.deletion_timestamp
        WITH pod, k8pod.namespace as ns, k8pod.cluster_uid as cuid, k8pod.containers as k8containers
        MATCH (cluster:KubernetesCluster {id: cuid})-[:HAS_NAMESPACE]->(space:KubernetesNamespace {name: ns})
        MERGE (space)-[rel1:HAS_POD]->(pod)
        ON CREATE SET rel1.firstseen = timestamp()
        SET rel1.lastupdated = $update_tag
        WITH pod, space, cluster, k8containers
        UNWIND k8containers as k8container
            MERGE (container: KubernetesContainer {id: k8container.uid})
            ON CREATE SET container.firstseen = timestamp()
            SET container.image = k8container.image,
                container.status_image_id = k8container.status.image_id,
                container.status_image_sha = k8container.status.image_sha,
                container.status_ready = k8container.status.ready,
                container.status_started = k8container.status.started,
                container.status_state = k8container.status.state,
                container.name = k8container.name,
                container.lastupdated = $update_tag
            WITH pod, space, cluster, container
            MERGE (pod)-[rel2:HAS_CONTAINER]->(container)
            ON CREATE SET rel2.firstseen = timestamp()
            SET rel2.lastupdated = $update_tag
            WITH pod, space, container
            MERGE (cluster)-[rel3:HAS_POD]->(pod)
            ON CREATE SET rel3.firstseen = timestamp()
            SET rel3.lastupdated = $update_tag
    """
    logger.info(f"Loading {len(data)} kubernetes pods.")
    session.run(ingestion_cypher_query, pods=data, update_tag=update_tag)
