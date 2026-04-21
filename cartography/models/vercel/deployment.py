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
class VercelDeploymentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uid")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    url: PropertyRef = PropertyRef("url", extra_index=True)
    created_at: PropertyRef = PropertyRef("created")
    ready_at: PropertyRef = PropertyRef("ready")
    state: PropertyRef = PropertyRef("state")
    target: PropertyRef = PropertyRef("target")
    source: PropertyRef = PropertyRef("source")
    creator_uid: PropertyRef = PropertyRef("creator_uid")
    meta_git_commit_sha: PropertyRef = PropertyRef("meta_git_commit_sha")
    meta_git_branch: PropertyRef = PropertyRef("meta_git_branch")


@dataclass(frozen=True)
class VercelDeploymentToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelProject)-[:RESOURCE]->(:VercelDeployment)
class VercelDeploymentToProjectRel(CartographyRelSchema):
    target_node_label: str = "VercelProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: VercelDeploymentToProjectRelProperties = (
        VercelDeploymentToProjectRelProperties()
    )


@dataclass(frozen=True)
class VercelDeploymentToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelDeployment)-[:CREATED_BY]->(:VercelUser)
class VercelDeploymentToUserRel(CartographyRelSchema):
    target_node_label: str = "VercelUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("creator_uid")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CREATED_BY"
    properties: VercelDeploymentToUserRelProperties = (
        VercelDeploymentToUserRelProperties()
    )


@dataclass(frozen=True)
class VercelDeploymentSchema(CartographyNodeSchema):
    label: str = "VercelDeployment"
    properties: VercelDeploymentNodeProperties = VercelDeploymentNodeProperties()
    sub_resource_relationship: VercelDeploymentToProjectRel = (
        VercelDeploymentToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [VercelDeploymentToUserRel()],
    )
