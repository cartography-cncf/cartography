import logging

from neo4j import Session

from cartography.config import Config
from cartography.intel.kubernetes.clusters import sync_kubernetes_cluster
from cartography.intel.kubernetes.namespaces import sync_namespaces
from cartography.intel.kubernetes.pods import sync_pods
from cartography.intel.kubernetes.secrets import sync_secrets
from cartography.intel.kubernetes.services import sync_services
from cartography.intel.kubernetes.util import get_k8s_clients
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_k8s_ingestion(session: Session, config: Config) -> None:
    if not config.update_tag:
        logger.error("Cartography update tag not provided.")
        return

    if not config.k8s_kubeconfig:
        logger.error("Kubernetes kubeconfig not provided.")
        return

    common_job_parameters = {"UPDATE_TAG": config.update_tag}

    for client in get_k8s_clients(config.k8s_kubeconfig):
        logger.info(f"Syncing data for k8s cluster {client.name}...")
        try:
            cluster_info = sync_kubernetes_cluster(
                session,
                client,
                config.update_tag,
                common_job_parameters,
            )
            common_job_parameters["CLUSTER_ID"] = cluster_info.get("id")

            sync_namespaces(session, client, config.update_tag, common_job_parameters)
            all_pods = sync_pods(
                session,
                client,
                config.update_tag,
                common_job_parameters,
            )
            sync_secrets(session, client, config.update_tag, common_job_parameters)
            sync_services(
                session,
                client,
                all_pods,
                config.update_tag,
                common_job_parameters,
            )
        except Exception:
            logger.exception(f"Failed to sync data for k8s cluster {client.name}...")
            raise
