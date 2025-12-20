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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    type: PropertyRef = PropertyRef("type")
    location: PropertyRef = PropertyRef("location")
    name: PropertyRef = PropertyRef("name")
    throughput: PropertyRef = PropertyRef("options.throughput")
    maxthroughput: PropertyRef = PropertyRef("options.autoscale_setting.max_throughput")
    container: PropertyRef = PropertyRef("resource.id")
    defaultttl: PropertyRef = PropertyRef("resource.default_ttl")
    analyticalttl: PropertyRef = PropertyRef("resource.analytical_storage_ttl")


@dataclass(frozen=True)
class AzureCosmosDBCassandraTableToCosmosDBCassandraKeyspaceProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureCosmosDBCassandraKeyspace)-[:CONTAINS]->(:AzureCosmosDBCassandraTable)
class AzureCosmosDBCassandraTableToCosmosDBCassandraKeyspaceRel(CartographyRelSchema):
    target_node_label: str = "AzureCosmosDBCassandraKeyspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("keyspace_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureCosmosDBCassandraTableToCosmosDBCassandraKeyspaceProperties = (
        AzureCosmosDBCassandraTableToCosmosDBCassandraKeyspaceProperties()
    )


@dataclass(frozen=True)
class AzureCosmosDBCassandraTableToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureCosmosDBCassandraTable)
class AzureCosmosDBCassandraTableToSubscriptionRel(CartographyRelSchema):
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
