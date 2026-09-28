from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import DATABASE


@dataclass(frozen=True)
class AzureSQLDatabaseProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Azure resource ID for the SQL database."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", description="Azure resource name.")
    location: PropertyRef = PropertyRef(
        "location", description="Azure region of the resource."
    )
    kind: PropertyRef = PropertyRef(
        "kind", description="Resource kind reported by Azure."
    )
    creationdate: PropertyRef = PropertyRef(
        "creation_date", description="Timestamp when the database was created."
    )
    databaseid: PropertyRef = PropertyRef(
        "database_id", description="Database identifier assigned by Azure SQL."
    )
    maxsizebytes: PropertyRef = PropertyRef(
        "max_size_bytes", description="Maximum database size in bytes."
    )
    licensetype: PropertyRef = PropertyRef(
        "license_type", description="License model for the database."
    )
    secondarylocation: PropertyRef = PropertyRef(
        "default_secondary_location",
        description="Default Azure region for the database's geo-secondary.",
    )
    elasticpoolid: PropertyRef = PropertyRef(
        "elastic_pool_id",
        description="Azure resource ID of the database's elastic pool.",
    )
    collation: PropertyRef = PropertyRef("collation", description="Database collation.")
    failovergroupid: PropertyRef = PropertyRef(
        "failover_group_id",
        description="Azure resource ID of the database's failover group.",
    )
    zoneredundant: PropertyRef = PropertyRef(
        "zone_redundant",
        description="Whether the database uses availability zone redundancy.",
    )
    restorabledroppeddbid: PropertyRef = PropertyRef(
        "restorable_dropped_database_id",
        description="Azure resource ID of the related restorable dropped database.",
    )
    recoverabledbid: PropertyRef = PropertyRef(
        "recoverable_database_id",
        description="Azure resource ID of the related recoverable database.",
    )


@dataclass(frozen=True)
class AzureSQLDatabaseToSQLServerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSQLServer)-[:CONTAINS]->(:AzureSQLDatabase)
class AzureSQLDatabaseToSQLServerRel(CartographyRelSchema):
    """An Azure SQL logical server contains this database."""

    target_node_label: str = "AzureSQLServer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("server_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureSQLDatabaseToSQLServerRelProperties = (
        AzureSQLDatabaseToSQLServerRelProperties()
    )


@dataclass(frozen=True)
class AzureSQLDatabaseToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureSQLDatabase)
class AzureSQLDatabaseToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains this SQL database resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureSQLDatabaseToSubscriptionRelProperties = (
        AzureSQLDatabaseToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
# (:AzureSQLServer)-[:RESOURCE]->(:AzureSQLDatabase) - Backwards compatibility
class AzureSQLDatabaseToSQLServerDeprecatedRel(CartographyRelSchema):
    """An Azure SQL logical server contains this database resource."""

    target_node_label: str = "AzureSQLServer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("server_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureSQLDatabaseToSQLServerRelProperties = (
        AzureSQLDatabaseToSQLServerRelProperties()
    )


@dataclass(frozen=True)
class AzureSQLDatabaseSchema(CartographyNodeSchema):
    """An Azure SQL database hosted by a logical server."""

    label: str = "AzureSQLDatabase"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([DATABASE])
    properties: AzureSQLDatabaseProperties = AzureSQLDatabaseProperties()
    sub_resource_relationship: AzureSQLDatabaseToSubscriptionRel = (
        AzureSQLDatabaseToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureSQLDatabaseToSQLServerRel(),
            # DEPRECATED: for backward compatibility, will be removed in v1.0.0
            AzureSQLDatabaseToSQLServerDeprecatedRel(),
        ]
    )
