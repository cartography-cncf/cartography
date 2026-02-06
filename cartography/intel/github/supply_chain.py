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
from cartography.models.github.packaged_matchlink import GitHubRepoPackagedFromMatchLink
from cartography.models.github.packaged_matchlink import (
    ImagePackagedByWorkflowMatchLink,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


def get_unmatched_container_images_with_history(
    neo4j_session: neo4j.Session,
    limit: int | None = None,
) -> list[ContainerImage]:
    """
    Query container images that don't yet have a PACKAGED_FROM relationship.

    Uses the generic ontology labels (Image, ImageTag, ImageLayer, ContainerRegistry)
    which work across different registries (ECR, GCR, etc.).

    Returns one image per registry repository (preferring 'latest' tag, then most recently pushed).
    Excludes images that already have a PACKAGED_FROM relationship (e.g. from provenance matching).

    :param neo4j_session: Neo4j session
    :param limit: Optional limit on number of images to return
    :return: List of ContainerImage objects with layer history populated
    """
    query = """
        MATCH (img:Image)<-[:IMAGE]-(repo_img:ImageTag)<-[:REPO_IMAGE]-(repo:ContainerRegistry)
        WHERE img.layer_diff_ids IS NOT NULL
          AND size(img.layer_diff_ids) > 0
          AND NOT exists((repo_img)-[:PACKAGED_FROM]->())
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
        f"Found {len(images)} container images with layer history (one per repository)"
    )
    return images


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

    Returns data formatted for load_matchlinks with GitHubRepoPackagedFromMatchLink schema.

    :param neo4j_session: Neo4j session
    :param organization: The GitHub organization name to match against
    :return: List of dicts ready for load_matchlinks
    """
    query = """
        MATCH (img:Image)<-[:IMAGE]-(repo_img:ImageTag)<-[:REPO_IMAGE]-(registry:ContainerRegistry)
        WHERE img.source_uri IS NOT NULL
        MATCH (gh_repo:GitHubRepository)
        WHERE gh_repo.id = img.source_uri
        MATCH (gh_repo)-[:OWNER]->(gh_org:GitHubOrganization {username: $organization})
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
                "dockerfile_path": None,
                "confidence": 1.0,
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
def get_images_with_workflow_provenance(
    neo4j_session: neo4j.Session,
    organization: str,
) -> list[dict[str, Any]]:
    """
    Query images with SLSA provenance workflow info for a given organization.

    Returns data formatted for load_matchlinks with ImagePackagedByWorkflowMatchLink schema.
    The MatchLink will handle joining to GitHubWorkflow via repo_url + path.

    :param neo4j_session: Neo4j session
    :param organization: The GitHub organization name to filter by
    :return: List of dicts ready for load_matchlinks
    """
    query = """
        MATCH (img:Image)
        WHERE img.source_uri IS NOT NULL
          AND img.invocation_workflow IS NOT NULL
        MATCH (gh_repo:GitHubRepository {id: img.source_uri})
              -[:OWNER]->(gh_org:GitHubOrganization {username: $organization})
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
                    if dockerfile_info is not None:
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
                    if dockerfile_info is not None:
                        all_dockerfiles.append(dockerfile_info)

    logger.info(
        f"Retrieved {len(all_dockerfiles)} dockerfile(s) from {len(repo_info_map)} repositories"
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
    image_limit: int | None = None,
    min_match_confidence: float = 0.5,
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
    :param image_limit: Optional limit on number of images to process
    :param min_match_confidence: Minimum confidence threshold for matches (default: 0.5)
    """
    logger.info("Starting supply chain sync for %s", organization)

    # Extract base REST API URL from the GraphQL URL
    base_url = api_url
    if base_url.endswith("/graphql"):
        base_url = base_url[:-8]

    # 1. PACKAGED_BY matchlinks (workflow provenance)
    workflow_data = get_images_with_workflow_provenance(neo4j_session, organization)
    if workflow_data:
        logger.info("Loading %d PACKAGED_BY workflow relationships", len(workflow_data))
        load_matchlinks(
            neo4j_session,
            ImagePackagedByWorkflowMatchLink(),
            workflow_data,
            lastupdated=update_tag,
            _sub_resource_label="GitHubOrganization",
            _sub_resource_id=organization,
        )

    # 2. PACKAGED_FROM matchlinks (SLSA provenance)
    provenance_data = get_provenance_matches_for_org(neo4j_session, organization)
    if provenance_data:
        logger.info(
            "Loading %d provenance-based PACKAGED_FROM relationships",
            len(provenance_data),
        )
        load_matchlinks(
            neo4j_session,
            GitHubRepoPackagedFromMatchLink(),
            provenance_data,
            lastupdated=update_tag,
            _sub_resource_label="GitHubOrganization",
            _sub_resource_id=organization,
        )

    # 3. Get images WITHOUT existing PACKAGED_FROM for dockerfile analysis
    unmatched = get_unmatched_container_images_with_history(
        neo4j_session,
        limit=image_limit,
    )

    # 4. Dockerfile analysis (only for unmatched images)
    if unmatched:
        dockerfiles = get_dockerfiles_for_repos(
            token, repos, base_url, org=organization
        )
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
                    "registry_repo_uri",
                )
                if matchlink_data:
                    logger.info(
                        "Loading %d dockerfile-based PACKAGED_FROM relationships",
                        len(matchlink_data),
                    )
                    load_matchlinks(
                        neo4j_session,
                        GitHubRepoPackagedFromMatchLink(),
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
        GitHubRepoPackagedFromMatchLink(),
        "GitHubOrganization",
        organization,
        update_tag,
    ).run(neo4j_session)

    logger.info("Completed supply chain sync for %s", organization)
