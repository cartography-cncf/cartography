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
class AzureFailoverGroupProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    location: PropertyRef = PropertyRef("location")
    replicationrole: PropertyRef = PropertyRef("replication_role")
    replicationstate: PropertyRef = PropertyRef("replication_state")


@dataclass(frozen=True)
class AzureFailoverGroupToSQLServerProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSQLServer)-[:RESOURCE]->(:AzureFailoverGroup)
class AzureFailoverGroupToSQLServerRel(CartographyRelSchema):
    target_node_label: str = "AzureSQLServer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("server_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureFailoverGroupToSQLServerProperties = (
        AzureFailoverGroupToSQLServerProperties()
    )


@dataclass(frozen=True)
class AzureFailoverGroupToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureFailoverGroup)
class AzureFailoverGroupToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureFailoverGroupToSubscriptionRelProperties = (
        AzureFailoverGroupToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureFailoverGroupSchema(CartographyNodeSchema):
    label: str = "AzureFailoverGroup"
    properties: AzureFailoverGroupProperties = AzureFailoverGroupProperties()
    sub_resource_relationship: AzureFailoverGroupToSubscriptionRel = (
        AzureFailoverGroupToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureFailoverGroupToSQLServerRel(),
        ]
    )
