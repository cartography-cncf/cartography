from typing import Any
from typing import Dict
from typing import List

import neo4j
from cloudflare import Cloudflare

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.cloudflare.dnsrecord import CloudflareDNSRecordSchema
from cartography.util import run_analysis_job
from cartography.util import timeit

# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)
# Records per API page, well under the documented maximum of 5000000.
_PER_PAGE = 1000


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: Cloudflare,
    common_job_parameters: Dict[str, Any],
    account_id: str,
    zones: List[Dict[str, Any]],
) -> None:
    # Each zone is loaded as soon as it is fetched, so an account with many
    # records never holds all of them in memory at once. DNS records are scoped
    # to the account (the tenant), so cleanup runs once after every zone has
    # been loaded: cleaning up per zone would delete the records of zones not
    # yet synced in this run and recreate them moments later.
    for zone in zones:
        load_dnsrecords(
            neo4j_session,
            get(client, zone["id"]),
            account_id,
            zone["id"],
            common_job_parameters["UPDATE_TAG"],
        )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(client: Cloudflare, zone_id: str) -> List[Dict[str, Any]]:
    # The SDK auto-paginates; the API defaults to 100 records per page and
    # allows up to 5000000, so a larger page size cuts the number of calls.
    # See https://developers.cloudflare.com/api/resources/dns/subresources/records/methods/list/
    return [
        dnsrecord.to_dict()
        for dnsrecord in client.dns.records.list(zone_id=zone_id, per_page=_PER_PAGE)
    ]


def load_dnsrecords(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    account_id: str,
    zone_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        CloudflareDNSRecordSchema(),
        data,
        lastupdated=update_tag,
        account_id=account_id,
        zone_id=zone_id,
    )


def migrate_account_resource_edges(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    """
    DEPRECATED: compatibility migration to backfill the RESOURCE edge from
    CloudflareAccount to CloudflareDNSRecord. Records ingested before the
    sub-resource moved from the zone to the account only carry the zone edge, so
    without this backfill they would sit outside the account-scoped cleanup and
    never be removed. Records whose zone was already deleted under the old
    per-zone scoping carry no owner at all and are swept instead. Must run
    before the zone cleanup, which would otherwise delete a stale zone and take
    the only path to its records with it. Remove in v1.0.0.
    """
    run_analysis_job(
        "cloudflare_dnsrecord_resource_edge_migration.json",
        neo4j_session,
        common_job_parameters,
    )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    GraphJob.from_node_schema(CloudflareDNSRecordSchema(), common_job_parameters).run(
        neo4j_session
    )
