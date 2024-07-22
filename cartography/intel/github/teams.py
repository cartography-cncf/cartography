import logging
from collections import namedtuple
from time import sleep
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
from cartography.util import timeit

logger = logging.getLogger(__name__)

RepoPermission = namedtuple('RepoPermission', ['repo_url', 'permission'])


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
                        repositories(first: 100) {
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

        repo_urls = []
        repo_permissions = []

        max_tries = 5

        for current_try in range(1, max_tries + 1):
            team_repos = _get_team_repos(org, api_url, token, team_name)

            try:
                # The `or []` is because `.nodes` can be None. See:
                # https://docs.github.com/en/graphql/reference/objects#teamrepositoryconnection
                for repo in team_repos.nodes or []:
                    repo_urls.append(repo['url'])

                # The `or []` is because `.edges` can be None.
                for edge in team_repos.edges or []:
                    repo_permissions.append(edge['permission'])
                # We're done! Break out of the retry loop.
                break

            except TypeError:
                # Handles issue #1334
                logger.warning(
                    f"GitHub returned None when trying to find repo or permission data for team {team_name}.",
                    exc_info=True,
                )
                if current_try == max_tries:
                    raise RuntimeError(f"GitHub returned a None repo url for team {team_name}, retries exhausted.")
                sleep(current_try ** 2)

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


def transform_teams(
        team_paginated_data: PaginatedGraphqlData,
        org_data: Dict[str, Any],
        team_repo_data: dict[str, list[RepoPermission]],
) -> list[dict[str, Any]]:
    result = []
    for team in team_paginated_data.nodes:
        team_name = team['slug']
        repo_info = {
            'name': team_name,
            'url': team['url'],
            'description': team['description'],
            'repo_count': team['repositories']['totalCount'],
            'org_url': org_data['url'],
            'org_login': org_data['login'],
        }
        repo_permissions = team_repo_data[team_name]
        if not repo_permissions:
            result.append(repo_info)
            continue

        # `permission` can be one of ADMIN, READ, WRITE, TRIAGE, or MAINTAIN
        for repo_url, permission in repo_permissions:
            repo_info_copy = repo_info.copy()
            repo_info_copy[permission] = repo_url
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
    processed_data = transform_teams(teams_paginated, org_data, team_repos)
    load_team_repos(neo4j_session, processed_data, common_job_parameters['UPDATE_TAG'], org_data['url'])
    common_job_parameters['org_url'] = org_data['url']
    cleanup(neo4j_session, common_job_parameters)
