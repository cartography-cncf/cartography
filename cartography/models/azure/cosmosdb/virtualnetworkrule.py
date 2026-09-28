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
class AzureCosmosDBVirtualNetworkRuleProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Azure resource ID of the allowed virtual network subnet.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    ignoremissingvnetserviceendpoint: PropertyRef = PropertyRef(
        "ignore_missing_v_net_service_endpoint",
        description="Whether the rule may reference a subnet without a service endpoint.",
    )


@dataclass(frozen=True)
class AzureCosmosDBVirtualNetworkRuleToCosmosDBAccountRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureCosmosDBAccount)-[:CONFIGURED_WITH]->(:AzureCosmosDBVirtualNetworkRule)
class AzureCosmosDBVirtualNetworkRuleToCosmosDBAccountRel(CartographyRelSchema):
    """A Cosmos DB account is configured with the virtual network rule."""

    target_node_label: str = "AzureCosmosDBAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("DatabaseAccountId", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONFIGURED_WITH"
    properties: AzureCosmosDBVirtualNetworkRuleToCosmosDBAccountRelProperties = (
        AzureCosmosDBVirtualNetworkRuleToCosmosDBAccountRelProperties()
    )


@dataclass(frozen=True)
class AzureCosmosDBVirtualNetworkRuleToSubscriptionRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureCosmosDBVirtualNetworkRule)
class AzureCosmosDBVirtualNetworkRuleToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the virtual network rule as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureCosmosDBVirtualNetworkRuleToSubscriptionRelProperties = (
        AzureCosmosDBVirtualNetworkRuleToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureCosmosDBVirtualNetworkRuleSchema(CartographyNodeSchema):
    """A subnet access rule configured for an Azure Cosmos DB account."""

    label: str = "AzureCosmosDBVirtualNetworkRule"
    properties: AzureCosmosDBVirtualNetworkRuleProperties = (
        AzureCosmosDBVirtualNetworkRuleProperties()
    )
    sub_resource_relationship: AzureCosmosDBVirtualNetworkRuleToSubscriptionRel = (
        AzureCosmosDBVirtualNetworkRuleToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureCosmosDBVirtualNetworkRuleToCosmosDBAccountRel(),
        ]
    )
