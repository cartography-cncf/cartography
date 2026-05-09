import json
import logging
import os
import time
from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import neo4j
from neo4j import GraphDatabase

from . import subscription
from . import tag
from . import tenant
from .resources import RESOURCE_FUNCTIONS
from .util.credentials import Authenticator
from .util.credentials import Credentials
from cartography.config import Config
from cartography.graph.session import Session
from cartography.intel.azure.util.common import parse_and_validate_azure_requested_syncs
from cartography.util import run_analysis_job
from cartography.util import timeit

logger = logging.getLogger(__name__)

AZURE_AUTH_MODE_USER_IMPERSONATION = "user_impersonation"
AZURE_AUTH_MODE_SERVICE_PRINCIPAL = "service_principal"


def concurrent_execution(
    service: str, service_func: Any, config: Config, credentials: Credentials, common_job_parameters: Dict, update_tag: int, subscription_id: str,
):
    try:
        logger.info(f"BEGIN processing for service: {service}")

        regions = config.params.get('regions', None)

        neo4j_auth = (config.neo4j_user, config.neo4j_password)
        neo4j_driver = GraphDatabase.driver(
            config.neo4j_uri,
            auth=neo4j_auth,
            max_connection_lifetime=config.neo4j_max_connection_lifetime,
        )
        if service == 'iam':
            service_func(Session(neo4j_driver), credentials, credentials.tenant_id, update_tag, common_job_parameters)
        elif service == 'key_vaults':
            service_func(
                Session(neo4j_driver), credentials,
                subscription_id, update_tag, common_job_parameters, regions,
            )
        else:
            service_func(
                Session(neo4j_driver), credentials.arm_credentials,
                subscription_id, update_tag, common_job_parameters, regions,
            )
        logger.info(f"END processing for service: {service}")
    except Exception as e:
        logger.warning(f"error to process service {service} - {e}")


def _sync_one_subscription(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    tenant: Dict,
    requested_syncs: List[str],
    update_tag: int,
    common_job_parameters: Dict,
    config: Config,
) -> None:

    common_job_parameters['Azure_Primary_AD_Domain_Name'] = tenant['defaultDomain']

    if os.environ.get("LOCAL_RUN", "0") == "1" or os.environ.get("CDX_RUN_AS") == "EKS":
        # BEGIN - Sequential Run

        service_timings: Dict[str, float] = {}
        sub_start = time.time()

        for func_name in requested_syncs:
            if func_name in RESOURCE_FUNCTIONS:
                try:
                    logger.info(f"Processing {func_name}")
                    t0 = time.time()
                    if func_name == 'iam':
                        RESOURCE_FUNCTIONS[func_name](neo4j_session, credentials, credentials.tenant_id, update_tag, common_job_parameters)

                    elif func_name == 'key_vaults':
                        RESOURCE_FUNCTIONS[func_name](neo4j_session, credentials, subscription_id, update_tag, common_job_parameters, config.params.get('regions', None))

                    else:
                        RESOURCE_FUNCTIONS[func_name](neo4j_session, credentials.arm_credentials, subscription_id, update_tag, common_job_parameters, config.params.get('regions', None))

                    elapsed = round(time.time() - t0, 2)
                    service_timings[func_name] = elapsed
                    logger.info(
                        json.dumps({
                            "event": "azure_service_timing",
                            "subscription_id": subscription_id,
                            "service": func_name,
                            "duration_seconds": elapsed,
                        }),
                    )
                except Exception as e:
                    logger.warning(f"error to process service {func_name} - {e}")
            else:
                logger.warning(f'AZURE sync function "{func_name}" was specified but does not exist. Did you misspell it?')

        total_services_elapsed = round(time.time() - sub_start, 2)
        logger.info(
            json.dumps({
                "event": "azure_subscription_timing_summary",
                "subscription_id": subscription_id,
                "total_duration_seconds": total_services_elapsed,
                "service_timings": service_timings,
                "slowest_service": max(service_timings, key=service_timings.get) if service_timings else None,
            }),
        )

        # END - Sequential Run

    else:
        # BEGIN - Parallel Run

        with ThreadPoolExecutor(max_workers=len(RESOURCE_FUNCTIONS)) as executor:
            futures = []
            for request in requested_syncs:
                if request in RESOURCE_FUNCTIONS:
                    try:
                        futures.append(
                            executor.submit(
                                concurrent_execution,
                                request,
                                RESOURCE_FUNCTIONS[request],
                                config,
                                credentials,
                                common_job_parameters,
                                update_tag,
                                subscription_id,
                            ),
                        )
                    except Exception as e:
                        logger.warning(f"error to append service {request} in futures - {e}")
                else:
                    logger.warning(f'Azure sync function "{request}" was specified but does not exist. Did you misspell it?')

            for future in as_completed(futures):
                logger.info(f'Result from Future - Service Processing: {future.result()}')

        # END - Parallel Run

    # call tag.sync() at the last, don't change position of tag.sync()
    tag.sync(neo4j_session, credentials.arm_credentials, subscription_id, update_tag, common_job_parameters, config)


def _sync_tenant(
    neo4j_session: neo4j.Session,
    tenant_obj: Dict,
    current_user: Optional[str],
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    logger.info("Syncing Azure Tenant: %s", tenant_obj['tenantId'])
    tenant.sync(
        neo4j_session, tenant_obj, current_user, update_tag,
        common_job_parameters,
    )


def _sync_multiple_subscriptions(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    tenant_obj: Dict,
    subscriptions: List[Dict],
    requested_syncs: List[str],
    update_tag: int,
    common_job_parameters: Dict,
    config: Config,
) -> None:
    logger.info("Syncing Azure subscriptions")

    tenant_id = tenant_obj['tenantId']

    subscription.sync(
        neo4j_session, tenant_id, subscriptions, update_tag,
        common_job_parameters,
    )

    common_job_parameters['AZURE_TENANT_ID'] = tenant_id

    for sub in subscriptions:
        common_job_parameters['AZURE_SUBSCRIPTION_ID'] = sub['subscriptionId']

        if common_job_parameters['AZURE_SUBSCRIPTION_ID'] != sub['subscriptionId']:
            continue

        logger.info(
            "Syncing Azure Subscription with ID '%s'",
            sub['subscriptionId'],
        )

        _sync_one_subscription(
            neo4j_session,
            credentials,
            sub['subscriptionId'],
            tenant_obj,
            requested_syncs,
            update_tag,
            common_job_parameters,
            config,
        )

        _analysis_jobs = [
            'azure_network_security_group_asset_exposure.json',
            'azure_vm_asset_exposure.json',
            'azure_network_subnet_asset_exposure.json',
            'azure_network_interface_asset_exposure.json',
            'azure_network_load_balancer_asset_exposure.json',
            'azure_storage_asset_exposure.json',
            'azure_sql_asset_exposure.json',
            'azure_cosmosdb_asset_exposure.json',
            'azure_keyvault_asset_exposure.json',
        ]
        analysis_timings: Dict[str, float] = {}
        for job_file in _analysis_jobs:
            t0 = time.time()
            run_analysis_job(job_file, neo4j_session, common_job_parameters)
            elapsed = round(time.time() - t0, 2)
            analysis_timings[job_file] = elapsed

        logger.info(
            json.dumps({
                "event": "azure_analysis_jobs_timing",
                "subscription_id": sub['subscriptionId'],
                "total_duration_seconds": round(sum(analysis_timings.values()), 2),
                "job_timings": analysis_timings,
            }),
        )

        del common_job_parameters["AZURE_SUBSCRIPTION_ID"]


@timeit
def start_azure_ingestion(
    neo4j_session: neo4j.Session,
    config: Config,
) -> None:
    common_job_parameters = {
        "WORKSPACE_ID": config.params['workspace']['id_string'],
        "DEFAULT_SUBSCRIPTION": config.params.get('defaultSubscription'),
        "GROUPS": config.params.get('groups', []),
        "UPDATE_TAG": config.update_tag,
        "permission_relationships_file": config.permission_relationships_file,
        "pagination": {},
    }

    try:
        # if config.azure_sp_auth:
        #     credentials = Authenticator().authenticate_sp(
        #         config.azure_tenant_id,
        #         config.azure_client_id,
        #         config.azure_client_secret,
        #     )
        # else:
        #     credentials = Authenticator().authenticate_cli()

        auth_mode = config.params.get('authMode', AZURE_AUTH_MODE_USER_IMPERSONATION)
        if auth_mode == AZURE_AUTH_MODE_USER_IMPERSONATION:
            logger.info("Using user impersonation for Azure authentication")
            credentials = Authenticator().impersonate_user(
                config.azure_client_id,
                config.azure_client_secret,
                config.azure_redirect_uri,
                config.azure_refresh_token,
                config.azure_graph_scope,
                config.azure_default_graph_scope,
                config.azure_azure_scope,
                config.azure_vault_scope,
                config.azure_subscription_id,
                config.azure_tenant_id,
            )
        elif auth_mode == AZURE_AUTH_MODE_SERVICE_PRINCIPAL:
            logger.info("Using service principal for Azure authentication")
            credentials = Authenticator().authenticate_service_principal(
                config.azure_tenant_id,
                config.azure_subscription_id,
                config.azure_client_id,
                config.azure_client_secret,
            )
        else:
            logger.error(f"Unsupported Azure authentication mode: {auth_mode}")
            raise ValueError(f"Unsupported Azure authentication mode: {auth_mode}")

    except Exception as e:
        logger.error(f"Unable to authenticate with Azure Service Principal, an error occurred: {e}. Make sure your Azure Service Principal details are provided correctly.", exc_info=True, stack_info=True)
        return

    requested_syncs: List[str] = list(RESOURCE_FUNCTIONS.keys())
    if config.azure_requested_syncs:
        azure_requested_syncs_string = ""
        for service in config.azure_requested_syncs:
            azure_requested_syncs_string += f"{service.get('name', '')},"
            if service.get('pagination', None):
                pagination = service.get('pagination', {})
                pagination['hasNextPage'] = False
                common_job_parameters['pagination'][service.get('name', None)] = pagination
        requested_syncs = parse_and_validate_azure_requested_syncs(azure_requested_syncs_string[:-1])

    tenant_obj = tenant.get_active_tenant(credentials)
    common_job_parameters['Azure_Primary_AD_Domain_Name'] = tenant_obj['defaultDomain']

    _sync_tenant(
        neo4j_session,
        tenant_obj,
        credentials.get_current_user(),
        config.update_tag,
        common_job_parameters,
    )

    if config.azure_sync_all_subscriptions:
        subscriptions = subscription.get_all_azure_subscriptions(credentials, common_job_parameters)

    else:
        subscriptions = subscription.get_current_azure_subscription(
            credentials, credentials.subscription_id, common_job_parameters,
        )

    if not subscriptions:
        logger.warning(
            "No valid Azure credentials are found. No Azure subscriptions can be synced. Exiting Azure sync stage.",
        )
        return

    _sync_multiple_subscriptions(
        neo4j_session,
        credentials,
        tenant_obj,
        subscriptions,
        requested_syncs,
        config.update_tag,
        common_job_parameters,
        config,
    )
    del common_job_parameters['Azure_Primary_AD_Domain_Name']
    return common_job_parameters
