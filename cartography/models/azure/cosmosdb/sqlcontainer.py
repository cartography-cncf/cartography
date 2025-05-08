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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    type: PropertyRef = PropertyRef("type")
    location: PropertyRef = PropertyRef("location")
    throughput: PropertyRef = PropertyRef("options.throughput")
    maxthroughput: PropertyRef = PropertyRef("options.autoscale_setting.max_throughput")
    container: PropertyRef = PropertyRef("resource.id")
    defaultttl: PropertyRef = PropertyRef("resource.default_ttl")
    analyticalttl: PropertyRef = PropertyRef("resource.analytical_storage_ttl")
    isautomaticindexingpolicy: PropertyRef = PropertyRef(
        "resource.indexing_policy.automatic"
    )
    indexingmode: PropertyRef = PropertyRef("resource.indexing_policy.indexing_mode")
    conflictresolutionpolicymode: PropertyRef = PropertyRef(
        "resource.conflict_resolution_policy.mode"
    )


@dataclass(frozen=True)
class AzureCosmosDBSqlContainerToCosmosDBSqlDatabaseProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureCosmosDBSqlDatabase)-[:CONTAINS]->(:AzureCosmosDBSqlContainer)
class AzureCosmosDBSqlContainerToCosmosDBSqlDatabaseRel(CartographyRelSchema):
    target_node_label: str = "AzureCosmosDBSqlDatabase"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("database_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureCosmosDBSqlContainerToCosmosDBSqlDatabaseProperties = (
        AzureCosmosDBSqlContainerToCosmosDBSqlDatabaseProperties()
    )


@dataclass(frozen=True)
class AzureCosmosDBSqlContainerToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureCosmosDBSqlContainer)
class AzureCosmosDBSqlContainerToSubscriptionRel(CartographyRelSchema):
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
