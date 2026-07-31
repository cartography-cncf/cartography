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
class AzureCosmosDBCassandraTableProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Azure resource ID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    type: PropertyRef = PropertyRef("type", description="Azure resource type.")
    location: PropertyRef = PropertyRef(
        "location",
        description="Azure region where the resource is located.",
    )
    name: PropertyRef = PropertyRef("name", description="Name of the Azure resource.")
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
        description="Name of the Cassandra table.",
    )
    defaultttl: PropertyRef = PropertyRef(
        "resource.default_ttl",
        description="Default item time to live in seconds.",
    )
    analyticalttl: PropertyRef = PropertyRef(
        "resource.analytical_storage_ttl",
        description="Analytical store time to live in seconds.",
    )


@dataclass(frozen=True)
class AzureCosmosDBCassandraTableToCosmosDBCassandraKeyspaceRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureCosmosDBCassandraKeyspace)-[:CONTAINS]->(:AzureCosmosDBCassandraTable)
class AzureCosmosDBCassandraTableToCosmosDBCassandraKeyspaceRel(CartographyRelSchema):
    """A Cassandra keyspace contains the table."""

    target_node_label: str = "AzureCosmosDBCassandraKeyspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("keyspace_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureCosmosDBCassandraTableToCosmosDBCassandraKeyspaceRelProperties = (
        AzureCosmosDBCassandraTableToCosmosDBCassandraKeyspaceRelProperties()
    )


@dataclass(frozen=True)
class AzureCosmosDBCassandraTableToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureCosmosDBCassandraTable)
class AzureCosmosDBCassandraTableToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the Cassandra table as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureCosmosDBCassandraTableToSubscriptionRelProperties = (
        AzureCosmosDBCassandraTableToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureCosmosDBCassandraTableSchema(CartographyNodeSchema):
    """An Apache Cassandra table in an Azure Cosmos DB keyspace."""

    label: str = "AzureCosmosDBCassandraTable"
    properties: AzureCosmosDBCassandraTableProperties = (
        AzureCosmosDBCassandraTableProperties()
    )
    sub_resource_relationship: AzureCosmosDBCassandraTableToSubscriptionRel = (
        AzureCosmosDBCassandraTableToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureCosmosDBCassandraTableToCosmosDBCassandraKeyspaceRel(),
        ]
    )
