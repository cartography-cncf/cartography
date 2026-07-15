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
class CloudflareMemberNodeProperties(CartographyNodeProperties):
    status: PropertyRef = PropertyRef(
        "status",
        description="Membership status in the account.",
    )
    email: PropertyRef = PropertyRef(
        "user.email",
        description="Related user's email address.",
    )
    firstname: PropertyRef = PropertyRef(
        "user.first_name",
        description="Related user's first name.",
    )
    user_id: PropertyRef = PropertyRef(
        "user.id",
        description="Related user's ID.",
    )
    lastname: PropertyRef = PropertyRef(
        "user.last_name",
        description="Related user's last name.",
    )
    two_factor_authentication_enabled: PropertyRef = PropertyRef(
        "user.two_factor_authentication_enabled",
        description="Whether the related user enabled two-factor authentication.",
    )
    id: PropertyRef = PropertyRef("id", description="Membership ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )


@dataclass(frozen=True)
class CloudflareMemberToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CloudflareMember)<-[:RESOURCE]-(:CloudflareAccount)
class CloudflareMemberToAccountRel(CartographyRelSchema):
    """The account contains the member."""

    target_node_label: str = "CloudflareAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("account_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CloudflareMemberToAccountRelProperties = (
        CloudflareMemberToAccountRelProperties()
    )


@dataclass(frozen=True)
class CloudflareMemberToCloudflareRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CloudflareRole)<-[:HAS_ROLE]-(:CloudflareMember)
class CloudflareMemberToCloudflareRoleRel(CartographyRelSchema):
    """The member has the assigned role."""

    target_node_label: str = "CloudflareRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "roles_ids",
                one_to_many=True,
            )
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ROLE"
    properties: CloudflareMemberToCloudflareRoleRelProperties = (
        CloudflareMemberToCloudflareRoleRelProperties()
    )


@dataclass(frozen=True)
class CloudflareMemberSchema(CartographyNodeSchema):
    """A user membership in a Cloudflare account."""

    label: str = "CloudflareMember"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["UserAccount"]
    )  # UserAccount label is used for ontology mapping
    properties: CloudflareMemberNodeProperties = CloudflareMemberNodeProperties()
    sub_resource_relationship: CloudflareMemberToAccountRel = (
        CloudflareMemberToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            CloudflareMemberToCloudflareRoleRel(),
        ],
    )
