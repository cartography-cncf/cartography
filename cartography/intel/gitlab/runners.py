"""
GitLab Runners Intelligence Module

Ingests GitLab CI/CD runners at three scopes:
- instance-level (`/api/v4/runners/all`, requires admin scope)
- group-level (`/api/v4/groups/:id/runners`)
- project-level (`/api/v4/projects/:id/runners`)

Each runner listed via the scope-specific endpoint is then enriched via
`/api/v4/runners/:id` to obtain the detail fields (architecture, platform,
contacted_at, etc.) which are not returned by the list endpoints.

A token without the right scope is tolerated: a 403 is logged once at warning
level and the affected scope is skipped, so the rest of the sync continues.
"""

import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gitlab.util import get_paginated
from cartography.intel.gitlab.util import get_single
from cartography.models.gitlab.runners import GitLabGroupRunnerSchema
from cartography.models.gitlab.runners import GitLabInstanceRunnerSchema
from cartography.models.gitlab.runners import GitLabProjectRunnerSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _list_runners_tolerant(
    gitlab_url: str,
    token: str,
    endpoint: str,
    scope_description: str,
    extra_params: dict[str, Any] | None = None,
) -> list[dict[str, Any]] | None:
    """
    Fetch a paginated list of runners. Returns:
    - the list on success
    - ``None`` on 403 (permission-denied), so the caller can skip BOTH the
      load AND the cleanup for that scope. Returning [] would make the
      cleanup phase delete everything previously ingested for that scope,
      which is data loss disguised as a successful empty sync.
    Other errors propagate.
    """
    try:
        return get_paginated(gitlab_url, token, endpoint, extra_params=extra_params)
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 403:
            logger.warning(
                "Token lacks permission to read %s. Skipping.",
                scope_description,
            )
            return None
        raise


@timeit
def get_instance_runners(
    gitlab_url: str,
    token: str,
) -> list[dict[str, Any]] | None:
    """
    Fetch all instance-level runners. Requires admin scope on the token.

    Returns ``None`` if the scope is denied (403), so the caller can skip the
    cleanup pass for instance-level runners and avoid data loss.
    """
    return _list_runners_tolerant(
        gitlab_url,
        token,
        "/api/v4/runners/all",
        "instance-level runners (/api/v4/runners/all, requires admin)",
    )


@timeit
def get_group_runners(
    gitlab_url: str,
    token: str,
    group_id: int,
) -> list[dict[str, Any]] | None:
    """
    Fetch group-level runners for a specific group, filtered to
    ``runner_type=group_type``.

    Without the ``type`` filter, GitLab returns runners *visible to* the
    group — including inherited instance runners — which would be attached
    to the group as if they were group-scoped. The instance runners are
    already collected by the instance-scope sync, and the
    project/instance scopes are similarly filtered.

    Returns ``None`` on 403.
    """
    return _list_runners_tolerant(
        gitlab_url,
        token,
        f"/api/v4/groups/{group_id}/runners",
        f"runners for group {group_id}",
        extra_params={"type": "group_type"},
    )


@timeit
def get_project_runners(
    gitlab_url: str,
    token: str,
    project_id: int,
) -> list[dict[str, Any]] | None:
    """
    Fetch project-level runners for a specific project, filtered to
    ``runner_type=project_type`` (see :func:`get_group_runners` for the
    rationale). Returns ``None`` on 403.
    """
    return _list_runners_tolerant(
        gitlab_url,
        token,
        f"/api/v4/projects/{project_id}/runners",
        f"runners for project {project_id}",
        extra_params={"type": "project_type"},
    )


@timeit
def get_runner_details(
    gitlab_url: str,
    token: str,
    runner_id: int,
) -> dict[str, Any] | None:
    """
    Fetch detailed runner info for a single runner. Returns None if forbidden.

    The list endpoints return a subset of fields; this endpoint adds
    architecture, platform, contacted_at, ip_address, maximum_timeout, etc.
    """
    try:
        return get_single(gitlab_url, token, f"/api/v4/runners/{runner_id}")
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code in (403, 404):
            logger.warning(
                "Could not fetch details for runner %s (status %s). Skipping.",
                runner_id,
                e.response.status_code,
            )
            return None
        raise


def transform_runners(
    raw_runners: list[dict[str, Any]],
    gitlab_url: str,
) -> list[dict[str, Any]]:
    """
    Transform raw GitLab runner data to match our schema. Pure: no I/O.

    `tag_list` is preserved as a list — Neo4j supports arrays of primitives.
    """
    transformed = []
    for runner in raw_runners:
        if runner is None:
            continue
        transformed.append(
            {
                "id": runner.get("id"),
                "description": runner.get("description"),
                "runner_type": runner.get("runner_type"),
                "is_shared": runner.get("is_shared"),
                "active": runner.get("active"),
                "paused": runner.get("paused"),
                "online": runner.get("online"),
                "status": runner.get("status"),
                "ip_address": runner.get("ip_address"),
                "architecture": runner.get("architecture"),
                "platform": runner.get("platform"),
                "contacted_at": runner.get("contacted_at"),
                "tag_list": runner.get("tag_list") or [],
                "run_untagged": runner.get("run_untagged"),
                "locked": runner.get("locked"),
                "access_level": runner.get("access_level"),
                "maximum_timeout": runner.get("maximum_timeout"),
                "gitlab_url": gitlab_url,
            }
        )
    return transformed


def _enrich_with_details(
    gitlab_url: str,
    token: str,
    listed_runners: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    For each runner in the list, fetch its detail record. If the detail
    call fails (403/404), fall back to the listed record rather than
    dropping the runner: the list endpoint already confirmed the runner
    exists, so dropping it would let the next cleanup phase delete a
    real runner from the graph. The detail-only fields (architecture,
    platform, contacted_at, ip_address, maximum_timeout, ...) are absent
    from the listed record and will be filled in next sync if the detail
    endpoint becomes reachable again.
    """
    enriched: list[dict[str, Any]] = []
    for runner in listed_runners:
        runner_id = runner.get("id")
        if runner_id is None:
            continue
        details = get_runner_details(gitlab_url, token, runner_id)
        enriched.append(details if details is not None else runner)
    return enriched


@timeit
def load_instance_runners(
    neo4j_session: neo4j.Session,
    runners: list[dict[str, Any]],
    org_id: int,
    gitlab_url: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GitLabInstanceRunnerSchema(),
        runners,
        lastupdated=update_tag,
        org_id=org_id,
        gitlab_url=gitlab_url,
    )


@timeit
def load_group_runners(
    neo4j_session: neo4j.Session,
    runners: list[dict[str, Any]],
    group_id: int,
    gitlab_url: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GitLabGroupRunnerSchema(),
        runners,
        lastupdated=update_tag,
        group_id=group_id,
        gitlab_url=gitlab_url,
    )


@timeit
def load_project_runners(
    neo4j_session: neo4j.Session,
    runners: list[dict[str, Any]],
    project_id: int,
    gitlab_url: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GitLabProjectRunnerSchema(),
        runners,
        lastupdated=update_tag,
        project_id=project_id,
        gitlab_url=gitlab_url,
    )


@timeit
def cleanup_instance_runners(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    org_id: int,
    gitlab_url: str,
) -> None:
    cleanup_params = {
        **common_job_parameters,
        "org_id": org_id,
        "gitlab_url": gitlab_url,
    }
    GraphJob.from_node_schema(GitLabInstanceRunnerSchema(), cleanup_params).run(
        neo4j_session
    )


@timeit
def cleanup_group_runners(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    group_id: int,
    gitlab_url: str,
) -> None:
    cleanup_params = {
        **common_job_parameters,
        "group_id": group_id,
        "gitlab_url": gitlab_url,
    }
    GraphJob.from_node_schema(GitLabGroupRunnerSchema(), cleanup_params).run(
        neo4j_session
    )


@timeit
def cleanup_project_runners(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    project_id: int,
    gitlab_url: str,
) -> None:
    cleanup_params = {
        **common_job_parameters,
        "project_id": project_id,
        "gitlab_url": gitlab_url,
    }
    GraphJob.from_node_schema(GitLabProjectRunnerSchema(), cleanup_params).run(
        neo4j_session
    )


@timeit
def sync_gitlab_runners(
    neo4j_session: neo4j.Session,
    gitlab_url: str,
    token: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    groups: list[dict[str, Any]],
    projects: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Sync GitLab runners at all three scopes (instance, group, project).

    Returns a "skipped scopes" map so the cleanup phase can avoid running
    cleanup for any scope where we received a 403. Running cleanup on a
    scope we couldn't read would delete every previously-ingested runner
    for that scope (cleanup matches by stale `lastupdated`).
    """
    org_id: int = common_job_parameters["org_id"]
    skipped: dict[str, Any] = {
        "instance": False,
        "groups": set(),
        "projects": set(),
    }

    logger.info("Syncing GitLab instance-level runners")
    instance_listed = get_instance_runners(gitlab_url, token)
    if instance_listed is None:
        skipped["instance"] = True
    else:
        instance_enriched = _enrich_with_details(gitlab_url, token, instance_listed)
        instance_transformed = transform_runners(instance_enriched, gitlab_url)
        load_instance_runners(
            neo4j_session, instance_transformed, org_id, gitlab_url, update_tag
        )
        logger.info("Loaded %d instance-level runners", len(instance_transformed))

    logger.info("Syncing GitLab group-level runners for %d groups", len(groups))
    for group in groups:
        group_id: int = group["id"]
        group_listed = get_group_runners(gitlab_url, token, group_id)
        if group_listed is None:
            skipped["groups"].add(group_id)
            continue
        if not group_listed:
            continue
        group_enriched = _enrich_with_details(gitlab_url, token, group_listed)
        group_transformed = transform_runners(group_enriched, gitlab_url)
        load_group_runners(
            neo4j_session, group_transformed, group_id, gitlab_url, update_tag
        )

    logger.info("Syncing GitLab project-level runners for %d projects", len(projects))
    for project in projects:
        project_id: int = project["id"]
        project_listed = get_project_runners(gitlab_url, token, project_id)
        if project_listed is None:
            skipped["projects"].add(project_id)
            continue
        if not project_listed:
            continue
        project_enriched = _enrich_with_details(gitlab_url, token, project_listed)
        project_transformed = transform_runners(project_enriched, gitlab_url)
        load_project_runners(
            neo4j_session, project_transformed, project_id, gitlab_url, update_tag
        )

    logger.info("GitLab runners sync completed")
    return skipped
