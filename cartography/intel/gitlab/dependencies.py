"""
GitLab Dependencies Intelligence Module

Fetches and parses individual dependencies from dependency scanning job artifacts.
"""

import gzip
import io
import json
import logging
import zipfile
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gitlab.util import check_rate_limit_remaining
from cartography.intel.gitlab.util import make_request_with_retry
from cartography.models.gitlab.dependencies import GitLabDependencySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Dependency scanning job names used by GitLab.
DEFAULT_DEPENDENCY_SCAN_JOB_NAME = "gemnasium-dependency_scanning"
AUTODEVOPS_PYTHON_DEPENDENCY_SCAN_JOB_NAME = "gemnasium-python-dependency_scanning"
AUTODEVOPS_MAVEN_DEPENDENCY_SCAN_JOB_NAME = "gemnasium-maven-dependency_scanning"
DEFAULT_DEPENDENCY_SCAN_JOB_NAMES = frozenset(
    (
        DEFAULT_DEPENDENCY_SCAN_JOB_NAME,
        AUTODEVOPS_PYTHON_DEPENDENCY_SCAN_JOB_NAME,
        AUTODEVOPS_MAVEN_DEPENDENCY_SCAN_JOB_NAME,
    )
)
DEPENDENCY_SCAN_JOBS_PER_PAGE = 100
CYCLONEDX_ARTIFACT_SUFFIXES = (".cdx.json", ".cdx.json.gz")


def _select_dependency_scan_job(
    jobs: list[dict[str, Any]],
    dependency_scan_job_name: str | None,
    default_branch: str | None = None,
) -> dict[str, Any] | None:
    """
    Select the latest dependency scan job from successful jobs.

    If no custom job name is configured, support all known GitLab dependency
    scan job names (default + AutoDevOps language-specific names). For any
    custom job name, only that specific name is matched. Prefer jobs that ran
    on the project default branch so branch-scoped dependency data wins over
    newer merge request or feature branch jobs.
    """
    candidate_names: set[str] | frozenset[str]
    if dependency_scan_job_name is None:
        candidate_names = DEFAULT_DEPENDENCY_SCAN_JOB_NAMES
    else:
        candidate_names = {dependency_scan_job_name}

    matching_jobs = [job for job in jobs if job.get("name") in candidate_names]
    if not matching_jobs:
        return None

    if default_branch:
        for job in matching_jobs:
            if job.get("ref") == default_branch:
                return job

    return matching_jobs[0]


def _get_successful_jobs(
    gitlab_url: str,
    headers: dict[str, str],
    project_id: int,
) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    jobs_url = f"{gitlab_url}/api/v4/projects/{project_id}/jobs"
    page = 1

    while True:
        params: dict[str, Any] = {
            "page": page,
            "per_page": DEPENDENCY_SCAN_JOBS_PER_PAGE,
            "scope[]": ["success"],
        }
        response = make_request_with_retry("GET", jobs_url, headers, params)
        response.raise_for_status()
        check_rate_limit_remaining(response)

        page_jobs = response.json()
        if not page_jobs:
            break

        jobs.extend(page_jobs)

        next_page = response.headers.get("X-Next-Page")
        if not next_page:
            break
        page = int(next_page)

    return jobs


def _is_cyclonedx_artifact(path: str) -> bool:
    filename = path.rsplit("/", 1)[-1]
    return filename in {
        "gl-sbom.cdx.json",
        "gl-sbom.cdx.json.gz",
    } or (
        filename.startswith("gl-sbom-")
        and filename.endswith(CYCLONEDX_ARTIFACT_SUFFIXES)
    )


def _load_cyclonedx_json(content: bytes, path: str) -> dict[str, Any]:
    if path.endswith(".gz"):
        content = gzip.decompress(content)
    return json.loads(content.decode("utf-8"))


def _parse_cyclonedx_artifact(
    content: bytes,
    path: str,
    dependency_files: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    report_data = _load_cyclonedx_json(content, path)
    return _parse_cyclonedx_sbom(report_data, dependency_files)


def _parse_cyclonedx_artifacts_zip(
    content: bytes,
    dependency_files: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    all_dependencies: list[dict[str, Any]] = []
    with zipfile.ZipFile(io.BytesIO(content)) as artifacts_zip:
        cdx_files = [f for f in artifacts_zip.namelist() if _is_cyclonedx_artifact(f)]

        if not cdx_files:
            logger.debug("No CycloneDX SBOM files found in artifacts archive.")
            logger.debug("Available files: %s", artifacts_zip.namelist())
            return []

        for cdx_file in cdx_files:
            logger.debug("Parsing CycloneDX SBOM file: %s", cdx_file)
            with artifacts_zip.open(cdx_file) as report_file:
                all_dependencies.extend(
                    _parse_cyclonedx_artifact(
                        report_file.read(),
                        cdx_file,
                        dependency_files,
                    )
                )

    return all_dependencies


def _get_dependency_scan_artifact_paths(job: dict[str, Any]) -> list[str]:
    artifact_paths: list[str] = []
    for artifact in job.get("artifacts") or []:
        path = artifact.get("filename")
        if path and _is_cyclonedx_artifact(path):
            artifact_paths.append(path)
    return artifact_paths


def _download_raw_cyclonedx_artifacts(
    gitlab_url: str,
    headers: dict[str, str],
    project_id: int,
    job_id: int,
    artifact_paths: list[str],
    dependency_files: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    all_dependencies: list[dict[str, Any]] = []
    for artifact_path in artifact_paths:
        artifacts_url = (
            f"{gitlab_url}/api/v4/projects/{project_id}/jobs/"
            f"{job_id}/artifacts/{artifact_path}"
        )
        response = make_request_with_retry("GET", artifacts_url, headers)
        if response.status_code == 404:
            logger.debug(
                "CycloneDX artifact %s was listed for job ID %s but is not downloadable.",
                artifact_path,
                job_id,
            )
            continue
        if response.status_code in (401, 403):
            _log_artifact_permission_warning(project_id, job_id, response.status_code)
            return []
        response.raise_for_status()
        check_rate_limit_remaining(response)
        all_dependencies.extend(
            _parse_cyclonedx_artifact(
                response.content,
                artifact_path,
                dependency_files,
            )
        )

    return all_dependencies


def _log_artifact_permission_warning(
    project_id: int,
    job_id: int | None,
    status_code: int,
) -> None:
    logger.warning(
        "GitLab returned %s while downloading dependency scanning artifacts for "
        "project ID %s job ID %s. Ensure the token user can download CI job "
        "artifacts for this project; artifacts:access restrictions may require "
        "Developer or Maintainer access.",
        status_code,
        project_id,
        job_id,
    )


def get_dependencies(
    gitlab_url: str,
    token: str,
    project_id: int,
    dependency_files: list[dict[str, Any]],
    default_branch: str = "main",
    dependency_scan_job_name: str | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch dependencies from the latest dependency scanning job artifacts.

    Finds a successful dependency scanning job, downloads its artifacts by job ID,
    and parses CycloneDX dependency scanning reports.

    Uses retry logic with exponential backoff for rate limiting and transient errors.

    :param gitlab_url: The GitLab instance URL.
    :param token: The GitLab API token.
    :param project_id: The numeric project ID.
    :param dependency_files: List of transformed dependency files for mapping.
    :param default_branch: The default branch to fetch artifacts from.
    :param dependency_scan_job_name: Optional custom dependency scanning job
        name to look for. If not provided, Cartography searches all known
        GitLab dependency scanning job names:
        'gemnasium-dependency_scanning',
        'gemnasium-python-dependency_scanning', and
        'gemnasium-maven-dependency_scanning'.
    :return: List of dependency dictionaries.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    logger.debug(
        f"Fetching dependencies from scanning artifacts for project ID {project_id}"
    )

    job_id: int | None = None
    dep_scan_job: dict[str, Any] | None = None
    try:
        jobs = _get_successful_jobs(gitlab_url, headers, project_id)

        # Find the most recent dependency scanning job matching the configured name
        dep_scan_job = _select_dependency_scan_job(
            jobs,
            dependency_scan_job_name,
            default_branch,
        )

        if not dep_scan_job:
            configured_job_name = (
                dependency_scan_job_name or "all known GitLab dependency scan jobs"
            )
            logger.info(
                "No successful dependency scanning job found for project ID %s. "
                "Searched for configured job '%s'.",
                project_id,
                configured_job_name,
            )
            return []

        job_id = dep_scan_job.get("id")
        job_name = dep_scan_job.get("name", DEFAULT_DEPENDENCY_SCAN_JOB_NAME)
        logger.debug(
            "Found dependency scanning job '%s' (ID %s, ref %s) for project ID %s",
            job_name,
            job_id,
            dep_scan_job.get("ref"),
            project_id,
        )

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching jobs for project ID {project_id}: {e}")
        return []

    # Download the job artifacts
    if not dep_scan_job:
        return []

    if job_id is None:
        logger.info(
            "Dependency scanning job for project ID %s did not include a job ID.",
            project_id,
        )
        return []

    artifacts_url = f"{gitlab_url}/api/v4/projects/{project_id}/jobs/{job_id}/artifacts"

    logger.debug(
        "Downloading artifacts for project ID %s job ID %s", project_id, job_id
    )

    try:
        response = make_request_with_retry("GET", artifacts_url, headers)

        logger.debug(f"Artifacts download response status: {response.status_code}")

        if response.status_code == 404:
            logger.info(
                "No artifacts found for dependency scanning job in project ID %s",
                project_id,
            )
            return []

        if response.status_code in (401, 403):
            _log_artifact_permission_warning(project_id, job_id, response.status_code)
            return []

        response.raise_for_status()
        check_rate_limit_remaining(response)

        try:
            all_dependencies = _parse_cyclonedx_artifacts_zip(
                response.content,
                dependency_files,
            )
        except zipfile.BadZipFile:
            all_dependencies = _parse_cyclonedx_artifact(
                response.content,
                (
                    "gl-sbom.cdx.json.gz"
                    if response.content.startswith(b"\x1f\x8b")
                    else "gl-sbom.cdx.json"
                ),
                dependency_files,
            )

        if not all_dependencies:
            artifact_paths = _get_dependency_scan_artifact_paths(dep_scan_job)
            all_dependencies = _download_raw_cyclonedx_artifacts(
                gitlab_url,
                headers,
                project_id,
                job_id,
                artifact_paths,
                dependency_files,
            )

        logger.debug(
            "Successfully parsed %s dependencies from CycloneDX SBOM artifact(s) "
            "for project ID %s",
            len(all_dependencies),
            project_id,
        )

    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading artifacts for job ID {job_id}: {e}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in CycloneDX SBOM: {e}")
        return []

    logger.debug(
        f"Extracted {len(all_dependencies)} dependencies for project ID {project_id}"
    )
    return all_dependencies


def _parse_cyclonedx_sbom(
    sbom_data: dict[str, Any],
    dependency_files: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Parse a CycloneDX SBOM file to extract dependencies.

    CycloneDX is the format GitLab uses for dependency scanning.
    Format: https://cyclonedx.org/

    GitLab stores the source manifest/lock file in the SBOM metadata as
    'gitlab:dependency_scanning:input_file:path'. All dependencies in this SBOM
    came from that single file.

    :param sbom_data: Parsed JSON from gl-sbom-*.cdx.json file
    :param dependency_files: List of dependency files for mapping paths to IDs
    :return: List of dependency dictionaries
    """
    dependencies = []

    # Create a mapping of file paths to dependency file IDs
    path_to_id = {
        df.get("path"): df.get("id") for df in dependency_files if df.get("path")
    }

    # Extract the source manifest file from SBOM metadata
    # GitLab stores this as 'gitlab:dependency_scanning:input_file:path'
    manifest_path = ""
    manifest_id = None
    metadata = sbom_data.get("metadata", {})
    metadata_properties = metadata.get("properties", [])
    for prop in metadata_properties:
        if prop.get("name") == "gitlab:dependency_scanning:input_file:path":
            manifest_path = prop.get("value", "")
            manifest_id = path_to_id.get(manifest_path)
            break

    # Extract components (dependencies) from the SBOM
    components = sbom_data.get("components", [])

    for component in components:
        if component.get("type") != "library":
            # Skip non-library components
            continue

        name = component.get("name", "")
        version = component.get("version", "")

        if not name:
            continue

        # Extract package manager from purl (Package URL)
        # Example: "pkg:npm/express@4.18.2" -> package_manager = "npm"
        purl = component.get("purl", "")
        package_manager = "unknown"
        if purl.startswith("pkg:"):
            # purl format: pkg:<type>/<name>@<version>
            parts = purl.split("/")
            if len(parts) >= 1:
                pkg_type = parts[0].replace("pkg:", "")
                package_manager = pkg_type

        dependency = {
            "name": name,
            "version": version,
            "package_manager": package_manager,
            "manifest_path": manifest_path,
        }

        # Add manifest_id if we found a matching DependencyFile
        if manifest_id:
            dependency["manifest_id"] = manifest_id

        dependencies.append(dependency)

    return dependencies


def transform_dependencies(
    raw_dependencies: list[dict[str, Any]],
    project_id: int,
    project_url: str,
    gitlab_url: str,
) -> list[dict[str, Any]]:
    """
    Transform raw dependency data to match our schema.
    """
    transformed = []

    for dep in raw_dependencies:
        name = dep.get("name", "")
        version = dep.get("version", "")
        package_manager = dep.get("package_manager", "unknown")
        manifest_id = dep.get("manifest_id")

        # Construct unique ID: project_url:package_manager:name@version
        # Example: "https://gitlab.com/group/project:npm:express@4.18.2"
        dep_id = f"{project_url}:{package_manager}:{name}@{version}"

        transformed_dep = {
            "id": dep_id,
            "name": name,
            "version": version,
            "package_manager": package_manager,
            "project_id": project_id,
            "project_url": project_url,
            "gitlab_url": gitlab_url,
        }

        if manifest_id:
            transformed_dep["manifest_id"] = manifest_id

        transformed.append(transformed_dep)

    logger.info(f"Transformed {len(transformed)} dependencies")
    return transformed


@timeit
def load_dependencies(
    neo4j_session: neo4j.Session,
    dependencies: list[dict[str, Any]],
    project_id: int,
    gitlab_url: str,
    update_tag: int,
) -> None:
    """
    Load GitLab dependencies into the graph for a specific project.
    """
    load(
        neo4j_session,
        GitLabDependencySchema(),
        dependencies,
        lastupdated=update_tag,
        project_id=project_id,
        gitlab_url=gitlab_url,
    )


@timeit
def cleanup_dependencies(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    project_id: int,
    gitlab_url: str,
) -> None:
    """
    Remove stale GitLab dependencies from the graph for a specific project.
    """
    logger.info(f"Running GitLab dependencies cleanup for project {project_id}")
    cleanup_params = {
        **common_job_parameters,
        "project_id": project_id,
        "gitlab_url": gitlab_url,
    }
    GraphJob.from_node_schema(GitLabDependencySchema(), cleanup_params).run(
        neo4j_session
    )


@timeit
def sync_gitlab_dependencies(
    neo4j_session: neo4j.Session,
    gitlab_url: str,
    token: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    projects: list[dict[str, Any]],
    dependency_files_by_project: dict[str, list[dict[str, Any]]] | None = None,
) -> None:
    """
    Sync GitLab dependencies for all projects.

    :param neo4j_session: Neo4j session.
    :param gitlab_url: The GitLab instance URL.
    :param token: The GitLab API token.
    :param update_tag: Update tag for tracking data freshness.
    :param common_job_parameters: Common job parameters.
    :param projects: List of project dicts to sync.
    :param dependency_files_by_project: Pre-fetched dependency files from dependency_files sync.
        If provided, avoids duplicate API calls. Dict maps project_url to list of files.
    """
    logger.info(f"Syncing GitLab dependencies for {len(projects)} projects")

    # Sync dependencies for each project
    for project in projects:
        project_id: int = project["id"]
        project_name: str = project["name"]
        project_url: str = project["web_url"]
        default_branch: str = project.get("default_branch") or "main"

        logger.debug(f"Syncing dependencies for project: {project_name}")

        # Use pre-fetched dependency files if available, otherwise fetch them
        if dependency_files_by_project is not None:
            transformed_files = dependency_files_by_project.get(project_url, [])
        else:
            # Fallback: import here to avoid circular import at module level
            from cartography.intel.gitlab.dependency_files import get_dependency_files
            from cartography.intel.gitlab.dependency_files import (
                transform_dependency_files,
            )

            raw_dependency_files = get_dependency_files(gitlab_url, token, project_id)
            if not raw_dependency_files:
                logger.debug(f"No dependency files found for project {project_name}")
                continue
            transformed_files = transform_dependency_files(
                raw_dependency_files, project_id, project_url, gitlab_url
            )

        if not transformed_files:
            logger.debug(f"No dependency files found for project {project_name}")
            continue

        raw_dependencies = get_dependencies(
            gitlab_url,
            token,
            project_id,
            transformed_files,
            default_branch,
        )

        if not raw_dependencies:
            logger.debug(f"No dependencies found for project {project_name}")
            continue

        transformed_dependencies = transform_dependencies(
            raw_dependencies,
            project_id,
            project_url,
            gitlab_url,
        )

        logger.debug(
            f"Found {len(transformed_dependencies)} dependencies in project {project_name}"
        )

        load_dependencies(
            neo4j_session,
            transformed_dependencies,
            project_id,
            gitlab_url,
            update_tag,
        )

    logger.info("GitLab dependencies sync completed")
