from typing import Any
from typing import Dict
from typing import List

import neo4j
from cloudflare import Cloudflare

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.cloudflare.workerroute import CloudflareWorkerRouteSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: Cloudflare,
    common_job_parameters: Dict[str, Any],
    account_id: str,
    zones: List[Dict[str, Any]],
) -> None:
    # Routes are defined per zone but scoped to the account (the tenant), so
    # cleanup runs once after every zone has been loaded: cleaning up per zone
    # would delete the routes of zones not yet synced in this run.
    for zone in zones:
        load_workerroutes(
            neo4j_session,
            transform_routes(get(client, zone["id"]), account_id),
            account_id,
            zone["id"],
            common_job_parameters["UPDATE_TAG"],
        )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(client: Cloudflare, zone_id: str) -> List[Dict[str, Any]]:
    return [route.to_dict() for route in client.workers.routes.list(zone_id=zone_id)]


def transform_routes(
    routes: List[Dict[str, Any]],
    account_id: str,
) -> List[Dict[str, Any]]:
    """
    Resolve the target script name to the qualified CloudflareWorkerScript ID.
    Routes without a script are left unresolved so no edge is attempted.
    """
    transformed = []
    for route in routes:
        row = route.copy()
        script = route.get("script")
        row["script_id"] = f"{account_id}/{script}" if script else None
        transformed.append(row)
    return transformed


def load_workerroutes(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    account_id: str,
    zone_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        CloudflareWorkerRouteSchema(),
        data,
        lastupdated=update_tag,
        account_id=account_id,
        zone_id=zone_id,
    )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    GraphJob.from_node_schema(CloudflareWorkerRouteSchema(), common_job_parameters).run(
        neo4j_session
    )
