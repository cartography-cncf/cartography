from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class AzureCosmosDBMongoDBDatabaseProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    type: PropertyRef = PropertyRef("type")
    location: PropertyRef = PropertyRef("location")
    throughput: PropertyRef = PropertyRef("options.throughput")
    maxthroughput: PropertyRef = PropertyRef("options.autoscale_setting.max_throughput")


@dataclass(frozen=True)
class AzureCosmosDBMongoDBDatabaseToCosmosDBAccountProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureCosmosDBAccount)-[:CONTAINS]->(:AzureCosmosDBMongoDBDatabase)
class AzureCosmosDBMongoDBDatabaseToCosmosDBAccountRel(CartographyRelSchema):
    target_node_label: str = "AzureCosmosDBAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("database_account_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureCosmosDBMongoDBDatabaseToCosmosDBAccountProperties = (
        AzureCosmosDBMongoDBDatabaseToCosmosDBAccountProperties()
    )


@dataclass(frozen=True)
class AzureCosmosDBMongoDBDatabaseToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureCosmosDBMongoDBDatabase)
class AzureCosmosDBMongoDBDatabaseToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureCosmosDBMongoDBDatabaseToSubscriptionRelProperties = (
        AzureCosmosDBMongoDBDatabaseToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureCosmosDBMongoDBDatabaseSchema(CartographyNodeSchema):
    label: str = "AzureCosmosDBMongoDBDatabase"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Database"])
    properties: AzureCosmosDBMongoDBDatabaseProperties = (
        AzureCosmosDBMongoDBDatabaseProperties()
    )
    sub_resource_relationship: AzureCosmosDBMongoDBDatabaseToSubscriptionRel = (
        AzureCosmosDBMongoDBDatabaseToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureCosmosDBMongoDBDatabaseToCosmosDBAccountRel(),
        ]
    )
