import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.civo.util import get_json_array
from cartography.intel.civo.util import require_non_empty
from cartography.models.civo.sshkey import CivoSSHKeySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    ssh_keys = get(api_session, common_job_parameters["BASE_URL"])
    transformed = transform_ssh_keys(ssh_keys)
    load_ssh_keys(
        neo4j_session,
        transformed,
        common_job_parameters["ACCOUNT_ID"],
        common_job_parameters["UPDATE_TAG"],
    )


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    """
    Live-tested against a real Civo account: GET /v2/sshkeys currently
    returns a bare JSON array, not the paginated {"page","per_page","pages",
    "items"} wrapper this module originally assumed (based on civogo, which
    itself paginates client-side over this endpoint) - use get_json_array,
    matching firewalls/networks/subnets/volumes/DNS/load balancers/regions.
    """
    return get_json_array(api_session, f"{base_url}/v2/sshkeys")


def transform_ssh_keys(ssh_keys: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for ssh_key in ssh_keys:
        ssh_key_id = require_non_empty(ssh_key.get("id"), "ssh key id")
        result.append(
            {
                "id": ssh_key_id,
                "name": ssh_key.get("name"),
                "fingerprint": ssh_key.get("fingerprint"),
            }
        )
    return result


@timeit
def load_ssh_keys(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        CivoSSHKeySchema(),
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(CivoSSHKeySchema(), common_job_parameters).run(
        neo4j_session,
    )
