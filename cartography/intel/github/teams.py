import logging
from collections import namedtuple
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.github.util import fetch_all
from cartography.intel.github.util import PaginatedGraphqlData
from cartography.models.github.teams import GitHubTeamSchema
from cartography.util import retries_with_backoff
from cartography.util import timeit

logger = logging.getLogger(__name__)

# A team's permission on a repo: https://docs.github.com/en/graphql/reference/enums#repositorypermission
RepoPermission = namedtuple('RepoPermission', ['repo_url', 'permission'])
# A team member's role: https://docs.github.com/en/graphql/reference/enums#teammemberrole
UserRole = namedtuple('UserRole', ['user_url', 'role'])
# Unlike the other tuples here, there is no qualification (like 'role' or 'permission') to the relationship.
# A child team is just a child team: https://docs.github.com/en/graphql/reference/objects#teamconnection
ChildTeam = namedtuple('ChildTeam', ['team_url'])


def backoff_handler(details: Dict) -> None:
    """
    Custom backoff handler for GitHub calls in this module.
    """
    team_name = details['kwargs'].get('team_name') or 'not present in kwargs'
    updated_details = {**details, 'team_name': team_name}
    logger.warning(
        "Backing off {wait:0.1f} seconds after {tries} tries. Calling function {target} for team {team_name}"
        .format(**updated_details),
    )


@timeit
def get_teams(org: str, api_url: str, token: str) -> Tuple[PaginatedGraphqlData, Dict[str, Any]]:
    org_teams_gql = """
        query($login: String!, $cursor: String) {
            organization(login: $login) {
                login
                url
                teams(first:100, after: $cursor) {
                    nodes {
                        slug
                        url
                        description
                        repositories {
                            totalCount
                        }
                        members(membership: IMMEDIATE) {
                            totalCount
                        }
                        childTeams {
                            totalCount
                        }
                    }
                    pageInfo{
                        endCursor
                        hasNextPage
                    }
                }
            }
        }
    """
    return fetch_all(token, api_url, org, org_teams_gql, 'teams')


def _get_teams_repos_inner_func(
        org: str,
        api_url: str,
        token: str,
        team_name: str,
        repo_urls: list[str],
        repo_permissions: list[str],
) -> None:
    logger.info(f"Loading team repos for {team_name}.")
    team_repos = _get_team_repos(org, api_url, token, team_name)

    # The `or []` is because `.nodes` can be None. See:
    # https://docs.github.com/en/graphql/reference/objects#teamrepositoryconnection
    for repo in team_repos.nodes or []:
        repo_urls.append(repo['url'])
    # The `or []` is because `.edges` can be None.
    for edge in team_repos.edges or []:
        repo_permissions.append(edge['permission'])


@timeit
def _get_team_repos_for_multiple_teams(
        team_raw_data: list[dict[str, Any]],
        org: str,
        api_url: str,
        token: str,
) -> dict[str, list[RepoPermission]]:
    result: dict[str, list[RepoPermission]] = {}
    for team in team_raw_data:
        team_name = team['slug']
        repo_count = team['repositories']['totalCount']

        if repo_count == 0:
            # This team has access to no repos so let's move on
            result[team_name] = []
            continue

        repo_urls: List[str] = []
        repo_permissions: List[str] = []

        retries_with_backoff(
            _get_teams_repos_inner_func,
            TypeError,
            5,
            backoff_handler,
        )(
            org=org,
            api_url=api_url,
            token=token,
            team_name=team_name,
            repo_urls=repo_urls,
            repo_permissions=repo_permissions,
        )
        # Shape = [(repo_url, 'WRITE'), ...]]
        result[team_name] = [RepoPermission(url, perm) for url, perm in zip(repo_urls, repo_permissions)]
    return result


@timeit
def _get_team_repos(org: str, api_url: str, token: str, team: str) -> PaginatedGraphqlData:
    team_repos_gql = """
    query($login: String!, $team: String!, $cursor: String) {
        organization(login: $login) {
            url
            login
            team(slug: $team) {
                slug
                repositories(first:100, after: $cursor) {
                    edges {
                        permission
                    }
                    nodes {
                        url
                    }
                    pageInfo {
                        endCursor
                        hasNextPage
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
    team_repos, _ = fetch_all(
        token,
        api_url,
        org,
        team_repos_gql,
        'team',
        resource_inner_type='repositories',
        team=team,
    )
    return team_repos


def _get_teams_users_inner_func(
        org: str, api_url: str, token: str, team_name: str,
        user_urls: List[str], user_roles: List[str],
) -> None:
    logger.info(f"Loading team users for {team_name}.")
    team_users = _get_team_users(org, api_url, token, team_name)
    # The `or []` is because `.nodes` can be None. See:
    # https://docs.github.com/en/graphql/reference/objects#teammemberconnection
    for user in team_users.nodes or []:
        user_urls.append(user['url'])
    # The `or []` is because `.edges` can be None.
    for edge in team_users.edges or []:
        user_roles.append(edge['role'])


def _get_team_users_for_multiple_teams(
        team_raw_data: list[dict[str, Any]],
        org: str,
        api_url: str,
        token: str,
) -> dict[str, list[UserRole]]:
    result: dict[str, list[UserRole]] = {}
    for team in team_raw_data:
        team_name = team['slug']
        user_count = team['members']['totalCount']

        if user_count == 0:
            # This team has no users so let's move on
            result[team_name] = []
            continue

        user_urls: List[str] = []
        user_roles: List[str] = []

        retries_with_backoff(_get_teams_users_inner_func, TypeError, 5, backoff_handler)(
            org=org, api_url=api_url, token=token, team_name=team_name, user_urls=user_urls, user_roles=user_roles,
        )

        # Shape = [(user_url, 'MAINTAINER'), ...]]
        result[team_name] = [UserRole(url, role) for url, role in zip(user_urls, user_roles)]
    return result


@timeit
def _get_team_users(org: str, api_url: str, token: str, team: str) -> PaginatedGraphqlData:
    team_users_gql = """
    query($login: String!, $team: String!, $cursor: String) {
        organization(login: $login) {
            url
            login
            team(slug: $team) {
                slug
                members(first: 100, after: $cursor, membership: IMMEDIATE) {
                    totalCount
                    nodes {
                        url
                    }
                    edges {
                        role
                    }
                    pageInfo {
                        endCursor
                        hasNextPage
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
    team_users, _ = fetch_all(
        token,
        api_url,
        org,
        team_users_gql,
        'team',
        resource_inner_type='members',
        team=team,
    )
    return team_users


def _get_child_teams_inner_func(
        org: str, api_url: str, token: str, team_name: str, team_urls: List[str],
) -> None:
    logger.info(f"Loading child teams for {team_name}.")
    child_teams = _get_child_teams(org, api_url, token, team_name)
    # The `or []` is because `.nodes` can be None. See:
    # https://docs.github.com/en/graphql/reference/objects#teammemberconnection
    for cteam in child_teams.nodes or []:
        team_urls.append(cteam['url'])
    # No edges to process here, the GitHub response for child teams has no relevant info in edges.


def _get_child_teams_for_multiple_teams(
        team_raw_data: list[dict[str, Any]],
        org: str,
        api_url: str,
        token: str,
) -> dict[str, list[ChildTeam]]:
    result: dict[str, list[ChildTeam]] = {}
    for team in team_raw_data:
        team_name = team['slug']
        team_count = team['childTeams']['totalCount']

        if team_count == 0:
            # This team has no child teams so let's move on
            result[team_name] = []
            continue

        team_urls: List[str] = []

        retries_with_backoff(_get_child_teams_inner_func, TypeError, 5, backoff_handler)(
            org=org, api_url=api_url, token=token, team_name=team_name, team_urls=team_urls,
        )

        result[team_name] = [ChildTeam(url) for url in team_urls]
    return result


def _get_child_teams(org: str, api_url: str, token: str, team: str) -> PaginatedGraphqlData:
    team_users_gql = """
    query($login: String!, $team: String!, $cursor: String) {
        organization(login: $login) {
            url
            login
            team(slug: $team) {
                slug
                childTeams(first: 100, after: $cursor) {
                    totalCount
                    nodes {
                        url
                    }
                    pageInfo {
                        endCursor
                        hasNextPage
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
    team_users, _ = fetch_all(
        token,
        api_url,
        org,
        team_users_gql,
        'team',
        resource_inner_type='childTeams',
        team=team,
    )
    return team_users


def transform_teams(
        team_paginated_data: PaginatedGraphqlData,
        org_data: Dict[str, Any],
        team_repo_data: dict[str, list[RepoPermission]],
        team_user_data: dict[str, list[UserRole]],
        team_child_team_data: dict[str, list[ChildTeam]],
) -> list[dict[str, Any]]:
    result = []
    for team in team_paginated_data.nodes:
        team_name = team['slug']
        repo_info = {
            'name': team_name,
            'url': team['url'],
            'description': team['description'],
            'repo_count': team['repositories']['totalCount'],
            'member_count': team['members']['totalCount'],
            'child_team_count': team['childTeams']['totalCount'],
            'org_url': org_data['url'],
            'org_login': org_data['login'],
        }
        repo_permissions = team_repo_data[team_name]
        user_roles = team_user_data[team_name]
        child_teams = team_child_team_data[team_name]

        if not repo_permissions and not user_roles and not child_teams:
            result.append(repo_info)
            continue

        if repo_permissions:
            # `permission` can be one of ADMIN, READ, WRITE, TRIAGE, or MAINTAIN
            for repo_url, permission in repo_permissions:
                repo_info_copy = repo_info.copy()
                repo_info_copy[permission] = repo_url
                result.append(repo_info_copy)
        if user_roles:
            # `role` can be one of MAINTAINER, MEMBER
            for user_url, role in user_roles:
                repo_info_copy = repo_info.copy()
                repo_info_copy[role] = user_url
                result.append(repo_info_copy)
        if child_teams:
            for (team_url,) in child_teams:
                repo_info_copy = repo_info.copy()
                # GitHub speaks of team-team relationships as 'child teams', as in the graphql query
                # or here: https://docs.github.com/en/graphql/reference/enums#teammembershiptype
                # We label the relationship as 'MEMBER_OF_TEAM' here because it is in line with
                # other similar relationships in Cartography.
                repo_info_copy['MEMBER_OF_TEAM'] = team_url
                result.append(repo_info_copy)
    return result


@timeit
def load_team_repos(
        neo4j_session: neo4j.Session,
        data: List[Dict[str, Any]],
        update_tag: int,
        organization_url: str,
) -> None:
    logger.info(f"Loading {len(data)} GitHub team-repos to the graph")
    load(
        neo4j_session,
        GitHubTeamSchema(),
        data,
        lastupdated=update_tag,
        org_url=organization_url,
    )


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    GraphJob.from_node_schema(GitHubTeamSchema(), common_job_parameters).run(neo4j_session)


@timeit
def sync_github_teams(
        neo4j_session: neo4j.Session,
        common_job_parameters: Dict[str, Any],
        github_api_key: str,
        github_url: str,
        organization: str,
) -> None:
    teams_paginated, org_data = get_teams(organization, github_url, github_api_key)
    team_repos = _get_team_repos_for_multiple_teams(teams_paginated.nodes, organization, github_url, github_api_key)
    team_users = _get_team_users_for_multiple_teams(teams_paginated.nodes, organization, github_url, github_api_key)
    team_children = _get_child_teams_for_multiple_teams(teams_paginated.nodes, organization, github_url, github_api_key)
    processed_data = transform_teams(teams_paginated, org_data, team_repos, team_users, team_children)
    load_team_repos(neo4j_session, processed_data, common_job_parameters['UPDATE_TAG'], org_data['url'])
    common_job_parameters['org_url'] = org_data['url']
    cleanup(neo4j_session, common_job_parameters)
