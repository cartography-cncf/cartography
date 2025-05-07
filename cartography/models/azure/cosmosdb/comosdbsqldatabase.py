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
class AzureCosmosDBSqlDatabaseProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    location: PropertyRef = PropertyRef("location")
    name: PropertyRef = PropertyRef("name")
    type: PropertyRef = PropertyRef("type")
    throughput: PropertyRef = PropertyRef("throughput")
    maxthroughput: PropertyRef = PropertyRef("maxthroughput")


@dataclass(frozen=True)
class AzureCosmosDBSqlDatabaseToCosmosDBAccountProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureCosmosDBAccount)-[:CONTAINS]->(:AzureCosmosDBSqlDatabase)
class AzureCosmosDBSqlDatabaseToCosmosDBAccountRel(CartographyRelSchema):
    target_node_label: str = "AzureCosmosDBAccount"
    # WIP: Check and update the target_node_matcher
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureCosmosDBSqlDatabaseToCosmosDBAccountProperties = (
        AzureCosmosDBSqlDatabaseToCosmosDBAccountProperties()
    )


@dataclass(frozen=True)
class AzureCosmosDBSqlDatabaseToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureCosmosDBSqlDatabase)
class AzureCosmosDBSqlDatabaseToSubscriptionRel(CartographyRelSchema):
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
    label: str = "AzureCosmosDBSqlDatabase"
    properties: AzureCosmosDBSqlDatabaseProperties = (
        AzureCosmosDBSqlDatabaseProperties()
    )
    sub_resource_relationship: AzureCosmosDBSqlDatabaseToSubscriptionRel = (
        AzureCosmosDBSqlDatabaseToSubscriptionRel()
    )
    other_relationsips: OtherRelationships = OtherRelationships(
        [
            AzureCosmosDBSqlDatabaseToCosmosDBAccountRel(),
        ]
    )
