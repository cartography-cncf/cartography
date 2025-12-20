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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    edition: PropertyRef = PropertyRef("edition")
    servicelevelobjective: PropertyRef = PropertyRef("service_level_objective")
    lastbackupdate: PropertyRef = PropertyRef("last_available_backup_date")


@dataclass(frozen=True)
class AzureRecoverableDatabaseToSQLServerProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSQLServer)-[:RESOURCE]->(:AzureRecoverableDatabase)
class AzureRecoverableDatabaseToSQLServerRel(CartographyRelSchema):
    target_node_label: str = "AzureSQLServer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("server_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureRecoverableDatabaseToSQLServerProperties = (
        AzureRecoverableDatabaseToSQLServerProperties()
    )


@dataclass(frozen=True)
class AzureRecoverableDatabaseToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureRecoverableDatabase)
class AzureRecoverableDatabaseToSubscriptionRel(CartographyRelSchema):
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
class AzureRecoverableDatabaseSchema(CartographyNodeSchema):
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
        ]
    )
