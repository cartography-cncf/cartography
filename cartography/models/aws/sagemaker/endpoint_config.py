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
class AWSSageMakerEndpointConfigNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("EndpointConfigArn")
    arn: PropertyRef = PropertyRef("EndpointConfigArn", extra_index=True)
    endpoint_config_name: PropertyRef = PropertyRef("EndpointConfigName")
    creation_time: PropertyRef = PropertyRef("CreationTime")
    model_name: PropertyRef = PropertyRef("ModelName")
    kms_key_id: PropertyRef = PropertyRef("KmsKeyId")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerEndpointConfigToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerEndpointConfigToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSSageMakerEndpointConfigToAWSAccountRelProperties = (
        AWSSageMakerEndpointConfigToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSSageMakerEndpointConfigToModelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerEndpointConfigToModelRel(CartographyRelSchema):
    target_node_label: str = "AWSSageMakerModel"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"model_name": PropertyRef("ModelName")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES"
    properties: AWSSageMakerEndpointConfigToModelRelProperties = (
        AWSSageMakerEndpointConfigToModelRelProperties()
    )


@dataclass(frozen=True)
class AWSSageMakerEndpointConfigSchema(CartographyNodeSchema):
    label: str = "AWSSageMakerEndpointConfig"
    properties: AWSSageMakerEndpointConfigNodeProperties = (
        AWSSageMakerEndpointConfigNodeProperties()
    )
    sub_resource_relationship: AWSSageMakerEndpointConfigToAWSAccountRel = (
        AWSSageMakerEndpointConfigToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSSageMakerEndpointConfigToModelRel(),
        ]
    )
