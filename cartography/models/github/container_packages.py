"""
GitHub Container Package Schema

Represents container packages (images) stored in GitHub Container Registry (GHCR).
Each organization can have multiple container packages.

See: https://docs.github.com/en/rest/packages/packages
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
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GitHubContainerPackageNodeProperties(CartographyNodeProperties):
    """
    Properties for a GitHub Container Package node.

    Container packages are collections of container images within GitHub Container Registry.
    """

    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    package_type: PropertyRef = PropertyRef("package_type")
    visibility: PropertyRef = PropertyRef("visibility")
    url: PropertyRef = PropertyRef("url")
    html_url: PropertyRef = PropertyRef("html_url")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    owner_login: PropertyRef = PropertyRef("owner_login")
    owner_type: PropertyRef = PropertyRef("owner_type")
    repository_id: PropertyRef = PropertyRef("repository_id")
    repository_name: PropertyRef = PropertyRef("repository_name")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubContainerPackageToOrgRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubContainerPackageToOrgRel(CartographyRelSchema):
    """
    Sub-resource relationship from GitHubContainerPackage to GitHubOrganization.
    All container registry resources are scoped to the organization for cleanup.
    """

    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org_url", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitHubContainerPackageToOrgRelProperties = (
        GitHubContainerPackageToOrgRelProperties()
    )


@dataclass(frozen=True)
class GitHubContainerPackageSchema(CartographyNodeSchema):
    """
    Schema for GitHub Container Package nodes.
    """

    label: str = "GitHubContainerPackage"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ContainerRegistry"])
    properties: GitHubContainerPackageNodeProperties = (
        GitHubContainerPackageNodeProperties()
    )
    sub_resource_relationship: GitHubContainerPackageToOrgRel = (
        GitHubContainerPackageToOrgRel()
    )
