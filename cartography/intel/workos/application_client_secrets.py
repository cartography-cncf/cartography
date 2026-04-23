import logging
from typing import Any

import neo4j
from workos import WorkOSClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.workos.application_client_secret import (
    WorkOSApplicationClientSecretSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: WorkOSClient,
    application_ids: list[str],
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync WorkOS Connect application client secrets.

    :param neo4j_session: Neo4J session for database interface
    :param client: WorkOS API client
    :param application_ids: List of Connect application IDs
    :param common_job_parameters: Common parameters for cleanup jobs
    :return: None
    """
    client_id = common_job_parameters["WORKOS_CLIENT_ID"]
    update_tag = common_job_parameters["UPDATE_TAG"]

    secrets_by_app = get(client, application_ids)
    transformed_secrets = transform(secrets_by_app)
    load_secrets(neo4j_session, transformed_secrets, client_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    client: WorkOSClient,
    application_ids: list[str],
) -> dict[str, list[Any]]:
    """
    Fetch client secrets for each Connect application.

    :param client: WorkOS API client
    :param application_ids: List of Connect application IDs
    :return: Mapping of application ID to list of ApplicationCredentialsListItem
    """
    logger.debug(
        "Fetching WorkOS Connect application client secrets for %d applications",
        len(application_ids),
    )
    secrets_by_app: dict[str, list[Any]] = {}
    for app_id in application_ids:
        secrets_by_app[app_id] = client.connect.list_application_client_secrets(app_id)
    return secrets_by_app


def transform(secrets_by_app: dict[str, list[Any]]) -> list[dict[str, Any]]:
    """
    Transform application client secrets for loading.

    :param secrets_by_app: Mapping of application ID to ApplicationCredentialsListItem list
    :return: Flat list of secret dicts with their parent application ID
    """
    result = []
    for app_id, secrets in secrets_by_app.items():
        for secret in secrets:
            result.append(
                {
                    "id": secret.id,
                    "secret_hint": secret.secret_hint,
                    "last_used_at": secret.last_used_at,
                    "created_at": secret.created_at,
                    "updated_at": secret.updated_at,
                    "application_id": app_id,
                },
            )
    logger.debug("Transformed %d WorkOS application client secrets", len(result))
    return result


@timeit
def load_secrets(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    client_id: str,
    update_tag: int,
) -> None:
    """
    Load application client secrets into Neo4j.
    """
    load(
        neo4j_session,
        WorkOSApplicationClientSecretSchema(),
        data,
        lastupdated=update_tag,
        WORKOS_CLIENT_ID=client_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Cleanup old application client secrets.
    """
    GraphJob.from_node_schema(
        WorkOSApplicationClientSecretSchema(),
        common_job_parameters,
    ).run(neo4j_session)
