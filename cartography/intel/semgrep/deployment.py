import logging
from typing import Any
from typing import Dict

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.models.semgrep.deployment import SemgrepDeploymentSchema
from cartography.stats import get_stats_client
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)
_TIMEOUT = (60, 60)


@timeit
def get_deployment(semgrep_app_token: str) -> Dict[str, Any]:
    """
    Gets the deployment associated with the passed Semgrep App token.
    param: semgrep_app_token: The Semgrep App token to use for authentication.
    """
    deployment = {}
    deployment_url = "https://semgrep.dev/api/v1/deployments"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {semgrep_app_token}",
    }
    response = requests.get(deployment_url, headers=headers, timeout=_TIMEOUT)
    response.raise_for_status()

    data = response.json()
    deployment["id"] = data["deployments"][0]["id"]
    deployment["name"] = data["deployments"][0]["name"]
    deployment["slug"] = data["deployments"][0]["slug"]

    return deployment


@timeit
def load_semgrep_deployment(
    neo4j_session: neo4j.Session, deployment: Dict[str, Any], update_tag: int,
) -> None:
    logger.info(f"Loading Semgrep deployment info {deployment} into the graph...")
    load(
        neo4j_session,
        SemgrepDeploymentSchema(),
        [deployment],
        lastupdated=update_tag,
    )
