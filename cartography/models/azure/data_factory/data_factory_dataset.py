import logging
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

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AzureDataFactoryDatasetProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    type: PropertyRef = PropertyRef("type")
    linked_service_id: PropertyRef = PropertyRef("linked_service_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    factory_id: PropertyRef = PropertyRef("factory_id")
    subscription_id: PropertyRef = PropertyRef("subscription_id", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureDataFactoryDatasetToFactoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureDataFactoryDatasetToFactoryRel(CartographyRelSchema):
    target_node_label: str = "AzureDataFactory"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("factory_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureDataFactoryDatasetToFactoryRelProperties = (
        AzureDataFactoryDatasetToFactoryRelProperties()
    )


@dataclass(frozen=True)
class AzureDataFactoryDatasetToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureDataFactoryDatasetToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("subscription_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureDataFactoryDatasetToSubscriptionRelProperties = (
        AzureDataFactoryDatasetToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class DatasetUsesLinkedServiceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatasetUsesLinkedServiceRel(CartographyRelSchema):
    target_node_label: str = "AzureDataFactoryLinkedService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("linked_service_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_LINKED_SERVICE"
    properties: DatasetUsesLinkedServiceRelProperties = (
        DatasetUsesLinkedServiceRelProperties()
    )


@dataclass(frozen=True)
class AzureDataFactoryDatasetSchema(CartographyNodeSchema):
    label: str = "AzureDataFactoryDataset"
    properties: AzureDataFactoryDatasetProperties = AzureDataFactoryDatasetProperties()
    sub_resource_relationship: AzureDataFactoryDatasetToSubscriptionRel = (
        AzureDataFactoryDatasetToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureDataFactoryDatasetToFactoryRel(),
            DatasetUsesLinkedServiceRel(),
        ],
    )
