import logging
import os
import re
from string import Template
from typing import Any

import neo4j
import yaml

from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.models.azure.permission_relationships import AzurePermissionMatchLink
from cartography.util import timeit

logger = logging.getLogger(__name__)


def resolve_azure_scope(scope: str) -> str:
    """
    Resolve Azure scope to follow the standard hierarchy pattern:
    /subscriptions/{subscriptionId}/resourcegroups/{resourceGroupName}/providers/{providerName}/{resourceType}/{resourceSubType1}/{resourceSubType2}/{resourceName}/

    If providers is given in scope, return as is. Meaning its already resource level.
    If not, add /* to the end to match any resource under that scope.
    """
    if "/providers/" in scope:
        return scope

    if not scope.endswith("/"):
        scope = scope + "/"

    scope = scope + "*"

    return scope


def compile_azure_regex(item: str) -> re.Pattern:
    if isinstance(item, str):
        # Escape special regex characters and convert Azure wildcards
        item = item.replace(".", "\\.").replace("*", ".*").replace("?", ".?")
        try:
            return re.compile(item, flags=re.IGNORECASE)
        except re.error:
            logger.warning(f"Azure regex did not compile for {item}")
            # Return a regex that matches nothing -> no false positives
            return re.compile("", flags=re.IGNORECASE)
    else:
        return item


def evaluate_clause(clause: str, match: str) -> bool:
    """Evaluates a clause in Azure RBAC. Clauses can be Azure actions, not_actions, data_actions, not_data_actions, or scopes.

    Arguments:
        clause {str, re.Pattern} -- The clause you are evaluating against. Clauses can use
            variable length wildcards (*)
            fixed length wildcards (?)
        match {str} -- The item to match against.

    Returns:
        [bool] -- True if the clause matched, False otherwise
    """
    result = compile_azure_regex(clause).fullmatch(match)
    return result is not None


def evaluate_scope_for_resource(assignment: dict, resource_id: str) -> bool:
    if "scope" not in assignment:
        return False
    scope = assignment["scope"]
    # scope is now a compiled regex pattern
    return evaluate_clause(scope, resource_id)


def evaluate_action_for_permission(permissions: dict, permission: str) -> bool:
    if not permissions["actions"]:
        return False
    for clause in permissions["actions"]:
        if evaluate_clause(clause, permission):
            return True
    return False


def evaluate_notaction_for_permission(permissions: dict, permission: str) -> bool:
    if not permissions["not_actions"]:
        return False  # Even tough most likely to not occur ever, should we still make this true?
    for clause in permissions["not_actions"]:
        if evaluate_clause(clause, permission):
            return True
    return False


def evaluate_dataaction_for_permission(permissions: dict, permission: str) -> bool:
    if not permissions["data_actions"]:
        return False
    for clause in permissions["data_actions"]:
        if evaluate_clause(clause, permission):
            return True
    return False


def evaluate_notdataaction_for_permission(permissions: dict, permission: str) -> bool:
    if not permissions["not_data_actions"]:
        return False  # Even tough most likely to not occur ever, should we still make this true?
    for clause in permissions["not_data_actions"]:
        if evaluate_clause(clause, permission):
            return True
    return False


def evaluate_role_assignment_for_permissions(
    assignment_data: dict[str, Any],
    permissions: list[str],
    resource_id: str,
) -> bool:
    permissions_dict = assignment_data["permissions"]
    scope = assignment_data["scope"]

    # Check scope matching
    if not evaluate_scope_for_resource({"scope": scope}, resource_id):
        return False

    for permission in permissions:
        # Check actions
        if not evaluate_notaction_for_permission(permissions_dict, permission):
            if evaluate_action_for_permission(permissions_dict, permission):
                return True

        # Check data actions
        if not evaluate_notdataaction_for_permission(permissions_dict, permission):
            if evaluate_dataaction_for_permission(permissions_dict, permission):
                return True

    return False


def principal_allowed_on_resource(
    role_assignments: dict[str, Any],
    resource_id: str,
    permissions: list[str],
) -> bool:
    if not isinstance(permissions, list):
        raise ValueError("permissions is not a list")
    # This will be divided into two sections to furhter incorporate the deny assignments logic, so that the functions building on top really shouldnt change
    for _, assignment_data in role_assignments.items():
        if evaluate_role_assignment_for_permissions(
            assignment_data, permissions, resource_id
        ):
            return True

    return False


def calculate_permission_relationships(
    principals: dict[str, Any],
    resource_ids: list[str],
    permissions: list[str],
) -> list[dict[str, Any]]:
    allowed_mappings: list[dict[str, Any]] = []
    for resource_id in resource_ids:
        for principal_id, role_assignments in principals.items():
            if principal_allowed_on_resource(
                role_assignments, resource_id, permissions
            ):
                # Get the principal type from the first role assignment
                principal_type = next(iter(role_assignments.values()))["principal_type"]
                allowed_mappings.append(
                    {
                        "principal_id": principal_id,
                        "resource_id": resource_id,
                        "principal_type": principal_type,
                    }
                )
    return allowed_mappings


@timeit
def get_principals_for_subscription(
    neo4j_session: neo4j.Session, subscription_id: str
) -> dict[str, Any]:
    get_principals_query = """
    MATCH
    (sub:AzureSubscription{id: $SubscriptionId})-[:RESOURCE]->
    (assignment:AzureRoleAssignment)-[:ROLE_ASSIGNED]->
    (definition:AzureRoleDefinition)-[:HAS_PERMISSIONS]->
    (permissions:AzurePermissions)
    MATCH
    (principal)-[:HAS_ROLE_ASSIGNMENT]->(assignment)
    WHERE principal:EntraUser OR principal:EntraGroup OR principal:EntraServicePrincipal
    RETURN
    DISTINCT principal.id as principal_id, assignment.id as assignment_id,
    assignment.scope as assignment_scope, collect(permissions) as permissions,
    assignment.principal_type as principal_type
    """

    results = neo4j_session.run(get_principals_query, SubscriptionId=subscription_id)

    principals: dict[str, Any] = {}
    for r in results:
        principal_id = r["principal_id"]
        assignment_id = r["assignment_id"]
        assignment_scope = r["assignment_scope"]
        permissions_nodes = r["permissions"]
        principal_type = r["principal_type"]

        if principal_id not in principals:
            principals[principal_id] = {}

        # Compile permissions from nodes
        compiled_permissions = compile_permissions_from_nodes(permissions_nodes)
        compiled_scope = compile_azure_regex(resolve_azure_scope(assignment_scope))

        principals[principal_id][assignment_id] = {
            "permissions": compiled_permissions,
            "scope": compiled_scope,
            "principal_type": principal_type,
        }

    return principals


def compile_permissions_from_nodes(permissions_nodes: list[dict]) -> dict[str, Any]:
    permissions: dict[str, list[str]] = {
        "actions": [],
        "not_actions": [],
        "data_actions": [],
        "not_data_actions": [],
    }

    for permission_node in permissions_nodes:
        permissions["actions"].extend(permission_node.get("actions", []))
        permissions["not_actions"].extend(permission_node.get("not_actions", []))
        permissions["data_actions"].extend(permission_node.get("data_actions", []))
        permissions["not_data_actions"].extend(
            permission_node.get("not_data_actions", [])
        )

    return compile_permissions(permissions)


def compile_permissions(permissions: dict[str, Any]) -> dict[str, Any]:
    action_types = ["actions", "not_actions", "data_actions", "not_data_actions"]
    compiled_permissions = {}

    for action_type in action_types:
        compiled_permissions[action_type] = [
            compile_azure_regex(item) for item in permissions[action_type]
        ]

    return compiled_permissions


@timeit
def get_resource_ids(
    neo4j_session: neo4j.Session, subscription_id: str, target_label: str
) -> list[str]:
    get_resource_query = Template(
        """
    MATCH (sub:AzureSubscription{id:$SubscriptionId})-[:RESOURCE]->(resource:$node_label)
    RETURN resource.id as resource_id
    """,
    )
    get_resource_query_template = get_resource_query.safe_substitute(
        node_label=target_label,
    )
    results = neo4j_session.run(
        get_resource_query_template,
        SubscriptionId=subscription_id,
    )
    resource_ids = [r["resource_id"] for r in results]
    return resource_ids


def parse_permission_relationships_file(file_path: str) -> list[dict[str, Any]]:
    try:
        if not os.path.isabs(file_path):
            file_path = os.path.join(os.getcwd(), file_path)
        with open(file_path) as f:
            relationship_mapping = yaml.load(f, Loader=yaml.FullLoader)
        return relationship_mapping or []
    except FileNotFoundError:
        logger.warning(
            f"Azure permission relationships file {file_path} not found, skipping sync stage {__name__}. "
            f"If you want to run this sync, please explicitly set a value for --azure-permission-relationships-file in the "
            f"command line interface."
        )
        return []


def is_valid_azure_rpr(rpr: dict[str, Any]) -> bool:
    required_fields = ["permissions", "relationship_name", "target_label"]
    for field in required_fields:
        if field not in rpr:
            return False
    return True


def transform_mappings(principal_mappings: list[dict]) -> dict[str, list[dict]]:
    """
    Transform principal mappings by grouping them by principal type.
    Adds 'Entra' prefix to principal types to match Entra node labels.
    """
    # Expected principal types for validation
    expected_types = {"User", "Group", "ServicePrincipal"}

    mappings_by_type: dict[str, list[dict]] = {}

    for mapping in principal_mappings:
        assignment_principal_type = mapping["principal_type"]

        # Validate principal type, no silent failure in case of change in expected principal types from MS
        if assignment_principal_type not in expected_types:
            logger.warning(
                f"Unknown principal type '{assignment_principal_type}' encountered - skipping permission relationships sync for this principal type."
            )
            continue

        # Add 'Entra' prefix to match Entra node labels
        entra_principal_type = f"Entra{assignment_principal_type}"

        if entra_principal_type not in mappings_by_type:
            mappings_by_type[entra_principal_type] = []
        mappings_by_type[entra_principal_type].append(mapping)

    return mappings_by_type


@timeit
def load_principal_mappings(
    neo4j_session: neo4j.Session,
    mappings_by_type: dict[str, list[dict]],
    node_label: str,
    relationship_name: str,
    update_tag: int,
    subscription_id: str,
) -> None:
    if not mappings_by_type:
        return

    # Iterate over each principal type
    principal_types = ["EntraUser", "EntraGroup", "EntraServicePrincipal"]

    for principal_type in principal_types:
        type_mappings = mappings_by_type.get(principal_type, [])

        if not type_mappings:
            continue

        # Create MatchLink schema with dynamic attributes
        matchlink_schema = AzurePermissionMatchLink(
            source_node_label=principal_type,
            target_node_label=node_label,
            rel_label=relationship_name,
        )

        logger.info(
            f"Loading {len(type_mappings)} {relationship_name} relationships for {principal_type} -> {node_label}"
        )

        load_matchlinks(
            neo4j_session,
            matchlink_schema,
            type_mappings,
            lastupdated=update_tag,
            _sub_resource_label="AzureSubscription",
            _sub_resource_id=subscription_id,
        )


@timeit
def cleanup_rpr(
    neo4j_session: neo4j.Session,
    node_label: str,
    relationship_name: str,
    update_tag: int,
    subscription_id: str,
) -> None:
    logger.info(
        "Cleaning up relationship '%s' for node label '%s'",
        relationship_name,
        node_label,
    )

    # Clean up for each principal type
    principal_types = ["EntraUser", "EntraGroup", "EntraServicePrincipal"]
    for principal_type in principal_types:
        # Create MatchLink schema with dynamic attributes
        matchlink_schema = AzurePermissionMatchLink(
            source_node_label=principal_type,
            target_node_label=node_label,
            rel_label=relationship_name,
        )

        GraphJob.from_matchlink(
            matchlink_schema,
            "AzureSubscription",
            subscription_id,
            update_tag,
        ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info(
        "Syncing Azure Permission Relationships for subscription '%s'.", subscription_id
    )

    pr_file = common_job_parameters.get("azure_permission_relationships_file")
    if not pr_file:
        logger.warning(
            "Azure permission relationships file was not specified, skipping. If this is not expected, please check your "
            "value of --azure-permission-relationships-file"
        )
        return

    # 1. GET - Fetch all Azure principals in suitable dict format
    principals = get_principals_for_subscription(neo4j_session, subscription_id)

    # 2. PARSE - Parse relationship file
    relationship_mapping = parse_permission_relationships_file(pr_file)

    # 3. EVALUATE - Evaluate each relationship and resource ID
    for rpr in relationship_mapping:
        if not is_valid_azure_rpr(rpr):
            logger.error(f"Invalid permission relationship configuration: {rpr}")
            continue

        target_label = rpr["target_label"]
        relationship_name = rpr["relationship_name"]
        permissions = rpr["permissions"]

        resource_ids = get_resource_ids(neo4j_session, subscription_id, target_label)

        logger.info(
            f"Evaluating relationship '{relationship_name}' for resource type '{target_label}'"
        )
        matches = calculate_permission_relationships(
            principals, resource_ids, permissions
        )

        matches_by_type = transform_mappings(matches)

        load_principal_mappings(
            neo4j_session,
            matches_by_type,
            target_label,
            relationship_name,
            update_tag,
            subscription_id,
        )
        cleanup_rpr(
            neo4j_session,
            target_label,
            relationship_name,
            update_tag,
            subscription_id,
        )

    logger.info(
        f"Completed Azure Permission Relationships sync for subscription {subscription_id}"
    )
