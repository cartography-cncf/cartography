import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.sentinelone.api import get_paginated_results
from cartography.intel.sentinelone.utils import get_application_id
from cartography.intel.sentinelone.utils import get_application_version_id
from cartography.models.sentinelone.application import S1ApplicationSchema
from cartography.models.sentinelone.application_version import (
    S1ApplicationVersionSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_application_data(
    account_id: str, api_url: str, api_token: str
) -> list[dict[str, Any]]:
    """
    Get application data from SentinelOne API
    :param account_id: SentinelOne account ID
    :param api_url: SentinelOne API URL
    :param api_token: SentinelOne API token
    :return: A list of application data dictionaries
    """
    logger.info(f"Retrieving SentinelOne application data for account {account_id}")
    applications = get_paginated_results(
        api_url=api_url,
        endpoint="/web/api/v2.1/application-management/inventory",
        api_token=api_token,
        params={
            "accountIds": account_id,
            "limit": 1000,
        },
    )

    logger.info(f"Retrieved {len(applications)} applications from SentinelOne")
    return applications


@timeit
def get_application_installs(
    app_inventory: list[dict[str, Any]], account_id: str, api_url: str, api_token: str
) -> list[dict[str, Any]]:
    """
    Get application installs from SentinelOne API
    :param app_inventory: List of applications to get installs for
    :param account_id: SentinelOne account ID
    :param api_url: SentinelOne API URL
    :param api_token: SentinelOne API token
    :return: A list of application installs data dictionaries
    """
    logger.info(
        f"Retrieving SentinelOne application installs for "
        f"{len(app_inventory)} applications in account "
        f"{account_id}",
    )

    application_installs = []
    for i, app in enumerate(app_inventory):
        logger.info(
            f"Retrieving SentinelOne installs for {app.get('applicationName')} "
            f"{app.get('applicationVendor')} ({i + 1}/{len(app_inventory)})",
        )
        name = app["applicationName"]
        vendor = app["applicationVendor"]
        app_installs = get_paginated_results(
            api_url=api_url,
            endpoint="/web/api/v2.1/application-management/inventory/endpoints",
            api_token=api_token,
            params={
                "accountIds": account_id,
                "limit": 1000,
                "applicationName": name,
                "applicationVendor": vendor,
            },
        )

        # Replace applicationVendor and applicationName with original values
        # for consistency with the application data
        for app_install in app_installs:
            app_install["applicationVendor"] = vendor
            app_install["applicationName"] = name
        application_installs.extend(app_installs)

    return application_installs


def transform_applications(
    applications_list: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Transform SentinelOne application data for loading into Neo4j
    :param applications_list: Raw application data from the API
    :return: Transformed application data
    """
    transformed_data = []
    for app in applications_list:
        vendor = app["applicationVendor"].strip()
        name = app["applicationName"].strip()
        app_id = get_application_id(name, vendor)
        transformed_app = {
            "id": app_id,
            "name": name,
            "vendor": vendor,
        }
        transformed_data.append(transformed_app)

    return transformed_data


def transform_application_versions(
    application_installs_list: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Transform SentinelOne application installs for loading into Neo4j
    :param application_installs_list: Raw application installs data from the API
    :return: Transformed application installs data
    """
    transformed_data = []
    for installed_version in application_installs_list:
        app_name = installed_version["applicationName"]
        app_vendor = installed_version["applicationVendor"]
        version = installed_version.get("version") or "unknown"

        transformed_version = {
            "id": get_application_version_id(
                app_name,
                app_vendor,
                version,
            ),
            "application_id": get_application_id(
                app_name,
                app_vendor,
            ),
            "application_name": app_name,
            "application_vendor": app_vendor,
            "agent_uuid": installed_version.get("endpointUuid"),
            "installation_path": installed_version.get("applicationInstallationPath"),
            "installed_dt": installed_version.get("applicationInstallationDate"),
            "version": version,
        }
        transformed_data.append(transformed_version)

    return transformed_data


@timeit
def load_application_data(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    """
    Load SentinelOne application data into Neo4j
    :param neo4j_session: Neo4j session
    :param data: The transformed application data
    :param account_id: The SentinelOne account ID
    :param update_tag: Update tag to set on the nodes
    :return: None
    """
    logger.info(f"Loading {len(data)} SentinelOne applications into Neo4j")
    load(
        neo4j_session,
        S1ApplicationSchema(),
        data,
        lastupdated=update_tag,
        S1_ACCOUNT_ID=account_id,
    )


@timeit
def load_application_versions(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    logger.info(f"Loading {len(data)} SentinelOne application versions into Neo4j")
    load(
        neo4j_session,
        S1ApplicationVersionSchema(),
        data,
        lastupdated=update_tag,
        S1_ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    logger.debug("Running SentinelOne S1Application cleanup")
    GraphJob.from_node_schema(S1ApplicationSchema(), common_job_parameters).run(
        neo4j_session
    )
    logger.debug("Running SentinelOne S1ApplicationVersion cleanup")
    GraphJob.from_node_schema(S1ApplicationVersionSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync SentinelOne applications
    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common job parameters containing API_URL, API_TOKEN, etc.
    :return: None
    """
    logger.info("Syncing SentinelOne application data")
    account_id = str(common_job_parameters["S1_ACCOUNT_ID"])
    api_url = str(common_job_parameters["API_URL"])
    api_token = str(common_job_parameters["API_TOKEN"])

    applications = get_application_data(account_id, api_url, api_token)
    application_versions = get_application_installs(
        applications, account_id, api_url, api_token
    )
    transformed_applications = transform_applications(applications)
    transformed_application_versions = transform_application_versions(
        application_versions
    )

    load_application_data(
        neo4j_session,
        transformed_applications,
        account_id,
        common_job_parameters["UPDATE_TAG"],
    )

    load_application_versions(
        neo4j_session,
        transformed_application_versions,
        account_id,
        common_job_parameters["UPDATE_TAG"],
    )

    cleanup(neo4j_session, common_job_parameters)
