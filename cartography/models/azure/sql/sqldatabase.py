from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class AzureSQLDatabaseProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    location: PropertyRef = PropertyRef("location")
    kind = PropertyRef("kind")
    creationdate: PropertyRef = PropertyRef("creation_date")
    databaseid: PropertyRef = PropertyRef("database_id")
    maxsizebytes: PropertyRef = PropertyRef("max_size_bytes")
    licensetype: PropertyRef = PropertyRef("license_type")
    secondarylocation: PropertyRef = PropertyRef("default_secondary_location")
    elasticpoolid: PropertyRef = PropertyRef("elastic_pool_id")
    collation: PropertyRef = PropertyRef("collation")
    failovergroupid: PropertyRef = PropertyRef("failover_group_id")
    zoneredundant: PropertyRef = PropertyRef("zone_redundant")
    restorabledroppeddbid: PropertyRef = PropertyRef("restorable_dropped_database_id")
    recoverabledbid: PropertyRef = PropertyRef("recoverable_database_id")


@dataclass(frozen=True)
class AzureSQLDatabaseToSQLServerProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSQLServer)-[:RESOURCE]->(:AzureSQLDatabase)
class AzureSQLDatabaseToSQLServerRel(CartographyRelSchema):
    target_node_label: str = "AzureSQLServer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("SERVER_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureSQLDatabaseToSQLServerProperties = (
        AzureSQLDatabaseToSQLServerProperties()
    )


@dataclass(frozen=True)
class AzureSQLDatabaseSchema(CartographyNodeSchema):
    label: str = "AzureSQLDatabase"
    properties: AzureSQLDatabaseProperties = AzureSQLDatabaseProperties()
    sub_resource_relationship: AzureSQLDatabaseToSQLServerRel = (
        AzureSQLDatabaseToSQLServerRel()
    )
