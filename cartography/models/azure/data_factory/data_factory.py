import logging
from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AzureDataFactoryProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Full Azure resource ID of the data factory."
    )
    name: PropertyRef = PropertyRef("name", description="Name of the data factory.")
    location: PropertyRef = PropertyRef(
        "location", description="Azure region where the data factory is deployed."
    )
    provisioning_state: PropertyRef = PropertyRef(
        "provisioning_state",
        description="Current provisioning state of the data factory.",
    )
    create_time: PropertyRef = PropertyRef(
        "create_time", description="Time when the data factory was created."
    )
    version: PropertyRef = PropertyRef(
        "version", description="Service version of the data factory."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureDataFactoryToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureDataFactoryToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains this data factory resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureDataFactoryToSubscriptionRelProperties = (
        AzureDataFactoryToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureDataFactorySchema(CartographyNodeSchema):
    """An Azure Data Factory resource for orchestrating data workflows."""

    label: str = "AzureDataFactory"
    properties: AzureDataFactoryProperties = AzureDataFactoryProperties()
    sub_resource_relationship: AzureDataFactoryToSubscriptionRel = (
        AzureDataFactoryToSubscriptionRel()
    )
