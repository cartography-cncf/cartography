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
GitHubOrganization, and those that are not part, or unaffiliated.  Both are represented as GitHubUser nodes with the
same properties.  The two schemas differ only in their relationships to the organization: affiliated users get
'MEMBER_OF' and 'ADMIN_OF', unaffiliated users get 'UNAFFILIATED'.

RE: Organization-scoped facts

A GitHubUser node is global, but the sync runs once per organization, and GitHub scopes some facts to the organization
being synced: 'has_2fa_enabled', 'is_enterprise_owner', 'organization_verified_domain_emails' and 'normalized_emails'.
A user can belong to several organizations, so the 'MEMBER_OF' and 'UNAFFILIATED' relationships hold each
organization's answer.  The node properties of the same names are owned by the analysis jobs in
cartography.analysis.github.analysis, which combine the answers of all of a user's organizations.
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
from cartography.models.ontology.labels import USER_ACCOUNT


@dataclass(frozen=True)
class GitHubUserNodeProperties(CartographyNodeProperties):
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
        "is_enterprise_owner",
        set_by_analysis=True,
        description="Whether the user is an enterprise owner in any of their organizations.",
    )
    email: PropertyRef = PropertyRef(
        "email", description="Publicly visible profile email."
    )
    company: PropertyRef = PropertyRef("company", description="Public profile company.")
    organization_verified_domain_emails: PropertyRef = PropertyRef(
        "organization_verified_domain_emails",
        set_by_analysis=True,
        description="Distinct email addresses verified against the domains of any of the "
        "user's organizations.",
    )
    normalized_emails: PropertyRef = PropertyRef(
        "normalized_emails",
        set_by_analysis=True,
        description="Distinct nonempty public and organization verified-domain emails "
        "across the user's organizations, normalized with the canonical user email "
        "policy for SAML conflict checks.",
    )
    has_2fa_enabled: PropertyRef = PropertyRef(
        "has_2fa_enabled",
        set_by_analysis=True,
        description="Whether the user has two-factor authentication enabled. True when "
        "any of the user's organizations reports it, false when none does and one "
        "reports it disabled, and unset when no organization exposes it.",
    )


@dataclass(frozen=True)
class GitHubUserToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubUserOrganizationFactsRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    has_2fa_enabled: PropertyRef = PropertyRef(
        "hasTwoFactorEnabled",
        description="Whether this organization reports two-factor authentication as "
        "enabled for the user. Unset when the organization does not expose it.",
    )
    is_enterprise_owner: PropertyRef = PropertyRef(
        "isEnterpriseOwner",
        description="Whether the user is an owner of this organization's enterprise.",
    )
    organization_verified_domain_emails: PropertyRef = PropertyRef(
        "organizationVerifiedDomainEmails",
        description="Email addresses verified against this organization's domains.",
    )
    normalized_emails: PropertyRef = PropertyRef(
        "normalized_emails",
        description="Distinct nonempty public and verified-domain emails for this "
        "organization, normalized with the canonical user email policy.",
    )


@dataclass(frozen=True)
class GitHubUserMemberOfOrganizationRel(CartographyRelSchema):
    """Links a GitHub user to an organization where the user is a member."""

    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("MEMBER_OF")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: GitHubUserOrganizationFactsRelProperties = (
        GitHubUserOrganizationFactsRelProperties()
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
    properties: GitHubUserOrganizationFactsRelProperties = (
        GitHubUserOrganizationFactsRelProperties()
    )


@dataclass(frozen=True)
class GitHubOrganizationUserSchema(CartographyNodeSchema):
    """A user account in GitHub."""

    label: str = "GitHubUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [USER_ACCOUNT]
    )  # UserAccount label is used for ontology mapping
    properties: GitHubUserNodeProperties = GitHubUserNodeProperties()
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
        [USER_ACCOUNT]
    )  # UserAccount label is used for ontology mapping
    properties: GitHubUserNodeProperties = GitHubUserNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GitHubUserUnaffiliatedOrganizationRel(),
        ],
    )
    sub_resource_relationship = None
