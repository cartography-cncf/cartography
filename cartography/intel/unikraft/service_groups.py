import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.unikraft.util import check_count_matches
from cartography.intel.unikraft.util import list_resources
from cartography.intel.unikraft.util import METRO_BASE_URLS
from cartography.intel.unikraft.util import require_non_empty
from cartography.models.unikraft.service_group import UnikraftServiceGroupSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    return list_resources(session, f"{base_url}/v1/services", "service_groups")


def transform(service_groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for service_group in service_groups:
        instance_ids = [
            instance["uuid"]
            for instance in service_group.get("instances") or []
            if instance.get("uuid")
        ]
        certificate_ids = {
            domain["certificate"]["uuid"]
            for domain in service_group.get("domains") or []
            if (domain.get("certificate") or {}).get("uuid")
        }
        domains = sorted(
            {
                domain["fqdn"]
                for domain in service_group.get("domains") or []
                if domain.get("fqdn")
            }
        )
        result.append(
            {
                "uuid": require_non_empty(
                    service_group.get("uuid"), "service group uuid"
                ),
                "name": service_group.get("name"),
                "created_at": service_group.get("created_at"),
                "persistent": service_group.get("persistent"),
                "autoscale": service_group.get("autoscale"),
                "soft_limit": service_group.get("soft_limit"),
                "hard_limit": service_group.get("hard_limit"),
                "status": service_group.get("status"),
                "message": service_group.get("message"),
                "instance_ids": instance_ids,
                "certificate_ids": sorted(certificate_ids),
                "domains": domains,
                "primary_domain": domains[0] if domains else None,
            }
        )
    return result


@timeit
def load_service_groups(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    metro: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        UnikraftServiceGroupSchema(),
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
        METRO=metro,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(UnikraftServiceGroupSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    expected_count: int | None,
) -> None:
    total_fetched = 0
    for metro, base_url in METRO_BASE_URLS.items():
        service_groups = get(session, base_url)
        total_fetched += len(service_groups)
        transformed = transform(service_groups)
        load_service_groups(neo4j_session, transformed, account_id, metro, update_tag)
    check_count_matches("service_groups", expected_count, total_fetched)
    cleanup(neo4j_session, common_job_parameters)
