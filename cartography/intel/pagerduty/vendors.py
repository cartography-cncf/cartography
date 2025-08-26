import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from pdpyras import APISession

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.pagerduty.vendor import PagerDutyVendorSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_vendors(
    neo4j_session: neo4j.Session,
    update_tag: int,
    pd_session: APISession,
    common_job_parameters: dict[str, Any],
) -> None:
    vendors = get_vendors(pd_session)
    load_vendor_data(neo4j_session, vendors, update_tag)
    cleanup(neo4j_session, common_job_parameters)


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
    logger.info(f"Loading {len(data)} pagerduty vendors.")
    load(neo4j_session, PagerDutyVendorSchema(), data, lastupdated=update_tag)


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(PagerDutyVendorSchema(), common_job_parameters).run(
        neo4j_session,
    )
