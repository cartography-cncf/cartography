import logging

import neo4j
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

import cartography.intel.vercel.accessgroups
import cartography.intel.vercel.aliases
import cartography.intel.vercel.deployments
import cartography.intel.vercel.dnsrecords
import cartography.intel.vercel.domains
import cartography.intel.vercel.edgeconfigs
import cartography.intel.vercel.edgeconfigtokens
import cartography.intel.vercel.environmentvariables
import cartography.intel.vercel.firewallbypassrules
import cartography.intel.vercel.firewallconfigs
import cartography.intel.vercel.integrations
import cartography.intel.vercel.logdrains
import cartography.intel.vercel.projectdomains
import cartography.intel.vercel.projects
import cartography.intel.vercel.securecomputenetworks
import cartography.intel.vercel.sharedenvironmentvariables
import cartography.intel.vercel.teams
import cartography.intel.vercel.users
import cartography.intel.vercel.webhooks
from cartography.config import Config
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_vercel_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Vercel data. Otherwise warn and exit.
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.vercel_token or not config.vercel_team_id:
        logger.info(
            "Vercel import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    api_session = requests.session()
    retry_policy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    api_session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    api_session.headers.update({"Authorization": f"Bearer {config.vercel_token}"})

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "BASE_URL": config.vercel_base_url,
        "TEAM_ID": config.vercel_team_id,
    }

    # Phase 1: Root tenant
    cartography.intel.vercel.teams.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Phase 2: Users (needed for CREATED_BY rels later)
    cartography.intel.vercel.users.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Phase 3: Projects (returns list for per-project iteration)
    projects = cartography.intel.vercel.projects.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Phase 4: Team-level resources
    domains = cartography.intel.vercel.domains.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )
    edge_configs = cartography.intel.vercel.edgeconfigs.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )
    cartography.intel.vercel.sharedenvironmentvariables.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )
    cartography.intel.vercel.integrations.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )
    cartography.intel.vercel.accessgroups.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )
    cartography.intel.vercel.webhooks.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )
    cartography.intel.vercel.logdrains.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )
    cartography.intel.vercel.securecomputenetworks.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        projects,
    )
    cartography.intel.vercel.aliases.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Phase 5: Per-project sub-resources
    for project in projects:
        project_id = project["id"]
        project_job_parameters = {
            **common_job_parameters,
            "project_id": project_id,
        }
        cartography.intel.vercel.deployments.sync(
            neo4j_session,
            api_session,
            project_job_parameters,
            project_id=project_id,
        )
        cartography.intel.vercel.environmentvariables.sync(
            neo4j_session,
            api_session,
            project_job_parameters,
            project_id=project_id,
        )
        cartography.intel.vercel.projectdomains.sync(
            neo4j_session,
            api_session,
            project_job_parameters,
            project_id=project_id,
        )
        cartography.intel.vercel.firewallconfigs.sync(
            neo4j_session,
            api_session,
            project_job_parameters,
            project_id=project_id,
        )
        cartography.intel.vercel.firewallbypassrules.sync(
            neo4j_session,
            api_session,
            project_job_parameters,
            project_id=project_id,
        )

    # Phase 6: Per-domain sub-resources
    for domain in domains:
        domain_name = domain["name"]
        domain_job_parameters = {
            **common_job_parameters,
            "domain_name": domain_name,
        }
        cartography.intel.vercel.dnsrecords.sync(
            neo4j_session,
            api_session,
            domain_job_parameters,
            domain_name=domain_name,
        )

    # Phase 7: Per-edge-config sub-resources
    for ec in edge_configs:
        ec_id = ec["id"]
        ec_job_parameters = {
            **common_job_parameters,
            "edge_config_id": ec_id,
        }
        cartography.intel.vercel.edgeconfigtokens.sync(
            neo4j_session,
            api_session,
            ec_job_parameters,
            edge_config_id=ec_id,
        )
