import logging

import neo4j

import cartography.intel.sweet.attack_chains
import cartography.intel.sweet.aws
import cartography.intel.sweet.vulnerabilities
from cartography.client.core.tx import load
from cartography.config import Config
from cartography.intel.sweet import api
from cartography.models.sweet.tenant import SweetTenantSchema
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
def load_tenant(
    neo4j_session: neo4j.Session,
    tenant_id: str,
    api_url: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SweetTenantSchema(),
        [{"id": tenant_id, "api_url": api_url}],
        lastupdated=update_tag,
    )


@timeit
def start_sweet_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """Ingest Sweet Security AWS connections, runtime vulnerabilities, and attack chains."""
    api_key = config.sweet_api_key
    api_secret = config.sweet_api_secret
    tenant_id = config.sweet_tenant_id
    if not (api_key or api_secret or tenant_id):
        logger.info(
            "Sweet import is not configured - skipping this module. "
            "Set sweet_api_key, sweet_api_secret, and sweet_tenant_id to enable.",
        )
        return
    if not (api_key and api_secret and tenant_id):
        missing = [
            name
            for name, value in (
                ("sweet_api_key", api_key),
                ("sweet_api_secret", api_secret),
                ("sweet_tenant_id", tenant_id),
            )
            if not value
        ]
        raise ValueError(
            "Sweet import is partially configured; missing "
            f"{', '.join(missing)}. Check --sweet-tenant-id and that the "
            "--sweet-api-key-env-var and --sweet-api-secret-env-var variables "
            "are set.",
        )

    api_url = api.normalize_api_url(config.sweet_api_url or api.DEFAULT_API_URL)

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "SWEET_TENANT_ID": tenant_id,
    }

    session = api.create_session()
    try:
        api.authenticate(session, api_url, api_key, api_secret)
        load_tenant(neo4j_session, tenant_id, api_url, config.update_tag)
        cartography.intel.sweet.aws.sync(
            neo4j_session,
            session,
            api_url,
            tenant_id,
            config.update_tag,
            common_job_parameters,
        )
        cartography.intel.sweet.vulnerabilities.sync(
            neo4j_session,
            session,
            api_url,
            tenant_id,
            config.update_tag,
            common_job_parameters,
        )
        cartography.intel.sweet.attack_chains.sync(
            neo4j_session,
            session,
            api_url,
            tenant_id,
            config.update_tag,
            common_job_parameters,
        )
    finally:
        session.close()

    merge_module_sync_metadata(
        neo4j_session,
        group_type="SweetTenant",
        group_id=tenant_id,
        synced_type="SweetData",
        update_tag=config.update_tag,
        stat_handler=stat_handler,
    )
