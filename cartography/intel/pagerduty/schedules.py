import logging
from typing import Any
from typing import Dict
from typing import List

import dateutil.parser
import neo4j
from pdpyras import APISession

from cartography.client.core.tx import run_write_query
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_schedules(
    neo4j_session: neo4j.Session,
    update_tag: int,
    pd_session: APISession,
) -> None:
    schedules = get_schedules(pd_session)
    load_schedule_data(neo4j_session, schedules, update_tag)


@timeit
def get_schedules(pd_session: APISession) -> List[Dict[str, Any]]:
    all_schedules: List[Dict[str, Any]] = []
    params = {"include[]": ["schedule_layers"]}
    for schedule in pd_session.iter_all("schedules", params=params):
        all_schedules.append(schedule)
    return all_schedules


def load_schedule_data(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:
    """
    Transform and load schedule information
    """
    ingestion_cypher_query = """
    UNWIND $Schedules AS schedule
        MERGE (u:PagerDutySchedule{id: schedule.id})
        ON CREATE SET u.html_url = schedule.html_url,
            u.firstseen = timestamp()
        SET u.type = schedule.type,
            u.summary = schedule.summary,
            u.name = schedule.name,
            u.time_zone = schedule.time_zone,
            u.description = schedule.description,
            u.lastupdated = $update_tag
    """
    logger.info(f"Loading {len(data)} pagerduty schedules.")
    users: List[Dict[str, Any]] = []
    layers: List[Dict[str, Any]] = []
    for schedule in data:
        if schedule.get("users"):
            for user in schedule["users"]:
                users.append({"schedule": schedule["id"], "user": user["id"]})
        if schedule.get("schedule_layers"):
            for layer in schedule["schedule_layers"]:
                layer["_schedule_id"] = schedule["id"]
                layers.append(layer)

    run_write_query(
        neo4j_session,
        ingestion_cypher_query,
        Schedules=data,
        update_tag=update_tag,
    )

    _attach_users(neo4j_session, users, update_tag)
    _attach_layers(neo4j_session, layers, update_tag)


def _attach_users(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:
    """
    Add relationship between schedule and users.
    """
    ingestion_cypher_query = """
    UNWIND $Relations AS relation
        MATCH (s:PagerDutySchedule{id: relation.schedule}), (u:PagerDutyUser{id: relation.user})
        MERGE (u)-[r:MEMBER_OF]->(s)
        ON CREATE SET r.firstseen = timestamp()
    """
    run_write_query(
        neo4j_session,
        ingestion_cypher_query,
        Relations=data,
        update_tag=update_tag,
    )


def _attach_layers(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:
    """
    Create layers for a schedule and attach them together
    """
    ingestion_cypher_query = """
    UNWIND $Layers AS layer
        MERGE (l:PagerDutyScheduleLayer{id: layer._layer_id})
        ON CREATE SET l.name = layer.name,
            l.schedule_id = layer._schedule_id
        SET l.start = layer.start,
            l.end = layer.end,
            l.rotation_virtual_start = layer.rotation_virtual_start,
            l.rotation_turn_length_seconds = layer.rotation_turn_length_seconds,
            l.lastupdated = $update_tag
        with l, layer._schedule_id as schedule_id
        MATCH (s:PagerDutySchedule{id: schedule_id})
        MERGE (s)-[r:HAS_LAYER]->(l)
        ON CREATE SET r.firstseen = timestamp()
    """
    users: List[Dict[str, Any]] = []
    for layer in data:
        layer["_layer_id"] = f"{layer['_schedule_id']}-{layer['name']}"
        for d_attr in ["start", "end", "rotation_virtual_start"]:
            if layer.get(d_attr):
                d_val = dateutil.parser.parse(layer[d_attr])
                layer[d_attr] = int(d_val.timestamp())
        if layer.get("users"):
            for user in layer["users"]:
                users.append(
                    {"layer_id": layer["_layer_id"], "user": user["user"]["id"]},
                )
    run_write_query(
        neo4j_session,
        ingestion_cypher_query,
        Layers=data,
        update_tag=update_tag,
    )

    _attach_layer_users(neo4j_session, users, update_tag)


def _attach_layer_users(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:
    """
    Add relationship between schedule layers and users.
    """
    ingestion_cypher_query = """
    UNWIND $Relations AS relation
        MATCH (l:PagerDutyScheduleLayer{id: relation.layer_id}), (u:PagerDutyUser{id: relation.user})
        MERGE (u)-[r:MEMBER_OF]->(l)
        ON CREATE SET r.firstseen = timestamp()
    """
    run_write_query(
        neo4j_session,
        ingestion_cypher_query,
        Relations=data,
        update_tag=update_tag,
    )
