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
class AzureRestorePointProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    location: PropertyRef = PropertyRef("location")
    restoredate: PropertyRef = PropertyRef("earliest_restore_date")
    restorepointtype: PropertyRef = PropertyRef("restore_point_type")
    creationdate: PropertyRef = PropertyRef("restore_point_creation_date")


@dataclass(frozen=True)
class AzureRestorePointToSQLDatabaseProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSQLDatabase)-[:CONTAINS]->(:AzureRestorePoint)
class AzureRestorePointToSQLDatabaseRel(CartographyRelSchema):
    target_node_label: str = "AzureSQLDatabase"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("database_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureRestorePointToSQLDatabaseProperties = (
        AzureRestorePointToSQLDatabaseProperties()
    )


@dataclass(frozen=True)
class AzureRestorePointToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureRestorePoint)
class AzureRestorePointToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureRestorePointToSubscriptionRelProperties = (
        AzureRestorePointToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureRestorePointSchema(CartographyNodeSchema):
    label: str = "AzureRestorePoint"
    properties: AzureRestorePointProperties = AzureRestorePointProperties()
    sub_resource_relationship: AzureRestorePointToSubscriptionRel = (
        AzureRestorePointToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureRestorePointToSQLDatabaseRel(),
        ]
    )
