from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GitHubOrganizationDomainNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="GitHub GraphQL node ID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    domain: PropertyRef = PropertyRef(
        "domain", extra_index=True, description="Domain name."
    )
    is_verified: PropertyRef = PropertyRef(
        "is_verified",
        description="Whether the organization proved ownership of the domain with a DNS record.",
    )
    is_approved: PropertyRef = PropertyRef(
        "is_approved",
        description="Whether an organization owner approved the domain without verifying ownership.",
    )
    is_required_for_policy_enforcement: PropertyRef = PropertyRef(
        "is_required_for_policy_enforcement",
        description="Whether the domain is needed to enforce the organization notification restriction policy.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the domain was added."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Timestamp when the domain was last updated."
    )


@dataclass(frozen=True)
class GitHubOrganizationDomainRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubOrganizationDomainToOrgRel(CartographyRelSchema):
    """Scopes a GitHub resource to its organization."""

    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org_url", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitHubOrganizationDomainRelProperties = (
        GitHubOrganizationDomainRelProperties()
    )


@dataclass(frozen=True)
class GitHubOrganizationDomainSchema(CartographyNodeSchema):
    """A verified or approved domain configured on a GitHub organization."""

    label: str = "GitHubOrganizationDomain"
    properties: GitHubOrganizationDomainNodeProperties = (
        GitHubOrganizationDomainNodeProperties()
    )
    sub_resource_relationship: GitHubOrganizationDomainToOrgRel = (
        GitHubOrganizationDomainToOrgRel()
    )
