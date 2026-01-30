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
def sync_teams(
    neo4j_session: neo4j.Session,
    update_tag: int,
    pd_session: APISession,
) -> None:
    teams = get_teams(pd_session)
    load_team_data(neo4j_session, teams, update_tag)
    relations = get_team_members(pd_session, teams)
    load_team_relations(neo4j_session, relations, update_tag)


@timeit
def get_teams(pd_session: APISession) -> List[Dict[str, Any]]:
    all_teams: List[Dict[str, Any]] = []
    for teams in pd_session.iter_all("teams"):
        all_teams.append(teams)
    return all_teams


@timeit
def get_team_members(
    pd_session: APISession,
    teams: List[Dict[str, Any]],
) -> List[Dict[str, str]]:
    relations: List[Dict[str, str]] = []
    for team in teams:
        team_id = team["id"]
        for member in pd_session.iter_all(f"teams/{team_id}/members"):
            relations.append(
                {"team": team_id, "user": member["user"]["id"], "role": member["role"]},
            )
    return relations


def load_team_data(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:
    """
    Transform and load teamuser information
    """
    ingestion_cypher_query = """
    UNWIND $Teams AS team
        MERGE (t:PagerDutyTeam{id: team.id})
        ON CREATE SET t.html_url = team.html_url,
            t.firstseen = timestamp()
        SET t.type = team.type,
            t.summary = team.summary,
            t.name = team.name,
            t.description = team.description,
            t.default_role = team.default_role,
            t.lastupdated = $update_tag
    """
    logger.info(f"Loading {len(data)} pagerduty teams.")

    run_write_query(
        neo4j_session,
        ingestion_cypher_query,
        Teams=data,
        update_tag=update_tag,
    )


def load_team_relations(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:
    """
    Attach users to their teams
    """
    ingestion_cypher_query = """
    UNWIND $Relations AS relation
        MATCH (t:PagerDutyTeam{id: relation.team}), (u:PagerDutyUser{id: relation.user})
        MERGE (u)-[r:MEMBER_OF]->(t)
        ON CREATE SET r.firstseen = timestamp()
        SET r.role = relation.role
    """
    run_write_query(
        neo4j_session,
        ingestion_cypher_query,
        Relations=data,
        update_tag=update_tag,
    )
