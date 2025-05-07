from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.core.relationships import OtherRelationships


@dataclass(frozen=True)
class AzureCosmosDBCassandraKeyspaceProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    location: PropertyRef = PropertyRef("location")
    name: PropertyRef = PropertyRef("name")
    type: PropertyRef = PropertyRef("type")
    throughput: PropertyRef = PropertyRef("options.throughput")
    maxthroughput: PropertyRef = PropertyRef("options.autoscale_setting.max_throughput")


@dataclass(frozen=True)
class AzureCosmosDBCassandraKeyspaceToCosmoDBAccountRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureCosmosDBAccount)-[:CONTAINS]->(:AzureCosmosDBCassandraKeyspace)
class AzureCosmosDBCassandraKeyspaceToCosmosDBAccountRel(CartographyRelSchema):
    target_node_label: str = "AzureCosmosDBAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("database_account_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONTAINS"
    properties: AzureCosmosDBCassandraKeyspaceToCosmoDBAccountRelProperties = (
        AzureCosmosDBCassandraKeyspaceToCosmoDBAccountRelProperties()
    )


@dataclass(frozen=True)
class AzureCosmosDBCassandraKeyspaceToSubscriptionRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)<-[:RESOURCE]-(:AzureCosmosDBCassandraKeyspace)
class AzureCosmosDBCassandraKeyspaceToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: AzureCosmosDBCassandraKeyspaceToSubscriptionRelProperties = (
        AzureCosmosDBCassandraKeyspaceToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureCosmosDBCassandraKeyspaceSchema(CartographyNodeSchema):
    label: str = "AzureCosmosDBCassandraKeyspace"
    properties: AzureCosmosDBCassandraKeyspaceProperties = (
        AzureCosmosDBCassandraKeyspaceProperties()
    )
    sub_resource_relationship: AzureCosmosDBCassandraKeyspaceToSubscriptionRel = (
        AzureCosmosDBCassandraKeyspaceToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureCosmosDBCassandraKeyspaceToCosmosDBAccountRel(),
        ],
    )
