import logging
from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties, CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties, CartographyRelSchema, LinkDirection, \
    make_target_node_matcher, TargetNodeMatcher

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AzureDataFactoryLinkedServiceProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    name: PropertyRef = PropertyRef('name')
    type: PropertyRef = PropertyRef('type')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class AzureDataFactoryLinkedServiceToFactoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class AzureDataFactoryLinkedServiceToFactoryRel(CartographyRelSchema):
    target_node_label: str = 'AzureDataFactory'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('FACTORY_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = 'CONTAINS'
    properties: AzureDataFactoryLinkedServiceToFactoryRelProperties = AzureDataFactoryLinkedServiceToFactoryRelProperties()


@dataclass(frozen=True)
class AzureDataFactoryLinkedServiceSchema(CartographyNodeSchema):
    label: str = 'AzureDataFactoryLinkedService'
    properties: AzureDataFactoryLinkedServiceProperties = AzureDataFactoryLinkedServiceProperties()
    sub_resource_relationship: AzureDataFactoryLinkedServiceToFactoryRel = AzureDataFactoryLinkedServiceToFactoryRel()