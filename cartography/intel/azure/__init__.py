import logging
from typing import TYPE_CHECKING

import neo4j

from cartography.analysis.azure.analysis import AZURE_COMPUTE_ASSET_EXPOSURE_JOBS
from cartography.analysis.azure.analysis import AZURE_FIREWALL_LB_PROTECTION
from cartography.analysis.azure.analysis import AZURE_LB_EXPOSURE
from cartography.config import Config
from cartography.util import run_analysis_job
from cartography.util import run_typed_analysis_job
from cartography.util import timeit
from cartography.util.lazy import lazy_callable
from cartography.util.lazy import lazy_import

# Submodules are bound lazily so that the provider SDK only loads once the config
if TYPE_CHECKING:
    from cartography.intel.azure.util.credentials import Credentials

# gate below has decided that this module has something to sync.
Authenticator = lazy_callable(
    "cartography.intel.azure.util.credentials", "Authenticator"
)
aks = lazy_import("cartography.intel.azure.aks")
data_factory_util = lazy_import("cartography.intel.azure.data_factory_util")
app_service = lazy_import("cartography.intel.azure.app_service")
application_gateways = lazy_import("cartography.intel.azure.application_gateways")
compute = lazy_import("cartography.intel.azure.compute")
container_instances = lazy_import("cartography.intel.azure.container_instances")
cosmosdb = lazy_import("cartography.intel.azure.cosmosdb")
data_factory = lazy_import("cartography.intel.azure.data_factory")
data_factory_dataset = lazy_import("cartography.intel.azure.data_factory_dataset")
data_factory_linked_service = lazy_import(
    "cartography.intel.azure.data_factory_linked_service"
)
data_factory_pipeline = lazy_import("cartography.intel.azure.data_factory_pipeline")
data_lake = lazy_import("cartography.intel.azure.data_lake")
event_grid = lazy_import("cartography.intel.azure.event_grid")
event_hub = lazy_import("cartography.intel.azure.event_hub")
event_hub_namespace = lazy_import("cartography.intel.azure.event_hub_namespace")
firewall = lazy_import("cartography.intel.azure.firewall")
functions = lazy_import("cartography.intel.azure.functions")
group_containers = lazy_import("cartography.intel.azure.group_containers")
key_vaults = lazy_import("cartography.intel.azure.key_vaults")
load_balancers = lazy_import("cartography.intel.azure.load_balancers")
logic_apps = lazy_import("cartography.intel.azure.logic_apps")
management_groups = lazy_import("cartography.intel.azure.management_groups")
monitor = lazy_import("cartography.intel.azure.monitor")
network = lazy_import("cartography.intel.azure.network")
permission_relationships = lazy_import(
    "cartography.intel.azure.permission_relationships"
)
rbac = lazy_import("cartography.intel.azure.rbac")
resource_groups = lazy_import("cartography.intel.azure.resource_groups")
security_center = lazy_import("cartography.intel.azure.security_center")
sql = lazy_import("cartography.intel.azure.sql")
storage = lazy_import("cartography.intel.azure.storage")
subscription = lazy_import("cartography.intel.azure.subscription")
synapse = lazy_import("cartography.intel.azure.synapse")
tenant = lazy_import("cartography.intel.azure.tenant")
workload_identity = lazy_import("cartography.intel.azure.workload_identity")


logger = logging.getLogger(__name__)


def _sync_data_factory(
    neo4j_session: neo4j.Session,
    credentials: "Credentials",
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    try:
        factories_raw = data_factory.sync_data_factories(
            neo4j_session,
            credentials,
            subscription_id,
            update_tag,
            common_job_parameters,
        )
        linked_services_by_factory = (
            data_factory_linked_service.sync_data_factory_linked_services(
                neo4j_session,
                credentials,
                factories_raw,
                subscription_id,
                update_tag,
                common_job_parameters,
            )
        )
        datasets_by_factory = data_factory_dataset.sync_data_factory_datasets(
            neo4j_session,
            credentials,
            factories_raw,
            linked_services_by_factory,
            subscription_id,
            update_tag,
            common_job_parameters,
        )
        data_factory_pipeline.sync_data_factory_pipelines(
            neo4j_session,
            credentials,
            factories_raw,
            datasets_by_factory,
            subscription_id,
            update_tag,
            common_job_parameters,
        )
    except data_factory_util.AzureDataFactoryTransientError as error:
        logger.warning(
            "Skipping Azure Data Factory sync after transient API failures "
            "for subscription %s (operation=%s, status_code=%s).",
            subscription_id,
            error.operation,
            error.status_code,
        )


def _sync_one_subscription(
    neo4j_session: neo4j.Session,
    credentials: "Credentials",
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    compute.sync(
        neo4j_session,
        credentials.credential,
        subscription_id,
        update_tag,
        common_job_parameters,
    )
    cosmosdb.sync(
        neo4j_session,
        credentials.credential,
        subscription_id,
        update_tag,
        common_job_parameters,
    )
    app_service.sync(
        neo4j_session,
        credentials,
        subscription_id,
        update_tag,
        common_job_parameters,
    )
    functions.sync(
        neo4j_session,
        credentials,
        subscription_id,
        update_tag,
        common_job_parameters,
    )
    event_grid.sync(
        neo4j_session,
        credentials,
        subscription_id,
        update_tag,
        common_job_parameters,
    )
    logic_apps.sync(
        neo4j_session,
        credentials,
        subscription_id,
        update_tag,
        common_job_parameters,
    )
    rbac.sync(
        neo4j_session,
        credentials,
        subscription_id,
        update_tag,
        common_job_parameters,
    )
    # Runs after compute/functions (identity principal ids) and rbac (role
    # assignments) so it can join them into the canonical ASSUMES edges.
    workload_identity.sync(
        neo4j_session,
        subscription_id,
        update_tag,
    )
    sql.sync(
        neo4j_session,
        credentials.credential,
        subscription_id,
        update_tag,
        common_job_parameters,
    )
    storage.sync(
        neo4j_session,
        credentials.credential,
        subscription_id,
        update_tag,
        common_job_parameters,
    )
    resource_groups.sync(
        neo4j_session,
        credentials,
        subscription_id,
        update_tag,
        common_job_parameters,
    )
    key_vaults.sync(
        neo4j_session,
        credentials,
        subscription_id,
        update_tag,
        common_job_parameters,
    )
    aks.sync(
        neo4j_session,
        credentials,
        subscription_id,
        update_tag,
        common_job_parameters,
    )
    namespaces = event_hub_namespace.sync_event_hub_namespaces(
        neo4j_session,
        credentials,
        subscription_id,
        update_tag,
        common_job_parameters,
    )
    event_hub.sync_event_hubs(
        neo4j_session,
        credentials,
        namespaces,
        subscription_id,
        update_tag,
        common_job_parameters,
    )
    _sync_data_factory(
        neo4j_session,
        credentials,
        subscription_id,
        update_tag,
        common_job_parameters,
    )
    data_lake.sync(
        neo4j_session,
        credentials,
        subscription_id,
        update_tag,
        common_job_parameters,
    )
    network.sync(
        neo4j_session,
        credentials,
        subscription_id,
        update_tag,
        common_job_parameters,
    )
    group_containers.sync_group_containers(
        neo4j_session,
        credentials,
        subscription_id,
        update_tag,
        common_job_parameters,
    )
    container_instances.sync(
        neo4j_session,
        credentials,
        subscription_id,
        update_tag,
        common_job_parameters,
    )
    firewall.sync(
        neo4j_session,
        credentials,
        subscription_id,
        update_tag,
        common_job_parameters,
    )
    load_balancers.sync(
        neo4j_session,
        credentials,
        subscription_id,
        update_tag,
        common_job_parameters,
    )
    application_gateways.sync(
        neo4j_session,
        credentials,
        subscription_id,
        update_tag,
        common_job_parameters,
    )
    synapse.sync(
        neo4j_session,
        credentials,
        subscription_id,
        update_tag,
        common_job_parameters,
    )
    monitor.sync(
        neo4j_session,
        credentials,
        subscription_id,
        update_tag,
        common_job_parameters,
    )
    security_center.sync(
        neo4j_session,
        credentials,
        subscription_id,
        update_tag,
        common_job_parameters,
    )
    permission_relationships.sync(
        neo4j_session,
        subscription_id,
        update_tag,
        common_job_parameters,
    )


def _sync_tenant(
    neo4j_session: neo4j.Session,
    credentials: "Credentials",
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    logger.info("Syncing Azure Tenant: %s", credentials.tenant_id)
    tenant.sync(
        neo4j_session,
        credentials.tenant_id or "",
        None,
        update_tag,
        common_job_parameters,
    )


def _sync_management_groups(
    neo4j_session: neo4j.Session,
    credentials: "Credentials",
    update_tag: int,
    common_job_parameters: dict,
) -> list[dict]:
    logger.info("Syncing Azure management groups for tenant: %s", credentials.tenant_id)
    return management_groups.sync(
        neo4j_session,
        credentials,
        credentials.tenant_id or "",
        update_tag,
        common_job_parameters,
    )


def _sync_multiple_subscriptions(
    neo4j_session: neo4j.Session,
    credentials: "Credentials",
    tenant_id: str,
    subscriptions: list[dict],
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    logger.info("Syncing Azure subscriptions")

    subscription.sync(
        neo4j_session,
        credentials,
        tenant_id,
        subscriptions,
        update_tag,
        common_job_parameters,
    )

    try:
        for sub in subscriptions:
            logger.info(
                "Syncing Azure Subscription with ID '%s'", sub["subscriptionId"]
            )
            common_job_parameters["AZURE_SUBSCRIPTION_ID"] = sub["subscriptionId"]

            _sync_one_subscription(
                neo4j_session,
                credentials,
                sub["subscriptionId"],
                update_tag,
                common_job_parameters,
            )
    finally:
        common_job_parameters.pop("AZURE_SUBSCRIPTION_ID", None)


@timeit
def start_azure_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "permission_relationships_file": config.permission_relationships_file,
        "azure_permission_relationships_file": config.azure_permission_relationships_file,
    }

    if config.azure_sp_auth:
        if not (
            config.azure_tenant_id
            and config.azure_client_id
            and config.azure_client_secret
        ):
            raise ValueError(
                "Azure Service Principal authentication requested, but tenant ID, client ID, "
                "and client secret were not all provided.",
            )

        credentials = Authenticator().authenticate_sp(
            config.azure_tenant_id,
            config.azure_client_id,
            config.azure_client_secret,
        )
    else:
        credentials = Authenticator().authenticate_cli()

    if not credentials:
        raise RuntimeError(
            "Azure authentication failed. Ensure Azure CLI login or Service Principal credentials are configured.",
        )

    common_job_parameters["TENANT_ID"] = credentials.tenant_id

    _sync_tenant(
        neo4j_session,
        credentials,
        config.update_tag,
        common_job_parameters,
    )
    # IMPORTANT: Azure hierarchy cleanup is deferred like GCP hierarchy cleanup.
    # The upper hierarchy is tenant -> management groups -> subscriptions, while
    # subscription-contained resources are owned by AzureSubscription. Load the
    # current management groups and subscriptions first, then clean stale
    # subscriptions before stale management groups so parent cleanup does not
    # orphan child resources or hierarchy edges. If management-group enumeration
    # fails, skip management-group cleanup for this run to preserve prior data.
    management_groups_synced = False
    management_group_data: list[dict] = []
    try:
        management_group_data = _sync_management_groups(
            neo4j_session,
            credentials,
            config.update_tag,
            common_job_parameters,
        )
        management_groups_synced = True
    except RuntimeError as e:
        logger.warning(
            "Skipping Azure management groups sync. Details: %s",
            e,
        )
    if credentials.tenant_id:
        if config.azure_sync_all_subscriptions:
            subscriptions = subscription.get_all_azure_subscriptions(credentials)

        else:
            sub_id_to_sync = config.azure_subscription_id or credentials.subscription_id
            subscriptions = subscription.get_current_azure_subscription(
                credentials,
                sub_id_to_sync,
            )

        if not subscriptions:
            raise RuntimeError(
                "No Azure subscriptions found. Ensure the credentials have access to at least one subscription.",
            )

        _sync_multiple_subscriptions(
            neo4j_session,
            credentials,
            credentials.tenant_id,
            subscriptions,
            config.update_tag,
            common_job_parameters,
        )
        if management_groups_synced:
            rbac.sync_management_group_role_assignments_for_management_groups(
                neo4j_session,
                credentials,
                management_group_data,
                subscriptions[0]["subscriptionId"],
                config.update_tag,
                common_job_parameters,
            )
            logger.debug("Running deferred Azure management group cleanup")
            management_groups.cleanup(
                neo4j_session,
                common_job_parameters,
                cascade_delete=True,
            )

        for job in AZURE_COMPUTE_ASSET_EXPOSURE_JOBS:
            run_typed_analysis_job(job, neo4j_session, common_job_parameters)

        # DEPRECATED: compatibility migration that swaps the AzureContainerInstance
        # and AzureGroupContainer labels so AzureContainerInstance now labels the
        # individual container and AzureGroupContainer labels the group. Remove in
        # v1.0.0.
        run_analysis_job(
            "azure_container_label_swap_migration.json",
            neo4j_session,
            common_job_parameters,
        )

        try:
            for sub in subscriptions:
                common_job_parameters["AZURE_SUBSCRIPTION_ID"] = sub["subscriptionId"]
                run_typed_analysis_job(
                    AZURE_LB_EXPOSURE,
                    neo4j_session,
                    common_job_parameters,
                )
                run_typed_analysis_job(
                    AZURE_FIREWALL_LB_PROTECTION,
                    neo4j_session,
                    common_job_parameters,
                )
        finally:
            common_job_parameters.pop("AZURE_SUBSCRIPTION_ID", None)
