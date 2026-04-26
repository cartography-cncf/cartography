import logging
import os
import re
from collections.abc import Iterator
from string import Template
from typing import Any
from typing import Callable

import neo4j
import yaml

from cartography.client.core.tx import load_matchlinks
from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.client.core.tx import read_list_of_values_tx
from cartography.graph.job import GraphJob
from cartography.helpers import batch as batch_items
from cartography.models.gcp.permission_relationships import GCPPermissionMatchLink
from cartography.util import timeit

logger = logging.getLogger(__name__)

GCP_PERMISSION_RELATIONSHIP_BATCH_SIZE = 500
GCP_POLICY_BINDING_READ_BATCH_SIZE = 500


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


def calculate_permission_relationships_for_resource(
    principals: dict[str, Any],
    resource_id: str,
    resource_scope: str,
    permissions: list[str],
) -> list[dict[str, Any]]:
    allowed_mappings: list[dict[str, Any]] = []
    for principal_email, policy_bindings in principals.items():
        if principal_allowed_on_resource(policy_bindings, resource_scope, permissions):
            allowed_mappings.append(
                {
                    "principal_email": principal_email,
                    "resource_id": resource_id,
                }
            )
    return allowed_mappings


def iter_permission_relationship_batches(
    principals: dict[str, Any],
    resource_dict: dict[str, str],
    permissions: list[str],
    batch_size: int = GCP_PERMISSION_RELATIONSHIP_BATCH_SIZE,
    progress_callback: Callable[[int, int], None] | None = None,
) -> Iterator[list[dict[str, Any]]]:
    if batch_size <= 0:
        raise ValueError(f"batch_size must be greater than 0, got {batch_size}")

    batch: list[dict[str, Any]] = []
    total_resources = len(resource_dict)
    for resources_processed, (resource_id, resource_scope) in enumerate(
        resource_dict.items(),
        start=1,
    ):
        batch.extend(
            calculate_permission_relationships_for_resource(
                principals,
                resource_id,
                resource_scope,
                permissions,
            )
        )
        if progress_callback is not None:
            progress_callback(resources_processed, total_resources)
        while len(batch) >= batch_size:
            yield batch[:batch_size]
            batch = batch[batch_size:]

    if batch:
        yield batch


@timeit
def get_principals_for_project(
    neo4j_session: neo4j.Session, project_id: str
) -> dict[str, Any]:
    """
    Get all principals (users, service accounts, groups) with their policy bindings
    for a given GCP project.
    """
    binding_ids = get_policy_binding_ids_for_project(neo4j_session, project_id)
    logger.info(
        "Found %d GCP policy bindings eligible for permission relationships in project '%s'.",
        len(binding_ids),
        project_id,
    )
    if not binding_ids:
        return {}

    principals: dict[str, Any] = {}
    for binding_ids_batch in batch_items(
        binding_ids,
        size=GCP_POLICY_BINDING_READ_BATCH_SIZE,
    ):
        logger.debug(
            "Fetching GCP principal policy bindings for project '%s' with %d binding ids.",
            project_id,
            len(binding_ids_batch),
        )
        results = get_principal_rows_for_policy_bindings(
            neo4j_session,
            project_id,
            binding_ids_batch,
        )
        merge_principal_rows(principals, results, project_id)

    return principals


def get_policy_binding_ids_for_project(
    neo4j_session: neo4j.Session,
    project_id: str,
) -> list[str]:
    get_binding_ids_query = """
    MATCH (:GCPProject{id: $ProjectId})-[:RESOURCE]->(binding:GCPPolicyBinding)
    WHERE binding.has_condition = false
    RETURN DISTINCT binding.id
    ORDER BY binding.id
    """
    return neo4j_session.execute_read(
        read_list_of_values_tx,
        get_binding_ids_query,
        ProjectId=project_id,
    )


def get_principal_rows_for_policy_bindings(
    neo4j_session: neo4j.Session,
    project_id: str,
    binding_ids: list[str],
) -> list[dict[str, Any]]:
    get_principals_query = """
    MATCH
    (project:GCPProject{id: $ProjectId})-[:RESOURCE]->
    (binding:GCPPolicyBinding)-[:GRANTS_ROLE]->
    (role:GCPRole)
    MATCH (principal:GCPPrincipal)-[:HAS_ALLOW_POLICY]->(binding)
    WHERE binding.has_condition = false
    AND binding.id IN $BindingIds
    RETURN
    DISTINCT principal.email as principal_email, binding.id as binding_id,
    binding.resource as binding_resource, role.permissions as role_permissions
    """

    return neo4j_session.execute_read(
        read_list_of_dicts_tx,
        get_principals_query,
        ProjectId=project_id,
        BindingIds=binding_ids,
    )


def merge_principal_rows(
    principals: dict[str, Any],
    rows: list[dict[str, Any]],
    project_id: str,
) -> None:
    for r in rows:
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
    batch_size: int = GCP_PERMISSION_RELATIONSHIP_BATCH_SIZE,
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
        batch_size=batch_size,
        lastupdated=update_tag,
        _sub_resource_label="GCPProject",
        _sub_resource_id=project_id,
    )


@timeit
def evaluate_and_load_permission_relationships(
    neo4j_session: neo4j.Session,
    principals: dict[str, Any],
    resource_dict: dict[str, str],
    permissions: list[str],
    matchlink_schema: GCPPermissionMatchLink,
    update_tag: int,
    project_id: str,
    batch_size: int = GCP_PERMISSION_RELATIONSHIP_BATCH_SIZE,
) -> int:
    if batch_size <= 0:
        raise ValueError(f"batch_size must be greater than 0, got {batch_size}")

    total_resources = len(resource_dict)
    if total_resources == 0:
        logger.info(
            "No %s resources found for relationship '%s' in project '%s'.",
            matchlink_schema.target_node_label,
            matchlink_schema.rel_label,
            project_id,
        )
        return 0

    relationships_loaded = 0
    progress_interval = max(1, min(100, total_resources // 10 or 1))

    def _log_progress(resources_processed: int, total_resources: int) -> None:
        if (
            resources_processed % progress_interval == 0
            or resources_processed == total_resources
        ):
            percent = (resources_processed / total_resources) * 100
            logger.info(
                "Relationship '%s' for '%s': processed %d/%d resources (%.1f%%), loaded %d relationships so far",
                matchlink_schema.rel_label,
                matchlink_schema.target_node_label,
                resources_processed,
                total_resources,
                percent,
                relationships_loaded,
            )

    for batch in iter_permission_relationship_batches(
        principals,
        resource_dict,
        permissions,
        batch_size=batch_size,
        progress_callback=_log_progress,
    ):
        load_principal_mappings(
            neo4j_session,
            batch,
            matchlink_schema,
            update_tag,
            project_id,
            batch_size=batch_size,
        )
        relationships_loaded += len(batch)

    logger.info(
        "Completed relationship '%s' for '%s': processed %d resources and loaded %d relationships",
        matchlink_schema.rel_label,
        matchlink_schema.target_node_label,
        total_resources,
        relationships_loaded,
    )
    return relationships_loaded


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
        principal_count = len(principals)
        resource_count = len(resource_dict)

        logger.info(
            "Starting relationship '%s' for resource type '%s' in project '%s' with %d permissions, %d principals, and %d resources",
            relationship_name,
            target_label,
            project_id,
            len(permissions),
            principal_count,
            resource_count,
        )

        # Create MatchLink schema with dynamic attributes
        matchlink_schema = GCPPermissionMatchLink(
            source_node_label="GCPPrincipal",
            target_node_label=target_label,
            rel_label=relationship_name,
        )

        loaded_relationship_count = evaluate_and_load_permission_relationships(
            neo4j_session,
            principals,
            resource_dict,
            permissions,
            matchlink_schema,
            update_tag,
            project_id,
            batch_size=GCP_PERMISSION_RELATIONSHIP_BATCH_SIZE,
        )
        logger.info(
            "Finished loading relationship '%s' for resource type '%s' in project '%s' with %d total relationships before cleanup",
            relationship_name,
            target_label,
            project_id,
            loaded_relationship_count,
        )
        cleanup_rpr(
            neo4j_session,
            matchlink_schema,
            update_tag,
            project_id,
        )

    logger.info(f"Completed GCP Permission Relationships sync for project {project_id}")
