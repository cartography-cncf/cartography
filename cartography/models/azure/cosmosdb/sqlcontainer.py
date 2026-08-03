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
class AzureCosmosDBSqlContainerProperties(CartographyNodeProperties):
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
    container: PropertyRef = PropertyRef(
        "resource.id",
        description="Name of the SQL container.",
    )
    defaultttl: PropertyRef = PropertyRef(
        "resource.default_ttl",
        description="Default item time to live in seconds.",
    )
    analyticalttl: PropertyRef = PropertyRef(
        "resource.analytical_storage_ttl",
        description="Analytical store time to live in seconds.",
    )
    isautomaticindexingpolicy: PropertyRef = PropertyRef(
        "resource.indexing_policy.automatic",
        description="Whether the indexing policy indexes documents automatically.",
    )
    indexingmode: PropertyRef = PropertyRef(
        "resource.indexing_policy.indexing_mode",
        description="Indexing mode applied by the container.",
    )
    conflictresolutionpolicymode: PropertyRef = PropertyRef(
        "resource.conflict_resolution_policy.mode",
        description="Conflict resolution mode used by the container.",
    )


@dataclass(frozen=True)
class AzureCosmosDBSqlContainerToCosmosDBSqlDatabaseRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureCosmosDBSqlDatabase)-[:CONTAINS]->(:AzureCosmosDBSqlContainer)
class AzureCosmosDBSqlContainerToCosmosDBSqlDatabaseRel(CartographyRelSchema):
    """A SQL database contains the container."""

    target_node_label: str = "AzureCosmosDBSqlDatabase"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("database_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureCosmosDBSqlContainerToCosmosDBSqlDatabaseRelProperties = (
        AzureCosmosDBSqlContainerToCosmosDBSqlDatabaseRelProperties()
    )


@dataclass(frozen=True)
class AzureCosmosDBSqlContainerToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureCosmosDBSqlContainer)
class AzureCosmosDBSqlContainerToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the SQL container as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureCosmosDBSqlContainerToSubscriptionRelProperties = (
        AzureCosmosDBSqlContainerToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureCosmosDBSqlContainerSchema(CartographyNodeSchema):
    """A container in an Azure Cosmos DB for NoSQL database."""

    label: str = "AzureCosmosDBSqlContainer"
    properties: AzureCosmosDBSqlContainerProperties = (
        AzureCosmosDBSqlContainerProperties()
    )
    sub_resource_relationship: AzureCosmosDBSqlContainerToSubscriptionRel = (
        AzureCosmosDBSqlContainerToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureCosmosDBSqlContainerToCosmosDBSqlDatabaseRel(),
        ]
    )
