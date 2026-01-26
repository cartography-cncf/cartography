import logging
import re
from typing import Any

import neo4j
import oci
from oci.exceptions import ConfigFileNotFound
from oci.exceptions import InvalidConfig
from oci.exceptions import ProfileNotFound

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.oci.tenancy import OCITenancySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_caller_identity() -> dict[Any, Any]:
    return {}


@timeit
def get_oci_account_default() -> dict[str, Any]:
    try:
        profile_oci_credentials = oci.config.from_file("~/.oci/config", "DEFAULT")
        oci.config.validate_config(profile_oci_credentials)
        return {"DEFAULT": profile_oci_credentials}
    except (ConfigFileNotFound, ProfileNotFound, InvalidConfig) as e:
        logger.debug("Error occurred getting default OCI profile.", exc_info=True)
        logger.error(
            (
                "Unable to get default OCI profile, an error occurred: '%s'. Make sure your OCI credentials are "
                "configured correctly, your OCI config file is valid, and your credentials have the required Audit "
                "policies attached (https://docs.cloud.oracle.com/iaas/Content/Identity/Concepts/commonpolicies.htm)."
            ),
            e,
        )
        return {}


@timeit
def get_oci_profile_names_from_config() -> list[Any]:
    config_path = oci.config._get_config_path_with_fallback("~/.oci/config")
    config = open(config_path).read()
    pattern = r"\[(.*)\]"
    m = re.findall(pattern, config)
    return m


@timeit
def get_oci_accounts_from_config() -> dict[str, Any]:

    available_profiles = get_oci_profile_names_from_config()

    d = {}
    for profile_name in available_profiles:
        if profile_name == "DEFAULT":
            logger.debug("Skipping OCI profile 'DEFAULT'.")
            continue
        try:
            profile_oci_credentials = oci.config.from_file(
                "~/.oci/config",
                profile_name,
            )
            oci.config.validate_config(profile_oci_credentials)
        except (ConfigFileNotFound, ProfileNotFound, InvalidConfig) as e:
            logger.debug(
                "Error occurred calling oci.config.from_file with profile_name '%s'.",
                profile_name,
                exc_info=True,
            )
            logger.error(
                (
                    "Unable to initialize an OCI session using profile '%s', an error occurred: '%s'. Make sure your "
                    "OCI credentials are configured correctly, your OCI config file is valid, and your credentials "
                    "have the required audit policies attached "
                    "(https://docs.cloud.oracle.com/iaas/Content/Identity/Concepts/commonpolicies.htm)."
                ),
                profile_name,
                e,
            )
            continue

        d[profile_name] = profile_oci_credentials
        logger.debug(
            "Discovered oci tenancy '%s' associated with configured profile '%s'.",
            d[profile_name]["tenancy"],
            profile_name,
        )
    return d


def transform_oci_accounts(
    oci_accounts: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Transform OCI accounts data for loading into Neo4j.
    """
    return [
        {
            "ocid": oci_accounts[name]["tenancy"],
            "name": name,
        }
        for name in oci_accounts
    ]


@timeit
def load_oci_accounts(
    neo4j_session: neo4j.Session,
    oci_accounts: list[dict[str, Any]],
    oci_update_tag: int,
) -> None:
    load(
        neo4j_session,
        OCITenancySchema(),
        oci_accounts,
        lastupdated=oci_update_tag,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(OCITenancySchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    accounts: dict[str, Any],
    oci_update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    transformed_accounts = transform_oci_accounts(accounts)
    load_oci_accounts(neo4j_session, transformed_accounts, oci_update_tag)
    cleanup(neo4j_session, common_job_parameters)
