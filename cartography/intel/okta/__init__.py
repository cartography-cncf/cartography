from __future__ import annotations

import logging
import re
from typing import Any

import neo4j
from okta.client import Client as OktaClient

from cartography.config import Config
from cartography.intel.okta import api_tokens
from cartography.intel.okta import applications
from cartography.intel.okta import authenticators
from cartography.intel.okta import awssaml
from cartography.intel.okta import devices
from cartography.intel.okta import factors
from cartography.intel.okta import groups
from cartography.intel.okta import log_streams
from cartography.intel.okta import network_zones
from cartography.intel.okta import organization
from cartography.intel.okta import origins
from cartography.intel.okta import policies
from cartography.intel.okta import users
from cartography.intel.okta.common import OKTA_OAUTH_DEFAULT_SCOPES
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
def _cleanup_okta_organizations(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
) -> None:
    """
    Remove stale Okta organization
    :param neo4j_session: The Neo4j session
    :param common_job_parameters: Parameters to carry to the cleanup job
    :return: Nothing
    """
    # DEPRECATED: migration cleanup, will be removed in v1
    run_cleanup_job("okta_import_cleanup.json", neo4j_session, common_job_parameters)
    cleanup_okta_groups(neo4j_session, common_job_parameters)


def cleanup_okta_groups(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
) -> None:
    run_cleanup_job("okta_groups_cleanup.json", neo4j_session, common_job_parameters)


def _has_oauth_credentials(config: Config) -> bool:
    return bool(config.okta_client_id and config.okta_private_key)


def _parse_scopes(scopes: str | None) -> list[str]:
    return [scope for scope in re.split(r"[\s,]+", scopes or "") if scope]


def create_okta_client(config: Config) -> OktaClient:
    """
    Build an Okta SDK client that authenticates with an OAuth service app when
    one is configured, and with an API token otherwise.
    """
    client_config: dict[str, Any] = {
        "orgUrl": f"https://{config.okta_org_id}.{config.okta_base_domain}",
    }
    if not _has_oauth_credentials(config):
        client_config["token"] = config.okta_api_key
        return OktaClient(client_config)

    if config.okta_api_key:
        logger.warning(
            "Both an Okta API key and OAuth client credentials are set; using the "
            "OAuth client.",
        )
    client_config.update(
        {
            "authorizationMode": "PrivateKey",
            "clientId": config.okta_client_id,
            # A PEM string or a JWK; the SDK also accepts a path to a PEM file.
            "privateKey": config.okta_private_key,
            "scopes": _parse_scopes(config.okta_scopes)
            or list(OKTA_OAUTH_DEFAULT_SCOPES),
            # Okta requires DPoP on new service apps by default. The SDK uses
            # whichever token type Okta returns, DPoP or Bearer.
            "dpopEnabled": config.okta_dpop_enabled,
        }
    )
    if config.okta_private_key_id:
        client_config["kid"] = config.okta_private_key_id
    return OktaClient(client_config)


@timeit
def start_okta_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    Starts the OKTA ingestion process
    :param neo4j_session: The Neo4j session
    :param config: A `cartography.config` object
    :return: Nothing
    """
    if bool(config.okta_client_id) != bool(config.okta_private_key):
        logger.warning(
            "Okta OAuth needs both okta_client_id and okta_private_key; ignoring "
            "the incomplete OAuth settings.",
        )
    if not (config.okta_api_key or _has_oauth_credentials(config)):
        logger.warning(
            "No valid Okta credentials could be found. Exiting Okta sync stage.",
        )
        return

    logger.debug("Starting Okta sync on %s", config.okta_org_id)

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "OKTA_ORG_ID": config.okta_org_id,
    }

    okta_client = create_okta_client(config)

    org_properties = organization.sync_okta_organization(
        neo4j_session,
        common_job_parameters,
        okta_client,
    )
    user_ids, user_roles_synced = users.sync_okta_users(
        okta_client,
        neo4j_session,
        common_job_parameters,
    )
    group_roles_synced = groups.sync_okta_groups(
        okta_client,
        neo4j_session,
        common_job_parameters,
    )
    users.sync_okta_user_types(okta_client, neo4j_session, common_job_parameters)
    app_ids = applications.sync_okta_applications(
        okta_client,
        neo4j_session,
        common_job_parameters,
    )
    origins.sync_okta_origins(okta_client, neo4j_session, common_job_parameters)
    authenticators.sync_okta_authenticators(
        okta_client,
        neo4j_session,
        common_job_parameters,
    )
    factors.sync_okta_user_factors(
        okta_client,
        neo4j_session,
        common_job_parameters,
        user_ids,
    )
    devices.sync_okta_devices(
        okta_client,
        neo4j_session,
        common_job_parameters,
    )
    log_streams_synced = log_streams.sync_okta_log_streams(
        okta_client,
        neo4j_session,
        common_job_parameters,
    )
    network_zones.sync_okta_network_zones(
        okta_client,
        neo4j_session,
        common_job_parameters,
    )
    # Runs after users and network zones: tokens link to both.
    api_tokens.sync_okta_api_tokens(
        okta_client,
        neo4j_session,
        common_job_parameters,
    )
    # Runs after applications and network zones: policies link to both.
    policies.sync_okta_policies(
        okta_client,
        neo4j_session,
        common_job_parameters,
        app_ids,
    )

    organization.record_okta_sync_coverage(
        neo4j_session,
        common_job_parameters,
        org_properties,
        {
            "log_streams_synced": log_streams_synced,
            "admin_roles_synced": user_roles_synced and group_roles_synced,
        },
    )

    # Sync Okta groups to AWS roles via SAML
    awssaml.sync_okta_aws_saml(
        neo4j_session,
        config.okta_saml_role_regex,
        config.update_tag,
        config.okta_org_id,
    )

    _cleanup_okta_organizations(neo4j_session, common_job_parameters)

    merge_module_sync_metadata(
        neo4j_session,
        group_type="OktaOrganization",
        group_id=config.okta_org_id,
        synced_type="OktaOrganization",
        update_tag=config.update_tag,
        stat_handler=stat_handler,
    )
