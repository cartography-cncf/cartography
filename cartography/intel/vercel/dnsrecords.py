import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.vercel.util import paginated_get
from cartography.models.vercel.dnsrecord import VercelDNSRecordSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
    domain_name: str,
) -> None:
    dns_records = get(
        api_session,
        common_job_parameters["BASE_URL"],
        common_job_parameters["TEAM_ID"],
        domain_name,
    )
    load_dns_records(
        neo4j_session,
        dns_records,
        common_job_parameters["TEAM_ID"],
        domain_name,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    team_id: str,
    domain_name: str,
) -> list[dict[str, Any]]:
    return paginated_get(
        api_session,
        f"{base_url}/v4/domains/{domain_name}/records",
        "records",
        team_id,
    )


@timeit
def load_dns_records(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    team_id: str,
    domain_name: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        VercelDNSRecordSchema(),
        data,
        lastupdated=update_tag,
        TEAM_ID=team_id,
        domain_name=domain_name,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(VercelDNSRecordSchema(), common_job_parameters).run(
        neo4j_session,
    )
