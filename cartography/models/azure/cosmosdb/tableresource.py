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
class AzureCosmosDBTableResourceProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Azure resource ID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", description="Name of the Azure resource.")
    type: PropertyRef = PropertyRef("type", description="Azure resource type.")
    location: PropertyRef = PropertyRef(
        "location",
        description="Azure region where the resource is located.",
    )
    throughput: PropertyRef = PropertyRef(
        "options.throughput",
        description="Manually provisioned throughput in request units per second.",
    )
    maxthroughput: PropertyRef = PropertyRef(
        "options.autoscale_setting.max_throughput",
        description="Maximum autoscale throughput in request units per second.",
    )


@dataclass(frozen=True)
class AzureCosmosDBTableResourceToCosmosDBAccountRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureCosmosDBAccount)-[:CONTAINS]->(:AzureCosmosDBTableResource)
class AzureCosmosDBTableResourceToCosmosDBAccountRel(CartographyRelSchema):
    """A Cosmos DB account contains the Table API table."""

    target_node_label: str = "AzureCosmosDBAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("database_account_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureCosmosDBTableResourceToCosmosDBAccountRelProperties = (
        AzureCosmosDBTableResourceToCosmosDBAccountRelProperties()
    )


@dataclass(frozen=True)
class AzureCosmosDBTableResourceToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureCosmosDBTableResource)
class AzureCosmosDBTableResourceToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the Table API table as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureCosmosDBTableResourceToSubscriptionRelProperties = (
        AzureCosmosDBTableResourceToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureCosmosDBTableResourceSchema(CartographyNodeSchema):
    """A table hosted by an Azure Cosmos DB for Table account."""

    label: str = "AzureCosmosDBTableResource"
    properties: AzureCosmosDBTableResourceProperties = (
        AzureCosmosDBTableResourceProperties()
    )
    sub_resource_relationship: AzureCosmosDBTableResourceToSubscriptionRel = (
        AzureCosmosDBTableResourceToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureCosmosDBTableResourceToCosmosDBAccountRel(),
        ]
    )
