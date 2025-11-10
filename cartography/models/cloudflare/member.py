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
    status: PropertyRef = PropertyRef("status")
    email: PropertyRef = PropertyRef("user.email")
    firstname: PropertyRef = PropertyRef("user.first_name")
    user_id: PropertyRef = PropertyRef("user.id")
    lastname: PropertyRef = PropertyRef("user.last_name")
    two_factor_authentication_enabled: PropertyRef = PropertyRef(
        "user.two_factor_authentication_enabled"
    )
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudflareMemberToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CloudflareMember)<-[:RESOURCE]-(:CloudflareAccount)
class CloudflareMemberToAccountRel(CartographyRelSchema):
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
class CloudflareMemberToCloudflareRoleProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CloudflareRole)<-[:HAS_ROLE]-(:CloudflareMember)
class CloudflareMemberToCloudflareRoleRel(CartographyRelSchema):
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
    properties: CloudflareMemberToCloudflareRoleProperties = (
        CloudflareMemberToCloudflareRoleProperties()
    )


@dataclass(frozen=True)
class CloudflareMemberSchema(CartographyNodeSchema):
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
