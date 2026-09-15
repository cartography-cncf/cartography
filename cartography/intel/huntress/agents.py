import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.huntress.util import get_paginated_huntress_items
from cartography.intel.huntress.util import required_id
from cartography.models.huntress.agent import HuntressAgentSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(api_session: requests.Session, base_uri: str) -> list[dict[str, Any]]:
    return get_paginated_huntress_items(api_session, base_uri, "agents", "agents")


def transform(api_result: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for agent in api_result:
        result.append(
            {
                "id": required_id(agent, "Agent"),
                "organization_id": agent.get("organization_id"),
                "hostname": agent.get("hostname"),
                "serial_number": agent.get("serial_number"),
                "domain_name": agent.get("domain_name"),
                "external_ip": agent.get("external_ip"),
                "ipv4_address": agent.get("ipv4_address"),
                "ipv4_addresses": agent.get("ipv4_addresses"),
                "mac_addresses": agent.get("mac_addresses"),
                "platform": agent.get("platform"),
                "os": agent.get("os"),
                "os_build_version": agent.get("os_build_version"),
                "os_major": agent.get("os_major"),
                "os_minor": agent.get("os_minor"),
                "os_patch": agent.get("os_patch"),
                "arch": agent.get("arch"),
                "service_pack_major": agent.get("service_pack_major"),
                "service_pack_minor": agent.get("service_pack_minor"),
                "win_build_number": agent.get("win_build_number"),
                "version": agent.get("version"),
                "edr_version": agent.get("edr_version"),
                "firewall_status": agent.get("firewall_status"),
                "defender_status": agent.get("defender_status"),
                "defender_substatus": agent.get("defender_substatus"),
                "defender_policy_status": agent.get("defender_policy_status"),
                "tamper_protection_configured": agent.get(
                    "tamper_protection_configured"
                ),
                "tamper_protection_actual": agent.get("tamper_protection_actual"),
                "tags": agent.get("tags"),
                "last_callback_at": agent.get("last_callback_at"),
                "last_survey_at": agent.get("last_survey_at"),
                "created_at": agent.get("created_at"),
                "updated_at": agent.get("updated_at"),
            }
        )
    return result


def load_agents(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: int,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        HuntressAgentSchema(),
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(HuntressAgentSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_uri: str,
    account_id: int,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    raw_data = get(api_session, base_uri)
    agents = transform(raw_data)
    load_agents(neo4j_session, agents, account_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
