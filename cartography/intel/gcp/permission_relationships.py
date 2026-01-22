import logging
import os
import re
from string import Template
from typing import Any

import neo4j
import yaml

from cartography.client.core.tx import load_matchlinks
from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.client.core.tx import read_list_of_values_tx
from cartography.graph.job import GraphJob
from cartography.models.gcp.permission_relationships import GCPPermissionMatchLink
from cartography.util import timeit

logger = logging.getLogger(__name__)


def resolve_gcp_scope(scope: str, project_id: str) -> str:
    """
    Resolve GCP scope to follow the standard hierarchy pattern.

    Process breakdown:
    - If scope starts with cloudresourcemanager.googleapis.com, return project/{project_id}/* (ORG,FOLDER,PROJECT)
    - Otherwise, return project/{project_id}/resource/{resource_id} where resource_id is scope.split("/")[-1]

    Typical Scope Examples:
    - ORG: //cloudresourcemanager.googleapis.com/organizations/{id}
    - FOLDER: //cloudresourcemanager.googleapis.com/folders/{id}
    - PROJECT: //cloudresourcemanager.googleapis.com/projects/{id}
    - BUCKET: //storage.googleapis.com/buckets/{bucket_name}
    - INSTANCE: //compute.googleapis.com/projects/{project_id}/zones/{zone}/instances/{instance_id}
    """
    if "cloudresourcemanager.googleapis.com" in scope:
        return f"project/{project_id}/*"

    return f"project/{project_id}/resource/{scope.split('/')[-1]}"


def compile_gcp_regex(item: str) -> re.Pattern:
    # Escape special regex characters
    item = item.replace(".", "\\.").replace("*", ".*")
    try:
        return re.compile(item, flags=re.IGNORECASE)
    except re.error:
        logger.warning(f"GCP regex did not compile for {item}")
        # Return a regex that matches nothing -> no false positives
        return re.compile("", flags=re.IGNORECASE)


def evaluate_clause(clause: re.Pattern, match: str) -> bool:
    """
    Evaluates a clause in GCP IAM. Clauses can be permissions, denied permissions, or scopes.

    Arguments:
        clause {re.Pattern} -- The compiled regex pattern to evaluate against. Clauses can use
            variable length wildcards (*)
        match {str} -- The item to match against.

    Returns:
        [bool] -- True if the clause matched, False otherwise
    """
    result = clause.fullmatch(match)
    return result is not None


def evaluate_scope_for_resource(assignment: dict, resource_scope: str) -> bool:
    scope = assignment["scope"]
    # scope is now a compiled regex pattern
    return evaluate_clause(scope, resource_scope)


def evaluate_denied_permission_for_permission(
    permissions: dict, permission: str
) -> bool:
    for clause in permissions["denied_permissions"]:
        if evaluate_clause(clause, permission):
            return True
    return False


def evaluate_permission_for_permission(permissions: dict, permission: str) -> bool:
    for clause in permissions["permissions"]:
        if evaluate_clause(clause, permission):
            return True
    return False


def evaluate_policy_binding_for_permissions(
    assignment_data: dict[str, Any],
    permissions: list[str],
    resource_scope: str,
) -> bool:
    permissions_dict = assignment_data["permissions"]
    scope = assignment_data["scope"]

    # Level 1: Check scope matching
    if not evaluate_scope_for_resource({"scope": scope}, resource_scope):
        return False

    for permission in permissions:
        # Level 2: Check denied permissions
        if not evaluate_denied_permission_for_permission(permissions_dict, permission):
            # Level 3: Check allowed permissions
            if evaluate_permission_for_permission(permissions_dict, permission):
                return True

    return False


def principal_allowed_on_resource(
    policy_bindings: dict[str, Any],
    resource_scope: str,
    permissions: list[str],
) -> bool:
    for _, assignment_data in policy_bindings.items():
        if evaluate_policy_binding_for_permissions(
            assignment_data, permissions, resource_scope
        ):
            return True

    return False


def calculate_permission_relationships(
    principals: dict[str, Any],
    resource_dict: dict[str, str],
    permissions: list[str],
) -> list[dict[str, Any]]:
    allowed_mappings: list[dict[str, Any]] = []
    for resource_id, resource_scope in resource_dict.items():
        for principal_email, policy_bindings in principals.items():
            if principal_allowed_on_resource(
                policy_bindings, resource_scope, permissions
            ):
                allowed_mappings.append(
                    {
                        "principal_email": principal_email,
                        "resource_id": resource_id,
                    }
                )
    return allowed_mappings


@timeit
def get_principals_for_project(
    neo4j_session: neo4j.Session, project_id: str
) -> dict[str, Any]:
    """
    Get all principals (users, service accounts, groups) with their policy bindings
    for a given GCP project.
    """
    get_principals_query = """
    MATCH
    (project:GCPProject{id: $ProjectId})-[:RESOURCE]->
    (binding:GCPPolicyBinding)-[:GRANTS_ROLE]->
    (role:GCPRole)
    MATCH
    (principal:GCPPrincipal)-[:HAS_ALLOW_POLICY]->(binding)
    WHERE binding.has_condition = false
    RETURN
    DISTINCT principal.email as principal_email, binding.id as binding_id,
    binding.resource as binding_resource, role.permissions as role_permissions
    """

    results = neo4j_session.execute_read(
        read_list_of_dicts_tx,
        get_principals_query,
        ProjectId=project_id,
    )

    principals: dict[str, Any] = {}
    for r in results:
        principal_email = r["principal_email"]
        binding_id = r["binding_id"]
        binding_resource = r["binding_resource"]
        role_permissions = r["role_permissions"] or []

        if principal_email not in principals:
            principals[principal_email] = {}

        # Compile permissions from role
        compiled_permissions = compile_permissions_from_role(role_permissions)
        compiled_scope = compile_gcp_regex(
            resolve_gcp_scope(binding_resource, project_id)
        )

        principals[principal_email][binding_id] = {
            "permissions": compiled_permissions,
            "scope": compiled_scope,
        }

    return principals


def compile_permissions_from_role(role_permissions: list[str]) -> dict[str, Any]:
    permissions: dict[str, list[str]] = {
        "permissions": [],
        "denied_permissions": [],
    }

    # For now, we only handle allow policies
    # GCP can have denied permissions and denied principals (under deny policies),
    # but we'd need to fetch that separately using the IAM API.
    permissions["permissions"] = role_permissions

    return compile_permissions(permissions)


def compile_permissions(permissions: dict[str, Any]) -> dict[str, Any]:
    compiled_permissions = {}
    compiled_permissions["permissions"] = [
        compile_gcp_regex(item) for item in permissions["permissions"]
    ]
    compiled_permissions["denied_permissions"] = [
        compile_gcp_regex(item) for item in permissions["denied_permissions"]
    ]

    return compiled_permissions


@timeit
def get_resource_ids(
    neo4j_session: neo4j.Session, project_id: str, target_label: str
) -> dict[str, str]:
    """
    Get resource IDs for a given resource type in a project.
    Returns a dictionary mapping actual resource IDs to their expected scopes.
    """
    get_resource_query = Template(
        """
    MATCH (project:GCPProject{id: $ProjectId})-[:RESOURCE]->(resource:$node_label)
    RETURN resource.id as resource_id
    """,
    )
    get_resource_query_template = get_resource_query.safe_substitute(
        node_label=target_label,
    )
    resource_ids = neo4j_session.execute_read(
        read_list_of_values_tx,
        get_resource_query_template,
        ProjectId=project_id,
    )
    resource_dict = {
        resource_id: f'project/{project_id}/resource/{resource_id.split("/")[-1]}'
        # Resource scope is project/{project_id}/resource/{last part of resource_id when separated by /}
        # Resource_id as key for loading and resource scope as value for scope evaluation
        for resource_id in resource_ids
    }
    return resource_dict


def parse_permission_relationships_file(file_path: str) -> list[dict[str, Any]]:
    try:
        if os.path.isabs(file_path):
            resolved_file_path = file_path
        else:
            resolved_file_path = os.path.join(os.getcwd(), file_path)
        with open(resolved_file_path) as f:
            relationship_mapping = yaml.load(f, Loader=yaml.FullLoader)
        return relationship_mapping or []
    except FileNotFoundError:
        logger.warning(
            f"GCP permission relationships file not found. Original filename passed to sync: '{file_path}', "
            f"resolved full path: '{resolved_file_path}'. Skipping sync stage {__name__}. "
            f"If you want to run this sync, please explicitly set a value for --gcp-permission-relationships-file in the "
            f"command line interface."
        )
        return []


def is_valid_gcp_rpr(rpr: dict[str, Any]) -> bool:
    required_fields = ["permissions", "relationship_name", "target_label"]
    for field in required_fields:
        if field not in rpr:
            return False
    return True


@timeit
def load_principal_mappings(
    neo4j_session: neo4j.Session,
    principal_mappings: list[dict[str, Any]],
    matchlink_schema: GCPPermissionMatchLink,
    update_tag: int,
    project_id: str,
) -> None:
    """
    Load principal mappings into Neo4j using MatchLinks.
    """
    if not principal_mappings:
        return

    logger.info(
        f"Loading {len(principal_mappings)} {matchlink_schema.rel_label} relationships "
        f"for {matchlink_schema.source_node_label} -> {matchlink_schema.target_node_label}"
    )

    load_matchlinks(
        neo4j_session,
        matchlink_schema,
        principal_mappings,
        lastupdated=update_tag,
        _sub_resource_label="GCPProject",
        _sub_resource_id=project_id,
    )


@timeit
def cleanup_rpr(
    neo4j_session: neo4j.Session,
    matchlink_schema: GCPPermissionMatchLink,
    update_tag: int,
    project_id: str,
) -> None:
    logger.info(
        "Cleaning up relationship '%s' for node label '%s'",
        matchlink_schema.rel_label,
        matchlink_schema.target_node_label,
    )

    GraphJob.from_matchlink(
        matchlink_schema,
        "GCPProject",
        project_id,
        update_tag,
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    project_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Syncing GCP Permission Relationships for project '%s'.", project_id)

    pr_file = common_job_parameters.get("gcp_permission_relationships_file")
    if not pr_file:
        logger.warning(
            "GCP permission relationships file was not specified, skipping. If this is not expected, please check your "
            "value of --gcp-permission-relationships-file"
        )
        return

    # 1. GET - Fetch all GCP principals in suitable dict format
    principals = get_principals_for_project(neo4j_session, project_id)

    # 2. PARSE - Parse relationship file
    relationship_mapping = parse_permission_relationships_file(pr_file)

    # 3. EVALUATE - Evaluate each relationship and resource ID
    for rpr in relationship_mapping:
        if not is_valid_gcp_rpr(rpr):
            logger.error(f"Invalid permission relationship configuration: {rpr}")
            continue

        target_label = rpr["target_label"]
        relationship_name = rpr["relationship_name"]
        permissions = rpr["permissions"]

        resource_dict = get_resource_ids(neo4j_session, project_id, target_label)

        logger.info(
            f"Evaluating relationship '{relationship_name}' for resource type '{target_label}'"
        )
        matches = calculate_permission_relationships(
            principals, resource_dict, permissions
        )

        # Create MatchLink schema with dynamic attributes
        matchlink_schema = GCPPermissionMatchLink(
            source_node_label="GCPPrincipal",
            target_node_label=target_label,
            rel_label=relationship_name,
        )

        load_principal_mappings(
            neo4j_session,
            matches,
            matchlink_schema,
            update_tag,
            project_id,
        )
        cleanup_rpr(
            neo4j_session,
            matchlink_schema,
            update_tag,
            project_id,
        )

    logger.info(f"Completed GCP Permission Relationships sync for project {project_id}")
