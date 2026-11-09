import logging

import neo4j

import cartography.intel.orca.alerts
import cartography.intel.orca.vulnerabilities
from cartography.config import Config
from cartography.intel.orca import api
from cartography.intel.orca.organization import load_organization
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
def start_orca_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """Ingest organization-wide Orca security findings."""
    api_endpoint = config.orca_api_endpoint
    api_token = config.orca_api_token
    if not api_endpoint or not api_token:
        logger.info(
            "Orca import is not configured - skipping this module. "
            "Set orca_api_endpoint and orca_api_token to enable.",
        )
        return

    try:
        api_endpoint = api.normalize_api_endpoint(api_endpoint)
    except ValueError as exc:
        logger.warning("Invalid Orca API endpoint - skipping this module: %s", exc)
        return
    session = api.create_session(api_token)
    try:
        organization = api.get_organization(session, api_endpoint)
        organization_id = organization["id"]
        common_job_parameters = {
            "UPDATE_TAG": config.update_tag,
            "ORCA_ORGANIZATION_ID": organization_id,
        }

        load_organization(
            neo4j_session,
            organization,
            config.update_tag,
        )
        alerts_complete = cartography.intel.orca.alerts.sync(
            neo4j_session,
            session,
            api_endpoint,
            organization_id,
            config.update_tag,
        )
        vulnerabilities_complete = cartography.intel.orca.vulnerabilities.sync(
            neo4j_session,
            session,
            api_endpoint,
            organization_id,
            config.update_tag,
        )

        # Cleanup is deliberately deferred until every feed has been fetched, and
        # skipped for a feed that came back short so its missing rows survive.
        if alerts_complete:
            cartography.intel.orca.alerts.cleanup(
                neo4j_session,
                common_job_parameters,
            )
        if vulnerabilities_complete:
            cartography.intel.orca.vulnerabilities.cleanup(
                neo4j_session,
                common_job_parameters,
            )
        if not (alerts_complete and vulnerabilities_complete):
            logger.warning(
                "Orca fetch for organization %s was incomplete; skipped stale "
                "cleanup for alerts=%s vulnerabilities=%s and left sync "
                "metadata unchanged.",
                organization_id,
                not alerts_complete,
                not vulnerabilities_complete,
            )
            return
        merge_module_sync_metadata(
            neo4j_session,
            group_type="OrcaOrganization",
            group_id=organization_id,
            synced_type="OrcaData",
            update_tag=config.update_tag,
            stat_handler=stat_handler,
        )
    finally:
        session.close()
