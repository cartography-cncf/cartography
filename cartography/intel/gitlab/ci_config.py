"""
GitLab CI/CD config Intelligence Module

Ingests each project's `.gitlab-ci.yml` (or its merged equivalent), creates a
GitLabCIConfig node summarising the parsed pipeline, plus one GitLabCIInclude
node per resolved `include:` entry. Also creates a scoped MatchLink linking
the config to project-level CI/CD variables it references at runtime.

Fetch strategy:
1. Try `GET /api/v4/projects/:id/ci/lint?dry_run=true&ref=:default_branch` —
   this returns the YAML merged with all includes expanded (richer data).
2. Fall back to the raw `.gitlab-ci.yml` from the repository if lint fails.
3. If both fail (404 / 403), skip the project silently.

The parser is pure (`ci_config_parser.py`) — all I/O lives here.
"""

import logging
from typing import Any

import neo4j
import requests
from urllib.parse import quote

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.gitlab.ci_config_parser import ParsedCIConfig
from cartography.intel.gitlab.ci_config_parser import parse_ci_config
from cartography.intel.gitlab.util import make_request_with_retry
from cartography.models.gitlab.ci_config import GitLabCIConfigSchema
from cartography.models.gitlab.ci_config import GitLabCIConfigToCIVariableMatchLink
from cartography.models.gitlab.ci_include import GitLabCIIncludeSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

DEFAULT_FILE_PATH = ".gitlab-ci.yml"


def _try_lint_merged_yaml(
    gitlab_url: str,
    token: str,
    project_id: int,
    ref: str | None,
) -> tuple[str | None, bool | None]:
    """
    Call /ci/lint with dry_run=true to obtain the merged YAML. Returns
    (merged_yaml, is_valid) on success; (None, None) if the call fails with
    403 / 404. Other errors propagate.
    """
    endpoint = f"/api/v4/projects/{project_id}/ci/lint"
    params: dict[str, Any] = {"dry_run": "true"}
    if ref:
        params["ref"] = ref

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    try:
        response = make_request_with_retry(
            "GET", f"{gitlab_url}{endpoint}", headers=headers, params=params
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code in (403, 404):
            logger.warning(
                "ci/lint not available for project %s (status %s).",
                project_id,
                e.response.status_code,
            )
            return None, None
        raise

    body = response.json()
    merged = body.get("merged_yaml")
    if not merged:
        return None, None
    return merged, bool(body.get("valid", False))


def _try_raw_ci_yaml(
    gitlab_url: str,
    token: str,
    project_id: int,
    ref: str | None,
    file_path: str = DEFAULT_FILE_PATH,
) -> str | None:
    """
    Fetch the raw `.gitlab-ci.yml` from the repository as a fallback when
    /ci/lint is unavailable. Returns None on 403 / 404.
    """
    encoded = quote(file_path, safe="")
    endpoint = f"/api/v4/projects/{project_id}/repository/files/{encoded}/raw"
    if ref:
        endpoint = f"{endpoint}?ref={ref}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    try:
        response = make_request_with_retry(
            "GET", f"{gitlab_url}{endpoint}", headers=headers
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code in (403, 404):
            logger.warning(
                "Raw .gitlab-ci.yml not available for project %s (status %s).",
                project_id,
                e.response.status_code,
            )
            return None
        raise
    return response.text


@timeit
def fetch_ci_config_yaml(
    gitlab_url: str,
    token: str,
    project: dict[str, Any],
) -> tuple[str | None, bool | None, bool]:
    """
    Try /ci/lint first, then fall back to the raw file. Returns
    (yaml_content, is_valid, is_merged). is_merged is True when the YAML
    came from /ci/lint (with includes expanded), False when it's raw.
    """
    project_id = project["id"]
    ref = project.get("default_branch")

    merged, is_valid = _try_lint_merged_yaml(gitlab_url, token, project_id, ref)
    if merged:
        return merged, is_valid, True

    raw = _try_raw_ci_yaml(gitlab_url, token, project_id, ref)
    if raw:
        return raw, None, False

    return None, None, False


def transform_ci_config(
    parsed: ParsedCIConfig,
    project_id: int,
    gitlab_url: str,
    is_merged: bool,
    file_path: str,
    project_protected_variable_keys: set[str],
) -> dict[str, Any]:
    """
    Build the CIConfig node record. `referenced_protected_variables` is the
    intersection of the parsed variable keys and the project's protected
    variables — surfaced as a separate field for security queries.
    """
    referenced_protected = sorted(
        set(parsed.referenced_variable_keys) & project_protected_variable_keys
    )
    return {
        "id": f"{project_id}:{file_path}",
        "project_id": project_id,
        "file_path": file_path,
        "is_valid": parsed.is_valid,
        "is_merged": is_merged,
        "job_count": parsed.job_count,
        "stages": parsed.stages,
        "trigger_rules": parsed.trigger_rules,
        "referenced_variable_keys": parsed.referenced_variable_keys,
        "referenced_protected_variables": referenced_protected,
        "default_image": parsed.default_image,
        "has_includes": parsed.has_includes,
        "include_count": len(parsed.includes),
        "gitlab_url": gitlab_url,
    }


def transform_ci_includes(
    parsed: ParsedCIConfig,
    project_id: int,
    gitlab_url: str,
    file_path: str,
) -> list[dict[str, Any]]:
    """One record per ParsedCIInclude. ID composite to avoid cross-project collisions."""
    config_id = f"{project_id}:{file_path}"
    records: list[dict[str, Any]] = []
    for include in parsed.includes:
        ref_part = include.ref or "none"
        records.append(
            {
                "id": (
                    f"{project_id}:{include.include_type}:{include.location}:{ref_part}"
                ),
                "include_type": include.include_type,
                "location": include.location,
                "ref": include.ref,
                "is_pinned": include.is_pinned,
                "is_local": include.is_local,
                "raw_include": include.raw_include,
                "config_id": config_id,
                "gitlab_url": gitlab_url,
            }
        )
    return records


def compute_config_variable_links(
    parsed: ParsedCIConfig,
    project_variables: list[dict[str, Any]],
    project_id: int,
    file_path: str,
) -> list[dict[str, Any]]:
    """
    For each variable referenced by the config that exists in the project's
    CI/CD variables, emit a `{config_id, variable_id}` MatchLink record.

    A variable matches if the parsed key equals the variable `key`. The
    variable's `environment_scope` is intentionally ignored here — we link
    the config to *every* variant of that key, since a static analysis
    cannot tell which environment the pipeline will run in.
    """
    config_id = f"{project_id}:{file_path}"
    referenced_keys = set(parsed.referenced_variable_keys)
    if not referenced_keys:
        return []

    return [
        {"config_id": config_id, "variable_id": variable["id"]}
        for variable in project_variables
        if variable.get("key") in referenced_keys
    ]


@timeit
def load_ci_config(
    neo4j_session: neo4j.Session,
    record: dict[str, Any],
    project_id: int,
    gitlab_url: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GitLabCIConfigSchema(),
        [record],
        lastupdated=update_tag,
        project_id=project_id,
        gitlab_url=gitlab_url,
    )


@timeit
def load_ci_includes(
    neo4j_session: neo4j.Session,
    records: list[dict[str, Any]],
    project_id: int,
    gitlab_url: str,
    update_tag: int,
) -> None:
    if not records:
        return
    load(
        neo4j_session,
        GitLabCIIncludeSchema(),
        records,
        lastupdated=update_tag,
        project_id=project_id,
        gitlab_url=gitlab_url,
    )


@timeit
def load_config_variable_links(
    neo4j_session: neo4j.Session,
    links: list[dict[str, Any]],
    project_id: int,
    gitlab_url: str,
    update_tag: int,
) -> None:
    if not links:
        return
    load_matchlinks(
        neo4j_session,
        GitLabCIConfigToCIVariableMatchLink(),
        links,
        lastupdated=update_tag,
        _sub_resource_label="GitLabProject",
        _sub_resource_id=project_id,
        gitlab_url=gitlab_url,
    )


@timeit
def cleanup_ci_configs(
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
    GraphJob.from_node_schema(GitLabCIConfigSchema(), cleanup_params).run(
        neo4j_session
    )


@timeit
def cleanup_ci_includes(
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
    GraphJob.from_node_schema(GitLabCIIncludeSchema(), cleanup_params).run(
        neo4j_session
    )


@timeit
def sync_gitlab_ci_config(
    neo4j_session: neo4j.Session,
    gitlab_url: str,
    token: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    projects: list[dict[str, Any]],
    variables_by_project: dict[int, list[dict[str, Any]]],
) -> None:
    """
    For each project: fetch its CI YAML, parse it, load CIConfig + includes,
    and emit MatchLinks to referenced project-level variables.
    """
    logger.info("Syncing GitLab CI configs for %d projects", len(projects))

    for project in projects:
        project_id: int = project["id"]
        yaml_content, is_valid, is_merged = fetch_ci_config_yaml(
            gitlab_url, token, project
        )
        if yaml_content is None:
            continue

        parsed = parse_ci_config(yaml_content, is_valid=is_valid)

        project_variables = variables_by_project.get(project_id, [])
        protected_keys = {
            v["key"] for v in project_variables if v.get("protected") and v.get("key")
        }

        config_record = transform_ci_config(
            parsed,
            project_id,
            gitlab_url,
            is_merged=is_merged,
            file_path=DEFAULT_FILE_PATH,
            project_protected_variable_keys=protected_keys,
        )
        include_records = transform_ci_includes(
            parsed, project_id, gitlab_url, DEFAULT_FILE_PATH
        )
        variable_links = compute_config_variable_links(
            parsed, project_variables, project_id, DEFAULT_FILE_PATH
        )

        load_ci_config(
            neo4j_session, config_record, project_id, gitlab_url, update_tag
        )
        load_ci_includes(
            neo4j_session, include_records, project_id, gitlab_url, update_tag
        )
        load_config_variable_links(
            neo4j_session, variable_links, project_id, gitlab_url, update_tag
        )

    logger.info("GitLab CI configs sync completed")
