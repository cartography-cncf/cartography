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
class PermissionSetProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("PermissionSetArn")
    name: PropertyRef = PropertyRef("Name")
    arn: PropertyRef = PropertyRef("PermissionSetArn")
    description: PropertyRef = PropertyRef("Description")
    session_duration: PropertyRef = PropertyRef("SessionDuration")
    instance_arn: PropertyRef = PropertyRef("InstanceArn", set_in_kwargs=True)
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
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
class RoleAssignmentAllowedByRelProperties(CartographyRelProperties):
    """
    Properties for the ALLOWED_BY relationship between AWSRole and AWSSSO principals.
    """

    # Mandatory fields for MatchLinks
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)

    # Role assignment specific properties
    permission_set_arn: PropertyRef = PropertyRef("PermissionSetArn")


@dataclass(frozen=True)
class AWSRoleToSSOUserMatchLink(CartographyRelSchema):
    """
    MatchLink for (AWSRole)-[:ALLOWED_BY]->(AWSSSOUser).

    See schema documentation for details.
    """

    # MatchLink-specific fields for AWSRole as source
    source_node_label: str = "AWSRole"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"arn": PropertyRef("RoleArn")},
    )

    # Standard CartographyRelSchema fields for AWSSSOUser as target
    target_node_label: str = "AWSSSOUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("UserId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ALLOWED_BY"
    properties: RoleAssignmentAllowedByRelProperties = (
        RoleAssignmentAllowedByRelProperties()
    )


@dataclass(frozen=True)
class AWSRoleToSSOGroupMatchLink(CartographyRelSchema):
    """
    MatchLink for (AWSRole)-[:ALLOWED_BY]->(AWSSSOGroup).

    See schema documentation for details.
    """

    source_node_label: str = "AWSRole"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"arn": PropertyRef("RoleArn")},
    )

    target_node_label: str = "AWSSSOGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("GroupId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ALLOWED_BY"
    properties: RoleAssignmentAllowedByRelProperties = (
        RoleAssignmentAllowedByRelProperties()
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
