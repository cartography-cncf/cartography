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
class AzureCosmosDBMongoDBCollectionProperties(CartographyNodeProperties):
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
    collectionname: PropertyRef = PropertyRef(
        "resource.id",
        description="Name of the MongoDB collection.",
    )
    analyticalttl: PropertyRef = PropertyRef(
        "resource.analytical_storage_ttl",
        description="Analytical store time to live in seconds.",
    )


@dataclass(frozen=True)
class AzureCosmosDBMongoDBCollectionToCosmosDBMongoDBDatabaseRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureCosmosDBMongoDBDatabase)-[:CONTAINS]->(:AzureCosmosDBMongoDBCollection)
class AzureCosmosDBMongoDBCollectionToCosmosDBMongoDBDatabaseRel(CartographyRelSchema):
    """A MongoDB database contains the collection."""

    target_node_label: str = "AzureCosmosDBMongoDBDatabase"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("database_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureCosmosDBMongoDBCollectionToCosmosDBMongoDBDatabaseRelProperties = (
        AzureCosmosDBMongoDBCollectionToCosmosDBMongoDBDatabaseRelProperties()
    )


@dataclass(frozen=True)
class AzureCosmosDBMongoDBCollectionToSubscriptionRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureCosmosDBMongoDBCollection)
class AzureCosmosDBMongoDBCollectionToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the MongoDB collection as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureCosmosDBMongoDBCollectionToSubscriptionRelProperties = (
        AzureCosmosDBMongoDBCollectionToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureCosmosDBMongoDBCollectionSchema(CartographyNodeSchema):
    """A MongoDB collection in an Azure Cosmos DB database."""

    label: str = "AzureCosmosDBMongoDBCollection"
    properties: AzureCosmosDBMongoDBCollectionProperties = (
        AzureCosmosDBMongoDBCollectionProperties()
    )
    sub_resource_relationship: AzureCosmosDBMongoDBCollectionToSubscriptionRel = (
        AzureCosmosDBMongoDBCollectionToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureCosmosDBMongoDBCollectionToCosmosDBMongoDBDatabaseRel(),
        ]
    )
