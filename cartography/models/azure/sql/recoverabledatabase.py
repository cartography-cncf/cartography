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
class AzureRecoverableDatabaseProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Azure resource ID for the recoverable database."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", description="Azure resource name.")
    edition: PropertyRef = PropertyRef(
        "edition", description="Service edition of the database."
    )
    servicelevelobjective: PropertyRef = PropertyRef(
        "service_level_objective",
        description="Service level objective of the database.",
    )
    lastbackupdate: PropertyRef = PropertyRef(
        "last_available_backup_date",
        description="Timestamp of the latest available database backup.",
    )


@dataclass(frozen=True)
class AzureRecoverableDatabaseToSQLServerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSQLServer)-[:CONTAINS]->(:AzureRecoverableDatabase)
class AzureRecoverableDatabaseToSQLServerRel(CartographyRelSchema):
    """An Azure SQL logical server contains this recoverable database."""

    target_node_label: str = "AzureSQLServer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("server_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureRecoverableDatabaseToSQLServerRelProperties = (
        AzureRecoverableDatabaseToSQLServerRelProperties()
    )


@dataclass(frozen=True)
class AzureRecoverableDatabaseToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureRecoverableDatabase)
class AzureRecoverableDatabaseToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains this recoverable database resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureRecoverableDatabaseToSubscriptionRelProperties = (
        AzureRecoverableDatabaseToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
# (:AzureSQLServer)-[:RESOURCE]->(:AzureRecoverableDatabase) - Backwards compatibility
class AzureRecoverableDatabaseToSQLServerDeprecatedRel(CartographyRelSchema):
    """An Azure SQL logical server contains this recoverable database resource."""

    target_node_label: str = "AzureSQLServer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("server_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureRecoverableDatabaseToSQLServerRelProperties = (
        AzureRecoverableDatabaseToSQLServerRelProperties()
    )


@dataclass(frozen=True)
class AzureRecoverableDatabaseSchema(CartographyNodeSchema):
    """An Azure SQL database recoverable from its available backups."""

    label: str = "AzureRecoverableDatabase"
    properties: AzureRecoverableDatabaseProperties = (
        AzureRecoverableDatabaseProperties()
    )
    sub_resource_relationship: AzureRecoverableDatabaseToSubscriptionRel = (
        AzureRecoverableDatabaseToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureRecoverableDatabaseToSQLServerRel(),
            # DEPRECATED: for backward compatibility, will be removed in v1.0.0
            AzureRecoverableDatabaseToSQLServerDeprecatedRel(),
        ]
    )
