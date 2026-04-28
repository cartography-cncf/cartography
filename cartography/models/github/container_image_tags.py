"""
GitHub Container Image Tag Schema.

Represents tags within a GitHub container package. Tags are pointers to
specific container images identified by digest. Multiple tags can point to
the same image digest (e.g., "latest" and "v1.0.0").
"""

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


@dataclass(frozen=True)
class GitHubContainerImageTagNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uri")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    uri: PropertyRef = PropertyRef("uri", extra_index=True)
    digest: PropertyRef = PropertyRef("digest", extra_index=True)
    image_pushed_at: PropertyRef = PropertyRef("image_pushed_at")
    package_id: PropertyRef = PropertyRef("package_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubContainerImageTagRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubContainerImageTagToOrgRel(CartographyRelSchema):
    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org_url", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitHubContainerImageTagRelProperties = (
        GitHubContainerImageTagRelProperties()
    )


@dataclass(frozen=True)
class GitHubContainerImageTagToImageRel(CartographyRelSchema):
    """
    Generic cross-registry edge from ImageTag to Image. The supply-chain
    matcher in cartography/intel/github/supply_chain.py traverses this edge
    via the (:Image)<-[:IMAGE]-(:ImageTag)<-[:REPO_IMAGE]-(:ContainerRegistry)
    pattern, so the relationship label and direction must match GitLab/AWS.
    """

    target_node_label: str = "GitHubContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IMAGE"
    properties: GitHubContainerImageTagRelProperties = (
        GitHubContainerImageTagRelProperties()
    )


@dataclass(frozen=True)
class GitHubContainerImageTagToPackageRel(CartographyRelSchema):
    """
    Generic cross-registry edge from ContainerRegistry to ImageTag.
    """

    target_node_label: str = "GitHubPackage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("package_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "REPO_IMAGE"
    properties: GitHubContainerImageTagRelProperties = (
        GitHubContainerImageTagRelProperties()
    )


@dataclass(frozen=True)
class GitHubContainerImageTagSchema(CartographyNodeSchema):
    label: str = "GitHubContainerImageTag"
    properties: GitHubContainerImageTagNodeProperties = (
        GitHubContainerImageTagNodeProperties()
    )
    sub_resource_relationship: GitHubContainerImageTagToOrgRel = (
        GitHubContainerImageTagToOrgRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GitHubContainerImageTagToPackageRel(),
            GitHubContainerImageTagToImageRel(),
        ],
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ImageTag"])
