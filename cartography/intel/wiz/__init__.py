import logging
from urllib.parse import urlparse

import neo4j
import requests

import cartography.intel.wiz.findings
import cartography.intel.wiz.issues
from cartography.client.core.tx import load
from cartography.config import Config
from cartography.intel.wiz.api import get_access_token
from cartography.models.wiz.tenant import WizTenantSchema
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)

WIZ_DEFAULT_AUTH_URL = "https://auth.app.wiz.io/oauth/token"


def _tenant_id_from_graphql_url(graphql_url: str) -> str:
    parsed = urlparse(graphql_url)
    return parsed.netloc or graphql_url


@timeit
def load_tenant(
    neo4j_session: neo4j.Session,
    tenant_id: str,
    graphql_url: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        WizTenantSchema(),
        [{"id": tenant_id, "graphql_url": graphql_url}],
        lastupdated=update_tag,
    )


@timeit
def start_wiz_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    if (
        not config.wiz_graphql_url
        or not config.wiz_client_id
        or not config.wiz_client_secret
    ):
        logger.info(
            "Wiz import is not configured - skipping this module. "
            "Set wiz_graphql_url, wiz_client_id, and wiz_client_secret to enable.",
        )
        return

    if config.wiz_lookback_days is not None and config.wiz_lookback_days < 1:
        logger.warning(
            "Wiz lookback days is less than 1 - skipping this module. "
            "Set wiz_lookback_days to a value greater than 0 to enable.",
        )
        return

    auth_url = config.wiz_auth_url or WIZ_DEFAULT_AUTH_URL
    if config.wiz_tenant_id:
        tenant_id = config.wiz_tenant_id
    else:
        tenant_id = _tenant_id_from_graphql_url(config.wiz_graphql_url)
        logger.warning(
            "Wiz tenant ID is not configured; using GraphQL API hostname %s as "
            "WizTenant id. Set wiz_tenant_id when syncing multiple Wiz tenants "
            "to the same graph.",
            tenant_id,
        )

    do_cleanup = config.wiz_lookback_days is None and not config.wiz_project_ids
    if config.wiz_lookback_days is not None:
        logger.warning(
            "Wiz lookback mode is incremental; skipping Wiz cleanup so older "
            "unchanged issues and findings are not deleted.",
        )
    if config.wiz_project_ids:
        logger.warning(
            "Wiz project filter is configured; skipping Wiz cleanup because "
            "project-filtered imports are partial tenant syncs.",
        )

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "WIZ_TENANT_ID": tenant_id,
    }

    session = requests.Session()
    token = get_access_token(
        session,
        auth_url,
        config.wiz_client_id,
        config.wiz_client_secret,
    )

    load_tenant(
        neo4j_session,
        tenant_id,
        config.wiz_graphql_url,
        config.update_tag,
    )
    cartography.intel.wiz.issues.sync(
        neo4j_session,
        session,
        config.wiz_graphql_url,
        token,
        tenant_id,
        config.update_tag,
        common_job_parameters,
        config.wiz_lookback_days,
        config.wiz_project_ids,
        do_cleanup=False,
    )
    cartography.intel.wiz.findings.sync(
        neo4j_session,
        session,
        config.wiz_graphql_url,
        token,
        tenant_id,
        config.update_tag,
        common_job_parameters,
        config.wiz_lookback_days,
        config.wiz_project_ids,
        do_cleanup=False,
    )

    if do_cleanup:
        cartography.intel.wiz.findings.cleanup(
            neo4j_session,
            common_job_parameters,
        )
        cartography.intel.wiz.issues.cleanup(neo4j_session, common_job_parameters)

    merge_module_sync_metadata(
        neo4j_session,
        group_type="WizTenant",
        group_id=tenant_id,
        synced_type="WizData",
        update_tag=config.update_tag,
        stat_handler=stat_handler,
    )
