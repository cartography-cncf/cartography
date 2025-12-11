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
class SSOUserProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("UserId")
    user_name: PropertyRef = PropertyRef("UserName")
    identity_store_id: PropertyRef = PropertyRef("IdentityStoreId")
    external_id: PropertyRef = PropertyRef("ExternalId", extra_index=True)
    region: PropertyRef = PropertyRef("Region")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SSOUserToOktaUserRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SSOUserToOktaUserRel(CartographyRelSchema):
    target_node_label: str = "UserAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ExternalId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CAN_ASSUME_IDENTITY"
    properties: SSOUserToOktaUserRelRelProperties = SSOUserToOktaUserRelRelProperties()


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
    """
    Represents that a user has been assigned this permission set in at least one AWS account.

    Semantics:
        This is a SUMMARY relationship indicating the user has some assignment involving this
        permission set. It does NOT indicate which specific accounts the user can access.

    To determine account-specific access:
        Follow the authoritative path through roles:
        (AWSSSOUser)-[:ALLOWED_BY]-(AWSRole)-[:RESOURCE]->(AWSAccount)

        The role's [:ASSIGNED_TO_ROLE] relationship links back to the permission set,
        providing the complete (User, PermissionSet, Account) context.

    Query examples:
        - "What permission sets does this user have?" → Use this HAS_PERMISSION_SET relationship
        - "Which accounts can this user access?" → Use the ALLOWED_BY → Role → Account path
    """

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
    properties: SSOUserProperties = SSOUserProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["UserAccount"]
    )  # UserAccount label is used for ontology mapping
    sub_resource_relationship: AWSSSOUserToAWSAccountRel = AWSSSOUserToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SSOUserToOktaUserRel(),
            AWSSSOUserToSSOGroupRel(),
            AWSSSOUserToPermissionSetRel(),
        ],
    )
