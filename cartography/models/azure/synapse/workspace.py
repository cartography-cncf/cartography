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
    id: PropertyRef = PropertyRef(
        "id", description="Full Azure resource ID of the Synapse workspace."
    )
    name: PropertyRef = PropertyRef(
        "name", description="Name of the Synapse workspace."
    )
    location: PropertyRef = PropertyRef(
        "location", description="Azure region where the workspace is deployed."
    )
    connectivity_endpoints: PropertyRef = PropertyRef(
        "connectivity_endpoints",
        description="Workspace service endpoints for web, SQL, and development access.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureSynapseWorkspaceToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureSynapseWorkspaceToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains this Synapse workspace resource."""

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
    """An Azure Synapse workspace that groups analytics data and services."""

    label: str = "AzureSynapseWorkspace"
    properties: AzureSynapseWorkspaceProperties = AzureSynapseWorkspaceProperties()
    sub_resource_relationship: AzureSynapseWorkspaceToSubscriptionRel = (
        AzureSynapseWorkspaceToSubscriptionRel()
    )
