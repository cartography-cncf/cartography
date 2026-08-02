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
    id: PropertyRef = PropertyRef(
        "id", description="Azure resource ID for the restorable dropped database."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    location: PropertyRef = PropertyRef(
        "location", description="Azure region of the resource."
    )
    name: PropertyRef = PropertyRef("name", description="Azure resource name.")
    databasename: PropertyRef = PropertyRef(
        "database_name", description="Name of the deleted database."
    )
    creationdate: PropertyRef = PropertyRef(
        "creation_date", description="Timestamp when the database was created."
    )
    deletiondate: PropertyRef = PropertyRef(
        "deletion_date", description="Timestamp when the database was deleted."
    )
    restoredate: PropertyRef = PropertyRef(
        "earliest_restore_date",
        description="Earliest timestamp to which the database can be restored.",
    )
    edition: PropertyRef = PropertyRef(
        "edition", description="Service edition of the database."
    )
    servicelevelobjective: PropertyRef = PropertyRef(
        "service_level_objective",
        description="Service level objective of the database.",
    )
    maxsizebytes: PropertyRef = PropertyRef(
        "max_size_bytes", description="Maximum database size in bytes."
    )


@dataclass(frozen=True)
class AzureRestorableDroppedDatabaseToSQLServerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSQLServer)-[:CONTAINS]->(:AzureRestorableDroppedDatabase)
class AzureRestorableDroppedDatabaseToSQLServerRel(CartographyRelSchema):
    """An Azure SQL logical server contains this restorable dropped database."""

    target_node_label: str = "AzureSQLServer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("server_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureRestorableDroppedDatabaseToSQLServerRelProperties = (
        AzureRestorableDroppedDatabaseToSQLServerRelProperties()
    )


@dataclass(frozen=True)
class AzureRestorableDroppedDatabaseToSubscriptionRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureRestorableDroppedDatabase)
class AzureRestorableDroppedDatabaseToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains this restorable database resource."""

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
# (:AzureSQLServer)-[:RESOURCE]->(:AzureRestorableDroppedDatabase) - Backwards compatibility
class AzureRestorableDroppedDatabaseToSQLServerDeprecatedRel(CartographyRelSchema):
    """An Azure SQL logical server contains this restorable database resource."""

    target_node_label: str = "AzureSQLServer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("server_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureRestorableDroppedDatabaseToSQLServerRelProperties = (
        AzureRestorableDroppedDatabaseToSQLServerRelProperties()
    )


@dataclass(frozen=True)
class AzureRestorableDroppedDatabaseSchema(CartographyNodeSchema):
    """A deleted Azure SQL database that remains available for restoration."""

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
            # DEPRECATED: for backward compatibility, will be removed in v1.0.0
            AzureRestorableDroppedDatabaseToSQLServerDeprecatedRel(),
        ]
    )
