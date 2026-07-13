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
from cartography.client.core.tx import load_matchlinks_cartesian_product
from cartography.client.core.tx import read_list_of_values_tx
from cartography.graph.job import GraphJob
from cartography.models.gcp.permission_relationships import (
    GCPConditionalPermissionMatchLink,
)
from cartography.models.gcp.permission_relationships import GCPPermissionMatchLink
from cartography.util import timeit

logger = logging.getLogger(__name__)

GCP_PERMISSION_RELATIONSHIP_BATCH_SIZE = 500
GCP_BIGQUERY_TABLE_PERMISSION_TABLE_BATCH_SIZE = 1000
GCP_BIGQUERY_TABLE_PERMISSION_PRINCIPAL_BATCH_SIZE = 100
GCPPrincipalPermissionContext = dict[str, dict[str, dict[str, Any]]]


def resolve_gcp_scope(scope: str, project_id: str) -> str:
    """
    Resolve a GCP IAM scope string to its canonical project-scoped form.

    Process breakdown:
    - If scope is at the resource manager hierarchy (org / folder / project),
      return project/{project_id}/* — this matches every project resource.
    - Otherwise, strip the leading "//{service.host}/" and use the remaining
      path verbatim. The path uniquely identifies the resource within the
      project — using the last segment alone collides for nested resources
      (e.g. two BigQuery tables named "events" in different datasets, or two
      KMS keys named "default" in different keyrings).

    Typical Scope Examples (followed by their resolved form):

    - ORG: //cloudresourcemanager.googleapis.com/organizations/{id}
        -> project/{project_id}/*
    - FOLDER: //cloudresourcemanager.googleapis.com/folders/{id}
        -> project/{project_id}/*
    - PROJECT: //cloudresourcemanager.googleapis.com/projects/{id}
        -> project/{project_id}/*
    - BUCKET: //storage.googleapis.com/buckets/{bucket_name}
        -> project/{project_id}/resource/buckets/{bucket_name}
    - BIGQUERY TABLE: //bigquery.googleapis.com/projects/{p}/datasets/{d}/tables/{t}
        -> project/{project_id}/resource/projects/{p}/datasets/{d}/tables/{t}
    - INSTANCE: //compute.googleapis.com/projects/{p}/zones/{z}/instances/{i}
        -> project/{project_id}/resource/projects/{p}/zones/{z}/instances/{i}
    """
    if "cloudresourcemanager.googleapis.com" in scope:
        return f"project/{project_id}/*"

    path = scope
    if path.startswith("//"):
        # Strip protocol marker and service host, keeping the resource path.
        without_protocol = path[2:]
        slash_idx = without_protocol.find("/")
        if slash_idx > 0:
            path = without_protocol[slash_idx + 1 :]
    return f"project/{project_id}/resource/{path}"


# Resource id formats that need a service-specific prefix to align with the
# path encoded in the IAM scope string. Most GCP resource ids already start
# with "projects/..." which matches their scope path verbatim; the table only
# needs entries for resources whose id is a bare name.
_GCP_TARGET_LABEL_TO_SCOPE_PATH_PREFIX: dict[str, str] = {
    "GCPBucket": "buckets",
}


def _canonical_resource_path(target_label: str, resource_id: str) -> str:
    """Return the resource path used in scope strings for this target label.

    Most GCP resource ids ingested by cartography are already in the
    ``projects/{p}/...`` form that matches what GCP IAM puts in the scope
    string. Two label families need translation:

    - ``GCPBucket``: the id is the bare bucket name; IAM scope path is
      ``buckets/{name}``.
    - BigQuery (``GCPBigQueryDataset``, ``GCPBigQueryTable``): cartography
      uses the legacy ``{project}:{dataset}[.table]`` id format, while IAM
      scope path is ``projects/{p}/datasets/{d}[/tables/{t}]``.
    """
    if target_label == "GCPBigQueryDataset":
        # "project:dataset" -> "projects/project/datasets/dataset"
        if ":" in resource_id:
            project_id, dataset_id = resource_id.split(":", 1)
            return f"projects/{project_id}/datasets/{dataset_id}"
        return resource_id
    if target_label == "GCPBigQueryTable":
        # "project:dataset.table" -> "projects/project/datasets/dataset/tables/table"
        if ":" in resource_id and "." in resource_id:
            project_id, rest = resource_id.split(":", 1)
            dataset_id, table_id = rest.split(".", 1)
            return f"projects/{project_id}/datasets/{dataset_id}/tables/{table_id}"
        return resource_id
    prefix = _GCP_TARGET_LABEL_TO_SCOPE_PATH_PREFIX.get(target_label)
    if prefix is None:
        return resource_id
    return f"{prefix}/{resource_id}"


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


def _assignment_allows_permissions(
    assignment_data: dict[str, Any],
    permissions: list[str],
) -> bool:
    """
    Check permission allow/deny logic without evaluating resource scope.

    Broad-scope handling uses this after it has already classified an
    assignment as project- or container-wide.
    """
    permissions_dict = assignment_data["permissions"]
    for permission in permissions:
        if not evaluate_denied_permission_for_permission(permissions_dict, permission):
            if evaluate_permission_for_permission(permissions_dict, permission):
                return True
    return False


def _split_project_scope_principals(
    principals: GCPPrincipalPermissionContext,
    permissions: list[str],
    project_id: str,
) -> tuple[set[str], GCPPrincipalPermissionContext]:
    project_scope_pattern = f"project/{project_id}/.*"
    project_scope_principals: set[str] = set()
    residual_principals: GCPPrincipalPermissionContext = {}

    for principal_email, policy_bindings in principals.items():
        for binding_id, assignment_data in policy_bindings.items():
            if not _assignment_allows_permissions(assignment_data, permissions):
                continue

            # Conditional grants must keep per-edge condition metadata, which the bulk
            # Cartesian loader cannot carry. Route them to the row-by-row path instead.
            if assignment_data[
                "scope"
            ].pattern == project_scope_pattern and not assignment_data.get(
                "has_condition"
            ):
                project_scope_principals.add(principal_email)
                continue

            residual_principals.setdefault(principal_email, {})[
                binding_id
            ] = assignment_data

    if project_scope_principals:
        for principal_email in project_scope_principals:
            residual_principals.pop(principal_email, None)

    return project_scope_principals, residual_principals


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


def collect_binding_conditions(
    policy_bindings: dict[str, Any],
    resource_scope: str,
    permissions: list[str],
) -> dict[str, Any]:
    """Determine the condition metadata to stamp on a granted permission edge.

    GCP evaluates IAM conditions at request time, so a conditional binding cannot be
    statically resolved. We annotate the edge instead:
    - If any matching binding grants the access unconditionally, the edge is reachable
      unconditionally and has_condition is False.
    - Otherwise every matching binding is conditional; has_condition is True and we
      surface the (de-duplicated) condition titles/expressions for downstream filtering.

    Only call this for edges already confirmed by principal_allowed_on_resource.
    """
    conditional: list[dict[str, Any]] = []
    for assignment_data in policy_bindings.values():
        if not evaluate_policy_binding_for_permissions(
            assignment_data, permissions, resource_scope
        ):
            continue
        if not assignment_data.get("has_condition"):
            return {
                "has_condition": False,
                "condition_title": None,
                "condition_expression": None,
            }
        conditional.append(assignment_data)

    if not conditional:
        return {
            "has_condition": False,
            "condition_title": None,
            "condition_expression": None,
        }

    titles = list(
        dict.fromkeys(
            a["condition_title"] for a in conditional if a.get("condition_title")
        )
    )
    expressions = list(
        dict.fromkeys(
            a["condition_expression"]
            for a in conditional
            if a.get("condition_expression")
        )
    )
    return {
        "has_condition": True,
        "condition_title": "; ".join(titles) if titles else None,
        "condition_expression": " || ".join(expressions) if expressions else None,
    }


def calculate_permission_relationships_for_resource(
    principals: dict[str, Any],
    resource_id: str,
    resource_scope: str,
    permissions: list[str],
) -> list[dict[str, Any]]:
    allowed_mappings: list[dict[str, Any]] = []
    for principal_email, policy_bindings in principals.items():
        if principal_allowed_on_resource(policy_bindings, resource_scope, permissions):
            conditions = collect_binding_conditions(
                policy_bindings, resource_scope, permissions
            )
            allowed_mappings.append(
                {
                    "principal_email": principal_email,
                    "resource_id": resource_id,
                    **conditions,
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


def _bigquery_dataset_id_from_table_id(table_id: str) -> str | None:
    if ":" not in table_id or "." not in table_id:
        return None
    project_id, rest = table_id.split(":", 1)
    dataset_id, _ = rest.split(".", 1)
    return f"{project_id}:{dataset_id}"


def _match_bigquery_dataset_scope(scope_pattern: str, project_id: str) -> str | None:
    match = re.fullmatch(
        rf"project/{re.escape(project_id)}/resource/projects/([^/]+)/datasets/([^/]+)",
        scope_pattern,
    )
    if match is None:
        return None
    scope_project_id, dataset_id = match.groups()
    return f"{scope_project_id}:{dataset_id}"


def split_bigquery_table_broad_scope_principals(
    principals: GCPPrincipalPermissionContext,
    permissions: list[str],
    project_id: str,
) -> tuple[set[str], dict[str, set[str]], GCPPrincipalPermissionContext]:
    """
    Split BigQuery table permissions into broad scopes and exact residual work.

    Project- and dataset-scope BigQuery grants can apply to every table in a
    project or dataset. Group those principals up front so they can be loaded
    through the core MatchLink Cartesian product helper instead of repeatedly
    evaluating the same broad scope for every table.
    """
    project_scope_principals, residual_principals = _split_project_scope_principals(
        principals,
        permissions,
        project_id,
    )
    dataset_scope_principals, residual_principals = (
        _split_bigquery_table_dataset_scope_principals(
            residual_principals,
            permissions,
            project_id,
        )
    )
    return project_scope_principals, dataset_scope_principals, residual_principals


def _split_bigquery_table_dataset_scope_principals(
    principals: GCPPrincipalPermissionContext,
    permissions: list[str],
    project_id: str,
) -> tuple[dict[str, set[str]], GCPPrincipalPermissionContext]:
    dataset_scope_principals: dict[str, set[str]] = {}
    residual_principals: GCPPrincipalPermissionContext = {}

    for principal_email, policy_bindings in principals.items():
        for binding_id, assignment_data in policy_bindings.items():
            if not _assignment_allows_permissions(assignment_data, permissions):
                continue

            # As with project scope, conditional grants cannot ride the bulk loader.
            if assignment_data.get("has_condition"):
                residual_principals.setdefault(principal_email, {})[
                    binding_id
                ] = assignment_data
                continue

            scope_pattern = assignment_data["scope"].pattern
            dataset_id = _match_bigquery_dataset_scope(scope_pattern, project_id)
            if dataset_id is not None:
                dataset_scope_principals.setdefault(dataset_id, set()).add(
                    principal_email
                )
                continue

            residual_principals.setdefault(principal_email, {})[
                binding_id
            ] = assignment_data

    return dataset_scope_principals, residual_principals


@timeit
def load_permission_relationships_cartesian_product(
    neo4j_session: neo4j.Session,
    matchlink_schema: GCPPermissionMatchLink,
    principal_emails: set[str],
    resource_ids: list[str],
    update_tag: int,
    project_id: str,
    scope_description: str,
    principal_batch_size: int = GCP_BIGQUERY_TABLE_PERMISSION_PRINCIPAL_BATCH_SIZE,
    resource_batch_size: int = GCP_BIGQUERY_TABLE_PERMISSION_TABLE_BATCH_SIZE,
) -> int:
    if not principal_emails or not resource_ids:
        return 0

    # A broad grant means each principal should link to each resource in this
    # scope. The core MatchLink helper performs that expansion in bounded graph
    # batches without constructing every pair as a Python dict first.
    return load_matchlinks_cartesian_product(
        neo4j_session,
        matchlink_schema,
        sorted(principal_emails),
        sorted(resource_ids),
        source_batch_size=principal_batch_size,
        target_batch_size=resource_batch_size,
        progress_description=(
            f"{matchlink_schema.rel_label} {matchlink_schema.target_node_label} permissions for {scope_description}"
        ),
        lastupdated=update_tag,
        # The bulk path only handles unconditional grants; set the condition fields
        # explicitly so a prior conditional edge on the same pair is cleared.
        has_condition=False,
        condition_title=None,
        condition_expression=None,
        _sub_resource_label="GCPProject",
        _sub_resource_id=project_id,
    )


@timeit
def _load_bigquery_dataset_scope_bulk(
    neo4j_session: neo4j.Session,
    dataset_scope_principals: dict[str, set[str]],
    resource_dict: dict[str, str],
    matchlink_schema: GCPPermissionMatchLink,
    update_tag: int,
    project_id: str,
) -> int:
    relationships_loaded = 0
    table_ids_by_dataset: dict[str, list[str]] = {}
    for table_id in resource_dict:
        dataset_id = _bigquery_dataset_id_from_table_id(table_id)
        if dataset_id in dataset_scope_principals:
            table_ids_by_dataset.setdefault(dataset_id, []).append(table_id)

    for dataset_id, dataset_table_ids in table_ids_by_dataset.items():
        dataset_principals = dataset_scope_principals[dataset_id]
        logger.info(
            "Bulk loading relationship '%s' for %d dataset-scope principals across %d BigQuery tables in dataset '%s'",
            matchlink_schema.rel_label,
            len(dataset_principals),
            len(dataset_table_ids),
            dataset_id,
        )
        relationships_loaded += load_permission_relationships_cartesian_product(
            neo4j_session,
            matchlink_schema,
            dataset_principals,
            dataset_table_ids,
            update_tag,
            project_id,
            f"dataset {dataset_id}",
        )

    return relationships_loaded


_ContainerScopeSplitter = Callable[
    [GCPPrincipalPermissionContext, list[str], str],
    tuple[dict[str, set[str]], GCPPrincipalPermissionContext],
]
_ContainerScopeBulkLoader = Callable[
    [
        neo4j.Session,
        dict[str, set[str]],
        dict[str, str],
        GCPPermissionMatchLink,
        int,
        str,
    ],
    int,
]

# Container scopes (e.g. a BigQuery dataset covering all its tables) are handled
# in two phases: a splitter separates broad-scope principals from exact residual
# work, then a bulk loader Cartesian-writes the broad grants.
_CONTAINER_SCOPE_HANDLERS: dict[
    str, tuple[_ContainerScopeSplitter, _ContainerScopeBulkLoader]
] = {
    "GCPBigQueryTable": (
        _split_bigquery_table_dataset_scope_principals,
        _load_bigquery_dataset_scope_bulk,
    ),
}


@timeit
def evaluate_and_load_scope_aware_permission_relationships(
    neo4j_session: neo4j.Session,
    principals: GCPPrincipalPermissionContext,
    resource_dict: dict[str, str],
    permissions: list[str],
    matchlink_schema: GCPPermissionMatchLink,
    update_tag: int,
    project_id: str,
    batch_size: int = GCP_PERMISSION_RELATIONSHIP_BATCH_SIZE,
) -> int:
    project_scope_principals, residual_principals = _split_project_scope_principals(
        principals,
        permissions,
        project_id,
    )

    # Split container-scope (e.g. BigQuery dataset) broad grants out of the residual
    # up front so we know the final residual before loading anything.
    dataset_scope_principals: dict[str, set[str]] = {}
    handler = _CONTAINER_SCOPE_HANDLERS.get(matchlink_schema.target_node_label)
    if handler is not None:
        splitter, _ = handler
        dataset_scope_principals, residual_principals = splitter(
            residual_principals,
            permissions,
            project_id,
        )

    relationships_loaded = 0
    resource_ids = list(resource_dict)

    # Load the residual (row-by-row) path FIRST. It may write conditional edges, and
    # the bulk unconditional loads below must overwrite any overlapping edge so that
    # broader unconditional access always wins (has_condition=false). See #2891 review.
    if residual_principals:
        residual_matchlink_schema = GCPConditionalPermissionMatchLink(
            source_node_label=matchlink_schema.source_node_label,
            target_node_label=matchlink_schema.target_node_label,
            rel_label=matchlink_schema.rel_label,
        )
        relationships_loaded += evaluate_and_load_permission_relationships(
            neo4j_session,
            residual_principals,
            resource_dict,
            permissions,
            residual_matchlink_schema,
            update_tag,
            project_id,
            batch_size=batch_size,
        )

    # Container (dataset) bulk: overwrites overlapping residual edges with
    # has_condition=false.
    if handler is not None and dataset_scope_principals:
        _, bulk_loader = handler
        relationships_loaded += bulk_loader(
            neo4j_session,
            dataset_scope_principals,
            resource_dict,
            matchlink_schema,
            update_tag,
            project_id,
        )

    # Project bulk is the broadest scope, so it runs last and wins over everything.
    if project_scope_principals:
        logger.info(
            "Bulk loading relationship '%s' for %d project-scope principals across %d %s resources in project '%s'",
            matchlink_schema.rel_label,
            len(project_scope_principals),
            len(resource_ids),
            matchlink_schema.target_node_label,
            project_id,
        )
        relationships_loaded += load_permission_relationships_cartesian_product(
            neo4j_session,
            matchlink_schema,
            project_scope_principals,
            resource_ids,
            update_tag,
            project_id,
            f"project {project_id}",
        )

    return relationships_loaded


@timeit
def build_principals_from_policy_bindings(
    policy_bindings: list[dict[str, Any]],
    role_permissions_by_name: dict[str, list[str]],
    project_id: str,
) -> GCPPrincipalPermissionContext:
    """
    Build the permission evaluation input directly from the current sync's
    transformed policy bindings and IAM role payloads.
    """
    principals: GCPPrincipalPermissionContext = {}
    compiled_assignments: dict[str, dict[str, Any]] = {}
    conditional_bindings = 0
    skipped_missing_roles = 0
    total_member_assignments = 0

    for binding in policy_bindings:
        role = binding["role"]
        role_permissions = role_permissions_by_name.get(role)
        if role_permissions is None:
            skipped_missing_roles += 1
            continue

        # Conditional bindings used to be dropped, which understated access. We now
        # keep them and carry the condition metadata so the edge can be flagged
        # (has_condition=True). GCP evaluates the CEL condition at request time, so we
        # cannot statically resolve allow vs deny here. See issue #2312.
        has_condition = bool(binding.get("has_condition"))
        if has_condition:
            conditional_bindings += 1

        binding_id = binding["id"]
        if binding_id not in compiled_assignments:
            compiled_assignments[binding_id] = {
                "permissions": compile_permissions_from_role(role_permissions),
                "scope": compile_gcp_regex(
                    resolve_gcp_scope(binding["resource"], project_id)
                ),
                "has_condition": has_condition,
                "condition_title": binding.get("condition_title"),
                "condition_expression": binding.get("condition_expression"),
            }

        # Share the compiled assignment across members of the same binding. Treat
        # it as read-only during relationship evaluation.
        for principal_email in binding["members"]:
            principals.setdefault(principal_email, {})[binding_id] = (
                compiled_assignments[binding_id]
            )
            total_member_assignments += 1

    logger.info(
        "Built GCP permission evaluation context for project '%s': bindings=%d, usable_bindings=%d, member_assignments=%d, principals=%d, conditional_bindings=%d, skipped_missing_roles=%d",
        project_id,
        len(policy_bindings),
        len(compiled_assignments),
        total_member_assignments,
        len(principals),
        conditional_bindings,
        skipped_missing_roles,
    )
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
    # Use the full resource_id (or its target-label-aware canonical form) as
    # the scope value so nested resources stay distinguishable. Truncating to
    # the last segment merged sibling resources sharing a leaf name (e.g. two
    # BigQuery tables named "events" in different datasets).
    resource_dict = {
        resource_id: (
            f"project/{project_id}/resource/"
            f"{_canonical_resource_path(target_label, resource_id)}"
        )
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
    matchlink_schema: GCPPermissionMatchLink | GCPConditionalPermissionMatchLink,
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
    principals: GCPPrincipalPermissionContext,
    resource_dict: dict[str, str],
    permissions: list[str],
    matchlink_schema: GCPPermissionMatchLink | GCPConditionalPermissionMatchLink,
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
    principals: GCPPrincipalPermissionContext,
) -> None:
    logger.info("Syncing GCP Permission Relationships for project '%s'.", project_id)

    pr_file = common_job_parameters.get("gcp_permission_relationships_file")
    if not pr_file:
        logger.warning(
            "GCP permission relationships file was not specified, skipping. If this is not expected, please check your "
            "value of --gcp-permission-relationships-file"
        )
        return

    # 1. PARSE - Parse relationship file
    relationship_mapping = parse_permission_relationships_file(pr_file)

    # 2. EVALUATE - Evaluate each relationship and resource ID
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

        loaded_relationship_count = (
            evaluate_and_load_scope_aware_permission_relationships(
                neo4j_session,
                principals,
                resource_dict,
                permissions,
                matchlink_schema,
                update_tag,
                project_id,
                batch_size=GCP_PERMISSION_RELATIONSHIP_BATCH_SIZE,
            )
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
