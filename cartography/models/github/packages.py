"""
GitHub Package Schema.

Represents container packages hosted on GitHub Container Registry (ghcr.io).

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
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GitHubPackageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("html_url")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    package_type: PropertyRef = PropertyRef("package_type", extra_index=True)
    visibility: PropertyRef = PropertyRef("visibility")
    uri: PropertyRef = PropertyRef("uri", extra_index=True)
    html_url: PropertyRef = PropertyRef("html_url", extra_index=True)
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubPackageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubPackageToOrgRel(CartographyRelSchema):
    """
    Sub-resource relationship from GitHubPackage to GitHubOrganization.
    """

    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org_url", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitHubPackageRelProperties = GitHubPackageRelProperties()


@dataclass(frozen=True)
class GitHubPackageToRepositoryRel(CartographyRelSchema):
    """
    Links a package to the repository that owns it. Best-effort — not every
    package payload has a `repository` field.
    """

    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repository_url")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_PACKAGE"
    properties: GitHubPackageRelProperties = GitHubPackageRelProperties()


@dataclass(frozen=True)
class GitHubPackageSchema(CartographyNodeSchema):
    label: str = "GitHubPackage"
    properties: GitHubPackageNodeProperties = GitHubPackageNodeProperties()
    sub_resource_relationship: GitHubPackageToOrgRel = GitHubPackageToOrgRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [GitHubPackageToRepositoryRel()],
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ContainerRegistry"])
