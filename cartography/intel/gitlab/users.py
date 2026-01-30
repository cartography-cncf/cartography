"""
GitLab Users Intelligence Module

This module handles syncing of GitLab users and their group memberships.
Users are fetched from the organization and all descendant groups, along with
their access levels and roles.

LIMITATION: This module only syncs CURRENT members of the organization and its groups.
Users who are not current members (e.g., former employees, external contributors who
committed to projects but were never members) are not tracked. Future enhancements
could add commit author tracking to capture these users.
"""

import logging
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gitlab.organizations import get_organization
from cartography.intel.gitlab.util import get_paginated
from cartography.models.gitlab.users import GitLabUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Map GitLab access levels to role names
ACCESS_LEVEL_TO_ROLE = {
    10: "guest",
    20: "reporter",
    30: "developer",
    40: "maintainer",
    50: "owner",
}


def get_group_members(
    gitlab_url: str, token: str, group_id: int
) -> list[dict[str, Any]]:
    """
    Fetch all members for a specific group from GitLab, including inherited members.

    Uses the /groups/:id/members/all endpoint which returns members from ancestor groups.
    If a user is a member of multiple ancestor groups, only the highest access level is returned.
    """
    logger.debug(f"Fetching members for group ID {group_id}")
    members = get_paginated(gitlab_url, token, f"/api/v4/groups/{group_id}/members/all")
    logger.debug(f"Fetched {len(members)} members for group ID {group_id}")
    return members


def get_commits(
    gitlab_url: str, token: str, project_id: int, since_days: int = 90
) -> list[dict[str, Any]]:
    """
    Fetch commits for a specific project from GitLab.

    Uses the /projects/:id/repository/commits endpoint.
    Returns commit data including author name, email, and committed date.

    :param gitlab_url: GitLab instance URL
    :param token: GitLab API token
    :param project_id: Numeric project ID
    :param since_days: Only fetch commits from the last N days. Defaults to 90.
    :return: List of commit dicts
    """
    logger.debug(f"Fetching commits for project ID {project_id}")

    # Calculate the since date
    since_date = datetime.now(timezone.utc) - timedelta(days=since_days)
    extra_params = {"since": since_date.isoformat()}
    logger.debug(
        f"Fetching commits since {since_date.isoformat()} ({since_days} days ago)"
    )

    commits = get_paginated(
        gitlab_url,
        token,
        f"/api/v4/projects/{project_id}/repository/commits",
        extra_params=extra_params,
    )
    logger.debug(f"Fetched {len(commits)} commits for project ID {project_id}")
    return commits


def transform_commit_activity(
    commits_by_project: dict[str, list[dict[str, Any]]],
    users_by_email: dict[str, str],
    users_by_name: dict[str, str],
    user_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Transform commits into user-project commit activity records.

    Groups commits by (author identifier, project) and calculates statistics.
    Takes existing user records and creates new records with commit properties added.

    Matching strategy:
    1. Try to match by author_email first (more accurate)
    2. Fall back to author_name if email not available or not found

    :param commits_by_project: Dict mapping project_url to list of commits
    :param users_by_email: Dict mapping user email to user web_url
    :param users_by_name: Dict mapping user display name to user web_url
    :param user_records: Existing user records with all user properties
    :return: List of commit activity records (user data + commit properties)
    """
    # Build a lookup from web_url to user record for quick access
    users_by_url = {record["web_url"]: record for record in user_records}

    # Aggregate: (user_url, project_url) -> list of commit dates
    activity: dict[tuple[str, str], list[str]] = {}

    # Track matching stats for logging
    email_matches = 0
    name_matches = 0
    no_matches = 0

    for project_url, commits in commits_by_project.items():
        for commit in commits:
            committed_date = commit.get("committed_date")
            author_email = commit.get("author_email")
            author_name = commit.get("author_name")

            if not committed_date:
                continue

            # Try to match user by email first, then fall back to name
            user_url = None
            if author_email and author_email in users_by_email:
                user_url = users_by_email[author_email]
                email_matches += 1
            elif author_name and author_name in users_by_name:
                user_url = users_by_name[author_name]
                name_matches += 1
            else:
                no_matches += 1
                continue

            key = (user_url, project_url)

            if key not in activity:
                activity[key] = []
            activity[key].append(committed_date)

    logger.info(
        f"Commit author matching: {email_matches} by email, "
        f"{name_matches} by name, {no_matches} unmatched"
    )

    # Build records by taking existing user data and adding commit properties
    records = []
    for (user_url, project_url), dates in activity.items():
        # Parse ISO dates to datetime objects for proper timezone-aware comparison
        commit_dates = [
            datetime.fromisoformat(date.replace("Z", "+00:00")) for date in dates
        ]

        # Find the user record (may have multiple if they have group memberships)
        # Just take the first one since we only need the user properties
        base_user_data = users_by_url.get(user_url)
        if not base_user_data:
            logger.warning(
                f"User {user_url} not found in user records, skipping commit activity"
            )
            continue

        # Get min/max dates and convert back to ISO format with Z suffix
        first_date = min(commit_dates).isoformat().replace("+00:00", "Z")
        last_date = max(commit_dates).isoformat().replace("+00:00", "Z")

        # Create new record with user properties + commit properties
        record = {
            **base_user_data,  # Copy all user properties
            "project_url": project_url,
            "commit_count": len(dates),
            "first_commit_date": first_date,
            "last_commit_date": last_date,
        }
        # Remove group relationship properties since this is for commits
        record.pop("group_url", None)
        record.pop("role", None)
        record.pop("access_level", None)

        records.append(record)

    logger.info(f"Transformed {len(records)} user-project commit relationships")
    return records


def transform_users_and_memberships(
    org_members: list[dict[str, Any]],
    group_members_by_group: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """
    Transform raw GitLab user and membership data into the format expected by the schema.

    Returns a list of user records where each record represents a user-group membership.
    For users with multiple group memberships, there will be multiple records with the
    same user data but different group_url/role/access_level.

    For users with no group memberships (org-level only), there will be one record with
    user data but no group relationship fields.
    """
    # Track which users we've seen and their group memberships
    user_memberships: dict[str, list[dict[str, Any]]] = {}

    # Process organization members (these may or may not have group memberships)
    for member in org_members:
        user_url = member.get("web_url")
        username = member.get("username", "")

        if not user_url:
            continue

        # Skip bot users (group/project access tokens)
        # These have usernames like: group_123_bot_abc or project_456_bot_xyz
        if "_bot_" in username:
            logger.debug(f"Skipping bot user: {username}")
            continue

        # Initialize user if not seen before
        if user_url not in user_memberships:
            user_memberships[user_url] = []

    # Process group memberships
    for group_url, members in group_members_by_group.items():
        for member in members:
            user_url = member.get("web_url")
            username = member.get("username", "")

            if not user_url:
                continue

            # Skip bot users (group/project access tokens)
            if "_bot_" in username:
                logger.debug(f"Skipping bot user: {username}")
                continue

            # Initialize user if not seen before
            if user_url not in user_memberships:
                user_memberships[user_url] = []

            # Add group membership
            access_level = member.get("access_level")
            role = (
                ACCESS_LEVEL_TO_ROLE.get(access_level, "unknown")
                if isinstance(access_level, int)
                else "unknown"
            )

            membership = {
                "web_url": user_url,  # User node id
                "username": member.get("username"),
                "name": member.get("name"),
                "state": member.get("state"),
                "email": member.get("email"),
                "is_admin": member.get("is_admin", False),
                "group_url": group_url,  # Target for MEMBER_OF relationship
                "role": role,
                "access_level": access_level,
            }
            user_memberships[user_url].append(membership)

    # Build final records: one record per user-group membership
    records: list[dict[str, Any]] = []
    users_without_groups = 0

    for user_url, memberships in user_memberships.items():
        if memberships:
            # User has group memberships - add one record per membership
            records.extend(memberships)
        else:
            # User has no group memberships - add single record with just user data
            # Find user data from org_members
            user_data = next(
                (m for m in org_members if m.get("web_url") == user_url), None
            )
            if user_data:
                records.append(
                    {
                        "web_url": user_url,  # User node id
                        "username": user_data.get("username"),
                        "name": user_data.get("name"),
                        "state": user_data.get("state"),
                        "email": user_data.get("email"),
                        "is_admin": user_data.get("is_admin", False),
                        # No group_url = no MEMBER_OF relationship created
                    }
                )
                users_without_groups += 1

    total_memberships = len(records) - users_without_groups
    logger.info(
        f"Transformed {len(user_memberships)} unique users: "
        f"{users_without_groups} org-only, {total_memberships} group memberships"
    )
    return records


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    user_records: list[dict[str, Any]],
    org_url: str,
    update_tag: int,
) -> None:
    """
    Load GitLab users and their group memberships into the graph.

    Note: Uses GitLabUserSchema which defines both MEMBER_OF (to groups) and
    COMMITTED_TO (to projects) relationships. Cartography automatically skips
    relationships when the required PropertyRef fields are missing from the data.
    Here, records contain group_url but not project_url, so only MEMBER_OF is created.
    """
    logger.info(f"Loading {len(user_records)} user records for organization {org_url}")
    load(
        neo4j_session,
        GitLabUserSchema(),
        user_records,
        lastupdated=update_tag,
        org_url=org_url,
    )


@timeit
def load_commit_activity(
    neo4j_session: neo4j.Session,
    activity_records: list[dict[str, Any]],
    org_url: str,
    update_tag: int,
) -> None:
    """
    Load GitLab user commit activity into the graph.

    Note: Uses the same GitLabUserSchema as load_users(). Cartography automatically
    skips relationships when the required PropertyRef fields are missing from the data.
    Here, records contain project_url but not group_url, so only COMMITTED_TO is created.
    """
    logger.info(f"Loading {len(activity_records)} commit activity records")
    load(
        neo4j_session,
        GitLabUserSchema(),
        activity_records,
        lastupdated=update_tag,
        org_url=org_url,
    )


@timeit
def cleanup_users(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    org_url: str,
) -> None:
    """
    Remove stale GitLab users from the graph for a specific organization.
    """
    logger.info(f"Running GitLab users cleanup for organization {org_url}")
    cleanup_params = {**common_job_parameters, "org_url": org_url}
    GraphJob.from_node_schema(GitLabUserSchema(), cleanup_params).run(neo4j_session)


@timeit
def sync_gitlab_users(
    neo4j_session: neo4j.Session,
    gitlab_url: str,
    token: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    groups: list[dict[str, Any]],
    projects: list[dict[str, Any]],
    commits_since_days: int = 90,
) -> None:
    """
    Sync GitLab users, their group memberships, and commit activity for a specific organization.

    :param commits_since_days: Number of days of commit history to fetch. Defaults to 90.
    """
    organization_id = common_job_parameters.get("ORGANIZATION_ID")
    if not organization_id:
        raise ValueError("ORGANIZATION_ID must be provided in common_job_parameters")

    logger.info(f"Syncing GitLab users for organization {organization_id}")

    # Fetch the organization to get its URL
    org = get_organization(gitlab_url, token, organization_id)
    org_url: str = org["web_url"]
    org_name: str = org["name"]

    logger.info(f"Syncing users for organization: {org_name} ({org_url})")

    # Fetch organization members
    try:
        org_members = get_group_members(gitlab_url, token, organization_id)
        logger.info(f"Fetched {len(org_members)} members from organization {org_name}")
    except Exception:
        logger.warning(
            f"Failed to fetch members for organization {org_name}", exc_info=True
        )
        org_members = []

    # Fetch members for all descendant groups
    group_members_by_group: dict[str, list[dict[str, Any]]] = {}
    for group in groups:
        group_id = group.get("id")
        group_url = group.get("web_url")
        if not group_id or not group_url:
            continue

        try:
            members = get_group_members(gitlab_url, token, group_id)
            if members:
                group_members_by_group[group_url] = members
                logger.debug(f"Fetched {len(members)} members for group {group_url}")
        except Exception:
            logger.warning(
                f"Failed to fetch members for group {group_url}", exc_info=True
            )
            continue

    logger.info(
        f"Fetched members from {len(group_members_by_group)} groups in {org_name}"
    )

    # Transform users and memberships into records
    user_records = transform_users_and_memberships(org_members, group_members_by_group)

    if not user_records:
        logger.info(f"No users found for organization {org_name}")
        return

    # Load users and their group memberships into Neo4j
    load_users(neo4j_session, user_records, org_url, update_tag)

    # Build email and name mappings for commit author matching
    # Try email first (more accurate), fall back to name
    users_by_email: dict[str, str] = {}
    users_by_name: dict[str, str] = {}

    # Track duplicate names for warning
    duplicate_names: set[str] = set()

    # Collect all members (org + groups) to process
    all_members = list(org_members)
    for members in group_members_by_group.values():
        all_members.extend(members)

    for member in all_members:
        name = member.get("name")
        email = member.get("email")
        web_url = member.get("web_url")
        username = member.get("username", "")

        # Skip bot users
        if "_bot_" in username:
            continue

        # Build email mapping (if email is available)
        if email and web_url:
            users_by_email[email] = web_url

        # Build name mapping (always available as fallback)
        if name and web_url:
            # Check for duplicate names
            if name in users_by_name and users_by_name[name] != web_url:
                duplicate_names.add(name)
            users_by_name[name] = web_url

    # Warn about duplicate names (silent data loss risk)
    if duplicate_names:
        logger.warning(
            f"Found {len(duplicate_names)} users with duplicate display names. "
            "Commit matching by name may be inaccurate for these users. "
            "Email matching will be attempted first."
        )

    logger.info(
        f"Built commit author mappings: {len(users_by_email)} by email, "
        f"{len(users_by_name)} by name"
    )

    # Fetch commits for all projects to build commit activity
    commits_by_project: dict[str, list[dict[str, Any]]] = {}
    for project in projects:
        project_id = project.get("id")
        project_url = project.get("web_url")
        if not project_id or not project_url:
            continue

        try:
            commits = get_commits(gitlab_url, token, project_id, commits_since_days)
            if commits:
                commits_by_project[project_url] = commits
                logger.debug(
                    f"Fetched {len(commits)} commits for project {project_url}"
                )
        except Exception:
            logger.warning(
                f"Failed to fetch commits for project {project_url}", exc_info=True
            )
            continue

    logger.info(f"Fetched commits from {len(commits_by_project)} projects")

    # Transform and load commit activity
    if commits_by_project:
        activity_records = transform_commit_activity(
            commits_by_project, users_by_email, users_by_name, user_records
        )
        if activity_records:
            load_commit_activity(neo4j_session, activity_records, org_url, update_tag)

    logger.info("GitLab users sync completed")
