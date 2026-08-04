import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.netlify.util import get_list
from cartography.intel.netlify.util import paginated_get
from cartography.models.netlify.dnsrecord import NetlifyDNSRecordSchema
from cartography.models.netlify.dnszone import NetlifyDNSZoneSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_netlify_dns(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    account_id: str,
    account_slug: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    zones = get_netlify_dns_zones(api_session, base_url, account_slug)
    records = []
    for zone in zones:
        records.extend(get_netlify_dns_records(api_session, base_url, zone["id"]))
    transformed_records = transform_netlify_dns_records(records)

    load_netlify_dns_zones(neo4j_session, zones, account_id, update_tag)
    load_netlify_dns_records(
        neo4j_session,
        transformed_records,
        account_id,
        update_tag,
    )
    cleanup_netlify_dns(neo4j_session, common_job_parameters)


@timeit
def get_netlify_dns_zones(
    api_session: requests.Session,
    base_url: str,
    account_slug: str,
) -> list[dict[str, Any]]:
    """
    Fetch the DNS zones of one team.

    The endpoint returns every zone the token can see unless it is filtered, so the team slug is
    passed explicitly: without it a token with access to several teams would pull another team's
    zones into this team's cleanup scope and then delete them.
    """
    return paginated_get(
        api_session,
        f"{base_url}/dns_zones",
        params={"account_slug": account_slug},
    )


@timeit
def get_netlify_dns_records(
    api_session: requests.Session,
    base_url: str,
    zone_id: str,
) -> list[dict[str, Any]]:
    return get_list(api_session, f"{base_url}/dns_zones/{zone_id}/dns_records")


def transform_netlify_dns_records(
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Copy `hostname` to `name`, which is what the DNSRecord ontology mapping requires.
    """
    return [{**record, "name": record.get("hostname")} for record in records]


@timeit
def load_netlify_dns_zones(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        NetlifyDNSZoneSchema(),
        data,
        lastupdated=update_tag,
        NETLIFY_ACCOUNT_ID=account_id,
    )


@timeit
def load_netlify_dns_records(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        NetlifyDNSRecordSchema(),
        data,
        lastupdated=update_tag,
        NETLIFY_ACCOUNT_ID=account_id,
    )


@timeit
def cleanup_netlify_dns(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    # Records before zones: a record hangs off its zone, so removing the zone first would strip
    # the edge that identifies the orphan.
    GraphJob.from_node_schema(NetlifyDNSRecordSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(NetlifyDNSZoneSchema(), common_job_parameters).run(
        neo4j_session,
    )
