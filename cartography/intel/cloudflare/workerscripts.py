import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from cloudflare import Cloudflare

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.cloudflare.workerscript import CloudflareWorkerScriptSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: Cloudflare,
    common_job_parameters: Dict[str, Any],
    account_id: str,
) -> None:
    scripts = get(client, account_id)
    load_workerscripts(
        neo4j_session,
        transform_scripts(scripts, account_id),
        account_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(client: Cloudflare, account_id: str) -> List[Dict[str, Any]]:
    return [
        script.to_dict()
        for script in client.workers.scripts.list(account_id=account_id)
    ]


def transform_scripts(
    scripts: List[Dict[str, Any]],
    account_id: str,
) -> List[Dict[str, Any]]:
    """
    Move the script name out of the API `id` field and qualify the graph ID with
    the account, since script names are only unique within an account.
    """
    transformed = []
    for script in scripts:
        name = script.get("id")
        if not name:
            # Without a name there is no identity to build on: every such record
            # would qualify to the same `<account_id>/` and merge into one node.
            logger.warning(
                "Skipping a Worker script of account %s: the API returned no script "
                "name to identify it by.",
                account_id,
            )
            continue
        row = script.copy()
        row["name"] = name
        row["id"] = f"{account_id}/{name}"
        transformed.append(row)
    return transformed


def load_workerscripts(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        CloudflareWorkerScriptSchema(),
        data,
        lastupdated=update_tag,
        account_id=account_id,
    )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        CloudflareWorkerScriptSchema(), common_job_parameters
    ).run(neo4j_session)
