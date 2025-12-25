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
class AWSEventSchemasRegistryNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("RegistryArn")
    name: PropertyRef = PropertyRef("RegistryName")
    description: PropertyRef = PropertyRef("Description")
    registry_arn: PropertyRef = PropertyRef("RegistryArn")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSEventSchemasRegistryToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSEventSchemasRegistryToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSEventSchemasRegistryToAWSAccountRelProperties = (
        AWSEventSchemasRegistryToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSEventSchemasRegistrySchema(CartographyNodeSchema):
    label: str = "AWSEventSchemasRegistry"
    properties: AWSEventSchemasRegistryNodeProperties = (
        AWSEventSchemasRegistryNodeProperties()
    )
    sub_resource_relationship: AWSEventSchemasRegistryToAWSAccountRel = (
        AWSEventSchemasRegistryToAWSAccountRel()
    )
