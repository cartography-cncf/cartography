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
class InstanceProfileNodeProperties(CartographyNodeProperties):
    """
    Schema describing a InstanceProfile.
    """

    arn: PropertyRef = PropertyRef("Arn")
    createdate: PropertyRef = PropertyRef("CreateDate")
    id: PropertyRef = PropertyRef("Arn")
    instance_profile_id: PropertyRef = PropertyRef("InstanceProfileId")
    instance_profile_name: PropertyRef = PropertyRef("InstanceProfileName")
    path: PropertyRef = PropertyRef("Path")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class InstanceProfileToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class InstanceProfileToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: InstanceProfileToAWSAccountRelRelProperties = (
        InstanceProfileToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class InstanceProfileToAWSRoleRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class InstanceProfileToAWSRoleRel(CartographyRelSchema):
    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("Roles", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: InstanceProfileToAWSRoleRelRelProperties = (
        InstanceProfileToAWSRoleRelRelProperties()
    )


@dataclass(frozen=True)
class InstanceProfileSchema(CartographyNodeSchema):
    label: str = "AWSInstanceProfile"
    properties: InstanceProfileNodeProperties = InstanceProfileNodeProperties()
    sub_resource_relationship: InstanceProfileToAWSAccountRel = (
        InstanceProfileToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            InstanceProfileToAWSRoleRel(),
        ]
    )
