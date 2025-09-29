import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import dateutil.parser
import neo4j
from pdpyras import APISession

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.pagerduty.schedule import PagerDutyScheduleSchema
from cartography.models.pagerduty.schedule_layer import PagerDutyScheduleLayerSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_schedules(
    neo4j_session: neo4j.Session,
    update_tag: int,
    pd_session: APISession,
    common_job_parameters: dict[str, Any],
) -> None:
    data = get_schedules(pd_session)
    schedules, layers = transform_schedules(data)
    load_schedule_data(neo4j_session, schedules, update_tag)
    load_layers_data(neo4j_session, layers, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get_schedules(pd_session: APISession) -> List[Dict[str, Any]]:
    all_schedules: List[Dict[str, Any]] = []
    params = {"include[]": ["schedule_layers"]}
    for schedule in pd_session.iter_all("schedules", params=params):
        all_schedules.append(schedule)
    return all_schedules


def transform_schedules(
    schedules: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Transform schedules to match the Neo4j schema.
    """
    transformed_schedules = []
    layers = []
    for schedule in schedules:
        schedule["users_id"] = [user["id"] for user in schedule.get("users", [])]
        for layer in schedule["schedule_layers"]:
            layer["_schedule_id"] = schedule["id"]
            layer["_layer_id"] = f"{schedule['id']}-{layer['name']}"
            for d_attr in ["start", "end", "rotation_virtual_start"]:
                if layer.get(d_attr) and isinstance(layer[d_attr], str):
                    d_val = dateutil.parser.parse(layer[d_attr])
                    layer[d_attr] = int(d_val.timestamp())
            layer["users_id"] = [user["user"]["id"] for user in layer.get("users", [])]
            layers.append(layer)
        transformed_schedules.append(schedule)
    return transformed_schedules, layers


@timeit
def load_schedule_data(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:
    """
    Transform and load schedule information
    """
    logger.info(f"Loading {len(data)} pagerduty schedules.")
    load(
        neo4j_session,
        PagerDutyScheduleSchema(),
        data,
        lastupdated=update_tag,
    )


@timeit
def load_layers_data(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:
    """
    Transform and load schedule layers information
    """
    logger.info(f"Loading {len(data)} pagerduty schedule layers.")
    load(
        neo4j_session,
        PagerDutyScheduleLayerSchema(),
        data,
        lastupdated=update_tag,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        PagerDutyScheduleLayerSchema(), common_job_parameters
    ).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(PagerDutyScheduleSchema(), common_job_parameters).run(
        neo4j_session,
    )
