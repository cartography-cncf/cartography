# Copyright (c) 2020, Oracle and/or its affiliates.
import logging
import re
from typing import Any
from typing import Dict
from typing import List

import neo4j
import oci
from oci.exceptions import ConfigFileNotFound
from oci.exceptions import InvalidConfig
from oci.exceptions import ProfileNotFound

from cartography.client.core.tx import run_write_query
from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)


def get_caller_identity() -> Dict[Any, Any]:
    return {}


def get_oci_account_default() -> Dict[str, Any]:
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


def get_oci_profile_names_from_config() -> List[Any]:
    config_path = oci.config._get_config_path_with_fallback("~/.oci/config")
    config = open(config_path).read()
    pattern = r"\[(.*)\]"
    m = re.findall(pattern, config)
    return m


def get_oci_accounts_from_config() -> Dict[str, Any]:

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


def load_oci_accounts(
    neo4j_session: neo4j.Session,
    oci_accounts: Dict[str, Any],
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    query = """
    MERGE (aa:OCITenancy{ocid: $TENANCY_ID})
    ON CREATE SET aa.firstseen = timestamp()
    SET aa.lastupdated = $oci_update_tag, aa.name = $ACCOUNT_NAME
    """
    for name in oci_accounts:
        run_write_query(
            neo4j_session,
            query,
            TENANCY_ID=oci_accounts[name]["tenancy"],
            ACCOUNT_NAME=name,
            oci_update_tag=oci_update_tag,
        )


def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    run_cleanup_job("oci_tenancy_cleanup.json", neo4j_session, common_job_parameters)


def sync(
    neo4j_session: neo4j.Session,
    accounts: Dict[str, Any],
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    load_oci_accounts(neo4j_session, accounts, oci_update_tag, common_job_parameters)
    cleanup(neo4j_session, common_job_parameters)
