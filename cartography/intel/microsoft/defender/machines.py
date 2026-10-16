import logging
from typing import Any

import neo4j
import requests
from azure.core.credentials import TokenCredential

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.microsoft.defender.client import get_collection
from cartography.intel.microsoft.defender.client import parse_timestamps
from cartography.intel.microsoft.util import normalize_azure_ad_device_id
from cartography.models.microsoft.defender.machine import DefenderMachineSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
MACHINES_URL = "https://api.security.microsoft.com/api/machines"
# The MDE API still requires the legacy resource audience, even on its new host.
MDE_SCOPE = "https://api.securitycenter.microsoft.com/.default"
MACHINE_PAGE_SIZE = 10000
PERMISSION = "WindowsDefenderATP Machine.Read.All"


@timeit
def get_machines(
    session: requests.Session, credential: TokenCredential
) -> list[dict[str, Any]]:
    return get_collection(
        session,
        credential,
        MACHINES_URL,
        MDE_SCOPE,
        {"$top": MACHINE_PAGE_SIZE},
        use_skip=True,
    )


def transform_machines(
    machines: list[dict[str, Any]], tenant_id: str
) -> list[dict[str, Any]]:
    result = []
    for machine in machines:
        normalized_id = normalize_azure_ad_device_id(machine.get("aadDeviceId"))
        data = {
            **machine,
            "id": f"{tenant_id}/{machine['id']}",
            "machine_id": machine["id"],
            "aadDeviceId": machine.get("aadDeviceId") if normalized_id else None,
            "aad_device_id_normalized": normalized_id,
        }
        parse_timestamps(data, ("firstSeen", "lastSeen"))
        result.append(data)
    return result


@timeit
def load_machines(
    neo4j_session: neo4j.Session,
    machines: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DefenderMachineSchema(),
        machines,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


@timeit
def cleanup_machines(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(DefenderMachineSchema(), common_job_parameters).run(
        neo4j_session
    )
