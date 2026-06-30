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
class AppRunnerServiceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("ServiceArn")
    arn: PropertyRef = PropertyRef("ServiceArn", extra_index=True)
    service_id: PropertyRef = PropertyRef("ServiceId")
    service_name: PropertyRef = PropertyRef("ServiceName")
    service_url: PropertyRef = PropertyRef("ServiceUrl")
    status: PropertyRef = PropertyRef("Status")
    instance_role_arn: PropertyRef = PropertyRef("InstanceRoleArn")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AppRunnerServiceToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AppRunnerServiceToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AppRunnerServiceToAWSAccountRelProperties = (
        AppRunnerServiceToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AppRunnerServiceToAWSRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AppRunnerServiceToAWSRoleRel(CartographyRelSchema):
    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("InstanceRoleArn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_INSTANCE_ROLE"
    properties: AppRunnerServiceToAWSRoleRelProperties = (
        AppRunnerServiceToAWSRoleRelProperties()
    )


@dataclass(frozen=True)
class AppRunnerServiceSchema(CartographyNodeSchema):
    label: str = "AppRunnerService"
    properties: AppRunnerServiceNodeProperties = AppRunnerServiceNodeProperties()
    sub_resource_relationship: AppRunnerServiceToAWSAccountRel = (
        AppRunnerServiceToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [AppRunnerServiceToAWSRoleRel()],
    )

