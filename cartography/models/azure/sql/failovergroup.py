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
    id: PropertyRef = PropertyRef(
        "id", description="Azure resource ID for the SQL failover group."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", description="Azure resource name.")
    location: PropertyRef = PropertyRef(
        "location", description="Azure region of the resource."
    )
    replicationrole: PropertyRef = PropertyRef(
        "replication_role",
        description="Local replication role of the failover group.",
    )
    replicationstate: PropertyRef = PropertyRef(
        "replication_state",
        description="Current replication state of the failover group.",
    )


@dataclass(frozen=True)
class AzureFailoverGroupToSQLServerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSQLServer)-[:CONTAINS]->(:AzureFailoverGroup)
class AzureFailoverGroupToSQLServerRel(CartographyRelSchema):
    """An Azure SQL logical server contains this failover group."""

    target_node_label: str = "AzureSQLServer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("server_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureFailoverGroupToSQLServerRelProperties = (
        AzureFailoverGroupToSQLServerRelProperties()
    )


@dataclass(frozen=True)
class AzureFailoverGroupToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureFailoverGroup)
class AzureFailoverGroupToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains this SQL failover group resource."""

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
# (:AzureSQLServer)-[:RESOURCE]->(:AzureFailoverGroup) - Backwards compatibility
class AzureFailoverGroupToSQLServerDeprecatedRel(CartographyRelSchema):
    """An Azure SQL logical server contains this failover group resource."""

    target_node_label: str = "AzureSQLServer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("server_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureFailoverGroupToSQLServerRelProperties = (
        AzureFailoverGroupToSQLServerRelProperties()
    )


@dataclass(frozen=True)
class AzureFailoverGroupSchema(CartographyNodeSchema):
    """An Azure SQL failover group for databases on partner servers."""

    label: str = "AzureFailoverGroup"
    properties: AzureFailoverGroupProperties = AzureFailoverGroupProperties()
    sub_resource_relationship: AzureFailoverGroupToSubscriptionRel = (
        AzureFailoverGroupToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureFailoverGroupToSQLServerRel(),
            # DEPRECATED: for backward compatibility, will be removed in v1.0.0
            AzureFailoverGroupToSQLServerDeprecatedRel(),
        ]
    )
