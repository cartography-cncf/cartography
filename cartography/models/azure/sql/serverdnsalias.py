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
class AzureServerDNSAliasProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Azure resource ID for the SQL server DNS alias."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", description="Azure resource name.")
    dnsrecord: PropertyRef = PropertyRef(
        "azure_dns_record",
        description="Fully qualified DNS record for the alias.",
    )


@dataclass(frozen=True)
class AzureServerDNSAliasToSQLServerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSQLServer)-[:USED_BY]->(:AzureServerDNSAlias)
class AzureServerDNSAliasToSQLServerRel(CartographyRelSchema):
    """An Azure SQL logical server is addressed through this DNS alias."""

    target_node_label: str = "AzureSQLServer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("server_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "USED_BY"
    properties: AzureServerDNSAliasToSQLServerRelProperties = (
        AzureServerDNSAliasToSQLServerRelProperties()
    )


@dataclass(frozen=True)
class AzureServerDNSAliasToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureServerDNSAlias)
class AzureServerDNSAliasToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains this SQL server DNS alias resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureServerDNSAliasToSubscriptionRelProperties = (
        AzureServerDNSAliasToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureServerDNSAliasSchema(CartographyNodeSchema):
    """A DNS alias for an Azure SQL logical server."""

    label: str = "AzureServerDNSAlias"
    properties: AzureServerDNSAliasProperties = AzureServerDNSAliasProperties()
    sub_resource_relationship: AzureServerDNSAliasToSubscriptionRel = (
        AzureServerDNSAliasToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureServerDNSAliasToSQLServerRel(),
        ]
    )
