import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from pdpyras import APISession

from cartography.client.core.tx import load
from cartography.client.core.tx import run_write_query
from cartography.graph.job import GraphJob
from cartography.models.pagerduty.team import PagerDutyTeamSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_teams(
    neo4j_session: neo4j.Session,
    update_tag: int,
    pd_session: APISession,
    common_job_parameters: dict[str, Any],
) -> None:
    teams = get_teams(pd_session)
    load_team_data(neo4j_session, teams, update_tag)
    relations = get_team_members(pd_session, teams)
    load_team_relations(neo4j_session, relations, update_tag)
    cleanup(neo4j_session, common_job_parameters)


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
    Transform and load team information
    """
    logger.info(f"Loading {len(data)} pagerduty teams.")
    load(neo4j_session, PagerDutyTeamSchema(), data, lastupdated=update_tag)


def load_team_relations(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:
    """
    Attach users to their teams.

    Note: This uses a separate Cypher query instead of the datamodel because
    the MEMBER_OF relationship has a 'role' property that varies per user-team pair.
    See https://github.com/cartography-cncf/cartography/issues/1589
    """
    ingestion_cypher_query = """
    UNWIND $Relations AS relation
        MATCH (t:PagerDutyTeam{id: relation.team}), (u:PagerDutyUser{id: relation.user})
        MERGE (u)-[r:MEMBER_OF]->(t)
        ON CREATE SET r.firstseen = timestamp()
        SET r.role = relation.role,
            r.lastupdated = $update_tag
    """
    run_write_query(
        neo4j_session,
        ingestion_cypher_query,
        Relations=data,
        update_tag=update_tag,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(PagerDutyTeamSchema(), common_job_parameters).run(
        neo4j_session,
    )
