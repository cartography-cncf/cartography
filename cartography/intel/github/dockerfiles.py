import base64
import json
import logging
import tempfile
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
from cartography.models.github.dockerfile_image import GitHubRepoBuiltFromRel
from cartography.util import timeit

logger = logging.getLogger(__name__)


# =============================================================================
# ECR Image Data Classes
# =============================================================================


@dataclass
class ECRImage:
    """Represents an ECR container image from the graph."""

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
    """Represents a match between an ECR repository and a Dockerfile."""

    ecr_repo_uri: str
    ecr_repo_name: str
    dockerfile_repo_url: str | None
    dockerfile_path: str | None
    confidence: float
    matched_commands: int
    total_commands: int
    command_similarity: float


# =============================================================================
# ECR Image Queries
# =============================================================================


def get_ecr_images_with_history(
    neo4j_session: neo4j.Session,
    limit: int | None = None,
) -> list[ECRImage]:
    """
    Query the graph to get ECR images with their metadata AND layer history in a single query.
    Returns one image per repository (preferring 'latest' tag, then most recently pushed).

    :param neo4j_session: Neo4j session
    :param limit: Optional limit on number of images to return
    :return: List of ECRImage objects with layer history populated
    """
    # Single query that gets images AND their layer history
    query = """
        MATCH (img:ECRImage)<-[:IMAGE]-(repo_img:ECRRepositoryImage)<-[:REPO_IMAGE]-(repo:ECRRepository)
        WHERE img.layer_diff_ids IS NOT NULL
          AND size(img.layer_diff_ids) > 0
          AND img.type = 'image'
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
        OPTIONAL MATCH (layer:ECRImageLayer {diff_id: diff_id})
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
            ECRImage(
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

    logger.info(f"Found {len(images)} ECR images with layer history (one per repository)")
    return images


# =============================================================================
# Dockerfile Matching
# =============================================================================


def match_images_to_dockerfiles(
    images: list[ECRImage],
    dockerfiles: list[dict[str, Any]],
    min_confidence: float = 0.5,
) -> list[ImageDockerfileMatch]:
    """
    Match ECR images to Dockerfiles based on layer history commands.

    :param images: List of ECR images to match (with layer_history already populated)
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
                    ecr_repo_uri=image.repo_uri,
                    ecr_repo_name=image.repo_name,
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
            "ecr_repo_uri": m.ecr_repo_uri,
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
        GitHubRepoBuiltFromRel(),
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
        GitHubRepoBuiltFromRel(),
        "GitHubOrganization",
        organization,
        update_tag,
    )
    cleanup_job.run(neo4j_session)

    logger.info("Cleanup complete")


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
            # Handle 403 (rate limit) and 422 (validation error) gracefully
            if e.response is not None and e.response.status_code in (403, 422):
                logger.warning(
                    f"Failed to search dockerfiles in org {org}: "
                    f"{e.response.status_code} - {e.response.reason}"
                )
                break
            raise
        except Exception as e:
            logger.warning(f"Failed to search dockerfiles in org {org}: {e}")
            break

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
        if e.response is not None and e.response.status_code in (403, 404, 422):
            logger.debug(
                f"Search failed for {owner}/{repo}: {e.response.status_code}"
            )
            return []
        raise
    except Exception as e:
        logger.warning(f"Failed to search dockerfiles in {owner}/{repo}: {e}")
        return []


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
        if e.response is not None and e.response.status_code == 404:
            logger.debug(f"File not found: {owner}/{repo}/{path}")
        else:
            logger.warning(f"Failed to get content for {owner}/{repo}/{path}: {e}")
        return None
    except Exception as e:
        logger.warning(f"Failed to get content for {owner}/{repo}/{path}: {e}")
        return None


def _extract_repo_info(repo: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
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
    repo_info_map: dict[str, tuple[str, str, str | None]] = {}  # full_name -> (owner, name, url)
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
                content = get_file_content(token, owner, repo_name, path, base_url=base_url)
                if content:
                    dockerfile_info = _build_dockerfile_info(item, content, repo_url, full_name)
                    all_dockerfiles.append(dockerfile_info)
    else:
        # Multiple orgs or org not specified: fall back to per-repo search
        logger.info(f"Using per-repo search for {len(repo_info_map)} repositories")
        for full_name, (owner, repo_name, repo_url) in repo_info_map.items():
            dockerfile_items = search_dockerfiles_in_repo(token, owner, repo_name, base_url)
            for item in dockerfile_items:
                path = item.get("path")
                if not path:
                    continue
                content = get_file_content(token, owner, repo_name, path, base_url=base_url)
                if content:
                    dockerfile_info = _build_dockerfile_info(item, content, repo_url, full_name)
                    all_dockerfiles.append(dockerfile_info)

    logger.info(
        f"Retrieved {len(all_dockerfiles)} dockerfile(s) from {len(repo_info_map)} repositories"
    )
    return all_dockerfiles


@dataclass
class DockerfileSyncResult:
    """Results from dockerfile sync operation."""

    dockerfiles: list[dict[str, Any]]
    images: list[ECRImage] | None = None
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
                    "ecr_repo_uri": m.ecr_repo_uri,
                    "ecr_repo_name": m.ecr_repo_name,
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
    def to_tempfile(self):
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
    match_ecr_images: bool = True,
    image_limit: int | None = None,
    min_match_confidence: float = 0.5,
) -> DockerfileSyncResult | None:
    """
    Sync Dockerfiles from GitHub repositories, query ECR images, and identify matches.

    This function:
    1. Searches for Dockerfile-related files in each repository
    2. Downloads their content and parses them
    3. Queries ALL ECR images from Neo4j (all tags)
    4. Matches images to Dockerfiles based on layer history commands
    5. Creates BUILT_FROM relationships between ECRRepositoryImage and GitHubRepository

    :param neo4j_session: Neo4j session for querying ECR images
    :param token: The GitHub API token
    :param api_url: The GitHub API URL (typically the GraphQL endpoint)
    :param organization: The GitHub organization name
    :param update_tag: The update timestamp tag
    :param common_job_parameters: Common job parameters
    :param repos: List of repository dictionaries to search for Dockerfiles
    :param match_ecr_images: Whether to query ECR images and perform matching (default: True)
    :param image_limit: Optional limit on number of ECR images to process
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

    # Extract base REST API URL from the GraphQL URL
    base_url = api_url
    if base_url.endswith("/graphql"):
        base_url = base_url[:-8]

    # Search and download Dockerfiles (uses org-wide search for efficiency)
    dockerfiles = get_dockerfiles_for_repos(token, repos, base_url, org=organization)

    if not dockerfiles:
        logger.info(f"No dockerfiles found in {organization}")
        return None

    images: list[ECRImage] | None = None
    matches: list[ImageDockerfileMatch] | None = None

    # Query ECR images and perform matching if requested
    if match_ecr_images:
        logger.info("Querying ECR images with layer history from Neo4j...")
        # Single query gets images AND their layer history
        images = get_ecr_images_with_history(neo4j_session, limit=image_limit)

        if images:
            logger.info(f"Found {len(images)} ECR images, performing matching...")
            matches = match_images_to_dockerfiles(
                images,
                dockerfiles,
                min_confidence=min_match_confidence,
            )

            # Log summary
            high_confidence = sum(1 for m in matches if m.confidence >= 0.75)
            logger.info(
                f"Matching complete: {len(matches)} matches found "
                f"({high_confidence} high confidence)"
            )

            # Load BUILT_FROM relationships to Neo4j
            if matches:
                load_dockerfile_image_relationships(
                    neo4j_session,
                    matches,
                    organization,
                    update_tag,
                )

                # Cleanup stale relationships
                cleanup_dockerfile_image_relationships(
                    neo4j_session,
                    organization,
                    update_tag,
                )
        else:
            logger.info("No ECR images found in Neo4j")

    result = DockerfileSyncResult(
        dockerfiles=dockerfiles,
        images=images,
        matches=matches,
    )

    logger.info(
        f"Completed dockerfile sync: {result.dockerfile_count} dockerfile(s), "
        f"{result.image_count} image(s), {result.match_count} match(es)"
    )
    return result
