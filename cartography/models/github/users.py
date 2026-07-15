"""
RE: Tenant relationship between GitHubUser and GitHubOrganization

Note this relationship is implemented via 'other_relationships' and not via the 'sub_resource_relationship'
as might be expected.

The 'sub_resource_relationship' typically describes the relationship of a node to its tenant (the org, project, or
other resource to which other nodes belong).  An assumption of that relationship is that if the tenant goes
away, all nodes related to it should be cleaned up.

In GitHub, though the GitHubUser's tenant seems to be GitHubOrganization, users actually exist independently.  There
is a concept of 'UNAFFILIATED' users (https://docs.github.com/en/graphql/reference/enums#roleinorganization) like
Enterprise Owners who are related to an org even if they are not direct members of it.  You would not want them to be
cleaned up, if an org goes away, and you could want them in your graph even if they are not members of any org in
the enterprise.

To allow for this in the schema, this relationship is treated as any other node-to-node relationship, via
'other_relationships', instead of as the typical 'sub_resource_relationship'.

RE: GitHubOrganizationUserSchema vs GitHubUnaffiliatedUserSchema

As noted above, there are implicitly two types of users, those that are part of, or affiliated, to a target
GitHubOrganization, and those that are not part, or unaffiliated.   Both are represented as GitHubUser nodes,
but there are two schemas below to allow for a difference between them: unaffiliated nodes lack this property:
  * the 'has_2fa_enabled' property, because the GitHub api does not return it, for these users
The main importance of having two schemas is to allow the two sets of users to be loaded separately.  If we are loading
an unaffiliated user, but the user already exists in the graph (perhaps they are members of another GitHub orgs for
example), then loading the unaffiliated user will not blank out the 'has_2fa_enabled' property.
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
class BaseGitHubUserNodeProperties(CartographyNodeProperties):
    # core properties in all GitHubUser nodes
    id: PropertyRef = PropertyRef("url", description="GitHub user profile URL.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    fullname: PropertyRef = PropertyRef("name", description="GitHub user display name.")
    username: PropertyRef = PropertyRef(
        "login", extra_index=True, description="GitHub user login."
    )
    is_site_admin: PropertyRef = PropertyRef(
        "isSiteAdmin", description="Whether the user is a GitHub site administrator."
    )
    is_enterprise_owner: PropertyRef = PropertyRef(
        "isEnterpriseOwner",
        description="Whether the user is a GitHub enterprise owner.",
    )
    email: PropertyRef = PropertyRef(
        "email", description="Publicly visible profile email."
    )
    company: PropertyRef = PropertyRef("company", description="Public profile company.")
    organization_verified_domain_emails: PropertyRef = PropertyRef(
        "organizationVerifiedDomainEmails",
        description="Email addresses verified against organization domains.",
    )


@dataclass(frozen=True)
class GitHubOrganizationUserNodeProperties(BaseGitHubUserNodeProperties):
    # specified for affiliated users only. The GitHub api does not return this property for unaffiliated users.
    has_2fa_enabled: PropertyRef = PropertyRef(
        "hasTwoFactorEnabled",
        description="Whether the organization member has two-factor authentication enabled.",
    )


@dataclass(frozen=True)
class GitHubUnaffiliatedUserNodeProperties(BaseGitHubUserNodeProperties):
    # No additional properties needed
    pass


@dataclass(frozen=True)
class GitHubUserToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubUserMemberOfOrganizationRel(CartographyRelSchema):
    """Links a GitHub user or child team to its parent organization or team."""

    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("MEMBER_OF")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: GitHubUserToOrganizationRelProperties = (
        GitHubUserToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class GitHubUserAdminOfOrganizationRel(CartographyRelSchema):
    """Identifies a user as an administrator of a GitHub organization."""

    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ADMIN_OF")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ADMIN_OF"
    properties: GitHubUserToOrganizationRelProperties = (
        GitHubUserToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class GitHubUserUnaffiliatedOrganizationRel(CartographyRelSchema):
    """Links an enterprise owner to an organization where the user is not a member."""

    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("UNAFFILIATED")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "UNAFFILIATED"
    properties: GitHubUserToOrganizationRelProperties = (
        GitHubUserToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class GitHubOrganizationUserSchema(CartographyNodeSchema):
    """A user account in GitHub."""

    label: str = "GitHubUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["UserAccount"]
    )  # UserAccount label is used for ontology mapping
    properties: GitHubOrganizationUserNodeProperties = (
        GitHubOrganizationUserNodeProperties()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GitHubUserMemberOfOrganizationRel(),
            GitHubUserAdminOfOrganizationRel(),
        ],
    )
    sub_resource_relationship = None


@dataclass(frozen=True)
class GitHubUnaffiliatedUserSchema(CartographyNodeSchema):
    """A user account in GitHub."""

    label: str = "GitHubUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["UserAccount"]
    )  # UserAccount label is used for ontology mapping
    properties: GitHubUnaffiliatedUserNodeProperties = (
        GitHubUnaffiliatedUserNodeProperties()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GitHubUserUnaffiliatedOrganizationRel(),
        ],
    )
    sub_resource_relationship = None
