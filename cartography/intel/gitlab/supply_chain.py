import base64
import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.gitlab.util import get_paginated
from cartography.intel.gitlab.util import get_single
from cartography.intel.supply_chain import ContainerImage
from cartography.intel.supply_chain import convert_layer_history_records
from cartography.intel.supply_chain import match_images_to_dockerfiles
from cartography.intel.supply_chain import parse_dockerfile_info
from cartography.intel.supply_chain import transform_matches_for_matchlink
from cartography.models.gitlab.packaged_matchlink import (
    GitLabProjectDockerfilePackagedFromMatchLink,
)
from cartography.models.gitlab.packaged_matchlink import (
    GitLabProjectProvenancePackagedFromMatchLink,
)
from cartography.util import run_analysis_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_unmatched_gitlab_container_images_with_history(
    neo4j_session: neo4j.Session,
    org_url: str,
    update_tag: int,
    limit: int | None = None,
) -> list[ContainerImage]:
    """
    Query GitLab container images not yet matched by provenance in this sync iteration.

    Scoped to the current GitLab organization via the graph path:
    GitLabOrganization → RESOURCE → GitLabContainerRepository → HAS_TAG → Tag → REFERENCES → Image.

    Returns one image per container repository (preferring 'latest' tag, then most recent).
    Excludes images that already have a PACKAGED_FROM relationship created in the current
    sync iteration (i.e. by provenance matching). Images with stale PACKAGED_FROM from
    previous iterations are included so they can be re-matched before cleanup removes them.

    :param neo4j_session: Neo4j session
    :param org_url: The GitLab organization URL to scope the query
    :param update_tag: The current sync update tag
    :param limit: Optional limit on number of images to return
    :return: List of ContainerImage objects with layer history populated
    """
    query = """
        MATCH (org:GitLabOrganization {id: $org_url})-[:RESOURCE]->(repo:GitLabContainerRepository)
              -[:HAS_TAG]->(tag:GitLabContainerRepositoryTag)
              -[:REFERENCES]->(img:GitLabContainerImage)
        WHERE img.layer_diff_ids IS NOT NULL
          AND size(img.layer_diff_ids) > 0
          AND NOT exists((img)-[:PACKAGED_FROM {lastupdated: $update_tag}]->())
        WITH repo, img, tag
        ORDER BY
            CASE WHEN tag.name = 'latest' THEN 0 ELSE 1 END,
            tag.created_at DESC
        WITH repo, collect({
            digest: img.digest,
            uri: img.uri,
            repository_location: repo.id,
            tag: tag.name,
            layer_diff_ids: img.layer_diff_ids,
            type: img.type,
            architecture: img.architecture,
            os: img.os
        })[0] AS best
        // Get layer history for each best image
        WITH best
        UNWIND range(0, size(best.layer_diff_ids) - 1) AS idx
        WITH best, best.layer_diff_ids[idx] AS diff_id, idx
        OPTIONAL MATCH (layer:ImageLayer {diff_id: diff_id})
        WITH best, idx, {
            diff_id: diff_id,
            history: layer.history,
            is_empty: layer.is_empty
        } AS layer_info
        ORDER BY idx
        WITH best, collect(layer_info) AS layer_history
        RETURN
            best.digest AS digest,
            best.uri AS uri,
            best.repository_location AS repository_location,
            best.tag AS tag,
            best.layer_diff_ids AS layer_diff_ids,
            best.type AS type,
            best.architecture AS architecture,
            best.os AS os,
            layer_history
    """

    if limit:
        query += f" LIMIT {limit}"

    result = neo4j_session.run(query, update_tag=update_tag, org_url=org_url)
    images = []

    for record in result:
        layer_history = convert_layer_history_records(record["layer_history"])

        images.append(
            ContainerImage(
                digest=record["digest"],
                uri=record["uri"] or "",
                registry_id=record["repository_location"] or None,
                display_name=record["repository_location"] or None,
                tag=record["tag"],
                layer_diff_ids=record["layer_diff_ids"] or [],
                image_type=record["type"],
                architecture=record["architecture"],
                os=record["os"],
                layer_history=layer_history,
            )
        )

    logger.info(
        f"Found {len(images)} GitLab container images with layer history (one per repository)"
    )
    return images


def search_dockerfiles_in_project(
    gitlab_url: str,
    token: str,
    project_id: int,
) -> list[dict[str, Any]]:
    """
    Search for Dockerfile files in a GitLab project using the repository tree API.

    :param gitlab_url: The GitLab instance URL
    :param token: GitLab API token
    :param project_id: The project ID to search in
    :return: List of file items containing dockerfile in the name
    """
    try:
        # Get repository tree with recursive search
        files = get_paginated(
            gitlab_url,
            token,
            f"/api/v4/projects/{project_id}/repository/tree",
            extra_params={"recursive": True, "per_page": 100},
        )

        # Filter for dockerfile-related files (case-insensitive)
        dockerfiles = [
            f
            for f in files
            if f.get("type") == "blob" and "dockerfile" in f.get("name", "").lower()
        ]

        logger.debug(f"Found {len(dockerfiles)} dockerfile(s) in project {project_id}")
        return dockerfiles

    except requests.exceptions.HTTPError as e:
        # Only 404 (project not found) is acceptable for skipping
        # 403 (forbidden) should propagate as it may indicate auth issues
        if e.response is not None and e.response.status_code == 404:
            logger.debug("Project not found: %d", project_id)
            return []
        raise


def get_file_content(
    gitlab_url: str,
    token: str,
    project_id: int,
    file_path: str,
    ref: str = "HEAD",
) -> str | None:
    """
    Download the content of a file from a GitLab project using the Repository Files API.

    :param gitlab_url: The GitLab instance URL
    :param token: GitLab API token
    :param project_id: The project ID
    :param file_path: The path to the file within the repository
    :param ref: The git reference (branch, tag, or commit SHA)
    :return: The file content as a string, or None if retrieval fails
    """
    import urllib.parse

    encoded_path = urllib.parse.quote(file_path, safe="")
    endpoint = f"/api/v4/projects/{project_id}/repository/files/{encoded_path}"

    try:
        response = get_single(gitlab_url, token, f"{endpoint}?ref={ref}")

        # GitLab returns content as base64 encoded
        if response.get("encoding") == "base64":
            content_b64 = response.get("content", "")
            content = base64.b64decode(content_b64).decode("utf-8")
            return content

        # If not base64 encoded, return raw content
        return response.get("content")

    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            logger.debug(f"File not found: project {project_id}/{file_path}")
            return None
        raise


def _build_dockerfile_info(
    file_item: dict[str, Any],
    content: str,
    project: dict[str, Any],
) -> dict[str, Any] | None:
    """Build dockerfile info dict with parsed content."""
    path = file_item.get("path", "")
    project_url = project.get("web_url", "")
    project_name = project.get("path_with_namespace", "")

    info = parse_dockerfile_info(content, path, project_name)
    if info is None:
        return None
    info["project_url"] = project_url
    info["project_name"] = project_name
    # Used by the shared matching algorithm
    info["source_repo_id"] = project_url
    return info


@timeit
def get_dockerfiles_for_projects(
    gitlab_url: str,
    token: str,
    projects: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Search and download Dockerfiles for a list of GitLab projects.

    :param gitlab_url: The GitLab instance URL
    :param token: GitLab API token
    :param projects: List of project dictionaries (from GitLab API)
    :return: List of dictionaries containing project info, file path, and content
    """
    if not projects:
        return []

    all_dockerfiles: list[dict[str, Any]] = []

    for project in projects:
        project_id = project.get("id")
        if not project_id:
            continue

        # Search for dockerfiles in this project
        dockerfile_items = search_dockerfiles_in_project(gitlab_url, token, project_id)

        for item in dockerfile_items:
            file_path = item.get("path")
            if not file_path:
                continue

            # Download the file content
            content = get_file_content(gitlab_url, token, project_id, file_path)
            if content:
                dockerfile_info = _build_dockerfile_info(item, content, project)
                if dockerfile_info is not None:
                    all_dockerfiles.append(dockerfile_info)

    logger.info(
        f"Retrieved {len(all_dockerfiles)} dockerfile(s) from {len(projects)} projects"
    )
    return all_dockerfiles


@timeit
def sync(
    neo4j_session: neo4j.Session,
    gitlab_url: str,
    token: str,
    org_url: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    projects: list[dict[str, Any]],
    image_limit: int | None = None,
    min_match_confidence: float = 0.5,
) -> None:
    """
    Sync supply chain relationships for a GitLab organization.

    Uses a two-stage matching approach:
    1. PACKAGED_FROM (provenance): SLSA provenance-based matching (100% confidence)
    2. PACKAGED_FROM (dockerfile): Dockerfile command matching for unmatched images

    Only images without an existing PACKAGED_FROM relationship go through the
    expensive Dockerfile analysis step.

    :param neo4j_session: Neo4j session for querying container images
    :param gitlab_url: The GitLab instance URL
    :param token: GitLab API token
    :param org_url: The GitLab organization URL
    :param update_tag: The update timestamp tag
    :param common_job_parameters: Common job parameters
    :param projects: List of project dictionaries to search for Dockerfiles
    :param image_limit: Optional limit on number of images to process
    :param min_match_confidence: Minimum confidence threshold for matches
    """
    logger.info("Starting supply chain sync for GitLab org %s", org_url)

    # 1. PACKAGED_FROM matchlinks (SLSA provenance — no pre-query needed)
    provenance_data = [
        {
            "project_url": p["web_url"],
            "match_method": "provenance",
            "dockerfile_path": None,
            "confidence": 1.0,
            "matched_commands": 0,
            "total_commands": 0,
            "command_similarity": 1.0,
        }
        for p in projects
        if p.get("web_url")
    ]
    if provenance_data:
        logger.info(
            "Loading provenance PACKAGED_FROM for %d projects",
            len(provenance_data),
        )
        load_matchlinks(
            neo4j_session,
            GitLabProjectProvenancePackagedFromMatchLink(),
            provenance_data,
            lastupdated=update_tag,
            _sub_resource_label="GitLabOrganization",
            _sub_resource_id=org_url,
        )

    # 2. Get images WITHOUT existing PACKAGED_FROM for dockerfile analysis
    unmatched = get_unmatched_gitlab_container_images_with_history(
        neo4j_session,
        org_url,
        update_tag,
        limit=image_limit,
    )

    # 3. Dockerfile analysis (only for unmatched images)
    if unmatched:
        dockerfiles = get_dockerfiles_for_projects(gitlab_url, token, projects)
        if dockerfiles:
            matches = match_images_to_dockerfiles(
                unmatched,
                dockerfiles,
                min_confidence=min_match_confidence,
            )
            if matches:
                matchlink_data = transform_matches_for_matchlink(
                    matches,
                    "project_url",
                )
                if matchlink_data:
                    logger.info(
                        "Loading %d dockerfile-based PACKAGED_FROM relationships",
                        len(matchlink_data),
                    )
                    load_matchlinks(
                        neo4j_session,
                        GitLabProjectDockerfilePackagedFromMatchLink(),
                        matchlink_data,
                        lastupdated=update_tag,
                        _sub_resource_label="GitLabOrganization",
                        _sub_resource_id=org_url,
                    )

    # 4. Cleanup stale relationships
    GraphJob.from_matchlink(
        GitLabProjectProvenancePackagedFromMatchLink(),
        "GitLabOrganization",
        org_url,
        update_tag,
    ).run(neo4j_session)

    GraphJob.from_matchlink(
        GitLabProjectDockerfilePackagedFromMatchLink(),
        "GitLabOrganization",
        org_url,
        update_tag,
    ).run(neo4j_session)

    # 5. Enrich PACKAGED_FROM with source_file from Image provenance
    run_analysis_job(
        "supply_chain_source_file.json",
        neo4j_session,
        common_job_parameters,
    )

    logger.info("Completed supply chain sync for GitLab org %s", org_url)
