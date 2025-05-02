# Copyright (c) 2020, Oracle and/or its affiliates.
import logging
from collections import namedtuple
from typing import Any
from typing import Dict
from typing import NamedTuple

import neo4j
import oci
from oci.exceptions import ConfigFileNotFound
from oci.exceptions import InvalidConfig
from oci.exceptions import ProfileNotFound

from cartography.config import Config

from . import iam
from . import organizations
from . import utils

# from cartography.util import run_analysis_job
# from cartography.util import run_cleanup_job
# from . import network
# from . import compute

logger = logging.getLogger(__name__)
Resources = namedtuple("Resources", "compute iam network")


def _sync_one_account(
    neo4j_session: neo4j.Session,
    resources: Resources,
    tenancy_id: str,
    oci_sync_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.info("Syncing OCI IAM client for OCI Tenancy with ID '%s'.", tenancy_id)
    iam.sync(
        neo4j_session,
        resources.iam,
        tenancy_id,
        oci_sync_tag,
        common_job_parameters,
    )

    regions = utils.get_regions_in_tenancy(neo4j_session, tenancy_id)
    for region in regions:
        logger.info(
            "Syncing OCI region '%s' for OCI Tenancy with ID '%s'.",
            region["name"],
            tenancy_id,
        )
        _change_resources_region(resources, region["name"])
        # compute.sync(neo4j_session, resources.compute,
        #   tenancy_id, region["name"], oci_sync_tag, common_job_parameters
        # )
        # network.sync(neo4j_session, resources.network,
        #   tenancy_id, region["name"], oci_sync_tag, common_job_parameters
        # )

    # Look into adding once DNS records are implemented.
    # NOTE clean up all DNS records, regardless of which job created them
    # run_cleanup_job('OCI_account_dns_cleanup.json', neo4j_session, common_job_parameters)


def _sync_multiple_accounts(
    neo4j_session: neo4j.Session,
    accounts: Dict[str, Any],
    sync_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.debug("Syncing OCI accounts: %s", ", ".join(accounts.keys()))
    organizations.sync(neo4j_session, accounts, sync_tag, common_job_parameters)

    for name in accounts:
        logger.info(
            "Syncing OCI Tenancy with ID '%s' using configured profile '%s'.",
            accounts[name]["tenancy"],
            name,
        )
        resources = _initialize_resources(accounts[name])
        tenancy_id = accounts[name]["tenancy"]
        common_job_parameters["OCI_TENANCY_ID"] = tenancy_id
        _sync_one_account(
            neo4j_session,
            resources,
            tenancy_id,
            sync_tag,
            common_job_parameters,
        )

    del common_job_parameters["OCI_TENANCY_ID"]

    # Look into adding cleanup
    # There may be orphan Users which point outside of known OCI accounts. This job cleans
    # up those nodes after all OCI accounts have been synced.
    # run_cleanup_job('oci_post_ingestion_principals_cleanup.json', neo4j_session, common_job_parameters)
    # There may be orphan DNS entries that point outside of known OCI zones. This job cleans
    # up those entries after all OCI accounts have been synced.
    # run_cleanup_job('oci_post_ingestion_dns_cleanup.json', neo4j_session, common_job_parameters)


def _change_resources_region(resources: NamedTuple, region: str) -> None:
    for resource in resources:
        resource.base_client.set_region(region)


def _get_network_resource(
    credentials: Dict[str, Any],
) -> oci.core.virtual_network_client.VirtualNetworkClient:
    """
    Instantiates a OCI VirtualNetworkClient resource object to call the Network API.
     See https://docs.cloud.oracle.com/en-us/iaas/Content/Network/Concepts/overview.htm.
    :param credentials: OCI Credentials object
    :return: A VirtualNetworkClient resource object
    """
    return oci.core.VirtualNetworkClient(credentials)


def _get_iam_resource(
    credentials: Dict[str, Any],
) -> oci.identity.identity_client.IdentityClient:
    """
    Instantiates a OCI IdentityCleint resource object to call the Identity API. This is used to users,
     ..., ... and ... data. See https://docs.cloud.oracle.com/iaas/Content/Compute/Concepts/computeoverview.htm.
    :param credentials: OCI Credentials object
    :return: A IdentityClient resource object
    """
    return oci.identity.IdentityClient(credentials)


def _get_compute_resource(
    credentials: Dict[str, Any],
) -> oci.core.compute_client.ComputeClient:
    """
    Instantiates a OCI ComputeClient resource object to call the Compute API. This is used to pull zone, instance, and
    networking data. https://docs.cloud.oracle.com/iaas/Content/Compute/Concepts/computeoverview.htm.
    :param credentials: The OCI Credentials object
    :return: A ComputeClient resource object
    """
    return oci.core.ComputeClient(credentials)


def _initialize_resources(credentials: Dict[str, Any]) -> Resources:
    """
    Create namedtuple of all resource objects necessary for OCI data gathering.
    :param credentials: The OCI config object
    :return: namedtuple of all resource objects
    """
    return Resources(
        compute=_get_compute_resource(credentials),
        iam=_get_iam_resource(credentials),
        network=_get_network_resource(credentials),
    )


def start_oci_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    Starts the OCI ingestion process by initializing OCI Application Default Credentials, creating the necessary
    resource objects, listing all OCI organizations and projects available to the OCI identity, and supplying that
    context to all intel modules.
    :param neo4j_session: The Neo4j session
    :param config: A `cartography.config` object
    :return: Nothing
    """
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }
    try:
        # Explicitly use Application Default Credentials.
        credentials = oci.config.from_file("~/.oci/config", "DEFAULT")
        oci.config.validate_config(credentials)
        # computeClient = oci.core.ComputeClient(credentials)
    except (ConfigFileNotFound, ProfileNotFound, InvalidConfig) as e:
        logger.debug("Error occurred calling oci.config.from_file.", exc_info=True)
        logger.error(
            (
                "Unable to initialize OCI creds. If you don't have OCI data or don't want to load "
                "OCI data then you can ignore this message. Otherwise, the error code is: %s "
                "Make sure your OCI credentials are configured correctly, your credentials file (if any) is valid, and "
                "that the identity you are authenticating to has the required Audit policies attached "
                "(https://docs.cloud.oracle.com/iaas/Content/Identity/Concepts/commonpolicies.htm)."
            ),
            e,
        )
        return

    if config.oci_sync_all_profiles:
        oci_accounts = organizations.get_oci_accounts_from_config()
    else:
        oci_accounts = organizations.get_oci_account_default()

    tenancy_list = []
    for x in oci_accounts:
        tenancy_list.append(oci_accounts[x]["tenancy"])

    if len(tenancy_list) != len(set(tenancy_list)):
        logger.warning(
            (
                "There are duplicate OCI tenancy's in your OCI configuration. It is strongly recommended that you run "
                "cartography with an OCI configuration which has exactly one profile for each OCI tenancy you want to "
                "sync. Doing otherwise will result in undefined and untested behavior."
            ),
        )

    if not oci_accounts:
        logger.warning(
            "No valid OCI credentials could be found. No OCI accounts can be synced. Exiting OCI sync stage.",
        )
        return

    _sync_multiple_accounts(
        neo4j_session,
        oci_accounts,
        config.update_tag,
        common_job_parameters,
    )

    # Look into adding analysis job once compute is implemented.
    # run_analysis_job(
    #    'oci_compute_asset_exposure.json',
    #    neo4j_session,
    #    common_job_parameters,
    # )
