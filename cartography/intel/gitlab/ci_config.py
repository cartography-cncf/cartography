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
from urllib.parse import quote

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gitlab.ci_config_parser import parse_ci_config
from cartography.intel.gitlab.ci_config_parser import parse_lint_includes
from cartography.intel.gitlab.ci_config_parser import ParsedCIConfig
from cartography.intel.gitlab.util import make_request_with_retry
from cartography.models.gitlab.ci_config import GitLabCIConfigSchema
from cartography.models.gitlab.ci_include import GitLabCIIncludeSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

DEFAULT_FILE_PATH = ".gitlab-ci.yml"


def _try_lint_merged_yaml(
    gitlab_url: str,
    token: str,
    project_id: int,
    ref: str | None,
) -> tuple[str | None, bool | None, bool, list[dict[str, Any]] | None]:
    """
    Call /ci/lint with dry_run=true to obtain the merged YAML. Returns
    ``(merged_yaml, is_valid, denied, lint_includes)``:

    - ``(yaml, True/False, False, includes)`` on a successful response
    - ``(None, None, False, None)`` on 404 (project has no pipeline)
    - ``(None, None, True, None)`` on 403 (token can't lint) — caller
      should fall back to the raw file
    Other errors propagate.

    The ``lint_includes`` field is GitLab's structured representation of
    the include directives that were resolved when building merged_yaml.
    The merged_yaml itself does NOT contain the original ``include:``
    block (the included content is inlined as jobs), so we read this
    field separately to retain include nodes on the lint path.
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
        if e.response is not None and e.response.status_code == 403:
            logger.warning(
                "ci/lint denied for project %s (token lacks Maintainer access). "
                "Falling back to raw .gitlab-ci.yml.",
                project_id,
            )
            return None, None, True, None
        if e.response is not None and e.response.status_code == 404:
            logger.warning(
                "ci/lint returned 404 for project %s (no pipeline / not enabled).",
                project_id,
            )
            return None, None, False, None
        raise

    body = response.json()
    merged = body.get("merged_yaml")
    lint_includes = body.get("includes")
    if merged is None:
        return None, None, False, None
    return merged, bool(body.get("valid", False)), False, lint_includes


def _try_raw_ci_yaml(
    gitlab_url: str,
    token: str,
    project_id: int,
    ref: str | None,
    file_path: str = DEFAULT_FILE_PATH,
) -> tuple[str | None, bool]:
    """
    Fetch the raw `.gitlab-ci.yml` from the repository as a fallback when
    /ci/lint is unavailable. Returns ``(text, denied)``:

    - ``(text, False)`` on success
    - ``(None, False)`` on 404 — the file does not exist, authoritative
    - ``(None, True)`` on 403 — the token cannot read repository files
    Other errors propagate.
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
        if e.response is not None and e.response.status_code == 403:
            logger.warning(
                "Raw .gitlab-ci.yml denied for project %s.",
                project_id,
            )
            return None, True
        if e.response is not None and e.response.status_code == 404:
            logger.warning(
                "Raw .gitlab-ci.yml not found for project %s.",
                project_id,
            )
            return None, False
        raise
    return response.text, False


@timeit
def fetch_ci_config_yaml(
    gitlab_url: str,
    token: str,
    project: dict[str, Any],
) -> tuple[str | None, bool | None, bool, bool, list[dict[str, Any]] | None]:
    """
    Try /ci/lint first, then fall back to the raw file. Returns
    ``(yaml_content, is_valid, is_merged, denied, lint_includes)``:

    - ``yaml_content`` is the raw or merged YAML, or ``None`` when no
      readable config was found.
    - ``is_merged`` is True when the YAML came from /ci/lint (with includes
      expanded), False when it's raw.
    - ``denied`` is True when BOTH paths returned 403.
    - ``lint_includes`` is GitLab's structured ``includes`` list from the
      lint response, or ``None`` if the lint path was not used. Needed
      because the merged_yaml does NOT contain the original ``include:``
      block — its content has been inlined as jobs — so the YAML parser
      alone would yield zero GitLabCIInclude nodes on the lint path.
    """
    project_id = project["id"]
    ref = project.get("default_branch")

    merged, is_valid, lint_denied, lint_includes = _try_lint_merged_yaml(
        gitlab_url, token, project_id, ref
    )
    if merged is not None:
        return merged, is_valid, True, False, lint_includes

    # Both 404 and 403 from /ci/lint fall back to the raw file. The raw
    # endpoint uses `read_repository`, broader than the Maintainer scope
    # /ci/lint needs.
    raw, raw_denied = _try_raw_ci_yaml(gitlab_url, token, project_id, ref)
    if raw is not None:
        return raw, None, False, False, None

    # Both paths failed. We only flag the project as ``denied`` if neither
    # path could authoritatively confirm the absence of a config — i.e.
    # both returned 403. A 404 from either endpoint (especially raw 404)
    # is authoritative absence and cleanup may run normally.
    denied = lint_denied and raw_denied
    return None, None, False, denied, None


def transform_ci_config(
    parsed: ParsedCIConfig,
    project_id: int,
    gitlab_url: str,
    is_merged: bool,
    file_path: str,
    project_variables: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Build the CIConfig node record.

    Two derived fields encode the variable references:

    - ``referenced_protected_variables`` — sorted list of variable keys
      that are referenced AND marked ``protected=True`` on the project.
      Surfaced as its own property for security queries.
    - ``referenced_variable_ids`` — IDs of project variables whose ``key``
      appears in the parsed pipeline; consumed by the
      ``REFERENCES_VARIABLE`` other_relationship at load time
      (``one_to_many=True``).
    """
    project_variables = project_variables or []
    referenced_keys = set(parsed.referenced_variable_keys)
    protected_keys = {
        v["key"] for v in project_variables if v.get("protected") and v.get("key")
    }
    referenced_protected = sorted(referenced_keys & protected_keys)
    referenced_variable_ids = [
        v["id"] for v in project_variables if v.get("key") in referenced_keys
    ]
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
        "referenced_variable_ids": referenced_variable_ids,
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
                "config_id": config_id,
                "gitlab_url": gitlab_url,
            }
        )
    return records


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
    GraphJob.from_node_schema(GitLabCIConfigSchema(), cleanup_params).run(neo4j_session)


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
    skip_projects: set[int] | None = None,
) -> set[int]:
    """
    For each project: fetch its CI YAML, parse it, and load CIConfig +
    includes. The config carries a ``referenced_variable_ids`` list that the
    schema turns into ``REFERENCES_VARIABLE`` edges to project-level CI
    variables at load time (one_to_many other_relationship).

    ``skip_projects`` lists project IDs whose CI variables could not be
    loaded this run (e.g. variables endpoint returned 403). Those projects
    are skipped here too — refreshing the config without its referenced
    variables would let cleanup wipe the ``REFERENCES_VARIABLE`` edges
    even though the variables themselves were preserved upstream.

    Returns the set of project IDs whose CI config could not be read
    because of permission denial OR which were forwarded via
    ``skip_projects``. The caller must skip ci_config / ci_include
    cleanup for these, otherwise it would delete previously-ingested data
    on a transient auth failure.
    """
    logger.info("Syncing GitLab CI configs for %d projects", len(projects))
    skip_projects = skip_projects or set()
    skipped_projects: set[int] = set(skip_projects)

    for project in projects:
        project_id: int = project["id"]
        if project_id in skip_projects:
            continue
        yaml_content, is_valid, is_merged, denied, lint_includes = fetch_ci_config_yaml(
            gitlab_url, token, project
        )
        if yaml_content is None:
            if denied:
                skipped_projects.add(project_id)
            continue

        parsed = parse_ci_config(yaml_content, is_valid=is_valid)
        # On the lint path the merged_yaml has no `include:` block (its
        # content was inlined as jobs), so populate `parsed.includes`
        # from the lint response's structured `includes` array.
        if is_merged and lint_includes is not None:
            lint_parsed = parse_lint_includes(lint_includes)
            parsed.includes = lint_parsed
            parsed.has_includes = bool(lint_parsed)
        project_variables = variables_by_project.get(project_id, [])

        config_record = transform_ci_config(
            parsed,
            project_id,
            gitlab_url,
            is_merged=is_merged,
            file_path=DEFAULT_FILE_PATH,
            project_variables=project_variables,
        )
        include_records = transform_ci_includes(
            parsed, project_id, gitlab_url, DEFAULT_FILE_PATH
        )

        load_ci_config(neo4j_session, config_record, project_id, gitlab_url, update_tag)
        load_ci_includes(
            neo4j_session, include_records, project_id, gitlab_url, update_tag
        )

    logger.info("GitLab CI configs sync completed")
    return skipped_projects
