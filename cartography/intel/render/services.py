import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.render.util import BASE_URL
from cartography.intel.render.util import list_paginated
from cartography.intel.render.util import require_non_empty
from cartography.models.render.service import RenderServiceLatestDeploySchema
from cartography.models.render.service import RenderServiceOntologyStateSchema
from cartography.models.render.service import RenderServiceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Sentinel distinguishing "this service's deploy fetch failed transiently this run"
# from a real `None` ("this service genuinely has no deploys yet"). Only a real `None`
# should null out latestDeploy* properties; a failed fetch must leave them untouched -
# see get_latest_deploys()/build_latest_deploy_rows().
DEPLOY_FETCH_FAILED = object()


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
    RenderServiceLatestDeployProperties' docstring.
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


def get_latest_deploys(
    session: requests.Session,
    services: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    :return: A mapping from service id to one of:
        - a deploy dict (the service's most recent deploy)
        - None (the service genuinely has no deploys yet, per Render)
        - DEPLOY_FETCH_FAILED (the per-service fetch failed transiently)

    A transient failure is deliberately distinguished from "no deploys yet" so
    build_latest_deploy_rows() can exclude that service entirely from the follow-up
    load() call, rather than nulling out real latest-deploy data from the last
    successful sync.
    """
    latest_deploys: dict[str, Any] = {}
    for service in services:
        service_id = service["id"]
        try:
            latest_deploys[service_id] = get_latest_deploy(session, service_id)
        except ValueError:
            # Malformed response shapes - including JSONDecodeError, which is a
            # ValueError subclass on every requests version this project supports
            # (unlike requests.exceptions.JSONDecodeError, which only exists from
            # requests 2.27 on and would raise AttributeError while being evaluated
            # as an except target on older installs) - indicate a real parsing bug,
            # not routine unavailability, and must stay loud.
            raise
        except requests.exceptions.RequestException as exc:
            logger.warning(
                "Render latest deploy fetch failed for service %s; leaving its "
                "existing latest deploy data untouched for this run rather than "
                "overwriting it with nulls: %s",
                service_id,
                exc,
            )
            latest_deploys[service_id] = DEPLOY_FETCH_FAILED
    return latest_deploys


def build_latest_deploy_rows(
    latest_deploys: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Builds one row per service whose deploy fetch succeeded this run - either with
    real deploy data or a confirmed "no deploys yet" result - for load_latest_deploys().
    Services excluded here (DEPLOY_FETCH_FAILED) are never passed to that load() call,
    so their existing latestDeploy* properties from the last successful sync are left
    untouched instead of being nulled out by a transient failure.
    """
    rows = []
    for service_id, deploy in latest_deploys.items():
        if deploy is DEPLOY_FETCH_FAILED:
            continue
        commit = (deploy or {}).get("commit") or {}
        image = (deploy or {}).get("image") or {}
        rows.append(
            {
                "id": service_id,
                "latestDeployId": (deploy or {}).get("id"),
                "latestDeployStatus": (deploy or {}).get("status"),
                "latestDeployTrigger": (deploy or {}).get("trigger"),
                "latestDeployCreatedAt": (deploy or {}).get("createdAt"),
                "latestDeployFinishedAt": (deploy or {}).get("finishedAt"),
                "latestDeployCommitMessage": commit.get("message"),
                "latestDeployImageRef": image.get("ref"),
            }
        )
    return rows


def build_ontology_state_rows(
    latest_deploys: dict[str, Any],
    services: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Builds one row per service for `effectiveDeployStatus` specifically - see
    RenderServiceOntologyStateProperties' docstring for why this has different
    inclusion logic from build_latest_deploy_rows(): a suspended service's effective
    status is always "suspended" regardless of deploy-fetch outcome, so it must still
    update on a transient deploy-fetch failure. A service is excluded here (preserving
    its prior effectiveDeployStatus) only when it is NOT suspended AND its deploy
    fetch failed this run - i.e. there is no reliable current information for it
    either way.
    """
    rows = []
    for service in services:
        service_id = service["id"]
        suspended = service.get("suspended") == "suspended"
        deploy = latest_deploys.get(service_id)
        if suspended:
            effective_status: Any = "suspended"
        elif deploy is DEPLOY_FETCH_FAILED:
            continue
        else:
            effective_status = (deploy or {}).get("status")
        rows.append({"id": service_id, "effectiveDeployStatus": effective_status})
    return rows


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
def load_latest_deploys(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Sets latestDeploy* properties on the RenderService nodes already loaded by
    load_services(), restricted to the services in `data` (built by
    build_latest_deploy_rows()). A service excluded from `data` is never mentioned in
    this call's Cypher SET clause, so its existing latestDeploy* properties are left
    exactly as they were - see RenderServiceLatestDeploySchema.
    """
    if not data:
        return
    load(
        neo4j_session,
        RenderServiceLatestDeploySchema(),
        data,
        lastupdated=update_tag,
    )


@timeit
def load_ontology_state(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Sets effectiveDeployStatus on the RenderService nodes already loaded by
    load_services(), restricted to the services in `data` (built by
    build_ontology_state_rows()). See RenderServiceOntologyStateSchema.
    """
    if not data:
        return
    load(
        neo4j_session,
        RenderServiceOntologyStateSchema(),
        data,
        lastupdated=update_tag,
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
    run_cleanup: bool = True,
) -> tuple[list[str], list[dict[str, Any]]]:
    """
    Sync the services belonging to a single Render workspace.

    :param run_cleanup: Pass False to defer this resource's cleanup to a later,
        explicit `cleanup()` call - used when other resources (custom domains, secret
        files, env vars, header rules, routes) are fetched per-service-id after this
        call returns, so that if one of those per-service fetches fails partway
        through, this resource's stale services haven't already been deleted this run
        (which would otherwise leave that failed resource's own still-valid child
        nodes pointing at a service that no longer exists).
    :return: A tuple of (service ids, raw un-transformed service objects). The ids let
        the caller fetch custom domains and secret files; the raw objects let the caller
        read each service's embedded `ipAllowList` without a second network call.
    """
    services = get(session, owner_id)
    transformed = transform(services)
    load_services(neo4j_session, transformed, owner_id, update_tag)
    latest_deploys = get_latest_deploys(session, transformed)
    load_latest_deploys(
        neo4j_session,
        build_latest_deploy_rows(latest_deploys),
        update_tag,
    )
    load_ontology_state(
        neo4j_session,
        build_ontology_state_rows(latest_deploys, transformed),
        update_tag,
    )
    if run_cleanup:
        cleanup(neo4j_session, common_job_parameters)
    return [service["id"] for service in transformed], services
