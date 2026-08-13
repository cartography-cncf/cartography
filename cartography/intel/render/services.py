import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.render.util import BASE_URL
from cartography.intel.render.util import list_paginated
from cartography.intel.render.util import require_non_empty
from cartography.models.render.service import RenderServiceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(session: requests.Session, owner_id: str) -> list[dict[str, Any]]:
    return list_paginated(
        session,
        f"{BASE_URL}/services",
        "service",
        params={"ownerId": [owner_id]},
    )


@timeit
def get_latest_deploy(
    session: requests.Session, service_id: str
) -> dict[str, Any] | None:
    """
    :return: The service's single most recent deploy, or None if it has never deployed.

    Deliberately does not use list_paginated(): only the newest deploy is wanted here
    (Render returns deploys newest-first), not a full page of deploy history, which
    would be unbounded time-series data poorly suited to a current-state graph - see
    RenderServiceNodeProperties.latest_deploy_id's comment.
    """
    response = session.get(
        f"{BASE_URL}/services/{service_id}/deploys",
        params={"limit": 1},
        timeout=(60, 60),
    )
    response.raise_for_status()
    body = response.json()
    if not isinstance(body, list):
        raise ValueError(
            f"Render API returned a non-list deploys response for service "
            f"{service_id}: {type(body)}."
        )
    if not body:
        return None
    entry = body[0]
    if not isinstance(entry, dict) or "deploy" not in entry:
        shape = (
            sorted(entry.keys()) if isinstance(entry, dict) else type(entry).__name__
        )
        raise ValueError(
            f"Render API returned a malformed deploy entry for service "
            f"{service_id}: expected a 'deploy' key; got {shape!r}."
        )
    deploy = entry["deploy"]
    if not isinstance(deploy, dict):
        raise ValueError(
            f"Render API returned a malformed deploy entry for service "
            f"{service_id}: expected 'deploy' to be an object, got {type(deploy).__name__}."
        )
    return deploy


def transform(services: list[dict[str, Any]]) -> list[dict[str, Any]]:
    transformed = []
    for service in services:
        details = service.get("serviceDetails") or {}
        registry_credential = service.get("registryCredential") or {}
        transformed.append(
            {
                "id": require_non_empty(service.get("id"), "service id"),
                "name": service.get("name"),
                "ownerId": service.get("ownerId"),
                "environmentId": service.get("environmentId"),
                "type": service.get("type"),
                "slug": service.get("slug"),
                "repo": service.get("repo"),
                "branch": service.get("branch"),
                "rootDir": service.get("rootDir"),
                "dashboardUrl": service.get("dashboardUrl"),
                "suspended": service.get("suspended"),
                "autoDeploy": service.get("autoDeploy"),
                "runtime": details.get("runtime"),
                "plan": details.get("plan"),
                "region": details.get("region"),
                "url": details.get("url"),
                "numInstances": details.get("numInstances"),
                "registryCredentialId": registry_credential.get("id"),
                "createdAt": service.get("createdAt"),
                "updatedAt": service.get("updatedAt"),
            }
        )
    return transformed


def apply_latest_deploys(
    services: list[dict[str, Any]],
    latest_deploys: dict[str, dict[str, Any] | None],
) -> None:
    """Mutates `services` rows in place, adding latestDeploy* fields from `latest_deploys`."""
    for service in services:
        deploy = latest_deploys.get(service["id"])
        if deploy is None:
            continue
        commit = deploy.get("commit") or {}
        image = deploy.get("image") or {}
        service["latestDeployId"] = deploy.get("id")
        service["latestDeployStatus"] = deploy.get("status")
        service["latestDeployTrigger"] = deploy.get("trigger")
        service["latestDeployCreatedAt"] = deploy.get("createdAt")
        service["latestDeployFinishedAt"] = deploy.get("finishedAt")
        service["latestDeployCommitMessage"] = commit.get("message")
        service["latestDeployImageRef"] = image.get("ref")


@timeit
def load_services(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    owner_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        RenderServiceSchema(),
        data,
        lastupdated=update_tag,
        OWNER_ID=owner_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(RenderServiceSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    owner_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> tuple[list[str], list[dict[str, Any]]]:
    """
    Sync the services belonging to a single Render workspace.

    :return: A tuple of (service ids, raw un-transformed service objects). The ids let
        the caller fetch custom domains and secret files; the raw objects let the caller
        read each service's embedded `ipAllowList` without a second network call.
    """
    services = get(session, owner_id)
    transformed = transform(services)
    latest_deploys = {
        service["id"]: get_latest_deploy(session, service["id"])
        for service in transformed
    }
    apply_latest_deploys(transformed, latest_deploys)
    load_services(neo4j_session, transformed, owner_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    return [service["id"] for service in transformed], services
