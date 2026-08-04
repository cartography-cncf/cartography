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
    id: PropertyRef = PropertyRef(
        "id", description="Full Azure resource ID of the workflow."
    )
    name: PropertyRef = PropertyRef("name", description="Name of the workflow.")
    location: PropertyRef = PropertyRef(
        "location", description="Azure region where the workflow is deployed."
    )
    state: PropertyRef = PropertyRef(
        "state", description="Current enabled or disabled state of the workflow."
    )
    created_time: PropertyRef = PropertyRef(
        "createdTime", description="Timestamp when the workflow was created."
    )
    changed_time: PropertyRef = PropertyRef(
        "changedTime", description="Timestamp when the workflow was last changed."
    )
    version: PropertyRef = PropertyRef(
        "version", description="Version identifier of the workflow."
    )
    access_endpoint: PropertyRef = PropertyRef(
        "accessEndpoint", description="Access endpoint for the workflow."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# --- Relationship Definitions ---
@dataclass(frozen=True)
class AzureLogicAppToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureLogicAppToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the Logic App workflow as a resource."""

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
    """A workflow managed by Azure Logic Apps."""

    label: str = "AzureLogicApp"
    properties: AzureLogicAppProperties = AzureLogicAppProperties()
    sub_resource_relationship: AzureLogicAppToSubscriptionRel = (
        AzureLogicAppToSubscriptionRel()
    )
