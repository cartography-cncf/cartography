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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    privateendpointid: PropertyRef = PropertyRef("private_endpoint.id")
    status: PropertyRef = PropertyRef("private_link_service_connection_state.status")
    actionrequired: PropertyRef = PropertyRef(
        "private_link_service_connection_state.actions_required"
    )


@dataclass(frozen=True)
class AzureCDBPrivateEndpointConnectionToCosmosDBAccountProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureCosmosDBAccount)-[:CONFIGURED_WITH]->(:AzureCDBPrivateEndpointConnection)
class AzureCDBPrivateEndpointConnectionToCosmosDBAccountRel(CartographyRelSchema):
    target_node_label: str = "AzureCosmosDBAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("DatabaseAccountId", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONFIGURED_WITH"
    properties: AzureCDBPrivateEndpointConnectionToCosmosDBAccountProperties = (
        AzureCDBPrivateEndpointConnectionToCosmosDBAccountProperties()
    )


@dataclass(frozen=True)
class AzureCDBPrivateEndpointConnectionToSubscriptionRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureCDBPrivateEndpointConnection)
class AzureCDBPrivateEndpointConnectionToSubscriptionRel(CartographyRelSchema):
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
