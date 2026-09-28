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
class AzureDataFactoryLinkedServiceProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Full Azure resource ID of the linked service."
    )
    name: PropertyRef = PropertyRef("name", description="Name of the linked service.")
    type: PropertyRef = PropertyRef(
        "type",
        description="Type of data store, compute service, or connection represented.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    factory_id: PropertyRef = PropertyRef(
        "factory_id",
        description="Full Azure resource ID of the data factory that contains the linked service.",
    )
    subscription_id: PropertyRef = PropertyRef(
        "subscription_id",
        set_in_kwargs=True,
        description="Azure subscription ID that contains the linked service.",
    )


@dataclass(frozen=True)
class AzureDataFactoryLinkedServiceToFactoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureDataFactoryLinkedServiceToFactoryRel(CartographyRelSchema):
    """An Azure Data Factory contains this linked service."""

    target_node_label: str = "AzureDataFactory"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("factory_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureDataFactoryLinkedServiceToFactoryRelProperties = (
        AzureDataFactoryLinkedServiceToFactoryRelProperties()
    )


@dataclass(frozen=True)
class AzureDataFactoryLinkedServiceToSubscriptionRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureDataFactoryLinkedServiceToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains this data factory linked service resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("subscription_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureDataFactoryLinkedServiceToSubscriptionRelProperties = (
        AzureDataFactoryLinkedServiceToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureDataFactoryLinkedServiceSchema(CartographyNodeSchema):
    """An Azure Data Factory connection to a data store or compute service."""

    label: str = "AzureDataFactoryLinkedService"
    properties: AzureDataFactoryLinkedServiceProperties = (
        AzureDataFactoryLinkedServiceProperties()
    )
    sub_resource_relationship: AzureDataFactoryLinkedServiceToSubscriptionRel = (
        AzureDataFactoryLinkedServiceToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureDataFactoryLinkedServiceToFactoryRel(),
        ],
    )
