import base64
import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.github.util import call_github_rest_api
from cartography.intel.supply_chain import ContainerImage
from cartography.intel.supply_chain import convert_layer_history_records
from cartography.intel.supply_chain import match_images_to_dockerfiles
from cartography.intel.supply_chain import parse_dockerfile_info
from cartography.intel.supply_chain import transform_matches_for_matchlink
from cartography.models.github.packaged_matchlink import (
    GitHubRepoDockerfilePackagedFromMatchLink,
)
from cartography.models.github.packaged_matchlink import (
    GitHubRepoProvenancePackagedFromMatchLink,
)
from cartography.models.github.packaged_matchlink import (
    ImagePackagedByWorkflowMatchLink,
)
from cartography.util import run_analysis_job
from cartography.util import timeit

logger = logging.getLogger(__name__)

_DEFAULT_IMAGE_LIMIT: int | None = None
_DEFAULT_MIN_MATCH_CONFIDENCE: float = 0.5


@timeit
def get_unmatched_container_images_with_history(
    neo4j_session: neo4j.Session,
    organization: str,
    update_tag: int,
    limit: int | None = None,
) -> list[ContainerImage]:
    """
    Query container images not yet matched by provenance in this sync iteration.

    Uses the generic ontology labels (Image, ImageTag, ImageLayer, ContainerRegistry)
    which work across different registries (ECR, GCR, etc.).

    Returns one image per registry repository (preferring 'latest' tag, then most recently pushed).
    Excludes images that:
    - Already have a PACKAGED_FROM created in this sync iteration (by provenance matching)
    - Already claimed by a different GitHub organization (prevents cross-org duplication
      and cleanup issues when orgs don't run at the same time)

    :param neo4j_session: Neo4j session
    :param organization: The GitHub organization name, used for cross-org scoping
    :param update_tag: The current sync update tag
    :param limit: Optional limit on number of images to return
    :return: List of ContainerImage objects with layer history populated
    """
    query = """
        MATCH (img:Image)<-[:IMAGE]-(repo_img:ImageTag)<-[:REPO_IMAGE]-(repo:ContainerRegistry)
        WHERE img.layer_diff_ids IS NOT NULL
          AND size(img.layer_diff_ids) > 0
          AND NOT exists((img)-[:PACKAGED_FROM {lastupdated: $update_tag}]->())
          AND (
              NOT exists((img)-[:PACKAGED_FROM {_sub_resource_label: 'GitHubOrganization'}]->())
              OR exists((img)-[:PACKAGED_FROM {_sub_resource_id: $organization}]->())
          )
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

    result = neo4j_session.run(query, update_tag=update_tag, organization=organization)
    images = []

    for record in result:
        layer_history = convert_layer_history_records(record["layer_history"])

        images.append(
            ContainerImage(
                digest=record["digest"],
                uri=record["uri"] or "",
                registry_id=record["repo_uri"] or None,
                display_name=record["repo_name"] or None,
                tag=record["tag"],
                layer_diff_ids=record["layer_diff_ids"] or [],
                image_type=record["type"],
                architecture=record["architecture"],
                os=record["os"],
                layer_history=layer_history,
            )
        )

    logger.info(
        "Found %d container images with layer history (one per repository)",
        len(images),
    )
    return images


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

    logger.info("Found %d dockerfile(s) in org %s", len(all_items), org)
    return all_items


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
) -> dict[str, Any] | None:
    """Build dockerfile info dict with parsed content."""
    path = item.get("path", "")

    info = parse_dockerfile_info(content, path, full_name)
    if info is None:
        return None
    info["repo_url"] = repo_url
    info["repo_name"] = full_name
    info["sha"] = item.get("sha")
    info["html_url"] = item.get("html_url")
    # Used by the shared matching algorithm
    info["source_repo_id"] = repo_url
    return info


@timeit
def get_dockerfiles_for_repos(
    token: str,
    repos: list[dict[str, Any]],
    org: str,
    base_url: str = "https://api.github.com",
) -> list[dict[str, Any]]:
    """
    Search and download Dockerfiles for a list of repositories using org-wide search.

    :param token: The GitHub API token
    :param repos: List of repository dictionaries (from GitHub API or transformed data)
    :param org: Organization name for org-wide search
    :param base_url: The base URL for the GitHub API
    :return: List of dictionaries containing repo info, file path, and content
    """
    if not repos:
        return []

    repo_info_map: dict[str, tuple[str, str, str | None]] = {}

    for repo in repos:
        owner, repo_name, repo_url = _extract_repo_info(repo)
        if not owner or not repo_name:
            continue
        full_name = f"{owner}/{repo_name}"
        repo_info_map[full_name] = (owner, repo_name, repo_url)

    if not repo_info_map:
        logger.warning("No valid repositories found")
        return []

    dockerfile_items = search_dockerfiles_in_org(token, org, base_url)

    items_by_repo: dict[str, list[dict[str, Any]]] = {}
    for item in dockerfile_items:
        repo_info = item.get("repository", {})
        full_name = repo_info.get("full_name", "")
        if full_name in repo_info_map:
            items_by_repo.setdefault(full_name, []).append(item)

    all_dockerfiles: list[dict[str, Any]] = []
    for full_name, items in items_by_repo.items():
        owner, repo_name, repo_url = repo_info_map[full_name]
        for item in items:
            path = item.get("path")
            if not path:
                continue
            content = get_file_content(token, owner, repo_name, path, base_url=base_url)
            if content:
                dockerfile_info = _build_dockerfile_info(
                    item, content, repo_url, full_name
                )
                if dockerfile_info is not None:
                    all_dockerfiles.append(dockerfile_info)

    logger.info(
        "Retrieved %d dockerfile(s) from %d repositories",
        len(all_dockerfiles),
        len(repo_info_map),
    )
    return all_dockerfiles


@timeit
def sync(
    neo4j_session: neo4j.Session,
    token: str,
    api_url: str,
    organization: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    repos: list[dict[str, Any]],
    workflows: list[dict[str, Any]] | None = None,
    image_limit: int | None = _DEFAULT_IMAGE_LIMIT,
    min_match_confidence: float = _DEFAULT_MIN_MATCH_CONFIDENCE,
) -> None:
    """
    Sync supply chain relationships for a GitHub organization.

    Uses a three-stage matching approach:
    1. PACKAGED_BY: Workflow provenance (Image -> GitHubWorkflow)
    2. PACKAGED_FROM (provenance): SLSA provenance-based matching (100% confidence)
    3. PACKAGED_FROM (dockerfile): Dockerfile command matching for unmatched images

    Only images without an existing PACKAGED_FROM relationship go through the
    expensive Dockerfile analysis step.

    :param neo4j_session: Neo4j session for querying container images
    :param token: The GitHub API token
    :param api_url: The GitHub API URL (typically the GraphQL endpoint)
    :param organization: The GitHub organization name
    :param update_tag: The update timestamp tag
    :param common_job_parameters: Common job parameters
    :param repos: List of repository dictionaries to search for Dockerfiles
    :param workflows: List of workflow dicts (with repo_url and path) from actions sync
    :param image_limit: Optional limit on number of images to process
    :param min_match_confidence: Minimum confidence threshold for matches (default: 0.5)
    """
    logger.info("Starting supply chain sync for %s", organization)

    # Extract base REST API URL from the GraphQL URL
    base_url = api_url
    if base_url.endswith("/graphql"):
        base_url = base_url[:-8]

    # 1. PACKAGED_BY matchlinks (workflow provenance — no pre-query needed)
    workflow_data = [
        {"repo_url": wf["repo_url"], "workflow_path": wf["path"]}
        for wf in (workflows or [])
        if wf.get("repo_url") and wf.get("path")
    ]
    if workflow_data:
        logger.info("Loading PACKAGED_BY for %d workflows", len(workflow_data))
        load_matchlinks(
            neo4j_session,
            ImagePackagedByWorkflowMatchLink(),
            workflow_data,
            lastupdated=update_tag,
            _sub_resource_label="GitHubOrganization",
            _sub_resource_id=organization,
        )

    # 2. PACKAGED_FROM matchlinks (SLSA provenance — no pre-query needed)
    repo_urls = [repo["url"] for repo in repos if repo.get("url")]
    provenance_data = [
        {
            "repo_url": url,
            "match_method": "provenance",
            "dockerfile_path": None,
            "confidence": 1.0,
            "matched_commands": 0,
            "total_commands": 0,
            "command_similarity": 1.0,
        }
        for url in repo_urls
    ]
    if provenance_data:
        logger.info(
            "Loading provenance PACKAGED_FROM for %d repos",
            len(provenance_data),
        )
        load_matchlinks(
            neo4j_session,
            GitHubRepoProvenancePackagedFromMatchLink(),
            provenance_data,
            lastupdated=update_tag,
            _sub_resource_label="GitHubOrganization",
            _sub_resource_id=organization,
        )

    # 3. Get images WITHOUT existing PACKAGED_FROM for dockerfile analysis
    unmatched = get_unmatched_container_images_with_history(
        neo4j_session,
        organization,
        update_tag,
        limit=image_limit,
    )

    # 4. Dockerfile analysis (only for unmatched images)
    if unmatched:
        dockerfiles = get_dockerfiles_for_repos(token, repos, organization, base_url)
        if dockerfiles:
            matches = match_images_to_dockerfiles(
                unmatched,
                dockerfiles,
                min_confidence=min_match_confidence,
            )
            if matches:
                matchlink_data = transform_matches_for_matchlink(
                    matches,
                    "repo_url",
                )
                if matchlink_data:
                    logger.info(
                        "Loading %d dockerfile-based PACKAGED_FROM relationships",
                        len(matchlink_data),
                    )
                    load_matchlinks(
                        neo4j_session,
                        GitHubRepoDockerfilePackagedFromMatchLink(),
                        matchlink_data,
                        lastupdated=update_tag,
                        _sub_resource_label="GitHubOrganization",
                        _sub_resource_id=organization,
                    )

    # 5. Cleanup stale relationships
    GraphJob.from_matchlink(
        ImagePackagedByWorkflowMatchLink(),
        "GitHubOrganization",
        organization,
        update_tag,
    ).run(neo4j_session)

    GraphJob.from_matchlink(
        GitHubRepoProvenancePackagedFromMatchLink(),
        "GitHubOrganization",
        organization,
        update_tag,
    ).run(neo4j_session)

    GraphJob.from_matchlink(
        GitHubRepoDockerfilePackagedFromMatchLink(),
        "GitHubOrganization",
        organization,
        update_tag,
    ).run(neo4j_session)

    # 6. Enrich PACKAGED_FROM with source_file from Image provenance
    run_analysis_job(
        "supply_chain_source_file.json",
        neo4j_session,
        common_job_parameters,
    )

    logger.info("Completed supply chain sync for %s", organization)
