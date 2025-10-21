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
class AzureSynapseWorkspaceProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    location: PropertyRef = PropertyRef("location")
    connectivity_endpoints: PropertyRef = PropertyRef("connectivity_endpoints")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureSynapseWorkspaceToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureSynapseWorkspaceToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureSynapseWorkspaceToSubscriptionRelProperties = (
        AzureSynapseWorkspaceToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureSynapseWorkspaceSchema(CartographyNodeSchema):
    label: str = "AzureSynapseWorkspace"
    properties: AzureSynapseWorkspaceProperties = AzureSynapseWorkspaceProperties()
    sub_resource_relationship: AzureSynapseWorkspaceToSubscriptionRel = (
        AzureSynapseWorkspaceToSubscriptionRel()
    )
