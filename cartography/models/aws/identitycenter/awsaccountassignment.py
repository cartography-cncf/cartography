from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class AWSSSOAccountAssignmentProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("AssignmentId")
    account_id: PropertyRef = PropertyRef("AccountId")
    permission_set_arn: PropertyRef = PropertyRef("PermissionSetArn")
    principal_id: PropertyRef = PropertyRef("PrincipalId")
    principal_type: PropertyRef = PropertyRef("PrincipalType")
    identity_store_id: PropertyRef = PropertyRef("IdentityStoreId")
    instance_arn: PropertyRef = PropertyRef("InstanceArn")
    region: PropertyRef = PropertyRef("Region")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSSOAccountAssignmentToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSSOAccountAssignmentToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSSSOAccountAssignmentToAWSAccountRelProperties = (
        AWSSSOAccountAssignmentToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSSSOAccountAssignmentTargetsAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSSOAccountAssignmentTargetsAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AccountId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "TARGETS_ACCOUNT"
    properties: AWSSSOAccountAssignmentTargetsAWSAccountRelProperties = (
        AWSSSOAccountAssignmentTargetsAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSSSOAccountAssignmentGrantsPermissionSetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSSOAccountAssignmentGrantsPermissionSetRel(CartographyRelSchema):
    target_node_label: str = "AWSPermissionSet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("PermissionSetArn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "GRANTS_PERMISSION_SET"
    properties: AWSSSOAccountAssignmentGrantsPermissionSetRelProperties = (
        AWSSSOAccountAssignmentGrantsPermissionSetRelProperties()
    )


@dataclass(frozen=True)
class AWSSSOAccountAssignmentInIdentityCenterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSSOAccountAssignmentInIdentityCenterRel(CartographyRelSchema):
    target_node_label: str = "AWSIdentityCenter"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("InstanceArn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSIGNMENT_IN"
    properties: AWSSSOAccountAssignmentInIdentityCenterRelProperties = (
        AWSSSOAccountAssignmentInIdentityCenterRelProperties()
    )


@dataclass(frozen=True)
class AWSSSOAccountAssignmentMaterializesAsAWSRoleRelProperties(
    CartographyRelProperties,
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSSOAccountAssignmentMaterializesAsAWSRoleRel(CartographyRelSchema):
    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("RoleArn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MATERIALIZES_AS"
    properties: AWSSSOAccountAssignmentMaterializesAsAWSRoleRelProperties = (
        AWSSSOAccountAssignmentMaterializesAsAWSRoleRelProperties()
    )


@dataclass(frozen=True)
class AWSSSOAccountAssignmentSchema(CartographyNodeSchema):
    label: str = "AWSSSOAccountAssignment"
    properties: AWSSSOAccountAssignmentProperties = AWSSSOAccountAssignmentProperties()
    sub_resource_relationship: AWSSSOAccountAssignmentToAWSAccountRel = (
        AWSSSOAccountAssignmentToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSSSOAccountAssignmentTargetsAWSAccountRel(),
            AWSSSOAccountAssignmentGrantsPermissionSetRel(),
            AWSSSOAccountAssignmentInIdentityCenterRel(),
            AWSSSOAccountAssignmentMaterializesAsAWSRoleRel(),
        ],
    )


@dataclass(frozen=True)
class AWSSSOAccountAssignmentToPrincipalRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label",
        set_in_kwargs=True,
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSSOAccountAssignmentToSSOUserMatchLink(CartographyRelSchema):
    source_node_label: str = "AWSSSOAccountAssignment"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("AssignmentId")},
    )
    target_node_label: str = "AWSSSOUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("PrincipalId"),
            "identity_store_id": PropertyRef("IdentityStoreId"),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSIGNED_TO"
    properties: AWSSSOAccountAssignmentToPrincipalRelProperties = (
        AWSSSOAccountAssignmentToPrincipalRelProperties()
    )


@dataclass(frozen=True)
class AWSSSOAccountAssignmentToSSOGroupMatchLink(CartographyRelSchema):
    source_node_label: str = "AWSSSOAccountAssignment"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("AssignmentId")},
    )
    target_node_label: str = "AWSSSOGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("PrincipalId"),
            "identity_store_id": PropertyRef("IdentityStoreId"),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSIGNED_TO"
    properties: AWSSSOAccountAssignmentToPrincipalRelProperties = (
        AWSSSOAccountAssignmentToPrincipalRelProperties()
    )
