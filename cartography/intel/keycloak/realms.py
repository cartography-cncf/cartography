import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.keycloak.realm import KeycloakRealmSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    common_job_parameters: dict[str, Any],
) -> list[dict]:
    realms = get(api_session, base_url)
    load_realms(neo4j_session, realms, common_job_parameters["UPDATE_TAG"])
    cleanup(neo4j_session, common_job_parameters)
    return realms


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    req = api_session.get(f"{base_url}/admin/realms", timeout=_TIMEOUT)
    req.raise_for_status()
    return req.json()


@timeit
def load_realms(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    logger.info("Loading %d Keycloak Realms into Neo4j.", len(data))
    load(
        neo4j_session,
        KeycloakRealmSchema(),
        data,
        LASTUPDATED=update_tag,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(KeycloakRealmSchema(), common_job_parameters).run(
        neo4j_session
    )
