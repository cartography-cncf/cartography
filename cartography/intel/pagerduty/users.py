import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from pdpyras import APISession

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.pagerduty.user import PagerDutyUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_users(
    neo4j_session: neo4j.Session,
    update_tag: int,
    pd_session: APISession,
    common_job_parameters: dict[str, Any],
) -> None:
    users = get_users(pd_session)
    load_user_data(neo4j_session, users, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get_users(pd_session: APISession) -> List[Dict[str, Any]]:
    all_users: List[Dict[str, Any]] = []
    for user in pd_session.iter_all("users"):
        all_users.append(user)
    return all_users


@timeit
def load_user_data(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:
    """
    Transform and load user information
    """
    logger.info(f"Loading {len(data)} pagerduty users.")
    load(neo4j_session, PagerDutyUserSchema(), data, lastupdated=update_tag)


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(PagerDutyUserSchema(), common_job_parameters).run(
        neo4j_session,
    )
