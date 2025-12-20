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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    location: PropertyRef = PropertyRef("location")
    partnerdatabase: PropertyRef = PropertyRef("partner_database")
    partnerlocation: PropertyRef = PropertyRef("partner_location")
    partnerrole: PropertyRef = PropertyRef("partner_role")
    partnerserver: PropertyRef = PropertyRef("partner_server")
    mode: PropertyRef = PropertyRef("replication_mode")
    state: PropertyRef = PropertyRef("replication_state")
    percentcomplete: PropertyRef = PropertyRef("percent_complete")
    role: PropertyRef = PropertyRef("role")
    starttime: PropertyRef = PropertyRef("start_time")
    terminationallowed: PropertyRef = PropertyRef("is_termination_allowed")


@dataclass(frozen=True)
class AzureReplicationLinkToSQLDatabaseProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSQLDatabase)-[:CONTAINS]->(:AzureReplicationLink)
class AzureReplicationLinkToSQLDatabaseRel(CartographyRelSchema):
    target_node_label: str = "AzureSQLDatabase"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("database_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureReplicationLinkToSQLDatabaseProperties = (
        AzureReplicationLinkToSQLDatabaseProperties()
    )


@dataclass(frozen=True)
class AzureReplicationLinkToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureReplicationLink)
class AzureReplicationLinkToSubscriptionRel(CartographyRelSchema):
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
