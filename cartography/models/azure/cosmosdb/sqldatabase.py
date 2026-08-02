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
from cartography.models.ontology.labels import DATABASE


@dataclass(frozen=True)
class AzureCosmosDBSqlDatabaseProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Azure resource ID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    location: PropertyRef = PropertyRef(
        "location",
        description="Azure region where the resource is located.",
    )
    name: PropertyRef = PropertyRef("name", description="Name of the Azure resource.")
    type: PropertyRef = PropertyRef("type", description="Azure resource type.")
    throughput: PropertyRef = PropertyRef(
        "options.throughput",
        description="Manually provisioned throughput in request units per second.",
    )
    maxthroughput: PropertyRef = PropertyRef(
        "options.autoscale_setting.max_throughput",
        description="Maximum autoscale throughput in request units per second.",
    )


@dataclass(frozen=True)
class AzureCosmosDBSqlDatabaseToCosmosDBAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureCosmosDBAccount)-[:CONTAINS]->(:AzureCosmosDBSqlDatabase)
class AzureCosmosDBSqlDatabaseToCosmosDBAccountRel(CartographyRelSchema):
    """A Cosmos DB account contains the SQL database."""

    target_node_label: str = "AzureCosmosDBAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("database_account_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureCosmosDBSqlDatabaseToCosmosDBAccountRelProperties = (
        AzureCosmosDBSqlDatabaseToCosmosDBAccountRelProperties()
    )


@dataclass(frozen=True)
class AzureCosmosDBSqlDatabaseToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureCosmosDBSqlDatabase)
class AzureCosmosDBSqlDatabaseToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the SQL database as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureCosmosDBSqlDatabaseToSubscriptionRelProperties = (
        AzureCosmosDBSqlDatabaseToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureCosmosDBSqlDatabaseSchema(CartographyNodeSchema):
    """A database for the Azure Cosmos DB for NoSQL API."""

    label: str = "AzureCosmosDBSqlDatabase"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([DATABASE])
    properties: AzureCosmosDBSqlDatabaseProperties = (
        AzureCosmosDBSqlDatabaseProperties()
    )
    sub_resource_relationship: AzureCosmosDBSqlDatabaseToSubscriptionRel = (
        AzureCosmosDBSqlDatabaseToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureCosmosDBSqlDatabaseToCosmosDBAccountRel(),
        ]
    )
