"""
GitLab Dependencies Intelligence Module

Fetches and parses individual dependencies from dependency scanning job artifacts.
"""

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

# Default dependency scanning job name (GitLab's default)
DEFAULT_DEPENDENCY_SCAN_JOB_NAME = "gemnasium-dependency_scanning"


def get_dependencies(
    gitlab_url: str,
    token: str,
    project_id: int,
    dependency_files: list[dict[str, Any]],
    default_branch: str = "main",
    dependency_scan_job_name: str = DEFAULT_DEPENDENCY_SCAN_JOB_NAME,
) -> list[dict[str, Any]]:
    """
    Fetch dependencies from the latest dependency scanning job artifacts.

    Finds the most recent successful dependency scanning job, downloads its artifacts,
    and parses the dependency scanning report.

    Uses retry logic with exponential backoff for rate limiting and transient errors.

    :param gitlab_url: The GitLab instance URL.
    :param token: The GitLab API token.
    :param project_id: The numeric project ID.
    :param dependency_files: List of transformed dependency files for mapping.
    :param default_branch: The default branch to fetch artifacts from.
    :param dependency_scan_job_name: The name of the dependency scanning job
        (default: 'gemnasium-dependency_scanning').
    :return: List of dependency dictionaries.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    logger.debug(
        f"Fetching dependencies from scanning artifacts for project ID {project_id}"
    )

    # Find the latest successful dependency scanning job
    jobs_url = f"{gitlab_url}/api/v4/projects/{project_id}/jobs"
    params: dict[str, Any] = {
        "per_page": 10,
        "scope[]": ["success"],
    }

    job_id: int | None = None
    try:
        response = make_request_with_retry("GET", jobs_url, headers, params)
        response.raise_for_status()
        check_rate_limit_remaining(response)
        jobs = response.json()

        # Find the most recent dependency scanning job matching the configured name
        dep_scan_job = None
        for job in jobs:
            if job.get("name") == dependency_scan_job_name:
                dep_scan_job = job
                break

        if not dep_scan_job:
            logger.debug(
                f"No successful '{dependency_scan_job_name}' job found for project ID {project_id}"
            )
            return []

        job_id = dep_scan_job.get("id")
        logger.debug(
            f"Found dependency scanning job ID {job_id} for project ID {project_id}"
        )

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching jobs for project ID {project_id}: {e}")
        return []

    # Download the job artifacts
    artifacts_url = f"{gitlab_url}/api/v4/projects/{project_id}/jobs/artifacts/{default_branch}/download"
    params_artifacts: dict[str, str] = {
        "job": dependency_scan_job_name,
    }

    logger.debug(
        f"Downloading artifacts from branch '{default_branch}' for project ID {project_id}"
    )

    try:
        response = make_request_with_retry(
            "GET", artifacts_url, headers, params_artifacts
        )

        logger.debug(f"Artifacts download response status: {response.status_code}")

        if response.status_code == 404:
            logger.debug(
                f"No artifacts found for dependency scanning job in project {project_id}"
            )
            return []

        if response.status_code == 401:
            # Auth errors are systemic - fail fast rather than silently skipping
            raise requests.exceptions.HTTPError(
                "Unauthorized (401) - token may need 'api' or 'read_api' scope",
                response=response,
            )

        response.raise_for_status()
        check_rate_limit_remaining(response)

        # The response is a ZIP file containing the artifacts
        artifacts_zip = zipfile.ZipFile(io.BytesIO(response.content))

        # Find and parse CycloneDX SBOM files (gl-sbom-*.cdx.json)
        # GitLab now uses CycloneDX format instead of the old gl-dependency-scanning-report.json
        cdx_files = [
            f
            for f in artifacts_zip.namelist()
            if f.startswith("gl-sbom-") and f.endswith(".cdx.json")
        ]

        if not cdx_files:
            logger.debug(
                f"No CycloneDX SBOM files found in artifacts for project ID {project_id}"
            )
            logger.debug(f"Available files: {artifacts_zip.namelist()}")
            return []

        # Parse all CycloneDX files (there may be multiple for different package managers)
        all_dependencies: list[dict[str, Any]] = []
        for cdx_file in cdx_files:
            logger.debug(f"Parsing CycloneDX SBOM file: {cdx_file}")
            with artifacts_zip.open(cdx_file) as report_file:
                report_data = json.load(report_file)
                deps = _parse_cyclonedx_sbom(report_data, dependency_files)
                all_dependencies.extend(deps)

        logger.debug(
            f"Successfully parsed {len(cdx_files)} CycloneDX SBOM file(s) for project ID {project_id}"
        )

    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading artifacts for job ID {job_id}: {e}")
        return []
    except zipfile.BadZipFile as e:
        logger.error(f"Invalid ZIP file for job ID {job_id}: {e}")
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
    project_url: str,
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
            "project_url": project_url,
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
    project_url: str,
    update_tag: int,
) -> None:
    """
    Load GitLab dependencies into the graph for a specific project.
    """
    logger.info(f"Loading {len(dependencies)} dependencies for project {project_url}")
    load(
        neo4j_session,
        GitLabDependencySchema(),
        dependencies,
        lastupdated=update_tag,
        project_url=project_url,
    )


@timeit
def cleanup_dependencies(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    project_url: str,
) -> None:
    """
    Remove stale GitLab dependencies from the graph for a specific project.
    """
    logger.info(f"Running GitLab dependencies cleanup for project {project_url}")
    cleanup_params = {**common_job_parameters, "project_url": project_url}
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
                raw_dependency_files, project_url
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

        transformed_dependencies = transform_dependencies(raw_dependencies, project_url)

        logger.debug(
            f"Found {len(transformed_dependencies)} dependencies in project {project_name}"
        )

        load_dependencies(
            neo4j_session, transformed_dependencies, project_url, update_tag
        )

    logger.info("GitLab dependencies sync completed")
