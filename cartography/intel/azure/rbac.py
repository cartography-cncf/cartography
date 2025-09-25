import json
import logging
from typing import Dict
from typing import List

import neo4j
from azure.core.exceptions import HttpResponseError
from azure.mgmt.authorization import AuthorizationManagementClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.azure.rbac import AzurePermissionsSchema
from cartography.models.azure.rbac import AzureRoleAssignmentSchema
from cartography.models.azure.rbac import AzureRoleDefinitionSchema
from cartography.util import timeit

from .util.credentials import Credentials

logger = logging.getLogger(__name__)


def get_client(
    credentials: Credentials,
    subscription_id: str,
) -> AuthorizationManagementClient:
    """
    Get Azure Authorization Management Client for RBAC operations
    """
    client = AuthorizationManagementClient(credentials.credential, subscription_id)
    return client


def get_role_assignments(
    credentials: Credentials,
    subscription_id: str,
) -> List[Dict]:
    """
    Fetch all role assignments for a subscription
    """
    try:
        client = get_client(credentials, subscription_id)
        role_assignments = list(client.role_assignments.list_for_subscription())

        result = []
        for assignment in role_assignments:
            assignment_dict = assignment.as_dict()
            assignment_dict["subscription_id"] = subscription_id
            result.append(assignment_dict)

        return result

    except HttpResponseError as e:
        logger.warning(
            f"Error while retrieving role assignments for subscription {subscription_id}: {e}"
        )
        return []


def get_role_definitions_by_ids(
    credentials: Credentials,
    subscription_id: str,
    role_definition_ids: List[str],
) -> List[Dict]:
    """
    Fetch specific role definitions by their IDs (more efficient than fetching all)
    """
    try:
        client = get_client(credentials, subscription_id)
        result = []

        # Extract unique role definition IDs
        unique_role_ids = list(set(role_definition_ids))
        logger.info(
            f"Fetching {len(unique_role_ids)} unique role definitions out of {len(role_definition_ids)} total role assignments"
        )

        for role_id in unique_role_ids:
            try:
                # Use get_by_id with the full role definition ID
                # Format: /subscriptions/{guid}/providers/Microsoft.Authorization/roleDefinitions/{roleDefinitionId}
                role_definition = client.role_definitions.get_by_id(role_id)
                definition_dict = role_definition.as_dict()
                definition_dict["subscription_id"] = subscription_id
                result.append(definition_dict)

            except HttpResponseError as e:
                logger.warning(f"Error fetching role definition {role_id}: {e}")
                continue

        return result

    except HttpResponseError as e:
        logger.warning(
            f"Error while retrieving role definitions for subscription {subscription_id}: {e}"
        )
        return []


def extract_role_definition_ids(role_assignments: List[Dict]) -> List[str]:
    """
    Extract unique role definition IDs from role assignments
    """
    role_ids = []
    for assignment in role_assignments:
        role_definition_id = assignment.get("role_definition_id")
        if role_definition_id:
            role_ids.append(role_definition_id)
    return role_ids


def transform_role_definitions(
    role_definitions: List[Dict],
) -> List[Dict]:
    """
    Transform role definition data for Neo4j ingestion
    """
    result = []

    for definition in role_definitions:
        # Generate permission IDs for this role definition
        permission_ids = []
        permissions = definition.get("permissions", [])
        for i in range(len(permissions)):
            permission_id = f"{definition['id']}/permissions/{i}"
            permission_ids.append(permission_id)

        transformed = {
            "id": definition["id"],
            "name": definition.get("name"),
            "type": definition.get("type"),
            "roleName": definition.get("role_name"),
            "description": definition.get("description"),
            "assignableScopes": definition.get("assignable_scopes"),
            "AZURE_SUBSCRIPTION_ID": definition.get("subscription_id"),
            "permission_ids": permission_ids,
        }
        result.append(transformed)

    return result


def transform_permissions(
    role_definitions: List[Dict],
) -> List[Dict]:
    """
    Transform permissions data for Neo4j ingestion as separate nodes
    """
    result = []

    for definition in role_definitions:
        permissions = definition.get("permissions", [])
        if not permissions:
            continue

        for i, permission_set in enumerate(permissions):
            # Create unique ID for this permission set
            permission_id = f"{definition['id']}/permissions/{i}"

            transformed = {
                "id": permission_id,
                "actions": permission_set.get("actions", []),
                "not_actions": permission_set.get("not_actions", []),
                "data_actions": permission_set.get("data_actions", []),
                "not_data_actions": permission_set.get("not_data_actions", []),
                "AZURE_SUBSCRIPTION_ID": definition.get("subscription_id"),
            }
            result.append(transformed)

    return result


def transform_role_assignments(
    role_assignments: List[Dict],
) -> List[Dict]:
    """
    Transform role assignment data for Neo4j ingestion as nodes
    """
    result = []

    for assignment in role_assignments:
        # CComplex object for storing in Neo4j, temporarily store as JSON string
        condition = assignment.get("condition")
        condition_json = json.dumps(condition) if condition else None

        transformed = {
            "id": assignment.get("id"),
            "name": assignment.get("name"),
            "type": assignment.get("type"),
            "principalId": assignment.get("principal_id"),
            "principalType": assignment.get("principal_type"),
            "roleDefinitionId": assignment.get("role_definition_id"),
            "scope": assignment.get("scope"),
            "scopeType": assignment.get("scope_type"),
            "createdOn": assignment.get("created_on"),
            "updatedOn": assignment.get("updated_on"),
            "createdBy": assignment.get("created_by"),
            "updatedBy": assignment.get("updated_by"),
            "condition": condition_json,
            "description": assignment.get("description"),
            "delegatedManagedIdentityResourceId": assignment.get(
                "delegated_managed_identity_resource_id"
            ),
            "AZURE_SUBSCRIPTION_ID": assignment.get("subscription_id"),
        }
        result.append(transformed)

    return result


def load_role_definitions(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureRoleDefinitionSchema(),
        data,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


def load_role_assignments(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureRoleAssignmentSchema(),
        data,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


def load_permissions(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzurePermissionsSchema(),
        data,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


def cleanup_role_definitions(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    GraphJob.from_node_schema(AzureRoleDefinitionSchema(), common_job_parameters).run(
        neo4j_session
    )


def cleanup_role_assignments(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    GraphJob.from_node_schema(AzureRoleAssignmentSchema(), common_job_parameters).run(
        neo4j_session
    )


def cleanup_permissions(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    GraphJob.from_node_schema(AzurePermissionsSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Main sync function for Azure RBAC data with role assignments as nodes and standard relationships
    """
    logger.info("Syncing Azure RBAC for subscription '%s'.", subscription_id)

    try:
        # GET
        role_assignments = get_role_assignments(credentials, subscription_id)

        # Intermediate step - to get the required role definitions
        role_definition_ids = extract_role_definition_ids(role_assignments)
        role_definitions = get_role_definitions_by_ids(
            credentials, subscription_id, role_definition_ids
        )

        # TRANSFORM
        transformed_definitions = transform_role_definitions(role_definitions)
        transformed_assignments = transform_role_assignments(role_assignments)
        transformed_permissions = transform_permissions(role_definitions)
        logger.info(f"Transformed permissions: {transformed_permissions}")

        # LOAD
        load_permissions(
            neo4j_session, transformed_permissions, subscription_id, update_tag
        )
        load_role_definitions(
            neo4j_session, transformed_definitions, subscription_id, update_tag
        )
        load_role_assignments(
            neo4j_session, transformed_assignments, subscription_id, update_tag
        )

        # CLEANUp
        cleanup_permissions(neo4j_session, common_job_parameters)
        cleanup_role_definitions(neo4j_session, common_job_parameters)
        cleanup_role_assignments(neo4j_session, common_job_parameters)

    except Exception as e:
        logger.error(
            f"Error during Azure RBAC sync for subscription {subscription_id}: {e}"
        )
        raise
