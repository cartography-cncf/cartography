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
    id: PropertyRef = PropertyRef(
        "EndpointConfigArn", description="The ARN of the Endpoint Config"
    )
    arn: PropertyRef = PropertyRef(
        "EndpointConfigArn",
        extra_index=True,
        description="The ARN of the Endpoint Config",
    )
    endpoint_config_name: PropertyRef = PropertyRef(
        "EndpointConfigName", description="The name of the Endpoint Config"
    )
    creation_time: PropertyRef = PropertyRef(
        "CreationTime", description="When the Endpoint Config was created"
    )
    model_name: PropertyRef = PropertyRef(
        "ModelName", description="The name of the model to deploy"
    )
    kms_key_id: PropertyRef = PropertyRef(
        "KmsKeyId",
        description="Identifier of the KMS key linked to this `AWSSageMakerEndpointConfig` node.",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The AWS region where the Endpoint Config exists",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class AWSSageMakerEndpointConfigToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerEndpointConfigToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSSageMakerEndpointConfig`."

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
    "Represents a `USES` relationship from `AWSSageMakerEndpointConfig` to `AWSSageMakerModel`."

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
    "Represents an `AWSSageMakerEndpointConfig` node in the AWS graph."

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
