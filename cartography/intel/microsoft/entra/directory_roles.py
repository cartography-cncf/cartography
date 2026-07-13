import logging
from typing import Any

import neo4j
from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.unified_role_assignment import UnifiedRoleAssignment
from msgraph.generated.models.unified_role_definition import UnifiedRoleDefinition

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.microsoft.entra.utils import (
    get_paginated_values_with_expired_page_retry,
)
from cartography.models.microsoft.entra.role_assignment import EntraRoleAssignmentSchema
from cartography.models.microsoft.entra.role_definition import EntraRoleDefinitionSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def get_role_definitions(
    client: GraphServiceClient,
) -> list[UnifiedRoleDefinition]:
    """
    Fetch all Entra directory role definitions from the Microsoft Graph unified
    RBAC endpoint, following pagination and restarting on expired page tokens.
    """
    builder = client.role_management.directory.role_definitions
    return await get_paginated_values_with_expired_page_retry(
        lambda: builder.get(),
        lambda next_link: builder.with_url(next_link).get(),
        "Entra directory role definitions",
    )


@timeit
async def get_role_assignments(
    client: GraphServiceClient,
) -> list[UnifiedRoleAssignment]:
    """
    Fetch all Entra directory role assignments from the Microsoft Graph unified
    RBAC endpoint, following pagination and restarting on expired page tokens.
    """
    builder = client.role_management.directory.role_assignments
    return await get_paginated_values_with_expired_page_retry(
        lambda: builder.get(),
        lambda next_link: builder.with_url(next_link).get(),
        "Entra directory role assignments",
    )


def transform_role_definitions(
    role_definitions: list[UnifiedRoleDefinition],
) -> list[dict[str, Any]]:
    """
    Transform Entra role definitions for graph loading.
    """
    result = []
    for role_definition in role_definitions:
        result.append(
            {
                "id": role_definition.id,
                "display_name": role_definition.display_name,
                "description": role_definition.description,
                "is_built_in": role_definition.is_built_in,
                "is_enabled": role_definition.is_enabled,
                "template_id": role_definition.template_id,
            }
        )
    return result


def transform_role_assignments(
    role_assignments: list[UnifiedRoleAssignment],
) -> list[dict[str, Any]]:
    """
    Transform Entra role assignments for graph loading.
    """
    result = []
    for role_assignment in role_assignments:
        result.append(
            {
                "id": role_assignment.id,
                "role_definition_id": role_assignment.role_definition_id,
                "principal_id": role_assignment.principal_id,
                "directory_scope_id": role_assignment.directory_scope_id,
                "app_scope_id": role_assignment.app_scope_id,
            }
        )
    return result


@timeit
def load_role_definitions(
    neo4j_session: neo4j.Session,
    role_definitions: list[dict[str, Any]],
    update_tag: int,
    tenant_id: str,
) -> None:
    load(
        neo4j_session,
        EntraRoleDefinitionSchema(),
        role_definitions,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


@timeit
def load_role_assignments(
    neo4j_session: neo4j.Session,
    role_assignments: list[dict[str, Any]],
    update_tag: int,
    tenant_id: str,
) -> None:
    load(
        neo4j_session,
        EntraRoleAssignmentSchema(),
        role_assignments,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


@timeit
def cleanup_directory_roles(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    """
    Delete stale Entra role assignments and role definitions (and their
    relationships) that were not updated in the last sync.
    """
    GraphJob.from_node_schema(EntraRoleAssignmentSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(EntraRoleDefinitionSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
async def sync_entra_directory_roles(
    neo4j_session: neo4j.Session,
    tenant_id: str,
    client_id: str,
    client_secret: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync Entra directory role definitions and role assignments to the graph.

    :param neo4j_session: Neo4j session
    :param tenant_id: Entra tenant ID
    :param client_id: Azure application client ID
    :param client_secret: Azure application client secret
    :param update_tag: Update tag for tracking data freshness
    :param common_job_parameters: Common job parameters for cleanup
    """
    credential = ClientSecretCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
    )
    client = GraphServiceClient(
        credential,
        scopes=["https://graph.microsoft.com/.default"],
    )

    # Role definitions are the targets of role assignments, so load them first.
    role_definitions = await get_role_definitions(client)
    load_role_definitions(
        neo4j_session,
        transform_role_definitions(role_definitions),
        update_tag,
        tenant_id,
    )
    logger.info("Loaded %d Entra role definitions", len(role_definitions))

    role_assignments = await get_role_assignments(client)
    load_role_assignments(
        neo4j_session,
        transform_role_assignments(role_assignments),
        update_tag,
        tenant_id,
    )
    logger.info("Loaded %d Entra role assignments", len(role_assignments))

    cleanup_directory_roles(neo4j_session, common_job_parameters)
