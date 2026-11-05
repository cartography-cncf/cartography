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
class TencentCloudCAMPolicyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description=(
            "`<account UIN>:<policy ID>`. Preset policies share one policy ID across every "
            "account, so the ID is scoped to the account that uses the policy."
        ),
    )
    policy_id: PropertyRef = PropertyRef(
        "policy_id", extra_index=True, description="Tencent Cloud ID of the policy."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the policy."
    )
    type: PropertyRef = PropertyRef(
        "type",
        description="`custom` for customer-managed policies, `preset` for Tencent Cloud managed policies.",
    )
    description: PropertyRef = PropertyRef(
        "description", description="Description of the policy."
    )
    policy_document: PropertyRef = PropertyRef(
        "policy_document",
        description="Raw JSON policy document. Only read for custom policies.",
    )
    service_type: PropertyRef = PropertyRef(
        "service_type",
        description="Product the policy is associated with, when Tencent Cloud reports one.",
    )
    add_time: PropertyRef = PropertyRef(
        "add_time", description="Time the policy was created."
    )
    update_time: PropertyRef = PropertyRef(
        "update_time", description="Time the policy was last updated."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TencentCloudCAMPolicyToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TencentCloudAccount)-[:RESOURCE]->(:TencentCloudCAMPolicy)
class TencentCloudCAMPolicyToAccountRel(CartographyRelSchema):
    """Connects a `TencentCloudAccount` to the custom policies it defines and the preset
    policies it attaches."""

    target_node_label: str = "TencentCloudAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TencentCloudCAMPolicyToAccountRelProperties = (
        TencentCloudCAMPolicyToAccountRelProperties()
    )


@dataclass(frozen=True)
class TencentCloudCAMPolicyToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TencentCloudCAMUser)-[:POLICY]->(:TencentCloudCAMPolicy)
class TencentCloudCAMPolicyToUserRel(CartographyRelSchema):
    """Connects a CAM sub-user to each policy attached directly to it."""

    target_node_label: str = "TencentCloudCAMUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("attached_user_uins", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "POLICY"
    properties: TencentCloudCAMPolicyToUserRelProperties = (
        TencentCloudCAMPolicyToUserRelProperties()
    )


@dataclass(frozen=True)
class TencentCloudCAMPolicyToGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TencentCloudCAMGroup)-[:POLICY]->(:TencentCloudCAMPolicy)
class TencentCloudCAMPolicyToGroupRel(CartographyRelSchema):
    """Connects a CAM user group to each policy attached to it."""

    target_node_label: str = "TencentCloudCAMGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("attached_group_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "POLICY"
    properties: TencentCloudCAMPolicyToGroupRelProperties = (
        TencentCloudCAMPolicyToGroupRelProperties()
    )


@dataclass(frozen=True)
class TencentCloudCAMPolicyToRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TencentCloudCAMRole)-[:POLICY]->(:TencentCloudCAMPolicy)
class TencentCloudCAMPolicyToRoleRel(CartographyRelSchema):
    """Connects a CAM role to each policy attached to it."""

    target_node_label: str = "TencentCloudCAMRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("attached_role_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "POLICY"
    properties: TencentCloudCAMPolicyToRoleRelProperties = (
        TencentCloudCAMPolicyToRoleRelProperties()
    )


@dataclass(frozen=True)
class TencentCloudCAMPolicySchema(CartographyNodeSchema):
    """A CAM permission policy. Custom policies are always ingested; preset (Tencent Cloud
    managed) policies are ingested only when attached to a user, group, or role."""

    label: str = "TencentCloudCAMPolicy"
    properties: TencentCloudCAMPolicyNodeProperties = (
        TencentCloudCAMPolicyNodeProperties()
    )
    sub_resource_relationship: TencentCloudCAMPolicyToAccountRel = (
        TencentCloudCAMPolicyToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            TencentCloudCAMPolicyToUserRel(),
            TencentCloudCAMPolicyToGroupRel(),
            TencentCloudCAMPolicyToRoleRel(),
        ],
    )
