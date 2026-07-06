import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.circleci.util import paginated_get
from cartography.intel.circleci.util import parse_iso
from cartography.models.circleci.context import CircleCIContextSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
    org_id: str,
) -> list[dict[str, Any]]:
    base_url = common_job_parameters["BASE_URL"]
    raw = get(api_session, base_url, org_id)
    contexts = transform(raw)
    # Enrich each context with the projects it is restricted to so the
    # one-to-many RESTRICTED_TO relationship can attach (best-effort). A
    # restrictions failure must not block ingesting the contexts themselves.
    restrictions_complete = True
    for context in contexts:
        try:
            context["restricted_project_ids"] = get_restricted_project_ids(
                api_session, base_url, context["id"]
            )
        except requests.exceptions.RequestException as exc:
            # Leave restricted_project_ids empty (no RESTRICTED_TO refreshed for
            # this context) and remember the data is incomplete. We must NOT let
            # a failed fetch look like "no restrictions" - see cleanup below.
            logger.warning(
                "Could not fetch restrictions for CircleCI context %s: %s",
                context["id"],
                exc,
            )
            restrictions_complete = False
    load_contexts(
        neo4j_session,
        contexts,
        org_id,
        common_job_parameters["UPDATE_TAG"],
    )
    # Cleanup deletes stale CircleCIContext nodes AND stale RESTRICTED_TO edges.
    # Skip it when restrictions were incomplete: an empty restricted_project_ids
    # from a failed fetch would otherwise wipe still-valid RESTRICTED_TO edges.
    if restrictions_complete:
        cleanup(neo4j_session, common_job_parameters)
    else:
        logger.warning(
            "Skipping CircleCI context cleanup for org %s: restrictions were "
            "incomplete this run, so stale nodes/edges are preserved rather than "
            "risk wiping valid RESTRICTED_TO relationships.",
            org_id,
        )
    return contexts


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    org_id: str,
) -> list[dict[str, Any]]:
    return paginated_get(
        api_session,
        f"{base_url}/context",
        params={"owner-id": org_id, "owner-type": "organization"},
    )


@timeit
def get_restricted_project_ids(
    api_session: requests.Session,
    base_url: str,
    context_id: str,
) -> list[str]:
    restrictions = paginated_get(
        api_session,
        f"{base_url}/context/{context_id}/restrictions",
    )
    return [r["project_id"] for r in restrictions if r.get("project_id")]


def transform(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": ctx["id"],
            "name": ctx.get("name"),
            "created_at": parse_iso(ctx.get("created_at")),
            "restricted_project_ids": [],
        }
        for ctx in raw
    ]


@timeit
def load_contexts(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        CircleCIContextSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(CircleCIContextSchema(), common_job_parameters).run(
        neo4j_session,
    )
