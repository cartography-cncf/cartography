import base64
import json
import logging
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.dockerfile_parser import extract_layer_commands_from_history
from cartography.intel.dockerfile_parser import find_best_dockerfile_matches
from cartography.intel.dockerfile_parser import parse as parse_dockerfile
from cartography.intel.dockerfile_parser import ParsedDockerfile
from cartography.intel.github.util import call_github_rest_api
from cartography.models.github.dockerfile_image import GitHubRepoBuiltFromMatchLink
from cartography.models.github.dockerfile_image import ImageBuiltByWorkflowMatchLink
from cartography.util import timeit

logger = logging.getLogger(__name__)


# =============================================================================
# ECR Image Data Classes
# =============================================================================


@dataclass
class ContainerImage:
    """Represents a container image from the graph (ECR, GCR, etc.)."""

    digest: str
    uri: str
    repo_uri: str
    repo_name: str
    tag: str | None
    layer_diff_ids: list[str]
    image_type: str | None
    architecture: str | None
    os: str | None
    layer_history: list[dict[str, Any]]


@dataclass
class ImageDockerfileMatch:
    """Represents a match between a container registry repository and a Dockerfile."""

    registry_repo_uri: str
    registry_repo_name: str
    dockerfile_repo_url: str | None
    dockerfile_path: str | None
    confidence: float
    matched_commands: int
    total_commands: int
    command_similarity: float


# =============================================================================
# ECR Image Queries
# =============================================================================


def get_container_images_with_history(
    neo4j_session: neo4j.Session,
    limit: int | None = None,
) -> list[ContainerImage]:
    """
    Query the graph to get container images with their metadata AND layer history.

    Uses the generic ontology labels (Image, ImageTag, ImageLayer, ContainerRegistry)
    which work across different registries (ECR, GCR, etc.).

    Returns one image per registry repository (preferring 'latest' tag, then most recently pushed).

    :param neo4j_session: Neo4j session
    :param limit: Optional limit on number of images to return
    :return: List of ContainerImage objects with layer history populated
    """
    # Single query that gets images AND their layer history
    # Uses generic ontology labels: Image, ImageTag, ImageLayer, ContainerRegistry
    query = """
        MATCH (img:Image)<-[:IMAGE]-(repo_img:ImageTag)<-[:REPO_IMAGE]-(repo:ContainerRegistry)
        WHERE img.layer_diff_ids IS NOT NULL
          AND size(img.layer_diff_ids) > 0
        WITH repo, img, repo_img
        ORDER BY
            CASE WHEN repo_img.tag = 'latest' THEN 0 ELSE 1 END,
            repo_img.image_pushed_at DESC
        WITH repo, collect({
            digest: img.digest,
            uri: repo_img.uri,
            repo_uri: repo.uri,
            repo_name: repo.name,
            tag: repo_img.tag,
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
            best.repo_uri AS repo_uri,
            best.repo_name AS repo_name,
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
            ContainerImage(
                digest=record["digest"],
                uri=record["uri"] or "",
                repo_uri=record["repo_uri"] or "",
                repo_name=record["repo_name"] or "",
                tag=record["tag"],
                layer_diff_ids=record["layer_diff_ids"] or [],
                image_type=record["type"],
                architecture=record["architecture"],
                os=record["os"],
                layer_history=layer_history,
            )
        )

    logger.info(
        f"Found {len(images)} container images with layer history (one per repository)"
    )
    return images


# =============================================================================
# Dockerfile Matching
# =============================================================================


def match_images_to_dockerfiles(
    images: list[ContainerImage],
    dockerfiles: list[dict[str, Any]],
    min_confidence: float = 0.5,
) -> list[ImageDockerfileMatch]:
    """
    Match container images to Dockerfiles based on layer history commands.

    :param images: List of container images to match (with layer_history already populated)
    :param dockerfiles: List of dockerfile dictionaries (from get_dockerfiles_for_repos)
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
            logger.debug(f"No layer history for image {image.repo_name}:{image.tag}")
            continue

        # Extract commands from history (no added_layer_count filtering for now)
        image_commands = extract_layer_commands_from_history(image.layer_history)
        if not image_commands:
            logger.debug(
                f"No commands extracted for image {image.repo_name}:{image.tag}"
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
                    registry_repo_uri=image.repo_uri,
                    registry_repo_name=image.repo_name,
                    dockerfile_repo_url=df_info.get("repo_url"),
                    dockerfile_path=df_info.get("path"),
                    confidence=best_match.confidence,
                    matched_commands=best_match.matched_commands,
                    total_commands=best_match.total_commands,
                    command_similarity=best_match.command_similarity,
                )
            )
            logger.debug(
                f"Matched {image.repo_name}:{image.tag} -> {df_info.get('path')} "
                f"(confidence: {best_match.confidence:.2f})"
            )
        else:
            logger.debug(f"No match found for image {image.repo_name}:{image.tag}")

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
            "repo_url": m.dockerfile_repo_url,
            "registry_repo_uri": m.registry_repo_uri,
            "match_method": "dockerfile_analysis",
            "dockerfile_path": m.dockerfile_path,
            "confidence": m.confidence,
            "matched_commands": m.matched_commands,
            "total_commands": m.total_commands,
            "command_similarity": m.command_similarity,
        }
        for m in matches
        if m.dockerfile_repo_url is not None
    ]


@timeit
def load_dockerfile_image_relationships(
    neo4j_session: neo4j.Session,
    matches: list[ImageDockerfileMatch],
    organization: str,
    update_tag: int,
) -> None:
    """
    Load BUILT_FROM relationships between ECRRepositoryImage and GitHubRepository.

    By matching on repo_uri, this creates relationships to ALL images in each
    ECR repository that was built from a Dockerfile in a GitHub repository.

    :param neo4j_session: Neo4j session
    :param matches: List of ImageDockerfileMatch objects
    :param organization: The GitHub organization name (used as sub_resource_id)
    :param update_tag: The update timestamp tag
    """
    if not matches:
        logger.info("No matches to load")
        return

    # Transform matches for MatchLink loading
    matchlink_data = transform_matches_for_matchlink(matches)

    if not matchlink_data:
        logger.info("No valid matches with repo URLs to load")
        return

    logger.info(f"Loading {len(matchlink_data)} BUILT_FROM relationships...")

    load_matchlinks(
        neo4j_session,
        GitHubRepoBuiltFromMatchLink(),
        matchlink_data,
        lastupdated=update_tag,
        _sub_resource_label="GitHubOrganization",
        _sub_resource_id=organization,
    )

    logger.info(f"Loaded {len(matchlink_data)} BUILT_FROM relationships")


@timeit
def cleanup_dockerfile_image_relationships(
    neo4j_session: neo4j.Session,
    organization: str,
    update_tag: int,
) -> None:
    """
    Clean up stale BUILT_FROM relationships.

    :param neo4j_session: Neo4j session
    :param organization: The GitHub organization name (used as sub_resource_id)
    :param update_tag: The update timestamp tag
    """
    logger.info("Cleaning up stale BUILT_FROM relationships...")

    cleanup_job = GraphJob.from_matchlink(
        GitHubRepoBuiltFromMatchLink(),
        "GitHubOrganization",
        organization,
        update_tag,
    )
    cleanup_job.run(neo4j_session)

    logger.info("Cleanup complete")


# =============================================================================
# SLSA Provenance-based Matching (Primary Method)
# =============================================================================


@timeit
def get_provenance_matches_for_org(
    neo4j_session: neo4j.Session,
    organization: str,
) -> list[dict[str, Any]]:
    """
    Query images with SLSA provenance that match GitHub repositories in an organization.

    This is the preferred matching method as it provides 100% confidence based on
    cryptographically signed provenance attestations, without needing Dockerfile
    content analysis.

    Returns data formatted for load_matchlinks with GitHubRepoBuiltFromMatchLink schema.

    :param neo4j_session: Neo4j session
    :param organization: The GitHub organization name to match against
    :return: List of dicts ready for load_matchlinks
    """
    # Query images that have source_uri and match it against GitHubRepository.id
    # The source_uri from SLSA provenance is like "https://github.com/org/repo"
    # which should match GitHubRepository.id
    query = """
        MATCH (img:Image)<-[:IMAGE]-(repo_img:ImageTag)<-[:REPO_IMAGE]-(registry:ContainerRegistry)
        WHERE img.source_uri IS NOT NULL
        MATCH (gh_repo:GitHubRepository)
        WHERE gh_repo.id = img.source_uri
        MATCH (gh_repo)<-[:OWNER]-(gh_org:GitHubOrganization {login: $organization})
        WITH DISTINCT registry.uri AS registry_repo_uri, gh_repo.id AS repo_url
        RETURN registry_repo_uri, repo_url
    """

    result = neo4j_session.run(query, organization=organization)
    matches = []

    for record in result:
        matches.append(
            {
                "registry_repo_uri": record["registry_repo_uri"],
                "repo_url": record["repo_url"],
                "match_method": "provenance",
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
        organization,
    )
    return matches


@timeit
def load_provenance_relationships(
    neo4j_session: neo4j.Session,
    organization: str,
    update_tag: int,
) -> int:
    """
    Load BUILT_FROM relationships based on SLSA provenance data.

    This is the primary matching method - uses provenance attestations to directly
    link container images to their source repositories with 100% confidence.

    :param neo4j_session: Neo4j session
    :param organization: The GitHub organization name
    :param update_tag: The update timestamp tag
    :return: Number of relationships created
    """
    matches = get_provenance_matches_for_org(neo4j_session, organization)

    if not matches:
        logger.info("No provenance-based matches found for %s", organization)
        return 0

    logger.info("Loading %d provenance-based BUILT_FROM relationships...", len(matches))

    load_matchlinks(
        neo4j_session,
        GitHubRepoBuiltFromMatchLink(),
        matches,
        lastupdated=update_tag,
        _sub_resource_label="GitHubOrganization",
        _sub_resource_id=organization,
    )

    logger.info("Loaded %d provenance-based BUILT_FROM relationships", len(matches))
    return len(matches)


@timeit
def get_images_with_workflow_provenance(
    neo4j_session: neo4j.Session,
    organization: str,
) -> list[dict[str, Any]]:
    """
    Query images with SLSA provenance workflow info for a given organization.

    Returns data formatted for load_matchlinks with ImageBuiltByWorkflowMatchLink schema.
    The MatchLink will handle joining to GitHubWorkflow via repo_url + path.

    :param neo4j_session: Neo4j session
    :param organization: The GitHub organization name to filter by
    :return: List of dicts ready for load_matchlinks
    """
    # Query images that have workflow provenance and belong to repos in this org
    query = """
        MATCH (img:Image)
        WHERE img.source_uri IS NOT NULL
          AND img.invocation_workflow IS NOT NULL
        MATCH (gh_repo:GitHubRepository {id: img.source_uri})
              <-[:OWNER]-(gh_org:GitHubOrganization {login: $organization})
        RETURN DISTINCT
            img.digest AS image_digest,
            img.source_uri AS workflow_repo_url,
            img.invocation_workflow AS workflow_path,
            img.invocation_run_number AS run_number
    """

    result = neo4j_session.run(query, organization=organization)
    matches = []

    for record in result:
        matches.append(
            {
                "image_digest": record["image_digest"],
                "workflow_repo_url": record["workflow_repo_url"],
                "workflow_path": record["workflow_path"],
                "run_number": record["run_number"],
            }
        )

    logger.info(
        "Found %d images with workflow provenance for organization %s",
        len(matches),
        organization,
    )
    return matches


@timeit
def load_workflow_relationships(
    neo4j_session: neo4j.Session,
    organization: str,
    update_tag: int,
) -> int:
    """
    Load BUILT_BY relationships between Image and GitHubWorkflow based on SLSA provenance.

    This creates relationships from container images to the GitHub Actions workflows
    that built them, with the run_number as a property.

    :param neo4j_session: Neo4j session
    :param organization: The GitHub organization name
    :param update_tag: The update timestamp tag
    :return: Number of relationships created
    """
    matches = get_images_with_workflow_provenance(neo4j_session, organization)

    if not matches:
        logger.info("No workflow matches found for %s", organization)
        return 0

    logger.info("Loading %d BUILT_BY workflow relationships...", len(matches))

    load_matchlinks(
        neo4j_session,
        ImageBuiltByWorkflowMatchLink(),
        matches,
        lastupdated=update_tag,
        _sub_resource_label="GitHubOrganization",
        _sub_resource_id=organization,
    )

    logger.info("Loaded %d BUILT_BY workflow relationships", len(matches))
    return len(matches)


@timeit
def cleanup_workflow_relationships(
    neo4j_session: neo4j.Session,
    organization: str,
    update_tag: int,
) -> None:
    """
    Clean up stale BUILT_BY workflow relationships.

    :param neo4j_session: Neo4j session
    :param organization: The GitHub organization name (used as sub_resource_id)
    :param update_tag: The update timestamp tag
    """
    logger.debug("Cleaning up stale BUILT_BY workflow relationships...")

    cleanup_job = GraphJob.from_matchlink(
        ImageBuiltByWorkflowMatchLink(),
        "GitHubOrganization",
        organization,
        update_tag,
    )
    cleanup_job.run(neo4j_session)


@timeit
def search_dockerfiles_in_org(
    token: str,
    org: str,
    base_url: str = "https://api.github.com",
) -> list[dict[str, Any]]:
    """
    Search for all Dockerfile-related files in an organization using GitHub Code Search API.

    This performs a single org-wide search instead of per-repo queries, which is more
    efficient and reduces API rate limit consumption.

    The search is case-insensitive and matches files containing "dockerfile" in the name.
    This includes: Dockerfile, dockerfile, DOCKERFILE, Dockerfile.*, *.dockerfile, etc.

    :param token: The GitHub API token
    :param org: The organization name
    :param base_url: The base URL for the GitHub API
    :return: List of file items from the search results (with pagination)
    """
    # GitHub Code Search is case-insensitive by default
    # The filename: qualifier matches files with "dockerfile" anywhere in the name
    query = f"filename:dockerfile org:{org}"

    all_items: list[dict[str, Any]] = []
    page = 1
    max_pages = 10  # GitHub limits to 1000 results (10 pages * 100 per_page)

    while page <= max_pages:
        params = {
            "q": query,
            "per_page": 100,
            "page": page,
        }

        try:
            response = call_github_rest_api("/search/code", token, base_url, params)
            items: list[dict[str, Any]] = response.get("items", [])
            all_items.extend(items)

            # Check if there are more pages
            total_count = response.get("total_count", 0)
            if len(all_items) >= total_count or len(items) < 100:
                break

            page += 1

        except requests.exceptions.HTTPError as e:
            # Only 422 (validation error for empty search results) is acceptable
            # Other errors (403 rate limit, 429 too many requests) should propagate
            if e.response is not None and e.response.status_code == 422:
                logger.debug(
                    "Search validation error for org %s (may have no results): %s",
                    org,
                    e.response.status_code,
                )
                break
            raise

    logger.info(f"Found {len(all_items)} dockerfile(s) in org {org}")
    return all_items


def search_dockerfiles_in_repo(
    token: str,
    owner: str,
    repo: str,
    base_url: str = "https://api.github.com",
) -> list[dict[str, Any]]:
    """
    Search for all Dockerfile-related files in a repository using GitHub Code Search API.

    Note: For multiple repos in the same org, prefer search_dockerfiles_in_org() for efficiency.

    :param token: The GitHub API token
    :param owner: The repository owner (user or organization)
    :param repo: The repository name
    :param base_url: The base URL for the GitHub API
    :return: List of file items from the search results
    """
    query = f"filename:dockerfile repo:{owner}/{repo}"

    params = {
        "q": query,
        "per_page": 100,
    }

    try:
        response = call_github_rest_api("/search/code", token, base_url, params)
        items: list[dict[str, Any]] = response.get("items", [])
        logger.debug(f"Found {len(items)} dockerfile(s) in {owner}/{repo}")
        return items
    except requests.exceptions.HTTPError as e:
        # Only 404 (repo not found) and 422 (validation error) are acceptable
        # 403 (forbidden/rate limit) and 429 (too many requests) should propagate
        if e.response is not None and e.response.status_code in (404, 422):
            logger.debug(
                "Search failed for %s/%s: %d", owner, repo, e.response.status_code
            )
            return []
        raise


def get_file_content(
    token: str,
    owner: str,
    repo: str,
    path: str,
    ref: str = "HEAD",
    base_url: str = "https://api.github.com",
) -> str | None:
    """
    Download the content of a file from a GitHub repository using the Contents API.

    :param token: The GitHub API token
    :param owner: The repository owner
    :param repo: The repository name
    :param path: The path to the file within the repository
    :param ref: The git reference (branch, tag, or commit SHA) to get the file from
    :param base_url: The base URL for the GitHub API
    :return: The file content as a string, or None if retrieval fails
    """
    # URL-encode the path to handle special characters
    endpoint = f"/repos/{owner}/{repo}/contents/{path}"
    params = {"ref": ref}

    try:
        response = call_github_rest_api(endpoint, token, base_url, params)

        # The content is base64 encoded
        if response.get("encoding") == "base64":
            content_b64 = response.get("content", "")
            # GitHub returns content with newlines for readability, remove them
            content_b64 = content_b64.replace("\n", "")
            content = base64.b64decode(content_b64).decode("utf-8")
            return content

        # If not base64 encoded, try to get raw content
        return response.get("content")

    except requests.exceptions.HTTPError as e:
        # 404: File not found, 403: No access, 422: Validation error
        # Note: 429 (rate limit) should propagate to trigger retry/failure
        if e.response is not None and e.response.status_code in (403, 404, 422):
            logger.debug(
                "Cannot fetch file %s/%s/%s: %d",
                owner,
                repo,
                path,
                e.response.status_code,
            )
            return None
        raise


def _extract_repo_info(
    repo: dict[str, Any],
) -> tuple[str | None, str | None, str | None]:
    """Extract owner, repo_name, and repo_url from a repository dict."""
    owner = None
    repo_name = None
    repo_url = None

    if isinstance(repo.get("owner"), dict):
        owner = repo["owner"].get("login")
    elif "nameWithOwner" in repo:
        name_with_owner = repo["nameWithOwner"]
        if "/" in name_with_owner:
            owner = name_with_owner.split("/")[0]

    repo_name = repo.get("name")
    repo_url = repo.get("url")

    return owner, repo_name, repo_url


def _build_dockerfile_info(
    item: dict[str, Any],
    content: str,
    repo_url: str | None,
    full_name: str,
) -> dict[str, Any]:
    """Build dockerfile info dict with parsed content."""
    path = item.get("path", "")

    try:
        parsed = parse_dockerfile(content)
        return {
            "repo_url": repo_url,
            "repo_name": full_name,
            "path": path,
            "content": content,
            "sha": item.get("sha"),
            "html_url": item.get("html_url"),
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
        logger.warning(f"Failed to parse Dockerfile {full_name}/{path}: {e}")
        return {
            "repo_url": repo_url,
            "repo_name": full_name,
            "path": path,
            "content": content,
            "sha": item.get("sha"),
            "html_url": item.get("html_url"),
            "parse_error": str(e),
        }


@timeit
def get_dockerfiles_for_repos(
    token: str,
    repos: list[dict[str, Any]],
    base_url: str = "https://api.github.com",
    org: str | None = None,
) -> list[dict[str, Any]]:
    """
    Search and download Dockerfiles for a list of repositories.

    Uses org-wide search when possible (single API call) instead of per-repo queries.

    :param token: The GitHub API token
    :param repos: List of repository dictionaries (from GitHub API or transformed data)
    :param base_url: The base URL for the GitHub API
    :param org: Organization name for org-wide search. If None, extracted from repos.
    :return: List of dictionaries containing repo info, file path, and content
    """
    if not repos:
        return []

    # Build lookup maps for repos
    repo_info_map: dict[str, tuple[str, str, str | None]] = (
        {}
    )  # full_name -> (owner, name, url)
    orgs_found: set[str] = set()

    for repo in repos:
        owner, repo_name, repo_url = _extract_repo_info(repo)
        if not owner or not repo_name:
            continue
        full_name = f"{owner}/{repo_name}"
        repo_info_map[full_name] = (owner, repo_name, repo_url)
        orgs_found.add(owner)

    if not repo_info_map:
        logger.warning("No valid repositories found")
        return []

    # Determine search strategy
    search_org = org or (orgs_found.pop() if len(orgs_found) == 1 else None)

    all_dockerfiles: list[dict[str, Any]] = []

    if search_org and len(orgs_found) <= 1:
        # Single org: use efficient org-wide search
        logger.info(f"Using org-wide search for {search_org}")
        dockerfile_items = search_dockerfiles_in_org(token, search_org, base_url)

        # Group items by repo
        items_by_repo: dict[str, list[dict[str, Any]]] = {}
        for item in dockerfile_items:
            repo_info = item.get("repository", {})
            full_name = repo_info.get("full_name", "")
            if full_name in repo_info_map:
                items_by_repo.setdefault(full_name, []).append(item)

        # Download content for matching repos
        for full_name, items in items_by_repo.items():
            owner, repo_name, repo_url = repo_info_map[full_name]
            for item in items:
                path = item.get("path")
                if not path:
                    continue
                content = get_file_content(
                    token, owner, repo_name, path, base_url=base_url
                )
                if content:
                    dockerfile_info = _build_dockerfile_info(
                        item, content, repo_url, full_name
                    )
                    all_dockerfiles.append(dockerfile_info)
    else:
        # Multiple orgs or org not specified: fall back to per-repo search
        logger.info(f"Using per-repo search for {len(repo_info_map)} repositories")
        for full_name, (owner, repo_name, repo_url) in repo_info_map.items():
            dockerfile_items = search_dockerfiles_in_repo(
                token, owner, repo_name, base_url
            )
            for item in dockerfile_items:
                path = item.get("path")
                if not path:
                    continue
                content = get_file_content(
                    token, owner, repo_name, path, base_url=base_url
                )
                if content:
                    dockerfile_info = _build_dockerfile_info(
                        item, content, repo_url, full_name
                    )
                    all_dockerfiles.append(dockerfile_info)

    logger.info(
        f"Retrieved {len(all_dockerfiles)} dockerfile(s) from {len(repo_info_map)} repositories"
    )
    return all_dockerfiles


@dataclass
class DockerfileSyncResult:
    """Results from dockerfile sync operation."""

    dockerfiles: list[dict[str, Any]]
    images: list[ContainerImage] | None = None
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

    @property
    def high_confidence_match_count(self) -> int:
        if not self.matches:
            return 0
        return sum(1 for m in self.matches if m.confidence >= 0.75)

    def to_dict(self) -> dict[str, Any]:
        """Convert results to a dictionary for serialization."""
        output: dict[str, Any] = {
            "dockerfiles": self.dockerfiles,
        }

        if self.images is not None:
            output["images"] = [
                {
                    "digest": img.digest,
                    "uri": img.uri,
                    "repo_uri": img.repo_uri,
                    "repo_name": img.repo_name,
                    "tag": img.tag,
                    "layer_count": len(img.layer_diff_ids),
                    "layer_diff_ids": img.layer_diff_ids,
                    "type": img.image_type,
                    "architecture": img.architecture,
                    "os": img.os,
                }
                for img in self.images
            ]

        if self.matches is not None:
            output["matches"] = [
                {
                    "registry_repo_uri": m.registry_repo_uri,
                    "registry_repo_name": m.registry_repo_name,
                    "dockerfile_repo_url": m.dockerfile_repo_url,
                    "dockerfile_path": m.dockerfile_path,
                    "confidence": m.confidence,
                    "matched_commands": m.matched_commands,
                    "total_commands": m.total_commands,
                    "command_similarity": m.command_similarity,
                }
                for m in self.matches
            ]

        output["summary"] = {
            "dockerfile_count": self.dockerfile_count,
            "image_count": self.image_count,
            "match_count": self.match_count,
            "high_confidence_matches": self.high_confidence_match_count,
        }

        return output

    @contextmanager
    def to_tempfile(self) -> Iterator[Path]:
        """
        Context manager that writes results to a temporary JSON file.
        The file is automatically deleted when the context exits.

        Usage:
            with result.to_tempfile() as temp_path:
                print(f"Results at: {temp_path}")
                # Use the file...
            # File is automatically deleted here
        """
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            prefix="github_dockerfiles_",
            delete=False,
            encoding="utf-8",
        ) as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
            temp_path = Path(f.name)

        logger.info(f"Wrote analysis results to {temp_path}")
        try:
            yield temp_path
        finally:
            if temp_path.exists():
                temp_path.unlink()
                logger.debug(f"Cleaned up temp file {temp_path}")


@timeit
def sync(
    neo4j_session: neo4j.Session,
    token: str,
    api_url: str,
    organization: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    repos: list[dict[str, Any]],
    match_container_images: bool = True,
    image_limit: int | None = None,
    min_match_confidence: float = 0.5,
) -> DockerfileSyncResult | None:
    """
    Sync Dockerfiles from GitHub repositories, query container images, and identify matches.

    This function uses a two-stage matching approach:
    1. PRIMARY: SLSA provenance-based matching (100% confidence from cryptographic attestations)
    2. FALLBACK: Dockerfile command matching (for images without provenance)

    The sync process:
    1. First tries provenance-based matching for images with source_uri from attestations
    2. Searches for Dockerfile-related files in each repository
    3. Downloads their content and parses them
    4. Matches remaining images to Dockerfiles based on layer history commands
    5. Creates BUILT_FROM relationships between ImageTag and GitHubRepository

    Works with any container registry that follows the cartography image ontology
    (ECR, GCR, etc.) by using the generic labels: Image, ImageTag, ImageLayer, ContainerRegistry.

    :param neo4j_session: Neo4j session for querying container images
    :param token: The GitHub API token
    :param api_url: The GitHub API URL (typically the GraphQL endpoint)
    :param organization: The GitHub organization name
    :param update_tag: The update timestamp tag
    :param common_job_parameters: Common job parameters
    :param repos: List of repository dictionaries to search for Dockerfiles
    :param match_container_images: Whether to query container images and perform matching (default: True)
    :param image_limit: Optional limit on number of images to process
    :param min_match_confidence: Minimum confidence threshold for matches (default: 0.5)
    :return: DockerfileSyncResult with dockerfiles, images, and matches, or None if no Dockerfiles found

    Example usage:
        result = sync(neo4j_session, token, api_url, org, update_tag, params, repos)
        if result:
            # Access results directly
            print(f"Found {result.dockerfile_count} dockerfiles")

            # Or write to temp file for debugging (auto-cleaned up)
            with result.to_tempfile() as temp_path:
                print(f"Results written to {temp_path}")
    """
    logger.info(
        f"Starting dockerfile sync for {len(repos)} repositories in {organization}"
    )

    # ==========================================================================
    # GET Stage: Collect all data
    # ==========================================================================

    # Extract base REST API URL from the GraphQL URL
    base_url = api_url
    if base_url.endswith("/graphql"):
        base_url = base_url[:-8]

    # GET: Provenance matches (from images already in graph)
    provenance_matches: list[dict[str, Any]] = []
    workflow_matches: list[dict[str, Any]] = []
    if match_container_images:
        provenance_matches = get_provenance_matches_for_org(neo4j_session, organization)
        workflow_matches = get_images_with_workflow_provenance(
            neo4j_session, organization
        )

    # GET: Search and download Dockerfiles (uses org-wide search for efficiency)
    dockerfiles = get_dockerfiles_for_repos(token, repos, base_url, org=organization)

    # GET: Container images for dockerfile matching
    images: list[ContainerImage] | None = None
    if match_container_images and dockerfiles:
        logger.info("Querying container images with layer history from Neo4j...")
        images = get_container_images_with_history(neo4j_session, limit=image_limit)

    # ==========================================================================
    # TRANSFORM Stage: Match images to dockerfiles
    # ==========================================================================
    matches: list[ImageDockerfileMatch] | None = None

    if images and dockerfiles:
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
    elif match_container_images and dockerfiles:
        logger.info("No container images found in Neo4j")

    # ==========================================================================
    # LOAD Stage: Create relationships in Neo4j
    # ==========================================================================
    if match_container_images:
        # Load provenance-based BUILT_FROM relationships
        if provenance_matches:
            logger.info(
                "Loading %d provenance-based BUILT_FROM relationships...",
                len(provenance_matches),
            )
            load_matchlinks(
                neo4j_session,
                GitHubRepoBuiltFromMatchLink(),
                provenance_matches,
                lastupdated=update_tag,
                _sub_resource_label="GitHubOrganization",
                _sub_resource_id=organization,
            )

        # Load workflow BUILT_BY relationships
        if workflow_matches:
            logger.info(
                "Loading %d BUILT_BY workflow relationships...", len(workflow_matches)
            )
            load_matchlinks(
                neo4j_session,
                ImageBuiltByWorkflowMatchLink(),
                workflow_matches,
                lastupdated=update_tag,
                _sub_resource_label="GitHubOrganization",
                _sub_resource_id=organization,
            )

        # Load dockerfile-based BUILT_FROM relationships
        if matches:
            load_dockerfile_image_relationships(
                neo4j_session,
                matches,
                organization,
                update_tag,
            )

    # ==========================================================================
    # CLEANUP Stage: Remove stale relationships
    # ==========================================================================
    # Check if we have any data to justify cleanup
    has_data = bool(dockerfiles or provenance_matches or workflow_matches)
    if not has_data:
        logger.info("No dockerfiles or provenance matches found in %s", organization)
        return None

    # Always cleanup stale relationships (covers both provenance and dockerfile matches)
    if match_container_images:
        cleanup_dockerfile_image_relationships(
            neo4j_session,
            organization,
            update_tag,
        )
        cleanup_workflow_relationships(
            neo4j_session,
            organization,
            update_tag,
        )

    result = DockerfileSyncResult(
        dockerfiles=dockerfiles or [],
        images=images,
        matches=matches,
    )

    logger.info(
        "Completed dockerfile sync: %d provenance matches, %d workflow matches, "
        "%d dockerfile(s), %d image(s), %d dockerfile matches",
        len(provenance_matches),
        len(workflow_matches),
        result.dockerfile_count,
        result.image_count,
        result.match_count,
    )
    return result
