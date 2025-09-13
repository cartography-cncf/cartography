import logging
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any

import neo4j

from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.github.util import fetch_page
from cartography.models.github.commits import GitHubUserCommittedToRepoRel
from cartography.util import timeit

logger = logging.getLogger(__name__)


GITHUB_REPO_COMMITS_PAGINATED_GRAPHQL = """
    query($login: String!, $repo: String!, $since: GitTimestamp!, $cursor: String) {
        organization(login: $login) {
            repository(name: $repo) {
                name
                url
                defaultBranchRef {
                    target {
                        ... on Commit {
                            history(first: 100, since: $since, after: $cursor) {
                                pageInfo {
                                    endCursor
                                    hasNextPage
                                }
                                nodes {
                                    committedDate
                                    author {
                                        user {
                                            url
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        rateLimit {
            limit
            cost
            remaining
            resetAt
        }
    }
"""


@timeit
def get_repo_commits(
    token: str,
    api_url: str,
    organization: str,
    repo_name: str,
    since_date: datetime,
) -> list[dict[str, Any]]:
    """
    Retrieve commits from a GitHub repository since a specific date.

    :param token: The Github API token as string.
    :param api_url: The Github v4 API endpoint as string.
    :param organization: The name of the target Github organization as string.
    :param repo_name: The name of the target Github repository as string.
    :param since_date: The datetime to fetch commits since.
    :return: A list of commits from the repository.
    """
    # Convert datetime to ISO format for GraphQL (GitTimestamp requires 'Z' suffix for UTC)
    since_iso = since_date.strftime("%Y-%m-%dT%H:%M:%SZ")

    logger.debug(f"Fetching commits for {organization}/{repo_name} since {since_iso}")

    all_commits = []
    cursor = None
    has_next_page = True

    while has_next_page:
        response = fetch_page(
            token,
            api_url,
            organization,
            GITHUB_REPO_COMMITS_PAGINATED_GRAPHQL,
            cursor,
            repo=repo_name,
            since=since_iso,
        )

        # Navigate to the nested commit history
        repo_data = response.get("data", {}).get("organization", {}).get("repository")
        if not repo_data:
            logger.warning(f"No repository data found for {organization}/{repo_name}")
            break

        default_branch = repo_data.get("defaultBranchRef")
        if not default_branch:
            logger.debug(f"Repository {organization}/{repo_name} has no default branch")
            break

        target = default_branch.get("target")
        if not target:
            logger.debug(
                f"Repository {organization}/{repo_name} default branch has no target"
            )
            break

        history = target.get("history")
        if not history:
            logger.debug(f"Repository {organization}/{repo_name} has no commit history")
            break

        # Add commits from this page
        commits = history.get("nodes", [])
        all_commits.extend(commits)

        # Check pagination
        page_info = history.get("pageInfo", {})
        has_next_page = page_info.get("hasNextPage", False)
        cursor = page_info.get("endCursor")

    return all_commits


def process_repo_commits_batch(
    neo4j_session: neo4j.Session,
    token: str,
    api_url: str,
    organization: str,
    repo_names: list[str],
    update_tag: int,
    lookback_days: int = 30,
    batch_size: int = 10,
) -> None:
    """
    Process repository commits in batches to save memory and API quota.

    :param neo4j_session: Neo4j session for database interface.
    :param token: The Github API token as string.
    :param api_url: The Github v4 API endpoint as string.
    :param organization: The name of the target Github organization as string.
    :param repo_names: List of repository names to process.
    :param update_tag: Timestamp used to determine data freshness.
    :param lookback_days: Number of days to look back for commits.
    :param batch_size: Number of repositories to process in each batch.
    """
    # Calculate lookback date based on configured days
    lookback_date = datetime.now(timezone.utc) - timedelta(days=lookback_days)

    logger.info(f"Processing {len(repo_names)} repositories in batches of {batch_size}")

    # Process repositories in batches
    for i in range(0, len(repo_names), batch_size):
        batch = repo_names[i : i + batch_size]
        logger.info(
            f"Processing batch {i // batch_size + 1}: {len(batch)} repositories"
        )

        # Process each repository in the batch
        batch_relationships = []

        for repo_name in batch:
            try:
                commits = get_repo_commits(
                    token,
                    api_url,
                    organization,
                    repo_name,
                    lookback_date,
                )

                # Transform commits for this single repo immediately
                repo_relationships = transform_single_repo_commits_to_relationships(
                    repo_name,
                    commits,
                    organization,
                )
                batch_relationships.extend(repo_relationships)

                logger.debug(
                    f"Found {len(commits)} commits in {repo_name}, created {len(repo_relationships)} relationships"
                )

            except Exception:
                logger.warning(
                    f"Failed to fetch commits for {repo_name}", exc_info=True
                )
                continue

        # Load this batch of relationships
        if batch_relationships:
            logger.info(f"Loading {len(batch_relationships)} relationships for batch")
            load_github_commit_relationships(
                neo4j_session,
                batch_relationships,
                organization,
                update_tag,
            )

        # Clear memory for next batch
        batch_relationships.clear()


def transform_single_repo_commits_to_relationships(
    repo_name: str,
    commits: list[dict[str, Any]],
    organization: str,
) -> list[dict[str, Any]]:
    """
    Transform commits from a single repository into user-repository relationships.
    Optimized for memory efficiency by processing one repo at a time.

    :param repo_name: The repository name.
    :param commits: List of commit data from the repository.
    :param organization: The Github organization name.
    :return: List of user-repository relationship records for this repo.
    """
    if not commits:
        return []

    repo_url = f"https://github.com/{organization}/{repo_name}"

    # Count commits and track date ranges per user for this repo
    user_commit_data: dict[str, dict[str, Any]] = {}

    for commit in commits:
        # Get user URL from author, skip if not available
        author_user = commit.get("author", {}).get("user")
        if not author_user or not author_user.get("url"):
            continue

        user_url = author_user["url"]
        commit_date = datetime.fromisoformat(
            commit["committedDate"].replace("Z", "+00:00")
        )

        if user_url not in user_commit_data:
            user_commit_data[user_url] = {"commit_count": 0, "commit_dates": []}

        user_commit_data[user_url]["commit_count"] += 1
        user_commit_data[user_url]["commit_dates"].append(commit_date)

    # Transform to relationship records
    relationships = []
    for user_url, data in user_commit_data.items():
        commit_dates = data["commit_dates"]
        relationships.append(
            {
                "user_url": user_url,
                "repo_url": repo_url,
                "commit_count": data["commit_count"],
                "last_commit_date": max(commit_dates).isoformat(),
                "first_commit_date": min(commit_dates).isoformat(),
            }
        )

    return relationships


def transform_commits_to_user_repo_relationships(
    commits_by_repo: dict[str, list[dict[str, Any]]],
    organization: str,
) -> list[dict[str, Any]]:
    """
    Transform commit data into user-repository relationship data.

    :param commits_by_repo: Dict mapping repo names to commit lists.
    :param organization: The Github organization name.
    :return: List of user-repository relationship records.
    """
    logger.info("Transforming commit data into user-repository relationships")

    # Group commits by user and repository
    user_repo_commits: dict[tuple[str, str], list[dict[str, Any]]] = {}

    for repo_name, commits in commits_by_repo.items():
        repo_url = f"https://github.com/{organization}/{repo_name}"

        for commit in commits:
            # Use author if available, otherwise use committer
            commit_user = commit.get("author", {}).get("user") or commit.get(
                "committer", {}
            ).get("user")

            if not commit_user or not commit_user.get("url"):
                continue

            user_url = commit_user["url"]
            key = (user_url, repo_url)

            if key not in user_repo_commits:
                user_repo_commits[key] = []

            user_repo_commits[key].append(commit)

    # Transform to relationship records
    relationships = []
    for (user_url, repo_url), commits in user_repo_commits.items():
        commit_dates = [
            datetime.fromisoformat(commit["committedDate"].replace("Z", "+00:00"))
            for commit in commits
        ]

        relationships.append(
            {
                "user_url": user_url,
                "repo_url": repo_url,
                "commit_count": len(commits),
                "last_commit_date": max(commit_dates).isoformat(),
                "first_commit_date": min(commit_dates).isoformat(),
            }
        )

    logger.info(f"Created {len(relationships)} user-repository relationships")
    return relationships


@timeit
def load_github_commit_relationships(
    neo4j_session: neo4j.Session,
    commit_relationships: list[dict[str, Any]],
    organization: str,
    update_tag: int,
) -> None:
    """
    Load GitHub user-repository commit relationships using MatchLinks.

    :param neo4j_session: Neo4j session for database interface.
    :param commit_relationships: List of user-repository relationship records.
    :param organization: The Github organization name for sub-resource scoping.
    :param update_tag: Timestamp used to determine data freshness.
    """
    if not commit_relationships:
        logger.info("No commit relationships to load")
        return

    logger.info(
        f"Loading {len(commit_relationships)} user-repository commit relationships"
    )

    # Use organization URL as the sub-resource identifier
    org_url = f"https://github.com/{organization}"

    load_matchlinks(
        neo4j_session,
        GitHubUserCommittedToRepoRel(),
        commit_relationships,
        lastupdated=update_tag,
        _sub_resource_label="GitHubOrganization",
        _sub_resource_id=org_url,
    )


@timeit
def cleanup_github_commit_relationships(
    neo4j_session: neo4j.Session,
    organization: str,
    update_tag: int,
) -> None:
    """
    Clean up stale GitHub user-repository commit relationships.

    :param neo4j_session: Neo4j session for database interface.
    :param organization: The Github organization name.
    :param update_tag: Timestamp used to determine data freshness.
    """
    logger.debug("Cleaning up GitHub user-repository commit relationships")

    org_url = f"https://github.com/{organization}"

    GraphJob.from_matchlink(
        GitHubUserCommittedToRepoRel(),
        "GitHubOrganization",
        org_url,
        update_tag,
    ).run(neo4j_session)


@timeit
def sync_github_commits(
    neo4j_session: neo4j.Session,
    token: str,
    api_url: str,
    organization: str,
    repo_names: list[str],
    update_tag: int,
    lookback_days: int = 30,
) -> None:
    """
    Sync GitHub commit relationships for the specified lookback period.
    Uses batch processing to minimize memory usage and API quota consumption.

    :param neo4j_session: Neo4j session for database interface.
    :param token: The Github API token as string.
    :param api_url: The Github v4 API endpoint as string.
    :param organization: The name of the target Github organization as string.
    :param repo_names: List of repository names to sync commits for.
    :param update_tag: Timestamp used to determine data freshness.
    :param lookback_days: Number of days to look back for commits.
    """
    logger.info(f"Starting GitHub commits sync for organization: {organization}")

    # Process repositories in batches to save memory and API quota
    # This approach processes repos in batches, transforms immediately, and loads in batches
    process_repo_commits_batch(
        neo4j_session,
        token,
        api_url,
        organization,
        repo_names,
        update_tag,
        lookback_days=lookback_days,
        batch_size=10,  # Process 10 repos at a time
    )

    # Cleanup stale relationships after all batches are processed
    cleanup_github_commit_relationships(neo4j_session, organization, update_tag)

    logger.info("Completed GitHub commits sync")
