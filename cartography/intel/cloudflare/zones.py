import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from cloudflare import Cloudflare

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.cloudflare.zone import CloudflareZoneSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: Cloudflare,
    common_job_parameters: Dict[str, Any],
    account_id: str,
) -> List[Dict]:
    zones = get(client, account_id)
    load_zones(
        neo4j_session,
        zones,
        account_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)
    return zones


@timeit
def get(
    client: Cloudflare,
    account_id: str,
) -> List[Dict[str, Any]]:
    return [zone.to_dict() for zone in client.zones.list(account=account_id)]


def load_zones(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d Cloudflare zones into Neo4j.", len(data))
    load(
        neo4j_session,
        CloudflareZoneSchema(),
        data,
        lastupdated=update_tag,
        account_id=account_id,
    )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    GraphJob.from_node_schema(CloudflareZoneSchema(), common_job_parameters).run(
        neo4j_session
    )
