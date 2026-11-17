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
class EventBridgeEventBusNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Arn", description="The ARN of the event bus")
    arn: PropertyRef = PropertyRef(
        "Arn",
        extra_index=True,
        description="The Amazon Resource Name (ARN) of the event bus",
    )
    name: PropertyRef = PropertyRef("Name", description="The name of the event bus")
    policy: PropertyRef = PropertyRef(
        "Policy",
        description="The resource policy of the event bus, if one is set",
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The region of the event bus"
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EventBridgeEventBusToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EventBridgeEventBusToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EventBridgeEventBusToAwsAccountRelProperties = (
        EventBridgeEventBusToAwsAccountRelProperties()
    )


@dataclass(frozen=True)
class EventBridgeEventBusSchema(CartographyNodeSchema):
    """Representation of an AWS [EventBridge event bus](https://docs.aws.amazon.com/eventbridge/latest/APIReference/API_EventBus.html)"""

    label: str = "AWSEventBridgeEventBus"
    properties: EventBridgeEventBusNodeProperties = EventBridgeEventBusNodeProperties()
    sub_resource_relationship: EventBridgeEventBusToAWSAccountRel = (
        EventBridgeEventBusToAWSAccountRel()
    )
