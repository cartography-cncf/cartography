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


# --- Node Definitions ---
@dataclass(frozen=True)
class AzureLogicAppProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    location: PropertyRef = PropertyRef("location")
    state: PropertyRef = PropertyRef("state")
    created_time: PropertyRef = PropertyRef("createdTime")
    changed_time: PropertyRef = PropertyRef("changedTime")
    version: PropertyRef = PropertyRef("version")
    access_endpoint: PropertyRef = PropertyRef("accessEndpoint")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# --- Relationship Definitions ---
@dataclass(frozen=True)
class AzureLogicAppToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureLogicAppToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureLogicAppToSubscriptionRelProperties = (
        AzureLogicAppToSubscriptionRelProperties()
    )


# --- Main Schema ---
@dataclass(frozen=True)
class AzureLogicAppSchema(CartographyNodeSchema):
    label: str = "AzureLogicApp"
    properties: AzureLogicAppProperties = AzureLogicAppProperties()
    sub_resource_relationship: AzureLogicAppToSubscriptionRel = (
        AzureLogicAppToSubscriptionRel()
    )
