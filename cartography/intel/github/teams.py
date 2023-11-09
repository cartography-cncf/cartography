import logging
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
        team_raw_data: List[Dict[str, Any]],
        org: str,
        api_url: str,
        token: str,
) -> Dict[str, Any]:
    result = {}
    for team in team_raw_data:
        team_name = team['slug']
        repo_count = team['repositories']['totalCount']

        team_repos = _get_team_repos(org, api_url, token, team_name) if repo_count > 0 else None

        # Shape = [(repo_url, 'WRITE'), ...]]
        repo_urls = [t['url'] for t in team_repos.nodes] if team_repos else []
        repo_permissions = [t['permission'] for t in team_repos.edges] if team_repos else []

        result[team_name] = list(zip(repo_urls, repo_permissions))
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
        team_repo_data: Dict[str, Any],
) -> List[Dict[str, Any]]:
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
