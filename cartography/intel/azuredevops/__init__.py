import base64
import json
import logging
import os
from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import neo4j
from neo4j import GraphDatabase
from requests import exceptions

from . import members
from . import organization
from . import projects
from . import repos
from .resources import RESOURCE_FUNCTIONS
from .util import get_access_token
from cartography.config import Config
from cartography.graph.session import Session
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_organization(
    neo4j_session: neo4j.Session,
    config: Config,
    org_name: str,
    url: str,
    access_token: str,
    common_job_parameters: Dict,
) -> None:
    """
    Sync an Azure DevOps organization with all its resources.

    The sync of:
    1. Organization details
    2. Projects
    3. Repositories (concurrently)
    4. Members (concurrently)

    Args:
        neo4j_session: Neo4j session for database operations
        config: Cartography configuration object
        org_name: Name of the Azure DevOps organization
        url: Base Azure DevOps URL
        access_token: Microsoft Entra ID OAuth access token
        common_job_parameters: Common parameters for all sync operations
    """
    try:
        logger.info(f"Syncing Azure DevOps Organization: {org_name}")

        # sync the organization details
        organization.sync(
            neo4j_session,
            common_job_parameters,
            access_token,
            url,
            org_name,
        )

        # Sync all projects for the organization and get the data back
        projects_data = projects.sync(
            neo4j_session,
            common_job_parameters,
            access_token,
            url,
            org_name,
        )

        repos.sync(
            neo4j_session,
            common_job_parameters,
            access_token,
            url,
            org_name,
            projects_data
        )

        members.sync(
            neo4j_session,
            common_job_parameters,
            access_token,
            url,
            org_name
        )

    except exceptions.RequestException as e:
        logger.error(
            f"Could not complete request to the Azure DevOps API for {org_name}: {e}",
        )
    except Exception as e:
        logger.error(
            f"Unexpected error during organization sync for {org_name}: {e}",
            exc_info=True,
        )


def validate_auth_config(auth_details: Dict) -> bool:
    """
    Validates the Azure DevOps authentication configuration.

    Required fields for Microsoft Entra ID OAuth:
    - tenant_id: Microsoft Entra ID tenant ID
    - client_id: Application (client) ID
    - client_secret: Application client secret
    - url: Azure DevOps base URL
    - name: Organization name to sync
    """
    if not isinstance(auth_details, dict):
        logger.error("Auth details must be a dictionary")
        return False

    if (
        "organization" not in auth_details or
        not isinstance(auth_details["organization"], list) or
        not auth_details["organization"]
    ):
        logger.error("Auth details must contain 'organization' as a non-empty list")
        return False

    for i, org in enumerate(auth_details["organization"]):
        required_fields = [
            "tenant_id",
            "client_id",
            "client_secret",
            "url",
            "name",
        ]

        missing_fields = [field for field in required_fields if field not in org]
        if missing_fields:
            logger.error(f"Organization {i} missing required fields: {missing_fields}")
            return False

        # Validate URL format
        if not org["url"].startswith("https://"):
            logger.error(f"Organization {i} URL must use HTTPS: {org['url']}")
            return False

    logger.info("Azure DevOps authentication configuration validation passed")
    return True


@timeit
def start_azure_devops_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Azure DevOps data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.azure_devops_config:
        logger.info(
            "Azure DevOps import is not configured - skipping this module. See docs to configure.",
        )
        return

    try:
        # Decode the base64-encoded configuration
        auth_details = config.azure_devops_config
        logger.info("Successfully decoded Azure DevOps configuration")

    except (json.JSONDecodeError, TypeError) as e:
        logger.error(f"Failed to parse Azure DevOps config: {e}", exc_info=True)
        return

    # Validate the configuration structure
    if not validate_auth_config(auth_details):
        logger.error("Invalid Azure DevOps configuration format")
        return

    common_job_parameters = {
        "WORKSPACE_ID": config.params["workspace"]["id_string"],
        "UPDATE_TAG": config.update_tag,
        "ORGANIZATION_ID": config.params["workspace"]["account_id"],
    }

    logger.info(
        f"Starting Azure DevOps sync for {len(auth_details['organization'])} organization(s)",
    )

    # Process each organization configuration
    for org_idx, org in enumerate(auth_details.get("organization", [])):
        try:
            logger.info(f"Processing organization {org_idx + 1}: {org.get('name')}")

            # Get Microsoft Entra ID OAuth access token
            access_token = get_access_token(
                org["tenant_id"],
                org["client_id"],
                org["client_secret"],
            )

            if not access_token:
                logger.error(
                    f"Failed to retrieve Azure DevOps access token for organization {org.get('name')}",
                )
                continue

            logger.info(
                f"Successfully obtained access token for organization {org.get('name')}",
            )

            # Filter organizations based on workspace account_id (similar to GitHub pattern)
            if common_job_parameters["ORGANIZATION_ID"] != org["name"]:
                logger.debug(
                    f"Skipping organization {org['name']} - not matching workspace account_id {common_job_parameters['ORGANIZATION_ID']}",
                )
                continue

            logger.info(f"Starting sync for organization: {org['name']}")
            sync_organization(
                neo4j_session,
                config,
                org["name"],
                org["url"],
                access_token,
                common_job_parameters,
            )

        except Exception as e:
            logger.error(
                f"Failed to process organization {org_idx + 1} ({org.get('name')}): {e}",
                exc_info=True,
            )
            continue

    logger.info("Azure DevOps ingestion completed")
    return common_job_parameters
