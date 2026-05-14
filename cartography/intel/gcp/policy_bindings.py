import hashlib
import logging
import time
from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from threading import BoundedSemaphore
from threading import Lock
from typing import Any

import neo4j
from google.api_core.exceptions import DeadlineExceeded
from google.api_core.exceptions import PermissionDenied
from google.api_core.exceptions import ResourceExhausted
from google.api_core.exceptions import RetryError
from google.api_core.exceptions import ServiceUnavailable
from google.api_core.retry import if_exception_type
from google.api_core.retry import Retry
from google.cloud.asset_v1 import AssetServiceClient
from google.cloud.asset_v1.types import BatchGetEffectiveIamPoliciesRequest
from google.cloud.asset_v1.types import SearchAllIamPoliciesRequest
from google.protobuf.json_format import MessageToDict

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.graph.statement import GraphStatement
from cartography.intel.gcp.permission_relationships import (
    build_principals_from_policy_bindings,
)
from cartography.intel.gcp.permission_relationships import GCPPrincipalPermissionContext
from cartography.models.core.common import PropertyRef
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import MatchLinkSubResource
from cartography.models.gcp.policy_bindings import GCPFolderPolicyBindingSchema
from cartography.models.gcp.policy_bindings import GCPOrganizationPolicyBindingSchema
from cartography.models.gcp.policy_bindings import GCPPolicyBindingAppliesToMatchLink
from cartography.models.gcp.policy_bindings import GCPPolicyBindingSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _FullNameMapping:
    """
    Rule that maps a Cloud Asset full resource name to a Cartography node.

    - ``service_prefix``: the full name must start with this (e.g.
      ``"//cloudkms.googleapis.com/"``).
    - ``marker``: the path segment identifying the resource type (e.g.
      ``"cryptoKeys"``). The segment immediately after the marker is the name.
    - ``label``: Cartography node label.
    - ``id_mode``:
        * ``"last_segment"``   — just the name (GCPProject, GCPBucket).
        * ``"type_prefixed"``  — ``"{marker}/{name}"`` (GCPFolder, GCPOrganization).
        * ``"full_path"``      — the whole path up to and including the name
          (KMS, Secrets, Artifact Registry, Cloud Run, Compute).
        * ``"bigquery_dataset"`` — ``"{project_id}:{dataset_id}"``.
        * ``"bigquery_table"`` — ``"{project_id}:{dataset_id}.{table_id}"``.
    - ``asset_type``: Cloud Asset asset type to request from
      SearchAllIamPolicies for direct child-resource policies. Resource Manager
      scopes are fetched through BatchGetEffectiveIamPolicies instead, so they
      do not need a search asset type here.
    - ``additional_asset_types``: Extra Cloud Asset asset types that use the
      same full-name shape and Cartography node label.
    """

    service_prefix: str
    marker: str
    label: str
    id_mode: str
    asset_type: str | None = None
    additional_asset_types: tuple[str, ...] = ()


# Order matters within a given service_prefix: more specific mappings first so
# nested resource types win (e.g. a cryptoKey full name also contains
# ``/keyRings/``, so GCPCryptoKey must precede GCPKeyRing).
_FULL_NAME_MAPPINGS: list[_FullNameMapping] = [
    # Cloud Resource Manager.
    _FullNameMapping(
        "//cloudresourcemanager.googleapis.com/",
        "projects",
        "GCPProject",
        "last_segment",
    ),
    _FullNameMapping(
        "//cloudresourcemanager.googleapis.com/",
        "folders",
        "GCPFolder",
        "type_prefixed",
    ),
    _FullNameMapping(
        "//cloudresourcemanager.googleapis.com/",
        "organizations",
        "GCPOrganization",
        "type_prefixed",
    ),
    # Cloud Storage.
    _FullNameMapping(
        "//storage.googleapis.com/",
        "buckets",
        "GCPBucket",
        "last_segment",
        "storage.googleapis.com/Bucket",
    ),
    # BigQuery — table wins over dataset (nested).
    _FullNameMapping(
        "//bigquery.googleapis.com/",
        "tables",
        "GCPBigQueryTable",
        "bigquery_table",
        "bigquery.googleapis.com/Table",
    ),
    _FullNameMapping(
        "//bigquery.googleapis.com/",
        "datasets",
        "GCPBigQueryDataset",
        "bigquery_dataset",
        "bigquery.googleapis.com/Dataset",
    ),
    # KMS — cryptoKey wins over keyRing (nested).
    _FullNameMapping(
        "//cloudkms.googleapis.com/",
        "cryptoKeys",
        "GCPCryptoKey",
        "full_path",
        "cloudkms.googleapis.com/CryptoKey",
    ),
    _FullNameMapping(
        "//cloudkms.googleapis.com/",
        "keyRings",
        "GCPKeyRing",
        "full_path",
        "cloudkms.googleapis.com/KeyRing",
    ),
    # Secret Manager — version wins over secret (nested).
    _FullNameMapping(
        "//secretmanager.googleapis.com/",
        "versions",
        "GCPSecretManagerSecretVersion",
        "full_path",
        "secretmanager.googleapis.com/SecretVersion",
    ),
    _FullNameMapping(
        "//secretmanager.googleapis.com/",
        "secrets",
        "GCPSecretManagerSecret",
        "full_path",
        "secretmanager.googleapis.com/Secret",
    ),
    # Artifact Registry.
    _FullNameMapping(
        "//artifactregistry.googleapis.com/",
        "repositories",
        "GCPArtifactRegistryRepository",
        "full_path",
        "artifactregistry.googleapis.com/Repository",
    ),
    # Cloud Run services.
    _FullNameMapping(
        "//run.googleapis.com/",
        "services",
        "GCPCloudRunService",
        "full_path",
        "run.googleapis.com/Service",
    ),
    # IAM service accounts.
    _FullNameMapping(
        "//iam.googleapis.com/",
        "serviceAccounts",
        "GCPServiceAccount",
        "last_segment",
        "iam.googleapis.com/ServiceAccount",
    ),
    # Cloud Functions.
    _FullNameMapping(
        "//cloudfunctions.googleapis.com/",
        "functions",
        "GCPCloudFunction",
        "full_path",
        "cloudfunctions.googleapis.com/Function",
        ("cloudfunctions.googleapis.com/CloudFunction",),
    ),
    # Compute — node id is the "partial URI" (``projects/.../{kind}/{name}``),
    # which matches the path left after stripping the service prefix.
    _FullNameMapping(
        "//compute.googleapis.com/",
        "instances",
        "GCPInstance",
        "full_path",
        "compute.googleapis.com/Instance",
    ),
    _FullNameMapping(
        "//compute.googleapis.com/",
        "networks",
        "GCPVpc",
        "full_path",
        "compute.googleapis.com/Network",
    ),
    _FullNameMapping(
        "//compute.googleapis.com/",
        "subnetworks",
        "GCPSubnet",
        "full_path",
        "compute.googleapis.com/Subnetwork",
    ),
    _FullNameMapping(
        "//compute.googleapis.com/",
        "firewalls",
        "GCPFirewall",
        "full_path",
        "compute.googleapis.com/Firewall",
    ),
]


def _bigquery_resource_id(parts: list[str], table: bool) -> str | None:
    try:
        project_id = parts[parts.index("projects") + 1]
        dataset_id = parts[parts.index("datasets") + 1]
    except (IndexError, ValueError):
        return None
    if not project_id or not dataset_id:
        return None
    if not table:
        return f"{project_id}:{dataset_id}"
    try:
        table_id = parts[parts.index("tables") + 1]
    except (IndexError, ValueError):
        return None
    if not table_id:
        return None
    return f"{project_id}:{dataset_id}.{table_id}"


def _parse_full_resource_name(full_name: str) -> tuple[str | None, str | None]:
    """
    Parse a GCP Cloud Asset full resource name and return the matching
    (target_node_label, target_id) pair when the resource type is part of the
    Cartography ontology, or (None, None) otherwise.

    Full resource name format: ``//{service}.googleapis.com/{path}``.
    """
    for mapping in _FULL_NAME_MAPPINGS:
        if not full_name.startswith(mapping.service_prefix):
            continue
        path = full_name[len(mapping.service_prefix) :].rstrip("/")
        if not path:
            continue
        parts = path.split("/")
        try:
            marker_idx = parts.index(mapping.marker)
        except ValueError:
            continue
        if marker_idx + 1 >= len(parts):
            continue
        name_segment = parts[marker_idx + 1]
        if not name_segment:
            continue
        if mapping.id_mode == "bigquery_dataset":
            return mapping.label, _bigquery_resource_id(parts, table=False)
        if mapping.id_mode == "bigquery_table":
            return mapping.label, _bigquery_resource_id(parts, table=True)
        if mapping.id_mode == "last_segment":
            return mapping.label, name_segment
        if mapping.id_mode == "type_prefixed":
            return mapping.label, f"{mapping.marker}/{name_segment}"
        # full_path: keep everything up to and including the resource name.
        # Sub-paths (e.g. a policy on a secret version, or on a cryptoKey
        # version) resolve to the nearest ancestor in the ontology via the
        # mapping order defined above.
        return mapping.label, "/".join(parts[: marker_idx + 2])
    return None, None


def _search_asset_types_from_full_name_mappings() -> list[str]:
    return [
        asset_type
        for mapping in _FULL_NAME_MAPPINGS
        for asset_type in (
            ((mapping.asset_type,) if mapping.asset_type is not None else ())
            + mapping.additional_asset_types
        )
    ]


class PolicyBindingsSyncStatus(str, Enum):
    SUCCESS = "success"
    SKIPPED_API_DISABLED = "skipped_api_disabled"
    SKIPPED_PERMISSION_DENIED = "skipped_permission_denied"
    SKIPPED_RATE_LIMIT = "skipped_rate_limit"
    SKIPPED_RETRY_EXHAUSTED = "skipped_retry_exhausted"


@dataclass(frozen=True)
class PolicyBindingsSyncResult:
    status: PolicyBindingsSyncStatus
    permission_context: GCPPrincipalPermissionContext


CAI_POLICY_BINDINGS_RETRY_INITIAL = 1.0
CAI_POLICY_BINDINGS_RETRY_MAX = 32.0
CAI_POLICY_BINDINGS_RETRY_MULTIPLIER = 2.0
CAI_POLICY_BINDINGS_RETRY_TIMEOUT = 300.0
CAI_POLICY_BINDINGS_BATCH_TIMEOUT = 300.0
CAI_POLICY_BINDINGS_SEARCH_TIMEOUT = 30.0
CAI_POLICY_BINDINGS_MIN_INTERVAL_SECONDS = {
    # Cloud Asset default quotas:
    # BatchGetEffectiveIamPolicies: 100/min/project ~= 0.6s between calls
    # SearchAllIamPolicies: 400/min/project ~= 0.15s between calls
    "batch_get_effective_iam_policies": 0.75,
    "search_all_iam_policies": 0.20,
}
GCP_POLICY_BINDINGS_GRAPH_BATCH_SIZE = 1000
GCP_POLICY_BINDINGS_CLEANUP_ITERATION_SIZE = 1000
GCP_POLICY_BINDINGS_GRAPH_CONCURRENCY = 4
# Without this filter, Cloud Asset can return direct IAM policies for very high
# cardinality child resources such as Artifact Registry Docker images. Those
# bindings are not useful to Cartography today and can dominate graph writes.
GCP_POLICY_BINDINGS_SEARCH_ASSET_TYPES = _search_asset_types_from_full_name_mappings()
_CAI_POLICY_BINDINGS_THROTTLE_LOCK = Lock()
_CAI_POLICY_BINDINGS_LAST_CALL_BY_OPERATION: dict[str, float] = {}
_GCP_POLICY_BINDINGS_GRAPH_SEMAPHORE = BoundedSemaphore(
    GCP_POLICY_BINDINGS_GRAPH_CONCURRENCY
)


@dataclass
class InheritedPolicyBindingClaimState:
    lock: Lock = field(default_factory=Lock)
    seen: set[tuple[str, str, str]] = field(default_factory=set)


def _wait_for_cai_policy_bindings_slot(operation: str) -> None:
    min_interval = CAI_POLICY_BINDINGS_MIN_INTERVAL_SECONDS[operation]
    sleep_for = 0.0
    with _CAI_POLICY_BINDINGS_THROTTLE_LOCK:
        now = time.monotonic()
        next_allowed_time = _CAI_POLICY_BINDINGS_LAST_CALL_BY_OPERATION.get(
            operation,
            now,
        )
        scheduled_time = max(now, next_allowed_time)
        sleep_for = max(0.0, scheduled_time - now)
        _CAI_POLICY_BINDINGS_LAST_CALL_BY_OPERATION[operation] = (
            scheduled_time + min_interval
        )

    if sleep_for > 0:
        logger.debug(
            "Throttling Cloud Asset policy bindings %s for %.2f seconds.",
            operation,
            sleep_for,
        )
        time.sleep(sleep_for)


def _log_cai_policy_bindings_retry(
    project_id: str,
    operation: str,
    exc: Exception,
) -> None:
    if isinstance(exc, ResourceExhausted):
        error_kind = "quota/rate-limit error"
    else:
        error_kind = "transient gRPC error"
    logger.warning(
        "Retrying Cloud Asset policy bindings %s for project %s after %s: %s",
        operation,
        project_id,
        error_kind,
        exc,
    )


def build_cai_policy_bindings_retry(project_id: str, operation: str) -> Retry:
    return Retry(
        predicate=if_exception_type(
            DeadlineExceeded,
            ResourceExhausted,
            ServiceUnavailable,
        ),
        initial=CAI_POLICY_BINDINGS_RETRY_INITIAL,
        maximum=CAI_POLICY_BINDINGS_RETRY_MAX,
        multiplier=CAI_POLICY_BINDINGS_RETRY_MULTIPLIER,
        timeout=CAI_POLICY_BINDINGS_RETRY_TIMEOUT,
        on_error=lambda exc: _log_cai_policy_bindings_retry(
            project_id,
            operation,
            exc,
        ),
    )


def _is_rate_limit_retry_error(exc: Exception) -> bool:
    return isinstance(exc, RetryError) and isinstance(exc.cause, ResourceExhausted)


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
    _wait_for_cai_policy_bindings_slot("batch_get_effective_iam_policies")
    response = client.batch_get_effective_iam_policies(
        request=BatchGetEffectiveIamPoliciesRequest(
            scope=effective_scope, names=[project_resource_name]
        ),
        retry=build_cai_policy_bindings_retry(
            project_id,
            "batch_get_effective_iam_policies",
        ),
        timeout=CAI_POLICY_BINDINGS_BATCH_TIMEOUT,
    )
    effective_dict = MessageToDict(response._pb, preserving_proto_field_name=True)

    policies.extend(
        effective_dict["policy_results"]
    )  # Fail Loudly if policy_results is not present

    # Fetch direct policy bindings for all child resources using search_all_iam_policies (project scope - no inheritance)
    search_request = SearchAllIamPoliciesRequest(
        scope=f"projects/{project_id}",
        asset_types=GCP_POLICY_BINDINGS_SEARCH_ASSET_TYPES,
    )
    search_retry = build_cai_policy_bindings_retry(
        project_id,
        "search_all_iam_policies",
    )
    _wait_for_cai_policy_bindings_slot("search_all_iam_policies")
    search_pager = client.search_all_iam_policies(
        request=search_request,
        retry=search_retry,
        timeout=CAI_POLICY_BINDINGS_SEARCH_TIMEOUT,
    )
    for page in search_pager.pages:
        for policy in page.results:
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
        if page.next_page_token:
            _wait_for_cai_policy_bindings_slot("search_all_iam_policies")

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
                is_public = False
                for member in members:
                    # GCP encodes the "anyone on the internet" principals as
                    # plain identifiers without a "type:" prefix. They never
                    # resolve to a real GCPPrincipal node, but we still want
                    # to keep the binding so callers can detect public exposure.
                    if member in ("allUsers", "allAuthenticatedUsers"):
                        is_public = True
                        continue
                    if ":" not in member:
                        continue
                    member_type, identifier = member.split(":", 1)
                    if member_type in ("user", "serviceAccount", "group"):
                        # Store only the email part
                        filtered_members.append(identifier)

                # Skip bindings that have no resolvable principals AND no public
                # exposure, e.g. unsupported principal types like domain:.
                if not filtered_members and not is_public:
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
                    bindings[key]["is_public"] = (
                        bindings[key].get("is_public", False) or is_public
                    )
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
                        "is_public": is_public,
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


def _get_inherited_binding_scope(
    binding: dict[str, Any],
) -> tuple[str, str] | None:
    if binding.get("resource_type") not in ("organization", "folder"):
        return None

    label, resource_id = _parse_full_resource_name(binding["resource"])
    if label not in ("GCPOrganization", "GCPFolder") or resource_id is None:
        return None
    return label, resource_id


def _split_bindings_by_graph_scope(
    bindings: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[tuple[str, str], list[dict[str, Any]]]]:
    direct_bindings: list[dict[str, Any]] = []
    inherited_bindings: dict[tuple[str, str], list[dict[str, Any]]] = {}

    for binding in bindings:
        inherited_scope = _get_inherited_binding_scope(binding)
        if inherited_scope is None:
            direct_bindings.append(binding)
            continue
        inherited_bindings.setdefault(inherited_scope, []).append(binding)

    return direct_bindings, inherited_bindings


def _claim_inherited_bindings_for_graph(
    inherited_bindings: dict[tuple[str, str], list[dict[str, Any]]],
    claim_state: InheritedPolicyBindingClaimState,
) -> dict[tuple[str, str], list[dict[str, Any]]]:
    claimed: dict[tuple[str, str], list[dict[str, Any]]] = {}
    with claim_state.lock:
        for scope, bindings in inherited_bindings.items():
            owner_label, owner_id = scope
            for binding in bindings:
                seen_key = (owner_label, owner_id, binding["id"])
                if seen_key in claim_state.seen:
                    continue
                claim_state.seen.add(seen_key)
                claimed.setdefault(scope, []).append(binding)

    return claimed


def make_policy_binding_applies_to_matchlink(
    target_node_label: str,
    owner_label: str,
) -> GCPPolicyBindingAppliesToMatchLink:
    return GCPPolicyBindingAppliesToMatchLink(
        target_node_label=target_node_label,
        source_node_sub_resource=MatchLinkSubResource(
            target_node_label=owner_label,
            target_node_matcher=make_target_node_matcher(
                {"id": PropertyRef("_sub_resource_id", set_in_kwargs=True)},
            ),
            direction=LinkDirection.INWARD,
            rel_label="RESOURCE",
        ),
    )


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
        batch_size=GCP_POLICY_BINDINGS_GRAPH_BATCH_SIZE,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )

    for target_label, links in _group_applies_to_links(bindings).items():
        load_matchlinks(
            neo4j_session,
            make_policy_binding_applies_to_matchlink(target_label, "GCPProject"),
            links,
            batch_size=GCP_POLICY_BINDINGS_GRAPH_BATCH_SIZE,
            lastupdated=update_tag,
            _sub_resource_label="GCPProject",
            _sub_resource_id=project_id,
        )


def _load_organization_bindings(
    neo4j_session: neo4j.Session,
    bindings: list[dict[str, Any]],
    org_resource_name: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GCPOrganizationPolicyBindingSchema(),
        bindings,
        batch_size=GCP_POLICY_BINDINGS_GRAPH_BATCH_SIZE,
        lastupdated=update_tag,
        ORG_RESOURCE_NAME=org_resource_name,
    )

    for target_label, links in _group_applies_to_links(bindings).items():
        load_matchlinks(
            neo4j_session,
            make_policy_binding_applies_to_matchlink(target_label, "GCPOrganization"),
            links,
            batch_size=GCP_POLICY_BINDINGS_GRAPH_BATCH_SIZE,
            lastupdated=update_tag,
            _sub_resource_label="GCPOrganization",
            _sub_resource_id=org_resource_name,
        )


def _load_folder_bindings(
    neo4j_session: neo4j.Session,
    bindings: list[dict[str, Any]],
    folder_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GCPFolderPolicyBindingSchema(),
        bindings,
        batch_size=GCP_POLICY_BINDINGS_GRAPH_BATCH_SIZE,
        lastupdated=update_tag,
        FOLDER_ID=folder_id,
    )

    for target_label, links in _group_applies_to_links(bindings).items():
        load_matchlinks(
            neo4j_session,
            make_policy_binding_applies_to_matchlink(target_label, "GCPFolder"),
            links,
            batch_size=GCP_POLICY_BINDINGS_GRAPH_BATCH_SIZE,
            lastupdated=update_tag,
            _sub_resource_label="GCPFolder",
            _sub_resource_id=folder_id,
        )


@timeit
def load_inherited_bindings(
    neo4j_session: neo4j.Session,
    inherited_bindings: dict[tuple[str, str], list[dict[str, Any]]],
    update_tag: int,
) -> int:
    loaded_count = 0
    for (owner_label, owner_id), bindings in inherited_bindings.items():
        if owner_label == "GCPOrganization":
            _load_organization_bindings(
                neo4j_session,
                bindings,
                owner_id,
                update_tag,
            )
        elif owner_label == "GCPFolder":
            _load_folder_bindings(
                neo4j_session,
                bindings,
                owner_id,
                update_tag,
            )
        else:
            raise ValueError(
                f"Unsupported inherited GCP policy binding owner label: {owner_label}"
            )
        loaded_count += len(bindings)
    return loaded_count


def _cleanup_applies_to_relationships(
    neo4j_session: neo4j.Session,
    sub_resource_label: str,
    sub_resource_id: str,
    update_tag: int,
) -> None:
    # APPLIES_TO can point at several resource labels. Clean up by relationship
    # scope directly instead of running the same stale-edge cleanup once per
    # possible target label.
    GraphStatement(
        """
        MATCH (:GCPPolicyBinding)-[r:APPLIES_TO]->()
        WHERE r.lastupdated <> $UPDATE_TAG
            AND r._sub_resource_label = $_sub_resource_label
            AND r._sub_resource_id = $_sub_resource_id
        WITH r LIMIT $LIMIT_SIZE
        DELETE r;
        """,
        parameters={
            "UPDATE_TAG": update_tag,
            "_sub_resource_label": sub_resource_label,
            "_sub_resource_id": sub_resource_id,
        },
        iterative=True,
        iterationsize=GCP_POLICY_BINDINGS_CLEANUP_ITERATION_SIZE,
        parent_job_name="APPLIES_TO",
    ).run(neo4j_session)


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.debug("Running GCP policy bindings cleanup job")

    # During migration, project cleanup also removes stale project-owned
    # RESOURCE edges for inherited org/folder bindings that are now owned by
    # their real scope.
    GraphJob.from_node_schema(
        GCPPolicyBindingSchema(),
        common_job_parameters,
        iterationsize=GCP_POLICY_BINDINGS_CLEANUP_ITERATION_SIZE,
    ).run(neo4j_session)

    project_id = common_job_parameters["PROJECT_ID"]
    update_tag = common_job_parameters["UPDATE_TAG"]
    _cleanup_applies_to_relationships(
        neo4j_session,
        "GCPProject",
        project_id,
        update_tag,
    )


@timeit
def cleanup_inherited_policy_bindings(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    folder_ids: list[str],
) -> None:
    logger.debug("Running inherited GCP policy bindings cleanup job")
    org_resource_name = common_job_parameters["ORG_RESOURCE_NAME"]
    update_tag = common_job_parameters["UPDATE_TAG"]

    GraphJob.from_node_schema(
        GCPOrganizationPolicyBindingSchema(),
        common_job_parameters,
        iterationsize=GCP_POLICY_BINDINGS_CLEANUP_ITERATION_SIZE,
    ).run(neo4j_session)
    _cleanup_applies_to_relationships(
        neo4j_session,
        "GCPOrganization",
        org_resource_name,
        update_tag,
    )

    for folder_id in folder_ids:
        folder_job_parameters = {
            **common_job_parameters,
            "FOLDER_ID": folder_id,
        }
        GraphJob.from_node_schema(
            GCPFolderPolicyBindingSchema(),
            folder_job_parameters,
            iterationsize=GCP_POLICY_BINDINGS_CLEANUP_ITERATION_SIZE,
        ).run(neo4j_session)
        _cleanup_applies_to_relationships(
            neo4j_session,
            "GCPFolder",
            folder_id,
            update_tag,
        )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    project_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    client: AssetServiceClient,
    role_permissions_by_name: dict[str, list[str]],
    inherited_binding_claim_state: InheritedPolicyBindingClaimState | None = None,
) -> PolicyBindingsSyncResult:
    """
    Sync GCP IAM policy bindings for a project.

    Returns a status describing whether policy bindings were refreshed.
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
        return PolicyBindingsSyncResult(
            PolicyBindingsSyncStatus.SKIPPED_PERMISSION_DENIED,
            {},
        )
    except RetryError as e:
        if _is_rate_limit_retry_error(e):
            logger.warning(
                "Cloud Asset policy bindings retries exhausted for project %s after quota/rate-limit errors. "
                "Preserving existing policy-binding and permission-relationship data. Error: %s",
                project_id,
                e,
            )
            return PolicyBindingsSyncResult(
                PolicyBindingsSyncStatus.SKIPPED_RATE_LIMIT,
                {},
            )
        logger.warning(
            "Cloud Asset policy bindings retries exhausted for project %s after transient gRPC errors. "
            "Preserving existing policy-binding and permission-relationship data. Error: %s",
            project_id,
            e,
        )
        return PolicyBindingsSyncResult(
            PolicyBindingsSyncStatus.SKIPPED_RETRY_EXHAUSTED,
            {},
        )
    except (DeadlineExceeded, ResourceExhausted, ServiceUnavailable) as e:
        if isinstance(e, ResourceExhausted):
            logger.warning(
                "Cloud Asset policy bindings rate-limited for project %s. "
                "Preserving existing policy-binding and permission-relationship data. Error: %s",
                project_id,
                e,
            )
            return PolicyBindingsSyncResult(
                PolicyBindingsSyncStatus.SKIPPED_RATE_LIMIT,
                {},
            )
        logger.warning(
            "Cloud Asset policy bindings failed for project %s with a transient gRPC error. "
            "Preserving existing policy-binding and permission-relationship data. Error: %s",
            project_id,
            e,
        )
        return PolicyBindingsSyncResult(
            PolicyBindingsSyncStatus.SKIPPED_RETRY_EXHAUSTED,
            {},
        )

    transformed_bindings_data = transform_bindings(bindings_data)
    direct_bindings, inherited_bindings = _split_bindings_by_graph_scope(
        transformed_bindings_data
    )
    permission_context = build_principals_from_policy_bindings(
        transformed_bindings_data,
        role_permissions_by_name,
        project_id,
    )

    if inherited_binding_claim_state is None:
        inherited_binding_claim_state = InheritedPolicyBindingClaimState()

    with _GCP_POLICY_BINDINGS_GRAPH_SEMAPHORE:
        inherited_bindings_to_load = _claim_inherited_bindings_for_graph(
            inherited_bindings,
            inherited_binding_claim_state,
        )
        inherited_loaded_count = load_inherited_bindings(
            neo4j_session,
            inherited_bindings_to_load,
            update_tag,
        )
        load_bindings(neo4j_session, direct_bindings, project_id, update_tag)
        cleanup(neo4j_session, common_job_parameters)
    logger.info(
        "Synced GCP policy bindings for project '%s': policy_results=%d, "
        "transformed_bindings=%d, direct_graph_bindings=%d, "
        "inherited_bindings=%d, newly_loaded_inherited_bindings=%d, "
        "permission_principals=%d",
        project_id,
        len(bindings_data["policy_results"]),
        len(transformed_bindings_data),
        len(direct_bindings),
        sum(len(bindings) for bindings in inherited_bindings.values()),
        inherited_loaded_count,
        len(permission_context),
    )
    return PolicyBindingsSyncResult(
        PolicyBindingsSyncStatus.SUCCESS,
        permission_context,
    )
