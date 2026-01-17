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
class AWSSageMakerEndpointNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("EndpointArn")
    arn: PropertyRef = PropertyRef("EndpointArn", extra_index=True)
    endpoint_name: PropertyRef = PropertyRef("EndpointName")
    endpoint_config_name: PropertyRef = PropertyRef("EndpointConfigName")
    endpoint_status: PropertyRef = PropertyRef("EndpointStatus")
    creation_time: PropertyRef = PropertyRef("CreationTime")
    last_modified_time: PropertyRef = PropertyRef("LastModifiedTime")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerEndpointToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerEndpointToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSSageMakerEndpointToAWSAccountRelProperties = (
        AWSSageMakerEndpointToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSSageMakerEndpointToEndpointConfigRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerEndpointToEndpointConfigRel(CartographyRelSchema):
    target_node_label: str = "AWSSageMakerEndpointConfig"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"endpoint_config_name": PropertyRef("EndpointConfigName")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES"
    properties: AWSSageMakerEndpointToEndpointConfigRelProperties = (
        AWSSageMakerEndpointToEndpointConfigRelProperties()
    )


@dataclass(frozen=True)
class AWSSageMakerEndpointSchema(CartographyNodeSchema):
    label: str = "AWSSageMakerEndpoint"
    properties: AWSSageMakerEndpointNodeProperties = (
        AWSSageMakerEndpointNodeProperties()
    )
    sub_resource_relationship: AWSSageMakerEndpointToAWSAccountRel = (
        AWSSageMakerEndpointToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSSageMakerEndpointToEndpointConfigRel(),
        ]
    )
