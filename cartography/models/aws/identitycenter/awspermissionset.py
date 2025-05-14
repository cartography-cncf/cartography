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
class PermissionSetProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("PermissionSetArn")
    name: PropertyRef = PropertyRef("Name")
    arn: PropertyRef = PropertyRef("PermissionSetArn")
    description: PropertyRef = PropertyRef("Description")
    session_duration: PropertyRef = PropertyRef("SessionDuration")
    instance_arn: PropertyRef = PropertyRef("InstanceArn", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class PermissionSetToInstanceRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class PermissionSetToInstanceRel(CartographyRelSchema):
    target_node_label: str = "AWSIdentityCenter"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("InstanceArn", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_PERMISSION_SET"
    properties: PermissionSetToInstanceRelRelProperties = (
        PermissionSetToInstanceRelRelProperties()
    )


@dataclass(frozen=True)
class PermissionSetToAWSRoleRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class PermissionSetToAWSRoleRel(CartographyRelSchema):
    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("RoleHint", fuzzy_and_ignore_case=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSIGNED_TO_ROLE"
    properties: PermissionSetToAWSRoleRelRelProperties = (
        PermissionSetToAWSRoleRelRelProperties()
    )


@dataclass(frozen=True)
class AWSPermissionSetToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:IdentityCenter)<-[:RESOURCE]-(:AWSAccount)
class AWSPermissionSetToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSPermissionSetToAWSAccountRelRelProperties = (
        AWSPermissionSetToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class AWSPermissionSetSchema(CartographyNodeSchema):
    label: str = "AWSPermissionSet"
    properties: PermissionSetProperties = PermissionSetProperties()
    sub_resource_relationship: AWSPermissionSetToAWSAccountRel = (
        AWSPermissionSetToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            PermissionSetToInstanceRel(),
            PermissionSetToAWSRoleRel(),
        ],
    )
