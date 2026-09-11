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
class GitHubExternalIdentityNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Organization URL and GitHub external identity node ID."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    saml_name_id: PropertyRef = PropertyRef(
        "saml_name_id",
        description="SAML NameID supplied by the organization's identity provider; not necessarily an email address.",
    )


@dataclass(frozen=True)
class GitHubExternalIdentityRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubExternalIdentityToOrganizationRel(CartographyRelSchema):
    """Scopes an external identity to the organization that federates it."""

    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org_url", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitHubExternalIdentityRelProperties = (
        GitHubExternalIdentityRelProperties()
    )


@dataclass(frozen=True)
class GitHubExternalIdentityToUserRel(CartographyRelSchema):
    """Links a GitHub account to its organization-specific external identity."""

    target_node_label: str = "GitHubUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_url")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_IDENTITY"
    properties: GitHubExternalIdentityRelProperties = (
        GitHubExternalIdentityRelProperties()
    )


@dataclass(frozen=True)
class GitHubExternalIdentitySchema(CartographyNodeSchema):
    """An organization's federated identity, optionally linked to a GitHub account.

    SAML NameIDs retain their provider meaning independently of GitHub public
    and verified-domain emails. Email-shaped NameIDs can link organization
    members to an existing canonical User when the match is unambiguous.
    """

    label: str = "GitHubExternalIdentity"
    properties: GitHubExternalIdentityNodeProperties = (
        GitHubExternalIdentityNodeProperties()
    )
    sub_resource_relationship: GitHubExternalIdentityToOrganizationRel = (
        GitHubExternalIdentityToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [GitHubExternalIdentityToUserRel()]
    )
