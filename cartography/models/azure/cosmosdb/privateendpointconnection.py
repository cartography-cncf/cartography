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


@dataclass(frozen=True)
class AzureCDBPrivateEndpointConnectionProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Azure resource ID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name",
        description="Name of the Azure resource.",
    )
    privateendpointid: PropertyRef = PropertyRef(
        "private_endpoint.id",
        description="Azure resource ID of the private endpoint.",
    )
    status: PropertyRef = PropertyRef(
        "private_link_service_connection_state.status",
        description="Approval status of the private endpoint connection.",
    )
    actionrequired: PropertyRef = PropertyRef(
        "private_link_service_connection_state.actions_required",
        description="Actions required to complete the private endpoint connection.",
    )


@dataclass(frozen=True)
class AzureCDBPrivateEndpointConnectionToCosmosDBAccountRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureCosmosDBAccount)-[:CONFIGURED_WITH]->(:AzureCDBPrivateEndpointConnection)
class AzureCDBPrivateEndpointConnectionToCosmosDBAccountRel(CartographyRelSchema):
    """A Cosmos DB account is configured with the private endpoint connection."""

    target_node_label: str = "AzureCosmosDBAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("DatabaseAccountId", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONFIGURED_WITH"
    properties: AzureCDBPrivateEndpointConnectionToCosmosDBAccountRelProperties = (
        AzureCDBPrivateEndpointConnectionToCosmosDBAccountRelProperties()
    )


@dataclass(frozen=True)
class AzureCDBPrivateEndpointConnectionToSubscriptionRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureCDBPrivateEndpointConnection)
class AzureCDBPrivateEndpointConnectionToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the private endpoint connection as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureCDBPrivateEndpointConnectionToSubscriptionRelProperties = (
        AzureCDBPrivateEndpointConnectionToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureCDBPrivateEndpointConnectionSchema(CartographyNodeSchema):
    """A private endpoint connection configured for an Azure Cosmos DB account."""

    label: str = "AzureCDBPrivateEndpointConnection"
    properties: AzureCDBPrivateEndpointConnectionProperties = (
        AzureCDBPrivateEndpointConnectionProperties()
    )
    sub_resource_relationship: AzureCDBPrivateEndpointConnectionToSubscriptionRel = (
        AzureCDBPrivateEndpointConnectionToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureCDBPrivateEndpointConnectionToCosmosDBAccountRel(),
        ]
    )
