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
def sync_users(
    neo4j_session: neo4j.Session,
    update_tag: int,
    pd_session: APISession,
) -> None:
    users = get_users(pd_session)
    load_user_data(neo4j_session, users, update_tag)


@timeit
def get_users(pd_session: APISession) -> List[Dict[str, Any]]:
    all_users: List[Dict[str, Any]] = []
    for user in pd_session.iter_all("users"):
        all_users.append(user)
    return all_users


def load_user_data(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:
    """
    Transform and load user information
    """
    ingestion_cypher_query = """
    UNWIND $Users AS user
        MERGE (u:PagerDutyUser{id: user.id})
        ON CREATE SET u.html_url = user.html_url,
            u.firstseen = timestamp()
        SET u.type = user.type,
            u.summary = user.summary,
            u.name = user.name,
            u.email = user.email,
            u.time_zone = user.time_zone,
            u.color = user.color,
            u.role = user.role,
            u.avatar_url = user.avatar_url,
            u.description = user.description,
            u.invitation_sent = user.invitation_sent,
            u.job_title = user.job_title,
            u.lastupdated = $update_tag
    """
    logger.info(f"Loading {len(data)} pagerduty users.")

    run_write_query(
        neo4j_session,
        ingestion_cypher_query,
        Users=data,
        update_tag=update_tag,
    )
