import logging
from typing import Any

import neo4j

import cartography.intel.sentra.alerts
import cartography.intel.sentra.data_classes
import cartography.intel.sentra.data_stores
import cartography.intel.sentra.policies
from cartography.client.core.tx import load
from cartography.config import Config
from cartography.intel.sentra import api
from cartography.models.sentra.tenant import SentraTenantSchema
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
def load_tenant(
    neo4j_session: neo4j.Session,
    current_user: dict[str, Any],
    api_url: str,
    update_tag: int,
) -> str:
    tenant_id = str(current_user["organization_id"])
    load(
        neo4j_session,
        SentraTenantSchema(),
        [
            {
                "id": tenant_id,
                "name": current_user.get("organization_name"),
                "organization_type": current_user.get("organization_type"),
                "api_url": api_url,
            },
        ],
        lastupdated=update_tag,
    )
    return tenant_id


@timeit
def start_sentra_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """Ingest Sentra data classes, data stores, policies, and active alerts."""
    if not config.sentra_api_key:
        logger.info(
            "Sentra import is not configured - skipping this module. "
            "Set sentra_api_key to enable.",
        )
        return

    api_url = (config.sentra_api_url or api.SENTRA_DEFAULT_API_URL).rstrip("/")
    session = api.build_session(config.sentra_api_key)

    current_user = api.get_current_user(session, api_url)
    tenant_id = load_tenant(neo4j_session, current_user, api_url, config.update_tag)
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "TENANT_ID": tenant_id,
    }

    # Data classes, data stores, and policies load before alerts, so each
    # relationship finds the node it points to.
    data_classes = cartography.intel.sentra.data_classes.sync(
        neo4j_session,
        session,
        api_url,
        tenant_id,
        config.update_tag,
        common_job_parameters,
    )
    aws_ids_by_store = cartography.intel.sentra.data_stores.sync(
        neo4j_session,
        session,
        api_url,
        tenant_id,
        config.update_tag,
        common_job_parameters,
    )
    cartography.intel.sentra.policies.sync(
        neo4j_session,
        session,
        api_url,
        tenant_id,
        config.update_tag,
        common_job_parameters,
        data_classes,
    )
    cartography.intel.sentra.alerts.sync(
        neo4j_session,
        session,
        api_url,
        tenant_id,
        config.update_tag,
        common_job_parameters,
        aws_ids_by_store,
    )

    merge_module_sync_metadata(
        neo4j_session,
        group_type="SentraTenant",
        group_id=tenant_id,
        synced_type="SentraData",
        update_tag=config.update_tag,
        stat_handler=stat_handler,
    )
