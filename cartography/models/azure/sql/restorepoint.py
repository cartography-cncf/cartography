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
    id: PropertyRef = PropertyRef(
        "id", description="Azure resource ID for the database restore point."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", description="Azure resource name.")
    location: PropertyRef = PropertyRef(
        "location", description="Azure region of the resource."
    )
    restoredate: PropertyRef = PropertyRef(
        "earliest_restore_date",
        description="Earliest timestamp to which the database can be restored.",
    )
    restorepointtype: PropertyRef = PropertyRef(
        "restore_point_type", description="Type of restore point."
    )
    creationdate: PropertyRef = PropertyRef(
        "restore_point_creation_date",
        description="Timestamp when the restore point was created.",
    )


@dataclass(frozen=True)
class AzureRestorePointToSQLDatabaseRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSQLDatabase)-[:CONTAINS]->(:AzureRestorePoint)
class AzureRestorePointToSQLDatabaseRel(CartographyRelSchema):
    """An Azure SQL database contains this restore point."""

    target_node_label: str = "AzureSQLDatabase"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("database_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureRestorePointToSQLDatabaseRelProperties = (
        AzureRestorePointToSQLDatabaseRelProperties()
    )


@dataclass(frozen=True)
class AzureRestorePointToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureRestorePoint)
class AzureRestorePointToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains this database restore point resource."""

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
    """A restore point for an Azure SQL database."""

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
