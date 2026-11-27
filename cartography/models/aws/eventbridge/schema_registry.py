from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class EventSchemasRegistryNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "RegistryArn",
        description="The ARN of the schema registry",
    )
    arn: PropertyRef = PropertyRef(
        "RegistryArn",
        extra_index=True,
        description="The Amazon Resource Name (ARN) of the schema registry",
    )
    name: PropertyRef = PropertyRef(
        "RegistryName",
        description="The name of the schema registry",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The AWS region of the schema registry",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EventSchemasRegistryToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EventSchemasRegistryToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EventSchemasRegistryToAWSAccountRelProperties = (
        EventSchemasRegistryToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class EventSchemasRegistrySchema(CartographyNodeSchema):
    """Representation of an AWS [EventBridge schema registry](https://docs.aws.amazon.com/eventbridge/latest/schema-reference/v1-registries-name-registryname.html)."""

    label: str = "AWSEventSchemasRegistry"
    properties: EventSchemasRegistryNodeProperties = (
        EventSchemasRegistryNodeProperties()
    )
    sub_resource_relationship: EventSchemasRegistryToAWSAccountRel = (
        EventSchemasRegistryToAWSAccountRel()
    )
