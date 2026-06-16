import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.circleci.util import _TIMEOUT
from cartography.intel.circleci.util import parse_iso
from cartography.models.circleci.oidc_config import CircleCIOidcConfigSchema
from cartography.models.circleci.project_oidc_config import (
    CircleCIProjectOidcConfigSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _transform_claims(raw: dict[str, Any], scope: str) -> dict[str, Any]:
    return {
        "scope": scope,
        "audience": raw.get("audience"),
        "audience_updated_at": parse_iso(raw.get("audience_updated_at")),
        "ttl": raw.get("ttl"),
        "ttl_updated_at": parse_iso(raw.get("ttl_updated_at")),
        "org_id": raw.get("org_id"),
        "project_id": raw.get("project_id"),
    }


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
    org_id: str,
) -> None:
    raw = get(api_session, common_job_parameters["BASE_URL"], org_id)
    configs = transform(raw, org_id)
    load_oidc_configs(
        neo4j_session,
        configs,
        org_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    org_id: str,
) -> dict[str, Any] | None:
    req = api_session.get(
        f"{base_url}/org/{org_id}/oidc-custom-claims",
        timeout=_TIMEOUT,
    )
    # 404 simply means no custom claims are configured for this org.
    if req.status_code == 404:
        return None
    req.raise_for_status()
    return req.json()


def transform(
    raw: dict[str, Any] | None,
    org_id: str,
) -> list[dict[str, Any]]:
    if not raw:
        return []
    claims = _transform_claims(raw, "organization")
    claims["id"] = org_id
    claims["org_id"] = raw.get("org_id") or org_id
    return [claims]


@timeit
def load_oidc_configs(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        CircleCIOidcConfigSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(CircleCIOidcConfigSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync_project(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
    org_id: str,
    project_id: str,
) -> None:
    raw = get_project(
        api_session, common_job_parameters["BASE_URL"], org_id, project_id
    )
    configs = transform_project(raw, org_id, project_id)
    load_project_oidc_configs(
        neo4j_session,
        configs,
        project_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup_project(neo4j_session, common_job_parameters)


@timeit
def get_project(
    api_session: requests.Session,
    base_url: str,
    org_id: str,
    project_id: str,
) -> dict[str, Any] | None:
    req = api_session.get(
        f"{base_url}/org/{org_id}/project/{project_id}/oidc-custom-claims",
        timeout=_TIMEOUT,
    )
    if req.status_code == 404:
        return None
    req.raise_for_status()
    return req.json()


def transform_project(
    raw: dict[str, Any] | None,
    org_id: str,
    project_id: str,
) -> list[dict[str, Any]]:
    if not raw:
        return []
    claims = _transform_claims(raw, "project")
    claims["id"] = project_id
    claims["org_id"] = raw.get("org_id") or org_id
    claims["project_id"] = raw.get("project_id") or project_id
    return [claims]


@timeit
def load_project_oidc_configs(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    project_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        CircleCIProjectOidcConfigSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_project(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        CircleCIProjectOidcConfigSchema(), common_job_parameters
    ).run(neo4j_session)
