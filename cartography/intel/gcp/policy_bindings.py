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
from cartography.graph.job import GraphJob
from cartography.models.gcp.policy_bindings import GCPPolicyBindingSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


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
