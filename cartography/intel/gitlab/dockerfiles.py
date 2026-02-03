"""
GitLab Dockerfiles Intelligence Module

Syncs Dockerfiles from GitLab projects and matches them to container images
based on layer history command analysis. Creates BUILT_FROM relationships
between ImageTag and GitLabProject nodes.
"""

import base64
import logging
from dataclasses import dataclass
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.dockerfile_parser import extract_layer_commands_from_history
from cartography.intel.dockerfile_parser import find_best_dockerfile_matches
from cartography.intel.dockerfile_parser import parse as parse_dockerfile
from cartography.intel.dockerfile_parser import ParsedDockerfile
from cartography.intel.gitlab.util import get_paginated
from cartography.intel.gitlab.util import get_single
from cartography.models.gitlab.dockerfile_image import GitLabProjectBuiltFromMatchLink
from cartography.util import timeit

logger = logging.getLogger(__name__)


# =============================================================================
# Container Image Data Classes
# =============================================================================


@dataclass
class GitLabContainerImage:
    """Represents a GitLab container image from the graph."""

    digest: str
    uri: str
    repository_location: str
    tag: str | None
    layer_diff_ids: list[str]
    image_type: str | None
    architecture: str | None
    os: str | None
    layer_history: list[dict[str, Any]]


@dataclass
class ImageDockerfileMatch:
    """Represents a match between a container repository and a Dockerfile."""

    registry_repo_location: str
    project_url: str
    dockerfile_path: str | None
    confidence: float
    matched_commands: int
    total_commands: int
    command_similarity: float


# =============================================================================
# Container Image Queries
# =============================================================================


def get_gitlab_container_images_with_history(
    neo4j_session: neo4j.Session,
    org_url: str,
    limit: int | None = None,
) -> list[GitLabContainerImage]:
    """
    Query the graph to get GitLab container images with their layer history.

    Returns one image per container repository (preferring 'latest' tag, then most recent).

    :param neo4j_session: Neo4j session
    :param org_url: The GitLab organization URL to scope the query
    :param limit: Optional limit on number of images to return
    :return: List of GitLabContainerImage objects with layer history populated
    """
    # Query GitLab-specific nodes with layer info
    query = """
        MATCH (img:GitLabContainerImage)<-[:REFERENCES]-(tag:GitLabContainerRepositoryTag)
              <-[:HAS_TAG]-(repo:GitLabContainerRepository)
        WHERE img.layer_diff_ids IS NOT NULL
          AND size(img.layer_diff_ids) > 0
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

    result = neo4j_session.run(query)
    images = []

    for record in result:
        # Convert layer_history from query result to expected format
        layer_history = [
            {
                "created_by": layer.get("history") or "",
                "empty_layer": layer.get("is_empty") or False,
                "diff_id": layer.get("diff_id"),
            }
            for layer in (record["layer_history"] or [])
        ]

        images.append(
            GitLabContainerImage(
                digest=record["digest"],
                uri=record["uri"] or "",
                repository_location=record["repository_location"] or "",
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


# =============================================================================
# Dockerfile Search and Download
# =============================================================================


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
        if e.response is not None and e.response.status_code in (403, 404):
            logger.debug(
                f"Cannot access project {project_id}: {e.response.status_code}"
            )
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
    # URL-encode the file path for the API
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
) -> dict[str, Any]:
    """Build dockerfile info dict with parsed content."""
    path = file_item.get("path", "")
    project_url = project.get("web_url", "")
    project_name = project.get("path_with_namespace", "")

    try:
        parsed = parse_dockerfile(content)
        return {
            "project_url": project_url,
            "project_name": project_name,
            "path": path,
            "content": content,
            "is_multistage": parsed.is_multistage,
            "stage_count": parsed.stage_count,
            "final_base_image": parsed.final_base_image,
            "all_base_images": parsed.all_base_images,
            "layer_count": parsed.layer_creating_instruction_count,
            "stages": [
                {
                    "name": stage.name,
                    "base_image": stage.base_image,
                    "base_image_tag": stage.base_image_tag,
                    "layer_count": stage.layer_count,
                }
                for stage in parsed.stages
            ],
        }
    except Exception as e:
        logger.warning(f"Failed to parse Dockerfile {project_name}/{path}: {e}")
        return {
            "project_url": project_url,
            "project_name": project_name,
            "path": path,
            "content": content,
            "parse_error": str(e),
        }


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
                all_dockerfiles.append(dockerfile_info)

    logger.info(
        f"Retrieved {len(all_dockerfiles)} dockerfile(s) from {len(projects)} projects"
    )
    return all_dockerfiles


# =============================================================================
# Dockerfile Matching
# =============================================================================


def match_images_to_dockerfiles(
    images: list[GitLabContainerImage],
    dockerfiles: list[dict[str, Any]],
    min_confidence: float = 0.5,
) -> list[ImageDockerfileMatch]:
    """
    Match container images to Dockerfiles based on layer history commands.

    :param images: List of container images to match (with layer_history already populated)
    :param dockerfiles: List of dockerfile dictionaries (from get_dockerfiles_for_projects)
    :param min_confidence: Minimum confidence threshold for matches
    :return: List of ImageDockerfileMatch objects
    """
    # Parse all dockerfiles into ParsedDockerfile objects
    parsed_dockerfiles: list[ParsedDockerfile] = []
    dockerfile_info_map: dict[str, dict[str, Any]] = {}

    for df_info in dockerfiles:
        if "parse_error" in df_info:
            continue
        try:
            parsed = parse_dockerfile(df_info["content"])
            # Store mapping from content_hash to original info
            dockerfile_info_map[parsed.content_hash] = df_info
            parsed_dockerfiles.append(parsed)
        except Exception as e:
            logger.warning(f"Failed to parse dockerfile {df_info.get('path')}: {e}")

    if not parsed_dockerfiles:
        logger.warning("No valid Dockerfiles to match against")
        return []

    matches: list[ImageDockerfileMatch] = []

    for image in images:
        # Use pre-loaded layer history from the image
        if not image.layer_history:
            logger.debug(
                f"No layer history for image {image.repository_location}:{image.tag}"
            )
            continue

        # Extract commands from history
        image_commands = extract_layer_commands_from_history(image.layer_history)
        if not image_commands:
            logger.debug(
                f"No commands extracted for image {image.repository_location}:{image.tag}"
            )
            continue

        # Find best matching Dockerfiles
        df_matches = find_best_dockerfile_matches(
            image_commands, parsed_dockerfiles, min_confidence
        )

        if df_matches:
            best_match = df_matches[0]
            df_info = dockerfile_info_map.get(best_match.dockerfile.content_hash, {})

            matches.append(
                ImageDockerfileMatch(
                    registry_repo_location=image.repository_location,
                    project_url=df_info.get("project_url", ""),
                    dockerfile_path=df_info.get("path"),
                    confidence=best_match.confidence,
                    matched_commands=best_match.matched_commands,
                    total_commands=best_match.total_commands,
                    command_similarity=best_match.command_similarity,
                )
            )
            logger.debug(
                f"Matched {image.repository_location}:{image.tag} -> {df_info.get('path')} "
                f"(confidence: {best_match.confidence:.2f})"
            )
        else:
            logger.debug(
                f"No match found for image {image.repository_location}:{image.tag}"
            )

    logger.info(
        f"Matched {len(matches)} images to Dockerfiles "
        f"(out of {len(images)} images, {len(parsed_dockerfiles)} Dockerfiles)"
    )
    return matches


def transform_matches_for_matchlink(
    matches: list[ImageDockerfileMatch],
) -> list[dict[str, Any]]:
    """
    Transform ImageDockerfileMatch objects into dictionaries for load_matchlinks.

    :param matches: List of ImageDockerfileMatch objects
    :return: List of dictionaries with fields matching the MatchLink schema
    """
    return [
        {
            "project_url": m.project_url,
            "registry_repo_location": m.registry_repo_location,
            "dockerfile_path": m.dockerfile_path,
            "confidence": m.confidence,
            "matched_commands": m.matched_commands,
            "total_commands": m.total_commands,
            "command_similarity": m.command_similarity,
        }
        for m in matches
        if m.project_url
    ]


# =============================================================================
# SLSA Provenance-based Matching (Primary Method)
# =============================================================================


def get_provenance_matches_for_org(
    neo4j_session: neo4j.Session,
    org_url: str,
) -> list[dict[str, Any]]:
    """
    Query images with SLSA provenance that match GitLab projects in an organization.

    This is the preferred matching method as it provides 100% confidence based on
    cryptographically signed provenance attestations, without needing Dockerfile
    content analysis.

    Returns data formatted for load_matchlinks with GitLabProjectBuiltFromMatchLink schema.

    :param neo4j_session: Neo4j session
    :param org_url: The GitLab organization URL to match against
    :return: List of dicts ready for load_matchlinks
    """
    # Query images that have source_uri and match it against GitLabProject.id
    # The source_uri from SLSA provenance is like "https://gitlab.com/org/repo"
    # which should match GitLabProject.id (web_url)
    query = """
        MATCH (img:Image)<-[:IMAGE]-(repo_img:ImageTag)
        WHERE img.source_uri IS NOT NULL
        MATCH (gl_project:GitLabProject)
        WHERE gl_project.id = img.source_uri
        MATCH (gl_project)-[:RESOURCE]->(gl_org:GitLabOrganization {id: $org_url})
        WITH DISTINCT repo_img.repository_location AS registry_repo_location,
                      gl_project.id AS project_url
        RETURN registry_repo_location, project_url
    """

    result = neo4j_session.run(query, org_url=org_url)
    matches = []

    for record in result:
        matches.append(
            {
                "registry_repo_location": record["registry_repo_location"],
                "project_url": record["project_url"],
                "dockerfile_path": None,  # Provenance doesn't include dockerfile path
                "confidence": 1.0,  # 100% confident from provenance
                "matched_commands": 0,
                "total_commands": 0,
                "command_similarity": 1.0,
            }
        )

    logger.info(
        "Found %d provenance-based matches for organization %s",
        len(matches),
        org_url,
    )
    return matches


@timeit
def load_provenance_relationships(
    neo4j_session: neo4j.Session,
    org_url: str,
    update_tag: int,
) -> int:
    """
    Load BUILT_FROM relationships based on SLSA provenance data.

    This is the primary matching method - uses provenance attestations to directly
    link container images to their source projects with 100% confidence.

    :param neo4j_session: Neo4j session
    :param org_url: The GitLab organization URL
    :param update_tag: The update timestamp tag
    :return: Number of relationships created
    """
    matches = get_provenance_matches_for_org(neo4j_session, org_url)

    if not matches:
        logger.info("No provenance-based matches found for %s", org_url)
        return 0

    logger.info("Loading %d provenance-based BUILT_FROM relationships...", len(matches))

    load_matchlinks(
        neo4j_session,
        GitLabProjectBuiltFromMatchLink(),
        matches,
        lastupdated=update_tag,
        _sub_resource_label="GitLabOrganization",
        _sub_resource_id=org_url,
    )

    logger.info("Loaded %d provenance-based BUILT_FROM relationships", len(matches))
    return len(matches)


# =============================================================================
# Load and Cleanup
# =============================================================================


@timeit
def load_dockerfile_image_relationships(
    neo4j_session: neo4j.Session,
    matches: list[ImageDockerfileMatch],
    org_url: str,
    update_tag: int,
) -> None:
    """
    Load BUILT_FROM relationships between ImageTag and GitLabProject.

    :param neo4j_session: Neo4j session
    :param matches: List of ImageDockerfileMatch objects
    :param org_url: The GitLab organization URL (used as sub_resource_id)
    :param update_tag: The update timestamp tag
    """
    if not matches:
        logger.info("No matches to load")
        return

    # Transform matches for MatchLink loading
    matchlink_data = transform_matches_for_matchlink(matches)

    if not matchlink_data:
        logger.info("No valid matches with project URLs to load")
        return

    logger.info(f"Loading {len(matchlink_data)} BUILT_FROM relationships...")

    load_matchlinks(
        neo4j_session,
        GitLabProjectBuiltFromMatchLink(),
        matchlink_data,
        lastupdated=update_tag,
        _sub_resource_label="GitLabOrganization",
        _sub_resource_id=org_url,
    )

    logger.info(f"Loaded {len(matchlink_data)} BUILT_FROM relationships")


@timeit
def cleanup_dockerfile_image_relationships(
    neo4j_session: neo4j.Session,
    org_url: str,
    update_tag: int,
) -> None:
    """
    Clean up stale BUILT_FROM relationships.

    :param neo4j_session: Neo4j session
    :param org_url: The GitLab organization URL (used as sub_resource_id)
    :param update_tag: The update timestamp tag
    """
    logger.info("Cleaning up stale BUILT_FROM relationships...")

    cleanup_job = GraphJob.from_matchlink(
        GitLabProjectBuiltFromMatchLink(),
        "GitLabOrganization",
        org_url,
        update_tag,
    )
    cleanup_job.run(neo4j_session)

    logger.info("Cleanup complete")


# =============================================================================
# Main Sync Entry Point
# =============================================================================


@dataclass
class DockerfileSyncResult:
    """Results from dockerfile sync operation."""

    dockerfiles: list[dict[str, Any]]
    images: list[GitLabContainerImage] | None = None
    matches: list[ImageDockerfileMatch] | None = None

    @property
    def dockerfile_count(self) -> int:
        return len(self.dockerfiles)

    @property
    def image_count(self) -> int:
        return len(self.images) if self.images else 0

    @property
    def match_count(self) -> int:
        return len(self.matches) if self.matches else 0


@timeit
def sync(
    neo4j_session: neo4j.Session,
    gitlab_url: str,
    token: str,
    org_url: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    projects: list[dict[str, Any]],
    match_container_images: bool = True,
    image_limit: int | None = None,
    min_match_confidence: float = 0.5,
) -> DockerfileSyncResult | None:
    """
    Sync Dockerfiles from GitLab projects, query container images, and identify matches.

    This function uses a two-stage matching approach:
    1. PRIMARY: SLSA provenance-based matching (100% confidence from cryptographic attestations)
    2. FALLBACK: Dockerfile command matching (for images without provenance)

    The sync process:
    1. First tries provenance-based matching for images with source_uri from attestations
    2. Searches for Dockerfile-related files in each project
    3. Downloads their content and parses them
    4. Matches remaining images to Dockerfiles based on layer history commands
    5. Creates BUILT_FROM relationships between ImageTag and GitLabProject

    :param neo4j_session: Neo4j session for querying container images
    :param gitlab_url: The GitLab instance URL
    :param token: GitLab API token
    :param org_url: The GitLab organization URL
    :param update_tag: The update timestamp tag
    :param common_job_parameters: Common job parameters
    :param projects: List of project dictionaries to search for Dockerfiles
    :param match_container_images: Whether to query container images and perform matching
    :param image_limit: Optional limit on number of images to process
    :param min_match_confidence: Minimum confidence threshold for matches
    :return: DockerfileSyncResult with dockerfiles, images, and matches, or None if no Dockerfiles found
    """
    logger.info("Starting GitLab dockerfile sync for %d projects", len(projects))

    # ==========================================================================
    # Stage 1: SLSA Provenance-based matching (PRIMARY - highest confidence)
    # ==========================================================================
    # Try provenance-based matching first - this provides 100% confidence from
    # cryptographically signed attestations without needing Dockerfile content.
    provenance_match_count = 0
    if match_container_images:
        provenance_match_count = load_provenance_relationships(
            neo4j_session,
            org_url,
            update_tag,
        )

    # ==========================================================================
    # Stage 2: Dockerfile command matching (FALLBACK)
    # ==========================================================================
    # Search and download Dockerfiles
    dockerfiles = get_dockerfiles_for_projects(gitlab_url, token, projects)

    if not dockerfiles:
        logger.info("No dockerfiles found in GitLab projects")
        # Even with no dockerfiles, we may have provenance matches, so continue
        if provenance_match_count == 0:
            # Cleanup any stale relationships
            if match_container_images:
                cleanup_dockerfile_image_relationships(
                    neo4j_session,
                    org_url,
                    update_tag,
                )
            return None

    images: list[GitLabContainerImage] | None = None
    matches: list[ImageDockerfileMatch] | None = None

    # Query container images and perform dockerfile command matching if requested
    if match_container_images and dockerfiles:
        logger.info("Querying GitLab container images with layer history from Neo4j...")
        images = get_gitlab_container_images_with_history(
            neo4j_session, org_url, limit=image_limit
        )

        if images:
            logger.info(
                "Found %d container images, performing dockerfile matching...",
                len(images),
            )
            matches = match_images_to_dockerfiles(
                images,
                dockerfiles,
                min_confidence=min_match_confidence,
            )

            # Log summary
            high_confidence = sum(1 for m in matches if m.confidence >= 0.75)
            logger.info(
                "Dockerfile matching complete: %d matches found (%d high confidence)",
                len(matches),
                high_confidence,
            )

            # Load BUILT_FROM relationships to Neo4j
            if matches:
                load_dockerfile_image_relationships(
                    neo4j_session,
                    matches,
                    org_url,
                    update_tag,
                )
        else:
            logger.info("No GitLab container images found in Neo4j")

    # Always cleanup stale relationships (covers both provenance and dockerfile matches)
    if match_container_images:
        cleanup_dockerfile_image_relationships(
            neo4j_session,
            org_url,
            update_tag,
        )

    result = DockerfileSyncResult(
        dockerfiles=dockerfiles or [],
        images=images,
        matches=matches,
    )

    logger.info(
        "Completed GitLab dockerfile sync: %d provenance matches, %d dockerfile(s), "
        "%d image(s), %d dockerfile matches",
        provenance_match_count,
        result.dockerfile_count,
        result.image_count,
        result.match_count,
    )
    return result
