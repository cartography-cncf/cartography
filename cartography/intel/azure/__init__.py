import logging
from typing import Dict
from typing import List

import neo4j

from cartography.config import Config
from cartography.util import timeit

from . import aks
from . import app_service
from . import compute
from . import container_instances
from . import cosmosdb
from . import data_factory
from . import data_factory_dataset
from . import data_factory_linked_service
from . import data_factory_pipeline
from . import data_lake
from . import event_grid
from . import functions
from . import load_balancers
from . import logic_apps
from . import monitor
from . import network
from . import permission_relationships
from . import rbac
from . import resource_groups
from . import security_center
from . import sql
from . import storage
from . import subscription
from . import tenant
from .util.credentials import Authenticator
from .util.credentials import Credentials

logger = logging.getLogger(__name__)


def _sync_one_subscription(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    container_instances.sync(
        neo4j_session,
        credentials,
        subscription_id,
        update_tag,
        common_job_parameters,
    )
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
    aks.sync(
        neo4j_session,
        credentials,
        subscription_id,
        update_tag,
        common_job_parameters,
    )
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
    load_balancers.sync(
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
    credentials: Credentials,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    logger.info("Syncing Azure Tenant: %s", credentials.tenant_id)
    tenant.sync(neo4j_session, credentials.tenant_id, None, update_tag, common_job_parameters)  # type: ignore


def _sync_multiple_subscriptions(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    tenant_id: str,
    subscriptions: List[Dict],
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    logger.info("Syncing Azure subscriptions")

    subscription.sync(
        neo4j_session,
        tenant_id,
        subscriptions,
        update_tag,
        common_job_parameters,
    )

    for sub in subscriptions:
        logger.info("Syncing Azure Subscription with ID '%s'", sub["subscriptionId"])
        common_job_parameters["AZURE_SUBSCRIPTION_ID"] = sub["subscriptionId"]

        _sync_one_subscription(
            neo4j_session,
            credentials,
            sub["subscriptionId"],
            update_tag,
            common_job_parameters,
        )

    del common_job_parameters["AZURE_SUBSCRIPTION_ID"]


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
