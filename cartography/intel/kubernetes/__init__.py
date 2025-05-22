import logging
from typing import Optional

from neo4j import Session

from cartography.config import Config
from cartography.intel.kubernetes.namespaces import sync_namespaces
from cartography.intel.kubernetes.pods import sync_pods
from cartography.intel.kubernetes.secrets import sync_secrets
from cartography.intel.kubernetes.services import sync_services
from cartography.intel.kubernetes.util import get_k8s_clients
from cartography.settings import check_module_settings
from cartography.settings import populate_settings_from_config
from cartography.settings import settings
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_k8s_ingestion(session: Session, config: Optional[Config] = None) -> None:
    # DEPRECATED: This is a temporary measure to support the old config format
    # and the new config format. The old config format is deprecated and will be removed in a future release.
    if config is not None:
        populate_settings_from_config(config)

    if not check_module_settings("k8s", ["kubeconfig"]):
        return

    common_job_parameters = {"UPDATE_TAG": settings.common.update_tag}

    for client in get_k8s_clients(settings.k8s.kubeconfig):
        logger.info(f"Syncing data for k8s cluster {client.name}...")
        try:
            cluster = sync_namespaces(session, client, settings.common.update_tag)
            pods = sync_pods(session, client, settings.common.update_tag, cluster)
            sync_services(session, client, settings.common.update_tag, cluster, pods)
            sync_secrets(session, client, settings.common.update_tag, cluster)
        except Exception:
            logger.exception(f"Failed to sync data for k8s cluster {client.name}...")
            raise

    run_cleanup_job(
        "kubernetes_import_cleanup.json",
        session,
        common_job_parameters,
        package="cartography.data.jobs.cleanup",
    )
