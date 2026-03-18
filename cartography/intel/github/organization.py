import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import neo4j

from cartography.intel.github.util import call_github_api
from cartography.intel.github.util import fetch_all
from cartography.intel.github.util import fetch_page
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


GITHUB_ORG_GRAPHQL = """
    query($login: String!) {
    organization(login: $login)
        {
            url
            login
            email
            id
            name
            description
            createdAt
            isVerified
            location
            requiresTwoFactorAuthentication
            websiteUrl
        }
    }
    """


@timeit
def get_organization(token: str, api_url: str, organization: str) -> Dict:
    """
    Retrieve GitHub organization Info as described in
    https://docs.github.com/en/graphql/reference/objects#organization.
    :param token: The Github API token as string.
    :param api_url: The Github v4 API endpoint as string.
    :param organization: The name of the target Github organization as string.
    :return: A dictionary of the GitHub organization.
    """
    org = fetch_page(token, api_url, organization, GITHUB_ORG_GRAPHQL)
    return org.get('data', {}).get('organization', {})


@timeit
def load_organization(
    neo4j_session: neo4j.Session, org_data: Dict,
    common_job_parameters: Dict[str, Any],
) -> None:
    query = """
    MERGE (org:GitHubOrganization{id: $OrgLogin})
    ON CREATE SET org.firstseen = timestamp()
    SET org.username = $OrgLogin,
    org.url = $OrgUrl,
    org.email = $OrgEmail,
    org.orgid = $OrgId,
    org.name = $OrgName,
    org.description = $OrgDescription,
    org.createdat = $OrgCreatedAt,
    org.isverified = $OrgIsVerified,
    org.location = $OrgLocation,
    org.websiteurl = $OrgWebsiteUrl,
    org.requirestwofactorauthentication = $OrgRequiresTwoFactorAuthentication,
    org.lastupdated = $UpdateTag
    WITH org

    match (owner:CloudanixWorkspace{id:$workspace_id})
    merge (org)<-[o:OWNER]-(owner)
    ON CREATE SET o.firstseen = timestamp()
    SET o.lastupdated = $UpdateTag;
    """
    neo4j_session.run(
        query,
        OrgLogin=org_data['login'],
        OrgUrl=org_data['url'],
        OrgEmail=org_data['email'],
        OrgId=org_data['id'],
        OrgName=org_data['name'],
        OrgDescription=org_data['description'],
        OrgCreatedAt=org_data['createdAt'],
        OrgIsVerified=org_data['isVerified'],
        OrgLocation=org_data['location'],
        OrgWebsiteUrl=org_data['websiteUrl'],
        OrgRequiresTwoFactorAuthentication=org_data.get('requiresTwoFactorAuthentication'),
        UpdateTag=common_job_parameters['UPDATE_TAG'],
        workspace_id=common_job_parameters['WORKSPACE_ID'],
    )


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('github_organization_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
        neo4j_session: neo4j.Session,
        github_api_key: str,
        github_org: str,
        github_url: str,
        common_job_parameters: Dict[str, Any],
) -> None:
    logger.info("Syncing GitHub Organization")

    org_data = get_organization(github_api_key, github_url, github_org)

    # Cartography supports Organizations only. No individual accounts.
    # Handle non-org based ingestion
    if org_data:
        load_organization(neo4j_session, org_data, common_job_parameters)

    cleanup(neo4j_session, common_job_parameters)
