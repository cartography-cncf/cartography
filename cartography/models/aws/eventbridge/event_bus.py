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
class AWSEventsEventBusNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Arn")
    name: PropertyRef = PropertyRef("Name")
    arn: PropertyRef = PropertyRef("Arn")
    policy: PropertyRef = PropertyRef("Policy")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSEventsEventBusToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSEventsEventBusToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSEventsEventBusToAWSAccountRelProperties = (
        AWSEventsEventBusToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSEventsEventBusSchema(CartographyNodeSchema):
    label: str = "AWSEventsEventBus"
    properties: AWSEventsEventBusNodeProperties = AWSEventsEventBusNodeProperties()
    sub_resource_relationship: AWSEventsEventBusToAWSAccountRel = (
        AWSEventsEventBusToAWSAccountRel()
    )
