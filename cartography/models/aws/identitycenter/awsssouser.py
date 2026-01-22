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
class AWSSSOUserProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("UserId")
    user_name: PropertyRef = PropertyRef("UserName")
    identity_store_id: PropertyRef = PropertyRef("IdentityStoreId")
    external_id: PropertyRef = PropertyRef("ExternalId", extra_index=True)
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSSOUserToOktaUserRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSSOUserToOktaUserRel(CartographyRelSchema):
    target_node_label: str = "UserAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ExternalId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CAN_ASSUME_IDENTITY"
    properties: AWSSSOUserToOktaUserRelRelProperties = (
        AWSSSOUserToOktaUserRelRelProperties()
    )


@dataclass(frozen=True)
class AWSSSOUserToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:IdentityCenter)<-[:RESOURCE]-(:AWSAccount)
class AWSSSOUserToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSSSOUserToAWSAccountRelRelProperties = (
        AWSSSOUserToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class AWSSSOUserToSSOGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSSOUserToSSOGroupRel(CartographyRelSchema):
    target_node_label: str = "AWSSSOGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("MemberOfGroups", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_SSO_GROUP"
    properties: AWSSSOUserToSSOGroupRelProperties = AWSSSOUserToSSOGroupRelProperties()


@dataclass(frozen=True)
class AWSSSOUserToPermissionSetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSSOUserToPermissionSetRel(CartographyRelSchema):
    target_node_label: str = "AWSPermissionSet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("AssignedPermissionSets", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_PERMISSION_SET"
    properties: AWSSSOUserToPermissionSetRelProperties = (
        AWSSSOUserToPermissionSetRelProperties()
    )


@dataclass(frozen=True)
class AWSSSOUserSchema(CartographyNodeSchema):
    label: str = "AWSSSOUser"
    properties: AWSSSOUserProperties = AWSSSOUserProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["UserAccount"]
    )  # UserAccount label is used for ontology mapping
    sub_resource_relationship: AWSSSOUserToAWSAccountRel = AWSSSOUserToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSSSOUserToOktaUserRel(),
            AWSSSOUserToSSOGroupRel(),
            AWSSSOUserToPermissionSetRel(),
        ],
    )
