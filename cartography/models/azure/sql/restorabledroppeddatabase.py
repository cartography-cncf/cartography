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
class AzureRestorableDroppedDatabaseProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    location: PropertyRef = PropertyRef("location")
    name: PropertyRef = PropertyRef("name")
    databasename: PropertyRef = PropertyRef("database_name")
    creationdate: PropertyRef = PropertyRef("creation_date")
    deletiondate: PropertyRef = PropertyRef("deletion_date")
    restoredate: PropertyRef = PropertyRef("earliest_restore_date")
    edition: PropertyRef = PropertyRef("edition")
    servicelevelobjective: PropertyRef = PropertyRef("service_level_objective")
    maxsizebytes: PropertyRef = PropertyRef("max_size_bytes")


@dataclass(frozen=True)
class AzureRestorableDroppedDatabaseToSQLServerProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSQLServer)-[:RESOURCE]->(:AzureRestorableDroppedDatabase)
class AzureRestorableDroppedDatabaseToSQLServerRel(CartographyRelSchema):
    target_node_label: str = "AzureSQLServer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("server_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureRestorableDroppedDatabaseToSQLServerProperties = (
        AzureRestorableDroppedDatabaseToSQLServerProperties()
    )


@dataclass(frozen=True)
class AzureRestorableDroppedDatabaseToSubscriptionRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureRestorableDroppedDatabase)
class AzureRestorableDroppedDatabaseToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureRestorableDroppedDatabaseToSubscriptionRelProperties = (
        AzureRestorableDroppedDatabaseToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureRestorableDroppedDatabaseSchema(CartographyNodeSchema):
    label: str = "AzureRestorableDroppedDatabase"
    properties: AzureRestorableDroppedDatabaseProperties = (
        AzureRestorableDroppedDatabaseProperties()
    )
    sub_resource_relationship: AzureRestorableDroppedDatabaseToSubscriptionRel = (
        AzureRestorableDroppedDatabaseToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureRestorableDroppedDatabaseToSQLServerRel(),
        ]
    )
