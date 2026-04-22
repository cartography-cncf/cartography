import hashlib
import logging
from typing import Any

import neo4j
from google.api_core.exceptions import PermissionDenied
from google.cloud.asset_v1 import AssetServiceClient
from google.cloud.asset_v1.types import BatchGetEffectiveIamPoliciesRequest
from google.cloud.asset_v1.types import SearchAllIamPoliciesRequest
from google.protobuf.json_format import MessageToDict

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.models.gcp.policy_bindings import GCPPolicyBindingAppliesToMatchLink
from cartography.models.gcp.policy_bindings import GCPPolicyBindingSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Maps a Cloud Asset full-resource-name prefix to the Cartography node label
# and the substring of the full name that corresponds to that node's `id`.
# Extend this as more resource types are brought into the ontology.
_FULL_RESOURCE_NAME_TO_NODE: list[tuple[str, str, str]] = [
    # (prefix to strip, target label, suffix template marker)
    # Tuple semantics: (prefix, target_label, id_format)
    #   id_format = "last"          -> take last path segment after prefix
    #   id_format = "type_prefixed" -> keep "{type}/{id}" (e.g. "organizations/1337")
    ("//cloudresourcemanager.googleapis.com/projects/", "GCPProject", "last"),
    (
        "//cloudresourcemanager.googleapis.com/folders/",
        "GCPFolder",
        "type_prefixed",
    ),
    (
        "//cloudresourcemanager.googleapis.com/organizations/",
        "GCPOrganization",
        "type_prefixed",
    ),
    ("//storage.googleapis.com/buckets/", "GCPBucket", "last"),
]


def _parse_full_resource_name(full_name: str) -> tuple[str | None, str | None]:
    """
    Parse a GCP Cloud Asset full resource name and return the matching
    (target_node_label, target_id) pair when the resource type is part of the
    Cartography ontology, or (None, None) otherwise.

    Full resource name format: //{service}.googleapis.com/{path}
    """
    for prefix, label, id_format in _FULL_RESOURCE_NAME_TO_NODE:
        if not full_name.startswith(prefix):
            continue
        suffix = full_name[len(prefix) :]
        if not suffix:
            return None, None
        # We only match the first path segment after the prefix — policies
        # attached to sub-resources (e.g. bucket objects) resolve back to the
        # owning top-level resource that exists in the graph.
        segment = suffix.split("/", 1)[0]
        if id_format == "type_prefixed":
            # Extract the resource type from the prefix (e.g. "folders")
            type_name = prefix.rstrip("/").rsplit("/", 1)[-1]
            return label, f"{type_name}/{segment}"
        return label, segment
    return None, None


@timeit
def get_policy_bindings(
    project_id: str,
    common_job_parameters: dict[str, Any],
    client: AssetServiceClient,
) -> dict[str, Any]:
    org_id = common_job_parameters.get("ORG_RESOURCE_NAME")
    project_resource_name = (
        f"//cloudresourcemanager.googleapis.com/projects/{project_id}"
    )

    policies = []

    # Fetch effective policies for project resource (using org scope for inheritance)
    effective_scope = org_id
    response = client.batch_get_effective_iam_policies(
        request=BatchGetEffectiveIamPoliciesRequest(
            scope=effective_scope, names=[project_resource_name]
        )
    )
    effective_dict = MessageToDict(response._pb, preserving_proto_field_name=True)

    policies.extend(
        effective_dict["policy_results"]
    )  # Fail Loudly if policy_results is not present

    # Fetch direct policy bindings for all child resources using search_all_iam_policies (project scope - no inheritance)
    search_request = SearchAllIamPoliciesRequest(
        scope=f"projects/{project_id}",
        asset_types=[],
    )
    for policy in client.search_all_iam_policies(request=search_request):
        policy_dict = MessageToDict(policy._pb, preserving_proto_field_name=True)
        # Filter out project resource itself (we already have effective policies for it)
        resource = policy_dict.get("resource", "")
        if resource != project_resource_name:
            policy_data = policy_dict.get("policy", {})
            bindings = policy_data.get("bindings", [])

            policies.append(
                {
                    "full_resource_name": resource,
                    "policies": [
                        {
                            "attached_resource": resource,
                            "policy": {"bindings": bindings},
                        }
                    ],
                }
            )

    return {
        "project_id": project_id,
        "organization": org_id,
        "policy_results": policies,
    }


def transform_bindings(data: dict[str, Any]) -> list[dict[str, Any]]:
    project_id = data["project_id"]
    bindings: dict[tuple[str, str, str | None], dict[str, Any]] = {}

    for policy_result in data["policy_results"]:
        for policy in policy_result.get("policies", []):
            resource = policy.get("attached_resource", "")

            # Determine resource type
            if "/organizations/" in resource:
                resource_type = "organization"
            elif "/folders/" in resource:
                resource_type = "folder"
            elif f"/projects/{project_id}" in resource and resource.endswith(
                f"/projects/{project_id}"
            ):
                resource_type = "project"
            else:
                resource_type = "resource"

            for binding in policy.get("policy", {}).get("bindings", []):
                role = binding.get("role")
                members = binding.get("members", [])
                condition = binding.get("condition")

                if not role or not members:
                    continue

                # Filter members to only user:, serviceAccount:, and group: types
                # Extract email part from each member (format: "type:email@example.com")
                filtered_members = []
                for member in members:
                    if ":" not in member:
                        continue
                    member_type, identifier = member.split(":", 1)
                    if member_type in ("user", "serviceAccount", "group"):
                        # Store only the email part
                        filtered_members.append(identifier)

                # Don't process if members(principals) are not from the supported types. For example -> allUsers:, allAuthenticatedUsers, etc.
                if not filtered_members:
                    continue

                # Extract condition expression for deduplication key
                # Include condition expression in key so conditional bindings stay distinct
                condition_expression = (
                    condition.get("expression") if condition else None
                )

                # Deduplicate bindings by (resource, role, condition_expression)
                # This ensures conditional bindings with different expressions are kept separate
                key = (resource, role, condition_expression)

                if key in bindings:
                    existing_members = set(bindings[key]["members"])
                    existing_members.update(filtered_members)
                    bindings[key]["members"] = list(existing_members)
                else:
                    # Generate unique ID that includes condition expression hash
                    condition_hash = ""
                    if condition_expression:
                        condition_hash = hashlib.sha256(
                            condition_expression.encode("utf-8")
                        ).hexdigest()[
                            :8
                        ]  # Use first 8 chars of hash for brevity

                    binding_id = f"{resource}_{role}"
                    if condition_hash:
                        binding_id = f"{binding_id}_{condition_hash}"

                    bindings[key] = {
                        "id": binding_id,
                        "role": role,
                        "resource": resource,
                        "resource_type": resource_type,
                        "members": sorted(filtered_members),
                        "has_condition": condition is not None,
                        "condition_title": (
                            condition.get("title") if condition else None
                        ),
                        "condition_expression": condition_expression,
                    }

    return list(bindings.values())


def _group_applies_to_links(
    bindings: list[dict[str, Any]],
) -> dict[str, list[dict[str, str]]]:
    """
    Group bindings by the Cartography label of their bound resource so
    load_matchlinks can be invoked once per target label. Bindings whose
    resource type is not yet in the ontology are silently dropped here — the
    binding node is still created by the main load(), just without an
    APPLIES_TO edge.
    """
    grouped: dict[str, list[dict[str, str]]] = {}
    for binding in bindings:
        label, target_id = _parse_full_resource_name(binding["resource"])
        if not label or not target_id:
            continue
        grouped.setdefault(label, []).append(
            {"binding_id": binding["id"], "target_id": target_id},
        )
    return grouped


@timeit
def load_bindings(
    neo4j_session: neo4j.Session,
    bindings: list[dict[str, Any]],
    project_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GCPPolicyBindingSchema(),
        bindings,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )

    for target_label, links in _group_applies_to_links(bindings).items():
        load_matchlinks(
            neo4j_session,
            GCPPolicyBindingAppliesToMatchLink(target_node_label=target_label),
            links,
            lastupdated=update_tag,
            _sub_resource_label="GCPProject",
            _sub_resource_id=project_id,
        )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.debug("Running GCP policy bindings cleanup job")

    GraphJob.from_node_schema(
        GCPPolicyBindingSchema(),
        common_job_parameters,
    ).run(neo4j_session)

    project_id = common_job_parameters["PROJECT_ID"]
    update_tag = common_job_parameters["UPDATE_TAG"]
    # Run a matchlink cleanup for every target label we know how to map. This
    # clears stale APPLIES_TO edges even if no binding in this sync targeted
    # that label.
    for target_label in {label for _, label, _ in _FULL_RESOURCE_NAME_TO_NODE}:
        GraphJob.from_matchlink(
            GCPPolicyBindingAppliesToMatchLink(target_node_label=target_label),
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
    client: AssetServiceClient,
) -> bool:
    """
    Sync GCP IAM policy bindings for a project.

    Returns True if sync was successful, False if skipped due to permissions.
    """
    try:
        bindings_data = get_policy_bindings(
            project_id, common_job_parameters=common_job_parameters, client=client
        )  # Why pass common_job_parameters here? Because we need to get the org_id for getting inherited policies.
    except PermissionDenied as e:
        logger.warning(
            "Permission denied when fetching policy bindings for project %s. "
            "Skipping policy bindings sync. To enable this feature, grant "
            "roles/cloudasset.viewer at the organization level. Error: %s",
            project_id,
            e,
        )
        return False

    transformed_bindings_data = transform_bindings(bindings_data)

    load_bindings(neo4j_session, transformed_bindings_data, project_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    return True
