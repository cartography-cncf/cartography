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
class AWSSageMakerUserProfileNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("UserProfileArn")
    arn: PropertyRef = PropertyRef("UserProfileArn", extra_index=True)
    user_profile_name: PropertyRef = PropertyRef("UserProfileName")
    domain_id: PropertyRef = PropertyRef("DomainId")
    status: PropertyRef = PropertyRef("Status")
    creation_time: PropertyRef = PropertyRef("CreationTime")
    last_modified_time: PropertyRef = PropertyRef("LastModifiedTime")
    execution_role: PropertyRef = PropertyRef("ExecutionRole")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerUserProfileToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerUserProfileToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSSageMakerUserProfileToAWSAccountRelProperties = (
        AWSSageMakerUserProfileToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSSageMakerUserProfileToRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerUserProfileToRoleRel(CartographyRelSchema):
    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("ExecutionRole")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_EXECUTION_ROLE"
    properties: AWSSageMakerUserProfileToRoleRelProperties = (
        AWSSageMakerUserProfileToRoleRelProperties()
    )


@dataclass(frozen=True)
class AWSSageMakerUserProfileToAWSSageMakerDomainRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerUserProfileToAWSSageMakerDomainRel(CartographyRelSchema):
    target_node_label: str = "AWSSageMakerDomain"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"domain_id": PropertyRef("DomainId")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AWSSageMakerUserProfileToAWSSageMakerDomainRelProperties = (
        AWSSageMakerUserProfileToAWSSageMakerDomainRelProperties()
    )


@dataclass(frozen=True)
class AWSSageMakerUserProfileSchema(CartographyNodeSchema):
    label: str = "AWSSageMakerUserProfile"
    properties: AWSSageMakerUserProfileNodeProperties = (
        AWSSageMakerUserProfileNodeProperties()
    )
    sub_resource_relationship: AWSSageMakerUserProfileToAWSAccountRel = (
        AWSSageMakerUserProfileToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSSageMakerUserProfileToRoleRel(),
            AWSSageMakerUserProfileToAWSSageMakerDomainRel(),
        ]
    )
