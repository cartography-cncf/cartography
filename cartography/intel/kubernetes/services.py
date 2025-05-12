import logging
from typing import Dict
from typing import List

from neo4j import Session

from cartography.intel.kubernetes.util import get_epoch
from cartography.intel.kubernetes.util import K8sClient
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_services(
    session: Session,
    client: K8sClient,
    update_tag: int,
    cluster: Dict,
    pods: List[Dict],
) -> None:
    services = get_services(client, cluster, pods)
    load_services(session, services, update_tag)


@timeit
def get_services(client: K8sClient, cluster: Dict, pods: List[Dict]) -> List[Dict]:
    services = list()
    for service in client.core.list_service_for_all_namespaces().items:
        item = {
            "uid": service.metadata.uid,
            "name": service.metadata.name,
            "creation_timestamp": get_epoch(service.metadata.creation_timestamp),
            "deletion_timestamp": get_epoch(service.metadata.deletion_timestamp),
            "namespace": service.metadata.namespace,
            "cluster_uid": cluster["uid"],
            "type": service.spec.type,
            "selector": service.spec.selector,
            "load_balancer_ip": service.spec.load_balancer_ip,
        }

        ingresses = service.status.load_balancer.ingress
        for ingress in ingresses or list():
            item.update({"ingress_host": ingress.hostname, "ingress_ip": ingress.ip})

        service_pods = list()
        for pod in pods:
            is_service_pod = True if service.spec.selector else False
            for selector in service.spec.selector or dict():
                if (
                    not pod.get("labels")
                    or selector not in pod["labels"]
                    or service.spec.selector[selector] != pod["labels"][selector]
                ):
                    is_service_pod = False
                    break
            if is_service_pod:
                service_pods.append(pod)
        item["pods"] = service_pods
        services.append(item)
    return services


def load_services(session: Session, data: List[Dict], update_tag: int) -> None:
    ingestion_cypher_query = """
    UNWIND $services as k8service
        MERGE (service:KubernetesService {id: k8service.uid})
        ON CREATE SET service.firstseen = timestamp()
        SET service.lastupdated = $update_tag,
            service.name = k8service.name,
            service.created_at = k8service.creation_timestamp,
            service.deleted_at = k8service.deletion_timestamp,
            service.type = k8service.type,
            service.load_balancer_ip = k8service.load_balancer_ip,
            service.ingress_host = k8service.ingress_host,
            service.ingress_ip = k8service.ingress_ip
        WITH service, k8service.namespace as ns, k8service.cluster_uid as cuid, k8service.pods as k8pods
        MATCH (cluster:KubernetesCluster {id: cuid})-[:HAS_NAMESPACE]->(space:KubernetesNamespace {name: ns})
        MERGE (space)-[rel1:HAS_SERVICE]->(service)
        ON CREATE SET rel1.firstseen = timestamp()
        SET rel1.lastupdated = $update_tag
        WITH service, k8pods
        UNWIND k8pods as k8pod
            MATCH (pod:KubernetesPod {id: k8pod.uid})
            MERGE (service)-[rel2:SERVES_POD]->(pod)
            ON CREATE SET rel2.firstseen = timestamp()
            SET rel2.lastupdated = $update_tag
    """
    logger.info(f"Loading {len(data)} kubernetes services.")
    session.run(ingestion_cypher_query, services=data, update_tag=update_tag)
