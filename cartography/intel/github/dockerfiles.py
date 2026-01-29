import base64
import json
import logging
import tempfile
from pathlib import Path
from typing import Any

import neo4j
import requests

from cartography.intel.github.util import call_github_rest_api
from cartography.util import timeit

logger = logging.getLogger(__name__)


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
                all_dockerfiles.append(
                    {
                        "repo_url": repo_url,
                        "repo_name": f"{owner}/{repo_name}",
                        "path": path,
                        "content": content,
                        "sha": item.get("sha"),
                        "html_url": item.get("html_url"),
                    }
                )

    logger.info(
        f"Retrieved content for {len(all_dockerfiles)} dockerfile(s) across {len(repos)} repositories"
    )
    return all_dockerfiles


def write_dockerfiles_to_tempfile(dockerfiles: list[dict[str, Any]]) -> Path:
    """
    Write the collected Dockerfiles to a temporary JSON file.

    :param dockerfiles: List of dockerfile dictionaries with repo info and content
    :return: Path to the created temporary file
    """
    # Create a temp file that won't be deleted on close
    temp_file = Path(tempfile.mktemp(suffix=".json", prefix="github_dockerfiles_"))

    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(dockerfiles, f, indent=2, ensure_ascii=False)

    logger.info(f"Wrote {len(dockerfiles)} dockerfile(s) to {temp_file}")
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
) -> Path | None:
    """
    Sync Dockerfiles from GitHub repositories: search, download, and write to a temp file.

    This function searches for Dockerfile-related files in each repository,
    downloads their content, and writes the results to a temporary JSON file
    for later analysis.

    :param neo4j_session: Neo4j session (unused in current implementation but kept for consistency)
    :param token: The GitHub API token
    :param api_url: The GitHub API URL (typically the GraphQL endpoint)
    :param organization: The GitHub organization name
    :param update_tag: The update timestamp tag (unused in current implementation)
    :param common_job_parameters: Common job parameters (unused in current implementation)
    :param repos: List of repository dictionaries to search for Dockerfiles
    :return: Path to the temporary file containing Dockerfiles, or None if no Dockerfiles found
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

    # Write to temp file
    temp_path = write_dockerfiles_to_tempfile(dockerfiles)

    logger.info(
        f"Completed dockerfile sync: {len(dockerfiles)} file(s) written to {temp_path}"
    )
    return temp_path
