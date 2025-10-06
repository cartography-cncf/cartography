import logging
from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties, CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties, CartographyRelSchema, LinkDirection, \
    make_target_node_matcher, TargetNodeMatcher

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AzureDataFactoryProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    name: PropertyRef = PropertyRef('name')
    location: PropertyRef = PropertyRef('location')
    provisioning_state: PropertyRef = PropertyRef('provisioning_state')
    create_time: PropertyRef = PropertyRef('create_time')
    version: PropertyRef = PropertyRef('version')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class AzureDataFactoryToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class AzureDataFactoryToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = 'AzureSubscription'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AZURE_SUBSCRIPTION_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = 'RESOURCE'
    properties: AzureDataFactoryToSubscriptionRelProperties = AzureDataFactoryToSubscriptionRelProperties()


@dataclass(frozen=True)
class AzureDataFactorySchema(CartographyNodeSchema):
    label: str = 'AzureDataFactory'
    properties: AzureDataFactoryProperties = AzureDataFactoryProperties()
    sub_resource_relationship: AzureDataFactoryToSubscriptionRel = AzureDataFactoryToSubscriptionRel()