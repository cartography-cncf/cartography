import logging
from typing import Dict
from typing import List

import neo4j

from cartography.config import Config
from cartography.util import timeit

from . import compute
from . import cosmosdb
from . import permission_relationships
from . import rbac
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

    try:
        if config.azure_sp_auth:
            credentials = Authenticator().authenticate_sp(
                config.azure_tenant_id,
                config.azure_client_id,
                config.azure_client_secret,
            )
        else:
            credentials = Authenticator().authenticate_cli()

    except Exception as e:
        logger.error(
            (
                "Unable to authenticate with Azure Service Principal, an error occurred: %s."
                "Make sure your credentials (CLI or Service Principal) are configured correctly."
            ),
            e,
        )
        return

    if not credentials:
        return

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
            logger.warning(
                "No valid Azure credentials are found. No Azure subscriptions can be synced. Exiting Azure sync stage.",
            )
            return

        _sync_multiple_subscriptions(
            neo4j_session,
            credentials,
            credentials.tenant_id,
            subscriptions,
            config.update_tag,
            common_job_parameters,
        )
