from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import COMPUTE_SERVICE


@dataclass(frozen=True)
class RailwayServiceInstanceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    service_id: PropertyRef = PropertyRef("serviceId", extra_index=True)
    service_name: PropertyRef = PropertyRef("serviceName", extra_index=True)
    environment_id: PropertyRef = PropertyRef("environmentId", extra_index=True)
    # Provenance: exactly one of these is set. `source_repo` is in owner/name form, matching
    # GitHubRepository.fullname.
    source_image: PropertyRef = PropertyRef("source_image", extra_index=True)
    source_repo: PropertyRef = PropertyRef("source_repo", extra_index=True)
    builder: PropertyRef = PropertyRef("builder")
    build_command: PropertyRef = PropertyRef("buildCommand")
    start_command: PropertyRef = PropertyRef("startCommand")
    root_directory: PropertyRef = PropertyRef("rootDirectory")
    dockerfile_path: PropertyRef = PropertyRef("dockerfilePath")
    # The effective region. Railway only populates ServiceInstance.region when the instance
    # overrides the workspace default, so transform() falls back to the workspace's
    # preferredRegion; region_is_workspace_default records which of the two it came from.
    # num_replicas scales the instance within this one region - Railway exposes no
    # per-replica placement.
    region: PropertyRef = PropertyRef("region", extra_index=True)
    region_is_workspace_default: PropertyRef = PropertyRef(
        "region_is_workspace_default",
    )
    num_replicas: PropertyRef = PropertyRef("numReplicas")
    sleep_application: PropertyRef = PropertyRef("sleepApplication")
    cron_schedule: PropertyRef = PropertyRef("cronSchedule")
    healthcheck_path: PropertyRef = PropertyRef("healthcheckPath")
    restart_policy_type: PropertyRef = PropertyRef("restartPolicyType")
    restart_policy_max_retries: PropertyRef = PropertyRef("restartPolicyMaxRetries")
    ipv6_egress_enabled: PropertyRef = PropertyRef("ipv6EgressEnabled")
    latest_deployment_id: PropertyRef = PropertyRef("latest_deployment_id")
    latest_deployment_status: PropertyRef = PropertyRef("latest_deployment_status")
    # Exposure signal: true when the instance is reachable from the internet through a
    # Railway-generated domain, a verified custom domain or a TCP proxy. Persisted so the
    # exposure rules can test it directly rather than re-deriving the join.
    is_publicly_exposed: PropertyRef = PropertyRef("is_publicly_exposed")
    created_at: PropertyRef = PropertyRef("createdAt")
    updated_at: PropertyRef = PropertyRef("updatedAt")


@dataclass(frozen=True)
class RailwayServiceInstanceToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayProject)-[:RESOURCE]->(:RailwayServiceInstance)
class RailwayServiceInstanceToProjectRel(CartographyRelSchema):
    target_node_label: str = "RailwayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RailwayServiceInstanceToProjectRelProperties = (
        RailwayServiceInstanceToProjectRelProperties()
    )


@dataclass(frozen=True)
class RailwayServiceInstanceToServiceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayService)-[:HAS]->(:RailwayServiceInstance)
class RailwayServiceInstanceToServiceRel(CartographyRelSchema):
    target_node_label: str = "RailwayService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("serviceId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: RailwayServiceInstanceToServiceRelProperties = (
        RailwayServiceInstanceToServiceRelProperties()
    )


@dataclass(frozen=True)
class RailwayServiceInstanceToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayEnvironment)-[:HAS]->(:RailwayServiceInstance)
class RailwayServiceInstanceToEnvironmentRel(CartographyRelSchema):
    target_node_label: str = "RailwayEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("environmentId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: RailwayServiceInstanceToEnvironmentRelProperties = (
        RailwayServiceInstanceToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
class RailwayServiceInstanceToGitHubRepositoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayServiceInstance)-[:DEPLOYED_FROM]->(:GitHubRepository), joined on owner/name.
# Best-effort: only created if the GitHub repo has also been ingested (OPTIONAL MATCH).
class RailwayServiceInstanceToGitHubRepositoryRel(CartographyRelSchema):
    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"fullname": PropertyRef("source_repo")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DEPLOYED_FROM"
    properties: RailwayServiceInstanceToGitHubRepositoryRelProperties = (
        RailwayServiceInstanceToGitHubRepositoryRelProperties()
    )


@dataclass(frozen=True)
class RailwayServiceInstanceSchema(CartographyNodeSchema):
    label: str = "RailwayServiceInstance"
    # The per-environment instance is the actual running workload, so this is where the
    # ComputeService label belongs rather than on RailwayService.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([COMPUTE_SERVICE])
    properties: RailwayServiceInstanceNodeProperties = (
        RailwayServiceInstanceNodeProperties()
    )
    sub_resource_relationship: RailwayServiceInstanceToProjectRel = (
        RailwayServiceInstanceToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            RailwayServiceInstanceToServiceRel(),
            RailwayServiceInstanceToEnvironmentRel(),
            RailwayServiceInstanceToGitHubRepositoryRel(),
        ],
    )
