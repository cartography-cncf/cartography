import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from pdpyras import APISession

from cartography.client.core.tx import run_write_query
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_vendors(
    neo4j_session: neo4j.Session,
    update_tag: int,
    pd_session: APISession,
) -> None:
    vendors = get_vendors(pd_session)
    load_vendor_data(neo4j_session, vendors, update_tag)


@timeit
def get_vendors(pd_session: APISession) -> List[Dict[str, Any]]:
    all_vendors: List[Dict[str, Any]] = []
    for vendor in pd_session.iter_all("vendors"):
        all_vendors.append(vendor)
    return all_vendors


def load_vendor_data(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:
    """
    Transform and load vendor information
    """
    ingestion_cypher_query = """
    UNWIND $Vendors AS vendor
        MERGE (v:PagerDutyVendor{id: vendor.id})
        ON CREATE SET v.firstseen = timestamp()
        SET v.type = vendor.type,
            v.summary = vendor.summary,
            v.name = vendor.name,
            v.website_url = vendor.website_url,
            v.logo_url = vendor.logo_url,
            v.thumbnail_url = vendor.thumbnail_url,
            v.description = vendor.description,
            v.integration_guide_url = vendor.integration_guide_url,
            v.lastupdated = $update_tag
    """
    logger.info(f"Loading {len(data)} pagerduty vendors.")

    run_write_query(
        neo4j_session,
        ingestion_cypher_query,
        Vendors=data,
        update_tag=update_tag,
    )
