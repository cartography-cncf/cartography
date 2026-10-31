import logging
from typing import Any

import neo4j
import scaleway
from scaleway.cockpit.v1 import CockpitV1GlobalAPI
from scaleway.cockpit.v1 import CockpitV1RegionalAPI
from scaleway.cockpit.v1 import DataSource
from scaleway.cockpit.v1 import Plan
from scaleway.cockpit.v1 import Token
from scaleway_core.api import ScalewayException

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import list_all_regions
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.cockpit.cockpit import ScalewayCockpitDataSourceSchema
from cartography.models.scaleway.cockpit.cockpit import ScalewayCockpitSchema
from cartography.models.scaleway.cockpit.cockpit import ScalewayCockpitTokenSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_PROJECT_UNREADABLE_STATUS_CODES = {403, 404}


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: scaleway.Client,
    common_job_parameters: dict[str, Any],
    org_id: str,
    projects_id: list[str],
    update_tag: int,
) -> None:
    plan_by_project, data_sources, tokens, completed_project_ids = get(
        client, projects_id
    )
    cockpits_by_project = transform_cockpits(plan_by_project)
    data_sources_by_project = transform_data_sources(data_sources)
    tokens_by_project = transform_tokens(tokens)
    load_cockpits(
        neo4j_session,
        cockpits_by_project,
        data_sources_by_project,
        tokens_by_project,
        update_tag,
    )
    cleanup(neo4j_session, completed_project_ids, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    projects_id: list[str],
) -> tuple[dict[str, Plan], list[DataSource], list[Token], list[str]]:
    # Cockpit has no organization-wide list endpoint: plan, data sources, and tokens
    # are all fetched per project.
    global_api = CockpitV1GlobalAPI(client)
    regional_api = CockpitV1RegionalAPI(client)
    plan_by_project: dict[str, Plan] = {}
    data_sources: list[DataSource] = []
    tokens: list[Token] = []
    completed_project_ids: list[str] = []
    for project_id in projects_id:
        try:
            project_plan = global_api.get_current_plan(project_id=project_id)
            project_data_sources = list_all_regions(
                regional_api.list_data_sources_all,
                project_id=project_id,
            )
            project_tokens = list_all_regions(
                regional_api.list_tokens_all,
                project_id=project_id,
            )
        except ScalewayException as exc:
            if not _is_project_unreadable(exc):
                raise
            logger.warning(
                "Failed to enumerate Scaleway Cockpit for project %s; skipping "
                "this project and preserving existing Cockpit graph data. Error: %s",
                project_id,
                exc,
            )
            continue
        plan_by_project[project_id] = project_plan
        data_sources.extend(project_data_sources)
        tokens.extend(project_tokens)
        completed_project_ids.append(project_id)
    return plan_by_project, data_sources, tokens, completed_project_ids


def _is_project_unreadable(exc: ScalewayException) -> bool:
    return exc.status_code in _PROJECT_UNREADABLE_STATUS_CODES


def transform_cockpits(
    plan_by_project: dict[str, Plan],
) -> dict[str, list[dict[str, Any]]]:
    return {
        project_id: [{"id": project_id, "plan_name": plan.name}]
        for project_id, plan in plan_by_project.items()
    }


def transform_data_sources(
    data_sources: list[DataSource],
) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for data_source in data_sources:
        result.setdefault(data_source.project_id, []).append(
            scaleway_obj_to_dict(data_source)
        )
    return result


def transform_tokens(tokens: list[Token]) -> dict[str, list[dict[str, Any]]]:
    # secret_key is the token's actual bearer credential - Scaleway's list API
    # returns it inline alongside the token's metadata, but it must never be
    # ingested. It's dropped here, immediately after SDK serialization and before
    # the row can reach load().
    result: dict[str, list[dict[str, Any]]] = {}
    for token in tokens:
        formatted = scaleway_obj_to_dict(token)
        formatted.pop("secret_key", None)
        result.setdefault(token.project_id, []).append(formatted)
    return result


@timeit
def load_cockpits(
    neo4j_session: neo4j.Session,
    cockpits_by_project: dict[str, list[dict[str, Any]]],
    data_sources_by_project: dict[str, list[dict[str, Any]]],
    tokens_by_project: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, cockpits in cockpits_by_project.items():
        load(
            neo4j_session,
            ScalewayCockpitSchema(),
            cockpits,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )
    for project_id, data_sources in data_sources_by_project.items():
        load(
            neo4j_session,
            ScalewayCockpitDataSourceSchema(),
            data_sources,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )
    for project_id, tokens in tokens_by_project.items():
        load(
            neo4j_session,
            ScalewayCockpitTokenSchema(),
            tokens,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    projects_id: list[str],
    common_job_parameters: dict[str, Any],
) -> None:
    for project_id in projects_id:
        scoped_job_parameters = common_job_parameters.copy()
        scoped_job_parameters["PROJECT_ID"] = project_id
        # Children before the Cockpit node itself.
        GraphJob.from_node_schema(
            ScalewayCockpitDataSourceSchema(), scoped_job_parameters
        ).run(neo4j_session)
        GraphJob.from_node_schema(
            ScalewayCockpitTokenSchema(), scoped_job_parameters
        ).run(neo4j_session)
        GraphJob.from_node_schema(ScalewayCockpitSchema(), scoped_job_parameters).run(
            neo4j_session
        )
