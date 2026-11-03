import logging
from collections.abc import Collection

import neo4j
import requests
from azure.core.credentials import TokenCredential

from cartography.config import Config
from cartography.intel.microsoft import credentials
from cartography.intel.microsoft.defender import alerts
from cartography.intel.microsoft.defender import machines
from cartography.intel.microsoft.defender.client import create_session
from cartography.intel.microsoft.defender.client import fetch_optional
from cartography.intel.microsoft.resources import DEFENDER_RESOURCES
from cartography.intel.microsoft.util import requested_microsoft_syncs
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    credential: TokenCredential,
    tenant_id: str,
    update_tag: int,
    requested: Collection[str] = DEFENDER_RESOURCES,
) -> None:
    """
    Sync the requested Defender datasets for one tenant.

    Every requested read and transform finishes before any write or cleanup, so a
    failed read leaves the previous snapshot intact. A dataset the tenant can't
    provide is skipped and neither loaded nor cleaned up.
    """
    raw_machines = (
        fetch_optional(
            "machines",
            machines.PERMISSION,
            lambda: machines.get_machines(session, credential),
        )
        if "defender_machines" in requested
        else None
    )
    raw_alerts = (
        fetch_optional(
            "alerts",
            alerts.PERMISSION,
            lambda: alerts.get_alerts(session, credential),
        )
        if "defender_alerts" in requested
        else None
    )
    machine_data = (
        machines.transform_machines(raw_machines, tenant_id)
        if raw_machines is not None
        else None
    )
    alert_data = (
        alerts.transform_alerts(raw_alerts, tenant_id)
        if raw_alerts is not None
        else None
    )

    if machine_data is not None:
        machines.load_machines(neo4j_session, machine_data, tenant_id, update_tag)
    if alert_data is not None:
        alerts.load_alerts(neo4j_session, alert_data, tenant_id, update_tag)

    common_job_parameters = {"TENANT_ID": tenant_id, "UPDATE_TAG": update_tag}
    if alert_data is not None:
        alerts.cleanup_alerts(neo4j_session, common_job_parameters)
    if machine_data is not None:
        machines.cleanup_machines(neo4j_session, common_job_parameters)


@timeit
def start_defender_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    requested = requested_microsoft_syncs(config)
    datasets = [
        resource
        for resource in DEFENDER_RESOURCES
        if requested is None or resource in requested
    ]
    if not datasets:
        return
    tenant_id = config.microsoft_tenant_id
    client_id = config.microsoft_client_id
    client_secret = config.microsoft_client_secret
    if not tenant_id or not client_id or not client_secret:
        raise ValueError(
            "Microsoft Defender requires Microsoft service principal credentials"
        )
    credential = credentials.make_credential(
        tenant_id,
        client_id,
        client_secret,
    )
    with create_session() as session:
        sync(
            neo4j_session,
            session,
            credential,
            tenant_id,
            config.update_tag,
            datasets,
        )
