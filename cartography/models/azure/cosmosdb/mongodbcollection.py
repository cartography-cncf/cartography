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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    type: PropertyRef = PropertyRef("type")
    location: PropertyRef = PropertyRef("location")
    throughput: PropertyRef = PropertyRef("options.throughput")
    maxthroughput: PropertyRef = PropertyRef("options.autoscale_setting.max_throughput")
    collectionname: PropertyRef = PropertyRef("resource.id")
    analyticalttl: PropertyRef = PropertyRef("resource.analytical_storage_ttl")


@dataclass(frozen=True)
class AzureCosmosDBMongoDBCollectionToCosmosDBMongoDBDatabaseProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureCosmosDBMongoDBDatabase)-[:CONTAINS]->(:AzureCosmosDBMongoDBCollection)
class AzureCosmosDBMongoDBCollectionToCosmosDBMongoDBDatabaseRel(CartographyRelSchema):
    target_node_label: str = "AzureCosmosDBMongoDBDatabase"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("database_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureCosmosDBMongoDBCollectionToCosmosDBMongoDBDatabaseProperties = (
        AzureCosmosDBMongoDBCollectionToCosmosDBMongoDBDatabaseProperties()
    )


@dataclass(frozen=True)
class AzureCosmosDBMongoDBCollectionToSubscriptionRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureCosmosDBMongoDBCollection)
class AzureCosmosDBMongoDBCollectionToSubscriptionRel(CartographyRelSchema):
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
