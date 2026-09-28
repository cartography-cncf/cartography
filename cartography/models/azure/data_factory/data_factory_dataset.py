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
    id: PropertyRef = PropertyRef(
        "id", description="Full Azure resource ID of the dataset."
    )
    name: PropertyRef = PropertyRef("name", description="Name of the dataset.")
    type: PropertyRef = PropertyRef(
        "type", description="Data format or storage type represented by the dataset."
    )
    linked_service_id: PropertyRef = PropertyRef(
        "linked_service_id",
        description="Full Azure resource ID of the linked service used by the dataset.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    factory_id: PropertyRef = PropertyRef(
        "factory_id",
        description="Full Azure resource ID of the data factory that contains the dataset.",
    )
    subscription_id: PropertyRef = PropertyRef(
        "subscription_id",
        set_in_kwargs=True,
        description="Azure subscription ID that contains the dataset.",
    )


@dataclass(frozen=True)
class AzureDataFactoryDatasetToFactoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureDataFactoryDatasetToFactoryRel(CartographyRelSchema):
    """An Azure Data Factory contains this dataset."""

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
    """An Azure subscription contains this data factory dataset resource."""

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
    """A data factory dataset uses a linked service to access data."""

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
    """A named Azure Data Factory dataset that describes data for activities."""

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
