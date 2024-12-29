import logging
from copy import deepcopy
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.github.util import fetch_all
from cartography.models.github.orgs import GitHubOrganizationSchema
from cartography.models.github.users import GitHubOrganizationUserSchema
from cartography.models.github.users import GitHubUnaffiliatedUserSchema
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


GITHUB_ORG_USERS_PAGINATED_GRAPHQL = """
    query($login: String!, $cursor: String) {
    organization(login: $login)
        {
            url
            login
            membersWithRole(first:100, after: $cursor){
                edges {
                    hasTwoFactorEnabled
                    node {
                        url
                        login
                        name
                        isSiteAdmin
                        email
                        company
                    }
                    role
                }
                pageInfo{
                    endCursor
                    hasNextPage
                }
            }
        }
    }
    """

GITHUB_ENTERPRISE_OWNER_USERS_PAGINATED_GRAPHQL = """
    query($login: String!, $cursor: String) {
    organization(login: $login)
        {
            url
            login
            enterpriseOwners(first:100, after: $cursor){
                edges {
                    node {
                        url
                        login
                        name
                        isSiteAdmin
                        email
                        company
                    }
                    organizationRole
                }
                pageInfo{
                    endCursor
                    hasNextPage
                }
            }
        }
    }
    """


@timeit
def get_users(token: str, api_url: str, organization: str) -> Tuple[List[Dict], Dict]:
    """
    Retrieve a list of users from the given GitHub organization as described in
    https://docs.github.com/en/graphql/reference/objects#organizationmemberedge.
    :param token: The Github API token as string.
    :param api_url: The Github v4 API endpoint as string.
    :param organization: The name of the target Github organization as string.
    :return: A 2-tuple containing
        1. a list of dicts representing users and
        2. data on the owning GitHub organization
        see tests.data.github.users.GITHUB_USER_DATA for shape of both
    """
    logger.info(f"Retrieving users from GitHub organization {organization}")
    users, org = fetch_all(
        token,
        api_url,
        organization,
        GITHUB_ORG_USERS_PAGINATED_GRAPHQL,
        'membersWithRole',
    )
    return users.edges, org


def get_enterprise_owners(token: str, api_url: str, organization: str) -> Tuple[List[Dict], Dict]:
    """
    Retrieve a list of enterprise owners from the given GitHub organization as described in
    https://docs.github.com/en/graphql/reference/objects#organizationenterpriseowneredge.
    :param token: The Github API token as string.
    :param api_url: The Github v4 API endpoint as string.
    :param organization: The name of the target Github organization as string.
    :return: A 2-tuple containing
        1. a list of dicts representing users who are enterprise owners
        3. data on the owning GitHub organization
        see tests.data.github.users.GITHUB_ENTERPRISE_OWNER_DATA for shape
    """
    logger.info(f"Retrieving enterprise owners from GitHub organization {organization}")
    owners, org = fetch_all(
        token,
        api_url,
        organization,
        GITHUB_ENTERPRISE_OWNER_USERS_PAGINATED_GRAPHQL,
        'enterpriseOwners',
    )
    return owners.edges, org


@timeit
def transform_users(user_data: List[Dict], owners_data: List[Dict], org_data: Dict) -> Tuple[List[Dict], List[Dict]]:
    """
    Taking raw user and owner data, return two lists of processed user data:
    * organization users aka affiliated users (users directly affiliated with an organization)
    * unaffiliated users (user who, for example, are enterprise owners but not members of the target organization).

    :param token: The Github API token as string.
    :param api_url: The Github v4 API endpoint as string.
    :param organization: The name of the target Github organization as string.
    :return: A 2-tuple containing
        1. a list of dicts representing users who are affiliated with the target org
           see tests.data.github.users.GITHUB_USER_DATA for shape
        2. a list of dicts representing users who are not affiliated (e.g. enterprise owners who are not also in
           the target org) — see tests.data.github.users.GITHUB_ENTERPRISE_OWNER_DATA for shape
        3. data on the owning GitHub organization
    """

    users_dict = {}
    for user in user_data:
        # all members get the 'MEMBER_OF' relationship
        processed_user = deepcopy(user['node'])
        processed_user['hasTwoFactorEnabled'] = user['hasTwoFactorEnabled']
        processed_user['MEMBER_OF'] = org_data['url']
        # admins get a second relationship expressing them as such
        if user['role'] == 'ADMIN':
            processed_user['ADMIN_OF'] = org_data['url']
        users_dict[processed_user['url']] = processed_user

    owners_dict = {}
    for owner in owners_data:
        processed_owner = deepcopy(owner['node'])
        processed_owner['isEnterpriseOwner'] = True
        if owner['organizationRole'] == 'UNAFFILIATED':
            processed_owner['UNAFFILIATED'] = org_data['url']
        else:
            processed_owner['MEMBER_OF'] = org_data['url']
        owners_dict[processed_owner['url']] = processed_owner

    affiliated_users = []  # users affiliated with the target org
    for url, user in users_dict.items():
        user['isEnterpriseOwner'] = url in owners_dict
        affiliated_users.append(user)

    unaffiliated_users = []  # users not affiliated with the target org
    for url, owner in owners_dict.items():
        if url not in users_dict:
            unaffiliated_users.append(owner)

    return affiliated_users, unaffiliated_users


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    node_schema: GitHubOrganizationUserSchema | GitHubUnaffiliatedUserSchema,
    user_data: List[Dict],
    org_data: Dict,
    update_tag: int,
) -> None:
    logger.info(f"Loading {len(user_data)} GitHub users to the graph")
    load(
        neo4j_session,
        node_schema,
        user_data,
        lastupdated=update_tag,
        org_url=org_data['url'],
    )


@timeit
def load_organization(
    neo4j_session: neo4j.Session,
    node_schema: GitHubOrganizationSchema,
    org_data: List[Dict[str, Any]],
    update_tag: int,
) -> None:
    logger.info(f"Loading {len(org_data)} GitHub organization to the graph")
    load(
        neo4j_session,
        node_schema,
        org_data,
        lastupdated=update_tag,
    )


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]) -> None:
    logger.info("Cleaning up GitHub users")
    GraphJob.from_node_schema(GitHubOrganizationUserSchema(), common_job_parameters).run(neo4j_session)
    GraphJob.from_node_schema(GitHubUnaffiliatedUserSchema(), common_job_parameters).run(neo4j_session)


@timeit
def sync(
        neo4j_session: neo4j.Session,
        common_job_parameters: Dict,
        github_api_key: str,
        github_url: str,
        organization: str,
) -> None:
    logger.info("Syncing GitHub users")
    user_data, org_data = get_users(github_api_key, github_url, organization)
    owners_data, org_data = get_enterprise_owners(github_api_key, github_url, organization)
    processed_affiliated_user_data, processed_unaffiliated_user_data = (
        transform_users(user_data, owners_data, org_data)
    )
    load_organization(
        neo4j_session, GitHubOrganizationSchema(), [org_data],
        common_job_parameters['UPDATE_TAG'],
    )
    load_users(
        neo4j_session, GitHubOrganizationUserSchema(), processed_affiliated_user_data, org_data,
        common_job_parameters['UPDATE_TAG'],
    )
    load_users(
        neo4j_session, GitHubUnaffiliatedUserSchema(), processed_unaffiliated_user_data, org_data,
        common_job_parameters['UPDATE_TAG'],
    )
    cleanup(neo4j_session, common_job_parameters)

    merge_module_sync_metadata(
        neo4j_session,
        group_type='GitHubOrganization',
        group_id=org_data['url'],
        synced_type='GitHubOrganization',
        update_tag=common_job_parameters['UPDATE_TAG'],
        stat_handler=stat_handler,
    )
