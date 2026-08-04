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
class AzureReplicationLinkProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Azure resource ID for the database replication link."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", description="Azure resource name.")
    location: PropertyRef = PropertyRef(
        "location", description="Azure region of the resource."
    )
    partnerdatabase: PropertyRef = PropertyRef(
        "partner_database", description="Name of the partner database."
    )
    partnerlocation: PropertyRef = PropertyRef(
        "partner_location", description="Azure region of the partner database."
    )
    partnerrole: PropertyRef = PropertyRef(
        "partner_role", description="Replication role of the partner database."
    )
    partnerserver: PropertyRef = PropertyRef(
        "partner_server", description="Name of the partner SQL logical server."
    )
    mode: PropertyRef = PropertyRef(
        "replication_mode", description="Replication mode of the link."
    )
    state: PropertyRef = PropertyRef(
        "replication_state", description="Current replication state of the link."
    )
    percentcomplete: PropertyRef = PropertyRef(
        "percent_complete",
        description="Percentage of initial seeding completed.",
    )
    role: PropertyRef = PropertyRef(
        "role", description="Local database's replication role."
    )
    starttime: PropertyRef = PropertyRef(
        "start_time", description="Timestamp when the replication link was created."
    )
    terminationallowed: PropertyRef = PropertyRef(
        "is_termination_allowed",
        description="Whether the replication link can currently be terminated.",
    )


@dataclass(frozen=True)
class AzureReplicationLinkToSQLDatabaseRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSQLDatabase)-[:CONTAINS]->(:AzureReplicationLink)
class AzureReplicationLinkToSQLDatabaseRel(CartographyRelSchema):
    """An Azure SQL database contains this replication link."""

    target_node_label: str = "AzureSQLDatabase"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("database_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureReplicationLinkToSQLDatabaseRelProperties = (
        AzureReplicationLinkToSQLDatabaseRelProperties()
    )


@dataclass(frozen=True)
class AzureReplicationLinkToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureReplicationLink)
class AzureReplicationLinkToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains this database replication link resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureReplicationLinkToSubscriptionRelProperties = (
        AzureReplicationLinkToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureReplicationLinkSchema(CartographyNodeSchema):
    """A replication link between an Azure SQL database and its partner."""

    label: str = "AzureReplicationLink"
    properties: AzureReplicationLinkProperties = AzureReplicationLinkProperties()
    sub_resource_relationship: AzureReplicationLinkToSubscriptionRel = (
        AzureReplicationLinkToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureReplicationLinkToSQLDatabaseRel(),
        ]
    )
