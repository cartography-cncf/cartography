import logging
import os
import re
from string import Template
from typing import Any
from typing import Dict
from typing import List

import neo4j
import yaml

from cartography.graph.statement import GraphStatement
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
    result = compile_azure_regex(clause).fullmatch(match.lower())
    return result is not None


def evaluate_scope_for_resource(assignment: Dict, resource_id: str) -> bool:
    if "scope" not in assignment:
        return False
    scope = assignment["scope"]
    # scope is now a compiled regex pattern
    return evaluate_clause(scope, resource_id)


def evaluate_action_for_permission(permissions: Dict, permission: str) -> bool:
    if not permissions["actions"]:
        return False
    for clause in permissions["actions"]:
        if evaluate_clause(clause, permission):
            return True
    return False


def evaluate_notaction_for_permission(permissions: Dict, permission: str) -> bool:
    if not permissions["not_actions"]:
        return False  # Even tough most likely to not occur ever, should we still make this true?
    for clause in permissions["not_actions"]:
        if evaluate_clause(clause, permission):
            return True
    return False


def evaluate_dataaction_for_permission(permissions: Dict, permission: str) -> bool:
    if not permissions["data_actions"]:
        return False
    for clause in permissions["data_actions"]:
        if evaluate_clause(clause, permission):
            return True
    return False


def evaluate_notdataaction_for_permission(permissions: Dict, permission: str) -> bool:
    if not permissions["not_data_actions"]:
        return False  # Even tough most likely to not occur ever, should we still make this true?
    for clause in permissions["not_data_actions"]:
        if evaluate_clause(clause, permission):
            return True
    return False


def compile_permissions(permissions: Dict[str, Any]) -> Dict[str, Any]:
    action_types = ["actions", "not_actions", "data_actions", "not_data_actions"]
    compiled_permissions = {}

    for action_type in action_types:
        compiled_permissions[action_type] = [
            compile_azure_regex(item) for item in permissions[action_type]
        ]

    return compiled_permissions


def evaluate_role_assignment_for_permissions(
    assignment_data: Dict[str, Any],
    permissions: List[str],
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
    role_assignments: Dict[str, Any],
    resource_id: str,
    permissions: List[str],
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
    principals: Dict[str, Any],
    resource_ids: List[str],
    permissions: List[str],
) -> List[Dict[str, Any]]:
    allowed_mappings: List[Dict[str, Any]] = []
    for resource_id in resource_ids:
        for principal_id, role_assignments in principals.items():
            if principal_allowed_on_resource(
                role_assignments, resource_id, permissions
            ):
                allowed_mappings.append(
                    {
                        "principal_id": principal_id,
                        "resource_id": resource_id,
                    }
                )
    return allowed_mappings


def get_principals_for_subscription(
    neo4j_session: neo4j.Session, subscription_id: str
) -> Dict[str, Any]:
    get_principals_query = """
    MATCH
    (sub:AzureSubscription{id: $SubscriptionId})-[:RESOURCE]->
    (assignment:AzureRoleAssignment)-[:ROLE_ASSIGNED]->
    (definition:AzureRoleDefinition)-[:HAS_PERMISSIONS]->
    (permissions:AzurePermissions)
    MATCH
    (principal)-[:HAS_ROLE_ASSIGNMENT]->(assignment)
    RETURN
    DISTINCT principal.id as principal_id, assignment.id as assignment_id,
    assignment.scope as assignment_scope, collect(permissions) as permissions,
    assignment.principal_type as principal_type
    """

    results = neo4j_session.run(get_principals_query, SubscriptionId=subscription_id)

    principals: Dict[str, Any] = {}
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


def compile_permissions_from_nodes(permissions_nodes: List[Dict]) -> Dict[str, Any]:
    permissions: Dict[str, List[str]] = {
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


def get_resource_ids(
    neo4j_session: neo4j.Session, subscription_id: str, target_label: str
) -> List[str]:
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


def parse_permission_relationships_file(file_path: str) -> List[Dict[str, Any]]:
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


def is_valid_azure_rpr(rpr: Dict[str, Any]) -> bool:
    required_fields = ["permissions", "relationship_name", "target_label"]
    for field in required_fields:
        if field not in rpr:
            return False
    return True


def load_principal_mappings(
    neo4j_session: neo4j.Session,
    principal_mappings: List[Dict],
    node_label: str,
    relationship_name: str,
    update_tag: int,
) -> None:
    if not principal_mappings:
        return

    map_policy_query = Template(
        """
        UNWIND $Mapping as mapping
        MATCH (principal{id:mapping.principal_id})
        MATCH (resource:$node_label{id:mapping.resource_id})
        MERGE (principal)-[r:$relationship_name]->(resource)
        SET r.lastupdated = $azure_update_tag
        """,
    )

    map_policy_query_template = map_policy_query.safe_substitute(
        node_label=node_label,
        relationship_name=relationship_name,
    )
    neo4j_session.run(
        map_policy_query_template,
        Mapping=principal_mappings,
        azure_update_tag=update_tag,
    )


def cleanup_rpr(
    neo4j_session: neo4j.Session,
    node_label: str,
    relationship_name: str,
    update_tag: int,
    current_azure_id: str,
) -> None:
    logger.info(
        "Cleaning up relationship '%s' for node label '%s'",
        relationship_name,
        node_label,
    )
    cleanup_rpr_query = Template(
        """
        MATCH (:AzureSubscription{id: $AZURE_ID})-[:RESOURCE]->(principal)-[r:$relationship_name]->
        (resource:$node_label)
        WHERE r.lastupdated <> $UPDATE_TAG
        AND (principal:EntraUser OR principal:EntraGroup OR principal:EntraApplication)
        WITH r LIMIT $LIMIT_SIZE  DELETE (r) return COUNT(*) as TotalCompleted
        """,
    )
    cleanup_rpr_query_template = cleanup_rpr_query.safe_substitute(
        node_label=node_label,
        relationship_name=relationship_name,
    )

    statement = GraphStatement(
        cleanup_rpr_query_template,
        {"UPDATE_TAG": update_tag, "AZURE_ID": current_azure_id},  # Azure id figure out
        True,
        1000,
        parent_job_name=f"{relationship_name}:{node_label}",
        parent_job_sequence_num=1,
    )
    statement.run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
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

        load_principal_mappings(
            neo4j_session,
            matches,
            target_label,
            relationship_name,
            update_tag,
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
