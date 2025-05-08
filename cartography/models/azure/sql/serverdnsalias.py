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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    dnsrecord: PropertyRef = PropertyRef("azure_dns_record")


@dataclass(frozen=True)
class AzureServerDNSAliasToSQLServerProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSQLServer)-[:USED_BY]->(:AzureServerDNSAlias)
class AzureServerDNSAliasToSQLServerRel(CartographyRelSchema):
    target_node_label: str = "AzureSQLServer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("server_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "USED_BY"
    properties: AzureServerDNSAliasToSQLServerProperties = (
        AzureServerDNSAliasToSQLServerProperties()
    )


@dataclass(frozen=True)
class AzureServerDNSAliasToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureServerDNSAlias)
class AzureServerDNSAliasToSubscriptionRel(CartographyRelSchema):
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
