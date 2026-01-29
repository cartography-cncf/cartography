import base64
import json
import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import neo4j
import requests

from cartography.intel.dockerfile_parser import extract_layer_commands_from_history
from cartography.intel.dockerfile_parser import find_best_dockerfile_matches
from cartography.intel.dockerfile_parser import parse as parse_dockerfile
from cartography.intel.dockerfile_parser import ParsedDockerfile
from cartography.intel.github.util import call_github_rest_api
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
    """Represents a match between an ECR image and a Dockerfile."""

    image_digest: str
    image_uri: str
    image_repo_name: str
    dockerfile_repo_url: str | None
    dockerfile_path: str | None
    confidence: float
    matched_commands: int
    total_commands: int
    command_similarity: float


# =============================================================================
# ECR Image Queries
# =============================================================================


def get_ecr_images(
    neo4j_session: neo4j.Session,
    limit: int | None = None,
) -> list[ECRImage]:
    """
    Query the graph to get ECR images with their metadata.
    Returns one image per repository (preferring 'latest' tag, then most recently pushed).

    :param neo4j_session: Neo4j session
    :param limit: Optional limit on number of images to return
    :return: List of ECRImage objects with layer history
    """
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
        RETURN
            best.digest AS digest,
            best.uri AS uri,
            best.repo_uri AS repo_uri,
            best.repo_name AS repo_name,
            best.tag AS tag,
            best.layer_diff_ids AS layer_diff_ids,
            best.type AS type,
            best.architecture AS architecture,
            best.os AS os
    """

    if limit:
        query += f" LIMIT {limit}"

    result = neo4j_session.run(query)
    images = []

    for record in result:
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
                layer_history=[],  # Will be populated separately
            )
        )

    logger.info(f"Found {len(images)} ECR images (one per repository)")
    return images


def get_image_layer_history(
    neo4j_session: neo4j.Session,
    image_digest: str,
) -> list[dict[str, Any]]:
    """
    Get layer history commands for an image from Neo4j.

    :param neo4j_session: Neo4j session
    :param image_digest: The image digest to get history for
    :return: List of history entries with 'created_by' and 'empty_layer' fields
    """
    query = """
        MATCH (img:ECRImage {digest: $digest})-[:HAS_LAYER]->(layer:ECRImageLayer)
        WITH img, layer
        ORDER BY
            CASE WHEN layer.diff_id IN img.layer_diff_ids
                 THEN apoc.coll.indexOf(img.layer_diff_ids, layer.diff_id)
                 ELSE 9999
            END
        RETURN layer.diff_id AS diff_id, layer.history AS history, layer.is_empty AS is_empty
    """

    try:
        result = neo4j_session.run(query, digest=image_digest)
        history = []
        for record in result:
            history.append(
                {
                    "created_by": record["history"] or "",
                    "empty_layer": record["is_empty"] or False,
                    "diff_id": record["diff_id"],
                }
            )
        return history
    except Exception as e:
        logger.warning(f"Failed to get layer history for {image_digest}: {e}")
        return []


def get_image_base_info(
    neo4j_session: neo4j.Session,
    image_digest: str,
) -> tuple[str | None, list[str] | None]:
    """
    Get base image info from BUILT_FROM relationship.

    :param neo4j_session: Neo4j session
    :param image_digest: The image digest
    :return: (base_digest, base_layer_diff_ids) or (None, None) if not found
    """
    query = """
        MATCH (img:ECRImage {digest: $digest})-[:BUILT_FROM]->(base:ECRImage)
        RETURN base.digest AS base_digest, base.layer_diff_ids AS base_layers
        LIMIT 1
    """

    result = neo4j_session.run(query, digest=image_digest)
    record = result.single()
    if record:
        return record["base_digest"], record["base_layers"]
    return None, None


def compute_added_layer_count(
    image_layers: list[str],
    base_layers: list[str] | None,
) -> int | None:
    """
    Compute how many layers were added on top of the base image.

    :param image_layers: List of layer diff_ids for the image
    :param base_layers: List of layer diff_ids for the base image
    :return: Number of added layers, or None if cannot be determined
    """
    if not base_layers:
        return None

    base_set = set(base_layers)
    added_count = sum(1 for layer in image_layers if layer not in base_set)
    return added_count


# =============================================================================
# Dockerfile Matching
# =============================================================================


def match_images_to_dockerfiles(
    neo4j_session: neo4j.Session,
    images: list[ECRImage],
    dockerfiles: list[dict[str, Any]],
    min_confidence: float = 0.5,
) -> list[ImageDockerfileMatch]:
    """
    Match ECR images to Dockerfiles based on layer history commands.

    :param neo4j_session: Neo4j session
    :param images: List of ECR images to match
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
        # Get layer history from Neo4j
        history = get_image_layer_history(neo4j_session, image.digest)
        if not history:
            logger.debug(f"No layer history for image {image.repo_name}:{image.tag}")
            continue

        # Get base image info to determine added layers
        base_digest, base_layers = get_image_base_info(neo4j_session, image.digest)
        added_layer_count = compute_added_layer_count(image.layer_diff_ids, base_layers)

        # Extract commands from history
        image_commands = extract_layer_commands_from_history(history, added_layer_count)
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
                    image_digest=image.digest,
                    image_uri=image.uri,
                    image_repo_name=image.repo_name,
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


@timeit
def search_dockerfiles_in_repo(
    token: str,
    owner: str,
    repo: str,
    base_url: str = "https://api.github.com",
) -> list[dict[str, Any]]:
    """
    Search for all Dockerfile-related files in a repository using GitHub Code Search API.

    The search is case-insensitive and matches files containing "dockerfile" in the name.
    This includes: Dockerfile, dockerfile, DOCKERFILE, Dockerfile.*, *.dockerfile, etc.

    :param token: The GitHub API token
    :param owner: The repository owner (user or organization)
    :param repo: The repository name
    :param base_url: The base URL for the GitHub API
    :return: List of file items from the search results
    """
    # GitHub Code Search is case-insensitive by default
    # The filename: qualifier matches files with "dockerfile" anywhere in the name
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
        # Handle 403 (rate limit) and 422 (validation error) gracefully
        if e.response is not None and e.response.status_code in (403, 422):
            logger.warning(
                f"Failed to search dockerfiles in {owner}/{repo}: {e.response.status_code} - {e.response.reason}"
            )
            return []
        # Handle 404 (repo not found or not accessible)
        if e.response is not None and e.response.status_code == 404:
            logger.debug(
                f"Repository {owner}/{repo} not found or not accessible for code search"
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


@timeit
def get_dockerfiles_for_repos(
    token: str,
    repos: list[dict[str, Any]],
    base_url: str = "https://api.github.com",
) -> list[dict[str, Any]]:
    """
    Search and download Dockerfiles for a list of repositories.

    :param token: The GitHub API token
    :param repos: List of repository dictionaries (from GitHub API or transformed data)
    :param base_url: The base URL for the GitHub API
    :return: List of dictionaries containing repo info, file path, and content
    """
    all_dockerfiles: list[dict[str, Any]] = []

    for repo in repos:
        # Handle both raw GitHub API response format and transformed format
        # Raw format has owner.login, transformed has different structure
        owner = None
        repo_name = None
        repo_url = None

        # Try to extract owner/repo from different possible formats
        if isinstance(repo.get("owner"), dict):
            owner = repo["owner"].get("login")
        elif "nameWithOwner" in repo:
            name_with_owner = repo["nameWithOwner"]
            if "/" in name_with_owner:
                owner = name_with_owner.split("/")[0]

        repo_name = repo.get("name")
        repo_url = repo.get("url")

        if not owner or not repo_name:
            logger.debug(f"Skipping repo with missing owner or name: {repo}")
            continue

        # Search for Dockerfiles in the repo
        dockerfile_items = search_dockerfiles_in_repo(token, owner, repo_name, base_url)

        for item in dockerfile_items:
            path = item.get("path")
            if not path:
                continue

            # Download the content
            content = get_file_content(token, owner, repo_name, path, base_url=base_url)

            if content:
                # Parse the Dockerfile to extract structured information
                try:
                    parsed = parse_dockerfile(content)
                    dockerfile_info = {
                        "repo_url": repo_url,
                        "repo_name": f"{owner}/{repo_name}",
                        "path": path,
                        "content": content,
                        "sha": item.get("sha"),
                        "html_url": item.get("html_url"),
                        # Parsed information
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
                    logger.warning(
                        f"Failed to parse Dockerfile {owner}/{repo_name}/{path}: {e}"
                    )
                    dockerfile_info = {
                        "repo_url": repo_url,
                        "repo_name": f"{owner}/{repo_name}",
                        "path": path,
                        "content": content,
                        "sha": item.get("sha"),
                        "html_url": item.get("html_url"),
                        "parse_error": str(e),
                    }

                all_dockerfiles.append(dockerfile_info)

    logger.info(
        f"Retrieved content for {len(all_dockerfiles)} dockerfile(s) across {len(repos)} repositories"
    )
    return all_dockerfiles


def write_results_to_tempfile(
    dockerfiles: list[dict[str, Any]],
    images: list[ECRImage] | None = None,
    matches: list[ImageDockerfileMatch] | None = None,
) -> Path:
    """
    Write the analysis results to a temporary JSON file.

    :param dockerfiles: List of dockerfile dictionaries with repo info and content
    :param images: Optional list of ECR images
    :param matches: Optional list of image-to-dockerfile matches
    :return: Path to the created temporary file
    """
    # Create a temp file that won't be deleted on close
    temp_file = Path(tempfile.mktemp(suffix=".json", prefix="github_dockerfiles_"))

    # Build output structure
    output: dict[str, Any] = {
        "dockerfiles": dockerfiles,
    }

    if images is not None:
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
            for img in images
        ]

    if matches is not None:
        output["matches"] = [
            {
                "image_digest": m.image_digest,
                "image_uri": m.image_uri,
                "image_repo_name": m.image_repo_name,
                "dockerfile_repo_url": m.dockerfile_repo_url,
                "dockerfile_path": m.dockerfile_path,
                "confidence": m.confidence,
                "matched_commands": m.matched_commands,
                "total_commands": m.total_commands,
                "command_similarity": m.command_similarity,
            }
            for m in matches
        ]

    # Add summary statistics
    output["summary"] = {
        "dockerfile_count": len(dockerfiles),
        "image_count": len(images) if images else 0,
        "match_count": len(matches) if matches else 0,
        "high_confidence_matches": (
            sum(1 for m in matches if m.confidence >= 0.75) if matches else 0
        ),
    }

    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    logger.info(f"Wrote analysis results to {temp_file}")
    return temp_file


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
) -> Path | None:
    """
    Sync Dockerfiles from GitHub repositories, query ECR images, and identify matches.

    This function:
    1. Searches for Dockerfile-related files in each repository
    2. Downloads their content and parses them
    3. Queries ECR images from Neo4j (most recent tag per repository)
    4. Matches images to Dockerfiles based on layer history commands
    5. Writes all results to a temporary JSON file

    :param neo4j_session: Neo4j session for querying ECR images
    :param token: The GitHub API token
    :param api_url: The GitHub API URL (typically the GraphQL endpoint)
    :param organization: The GitHub organization name
    :param update_tag: The update timestamp tag (unused in current implementation)
    :param common_job_parameters: Common job parameters (unused in current implementation)
    :param repos: List of repository dictionaries to search for Dockerfiles
    :param match_ecr_images: Whether to query ECR images and perform matching (default: True)
    :param image_limit: Optional limit on number of ECR images to process
    :param min_match_confidence: Minimum confidence threshold for matches (default: 0.5)
    :return: Path to the temporary file containing results, or None if no Dockerfiles found
    """
    logger.info(
        f"Starting dockerfile sync for {len(repos)} repositories in {organization}"
    )

    # Extract base REST API URL from the GraphQL URL
    base_url = api_url
    if base_url.endswith("/graphql"):
        base_url = base_url[:-8]

    # Search and download Dockerfiles
    dockerfiles = get_dockerfiles_for_repos(token, repos, base_url)

    if not dockerfiles:
        logger.info(f"No dockerfiles found in {organization}")
        return None

    images: list[ECRImage] | None = None
    matches: list[ImageDockerfileMatch] | None = None

    # Query ECR images and perform matching if requested
    if match_ecr_images:
        logger.info("Querying ECR images from Neo4j...")
        images = get_ecr_images(neo4j_session, limit=image_limit)

        if images:
            logger.info(f"Found {len(images)} ECR images, performing matching...")
            matches = match_images_to_dockerfiles(
                neo4j_session,
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
        else:
            logger.info("No ECR images found in Neo4j")

    # Write results to temp file
    temp_path = write_results_to_tempfile(dockerfiles, images, matches)

    logger.info(
        f"Completed dockerfile sync: {len(dockerfiles)} dockerfile(s), "
        f"{len(images) if images else 0} image(s), "
        f"{len(matches) if matches else 0} match(es) written to {temp_path}"
    )
    return temp_path
