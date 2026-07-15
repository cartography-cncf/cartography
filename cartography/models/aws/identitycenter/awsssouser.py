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
    id: PropertyRef = PropertyRef(
        "UserId", description="Unique identifier for the SSO user"
    )
    user_name: PropertyRef = PropertyRef(
        "UserName", description="The username of the SSO user"
    )
    identity_store_id: PropertyRef = PropertyRef(
        "IdentityStoreId", description="The identity store ID of the SSO user"
    )
    external_id: PropertyRef = PropertyRef(
        "ExternalId", extra_index=True, description="The external ID of the SSO user"
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The AWS region"
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class AWSSSOUserToOktaUserRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSSOUserToOktaUserRel(CartographyRelSchema):
    "Represents a `CAN_ASSUME_IDENTITY` relationship from `UserAccount` to `AWSSSOUser`."

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
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSSSOUser`."

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
# DEPRECATED: replaced by the canonical (:UserAccount)-[:MEMBER_OF]->(:UserGroup)
# edge (AWSSSOUserToSSOGroupMemberOfRel). Kept for backward compatibility, will
# be removed in v1.0.0.
class AWSSSOUserToSSOGroupRel(CartographyRelSchema):
    "Represents a `MEMBER_OF_SSO_GROUP` relationship from `AWSSSOUser` to `AWSSSOGroup`."

    target_node_label: str = "AWSSSOGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("MemberOfGroups", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_SSO_GROUP"
    properties: AWSSSOUserToSSOGroupRelProperties = AWSSSOUserToSSOGroupRelProperties()


@dataclass(frozen=True)
class AWSSSOUserToSSOGroupMemberOfRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# Canonical ontology edge: (:UserAccount)-[:MEMBER_OF]->(:UserGroup)
class AWSSSOUserToSSOGroupMemberOfRel(CartographyRelSchema):
    "Represents a `MEMBER_OF` relationship from `AWSSSOUser` to `AWSSSOGroup`."

    target_node_label: str = "AWSSSOGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("MemberOfGroups", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: AWSSSOUserToSSOGroupMemberOfRelProperties = (
        AWSSSOUserToSSOGroupMemberOfRelProperties()
    )


@dataclass(frozen=True)
class AWSSSOUserToPermissionSetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# DEPRECATED: replaced by the canonical (:UserAccount)-[:HAS_ROLE]->(:PermissionRole)
# edge (AWSSSOUserToPermissionSetHasRoleRel). Kept for backward compatibility,
# will be removed in v1.0.0.
class AWSSSOUserToPermissionSetRel(CartographyRelSchema):
    "Represents a `HAS_PERMISSION_SET` relationship from `AWSSSOUser` to `AWSPermissionSet`."

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
class AWSSSOUserToPermissionSetHasRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# Canonical ontology edge: (:UserAccount)-[:HAS_ROLE]->(:PermissionRole)
class AWSSSOUserToPermissionSetHasRoleRel(CartographyRelSchema):
    "Represents a `HAS_ROLE` relationship from `AWSSSOUser` to `AWSPermissionSet`."

    target_node_label: str = "AWSPermissionSet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("AssignedPermissionSets", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ROLE"
    properties: AWSSSOUserToPermissionSetHasRoleRelProperties = (
        AWSSSOUserToPermissionSetHasRoleRelProperties()
    )


@dataclass(frozen=True)
class AWSSSOUserSchema(CartographyNodeSchema):
    "Represents an `AWSSSOUser` node in the AWS graph."

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
            AWSSSOUserToSSOGroupMemberOfRel(),
            AWSSSOUserToPermissionSetRel(),
            AWSSSOUserToPermissionSetHasRoleRel(),
        ],
    )
