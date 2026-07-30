from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class RailwayDeploymentTriggerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    provider: PropertyRef = PropertyRef("provider", extra_index=True)
    # owner/name form, matching GitHubRepository.fullname.
    repository: PropertyRef = PropertyRef("repository", extra_index=True)
    branch: PropertyRef = PropertyRef("branch")
    service_id: PropertyRef = PropertyRef("serviceId")
    environment_id: PropertyRef = PropertyRef("environmentId")


@dataclass(frozen=True)
class RailwayDeploymentTriggerToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayProject)-[:RESOURCE]->(:RailwayDeploymentTrigger)
class RailwayDeploymentTriggerToProjectRel(CartographyRelSchema):
    target_node_label: str = "RailwayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RailwayDeploymentTriggerToProjectRelProperties = (
        RailwayDeploymentTriggerToProjectRelProperties()
    )


@dataclass(frozen=True)
class RailwayDeploymentTriggerToServiceInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayServiceInstance)-[:HAS]->(:RailwayDeploymentTrigger)
class RailwayDeploymentTriggerToServiceInstanceRel(CartographyRelSchema):
    target_node_label: str = "RailwayServiceInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "service_id": PropertyRef("serviceId"),
            "environment_id": PropertyRef("environmentId"),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: RailwayDeploymentTriggerToServiceInstanceRelProperties = (
        RailwayDeploymentTriggerToServiceInstanceRelProperties()
    )


@dataclass(frozen=True)
class RailwayDeploymentTriggerToGitHubRepositoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayDeploymentTrigger)-[:TRACKS]->(:GitHubRepository), joined on owner/name.
# Best-effort: only created if the GitHub repo has also been ingested (OPTIONAL MATCH).
class RailwayDeploymentTriggerToGitHubRepositoryRel(CartographyRelSchema):
    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"fullname": PropertyRef("repository")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "TRACKS"
    properties: RailwayDeploymentTriggerToGitHubRepositoryRelProperties = (
        RailwayDeploymentTriggerToGitHubRepositoryRelProperties()
    )


@dataclass(frozen=True)
class RailwayDeploymentTriggerSchema(CartographyNodeSchema):
    label: str = "RailwayDeploymentTrigger"
    properties: RailwayDeploymentTriggerNodeProperties = (
        RailwayDeploymentTriggerNodeProperties()
    )
    sub_resource_relationship: RailwayDeploymentTriggerToProjectRel = (
        RailwayDeploymentTriggerToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            RailwayDeploymentTriggerToServiceInstanceRel(),
            RailwayDeploymentTriggerToGitHubRepositoryRel(),
        ],
    )
