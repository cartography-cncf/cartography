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
    id: PropertyRef = PropertyRef(
        "id", description="ID of the Railway service instance."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    service_id: PropertyRef = PropertyRef(
        "serviceId", extra_index=True, description="ID of the parent service."
    )
    service_name: PropertyRef = PropertyRef(
        "serviceName", extra_index=True, description="Name of the parent service."
    )
    environment_id: PropertyRef = PropertyRef(
        "environmentId",
        extra_index=True,
        description="ID of the environment where the instance is deployed.",
    )
    # Provenance: exactly one of these is set. `source_repo` is in owner/name form, matching
    # GitHubRepository.fullname.
    source_image: PropertyRef = PropertyRef(
        "source_image",
        extra_index=True,
        description="Container image run by the instance, when deployed from a registry.",
    )
    source_repo: PropertyRef = PropertyRef(
        "source_repo",
        extra_index=True,
        description="Source repository in owner/name form, when deployed from git.",
    )
    builder: PropertyRef = PropertyRef(
        "builder", description="Build system used by the instance."
    )
    build_command: PropertyRef = PropertyRef(
        "buildCommand", description="Custom build command, if configured."
    )
    start_command: PropertyRef = PropertyRef(
        "startCommand", description="Custom start command, if configured."
    )
    root_directory: PropertyRef = PropertyRef(
        "rootDirectory", description="Repository subdirectory built by the service."
    )
    dockerfile_path: PropertyRef = PropertyRef(
        "dockerfilePath", description="Path to the custom Dockerfile, if configured."
    )
    # The effective region. Railway only populates ServiceInstance.region when the instance
    # overrides the workspace default, so transform() falls back to the workspace's
    # preferredRegion; region_is_workspace_default records which of the two it came from.
    # num_replicas scales the instance within this one region - Railway exposes no
    # per-replica placement.
    region: PropertyRef = PropertyRef(
        "region", extra_index=True, description="Effective deployment region."
    )
    region_is_workspace_default: PropertyRef = PropertyRef(
        "region_is_workspace_default",
        description="Whether the effective region comes from the workspace default.",
    )
    num_replicas: PropertyRef = PropertyRef(
        "numReplicas", description="Number of replicas running in the effective region."
    )
    sleep_application: PropertyRef = PropertyRef(
        "sleepApplication", description="Whether the application sleeps while inactive."
    )
    cron_schedule: PropertyRef = PropertyRef(
        "cronSchedule",
        description="Cron schedule for scheduled execution, if configured.",
    )
    healthcheck_path: PropertyRef = PropertyRef(
        "healthcheckPath", description="HTTP health-check path, if configured."
    )
    restart_policy_type: PropertyRef = PropertyRef(
        "restartPolicyType", description="Policy governing when the instance restarts."
    )
    restart_policy_max_retries: PropertyRef = PropertyRef(
        "restartPolicyMaxRetries",
        description="Maximum restart attempts allowed by the restart policy.",
    )
    ipv6_egress_enabled: PropertyRef = PropertyRef(
        "ipv6EgressEnabled", description="Whether outbound IPv6 traffic is enabled."
    )
    latest_deployment_id: PropertyRef = PropertyRef(
        "latest_deployment_id", description="ID of the latest deployment."
    )
    latest_deployment_status: PropertyRef = PropertyRef(
        "latest_deployment_status", description="Status of the latest deployment."
    )
    # Exposure signal: true when the instance is reachable from the internet through a
    # Railway-generated domain, a verified custom domain or a TCP proxy. Persisted so the
    # exposure rules can test it directly rather than re-deriving the join.
    is_publicly_exposed: PropertyRef = PropertyRef(
        "is_publicly_exposed",
        description="Whether the instance is reachable from the public internet.",
    )
    created_at: PropertyRef = PropertyRef(
        "createdAt", description="Time when the service instance was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updatedAt", description="Time when the service instance was last modified."
    )


@dataclass(frozen=True)
class RailwayServiceInstanceToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayProject)-[:RESOURCE]->(:RailwayServiceInstance)
class RailwayServiceInstanceToProjectRel(CartographyRelSchema):
    """Connects a Railway project to a service instance that it contains."""

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
    """Connects a Railway service to one of its environment-specific instances."""

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
    """Connects a Railway environment to a service instance deployed within it."""

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
    """Identifies the GitHub repository used to deploy a Railway service instance."""

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
    """A Railway service deployed into a specific environment."""

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
